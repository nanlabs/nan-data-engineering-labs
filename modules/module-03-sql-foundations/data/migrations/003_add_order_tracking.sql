-- =====================================================
-- Migration: Add order tracking
-- Version: 003
-- Date: 2024-03-01
-- Description: Add tracking number and estimated delivery
-- =====================================================

-- Up Migration
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS estimated_delivery DATE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipped_date TIMESTAMP;

-- Add index for tracking lookups
CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_number) WHERE tracking_number IS NOT NULL;

-- Add index for delivery date queries
CREATE INDEX IF NOT EXISTS idx_orders_delivery ON orders(estimated_delivery) WHERE estimated_delivery IS NOT NULL;

-- Comments
COMMENT ON COLUMN orders.tracking_number IS 'Shipping carrier tracking number';
COMMENT ON COLUMN orders.estimated_delivery IS 'Estimated delivery date';
COMMENT ON COLUMN orders.shipped_date IS 'Actual shipment date/time';

-- Example usage:
-- UPDATE orders SET tracking_number = '1Z999AA10123456784',
--                   estimated_delivery = CURRENT_DATE + INTERVAL '5 days',
--                   shipped_date = CURRENT_TIMESTAMP
-- WHERE order_id = 1 AND status = 'shipped';

-- Down Migration (rollback)
-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_orders_tracking;
-- DROP INDEX IF EXISTS idx_orders_delivery;
-- ALTER TABLE orders DROP COLUMN IF EXISTS tracking_number;
-- ALTER TABLE orders DROP COLUMN IF EXISTS estimated_delivery;
-- ALTER TABLE orders DROP COLUMN IF EXISTS shipped_date;
