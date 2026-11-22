from app.extensions import db
from app.models.user import utc_now
from app.utils.numbers import to_float


class Inventory(db.Model):
    """Current stock of one item. One row per item (unique item_id).

    Quantities are always in the item's own unit (item.unit).
    """

    __tablename__ = "inventory"
    __table_args__ = (db.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),)

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("grocery_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    low_stock_threshold = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    expiry_date = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    item = db.relationship("GroceryItem", back_populates="inventory")

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_name": self.item.name,
            "category": self.item.category,
            "priority": self.item.priority,
            "unit": self.item.unit,
            "is_archived": self.item.is_archived,
            "quantity": to_float(self.quantity),
            "low_stock_threshold": to_float(self.low_stock_threshold),
            "is_low_stock": self.is_low_stock,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "updated_at": self.updated_at.isoformat(),
        }


class StockMovement(db.Model):
    """Audit trail: every change to inventory is logged here.

    This makes stock changes traceable (useful in a viva demo) and lets us
    show exactly why a quantity changed.
    """

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("grocery_items.id", ondelete="CASCADE"), nullable=False, index=True)
    change_quantity = db.Column(db.Numeric(12, 3), nullable=False)
    reason = db.Column(db.String(40), nullable=False)
    reference_type = db.Column(db.String(30))
    reference_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
