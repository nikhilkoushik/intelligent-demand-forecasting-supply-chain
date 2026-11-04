
import os

import psycopg
from dotenv import load_dotenv

# Load configuration from the project root's .env file.
load_dotenv()

# Read database connection settings.
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.environ["DB_PASSWORD"],
    "connect_timeout": 10,
}

# Open the database connection.
with psycopg.connect(**db_config) as conn:

    # Create a cursor to execute SQL.
    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                current_database(),
                current_user,
                version();
        """)

        database, user, version = cur.fetchone()

        print("Connection successful!")
        print("Database:", database)
        print("Connected user:", user)
        print("PostgreSQL:", version.split(",")[0])

        # Ensure we are using the intended database.
        if database != "demand_forecasting":
            raise RuntimeError(
                "Connected to the wrong database!"
            )
