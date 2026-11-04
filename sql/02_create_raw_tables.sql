
-- Project 2: M5 Forecasting Database
-- Run against: demand_forecasting

-- 1. Calendar table
CREATE TABLE IF NOT EXISTS raw.m5_calendar (
    d VARCHAR(10) PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    wm_yr_wk INTEGER NOT NULL,
    weekday VARCHAR(15),
    wday SMALLINT,
    month SMALLINT,
    year SMALLINT,
    event_name_1 TEXT,
    event_type_1 TEXT,
    event_name_2 TEXT,
    event_type_2 TEXT,
    snap_ca SMALLINT,
    snap_tx SMALLINT,
    snap_wi SMALLINT
);

-- 2. Weekly selling prices
CREATE TABLE IF NOT EXISTS raw.m5_sell_prices (
    store_id VARCHAR(20) NOT NULL,
    item_id VARCHAR(40) NOT NULL,
    wm_yr_wk INTEGER NOT NULL,
    sell_price NUMERIC(12,4) NOT NULL
        CHECK (sell_price > 0),

    PRIMARY KEY (store_id, item_id, wm_yr_wk)
);

-- 3. Daily product demand
CREATE TABLE IF NOT EXISTS raw.m5_sales_daily (
    item_id VARCHAR(40) NOT NULL,
    dept_id VARCHAR(30) NOT NULL,
    cat_id VARCHAR(30) NOT NULL,
    store_id VARCHAR(20) NOT NULL,
    state_id VARCHAR(5) NOT NULL,
    d VARCHAR(10) NOT NULL,
    units_sold INTEGER NOT NULL
        CHECK (units_sold >= 0),

    PRIMARY KEY (store_id, item_id, d)
);
