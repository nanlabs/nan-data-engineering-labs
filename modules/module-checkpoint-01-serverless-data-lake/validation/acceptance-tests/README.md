# Acceptance Tests - Serverless Data Lake Checkpoint

Comprehensive acceptance tests for validating the Checkpoint 01: Serverless Data Lake implementation.

## Overview

This test suite validates:
- ✅ Infrastructure deployment (S3, IAM, Lambda, Glue, Athena, SNS, CloudWatch)
- ✅ Data pipeline functionality (upload, transform, query)
- ✅ Data quality (schema, completeness, transformations, referential integrity)
- ✅ Performance (execution time, resource usage)
- ✅ Cost optimization (storage, compute, staying within budget)

## Test Files

| File | Lines | Description |
|------|-------|-------------|
| `test_infrastructure.py` | ~400 | Infrastructure deployment validation |
| `test_data_pipeline.py` | ~500 | End-to-end pipeline integration tests |
| `test_data_quality.py` | ~350 | Data quality and integrity tests |
| `test_performance.py` | ~300 | Performance and cost optimization tests |
| `conftest.py` | ~200 | pytest configuration and fixtures |
| `requirements.txt` | ~25 | Python dependencies |
| `run_tests.sh` | ~100 | Test execution script |

**Total**: ~1,875 lines of test code

## Prerequisites

### 1. AWS Credentials

Configure AWS credentials with appropriate permissions:

```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

### 2. Python Environment

Python 3.8+ required:

```bash
python --version  # Should be 3.8 or higher
```

### 3. Infrastructure Deployed

Ensure the serverless data lake infrastructure is deployed:
- S3 buckets (raw, processed, curated, logs, athena-results)
- IAM roles (Lambda, Glue)
- Lambda functions (file-validator, metadata-extractor, etc.)
- Glue database, crawlers, and ETL jobs
- Athena workgroup
- SNS topic
- CloudWatch alarms

## Quick Start

### Option 1: Using the Test Runner Script (Recommended)

```bash
# Run all tests
./run_tests.sh

# Run only quick tests (exclude slow/expensive)
./run_tests.sh --quick

# Run only integration tests
./run_tests.sh --integration

# Run with verbose output
./run_tests.sh --verbose

# Run tests in parallel (faster)
./run_tests.sh --parallel
```

### Option 2: Using pytest Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest test_infrastructure.py

# Run specific test
pytest test_infrastructure.py::TestS3Infrastructure::test_s3_buckets_exist

# Run with coverage
pytest --cov=. --cov-report=html
```

## Test Categories

Tests are marked with pytest markers for selective execution:

### Integration Tests
Tests that interact with actual AWS resources:
```bash
pytest -m integration
```

### Slow Tests
Tests that take longer to execute (> 10 seconds):
```bash
pytest -m slow
```

### Expensive Tests
Tests that may incur AWS costs (Glue jobs, large queries):
```bash
pytest -m expensive
```

### Quick Tests Only
Exclude slow and expensive tests:
```bash
pytest -m "not slow and not expensive"
```

## Environment Configuration

Configure tests using environment variables:

```bash
# AWS Region
export AWS_REGION="us-east-1"

# S3 Bucket Prefix
export BUCKET_PREFIX="data-lake-checkpoint01"

# Project Name
export PROJECT_NAME="serverless-data-lake"

# Environment (test, dev, prod)
export ENVIRONMENT="test"
```

## Test Reports

After running tests, reports are generated in the `reports/` directory:

### HTML Test Report
```bash
open reports/test-report.html
```

Shows:
- Test results (passed/failed/skipped)
- Execution time per test
- Failure details with stack traces
- Test summary statistics

### Coverage Report
```bash
open reports/coverage/index.html
```

Shows:
- Code coverage percentage
- Line-by-line coverage
- Uncovered lines highlighted

## Understanding Test Results

### All Tests Passed ✓
```
╔════════════════════════════════════════════════════════════╗
║  ✓ ALL TESTS PASSED                                       ║
╚════════════════════════════════════════════════════════════╝
```
Infrastructure is correctly deployed and functioning.

### Some Tests Failed ✗
```
╔════════════════════════════════════════════════════════════╗
║  ✗ SOME TESTS FAILED                                      ║
╚════════════════════════════════════════════════════════════╝
```
Check `reports/test-report.html` for detailed failure information.

## Common Test Scenarios

### Scenario 1: Initial Infrastructure Validation

After deploying infrastructure:
```bash
./run_tests.sh --quick
```

This runs fast tests to verify:
- ✅ All buckets exist
- ✅ IAM roles are configured
- ✅ Lambda functions are deployed
- ✅ Glue resources are created

### Scenario 2: End-to-End Pipeline Test

After deploying complete pipeline:
```bash
pytest test_data_pipeline.py::TestEndToEnd::test_complete_pipeline_flow -v
```

This validates:
- ✅ Data upload to raw bucket
- ✅ Lambda processing
- ✅ Data transformation
- ✅ Athena queries

### Scenario 3: Data Quality Validation

After running data through pipeline:
```bash
pytest test_data_quality.py -v
```

This checks:
- ✅ Schema correctness
- ✅ No nulls in key columns
- ✅ Transformations applied
- ✅ No duplicates
- ✅ Data freshness

### Scenario 4: Performance Benchmarking

To measure performance:
```bash
pytest test_performance.py -v
```

This measures:
- ✅ Lambda execution time
- ✅ Glue job duration
- ✅ Athena query speed
- ✅ Cost estimates

## Troubleshooting

### Test Failures

#### "Bucket does not exist"
**Problem**: S3 buckets not created or name mismatch
**Solution**: Check `BUCKET_PREFIX` environment variable matches your deployment

#### "IAM role does not exist"
**Problem**: IAM roles not created or incorrect names
**Solution**: Verify IAM roles are deployed with expected names

#### "Lambda function does not exist"
**Problem**: Lambda functions not deployed
**Solution**: Check Lambda deployment in AWS Console

#### "No data in bronze/silver/gold layer"
**Problem**: Pipeline hasn't processed data yet
**Solution**: Upload sample data and wait for processing

#### "AWS credentials not configured"
**Problem**: No AWS credentials available
**Solution**: Run `aws configure` or set environment variables

### Performance Issues

If tests are too slow:
```bash
# Run in parallel
./run_tests.sh --parallel

# Skip slow tests
./run_tests.sh --quick
```

### Cost Concerns

Some tests may incur AWS costs:
- Glue job execution (marked with `@pytest.mark.expensive`)
- Athena queries (minimal cost)
- Lambda invocations (usually within Free Tier)

To skip expensive tests:
```bash
pytest -m "not expensive"
```

## Extending Tests

### Adding New Tests

1. Choose appropriate test file based on category
2. Follow existing test patterns
3. Use fixtures from `conftest.py`
4. Add appropriate pytest markers

Example:
```python
@pytest.mark.integration
def test_new_feature(s3_client, bucket_names):
    """Test description"""
    # Test implementation
    assert condition, "Error message"
```

### Adding New Fixtures

Add fixtures to `conftest.py`:
```python
@pytest.fixture
def my_fixture():
    """Fixture description"""
    # Setup
    yield value
    # Teardown
```

## Best Practices

### 1. Run Tests After Every Change
```bash
./run_tests.sh --quick
```

### 2. Use Cleanup Fixtures
Tests should clean up resources they create using the `cleanup_test_data` fixture.

### 3. Mock Expensive Operations
Use `moto` to mock AWS services during development:
```python
from moto import mock_s3

@mock_s3
def test_with_mock():
    # Test implementation
```

### 4. Document Test Purpose
Each test should have a clear docstring explaining what it validates.

### 5. Use Meaningful Assertions
```python
# Good
assert bucket_exists, f"Bucket {bucket_name} does not exist"

# Bad
assert bucket_exists
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Acceptance Tests
  run: |
    cd validation/acceptance-tests
    ./run_tests.sh --quick
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_REGION: us-east-1
```

### GitLab CI

```yaml
acceptance_tests:
  script:
    - cd validation/acceptance-tests
    - ./run_tests.sh --quick
  variables:
    AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
    AWS_REGION: us-east-1
```

## Support

For issues or questions:
1. Check test logs in `reports/test-report.html`
2. Review AWS CloudWatch logs for Lambda/Glue failures
3. Verify infrastructure deployment in AWS Console
4. Check environment variables are correctly set

## License

Part of the Cloud Data Engineering Training Program.
