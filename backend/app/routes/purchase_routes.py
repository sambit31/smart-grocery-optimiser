from flask import Blueprint, g, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import GroceryItem, Purchase
from app.services import purchase_service
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import error, success
from app.utils.validators import (
    ValidationError,
    get_json_body,
    parse_bool,
    parse_date,
    parse_decimal,
    parse_int,
    require_string,
    validate_date_range,
)

purchase_bp = Blueprint("purchases", __name__, url_prefix="/api/purchases")


def _read_purchase_fields(data):
    item = get_owned_or_404(GroceryItem, parse_int(data, "item_id", "Item"), "Item")
    quantity = parse_decimal(data, "quantity", "Quantity", max_value=100_000, allow_zero=False)
    unit_price = parse_decimal(data, "unit_price", "Unit price", max_value=1_000_000, required=False, places=2)
    return {
        "item": item,
        "quantity": quantity,
        "unit_price": unit_price if unit_price is not None else item.unit_price,
        "purchase_date": parse_date(data, "purchase_date", "Purchase date", allow_future=False),
        "store_name": require_string(data, "store_name", "Store name", max_length=120, required=False),
        "notes": require_string(data, "notes", "Notes", max_length=500, required=False),
    }


def _filtered_query(args):
    query = Purchase.query.filter_by(household_id=g.household.id)
    start = parse_date(args, "start_date", "Start date", required=False)
    end = parse_date(args, "end_date", "End date", required=False)
    validate_date_range(start, end)
    if start:
        query = query.filter(Purchase.purchase_date >= start)
    if end:
        query = query.filter(Purchase.purchase_date <= end)
    if args.get("item_id"):
        query = query.filter(Purchase.item_id == parse_int(args, "item_id", "Item"))
    return query


@purchase_bp.get("")
@household_required
def list_purchases():
    query = _filtered_query(request.args)
    total = query.with_entities(func.coalesce(func.sum(Purchase.total_price), 0)).scalar()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    pagination = query.order_by(Purchase.purchase_date.desc(), Purchase.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success(
        {
            "purchases": [p.to_dict() for p in pagination.items],
            "total_expenditure": float(total or 0),
            "pagination": {"page": pagination.page, "per_page": per_page, "total": pagination.total,
                           "pages": pagination.pages},
        }
    )


@purchase_bp.post("")
@household_required
def create_purchase():
    data = get_json_body(request)
    fields = _read_purchase_fields(data)
    if fields["item"].is_archived:
        raise ValidationError("This item is archived. Restore it before recording new purchases.")
    client_reference = require_string(data, "client_reference", "Client reference", max_length=64, required=False)
    try:
        purchase = purchase_service.create_purchase(
            g.household.id,
            fields["item"],
            fields["quantity"],
            fields["unit_price"],
            fields["purchase_date"],
            fields["store_name"],
            fields["notes"],
            apply_to_inventory=parse_bool(data, "update_inventory", default=True),
            client_reference=client_reference,
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("This purchase was already recorded (duplicate submission ignored).", 409)
    return success({"purchase": purchase.to_dict()}, "Purchase recorded.", 201)


@purchase_bp.get("/<int:purchase_id>")
@household_required
def get_purchase(purchase_id):
    return success({"purchase": get_owned_or_404(Purchase, purchase_id, "Purchase").to_dict()})


@purchase_bp.put("/<int:purchase_id>")
@household_required
def update_purchase(purchase_id):
    purchase = get_owned_or_404(Purchase, purchase_id, "Purchase")
    fields = _read_purchase_fields(get_json_body(request))
    if purchase.recommendation_item_id and fields["item"].id != purchase.item_id:
        raise ValidationError("A purchase made from a grocery plan cannot be moved to a different item.")
    purchase_service.update_purchase(
        purchase, fields["item"], fields["quantity"], fields["unit_price"], fields["purchase_date"],
        fields["store_name"], fields["notes"],
    )
    db.session.commit()
    return success({"purchase": purchase.to_dict()}, "Purchase updated and stock reconciled.")


@purchase_bp.delete("/<int:purchase_id>")
@household_required
def delete_purchase(purchase_id):
    purchase = get_owned_or_404(Purchase, purchase_id, "Purchase")
    purchase_service.delete_purchase(purchase)
    db.session.commit()
    return success(None, "Purchase deleted and its stock reversed.")

