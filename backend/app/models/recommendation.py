import json

from app.extensions import db
from app.models.user import utc_now
from app.utils.numbers import round_money, to_float


class Recommendation(db.Model):
    """A saved grocery plan. Status: generated -> optimised -> completed."""

    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    planning_period_start = db.Column(db.Date, nullable=False)
    planning_period_end = db.Column(db.Date, nullable=False)
    predicted_total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    final_total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    budget = db.Column(db.Numeric(12, 2), nullable=False)
    prediction_method = db.Column(db.String(120), nullable=False)
    history_periods = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(20), nullable=False, default="generated")
    budget_status = db.Column(db.String(30), nullable=False, default="within_budget")
    # JSON list of human-readable explanation lines from budget optimisation.
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    items = db.relationship(
        "RecommendationItem",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="RecommendationItem.id",
    )

    def explanation_lines(self):
        return json.loads(self.explanation) if self.explanation else []

    def to_dict(self, include_items=True):
        data = {
            "id": self.id,
            "planning_period_start": self.planning_period_start.isoformat(),
            "planning_period_end": self.planning_period_end.isoformat(),
            "predicted_total_cost": to_float(self.predicted_total_cost),
            "final_total_cost": to_float(self.final_total_cost),
            "budget": to_float(self.budget),
            "remaining_budget": to_float(self.budget - self.final_total_cost),
            "prediction_method": self.prediction_method,
            "history_periods": self.history_periods,
            "status": self.status,
            "budget_status": self.budget_status,
            "explanation": self.explanation_lines(),
            "created_at": self.created_at.isoformat(),
            "item_count": len(self.items),
            "purchased_count": sum(1 for i in self.items if i.is_purchased),
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class RecommendationItem(db.Model):
    __tablename__ = "recommendation_items"
    __table_args__ = (db.UniqueConstraint("recommendation_id", "item_id", name="uq_recommendation_item"),)

    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(
        db.Integer, db.ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id = db.Column(db.Integer, db.ForeignKey("grocery_items.id"), nullable=False)
    predicted_quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    stock_quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    recommended_quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    final_quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    priority = db.Column(db.String(20), nullable=False)
    # consumption_history | user_estimate | no_data
    prediction_source = db.Column(db.String(30), nullable=False)
    periods_used = db.Column(db.Integer, nullable=False, default=0)
    data_sufficiency = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(500))
    # full | reduced | removed | unaffordable | not_needed | needs_data | edited
    plan_status = db.Column(db.String(20), nullable=False, default="full")
    adjustment_note = db.Column(db.String(500))
    is_checked = db.Column(db.Boolean, nullable=False, default=False)
    is_purchased = db.Column(db.Boolean, nullable=False, default=False)

    recommendation = db.relationship("Recommendation", back_populates="items")
    item = db.relationship("GroceryItem")
    purchase = db.relationship("Purchase", uselist=False, foreign_keys="Purchase.recommendation_item_id")

    @property
    def fits_budget(self):
        return self.plan_status in ("full", "reduced", "not_needed", "edited")

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_name": self.item.name,
            "category": self.item.category,
            "unit": self.item.unit,
            "predicted_quantity": to_float(self.predicted_quantity),
            "stock_quantity": to_float(self.stock_quantity),
            "recommended_quantity": to_float(self.recommended_quantity),
            "final_quantity": to_float(self.final_quantity),
            "unit_price": to_float(self.unit_price),
            "estimated_cost": to_float(self.estimated_cost),
            # Cost of the unadjusted recommendation (before budget changes/edits).
            "recommended_cost": to_float(round_money(self.recommended_quantity * self.unit_price)),
            "priority": self.priority,
            "prediction_source": self.prediction_source,
            "periods_used": self.periods_used,
            "data_sufficiency": self.data_sufficiency,
            "reason": self.reason,
            "plan_status": self.plan_status,
            "fits_budget": self.fits_budget,
            "adjustment_note": self.adjustment_note,
            "is_checked": self.is_checked,
            "is_purchased": self.is_purchased,
            "purchase_id": self.purchase.id if self.purchase else None,
        }
