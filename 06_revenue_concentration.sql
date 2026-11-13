-- How concentrated is revenue? Split buyers into ten equal groups by spend
-- and show each group's share of total revenue (a Pareto analysis).
-- Technique: NTILE() + running total with SUM() OVER.

WITH customer_revenue AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM order_revenue
    GROUP BY customer_id
),
deciles AS (
    SELECT
        NTILE(10) OVER (ORDER BY revenue DESC) AS decile,   -- 1 = top 10 % of buyers
        revenue
    FROM customer_revenue
)
SELECT
    decile,
    COUNT(*)                                                    AS customers,
    ROUND(SUM(revenue), 2)                                      AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1)  AS revenue_share_pct,
    ROUND(100.0 * SUM(SUM(revenue)) OVER (ORDER BY decile)
          / SUM(SUM(revenue)) OVER (), 1)                       AS cumulative_share_pct
FROM deciles
GROUP BY decile
ORDER BY decile;
