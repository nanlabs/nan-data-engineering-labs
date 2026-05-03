# Real-Time Analytics Platform - Project Checklist

Use this checklist to track your progress through the project. Check off items as you complete them.

---

## Phase 1: Infrastructure Setup

### 1.1 Core Infrastructure Definition

#### Terraform Configuration
- [ ] Configure AWS provider in `main.tf`
  - [ ] Set AWS region
  - [ ] Configure default tags
  - [ ] Set up backend for state management

#### Kinesis Data Stream
- [ ] Create Kinesis Data Stream resource in Terraform
  - [ ] Stream name: `ride-events-stream`
  - [ ] Configure shard count (start with 2)
  - [ ] Set retention period to 24 hours
  - [ ] Enable server-side encryption
  - [ ] Add stream mode configuration

#### DynamoDB Tables
- [ ] Create `rides_table` DynamoDB table
  - [ ] Set partition key: `ride_id` (String)
  - [ ] Set sort key: `timestamp` (Number)
  - [ ] Configure billing mode (on-demand or provisioned)
  - [ ] Enable point-in-time recovery
  - [ ] Enable encryption at rest
  - [ ] Create GSI on `status` attribute
  - [ ] Add TTL attribute configuration

- [ ] Create `metrics_table` DynamoDB table
  - [ ] Set partition key: `metric_name` (String)
  - [ ] Set sort key: `timestamp` (Number)
  - [ ] Configure billing mode
  - [ ] Enable point-in-time recovery
  - [ ] Enable encryption at rest
  - [ ] Add TTL for old metrics

#### S3 Buckets
- [ ] Create `raw-events-bucket`
  - [ ] Enable versioning
  - [ ] Enable server-side encryption (AES256 or KMS)
  - [ ] Configure bucket policy
  - [ ] Set up lifecycle policy (transition to IA after 30 days)
  - [ ] Enable access logging

- [ ] Create `processed-events-bucket`
  - [ ] Enable versioning
  - [ ] Enable server-side encryption
  - [ ] Configure bucket policy
  - [ ] Set up lifecycle policy
  - [ ] Enable access logging

- [ ] Create `athena-results-bucket`
  - [ ] Enable encryption
  - [ ] Configure lifecycle policy (delete after 7 days)

### 1.2 Variables and Outputs Configuration

#### Variables Definition
- [ ] Define `environment` variable (dev, staging, prod)
- [ ] Define `aws_region` variable with default
- [ ] Define `project_name` variable
- [ ] Define `kinesis_shard_count` variable
  - [ ] Add validation rule (min: 1, max: 10)
- [ ] Define `dynamodb_billing_mode` variable
- [ ] Define `tags` variable as map
- [ ] Add descriptions to all variables
- [ ] Create `terraform.tfvars` file with values

#### Outputs Configuration
- [ ] Export Kinesis stream ARN
- [ ] Export Kinesis stream name
- [ ] Export `rides_table` name and ARN
- [ ] Export `metrics_table` name and ARN
- [ ] Export S3 bucket names and ARNs
- [ ] Export AWS region
- [ ] Add descriptions to all outputs

### 1.3 Infrastructure Deployment

- [ ] Initialize Terraform
  ```bash
  cd infrastructure/terraform
  terraform init
  ```
- [ ] Validate Terraform configuration
  ```bash
  terraform validate
  ```
- [ ] Format Terraform files
  ```bash
  terraform fmt -recursive
  ```
- [ ] Generate and review execution plan
  ```bash
  terraform plan -out=tfplan
  ```
- [ ] Apply infrastructure changes
  ```bash
  terraform apply tfplan
  ```
- [ ] Verify resources in AWS Console
  - [ ] Kinesis stream is active
  - [ ] DynamoDB tables created
  - [ ] S3 buckets created
  - [ ] IAM roles and policies created

---

## Phase 2: Event Producer Development

### 2.1 Kinesis Utilities Implementation

#### KinesisProducer Class (`pipelines/producers/common/kinesis_utils.py`)
- [ ] Create `KinesisProducer` class
  - [ ] Initialize with stream name and boto3 client
  - [ ] Add configuration for batch size and retry logic

- [ ] Implement `put_record()` method
  - [ ] Accept event data as dictionary
  - [ ] Serialize event to JSON
  - [ ] Generate partition key (use ride_id or random)
  - [ ] Call Kinesis `put_record` API
  - [ ] Handle `ProvisionedThroughputExceededException`
  - [ ] Implement exponential backoff retry logic
  - [ ] Log successful sends
  - [ ] Return success/failure status

- [ ] Implement `batch_put_records()` method
  - [ ] Accept list of events
  - [ ] Batch records (max 500 per request)
  - [ ] Call Kinesis `put_records` API
  - [ ] Parse response for failed records
  - [ ] Retry failed records with backoff
  - [ ] Return success and failure counts
  - [ ] Log batch statistics

- [ ] Add utility methods
  - [ ] `_generate_partition_key()`: Create consistent partition keys
  - [ ] `_serialize_event()`: JSON serialization with date handling
  - [ ] `_retry_with_backoff()`: Generic retry logic

- [ ] Add logging configuration
- [ ] Add CloudWatch metrics publishing (optional)
- [ ] Add unit tests for utility functions

### 2.2 Ride Event Producer Implementation

#### Event Generation (`pipelines/producers/ride_event_producer.py`)
- [ ] Import required libraries (boto3, json, datetime, random, argparse)
- [ ] Define event schemas as dataclasses or dicts

- [ ] Create `RideEventGenerator` class
  - [ ] Initialize with configuration parameters
  - [ ] Define event type probabilities
  - [ ] Store state for ride lifecycles

- [ ] Implement `generate_ride_started_event()` method
  - [ ] Generate unique `ride_id` (UUID)
  - [ ] Generate random `driver_id` and `passenger_id`
  - [ ] Generate realistic pickup location (lat/lon)
  - [ ] Generate destination location
  - [ ] Set timestamp to current time
  - [ ] Set event type to `ride_started`
  - [ ] Store ride in active rides dictionary

- [ ] Implement `generate_ride_completed_event()` method
  - [ ] Select random active ride
  - [ ] Calculate ride duration (5-60 minutes)
  - [ ] Calculate distance (1-50 km)
  - [ ] Calculate fare based on distance and duration
  - [ ] Set completion timestamp
  - [ ] Set event type to `ride_completed`
  - [ ] Remove from active rides

- [ ] Implement `generate_ride_cancelled_event()` method
  - [ ] Select random active ride
  - [ ] Generate cancellation reason
  - [ ] Set cancellation timestamp
  - [ ] Set event type to `ride_cancelled`
  - [ ] Remove from active rides

- [ ] Implement main producer loop
  - [ ] Initialize KinesisProducer
  - [ ] Parse command-line arguments
  - [ ] Calculate sleep time based on target rate
  - [ ] Generate events continuously
  - [ ] Send to Kinesis in batches
  - [ ] Log statistics (events sent, errors, rate)
  - [ ] Implement graceful shutdown on SIGINT

#### CLI Configuration
- [ ] Add `--stream-name` argument (required)
- [ ] Add `--rate` argument for events per second (default: 10)
- [ ] Add `--duration` argument in seconds (default: run indefinitely)
- [ ] Add `--batch-size` argument (default: 100)
- [ ] Add `--region` argument (default: us-east-1)
- [ ] Add `--profile` argument for AWS profile

#### Testing
- [ ] Test producer with low rate (1 event/sec)
- [ ] Test producer with high rate (100 events/sec)
- [ ] Verify events in Kinesis Data Viewer
- [ ] Monitor CloudWatch metrics for Kinesis

---

## Phase 3: Stream Processing with Lambda

### 3.1 DynamoDB Utilities Implementation

#### DynamoDBClient Class (`pipelines/lambda/common/dynamodb_utils.py`)
- [ ] Create `DynamoDBClient` class
  - [ ] Initialize with table name and boto3 resource
  - [ ] Add retry configuration

- [ ] Implement `put_item()` method
  - [ ] Accept item as dictionary
  - [ ] Convert Python types to DynamoDB types
  - [ ] Call `put_item` API
  - [ ] Handle `ProvisionedThroughputExceededException`
  - [ ] Implement retry logic
  - [ ] Return success/failure

- [ ] Implement `get_item()` method
  - [ ] Accept key as dictionary
  - [ ] Call `get_item` API
  - [ ] Handle item not found
  - [ ] Return item or None

- [ ] Implement `query()` method
  - [ ] Accept partition key and optional filters
  - [ ] Build query expression
  - [ ] Handle pagination
  - [ ] Return list of items

- [ ] Implement `update_item()` method
  - [ ] Accept key and update attributes
  - [ ] Build update expression dynamically
  - [ ] Handle conditional updates
  - [ ] Return updated attributes

- [ ] Implement `batch_write()` method
  - [ ] Accept list of items
  - [ ] Batch in groups of 25
  - [ ] Handle unprocessed items
  - [ ] Retry with exponential backoff
  - [ ] Return success/failure counts

- [ ] Add utility methods
  - [ ] `_build_update_expression()`: Generate update expression
  - [ ] `_serialize_item()`: Convert to DynamoDB format
  - [ ] `_deserialize_item()`: Convert from DynamoDB format

### 3.2 Ride Processor Lambda Implementation

#### Lambda Handler (`pipelines/lambda/rides_processor/handler.py`)
- [ ] Import required libraries (json, boto3, base64, datetime, logging)
- [ ] Initialize DynamoDB and S3 clients
- [ ] Set up logging

- [ ] Implement `lambda_handler(event, context)` function
  - [ ] Log invocation details
  - [ ] Parse Kinesis records from event
  - [ ] Initialize counters for metrics

- [ ] Implement record processing loop
  - [ ] Decode base64 Kinesis data
  - [ ] Deserialize JSON event
  - [ ] Validate event schema
  - [ ] Route to appropriate handler based on event type

- [ ] Implement `process_ride_started(event)` function
  - [ ] Extract event fields
  - [ ] Create ride record for DynamoDB
  - [ ] Set status to `active`
  - [ ] Set start_time
  - [ ] Use `put_item()` to store in `rides_table`
  - [ ] Increment active rides counter in `metrics_table`
  - [ ] Log ride start

- [ ] Implement `process_ride_completed(event)` function
  - [ ] Get existing ride from DynamoDB
  - [ ] Update ride status to `completed`
  - [ ] Set end_time
  - [ ] Calculate duration
  - [ ] Add fare and distance
  - [ ] Use `update_item()` to update ride
  - [ ] Decrement active rides counter
  - [ ] Increment completed rides counter
  - [ ] Update rolling average fare metric
  - [ ] Update rolling completion rate metric
  - [ ] Log ride completion

- [ ] Implement `process_ride_cancelled(event)` function
  - [ ] Get existing ride from DynamoDB
  - [ ] Update ride status to `cancelled`
  - [ ] Set cancellation_time and reason
  - [ ] Use `update_item()` to update ride
  - [ ] Decrement active rides counter
  - [ ] Increment cancelled rides counter
  - [ ] Update cancellation rate metric
  - [ ] Log ride cancellation

- [ ] Implement S3 archival logic
  - [ ] Batch events by partition (date)
  - [ ] Format S3 key: `year=YYYY/month=MM/day=DD/hour=HH/batch_{uuid}.json`
  - [ ] Write batch to S3 using `put_object()`
  - [ ] Handle S3 errors gracefully

- [ ] Implement error handling
  - [ ] Wrap processing in try/except
  - [ ] Log errors with full context
  - [ ] Send failed records to SQS dead letter queue
  - [ ] Don't fail entire batch for single record error

- [ ] Implement CloudWatch metrics
  - [ ] Publish custom metric for processing latency
  - [ ] Publish custom metric for records processed
  - [ ] Publish custom metric for errors

- [ ] Return response
  - [ ] Return success count and failure count
  - [ ] Include batchItemFailures for partial batch failure

### 3.3 Lambda Infrastructure Configuration

#### Terraform Lambda Resources
- [ ] Create IAM role for Lambda
  - [ ] Add trust policy for Lambda service

- [ ] Create IAM policy for Lambda permissions
  - [ ] Kinesis: `GetRecords`, `GetShardIterator`, `DescribeStream`, `ListStreams`
  - [ ] DynamoDB: `PutItem`, `GetItem`, `UpdateItem`, `Query`
  - [ ] S3: `PutObject`, `GetObject`
  - [ ] CloudWatch Logs: `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`
  - [ ] CloudWatch Metrics: `PutMetricData`
  - [ ] Attach policy to role

- [ ] Package Lambda code
  - [ ] Create `lambda_package.zip` with handler and dependencies
  - [ ] Include common utilities in package

- [ ] Create Lambda function resource
  - [ ] Set runtime to `python3.9`
  - [ ] Set handler to `handler.lambda_handler`
  - [ ] Set timeout to 60 seconds
  - [ ] Set memory to 512 MB
  - [ ] Attach IAM role
  - [ ] Set environment variables:
    - [ ] `RIDES_TABLE_NAME`
    - [ ] `METRICS_TABLE_NAME`
    - [ ] `EVENTS_BUCKET_NAME`
    - [ ] `LOG_LEVEL`

- [ ] Create Kinesis event source mapping
  - [ ] Link to Kinesis stream
  - [ ] Set batch size to 100
  - [ ] Set starting position to `LATEST`
  - [ ] Enable bisect on function error
  - [ ] Set maximum retry attempts
  - [ ] Configure maximum record age

- [ ] Create CloudWatch log group
  - [ ] Set retention period (7 days)

- [ ] Create SQS dead letter queue (optional)
  - [ ] Link to Lambda function

#### Deployment
- [ ] Run `terraform apply` to deploy Lambda
- [ ] Verify Lambda function in AWS Console
- [ ] Verify event source mapping is enabled
- [ ] Test Lambda with sample event

---

## Phase 4: Analytics Layer Setup

### 4.1 AWS Glue Catalog Configuration

#### Glue Database
- [ ] Add Glue database resource to Terraform
  - [ ] Database name: `ride_analytics_db`
  - [ ] Add description
  - [ ] Add catalog ID

#### Glue Crawler
- [ ] Create IAM role for Glue Crawler
  - [ ] Add trust policy for Glue service
  - [ ] Add policy for S3 read access
  - [ ] Add policy for Glue catalog write access

- [ ] Add Glue crawler resource to Terraform
  - [ ] Crawler name: `ride-events-crawler`
  - [ ] Target S3 path: processed events bucket
  - [ ] Database name: `ride_analytics_db`
  - [ ] Set schedule: `cron(0 * * * ? *)` (hourly)
  - [ ] Configure schema change policy
  - [ ] Set table prefix (optional)

- [ ] Deploy Glue resources with Terraform
- [ ] Manually run crawler for first time
- [ ] Verify table created in Glue catalog
- [ ] Check table schema and partitions

### 4.2 Athena Query Development

#### Business Queries (`sql/athena/business_queries.sql`)

- [ ] **Query 1: Daily Ride Statistics**
  - [ ] Count total rides by date
  - [ ] Calculate average fare by date
  - [ ] Calculate average distance by date
  - [ ] Calculate average duration by date
  - [ ] Group by status (completed, cancelled)
  - [ ] Order by date descending
  - [ ] Add comments explaining query logic

- [ ] **Query 2: Peak Hours Analysis**
  - [ ] Extract hour from timestamp
  - [ ] Count rides by hour
  - [ ] Sum revenue by hour
  - [ ] Calculate average fare by hour
  - [ ] Order by ride count descending
  - [ ] Add visualization suggestion in comments

- [ ] **Query 3: Driver Performance**
  - [ ] Group by driver_id
  - [ ] Count completed rides per driver
  - [ ] Sum earnings per driver
  - [ ] Calculate average rating per driver
  - [ ] Calculate acceptance rate per driver
  - [ ] Rank drivers using RANK() window function
  - [ ] Filter to top 20 drivers
  - [ ] Add performance criteria in comments

- [ ] **Query 4: Cancellation Analysis**
  - [ ] Calculate overall cancellation rate
  - [ ] Group cancellations by reason
  - [ ] Count cancellations by reason
  - [ ] Calculate percentage of total for each reason
  - [ ] Show trend over time (daily cancellation rate)
  - [ ] Identify days with highest cancellation rate
  - [ ] Add insights in comments

- [ ] **Query 5: Real-Time Active Rides**
  - [ ] Filter for rides with status = 'active'
  - [ ] Calculate current ride duration
  - [ ] Estimate completion time based on average
  - [ ] Show pickup and destination locations
  - [ ] Order by start time
  - [ ] Add refresh frequency recommendation

#### Query Testing
- [ ] Create Athena workgroup in Terraform
- [ ] Set up S3 location for query results
- [ ] Test each query in Athena console
- [ ] Verify query results are correct
- [ ] Optimize queries for performance (partitioning, projections)
- [ ] Save queries in Athena console
- [ ] Document expected run time for each query

---

## Phase 5: Workflow Orchestration

### 5.1 Airflow DAG Development

#### Batch Processing DAG (`airflow/dags/batch_processing_dag.py`)
- [ ] Import Airflow modules (DAG, operators, sensors)
- [ ] Define default DAG arguments
  - [ ] Owner
  - [ ] Start date
  - [ ] Retries: 3
  - [ ] Retry delay: 5 minutes
  - [ ] Email on failure

- [ ] Create DAG definition
  - [ ] DAG ID: `ride_analytics_batch_processing`
  - [ ] Schedule interval: `@daily` (0 0 * * *)
  - [ ] Catchup: False
  - [ ] Max active runs: 1
  - [ ] Tags: ['ride_analytics', 'batch']

- [ ] **Task 1: Run Glue Crawler**
  - [ ] Use `AwsGlueCrawlerOperator`
  - [ ] Configure crawler name
  - [ ] Set wait for completion to True

- [ ] **Task 2: Daily Aggregation Query**
  - [ ] Use `AthenaOperator`
  - [ ] Execute daily statistics query
  - [ ] Configure database and output location
  - [ ] Set query execution timeout

- [ ] **Task 3: Store Aggregation Results**
  - [ ] Use `S3CreateObjectOperator` or PythonOperator
  - [ ] Read Athena query results
  - [ ] Transform to desired format (Parquet)
  - [ ] Write to S3 analytics bucket

- [ ] **Task 4: Update CloudWatch Metrics**
  - [ ] Use `PythonOperator`
  - [ ] Read aggregation results
  - [ ] Publish custom metrics to CloudWatch
  - [ ] Metrics: total_daily_rides, daily_revenue, avg_daily_fare

- [ ] **Task 5: Send Summary Email**
  - [ ] Use `EmailOperator`
  - [ ] Format email with daily summary
  - [ ] Include key metrics
  - [ ] Attach visualization or link to dashboard

- [ ] Define task dependencies
  ```python
  task1 >> task2 >> task3 >> task4 >> task5
  ```

- [ ] Add task documentation with docstrings
- [ ] Implement error handling and alerting

### 5.2 Airflow Deployment

#### Docker Compose Configuration
- [ ] Update `docker-compose.yml` in project root
  - [ ] Add Airflow services (webserver, scheduler, worker)
  - [ ] Configure PostgreSQL database for Airflow metadata
  - [ ] Configure Redis for Celery executor (if using)
  - [ ] Mount DAGs folder
  - [ ] Set environment variables for AWS credentials
  - [ ] Configure volumes for logs and plugins

- [ ] Createairflow.cfg` with custom settings (optional)
- [ ] Create `requirements.txt` for Airflow with AWS providers

#### Airflow Initialization
- [ ] Start Airflow services
  ```bash
  docker-compose up -d
  ```
- [ ] Initialize Airflow database
  ```bash
  docker-compose exec airflow-webserver airflow db init
  ```
- [ ] Create Airflow admin user
  ```bash
  docker-compose exec airflow-webserver airflow users create \
    --username admin --password admin --firstname Admin --lastname User \
    --role Admin --email admin@example.com
  ```
- [ ] Configure AWS connection in Airflow UI
- [ ] Verify DAG appears in Airflow UI
- [ ] Enable DAG
- [ ] Trigger manual DAG run to test
- [ ] Monitor DAG execution and task logs

---

## Phase 6: Monitoring and Dashboards

### 6.1 CloudWatch Dashboard Configuration

#### Dashboard Definition (`monitoring/cloudwatch/ride_analytics_dashboard.json`)
- [ ] Create dashboard JSON structure
- [ ] Set dashboard name and region

- [ ] Add Kinesis metrics widgets
  - [ ] Incoming records count (sum)
  - [ ] Incoming bytes (sum)
  - [ ] GetRecords.IteratorAgeMilliseconds (average)
  - [ ] WriteProvisionedThroughputExceeded (sum)

- [ ] Add Lambda metrics widgets
  - [ ] Invocations count (sum)
  - [ ] Errors count (sum)
  - [ ] Duration (average, max)
  - [ ] Throttles (sum)
  - [ ] ConcurrentExecutions (max)

- [ ] Add DynamoDB metrics widgets
  - [ ] ConsumedReadCapacityUnits (sum)
  - [ ] ConsumedWriteCapacityUnits (sum)
  - [ ] UserErrors (sum)
  - [ ] SystemErrors (sum)
  - [ ] ThrottledRequests (sum)

- [ ] Add custom business metrics widgets
  - [ ] Active rides (gauge - latest value)
  - [ ] Completion rate (percentage)
  - [ ] Average fare (line chart)
  - [ ] Total daily revenue (number)
  - [ ] Cancellation rate (percentage)

- [ ] Add S3 metrics widgets
  - [ ] Number of objects
  - [ ] Bucket size

- [ ] Configure widget properties
  - [ ] Set appropriate time periods
  - [ ] Configure y-axis settings
  - [ ] Add annotations for thresholds
  - [ ] Set widget positions and sizes

#### Dashboard Deployment
- [ ] Deploy dashboard using AWS CLI
  ```bash
  aws cloudwatch put-dashboard \
    --dashboard-name RideAnalyticsMonitoring \
    --dashboard-body file://monitoring/cloudwatch/ride_analytics_dashboard.json
  ```
- [ ] Verify dashboard in CloudWatch console
- [ ] Test all widgets display data correctly
- [ ] Share dashboard link with team

### 6.2 CloudWatch Alarms Configuration

#### Terraform Alarm Resources
- [ ] **Alarm 1: High Lambda Error Rate**
  - [ ] Create SNS topic for alerts
  - [ ] Create CloudWatch alarm
  - [ ] Metric: Lambda Errors
  - [ ] Threshold: Error rate > 5%
  - [ ] Evaluation periods: 2 of 5 minutes
  - [ ] Actions: Send to SNS topic

- [ ] **Alarm 2: DynamoDB Throttling**
  - [ ] Metric: ThrottledRequests
  - [ ] Threshold: > 0
  - [ ] Evaluation periods: 1
  - [ ] Actions: Send to SNS topic

- [ ] **Alarm 3: High Kinesis Iterator Age**
  - [ ] Metric: GetRecords.IteratorAgeMilliseconds
  - [ ] Threshold: > 60000 (1 minute)
  - [ ] Evaluation periods: 2
  - [ ] Actions: Send to SNS topic

- [ ] **Alarm 4: Low Completion Rate**
  - [ ] Metric: Custom metric for completion rate
  - [ ] Threshold: < 80%
  - [ ] Evaluation periods: 3 of 15 minutes
  - [ ] Actions: Send to SNS topic and escalation

- [ ] Subscribe email to SNS topic
- [ ] Test alarms by triggering threshold conditions

### 6.3 Grafana Dashboard (Optional)

#### Grafana Setup
- [ ] Add Grafana service to `docker-compose.yml`
- [ ] Configure volume for Grafana data persistence
- [ ] Start Grafana container
- [ ] Access Grafana UI at `http://localhost:3000`
- [ ] Change default admin password

#### Dashboard Creation
- [ ] Add CloudWatch datasource
  - [ ] Configure AWS credentials
  - [ ] Test connection

- [ ] Create new dashboard: "Ride Analytics Operational"
  - [ ] **Panel 1**: Real-time ride count (stat panel)
  - [ ] **Panel 2**: Revenue trend last 24h (time series)
  - [ ] **Panel 3**: Top drivers leaderboard (table)
  - [ ] **Panel 4**: Geographic heatmap (map panel with plugins)
  - [ ] **Panel 5**: Ride status distribution (pie chart)
  - [ ] **Panel 6**: Average fare by hour (bar chart)

- [ ] Configure panel refresh intervals
- [ ] Add dashboard variables for filtering (date range, region)
- [ ] Export dashboard JSON
- [ ] Save to `monitoring/grafana/ride_metrics_dashboard.json`

---

## Phase 7: Testing and Validation

### 7.1 Infrastructure Tests

#### Test File (`validation/test_infrastructure.py`)
- [ ] Import pytest and boto3
- [ ] Create fixtures for AWS clients

- [ ] Test: Kinesis stream exists
  - [ ] Use boto3 to describe stream
  - [ ] Assert stream status is ACTIVE
  - [ ] Assert shard count matches configuration

- [ ] Test: DynamoDB tables exist
  - [ ] Describe `rides_table`
  - [ ] Assert table status is ACTIVE
  - [ ] Verify partition key and sort key schema
  - [ ] Verify GSI exists
  - [ ] Describe `metrics_table`
  - [ ] Assert table status is ACTIVE

- [ ] Test: S3 buckets exist and configured
  - [ ] List buckets and verify names
  - [ ] Check versioning is enabled
  - [ ] Check encryption is enabled
  - [ ] Verify lifecycle policies exist

- [ ] Test: Lambda function deployed
  - [ ] Get Lambda function configuration
  - [ ] Assert runtime is python3.9
  - [ ] Assert environment variables are set
  - [ ] Verify event source mapping exists and enabled

- [ ] Test: IAM permissions are correct
  - [ ] Simulate Lambda role permissions
  - [ ] Assert can write to DynamoDB
  - [ ] Assert can write to S3
  - [ ] Assert can read from Kinesis

### 7.2 Pipeline Tests

#### Test File (`validation/test_streaming_pipeline.py`)
- [ ] Import required libraries and fixtures

- [ ] Test: Producer can send to Kinesis
  - [ ] Generate test event
  - [ ] Use KinesisProducer to send event
  - [ ] Assert no errors
  - [ ] Verify event in stream using GetRecords

- [ ] Test: Lambda processes events correctly
  - [ ] Send ride_started event
  - [ ] Wait for Lambda processing (5 seconds)
  - [ ] Query DynamoDB for ride record
  - [ ] Assert ride exists with correct status

- [ ] Test: Ride lifecycle end-to-end
  - [ ] Send ride_started event
  - [ ] Wait for processing
  - [ ] Send ride_completed event
  - [ ] Wait for processing
  - [ ] Query DynamoDB for final ride state
  - [ ] Assert status is 'completed'
  - [ ] Assert fare and duration calculated

- [ ] Test: Data written to S3
  - [ ] Send batch of events
  - [ ] Wait for Lambda processing
  - [ ] List S3 objects in bucket
  - [ ] Assert objects exist with correct partition structure
  - [ ] Download object and verify content

- [ ] Test: End-to-end latency
  - [ ] Record timestamp before sending event
  - [ ] Send event to Kinesis
  - [ ] Poll DynamoDB until record appears
  - [ ] Calculate latency
  - [ ] Assert latency < 5 seconds

- [ ] Test: Metrics updated correctly
  - [ ] Query `metrics_table` for active_rides counter
  - [ ] Send ride_started event
  - [ ] Wait for processing
  - [ ] Query metrics again
  - [ ] Assert counter incremented

### 7.3 Data Quality Tests

#### Test File (`validation/test_data_quality.py`)
- [ ] Import pytest and data validation libraries

- [ ] Test: Event schema validation
  - [ ] Define JSON schema for each event type
  - [ ] Generate test events
  - [ ] Validate against schema using jsonschema
  - [ ] Assert validation passes for valid events
  - [ ] Assert validation fails for invalid events

- [ ] Test: No null values in critical fields
  - [ ] Query sample of records from DynamoDB
  - [ ] Check critical fields (ride_id, status, timestamp)
  - [ ] Assert none are null or empty

- [ ] Test: Data accuracy - fare calculation
  - [ ] Generate ride with known distance and duration
  - [ ] Process through Lambda
  - [ ] Retrieve calculated fare
  - [ ] Assert fare matches expected calculation

- [ ] Test: Data freshness
  - [ ] Query most recent records from DynamoDB
  - [ ] Check timestamp of latest record
  - [ ] Assert timestamp is within last 5 minutes

- [ ] Test: No duplicate ride IDs
  - [ ] Query all ride_ids from DynamoDB
  - [ ] Check for duplicates
  - [ ] Assert all ride_ids are unique

- [ ] Test: Valid status transitions
  - [ ] Track ride lifecycle
  - [ ] Assert status only transitions from:
    - [ ] active -> completed
    - [ ] active -> cancelled
  - [ ] Assert no invalid transitions

#### Run All Tests
- [ ] Execute pytest
  ```bash
  cd validation
  pytest -v --tb=short
  ```
- [ ] Review test results
- [ ] Fix any failing tests
- [ ] Aim for test first with this:
  - [ ] All infrastructure tests pass
  - [ ] All pipeline tests pass
  - [ ] All data quality tests pass

---

## Phase 8: Deployment and Optimization

### 8.1 Production Deployment

#### Production Configuration
- [ ] Create `prod.tfvars` file
  - [ ] Set environment = "prod"
  - [ ] Increase Kinesis shard count (4-8)
  - [ ] Set DynamoDB to on-demand or higher provisioned capacity
  - [ ] Enable DynamoDB autoscaling
  - [ ] Configure backup schedules
  - [ ] Enable cross-region replication (optional)

- [ ] Create production Terraform workspace
  ```bash
  terraform workspace new prod
  terraform workspace select prod
  ```

- [ ] Review production changes
  ```bash
  terraform plan -var-file=prod.tfvars
  ```

- [ ] Deploy to production
  ```bash
  terraform apply -var-file=prod.tfvars
  ```

- [ ] Verify all resources deployed correctly
- [ ] Update DNS/endpoints if needed
- [ ] Configure production monitoring alerts

### 8.2 Performance Optimization

#### Kinesis Optimization
- [ ] Monitor Kinesis metrics for hot shards
- [ ] Calculate required throughput (MB/s, records/s)
- [ ] Right-size shard count
  - [ ] Rule: 1 MB/s write, 2 MB/s read per shard
- [ ] Consider enhanced fan-out for multiple consumers
- [ ] Test with load testing tool

#### Lambda Optimization
- [ ] Enable AWS X-Ray for tracing
- [ ] Analyze Lambda execution traces
- [ ] Review memory usage with CloudWatch Insights
  ```sql
  filter @type = "REPORT"
  | stats max(@memorySize / 1024 / 1024) as provisioned_memory_mb,
          max(@maxMemoryUsed / 1024 / 1024) as max_memory_used_mb
  ```
- [ ] Adjust memory based on profiling
- [ ] Optimize cold start if needed
  - [ ] Consider provisioned concurrency
  - [ ] Minimize import statements
  - [ ] Use Lambda layers for dependencies
- [ ] Set appropriate reserved concurrency
- [ ] Configure Lambda timeout optimally

#### DynamoDB Optimization
- [ ] Review DynamoDB access patterns
- [ ] Analyze hot partition keys
- [ ] Optimize GSI queries
- [ ] Consider adding DynamoDB Accelerator (DAX) if read-heavy
  - [ ] Create DAX cluster in Terraform
  - [ ] Update Lambda to use DAX endpoint
- [ ] Review and optimize item size (< 400 KB)
- [ ] Configure DynamoDB auto-scaling policies
  - [ ] Set target utilization (70%)
  - [ ] Set min/max capacity

#### S3 Optimization
- [ ] Review object size distribution
- [ ] Implement S3 Select for query optimization
- [ ] Enable S3 Transfer Acceleration if uploading from far regions
- [ ] Use S3 Intelligent-Tiering for cost optimization
- [ ] Compress objects before upload (gzip)
- [ ] Optimize Parquet file size (128 MB - 1 GB)

### 8.3 Cost Optimization

#### Cost Analysis
- [ ] Enable AWS Cost Explorer
- [ ] Tag all resources with project and environment tags
- [ ] Review cost breakdown by service
- [ ] Identify top cost drivers

#### Optimization Actions
- [ ] **Kinesis**: Right-size shard count for actual throughput
- [ ] **Lambda**:
  - [ ] Optimize memory to reduce duration
  - [ ] Review timeout settings
  - [ ] Use ARM architecture (Graviton2) if compatible
- [ ] **DynamoDB**:
  - [ ] Switch to on-demand if traffic is unpredictable
  - [ ] Review and delete unused GSIs
  - [ ] Enable automatic backups only if needed
- [ ] **S3**:
  - [ ] Implement lifecycle policies
    - [ ] Transition to S3 IA after 30 days
    - [ ] Transition to Glacier after 90 days
    - [ ] Delete after 1 year (or as needed)
  - [ ] Delete incomplete multipart uploads after 7 days
  - [ ] Compress data before storage
- [ ] **CloudWatch**:
  - [ ] Reduce log retention period (7 days for dev,  30 days for prod)
  - [ ] Filter logs before sending to CloudWatch
  - [ ] Use CloudWatch Logs Insights efficiently

#### Cost Monitoring
- [ ] Set up AWS Budget
  - [ ] Monthly budget threshold
  - [ ] Alert at 80% and 100%
- [ ] Create cost anomaly detection alert
- [ ] Schedule weekly cost review
- [ ] Document cost optimization opportunities

---

## Final Checklist

### Documentation
- [ ] Complete README.md with:
  - [ ] Architecture diagram (draw.io, lucidchart, or ASCII)
  - [ ] Setup instructions
  - [ ] Usage examples
  - [ ] Troubleshooting section

- [ ] Create/update ARCHITECTURE-DECISIONS.md
  - [ ] Document key design decisions
  - [ ] Explain trade-offs
  - [ ] Include alternatives considered

- [ ] Document Lambda functions
  - [ ] Add docstrings to all functions
  - [ ] Comment complex logic
  - [ ] Include usage examples

- [ ] Create deployment guide
  - [ ] Step-by-step deployment instructions
  - [ ] Prerequisites checklist
  - [ ] Rollback procedures
  - [ ] Post-deployment verification steps

- [ ] Create troubleshooting guide
  - [ ] Common issues and solutions
  - [ ] How to check logs
  - [ ] How to debug Lambda
  - [ ] Contact information for support

### Evidence Collection
- [ ] Take screenshots of:
  - [ ] Kinesis stream with active shards
  - [ ] DynamoDB tables with sample data
  - [ ] Lambda function configuration
  - [ ] CloudWatch dashboard showing metrics
  - [ ] Athena query results
  - [ ] Airflow DAG graph
  - [ ] Grafana dashboard (if implemented)
  - [ ] Cost Explorer showing project costs

- [ ] Record test results
  - [ ] Save pytest output to file
  - [ ] Include test coverage report
  - [ ] Document any test failures and resolutions

- [ ] Collect performance metrics
  - [ ] End-to-end latency measurements
  - [ ] Throughput test results
  - [ ] Lambda execution duration statistics
  - [ ] Cost per million events processed

### Video Demo
- [ ] Record 5-10 minute video demonstration
  - [ ] Start with architecture overview (slides or diagram)
  - [ ] Show AWS Console with deployed resources
  - [ ] Demo producer sending events (terminal)
  - [ ] Show CloudWatch dashboard updating in real-time
  - [ ] Run Athena query and show results
  - [ ] Show Airflow DAG in UI and trigger run
  - [ ] Briefly show test results
  - [ ] Wrap up with lessons learned

- [ ] Upload video to YouTube/Google Drive
- [ ] Make video accessible (public or unlisted)
- [ ] Include link in submission

### Submission Preparation
- [ ] Clean up code
  - [ ] Remove commented-out code
  - [ ] Remove debug print statements
  - [ ] Format code consistently (black, prettier)
  - [ ] Run linter (pylint, flake8)

- [ ] Commit all changes to Git
  - [ ] Write clear commit messages
  - [ ] Create logical commits (not one big commit)
  - [ ] Tag final version: `git tag v1.0`

- [ ] Push to GitHub/GitLab
  - [ ] Ensure repository is accessible
  - [ ] Update .gitignore (exclude .env,tfstate, venv)
  - [ ] Add README in root of repository

- [ ] Prepare submission package
  - [ ] Repository URL
  - [ ] Video demonstration URL
  - [ ] Documentation PDFs (optional)
  - [ ] Architecture diagram PNG/PDF

### Final Review
- [ ] Review all checklist items completed
- [ ] Re-run all tests one final time
- [ ] Verify production deployment still working
- [ ] Review submission requirements
- [ ] Submit by deadline

---

**Congratulations on completing the Real-Time Analytics Platform checkpoint project!**
