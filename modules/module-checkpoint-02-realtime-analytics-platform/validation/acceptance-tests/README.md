# Acceptance Tests - Real-Time Analytics Platform

Comprehensive test suite for validating the Real-Time Analytics Platform (Checkpoint 02).

## Overview

This test suite validates the complete implementation of the real-time analytics platform, covering:

- **Infrastructure**: AWS resource configuration and deployment
- **Streaming Pipeline**: Data ingestion and processing
- **Data Quality**: Schema validation, completeness, and accuracy
- **Performance**: Throughput, latency, and cost efficiency
- **Orchestration**: Workflow automation and scheduling

## Test Categories

### 1. Infrastructure Tests (`test_infrastructure.py`)

Validates that all AWS resources are properly deployed and configured:

- ✅ Kinesis streams (4 streams with correct shard count, retention, encryption)
- ✅ Lambda functions (proper memory, timeout, event source mappings)
- ✅ DynamoDB tables (correct keys, GSIs, streams, PITR enabled)
- ✅ IAM roles and policies (least privilege)
- ✅ S3 buckets (versioning, encryption, lifecycle)
- ✅ Step Functions state machines
- ✅ CloudWatch alarms and log groups
- ✅ SNS topics for alerting

### 2. Streaming Pipeline Tests (`test_streaming_pipeline.py`)

Validates end-to-end data flow:

- ✅ Kinesis PutRecords success
- ✅ Lambda triggered by Kinesis events
- ✅ Data persisted to DynamoDB
- ✅ Events archived to S3 with proper partitioning
- ✅ Complete ride lifecycle (request → start → complete)
- ✅ Fraud detection and alerting
- ✅ Rating processing and driver score updates
- ✅ Analytics outputs (surge pricing, hot spots)
- ✅ Error handling and DLQ routing
- ✅ Idempotency

### 3. Data Quality Tests (`test_data_quality.py`)

Validates data integrity:

- ✅ Schema validation (all required fields present)
- ✅ Completeness (no data loss)
- ✅ Timeliness (processing latency < 10s P95)
- ✅ Accuracy (fare calculations, coordinates)
- ✅ Consistency (DynamoDB vs S3 archives)
- ✅ Referential integrity (ride_id references)
- ✅ Data type enforcement

### 4. Performance Tests (`test_performance.py`)

Validates system performance:

- ✅ Throughput (1000 events/second without throttling)
- ✅ End-to-end latency (< 5s P95)
- ✅ Lambda execution time (< 1s)
- ✅ DynamoDB query latency (< 100ms)
- ✅ Cost efficiency (< $50 per 1M events)
- ✅ Load handling (100K events)
- ✅ Concurrent processing

### 5. Orchestration Tests (`test_orchestration.py`)

Validates workflow automation:

- ✅ Step Functions execution
- ✅ Daily aggregation workflow
- ✅ Weekly reporting workflow
- ✅ Error handling and retries
- ✅ EventBridge schedules
- ✅ Workflow outputs and side effects

## Setup Instructions

### Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Configured with credentials
   ```bash
   aws configure
   ```
3. **Python 3.9+**: Installed on your system
4. **Infrastructure Deployed**: The platform must be deployed before running tests

### Installation

1. Navigate to the test directory:
   ```bash
   cd validation/acceptance-tests
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export PROJECT_NAME="rideshare-analytics"
   export ENVIRONMENT="dev"
   export AWS_REGION="us-east-1"
   ```

## Running Tests

### Option 1: Run All Tests (Recommended)

```bash
./run_tests.sh all
```

### Option 2: Run Specific Test Suites

```bash
# Infrastructure tests only
./run_tests.sh infrastructure

# Streaming pipeline tests
./run_tests.sh streaming

# Data quality tests
./run_tests.sh quality

# Performance tests
./run_tests.sh performance

# Orchestration tests
./run_tests.sh orchestration
```

### Option 3: Run with pytest Directly

```bash
# All tests
pytest -v

# Specific test file
pytest -v test_infrastructure.py

# Specific test class
pytest -v test_streaming_pipeline.py::TestKinesisIngestion

# Specific test
pytest -v test_performance.py::TestLatency::test_end_to_end_latency

# Run with markers
pytest -v -m "not slow"
```

## Test Reports

After running tests, reports are generated in `./test-reports/`:

- **HTML Report**: `report_YYYYMMDD_HHMMSS.html` - Detailed test results
- **JUnit XML**: `junit_YYYYMMDD_HHMMSS.xml` - CI/CD integration format
- **Coverage Report**: `coverage_YYYYMMDD_HHMMSS/index.html` - Code coverage

View HTML report:
```bash
open test-reports/report_*.html
```

## Interpreting Results

### Test Status Indicators

- ✅ **PASSED**: Test completed successfully
- ❌ **FAILED**: Test found an issue (requires attention)
- ⊘ **SKIPPED**: Test couldn't run (infrastructure not ready, dependencies missing)

### Understanding Skipped Tests

Tests may be skipped for valid reasons:

1. **Infrastructure Not Deployed**: Deploy the platform first
2. **Timing Issues**: Some tests need time for data to propagate
3. **Optional Features**: Feature not yet implemented (e.g., fraud detection)

### Common Issues

#### AWS Credentials Error
```
Error: AWS credentials not configured properly
```
**Solution**: Run `aws configure` and provide valid credentials

#### Infrastructure Not Found
```
AssertionError: Stream rideshare-analytics-dev-rides-stream not found
```
**Solution**: Deploy infrastructure with Terraform first

#### Processing Delays
```
Skipped: Event not processed within timeout
```
**Solution**: Wait a few minutes and retry - Lambda cold starts can cause delays

## Test Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `rideshare-analytics` | Project name prefix |
| `ENVIRONMENT` | `dev` | Environment (dev/staging/prod) |
| `AWS_REGION` | `us-east-1` | AWS region |

### Pytest Configuration

Create `pytest.ini` for custom configuration:

```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    infrastructure: infrastructure validation tests
    streaming: streaming pipeline tests
    quality: data quality tests
    performance: performance tests
    orchestration: orchestration tests

testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Troubleshooting

### Issue: Tests Timing Out

**Symptoms**: Events sent but not appearing in DynamoDB

**Possible Causes**:
- Lambda cold start delays
- Kinesis event source mapping disabled
- IAM permission issues

**Solutions**:
1. Check Lambda function logs in CloudWatch
2. Verify event source mapping is enabled
3. Review IAM role policies

### Issue: Throttling Errors

**Symptoms**: `ProvisionedThroughputExceededException`

**Solutions**:
1. Increase Kinesis shard count
2. Add exponential backoff in producers
3. Use batch operations

### Issue: DynamoDB Queries Slow

**Symptoms**: Query latency > 500ms

**Solutions**:
1. Check DynamoDB table capacity mode
2. Verify GSI configuration
3. Review query patterns

### Issue: Cost Tests Failing

**Symptoms**: Estimated costs exceed threshold

**Solutions**:
1. Review resource configurations (oversized Lambda, too many shards)
2. Enable lifecycle policies on S3
3. Use on-demand billing for DynamoDB if usage is variable

## Best Practices

### Running Tests in CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run Acceptance Tests
  run: |
    cd validation/acceptance-tests
    ./run_tests.sh all
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_REGION: us-east-1
```

### Test Isolation

- Each test should be independent
- Use unique IDs (timestamps) for test data
- Clean up test data when possible

### Test Data

- Use faker library for realistic test data
- Generate diverse scenarios (edge cases)
- Test with various data volumes

## Contributing

When adding new tests:

1. Follow naming convention: `test_<feature>_<scenario>`
2. Add docstrings explaining what is tested
3. Use appropriate test markers
4. Include both positive and negative test cases
5. Update this README with new test categories

## Support

For issues or questions:

1. Check CloudWatch Logs for Lambda function errors
2. Review Terraform outputs for resource names
3. Verify AWS permissions
4. Consult the main project documentation

## License

This test suite is part of the Cloud Data Engineering Training Program.
