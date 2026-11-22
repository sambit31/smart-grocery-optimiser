from datetime import date

from flask import Blueprint, g, request

from app.models import GroceryItem, Recommendation
from app.services import report_service
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import success
from app.utils.validators import parse_int

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


def _months_arg():
    return parse_int(request.args, "months", "Months", 1, 24, required=False) or 6


@dashboard_bp.get("/dashboard/summary")
@household_required
def summary():
    return success(report_service.dashboard_summary(g.household))


@dashboard_bp.get("/reports/spending")
@household_required
def spending():
    months = _months_arg()
    by_month = report_service.monthly_spending(g.household, months)
    start = date.fromisoformat(by_month[0]["month"] + "-01")
    total = sum(m["total"] for m in by_month)
    return success(
        {
            "by_month": by_month,
            "by_category": report_service.spending_by_category(g.household, start),
            "total_spent": round(total, 2),
            "average_monthly": round(total / months, 2),
            "months": months,
        }
    )


@dashboard_bp.get("/reports/consumption")
@household_required
def consumption():
    months = _months_arg()
    item_id = parse_int(request.args, "item_id", "Item", required=False)
    trend = None
    if item_id:
        item = get_owned_or_404(GroceryItem, item_id, "Item")
        trend = {"item_id": item.id, "item_name": item.name, "unit": item.unit,
                 "months": report_service.consumption_trend(g.household, item.id, months)}
    return success(
        {
            "last_30_days": report_service.consumption_last_days(g.household, 30),
            "trend": trend,
        }
    )


@dashboard_bp.get("/reports/recommendations")
@household_required
def recommendations():
    plans = (
        Recommendation.query.filter_by(household_id=g.household.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(20)
        .all()
    )
    return success(
        {
            "history": [p.to_dict(include_items=False) for p in plans],
            "predicted_vs_purchased": report_service.predicted_vs_purchased(g.household),
        }
    )
