"""Input validation helpers.

Every route reads request data through these functions, so the same rules
apply everywhere and invalid input always produces a clear 400 message.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Raised for bad user input. Converted to a 400 JSON response."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_json_body(request):
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def require_string(data, field, label=None, max_length=255, required=True):
    label = label or field.replace("_", " ").capitalize()
    value = data.get(field)
    if value is None or (isinstance(value, str) and value.strip() == ""):
        if required:
            raise ValidationError(f"{label} is required.")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    value = value.strip()
    if len(value) > max_length:
        raise ValidationError(f"{label} must be at most {max_length} characters.")
    return value


def parse_decimal(data, field, label=None, min_value=None, max_value=None, required=True,
                  allow_zero=True, places=3):
    label = label or field.replace("_", " ").capitalize()
    raw = data.get(field)
    if raw is None or raw == "":
        if required:
            raise ValidationError(f"{label} is required.")
        return None
    if isinstance(raw, bool):
        raise ValidationError(f"{label} must be a number.")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{label} must be a number.")
    if not value.is_finite():
        raise ValidationError(f"{label} must be a number.")
    if value < 0:
        raise ValidationError(f"{label} must be zero or greater.")
    if not allow_zero and value == 0:
        raise ValidationError(f"{label} must be greater than zero.")
    if min_value is not None and value < Decimal(str(min_value)):
        raise ValidationError(f"{label} must be at least {min_value}.")
    if max_value is not None and value > Decimal(str(max_value)):
        raise ValidationError(f"{label} must be at most {max_value}.")
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and -exponent > places:
        raise ValidationError(f"{label} can have at most {places} decimal places.")
    return value


def parse_signed_decimal(data, field, label=None, max_abs=1_000_000):
    """Like parse_decimal but allows negative values (for stock +/- changes)."""
    label = label or field.replace("_", " ").capitalize()
    raw = data.get(field)
    if raw is None or raw == "" or isinstance(raw, bool):
        raise ValidationError(f"{label} is required.")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{label} must be a number.")
    if not value.is_finite() or value == 0:
        raise ValidationError(f"{label} must be a non-zero number.")
    if abs(value) > max_abs:
        raise ValidationError(f"{label} is too large.")
    return value


def parse_int(data, field, label=None, min_value=None, max_value=None, required=True):
    label = label or field.replace("_", " ").capitalize()
    raw = data.get(field)
    if raw is None or raw == "":
        if required:
            raise ValidationError(f"{label} is required.")
        return None
    if isinstance(raw, bool):
        raise ValidationError(f"{label} must be a whole number.")
    try:
        if isinstance(raw, float) and not raw.is_integer():
            raise ValueError
        value = int(str(raw).strip())
    except (ValueError, TypeError):
        raise ValidationError(f"{label} must be a whole number.")
    if min_value is not None and value < min_value:
        raise ValidationError(f"{label} must be at least {min_value}.")
    if max_value is not None and value > max_value:
        raise ValidationError(f"{label} must be at most {max_value}.")
    return value


def parse_date(data, field, label=None, required=True, allow_future=True):
    label = label or field.replace("_", " ").capitalize()
    raw = data.get(field)
    if raw is None or raw == "":
        if required:
            raise ValidationError(f"{label} is required.")
        return None
    try:
        value = date.fromisoformat(str(raw)[:10])
    except ValueError:
        raise ValidationError(f"{label} must be a valid date (YYYY-MM-DD).")
    if not allow_future and value > date.today():
        raise ValidationError(f"{label} cannot be in the future.")
    return value


def parse_choice(data, field, choices, label=None, required=True):
    label = label or field.replace("_", " ").capitalize()
    value = data.get(field)
    if value is None or value == "":
        if required:
            raise ValidationError(f"{label} is required.")
        return None
    if value not in choices:
        raise ValidationError(f"{label} must be one of: {', '.join(choices)}.")
    return value


def parse_bool(data, field, default=False):
    value = data.get(field, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def validate_email(email):
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Please enter a valid email address.")
    return email.lower()


def validate_password(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one letter and one number.")
    return password


def validate_date_range(start, end):
    if start and end and start > end:
        raise ValidationError("Start date must be on or before end date.")
