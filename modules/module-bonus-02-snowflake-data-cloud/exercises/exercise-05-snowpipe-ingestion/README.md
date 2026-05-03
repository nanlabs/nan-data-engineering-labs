# Exercise 05: Snowpipe Auto-Ingestion

## Overview
Implement event-driven, near real-time data loading with Snowpipe to automatically ingest files from cloud storage as they arrive, eliminating the need for scheduled batch loads.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Module 02 (Storage basics), Exercise 01 (Virtual Warehouses), AWS/Azure/GCP account with S3 bucket

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create external stages pointing to cloud storage (S3/Azure/GCS)
- Configure file formats for structured and semi-structured data
- Create and manage Snowpipe objects
- Set up cloud event notifications (S3 Event Notifications)
- Monitor Snowpipe ingestion and troubleshoot failures
- Calculate and optimize Snowpipe costs
- Handle schema evolution and data quality issues

---

## Scenario
You're managing an IoT platform that collects sensor data from thousands of devices deployed in the field. Sensors generate JSON files every minute and upload them to an S3 bucket. Requirements:
- **Near real-time ingestion**: Data must be available within 1-2 minutes of file upload
- **Zero manual intervention**: No scheduled jobs or manual COPY commands
- **Cost-effective**: Minimize compute costs while maintaining performance
- **Error handling**: Track and alert on failed ingestions

Your goal is to implement a fully automated ingestion pipeline using Snowpipe.

---

## Requirements

### Task 1: Setup Stage & Format (20 min)
Create an external stage connected to cloud storage and define file formats.

**Create Storage Integration** (requires ACCOUNTADMIN):
```sql
-- For AWS S3
CREATE OR REPLACE STORAGE INTEGRATION s3_integration
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-s3-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://your-iot-bucket/sensor-data/');

-- Describe integration to get AWS_IAM_USER_ARN and AWS_EXTERNAL_ID
DESC STORAGE INTEGRATION s3_integration;
```

**AWS IAM Setup** (in AWS Console):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/snowflake"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "SNOWFLAKE_EXTERNAL_ID"
        }
      }
    }
  ]
}
```

**Create External Stage**:
```sql
CREATE OR REPLACE STAGE s3_sensor_stage
    STORAGE_INTEGRATION = s3_integration
    URL = 's3://your-iot-bucket/sensor-data/'
    FILE_FORMAT = (TYPE = 'JSON');

-- Test stage access
LIST @s3_sensor_stage;
```

**Create File Formats**:
```sql
-- JSON format for sensor data
CREATE OR REPLACE FILE FORMAT json_sensor_format
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    DATE_FORMAT = 'AUTO'
    TIME_FORMAT = 'AUTO'
    TIMESTAMP_FORMAT = 'AUTO';

-- CSV format (alternative)
CREATE OR REPLACE FILE FORMAT csv_sensor_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '')
    EMPTY_FIELD_AS_NULL = TRUE
    COMPRESSION = 'GZIP';

-- Verify formats
SHOW FILE FORMATS LIKE '%sensor%';
```

**Test File Read**:
```sql
-- Create sample JSON file content:
-- {"sensor_id": "SENSOR_001", "timestamp": "2024-03-09T10:30:00Z", "temperature": 22.5, "humidity": 65.2, "location": {"lat": 40.7128, "lon": -74.0060}}

-- Test reading from stage (manually upload test file first)
SELECT
    $1:sensor_id::VARCHAR as sensor_id,
    $1:timestamp::TIMESTAMP as reading_time,
    $1:temperature::FLOAT as temperature,
    $1:humidity::FLOAT as humidity,
    $1:location as location_json
FROM @s3_sensor_stage/test_sensor.json
(FILE_FORMAT => json_sensor_format);
```

**Success Criteria**:
- ✅ Storage integration created and configured
- ✅ External stage pointing to S3 bucket
- ✅ File formats defined (JSON and CSV)
- ✅ Stage accessible (LIST command works)
- ✅ Test file read successfully with correct schema mapping

---

### Task 2: Create Target Table (15 min)
Design and create the target table for sensor data with appropriate schema.

**Create Sensor Data Table**:
```sql
CREATE OR REPLACE TABLE sensor_data (
    -- Extracted fields
    sensor_id VARCHAR(50) NOT NULL,
    reading_timestamp TIMESTAMP NOT NULL,
    temperature FLOAT,
    humidity FLOAT,

    -- Semi-structured location data
    location VARIANT,

    -- Metadata columns
    file_name VARCHAR(500),
    file_row_number INT,
    load_timestamp TIMESTAMP DEFAULT current_timestamp(),

    -- Constraints
    PRIMARY KEY (sensor_id, reading_timestamp)
);
```

**Create Staging/Raw Table** (optional, for ELT pattern):
```sql
CREATE OR REPLACE TABLE sensor_data_raw (
    raw_json VARIANT,
    file_name VARCHAR(500),
    load_timestamp TIMESTAMP DEFAULT current_timestamp()
);
```

**Test Manual COPY**:
```sql
-- Copy from stage to table (to verify schema mapping)
COPY INTO sensor_data (sensor_id, reading_timestamp, temperature, humidity, location, file_name)
FROM (
    SELECT
        $1:sensor_id::VARCHAR,
        $1:timestamp::TIMESTAMP,
        $1:temperature::FLOAT,
        $1:humidity::FLOAT,
        $1:location,
        METADATA$FILENAME
    FROM @s3_sensor_stage
)
FILE_FORMAT = json_sensor_format
PATTERN = '.*test.*';

-- Verify data loaded
SELECT * FROM sensor_data LIMIT 10;

-- Query location data
SELECT
    sensor_id,
    reading_timestamp,
    temperature,
    location:lat::FLOAT as latitude,
    location:lon::FLOAT as longitude
FROM sensor_data
LIMIT 10;
```

**Success Criteria**:
- ✅ `sensor_data` table created with appropriate schema
- ✅ Table includes metadata columns (file_name, load_timestamp)
- ✅ Semi-structured VARIANT column for location
- ✅ Manual COPY command works successfully
- ✅ Can query JSON fields from location VARIANT

---

### Task 3: Create Snowpipe (25 min)
Configure Snowpipe to automatically load new files as they arrive.

**Create Snowpipe**:
```sql
CREATE OR REPLACE PIPE sensor_data_pipe
    AUTO_INGEST = TRUE
    AWS_SNS_TOPIC = 'arn:aws:sns:us-east-1:123456789012:snowflake-s3-events'
    COMMENT = 'Auto-ingest sensor data from S3'
AS
COPY INTO sensor_data (sensor_id, reading_timestamp, temperature, humidity, location, file_name)
FROM (
    SELECT
        $1:sensor_id::VARCHAR,
        $1:timestamp::TIMESTAMP,
        $1:temperature::FLOAT,
        $1:humidity::FLOAT,
        $1:location,
        METADATA$FILENAME
    FROM @s3_sensor_stage
)
FILE_FORMAT = json_sensor_format
ON_ERROR = 'CONTINUE';  -- Skip bad files, don't fail entire load

-- Get pipe notification channel (for S3 event configuration)
DESC PIPE sensor_data_pipe;
```

**Important Pipe Details**:
```sql
-- Show pipes
SHOW PIPES LIKE 'sensor_data_pipe';

-- Check pipe status
SELECT SYSTEM$PIPE_STATUS('sensor_data_pipe');

-- Pipe properties from DESC output:
-- notification_channel: SQS queue ARN for S3 to send events
-- Copy these values for AWS S3 event notification setup
```

**Pause/Resume Pipe**:
```sql
-- Pause pipe (stops processing)
ALTER PIPE sensor_data_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Resume pipe
ALTER PIPE sensor_data_pipe SET PIPE_EXECUTION_PAUSED = FALSE;

-- Note: Pipes start in active state by default
```

**Success Criteria**:
- ✅ Snowpipe created with AUTO_INGEST=TRUE
- ✅ COPY statement properly maps JSON fields to table columns
- ✅ ON_ERROR='CONTINUE' configured for resilience
- ✅ notification_channel identified from DESC PIPE output
- ✅ Pipe shows as active in SHOW PIPES

---

### Task 4: S3 Event Notification (20 min)
Configure S3 bucket to send events to Snowpipe via SNS/SQS.

**AWS Setup Overview**:
1. Create SNS Topic
2. Subscribe Snowpipe SQS queue to SNS topic
3. Configure S3 bucket event notification to publish to SNS

**Step 1: Create SNS Topic** (AWS Console or CLI):
```bash
# AWS CLI
aws sns create-topic \
    --name snowflake-s3-events \
    --region us-east-1
```

**Step 2: Subscribe Snowpipe SQS to SNS**:
```bash
# Get SQS ARN from DESC PIPE output (notification_channel)
# Example: arn:aws:sqs:us-east-1:123456789012:sf-snowpipe-AIDAJKLMNOPQRSTUVWXYZ-abcd1234

aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:snowflake-s3-events \
    --protocol sqs \
    --notification-endpoint arn:aws:sqs:us-east-1:123456789012:sf-snowpipe-AIDAJKLMNOPQRSTUVWXYZ-abcd1234
```

**Step 3: Configure S3 Event Notification**:
```xml
<!-- In S3 Console: Bucket Properties -> Event Notifications -->
<EventNotification>
  <Id>snowflake-sensor-data</Id>
  <Prefix>sensor-data/</Prefix>
  <Event>s3:ObjectCreated:*</Event>
  <Topic>arn:aws:sns:us-east-1:123456789012:snowflake-s3-events</Topic>
</EventNotification>
```

**Alternative: CLI**:
```bash
aws s3api put-bucket-notification-configuration \
    --bucket your-iot-bucket \
    --notification-configuration file://notification.json
```

**notification.json**:
```json
{
  "TopicConfigurations": [
    {
      "Id": "snowflake-sensor-data",
      "TopicArn": "arn:aws:sns:us-east-1:123456789012:snowflake-s3-events",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "prefix",
              "Value": "sensor-data/"
            }
          ]
        }
      }
    }
  ]
}
```

**Document Setup Steps**:
Create `aws-setup-guide.md` documenting:
- Storage Integration setup
- IAM role/policy configuration
- SNS topic creation
- SQS subscription
- S3 event notification
- Troubleshooting common issues

**Success Criteria**:
- ✅ SNS topic created for S3 events
- ✅ Snowpipe SQS queue subscribed to SNS
- ✅ S3 bucket configured to send ObjectCreated events
- ✅ Event notification filtered to sensor-data/ prefix
- ✅ Setup documented in aws-setup-guide.md

---

### Task 5: Manual Testing (20 min)
Test Snowpipe ingestion both manually and automatically.

**Generate Test JSON Files**:
```python
# generate_sensor_data.py
import json
from datetime import datetime, timedelta
import random

def generate_sensor_file(sensor_id, timestamp):
    data = {
        "sensor_id": sensor_id,
        "timestamp": timestamp.isoformat() + "Z",
        "temperature": round(random.uniform(15.0, 30.0), 2),
        "humidity": round(random.uniform(40.0, 80.0), 2),
        "location": {
            "lat": round(random.uniform(40.0, 45.0), 6),
            "lon": round(random.uniform(-75.0, -70.0), 6)
        }
    }
    return data

# Generate 10 files
base_time = datetime.utcnow()
for i in range(10):
    sensor_id = f"SENSOR_{random.randint(1, 5):03d}"
    timestamp = base_time + timedelta(minutes=i)
    filename = f"sensor-data/sensor_{sensor_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w') as f:
        json.dump(generate_sensor_file(sensor_id, timestamp), f)

    print(f"Generated: {filename}")
```

**Upload Files to S3**:
```bash
# Upload test files
aws s3 cp sensor-data/ s3://your-iot-bucket/sensor-data/ --recursive

# Verify upload
aws s3 ls s3://your-iot-bucket/sensor-data/
```

**Manual Pipe Refresh** (for testing without event notification):
```sql
-- Manually trigger pipe to check for new files
ALTER PIPE sensor_data_pipe REFRESH;

-- Wait 10-30 seconds, then check load status
SELECT
    *
FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(hours, -1, current_timestamp())
))
ORDER BY last_load_time DESC;
```

**Verify Data Loaded**:
```sql
-- Check row count
SELECT COUNT(*) as total_records FROM sensor_data;

-- View recent loads
SELECT
    sensor_id,
    reading_timestamp,
    temperature,
    humidity,
    file_name,
    load_timestamp
FROM sensor_data
ORDER BY load_timestamp DESC
LIMIT 20;

-- Verify file metadata
SELECT
    file_name,
    COUNT(*) as records_per_file,
    MIN(load_timestamp) as load_time
FROM sensor_data
GROUP BY file_name
ORDER BY load_time DESC;
```

**Query COPY_HISTORY**:
```sql
-- Detailed copy history
SELECT
    file_name,
    stage_location,
    row_count,
    row_parsed,
    first_error_message,
    first_error_line,
    first_error_character,
    first_error_column_name,
    error_count,
    CASE
        WHEN status = 'LOADED' THEN '✅'
        WHEN status = 'LOAD_FAILED' THEN '❌'
        ELSE status
    END as load_status,
    last_load_time
FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(hours, -24, current_timestamp())
))
ORDER BY last_load_time DESC;
```

**Success Criteria**:
- ✅ Generated and uploaded 10 test JSON files to S3
- ✅ Manual REFRESH triggered Snowpipe ingestion
- ✅ All files loaded successfully (status='LOADED')
- ✅ Data visible in sensor_data table within 1-2 minutes
- ✅ COPY_HISTORY shows zero errors
- ✅ (Bonus) Auto-ingestion working via S3 events

---

### Task 6: Monitoring & Costs (20 min)
Implement monitoring queries and calculate Snowpipe costs.

**Monitor Pipe Usage**:
```sql
-- Snowpipe credit usage
SELECT
    pipe_name,
    DATE(start_time) as usage_date,
    SUM(credits_used) as total_credits,
    SUM(bytes_inserted) / (1024*1024*1024) as gb_inserted,
    SUM(files_inserted) as files_loaded
FROM snowflake.account_usage.pipe_usage_history
WHERE pipe_name = 'SENSOR_DATA_PIPE'
    AND start_time >= DATEADD(day, -7, current_timestamp())
GROUP BY pipe_name, usage_date
ORDER BY usage_date DESC;

-- Files processed by pipe
SELECT
    DATE(last_load_time) as load_date,
    COUNT(*) as files_loaded,
    SUM(row_count) as total_rows,
    SUM(file_size) / (1024*1024) as total_mb
FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(day, -7, current_timestamp())
))
WHERE status = 'LOADED'
GROUP BY load_date
ORDER BY load_date DESC;
```

**Calculate Snowpipe Costs**:
```sql
-- Snowpipe pricing: 0.06 credits per 1,000 files loaded
-- Compute costs: Based on data loaded (serverless compute)

WITH pipe_stats AS (
    SELECT
        SUM(credits_used) as total_credits,
        SUM(files_inserted) as total_files,
        SUM(bytes_inserted) / (1024*1024*1024) as total_gb
    FROM snowflake.account_usage.pipe_usage_history
    WHERE pipe_name = 'SENSOR_DATA_PIPE'
        AND start_time >= DATEADD(day, -30, current_timestamp())
)
SELECT
    total_files,
    total_gb,
    total_credits,
    total_credits * 2.00 as cost_usd,  -- Adjust for your pricing tier
    (total_files / 1000.0 * 0.06) as expected_file_cost_credits,

    -- Cost per file
    (total_credits / total_files) as credits_per_file,

    -- Cost per GB
    (total_credits / total_gb) as credits_per_gb,

    -- Monthly projection
    total_credits as monthly_credits,
    (total_credits * 2.00) as monthly_cost_usd
FROM pipe_stats;
```

**Error Tracking**:
```sql
-- Failed file loads
SELECT
    file_name,
    table_name,
    first_error_message,
    first_error_line,
    error_count,
    last_load_time
FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(day, -7, current_timestamp())
))
WHERE status = 'LOAD_FAILED'
ORDER BY last_load_time DESC;

-- Pipe error summary
SELECT
    DATE(last_load_time) as error_date,
    COUNT(*) as failed_files,
    array_agg(DISTINCT first_error_message) as error_types
FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(day, -30, current_timestamp())
))
WHERE status = 'LOAD_FAILED'
GROUP BY error_date
ORDER BY error_date DESC;
```

**Validate Data Quality**:
```sql
-- Use VALIDATE function to check files without loading
SELECT
    file_name,
    file_size,
    row_count,
    error_count,
    first_error_message
FROM table(
    validate(sensor_data, job_id => '_last')
);

-- Check for duplicate loads (same file loaded twice)
SELECT
    file_name,
    COUNT(*) as load_count,
    array_agg(load_timestamp) as load_times
FROM sensor_data
GROUP BY file_name
HAVING COUNT(*) > 1
ORDER BY load_count DESC;
```

**Create Monitoring Dashboard View**:
```sql
CREATE OR REPLACE VIEW v_snowpipe_dashboard AS
SELECT
    'sensor_data_pipe' as pipe_name,

    -- Today's stats
    (SELECT COUNT(*) FROM sensor_data WHERE DATE(load_timestamp) = CURRENT_DATE()) as files_today,
    (SELECT COUNT(DISTINCT sensor_id) FROM sensor_data WHERE DATE(load_timestamp) = CURRENT_DATE()) as sensors_today,

    -- Last load
    (SELECT MAX(load_timestamp) FROM sensor_data) as last_load_time,
    TIMESTAMPDIFF(minute, (SELECT MAX(load_timestamp) FROM sensor_data), current_timestamp()) as minutes_since_last_load,

    -- Errors (last 24h)
    (SELECT COUNT(*)
     FROM table(information_schema.copy_history(TABLE_NAME => 'SENSOR_DATA', START_TIME => DATEADD(hour, -24, current_timestamp())))
     WHERE status = 'LOAD_FAILED') as errors_24h,

    -- Status
    CASE
        WHEN minutes_since_last_load < 10 THEN '🟢 Healthy'
        WHEN minutes_since_last_load < 60 THEN '🟡 Delayed'
        ELSE '🔴 Stale'
    END as health_status;

-- Query dashboard
SELECT * FROM v_snowpipe_dashboard;
```

**Set Up Alerts** (document as SQL, implement with scheduler):
```sql
-- Alert: No data loaded in 30 minutes
SELECT
    'ALERT: Snowpipe stale' as alert_type,
    MAX(load_timestamp) as last_load,
    TIMESTAMPDIFF(minute, MAX(load_timestamp), current_timestamp()) as minutes_stale
FROM sensor_data
HAVING minutes_stale > 30;

-- Alert: High error rate (>5% failures)
SELECT
    'ALERT: High error rate' as alert_type,
    error_count,
    total_files,
    (error_count::FLOAT / total_files * 100) as error_rate_pct
FROM (
    SELECT
        SUM(CASE WHEN status = 'LOAD_FAILED' THEN 1 ELSE 0 END) as error_count,
        COUNT(*) as total_files
    FROM table(information_schema.copy_history(
        TABLE_NAME => 'SENSOR_DATA',
        START_TIME => DATEADD(hour, -1, current_timestamp())
    ))
)
WHERE error_rate_pct > 5;
```

**Success Criteria**:
- ✅ Pipe usage query shows credit consumption
- ✅ Cost calculation: ~0.06 credits per 1K files
- ✅ Error tracking queries identify failed loads
- ✅ VALIDATE function used to check files
- ✅ Monitoring dashboard view created
- ✅ Alert queries documented for stale data and high error rate

---

## Hints

<details>
<summary>Hint 1: Storage Integration Setup</summary>

```sql
-- Create storage integration (ACCOUNTADMIN role)
USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION s3_integration
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = S3
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_ACCOUNT:role/snowflake-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://your-bucket/path/');

-- Get integration details for AWS setup
DESC STORAGE INTEGRATION s3_integration;

-- Look for these values:
-- STORAGE_AWS_IAM_USER_ARN: Use as Principal in IAM trust policy
-- STORAGE_AWS_EXTERNAL_ID: Use as Condition in IAM trust policy

-- Grant usage to role
GRANT USAGE ON INTEGRATION s3_integration TO ROLE SYSADMIN;
```
</details>

<details>
<summary>Hint 2: Testing Without Auto-Ingest</summary>

```sql
-- Create pipe without auto-ingest for testing
CREATE PIPE test_pipe
    AUTO_INGEST = FALSE  -- No S3 events required
AS
COPY INTO target_table FROM @stage_name;

-- Manually trigger pipe
ALTER PIPE test_pipe REFRESH;

-- Check status
SELECT SYSTEM$PIPE_STATUS('test_pipe');

-- Enable auto-ingest later
ALTER PIPE test_pipe SET PIPE_EXECUTION_PAUSED = TRUE;
-- Update AWS S3 event notification
ALTER PIPE test_pipe SET PIPE_EXECUTION_PAUSED = FALSE;
```
</details>

<details>
<summary>Hint 3: JSON Parsing from Stage</summary>

```sql
-- Query JSON directly from stage
SELECT
    $1:field_name::VARCHAR as field,
    $1:nested.property::FLOAT as nested_field,
    $1 as full_json
FROM @stage_name/file.json
(FILE_FORMAT => json_format);

-- Flatten arrays
SELECT
    value:id::INT as id,
    value:name::VARCHAR as name
FROM @stage_name/file.json,
LATERAL FLATTEN(input => $1:array_field);

-- Handle missing fields
SELECT
    $1:sensor_id::VARCHAR as sensor_id,
    COALESCE($1:temperature::FLOAT, -999.0) as temperature,  -- Default for nulls
    TRY_CAST($1:humidity AS FLOAT) as humidity  -- NULL if cast fails
FROM @stage_name;
```
</details>

<details>
<summary>Hint 4: Snowpipe Management</summary>

```sql
-- Show all pipes
SHOW PIPES;

-- Describe pipe (get SQS ARN)
DESC PIPE sensor_data_pipe;

-- Check pipe status
SELECT SYSTEM$PIPE_STATUS('sensor_data_pipe');
-- Returns JSON: {"executionState": "RUNNING", "pendingFileCount": 0}

-- Pause pipe
ALTER PIPE sensor_data_pipe SET PIPE_EXECUTION_PAUSED = TRUE;

-- Resume pipe
ALTER PIPE sensor_data_pipe SET PIPE_EXECUTION_PAUSED = FALSE;

-- Refresh pipe (manually check for new files)
ALTER PIPE sensor_data_pipe REFRESH;

-- Recreate pipe
CREATE OR REPLACE PIPE sensor_data_pipe ...;

-- Drop pipe
DROP PIPE sensor_data_pipe;
```
</details>

<details>
<summary>Hint 5: Troubleshooting Common Issues</summary>

```sql
-- Issue: No files loading
-- 1. Check pipe status
SELECT SYSTEM$PIPE_STATUS('sensor_data_pipe');

-- 2. Verify stage access
LIST @s3_sensor_stage;

-- 3. Check copy history for errors
SELECT * FROM table(information_schema.copy_history(
    TABLE_NAME => 'SENSOR_DATA',
    START_TIME => DATEADD(hour, -1, current_timestamp())
));

-- 4. Test manual COPY
COPY INTO sensor_data FROM @s3_sensor_stage
FILE_FORMAT = json_sensor_format
VALIDATION_MODE = 'RETURN_ERRORS';

-- Issue: S3 events not reaching pipe
-- 1. Verify SNS topic has SQS subscription
-- 2. Check S3 event notification configuration
-- 3. Verify IAM permissions on SNS topic
-- 4. Test by manually uploading file to S3

-- Issue: Parse errors
-- 1. Validate file format
SELECT * FROM table(
    validate(sensor_data, job_id => '_last')
);

-- 2. Query raw file
SELECT $1 FROM @s3_sensor_stage/problem_file.json;

-- 3. Use ON_ERROR='CONTINUE' to skip bad files
CREATE PIPE ... AS COPY INTO ... ON_ERROR='CONTINUE';
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-05-snowpipe-ingestion
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: S3 stage and file formats configured
✅ Task 2: Target table sensor_data created with schema
✅ Task 3: Snowpipe sensor_data_pipe created
✅ Task 4: S3 event notification documented (manual setup)
✅ Task 5: Test files loaded successfully (10+ files)
✅ Task 6: Monitoring queries working, cost: ~0.06 credits/1K files

🎉 Exercise 05 Complete! Snowpipe auto-ingestion operational.
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All stage, format, table, and pipe creation commands
2. `aws-setup-guide.md` - Complete AWS configuration steps
3. `monitoring-queries.sql` - Saved monitoring and alerting queries
4. `cost-analysis.md` - Document actual costs for your test loads
5. Screenshot of COPY_HISTORY showing successful loads

---

## Resources
- Snowflake Documentation: [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe)
- Snowflake Documentation: [External Stages](https://docs.snowflake.com/en/user-guide/data-load-s3)
- AWS Documentation: [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)
- Notebook: `notebooks/05-snowpipe.sql`
- Theory: `theory/concepts.md#snowpipe`
- S3 Setup Guide: `docs/aws-s3-snowpipe-setup.md`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 06: Secure Data Sharing (partner data distribution)
- Explore Snowpipe Streaming API (for sub-minute latency)
- Implement dead letter queue for failed files
- Set up CloudWatch/SNS alerts for pipe failures
- Compare Snowpipe vs. COPY command costs for your workload
