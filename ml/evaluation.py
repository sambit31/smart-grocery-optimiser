"""Chronological evaluation for grocery consumption forecasting."""

import math

from ml.forecasting import (
    SMA,
    WMA,
    LINEAR_REGRESSION,
    forecast_consumption,
)


def calculate_mae(actual, predicted):
    """Mean Absolute Error."""
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Actual and predicted values must have equal non-zero lengths.")

    return sum(
        abs(a - p) for a, p in zip(actual, predicted)
    ) / len(actual)


def calculate_rmse(actual, predicted):
    """Root Mean Squared Error."""
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Actual and predicted values must have equal non-zero lengths.")

    mse = sum(
        (a - p) ** 2 for a, p in zip(actual, predicted)
    ) / len(actual)

    return math.sqrt(mse)


def evaluate_model(history, method, min_train_periods=3):
    """Evaluate a model using expanding-window walk-forward validation."""

    values = [float(value) for value in history]

    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Consumption values must be finite and non-negative.")

    if min_train_periods < 1:
        raise ValueError("Minimum training periods must be positive.")

    actual = []
    predicted = []

    for index in range(min_train_periods, len(values)):
        train_history = values[:index]

        try:
            prediction = forecast_consumption(train_history, method)
        except ValueError:
            continue

        actual.append(values[index])
        predicted.append(prediction)

    if not actual:
        return None

    return {
        "model": method,
        "samples": len(actual),
        "mae": calculate_mae(actual, predicted),
        "rmse": calculate_rmse(actual, predicted),
    }


def compare_models(history):
    """Compare eligible models and rank by MAE, then RMSE."""

    results = []

    for method in (SMA, WMA, LINEAR_REGRESSION):
        result = evaluate_model(history, method)

        if result is not None:
            results.append(result)

    return sorted(results, key=lambda row: (row["mae"], row["rmse"]))
