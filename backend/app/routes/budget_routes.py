from flask import Blueprint

from app.extensions import db
from app.models import Recommendation
from app.services import recommendation_service
from app.utils.decorators import get_owned_or_404, household_required
from app.utils.responses import success

budget_bp = Blueprint("budget", __name__, url_prefix="/api")


@budget_bp.post("/recommendations/<int:recommendation_id>/optimise-budget")
@household_required
def optimise_budget(recommendation_id):
    recommendation = get_owned_or_404(Recommendation, recommendation_id, "Plan")
    summary = recommendation_service.optimise_plan(recommendation)
    db.session.commit()
    summary_json = {
        key: (float(value) if key not in ("budget_status", "explanation", "unaffordable_items") else value)
        for key, value in summary.items()
    }
    return success(
        {"recommendation": recommendation.to_dict(), "summary": summary_json},
        "Budget optimisation applied.",
    )
