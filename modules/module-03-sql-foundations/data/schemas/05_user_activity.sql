-- =====================================================
-- Table: user_activity
-- Description: User activity log with event tracking
-- =====================================================

CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    product_id INTEGER REFERENCES products(product_id) ON DELETE SET NULL,
    details JSONB,

    -- Constraints
    CONSTRAINT user_activity_type_valid CHECK (activity_type IN ('login', 'logout', 'view_product', 'add_to_cart', 'purchase', 'review'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(activity_timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_details ON user_activity USING gin(details);

-- Comments
COMMENT ON TABLE user_activity IS 'User event log for behavior tracking and analytics';
COMMENT ON COLUMN user_activity.activity_id IS 'Unique activity identifier (auto-increment)';
COMMENT ON COLUMN user_activity.user_id IS 'Foreign key to users table';
COMMENT ON COLUMN user_activity.activity_type IS 'Event type: login, logout, view_product, add_to_cart, purchase, review';
COMMENT ON COLUMN user_activity.product_id IS 'Optional foreign key to products table (for product-related events)';
COMMENT ON COLUMN user_activity.details IS 'JSON metadata (IP address, user agent, session ID, etc.)';
