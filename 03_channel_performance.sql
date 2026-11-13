-- Which acquisition channels bring customers who buy, and buy again?
-- Technique: LEFT JOIN so that signups who never ordered are still counted.

WITH per_customer AS (
    SELECT
        c.customer_id,
        c.channel,
        COUNT(r.order_id)        AS orders,
        COALESCE(SUM(r.revenue), 0) AS revenue
    FROM customers c
    LEFT JOIN order_revenue r ON r.customer_id = c.customer_id
    GROUP BY c.customer_id
)
SELECT
    channel,
    COUNT(*)                                                   AS signups,
    SUM(orders > 0)                                            AS buyers,
    ROUND(100.0 * SUM(orders > 0) / COUNT(*), 1)               AS conversion_pct,
    ROUND(100.0 * SUM(orders > 1) / SUM(orders > 0), 1)        AS repeat_buyer_pct,
    ROUND(SUM(revenue) / COUNT(*), 2)                          AS revenue_per_signup,
    ROUND(SUM(revenue), 2)                                     AS revenue
FROM per_customer
GROUP BY channel
ORDER BY revenue_per_signup DESC;
