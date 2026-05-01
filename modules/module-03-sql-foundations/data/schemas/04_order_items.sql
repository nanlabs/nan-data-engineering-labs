-- =====================================================
-- Table: order_items
-- Description: Line items for each order (junction table)
-- =====================================================

CREATE TABLE IF NOT EXISTS order_items (
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
    CONSTRAINT order_items_unique_product_per_order UNIQUE (order_id, product_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- Comments
COMMENT ON TABLE order_items IS 'Individual line items within orders (many-to-many junction table)';
COMMENT ON COLUMN order_items.order_item_id IS 'Unique order item identifier (auto-increment)';
COMMENT ON COLUMN order_items.order_id IS 'Foreign key to orders table';
COMMENT ON COLUMN order_items.product_id IS 'Foreign key to products table';
COMMENT ON COLUMN order_items.quantity IS 'Number of units ordered';
COMMENT ON COLUMN order_items.unit_price IS 'Price per unit at time of order';
COMMENT ON COLUMN order_items.subtotal IS 'Line total (quantity × unit_price)';
