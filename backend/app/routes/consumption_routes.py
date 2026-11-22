from flask import Blueprint, g, request

from app.extensions import db
from app.models import Consumption, GroceryItem
from app.services import purchase_service
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import success
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

consumption_bp = Blueprint("consumption", __name__, url_prefix="/api/consumption")


def _read_fields(data):
    return {
        "item": get_owned_or_404(GroceryItem, parse_int(data, "item_id", "Item"), "Item"),
        "quantity": parse_decimal(data, "quantity", "Quantity", max_value=100_000, allow_zero=False),
        "consumed_at": parse_date(data, "consumed_at", "Consumption date", allow_future=False),
        "notes": require_string(data, "notes", "Notes", max_length=500, required=False),
    }


@consumption_bp.get("")
@household_required
def list_consumption():
    args = request.args
    query = Consumption.query.filter_by(household_id=g.household.id)
    start = parse_date(args, "start_date", "Start date", required=False)
    end = parse_date(args, "end_date", "End date", required=False)
    validate_date_range(start, end)
    if start:
        query = query.filter(Consumption.consumed_at >= start)
    if end:
        query = query.filter(Consumption.consumed_at <= end)
    if args.get("item_id"):
        query = query.filter(Consumption.item_id == parse_int(args, "item_id", "Item"))
    page = max(1, args.get("page", 1, type=int))
    per_page = min(100, max(1, args.get("per_page", 20, type=int)))
    pagination = query.order_by(Consumption.consumed_at.desc(), Consumption.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success(
        {
            "consumption": [c.to_dict() for c in pagination.items],
            "pagination": {"page": pagination.page, "per_page": per_page, "total": pagination.total,
                           "pages": pagination.pages},
        }
    )


@consumption_bp.post("")
@household_required
def create_consumption():
    data = get_json_body(request)
    fields = _read_fields(data)
    if fields["item"].is_archived:
        raise ValidationError("This item is archived. Restore it before recording consumption.")
    record = purchase_service.create_consumption(
        g.household.id, fields["item"], fields["quantity"], fields["consumed_at"], fields["notes"],
        deduct_from_stock=parse_bool(data, "deduct_from_stock", default=True),
    )
    db.session.commit()
    return success({"consumption": record.to_dict()}, "Consumption recorded.", 201)


@consumption_bp.put("/<int:record_id>")
@household_required
def update_consumption(record_id):
    record = get_owned_or_404(Consumption, record_id, "Consumption record")
    fields = _read_fields(get_json_body(request))
    purchase_service.update_consumption(record, fields["item"], fields["quantity"], fields["consumed_at"],
                                        fields["notes"])
    db.session.commit()
    return success({"consumption": record.to_dict()}, "Consumption updated.")


@consumption_bp.delete("/<int:record_id>")
@household_required
def delete_consumption(record_id):
    record = get_owned_or_404(Consumption, record_id, "Consumption record")
    purchase_service.delete_consumption(record)
    db.session.commit()
    return success(None, "Consumption record deleted.")
