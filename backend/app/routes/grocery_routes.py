from flask import Blueprint, g, request
from sqlalchemy import func

from app.constants import CATEGORIES, PRIORITIES, UNITS
from app.extensions import db
from app.models import Consumption, GroceryItem, Inventory, Purchase, RecommendationItem, StockMovement
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import error, success
from app.utils.validators import (
    ValidationError,
    get_json_body,
    parse_bool,
    parse_choice,
    parse_decimal,
    require_string,
)

grocery_bp = Blueprint("groceries", __name__, url_prefix="/api/groceries")

SORT_OPTIONS = {
    "name": GroceryItem.name.asc(),
    "price_asc": GroceryItem.unit_price.asc(),
    "price_desc": GroceryItem.unit_price.desc(),
    "category": GroceryItem.category.asc(),
    "newest": GroceryItem.created_at.desc(),
}


def _read_item_fields(data):
    return {
        "name": require_string(data, "name", "Item name", max_length=120),
        "category": parse_choice(data, "category", CATEGORIES, "Category"),
        "unit": parse_choice(data, "unit", UNITS, "Unit"),
        "unit_price": parse_decimal(data, "unit_price", "Unit price", max_value=1_000_000, allow_zero=False, places=2),
        "priority": parse_choice(data, "priority", PRIORITIES, "Priority"),
        "description": require_string(data, "description", "Description", max_length=500, required=False),
        "initial_monthly_estimate": parse_decimal(
            data, "initial_monthly_estimate", "Initial monthly estimate", max_value=100_000, required=False
        ),
    }


def _related_counts(item_id):
    return {
        "purchases": Purchase.query.filter_by(item_id=item_id).count(),
        "consumption": Consumption.query.filter_by(item_id=item_id).count(),
        "plans": RecommendationItem.query.filter_by(item_id=item_id).count(),
    }


def _name_taken(name, exclude_id=None):
    query = GroceryItem.query.filter(
        GroceryItem.household_id == g.household.id, func.lower(GroceryItem.name) == name.lower()
    )
    if exclude_id:
        query = query.filter(GroceryItem.id != exclude_id)
    return query.first()


@grocery_bp.get("")
@household_required
def list_items():
    args = request.args
    query = GroceryItem.query.filter_by(household_id=g.household.id)
    if not parse_bool(args, "include_archived"):
        query = query.filter_by(is_archived=False)
    if args.get("search"):
        query = query.filter(GroceryItem.name.ilike(f"%{args['search'].strip()[:100]}%"))
    if args.get("category"):
        query = query.filter_by(category=args["category"])
    if args.get("priority"):
        query = query.filter_by(priority=args["priority"])
    query = query.order_by(SORT_OPTIONS.get(args.get("sort"), GroceryItem.name.asc()), GroceryItem.id)

    page = max(1, args.get("page", 1, type=int))
    per_page = min(100, max(1, args.get("per_page", 20, type=int)))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return success(
        {
            "items": [item.to_dict() for item in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }
    )


@grocery_bp.post("")
@household_required
def create_item():
    fields = _read_item_fields(get_json_body(request))
    existing = _name_taken(fields["name"])
    if existing and not existing.is_archived:
        return error(f"An item named '{fields['name']}' already exists.", 409)
    if existing and existing.is_archived:
        # Re-adding an archived item restores it (keeps its history).
        for key, value in fields.items():
            setattr(existing, key, value)
        existing.is_archived = False
        db.session.commit()
        return success({"item": existing.to_dict()}, "Archived item restored and updated.", 200)

    item = GroceryItem(household_id=g.household.id, **fields)
    db.session.add(item)
    db.session.commit()
    return success({"item": item.to_dict()}, "Item added.", 201)


@grocery_bp.get("/<int:item_id>")
@household_required
def get_item(item_id):
    item = get_owned_or_404(GroceryItem, item_id, "Item")
    data = item.to_dict()
    data["related_counts"] = _related_counts(item.id)
    return success({"item": data})


@grocery_bp.put("/<int:item_id>")
@household_required
def update_item(item_id):
    item = get_owned_or_404(GroceryItem, item_id, "Item")
    data = get_json_body(request)
    fields = _read_item_fields(data)
    if _name_taken(fields["name"], exclude_id=item.id):
        return error(f"An item named '{fields['name']}' already exists.", 409)
    has_history = any(_related_counts(item.id).values()) or (item.inventory and item.inventory.quantity > 0)
    if fields["unit"] != item.unit and has_history:
        raise ValidationError("The unit cannot be changed once the item has stock or history (quantities would no longer match).")
    for key, value in fields.items():
        setattr(item, key, value)
    if "is_archived" in data:
        item.is_archived = parse_bool(data, "is_archived")
    db.session.commit()
    return success({"item": item.to_dict()}, "Item updated.")


@grocery_bp.delete("/<int:item_id>")
@household_required
def delete_item(item_id):
    """Documented rule: archive if the item has history, otherwise delete."""
    item = get_owned_or_404(GroceryItem, item_id, "Item")
    if any(_related_counts(item.id).values()):
        item.is_archived = True
        db.session.commit()
        return success({"archived": True}, "Item has purchase/consumption/plan history, so it was archived. History is kept.")
    StockMovement.query.filter_by(item_id=item.id).delete()
    Inventory.query.filter_by(item_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    return success({"archived": False}, "Item deleted.")
