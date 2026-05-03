-- ============================================================================
-- Exercise 05: Snowpipe Automated Ingestion
-- Complete Solution
-- ============================================================================
-- OBJECTIVE: Implement automated data ingestion using Snowpipe
-- This solution demonstrates production-grade Snowpipe configuration
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- Create database for ingestion exercise
CREATE DATABASE IF NOT EXISTS INGESTION_LAB
    COMMENT = 'Laboratory for Snowpipe automated ingestion';

-- Create schema for IoT data
CREATE SCHEMA IF NOT EXISTS INGESTION_LAB.IOT_DATA
    COMMENT = 'Schema for IoT sensor data ingestion';

USE SCHEMA INGESTION_LAB.IOT_DATA;

-- Step 2: Create External Stage (S3)
-- ============================================================================
-- Option 1: Using AWS credentials directly (for training)
-- IMPORTANT: In production, use Storage Integration for security
CREATE OR REPLACE STAGE s3_stage
    URL = 's3://training-bucket/iot-data/'
    CREDENTIALS = (
        AWS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
        AWS_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    )
    COMMENT = 'External stage for S3 IoT data (training example)';

-- Option 2: Using Storage Integration (recommended for production)
-- First create storage integration (requires ACCOUNTADMIN):
/*
CREATE STORAGE INTEGRATION s3_int
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://training-bucket/iot-data/');

-- Then create stage using integration:
CREATE OR REPLACE STAGE s3_stage
    URL = 's3://training-bucket/iot-data/'
    STORAGE_INTEGRATION = s3_int;
*/

-- List files in the stage to verify connection
LIST @s3_stage;

-- Check stage properties
SHOW STAGES LIKE 's3_stage';

-- Step 3: Create File Format
-- ============================================================================
-- Create JSON file format for IoT sensor data
CREATE OR REPLACE FILE FORMAT json_format
    TYPE = 'JSON'
    COMPRESSION = 'AUTO'
    STRIP_OUTER_ARRAY = TRUE
    DATE_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO'
    TRIM_SPACE = TRUE
    STRIP_NULL_VALUES = FALSE
    COMMENT = 'JSON format for IoT sensor data';

-- Test file format by querying sample file
SELECT
    $1:sensor_id::VARCHAR AS sensor_id,
    $1:timestamp::TIMESTAMP_NTZ AS timestamp,
    $1:temperature::DOUBLE AS temperature,
    $1:humidity::DOUBLE AS humidity,
    $1:location AS location,
    METADATA$FILENAME AS source_file,
    METADATA$FILE_ROW_NUMBER AS file_row_number
FROM @s3_stage
(FILE_FORMAT => json_format)
LIMIT 10;

-- Step 4: Create Target Table
-- ============================================================================
-- Create sensor_data table with appropriate schema
CREATE OR REPLACE TABLE sensor_data (
    SENSOR_ID VARCHAR(50) NOT NULL,
    TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    TEMPERATURE DOUBLE,
    HUMIDITY DOUBLE,
    LOCATION VARIANT,
    SOURCE_FILE VARCHAR(500),
    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_sensor_data PRIMARY KEY (SENSOR_ID, TIMESTAMP)
) COMMENT = 'IoT sensor data ingested via Snowpipe';

-- Create indexes for common queries
CREATE INDEX idx_sensor_timestamp ON sensor_data(SENSOR_ID, TIMESTAMP);

-- Step 5: Create Snowpipe
-- ============================================================================
-- Create pipe with AUTO_INGEST enabled
CREATE OR REPLACE PIPE sensor_pipe
    AUTO_INGEST = TRUE
    AWS_SNS_TOPIC = 'arn:aws:sns:us-east-1:123456789012:snowpipe-topic'
    COMMENT = 'Automated ingestion pipe for IoT sensor data'
AS
COPY INTO sensor_data (
    SENSOR_ID,
    TIMESTAMP,
    TEMPERATURE,
    HUMIDITY,
    LOCATION,
    SOURCE_FILE
)
FROM (
    SELECT
        $1:sensor_id::VARCHAR,
        $1:timestamp::TIMESTAMP_NTZ,
        $1:temperature::DOUBLE,
        $1:humidity::DOUBLE,
        $1:location,
        METADATA$FILENAME
    FROM @s3_stage
)
FILE_FORMAT = json_format
PATTERN = '.*sensor.*[.]json'
ON_ERROR = 'CONTINUE';

-- Get pipe notification channel for S3 event configuration
SHOW PIPES LIKE 'sensor_pipe';

-- The notification_channel value from above should be configured in S3
-- Example: arn:aws:sqs:us-east-1:123456789012:sf-snowpipe-AIDAIG26EXAMPLE-tHBzti6RneD3sFh209fjKH

-- Step 6: Manually Trigger Pipe (Testing)
-- ============================================================================
-- Manually refresh pipe to load existing files in stage
ALTER PIPE sensor_pipe REFRESH;

-- Check pipe status
SELECT SYSTEM$PIPE_STATUS('sensor_pipe') AS pipe_status;

-- Parse the JSON result for better readability
SELECT
    PARSE_JSON(SYSTEM$PIPE_STATUS('sensor_pipe')):executionState::VARCHAR AS execution_state,
    PARSE_JSON(SYSTEM$PIPE_STATUS('sensor_pipe')):pendingFileCount::INTEGER AS pending_files;

-- Verify data loaded into sensor_data table
SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT SENSOR_ID) AS unique_sensors,
    MIN(TIMESTAMP) AS earliest_reading,
    MAX(TIMESTAMP) AS latest_reading,
    MAX(INGESTION_TIME) AS last_ingestion
FROM sensor_data;

-- Sample data
SELECT * FROM sensor_data LIMIT 10;

-- Step 7: Monitor Pipe Activity
-- ============================================================================
-- Query pipe usage history (last 7 days)
SELECT
    PIPE_NAME,
    TO_DATE(START_TIME) AS load_date,
    SUM(FILES_INSERTED) AS total_files,
    SUM(BYTES_INSERTED) AS total_bytes,
    ROUND(SUM(BYTES_INSERTED) / 1024 / 1024 / 1024, 2) AS total_gb,
    SUM(CREDITS_USED) AS total_credits,
    MAX(END_TIME) AS last_load_time
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME = 'SENSOR_PIPE'
    AND START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY PIPE_NAME, TO_DATE(START_TIME)
ORDER BY load_date DESC;

-- Query copy history for detailed file-level information
SELECT
    FILE_NAME,
    TABLE_NAME,
    STATUS,
    ROW_COUNT,
    ROW_PARSED,
    ERROR_COUNT,
    ERROR_LIMIT,
    FIRST_ERROR_MESSAGE,
    LAST_LOAD_TIME
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
))
ORDER BY LAST_LOAD_TIME DESC
LIMIT 100;

-- Check for any load errors
SELECT
    FILE_NAME,
    ERROR_COUNT,
    FIRST_ERROR_MESSAGE,
    LAST_LOAD_TIME
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
))
WHERE STATUS = 'LOAD_FAILED' OR ERROR_COUNT > 0
ORDER BY LAST_LOAD_TIME DESC;

-- Step 8: Cost Analysis
-- ============================================================================
-- Calculate Snowpipe costs (0.06 credits per 1,000 files)
SELECT
    'Snowpipe Cost Analysis' AS report_title,
    SUM(FILES_INSERTED) AS total_files_loaded,
    ROUND(SUM(FILES_INSERTED) / 1000.0 * 0.06, 4) AS snowpipe_credits,
    ROUND(SUM(BYTES_INSERTED) / 1024 / 1024 / 1024, 2) AS total_gb_ingested,
    ROUND((SUM(FILES_INSERTED) / 1000.0 * 0.06) /
          NULLIF(SUM(BYTES_INSERTED) / 1024 / 1024 / 1024, 0), 6) AS credits_per_gb,
    ROUND(SUM(FILES_INSERTED) / 1000.0 * 0.06 * 3.00, 2) AS estimated_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME = 'SENSOR_PIPE'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP());

-- Detailed cost breakdown by day
SELECT
    TO_DATE(START_TIME) AS load_date,
    SUM(FILES_INSERTED) AS files_loaded,
    ROUND(SUM(BYTES_INSERTED) / 1024 / 1024 / 1024, 3) AS gb_loaded,
    ROUND(SUM(FILES_INSERTED) / 1000.0 * 0.06, 4) AS daily_credits,
    ROUND(SUM(FILES_INSERTED) / 1000.0 * 0.06 * 3.00, 2) AS daily_cost_usd
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME = 'SENSOR_PIPE'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY TO_DATE(START_TIME)
ORDER BY load_date DESC;

-- Compare Snowpipe vs Warehouse costs
SELECT
    'Cost Comparison' AS analysis,
    ROUND(SUM(FILES_INSERTED) / 1000.0 * 0.06, 4) AS snowpipe_credits,
    '0.20 - 0.50' AS estimated_warehouse_credits_range,
    '60-85% savings' AS cost_benefit
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME = 'SENSOR_PIPE'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP());

-- Step 9: Data Quality Validation
-- ============================================================================
-- Use VALIDATE function to check files without loading
SELECT
    METADATA$FILENAME AS file_name,
    METADATA$FILE_ROW_NUMBER AS row_number,
    $1 AS json_content
FROM @s3_stage
(FILE_FORMAT => json_format)
WHERE $1:sensor_id IS NULL
   OR $1:timestamp IS NULL
   OR $1:temperature IS NULL
LIMIT 100;

-- Query sensor_data for basic statistics
SELECT
    SENSOR_ID,
    COUNT(*) AS reading_count,
    MIN(TIMESTAMP) AS first_reading,
    MAX(TIMESTAMP) AS last_reading,
    DATEDIFF(DAY, MIN(TIMESTAMP), MAX(TIMESTAMP)) AS days_active,
    AVG(TEMPERATURE) AS avg_temperature,
    AVG(HUMIDITY) AS avg_humidity,
    STDDEV(TEMPERATURE) AS temp_stddev
FROM sensor_data
GROUP BY SENSOR_ID
ORDER BY reading_count DESC;

-- Data completeness check
SELECT
    TO_DATE(TIMESTAMP) AS reading_date,
    COUNT(*) AS total_readings,
    COUNT(DISTINCT SENSOR_ID) AS active_sensors,
    SUM(CASE WHEN TEMPERATURE IS NULL THEN 1 ELSE 0 END) AS missing_temp,
    SUM(CASE WHEN HUMIDITY IS NULL THEN 1 ELSE 0 END) AS missing_humidity,
    ROUND(100.0 * SUM(CASE WHEN TEMPERATURE IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS temp_null_pct
FROM sensor_data
GROUP BY TO_DATE(TIMESTAMP)
ORDER BY reading_date DESC
LIMIT 30;

-- Check for duplicate records
SELECT
    SENSOR_ID,
    TIMESTAMP,
    COUNT(*) AS duplicate_count
FROM sensor_data
GROUP BY SENSOR_ID, TIMESTAMP
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Identify anomalies (outlier detection)
WITH stats AS (
    SELECT
        AVG(TEMPERATURE) AS avg_temp,
        STDDEV(TEMPERATURE) AS stddev_temp
    FROM sensor_data
)
SELECT
    sd.SENSOR_ID,
    sd.TIMESTAMP,
    sd.TEMPERATURE,
    ABS(sd.TEMPERATURE - s.avg_temp) / s.stddev_temp AS z_score
FROM sensor_data sd, stats s
WHERE ABS(sd.TEMPERATURE - s.avg_temp) / s.stddev_temp > 3
ORDER BY z_score DESC
LIMIT 50;

-- Step 10: Advanced Monitoring Queries
-- ============================================================================
-- Create view for pipe monitoring dashboard
CREATE OR REPLACE VIEW pipe_monitoring_dashboard AS
SELECT
    TO_DATE(START_TIME) AS load_date,
    PIPE_NAME,
    SUM(FILES_INSERTED) AS files_loaded,
    SUM(CASE WHEN ERROR_SEEN THEN 1 ELSE 0 END) AS files_with_errors,
    ROUND(100.0 * SUM(CASE WHEN ERROR_SEEN THEN 1 ELSE 0 END) /
          NULLIF(SUM(FILES_INSERTED), 0), 2) AS error_rate_pct,
    ROUND(SUM(BYTES_INSERTED) / 1024 / 1024, 2) AS mb_loaded,
    ROUND(SUM(CREDITS_USED), 4) AS credits_used,
    AVG(DATEDIFF(SECOND, START_TIME, END_TIME)) AS avg_latency_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE PIPE_NAME = 'SENSOR_PIPE'
    AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY TO_DATE(START_TIME), PIPE_NAME;

-- Query the dashboard
SELECT * FROM pipe_monitoring_dashboard ORDER BY load_date DESC;

-- Query to identify slow-loading files
SELECT
    FILE_NAME,
    ROW_COUNT,
    FILE_SIZE,
    LAST_LOAD_TIME,
    DATEDIFF(SECOND, LAST_LOAD_TIME, CURRENT_TIMESTAMP()) AS seconds_since_load,
    ROUND(FILE_SIZE / 1024 / 1024, 2) AS file_size_mb,
    ROUND(ROW_COUNT / NULLIF(FILE_SIZE / 1024 / 1024, 0), 0) AS rows_per_mb
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
))
WHERE FILE_SIZE > 10485760  -- Files > 10MB
ORDER BY FILE_SIZE DESC
LIMIT 20;

-- Alert query for high error rate (> 5%)
WITH error_summary AS (
    SELECT
        TO_DATE(LAST_LOAD_TIME) AS load_date,
        COUNT(*) AS total_files,
        SUM(CASE WHEN STATUS = 'LOAD_FAILED' OR ERROR_COUNT > 0 THEN 1 ELSE 0 END) AS failed_files,
        ROUND(100.0 * SUM(CASE WHEN STATUS = 'LOAD_FAILED' OR ERROR_COUNT > 0 THEN 1 ELSE 0 END) /
              COUNT(*), 2) AS error_rate_pct
    FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
        TABLE_NAME => 'SENSOR_DATA',
        START_TIME => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
    ))
    GROUP BY TO_DATE(LAST_LOAD_TIME)
)
SELECT
    load_date,
    total_files,
    failed_files,
    error_rate_pct,
    CASE
        WHEN error_rate_pct > 5 THEN '🚨 ALERT: High error rate!'
        WHEN error_rate_pct > 2 THEN '⚠️  WARNING: Elevated errors'
        ELSE '✓ OK'
    END AS status
FROM error_summary
WHERE error_rate_pct > 0
ORDER BY load_date DESC;

-- Ingestion lag monitoring
SELECT
    SENSOR_ID,
    MAX(TIMESTAMP) AS last_reading_time,
    MAX(INGESTION_TIME) AS last_ingestion_time,
    DATEDIFF(MINUTE, MAX(TIMESTAMP), CURRENT_TIMESTAMP()) AS minutes_since_reading,
    DATEDIFF(MINUTE, MAX(INGESTION_TIME), CURRENT_TIMESTAMP()) AS minutes_since_ingestion,
    CASE
        WHEN DATEDIFF(MINUTE, MAX(INGESTION_TIME), CURRENT_TIMESTAMP()) > 60
        THEN '⚠️  Ingestion delayed'
        ELSE '✓ Current'
    END AS ingestion_status
FROM sensor_data
GROUP BY SENSOR_ID
ORDER BY minutes_since_ingestion DESC;

-- ============================================================================
-- Performance Optimization Tips
-- ============================================================================
-- 1. Use PATTERN to filter files for better performance
-- 2. Set appropriate ON_ERROR handling (CONTINUE vs ABORT_STATEMENT)
-- 3. Consider partitioning large tables by date
-- 4. Use clustering keys for frequently queried columns
-- 5. Monitor and optimize file sizes (100-250MB recommended)
-- 6. Use column-level statistics for query optimization

-- Example: Add clustering to improve query performance
ALTER TABLE sensor_data CLUSTER BY (SENSOR_ID, TO_DATE(TIMESTAMP));

-- ============================================================================
-- S3 Event Notification Setup (Documentation)
-- ============================================================================
/*
To enable AUTO_INGEST, configure S3 bucket event notifications:

1. Get notification channel from Snowflake:
   SHOW PIPES LIKE 'sensor_pipe';
   -- Note the 'notification_channel' value (SQS ARN)

2. In AWS Console:
   - Navigate to S3 bucket: training-bucket
   - Properties → Event notifications → Create event notification
   - Name: snowflake-sensor-pipe-events
   - Event types: ✓ All object create events (s3:ObjectCreated:*)
   - Prefix: iot-data/
   - Suffix: .json
   - Destination: SQS Queue
   - SQS Queue: Select/paste Snowflake notification_channel ARN

3. Test:
   - Upload a test JSON file to s3://training-bucket/iot-data/
   - Should automatically trigger Snowpipe within seconds
   - Verify with SELECT SYSTEM$PIPE_STATUS('sensor_pipe')

4. Monitoring:
   - CloudWatch logs for S3 events
   - Snowflake COPY_HISTORY for load status
   - PIPE_USAGE_HISTORY for costs
*/

-- ============================================================================
-- Complete - Exercise 05 Solution Implemented Successfully
-- ============================================================================
