-- ============================================================================
-- Exercise 04: Change Data Capture with Streams and Tasks
-- Starter Code
-- ============================================================================
-- OBJECTIVE: Implement CDC pipeline using Snowflake Streams and Tasks
-- - Set up source table with sample data
-- - Create stream to capture changes
-- - Build automated task pipeline
-- - Implement error handling and monitoring
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
-- TODO: Create database and schema for CDC exercise
-- Hint: USE appropriate database and schema naming conventions

USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- TODO: Create database CDC_LAB
-- YOUR CODE HERE:


-- TODO: Create schema PIPELINE
-- YOUR CODE HERE:


USE SCHEMA CDC_LAB.PIPELINE;


-- Step 2: Source Table Setup (Bronze Layer)
-- ============================================================================
-- TODO: Create bronze_orders table with following columns:
--   - ORDER_ID: Unique identifier (NUMBER)
--   - CUSTOMER_ID: Customer reference (VARCHAR 50)
--   - PRODUCT: Product name (VARCHAR 100)
--   - AMOUNT: Order amount (NUMBER 10,2)
--   - STATUS: Order status (VARCHAR 20)
--   - CREATED_AT: Timestamp (TIMESTAMP_NTZ)
-- YOUR CODE HERE:


-- TODO: Insert initial sample data (1000 orders)
-- Hint: Use GENERATOR with ROW_NUMBER() and random functions
-- Generate orders from last 30 days with random amounts $10-$500
-- YOUR CODE HERE:


-- TODO: Verify initial data load
-- YOUR CODE HERE:


-- Step 3: Create Stream for Change Tracking
-- ============================================================================
-- TODO: Create stream orders_stream on bronze_orders table
-- Stream should capture all DML operations (INSERT, UPDATE, DELETE)
-- YOUR CODE HERE:


-- TODO: Query stream metadata to understand structure
-- Hint: SELECT * FROM orders_stream LIMIT 5;
-- YOUR CODE HERE:


-- Step 4: Generate Sample Changes
-- ============================================================================
-- TODO: Insert 100 new orders
-- Use current timestamp and varied order amounts
-- YOUR CODE HERE:


-- TODO: Update 50 existing orders (change STATUS to 'COMPLETED')
-- Select random order IDs for update
-- YOUR CODE HERE:


-- TODO: Delete 20 orders (cancelled orders)
-- Select random order IDs for deletion
-- YOUR CODE HERE:


-- TODO: Query stream to see captured changes
-- Check how many INSERT, UPDATE, DELETE operations are captured
-- Hint: Use METADATA$ACTION and METADATA$ISUPDATE columns
-- YOUR CODE HERE:


-- Step 5: Manual Stream Consumption
-- ============================================================================
-- TODO: Create silver_orders table (transformed layer)
-- Include columns: ORDER_ID, CUSTOMER_ID, PRODUCT, AMOUNT, STATUS,
--                  CREATED_AT, UPDATED_AT, IS_DELETED
-- YOUR CODE HERE:


-- TODO: Consume stream and insert into silver_orders
-- Transform data:
--   - For INSERT: Copy all fields, set UPDATED_AT to CREATED_AT, IS_DELETED=FALSE
--   - For UPDATE: Copy all fields, set UPDATED_AT to CURRENT_TIMESTAMP(), IS_DELETED=FALSE
--   - For DELETE: Mark IS_DELETED=TRUE, set UPDATED_AT to CURRENT_TIMESTAMP()
-- YOUR CODE HERE:


-- TODO: Verify stream is now empty after consumption
-- YOUR CODE HERE:


-- Step 6: Create Automated Task (Single Task)
-- ============================================================================
-- TODO: Create task process_to_silver with following requirements:
--   - Schedule: Every 5 minutes
--   - Condition: Only run when stream has data (SYSTEM$STREAM_HAS_DATA)
--   - Action: Merge changes from stream into silver_orders
-- YOUR CODE HERE:


-- TODO: Resume the task to activate it
-- YOUR CODE HERE:


-- TODO: Generate more changes to test task execution
-- Insert 50 new orders
-- YOUR CODE HERE:


-- TODO: Wait and check task execution history
-- Hint: SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
-- YOUR CODE HERE:


-- Step 7: Build Task DAG Pipeline (Bronze -> Silver -> Gold)
-- ============================================================================
-- TODO: Create gold_daily_sales table for aggregated metrics
-- Columns: SALE_DATE (DATE), TOTAL_ORDERS (NUMBER), TOTAL_REVENUE (NUMBER 18,2),
--          UPDATED_AT (TIMESTAMP_NTZ)
-- YOUR CODE HERE:


-- TODO: Suspend existing process_to_silver task before modifying pipeline
-- YOUR CODE HERE:


-- TODO: Create root task: extract_from_bronze
-- Schedule: Every 10 minutes
-- Condition: Check stream has data
-- Action: Stage changes in temporary table or directly process
-- YOUR CODE HERE:


-- TODO: Create child task: transform_to_silver
-- No schedule (runs after parent)
-- AFTER extract_from_bronze
-- Action: Apply business transformations and load to silver
-- YOUR CODE HERE:


-- TODO: Create final task: aggregate_to_gold
-- AFTER transform_to_silver
-- Action: Calculate daily aggregations and update gold table
-- YOUR CODE HERE:


-- TODO: Resume all tasks in correct order (child to parent)
-- YOUR CODE HERE:


-- Step 8: Error Handling Implementation
-- ============================================================================
-- TODO: Create error_log table
-- Columns: ERROR_ID (autoincrement), TASK_NAME, ERROR_MESSAGE, ERROR_TIME
-- YOUR CODE HERE:


-- TODO: Modify task with error handling logic
-- Wrap main logic in TRY/CATCH equivalent
-- Log errors to error_log table
-- Consider using EXECUTE IMMEDIATE for dynamic error handling
-- YOUR CODE HERE:


-- Step 9: Monitoring and Observability
-- ============================================================================
-- TODO: Query to show all tasks and their status
-- YOUR CODE HERE:


-- TODO: Query to show task execution history (last 10 runs)
-- Include: task_name, scheduled_time, completed_time, state, error_message
-- YOUR CODE HERE:


-- TODO: Query to show stream metrics
-- Check: STALE status, current offset, table version
-- YOUR CODE HERE:


-- TODO: Calculate task credits consumed
-- Query TASK_HISTORY for credit consumption
-- YOUR CODE HERE:


-- Step 10: Advanced Scenarios
-- ============================================================================
-- TODO: Implement task with multiple streams
-- Create second stream on different table and process both
-- YOUR CODE HERE:


-- TODO: Implement conditional logic in task
-- Process different record types differently based on STATUS
-- YOUR CODE HERE:


-- TODO: Create task chain for SCD Type 2 implementation
-- Track historical changes in dedicated history table
-- YOUR CODE HERE:


-- Step 11: Testing and Validation
-- ============================================================================
-- TODO: Generate large batch of changes (10,000 records)
-- Test task performance and stream handling
-- YOUR CODE HERE:


-- TODO: Verify data consistency between layers
-- Compare record counts: bronze vs silver vs gold
-- YOUR CODE HERE:


-- TODO: Test task failure and recovery
-- Intentionally cause error and verify logging
-- YOUR CODE HERE:


-- Cleanup Commands (DO NOT RUN DURING EXERCISE)
-- ============================================================================
-- DROP TASK IF EXISTS aggregate_to_gold;
-- DROP TASK IF EXISTS transform_to_silver;
-- DROP TASK IF EXISTS extract_from_bronze;
-- DROP TASK IF EXISTS process_to_silver;
-- DROP STREAM IF EXISTS orders_stream;
-- DROP TABLE IF EXISTS error_log;
-- DROP TABLE IF EXISTS gold_daily_sales;
-- DROP TABLE IF EXISTS silver_orders;
-- DROP TABLE IF EXISTS bronze_orders;
-- DROP SCHEMA IF EXISTS CDC_LAB.PIPELINE;
-- DROP DATABASE IF EXISTS CDC_LAB;

-- ============================================================================
-- Validation Checklist
-- ============================================================================
-- [ ] Stream created and capturing changes correctly
-- [ ] Manual stream consumption working
-- [ ] Single task created with correct schedule
-- [ ] Task DAG with 3 tasks and proper dependencies
-- [ ] Error handling implemented
-- [ ] Monitoring queries returning expected results
-- [ ] Gold aggregations match source data
-- [ ] Task execution history shows successful runs
-- [ ] Stream offset advancing properly
-- [ ] No data loss during CDC process
-- ============================================================================
