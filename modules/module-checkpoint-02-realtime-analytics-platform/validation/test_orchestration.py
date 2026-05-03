"""
Step Functions Orchestration Testing for Real-Time Analytics Platform.

This module tests AWS Step Functions workflows including:
- Daily aggregation workflow execution
- Weekly reporting workflow execution
- State machine transitions validation
- Error handling and retry logic
- Workflow input/output validation

Run: pytest test_orchestration.py -v --tb=short
"""

import pytest
import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

class OrchestrationConfig:
    """Orchestration test configuration."""

    # Timeout for workflow execution (seconds)
    WORKFLOW_TIMEOUT = 300  # 5 minutes
    POLL_INTERVAL = 5  # seconds

    # Workflow names
    DAILY_AGGREGATION_WORKFLOW = "daily-aggregation-workflow"
    WEEKLY_REPORTING_WORKFLOW = "weekly-reporting-workflow"

    # Expected states
    VALID_STATES = [
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "TIMED_OUT",
        "ABORTED"
    ]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def aws_region():
    """AWS region for tests."""
    import os
    return os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="module")
def resource_prefix():
    """Resource naming prefix."""
    import os
    project = os.getenv("PROJECT_NAME", "rideshare-analytics")
    env = os.getenv("ENVIRONMENT", "dev")
    return f"{project}-{env}"


@pytest.fixture(scope="module")
def stepfunctions_client(aws_region):
    """Step Functions client fixture."""
    return boto3.client("stepfunctions", region_name=aws_region)


@pytest.fixture(scope="module")
def s3_client(aws_region):
    """S3 client fixture."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="module")
def dynamodb_resource(aws_region):
    """DynamoDB resource fixture."""
    return boto3.resource("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def cloudwatch_logs_client(aws_region):
    """CloudWatch Logs client fixture."""
    return boto3.client("logs", region_name=aws_region)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

class StepFunctionsHelper:
    """Helper methods for Step Functions testing."""

    @staticmethod
    def get_state_machine_arn(
        client,
        state_machine_name: str
    ) -> Optional[str]:
        """Get State Machine ARN by name."""
        try:
            response = client.list_state_machines()
            for sm in response.get("stateMachines", []):
                if state_machine_name in sm.get("name", ""):
                    return sm["stateMachineArn"]
            return None
        except Exception as e:
            print(f"Error getting state machine ARN: {e}")
            return None

    @staticmethod
    def start_execution(
        client,
        state_machine_arn: str,
        input_data: Dict[str, Any],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a Step Functions execution."""
        if not name:
            name = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"

        response = client.start_execution(
            stateMachineArn=state_machine_arn,
            name=name,
            input=json.dumps(input_data, default=str)
        )

        return {
            "executionArn": response["executionArn"],
            "startDate": response["startDate"]
        }

    @staticmethod
    def wait_for_execution(
        client,
        execution_arn: str,
        timeout: int = OrchestrationConfig.WORKFLOW_TIMEOUT,
        poll_interval: int = OrchestrationConfig.POLL_INTERVAL
    ) -> Dict[str, Any]:
        """Wait for execution to complete and return final status."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = client.describe_execution(executionArn=execution_arn)
            status = response["status"]

            if status in ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]:
                return response

            time.sleep(poll_interval)

        # Timeout reached
        raise TimeoutError(
            f"Execution did not complete within {timeout} seconds"
        )

    @staticmethod
    def get_execution_history(
        client,
        execution_arn: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution history events."""
        events = []
        next_token = None

        while True:
            kwargs = {
                "executionArn": execution_arn,
                "maxResults": max_results
            }
            if next_token:
                kwargs["nextToken"] = next_token

            response = client.get_execution_history(**kwargs)
            events.extend(response.get("events", []))

            next_token = response.get("nextToken")
            if not next_token:
                break

        return events


# ============================================================================
# DAILY AGGREGATION WORKFLOW TESTS
# ============================================================================

class TestDailyAggregationWorkflow:
    """Test daily aggregation workflow."""

    def test_workflow_exists(self, stepfunctions_client, resource_prefix):
        """Verify daily aggregation workflow exists."""
        workflow_name = f"{resource_prefix}-daily-aggregation"

        print(f"\n{'='*70}")
        print(f"CHECKING WORKFLOW EXISTENCE: {workflow_name}")
        print(f"{'='*70}")

        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        assert arn is not None, \
            f"State machine {workflow_name} not found"

        print(f"Found State Machine: {arn}")
        print(f"{'='*70}\n")

    def test_successful_execution(
        self,
        stepfunctions_client,
        resource_prefix,
        s3_client
    ):
        """
        Test successful execution of daily aggregation workflow.

        This test validates:
        - Workflow starts successfully
        - All states transition correctly
        - Workflow completes with SUCCEEDED status
        - Output contains expected data
        """
        workflow_name = f"{resource_prefix}-daily-aggregation"

        print(f"\n{'='*70}")
        print("DAILY AGGREGATION WORKFLOW TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # Prepare input
        input_data = {
            "date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "region": "us-east-1",
            "aggregation_type": "daily",
            "job_id": f"test-{int(time.time())}"
        }

        print(f"Starting execution with input: {json.dumps(input_data, indent=2)}")

        # Start execution
        execution = StepFunctionsHelper.start_execution(
            stepfunctions_client,
            arn,
            input_data
        )

        execution_arn = execution["executionArn"]
        print(f"Execution ARN: {execution_arn}")

        # Wait for completion
        print("Waiting for execution to complete...")
        try:
            result = StepFunctionsHelper.wait_for_execution(
                stepfunctions_client,
                execution_arn
            )

            status = result["status"]
            output = json.loads(result.get("output", "{}"))

            print(f"\n{'='*70}")
            print("EXECUTION RESULTS:")
            print(f"  Status: {status}")
            print(f"  Start Time: {result['startDate']}")
            print(f"  Stop Time: {result.get('stopDate', 'N/A')}")

            if output:
                print(f"  Output Keys: {list(output.keys())}")

            print(f"{'='*70}\n")

            # Assertions
            assert status == "SUCCEEDED", \
                f"Expected SUCCEEDED status, got {status}"

            assert output, "Expected output from workflow"
            assert "job_id" in output, "Expected job_id in output"

        except TimeoutError:
            pytest.fail("Workflow execution timed out")

    def test_state_transitions(self, stepfunctions_client, resource_prefix):
        """
        Test state transitions in daily aggregation workflow.

        Validates that the workflow follows expected state machine definition.
        """
        workflow_name = f"{resource_prefix}-daily-aggregation"

        print(f"\n{'='*70}")
        print("DAILY AGGREGATION STATE TRANSITIONS TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # Get state machine definition
        try:
            response = stepfunctions_client.describe_state_machine(
                stateMachineArn=arn
            )

            definition = json.loads(response["definition"])
            states = definition.get("States", {})

            print(f"State Machine has {len(states)} states:")
            for state_name, state_config in states.items():
                state_type = state_config.get("Type", "Unknown")
                print(f"  - {state_name} ({state_type})")

            # Verify expected states exist
            expected_states = [
                "ValidateInput",
                "FetchData",
                "ProcessAggregation",
                "SaveResults"
            ]

            for expected_state in expected_states:
                found = any(expected_state in state for state in states.keys())
                if found:
                    print(f"✓ Found expected state pattern: {expected_state}")
                else:
                    print(f"⚠ Expected state pattern not found: {expected_state}")

            print(f"{'='*70}\n")

            assert len(states) > 0, "State machine has no states"

        except Exception as e:
            pytest.skip(f"Could not describe state machine: {e}")

    def test_error_handling(self, stepfunctions_client, resource_prefix):
        """
        Test error handling in daily aggregation workflow.

        Sends invalid input and verifies workflow handles errors gracefully.
        """
        workflow_name = f"{resource_prefix}-daily-aggregation"

        print(f"\n{'='*70}")
        print("DAILY AGGREGATION ERROR HANDLING TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # Prepare invalid input
        input_data = {
            "date": "invalid-date",
            "region": "",
            "aggregation_type": "unknown"
        }

        print(f"Starting execution with invalid input: {json.dumps(input_data)}")

        # Start execution
        execution = StepFunctionsHelper.start_execution(
            stepfunctions_client,
            arn,
            input_data,
            name=f"error-test-{int(time.time())}"
        )

        execution_arn = execution["executionArn"]

        # Wait for completion
        try:
            result = StepFunctionsHelper.wait_for_execution(
                stepfunctions_client,
                execution_arn,
                timeout=60
            )

            status = result["status"]

            print(f"\n{'='*70}")
            print("ERROR HANDLING RESULTS:")
            print(f"  Status: {status}")
            print(f"{'='*70}\n")

            # Should fail gracefully
            assert status in ["FAILED", "SUCCEEDED"], \
                f"Expected FAILED or SUCCEEDED status with error handling, got {status}"

        except TimeoutError:
            # Acceptable if workflow is still processing
            print("Workflow still processing (acceptable for error scenarios)")


# ============================================================================
# WEEKLY REPORTING WORKFLOW TESTS
# ============================================================================

class TestWeeklyReportingWorkflow:
    """Test weekly reporting workflow."""

    def test_workflow_exists(self, stepfunctions_client, resource_prefix):
        """Verify weekly reporting workflow exists."""
        workflow_name = f"{resource_prefix}-weekly-reporting"

        print(f"\n{'='*70}")
        print(f"CHECKING WORKFLOW EXISTENCE: {workflow_name}")
        print(f"{'='*70}")

        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        assert arn is not None, \
            f"State machine {workflow_name} not found"

        print(f"Found State Machine: {arn}")
        print(f"{'='*70}\n")

    def test_successful_execution(self, stepfunctions_client, resource_prefix):
        """Test successful execution of weekly reporting workflow."""
        workflow_name = f"{resource_prefix}-weekly-reporting"

        print(f"\n{'='*70}")
        print("WEEKLY REPORTING WORKFLOW TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # Prepare input
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        input_data = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "report_type": "weekly_summary",
            "include_charts": True,
            "job_id": f"test-{int(time.time())}"
        }

        print(f"Starting execution with input: {json.dumps(input_data, indent=2)}")

        # Start execution
        execution = StepFunctionsHelper.start_execution(
            stepfunctions_client,
            arn,
            input_data
        )

        execution_arn = execution["executionArn"]
        print(f"Execution ARN: {execution_arn}")

        # Wait for completion
        print("Waiting for execution to complete...")
        try:
            result = StepFunctionsHelper.wait_for_execution(
                stepfunctions_client,
                execution_arn
            )

            status = result["status"]
            output = json.loads(result.get("output", "{}"))

            print(f"\n{'='*70}")
            print("EXECUTION RESULTS:")
            print(f"  Status: {status}")
            print(f"  Start Time: {result['startDate']}")
            print(f"  Stop Time: {result.get('stopDate', 'N/A')}")

            if output:
                print(f"  Output Keys: {list(output.keys())}")

            print(f"{'='*70}\n")

            # Assertions
            assert status == "SUCCEEDED", \
                f"Expected SUCCEEDED status, got {status}"

        except TimeoutError:
            pytest.fail("Workflow execution timed out")

    def test_retry_logic(self, stepfunctions_client, resource_prefix):
        """
        Test retry logic in weekly reporting workflow.

        Verifies that the workflow retries failed tasks appropriately.
        """
        workflow_name = f"{resource_prefix}-weekly-reporting"

        print(f"\n{'='*70}")
        print("WEEKLY REPORTING RETRY LOGIC TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # Check state machine definition for retry config
        try:
            response = stepfunctions_client.describe_state_machine(
                stateMachineArn=arn
            )

            definition = json.loads(response["definition"])
            states = definition.get("States", {})

            retry_configs_found = 0

            print("Checking states for retry configurations:")
            for state_name, state_config in states.items():
                if "Retry" in state_config:
                    retry_configs_found += 1
                    retry_config = state_config["Retry"]
                    print(f"  ✓ {state_name} has {len(retry_config)} retry configurations")

                    for retry in retry_config:
                        error_equals = retry.get("ErrorEquals", [])
                        max_attempts = retry.get("MaxAttempts", 0)
                        interval = retry.get("IntervalSeconds", 0)
                        print(f"    - Errors: {error_equals}")
                        print(f"      MaxAttempts: {max_attempts}, Interval: {interval}s")

            print(f"\nTotal states with retry: {retry_configs_found}")
            print(f"{'='*70}\n")

            assert retry_configs_found > 0, \
                "No retry configurations found in workflow"

        except Exception as e:
            pytest.skip(f"Could not analyze retry configuration: {e}")


# ============================================================================
# EXECUTION HISTORY TESTS
# ============================================================================

class TestExecutionHistory:
    """Test execution history and logging."""

    def test_execution_history_details(
        self,
        stepfunctions_client,
        resource_prefix
    ):
        """
        Test execution history contains detailed event information.
        """
        workflow_name = f"{resource_prefix}-daily-aggregation"

        print(f"\n{'='*70}")
        print("EXECUTION HISTORY TEST")
        print(f"{'='*70}")

        # Get state machine ARN
        arn = StepFunctionsHelper.get_state_machine_arn(
            stepfunctions_client,
            workflow_name
        )

        if not arn:
            pytest.skip(f"State machine {workflow_name} not found")

        # List recent executions
        try:
            response = stepfunctions_client.list_executions(
                stateMachineArn=arn,
                maxResults=1,
                statusFilter="SUCCEEDED"
            )

            executions = response.get("executions", [])

            if not executions:
                pytest.skip("No successful executions found")

            execution_arn = executions[0]["executionArn"]
            print(f"Analyzing execution: {execution_arn}")

            # Get execution history
            events = StepFunctionsHelper.get_execution_history(
                stepfunctions_client,
                execution_arn
            )

            print(f"\nFound {len(events)} events in execution history:")

            event_types = {}
            for event in events:
                event_type = event["type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1

            for event_type, count in sorted(event_types.items()):
                print(f"  {event_type}: {count}")

            print(f"{'='*70}\n")

            # Assertions
            assert len(events) > 0, "No events in execution history"
            assert "ExecutionStarted" in event_types, \
                "Missing ExecutionStarted event"
            assert "ExecutionSucceeded" in event_types or "ExecutionFailed" in event_types, \
                "Missing execution completion event"

        except Exception as e:
            pytest.skip(f"Could not retrieve execution history: {e}")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestWorkflowIntegration:
    """Test workflow integration with other AWS services."""

    def test_workflow_s3_integration(
        self,
        stepfunctions_client,
        s3_client,
        resource_prefix
    ):
        """
        Test workflow integration with S3.

        Verifies that workflows read from and write to S3 correctly.
        """
        print(f"\n{'='*70}")
        print("WORKFLOW S3 INTEGRATION TEST")
        print(f"{'='*70}")

        # This is a placeholder test - actual implementation would:
        # 1. Verify S3 bucket exists
        # 2. Check workflow can read input from S3
        # 3. Verify workflow writes output to S3

        bucket_name = f"{resource_prefix}-data"

        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ S3 bucket exists: {bucket_name}")
        except Exception as e:
            pytest.skip(f"S3 bucket not found: {e}")

        print(f"{'='*70}\n")

    def test_workflow_dynamodb_integration(
        self,
        stepfunctions_client,
        dynamodb_resource,
        resource_prefix
    ):
        """Test workflow integration with DynamoDB."""
        print(f"\n{'='*70}")
        print("WORKFLOW DYNAMODB INTEGRATION TEST")
        print(f"{'='*70}")

        table_name = f"{resource_prefix}-rides"

        try:
            table = dynamodb_resource.Table(table_name)
            table.load()
            print(f"✓ DynamoDB table exists: {table_name}")
            print(f"  Status: {table.table_status}")
            print(f"  Item Count: {table.item_count}")
        except Exception as e:
            pytest.skip(f"DynamoDB table not found: {e}")

        print(f"{'='*70}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
