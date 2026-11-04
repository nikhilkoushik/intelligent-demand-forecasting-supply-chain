
import os

import numpy as np
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.environ["DB_PASSWORD"],
}

STORE = "CA_1"
TRAIN_END = 1857
VALIDATION_END = 1885
HORIZON = 28


def main():

    # STEP 1: Read daily store sales from PostgreSQL.
    sql = """
        SELECT
            CAST(SUBSTRING(s.d FROM 3) AS INTEGER)
                AS day_number,
            c.date,
            SUM(s.units_sold) AS total_units

        FROM raw.m5_sales_daily AS s

        JOIN raw.m5_calendar AS c
            ON s.d = c.d

        WHERE s.store_id = %s
          AND CAST(SUBSTRING(s.d FROM 3) AS INTEGER)
              <= %s

        GROUP BY s.d, c.date
        ORDER BY day_number
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database()"
            )

            if cur.fetchone()[0] != "demand_forecasting":
                raise RuntimeError("Wrong database!")

            cur.execute(sql, (STORE, VALIDATION_END))
            rows = cur.fetchall()

    df = pd.DataFrame(
        rows,
        columns=["day_number", "date", "total_units"]
    )

    # STEP 2: Verify uninterrupted daily history.
    expected_days = list(range(1, VALIDATION_END + 1))

    if df["day_number"].tolist() != expected_days:
        raise RuntimeError(
            "Missing, duplicate, or unordered dates!"
        )

    # STEP 3: Create chronological train/validation sets.
    train = df[df["day_number"] <= TRAIN_END]
    validation = df[
        (df["day_number"] > TRAIN_END)
        & (df["day_number"] <= VALIDATION_END)
    ]

    if len(validation) != HORIZON:
        raise RuntimeError(
            "Validation period must contain 28 days."
        )

    # STEP 4: Take the last observed 7 days of training.
    last_week = (
        train["total_units"]
        .tail(7)
        .to_numpy(dtype=float)
    )

    # STEP 5: Repeat that weekly pattern for 28 days.
    predictions = np.tile(last_week, 4)

    actual = validation["total_units"].to_numpy(
        dtype=float
    )

    # STEP 6: Evaluate accuracy.
    absolute_errors = np.abs(actual - predictions)

    wape = (
        100 * absolute_errors.sum() / actual.sum()
        if actual.sum() > 0
        else float("nan")
    )

    bias = (
        100 * (predictions - actual).sum() / actual.sum()
        if actual.sum() > 0
        else float("nan")
    )

    result = validation[
        ["date", "day_number", "total_units"]
    ].copy()

    result["predicted_units"] = predictions
    result["absolute_error"] = absolute_errors

    print("\n=== SEASONAL NAIVE BASELINE ===")
    print("Store:", STORE)
    print("Training days:", len(train))
    print("Validation days:", len(validation))
    print("Forecast horizon:", HORIZON)

    print("\nFirst seven forecasted days:")
    print(result.head(7).to_string(index=False))

    print("\nValidation WAPE:", round(wape, 2), "%")
    print("Validation bias:", round(bias, 2), "%")

    # Save baseline forecasts for future model comparison.
    from pathlib import Path

    output_dir = Path("artifacts/baselines")
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = (
        output_dir / "ca1_seasonal_naive_validation.csv"
    )

    result.to_csv(predictions_path, index=False)

    # Save metrics with the experiment settings.
    metrics_path = (
        output_dir / "ca1_seasonal_naive_metrics.csv"
    )

    metrics = pd.DataFrame([{
        "model": "seasonal_naive_7day",
        "store_id": STORE,
        "train_end_day": TRAIN_END,
        "validation_end_day": VALIDATION_END,
        "horizon_days": HORIZON,
        "wape_pct": round(wape, 4),
        "bias_pct": round(bias, 4),
    }])

    metrics.to_csv(metrics_path, index=False)

    print("\nSaved prediction file:", predictions_path)
    print("Saved metrics file:", metrics_path)


if __name__ == "__main__":
    main()
