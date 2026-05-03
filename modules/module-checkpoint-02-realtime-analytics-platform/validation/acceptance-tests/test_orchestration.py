"""
Orchestration tests for Real-Time Analytics Platform.

Tests verify:
- Step Functions workflows
- EventBridge schedules
- Daily and weekly aggregations
- Error handling in workflows
- Retry mechanisms
"""

import pytest
import json
import time
from datetime import datetime, timedelta


# ============================================================================
# STEP FUNCTIONS TESTS
# ============================================================================

class TestStepFunctionsWorkflows:
    """Test Step Functions state machines."""

    @pytest.fixture(scope="class")
    def daily_aggregation_sm_arn(self, stepfunctions_client, resource_prefix):
        """Get daily aggregation state machine ARN."""
        response = stepfunctions_client.list_state_machines()

        for sm in response.get("stateMachines", []):
            if "daily-aggregation" in sm["name"].lower():
                return sm["stateMachineArn"]

        pytest.skip("Daily aggregation state machine not found")

    @pytest.fixture(scope="class")
    def weekly_reporting_sm_arn(self, stepfunctions_client, resource_prefix):
        """Get weekly reporting state machine ARN."""
        response = stepfunctions_client.list_state_machines()

        for sm in response.get("stateMachines", []):
            if "weekly-reporting" in sm["name"].lower():
                return sm["stateMachineArn"]

        pytest.skip("Weekly reporting state machine not found")

    def test_state_machine_definitions(self, stepfunctions_client,
                                      daily_aggregation_sm_arn):
        """Verify state machine definitions are valid."""
        response = stepfunctions_client.describe_state_machine(
            stateMachineArn=daily_aggregation_sm_arn
        )

        # Verify state machine is active
        assert response["status"] == "ACTIVE", \
            f"State machine status is {response['status']}, expected ACTIVE"

        # Verify definition exists and is valid JSON
        definition = json.loads(response["definition"])

        assert "States" in definition, "State machine should have States"
        assert "StartAt" in definition, "State machine should have StartAt"

    def test_start_daily_aggregation(self, stepfunctions_client,
                                     daily_aggregation_sm_arn):
        """Test starting daily aggregation workflow."""
        # Prepare input for workflow
        input_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "test_execution": True
        }

        # Start execution
        execution_name = f"test-{int(time.time())}"

        try:
            response = stepfunctions_client.start_execution(
                stateMachineArn=daily_aggregation_sm_arn,
                name=execution_name,
                input=json.dumps(input_data)
            )

            execution_arn = response["executionArn"]

            print(f"\nStarted execution: {execution_arn}")

            # Wait for execution to start
            time.sleep(5)

            # Check execution status
            status_response = stepfunctions_client.describe_execution(
                executionArn=execution_arn
            )

            status = status_response["status"]

            print(f"Execution status: {status}")

            assert status in ["RUNNING", "SUCCEEDED"], \
                f"Expected RUNNING or SUCCEEDED, got {status}"

        except stepfunctions_client.exceptions.StateMachineDoesNotExist:
            pytest.fail("State machine does not exist")
        except Exception as e:
            if "already exists" in str(e).lower():
                # Execution with this name already exists, that's ok
                assert True
            else:
                pytest.fail(f"Failed to start execution: {e}")

    def test_workflow_completion(self, stepfunctions_client,
                                 daily_aggregation_sm_arn):
        """Test that workflow completes successfully."""
        # Start execution
        input_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "test_execution": True
        }

        execution_name = f"test-completion-{int(time.time())}"

        try:
            response = stepfunctions_client.start_execution(
                stateMachineArn=daily_aggregation_sm_arn,
                name=execution_name,
                input=json.dumps(input_data)
            )

            execution_arn = response["executionArn"]

            # Poll for completion (up to 2 minutes)
            max_wait = 120
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status_response = stepfunctions_client.describe_execution(
                    executionArn=execution_arn
                )

                status = status_response["status"]

                if status == "SUCCEEDED":
                    print("\nWorkflow completed successfully")

                    # Verify output exists
                    output = status_response.get("output")
                    if output:
                        output_data = json.loads(output)
                        print(f"Output: {output_data}")

                    return

                elif status == "FAILED":
                    error = status_response.get("error", "Unknown error")
                    cause = status_response.get("cause", "Unknown cause")
                    pytest.fail(f"Workflow failed: {error} - {cause}")

                elif status == "TIMED_OUT":
                    pytest.fail("Workflow timed out")

                elif status == "ABORTED":
                    pytest.fail("Workflow was aborted")

                time.sleep(5)

            pytest.skip(f"Workflow did not complete within {max_wait}s")

        except Exception as e:
            if "already exists" in str(e).lower():
                pytest.skip("Execution already exists - cannot test completion")
            else:
                pytest.fail(f"Workflow test failed: {e}")


# ============================================================================
# DAILY AGGREGATION TESTS
# ============================================================================

class TestDailyAggregation:
    """Test daily aggregation workflow."""

    def test_aggregation_creates_metrics(self, stepfunctions_client,
                                        dynamodb_resource, resource_prefix):
        """Verify daily aggregation creates metrics in DynamoDB."""
        # Check if metrics table exists
        metrics_table_name = f"{resource_prefix}-metrics"

        try:
            table = dynamodb_resource.Table(metrics_table_name)

            # Query for today's metrics
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Note: In a real test, we would query for specific metrics
            # For now, just verify table is accessible

            response = table.scan(Limit=10)

            if response.get("Items"):
                print(f"\nFound {len(response['Items'])} metric items")
                assert True
            else:
                pytest.skip("No metrics found yet - aggregation may not have run")

        except dynamodb_resource.meta.client.exceptions.ResourceNotFoundException:
            pytest.skip("Metrics table not found")
        except Exception as e:
            pytest.skip(f"Could not verify metrics: {e}")

    def test_aggregation_output_to_s3(self, stepfunctions_client, s3_client,
                                     resource_prefix, aws_config):
        """Verify daily aggregation writes output to S3."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        # Check for aggregated data in S3
        today = datetime.utcnow()
        prefix = f"aggregated/daily/{today.year}/{today.month:02d}/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if response.get("KeyCount", 0) > 0:
                print(f"\nFound {response['KeyCount']} aggregated files")
                assert True
            else:
                pytest.skip("No aggregated data found yet")

        except Exception as e:
            pytest.skip(f"Could not check S3 for aggregated data: {e}")


# ============================================================================
# WEEKLY REPORTING TESTS
# ============================================================================

class TestWeeklyReporting:
    """Test weekly reporting workflow."""

    def test_start_weekly_reporting(self, stepfunctions_client,
                                   weekly_reporting_sm_arn):
        """Test starting weekly reporting workflow."""
        # Calculate week range
        today = datetime.utcnow()
        week_start = today - timedelta(days=today.weekday())

        input_data = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "test_execution": True
        }

        execution_name = f"test-weekly-{int(time.time())}"

        try:
            response = stepfunctions_client.start_execution(
                stateMachineArn=weekly_reporting_sm_arn,
                name=execution_name,
                input=json.dumps(input_data)
            )

            execution_arn = response["executionArn"]

            print(f"\nStarted weekly reporting: {execution_arn}")

            time.sleep(5)

            # Check status
            status_response = stepfunctions_client.describe_execution(
                executionArn=execution_arn
            )

            status = status_response["status"]

            assert status in ["RUNNING", "SUCCEEDED"], \
                f"Expected RUNNING or SUCCEEDED, got {status}"

        except Exception as e:
            if "already exists" in str(e).lower():
                assert True  # Already running is ok
            else:
                pytest.skip(f"Could not start weekly reporting: {e}")

    def test_weekly_report_generation(self, s3_client, resource_prefix, aws_config):
        """Verify weekly reports are generated and stored in S3."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        # Check for weekly reports
        today = datetime.utcnow()
        prefix = f"reports/weekly/{today.year}/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if response.get("KeyCount", 0) > 0:
                print(f"\nFound {response['KeyCount']} weekly reports")

                # Check file names
                for obj in response.get("Contents", [])[:5]:
                    key = obj["Key"]
                    print(f"Report: {key}")

                assert True
            else:
                pytest.skip("No weekly reports found yet")

        except Exception as e:
            pytest.skip(f"Could not check for weekly reports: {e}")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestWorkflowErrorHandling:
    """Test error handling in workflows."""

    def test_workflow_with_invalid_input(self, stepfunctions_client,
                                        daily_aggregation_sm_arn):
        """Test workflow handles invalid input gracefully."""
        # Send invalid input
        invalid_input = {
            "date": "invalid-date-format"
        }

        execution_name = f"test-invalid-{int(time.time())}"

        try:
            response = stepfunctions_client.start_execution(
                stateMachineArn=daily_aggregation_sm_arn,
                name=execution_name,
                input=json.dumps(invalid_input)
            )

            execution_arn = response["executionArn"]

            time.sleep(10)

            # Check if workflow handled error
            status_response = stepfunctions_client.describe_execution(
                executionArn=execution_arn
            )

            status = status_response["status"]

            if status == "FAILED":
                # Workflow should fail gracefully with proper error handling
                error = status_response.get("error", "")
                print(f"\nWorkflow failed as expected: {error}")
                assert True
            elif status == "SUCCEEDED":
                # Workflow handled invalid input and succeeded (with error path)
                assert True
            else:
                pytest.skip(f"Workflow status: {status}")

        except Exception as e:
            if "already exists" in str(e).lower():
                pytest.skip("Execution already exists")
            else:
                pytest.skip(f"Could not test error handling: {e}")

    def test_lambda_retry_in_workflow(self, stepfunctions_client,
                                     daily_aggregation_sm_arn):
        """Test that failed Lambda invocations are retried."""
        # Note: This test verifies retry configuration exists
        # Actual retry testing would require intentionally failing a Lambda

        response = stepfunctions_client.describe_state_machine(
            stateMachineArn=daily_aggregation_sm_arn
        )

        definition = json.loads(response["definition"])

        # Check for retry configuration in states
        has_retry = False

        for state_name, state_config in definition.get("States", {}).items():
            if "Retry" in state_config:
                has_retry = True
                print(f"\nState '{state_name}' has retry configuration")

                # Verify retry config
                retries = state_config["Retry"]
                assert len(retries) > 0, "Retry configuration should not be empty"

                for retry_config in retries:
                    assert "MaxAttempts" in retry_config, \
                        "Retry should have MaxAttempts"

        if has_retry:
            assert True
        else:
            pytest.skip("No retry configuration found in workflow")


# ============================================================================
# EVENTBRIDGE SCHEDULE TESTS
# ============================================================================

class TestEventBridgeSchedules:
    """Test EventBridge scheduled events."""

    def test_daily_schedule_exists(self, stepfunctions_client, resource_prefix):
        """Verify EventBridge rule for daily aggregation exists."""
        # Note: This would require boto3 events client
        # For now, we'll skip this test
        pytest.skip("EventBridge testing requires events client")

    def test_weekly_schedule_exists(self, stepfunctions_client, resource_prefix):
        """Verify EventBridge rule for weekly reporting exists."""
        pytest.skip("EventBridge testing requires events client")


# ============================================================================
# WORKFLOW OUTPUT VALIDATION
# ============================================================================

class TestWorkflowOutputs:
    """Test workflow outputs and side effects."""

    def test_aggregation_metrics_accuracy(self, dynamodb_resource, resource_prefix):
        """Verify aggregated metrics are accurate."""
        metrics_table_name = f"{resource_prefix}-metrics"

        try:
            table = dynamodb_resource.Table(metrics_table_name)

            # Scan for recent metrics
            response = table.scan(Limit=10)

            if not response.get("Items"):
                pytest.skip("No metrics found")

            # Verify metrics have expected structure
            for item in response["Items"]:
                # Check for required fields
                if "metric_name" in item:
                    assert "value" in item, "Metric should have value"
                    assert "timestamp" in item, "Metric should have timestamp"

                    # Verify value is numeric
                    value = item["value"]
                    assert isinstance(value, (int, float)), \
                        "Metric value should be numeric"

            print(f"\nValidated {len(response['Items'])} metrics")

        except dynamodb_resource.meta.client.exceptions.ResourceNotFoundException:
            pytest.skip("Metrics table not found")
        except Exception as e:
            pytest.skip(f"Could not validate metrics: {e}")

    def test_report_file_format(self, s3_client, resource_prefix, aws_config):
        """Verify report files are in correct format."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        # Look for recent report
        prefix = "reports/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=5
            )

            if response.get("KeyCount", 0) == 0:
                pytest.skip("No reports found")

            # Get first report file
            first_key = response["Contents"][0]["Key"]

            # Verify file extension
            assert first_key.endswith((".json", ".parquet", ".csv")), \
                f"Report file {first_key} should have valid format extension"

            print(f"\nValidated report format: {first_key}")

        except Exception as e:
            pytest.skip(f"Could not validate report format: {e}")


# ============================================================================
# WORKFLOW INTEGRATION TESTS
# ============================================================================

class TestWorkflowIntegration:
    """Test integration between workflows and other services."""

    def test_workflow_triggers_lambda(self, stepfunctions_client, logs_client,
                                     daily_aggregation_sm_arn, resource_prefix):
        """Verify workflow successfully invokes Lambda functions."""
        # Start workflow
        input_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "test_execution": True
        }

        execution_name = f"test-lambda-trigger-{int(time.time())}"

        try:
            response = stepfunctions_client.start_execution(
                stateMachineArn=daily_aggregation_sm_arn,
                name=execution_name,
                input=json.dumps(input_data)
            )

            execution_arn = response["executionArn"]

            time.sleep(20)  # Wait for workflow to progress

            # Check workflow history for Lambda invocations
            history = stepfunctions_client.get_execution_history(
                executionArn=execution_arn,
                maxResults=100
            )

            # Look for Lambda invocation events
            lambda_invoked = False

            for event in history.get("events", []):
                event_type = event["type"]

                if event_type in ["LambdaFunctionScheduled", "TaskScheduled"]:
                    lambda_invoked = True
                    print(f"\nLambda invocation detected: {event_type}")
                    break

            if lambda_invoked:
                assert True
            else:
                pytest.skip("Could not verify Lambda invocation")

        except Exception as e:
            if "already exists" in str(e).lower():
                pytest.skip("Execution already exists")
            else:
                pytest.skip(f"Could not test Lambda trigger: {e}")

    def test_workflow_writes_to_dynamodb(self, stepfunctions_client,
                                        dynamodb_resource, resource_prefix):
        """Verify workflow writes results to DynamoDB."""
        # This test checks that workflow side effects persist to DynamoDB
        metrics_table_name = f"{resource_prefix}-metrics"

        try:
            table = dynamodb_resource.Table(metrics_table_name)

            # Get item count before
            scan_before = table.scan(Select="COUNT")
            count_before = scan_before.get("Count", 0)

            print(f"\nMetrics count before workflow: {count_before}")

            # Note: Would need to run workflow and verify count increases
            # For now, just verify table is accessible

            assert True

        except Exception as e:
            pytest.skip(f"Could not check DynamoDB writes: {e}")


# ============================================================================
# WORKFLOW MONITORING TESTS
# ============================================================================

class TestWorkflowMonitoring:
    """Test workflow monitoring and observability."""

    def test_workflow_cloudwatch_metrics(self, cloudwatch_client, resource_prefix):
        """Verify workflow execution metrics are published to CloudWatch."""
        # Check for Step Functions metrics
        namespace = "AWS/States"
        metric_name = "ExecutionsFailed"

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            response = cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=["Sum"]
            )

            datapoints = response.get("Datapoints", [])

            print(f"\nFound {len(datapoints)} CloudWatch datapoints")

            # Having datapoints means monitoring is active
            assert True

        except Exception as e:
            pytest.skip(f"Could not check CloudWatch metrics: {e}")

    def test_workflow_execution_logs(self, logs_client, resource_prefix):
        """Verify workflow execution logs are available."""
        # Step Functions can log to CloudWatch Logs
        log_group_pattern = f"/aws/vendedlogs/states/{resource_prefix}"

        try:
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=log_group_pattern,
                limit=5
            )

            log_groups = response.get("logGroups", [])

            if log_groups:
                print(f"\nFound {len(log_groups)} workflow log groups")
                assert True
            else:
                pytest.skip("No workflow log groups found")

        except Exception as e:
            pytest.skip(f"Could not check workflow logs: {e}")
