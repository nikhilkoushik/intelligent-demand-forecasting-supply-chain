
import io
import os
import time
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data/raw/sales_train_validation.csv")

BATCH_SIZE = 50
EXPECTED_SERIES = 30_490
EXPECTED_DAYS = 1_913
PILOT_SERIES = 100

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.environ["DB_PASSWORD"],
}

ID_COLUMNS = [
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
]

COPY_SQL = """
COPY raw.m5_sales_daily
(item_id, dept_id, cat_id, store_id, state_id, d, units_sold)
FROM STDIN WITH (FORMAT CSV)
"""


def main():
    start_time = time.perf_counter()

    if not CSV_PATH.is_file():
        raise FileNotFoundError(CSV_PATH)

    # Check the source file structure.
    header = pd.read_csv(CSV_PATH, nrows=0).columns
    days = [c for c in header if c.startswith("d_")]

    if len(days) != EXPECTED_DAYS:
        raise ValueError("Unexpected number of sales days")

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT current_database()")
            if cur.fetchone()[0] != "demand_forecasting":
                raise RuntimeError("Wrong database!")

            # Record which batches have completed.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS
                monitoring.m5_sales_ingestion_batches (
                    batch_number INTEGER PRIMARY KEY,
                    first_series INTEGER NOT NULL,
                    series_count INTEGER NOT NULL,
                    rows_loaded BIGINT NOT NULL,
                    completed_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            conn.commit()

            cur.execute("""
                SELECT batch_number, first_series,
                       series_count, rows_loaded
                FROM monitoring.m5_sales_ingestion_batches
            """)
            completed = {
                row[0]: row[1:] for row in cur.fetchall()
            }

            cur.execute("SELECT COUNT(*) FROM raw.m5_sales_daily")
            existing_rows = cur.fetchone()[0]

            if not completed:
                # Verify that the existing 100-series pilot
                # really matches the beginning of our CSV.
                pilot = pd.read_csv(
                    CSV_PATH,
                    nrows=PILOT_SERIES,
                    usecols=["store_id", "item_id"],
                )

                expected_keys = set(
                    zip(pilot["store_id"], pilot["item_id"])
                )

                cur.execute("""
                    SELECT store_id, item_id, COUNT(*)
                    FROM raw.m5_sales_daily
                    GROUP BY store_id, item_id
                """)
                actual = {
                    (store, item): count
                    for store, item, count in cur.fetchall()
                }

                if (
                    existing_rows != PILOT_SERIES * EXPECTED_DAYS
                    or len(expected_keys) != PILOT_SERIES
                    or set(actual) != expected_keys
                    or any(n != EXPECTED_DAYS for n in actual.values())
                ):
                    raise RuntimeError(
                        "Pilot data does not match the first "
                        "100 CSV series. Import stopped safely."
                    )

                # Register both completed 50-series pilot batches.
                for batch_number, first_series in [(1, 0), (2, 50)]:
                    cur.execute("""
                        INSERT INTO
                        monitoring.m5_sales_ingestion_batches
                        (batch_number, first_series,
                         series_count, rows_loaded)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        batch_number,
                        first_series,
                        50,
                        50 * EXPECTED_DAYS,
                    ))

                conn.commit()
                completed = {
                    1: (0, 50, 50 * EXPECTED_DAYS),
                    2: (50, 50, 50 * EXPECTED_DAYS),
                }

                print("Existing 100-series pilot verified.")

            # Every completed batch must match its metadata.
            tracked_rows = sum(
                details[2] for details in completed.values()
            )

            if existing_rows != tracked_rows:
                raise RuntimeError(
                    "Database row count does not match "
                    "completed batch records. Stopping safely."
                )

            print("Previously imported rows:", f"{existing_rows:,}")

            reader = pd.read_csv(
                CSV_PATH,
                chunksize=BATCH_SIZE,
            )

            total_series = 0

            for batch_number, sales in enumerate(reader, start=1):
                first_series = total_series
                series_count = len(sales)
                total_series += series_count

                expected_rows = series_count * EXPECTED_DAYS

                if batch_number in completed:
                    expected_metadata = (
                        first_series, series_count, expected_rows
                    )

                    if completed[batch_number] != expected_metadata:
                        raise RuntimeError(
                            f"Batch {batch_number} metadata mismatch"
                        )
                    continue

                # One item-store combination per source row.
                if sales.duplicated(
                    ["store_id", "item_id"]
                ).any():
                    raise ValueError(
                        f"Duplicate series in batch {batch_number}"
                    )

                # Convert daily columns into individual rows.
                long_sales = sales.melt(
                    id_vars=ID_COLUMNS,
                    value_vars=days,
                    var_name="d",
                    value_name="units_sold",
                )

                if long_sales["units_sold"].isna().any():
                    raise ValueError("Missing sales detected")

                if (long_sales["units_sold"] < 0).any():
                    raise ValueError("Negative sales detected")

                if len(long_sales) != expected_rows:
                    raise RuntimeError("Batch row count mismatch")

                buffer = io.StringIO()
                long_sales.to_csv(
                    buffer,
                    index=False,
                    header=False,
                )

                # COPY and progress record share one transaction.
                with cur.copy(COPY_SQL) as copy:
                    copy.write(buffer.getvalue())

                cur.execute("""
                    INSERT INTO
                    monitoring.m5_sales_ingestion_batches
                    (batch_number, first_series,
                     series_count, rows_loaded)
                    VALUES (%s, %s, %s, %s)
                """, (
                    batch_number,
                    first_series,
                    series_count,
                    expected_rows,
                ))

                # Commit only after both operations succeed.
                conn.commit()

                print(
                    f"Batch {batch_number}: "
                    f"{expected_rows:,} rows committed | "
                    f"{total_series:,} series processed",
                    flush=True,
                )

            if total_series != EXPECTED_SERIES:
                raise RuntimeError(
                    f"Expected {EXPECTED_SERIES} series, "
                    f"found {total_series}"
                )

            # Final database validation.
            cur.execute("""
                SELECT COUNT(*)
                FROM raw.m5_sales_daily
            """)
            final_rows = cur.fetchone()[0]

            expected_total = EXPECTED_SERIES * EXPECTED_DAYS

            if final_rows != expected_total:
                raise RuntimeError(
                    f"Expected {expected_total:,}, "
                    f"found {final_rows:,}"
                )

            print("\nFULL IMPORT SUCCESSFUL!")
            print("Total series:", f"{total_series:,}")
            print("Total daily records:", f"{final_rows:,}")
            print(
                "Elapsed seconds:",
                round(time.perf_counter() - start_time, 2)
            )


if __name__ == "__main__":
    main()
