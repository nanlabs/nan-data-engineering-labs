# Testing Guide - Real-Time Analytics Platform

## Overview

This directory contains comprehensive test suites for the Real-Time Analytics Platform (Checkpoint 02). The testing framework validates infrastructure, performance, data quality, streaming pipelines, and orchestration workflows.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Environment Configuration](#environment-configuration)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Prerequisites

### Required Tools

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **AWS CLI**
   ```bash
   aws --version
   aws configure
   ```

3. **pytest and Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### AWS Permissions

The test suite requires the following AWS permissions:

- **Kinesis**: `kinesis:DescribeStream`, `kinesis:PutRecord`, `kinesis:PutRecords`
- **DynamoDB**: `dynamodb:DescribeTable`, `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query`, `dynamodb:Scan`
- **Lambda**: `lambda:GetFunction`, `lambda:InvokeFunction`
- **Step Functions**: `states:DescribeStateMachine`, `states:StartExecution`, `states:DescribeExecution`, `states:GetExecutionHistory`
- **S3**: `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`
- **CloudWatch**: `cloudwatch:GetMetricStatistics`, `logs:DescribeLogGroups`, `logs:FilterLogEvents`

### Deployed Infrastructure

Before running tests, ensure the following AWS resources are deployed:

- **Kinesis Data Stream**: `{project}-{env}-rides-stream`
- **DynamoDB Table**: `{project}-{env}-rides`
- **Lambda Functions**: Stream processor and aggregation functions
- **Step Functions**: Daily and weekly workflow state machines
- **S3 Bucket**: Data storage bucket
- **IAM Roles**: Proper execution roles

---

## Quick Start

### 1. Clone and Navigate

```bash
cd modules/module-checkpoint-02-realtime-analytics-platform/validation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
export AWS_REGION=us-east-1
export PROJECT_NAME=rideshare-analytics
export ENVIRONMENT=dev
```

### 4. Run All Tests

```bash
chmod +x run_tests.sh
./run_tests.sh --all
```

### 5. View Results

```bash
ls -lh test-results/
```

---

## Test Structure

```
validation/
├── acceptance-tests/          # Comprehensive acceptance test suite
│   ├── conftest.py           # Shared fixtures and configuration
│   ├── test_infrastructure.py # Infrastructure validation tests
│   ├── test_streaming_pipeline.py # Pipeline integration tests
│   ├── test_data_quality.py  # Data quality validation
│   ├── test_performance.py   # Performance benchmarking
│   └── test_orchestration.py # Workflow orchestration tests
│
├── test_performance.py        # Standalone performance load tests
├── test_orchestration.py      # Standalone orchestration tests
├── run_tests.sh               # Test execution script
├── README.md                  # This file
└── test-results/              # Test output directory (generated)
    ├── coverage/              # Coverage reports
    ├── html-report/           # HTML test reports
    └── *.xml                  # JUnit XML reports
```

---

## Test Categories

### 1. Infrastructure Tests

**Location**: `acceptance-tests/test_infrastructure.py`

**Purpose**: Validate AWS resource deployment and configuration

**Tests Include**:
- ✓ Kinesis stream exists and is active
- ✓ DynamoDB table exists with correct schema
- ✓ Lambda functions are deployed with proper configuration
- ✓ Step Functions state machines are defined
- ✓ IAM roles and policies are configured
- ✓ S3 buckets exist with correct permissions

**Run Command**:
```bash
pytest acceptance-tests/test_infrastructure.py -v
```

### 2. Streaming Pipeline Tests

**Location**: `acceptance-tests/test_streaming_pipeline.py`

**Purpose**: Validate end-to-end data flow through streaming pipeline

**Tests Include**:
- ✓ Events ingested into Kinesis
- ✓ Lambda processing triggered
- ✓ Data written to DynamoDB
- ✓ Data written to S3
- ✓ Event ordering maintained
- ✓ Duplicate event handling

**Run Command**:
```bash
pytest acceptance-tests/test_streaming_pipeline.py -v
```

### 3. Data Quality Tests

**Location**: `acceptance-tests/test_data_quality.py`

**Purpose**: Validate data integrity and quality constraints

**Tests Include**:
- ✓ Schema validation
- ✓ Required fields present
- ✓ Data type correctness
- ✓ Value range validation
- ✓ Null handling
- ✓ Format consistency

**Run Command**:
```bash
pytest acceptance-tests/test_data_quality.py -v
```

### 4. Performance Tests

**Location**: `test_performance.py`

**Purpose**: Load testing and performance benchmarking

**Tests Include**:
- ✓ Kinesis throughput (1000 events/sec)
- ✓ Sustained load testing (60s+)
- ✓ Lambda latency measurements (p50, p95, p99)
- ✓ DynamoDB read/write throughput
- ✓ Memory usage profiling
- ✓ CloudWatch metrics validation

**Run Command**:
```bash
pytest test_performance.py -v
```

**Performance Thresholds**:
- Kinesis: 1000 events/sec peak, 100 events/sec sustained
- Lambda P99 latency: < 5 seconds
- Lambda P95 latency: < 3 seconds
- DynamoDB: 100 reads/writes per second

### 5. Orchestration Tests

**Location**: `test_orchestration.py`

**Purpose**: Validate Step Functions workflows

**Tests Include**:
- ✓ Daily aggregation workflow execution
- ✓ Weekly reporting workflow execution
- ✓ State transitions validation
- ✓ Error handling mechanisms
- ✓ Retry logic verification
- ✓ Integration with Lambda and S3

**Run Command**:
```bash
pytest test_orchestration.py -v
```

---

## Running Tests

### Using the Test Runner Script

The `run_tests.sh` script provides a comprehensive test execution framework with environment validation and reporting.

#### All Tests

```bash
./run_tests.sh --all
```

#### Unit Tests Only

```bash
./run_tests.sh --unit
```

#### Integration Tests Only

```bash
./run_tests.sh --integration
```

#### Performance Tests Only

```bash
./run_tests.sh --performance
```

#### Orchestration Tests Only

```bash
./run_tests.sh --orchestration
```

#### With Coverage Report

```bash
./run_tests.sh --all --coverage
```

#### With HTML Report

```bash
./run_tests.sh --all --html
```

#### Verbose Output

```bash
./run_tests.sh --all --verbose
```

### Using pytest Directly

#### Run All Tests

```bash
pytest validation/ -v
```

#### Run Specific Test File

```bash
pytest validation/test_performance.py -v
```

#### Run Specific Test Class

```bash
pytest validation/test_performance.py::TestKinesisThroughput -v
```

#### Run Specific Test Method

```bash
pytest validation/test_performance.py::TestKinesisThroughput::test_peak_throughput_1000_events_per_second -v
```

#### Run with Markers

```bash
pytest validation/ -v -m "performance"
pytest validation/ -v -m "not slow"
```

#### Generate Coverage Report

```bash
pytest validation/ --cov --cov-report=html:htmlcov --cov-report=term
```

#### Run in Parallel

```bash
pytest validation/ -v -n auto
```

---

## Environment Configuration

### Required Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_PROFILE=default  # optional

# Project Configuration
export PROJECT_NAME=rideshare-analytics
export ENVIRONMENT=dev

# Test Configuration (optional)
export SKIP_SETUP=false
export TEST_TIMEOUT=300
```

### Configuration File

Create a `.env` file in the validation directory:

```bash
# .env
AWS_REGION=us-east-1
PROJECT_NAME=rideshare-analytics
ENVIRONMENT=dev
RESOURCE_PREFIX=rideshare-analytics-dev
```

Load environment variables:

```bash
export $(cat .env | xargs)
```

### AWS Profile Configuration

If using multiple AWS profiles:

```bash
export AWS_PROFILE=dev-profile
aws configure --profile dev-profile
```

---

## CI/CD Integration

### GitHub Actions

Example workflow (`.github/workflows/test.yml`):

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Run tests
      run: |
        cd modules/module-checkpoint-02-realtime-analytics-platform/validation
        ./run_tests.sh --all --coverage
      env:
        PROJECT_NAME: rideshare-analytics
        ENVIRONMENT: dev

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./validation/test-results/coverage/coverage.xml
```

### GitLab CI

Example `.gitlab-ci.yml`:

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.9
  before_script:
    - pip install -r requirements.txt
    - apt-get update && apt-get install -y awscli
  script:
    - cd modules/module-checkpoint-02-realtime-analytics-platform/validation
    - ./run_tests.sh --all --coverage
  artifacts:
    reports:
      junit: validation/test-results/*.xml
      coverage_report:
        coverage_format: cobertura
        path: validation/test-results/coverage/coverage.xml
  only:
    - main
    - develop
```

### Jenkins Pipeline

Example `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-1'
        PROJECT_NAME = 'rideshare-analytics'
        ENVIRONMENT = 'dev'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                dir('modules/module-checkpoint-02-realtime-analytics-platform/validation') {
                    sh './run_tests.sh --all --coverage --html'
                }
            }
        }

        stage('Publish Results') {
            steps {
                junit 'validation/test-results/*.xml'
                publishHTML([
                    reportDir: 'validation/test-results/coverage',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Found

**Error**: `Unable to locate credentials`

**Solution**:
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

#### 2. Resource Not Found

**Error**: `ResourceNotFoundException`

**Solution**:
- Verify infrastructure is deployed: `aws cloudformation list-stacks`
- Check resource naming: Ensure `PROJECT_NAME` and `ENVIRONMENT` match deployed resources
- Verify AWS region: Ensure `AWS_REGION` is correct

#### 3. Permission Denied

**Error**: `AccessDeniedException`

**Solution**:
- Check IAM permissions for the user/role
- Verify IAM policies include required actions
- Check resource-based policies (S3 bucket policies, etc.)

#### 4. Timeout Errors

**Error**: `TimeoutError: Execution did not complete`

**Solution**:
- Increase timeout in test configuration
- Check CloudWatch logs for Lambda errors
- Verify Step Functions execution didn't stall

#### 5. Import Errors

**Error**: `ModuleNotFoundError: No module named 'boto3'`

**Solution**:
```bash
pip install -r requirements.txt
# OR
pip install boto3 pytest pytest-cov faker
```

### Debugging Tests

#### Enable Verbose Output

```bash
pytest validation/ -v -s
```

#### Run Single Test

```bash
pytest validation/test_performance.py::TestKinesisThroughput::test_peak_throughput_1000_events_per_second -v -s
```

#### Add Breakpoints

```python
import pdb; pdb.set_trace()
```

#### Check AWS Resources

```bash
# List Kinesis streams
aws kinesis list-streams

# Describe DynamoDB table
aws dynamodb describe-table --table-name rideshare-analytics-dev-rides

# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'rideshare')]"

# List Step Functions
aws stepfunctions list-state-machines
```

#### View CloudWatch Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/rideshare-analytics-dev-stream-processor --follow

# Get recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/rideshare-analytics-dev-stream-processor \
  --filter-pattern "ERROR"
```

---

## Best Practices

### Test Development

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always clean up resources created during tests
3. **Idempotency**: Tests should be repeatable with consistent results
4. **Assertions**: Use descriptive assertion messages
5. **Fixtures**: Use pytest fixtures for shared setup
6. **Mocking**: Mock external dependencies when appropriate

### Performance Testing

1. **Warm-up**: Run warm-up iterations before measuring performance
2. **Statistical Significance**: Run multiple iterations and use percentiles
3. **Resource Cleanup**: Clean up test data after performance tests
4. **Throttling**: Be aware of AWS service limits and throttling
5. **Cost Management**: Monitor costs from load testing

### CI/CD Integration

1. **Fast Feedback**: Run quick smoke tests first
2. **Parallel Execution**: Run independent tests in parallel
3. **Artifact Storage**: Store test results and reports
4. **Failure Notifications**: Configure alerts for test failures
5. **Test Selection**: Run full suite on main branches, subset on PRs

### Security

1. **Credentials**: Never commit AWS credentials to version control
2. **IAM Roles**: Use IAM roles for CI/CD instead of access keys
3. **Least Privilege**: Grant minimum required permissions
4. **Secret Management**: Use AWS Secrets Manager or Parameter Store
5. **Audit Logging**: Enable CloudTrail for test account activity

---

## Additional Resources

### Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Testing Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/framework/test.html)

### Test Coverage Goals

- **Unit Tests**: > 80% code coverage
- **Integration Tests**: All critical paths covered
- **Performance Tests**: Key performance indicators validated
- **Orchestration Tests**: All workflows tested

### Maintenance

- Review and update tests with infrastructure changes
- Update performance thresholds as system scales
- Add tests for new features
- Remove obsolete tests
- Keep dependencies up to date

---

## Support

For issues or questions:

1. Check this documentation
2. Review CloudWatch logs
3. Check existing GitHub issues
4. Create new issue with:
   - Test output
   - Environment details
   - Steps to reproduce

---

**Last Updated**: March 2026
**Version**: 1.0
**Maintained by**: Cloud Data Training Team
