"""Builds, saves and updates grocery plans (recommendations).

Flow: generate_plan() -> optimise_plan() -> update_line()/mark_line_purchased()
"""
import json
from datetime import date, timedelta
from decimal import Decimal

from flask import current_app

from app.constants import DAYS_PER_PERIOD, INDIVISIBLE_UNITS
from app.extensions import db
from app.models import GroceryItem, Recommendation, RecommendationItem
from app.services import budget_service, prediction_service
from app.services.inventory_service import current_stock
from app.services.purchase_service import create_purchase
from app.utils.numbers import round_money, to_decimal, unit_step
from app.utils.validators import ValidationError


def plan_budget(household, planning_days):
    """Budget for the planning period = monthly budget scaled by days / 30."""
    return round_money(household.monthly_budget * Decimal(planning_days) / Decimal(DAYS_PER_PERIOD))


def generate_plan(household, reference_date=None, history_periods=None):
    reference_date = reference_date or date.today()
    history_periods = history_periods or current_app.config["PREDICTION_HISTORY_PERIODS"]
    planning_days = household.planning_period_days

    items = (
        GroceryItem.query.filter_by(household_id=household.id, is_archived=False)
        .order_by(GroceryItem.name)
        .all()
    )
    if not items:
        raise ValidationError("Add grocery items to your catalogue before generating a plan.")

    recommendation = Recommendation(
        household_id=household.id,
        planning_period_start=reference_date,
        planning_period_end=reference_date + timedelta(days=planning_days - 1),
        budget=plan_budget(household, planning_days),
        prediction_method=prediction_service.prediction_method_label(history_periods),
        history_periods=history_periods,
        status="generated",
    )
    db.session.add(recommendation)

    for item in items:
        records = prediction_service.load_consumption_records(household.id, item.id, reference_date, history_periods)
        result = prediction_service.predict_item(
            item,
            current_stock(household.id, item.id),
            records,
            reference_date,
            planning_days,
            history_periods,
        )
        if result["prediction_source"] == prediction_service.SOURCE_NONE:
            plan_status = "needs_data"
        elif result["recommended_quantity"] > 0:
            plan_status = "full"
        else:
            plan_status = "not_needed"

        recommendation.items.append(
            RecommendationItem(
                item_id=item.id,
                item=item,
                predicted_quantity=result["predicted_quantity"],
                stock_quantity=result["stock_quantity"],
                recommended_quantity=result["recommended_quantity"],
                final_quantity=result["recommended_quantity"],
                unit_price=item.unit_price,
                estimated_cost=budget_service.line_cost(result["recommended_quantity"], item.unit_price),
                priority=item.priority,
                prediction_source=result["prediction_source"],
                periods_used=result["periods_used"],
                data_sufficiency=result["data_sufficiency"],
                reason=result["reason"],
                plan_status=plan_status,
            )
        )

    total = sum((line.estimated_cost for line in recommendation.items), Decimal("0"))
    recommendation.predicted_total_cost = total
    recommendation.final_total_cost = total
    if total <= recommendation.budget:
        recommendation.budget_status = budget_service.STATUS_WITHIN
        note = "Estimated cost is within the budget."
    else:
        recommendation.budget_status = "needs_optimisation"
        note = "Estimated cost is over the budget. Run budget optimisation to adjust the plan."
    recommendation.explanation = json.dumps([note])
    db.session.flush()
    return recommendation


def optimise_plan(recommendation):
    if any(line.is_purchased for line in recommendation.items):
        raise ValidationError("This plan already has purchased items, so it can no longer be re-optimised.", 409)

    lines = [
        {
            "line": line,
            "item_name": line.item.name,
            "unit": line.item.unit,
            "unit_price": line.unit_price,
            "priority": line.priority,
            "recommended_quantity": line.recommended_quantity,
            "plan_status": "needs_data" if line.prediction_source == prediction_service.SOURCE_NONE else None,
        }
        for line in recommendation.items
    ]
    lines, summary = budget_service.optimise(lines, recommendation.budget)

    for data in lines:
        line = data["line"]
        line.final_quantity = data["final_quantity"]
        line.estimated_cost = data["estimated_cost"]
        line.plan_status = data["plan_status"]
        line.adjustment_note = data["adjustment_note"]

    recommendation.predicted_total_cost = summary["predicted_total_cost"]
    recommendation.final_total_cost = summary["final_total_cost"]
    recommendation.budget_status = summary["budget_status"]
    recommendation.explanation = json.dumps(summary["explanation"])
    recommendation.status = "optimised"
    return summary


def recalculate_totals(recommendation):
    total = sum((line.estimated_cost for line in recommendation.items), Decimal("0"))
    recommendation.final_total_cost = round_money(total)
    if total <= recommendation.budget:
        if recommendation.budget_status != budget_service.STATUS_OPTIMISED:
            recommendation.budget_status = budget_service.STATUS_WITHIN
    else:
        recommendation.budget_status = budget_service.STATUS_OVER


def validate_quantity_for_unit(quantity, unit):
    step = unit_step(unit)
    if unit in INDIVISIBLE_UNITS and quantity % step != 0:
        raise ValidationError(f"Quantity for items sold by '{unit}' must be a whole number.")


def update_line(recommendation, line, final_quantity=None, is_checked=None):
    if final_quantity is not None:
        if line.is_purchased:
            raise ValidationError("This item has already been purchased; its quantity can no longer be edited.", 409)
        validate_quantity_for_unit(final_quantity, line.item.unit)
        old = line.final_quantity
        line.final_quantity = final_quantity
        line.estimated_cost = budget_service.line_cost(final_quantity, line.unit_price)
        if final_quantity != old:
            line.plan_status = "edited"
            line.adjustment_note = (
                f"Edited by you from {to_decimal(old).normalize():f} to "
                f"{to_decimal(final_quantity).normalize():f} {line.item.unit}."
            )
        recalculate_totals(recommendation)
    if is_checked is not None:
        # Checking a box is ONLY a shopping-trip tick. It does not record a
        # purchase or change inventory — that is mark_line_purchased().
        line.is_checked = is_checked
    return line


def mark_line_purchased(household, recommendation, line, quantity=None, unit_price=None,
                        purchase_date=None, store_name=None):
    if line.is_purchased:
        raise ValidationError("This item is already recorded as purchased.", 409)
    quantity = quantity if quantity is not None else line.final_quantity
    if quantity <= 0:
        raise ValidationError("Purchased quantity must be greater than zero.")
    validate_quantity_for_unit(quantity, line.item.unit)
    unit_price = unit_price if unit_price is not None else line.unit_price

    purchase = create_purchase(
        household.id,
        line.item,
        quantity,
        unit_price,
        purchase_date or date.today(),
        store_name=store_name,
        notes=f"From grocery plan #{recommendation.id}",
        apply_to_inventory=True,
        recommendation_item_id=line.id,
    )
    line.is_purchased = True
    line.is_checked = True

    to_buy = [l for l in recommendation.items if l.final_quantity > 0]
    if to_buy and all(l.is_purchased for l in to_buy):
        recommendation.status = "completed"
    return purchase
