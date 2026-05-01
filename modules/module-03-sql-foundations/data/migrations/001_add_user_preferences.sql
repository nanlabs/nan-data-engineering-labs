-- =====================================================
-- Migration: Add user preferences column
-- Version: 001
-- Date: 2024-01-15
-- Description: Add JSONB column for user preferences
-- =====================================================

-- Up Migration
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::JSONB;

-- Add index on preferences for efficient queries
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING gin(preferences);

-- Comment
COMMENT ON COLUMN users.preferences IS 'User preferences and settings (JSON format)';

-- Example usage:
-- UPDATE users SET preferences = '{"theme": "dark", "notifications": true}'::JSONB WHERE user_id = 1;

-- Down Migration (rollback)
-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_users_preferences;
-- ALTER TABLE users DROP COLUMN IF EXISTS preferences;
