"""Small Decimal helpers used across models and services.

Money and quantities are stored as DECIMAL in MySQL and handled as Python
Decimal in the backend, so there are no floating-point rounding surprises.
They are converted to float only when sent to the frontend as JSON.
"""
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.constants import UNIT_STEP

MONEY_PLACES = Decimal("0.01")
QTY_PLACES = Decimal("0.001")


def to_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value):
    return to_decimal(value).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def round_qty(value):
    return to_decimal(value).quantize(QTY_PLACES, rounding=ROUND_HALF_UP)


def unit_step(unit):
    return Decimal(UNIT_STEP.get(unit, "0.001"))


def round_up_to_unit(quantity, unit):
    """Round a quantity UP to the unit's buying step (e.g. 2.3 pieces -> 3)."""
    step = unit_step(unit)
    quantity = to_decimal(quantity)
    if quantity <= 0:
        return Decimal("0")
    steps = (quantity / step).to_integral_value(rounding=ROUND_CEILING)
    return round_qty(steps * step)


def to_float(value):
    if value is None:
        return None
    return float(value)
