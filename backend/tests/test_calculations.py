"""Pure business-logic tests: prediction, stock adjustment and budget rules."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.services import budget_service
from app.services.prediction_service import (
    average_requirement,
    period_totals,
    predict_item,
    recommended_quantity,
)

D = Decimal
TODAY = date(2026, 10, 16)


# ---- Required examples A, B, C: stock adjustment ----------------------------

def test_example_a_rice_8_minus_3_is_5():
    assert recommended_quantity(D("8"), D("3")) == D("5")


def test_example_b_stock_exceeds_prediction_gives_zero():
    assert recommended_quantity(D("4"), D("6")) == D("0")


def test_example_c_no_stock_buys_full_prediction():
    assert recommended_quantity(D("5"), D("0")) == D("5")


# ---- Average-based prediction ----------------------------------------------

def test_average_of_7_8_9_is_8():
    assert average_requirement([D("7"), D("8"), D("9")]) == D("8")


def test_average_of_no_data_is_none():
    assert average_requirement([]) is None


def test_consumption_aggregates_into_30_day_period_totals():
    records = [
        (TODAY - timedelta(days=2), D("4")),   # period 1
        (TODAY - timedelta(days=10), D("5")),  # period 1  -> 9
        (TODAY - timedelta(days=40), D("8")),  # period 2  -> 8
        (TODAY - timedelta(days=65), D("3")),  # period 3
        (TODAY - timedelta(days=70), D("4")),  # period 3  -> 7
        (TODAY - timedelta(days=200), D("99")),  # outside window, ignored
    ]
    assert period_totals(records, TODAY, 3) == [D("9"), D("8"), D("7")]


def test_periods_before_first_record_are_not_counted():
    records = [(TODAY - timedelta(days=5), D("6"))]
    assert period_totals(records, TODAY, 3) == [D("6")]  # only 1 period, not [6, 0, 0]


def test_gap_after_first_record_counts_as_zero_usage():
    records = [(TODAY - timedelta(days=70), D("6"))]  # only in period 3
    assert period_totals(records, TODAY, 3) == [D("0"), D("0"), D("6")]


def _item(unit="kg", estimate=None):
    return SimpleNamespace(id=1, name="Rice", unit=unit,
                           initial_monthly_estimate=D(estimate) if estimate else None)


def test_predict_item_from_history_and_stock():
    records = [(TODAY - timedelta(days=d), D(q)) for d, q in [(5, "9"), (35, "8"), (65, "7")]]
    result = predict_item(_item(), D("3"), records, TODAY, planning_days=30, history_periods=3)
    assert result["predicted_quantity"] == D("8")
    assert result["recommended_quantity"] == D("5")
    assert result["prediction_source"] == "consumption_history"
    assert result["data_sufficiency"] == "good"


def test_predict_scales_to_planning_period():
    records = [(TODAY - timedelta(days=5), D("30"))]
    result = predict_item(_item(), D("0"), records, TODAY, planning_days=15, history_periods=3)
    assert result["predicted_quantity"] == D("15")
    assert result["data_sufficiency"] == "limited"


def test_fallback_to_labelled_user_estimate():
    result = predict_item(_item(estimate="6"), D("1"), [], TODAY, 30, 3)
    assert result["prediction_source"] == "user_estimate"
    assert result["recommended_quantity"] == D("5")
    assert "estimate" in result["reason"].lower()


def test_no_history_and_no_estimate_recommends_nothing():
    result = predict_item(_item(), D("0"), [], TODAY, 30, 3)
    assert result["prediction_source"] == "no_data"
    assert result["recommended_quantity"] == D("0")


def test_indivisible_units_round_up_to_whole():
    records = [(TODAY - timedelta(days=5), D("2.3"))]
    result = predict_item(_item(unit="packet"), D("0"), records, TODAY, 30, 3)
    assert result["recommended_quantity"] == D("3")


# ---- Budget optimisation -----------------------------------------------------

def _line(name, priority, qty, price, unit="kg"):
    return {"item_name": name, "priority": priority, "recommended_quantity": D(qty),
            "unit_price": D(price), "unit": unit}


def test_within_budget_keeps_quantities():
    lines = [_line("Rice", "Essential", "5", "50"), _line("Chips", "Optional", "2", "20")]
    lines, summary = budget_service.optimise(lines, D("1000"))
    assert summary["budget_status"] == "within_budget"
    assert summary["final_total_cost"] == D("290.00")
    assert all(l["final_quantity"] == l["recommended_quantity"] for l in lines)


def test_example_d_optional_reduced_first_then_total_recalculated():
    lines = [
        _line("Rice", "Essential", "5", "50"),            # 250
        _line("Dal", "Important", "2", "100"),            # 200
        _line("Chips", "Optional", "4", "25", "packet"),  # 100
    ]
    # Total 550, budget 480 -> 70 over. Chips (Optional) reduced by 3 packets (75).
    lines, summary = budget_service.optimise(lines, D("480"))
    by_name = {l["item_name"]: l for l in lines}
    assert by_name["Chips"]["final_quantity"] == D("1")
    assert by_name["Chips"]["plan_status"] == "reduced"
    assert by_name["Dal"]["final_quantity"] == D("2")   # Important untouched
    assert by_name["Rice"]["final_quantity"] == D("5")  # Essential untouched
    assert summary["final_total_cost"] == D("475.00")
    assert summary["budget_status"] == "optimised_to_fit"
    assert summary["shortfall"] == D("0")


def test_important_reduced_only_after_optional_removed():
    lines = [
        _line("Rice", "Essential", "5", "50"),            # 250
        _line("Dal", "Important", "2", "100"),            # 200
        _line("Chips", "Optional", "4", "25", "packet"),  # 100
    ]
    lines, summary = budget_service.optimise(lines, D("300"))
    by_name = {l["item_name"]: l for l in lines}
    assert by_name["Chips"]["final_quantity"] == D("0")
    assert by_name["Chips"]["plan_status"] == "removed"
    assert by_name["Dal"]["final_quantity"] == D("0.5")
    assert by_name["Rice"]["final_quantity"] == D("5")
    assert summary["final_total_cost"] <= D("300")


def test_essentials_alone_exceed_budget_are_kept_and_reported():
    lines = [
        _line("Rice", "Essential", "10", "50"),   # 500
        _line("Oil", "Essential", "2", "150"),    # 300
        _line("Chips", "Optional", "2", "20"),    # 40
    ]
    lines, summary = budget_service.optimise(lines, D("600"))
    by_name = {l["item_name"]: l for l in lines}
    assert by_name["Chips"]["final_quantity"] == D("0")
    # Essentials are never silently cut.
    assert by_name["Rice"]["final_quantity"] == D("10")
    assert by_name["Oil"]["final_quantity"] == D("2")
    assert summary["budget_status"] == "over_budget"
    assert summary["shortfall"] == D("200.00")
    assert summary["unaffordable_items"] == ["Rice"]  # cheaper Oil fits first
    assert any("NOT removed" in line for line in summary["explanation"])


def test_optimisation_is_deterministic():
    make = lambda: [_line("A", "Optional", "3", "40"), _line("B", "Optional", "3", "40"),
                    _line("C", "Essential", "1", "100")]
    first = budget_service.optimise(make(), D("150"))
    second = budget_service.optimise(make(), D("150"))
    assert [l["final_quantity"] for l in first[0]] == [l["final_quantity"] for l in second[0]]
