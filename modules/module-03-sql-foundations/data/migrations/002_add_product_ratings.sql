-- =====================================================
-- Migration: Add product ratings
-- Version: 002
-- Date: 2024-02-01
-- Description: Add average rating and review count to products
-- =====================================================

-- Up Migration
ALTER TABLE products ADD COLUMN IF NOT EXISTS average_rating DECIMAL(3, 2) DEFAULT 0.00;
ALTER TABLE products ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;

-- Add constraints
ALTER TABLE products ADD CONSTRAINT products_rating_range CHECK (average_rating >= 0 AND average_rating <= 5.00);
ALTER TABLE products ADD CONSTRAINT products_review_count_non_negative CHECK (review_count >= 0);

-- Add index for filtering by rating
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(average_rating DESC) WHERE is_available = TRUE;

-- Comments
COMMENT ON COLUMN products.average_rating IS 'Average customer rating (0.00 to 5.00)';
COMMENT ON COLUMN products.review_count IS 'Total number of reviews';

-- Example usage:
-- UPDATE products SET average_rating = 4.5, review_count = 120 WHERE product_id = 1;

-- Down Migration (rollback)
-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_products_rating;
-- ALTER TABLE products DROP CONSTRAINT IF EXISTS products_rating_range;
-- ALTER TABLE products DROP CONSTRAINT IF EXISTS products_review_count_non_negative;
-- ALTER TABLE products DROP COLUMN IF EXISTS average_rating;
-- ALTER TABLE products DROP COLUMN IF EXISTS review_count;
