
-- M5 price coverage validation
-- Uses product-store series and calendar weeks
-- rather than joining every individual sales record.

WITH store_items AS (
    SELECT DISTINCT store_id, item_id
    FROM raw.m5_sell_prices
),
calendar_weeks AS (
    SELECT
        wm_yr_wk,
        COUNT(*) AS days_in_week
    FROM raw.m5_calendar
    WHERE CAST(SUBSTRING(d FROM 3) AS INTEGER) <= 1913
    GROUP BY wm_yr_wk
),
first_prices AS (
    SELECT
        store_id,
        item_id,
        MIN(wm_yr_wk) AS first_week
    FROM raw.m5_sell_prices
    GROUP BY store_id, item_id
)
SELECT
    i.store_id,

    COALESCE(SUM(w.days_in_week), 0)
        AS total_sales_records,

    COALESCE(SUM(w.days_in_week)
        FILTER (WHERE p.item_id IS NOT NULL), 0)
        AS records_with_price,

    COALESCE(SUM(w.days_in_week)
        FILTER (WHERE p.item_id IS NULL), 0)
        AS records_without_price,

    COALESCE(SUM(w.days_in_week)
        FILTER (
            WHERE p.item_id IS NULL
              AND w.wm_yr_wk < f.first_week
        ), 0) AS before_first_price,

    COALESCE(SUM(w.days_in_week)
        FILTER (
            WHERE p.item_id IS NULL
              AND w.wm_yr_wk >= f.first_week
        ), 0) AS after_first_price

FROM store_items AS i
CROSS JOIN calendar_weeks AS w

LEFT JOIN first_prices AS f
    ON i.store_id = f.store_id
   AND i.item_id = f.item_id

LEFT JOIN raw.m5_sell_prices AS p
    ON i.store_id = p.store_id
   AND i.item_id = p.item_id
   AND w.wm_yr_wk = p.wm_yr_wk

GROUP BY i.store_id
ORDER BY i.store_id;
