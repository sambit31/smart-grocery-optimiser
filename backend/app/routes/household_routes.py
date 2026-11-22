from flask import Blueprint, g, request

from app.constants import CATEGORIES, FREQUENCY_DAYS, PRIORITIES, SHOPPING_FREQUENCIES, UNITS
from app.extensions import db
from app.models import Household
from app.utils.decorators import household_required, login_required
from app.utils.responses import error, success
from app.utils.validators import get_json_body, parse_choice, parse_decimal, parse_int, require_string

household_bp = Blueprint("household", __name__, url_prefix="/api")


def _read_household_fields(data):
    """Only these fields can be set by the user (prevents mass assignment)."""
    frequency = parse_choice(data, "shopping_frequency", SHOPPING_FREQUENCIES, "Shopping frequency")
    planning_days = parse_int(data, "planning_period_days", "Planning period (days)", 1, 90, required=False)
    return {
        "household_name": require_string(data, "household_name", "Household name", max_length=120),
        "family_size": parse_int(data, "family_size", "Family size", 1, 30),
        "shopping_frequency": frequency,
        "monthly_budget": parse_decimal(
            data, "monthly_budget", "Monthly budget", max_value=10_000_000, allow_zero=False, places=2
        ),
        "planning_period_days": planning_days or FREQUENCY_DAYS[frequency],
    }


@household_bp.get("/household")
@login_required
def get_household():
    household = Household.query.filter_by(user_id=g.current_user.id).first()
    return success({"household": household.to_dict() if household else None})


@household_bp.post("/household")
@login_required
def create_household():
    if Household.query.filter_by(user_id=g.current_user.id).first():
        return error("You already have a household. Use update instead.", 409)
    fields = _read_household_fields(get_json_body(request))
    household = Household(user_id=g.current_user.id, **fields)
    db.session.add(household)
    db.session.commit()
    return success({"household": household.to_dict()}, "Household created.", 201)


@household_bp.put("/household")
@household_required
def update_household():
    fields = _read_household_fields(get_json_body(request))
    for key, value in fields.items():
        setattr(g.household, key, value)
    db.session.commit()
    return success({"household": g.household.to_dict()}, "Household updated.")


@household_bp.get("/meta/options")
def options():
    """Dropdown options, defined once in app/constants.py."""
    return success(
        {
            "categories": CATEGORIES,
            "units": UNITS,
            "priorities": PRIORITIES,
            "shopping_frequencies": SHOPPING_FREQUENCIES,
            "frequency_days": FREQUENCY_DAYS,
        }
    )
