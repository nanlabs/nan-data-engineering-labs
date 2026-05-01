-- =====================================================
-- Module 03: SQL Foundations - Database Initialization
-- =====================================================
-- This script creates the e-commerce sample database
-- with tables, sample data, and useful functions.
--
-- Database: ecommerce
-- Schema: public
-- Tables: users, products, orders, order_items, user_activity
-- =====================================================

-- Set timezone and locale
SET timezone = 'UTC';
SET client_encoding = 'UTF8';

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =====================================================
-- DROP EXISTING TABLES (for clean re-initialization)
-- =====================================================

DROP TABLE IF EXISTS user_activity CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =====================================================
-- CREATE TABLES
-- =====================================================

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    country VARCHAR(2) NOT NULL,  -- ISO 3166-1 alpha-2
    city VARCHAR(100),
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    loyalty_points INTEGER NOT NULL DEFAULT 0,

    -- Constraints
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_loyalty_points_positive CHECK (loyalty_points >= 0)
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,

    -- Constraints
    CONSTRAINT products_price_positive CHECK (price > 0),
    CONSTRAINT products_stock_non_negative CHECK (stock_quantity >= 0)
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    shipping_address TEXT,
    payment_method VARCHAR(50),

    -- Constraints
    CONSTRAINT orders_total_amount_positive CHECK (total_amount >= 0),
    CONSTRAINT orders_status_valid CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

-- Order items (junction table for orders and products)
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,

    -- Constraints
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_unit_price_positive CHECK (unit_price >= 0),
    CONSTRAINT order_items_subtotal_correct CHECK (subtotal = quantity * unit_price),

    -- Prevent duplicate products in same order
    CONSTRAINT order_items_unique_product_per_order UNIQUE (order_id, product_id)
);

-- User activity log table
CREATE TABLE user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    product_id INTEGER REFERENCES products(product_id) ON DELETE SET NULL,
    details JSONB,

    -- Constraints
    CONSTRAINT user_activity_type_valid CHECK (activity_type IN ('login', 'logout', 'view_product', 'add_to_cart', 'purchase', 'review'))
);

-- =====================================================
-- CREATE INDEXES
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_users_registration_date ON users(registration_date);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Products indexes
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_name_trgm ON products USING gin(product_name gin_trgm_ops);  -- Fuzzy search

-- Orders indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);  -- Composite index

-- Order items indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- User activity indexes
CREATE INDEX idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX idx_user_activity_timestamp ON user_activity(activity_timestamp);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX idx_user_activity_details ON user_activity USING gin(details);  -- JSONB index

-- =====================================================
-- INSERT SAMPLE DATA
-- =====================================================

-- Insert users (100 users)
INSERT INTO users (email, first_name, last_name, country, city, registration_date, is_active, loyalty_points)
VALUES
    ('john.smith@email.com', 'John', 'Smith', 'US', 'New York', '2023-01-15', TRUE, 150),
    ('jane.doe@email.com', 'Jane', 'Doe', 'US', 'Los Angeles', '2023-02-20', TRUE, 220),
    ('bob.wilson@email.com', 'Bob', 'Wilson', 'GB', 'London', '2023-03-10', TRUE, 80),
    ('alice.brown@email.com', 'Alice', 'Brown', 'CA', 'Toronto', '2023-04-05', TRUE, 300),
    ('charlie.davis@email.com', 'Charlie', 'Davis', 'AU', 'Sydney', '2023-05-12', TRUE, 45),
    ('emma.garcia@email.com', 'Emma', 'Garcia', 'ES', 'Madrid', '2023-06-18', TRUE, 190),
    ('david.martinez@email.com', 'David', 'Martinez', 'MX', 'Mexico City', '2023-07-22', TRUE, 110),
    ('sophia.lee@email.com', 'Sophia', 'Lee', 'KR', 'Seoul', '2023-08-30', TRUE, 260),
    ('james.taylor@email.com', 'James', 'Taylor', 'US', 'Chicago', '2023-09-14', TRUE, 75),
    ('olivia.white@email.com', 'Olivia', 'White', 'GB', 'Manchester', '2023-10-08', TRUE, 340),
    ('lucas.anderson@email.com', 'Lucas', 'Anderson', 'SE', 'Stockholm', '2023-11-20', FALSE, 20),
    ('mia.thomas@email.com', 'Mia', 'Thomas', 'FR', 'Paris', '2023-12-05', TRUE, 280),
    ('noah.jackson@email.com', 'Noah', 'Jackson', 'US', 'Houston', '2024-01-10', TRUE, 95),
    ('ava.harris@email.com', 'Ava', 'Harris', 'CA', 'Vancouver', '2024-02-15', TRUE, 170),
    ('william.martin@email.com', 'William', 'Martin', 'DE', 'Berlin', '2024-03-22', TRUE, 210);

-- Insert more users (to reach ~50 total for exercises)
INSERT INTO users (email, first_name, last_name, country, city, registration_date, is_active, loyalty_points)
SELECT
    'user' || generate_series || '@example.com',
    'User' || generate_series,
    'Test' || generate_series,
    CASE (generate_series % 5)
        WHEN 0 THEN 'US'
        WHEN 1 THEN 'GB'
        WHEN 2 THEN 'CA'
        WHEN 3 THEN 'AU'
        ELSE 'DE'
    END,
    CASE (generate_series % 5)
        WHEN 0 THEN 'New York'
        WHEN 1 THEN 'London'
        WHEN 2 THEN 'Toronto'
        WHEN 3 THEN 'Sydney'
        ELSE 'Berlin'
    END,
    CURRENT_DATE - (generate_series || ' days')::INTERVAL,
    (generate_series % 10) != 0,  -- 10% inactive
    (generate_series * 13) % 500
FROM generate_series(16, 50);

-- Insert products (50 products across categories)
INSERT INTO products (product_name, category, price, stock_quantity, description, is_available)
VALUES
    ('Laptop Pro 15"', 'Electronics', 1299.99, 45, 'High-performance laptop with 16GB RAM', TRUE),
    ('Wireless Mouse', 'Electronics', 29.99, 200, 'Ergonomic wireless mouse with USB receiver', TRUE),
    ('USB-C Cable 2m', 'Electronics', 12.99, 500, 'Durable USB-C charging cable', TRUE),
    ('Bluetooth Headphones', 'Electronics', 89.99, 120, 'Noise-cancelling over-ear headphones', TRUE),
    ('4K Monitor 27"', 'Electronics', 399.99, 30, 'Ultra HD monitor with HDR support', TRUE),
    ('Mechanical Keyboard', 'Electronics', 149.99, 80, 'RGB backlit mechanical gaming keyboard', TRUE),
    ('Webcam HD', 'Electronics', 59.99, 150, '1080p webcam with built-in microphone', TRUE),
    ('External SSD 1TB', 'Electronics', 119.99, 95, 'Portable solid-state drive', TRUE),
    ('Phone Case', 'Accessories', 15.99, 300, 'Protective silicone phone case', TRUE),
    ('Screen Protector', 'Accessories', 9.99, 400, 'Tempered glass screen protector', TRUE),

    ('Python Programming Book', 'Books', 49.99, 60, 'Comprehensive guide to Python', TRUE),
    ('SQL for Data Science', 'Books', 39.99, 75, 'Learn SQL for data analysis', TRUE),
    ('Cloud Computing Guide', 'Books', 54.99, 40, 'Introduction to AWS and Azure', TRUE),
    ('Data Engineering Handbook', 'Books', 64.99, 35, 'Complete data engineering reference', TRUE),
    ('Machine Learning Basics', 'Books', 44.99, 55, 'Introduction to ML algorithms', TRUE),

    ('Office Chair', 'Furniture', 249.99, 25, 'Ergonomic office chair with lumbar support', TRUE),
    ('Standing Desk', 'Furniture', 399.99, 15, 'Adjustable height standing desk', TRUE),
    ('Desk Lamp', 'Furniture', 34.99, 100, 'LED desk lamp with adjustable brightness', TRUE),
    ('Bookshelf', 'Furniture', 89.99, 20, '5-tier wooden bookshelf', TRUE),
    ('Monitor Stand', 'Furniture', 29.99, 70, 'Adjustable monitor riser', TRUE),

    ('Protein Powder', 'Sports', 39.99, 150, '2kg whey protein powder', TRUE),
    ('Yoga Mat', 'Sports', 24.99, 80, 'Non-slip exercise yoga mat', TRUE),
    ('Resistance Bands Set', 'Sports', 19.99, 120, 'Set of 5 resistance bands', TRUE),
    ('Water Bottle', 'Sports', 14.99, 200, 'Insulated stainless steel water bottle', TRUE),
    ('Gym Bag', 'Sports', 34.99, 90, 'Spacious sports duffel bag', TRUE),

    ('Coffee Maker', 'Home', 79.99, 50, 'Programmable drip coffee maker', TRUE),
    ('Blender', 'Home', 49.99, 65, 'High-speed blender for smoothies', TRUE),
    ('Air Fryer', 'Home', 99.99, 40, '5L capacity air fryer', TRUE),
    ('Vacuum Cleaner', 'Home', 159.99, 30, 'Cordless stick vacuum cleaner', TRUE),
    ('Electric Kettle', 'Home', 29.99, 100, '1.7L stainless steel kettle', TRUE);

-- Add more products to reach 50
INSERT INTO products (product_name, category, price, stock_quantity, description, is_available)
SELECT
    'Product ' || generate_series,
    CASE (generate_series % 6)
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Books'
        WHEN 2 THEN 'Furniture'
        WHEN 3 THEN 'Sports'
        WHEN 4 THEN 'Home'
        ELSE 'Accessories'
    END,
    (10 + (generate_series * 7) % 500)::DECIMAL(10,2),
    (generate_series * 11) % 200 + 10,
    'Description for product ' || generate_series,
    (generate_series % 15) != 0  -- 93% available
FROM generate_series(31, 50);

-- Insert orders (200 orders)
INSERT INTO orders (user_id, order_date, total_amount, status, shipping_address, payment_method)
SELECT
    (random() * 49 + 1)::INTEGER,  -- Random user_id from 1-50
    TIMESTAMP '2023-01-01' + (random() * (TIMESTAMP '2024-12-31' - TIMESTAMP '2023-01-01')),
    (random() * 500 + 20)::DECIMAL(10,2),
    CASE (random() * 100)::INTEGER % 5
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'shipped'
        WHEN 3 THEN 'delivered'
        ELSE 'delivered'  -- Most orders delivered
    END,
    'Address Line ' || generate_series,
    CASE (random() * 10)::INTEGER % 3
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'paypal'
        ELSE 'debit_card'
    END
FROM generate_series(1, 200);

-- Insert order items (2-5 items per order, ~600 total)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
SELECT
    o.order_id,
    (random() * 49 + 1)::INTEGER,  -- Random product_id from 1-50
    (random() * 4 + 1)::INTEGER,   -- Quantity 1-5
    p.price,
    (random() * 4 + 1)::INTEGER * p.price
FROM orders o
CROSS JOIN LATERAL (
    SELECT product_id, price FROM products WHERE product_id = (random() * 49 + 1)::INTEGER LIMIT 1
) p
CROSS JOIN generate_series(1, (random() * 3 + 2)::INTEGER)  -- 2-5 items per order
ON CONFLICT (order_id, product_id) DO NOTHING;  -- Skip duplicates

-- Update order totals based on actual items
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(subtotal), 0)
    FROM order_items oi
    WHERE oi.order_id = o.order_id
);

-- Insert user activity (1000 activities)
INSERT INTO user_activity (user_id, activity_type, activity_timestamp, product_id, details)
SELECT
    (random() * 49 + 1)::INTEGER,
    CASE (random() * 100)::INTEGER % 6
        WHEN 0 THEN 'login'
        WHEN 1 THEN 'logout'
        WHEN 2 THEN 'view_product'
        WHEN 3 THEN 'add_to_cart'
        WHEN 4 THEN 'purchase'
        ELSE 'review'
    END,
    TIMESTAMP '2023-01-01' + (random() * (TIMESTAMP '2024-12-31' - TIMESTAMP '2023-01-01')),
    CASE WHEN (random() * 10)::INTEGER > 3 THEN (random() * 49 + 1)::INTEGER ELSE NULL END,
    jsonb_build_object(
        'ip_address', '192.168.' || (random() * 255)::INTEGER || '.' || (random() * 255)::INTEGER,
        'user_agent', 'Mozilla/5.0',
        'session_id', uuid_generate_v4()
    )
FROM generate_series(1, 1000);

-- =====================================================
-- CREATE VIEWS
-- =====================================================

-- View: Order summary with user and product details
CREATE OR REPLACE VIEW v_order_summary AS
SELECT
    o.order_id,
    o.order_date,
    u.user_id,
    u.first_name || ' ' || u.last_name AS customer_name,
    u.email,
    u.country,
    COUNT(DISTINCT oi.product_id) AS products_count,
    SUM(oi.quantity) AS total_items,
    o.total_amount,
    o.status
FROM orders o
JOIN users u ON o.user_id = u.user_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_date, u.user_id, u.first_name, u.last_name, u.email, u.country, o.total_amount, o.status;

-- View: Product sales summary
CREATE OR REPLACE VIEW v_product_sales AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.subtotal) AS total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category, p.price;

-- View: User purchase summary
CREATE OR REPLACE VIEW v_user_summary AS
SELECT
    u.user_id,
    u.email,
    u.first_name || ' ' || u.last_name AS full_name,
    u.country,
    u.registration_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    COALESCE(AVG(o.total_amount), 0) AS avg_order_value,
    MAX(o.order_date) AS last_order_date,
    u.loyalty_points
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.email, u.first_name, u.last_name, u.country, u.registration_date, u.loyalty_points;

-- =====================================================
-- CREATE FUNCTIONS
-- =====================================================

-- Function: Update product stock after order
CREATE OR REPLACE FUNCTION update_product_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate loyalty points for order
CREATE OR REPLACE FUNCTION calculate_loyalty_points(order_amount DECIMAL)
RETURNS INTEGER AS $$
BEGIN
    -- 1 point per $10 spent
    RETURN FLOOR(order_amount / 10)::INTEGER;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function: Get top products by category
CREATE OR REPLACE FUNCTION get_top_products_by_category(
    p_category VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    product_id INTEGER,
    product_name VARCHAR,
    total_sold BIGINT,
    revenue NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.product_id,
        p.product_name,
        SUM(oi.quantity) AS total_sold,
        SUM(oi.subtotal) AS revenue
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    WHERE p.category = p_category
    GROUP BY p.product_id, p.product_name
    ORDER BY total_sold DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CREATE TRIGGERS
-- =====================================================

-- Trigger: Update updated_at timestamp on product changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================

-- Grant read access to all tables (useful for read-only users)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;

-- =====================================================
-- ANALYZE TABLES
-- =====================================================

-- Update statistics for query optimizer
ANALYZE users;
ANALYZE products;
ANALYZE orders;
ANALYZE order_items;
ANALYZE user_activity;

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Database: ecommerce';
    RAISE NOTICE 'Tables created: 5';
    RAISE NOTICE 'Sample users: %', (SELECT COUNT(*) FROM users);
    RAISE NOTICE 'Sample products: %', (SELECT COUNT(*) FROM products);
    RAISE NOTICE 'Sample orders: %', (SELECT COUNT(*) FROM orders);
    RAISE NOTICE 'Sample order items: %', (SELECT COUNT(*) FROM order_items);
    RAISE NOTICE 'Sample activities: %', (SELECT COUNT(*) FROM user_activity);
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Ready for SQL exercises!';
    RAISE NOTICE '==============================================';
END $$;
