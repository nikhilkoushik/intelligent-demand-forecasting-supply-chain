
import os
from pathlib import Path

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
SAMPLE_SERIES = 100

OUTPUT_PATH = Path(
    "data/processed/ca1_100_series_daily.parquet"
)


def main():
    # Select a reproducible group of product IDs.
    sql = """
        WITH selected_items AS (
            SELECT DISTINCT item_id
            FROM raw.m5_sales_daily
            WHERE store_id = %s
            ORDER BY item_id
            LIMIT %s
        )
        SELECT
            s.store_id,
            s.item_id,
            s.dept_id,
            s.cat_id,
            c.date,
            CAST(SUBSTRING(s.d FROM 3) AS INTEGER)
                AS day_number,
            s.units_sold,
            c.wday,
            c.month,
            c.year,
            c.event_type_1,
            c.snap_ca,
            p.sell_price
        FROM raw.m5_sales_daily AS s
        JOIN selected_items AS i
            ON s.item_id = i.item_id
        JOIN raw.m5_calendar AS c
            ON s.d = c.d
        LEFT JOIN raw.m5_sell_prices AS p
            ON s.store_id = p.store_id
           AND s.item_id = p.item_id
           AND c.wm_yr_wk = p.wm_yr_wk
        WHERE s.store_id = %s
        ORDER BY s.item_id, day_number
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            if cur.fetchone()[0] != "demand_forecasting":
                raise RuntimeError("Wrong database!")

            cur.execute(
                sql,
                (STORE, SAMPLE_SERIES, STORE)
            )
            rows = cur.fetchall()
            column_names = [
                description.name
                for description in cur.description
            ]

    df = pd.DataFrame(rows, columns=column_names)

    expected_rows = SAMPLE_SERIES * 1913

    if len(df) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows:,} rows, "
            f"found {len(df):,}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(OUTPUT_PATH, index=False)

    print("Dataset extraction successful!")
    print("Store:", STORE)
    print("Product series:", df["item_id"].nunique())
    print("Daily records:", f"{len(df):,}")
    print("Missing prices:", df["sell_price"].isna().sum())
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
