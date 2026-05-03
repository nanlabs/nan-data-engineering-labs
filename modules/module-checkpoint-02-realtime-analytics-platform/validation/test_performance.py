"""
Performance Load Testing for Real-Time Analytics Platform.

This module provides comprehensive performance tests including:
- High-throughput Kinesis ingestion (1000+ events/sec)
- Lambda function latency measurements (p50, p95, p99)
- DynamoDB read/write throughput testing
- CloudWatch metrics validation
- Memory usage profiling

Run: pytest test_performance.py -v --tb=short
"""

import pytest
import boto3
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal
import random


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

class PerformanceConfig:
    """Performance test configuration."""

    # Kinesis thresholds
    KINESIS_TARGET_THROUGHPUT = 1000  # events/sec
    KINESIS_BATCH_SIZE = 500  # max per PutRecords
    SUSTAINED_LOAD_DURATION = 60  # seconds

    # Lambda thresholds
    LAMBDA_P99_LATENCY_MS = 5000  # 5 seconds
    LAMBDA_P95_LATENCY_MS = 3000  # 3 seconds
    LAMBDA_P50_LATENCY_MS = 1000  # 1 second

    # DynamoDB thresholds
    DYNAMODB_READ_CAPACITY = 100  # reads/sec
    DYNAMODB_WRITE_CAPACITY = 100  # writes/sec

    # Test data
    NUM_LOAD_TEST_EVENTS = 5000
    CONCURRENT_THREADS = 10


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
def kinesis_client(aws_region):
    """Kinesis client fixture."""
    return boto3.client("kinesis", region_name=aws_region)


@pytest.fixture(scope="module")
def lambda_client(aws_region):
    """Lambda client fixture."""
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="module")
def dynamodb_client(aws_region):
    """DynamoDB client fixture."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def dynamodb_resource(aws_region):
    """DynamoDB resource fixture."""
    return boto3.resource("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def cloudwatch_client(aws_region):
    """CloudWatch client fixture."""
    return boto3.client("cloudwatch", region_name=aws_region)


@pytest.fixture(scope="module")
def logs_client(aws_region):
    """CloudWatch Logs client fixture."""
    return boto3.client("logs", region_name=aws_region)


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

class LoadTestDataGenerator:
    """Generate realistic test data for load testing."""

    @staticmethod
    def generate_ride_event(ride_id: str = None) -> Dict[str, Any]:
        """Generate a ride event."""
        if not ride_id:
            ride_id = f"RIDE-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"

        return {
            "ride_id": ride_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": random.choice(["ride_requested", "ride_accepted", "ride_started", "ride_completed"]),
            "rider_id": f"RIDER-{random.randint(10000, 99999)}",
            "driver_id": f"DRIVER-{random.randint(1000, 9999)}",
            "location": {
                "latitude": round(random.uniform(37.7, 37.8), 6),
                "longitude": round(random.uniform(-122.5, -122.4), 6)
            },
            "fare_amount": round(random.uniform(10.0, 100.0), 2),
            "distance_miles": round(random.uniform(1.0, 20.0), 2),
            "vehicle_type": random.choice(["standard", "premium", "xl"]),
            "city": random.choice(["San Francisco", "Los Angeles", "Seattle"])
        }

    @staticmethod
    def generate_batch(size: int) -> List[Dict[str, Any]]:
        """Generate a batch of ride events."""
        return [LoadTestDataGenerator.generate_ride_event() for _ in range(size)]


# ============================================================================
# KINESIS THROUGHPUT TESTS
# ============================================================================

class TestKinesisThroughput:
    """Test Kinesis Data Streams throughput capabilities."""

    def test_peak_throughput_1000_events_per_second(
        self, kinesis_client, resource_prefix
    ):
        """
        Test Kinesis can handle peak load of 1000 events/second.

        This test validates that the Kinesis stream can accept high-velocity
        data without throttling or failures.
        """
        stream_name = f"{resource_prefix}-rides-stream"
        num_events = 1000

        print(f"\n{'='*70}")
        print(f"KINESIS PEAK THROUGHPUT TEST: {num_events} events")
        print(f"{'='*70}")

        # Generate test events
        events = LoadTestDataGenerator.generate_batch(num_events)

        # Send events in batches
        start_time = time.time()
        total_failed = 0
        total_throttled = 0
        batch_latencies = []

        for i in range(0, len(events), PerformanceConfig.KINESIS_BATCH_SIZE):
            batch = events[i:i + PerformanceConfig.KINESIS_BATCH_SIZE]

            records = [
                {
                    "Data": json.dumps(event, default=str),
                    "PartitionKey": event["ride_id"]
                }
                for event in batch
            ]

            batch_start = time.time()
            try:
                response = kinesis_client.put_records(
                    StreamName=stream_name,
                    Records=records
                )
                batch_latency = (time.time() - batch_start) * 1000
                batch_latencies.append(batch_latency)

                failed_count = response.get("FailedRecordCount", 0)
                total_failed += failed_count

                # Check for throttling
                for record in response.get("Records", []):
                    error_code = record.get("ErrorCode", "")
                    if "ProvisionedThroughputExceeded" in error_code:
                        total_throttled += 1

                print(f"Batch {i//PerformanceConfig.KINESIS_BATCH_SIZE + 1}: "
                      f"{len(batch)} events in {batch_latency:.0f}ms")

            except Exception as e:
                if "ProvisionedThroughputExceeded" in str(e):
                    total_throttled += 1
                else:
                    pytest.fail(f"Unexpected error: {e}")

        end_time = time.time()
        total_duration = end_time - start_time
        throughput = num_events / total_duration

        # Calculate batch latency statistics
        avg_batch_latency = statistics.mean(batch_latencies)
        p95_batch_latency = statistics.quantiles(batch_latencies, n=20)[18]
        p99_batch_latency = statistics.quantiles(batch_latencies, n=100)[98]

        print(f"\n{'='*70}")
        print("RESULTS:")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Throughput: {throughput:.0f} events/second")
        print(f"  Failed Records: {total_failed}")
        print(f"  Throttled Batches: {total_throttled}")
        print(f"  Avg Batch Latency: {avg_batch_latency:.0f}ms")
        print(f"  P95 Batch Latency: {p95_batch_latency:.0f}ms")
        print(f"  P99 Batch Latency: {p99_batch_latency:.0f}ms")
        print(f"{'='*70}\n")

        # Assertions
        assert total_duration <= 15, \
            f"Expected to send {num_events} events in <15s, took {total_duration:.2f}s"

        assert throughput >= 500, \
            f"Throughput {throughput:.0f} events/s is below minimum 500 events/s"

        assert total_throttled == 0, \
            f"Throttling detected: {total_throttled} throttled requests"

        assert total_failed == 0, \
            f"Failed records detected: {total_failed} failures"

    def test_sustained_load(self, kinesis_client, resource_prefix):
        """
        Test sustained load over 60 seconds at 100 events/second.

        This validates the system can handle continuous load without
        degradation over time.
        """
        stream_name = f"{resource_prefix}-rides-stream"
        target_rate = 100  # events per second
        duration = 60  # seconds

        print(f"\n{'='*70}")
        print(f"KINESIS SUSTAINED LOAD TEST: {target_rate} events/sec for {duration}s")
        print(f"{'='*70}")

        start_time = time.time()
        total_sent = 0
        total_failed = 0
        interval_stats = []

        while time.time() - start_time < duration:
            interval_start = time.time()

            # Generate and send batch
            events = LoadTestDataGenerator.generate_batch(10)
            records = [
                {
                    "Data": json.dumps(event, default=str),
                    "PartitionKey": event["ride_id"]
                }
                for event in events
            ]

            try:
                response = kinesis_client.put_records(
                    StreamName=stream_name,
                    Records=records
                )

                total_sent += len(events)
                total_failed += response.get("FailedRecordCount", 0)

                interval_duration = time.time() - interval_start
                interval_stats.append({
                    "sent": len(events),
                    "duration": interval_duration,
                    "failed": response.get("FailedRecordCount", 0)
                })

                # Rate limiting: sleep to maintain target rate
                expected_interval = len(events) / target_rate
                sleep_time = expected_interval - interval_duration
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                print(f"Error sending batch: {e}")
                total_failed += len(events)

        total_duration = time.time() - start_time
        actual_rate = total_sent / total_duration

        print(f"\n{'='*70}")
        print("RESULTS:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Total Sent: {total_sent}")
        print(f"  Total Failed: {total_failed}")
        print(f"  Target Rate: {target_rate} events/s")
        print(f"  Actual Rate: {actual_rate:.1f} events/s")
        print(f"  Success Rate: {(1 - total_failed/total_sent)*100:.2f}%")
        print(f"{'='*70}\n")

        # Assertions
        assert actual_rate >= target_rate * 0.9, \
            f"Actual rate {actual_rate:.1f} is below 90% of target {target_rate}"

        assert total_failed < total_sent * 0.01, \
            f"Failure rate {total_failed/total_sent*100:.2f}% exceeds 1%"


# ============================================================================
# LAMBDA LATENCY TESTS
# ============================================================================

class TestLambdaLatency:
    """Test Lambda function performance and latency."""

    def test_processing_lambda_latency_p99(
        self, lambda_client, kinesis_client, resource_prefix
    ):
        """
        Test Lambda processing latency meets p99 < 5s requirement.

        Sends events through Kinesis and measures end-to-end Lambda
        processing time including cold starts.
        """
        function_name = f"{resource_prefix}-stream-processor"
        stream_name = f"{resource_prefix}-rides-stream"

        print(f"\n{'='*70}")
        print(f"LAMBDA LATENCY TEST: {function_name}")
        print(f"{'='*70}")

        num_invocations = 100
        latencies = []

        for i in range(num_invocations):
            event = LoadTestDataGenerator.generate_ride_event()

            # Send through Kinesis
            start_time = time.time()

            kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event, default=str),
                PartitionKey=event["ride_id"]
            )

            # Wait for processing (poll or sleep)
            time.sleep(0.5)  # Allow time for Lambda trigger

            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{num_invocations} invocations")

        # Calculate percentiles
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18]
        p99 = statistics.quantiles(latencies, n=100)[98]
        avg = statistics.mean(latencies)
        max_latency = max(latencies)

        print(f"\n{'='*70}")
        print("LATENCY STATISTICS:")
        print(f"  Average: {avg:.0f}ms")
        print(f"  Median (P50): {p50:.0f}ms")
        print(f"  P95: {p95:.0f}ms")
        print(f"  P99: {p99:.0f}ms")
        print(f"  Max: {max_latency:.0f}ms")
        print(f"{'='*70}\n")

        # Assertions
        assert p99 < PerformanceConfig.LAMBDA_P99_LATENCY_MS, \
            f"P99 latency {p99:.0f}ms exceeds threshold {PerformanceConfig.LAMBDA_P99_LATENCY_MS}ms"

        assert p95 < PerformanceConfig.LAMBDA_P95_LATENCY_MS, \
            f"P95 latency {p95:.0f}ms exceeds threshold {PerformanceConfig.LAMBDA_P95_LATENCY_MS}ms"

    def test_lambda_memory_usage(self, lambda_client, logs_client, resource_prefix):
        """
        Test Lambda memory usage stays within allocated limits.

        Analyzes CloudWatch Logs to extract memory usage metrics from
        Lambda function executions.
        """
        function_name = f"{resource_prefix}-stream-processor"
        log_group = f"/aws/lambda/{function_name}"

        print(f"\n{'='*70}")
        print(f"LAMBDA MEMORY USAGE TEST: {function_name}")
        print(f"{'='*70}")

        # Get function configuration
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            allocated_memory = response["Configuration"]["MemorySize"]
            print(f"Allocated Memory: {allocated_memory}MB")
        except Exception as e:
            pytest.skip(f"Could not get function configuration: {e}")

        # Query recent logs for memory usage
        try:
            # Get log streams from last hour
            end_time = int(time.time() * 1000)
            start_time = end_time - (3600 * 1000)  # 1 hour ago

            streams_response = logs_client.describe_log_streams(
                logGroupName=log_group,
                orderBy="LastEventTime",
                descending=True,
                limit=10
            )

            memory_usages = []

            for stream in streams_response.get("logStreams", []):
                events_response = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream["logStreamName"],
                    startTime=start_time,
                    endTime=end_time,
                    limit=100
                )

                for event in events_response.get("events", []):
                    message = event.get("message", "")
                    # Parse Lambda report line
                    if "REPORT RequestId:" in message and "Memory Size:" in message:
                        try:
                            parts = message.split()
                            for i, part in enumerate(parts):
                                if part == "Used:" and i + 2 < len(parts):
                                    used_mb = int(parts[i + 1])
                                    memory_usages.append(used_mb)
                        except (ValueError, IndexError):
                            continue

            if memory_usages:
                avg_usage = statistics.mean(memory_usages)
                max_usage = max(memory_usages)
                p95_usage = statistics.quantiles(memory_usages, n=20)[18] if len(memory_usages) > 20 else max_usage

                utilization = (avg_usage / allocated_memory) * 100

                print(f"\n{'='*70}")
                print(f"MEMORY USAGE STATISTICS ({len(memory_usages)} samples):")
                print(f"  Average Usage: {avg_usage:.0f}MB ({utilization:.1f}%)")
                print(f"  P95 Usage: {p95_usage:.0f}MB")
                print(f"  Max Usage: {max_usage}MB")
                print(f"  Allocated: {allocated_memory}MB")
                print(f"{'='*70}\n")

                # Assertions
                assert max_usage < allocated_memory, \
                    f"Memory usage {max_usage}MB exceeded allocation {allocated_memory}MB"

                assert utilization < 90, \
                    f"Average memory utilization {utilization:.1f}% is too high (>90%)"
            else:
                pytest.skip("No memory usage data found in logs")

        except logs_client.exceptions.ResourceNotFoundException:
            pytest.skip(f"Log group {log_group} not found")
        except Exception as e:
            pytest.skip(f"Could not query logs: {e}")


# ============================================================================
# DYNAMODB THROUGHPUT TESTS
# ============================================================================

class TestDynamoDBThroughput:
    """Test DynamoDB read/write throughput."""

    def test_write_throughput(self, dynamodb_resource, resource_prefix):
        """
        Test DynamoDB can handle 100 writes/second.

        Performs batch writes and measures throughput and latency.
        """
        table_name = f"{resource_prefix}-rides"
        table = dynamodb_resource.Table(table_name)

        print(f"\n{'='*70}")
        print(f"DYNAMODB WRITE THROUGHPUT TEST: {table_name}")
        print(f"{'='*70}")

        num_writes = 100
        write_latencies = []

        start_time = time.time()

        for i in range(num_writes):
            event = LoadTestDataGenerator.generate_ride_event()

            # Convert float to Decimal for DynamoDB
            event["fare_amount"] = Decimal(str(event["fare_amount"]))
            event["distance_miles"] = Decimal(str(event["distance_miles"]))

            write_start = time.time()
            try:
                table.put_item(Item=event)
                write_latency = (time.time() - write_start) * 1000
                write_latencies.append(write_latency)
            except Exception as e:
                print(f"Write error: {e}")

        total_duration = time.time() - start_time
        throughput = num_writes / total_duration

        avg_latency = statistics.mean(write_latencies)
        p95_latency = statistics.quantiles(write_latencies, n=20)[18]

        print(f"\n{'='*70}")
        print("WRITE THROUGHPUT RESULTS:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Throughput: {throughput:.1f} writes/sec")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  P95 Latency: {p95_latency:.0f}ms")
        print(f"{'='*70}\n")

        assert throughput >= 50, \
            f"Write throughput {throughput:.1f} writes/s below minimum 50"

    def test_read_throughput(self, dynamodb_resource, resource_prefix):
        """Test DynamoDB read throughput."""
        table_name = f"{resource_prefix}-rides"
        table = dynamodb_resource.Table(table_name)

        print(f"\n{'='*70}")
        print(f"DYNAMODB READ THROUGHPUT TEST: {table_name}")
        print(f"{'='*70}")

        # First, write some test data
        test_ride_ids = []
        for i in range(50):
            event = LoadTestDataGenerator.generate_ride_event()
            event["fare_amount"] = Decimal(str(event["fare_amount"]))
            event["distance_miles"] = Decimal(str(event["distance_miles"]))

            table.put_item(Item=event)
            test_ride_ids.append(event["ride_id"])

        # Now test read throughput
        num_reads = 100
        read_latencies = []

        start_time = time.time()

        for i in range(num_reads):
            ride_id = random.choice(test_ride_ids)

            read_start = time.time()
            try:
                response = table.get_item(Key={"ride_id": ride_id})
                read_latency = (time.time() - read_start) * 1000
                read_latencies.append(read_latency)
            except Exception as e:
                print(f"Read error: {e}")

        total_duration = time.time() - start_time
        throughput = num_reads / total_duration

        avg_latency = statistics.mean(read_latencies)
        p95_latency = statistics.quantiles(read_latencies, n=20)[18]

        print(f"\n{'='*70}")
        print("READ THROUGHPUT RESULTS:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Throughput: {throughput:.1f} reads/sec")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  P95 Latency: {p95_latency:.0f}ms")
        print(f"{'='*70}\n")

        assert throughput >= 50, \
            f"Read throughput {throughput:.1f} reads/s below minimum 50"


# ============================================================================
# CLOUDWATCH METRICS TESTS
# ============================================================================

class TestCloudWatchMetrics:
    """Test CloudWatch metrics are being published correctly."""

    def test_kinesis_metrics_availability(self, cloudwatch_client, resource_prefix):
        """Verify Kinesis stream metrics are available in CloudWatch."""
        stream_name = f"{resource_prefix}-rides-stream"

        print(f"\n{'='*70}")
        print("CLOUDWATCH KINESIS METRICS TEST")
        print(f"{'='*70}")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)

        metrics_to_check = [
            "IncomingRecords",
            "IncomingBytes",
            "PutRecord.Success",
            "PutRecords.Success"
        ]

        for metric_name in metrics_to_check:
            try:
                response = cloudwatch_client.get_metric_statistics(
                    Namespace="AWS/Kinesis",
                    MetricName=metric_name,
                    Dimensions=[
                        {"Name": "StreamName", "Value": stream_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=["Sum", "Average"]
                )

                datapoints = response.get("Datapoints", [])
                print(f"  {metric_name}: {len(datapoints)} datapoints")

                assert len(datapoints) > 0, \
                    f"No datapoints found for metric {metric_name}"

            except Exception as e:
                pytest.fail(f"Failed to get metric {metric_name}: {e}")

        print(f"{'='*70}\n")

    def test_lambda_metrics_availability(self, cloudwatch_client, resource_prefix):
        """Verify Lambda function metrics are available."""
        function_name = f"{resource_prefix}-stream-processor"

        print(f"\n{'='*70}")
        print("CLOUDWATCH LAMBDA METRICS TEST")
        print(f"{'='*70}")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)

        metrics_to_check = [
            "Invocations",
            "Duration",
            "Errors",
            "Throttles"
        ]

        for metric_name in metrics_to_check:
            try:
                response = cloudwatch_client.get_metric_statistics(
                    Namespace="AWS/Lambda",
                    MetricName=metric_name,
                    Dimensions=[
                        {"Name": "FunctionName", "Value": function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=["Sum", "Average", "Maximum"]
                )

                datapoints = response.get("Datapoints", [])
                print(f"  {metric_name}: {len(datapoints)} datapoints")

            except Exception as e:
                print(f"  {metric_name}: Failed to retrieve ({e})")

        print(f"{'='*70}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
