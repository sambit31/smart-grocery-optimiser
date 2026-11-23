
from datetime import date

from flask import Blueprint, current_app, g, request
from app.models import Inventory, Recommendation
from app.services import ai_service, report_service
from app.utils.decorators import household_required
from app.utils.responses import success

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


def get_household_ai_data():
    summary = report_service.dashboard_summary(g.household)
    household = summary.get("household", {})
    today = date.today()

    return {
        "current_date": today.isoformat(),
        "current_month": today.strftime("%B %Y"),
        "household_size": household.get("family_size"),
        "monthly_budget": summary["monthly_budget"],
        "spent_this_month": summary["spent_this_month"],
        "remaining_budget": summary["remaining_budget"],
        "low_stock_count": summary["low_stock_count"],
        "low_stock_items": summary["low_stock_items"],
        "upcoming_purchases": summary["upcoming_purchases"],
        "monthly_spending": summary["monthly_spending"],
        "consumption_overview": summary["consumption_overview"],
    }


@ai_bp.post("/insights")
@household_required
def insights():
    data = get_household_ai_data()
    result = ai_service.generate_grocery_insights(data)

    return success({"insights": result})


@ai_bp.post("/chat")
@household_required
def chat():
    body = request.get_json(silent=True) or {}

    question = body.get("question", "").strip()
    history = body.get("history", [])

    if not question:
        return {
            "success": False,
            "message": "Please enter a question."
        }, 400

    if len(question) > 1000:
        return {
            "success": False,
            "message": "Question must be under 1000 characters."
        }, 400

    if not isinstance(history, list) or len(history) > 10:
        return {
            "success": False,
            "message": "Invalid chat history."
        }, 400

    for message in history:
        if (
            not isinstance(message, dict)
            or message.get("role") not in ("user", "assistant")
            or not isinstance(message.get("content"), str)
            or len(message["content"]) > 2000
        ):
            return {
                "success": False,
                "message": "Invalid chat message."
            }, 400

    data = get_household_ai_data()

    answer = ai_service.chat_with_grocery_assistant(
        question,
        data,
        history
    )

    return success({"answer": answer})


@ai_bp.post("/recommendations")
@household_required
def shopping_recommendations():
    recommendation = (
        Recommendation.query
        .filter_by(household_id=g.household.id)
        .order_by(
            Recommendation.created_at.desc(),
            Recommendation.id.desc()
        )
        .first()
    )

    if recommendation is None:
        return {
            "success": False,
            "message": "Generate a grocery plan before requesting AI recommendations."
        }, 404

    inventory_records = (
        Inventory.query
        .filter_by(household_id=g.household.id)
        .all()
    )

    data = {
     "currency": current_app.config["CURRENCY"],
    "currency_symbol": current_app.config["CURRENCY_SYMBOL"],
    "current_date": date.today().isoformat(),
    "shopping_plan": recommendation.to_dict(),
        "inventory": [
            record.to_dict()
            for record in inventory_records
        ],
    }

    result = ai_service.generate_shopping_recommendations(data)

    return success({
        "recommendation_id": recommendation.id,
        "recommendations": result
    })
