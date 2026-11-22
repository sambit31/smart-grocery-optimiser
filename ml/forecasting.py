"""Reusable grocery consumption forecasting algorithms."""

import math

from sklearn.linear_model import LinearRegression


SMA = "simple_moving_average"
WMA = "weighted_moving_average"
LINEAR_REGRESSION = "linear_regression"


def validate_history(history):
    """Validate historical 30-day consumption totals."""
    if not history:
        raise ValueError("Consumption history cannot be empty.")

    values = [float(value) for value in history]

    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Consumption values must be finite and non-negative.")

    return values


def simple_moving_average(history):
    """Predict using the average of all available periods."""
    values = validate_history(history)
    return sum(values) / len(values)


def weighted_moving_average(history):
    """Give more importance to recent consumption periods."""
    values = validate_history(history)

    if len(values) < 2:
        raise ValueError("Weighted moving average needs at least 2 periods.")

    weights = range(1, len(values) + 1)

    weighted_total = sum(
        value * weight
        for value, weight in zip(values, weights)
    )

    return weighted_total / sum(weights)


def linear_regression(history):
    """Forecast the next period using a linear consumption trend."""
    values = validate_history(history)

    if len(values) < 3:
        raise ValueError("Linear regression needs at least 3 periods.")

    # Input history must be oldest-to-newest.
    X = [[index] for index in range(len(values))]
    y = values

    model = LinearRegression()
    model.fit(X, y)

    prediction = model.predict([[len(values)]])[0]

    # Consumption cannot be negative.
    return max(0.0, float(prediction))


def forecast_candidates(history):
    """Return predictions from every model with enough history."""
    values = validate_history(history)

    predictions = {
        SMA: simple_moving_average(values)
    }

    if len(values) >= 2:
        predictions[WMA] = weighted_moving_average(values)

    if len(values) >= 3:
        predictions[LINEAR_REGRESSION] = linear_regression(values)

    return predictions


def forecast_consumption(history, method=SMA):
    """Generate one forecast using the requested method."""
    methods = {
        SMA: simple_moving_average,
        WMA: weighted_moving_average,
        LINEAR_REGRESSION: linear_regression,
    }

    if method not in methods:
        raise ValueError(f"Unknown forecasting method: {method}")

    return methods[method](history)

def select_best_model(history, min_samples=5, improvement_threshold=0.10):
    """
    Select a forecasting model using chronological validation.

    SMA is the default safe model.
    Another model must improve MAE by at least 10%.
    """

    from ml.evaluation import evaluate_model

    values = validate_history(history)

    results = []

    for method in (SMA, WMA, LINEAR_REGRESSION):
        result = evaluate_model(values, method)

        if result is not None and result["samples"] >= min_samples:
            results.append(result)

    # Always use SMA if there isn't enough validation data.
    if not results:
        return {
            "selected_model": SMA,
            "reason": "Insufficient validation data; using SMA."
        }

    sma_result = next(
        (result for result in results if result["model"] == SMA),
        None
    )

    if sma_result is None:
        return {
            "selected_model": SMA,
            "reason": "SMA baseline unavailable; using SMA fallback."
        }

    best_result = min(results, key=lambda result: result["mae"])

    if best_result["model"] == SMA:
        return {
            "selected_model": SMA,
            "reason": "SMA has the lowest validation error."
        }

    required_mae = sma_result["mae"] * (1 - improvement_threshold)

    if best_result["mae"] < required_mae:
        return {
            "selected_model": best_result["model"],
            "reason": (
                f"{best_result['model']} improved MAE by at least "
                f"{improvement_threshold:.0%} over SMA."
            )
        }

    return {
        "selected_model": SMA,
        "reason": "Alternative models did not improve MAE enough."
    }