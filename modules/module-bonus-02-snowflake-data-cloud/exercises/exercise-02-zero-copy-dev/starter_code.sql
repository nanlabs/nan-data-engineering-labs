-- ============================================================================
-- Exercise 02: Zero-Copy Cloning for Development
-- ============================================================================
--
-- Learning Objectives:
-- - Understand Snowflake's zero-copy cloning architecture
-- - Clone databases, schemas, and tables instantly
-- - Track storage divergence between clones
-- - Calculate cost savings from zero-copy cloning
-- - Implement development/testing workflows with clones
--
-- Estimated Time: 75 minutes
-- Difficulty: Intermediate
-- ============================================================================

-- ============================================================================
-- SETUP: Create Production Environment
-- ============================================================================

-- Create production database and schema
CREATE OR REPLACE DATABASE prod_db;
USE DATABASE prod_db;
CREATE SCHEMA IF NOT EXISTS sales;
USE SCHEMA sales;

-- ============================================================================
-- TASK 1: Setup Production Data (20 points)
-- ============================================================================
-- Create production tables with realistic data to demonstrate cloning.
-- ============================================================================

-- TODO: Create customers table with 10,000 records
-- Include columns: customer_id, name, email, region, signup_date
-- Your code here:


-- TODO: Create orders table with 50,000 records
-- Include columns: order_id, customer_id, order_date, amount, status
-- Your code here:


-- TODO: Create order_items table with 150,000 records
-- Include columns: item_id, order_id, product_name, quantity, unit_price
-- Your code here:


-- TODO: Verify production data
-- Check row counts for all tables
-- Your code here:


-- ============================================================================
-- TASK 2: Clone Production Database (15 points)
-- ============================================================================
-- Create a complete clone of the production database for development.
-- This should be instant and consume no additional storage initially.
-- ============================================================================

-- TODO: Clone the entire production database to dev_db
-- This is a zero-copy clone - instant and no additional storage
-- Your code here:


-- TODO: Verify the clone was created successfully
-- Check that dev_db has the same structure as prod_db
-- Your code here:


-- TODO: Compare row counts between prod and dev
-- Ensure data was cloned correctly
-- Your code here:


-- ============================================================================
-- TASK 3: Clone Individual Tables (15 points)
-- ============================================================================
-- Create table-level clones for specific testing scenarios.
-- ============================================================================

-- TODO: Create a clone of the customers table for testing
-- Name it: customers_test
-- Your code here:


-- TODO: Create a historical clone of orders from 1 hour ago
-- Use AT(OFFSET => -3600) for time travel
-- Your code here:


-- TODO: Clone specific schema only
-- Clone the sales schema to a new schema called sales_backup
-- Your code here:


-- ============================================================================
-- TASK 4: Make Modifications in Development (20 points)
-- ============================================================================
-- Demonstrate that clones are independent - changes in dev don't affect prod.
-- ============================================================================

-- TODO: Use the dev database
-- Your code here:


-- TODO: Insert new records into dev customers table
-- Add 100 new test customers
-- Your code here:


-- TODO: Update records in dev orders table
-- Update order status for testing
-- Your code here:


-- TODO: Delete some records in dev
-- Remove test data to simulate cleanup
-- Your code here:


-- TODO: Verify prod is unchanged
-- Switch to prod_db and verify no changes occurred
-- Your code here:


-- ============================================================================
-- TASK 5: Time Travel Cloning (15 points)
-- ============================================================================
-- Clone data from specific points in time for recovery or analysis.
-- ============================================================================

-- TODO: Clone customers table from 30 minutes ago
-- Use AT(OFFSET => -1800)
-- Your code here:


-- TODO: Clone orders table from a specific timestamp
-- Use AT(TIMESTAMP => 'YYYY-MM-DD HH:MI:SS')
-- Your code here:


-- TODO: Clone before a specific statement
-- Use BEFORE(STATEMENT => 'query_id')
-- First get a query_id from query_history
-- Your code here:


-- ============================================================================
-- TASK 6: Track Storage Divergence (15 points)
-- ============================================================================
-- Monitor how storage usage changes as clones diverge from originals.
-- ============================================================================

-- TODO: Query table storage metrics
-- Use TABLE_STORAGE_METRICS to see storage usage
-- Your code here:


-- TODO: Calculate storage divergence percentage
-- Compare active bytes between original and cloned tables
-- Your code here:


-- TODO: Analyze storage costs
-- Calculate monthly storage costs based on divergence
-- Assume $23 per TB per month for storage
-- Your code here:


-- TODO: Identify tables with highest storage usage
-- Find which tables consume the most storage
-- Your code here:


-- ============================================================================
-- COST SAVINGS ANALYSIS
-- ============================================================================
-- Document the cost savings from using zero-copy cloning:
--
-- Scenario: Daily refresh of 1TB production database to dev environment
--
-- Traditional Approach (Full Copy):
-- - Storage required: _____ TB
-- - Time required: _____ hours
-- - Storage cost: $ _____ per month
-- - Total cost: $ _____ per month
--
-- Zero-Copy Cloning Approach:
-- - Initial storage: _____ TB (zero)
-- - Time required: _____ seconds
-- - Storage cost (divergence only): $ _____ per month
-- - Total savings: $ _____ per month ( _____% reduction)
--
-- Additional Benefits:
-- 1. _________________________________________________________________
-- 2. _________________________________________________________________
-- 3. _________________________________________________________________
-- ============================================================================

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================
-- Uncomment to remove exercise resources

-- DROP DATABASE IF EXISTS prod_db;
-- DROP DATABASE IF EXISTS dev_db;

-- ============================================================================
-- END OF EXERCISE
-- ============================================================================
