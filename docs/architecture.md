# System Architecture

```mermaid
flowchart TD
    A[Walmart M5 Sales, Calendar, Pricing] --> B[PostgreSQL Raw Data]
    B --> C[Python Feature Engineering]
    C --> D[Poisson LightGBM V3]
    D --> E[Historical Demand Forecasts]
    E --> F[Inventory Planning Engine]
    F --> G[Replenishment Recommendations]
    E --> H[PostgreSQL Forecasting Schema]
    G --> H
    H --> I[Python Agent Tool Functions]
    I --> J[Future Agentic AI Command Center]
```

## Current Implementation
The forecasting and inventory modules are implemented.
The final multi-agent orchestration is future work.

## Operational Data
Inventory and supplier inputs are simulated for demonstration.

## Decision Policy
Periodic-review inventory planning using an assumed demand
uncertainty model and an order-up-to replenishment target.
