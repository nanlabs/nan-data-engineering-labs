-- =====================================================
-- Table: users
-- Description: User account information
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_country ON users(country);
CREATE INDEX IF NOT EXISTS idx_users_registration_date ON users(registration_date);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE users IS 'Registered user accounts with contact and loyalty information';
COMMENT ON COLUMN users.user_id IS 'Unique user identifier (auto-increment)';
COMMENT ON COLUMN users.email IS 'User email address (unique, validated format)';
COMMENT ON COLUMN users.country IS 'ISO 3166-1 alpha-2 country code';
COMMENT ON COLUMN users.loyalty_points IS 'Accumulated reward points';
