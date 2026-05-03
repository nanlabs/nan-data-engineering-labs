-- ============================================================================
-- Exercise 01: Warehouse Optimization
-- ============================================================================
--
-- Learning Objectives:
-- - Create and configure virtual warehouses with different sizes
-- - Test performance characteristics across warehouse sizes
-- - Configure auto-suspend and auto-resume settings
-- - Implement multi-cluster warehouses for concurrency
-- - Monitor credit consumption and costs
-- - Develop optimization strategies
--
-- Estimated Time: 90 minutes
-- Difficulty: Intermediate
-- ============================================================================

-- ============================================================================
-- SETUP: Create Database and Use Context
-- ============================================================================

-- Create a dedicated database for this exercise
CREATE DATABASE IF NOT EXISTS warehouse_optimization_db;
USE DATABASE warehouse_optimization_db;
CREATE SCHEMA IF NOT EXISTS performance_testing;
USE SCHEMA performance_testing;

-- ============================================================================
-- TASK 1: Create Warehouses with Different Sizes (20 points)
-- ============================================================================
-- Create three warehouses with different sizes to test performance
-- characteristics and understand cost implications.
--
-- Requirements:
-- - Create COMPUTE_WH_XSMALL (X-Small size)
-- - Create COMPUTE_WH_MEDIUM (Medium size)
-- - Create COMPUTE_WH_LARGE (Large size)
-- - Set appropriate auto-suspend times
-- - Configure auto-resume
-- ============================================================================

-- TODO: Create X-Small warehouse
-- Hint: Use AUTO_SUSPEND = 60 (1 minute)
-- Your code here:


-- TODO: Create Medium warehouse
-- Hint: Use AUTO_SUSPEND = 120 (2 minutes)
-- Your code here:


-- TODO: Create Large warehouse
-- Hint: Use AUTO_SUSPEND = 180 (3 minutes)
-- Your code here:


-- ============================================================================
-- TASK 2: Setup Test Data for Performance Testing (15 points)
-- ============================================================================
-- Create tables with sufficient data to demonstrate performance differences
-- across warehouse sizes.
-- ============================================================================

-- TODO: Create a fact table with 1 million rows
-- Hint: Use GENERATOR to create sample data
-- Your code here:


-- TODO: Create a dimension table with 100,000 rows
-- Your code here:


-- ============================================================================
-- TASK 3: Performance Testing Across Warehouse Sizes (25 points)
-- ============================================================================
-- Run the same query on different warehouse sizes and compare execution times.
-- Document your findings.
-- ============================================================================

-- TODO: Execute on X-Small warehouse
-- Run a complex analytical query
-- Your code here:


-- TODO: Execute on Medium warehouse
-- Run the same query
-- Your code here:


-- TODO: Execute on Large warehouse
-- Run the same query
-- Your code here:


-- TODO: Document timing results
-- Create a comparison table to store results
-- Your code here:


-- ============================================================================
-- TASK 4: Configure Auto-Suspend and Auto-Resume (15 points)
-- ============================================================================
-- Optimize warehouse configuration to reduce costs while maintaining
-- performance for different workload patterns.
-- ============================================================================

-- TODO: Configure aggressive auto-suspend for development warehouse
-- Suspend after 1 minute of inactivity
-- Your code here:


-- TODO: Configure moderate auto-suspend for production warehouse
-- Suspend after 5 minutes of inactivity
-- Your code here:


-- TODO: Test auto-suspend behavior
-- Run a query, wait, and verify warehouse suspends
-- Your code here:


-- ============================================================================
-- TASK 5: Implement Multi-Cluster Warehouse (15 points)
-- ============================================================================
-- Configure a multi-cluster warehouse to handle concurrent workloads
-- efficiently with automatic scaling.
-- ============================================================================

-- TODO: Create multi-cluster warehouse
-- Configure with MIN_CLUSTER_COUNT = 1, MAX_CLUSTER_COUNT = 3
-- Use SCALING_POLICY = STANDARD
-- Your code here:


-- TODO: Configure scaling parameters
-- Set appropriate auto-suspend time
-- Your code here:


-- ============================================================================
-- TASK 6: Monitor Credit Usage and Costs (10 points)
-- ============================================================================
-- Query Snowflake's metadata to understand warehouse credit consumption
-- and calculate costs.
-- ============================================================================

-- TODO: Query warehouse metering history
-- Show credit consumption by warehouse for the last 7 days
-- Your code here:


-- TODO: Calculate estimated costs
-- Assuming $2 per credit for Enterprise Edition
-- Your code here:


-- TODO: Identify top cost drivers
-- Find warehouses with highest credit consumption
-- Your code here:


-- ============================================================================
-- OPTIMIZATION STRATEGIES DOCUMENTATION
-- ============================================================================
-- Document your optimization strategies and expected savings below:
--
-- Strategy 1: _______________________________________________________________
-- Expected Savings: _________________________________________________________
-- Implementation: ___________________________________________________________
--
-- Strategy 2: _______________________________________________________________
-- Expected Savings: _________________________________________________________
-- Implementation: ___________________________________________________________
--
-- Strategy 3: _______________________________________________________________
-- Expected Savings: _________________________________________________________
-- Implementation: ___________________________________________________________
--
-- Strategy 4: _______________________________________________________________
-- Expected Savings: _________________________________________________________
-- Implementation: ___________________________________________________________
--
-- Strategy 5: _______________________________________________________________
-- Expected Savings: _________________________________________________________
-- Implementation: ___________________________________________________________
-- ============================================================================

-- ============================================================================
-- CLEANUP (Optional)
-- ============================================================================
-- Uncomment to remove exercise resources

-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_XSMALL;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_MEDIUM;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_LARGE;
-- DROP WAREHOUSE IF EXISTS COMPUTE_WH_MULTI;
-- DROP DATABASE IF EXISTS warehouse_optimization_db;

-- ============================================================================
-- END OF EXERCISE
-- ============================================================================
