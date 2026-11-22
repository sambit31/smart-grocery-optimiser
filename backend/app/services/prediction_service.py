"""Consumption-based prediction (simple moving average).

HOW IT WORKS
------------
1. Consumption records are grouped into rolling 30-day periods counting back
   from the reference date: period 1 = last 30 days, period 2 = 31-60 days
   ago, and so on. Every record is summed into its period, so we always
   average PERIOD TOTALS (never daily values mixed with monthly totals).
2. We look back over the configured history window (default 3 periods).
   Periods older than the item's first-ever record are ignored (the household
   was not tracking it then). Periods after the first record that have no
   entries count as zero usage.
3. average_per_period = sum(period totals) / number of periods used
4. The average is scaled to the planning period:
   predicted_requirement = average_per_period * planning_days / 30
5. recommended_quantity = max(0, predicted_requirement - current_stock)

If an item has no consumption history, the user's own "initial monthly
estimate" is used and clearly labelled. If that is also missing, the item is
marked "needs data" and nothing is recommended for it. No history is ever
invented.
"""
from datetime import timedelta
from decimal import Decimal

import pandas as pd

from app.constants import DAYS_PER_PERIOD
from app.models import Consumption
from app.utils.numbers import round_qty, round_up_to_unit, to_decimal
from ml.forecasting import (
    SMA,
    forecast_consumption,
    select_best_model,
)

SOURCE_HISTORY = "consumption_history"
SOURCE_ESTIMATE = "user_estimate"
SOURCE_NONE = "no_data"


def period_totals(records, reference_date, history_periods):
    """Group (consumed_at, quantity) records into 30-day period totals.

    Returns a list of Decimal totals, most recent period first, containing only
    the periods that count (see module docstring). Pure function: easy to test.
    """
    if not records:
        return []

    frame = pd.DataFrame(records, columns=["consumed_at", "quantity"])
    frame["days_ago"] = frame["consumed_at"].apply(lambda d: (reference_date - d).days)
    # Ignore future-dated records and anything outside the history window.
    frame = frame[(frame["days_ago"] >= 0) & (frame["days_ago"] < history_periods * DAYS_PER_PERIOD)]
    if frame.empty:
        return []

    frame["period"] = frame["days_ago"] // DAYS_PER_PERIOD + 1  # 1 = most recent
    frame["quantity"] = frame["quantity"].apply(to_decimal)
    sums = frame.groupby("period")["quantity"].apply(lambda s: sum(s, Decimal("0")))

    oldest_period_with_data = int(sums.index.max())
    return [sums.get(p, Decimal("0")) for p in range(1, oldest_period_with_data + 1)]


def average_requirement(totals):
    """Simple average of period totals. Example: [7, 8, 9] -> 8."""
    if not totals:
        return None
    return sum(totals, Decimal("0")) / Decimal(len(totals))


def recommended_quantity(predicted_requirement, current_stock):
    """recommended = max(0, predicted - stock). Never negative."""
    result = to_decimal(predicted_requirement) - to_decimal(current_stock)
    return round_qty(max(Decimal("0"), result))


def data_sufficiency(periods_used, history_periods):
    if periods_used >= history_periods:
        return "good"
    if periods_used > 0:
        return "limited"
    return "insufficient"


def predict_item(item, stock, consumption_records, reference_date, planning_days, history_periods):
    """Predict one item's requirement using automatic model selection."""

    scale = Decimal(planning_days) / Decimal(DAYS_PER_PERIOD)
    totals = period_totals(consumption_records, reference_date, history_periods)

    if totals:
        source = SOURCE_HISTORY
        periods_used = len(totals)

        # Backend totals are newest-to-oldest.
        # ML models require oldest-to-newest.
        history = [float(value) for value in reversed(totals)]

        # Select the best model using chronological validation.
        selection = select_best_model(history)
        selected_model = selection["selected_model"]
        selection_reason = selection["reason"]

        # Calculate the forecast using the selected model.
        try:
            predicted_per_period = Decimal(
                str(forecast_consumption(history, selected_model))
            )
        except (ValueError, ArithmeticError):
            # Safe fallback if the selected model cannot forecast.
            selected_model = SMA
            predicted_per_period = Decimal(
                str(forecast_consumption(history, SMA))
            )
            selection_reason = "Selected model failed; SMA fallback used."

        predicted = round_qty(predicted_per_period * scale)

        model_names = {
            "simple_moving_average": "Simple Moving Average",
            "weighted_moving_average": "Weighted Moving Average",
            "linear_regression": "Linear Regression",
        }
        model_name = model_names.get(selected_model, selected_model)

        shown_totals = ", ".join(
            f"{value:g}" for value in history
        )

        reason = (
            f"{model_name} forecast using {periods_used} chronological "
            f"30-day period(s) [{shown_totals}] {item.unit}. "
            f"Model selection: {selection_reason} "
            f"Forecast scaled to {planning_days} days."
        )

    elif item.initial_monthly_estimate is not None:
        source = SOURCE_ESTIMATE
        predicted = round_qty(item.initial_monthly_estimate * scale)
        periods_used = 0

        reason = (
            f"No consumption history yet. Using your initial estimate of "
            f"{item.initial_monthly_estimate.normalize():f} "
            f"{item.unit}/month, scaled to {planning_days} days."
        )

    else:
        source = SOURCE_NONE
        predicted = Decimal("0")
        periods_used = 0

        reason = (
            "No consumption history or initial estimate. "
            "Record consumption or add an estimate to get a prediction."
        )

    stock = to_decimal(stock)
    needed = recommended_quantity(predicted, stock)

    # Keep existing packaged / indivisible unit rounding.
    needed = round_up_to_unit(needed, item.unit)

    if source != SOURCE_NONE:
        reason += (
            f" Need {predicted.normalize():f} "
            f"- stock {stock.normalize():f} "
            f"-> buy {needed.normalize():f} {item.unit}."
        )

    return {
        "item_id": item.id,
        "predicted_quantity": predicted,
        "stock_quantity": stock,
        "recommended_quantity": needed,
        "prediction_source": source,
        "periods_used": periods_used,
        "data_sufficiency": (
            data_sufficiency(periods_used, history_periods)
            if source == SOURCE_HISTORY
            else (
                "estimate"
                if source == SOURCE_ESTIMATE
                else "insufficient"
            )
        ),
        "reason": reason,
    }


def load_consumption_records(household_id, item_id, reference_date, history_periods):
    start = reference_date - timedelta(days=history_periods * DAYS_PER_PERIOD)
    rows = (
        Consumption.query.with_entities(Consumption.consumed_at, Consumption.quantity)
        .filter(
            Consumption.household_id == household_id,
            Consumption.item_id == item_id,
            Consumption.consumed_at > start,
            Consumption.consumed_at <= reference_date,
        )
        .all()
    )
    return [(row.consumed_at, row.quantity) for row in rows]


def prediction_method_label(history_periods):
    return (
        f"Adaptive per-item forecasting (SMA/WMA/LR), "
        f"last {history_periods} x 30-day periods"
    )