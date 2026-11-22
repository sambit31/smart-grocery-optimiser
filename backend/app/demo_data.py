"""DEMONSTRATION DATA — not real household history.

Creates one demo account with a catalogue, stock, ~6 months of purchases and
~3 months of consumption so every screen has something to show in a viva.
Dates are relative to today so the demo never goes stale. A fixed random seed
keeps the numbers identical on every run.

Historical demo records are inserted with applied_to_inventory /
deducted_from_stock = False: they are history only, and the current stock is
set directly below.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import (
    Consumption,
    Feedback,
    GroceryItem,
    Household,
    Inventory,
    Purchase,
    Recommendation,
    RecommendationItem,
    StockMovement,
    User,
)
from app.utils.numbers import round_money, round_qty

DEMO_EMAIL = "demo@grocery.local"
DEMO_PASSWORD = "Demo@1234"

# name, category, unit, price (INR), priority, avg monthly use, current stock, low-stock level
DEMO_ITEMS = [
    ("Basmati Rice", "Rice and Grains", "kg", "95", "Essential", 8, 3, 2),
    ("Wheat Atta", "Rice and Grains", "kg", "48", "Essential", 10, 4, 3),
    ("Toor Dal", "Pulses and Dal", "kg", "160", "Essential", 2.5, 0.5, 1),
    ("Moong Dal", "Pulses and Dal", "kg", "130", "Important", 1.5, 1, 0.5),
    ("Mustard Oil", "Cooking Oil", "litre", "175", "Essential", 3, 1, 1),
    ("Milk", "Dairy", "litre", "56", "Essential", 30, 2, 2),
    ("Paneer", "Dairy", "g", "0.40", "Important", 800, 0, 200),
    ("Onion", "Vegetables", "kg", "40", "Essential", 5, 1.5, 1),
    ("Potato", "Vegetables", "kg", "30", "Essential", 6, 2, 1),
    ("Tomato", "Vegetables", "kg", "35", "Important", 4, 0.5, 1),
    ("Banana", "Fruits", "piece", "6", "Important", 40, 6, 6),
    ("Turmeric Powder", "Spices", "packet", "45", "Important", 1, 1, 0),
    ("Garam Masala", "Spices", "packet", "70", "Optional", 1, 0, 0),
    ("Namkeen", "Snacks", "packet", "55", "Optional", 6, 1, 1),
    ("Biscuits", "Snacks", "packet", "30", "Optional", 8, 2, 2),
    ("Dishwash Liquid", "Household Essentials", "ml", "0.22", "Important", 500, 250, 200),
]

# Items WITHOUT consumption history, to demonstrate the two fallback cases:
# name, category, unit, price, priority, initial monthly estimate (None = no data), stock
DEMO_ITEMS_WITHOUT_HISTORY = [
    ("Desi Ghee", "Dairy", "litre", "620", "Important", "0.5", 0),   # uses "Your estimate"
    ("Jaggery", "Other", "kg", "70", "Optional", None, 0),           # shows "Needs data"
]


def _remove_existing_demo_account():
    """Delete a previous demo account, child tables first (FK-safe on MySQL)."""
    user = User.query.filter_by(email=DEMO_EMAIL).first()
    if user is None:
        return
    household = Household.query.filter_by(user_id=user.id).first()
    if household:
        hid = household.id
        plan_ids = [r.id for r in Recommendation.query.filter_by(household_id=hid)]
        Purchase.query.filter_by(household_id=hid).delete()
        if plan_ids:
            RecommendationItem.query.filter(RecommendationItem.recommendation_id.in_(plan_ids)).delete()
        for model in (Recommendation, Consumption, StockMovement, Inventory, Feedback, GroceryItem):
            model.query.filter_by(household_id=hid).delete()
        db.session.delete(household)
    db.session.delete(user)
    db.session.commit()


def seed():
    _remove_existing_demo_account()

    rng = random.Random(42)
    today = date.today()

    user = User(name="Demo User", email=DEMO_EMAIL)
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    db.session.flush()

    household = Household(
        user_id=user.id,
        household_name="Sharma Family (Demo)",
        family_size=4,
        shopping_frequency="Monthly",
        monthly_budget=Decimal("4000"),
        planning_period_days=30,
    )
    db.session.add(household)
    db.session.flush()

    for name, category, unit, price, priority, monthly, stock, low in DEMO_ITEMS:
        item = GroceryItem(
            household_id=household.id,
            name=name,
            category=category,
            unit=unit,
            unit_price=Decimal(price),
            priority=priority,
            description="[DEMO DATA]",
        )
        db.session.add(item)
        db.session.flush()
        db.session.add(Inventory(household_id=household.id, item_id=item.id,
                                 quantity=round_qty(stock), low_stock_threshold=round_qty(low)))

        # ~90 days of consumption with mild variation: weekly entries, or one
        # entry per 30 days for slow items (e.g. 1 spice packet a month).
        whole = unit in ("piece", "packet", "g", "ml")
        interval = 30 if whole and monthly < 4 else 7
        per_entry = Decimal(str(monthly)) * interval / 30
        for index in range(90 // interval):
            qty = per_entry * Decimal(str(rng.uniform(0.85, 1.15)))
            qty = max(Decimal("1"), qty.quantize(Decimal("1"))) if whole else round_qty(qty)
            db.session.add(Consumption(
                household_id=household.id, item_id=item.id, quantity=qty,
                consumed_at=today - timedelta(days=index * interval + 1),
                notes="[DEMO DATA] recorded usage", deducted_from_stock=False,
            ))

        # ~6 months of purchases, about twice a month.
        for visit in range(12):
            qty = Decimal(str(monthly)) / 2 * Decimal(str(rng.uniform(0.8, 1.2)))
            qty = qty.quantize(Decimal("1")) if whole else round_qty(qty)
            if qty <= 0:
                continue
            unit_price = round_money(Decimal(price) * Decimal(str(rng.uniform(0.95, 1.05))))
            db.session.add(Purchase(
                household_id=household.id, item_id=item.id, quantity=qty, unit_price=unit_price,
                total_price=round_money(qty * unit_price),
                purchase_date=today - timedelta(days=visit * 15 + 3),
                store_name=rng.choice(["Local Kirana", "Big Bazaar", "Reliance Fresh"]),
                notes="[DEMO DATA]", applied_to_inventory=False,
            ))

    for name, category, unit, price, priority, estimate, stock in DEMO_ITEMS_WITHOUT_HISTORY:
        item = GroceryItem(
            household_id=household.id, name=name, category=category, unit=unit,
            unit_price=Decimal(price), priority=priority, description="[DEMO DATA] no history",
            initial_monthly_estimate=Decimal(estimate) if estimate else None,
        )
        db.session.add(item)
        db.session.flush()
        db.session.add(Inventory(household_id=household.id, item_id=item.id, quantity=round_qty(stock)))

    db.session.commit()
    return DEMO_EMAIL, DEMO_PASSWORD
