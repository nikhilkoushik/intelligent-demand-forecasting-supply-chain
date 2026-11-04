
# src/forecasting/agent_tools.py

import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def get_engine():
    """Connect to the supply chain forecasting database."""

    url = URL.create(
        "postgresql+psycopg",
        username=os.getenv("PGUSER", "nikhilkoushik"),
        password=os.getenv("PGPASSWORD") or None,
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database="demand_forecasting",
    )

    return create_engine(url)


def get_demand_forecast(store_id: str, item_id: str):
    """
    Return historical 28-day forecast records
    for a selected product and store.
    """

    query = text("""
        SELECT
            forecast_date,
            predicted_units,
            actual_units
        FROM forecasting.demand_forecasts
        WHERE store_id = :store_id
          AND item_id = :item_id
        ORDER BY forecast_date
    """)

    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {
                "store_id": store_id,
                "item_id": item_id
            }
        ).mappings().all()

    engine.dispose()

    return [
        {
            "forecast_date": str(row["forecast_date"]),
            "predicted_units": float(row["predicted_units"]),
            "actual_units": row["actual_units"]
        }
        for row in rows
    ]


def get_inventory_recommendation(
    store_id: str,
    item_id: str
):
    """Return the simulated inventory planning result."""

    query = text("""
        SELECT *
        FROM forecasting.inventory_recommendations
        WHERE store_id = :store_id
          AND item_id = :item_id
    """)

    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {
                "store_id": store_id,
                "item_id": item_id
            }
        ).mappings().first()

    engine.dispose()

    return dict(row) if row else None


def get_high_risk_products(store_id: str):
    """Return products with high simulated inventory risk."""

    query = text("""
        SELECT
            item_id,
            inventory_on_hand,
            lead_time_days,
            reorder_point,
            recommended_order_qty,
            risk_status
        FROM forecasting.inventory_recommendations
        WHERE store_id = :store_id
          AND risk_status = 'HIGH'
        ORDER BY recommended_order_qty DESC
    """)

    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {"store_id": store_id}
        ).mappings().all()

    engine.dispose()

    return [dict(row) for row in rows]
