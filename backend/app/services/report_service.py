"""Aggregations for the dashboard and reports. All figures come from the DB.

Grouping by calendar month is done in Python (not SQL date functions) so the
same code works on MySQL and on the SQLite test database.
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from app.models import Consumption, GroceryItem, Inventory, Purchase, Recommendation
from app.utils.numbers import round_money, round_qty, to_float


def month_keys(months, today=None):
    """Last `months` calendar months, oldest first, as (year, month) tuples."""
    today = today or date.today()
    year, month = today.year, today.month
    keys = []
    for _ in range(months):
        keys.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(keys))


def month_label(key):
    return date(key[0], key[1], 1).strftime("%b %Y")


def first_day(key):
    return date(key[0], key[1], 1)


def monthly_spending(household, months=6, today=None):
    keys = month_keys(months, today)
    rows = Purchase.query.filter(
        Purchase.household_id == household.id, Purchase.purchase_date >= first_day(keys[0])
    ).all()
    totals = defaultdict(Decimal)
    for purchase in rows:
        totals[(purchase.purchase_date.year, purchase.purchase_date.month)] += purchase.total_price
    budget = household.monthly_budget
    return [
        {
            "month": f"{k[0]}-{k[1]:02d}",
            "label": month_label(k),
            "total": to_float(round_money(totals[k])),
            "budget": to_float(budget),
            "budget_used_percent": round(float(totals[k] / budget * 100), 1) if budget else 0,
        }
        for k in keys
    ]


def spending_by_category(household, start_date):
    rows = Purchase.query.filter(
        Purchase.household_id == household.id, Purchase.purchase_date >= start_date
    ).all()
    totals = defaultdict(Decimal)
    for purchase in rows:
        totals[purchase.item.category] += purchase.total_price
    return sorted(
        ({"category": c, "total": to_float(round_money(t))} for c, t in totals.items()),
        key=lambda r: -r["total"],
    )


def consumption_last_days(household, days=30, today=None, limit=None):
    today = today or date.today()
    rows = Consumption.query.filter(
        Consumption.household_id == household.id, Consumption.consumed_at > today - timedelta(days=days)
    ).all()
    totals = defaultdict(Decimal)
    items = {}
    for record in rows:
        totals[record.item_id] += record.quantity
        items[record.item_id] = record.item
    result = sorted(
        (
            {"item_id": i, "item_name": items[i].name, "unit": items[i].unit,
             "quantity": to_float(round_qty(q)), "category": items[i].category}
            for i, q in totals.items()
        ),
        key=lambda r: r["item_name"],
    )
    return result[:limit] if limit else result


def consumption_trend(household, item_id, months=6, today=None):
    keys = month_keys(months, today)
    rows = Consumption.query.filter(
        Consumption.household_id == household.id,
        Consumption.item_id == item_id,
        Consumption.consumed_at >= first_day(keys[0]),
    ).all()
    totals = defaultdict(Decimal)
    for record in rows:
        totals[(record.consumed_at.year, record.consumed_at.month)] += record.quantity
    return [{"month": f"{k[0]}-{k[1]:02d}", "label": month_label(k), "quantity": to_float(round_qty(totals[k]))}
            for k in keys]


def predicted_vs_purchased(household, limit=5):
    """For recent plans: planned quantity vs quantity actually bought in the plan window."""
    plans = (
        Recommendation.query.filter_by(household_id=household.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .limit(limit)
        .all()
    )
    result = []
    for plan in plans:
        purchases = Purchase.query.filter(
            Purchase.household_id == household.id,
            Purchase.purchase_date >= plan.planning_period_start,
            Purchase.purchase_date <= plan.planning_period_end,
        ).all()
        bought = defaultdict(Decimal)
        for purchase in purchases:
            bought[purchase.item_id] += purchase.quantity
        lines = [
            {
                "item_name": line.item.name,
                "unit": line.item.unit,
                "predicted": to_float(line.predicted_quantity),
                "planned": to_float(line.final_quantity),
                "purchased": to_float(round_qty(bought[line.item_id])),
            }
            for line in plan.items
            if line.final_quantity > 0 or bought[line.item_id] > 0
        ]
        result.append(
            {
                "recommendation_id": plan.id,
                "period": f"{plan.planning_period_start.isoformat()} to {plan.planning_period_end.isoformat()}",
                "has_purchase_data": bool(purchases),
                "items": lines,
            }
        )
    return result


def dashboard_summary(household, today=None):
    today = today or date.today()
    month_start = today.replace(day=1)
    spent_this_month = sum(
        (p.total_price for p in Purchase.query.filter(
            Purchase.household_id == household.id, Purchase.purchase_date >= month_start,
            Purchase.purchase_date <= today)),
        Decimal("0"),
    )
    active_items = GroceryItem.query.filter_by(household_id=household.id, is_archived=False).count()
    inventory = (
        Inventory.query.join(GroceryItem)
        .filter(Inventory.household_id == household.id, GroceryItem.is_archived.is_(False))
        .all()
    )
    low_stock = [r for r in inventory if r.is_low_stock]
    recent = (
        Purchase.query.filter_by(household_id=household.id)
        .order_by(Purchase.purchase_date.desc(), Purchase.id.desc())
        .limit(5)
        .all()
    )
    latest_plan = (
        Recommendation.query.filter_by(household_id=household.id)
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        .first()
    )
    upcoming = []
    if latest_plan:
        upcoming = [
            {"item_name": l.item.name, "quantity": to_float(l.final_quantity), "unit": l.item.unit,
             "estimated_cost": to_float(l.estimated_cost), "priority": l.priority}
            for l in latest_plan.items
            if l.final_quantity > 0 and not l.is_purchased
        ][:6]

    return {
        "household": household.to_dict(),
        "monthly_budget": to_float(household.monthly_budget),
        "spent_this_month": to_float(round_money(spent_this_month)),
        "remaining_budget": to_float(round_money(household.monthly_budget - spent_this_month)),
        "estimated_plan_cost": to_float(latest_plan.final_total_cost) if latest_plan else None,
        "item_count": active_items,
        "low_stock_count": len(low_stock),
        "low_stock_items": [r.to_dict() for r in low_stock[:5]],
        "recent_purchases": [p.to_dict() for p in recent],
        "upcoming_purchases": upcoming,
        "latest_plan": latest_plan.to_dict(include_items=False) if latest_plan else None,
        "monthly_spending": monthly_spending(household, 6, today),
        "consumption_overview": consumption_last_days(household, 30, today, limit=8),
    }
