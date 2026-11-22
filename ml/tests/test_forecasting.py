
import pytest

from ml.forecasting import (
    SMA,
    WMA,
    LINEAR_REGRESSION,
    simple_moving_average,
    weighted_moving_average,
    linear_regression,
    forecast_candidates,
)
from ml.evaluation import (
    calculate_mae,
    calculate_rmse,
    evaluate_model,
    compare_models,
)


def test_simple_moving_average():
    assert simple_moving_average([7, 8, 9]) == 8


def test_weighted_moving_average():
    assert weighted_moving_average([7, 8, 9]) == pytest.approx(8.333333)


def test_linear_regression():
    assert linear_regression([7, 8, 9, 10]) == pytest.approx(11)


def test_negative_consumption_rejected():
    with pytest.raises(ValueError):
        simple_moving_average([7, -2, 9])


def test_empty_history_rejected():
    with pytest.raises(ValueError):
        simple_moving_average([])


def test_insufficient_history_for_linear_regression():
    with pytest.raises(ValueError):
        linear_regression([7, 8])


def test_forecast_candidates():
    result = forecast_candidates([7, 8, 9])

    assert SMA in result
    assert WMA in result
    assert LINEAR_REGRESSION in result


def test_mae():
    assert calculate_mae([10, 20], [12, 18]) == 2


def test_rmse():
    assert calculate_rmse([10, 20], [12, 18]) == 2


def test_evaluation_uses_chronological_history():
    result = evaluate_model(
        [7, 8, 9, 10, 11, 12],
        LINEAR_REGRESSION,
    )

    assert result is not None
    assert result["samples"] == 3
    assert result["mae"] == pytest.approx(0)


def test_model_comparison():
    results = compare_models(
        [7, 8, 7, 9, 8, 10, 9, 11, 10, 12, 11, 13]
    )

    assert len(results) == 3
    assert results[0]["mae"] <= results[1]["mae"]
    assert results[1]["mae"] <= results[2]["mae"]
