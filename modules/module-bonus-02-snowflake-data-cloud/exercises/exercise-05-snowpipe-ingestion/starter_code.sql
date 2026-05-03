-- ============================================================================
-- Exercise 05: Snowpipe Automated Ingestion
-- Starter Code
-- ============================================================================
-- OBJECTIVE: Implement automated data ingestion using Snowpipe
-- - Configure external stage (S3)
-- - Create file format for JSON data
-- - Set up Snowpipe for continuous ingestion
-- - Configure S3 event notifications
-- - Monitor ingestion and costs
-- ============================================================================

-- Step 1: Environment Setup
-- ============================================================================
-- TODO: Set up environment
-- YOUR CODE HERE:

USE ROLE TRAINING_ROLE;
USE WAREHOUSE TRAINING_WH;

-- TODO: Create database INGESTION_LAB
-- YOUR CODE HERE:


-- TODO: Create schema IOT_DATA
-- YOUR CODE HERE:


USE SCHEMA INGESTION_LAB.IOT_DATA;


-- Step 2: Create External Stage (S3)
-- ============================================================================
-- TODO: Create external stage pointing to S3 bucket
-- Stage name: s3_stage
-- URL: s3://training-bucket/iot-data/
-- Credentials: Use AWS_KEY_ID and AWS_SECRET_KEY
-- Hint: You'll need valid AWS credentials or use Snowflake storage integration
-- YOUR CODE HERE:


-- TODO: List files in the stage to verify connection
-- YOUR CODE HERE:


-- Step 3: Create File Format
-- ============================================================================
-- TODO: Create file format for JSON data
-- Format name: json_format
-- TYPE: JSON
-- Consider options: STRIP_OUTER_ARRAY, DATE_FORMAT, TIMESTAMP_FORMAT
-- YOUR CODE HERE:


-- TODO: Test file format by querying sample file
-- Use SELECT from stage with file format
-- YOUR CODE HERE:


-- Step 4: Create Target Table
-- ============================================================================
-- TODO: Create sensor_data table with following columns:
--   - SENSOR_ID: VARCHAR(50)
--   - TIMESTAMP: TIMESTAMP_NTZ
--   - TEMPERATURE: DOUBLE
--   - HUMIDITY: DOUBLE
--   - LOCATION: VARIANT (for nested JSON)
--   - INGESTION_TIME: TIMESTAMP_NTZ (default CURRENT_TIMESTAMP)
-- YOUR CODE HERE:


-- Step 5: Create Snowpipe
-- ============================================================================
-- TODO: Create pipe sensor_pipe with AUTO_INGEST enabled
-- Pipe should COPY INTO sensor_data FROM @s3_stage
-- Use json_format file format
-- Pattern: Match specific file patterns if needed (e.g., '.*sensor.*\\.json')
-- YOUR CODE HERE:


-- TODO: Get pipe notification channel for S3 event configuration
-- Use SHOW PIPES and note the notification_channel
-- YOUR CODE HERE:


-- Step 6: Manually Trigger Pipe (Testing)
-- ============================================================================
-- TODO: Manually refresh pipe to load existing files
-- YOUR CODE HERE:


-- TODO: Check pipe status
-- Use SYSTEM$PIPE_STATUS function
-- YOUR CODE HERE:


-- TODO: Verify data loaded into sensor_data table
-- YOUR CODE HERE:


-- Step 7: Monitor Pipe Activity
-- ============================================================================
-- TODO: Query pipe usage history
-- Check credits consumed, files loaded, bytes processed
-- YOUR CODE HERE:


-- TODO: Query copy history to see file-level details
-- Include: file name, status, rows loaded, errors
-- YOUR CODE HERE:


-- TODO: Check for any load errors
-- YOUR CODE HERE:


-- Step 8: Cost Analysis
-- ============================================================================
-- TODO: Calculate Snowpipe costs
-- Snowpipe charges: 0.06 credits per 1,000 files loaded
-- Query PIPE_USAGE_HISTORY and calculate total cost
-- YOUR CODE HERE:


-- TODO: Analyze cost per GB of data ingested
-- YOUR CODE HERE:


-- Step 9: Data Quality Validation
-- ============================================================================
-- TODO: Use VALIDATE function to check files without loading
-- Check for malformed JSON or schema issues
-- YOUR CODE HERE:


-- TODO: Query sensor_data for basic statistics
-- Count by sensor_id, date ranges, data completeness
-- YOUR CODE HERE:


-- TODO: Check for duplicate records based on SENSOR_ID and TIMESTAMP
-- YOUR CODE HERE:


-- Step 10: Advanced Monitoring Queries
-- ============================================================================
-- TODO: Create view for pipe monitoring dashboard
-- Include: load rate, success rate, error rate, credit consumption
-- YOUR CODE HERE:


-- TODO: Query to identify slow-loading files
-- YOUR CODE HERE:


-- TODO: Alert query for failed loads (error rate > 5%)
-- YOUR CODE HERE:


-- Cleanup Commands (DO NOT RUN DURING EXERCISE)
-- ============================================================================
-- ALTER PIPE sensor_pipe SET PIPE_EXECUTION_PAUSED = TRUE;
-- DROP PIPE IF EXISTS sensor_pipe;
-- DROP TABLE IF EXISTS sensor_data;
-- DROP FILE FORMAT IF EXISTS json_format;
-- DROP STAGE IF EXISTS s3_stage;
-- DROP SCHEMA IF EXISTS INGESTION_LAB.IOT_DATA;
-- DROP DATABASE IF EXISTS INGESTION_LAB;

-- ============================================================================
-- Validation Checklist
-- ============================================================================
-- [ ] External stage created and accessible
-- [ ] File format correctly parses JSON files
-- [ ] Target table created with proper schema
-- [ ] Snowpipe created with AUTO_INGEST enabled
-- [ ] Notification channel obtained for S3 configuration
-- [ ] Manual refresh successful
-- [ ] Data loaded into target table
-- [ ] Monitoring queries returning results
-- [ ] Cost calculations accurate
-- [ ] Error tracking working
-- ============================================================================

-- ============================================================================
-- S3 Event Notification Configuration (Reference)
-- ============================================================================
-- After creating the pipe, configure S3 bucket notifications:
-- 1. Go to S3 bucket -> Properties -> Event notifications
-- 2. Create new event notification
-- 3. Event types: ObjectCreated (All)
-- 4. Prefix: iot-data/ (or your path)
-- 5. Suffix: .json
-- 6. Send to: SQS Queue
-- 7. SQS Queue ARN: <use notification_channel from SHOW PIPES>
-- ============================================================================
