
import os
import io
import time
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data/raw/sales_train_validation.csv")

# Import only 100 product-store series for our pilot.
PILOT_SERIES = 100
BATCH_SIZE = 25
DAYS_PER_SERIES = 1913

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
    (item_id, dept_id, cat_id, store_id,
     state_id, d, units_sold)
    FROM STDIN
    WITH (FORMAT CSV)
"""


def main():
    start = time.perf_counter()
    total_rows = 0

    if not CSV_PATH.is_file():
        raise FileNotFoundError(CSV_PATH)

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            # Confirm the correct database.
            cur.execute("SELECT current_database()")
            if cur.fetchone()[0] != "demand_forecasting":
                raise RuntimeError("Wrong database!")

            # Prevent accidental duplicate pilot imports.
            cur.execute("SELECT COUNT(*) FROM raw.m5_sales_daily")
            if cur.fetchone()[0] != 0:
                raise RuntimeError(
                    "Sales table already contains data. "
                    "Stop and inspect before importing."
                )

            # Read 25 product-store series at a time.
            reader = pd.read_csv(
                CSV_PATH,
                nrows=PILOT_SERIES,
                chunksize=BATCH_SIZE,
            )

            for batch_number, sales in enumerate(reader, start=1):

                day_columns = [
                    col for col in sales.columns
                    if col.startswith("d_")
                ]

                # Wide format -> long format.
                sales_long = sales.melt(
                    id_vars=ID_COLUMNS,
                    value_vars=day_columns,
                    var_name="d",
                    value_name="units_sold",
                )

                # Validate before importing.
                if sales_long["units_sold"].isna().any():
                    raise ValueError("Missing sales detected!")

                if (sales_long["units_sold"] < 0).any():
                    raise ValueError("Negative sales detected!")

                # Convert this batch into CSV text.
                buffer = io.StringIO()
                sales_long.to_csv(
                    buffer,
                    index=False,
                    header=False,
                )

                # Transfer the batch to PostgreSQL.
                with cur.copy(COPY_SQL) as copy:
                    copy.write(buffer.getvalue())

                total_rows += len(sales_long)

                print(
                    f"Batch {batch_number}: "
                    f"{len(sales_long):,} rows imported"
                )

            # Verify the total before committing.
            expected = PILOT_SERIES * DAYS_PER_SERIES

            cur.execute("SELECT COUNT(*) FROM raw.m5_sales_daily")
            actual = cur.fetchone()[0]

            if actual != expected:
                raise RuntimeError(
                    f"Expected {expected:,}, found {actual:,}"
                )

    # The transaction commits when the connection closes normally.
    print("\nPilot import successful!")
    print("Total records:", f"{total_rows:,}")
    print(
        "Elapsed time:",
        round(time.perf_counter() - start, 2),
        "seconds"
    )


if __name__ == "__main__":
    main()
