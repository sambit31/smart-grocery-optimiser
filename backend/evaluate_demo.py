
"""Evaluate grocery forecasting models using the demo household data.

This script only reads existing database records.
It does not modify inventory, recommendations, or consumption history.
"""

import csv
from datetime import date
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import User, GroceryItem
from app.services import prediction_service
from app.services.inventory_service import current_stock

from ml.forecasting import select_best_model
from ml.evaluation import compare_models


DEMO_EMAIL = "demo@grocery.local"

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_FILE = OUTPUT_DIR / "demo_ml_evaluation.csv"


def format_history(values):
    """Format historical monthly consumption for the CSV report."""
    return " | ".join(f"{float(value):.3f}" for value in values)


def evaluate_demo():
    app = create_app()

    with app.app_context():
        # Find only the demonstration user's household.
        user = User.query.filter_by(email=DEMO_EMAIL).first()

        if not user or not user.household:
            print("Demo account or household not found.")
            print("Run the seed-demo command first.")
            return

        household = user.household
        reference_date = date.today()

        history_periods = app.config["PREDICTION_HISTORY_PERIODS"]
        planning_days = household.planning_period_days

        items = (
            GroceryItem.query
            .filter_by(household_id=household.id, is_archived=False)
            .order_by(GroceryItem.name)
            .all()
        )

        report_rows = []

        for item in items:
            records = prediction_service.load_consumption_records(
                household.id,
                item.id,
                reference_date,
                history_periods,
            )

            stock = current_stock(household.id, item.id)

            # Use the actual production prediction logic.
            prediction = prediction_service.predict_item(
                item,
                stock,
                records,
                reference_date,
                planning_days,
                history_periods,
            )

            # Convert monthly totals into oldest-to-newest order.
            totals = prediction_service.period_totals(
                records,
                reference_date,
                history_periods,
            )

            history = [float(value) for value in reversed(totals)]

            # Select the model using the same selection logic as production.
            if history:
                selection = select_best_model(history)
                selected_model = selection["selected_model"]
                selection_reason = selection["reason"]

                # Evaluate all candidate models using chronological validation.
                comparisons = compare_models(history)
            else:
                selected_model = "not_applicable"
                selection_reason = prediction["reason"]
                comparisons = []

            # Store comparison metrics by model name.
            metrics = {
                result["model"]: result
                for result in comparisons
            }

            def metric_value(model_name, metric_name):
                result = metrics.get(model_name)

                if result is None:
                    return "N/A"

                value = result.get(metric_name)

                return round(float(value), 4) if value is not None else "N/A"

            row = {
                "item_name": item.name,
                "unit": item.unit,
                "prediction_source": prediction["prediction_source"],
                "selected_model": selected_model,
                "selection_reason": selection_reason,
                "periods_used": prediction["periods_used"],
                "historical_consumption": format_history(history),
                "predicted_consumption": float(prediction["predicted_quantity"]),
                "current_stock": float(prediction["stock_quantity"]),
                "recommended_purchase_quantity": float(
                    prediction["recommended_quantity"]
                ),
                "data_sufficiency": prediction["data_sufficiency"],

                "sma_mae": metric_value("simple_moving_average", "mae"),
                "sma_rmse": metric_value("simple_moving_average", "rmse"),

                "wma_mae": metric_value("weighted_moving_average", "mae"),
                "wma_rmse": metric_value("weighted_moving_average", "rmse"),

                "lr_mae": metric_value("linear_regression", "mae"),
                "lr_rmse": metric_value("linear_regression", "rmse"),
            }

            report_rows.append(row)

            print(
                f"{item.name:25} | "
                f"Model: {selected_model:25} | "
                f"Forecast: {row['predicted_consumption']:10.3f} "
                f"{item.unit} | "
                f"Stock: {row['current_stock']:10.3f} | "
                f"Buy: {row['recommended_purchase_quantity']:10.3f}"
            )

        # Export report.
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

        print("\nEvaluation completed.")
        print(f"Items evaluated: {len(report_rows)}")
        print(f"CSV report: {OUTPUT_FILE}")


if __name__ == "__main__":
    evaluate_demo()
