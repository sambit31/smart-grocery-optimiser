from app.extensions import db
from app.models.user import utc_now
from app.utils.numbers import to_float


class Consumption(db.Model):
    __tablename__ = "consumption"
    __table_args__ = (db.Index("ix_consumption_household_item_date", "household_id", "item_id", "consumed_at"),)

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("grocery_items.id"), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    consumed_at = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500))
    # True when this record subtracted its quantity from inventory. Stored so
    # edits/deletes reverse exactly what was applied (no double counting).
    deducted_from_stock = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    item = db.relationship("GroceryItem")

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_name": self.item.name,
            "category": self.item.category,
            "unit": self.item.unit,
            "quantity": to_float(self.quantity),
            "consumed_at": self.consumed_at.isoformat(),
            "notes": self.notes,
            "deducted_from_stock": self.deducted_from_stock,
            "created_at": self.created_at.isoformat(),
        }
