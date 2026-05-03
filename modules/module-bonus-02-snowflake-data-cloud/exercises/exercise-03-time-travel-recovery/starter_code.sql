-- ============================================================================
-- Exercise 03: Time Travel and Data Recovery
-- ============================================================================
--
-- Learning Objectives:
-- - Use Time Travel to query historical data states
-- - Recover dropped tables with UNDROP command
-- - Perform point-in-time recovery after data corruption
-- - Configure retention periods for different scenarios
-- - Design comprehensive disaster recovery strategies
--
-- Estimated Time: 90 minutes
-- Difficulty: Intermediate to Advanced
-- ============================================================================

-- ============================================================================
-- SETUP: Create Database and Initial Tables
-- ============================================================================

CREATE OR REPLACE DATABASE time_travel_demo;
USE DATABASE time_travel_demo;
CREATE SCHEMA IF NOT EXISTS recovery;
USE SCHEMA recovery;

-- ============================================================================
-- TASK 1: Setup and Track Data Changes Over Time (15 points)
-- ============================================================================
-- Create tables and make a series of tracked changes to demonstrate
-- Time Travel capabilities.
-- ============================================================================

-- TODO: Create orders table with 1000 initial records
-- Include: order_id, customer_id, amount, order_date, status
-- Your code here:


-- TODO: Record the current timestamp
-- Save this for later time travel queries
-- Your code here:


-- TODO: Make first modification - Insert 200 more orders
-- Wait a few seconds between operations
-- Your code here:


-- TODO: Make second modification - Update order statuses
-- Change some orders to 'shipped' status
-- Your code here:


-- TODO: Make third modification - Delete some old orders
-- Remove orders older than 180 days
-- Your code here:


-- TODO: Verify current state
-- Check final row count and status distribution
-- Your code here:


-- ============================================================================
-- TASK 2: Query Historical Data States (20 points)
-- ============================================================================
-- Use Time Travel to query data as it existed at different points in time.
-- ============================================================================

-- TODO: Query orders table at initial creation time
-- Use AT(TIMESTAMP => 'yyyy-mm-dd hh:mi:ss')
-- Your code here:


-- TODO: Query orders after first insert (1200 rows)
-- Use AT(OFFSET => -seconds_ago)
-- Your code here:


-- TODO: Query orders before the DELETE operation
-- Use BEFORE(STATEMENT => 'query_id')
-- Your code here:


-- TODO: Compare row counts across different time points
-- Show how data evolved over time
-- Your code here:


-- TODO: Query specific columns at historical timestamps
-- Show order status changes over time
-- Your code here:


-- ============================================================================
-- TASK 3: UNDROP - Recover Dropped Objects (20 points)
-- ============================================================================
-- Demonstrate recovery of accidentally dropped tables and schemas.
-- ============================================================================

-- TODO: Create a test table with important data
-- Name it: customer_data
-- Your code here:


-- TODO: Verify the table exists and has data
-- Your code here:


-- TODO: Simulate accidental drop
-- DROP TABLE customer_data;
-- Your code here:


-- TODO: Verify the table is gone
-- Try to query it (should fail)
-- Your code here:


-- TODO: Recover the table using UNDROP
-- UNDROP TABLE customer_data;
-- Your code here:


-- TODO: Verify data was recovered completely
-- Check row count matches original
-- Your code here:


-- TODO: Test UNDROP with schemas
-- Drop and recover an entire schema
-- Your code here:


-- ============================================================================
-- TASK 4: Point-in-Time Recovery (25 points)
-- ============================================================================
-- Simulate data corruption and perform point-in-time recovery.
-- ============================================================================

-- TODO: Create a critical transactions table
-- Include transaction_id, account_id, amount, timestamp
-- Your code here:


-- TODO: Load initial correct data (500 transactions)
-- Your code here:


-- TODO: Record timestamp BEFORE corruption
-- This is your recovery point
-- Your code here:


-- TODO: Simulate data corruption
-- Accidentally update all amounts to zero or delete important records
-- Your code here:


-- TODO: Verify corruption occurred
-- Check that data is damaged
-- Your code here:


-- TODO: Perform point-in-time recovery
-- Clone data from before corruption timestamp
-- Your code here:


-- TODO: Replace corrupted table with recovered data
-- Drop corrupted table and rename clone
-- Your code here:


-- TODO: Verify recovery was successful
-- Check all data is intact
-- Your code here:


-- ============================================================================
-- TASK 5: Configure Retention Periods (10 points)
-- ============================================================================
-- Set appropriate retention periods for different types of data.
-- ============================================================================

-- TODO: Check default retention period
-- Query table metadata
-- Your code here:


-- TODO: Set extended retention for critical financial data
-- ALTER TABLE ... SET DATA_RETENTION_TIME_IN_DAYS = 90
-- Note: Requires Enterprise Edition or higher
-- Your code here:


-- TODO: Set different retention for temporary/staging tables
-- Use 0 or 1 day retention
-- Your code here:


-- TODO: View retention settings for all tables
-- Query INFORMATION_SCHEMA
-- Your code here:


-- ============================================================================
-- TASK 6: Design Disaster Recovery Plan (10 points)
-- ============================================================================
-- Document comprehensive disaster recovery scenarios and solutions.
-- ============================================================================

-- Scenario 1: Accidental Table Drop
-- Problem: ______________________________________________________________
-- Solution: ______________________________________________________________
-- SQL Example: ______________________________________________________________
-- Recovery Time: ______________________________________________________________


-- Scenario 2: Bulk Data Corruption
-- Problem: ______________________________________________________________
-- Solution: ______________________________________________________________
-- SQL Example: ______________________________________________________________
-- Recovery Time: ______________________________________________________________


-- Scenario 3: Malicious Data Deletion
-- Problem: ______________________________________________________________
-- Solution: ______________________________________________________________
-- SQL Example: ______________________________________________________________
-- Recovery Time: ______________________________________________________________


-- Scenario 4: Application Bug Data Damage
-- Problem: ______________________________________________________________
-- Solution: ______________________________________________________________
-- SQL Example: ______________________________________________________________
-- Recovery Time: ______________________________________________________________


-- Scenario 5: Incomplete Transaction Rollback
-- Problem: ______________________________________________________________
-- Solution: ______________________________________________________________
-- SQL Example: ______________________________________________________________
-- Recovery Time: ______________________________________________________________

-- ============================================================================
-- BONUS: Advanced Time Travel Queries (Extra Credit)
-- ============================================================================

-- TODO: Query changes between two timestamps
-- Show what changed in a specific time window
-- Your code here:


-- TODO: Track who made changes when
-- Use QUERY_HISTORY to find modification queries
-- Your code here:


-- TODO: Create audit trail using Time Travel
-- Compare current vs historical states
-- Your code here:


-- ============================================================================
-- IMPORTANT NOTES ON TIME TRAVEL
-- ============================================================================
--
-- 1. Time Travel Retention Periods:
--    - Standard Edition: 1 day (default, max)
--    - Enterprise Edition: 0-90 days (configurable)
--
-- 2. Fail-safe Period:
--    - Additional 7 days after Time Travel
--    - Only recoverable by Snowflake Support
--    - Automatic, non-configurable
--
-- 3. Storage Costs:
--    - Time Travel data is stored and billed
--    - Monitor using TABLE_STORAGE_METRICS
--    - Balance retention needs vs costs
--
-- 4. Query Performance:
--    - Historical queries may be slower
--    - Depend on data change volume
--    - Use specific timestamps when possible
--
-- ============================================================================

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================
-- Uncomment to remove exercise resources

-- DROP DATABASE IF EXISTS time_travel_demo;

-- ============================================================================
-- END OF EXERCISE
-- ============================================================================
