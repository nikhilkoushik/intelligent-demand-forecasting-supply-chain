
import os
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("data/raw/sell_prices.csv")
EXPECTED_ROWS = 6_841_121

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.environ["DB_PASSWORD"],
}

def main():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(CSV_PATH)

    start = time.perf_counter()

    with psycopg.connect(**db_config) as conn:
        with conn.cursor() as cur:

            # Protect against connecting to the wrong database.
            cur.execute("SELECT current_database()")
            database = cur.fetchone()[0]

            if database != "demand_forecasting":
                raise RuntimeError("Wrong database connection!")

            # Re-running this script should not duplicate records.
            cur.execute("DELETE FROM raw.m5_sell_prices")

            copy_sql = """
                COPY raw.m5_sell_prices
                (store_id, item_id, wm_yr_wk, sell_price)
                FROM STDIN
                WITH (FORMAT CSV, HEADER TRUE)
            """

            # Stream the CSV instead of loading it all into memory.
            with cur.copy(copy_sql) as copy:
                with CSV_PATH.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        copy.write(chunk)

            # Check the number of imported records.
            cur.execute("""
                SELECT COUNT(*)
                FROM raw.m5_sell_prices
            """)

            count = cur.fetchone()[0]

            if count != EXPECTED_ROWS:
                raise RuntimeError(
                    f"Expected {EXPECTED_ROWS}, found {count}"
                )

            print("Selling-price import successful!")
            print("Records:", f"{count:,}")
            print(
                "Elapsed time:",
                round(time.perf_counter() - start, 2),
                "seconds"
            )

if __name__ == "__main__":
    main()
