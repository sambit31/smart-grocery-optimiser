"""Prediction and saved-plan (recommendation) endpoints."""
from flask import Blueprint, g, request

from app.extensions import db
from app.models import Recommendation, RecommendationItem
from app.services import recommendation_service
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
)

prediction_bp = Blueprint("predictions", __name__, url_prefix="/api")


def _get_line(recommendation, line_id):
    line = RecommendationItem.query.filter_by(id=line_id, recommendation_id=recommendation.id).first()
    if line is None:
        raise ValidationError("Plan item not found.", 404)
    return line


@prediction_bp.post("/predictions/generate")
@household_required
def generate():
    data = get_json_body(request)
    history_periods = parse_int(data, "history_periods", "History window", 1, 12, required=False)
    recommendation = recommendation_service.generate_plan(g.household, history_periods=history_periods)
    if parse_bool(data, "optimise", default=False):
        recommendation_service.optimise_plan(recommendation)
    db.session.commit()
    return success({"recommendation": recommendation.to_dict()}, "Grocery plan generated and saved.", 201)


@prediction_bp.get("/predictions/latest")
@household_required
def latest():
    recommendation = (
        Recommendation.query.filter_by(household_id=g.household.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .first()
    )
    return success({"recommendation": recommendation.to_dict() if recommendation else None})


@prediction_bp.get("/recommendations")
@household_required
def list_recommendations():
    plans = (
        Recommendation.query.filter_by(household_id=g.household.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(50)
        .all()
    )
    return success({"recommendations": [p.to_dict(include_items=False) for p in plans]})


@prediction_bp.get("/recommendations/<int:recommendation_id>")
@household_required
def get_recommendation(recommendation_id):
    recommendation = get_owned_or_404(Recommendation, recommendation_id, "Plan")
    return success({"recommendation": recommendation.to_dict()})


@prediction_bp.patch("/recommendations/<int:recommendation_id>/items/<int:line_id>")
@household_required
def update_item(recommendation_id, line_id):
    """Edit a line's final quantity and/or tick its checkbox (no purchase recorded)."""
    recommendation = get_owned_or_404(Recommendation, recommendation_id, "Plan")
    line = _get_line(recommendation, line_id)
    data = get_json_body(request)
    final_quantity = parse_decimal(data, "final_quantity", "Quantity", max_value=100_000, required=False)
    is_checked = parse_bool(data, "is_checked") if "is_checked" in data else None
    if final_quantity is None and is_checked is None:
        raise ValidationError("Nothing to update. Send final_quantity and/or is_checked.")
    recommendation_service.update_line(recommendation, line, final_quantity, is_checked)
    db.session.commit()
    return success({"recommendation": recommendation.to_dict()}, "Plan item updated.")


@prediction_bp.post("/recommendations/<int:recommendation_id>/items/<int:line_id>/mark-purchased")
@household_required
def mark_purchased(recommendation_id, line_id):
    """Explicitly record the purchase AND add it to inventory (one transaction)."""
    recommendation = get_owned_or_404(Recommendation, recommendation_id, "Plan")
    line = _get_line(recommendation, line_id)
    data = get_json_body(request)
    purchase = recommendation_service.mark_line_purchased(
        g.household,
        recommendation,
        line,
        quantity=parse_decimal(data, "quantity", "Quantity", max_value=100_000, required=False),
        unit_price=parse_decimal(data, "unit_price", "Unit price", max_value=1_000_000, required=False, places=2),
        purchase_date=parse_date(data, "purchase_date", "Purchase date", required=False, allow_future=False),
        store_name=require_string(data, "store_name", "Store name", max_length=120, required=False),
    )
    db.session.commit()
    return success(
        {"recommendation": recommendation.to_dict(), "purchase": purchase.to_dict()},
        "Purchase recorded and inventory updated.",
        201,
    )
