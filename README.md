# Intelligent Demand Forecasting & Supply Chain Planning Engine

## Overview
An end-to-end supply chain analytics project using Walmart M5
sales data, PostgreSQL, Python, and LightGBM.

The system transforms historical sales into demand forecasts,
evaluates model performance, and generates simulated inventory
replenishment recommendations.

## Technology Stack
- PostgreSQL and SQL
- Python, pandas, NumPy
- LightGBM (Poisson regression)
- SciPy
- SQLAlchemy and psycopg
- Jupyter Notebook

## Data Engineering
- Ingested approximately 58.3 million daily sales records.
- Integrated sales, calendar, and pricing datasets.
- Built a forecasting development sample of 100 products
  from store CA_1.

## Forecasting
Compared seasonal naive, intermittent-demand methods,
and LightGBM forecasting approaches.

Selected Poisson LightGBM V3 as the development baseline.

Four-window pooled development results:
- WAPE: 84.71%
- Forecast bias: -2.95%

Calendar-aware V4 was also evaluated but did not improve
overall WAPE across the four development windows.

These are historical development results, not guaranteed
future production performance.

## Inventory Planning
Implemented an illustrative periodic-review inventory policy:
- Lead-time demand
- Safety stock
- Reorder points
- Order-up-to inventory levels
- Recommended order quantities
- Inventory risk classification

Inventory balances, supplier lead times, and demand uncertainty
assumptions are simulated, not actual Walmart operational records.

## PostgreSQL Outputs
- forecasting.demand_forecasts
- forecasting.inventory_recommendations

## Agent-Ready Functions
Located in src/forecasting/agent_tools.py:

- get_demand_forecast(store_id, item_id)
- get_inventory_recommendation(store_id, item_id)
- get_high_risk_products(store_id)

These functions retrieve historical forecasts and simulated
planning results. They do not place orders or produce live forecasts.

## Current Limitations
- High SKU-level forecast error remains.
- Model evaluation was used for development and selection.
- Inventory and supplier parameters are hypothetical.
- Safety-stock assumptions are not service-level calibrated.
- Forecast records are historical, not live predictions.
- Future integration can expose these functions as AI agent tools.

## Future Architecture
This module will eventually integrate with:
1. Supply Chain SQL Forensics
2. Inventory Digital Twin and S&OP Optimization
3. Real-Time Logistics Monitoring
4. Agentic AI Supply Chain Command Center

## Data Source
Walmart M5 Forecasting dataset.
