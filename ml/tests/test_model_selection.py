import pytest

from ml.forecasting import (
    SMA,
    WMA,
    LINEAR_REGRESSION,
    select_best_model,
)


def test_limited_history_uses_sma_fallback():
    history = [8, 10, 9, 11, 10, 12]

    result = select_best_model(history)

    assert result["selected_model"] == SMA
    assert "Insufficient validation data" in result["reason"]


def test_stable_consumption_selects_sma():
    history = [8, 8, 9, 8, 8, 9, 8, 8, 9, 8,
               8, 9, 8, 8, 9, 8, 8, 9, 8, 8]

    result = select_best_model(history)

    assert result["selected_model"] == SMA


def test_upward_trend_can_select_linear_regression():
    history = [7, 8, 7, 9, 8, 10, 9, 11, 10, 12, 11, 13,
               12, 14, 13, 15]

    result = select_best_model(history)

    assert result["selected_model"] == LINEAR_REGRESSION


def test_wma_selected_when_improvement_is_significant(monkeypatch):
    from ml import evaluation

    results = {
        SMA: {"model": SMA, "mae": 10.0, "rmse": 11.0, "samples": 8},
        WMA: {"model": WMA, "mae": 8.5, "rmse": 9.0, "samples": 8},
        LINEAR_REGRESSION: {
            "model": LINEAR_REGRESSION,
            "mae": 9.5,
            "rmse": 10.0,
            "samples": 8,
        },
    }

    monkeypatch.setattr(
        evaluation,
        "evaluate_model",
        lambda history, method: results[method],
    )

    result = select_best_model([8, 9, 10, 11, 12, 13, 14, 15])

    assert result["selected_model"] == WMA


def test_sma_used_when_improvement_is_too_small(monkeypatch):
    from ml import evaluation

    results = {
        SMA: {"model": SMA, "mae": 10.0, "rmse": 11.0, "samples": 8},
        WMA: {"model": WMA, "mae": 9.5, "rmse": 10.0, "samples": 8},
        LINEAR_REGRESSION: {
            "model": LINEAR_REGRESSION,
            "mae": 9.2,
            "rmse": 9.8,
            "samples": 8,
        },
    }

    monkeypatch.setattr(
        evaluation,
        "evaluate_model",
        lambda history, method: results[method],
    )

    result = select_best_model([8, 9, 10, 11, 12, 13, 14, 15])

    assert result["selected_model"] == SMA
    assert "did not improve MAE enough" in result["reason"]
