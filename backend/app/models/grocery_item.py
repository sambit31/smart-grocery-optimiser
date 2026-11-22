from app.extensions import db
from app.models.user import utc_now
from app.utils.numbers import to_float


class GroceryItem(db.Model):
    """A catalogue item belonging to one household.

    Deletion rule: an item that has purchases, consumption or plan entries is
    *archived* (is_archived = True) instead of deleted, so history is kept.
    Items with no related records are deleted permanently.
    """

    __tablename__ = "grocery_items"
    __table_args__ = (db.UniqueConstraint("household_id", "name", name="uq_item_household_name"),)

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="Important")
    description = db.Column(db.String(500))
    # Optional user-entered estimate used ONLY when there is no consumption history.
    initial_monthly_estimate = db.Column(db.Numeric(12, 3))
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    inventory = db.relationship("Inventory", back_populates="item", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "unit_price": to_float(self.unit_price),
            "priority": self.priority,
            "description": self.description,
            "initial_monthly_estimate": to_float(self.initial_monthly_estimate),
            "is_archived": self.is_archived,
            "current_stock": to_float(self.inventory.quantity) if self.inventory else 0.0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
