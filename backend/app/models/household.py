from app.extensions import db
from app.models.user import utc_now
from app.utils.numbers import to_float


class Household(db.Model):
    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)
    # unique=True enforces "one household per user" for this version.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    household_name = db.Column(db.String(120), nullable=False)
    family_size = db.Column(db.Integer, nullable=False)
    shopping_frequency = db.Column(db.String(20), nullable=False, default="Monthly")
    monthly_budget = db.Column(db.Numeric(12, 2), nullable=False)
    planning_period_days = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = db.relationship("User", back_populates="household")

    def to_dict(self):
        return {
            "id": self.id,
            "household_name": self.household_name,
            "family_size": self.family_size,
            "shopping_frequency": self.shopping_frequency,
            "monthly_budget": to_float(self.monthly_budget),
            "planning_period_days": self.planning_period_days,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
