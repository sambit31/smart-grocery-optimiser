from flask import Blueprint, current_app, g, request
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import User
from app.utils.decorators import login_required
from app.utils.responses import error, success
from app.utils.validators import (
    ValidationError,
    get_json_body,
    require_string,
    validate_email,
    validate_password,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _auth_limit():
    return current_app.config["AUTH_RATE_LIMIT"]


def _login_response(user, message, status=200):
    response, code = success({"user": user.to_dict()}, message, status)
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response, code


@auth_bp.post("/register")
@limiter.limit(_auth_limit)
def register():
    data = get_json_body(request)
    name = require_string(data, "name", "Name", max_length=100)
    email = validate_email(require_string(data, "email", "Email", max_length=255))
    password = require_string(data, "password", "Password", max_length=128)
    confirm = require_string(data, "confirm_password", "Confirm password", max_length=128)
    validate_password(password)
    if password != confirm:
        raise ValidationError("Passwords do not match.")

    if User.query.filter_by(email=email).first():
        return error("An account with this email already exists.", 409)

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # two requests racing for the same email
        db.session.rollback()
        return error("An account with this email already exists.", 409)
    return _login_response(user, "Account created successfully.", 201)


@auth_bp.post("/login")
@limiter.limit(_auth_limit)
def login():
    data = get_json_body(request)
    email = require_string(data, "email", "Email", max_length=255).lower()
    password = require_string(data, "password", "Password", max_length=128)
    user = User.query.filter_by(email=email).first()
    # Same message for unknown email and wrong password (no account probing).
    if user is None or not user.check_password(password):
        return error("Invalid email or password.", 401)
    return _login_response(user, "Logged in successfully.")


@auth_bp.post("/logout")
def logout():
    response, code = success(None, "Logged out.")
    unset_jwt_cookies(response)
    return response, code


@auth_bp.get("/me")
@login_required
def me():
    return success({"user": g.current_user.to_dict()})
