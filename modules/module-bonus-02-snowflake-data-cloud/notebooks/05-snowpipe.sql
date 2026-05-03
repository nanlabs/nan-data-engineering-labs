-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 05: Snowpipe for Continuous Data Loading
-- ============================================================================
-- Description: Master Snowpipe for serverless, continuous data ingestion from
--              cloud storage (S3/Azure/GCS). Learn auto-ingest, manual refresh,
--              error handling, and cost optimization.
--
-- Prerequisites:
--   - Snowflake account with CREATE PIPE privilege
--   - Access to S3, Azure Blob, or GCS bucket
--   - Understanding of Snowflake stages and file formats
--   - Completed Streams and Tasks notebook
--
-- Estimated Time: 75 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Create Environment for Snowpipe
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Create dedicated warehouse (Snowpipe uses serverless compute, but we need warehouse for setup)
CREATE OR REPLACE WAREHOUSE snowpipe_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE snowpipe_wh;

-- Create database for Snowpipe experiments
CREATE OR REPLACE DATABASE snowpipe_lab;
USE DATABASE snowpipe_lab;

CREATE SCHEMA IF NOT EXISTS ingestion;
USE SCHEMA ingestion;

-- Note: Snowpipe itself does NOT use the warehouse - it uses serverless compute
-- The warehouse is only for running setup queries and manual operations


-- ============================================================================
-- SECTION 1: Create Target Tables
-- ============================================================================
-- Define tables for incoming data from cloud storage.
-- ============================================================================

-- Create sales transaction table
CREATE OR REPLACE TABLE sales (
    sale_id VARCHAR(50),
    transaction_date TIMESTAMP_NTZ,
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    category VARCHAR(50),
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    quantity NUMBER(10,0),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    payment_method VARCHAR(30),
    store_location VARCHAR(100),
    region VARCHAR(50),
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file VARCHAR(500)
);

-- Create table for JSON formatted data
CREATE OR REPLACE TABLE events (
    event_id VARCHAR(50),
    event_type VARCHAR(50),
    user_id VARCHAR(50),
    timestamp TIMESTAMP_NTZ,
    properties VARIANT,
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file VARCHAR(500)
);

-- Create table for CSV data
CREATE OR REPLACE TABLE customer_updates (
    customer_id VARCHAR(50),
    email VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(10),
    zip_code VARCHAR(10),
    update_timestamp TIMESTAMP_NTZ,
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file VARCHAR(500)
);

-- Create error tracking table
CREATE OR REPLACE TABLE load_errors (
    error_id NUMBER IDENTITY(1,1),
    file_name VARCHAR(500),
    error_message VARCHAR(5000),
    error_line_number NUMBER,
    error_character_position NUMBER,
    error_column VARCHAR(100),
    rejected_record VARCHAR(5000),
    detected_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);


-- ============================================================================
-- SECTION 2: Create External Stage
-- ============================================================================
-- External stages reference cloud storage locations (S3, Azure, GCS).
-- Snowpipe loads data from stages automatically.
-- ============================================================================

-- Create file format for JSON data
CREATE OR REPLACE FILE FORMAT json_format
    TYPE = 'JSON'
    COMPRESSION = 'AUTO'
    STRIP_OUTER_ARRAY = TRUE
    DATE_FORMAT = 'AUTO'
    TIME_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO';

-- Create file format for CSV data
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = 'CSV'
    COMPRESSION = 'AUTO'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    ESCAPE = 'NONE'
    ESCAPE_UNENCLOSED_FIELD = '\134'
    DATE_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO'
    NULL_IF = ('NULL', 'null', '');

-- Create file format for Parquet data
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = 'PARQUET'
    COMPRESSION = 'AUTO';


-- Option 1: S3 Stage with IAM Role (recommended for production)
-- Replace with your actual S3 bucket and IAM role ARN
CREATE OR REPLACE STAGE s3_sales_stage
    URL = 's3://your-bucket-name/sales/incoming/'
    CREDENTIALS = (AWS_ROLE = 'arn:aws:iam::123456789012:role/SnowflakeS3Access')
    FILE_FORMAT = json_format
    COMMENT = 'S3 stage for sales data ingestion';

-- Option 2: S3 Stage with Access Keys (less secure, for testing only)
/*
CREATE OR REPLACE STAGE s3_sales_stage
    URL = 's3://your-bucket-name/sales/incoming/'
    CREDENTIALS = (
        AWS_KEY_ID = 'YOUR_AWS_ACCESS_KEY'
        AWS_SECRET_KEY = 'YOUR_AWS_SECRET_KEY'
    )
    FILE_FORMAT = json_format;
*/

-- Option 3: Azure Blob Storage Stage
/*
CREATE OR REPLACE STAGE azure_sales_stage
    URL = 'azure://youraccount.blob.core.windows.net/container/path/'
    CREDENTIALS = (
        AZURE_SAS_TOKEN = 'your_sas_token'
    )
    FILE_FORMAT = json_format;
*/

-- Option 4: Google Cloud Storage Stage
/*
CREATE OR REPLACE STAGE gcs_sales_stage
    URL = 'gcs://your-bucket-name/sales/incoming/'
    STORAGE_INTEGRATION = gcs_integration
    FILE_FORMAT = json_format;
*/

-- For this tutorial, create internal stage for testing
CREATE OR REPLACE STAGE internal_sales_stage
    FILE_FORMAT = json_format
    COPY_OPTIONS = (ON_ERROR = 'CONTINUE')
    COMMENT = 'Internal stage for testing Snowpipe';


-- List stages
SHOW STAGES;

-- Describe stage configuration
DESC STAGE internal_sales_stage;


-- Test stage by listing files (for external stages)
-- LIST @s3_sales_stage;


-- Create additional stages for different data types
CREATE OR REPLACE STAGE csv_stage
    FILE_FORMAT = csv_format
    COMMENT = 'Stage for CSV customer updates';

CREATE OR REPLACE STAGE parquet_stage
    FILE_FORMAT = parquet_format
    COMMENT = 'Stage for Parquet data files';


-- ============================================================================
-- SECTION 3: Create Snowpipe
-- ============================================================================
-- Snowpipe automates data loading from stages using serverless compute.
-- It can trigger automatically via cloud notifications or manual refresh.
-- ============================================================================

-- Create basic Snowpipe for JSON sales data
CREATE OR REPLACE PIPE sales_pipe
    AUTO_INGEST = TRUE  -- Enable automatic loading via cloud notifications
    COMMENT = 'Continuously load sales data from S3'
AS
    COPY INTO sales (
        sale_id,
        transaction_date,
        product_id,
        product_name,
        category,
        customer_id,
        customer_name,
        quantity,
        unit_price,
        total_amount,
        payment_method,
        store_location,
        region,
        source_file
    )
    FROM (
        SELECT
            $1:sale_id::VARCHAR AS sale_id,
            $1:transaction_date::TIMESTAMP_NTZ AS transaction_date,
            $1:product_id::VARCHAR AS product_id,
            $1:product_name::VARCHAR AS product_name,
            $1:category::VARCHAR AS category,
            $1:customer_id::VARCHAR AS customer_id,
            $1:customer_name::VARCHAR AS customer_name,
            $1:quantity::NUMBER AS quantity,
            $1:unit_price::DECIMAL(10,2) AS unit_price,
            $1:total_amount::DECIMAL(12,2) AS total_amount,
            $1:payment_method::VARCHAR AS payment_method,
            $1:store_location::VARCHAR AS store_location,
            $1:region::VARCHAR AS region,
            METADATA$FILENAME AS source_file
        FROM @internal_sales_stage
    )
    FILE_FORMAT = json_format;


-- View pipe configuration
SHOW PIPES;

DESC PIPE sales_pipe;


-- Create pipe for event data with error handling
CREATE OR REPLACE PIPE events_pipe
    AUTO_INGEST = TRUE
    ERROR_INTEGRATION = NULL  -- Can integrate with notification system
    COMMENT = 'Load event data with error tracking'
AS
    COPY INTO events (
        event_id,
        event_type,
        user_id,
        timestamp,
        properties,
        source_file
    )
    FROM (
        SELECT
            $1:event_id::VARCHAR,
            $1:event_type::VARCHAR,
            $1:user_id::VARCHAR,
            $1:timestamp::TIMESTAMP_NTZ,
            $1:properties::VARIANT,
            METADATA$FILENAME
        FROM @internal_sales_stage
    )
    FILE_FORMAT = json_format
    ON_ERROR = 'CONTINUE';  -- Continue loading even if some records fail


-- Create pipe for CSV customer data
CREATE OR REPLACE PIPE customer_updates_pipe
    AUTO_INGEST = TRUE
AS
    COPY INTO customer_updates (
        customer_id,
        email,
        first_name,
        last_name,
        phone,
        address,
        city,
        state,
        zip_code,
        update_timestamp,
        source_file
    )
    FROM (
        SELECT
            $1::VARCHAR,
            $2::VARCHAR,
            $3::VARCHAR,
            $4::VARCHAR,
            $5::VARCHAR,
            $6::VARCHAR,
            $7::VARCHAR,
            $8::VARCHAR,
            $9::VARCHAR,
            $10::TIMESTAMP_NTZ,
            METADATA$FILENAME
        FROM @csv_stage
    )
    FILE_FORMAT = csv_format
    ON_ERROR = 'SKIP_FILE';  -- Skip entire file if errors exceed threshold


-- Create pipe with pattern matching (load only specific files)
CREATE OR REPLACE PIPE sales_filtered_pipe
    AUTO_INGEST = FALSE  -- Manual refresh only
AS
    COPY INTO sales
    FROM @internal_sales_stage
    FILE_FORMAT = json_format
    PATTERN = '.*sales_[0-9]{8}\\.json';  -- Only files matching pattern


-- List all pipes
SHOW PIPES IN SCHEMA ingestion;


-- ============================================================================
-- SECTION 4: Configure Cloud Event Notifications
-- ============================================================================
-- For AUTO_INGEST to work, configure cloud storage notifications to alert
-- Snowpipe when new files arrive.
-- ============================================================================

-- Get the notification channel for the pipe
-- This ARN/URL is used in cloud storage event configuration
DESC PIPE sales_pipe;
-- Look for 'notification_channel' in output


-- AWS S3 Configuration Steps (execute in AWS Console/CLI):
/*
1. Get the Snowpipe SQS queue ARN from DESC PIPE output:
   notification_channel: arn:aws:sqs:us-east-1:123456789:sf-snowpipe-AIDXXXXXX-XXXXX

2. Create S3 Event Notification:
   - Go to S3 bucket properties
   - Under "Event notifications", create new notification
   - Event types: s3:ObjectCreated:*
   - Prefix: sales/incoming/ (match your stage path)
   - Suffix: .json (optional filter)
   - Destination: SQS queue
   - Queue ARN: <paste notification_channel from step 1>

3. Update bucket policy to allow SNS/SQS notifications:
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSnowflakeAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/SnowflakeS3Access"
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}

4. Test by uploading a file to S3 bucket
*/


-- Azure Blob Storage Configuration:
/*
1. Get notification channel URL from DESC PIPE
2. Create Azure Event Grid subscription:
   - Source: Blob Storage account
   - Event types: Blob Created
   - Endpoint: Snowflake notification URL
   - Filters: Container name and blob prefix
*/


-- GCS Configuration:
/*
1. Enable Pub/Sub notifications on GCS bucket
2. Create topic and subscription
3. Configure subscription to point to Snowflake notification channel
4. Grant Snowflake service account pub/sub permissions
*/


-- For internal stages (testing), use manual refresh instead of AUTO_INGEST
ALTER PIPE sales_pipe SET PIPE_EXECUTION_PAUSED = FALSE;


-- ============================================================================
-- SECTION 5: Manual Pipe Refresh
-- ============================================================================
-- Manually trigger Snowpipe to load files, useful for testing or batch loads.
-- ============================================================================

-- Create sample JSON data for testing
-- First, create sample files in internal stage

-- Create sample data directly
CREATE OR REPLACE TABLE sales_sample_data AS
SELECT
    CONCAT('SALE-', SEQ4()) AS sale_id,
    DATEADD(MINUTE, -UNIFORM(1, 10080, RANDOM()), CURRENT_TIMESTAMP()) AS transaction_date,
    CONCAT('PROD-', UNIFORM(1, 100, RANDOM())) AS product_id,
    CONCAT('Product ', UNIFORM(1, 100, RANDOM())) AS product_name,
    ARRAY_GET(PARSE_JSON('["Electronics","Clothing","Food","Books","Home"]'),
              UNIFORM(0, 4, RANDOM())) AS category,
    CONCAT('CUST-', UNIFORM(1, 500, RANDOM())) AS customer_id,
    CONCAT('Customer ', UNIFORM(1, 500, RANDOM())) AS customer_name,
    UNIFORM(1, 10, RANDOM()) AS quantity,
    UNIFORM(10, 500, RANDOM()) AS unit_price,
    (UNIFORM(1, 10, RANDOM()) * UNIFORM(10, 500, RANDOM())) AS total_amount,
    ARRAY_GET(PARSE_JSON('["Credit Card","PayPal","Debit Card","Cash"]'),
              UNIFORM(0, 3, RANDOM())) AS payment_method,
    CONCAT('Store ', UNIFORM(1, 20, RANDOM())) AS store_location,
    ARRAY_GET(PARSE_JSON('["North","South","East","West","Central"]'),
              UNIFORM(0, 4, RANDOM())) AS region
FROM TABLE(GENERATOR(ROWCOUNT => 1000));

-- Export to stage as JSON
COPY INTO @internal_sales_stage/sales_batch_001.json
FROM (
    SELECT OBJECT_CONSTRUCT(
        'sale_id', sale_id,
        'transaction_date', transaction_date,
        'product_id', product_id,
        'product_name', product_name,
        'category', category,
        'customer_id', customer_id,
        'customer_name', customer_name,
        'quantity', quantity,
        'unit_price', unit_price,
        'total_amount', total_amount,
        'payment_method', payment_method,
        'store_location', store_location,
        'region', region
    )
    FROM sales_sample_data
)
FILE_FORMAT = json_format
SINGLE = TRUE
OVERWRITE = TRUE;

-- List files in stage
LIST @internal_sales_stage;


-- Manually refresh pipe to load specific files
ALTER PIPE sales_pipe REFRESH;

-- Or refresh specific path
ALTER PIPE sales_pipe REFRESH PREFIX = 'sales_batch';


-- View pipe status
SELECT SYSTEM$PIPE_STATUS('sales_pipe');
-- Returns JSON with execution status, pending files, etc.


-- Parse pipe status for better readability
SELECT
    PARSE_JSON(SYSTEM$PIPE_STATUS('sales_pipe')):executionState::VARCHAR AS execution_state,
    PARSE_JSON(SYSTEM$PIPE_STATUS('sales_pipe')):pendingFileCount::NUMBER AS pending_files,
    PARSE_JSON(SYSTEM$PIPE_STATUS('sales_pipe')):lastReceivedMessageTimestamp::TIMESTAMP_NTZ AS last_message;


-- Wait a few seconds for pipe to process
CALL SYSTEM$WAIT(5);

-- Check if data loaded
SELECT COUNT(*) FROM sales;
-- Should show records loaded

SELECT * FROM sales LIMIT 10;


-- Force refresh for all unloaded files in stage
-- This is useful when AUTO_INGEST failed or for backfilling
ALTER PIPE sales_pipe REFRESH;


-- Pause pipe (stop processing)
ALTER PIPE sales_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Resume pipe
ALTER PIPE sales_pipe SET PIPE_EXECUTION_PAUSED = FALSE;


-- ============================================================================
-- SECTION 6: Monitor Snowpipe
-- ============================================================================
-- Track pipe execution, file processing, and error rates.
-- ============================================================================

-- Query pipe execution history from INFORMATION_SCHEMA
SELECT
    pipe_name,
    file_name,
    stage_location,
    file_size,
    row_count,
    row_parsed,
    first_error_message,
    first_error_line_number,
    system_error,
    status,
    last_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'SALES',
    START_TIME => DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
))
ORDER BY last_load_time DESC;


-- Query from ACCOUNT_USAGE (more historical data, 2-hour latency)
SELECT
    pipe_name,
    file_name,
    stage_location,
    file_size / (1024*1024) AS file_size_mb,
    row_count,
    row_parsed,
    error_count,
    error_limit,
    status,
    first_error_message,
    last_load_time
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE pipe_name = 'SALES_PIPE'
  AND last_load_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY last_load_time DESC
LIMIT 100;


-- Pipe usage statistics
SELECT
    pipe_name,
    DATE(start_time) AS load_date,
    COUNT(*) AS file_count,
    SUM(file_size) / (1024*1024*1024) AS total_gb,
    SUM(row_count) AS total_rows,
    AVG(file_size) / (1024*1024) AS avg_file_size_mb,
    AVG(row_count) AS avg_rows_per_file,
    SUM(error_count) AS total_errors
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE pipe_name = 'SALES_PIPE'
  AND start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY pipe_name, DATE(start_time)
ORDER BY load_date DESC;


-- Failed loads analysis
SELECT
    pipe_name,
    file_name,
    error_count,
    first_error_message,
    first_error_line_number,
    first_error_column_name,
    last_load_time
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE pipe_name = 'SALES_PIPE'
  AND status = 'LOAD_FAILED'
  AND last_load_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY last_load_time DESC;


-- Query PIPE_USAGE_HISTORY for credit consumption
SELECT
    pipe_name,
    DATE(start_time) AS usage_date,
    SUM(credits_used) AS total_credits,
    SUM(bytes_inserted) / (1024*1024*1024) AS total_gb_loaded,
    SUM(files_inserted) AS total_files_loaded,
    AVG(credits_used) AS avg_credits_per_run
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE pipe_name = 'SALES_PIPE'
  AND start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY pipe_name, DATE(start_time)
ORDER BY usage_date DESC;


-- Overall Snowpipe health dashboard
SELECT
    p.pipe_name,
    p.pipe_schema,
    PARSE_JSON(SYSTEM$PIPE_STATUS(p.pipe_name)):executionState::VARCHAR AS state,
    PARSE_JSON(SYSTEM$PIPE_STATUS(p.pipe_name)):pendingFileCount::NUMBER AS pending_files,
    COUNT(DISTINCT c.file_name) AS files_loaded_today,
    SUM(c.row_count) AS rows_loaded_today,
    SUM(c.error_count) AS errors_today
FROM INFORMATION_SCHEMA.PIPES p
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY c
    ON p.pipe_name = c.pipe_name
    AND c.last_load_time >= CURRENT_DATE()
WHERE p.pipe_schema = 'INGESTION'
GROUP BY p.pipe_name, p.pipe_schema
ORDER BY p.pipe_name;


-- Latency analysis (time from file arrival to load completion)
SELECT
    pipe_name,
    file_name,
    last_load_time,
    LAG(last_load_time) OVER (PARTITION BY pipe_name ORDER BY last_load_time) AS previous_load_time,
    DATEDIFF(SECOND,
             LAG(last_load_time) OVER (PARTITION BY pipe_name ORDER BY last_load_time),
             last_load_time) AS seconds_between_loads
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE pipe_name = 'SALES_PIPE'
  AND last_load_time >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
ORDER BY last_load_time DESC
LIMIT 50;


-- ============================================================================
-- SECTION 7: Error Handling and Data Quality
-- ============================================================================
-- Detect and handle load errors for data quality assurance.
-- ============================================================================

-- Use VALIDATION_MODE to test COPY statement without loading data
COPY INTO sales
FROM @internal_sales_stage
FILE_FORMAT = json_format
VALIDATION_MODE = 'RETURN_ERRORS';  -- Returns first error per file
-- Shows errors without actually loading data


-- Full validation (check all rows, can be slow)
COPY INTO sales
FROM @internal_sales_stage
FILE_FORMAT = json_format
VALIDATION_MODE = 'RETURN_ALL_ERRORS';  -- Returns all errors
-- Use for thorough data quality checks


-- Load with error tracking
COPY INTO sales
FROM @internal_sales_stage
FILE_FORMAT = json_format
ON_ERROR = 'CONTINUE'  -- Continue loading even with errors
SIZE_LIMIT = 1000000;  -- Limit to 1MB per file for testing


-- Query COPY command history for errors
SELECT
    file_name,
    status,
    row_count,
    row_parsed,
    error_count,
    first_error_message,
    first_error_line_number,
    first_error_column_name
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'SALES',
    START_TIME => DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
))
WHERE status != 'LOADED'
ORDER BY last_load_time DESC;


-- Create view for load monitoring
CREATE OR REPLACE VIEW load_monitoring AS
SELECT
    pipe_name,
    file_name,
    stage_location,
    row_count,
    error_count,
    ROUND((error_count::FLOAT / NULLIF(row_parsed, 0)) * 100, 2) AS error_rate_pct,
    status,
    first_error_message,
    last_load_time
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE last_load_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP());

SELECT * FROM load_monitoring
WHERE error_count > 0
ORDER BY error_count DESC;


-- Create alert task for failed loads (requires Tasks enabled)
CREATE OR REPLACE TABLE load_failure_alerts (
    alert_id NUMBER IDENTITY(1,1),
    pipe_name VARCHAR(100),
    file_name VARCHAR(500),
    error_message VARCHAR(5000),
    alert_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TASK monitor_load_failures
    WAREHOUSE = snowpipe_wh
    SCHEDULE = '15 MINUTE'
AS
    INSERT INTO load_failure_alerts (pipe_name, file_name, error_message)
    SELECT
        pipe_name,
        file_name,
        first_error_message
    FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
    WHERE status = 'LOAD_FAILED'
      AND last_load_time >= DATEADD(MINUTE, -15, CURRENT_TIMESTAMP())
      AND file_name NOT IN (
          SELECT file_name FROM load_failure_alerts
          WHERE alert_time >= DATEADD(HOUR, -1, CURRENT_TIMESTAMP())
      );

-- ALTER TASK monitor_load_failures RESUME;


-- Track data quality metrics
CREATE OR REPLACE VIEW data_quality_metrics AS
SELECT
    DATE(last_load_time) AS load_date,
    pipe_name,
    COUNT(DISTINCT file_name) AS files_processed,
    SUM(row_count) AS total_rows,
    SUM(error_count) AS total_errors,
    ROUND(AVG((error_count::FLOAT / NULLIF(row_parsed, 0)) * 100), 2) AS avg_error_rate_pct,
    SUM(CASE WHEN status = 'LOADED' THEN 1 ELSE 0 END) AS successful_loads,
    SUM(CASE WHEN status = 'LOAD_FAILED' THEN 1 ELSE 0 END) AS failed_loads,
    ROUND(100.0 * SUM(CASE WHEN status = 'LOADED' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE last_load_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY DATE(last_load_time), pipe_name;

SELECT * FROM data_quality_metrics
ORDER BY load_date DESC, pipe_name;


-- ============================================================================
-- SECTION 8: Cost Calculation and Optimization
-- ============================================================================
-- Calculate Snowpipe costs and optimize for efficiency.
-- ============================================================================

-- Snowpipe pricing: ~0.06 credits per 1,000 files loaded (serverless compute)
-- Plus standard storage and cloud services costs

-- Calculate monthly Snowpipe cost
WITH pipe_stats AS (
    SELECT
        pipe_name,
        DATE_TRUNC('MONTH', start_time) AS month,
        SUM(files_inserted) AS total_files,
        SUM(bytes_inserted) / (1024*1024*1024) AS total_gb,
        SUM(credits_used) AS total_credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
    WHERE start_time >= DATEADD(MONTH, -3, CURRENT_TIMESTAMP())
    GROUP BY pipe_name, DATE_TRUNC('MONTH', start_time)
)
SELECT
    pipe_name,
    month,
    total_files,
    ROUND(total_gb, 2) AS total_gb_loaded,
    total_credits,
    ROUND(total_credits * 4, 2) AS estimated_cost_usd,  -- $4 per credit
    ROUND((total_files / 1000.0) * 0.06, 4) AS estimated_file_processing_credits,
    ROUND(total_credits / NULLIF(total_files, 0), 6) AS credits_per_file
FROM pipe_stats
ORDER BY month DESC, pipe_name;


-- Optimization opportunity analysis
WITH daily_loads AS (
    SELECT
        pipe_name,
        DATE(start_time) AS load_date,
        COUNT(DISTINCT file_name) AS file_count,
        AVG(file_size) / (1024*1024) AS avg_file_size_mb,
        SUM(credits_used) AS credits_used
    FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
    WHERE pipe_name IS NOT NULL
      AND start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
    GROUP BY pipe_name, DATE(start_time)
)
SELECT
    pipe_name,
    AVG(file_count) AS avg_daily_files,
    AVG(avg_file_size_mb) AS avg_file_size_mb,
    AVG(credits_used) AS avg_daily_credits,
    CASE
        WHEN AVG(avg_file_size_mb) < 1 THEN 'Consider batching small files (< 1MB)'
        WHEN AVG(file_count) < 10 THEN 'Low volume - consider scheduled COPY instead'
        WHEN AVG(file_count) > 10000 THEN 'High volume - optimize file size and format'
        ELSE 'Well-optimized'
    END AS optimization_recommendation
FROM daily_loads
GROUP BY pipe_name
ORDER BY avg_daily_credits DESC;


-- Cost comparison: Snowpipe vs. COPY with warehouse
CREATE OR REPLACE VIEW cost_comparison AS
SELECT
    'Snowpipe (Serverless)' AS method,
    1000 AS files_per_day,
    50 AS avg_file_size_mb,
    -- Snowpipe: 0.06 credits per 1000 files
    (1000 / 1000.0) * 0.06 * 30 AS monthly_credits,
    ((1000 / 1000.0) * 0.06 * 30) * 4 AS monthly_cost_usd
UNION ALL
SELECT
    'COPY with X-Small WH' AS method,
    1000,
    50,
    -- X-Small warehouse: ~1 credit/hour, assume 2 hours/day for COPY
    2 * 30 AS monthly_credits,
    (2 * 30) * 4 AS monthly_cost_usd
UNION ALL
SELECT
    'COPY with Small WH' AS method,
    1000,
    50,
    -- Small warehouse: ~2 credits/hour
    4 * 30 AS monthly_credits,
    (4 * 30) * 4 AS monthly_cost_usd;

SELECT
    method,
    files_per_day,
    monthly_credits,
    monthly_cost_usd,
    CASE
        WHEN monthly_cost_usd = (SELECT MIN(monthly_cost_usd) FROM cost_comparison) THEN '✓ Most Cost-Effective'
        ELSE ''
    END AS recommendation
FROM cost_comparison
ORDER BY monthly_cost_usd;


 -- Best practices for cost optimization
CREATE OR REPLACE VIEW snowpipe_optimization_guide AS
SELECT
    'Batch small files' AS practice,
    'Combine files to 100-250MB before loading' AS implementation,
    'Reduce per-file processing overhead' AS benefit,
    'High' AS impact
UNION ALL
SELECT
    'Use compressed files',
    'Enable GZIP/BZIP2/ZSTD compression',
    'Reduce data transfer and storage costs',
    'High'
UNION ALL
SELECT
    'Partition by date',
    'Organize files by date in S3 paths',
    'Enable efficient data lifecycle management',
    'Medium'
UNION ALL
SELECT
    'Use Parquet/ORC format',
    'Columnar formats for analytical workloads',
    'Faster loads and queries, less storage',
    'High'
UNION ALL
SELECT
    'Monitor error rates',
    'Alert on error_rate > 1%',
    'Catch data quality issues early',
    'Medium'
UNION ALL
SELECT
    'Set appropriate ON_ERROR',
    'Use SKIP_FILE for critical pipes',
    'Prevent bad data from entering tables',
    'High'
UNION ALL
SELECT
    'Use AUTO_INGEST wisely',
    'Disable for infrequent loads (< 1/hour)',
    'Save cloud notification costs',
    'Low'
UNION ALL
SELECT
    'Archive loaded files',
    'Move to Glacier after successful load',
    'Reduce S3 storage costs',
    'Medium';

SELECT * FROM snowpipe_optimization_guide ORDER BY impact DESC, practice;


-- Monthly cost tracking and forecasting
WITH monthly_usage AS (
    SELECT
        DATE_TRUNC('MONTH', start_time) AS month,
        SUM(files_inserted) AS total_files,
        SUM(bytes_inserted) / (1024*1024*1024) AS total_gb,
        SUM(credits_used) AS total_credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
    WHERE start_time >= DATEADD(MONTH, -6, CURRENT_TIMESTAMP())
    GROUP BY DATE_TRUNC('MONTH', start_time)
)
SELECT
    month,
    total_files,
    ROUND(total_gb, 2) AS total_gb,
    ROUND(total_credits, 2) AS total_credits,
    ROUND(total_credits * 4, 2) AS cost_usd,
    ROUND(LAG(total_credits) OVER (ORDER BY month), 2) AS prev_month_credits,
    ROUND(((total_credits - LAG(total_credits) OVER (ORDER BY month)) /
           NULLIF(LAG(total_credits) OVER (ORDER BY month), 0)) * 100, 1) AS growth_pct
FROM monthly_usage
ORDER BY month DESC;


-- ============================================================================
-- CLEANUP
-- ============================================================================

/*
-- Pause all pipes
ALTER PIPE sales_pipe SET PIPE_EXECUTION_PAUSED = TRUE;
ALTER PIPE events_pipe SET PIPE_EXECUTION_PAUSED = TRUE;
ALTER PIPE customer_updates_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Drop pipes
DROP PIPE IF EXISTS sales_pipe;
DROP PIPE IF EXISTS events_pipe;
DROP PIPE IF EXISTS customer_updates_pipe;
DROP PIPE IF EXISTS sales_filtered_pipe;

-- Drop database and warehouse
DROP DATABASE IF EXISTS snowpipe_lab;
DROP WAREHOUSE IF EXISTS snowpipe_wh;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Snowpipe enables continuous, serverless data loading from cloud storage
--    (S3, Azure Blob, GCS) without managing compute resources.
--
-- 2. AUTO_INGEST with cloud notifications (S3 Events, Azure Event Grid)
--    triggers automatic loading when new files arrive.
--
-- 3. Manual refresh with ALTER PIPE...REFRESH for batch loads or testing.
--    Useful when AUTO_INGEST isn't configured.
--
-- 4. Snowpipe pricing: ~0.06 credits per 1,000 files loaded. Serverless
--    compute means no idle warehouse costs.
--
-- 5. Monitor loads using COPY_HISTORY and PIPE_USAGE_HISTORY views.
--    Track file counts, error rates, and credit consumption.
--
-- 6. Error handling options:
--    - ON_ERROR = 'CONTINUE': Load valid data, skip bad records
--    - ON_ERROR = 'SKIP_FILE': Skip entire file if errors found
--    - VALIDATION_MODE: Test loads without inserting data
--
-- 7. Cost optimization strategies:
--    - Batch small files to 100-250MB before loading
--    - Use compressed formats (GZIP, Parquet, ORC)
--    - Monitor and reduce error rates
--    - Consider scheduled COPY for low-volume loads
--
-- 8. Best practices:
--    - Partition files by date in storage paths
--    - Use columnar formats (Parquet) for analytics
--    - Set up alerts for failed loads
--    - Archive loaded files to cheaper storage tiers
--
-- 9. Use cases:
--    - Real-time data ingestion from applications
--    - IoT sensor data streaming
--    - Log file processing
--    - CDC from external systems
--    - Clickstream analytics
--
-- 10. Snowpipe vs. Tasks with COPY:
--     - Snowpipe: Continuous, sub-minute latency, serverless
--     - Tasks: Scheduled, batch-oriented, uses warehouse compute
--     - Choose based on latency requirements and file arrival patterns
-- ============================================================================
