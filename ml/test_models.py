
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# Sample data for testing only
data = {
    "month": list(range(1, 13)),
    "consumption": [7, 8, 7, 9, 8, 10, 9, 11, 10, 12, 11, 13]
}

df = pd.DataFrame(data)

# First 10 months for training
train = df.iloc[:10]

# Last 2 months for testing
test = df.iloc[10:]

# Train Linear Regression
model = LinearRegression()
model.fit(train[["month"]], train["consumption"])

# Predict the last 2 months
predictions = model.predict(test[["month"]])

# Moving Average using the previous 3 months
moving_predictions = []

for index in test.index:
    previous = df.loc[:index - 1, "consumption"].tail(3)
    moving_predictions.append(previous.mean())

# Display results
print("Actual:", test["consumption"].tolist())
print("Linear Regression:", predictions.round(2).tolist())
print("Moving Average:", [round(x, 2) for x in moving_predictions])

# Compare prediction errors
ml_error = mean_absolute_error(test["consumption"], predictions)
ma_error = mean_absolute_error(test["consumption"], moving_predictions)

print("Linear Regression MAE:", round(ml_error, 2))
print("Moving Average MAE:", round(ma_error, 2))
