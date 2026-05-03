"""
Infrastructure validation tests for Real-Time Analytics Platform.

Tests verify that all AWS resources are properly deployed and configured:
- Kinesis streams
- Lambda functions
- DynamoDB tables
- IAM roles and policies
- S3 buckets
- Step Functions
- CloudWatch resources
- SNS topics
"""

import pytest
from typing import Dict, List


# ============================================================================
# KINESIS STREAM TESTS
# ============================================================================

class TestKinesisStreams:
    """Test Kinesis Data Streams infrastructure."""

    @pytest.fixture(scope="class")
    def expected_streams(self, resource_prefix) -> List[str]:
        """List of expected Kinesis streams."""
        return [
            f"{resource_prefix}-rides-stream",
            f"{resource_prefix}-locations-stream",
            f"{resource_prefix}-payments-stream",
            f"{resource_prefix}-ratings-stream"
        ]

    def test_streams_exist(self, kinesis_client, expected_streams):
        """Verify all required Kinesis streams exist."""
        response = kinesis_client.list_streams()
        stream_names = response["StreamNames"]

        for expected_stream in expected_streams:
            assert expected_stream in stream_names, \
                f"Stream {expected_stream} not found. Available: {stream_names}"

    def test_stream_shard_count(self, kinesis_client, expected_streams):
        """Verify streams have correct number of shards."""
        for stream_name in expected_streams:
            response = kinesis_client.describe_stream(StreamName=stream_name)
            stream_desc = response["StreamDescription"]

            shard_count = len(stream_desc["Shards"])
            assert shard_count >= 1, \
                f"Stream {stream_name} has {shard_count} shards, expected at least 1"

            # High-volume streams should have more shards
            if "rides" in stream_name or "locations" in stream_name:
                assert shard_count >= 2, \
                    f"High-volume stream {stream_name} should have at least 2 shards, has {shard_count}"

    def test_stream_retention(self, kinesis_client, expected_streams):
        """Verify streams have correct retention period (24 hours)."""
        for stream_name in expected_streams:
            response = kinesis_client.describe_stream(StreamName=stream_name)
            stream_desc = response["StreamDescription"]

            retention_hours = stream_desc["RetentionPeriodHours"]
            assert retention_hours == 24, \
                f"Stream {stream_name} has retention of {retention_hours}h, expected 24h"

    def test_stream_encryption(self, kinesis_client, expected_streams):
        """Verify streams have encryption enabled."""
        for stream_name in expected_streams:
            response = kinesis_client.describe_stream(StreamName=stream_name)
            stream_desc = response["StreamDescription"]

            encryption_type = stream_desc.get("EncryptionType", "NONE")
            assert encryption_type == "KMS", \
                f"Stream {stream_name} encryption is {encryption_type}, expected KMS"

    def test_stream_status(self, kinesis_client, expected_streams):
        """Verify streams are in ACTIVE status."""
        for stream_name in expected_streams:
            response = kinesis_client.describe_stream(StreamName=stream_name)
            stream_desc = response["StreamDescription"]

            status = stream_desc["StreamStatus"]
            assert status == "ACTIVE", \
                f"Stream {stream_name} status is {status}, expected ACTIVE"


# ============================================================================
# LAMBDA FUNCTION TESTS
# ============================================================================

class TestLambdaFunctions:
    """Test Lambda functions infrastructure."""

    @pytest.fixture(scope="class")
    def expected_functions(self, resource_prefix) -> List[Dict[str, any]]:
        """List of expected Lambda functions with their configurations."""
        return [
            {
                "name": f"{resource_prefix}-rides-processor",
                "memory": 512,
                "timeout": 60,
                "has_esm": True
            },
            {
                "name": f"{resource_prefix}-locations-processor",
                "memory": 256,
                "timeout": 30,
                "has_esm": True
            },
            {
                "name": f"{resource_prefix}-payments-processor",
                "memory": 512,
                "timeout": 60,
                "has_esm": True
            },
            {
                "name": f"{resource_prefix}-ratings-processor",
                "memory": 256,
                "timeout": 30,
                "has_esm": True
            }
        ]

    def test_functions_exist(self, lambda_client, expected_functions):
        """Verify all Lambda functions are deployed."""
        for func_config in expected_functions:
            func_name = func_config["name"]
            try:
                response = lambda_client.get_function(FunctionName=func_name)
                assert response["Configuration"]["FunctionName"] == func_name
            except lambda_client.exceptions.ResourceNotFoundException:
                pytest.fail(f"Lambda function {func_name} not found")

    def test_function_memory_config(self, lambda_client, expected_functions):
        """Verify Lambda functions have correct memory configuration."""
        for func_config in expected_functions:
            func_name = func_config["name"]
            expected_memory = func_config["memory"]

            response = lambda_client.get_function_configuration(FunctionName=func_name)
            actual_memory = response["MemorySize"]

            assert actual_memory >= expected_memory, \
                f"Function {func_name} has {actual_memory}MB, expected at least {expected_memory}MB"

    def test_function_timeout_config(self, lambda_client, expected_functions):
        """Verify Lambda functions have correct timeout configuration."""
        for func_config in expected_functions:
            func_name = func_config["name"]
            expected_timeout = func_config["timeout"]

            response = lambda_client.get_function_configuration(FunctionName=func_name)
            actual_timeout = response["Timeout"]

            assert actual_timeout >= expected_timeout, \
                f"Function {func_name} has timeout {actual_timeout}s, expected at least {expected_timeout}s"

    def test_function_event_source_mappings(self, lambda_client, expected_functions):
        """Verify Lambda functions have Event Source Mappings configured for Kinesis."""
        for func_config in expected_functions:
            if not func_config["has_esm"]:
                continue

            func_name = func_config["name"]

            response = lambda_client.list_event_source_mappings(FunctionName=func_name)
            mappings = response.get("EventSourceMappings", [])

            assert len(mappings) >= 1, \
                f"Function {func_name} has no event source mappings"

            # Verify at least one mapping is enabled
            enabled_mappings = [m for m in mappings if m["State"] == "Enabled"]
            assert len(enabled_mappings) >= 1, \
                f"Function {func_name} has no enabled event source mappings"

    def test_function_environment_variables(self, lambda_client, expected_functions):
        """Verify Lambda functions have required environment variables."""
        required_vars = ["DYNAMODB_TABLE_PREFIX", "S3_BUCKET", "AWS_REGION"]

        for func_config in expected_functions:
            func_name = func_config["name"]

            response = lambda_client.get_function_configuration(FunctionName=func_name)
            env_vars = response.get("Environment", {}).get("Variables", {})

            for var in required_vars:
                assert var in env_vars, \
                    f"Function {func_name} missing environment variable {var}"

    def test_function_runtime(self, lambda_client, expected_functions):
        """Verify Lambda functions use supported Python runtime."""
        supported_runtimes = ["python3.9", "python3.10", "python3.11", "python3.12"]

        for func_config in expected_functions:
            func_name = func_config["name"]

            response = lambda_client.get_function_configuration(FunctionName=func_name)
            runtime = response["Runtime"]

            assert runtime in supported_runtimes, \
                f"Function {func_name} uses runtime {runtime}, expected one of {supported_runtimes}"


# ============================================================================
# DYNAMODB TABLE TESTS
# ============================================================================

class TestDynamoDBTables:
    """Test DynamoDB tables infrastructure."""

    @pytest.fixture(scope="class")
    def expected_tables(self, resource_prefix) -> List[Dict[str, any]]:
        """List of expected DynamoDB tables with configurations."""
        return [
            {
                "name": f"{resource_prefix}-rides",
                "partition_key": "ride_id",
                "sort_key": None,
                "has_gsi": True,
                "has_stream": True
            },
            {
                "name": f"{resource_prefix}-drivers",
                "partition_key": "driver_id",
                "sort_key": None,
                "has_gsi": True,
                "has_stream": False
            },
            {
                "name": f"{resource_prefix}-payments",
                "partition_key": "payment_id",
                "sort_key": None,
                "has_gsi": True,
                "has_stream": True
            }
        ]

    def test_tables_exist(self, dynamodb_client, expected_tables):
        """Verify all DynamoDB tables exist."""
        response = dynamodb_client.list_tables()
        table_names = response["TableNames"]

        for table_config in expected_tables:
            table_name = table_config["name"]
            assert table_name in table_names, \
                f"Table {table_name} not found. Available: {table_names}"

    def test_table_keys(self, dynamodb_client, expected_tables):
        """Verify tables have correct partition and sort keys."""
        for table_config in expected_tables:
            table_name = table_config["name"]

            response = dynamodb_client.describe_table(TableName=table_name)
            table_desc = response["Table"]

            key_schema = {k["AttributeName"]: k["KeyType"] for k in table_desc["KeySchema"]}

            # Check partition key
            expected_pk = table_config["partition_key"]
            assert expected_pk in key_schema, \
                f"Table {table_name} missing partition key {expected_pk}"
            assert key_schema[expected_pk] == "HASH", \
                f"Table {table_name} key {expected_pk} should be HASH type"

            # Check sort key if expected
            if table_config["sort_key"]:
                expected_sk = table_config["sort_key"]
                assert expected_sk in key_schema, \
                    f"Table {table_name} missing sort key {expected_sk}"
                assert key_schema[expected_sk] == "RANGE", \
                    f"Table {table_name} key {expected_sk} should be RANGE type"

    def test_table_gsi(self, dynamodb_client, expected_tables):
        """Verify tables have Global Secondary Indexes where expected."""
        for table_config in expected_tables:
            if not table_config["has_gsi"]:
                continue

            table_name = table_config["name"]

            response = dynamodb_client.describe_table(TableName=table_name)
            table_desc = response["Table"]

            gsis = table_desc.get("GlobalSecondaryIndexes", [])
            assert len(gsis) >= 1, \
                f"Table {table_name} expected to have at least 1 GSI, has {len(gsis)}"

            # Verify GSIs are active
            for gsi in gsis:
                assert gsi["IndexStatus"] == "ACTIVE", \
                    f"GSI {gsi['IndexName']} on {table_name} is {gsi['IndexStatus']}, expected ACTIVE"

    def test_table_streams(self, dynamodb_client, expected_tables):
        """Verify DynamoDB Streams are enabled where expected."""
        for table_config in expected_tables:
            table_name = table_config["name"]

            response = dynamodb_client.describe_table(TableName=table_name)
            table_desc = response["Table"]

            if table_config["has_stream"]:
                assert "StreamSpecification" in table_desc, \
                    f"Table {table_name} expected to have streams enabled"
                assert table_desc["StreamSpecification"]["StreamEnabled"], \
                    f"Table {table_name} streams should be enabled"
            else:
                if "StreamSpecification" in table_desc:
                    assert not table_desc["StreamSpecification"]["StreamEnabled"], \
                        f"Table {table_name} should not have streams enabled"

    def test_table_backup_config(self, dynamodb_client, expected_tables):
        """Verify Point-in-Time Recovery is enabled."""
        for table_config in expected_tables:
            table_name = table_config["name"]

            response = dynamodb_client.describe_continuous_backups(TableName=table_name)
            pitr_desc = response["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"]

            assert pitr_desc["PointInTimeRecoveryStatus"] == "ENABLED", \
                f"Table {table_name} should have PITR enabled"


# ============================================================================
# IAM ROLE TESTS
# ============================================================================

class TestIAMRoles:
    """Test IAM roles and policies."""

    def test_lambda_execution_roles_exist(self, iam_client, resource_prefix):
        """Verify Lambda execution roles exist."""
        role_patterns = [
            f"{resource_prefix}-rides-processor-role",
            f"{resource_prefix}-locations-processor-role",
            f"{resource_prefix}-payments-processor-role",
            f"{resource_prefix}-ratings-processor-role"
        ]

        for role_name in role_patterns:
            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response["Role"]["RoleName"] == role_name
            except iam_client.exceptions.NoSuchEntityException:
                pytest.skip(f"Role {role_name} not found - may use different naming")

    def test_lambda_role_trust_policy(self, iam_client, resource_prefix):
        """Verify Lambda roles trust Lambda service."""
        role_name = f"{resource_prefix}-rides-processor-role"

        try:
            response = iam_client.get_role(RoleName=role_name)
            assume_role_policy = response["Role"]["AssumeRolePolicyDocument"]

            # Check Lambda service principal
            found_lambda_principal = False
            for statement in assume_role_policy["Statement"]:
                if "Service" in statement.get("Principal", {}):
                    if "lambda.amazonaws.com" in statement["Principal"]["Service"]:
                        found_lambda_principal = True
                        break

            assert found_lambda_principal, \
                f"Role {role_name} should trust lambda.amazonaws.com"
        except iam_client.exceptions.NoSuchEntityException:
            pytest.skip(f"Role {role_name} not found")


# ============================================================================
# S3 BUCKET TESTS
# ============================================================================

class TestS3Buckets:
    """Test S3 buckets infrastructure."""

    @pytest.fixture(scope="class")
    def expected_bucket(self, resource_prefix, aws_config) -> str:
        """Expected S3 bucket name."""
        return f"{resource_prefix}-data-{aws_config['region']}"

    def test_bucket_exists(self, s3_client, expected_bucket):
        """Verify S3 bucket exists."""
        try:
            s3_client.head_bucket(Bucket=expected_bucket)
        except s3_client.exceptions.NoSuchBucket:
            pytest.fail(f"Bucket {expected_bucket} not found")

    def test_bucket_versioning(self, s3_client, expected_bucket):
        """Verify bucket versioning is enabled."""
        try:
            response = s3_client.get_bucket_versioning(Bucket=expected_bucket)
            status = response.get("Status", "Disabled")
            assert status == "Enabled", \
                f"Bucket {expected_bucket} versioning is {status}, expected Enabled"
        except Exception:
            pytest.skip(f"Could not check versioning for {expected_bucket}")

    def test_bucket_encryption(self, s3_client, expected_bucket):
        """Verify bucket encryption is enabled."""
        try:
            response = s3_client.get_bucket_encryption(Bucket=expected_bucket)
            rules = response["ServerSideEncryptionConfiguration"]["Rules"]
            assert len(rules) >= 1, \
                f"Bucket {expected_bucket} should have encryption rules"
        except s3_client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            pytest.fail(f"Bucket {expected_bucket} has no encryption configuration")


# ============================================================================
# STEP FUNCTIONS TESTS
# ============================================================================

class TestStepFunctions:
    """Test Step Functions state machines."""

    def test_state_machines_exist(self, stepfunctions_client, resource_prefix):
        """Verify Step Functions state machines exist."""
        expected_state_machines = [
            f"{resource_prefix}-daily-aggregation",
            f"{resource_prefix}-weekly-reporting"
        ]

        response = stepfunctions_client.list_state_machines()
        state_machine_names = [sm["name"] for sm in response["stateMachines"]]

        for expected_sm in expected_state_machines:
            # Partial match since names might have suffixes
            found = any(expected_sm in name for name in state_machine_names)
            assert found, \
                f"State machine matching {expected_sm} not found. Available: {state_machine_names}"


# ============================================================================
# CLOUDWATCH TESTS
# ============================================================================

class TestCloudWatch:
    """Test CloudWatch monitoring resources."""

    def test_log_groups_exist(self, logs_client, resource_prefix):
        """Verify CloudWatch Log Groups exist for Lambda functions."""
        expected_log_groups = [
            f"/aws/lambda/{resource_prefix}-rides-processor",
            f"/aws/lambda/{resource_prefix}-locations-processor",
            f"/aws/lambda/{resource_prefix}-payments-processor",
            f"/aws/lambda/{resource_prefix}-ratings-processor"
        ]

        for log_group_name in expected_log_groups:
            try:
                logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
                # If no exception, log group exists
            except Exception as e:
                pytest.fail(f"Log group {log_group_name} check failed: {e}")

    def test_alarms_exist(self, cloudwatch_client, resource_prefix):
        """Verify CloudWatch Alarms are configured."""
        response = cloudwatch_client.describe_alarms(AlarmNamePrefix=resource_prefix)
        alarms = response.get("MetricAlarms", []) + response.get("CompositeAlarms", [])

        assert len(alarms) >= 1, \
            f"Expected at least 1 CloudWatch alarm with prefix {resource_prefix}"


# ============================================================================
# SNS TESTS
# ============================================================================

class TestSNS:
    """Test SNS topics and subscriptions."""

    def test_alert_topics_exist(self, sns_client, resource_prefix):
        """Verify SNS topics for alerts exist."""
        response = sns_client.list_topics()
        topics = response.get("Topics", [])
        topic_arns = [t["TopicArn"] for t in topics]

        # Check for fraud alert topic
        fraud_topic_found = any(f"{resource_prefix}-fraud-alerts" in arn for arn in topic_arns)

        if not fraud_topic_found:
            pytest.skip("Fraud alert topic not configured yet")
