
import os
import csv
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# STEP 1: Load database configuration
load_dotenv()

# STEP 2: Locate our source file
csv_path = Path("data/raw/calendar.csv")

# STEP 3: Configure PostgreSQL connection
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.environ["DB_PASSWORD"],
}

# STEP 4: Define the columns in CSV order
columns = [
    "date",
    "wm_yr_wk",
    "weekday",
    "wday",
    "month",
    "year",
    "d",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "snap_ca",
    "snap_tx",
    "snap_wi",
]

column_names = ", ".join(columns)

# STEP 5: Connect and import with PostgreSQL COPY
with psycopg.connect(**db_config) as conn:
    with conn.cursor() as cur:

        # Ensure the script is connected to Project 2.
        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()[0]

        if db_name != "demand_forecasting":
            raise RuntimeError("Wrong database connection!")

        # Make the load repeatable.
        # Do not use TRUNCATE CASCADE on production data.
        cur.execute("DELETE FROM raw.m5_calendar")

        copy_sql = f"""
            COPY raw.m5_calendar ({column_names})
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE, NULL '')
        """

        with cur.copy(copy_sql) as copy:
            with csv_path.open("r", encoding="utf-8") as source:
                while chunk := source.read(1024 * 1024):
                    copy.write(chunk)

        # Verify the loaded data.
        cur.execute("""
            SELECT
                COUNT(*),
                MIN(date),
                MAX(date)
            FROM raw.m5_calendar
        """)

        count, first_date, last_date = cur.fetchone()

        if count != 1969:
            raise RuntimeError(
                f"Expected 1969 calendar rows, found {count}"
            )

        print("Calendar import successful!")
        print("Total records:", count)
        print("First date:", first_date)
        print("Last date:", last_date)
