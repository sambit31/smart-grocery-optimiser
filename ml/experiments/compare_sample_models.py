
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# Load sample data
df = pd.read_csv(Path(__file__).resolve().parents[1] / "datasets" / "sample_consumption.csv")

# Test each model on multiple prediction periods
results = []

for test_start in range(8, len(df)):
    train = df.iloc[:test_start]
    test = df.iloc[test_start:test_start + 1]

    # Model 1: Linear Regression
    model = LinearRegression()
    model.fit(train[["month"]], train["consumption"])

    linear_prediction = model.predict(test[["month"]])[0]

    # Model 2: Moving Average (previous 3 months)
    previous = train["consumption"].tail(3)
    moving_prediction = previous.mean()

    actual = test["consumption"].iloc[0]

    results.append({
        "Month": int(test["month"].iloc[0]),
        "Actual": actual,
        "Linear Regression": round(linear_prediction, 2),
        "Moving Average": round(moving_prediction, 2),
        "Linear Error": abs(actual - linear_prediction),
        "Moving Error": abs(actual - moving_prediction)
    })

# Display each prediction
result_df = pd.DataFrame(results)

print("\nPREDICTION RESULTS")
print(result_df.round(2).to_string(index=False))

# Calculate overall errors
linear_mae = mean_absolute_error(
    result_df["Actual"], result_df["Linear Regression"]
)

moving_mae = mean_absolute_error(
    result_df["Actual"], result_df["Moving Average"]
)

print("\nMODEL COMPARISON")
print("Number of test periods:", len(result_df))
print("Linear Regression MAE:", round(linear_mae, 2))
print("Moving Average MAE:", round(moving_mae, 2))

if linear_mae < moving_mae:
    print("Better model on this sample: Linear Regression")
elif moving_mae < linear_mae:
    print("Better model on this sample: Moving Average")
else:
    print("Both models have equal MAE on this sample")
