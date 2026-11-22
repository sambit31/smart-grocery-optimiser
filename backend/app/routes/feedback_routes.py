from flask import Blueprint, g, request

from app.extensions import db
from app.models import Feedback
from app.utils.decorators import household_required
from app.utils.responses import success
from app.utils.validators import get_json_body, parse_int, require_string

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@feedback_bp.get("")
@household_required
def list_feedback():
    rows = Feedback.query.filter_by(household_id=g.household.id).order_by(Feedback.created_at.desc()).all()
    return success({"feedback": [f.to_dict() for f in rows]})


@feedback_bp.post("")
@household_required
def create_feedback():
    data = get_json_body(request)
    feedback = Feedback(
        household_id=g.household.id,
        rating=parse_int(data, "rating", "Rating", 1, 5),
        comment=require_string(data, "comment", "Comment", max_length=1000, required=False),
    )
    db.session.add(feedback)
    db.session.commit()
    return success({"feedback": feedback.to_dict()}, "Thank you for your feedback!", 201)
