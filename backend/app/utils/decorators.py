"""Route decorators for authentication and household ownership."""
from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models import Household, User
from app.utils.validators import ValidationError


def login_required(view):
    """Require a valid JWT cookie and load the user into g.current_user."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = db.session.get(User, int(get_jwt_identity()))
        if user is None:
            raise ValidationError("Your session is no longer valid. Please log in again.", 401)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def household_required(view):
    """Require login AND an existing household; loads it into g.household.

    Every household-scoped route uses this, and every query then filters by
    g.household.id, so a user can never read or change another household's data.
    """

    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        household = Household.query.filter_by(user_id=g.current_user.id).first()
        if household is None:
            raise ValidationError("Please set up your household first.", 409)
        g.household = household
        return view(*args, **kwargs)

    return wrapper


def get_owned_or_404(model, record_id, label="Record"):
    """Fetch a record only if it belongs to the current household.

    Returns 404 (not 403) for other households' records so we do not reveal
    that the record exists.
    """
    record = model.query.filter_by(id=record_id, household_id=g.household.id).first()
    if record is None:
        raise ValidationError(f"{label} not found.", 404)
    return record
