-- Monthly trading summary with month-over-month and year-over-year growth.
-- Technique: CTE + LAG() window function.

WITH monthly AS (
    SELECT
        order_month,
        COUNT(*)                    AS orders,
        COUNT(DISTINCT customer_id) AS customers,
        ROUND(SUM(revenue), 2)      AS revenue,
        ROUND(AVG(revenue), 2)      AS avg_order_value
    FROM order_revenue
    GROUP BY order_month
)
SELECT
    order_month,
    orders,
    customers,
    revenue,
    avg_order_value,
    ROUND(100.0 * (revenue - LAG(revenue, 1) OVER w) / LAG(revenue, 1) OVER w, 1)
        AS mom_growth_pct,
    ROUND(100.0 * (revenue - LAG(revenue, 12) OVER w) / LAG(revenue, 12) OVER w, 1)
        AS yoy_growth_pct
FROM monthly
WINDOW w AS (ORDER BY order_month)
ORDER BY order_month;
