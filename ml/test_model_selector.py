from pathlib import Path

from ml.evaluate_scenarios import load_consumption_history
from ml.forecasting import select_best_model

ML_DIR = Path(__file__).resolve().parent

for file_path in sorted(ML_DIR.glob("*_consumption.csv")):
    history = load_consumption_history(file_path)

    result = select_best_model(history)

    print("\nScenario:", file_path.stem)
    print("Selected:", result["selected_model"])
    print("Reason:", result["reason"])
