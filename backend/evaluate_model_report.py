
"""Generate a normalized model comparison report."""

import csv
from pathlib import Path

from ml.evaluation import compare_models


OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
INPUT_FILE = OUTPUT_DIR / "synthetic_ml_evaluation.csv"
OUTPUT_FILE = OUTPUT_DIR / "final_model_comparison.csv"

MODELS = {
    "SMA": "simple_moving_average",
    "WMA": "weighted_moving_average",
    "Linear Regression": "linear_regression",
}


def run_report():
    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        source_rows = list(csv.DictReader(file))

    report_rows = []
    wins = {name: 0 for name in MODELS}

    for row in source_rows:
        item = row["item_name"]

        history = [
            float(value)
            for value in row["historical_consumption"].split(" | ")
        ]

        comparisons = compare_models(history)
        metrics = {result["model"]: result for result in comparisons}

        average_consumption = sum(history) / len(history)

        sma = metrics.get("simple_moving_average")
        sma_mae = float(sma["mae"]) if sma and sma["mae"] is not None else None

        valid_models = []

        for display_name, model_key in MODELS.items():
            result = metrics.get(model_key)

            if result and result.get("mae") is not None:
                valid_models.append((display_name, float(result["mae"])))

        if not valid_models:
            continue

        best_model, best_mae = min(valid_models, key=lambda x: x[1])
        wins[best_model] += 1

        output = {
            "item_name": item,
            "selected_model": row["selected_model"],
            "best_model_by_mae": best_model,
            "average_consumption": round(average_consumption, 4),
            "best_model_mae": round(best_mae, 4),
            "best_model_normalized_mae_percent": round(
                (best_mae / average_consumption) * 100, 2
            ) if average_consumption else "N/A",
            "improvement_over_sma_percent": round(
                ((sma_mae - best_mae) / sma_mae) * 100, 2
            ) if sma_mae and sma_mae > 0 else "N/A",
        }

        for display_name, model_key in MODELS.items():
            result = metrics.get(model_key)

            output[f"{model_key}_mae"] = (
                round(float(result["mae"]), 4)
                if result and result.get("mae") is not None
                else "N/A"
            )

        report_rows.append(output)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if report_rows:
        with OUTPUT_FILE.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=report_rows[0].keys(),
            )
            writer.writeheader()
            writer.writerows(report_rows)

    print("\n========== MODEL WIN COUNTS ==========")

    for model, count in wins.items():
        print(f"{model:20}: {count}")

    print("\n========== ITEM-WISE COMPARISON ==========")

    for row in report_rows:
        print(
            f"{row['item_name']:20} | "
            f"Best: {row['best_model_by_mae']:20} | "
            f"Normalized MAE: "
            f"{row['best_model_normalized_mae_percent']}%"
        )

    print("\nReport generated:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    run_report()
