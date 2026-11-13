-- RFM segmentation: score every buyer on Recency, Frequency and Monetary value,
-- then group them into segments a marketing team could act on.
-- Technique: NTILE() window function + CASE.
-- "Today" is taken as the day after the last order in the data.

WITH rfm AS (
    SELECT
        customer_id,
        CAST(julianday((SELECT DATE(MAX(order_date), '+1 day') FROM order_revenue))
             - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
        COUNT(*)     AS frequency,
        SUM(revenue) AS monetary
    FROM order_revenue
    GROUP BY customer_id
),
scored AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,  -- 4 = most recent
        NTILE(4) OVER (ORDER BY monetary)          AS m_score   -- 4 = highest spend
    FROM rfm
),
segmented AS (
    SELECT
        *,
        CASE
            WHEN r_score >= 3 AND frequency >= 3 THEN 'Loyal'
            WHEN r_score >= 3 AND frequency = 2  THEN 'Promising'
            WHEN r_score >= 3                    THEN 'New / one-time'
            WHEN frequency >= 2 AND m_score >= 3 THEN 'At risk (was valuable)'
            ELSE 'Lapsed'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*)                                                   AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)         AS customer_share_pct,
    ROUND(AVG(recency_days))                                   AS avg_recency_days,
    ROUND(AVG(frequency), 2)                                   AS avg_orders,
    ROUND(AVG(monetary), 2)                                    AS avg_revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS revenue_share_pct
FROM segmented
GROUP BY segment
ORDER BY revenue_share_pct DESC;
