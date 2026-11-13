-- Sales and return rate by product category.
-- Technique: conditional aggregation + share of total with a window function.

SELECT
    p.category,
    SUM(i.quantity)                                              AS units_sold,
    ROUND(SUM(i.quantity * i.unit_price * (1 - i.discount)), 2)  AS gross_revenue,
    ROUND(100.0 * SUM(i.is_returned * i.quantity) / SUM(i.quantity), 1)
                                                                 AS return_rate_pct,
    ROUND(SUM((1 - i.is_returned) * i.quantity * i.unit_price * (1 - i.discount)), 2)
                                                                 AS net_revenue,
    ROUND(100.0 * SUM((1 - i.is_returned) * i.quantity * i.unit_price * (1 - i.discount))
          / SUM(SUM((1 - i.is_returned) * i.quantity * i.unit_price * (1 - i.discount))) OVER (), 1)
                                                                 AS net_revenue_share_pct
FROM order_items i
JOIN orders   o ON o.order_id   = i.order_id
JOIN products p ON p.product_id = i.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY net_revenue DESC;
