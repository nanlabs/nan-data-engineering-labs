# Real-Time Analytics Platform - Starter Template

## Overview

Welcome to the Real-Time Analytics Platform checkpoint project! This hands-on project challenges you to build a complete end-to-end streaming analytics system using AWS services and modern data engineering tools.

## Learning Objectives

By completing this project, you will:

- Design and implement a real-time data streaming architecture using AWS Kinesis
- Develop serverless data processing pipelines with AWS Lambda
- Store and manage streaming data using DynamoDB and S3
- Build analytics queries using Amazon Athena and Glue
- Orchestrate workflows using Apache Airflow
- Create monitoring dashboards with CloudWatch and Grafana
- Implement data quality checks and validation
- Deploy infrastructure as code using Terraform
- Apply best practices for security, cost optimization, and performance

## Project Scenario

You are building a real-time analytics platform for a ride-sharing company. The system needs to:

1. Ingest ride events (started, completed, cancelled) in real-time
2. Process events to calculate ride lifecycle metrics
3. Store processed data in DynamoDB and S3 data lake
4. Provide real-time dashboards showing active rides, completion rates
5. Run batch analytics on historical data
6. Ensure data quality and alerting

## Architecture Components

### Data Ingestion Layer
- **Kinesis Data Streams**: Ingest ride events at scale
- **Producer Applications**: Simulate ride event generation

### Processing Layer
- **Lambda Functions**: Process events in real-time
- **DynamoDB**: Store ride state and metrics
- **S3**: Archive raw and processed events

### Analytics Layer
- **AWS Glue**: Catalog data in S3
- **Amazon Athena**: Query historical ride data
- **CloudWatch Metrics**: Real-time monitoring

### Orchestration Layer
- **Apache Airflow**: Scheduled batch jobs
- **AWS EventBridge**: Event-driven workflows

### Visualization Layer
- **CloudWatch Dashboards**: Operational metrics
- **Grafana**: Custom analytics dashboards

## Getting Started

### Prerequisites

Before starting this project, ensure you have:

- AWS Account with appropriate permissions
- Terraform installed (v1.0+)
- Python 3.9+ installed
- Docker and Docker Compose installed
- AWS CLI configured with credentials
- Git for version control

### Environment Setup

1. **Clone and Navigate to Project**
   ```bash
   cd /path/to/module-checkpoint-02-realtime-analytics-platform
   cd starter-template
   ```

2. **Create Python Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set AWS Environment Variables**
   ```bash
   export AWS_PROFILE=your-profile
   export AWS_REGION=us-east-1
   export ENVIRONMENT=dev
   ```

5. **Initialize Terraform**
   ```bash
   cd infrastructure/terraform
   terraform init
   ```

### Project Structure

```
starter-template/
├── README.md                          # This file
├── CHECKLIST.md                       # Task completion checklist
├── requirements.txt                   # Python dependencies
├── infrastructure/
│   └── terraform/                     # Infrastructure as Code
│       ├── main.tf                    # Main infrastructure definitions
│       ├── variables.tf               # Variable declarations
│       └── outputs.tf                 # Output values
├── pipelines/
│   ├── producers/                     # Event producer applications
│   │   ├── ride_event_producer.py    # Generate ride events
│   │   └── common/
│   │       └── kinesis_utils.py      # Kinesis helper functions
│   └── lambda/                        # Lambda function code
│       ├── rides_processor/
│       │   └── handler.py            # Process ride events
│       └── common/
│           └── dynamodb_utils.py     # DynamoDB helper functions
├── sql/
│   └── athena/                        # Athena SQL queries
│       └── business_queries.sql      # Analytics queries
├── airflow/
│   └── dags/                         # Airflow DAG definitions
├── monitoring/
│   ├── cloudwatch/                   # CloudWatch dashboard configs
│   └── grafana/                      # Grafana dashboard configs
└── validation/                        # Testing and validation
    ├── test_infrastructure.py
    ├── test_streaming_pipeline.py
    └── test_data_quality.py
```

## Implementation Steps

Follow these phases in order. Complete each phase before moving to the next. Use CHECKLIST.md to track your progress.

---

### **Phase 1: Infrastructure Setup** (Estimated Time: 3-4 hours)

#### 1.1 Define Core Infrastructure

**TODO**: Complete `infrastructure/terraform/main.tf`

1. Configure AWS provider with region and tags
2. Create Kinesis Data Stream for ride events:
   - Stream name: `ride-events-stream`
   - Shard count: Start with 2 shards
   - Retention period: 24 hours
   - Enable encryption
3. Create DynamoDB tables:
   - `rides_table`: Store ride state and metadata
     - Partition key: `ride_id`
     - Sort key: `timestamp`
     - Global secondary index on `status`
   - `metrics_table`: Store aggregated metrics
     - Partition key: `metric_name`
     - Sort key: `timestamp`
4. Create S3 buckets:
   - `raw-events-bucket`: Store raw event data
   - `processed-events-bucket`: Store processed data
   - Enable versioning and encryption
   - Set lifecycle policies

#### 1.2 Configure Variables and Outputs

**TODO**: Complete `infrastructure/terraform/variables.tf`
- Define variables for environment, region, project name
- Add validation rules for critical variables
- Set appropriate defaults

**TODO**: Complete `infrastructure/terraform/outputs.tf`
- Export Kinesis stream ARN and name
- Export DynamoDB table names
- Export S3 bucket names
- Export Lambda function ARNs

#### 1.3 Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform plan -out=tfplan
terraform apply tfplan
```

**Validation**: Verify resources in AWS Console

---

### **Phase 2: Event Producer Development** (Estimated Time: 2-3 hours)

#### 2.1 Implement Kinesis Utilities

**TODO**: Complete `pipelines/producers/common/kinesis_utils.py`

1. Create `KinesisProducer` class
2. Implement `put_record()` method:
   - Accept event data as dict
   - Serialize to JSON
   - Generate partition key
   - Send to Kinesis stream
   - Handle errors with exponential backoff
3. Implement `batch_put_records()` method:
   - Accept list of events
   - Batch up to 500 records
   - Implement retry logic for failed records
   - Return success/failure counts
4. Add logging and metrics

#### 2.2 Build Ride Event Producer

**TODO**: Complete `pipelines/producers/ride_event_producer.py`

1. Generate realistic ride events:
   - Event types: `ride_started`, `ride_completed`, `ride_cancelled`
   - Fields: `ride_id`, `driver_id`, `passenger_id`, `location`, `timestamp`, `fare`, `distance`
2. Implement event generation logic:
   - Random sampling of event types
   - Realistic time intervals
   - Geographic coordinates
3. Send events to Kinesis stream using KinesisProducer
4. Add CLI arguments for:
   - Event rate (events per second)
   - Duration (how long to run)
   - Stream name
5. Implement graceful shutdown

**Run Producer**:
```bash
python pipelines/producers/ride_event_producer.py \
  --stream-name ride-events-stream \
  --rate 10 \
  --duration 3600
```

---

### **Phase 3: Stream Processing with Lambda** (Estimated Time: 4-5 hours)

#### 3.1 Implement DynamoDB Utilities

**TODO**: Complete `pipelines/lambda/common/dynamodb_utils.py`

1. Create `DynamoDBClient` class
2. Implement CRUD operations:
   - `put_item()`: Insert or update item
   - `get_item()`: Retrieve item by key
   - `query()`: Query with filters
   - `update_item()`: Partial updates
   - `batch_write()`: Batch insert/update
3. Add error handling and retries
4. Implement conditional writes for consistency

#### 3.2 Build Ride Processor Lambda

**TODO**: Complete `pipelines/lambda/rides_processor/handler.py`

1. Implement `lambda_handler()` function:
   - Parse Kinesis records from event
   - Decode base64 data
   - Deserialize JSON events
2. Process each ride event:
   - **ride_started**: Create new ride record in DynamoDB
   - **ride_completed**: Update ride with completion data, calculate fare, duration
   - **ride_cancelled**: Update ride status, record cancellation reason
3. Update metrics in DynamoDB:
   - Total rides counter
   - Active rides counter
   - Average fare calculation
   - Completion rate
4. Archive events to S3:
   - Partition by date: `s3://bucket/year=2026/month=03/day=10/`
   - Store as JSON or Parquet
5. Add error handling and dead letter queue
6. Log key metrics to CloudWatch

#### 3.3 Configure Lambda

**TODO**: Update `infrastructure/terraform/main.tf` with Lambda configuration

1. Create Lambda function resource:
   - Runtime: Python 3.9
   - Handler: `handler.lambda_handler`
   - Timeout: 60 seconds
   - Memory: 512 MB
2. Create IAM role with permissions:
   - Read from Kinesis
   - Write to DynamoDB
   - Write to S3
   - Write to CloudWatch Logs
3. Add Kinesis event source mapping:
   - Batch size: 100 records
   - Starting position: LATEST
   - Enable bisect on function error
4. Configure environment variables
5. Deploy Lambda code using zip file

---

### **Phase 4: Analytics Layer Setup** (Estimated Time: 2-3 hours)

#### 4.1 Configure AWS Glue Catalog

**TODO**: Update `infrastructure/terraform/main.tf` with Glue resources

1. Create Glue database: `ride_analytics_db`
2. Create Glue crawler:
   - Target: S3 processed events bucket
   - Schedule: Hourly
   - Output database: `ride_analytics_db`
3. Run crawler to catalog tables

#### 4.2 Develop Athena Queries

**TODO**: Complete `sql/athena/business_queries.sql`

1. **Query 1: Daily Ride Statistics**
   - Count total rides per day
   - Calculate average fare, distance, duration
   - Group by date and status

2. **Query 2: Peak Hours Analysis**
   - Identify busiest hours of the day
   - Show ride counts by hour
   - Calculate hourly revenue

3. **Query 3: Driver Performance**
   - Rank drivers by number of completed rides
   - Calculate average rating per driver
   - Show earnings per driver

4. **Query 4: Cancellation Analysis**
   - Calculate cancellation rate
   - Identify top cancellation reasons
   - Show cancellation trends over time

5. **Query 5: Real-Time Active Rides**
   - Show currently active rides
   - Display ride duration so far
   - Show estimated completion time

#### 4.3 Test Queries

```bash
aws athena start-query-execution \
  --query-string "$(cat sql/athena/business_queries.sql | grep -A 10 'Daily Ride Statistics')" \
  --result-configuration "OutputLocation=s3://your-athena-results-bucket/" \
  --query-execution-context "Database=ride_analytics_db"
```

---

### **Phase 5: Workflow Orchestration** (Estimated Time: 2-3 hours)

#### 5.1 Create Airflow DAGs

**TODO**: Create `airflow/dags/batch_processing_dag.py`

1. Define DAG:
   - Schedule: Daily at midnight
   - Catchup: False
   - Max active runs: 1

2. Tasks:
   - **Task 1**: Run Glue crawler to update catalog
   - **Task 2**: Execute daily aggregation Athena query
   - **Task 3**: Store results in S3
   - **Task 4**: Update CloudWatch custom metrics
   - **Task 5**: Send summary email report

3. Set task dependencies and retries

#### 5.2 Deploy Airflow

**TODO**: Update `docker-compose.yml` for Airflow

```bash
docker-compose up -d
```

Access Airflow UI: `http://localhost:8080`

---

### **Phase 6: Monitoring and Dashboards** (Estimated Time: 2-3 hours)

#### 6.1 CloudWatch Dashboards

**TODO**: Create `monitoring/cloudwatch/ride_analytics_dashboard.json`

1. Add widgets for:
   - Kinesis incoming records per second
   - Lambda invocations and errors
   - DynamoDB read/write capacity
   - Active rides gauge
   - Completion rate percentage
   - Average fare line chart

2. Deploy dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name RideAnalytics \
  --dashboard-body file://monitoring/cloudwatch/ride_analytics_dashboard.json
```

#### 6.2 CloudWatch Alarms

**TODO**: Update `infrastructure/terraform/main.tf` with alarms

1. Lambda error rate > 5%
2. DynamoDB throttled requests > 0
3. Kinesis iterator age > 1 minute
4. Low completion rate < 80%

#### 6.3 Grafana Dashboards

**TODO**: Create `monitoring/grafana/ride_metrics_dashboard.json`

1. Configure CloudWatch data source
2. Create panels for business metrics:
   - Real-time ride count
   - Revenue trends
   - Geographic heatmap
   - Driver leaderboard

---

### **Phase 7: Testing and Validation** (Estimated Time: 2-3 hours)

#### 7.1 Infrastructure Tests

**TODO**: Complete `validation/test_infrastructure.py`

1. Test Kinesis stream exists and is active
2. Test DynamoDB tables exist with correct schema
3. Test S3 buckets exist with encryption
4. Test Lambda functions are deployed
5. Test IAM permissions are correct

#### 7.2 Pipeline Tests

**TODO**: Complete `validation/test_streaming_pipeline.py`

1. Test producer can send events to Kinesis
2. Test Lambda processes events correctly
3. Test data is written to DynamoDB
4. Test events are archived to S3
5. Test end-to-end latency < 5 seconds

#### 7.3 Data Quality Tests

**TODO**: Complete `validation/test_data_quality.py`

1. Test schema validation for events
2. Test data completeness (no null critical fields)
3. Test data accuracy (calculations correct)
4. Test data freshness (recent timestamp)
5. Test duplicate detection

**Run Tests**:
```bash
pytest validation/ -v
```

---

### **Phase 8: Deployment and Optimization** (Estimated Time: 2-3 hours)

#### 8.1 Production Deployment

1. Create production Terraform workspace:
```bash
terraform workspace new prod
terraform workspace select prod
```

2. Update variables for production:
   - Increase Kinesis shard count
   - Enable DynamoDB autoscaling
   - Configure backup schedules
   - Set up cross-region replication

3. Deploy to production:
```bash
terraform apply -var-file=prod.tfvars
```

#### 8.2 Performance Optimization

**TODO**: Optimize system performance

1. Kinesis:
   - Right-size shard count based on throughput
   - Enable enhanced fan-out if needed

2. Lambda:
   - Optimize memory based on profiling
   - Enable reserved concurrency if needed
   - Reduce cold starts with provisioned concurrency

3. DynamoDB:
   - Optimize read/write capacity
   - Add caching layer (DAX) if needed
   - Review access patterns and indexes

4. S3:
   - Configure S3 lifecycle policies
   - Use S3 Select for query optimization
   - Enable S3 Transfer Acceleration

#### 8.3 Cost Optimization

**TODO**: Review and optimize costs

1. Set up AWS Cost Explorer tags
2. Review Kinesis shard hours usage
3. Optimize Lambda memory and timeout
4. Configure DynamoDB on-demand if appropriate
5. Implement S3 Intelligent-Tiering
6. Set up cost anomaly alerts

---

## Submission Guidelines

### What to Submit

1. **Code Repository**:
   - All completed code files
   - Terraform configuration files
   - README with architecture diagram
   - Git history showing incremental development

2. **Documentation**:
   - Architecture decisions document
   - API documentation for Lambda functions
   - Deployment guide
   - Troubleshooting guide

3. **Evidence of Completion**:
   - Screenshots of AWS resources
   - CloudWatch dashboard showing metrics
   - Athena query results
   - Test execution results (pytest output)

4. **Video Demo** (5-10 minutes):
   - Architecture overview
   - Live demonstration of:
     - Producer sending events
     - Real-time dashboard showing metrics
     - Running Athena queries
     - Airflow DAG execution

### Evaluation Criteria

Your project will be evaluated on:

1. **Functionality** (40%):
   - All components working end-to-end
   - Correct event processing logic
   - Accurate analytics queries
   - Proper error handling

2. **Architecture & Design** (25%):
   - Appropriate service selection
   - Scalability considerations
   - Security best practices
   - Code organization and modularity

3. **Code Quality** (20%):
   - Clean, readable code
   - Proper error handling
   - Comprehensive logging
   - Unit test coverage

4. **Documentation** (10%):
   - Clear architecture diagrams
   - Complete README
   - Inline code comments
   - Deployment instructions

5. **Innovation** (5%):
   - Creative solutions to challenges
   - Advanced features implementation
   - Performance optimizations

### Submission Deadline

Complete the project within 2 weeks. Submit via:
- Git repository URL (GitHub/GitLab)
- Video demonstration link
- Architecture documentation

---

## Additional Resources

### AWS Documentation
- [Kinesis Data Streams Developer Guide](https://docs.aws.amazon.com/streams/)
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [Athena User Guide](https://docs.aws.amazon.com/athena/)

### Tutorials and Examples
- [Streaming Analytics with Kinesis](https://aws.amazon.com/kinesis/getting-started/)
- [Serverless Architecture Patterns](https://aws.amazon.com/serverless/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/)

### Community Support
- Project discussion forum: [Link to forum]
- Office hours: Wednesdays 3-5 PM
- Slack channel: #checkpoint-02-realtime

---

## Troubleshooting

### Common Issues

**Issue**: Kinesis stream not receiving records
- Check AWS credentials and permissions
- Verify stream name matches configuration
- Check producer error logs

**Issue**: Lambda function timeout
- Increase timeout in Terraform configuration
- Optimize batch size for Kinesis trigger
- Review CloudWatch logs for bottlenecks

**Issue**: DynamoDB throttling
- Increase provisioned capacity
- Switch to on-demand billing mode
- Review access patterns and indexes

**Issue**: High AWS costs
- Reduce Kinesis shard count during development
- Use on-demand DynamoDB for variable workloads
- Clean up unused resources regularly

---

## Next Steps

After completing this checkpoint:

1. Review the complete solution implementation
2. Compare your approach with best practices
3. Identify areas for improvement
4. Move on to Module 09: Data Quality
5. Prepare for Checkpoint 03: Enterprise Data Lakehouse

---

**Good luck! Remember: Focus on understanding the concepts, not just completing tasks. The journey is as important as the destination.**
