-- ============================================================================
-- Exercise 04: Change Data Capture with Streams and Tasks
-- Complete Solution
-- ============================================================================
-- OBJECTIVE: Implement CDC pipeline using Snowflake Streams and Tasks
-- This solution demonstrates production-grade CDC implementation
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- Create database for CDC exercise
CREATE DATABASE IF NOT EXISTS CDC_LAB
    COMMENT = 'Change Data Capture laboratory for streams and tasks';

-- Create schema for pipeline objects
CREATE SCHEMA IF NOT EXISTS CDC_LAB.PIPELINE
    COMMENT = 'CDC pipeline schema containing bronze, silver, gold layers';

USE SCHEMA CDC_LAB.PIPELINE;

-- Step 2: Source Table Setup (Bronze Layer)
-- ============================================================================
-- Create bronze_orders table (source system data)
CREATE OR REPLACE TABLE bronze_orders (
    ORDER_ID NUMBER AUTOINCREMENT,
    CUSTOMER_ID VARCHAR(50) NOT NULL,
    PRODUCT VARCHAR(100) NOT NULL,
    AMOUNT NUMBER(10,2) NOT NULL,
    STATUS VARCHAR(20) DEFAULT 'PENDING',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_bronze_orders PRIMARY KEY (ORDER_ID)
) COMMENT = 'Bronze layer: Raw order data from source system';

-- Insert initial sample data (1000 orders)
INSERT INTO bronze_orders (CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT)
SELECT
    'CUST_' || LPAD(ABS(MOD(SEQ4(), 100)), 5, '0') AS CUSTOMER_ID,
    CASE ABS(MOD(SEQ4(), 8))
        WHEN 0 THEN 'Laptop Pro 15'
        WHEN 1 THEN 'Wireless Mouse'
        WHEN 2 THEN 'USB-C Hub'
        WHEN 3 THEN 'Mechanical Keyboard'
        WHEN 4 THEN '27" Monitor'
        WHEN 5 THEN 'Webcam HD'
        WHEN 6 THEN 'Desk Lamp LED'
        ELSE 'Office Chair'
    END AS PRODUCT,
    ROUND(UNIFORM(10, 500, RANDOM()), 2) AS AMOUNT,
    CASE ABS(MOD(SEQ4(), 10))
        WHEN 0 THEN 'PENDING'
        WHEN 1 THEN 'PROCESSING'
        WHEN 2 THEN 'COMPLETED'
        WHEN 3 THEN 'SHIPPED'
        ELSE 'PENDING'
    END AS STATUS,
    DATEADD(SECOND,
            -UNIFORM(1, 2592000, RANDOM()),
            CURRENT_TIMESTAMP()) AS CREATED_AT
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- Verify initial data load
SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT CUSTOMER_ID) AS unique_customers,
    SUM(AMOUNT) AS total_revenue,
    MIN(CREATED_AT) AS earliest_order,
    MAX(CREATED_AT) AS latest_order
FROM bronze_orders;

-- Step 3: Create Stream for Change Tracking
-- ============================================================================
-- Create stream on bronze_orders to capture all changes
CREATE OR REPLACE STREAM orders_stream
ON TABLE bronze_orders
APPEND_ONLY = FALSE
SHOW_INITIAL_ROWS = FALSE
COMMENT = 'Stream to capture INSERT, UPDATE, DELETE on bronze_orders';

-- Query stream metadata structure
-- Note: Stream is empty until changes occur
SELECT
    SYSTEM$STREAM_HAS_DATA('orders_stream') AS has_data,
    'Stream created successfully - waiting for changes' AS status;

-- Describe stream structure to see metadata columns
DESC STREAM orders_stream;

-- Step 4: Generate Sample Changes
-- ============================================================================
-- Insert 100 new orders
INSERT INTO bronze_orders (CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT)
SELECT
    'CUST_' || LPAD(ABS(MOD(SEQ4(), 100)), 5, '0') AS CUSTOMER_ID,
    CASE ABS(MOD(SEQ4(), 5))
        WHEN 0 THEN 'Phone Case'
        WHEN 1 THEN 'Screen Protector'
        WHEN 2 THEN 'Charging Cable'
        WHEN 3 THEN 'Power Bank'
        ELSE 'Bluetooth Speaker'
    END AS PRODUCT,
    ROUND(UNIFORM(15, 350, RANDOM()), 2) AS AMOUNT,
    'PENDING' AS STATUS,
    CURRENT_TIMESTAMP() AS CREATED_AT
FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- Update 50 existing orders (mark as completed)
UPDATE bronze_orders
SET STATUS = 'COMPLETED'
WHERE ORDER_ID IN (
    SELECT ORDER_ID
    FROM bronze_orders
    WHERE STATUS = 'PENDING'
    LIMIT 50
);

-- Delete 20 orders (cancelled orders)
DELETE FROM bronze_orders
WHERE ORDER_ID IN (
    SELECT ORDER_ID
    FROM bronze_orders
    WHERE STATUS = 'PENDING'
    LIMIT 20
);

-- Query stream to see captured changes
SELECT
    METADATA$ACTION AS action_type,
    METADATA$ISUPDATE AS is_update,
    METADATA$ROW_ID AS row_id,
    ORDER_ID,
    CUSTOMER_ID,
    PRODUCT,
    AMOUNT,
    STATUS,
    CREATED_AT
FROM orders_stream
ORDER BY METADATA$ACTION, ORDER_ID
LIMIT 20;

-- Count changes by type
SELECT
    METADATA$ACTION AS action_type,
    COUNT(*) AS change_count
FROM orders_stream
GROUP BY METADATA$ACTION
ORDER BY action_type;

-- Step 5: Manual Stream Consumption
-- ============================================================================
-- Create silver_orders table (transformed layer)
CREATE OR REPLACE TABLE silver_orders (
    ORDER_ID NUMBER NOT NULL,
    CUSTOMER_ID VARCHAR(50) NOT NULL,
    PRODUCT VARCHAR(100) NOT NULL,
    AMOUNT NUMBER(10,2) NOT NULL,
    STATUS VARCHAR(20) NOT NULL,
    CREATED_AT TIMESTAMP_NTZ NOT NULL,
    UPDATED_AT TIMESTAMP_NTZ NOT NULL,
    IS_DELETED BOOLEAN DEFAULT FALSE,
    CONSTRAINT pk_silver_orders PRIMARY KEY (ORDER_ID)
) COMMENT = 'Silver layer: Transformed orders with CDC tracking';

-- Consume stream and load into silver_orders
MERGE INTO silver_orders AS target
USING (
    SELECT
        ORDER_ID,
        CUSTOMER_ID,
        PRODUCT,
        AMOUNT,
        STATUS,
        CREATED_AT,
        CURRENT_TIMESTAMP() AS UPDATED_AT,
        METADATA$ACTION,
        METADATA$ISUPDATE
    FROM orders_stream
) AS source
ON target.ORDER_ID = source.ORDER_ID
WHEN MATCHED AND source.METADATA$ACTION = 'DELETE' THEN
    UPDATE SET
        IS_DELETED = TRUE,
        UPDATED_AT = CURRENT_TIMESTAMP()
WHEN MATCHED AND source.METADATA$ACTION = 'INSERT' AND source.METADATA$ISUPDATE = TRUE THEN
    UPDATE SET
        CUSTOMER_ID = source.CUSTOMER_ID,
        PRODUCT = source.PRODUCT,
        AMOUNT = source.AMOUNT,
        STATUS = source.STATUS,
        UPDATED_AT = CURRENT_TIMESTAMP()
WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT' THEN
    INSERT (ORDER_ID, CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT, UPDATED_AT, IS_DELETED)
    VALUES (source.ORDER_ID, source.CUSTOMER_ID, source.PRODUCT, source.AMOUNT,
            source.STATUS, source.CREATED_AT, source.UPDATED_AT, FALSE);

-- Verify stream is now empty (changes consumed)
SELECT
    SYSTEM$STREAM_HAS_DATA('orders_stream') AS has_data,
    COUNT(*) AS remaining_records
FROM orders_stream;

-- Verify silver_orders data
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN IS_DELETED THEN 1 ELSE 0 END) AS deleted_count,
    SUM(CASE WHEN NOT IS_DELETED THEN 1 ELSE 0 END) AS active_count
FROM silver_orders;

-- Step 6: Create Automated Task (Single Task)
-- ============================================================================
-- Create task to automatically process stream changes
CREATE OR REPLACE TASK process_to_silver
    WAREHOUSE = TRAINING_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
    AS
    MERGE INTO silver_orders AS target
    USING (
        SELECT
            ORDER_ID,
            CUSTOMER_ID,
            PRODUCT,
            AMOUNT,
            STATUS,
            CREATED_AT,
            CURRENT_TIMESTAMP() AS UPDATED_AT,
            METADATA$ACTION,
            METADATA$ISUPDATE
        FROM orders_stream
    ) AS source
    ON target.ORDER_ID = source.ORDER_ID
    WHEN MATCHED AND source.METADATA$ACTION = 'DELETE' THEN
        UPDATE SET
            IS_DELETED = TRUE,
            UPDATED_AT = CURRENT_TIMESTAMP()
    WHEN MATCHED AND source.METADATA$ACTION = 'INSERT' AND source.METADATA$ISUPDATE = TRUE THEN
        UPDATE SET
            CUSTOMER_ID = source.CUSTOMER_ID,
            PRODUCT = source.PRODUCT,
            AMOUNT = source.AMOUNT,
            STATUS = source.STATUS,
            UPDATED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT' THEN
        INSERT (ORDER_ID, CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT, UPDATED_AT, IS_DELETED)
        VALUES (source.ORDER_ID, source.CUSTOMER_ID, source.PRODUCT, source.AMOUNT,
                source.STATUS, source.CREATED_AT, source.UPDATED_AT, FALSE);

-- Resume task to activate it
ALTER TASK process_to_silver RESUME;

-- Verify task is running
SHOW TASKS LIKE 'process_to_silver';

-- Generate more changes to test task execution
INSERT INTO bronze_orders (CUSTOMER_ID, PRODUCT, AMOUNT, STATUS)
SELECT
    'CUST_' || LPAD(ABS(MOD(SEQ4(), 100)), 5, '0'),
    'Test Product ' || SEQ4(),
    ROUND(UNIFORM(20, 200, RANDOM()), 2),
    'PENDING'
FROM TABLE(GENERATOR(ROWCOUNT => 50));

-- Check task execution history (wait 5-10 minutes for first run)
SELECT
    NAME AS task_name,
    SCHEDULED_TIME,
    COMPLETED_TIME,
    STATE,
    ERROR_CODE,
    ERROR_MESSAGE,
    DATEDIFF(SECOND, SCHEDULED_TIME, COMPLETED_TIME) AS duration_seconds
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD(HOUR, -1, CURRENT_TIMESTAMP()),
    TASK_NAME => 'PROCESS_TO_SILVER'
))
ORDER BY SCHEDULED_TIME DESC
LIMIT 10;

-- Step 7: Build Task DAG Pipeline (Bronze -> Silver -> Gold)
-- ============================================================================
-- Create gold_daily_sales table for aggregated metrics
CREATE OR REPLACE TABLE gold_daily_sales (
    SALE_DATE DATE NOT NULL,
    TOTAL_ORDERS NUMBER NOT NULL,
    TOTAL_REVENUE NUMBER(18,2) NOT NULL,
    AVG_ORDER_VALUE NUMBER(10,2),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_gold_daily_sales PRIMARY KEY (SALE_DATE)
) COMMENT = 'Gold layer: Daily sales aggregations';

-- Suspend existing task before rebuilding pipeline
ALTER TASK IF EXISTS process_to_silver SUSPEND;

-- Create root task: extract_from_bronze
CREATE OR REPLACE TASK extract_from_bronze
    WAREHOUSE = TRAINING_WH
    SCHEDULE = '10 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
    COMMENT = 'Root task: Extract changes from bronze layer stream'
    AS
    -- Stage changes in temporary staging table
    CREATE OR REPLACE TEMPORARY TABLE stage_orders AS
    SELECT
        ORDER_ID,
        CUSTOMER_ID,
        PRODUCT,
        AMOUNT,
        STATUS,
        CREATED_AT,
        METADATA$ACTION,
        METADATA$ISUPDATE
    FROM orders_stream;

-- Create child task: transform_to_silver
CREATE OR REPLACE TASK transform_to_silver
    WAREHOUSE = TRAINING_WH
    AFTER extract_from_bronze
    COMMENT = 'Child task: Transform and load to silver layer'
    AS
    MERGE INTO silver_orders AS target
    USING (
        SELECT
            ORDER_ID,
            CUSTOMER_ID,
            PRODUCT,
            AMOUNT,
            STATUS,
            CREATED_AT,
            CURRENT_TIMESTAMP() AS UPDATED_AT,
            METADATA$ACTION,
            METADATA$ISUPDATE
        FROM stage_orders
    ) AS source
    ON target.ORDER_ID = source.ORDER_ID
    WHEN MATCHED AND source.METADATA$ACTION = 'DELETE' THEN
        UPDATE SET
            IS_DELETED = TRUE,
            UPDATED_AT = CURRENT_TIMESTAMP()
    WHEN MATCHED AND source.METADATA$ACTION = 'INSERT' AND source.METADATA$ISUPDATE = TRUE THEN
        UPDATE SET
            CUSTOMER_ID = source.CUSTOMER_ID,
            PRODUCT = source.PRODUCT,
            AMOUNT = source.AMOUNT,
            STATUS = source.STATUS,
            UPDATED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT' THEN
        INSERT (ORDER_ID, CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT, UPDATED_AT, IS_DELETED)
        VALUES (source.ORDER_ID, source.CUSTOMER_ID, source.PRODUCT, source.AMOUNT,
                source.STATUS, source.CREATED_AT, source.UPDATED_AT, FALSE);

-- Create final task: aggregate_to_gold
CREATE OR REPLACE TASK aggregate_to_gold
    WAREHOUSE = TRAINING_WH
    AFTER transform_to_silver
    COMMENT = 'Final task: Aggregate metrics to gold layer'
    AS
    MERGE INTO gold_daily_sales AS target
    USING (
        SELECT
            DATE(CREATED_AT) AS SALE_DATE,
            COUNT(*) AS TOTAL_ORDERS,
            SUM(AMOUNT) AS TOTAL_REVENUE,
            AVG(AMOUNT) AS AVG_ORDER_VALUE
        FROM silver_orders
        WHERE NOT IS_DELETED
            AND DATE(CREATED_AT) >= DATEADD(DAY, -7, CURRENT_DATE())
        GROUP BY DATE(CREATED_AT)
    ) AS source
    ON target.SALE_DATE = source.SALE_DATE
    WHEN MATCHED THEN
        UPDATE SET
            TOTAL_ORDERS = source.TOTAL_ORDERS,
            TOTAL_REVENUE = source.TOTAL_REVENUE,
            AVG_ORDER_VALUE = source.AVG_ORDER_VALUE,
            UPDATED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (SALE_DATE, TOTAL_ORDERS, TOTAL_REVENUE, AVG_ORDER_VALUE, UPDATED_AT)
        VALUES (source.SALE_DATE, source.TOTAL_ORDERS, source.TOTAL_REVENUE,
                source.AVG_ORDER_VALUE, CURRENT_TIMESTAMP());

-- Resume tasks in correct order (child to parent)
ALTER TASK aggregate_to_gold RESUME;
ALTER TASK transform_to_silver RESUME;
ALTER TASK extract_from_bronze RESUME;

-- Verify task DAG
SELECT
    NAME,
    STATE,
    SCHEDULE,
    PREDECESSORS,
    CONDITION
FROM TABLE(INFORMATION_SCHEMA.TASK_DEPENDENTS(
    TASK_NAME => 'CDC_LAB.PIPELINE.EXTRACT_FROM_BRONZE',
    RECURSIVE => TRUE
))
ORDER BY NAME;

-- Step 8: Error Handling Implementation
-- ============================================================================
-- Create error_log table
CREATE OR REPLACE TABLE error_log (
    ERROR_ID NUMBER AUTOINCREMENT,
    TASK_NAME VARCHAR(200),
    ERROR_MESSAGE VARCHAR(5000),
    ERROR_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_error_log PRIMARY KEY (ERROR_ID)
) COMMENT = 'Error logging table for task failures';

-- Create task with error handling (example)
CREATE OR REPLACE TASK transform_to_silver_with_error_handling
    WAREHOUSE = TRAINING_WH
    AFTER extract_from_bronze
    COMMENT = 'Transform task with error handling'
    AS
    BEGIN
        -- Main transformation logic
        MERGE INTO silver_orders AS target
        USING (
            SELECT
                ORDER_ID,
                CUSTOMER_ID,
                PRODUCT,
                AMOUNT,
                STATUS,
                CREATED_AT,
                CURRENT_TIMESTAMP() AS UPDATED_AT,
                METADATA$ACTION,
                METADATA$ISUPDATE
            FROM stage_orders
        ) AS source
        ON target.ORDER_ID = source.ORDER_ID
        WHEN MATCHED AND source.METADATA$ACTION = 'DELETE' THEN
            UPDATE SET
                IS_DELETED = TRUE,
                UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN MATCHED AND source.METADATA$ACTION = 'INSERT' AND source.METADATA$ISUPDATE = TRUE THEN
            UPDATE SET
                CUSTOMER_ID = source.CUSTOMER_ID,
                PRODUCT = source.PRODUCT,
                AMOUNT = source.AMOUNT,
                STATUS = source.STATUS,
                UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT' THEN
            INSERT (ORDER_ID, CUSTOMER_ID, PRODUCT, AMOUNT, STATUS, CREATED_AT, UPDATED_AT, IS_DELETED)
            VALUES (source.ORDER_ID, source.CUSTOMER_ID, source.PRODUCT, source.AMOUNT,
                    source.STATUS, source.CREATED_AT, source.UPDATED_AT, FALSE);
    EXCEPTION
        WHEN OTHER THEN
            -- Log error to error_log table
            INSERT INTO error_log (TASK_NAME, ERROR_MESSAGE)
            VALUES ('transform_to_silver', SQLERRM);
            -- Re-raise exception for task to show as failed
            RAISE;
    END;

-- Step 9: Monitoring and Observability
-- ============================================================================
-- Query to show all tasks and their status
SELECT
    NAME AS task_name,
    DATABASE_NAME,
    SCHEMA_NAME,
    STATE,
    SCHEDULE,
    CONDITION,
    WAREHOUSE,
    COMMENT
FROM INFORMATION_SCHEMA.TASKS
WHERE SCHEMA_NAME = 'PIPELINE'
ORDER BY NAME;

-- Query task execution history (last 10 runs)
SELECT
    NAME AS task_name,
    DATABASE_NAME || '.' || SCHEMA_NAME AS full_schema,
    SCHEDULED_TIME,
    COMPLETED_TIME,
    STATE,
    RETURN_VALUE,
    ERROR_CODE,
    ERROR_MESSAGE,
    DATEDIFF(SECOND, SCHEDULED_TIME, COMPLETED_TIME) AS duration_seconds
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD(DAY, -1, CURRENT_TIMESTAMP())
))
WHERE SCHEMA_NAME = 'PIPELINE'
ORDER BY SCHEDULED_TIME DESC
LIMIT 10;

-- Query stream metrics
SHOW STREAMS LIKE 'orders_stream';

SELECT
    SYSTEM$STREAM_HAS_DATA('orders_stream') AS has_pending_data,
    (SELECT COUNT(*) FROM orders_stream) AS pending_changes;

-- Calculate task credits consumed
SELECT
    NAME AS task_name,
    COUNT(*) AS execution_count,
    SUM(DATEDIFF(SECOND, SCHEDULED_TIME, COMPLETED_TIME)) AS total_seconds,
    ROUND(SUM(DATEDIFF(SECOND, SCHEDULED_TIME, COMPLETED_TIME)) / 3600.0, 4) AS compute_hours
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
))
WHERE SCHEMA_NAME = 'PIPELINE' AND STATE = 'SUCCEEDED'
GROUP BY NAME
ORDER BY total_seconds DESC;

-- Step 10: Validation Queries
-- ============================================================================
-- Verify data consistency across layers
SELECT
    'Bronze' AS layer,
    COUNT(*) AS record_count,
    SUM(AMOUNT) AS total_amount
FROM bronze_orders
UNION ALL
SELECT
    'Silver' AS layer,
    COUNT(*) AS record_count,
    SUM(AMOUNT) AS total_amount
FROM silver_orders
WHERE NOT IS_DELETED
UNION ALL
SELECT
    'Gold (Aggregated)' AS layer,
    SUM(TOTAL_ORDERS) AS record_count,
    SUM(TOTAL_REVENUE) AS total_amount
FROM gold_daily_sales;

-- Check gold aggregations accuracy
SELECT
    SALE_DATE,
    TOTAL_ORDERS,
    TOTAL_REVENUE,
    AVG_ORDER_VALUE,
    UPDATED_AT
FROM gold_daily_sales
ORDER BY SALE_DATE DESC
LIMIT 10;

-- ============================================================================
-- Summary Report
-- ============================================================================
SELECT
    '=== CDC Pipeline Summary ===' AS report_section;

SELECT
    'Stream Status' AS metric,
    SYSTEM$STREAM_HAS_DATA('orders_stream') AS value
UNION ALL
SELECT
    'Bronze Orders',
    COUNT(*)::VARCHAR
FROM bronze_orders
UNION ALL
SELECT
    'Silver Orders (Active)',
    COUNT(*)::VARCHAR
FROM silver_orders
WHERE NOT IS_DELETED
UNION ALL
SELECT
    'Silver Orders (Deleted)',
    COUNT(*)::VARCHAR
FROM silver_orders
WHERE IS_DELETED
UNION ALL
SELECT
    'Gold Daily Aggregates',
    COUNT(*)::VARCHAR
FROM gold_daily_sales;

-- ============================================================================
-- Complete - Exercise 04 Solution Implemented Successfully
-- ============================================================================
