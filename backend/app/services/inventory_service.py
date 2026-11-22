"""Inventory business logic.

ALL stock changes go through change_stock(). It never lets stock go negative
and logs every change in stock_movements. It does NOT commit: the calling
route commits once, so a purchase and its stock update succeed or fail together
(one database transaction).
"""
from decimal import Decimal

from app.extensions import db
from app.models import Inventory, StockMovement
from app.utils.numbers import round_qty
from app.utils.validators import ValidationError


def get_inventory_record(household_id, item_id, lock=False):
    query = Inventory.query.filter_by(household_id=household_id, item_id=item_id)
    if lock:
        # SELECT ... FOR UPDATE on MySQL, so two simultaneous requests
        # cannot both read the old quantity. (Ignored by SQLite.)
        query = query.with_for_update()
    return query.first()


def get_or_create_inventory(household_id, item_id):
    record = get_inventory_record(household_id, item_id, lock=True)
    if record is None:
        record = Inventory(household_id=household_id, item_id=item_id, quantity=Decimal("0"))
        db.session.add(record)
        db.session.flush()
    return record


def current_stock(household_id, item_id):
    record = get_inventory_record(household_id, item_id)
    return record.quantity if record else Decimal("0")


def change_stock(household_id, item, change, reason, reference_type=None, reference_id=None):
    """Add (positive change) or remove (negative change) stock for an item."""
    change = round_qty(change)
    if change == 0:
        return get_or_create_inventory(household_id, item.id)

    record = get_or_create_inventory(household_id, item.id)
    new_quantity = round_qty(record.quantity + change)
    if new_quantity < 0:
        raise ValidationError(
            f"Not enough stock of {item.name}: only {record.quantity.normalize():f} {item.unit} available, "
            f"but this change needs {abs(change).normalize():f} {item.unit}."
        )
    record.quantity = new_quantity
    db.session.add(
        StockMovement(
            household_id=household_id,
            item_id=item.id,
            change_quantity=change,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
        )
    )
    return record


def set_stock(household_id, item, new_quantity, reason="manual_set"):
    """Set an absolute stock level (logged as the difference)."""
    record = get_or_create_inventory(household_id, item.id)
    difference = round_qty(new_quantity) - record.quantity
    return change_stock(household_id, item, difference, reason, "inventory", record.id)
