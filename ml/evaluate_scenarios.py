"""Evaluate forecasting models on grocery consumption scenarios."""

import csv
from pathlib import Path

from ml.evaluation import compare_models

ML_DIR = Path(__file__).resolve().parent

def load_consumption_history(file_path):
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        # Ignore blank lines before or between CSV records.
        rows = csv.DictReader(line for line in file if line.strip())

        required_columns = {"month", "consumption"}

        if not rows.fieldnames or not required_columns.issubset(rows.fieldnames):
            raise ValueError(f"Invalid CSV headers in {file_path.name}")

        records = [
            {
                "month": int(row["month"]),
                "consumption": float(row["consumption"])
            }
            for row in rows
        ]

    records.sort(key=lambda row: row["month"])

    if not records:
        raise ValueError(f"No consumption records in {file_path.name}")

    history = [row["consumption"] for row in records]

    return history


def evaluate_scenarios():
    files = sorted((ML_DIR / "datasets").glob("*_consumption.csv"))

    for file_path in files:
        print("\n" + "=" * 60)
        print(f"SCENARIO: {file_path.stem.upper()}")
        print("=" * 60)

        history = load_consumption_history(file_path)

        print(f"Historical periods: {len(history)}")

        results = compare_models(history)

        if not results:
            print("Not enough historical data for evaluation.")
            continue

        print("\nModel comparison:")

        for result in results:
            print(
                f"{result['model']:25} "
                f"MAE: {result['mae']:.3f} | "
                f"RMSE: {result['rmse']:.3f} | "
                f"Samples: {result['samples']}"
            )

        print(f"\nBest model: {results[0]['model']}")


if __name__ == "__main__":
    evaluate_scenarios()
