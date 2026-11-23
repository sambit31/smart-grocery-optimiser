
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import joblib

# Sample monthly rice consumption data
data = {
    "month": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "consumption": [7, 8, 7, 9, 8, 10, 9, 11, 10, 12]
}

df = pd.DataFrame(data)

# Input (month) and output (consumption)
X = df[["month"]]
y = df["consumption"]

# Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train the ML model
model = LinearRegression()
model.fit(X_train, y_train)

# Test the model
predictions = model.predict(X_test)
error = mean_absolute_error(y_test, predictions)

print("Actual consumption:", list(y_test))
print("Predicted consumption:", predictions.round(2))
print("Mean Absolute Error:", round(error, 2))

# Save the trained model
joblib.dump(model, Path(__file__).resolve().parents[1] / "models" / "rice_model.pkl")

print("Model saved successfully!")
