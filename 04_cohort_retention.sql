-- Cohort retention: of the customers who first ordered in a given quarter,
-- what share ordered again N quarters later?
-- Technique: chained CTEs, date arithmetic, FIRST_VALUE() window function.

WITH order_quarters AS (
    SELECT DISTINCT
        customer_id,
        CAST(strftime('%Y', order_date) AS INTEGER) * 4
          + (CAST(strftime('%m', order_date) AS INTEGER) - 1) / 3 AS quarter_index,
        strftime('%Y', order_date) || '-Q'
          || ((CAST(strftime('%m', order_date) AS INTEGER) - 1) / 3 + 1) AS quarter_label
    FROM order_revenue
),
with_cohort AS (
    SELECT
        customer_id,
        quarter_index,
        MIN(quarter_index) OVER (PARTITION BY customer_id) AS cohort_index,
        FIRST_VALUE(quarter_label) OVER (
            PARTITION BY customer_id ORDER BY quarter_index
        ) AS cohort
    FROM order_quarters
),
activity AS (
    SELECT
        cohort,
        quarter_index - cohort_index AS quarters_since_first_order,
        COUNT(*)                     AS active_customers
    FROM with_cohort
    GROUP BY cohort, quarters_since_first_order
)
SELECT
    cohort,
    quarters_since_first_order,
    active_customers,
    FIRST_VALUE(active_customers) OVER w AS cohort_size,
    ROUND(100.0 * active_customers / FIRST_VALUE(active_customers) OVER w, 1)
        AS retention_pct
FROM activity
WINDOW w AS (PARTITION BY cohort ORDER BY quarters_since_first_order)
ORDER BY cohort, quarters_since_first_order;
