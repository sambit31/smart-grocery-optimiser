
"""Evaluate forecasting models using synthetic 12-month grocery histories.

This script does not connect to or modify the database.
It evaluates SMA, WMA and Linear Regression using chronological validation.
"""

import csv
from pathlib import Path

from ml.forecasting import select_best_model
from ml.evaluation import compare_models


OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_FILE = OUTPUT_DIR / "synthetic_ml_evaluation.csv"


# Synthetic monthly consumption: oldest month to newest month.
# These are test values, NOT real customer consumption.
SYNTHETIC_DATA = {
    "Banana": [20, 22, 24, 25, 27, 29, 31, 33, 35, 37, 39, 41],
    "Milk": [18, 20, 19, 22, 21, 24, 23, 25, 26, 24, 27, 28],
    "Rice": [8, 7, 9, 8, 10, 9, 11, 10, 12, 11, 13, 12],
    "Potato": [5, 7, 6, 8, 7, 9, 8, 10, 9, 11, 10, 12],
    "Onion": [10, 12, 9, 11, 13, 10, 12, 14, 11, 13, 15, 12],
    "Cooking Oil": [2, 2.2, 2.4, 2.5, 2.7, 2.9, 3, 3.2, 3.4, 3.5, 3.7, 3.9],
    "Biscuits": [5, 5, 6, 5, 7, 6, 7, 7, 8, 7, 9, 8],
    "Dishwash Liquid": [300, 320, 310, 340, 330, 360, 350, 380, 370, 400, 390, 420],
}


def evaluate_synthetic():
    report_rows = []
    all_metrics = {
        "simple_moving_average": [],
        "weighted_moving_average": [],
        "linear_regression": [],
    }

    print("\n========== SYNTHETIC ML EVALUATION ==========\n")

    for item_name, history in SYNTHETIC_DATA.items():

        # Select the best model using the production selection logic.
        selection = select_best_model(history)

        # Compare all models using chronological validation.
        comparisons = compare_models(history)

        metrics = {
            result["model"]: result
            for result in comparisons
        }

        row = {
            "item_name": item_name,
            "historical_periods": len(history),
            "historical_consumption": " | ".join(
                str(value) for value in history
            ),
            "selected_model": selection["selected_model"],
            "selection_reason": selection["reason"],
        }

        for model_name in all_metrics:
            result = metrics.get(model_name)

            if result and result.get("mae") is not None:
                mae = float(result["mae"])
                rmse = float(result["rmse"])

                row[f"{model_name}_mae"] = round(mae, 4)
                row[f"{model_name}_rmse"] = round(rmse, 4)

                all_metrics[model_name].append({
                    "mae": mae,
                    "rmse": rmse,
                })
            else:
                row[f"{model_name}_mae"] = "N/A"
                row[f"{model_name}_rmse"] = "N/A"

        report_rows.append(row)

        print(
            f"{item_name:20} | "
            f"Selected: {selection['selected_model']}"
        )

    # Export item-wise results.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if report_rows:
        with OUTPUT_FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=report_rows[0].keys(),
            )
            writer.writeheader()
            writer.writerows(report_rows)

    # Display average validation errors across all synthetic items.
    print("\n========== OVERALL MODEL COMPARISON ==========")
    print(f"{'Model':30} {'Average MAE':15} {'Average RMSE':15}")

    for model_name, results in all_metrics.items():
        if results:
            avg_mae = sum(r["mae"] for r in results) / len(results)
            avg_rmse = sum(r["rmse"] for r in results) / len(results)

            print(
                f"{model_name:30} "
                f"{avg_mae:<15.4f} "
                f"{avg_rmse:<15.4f}"
            )
        else:
            print(f"{model_name:30} No validation results")

    print("\nEvaluation completed.")
    print(f"Items evaluated: {len(report_rows)}")
    print(f"CSV report: {OUTPUT_FILE}")
    print("\nNOTE: These results use synthetic data, not real-world data.")


if __name__ == "__main__":
    evaluate_synthetic()
