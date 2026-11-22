from flask import Blueprint, g, request

from app.extensions import db
from app.models import GroceryItem, Inventory
from app.services.inventory_service import change_stock, set_stock
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import error, success
from app.utils.validators import (
    get_json_body,
    parse_bool,
    parse_date,
    parse_decimal,
    parse_int,
    parse_signed_decimal,
    require_string,
)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@inventory_bp.get("")
@household_required
def list_inventory():
    args = request.args
    query = Inventory.query.join(GroceryItem).filter(
        Inventory.household_id == g.household.id, GroceryItem.is_archived.is_(False)
    )
    if args.get("search"):
        query = query.filter(GroceryItem.name.ilike(f"%{args['search'].strip()[:100]}%"))
    if args.get("category"):
        query = query.filter(GroceryItem.category == args["category"])
    if parse_bool(args, "low_stock"):
        query = query.filter(Inventory.quantity <= Inventory.low_stock_threshold)
    records = query.order_by(GroceryItem.name).all()

    tracked_ids = {r.item_id for r in Inventory.query.filter_by(household_id=g.household.id)}
    untracked = (
        GroceryItem.query.filter_by(household_id=g.household.id, is_archived=False)
        .filter(GroceryItem.id.notin_(tracked_ids) if tracked_ids else True)
        .order_by(GroceryItem.name)
        .all()
    )
    return success(
        {
            "inventory": [r.to_dict() for r in records],
            "low_stock_count": sum(1 for r in records if r.is_low_stock),
            "untracked_items": [{"id": i.id, "name": i.name, "unit": i.unit} for i in untracked],
        }
    )


@inventory_bp.post("")
@household_required
def add_inventory():
    data = get_json_body(request)
    item = get_owned_or_404(GroceryItem, parse_int(data, "item_id", "Item"), "Item")
    if item.is_archived:
        return error("This item is archived. Restore it before adding stock.", 400)
    if Inventory.query.filter_by(item_id=item.id).first():
        return error(f"{item.name} is already in your inventory. Update its quantity instead.", 409)
    quantity = parse_decimal(data, "quantity", "Quantity", max_value=1_000_000)
    record = Inventory(
        household_id=g.household.id,
        item_id=item.id,
        quantity=0,
        low_stock_threshold=parse_decimal(data, "low_stock_threshold", "Low-stock level", max_value=1_000_000,
                                          required=False) or 0,
        expiry_date=parse_date(data, "expiry_date", "Expiry date", required=False),
    )
    db.session.add(record)
    db.session.flush()
    change_stock(g.household.id, item, quantity, "initial_stock", "inventory", record.id)
    db.session.commit()
    return success({"inventory": record.to_dict()}, "Stock added.", 201)


@inventory_bp.put("/<int:record_id>")
@household_required
def update_inventory(record_id):
    """Set the absolute quantity, low-stock level and expiry date."""
    record = get_owned_or_404(Inventory, record_id, "Inventory record")
    data = get_json_body(request)
    quantity = parse_decimal(data, "quantity", "Quantity", max_value=1_000_000)
    record.low_stock_threshold = parse_decimal(
        data, "low_stock_threshold", "Low-stock level", max_value=1_000_000, required=False
    ) or 0
    record.expiry_date = parse_date(data, "expiry_date", "Expiry date", required=False)
    set_stock(g.household.id, record.item, quantity, "manual_set")
    db.session.commit()
    return success({"inventory": record.to_dict()}, "Inventory updated.")


@inventory_bp.patch("/<int:record_id>/quantity")
@household_required
def adjust_quantity(record_id):
    """Increase (positive change) or decrease (negative change) stock."""
    record = get_owned_or_404(Inventory, record_id, "Inventory record")
    data = get_json_body(request)
    change = parse_signed_decimal(data, "change", "Change")
    reason = require_string(data, "reason", "Reason", max_length=40, required=False) or "manual_adjustment"
    change_stock(g.household.id, record.item, change, reason[:40], "inventory", record.id)
    db.session.commit()
    return success({"inventory": record.to_dict()}, "Stock adjusted.")
