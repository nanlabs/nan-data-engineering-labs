-- ============================================================================
-- Exercise 06: Data Sharing and Secure Views
-- Starter Code
-- ============================================================================
-- OBJECTIVE: Implement Snowflake Data Sharing with secure views
-- - Create shared database and populate with data
-- - Set up secure views with row-level security
-- - Configure data share and grant permissions
-- - Add consumer accounts
-- - Monitor usage and costs
-- - Explore Snowflake Data Marketplace
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
-- TODO: Set up environment
-- YOUR CODE HERE:

USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- TODO: Create database for sharing
-- Database name: SHARED_ANALYTICS
-- YOUR CODE HERE:


-- TODO: Create schema CUSTOMER_DATA
-- YOUR CODE HERE:


USE SCHEMA SHARED_ANALYTICS.CUSTOMER_DATA;


-- Step 2: Create and Populate Source Tables
-- ============================================================================
-- TODO: Create customer_metrics table with columns:
--   - CUSTOMER_ID: VARCHAR(50)
--   - METRIC_NAME: VARCHAR(100)
--   - VALUE: DOUBLE
--   - DATE: DATE
--   - CATEGORY: VARCHAR(50)
--   - REGION: VARCHAR(50)
-- YOUR CODE HERE:


-- TODO: Insert sample data for 5 different customers
-- Generate 10,000 rows total with various metrics like:
--   - revenue, orders, sessions, conversion_rate, avg_order_value
-- Use date range: last 90 days
-- YOUR CODE HERE:


-- TODO: Verify data distribution
-- Check counts per customer and date range
-- YOUR CODE HERE:


-- Step 3: Create Secure View with Row-Level Security
-- ============================================================================
-- TODO: Create secure view customer_metrics_filtered
-- Implement row-level security that filters by CUSTOMER_ID
-- Use CURRENT_USER() or session context to determine which rows to show
-- Hint: Consider using CURRENT_ACCOUNT_SECURE_VIEWS() for share context
-- YOUR CODE HERE:


-- TODO: Test secure view with different contexts
-- YOUR CODE HERE:


-- Step 4: Implement Column Masking for PII
-- ============================================================================
-- TODO: Create table customer_details with PII
--   - CUSTOMER_ID, NAME, EMAIL, PHONE, ADDRESS, CREDIT_CARD
-- YOUR CODE HERE:


-- TODO: Create secure view with masking
-- Mask EMAIL (show domain only), PHONE (show last 4 digits)
-- Mask CREDIT_CARD completely (show XXXX-XXXX-XXXX-1234 pattern)
-- YOUR CODE HERE:


-- TODO: Test masked view
-- YOUR CODE HERE:


-- Step 5: Create Data Share
-- ============================================================================
-- TODO: Create share object
-- Share name: client_analytics
-- Add meaningful comment
-- YOUR CODE HERE:


-- TODO: Grant USAGE on database to share
-- YOUR CODE HERE:


-- TODO: Grant USAGE on schema to share
-- YOUR CODE HERE:


-- TODO: Grant SELECT on tables/views to share
-- Share both customer_metrics_filtered and customer_details_masked
-- YOUR CODE HERE:


-- TODO: Show share configuration
-- YOUR CODE HERE:


-- Step 6: Add Consumer Accounts
-- ============================================================================
-- TODO: Add consumer accounts to share
-- Use format: 'ORG_NAME.ACCOUNT_NAME' (e.g., 'ABC12345')
-- Note: In real scenario, you'd get actual account identifiers from consumers
-- YOUR CODE HERE:


-- TODO: Show accounts that have access to share
-- YOUR CODE HERE:


-- Step 7: Consumer Simulation (Provider Side)
-- ============================================================================
-- TODO: Create outbound share listing (optional - for marketplace)
-- YOUR CODE HERE:


-- TODO: Query share metadata
-- Check what objects are shared
-- YOUR CODE HERE:


-- Step 8: Monitor Data Transfer and Usage
-- ============================================================================
-- TODO: Query DATA_TRANSFER_HISTORY
-- Check bytes transferred to each consumer account
-- YOUR CODE HERE:


-- TODO: Calculate data transfer costs
-- Data transfer within same region: typically free
-- Data transfer cross-region: varies by cloud provider and regions
-- YOUR CODE HERE:


-- TODO: Query access history to see who's querying shared data
-- Use ACCESS_HISTORY view
-- YOUR CODE HERE:


-- Step 9: Snowflake Data Marketplace Exploration
-- ============================================================================
-- TODO: Browse available datasets in Snowflake Data Marketplace
-- Document 3 interesting datasets:
--   1. Dataset name, provider, description, use case
--   2. Dataset name, provider, description, use case
--   3. Dataset name, provider, description, use case
-- YOUR CODE HERE (Use SHOW SHARES FROM DATA EXCHANGE):


-- TODO: Query a marketplace dataset (if available)
-- Example: Use weather data, financial data, or demographic data
-- YOUR CODE HERE:


-- Step 10: Advanced Sharing Scenarios
-- ============================================================================
-- TODO: Create aggregated secure view for share
-- Aggregate metrics to daily/weekly level to protect granular data
-- YOUR CODE HERE:


-- TODO: Implement time-based access control
-- Create view that only shows recent data (e.g., last 30 days)
-- YOUR CODE HERE:


-- TODO: Create share with multiple data granularities
-- Offer both detailed and aggregated views
-- YOUR CODE HERE:


-- Cleanup Commands (DO NOT RUN DURING EXERCISE)
-- ============================================================================
-- DROP SHARE IF EXISTS client_analytics;
-- DROP VIEW IF EXISTS customer_details_masked;
-- DROP VIEW IF EXISTS customer_metrics_filtered;
-- DROP TABLE IF EXISTS customer_details;
-- DROP TABLE IF EXISTS customer_metrics;
-- DROP SCHEMA IF EXISTS SHARED_ANALYTICS.CUSTOMER_DATA;
-- DROP DATABASE IF EXISTS SHARED_ANALYTICS;

-- ============================================================================
-- Validation Checklist
-- ============================================================================
-- [ ] Database and tables created with sample data
-- [ ] Secure views implement row-level security
-- [ ] Column masking applied for PII fields
-- [ ] Share created with proper grants
-- [ ] Consumer accounts added to share
-- [ ] Usage monitoring queries working
-- [ ] DATA_TRANSFER_HISTORY accessible
-- [ ] Snowflake Marketplace explored (3 datasets documented)
-- [ ] Share configuration verified
-- [ ] Access controls tested
-- ============================================================================

-- ============================================================================
-- Data Sharing Best Practices
-- ============================================================================
-- 1. Always use SECURE views for shared data (prevents view expansion)
-- 2. Implement row-level security for multi-tenant scenarios
-- 3. Mask or exclude PII unless explicitly required
-- 4. Monitor data transfer costs for cross-region shares
-- 5. Use aggregated views when possible to reduce data exposure
-- 6. Document share contents and update policies
-- 7. Regularly audit share access and usage
-- 8. Consider creating separate schemas for different share types
-- 9. Use meaningful naming conventions for shares
-- 10. Test shares from consumer perspective before distribution
-- ============================================================================
