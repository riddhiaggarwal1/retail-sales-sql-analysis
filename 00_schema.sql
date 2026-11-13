-- Schema for the retail database (SQLite).

DROP VIEW  IF EXISTS order_revenue;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    signup_date TEXT NOT NULL,          -- ISO date, YYYY-MM-DD
    city        TEXT NOT NULL,
    channel     TEXT NOT NULL           -- acquisition channel
);

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    list_price   REAL NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('completed', 'cancelled'))
);

CREATE TABLE order_items (
    order_id    INTEGER NOT NULL REFERENCES orders (order_id),
    product_id  INTEGER NOT NULL REFERENCES products (product_id),
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    discount    REAL NOT NULL,          -- 0.10 = 10 % off
    is_returned INTEGER NOT NULL        -- 1 = item was sent back
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_items_order     ON order_items (order_id);

-- One row per completed order with its net revenue
-- (after discounts, excluding returned items).
-- Orders where every item was returned are left out.
CREATE VIEW order_revenue AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    strftime('%Y-%m', o.order_date) AS order_month,
    SUM(i.quantity * i.unit_price * (1 - i.discount)) AS revenue
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
WHERE o.status = 'completed'
  AND i.is_returned = 0
GROUP BY o.order_id;
