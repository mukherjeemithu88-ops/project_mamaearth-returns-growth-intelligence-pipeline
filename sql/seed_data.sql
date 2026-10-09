-- Mamaearth Capstone - SQLite seed/load script
-- Run from C:\Mamaearth-Capstone with:
-- sqlite> .read sql/seed_data.sql
--
-- This script is intentionally a SQLite CLI script because the
-- capstone permits an equivalent loader script for CSV import.
-- It clears existing rows so the script can be re-run safely.

DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;

.import --csv --skip 1 data/customers.csv customers
.import --csv --skip 1 data/products.csv products
.import --csv --skip 1 data/orders.csv orders

-- SQLite .import loads blank CSV cells as empty text.
-- Convert the deliberately blank values to SQL NULL as required by the brief.
UPDATE orders
SET discount_pct = NULL
WHERE discount_pct = '';

UPDATE orders
SET rating = NULL
WHERE rating = '';

-- Validation checks required by the capstone.
SELECT COUNT(*) AS total_customers FROM customers;
SELECT COUNT(*) AS total_products FROM products;
SELECT COUNT(*) AS total_orders FROM orders;
SELECT COUNT(*) AS rated_orders FROM orders WHERE rating IS NOT NULL;
SELECT COUNT(*) AS unrated_orders FROM orders WHERE rating IS NULL;
