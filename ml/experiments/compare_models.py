import os
from pathlib import Path
import pymysql
import pandas as pd
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# Load the existing ML environment file
env_path = Path(__file__).resolve().parents[2] / "ml.env"
load_dotenv(env_path)

# Database connection
conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)

# Read actual consumption history
query = """
SELECT consumed_at, SUM(quantity) AS consumption
FROM consumption
WHERE household_id = 1 AND item_id = 1
GROUP BY consumed_at
ORDER BY consumed_at
"""

df = pd.read_sql(query, conn)
conn.close()

if len(df) < 4:
    print("Not enough consumption history for reliable ML testing.")
    print("Records found:", len(df))
    print(df.to_string(index=False))
    print("Add more historical data before comparing model accuracy.")
else:
    df["month"] = range(1, len(df) + 1)

    # Keep the last 2 observations for testing
    train = df.iloc[:-2]
    test = df.iloc[-2:]

    model = LinearRegression()
    model.fit(train[["month"]], train["consumption"])

    predictions = model.predict(test[["month"]])

    moving_predictions = []
    for index in test.index:
        previous = df.loc[:index - 1, "consumption"].tail(3)
        moving_predictions.append(previous.mean())

    print("Actual:", test["consumption"].tolist())
    print("Linear Regression:", predictions.round(2).tolist())
    print("Moving Average:", [round(x, 2) for x in moving_predictions])

    print(
        "ML Error:",
        round(mean_absolute_error(test["consumption"], predictions), 2)
    )
    print(
        "Moving Average Error:",
        round(mean_absolute_error(
            test["consumption"], moving_predictions
        ), 2)
    )
