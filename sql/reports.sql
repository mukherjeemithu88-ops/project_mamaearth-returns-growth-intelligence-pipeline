-- Mamaearth Returns & Growth Intelligence Pipeline
-- Part 1 — SQL Relational Layer & Reporting
-- Task 3 — Reports

-- Task 3(a) — Order totals
-- SQLite output:
-- total_orders | total_revenue | avg_order_value
-- 180          | 99860.2       | 554.78

SELECT
    COUNT(*) AS total_orders,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_revenue,
    ROUND(
        AVG(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS avg_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;



-- Task 3(b) — COUNT(*) vs COUNT(rating)
-- SQLite output:
-- total_orders | rated_orders | unrated_orders
-- 180          | 165          | 15

SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;




-- Task 3(c) — Customer with zero orders
-- Query 1: LEFT JOIN output
-- customer_id | name   | order_count
-- C045        | Vihaan | 0

SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.name
HAVING COUNT(o.order_id) = 0;


-- Query 2: NOT IN output
-- customer_id | name
-- C045        | Vihaan

SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
);



-- Task 3(d) — City-wise return rate
-- SQLite output:
-- city      | total_orders | returned_orders | return_rate_pct
-- Jaipur    | 19           | 8               | 42.1
-- Lucknow   | 49           | 15              | 30.6
-- Bangalore | 33           | 8               | 24.2

SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(
        100.0 * SUM(o.returned) / COUNT(o.order_id),
        1
    ) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;



-- Task 3(e) — Customer ranking by total spend
-- Tie-break: customer_id ASC makes the ranking deterministic when customers have equal total spend.

-- Query 1: Top 5
-- SQLite output:
-- customer_id | name    | total_spend
-- C043        | Reyansh | 12920.0
-- C026        | Isha    | 8371.6
-- C008        | Meera   | 4564.6
-- C011        | Arjun   | 4111.0
-- C042        | Sanya   | 3785.0

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.name
ORDER BY
    total_spend DESC,
    c.customer_id ASC
LIMIT 5;


-- Query 2: Ranks 3–5 using LIMIT/OFFSET
-- SQLite output:
-- customer_id | name  | total_spend
-- C008        | Meera | 4564.6
-- C011        | Arjun | 4111.0
-- C042        | Sanya | 3785.0

SELECT
    c.customer_id,
    c.name,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.name
ORDER BY
    total_spend DESC,
    c.customer_id ASC
LIMIT 3 OFFSET 2;



-- Task 3(f) — Category revenue
-- SQLite output:
-- category     | order_count | category_revenue
-- Haircare     | 54          | 44956.1
-- Skincare     | 60          | 27346.0
-- Babycare     | 30          | 16805.0
-- PersonalCare | 36          | 10753.1

SELECT
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(
        SUM(
            o.quantity * p.price *
            (1 - COALESCE(o.discount_pct, 0) / 100.0)
        ),
        2
    ) AS category_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- Task 3(g) — Customers whose name starts with 'A'
-- SQLite output:
-- customer_id | name
-- C001        | Aarav
-- C003        | Aditi
-- C004        | Ananya
-- C011        | Arjun
-- C021        | Aryan
-- C030        | Anika
-- C031        | Aditya
-- C036        | Aisha
-- C041        | Ayaan
-- C044        | Aria

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%'
ORDER BY customer_id;




-- Task 3(h) — Distinct acquisition sources
-- SQLite output:
-- acquisition_source
-- Ad
-- Organic
-- Referral
-- Social

SELECT DISTINCT
    acquisition_source
FROM customers
ORDER BY acquisition_source;



-- Task 3(i) — Loyalty tier using ALTER TABLE + CASE

ALTER TABLE customers
ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier =
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END;

-- SQLite output:
-- loyalty_tier | customer_count
-- Gold         | 28
-- Silver       | 17

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
