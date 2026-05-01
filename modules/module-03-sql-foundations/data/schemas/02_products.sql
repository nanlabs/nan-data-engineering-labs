-- =====================================================
-- Table: products
-- Description: Product catalog with pricing and inventory
-- =====================================================

CREATE TABLE IF NOT EXISTS products (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin(product_name gin_trgm_ops);

-- Comments
COMMENT ON TABLE products IS 'Product catalog with pricing, inventory, and categorization';
COMMENT ON COLUMN products.product_id IS 'Unique product identifier (auto-increment)';
COMMENT ON COLUMN products.category IS 'Product category (Electronics, Books, Furniture, Sports, Home, Accessories)';
COMMENT ON COLUMN products.price IS 'Product price in USD (must be positive)';
COMMENT ON COLUMN products.stock_quantity IS 'Available inventory count';
COMMENT ON COLUMN products.is_available IS 'Product availability for purchase';
