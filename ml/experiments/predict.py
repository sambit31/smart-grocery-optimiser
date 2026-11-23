
from pathlib import Path
import joblib
import pandas as pd

# Load the trained model
model = joblib.load(Path(__file__).resolve().parents[1] / "models" / "rice_model.pkl")

# Predict consumption for month 11
new_data = pd.DataFrame({"month": [11]})

prediction = model.predict(new_data)

print("Predicted rice consumption:", round(prediction[0], 2), "kg")
