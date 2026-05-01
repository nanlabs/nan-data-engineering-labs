-- =====================================================
-- Table: orders
-- Description: Customer orders with status and totals
-- =====================================================

CREATE TABLE IF NOT EXISTS orders (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_date ON orders(user_id, order_date);

-- Comments
COMMENT ON TABLE orders IS 'Customer purchase orders with status tracking and totals';
COMMENT ON COLUMN orders.order_id IS 'Unique order identifier (auto-increment)';
COMMENT ON COLUMN orders.user_id IS 'Foreign key to users table';
COMMENT ON COLUMN orders.status IS 'Order status: pending, processing, shipped, delivered, cancelled';
COMMENT ON COLUMN orders.total_amount IS 'Total order value in USD';
COMMENT ON COLUMN orders.payment_method IS 'Payment type: credit_card, debit_card, paypal';
