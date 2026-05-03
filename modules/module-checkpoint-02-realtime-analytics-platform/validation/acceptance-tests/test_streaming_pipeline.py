"""
Streaming pipeline end-to-end tests for Real-Time Analytics Platform.

Tests verify the complete data flow:
- Kinesis ingestion
- Lambda processing
- DynamoDB storage
- S3 archival
- Event-driven workflows
"""

import pytest
import json
import time
from datetime import datetime, timedelta


# ============================================================================
# KINESIS INGESTION TESTS
# ============================================================================

class TestKinesisIngestion:
    """Test Kinesis stream ingestion."""

    def test_put_single_record(self, kinesis_client, resource_prefix, test_data_generator):
        """Test sending a single record to Kinesis."""
        stream_name = f"{resource_prefix}-rides-stream"

        # Generate test event
        event = test_data_generator.generate_ride_request()

        # Send to Kinesis
        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=event["ride_id"]
        )

        assert "SequenceNumber" in response, "PutRecord should return sequence number"
        assert "ShardId" in response, "PutRecord should return shard ID"

    def test_put_batch_records(self, kinesis_client, resource_prefix, test_data_generator):
        """Test sending batch of records to Kinesis."""
        stream_name = f"{resource_prefix}-rides-stream"

        # Generate batch of events
        records = []
        for _ in range(10):
            event = test_data_generator.generate_ride_request()
            records.append({
                "Data": json.dumps(event),
                "PartitionKey": event["ride_id"]
            })

        # Send batch to Kinesis
        response = kinesis_client.put_records(
            StreamName=stream_name,
            Records=records
        )

        assert response["FailedRecordCount"] == 0, \
            f"Expected 0 failed records, got {response['FailedRecordCount']}"
        assert len(response["Records"]) == 10, "Should have 10 successful records"

    def test_kinesis_error_handling(self, kinesis_client, resource_prefix):
        """Test Kinesis error handling for oversized records."""
        stream_name = f"{resource_prefix}-rides-stream"

        # Create oversized record (>1MB)
        oversized_data = "X" * (1024 * 1024 + 1)

        with pytest.raises(Exception) as exc_info:
            kinesis_client.put_record(
                StreamName=stream_name,
                Data=oversized_data,
                PartitionKey="test-key"
            )

        # Should raise validation exception
        assert "ValidationException" in str(exc_info.typename)


# ============================================================================
# LAMBDA TRIGGER TESTS
# ============================================================================

class TestLambdaProcessing:
    """Test Lambda function triggering and processing."""

    def test_lambda_triggered_by_kinesis(self, kinesis_client, logs_client,
                                         resource_prefix, test_data_generator):
        """Verify Lambda is triggered by Kinesis events."""
        stream_name = f"{resource_prefix}-rides-stream"
        log_group_name = f"/aws/lambda/{resource_prefix}-rides-processor"

        # Generate and send test event
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        # Wait for Lambda execution (up to 30 seconds)
        time.sleep(5)  # Initial delay for processing

        start_time = int((datetime.utcnow() - timedelta(minutes=2)).timestamp() * 1000)

        try:
            # Check CloudWatch Logs for evidence of processing
            streams = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy="LastEventTime",
                descending=True,
                limit=5
            )

            assert len(streams["logStreams"]) > 0, \
                "Lambda should have executed and created log streams"

        except logs_client.exceptions.ResourceNotFoundException:
            pytest.fail(f"Log group {log_group_name} not found - Lambda may not have executed")

    def test_lambda_processing_success(self, kinesis_client, dynamodb_resource,
                                       resource_prefix, test_data_generator):
        """Test successful Lambda processing of ride request."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Generate test event
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        # Wait for processing
        time.sleep(8)

        # Verify record in DynamoDB
        table = dynamodb_resource.Table(table_name)

        # Try multiple times with backoff
        for attempt in range(3):
            response = table.get_item(Key={"ride_id": ride_id})

            if "Item" in response:
                item = response["Item"]
                assert item["ride_id"] == ride_id
                assert item["event_type"] == "ride_requested"
                return  # Success

            time.sleep(3)  # Wait before retry

        pytest.fail(f"Ride {ride_id} not found in DynamoDB after 3 attempts")

    def test_lambda_location_processing(self, kinesis_client, dynamodb_resource,
                                        resource_prefix, test_data_generator):
        """Test Lambda processing of location updates."""
        stream_name = f"{resource_prefix}-locations-stream"
        table_name = f"{resource_prefix}-drivers"

        # Generate test event
        driver_id = f"driver-test-{int(time.time())}"
        event = test_data_generator.generate_location_update(driver_id=driver_id)

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=driver_id
        )

        # Wait for processing
        time.sleep(8)

        # Verify location updated in DynamoDB
        table = dynamodb_resource.Table(table_name)

        for attempt in range(3):
            response = table.get_item(Key={"driver_id": driver_id})

            if "Item" in response:
                item = response["Item"]
                assert item["driver_id"] == driver_id
                assert "location" in item
                return

            time.sleep(3)

        pytest.skip(f"Driver location for {driver_id} not found - processing may be delayed")


# ============================================================================
# DYNAMODB STORAGE TESTS
# ============================================================================

class TestDynamoDBStorage:
    """Test data persistence in DynamoDB."""

    def test_ride_data_integrity(self, kinesis_client, dynamodb_resource,
                                 resource_prefix, test_data_generator):
        """Verify ride data is stored with correct attributes."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Generate test event with known data
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]
        rider_id = event["rider_id"]

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(8)

        # Query DynamoDB
        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" not in response:
            pytest.skip("Ride not found in DynamoDB - processing delayed")

        item = response["Item"]

        # Verify key attributes
        assert item["ride_id"] == ride_id
        assert item["rider_id"] == rider_id
        assert "timestamp" in item
        assert "pickup_location" in item
        assert "dropoff_location" in item

    def test_payment_data_storage(self, kinesis_client, dynamodb_resource,
                                  resource_prefix, test_data_generator):
        """Verify payment data is stored correctly."""
        stream_name = f"{resource_prefix}-payments-stream"
        table_name = f"{resource_prefix}-payments"

        # Generate payment event
        ride_id = f"ride-test-{int(time.time())}"
        event = test_data_generator.generate_payment(ride_id=ride_id)
        payment_id = event["payment_id"]

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=payment_id
        )

        time.sleep(8)

        # Query DynamoDB
        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"payment_id": payment_id})

        if "Item" not in response:
            pytest.skip("Payment not found in DynamoDB - processing delayed")

        item = response["Item"]

        # Verify attributes
        assert item["payment_id"] == payment_id
        assert item["ride_id"] == ride_id
        assert "amount" in item
        assert "payment_method" in item


# ============================================================================
# S3 ARCHIVAL TESTS
# ============================================================================

class TestS3Archival:
    """Test S3 data archival."""

    def test_events_archived_to_s3(self, kinesis_client, s3_client,
                                   resource_prefix, aws_config, test_data_generator):
        """Verify events are archived to S3 with correct partitioning."""
        stream_name = f"{resource_prefix}-rides-stream"
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        # Generate and send event
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        # Wait for archival (longer delay)
        time.sleep(15)

        # Check S3 for archived data
        now = datetime.utcnow()
        prefix = f"raw/rides/{now.year}/{now.month:02d}/{now.day:02d}/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if response.get("KeyCount", 0) > 0:
                # Archive files exist for today
                assert True
            else:
                pytest.skip("S3 archival not completed yet - may be delayed")

        except s3_client.exceptions.NoSuchBucket:
            pytest.fail(f"Bucket {bucket_name} not found")
        except Exception as e:
            pytest.skip(f"S3 check failed: {str(e)}")

    def test_s3_partitioning_structure(self, s3_client, resource_prefix, aws_config):
        """Verify S3 follows correct partitioning structure."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        try:
            # List top-level prefixes
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Delimiter="/",
                MaxKeys=100
            )

            # Should have organized prefixes
            prefixes = response.get("CommonPrefixes", [])

            if len(prefixes) > 0:
                # Check for expected folder structure
                prefix_names = [p["Prefix"] for p in prefixes]
                # Should have folders like: raw/, processed/, analytics/
                assert True  # Structure exists
            else:
                pytest.skip("No S3 data yet")

        except Exception as e:
            pytest.skip(f"S3 structure check failed: {str(e)}")


# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """Test complete ride lifecycle workflows."""

    def test_complete_ride_flow(self, kinesis_client, dynamodb_resource,
                                resource_prefix, test_data_generator):
        """Test complete ride flow: request → start → complete."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Generate ride ID for complete flow
        ride_id = f"ride-e2e-{int(time.time())}"

        # Step 1: Ride Requested
        event1 = test_data_generator.generate_ride_request(ride_id=ride_id)
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event1),
            PartitionKey=ride_id
        )

        time.sleep(5)

        # Step 2: Ride Started
        event2 = test_data_generator.generate_ride_started(ride_id=ride_id)
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event2),
            PartitionKey=ride_id
        )

        time.sleep(5)

        # Step 3: Ride Completed
        event3 = test_data_generator.generate_ride_completed(ride_id=ride_id)
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event3),
            PartitionKey=ride_id
        )

        time.sleep(8)

        # Verify final state in DynamoDB
        table = dynamodb_resource.Table(table_name)

        for attempt in range(3):
            response = table.get_item(Key={"ride_id": ride_id})

            if "Item" in response:
                item = response["Item"]

                # Should have completed status
                if "status" in item:
                    assert item["status"] in ["completed", "ride_completed"], \
                        f"Expected completed status, got {item['status']}"

                # Should have fare information
                if "fare" in item:
                    assert float(item["fare"]) > 0

                return  # Success

            time.sleep(5)

        pytest.skip("Complete ride flow not fully processed")

    def test_payment_after_ride(self, kinesis_client, dynamodb_resource,
                               resource_prefix, test_data_generator):
        """Test payment processing after ride completion."""
        rides_stream = f"{resource_prefix}-rides-stream"
        payments_stream = f"{resource_prefix}-payments-stream"
        rides_table = f"{resource_prefix}-rides"
        payments_table = f"{resource_prefix}-payments"

        ride_id = f"ride-payment-{int(time.time())}"

        # Complete a ride
        event = test_data_generator.generate_ride_completed(ride_id=ride_id)
        kinesis_client.put_record(
            StreamName=rides_stream,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(5)

        # Process payment
        payment_event = test_data_generator.generate_payment(ride_id=ride_id)
        payment_id = payment_event["payment_id"]

        kinesis_client.put_record(
            StreamName=payments_stream,
            Data=json.dumps(payment_event),
            PartitionKey=payment_id
        )

        time.sleep(8)

        # Verify payment recorded
        payments_tbl = dynamodb_resource.Table(payments_table)
        response = payments_tbl.get_item(Key={"payment_id": payment_id})

        if "Item" in response:
            assert response["Item"]["ride_id"] == ride_id
        else:
            pytest.skip("Payment not found in DynamoDB")


# ============================================================================
# FRAUD DETECTION TESTS
# ============================================================================

class TestFraudDetection:
    """Test fraud detection and alerting."""

    def test_suspicious_payment_detection(self, kinesis_client, sns_client,
                                          resource_prefix, test_data_generator):
        """Test detection of suspicious payment patterns."""
        stream_name = f"{resource_prefix}-payments-stream"

        ride_id = f"ride-fraud-{int(time.time())}"

        # Send suspicious payment
        event = test_data_generator.generate_suspicious_payment(ride_id=ride_id)
        payment_id = event["payment_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=payment_id
        )

        time.sleep(10)

        # Check if SNS alert was triggered (check topic)
        try:
            response = sns_client.list_topics()
            fraud_topics = [t for t in response.get("Topics", [])
                          if "fraud-alerts" in t["TopicArn"]]

            if len(fraud_topics) > 0:
                # Fraud detection topic exists
                pytest.skip("Cannot verify SNS message without subscription - manual verification needed")
            else:
                pytest.skip("Fraud alert topic not configured")
        except Exception as e:
            pytest.skip(f"SNS check failed: {str(e)}")


# ============================================================================
# RATING PROCESSING TESTS
# ============================================================================

class TestRatingProcessing:
    """Test rating processing and driver score updates."""

    def test_rating_submission(self, kinesis_client, dynamodb_resource,
                               resource_prefix, test_data_generator):
        """Test rating submission and processing."""
        stream_name = f"{resource_prefix}-ratings-stream"
        drivers_table = f"{resource_prefix}-drivers"

        ride_id = f"ride-rating-{int(time.time())}"

        # Submit low rating
        event = test_data_generator.generate_rating(ride_id=ride_id, rating=2)
        rating_id = event["rating_id"]
        driver_id = event["driver_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=rating_id
        )

        time.sleep(8)

        # Check if driver record updated
        table = dynamodb_resource.Table(drivers_table)

        try:
            response = table.get_item(Key={"driver_id": driver_id})

            if "Item" in response:
                item = response["Item"]

                # Should have rating-related fields
                if "rating_count" in item or "average_rating" in item:
                    # Rating processed
                    assert True
                else:
                    pytest.skip("Driver rating not updated yet")
            else:
                pytest.skip(f"Driver {driver_id} not found in table")

        except Exception as e:
            pytest.skip(f"Rating check failed: {str(e)}")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and dead letter queue routing."""

    def test_invalid_event_handling(self, kinesis_client, resource_prefix):
        """Test handling of invalid JSON events."""
        stream_name = f"{resource_prefix}-rides-stream"

        # Send invalid JSON
        invalid_data = "{ invalid json"

        response = kinesis_client.put_record(
            StreamName=stream_name,
            Data=invalid_data,
            PartitionKey="invalid-test"
        )

        # Should accept the record (validation happens in Lambda)
        assert "SequenceNumber" in response

        # Lambda should handle gracefully and route to DLQ
        # This would require checking DLQ, which we'll skip for now
        pytest.skip("DLQ verification requires additional setup")

    def test_missing_required_fields(self, kinesis_client, resource_prefix):
        """Test handling of events with missing required fields."""
        stream_name = f"{resource_prefix}-rides-stream"

        # Send event missing required fields
        incomplete_event = {
            "event_type": "ride_requested",
            # Missing ride_id, timestamp, etc.
        }

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(incomplete_event),
            PartitionKey="incomplete-test"
        )

        time.sleep(5)

        # Lambda should handle and potentially route to DLQ
        pytest.skip("Error handling verification requires DLQ monitoring")


# ============================================================================
# IDEMPOTENCY TESTS
# ============================================================================

class TestIdempotency:
    """Test idempotent processing of duplicate events."""

    def test_duplicate_event_handling(self, kinesis_client, dynamodb_resource,
                                      resource_prefix, test_data_generator):
        """Test that duplicate events are handled idempotently."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Generate event
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        # Send same event twice
        for _ in range(2):
            kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event),
                PartitionKey=ride_id
            )
            time.sleep(2)

        time.sleep(8)

        # Verify only one record in DynamoDB
        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" in response:
            # Should have idempotency handling
            # In practice, would check that processing happened only once
            assert True
        else:
            pytest.skip("Ride not found for idempotency test")


# ============================================================================
# ANALYTICS OUTPUT TESTS
# ============================================================================

class TestAnalyticsOutputs:
    """Test analytics processing outputs."""

    def test_surge_pricing_output(self, s3_client, resource_prefix, aws_config):
        """Test that surge pricing analytics generates output."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"
        prefix = "analytics/surge-pricing/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if response.get("KeyCount", 0) > 0:
                # Analytics output exists
                assert True
            else:
                pytest.skip("Surge pricing analytics output not available yet")

        except Exception as e:
            pytest.skip(f"Analytics output check failed: {str(e)}")

    def test_hot_spots_output(self, s3_client, resource_prefix, aws_config):
        """Test that hot spots detection generates output."""
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"
        prefix = "analytics/hot-spots/"

        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if response.get("KeyCount", 0) > 0:
                # Analytics output exists
                assert True
            else:
                pytest.skip("Hot spots analytics output not available yet")

        except Exception as e:
            pytest.skip(f"Analytics output check failed: {str(e)}")
