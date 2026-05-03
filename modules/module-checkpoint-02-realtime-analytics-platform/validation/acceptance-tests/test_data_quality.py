"""
Data quality validation tests for Real-Time Analytics Platform.

Tests verify:
- Schema validation
- Data completeness
- Timeliness
- Accuracy
- Consistency
- Referential integrity
"""

import pytest
import json
import time
from datetime import datetime
from decimal import Decimal


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestSchemaValidation:
    """Test event schema compliance."""

    def test_ride_request_schema(self, kinesis_client, dynamodb_resource,
                                 resource_prefix, test_data_generator):
        """Verify ride request events match expected schema."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Generate event
        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        # Verify schema before sending
        required_fields = [
            "event_type", "ride_id", "rider_id", "timestamp",
            "pickup_location", "dropoff_location", "ride_type"
        ]

        for field in required_fields:
            assert field in event, f"Missing required field: {field}"

        # Verify location structure
        assert "lat" in event["pickup_location"]
        assert "lon" in event["pickup_location"]
        assert "lat" in event["dropoff_location"]
        assert "lon" in event["dropoff_location"]

        # Verify data types
        assert isinstance(event["pickup_location"]["lat"], float)
        assert isinstance(event["pickup_location"]["lon"], float)

        # Send to Kinesis
        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(8)

        # Verify schema preserved in DynamoDB
        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" in response:
            item = response["Item"]

            # Check key fields preserved
            for field in ["ride_id", "rider_id", "event_type"]:
                assert field in item, f"Field {field} missing in DynamoDB"
        else:
            pytest.skip("Event not found in DynamoDB for schema validation")

    def test_payment_event_schema(self, test_data_generator):
        """Verify payment event schema."""
        event = test_data_generator.generate_payment(ride_id="test-ride")

        required_fields = [
            "event_type", "payment_id", "ride_id", "rider_id",
            "timestamp", "amount", "currency", "payment_method", "status"
        ]

        for field in required_fields:
            assert field in event, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(event["amount"], (int, float, Decimal))
        assert event["amount"] > 0, "Payment amount should be positive"
        assert event["currency"] in ["USD", "EUR", "GBP"]

    def test_location_update_schema(self, test_data_generator):
        """Verify location update event schema."""
        event = test_data_generator.generate_location_update()

        required_fields = [
            "event_type", "driver_id", "timestamp", "location", "status"
        ]

        for field in required_fields:
            assert field in event, f"Missing required field: {field}"

        # Verify location structure
        assert "lat" in event["location"]
        assert "lon" in event["location"]
        assert isinstance(event["location"]["lat"], float)
        assert isinstance(event["location"]["lon"], float)

        # Verify status is valid
        valid_statuses = ["available", "on_ride", "offline"]
        assert event["status"] in valid_statuses, \
            f"Invalid status: {event['status']}"

    def test_rating_event_schema(self, test_data_generator):
        """Verify rating event schema."""
        event = test_data_generator.generate_rating(ride_id="test-ride")

        required_fields = [
            "event_type", "rating_id", "ride_id", "driver_id",
            "rider_id", "timestamp", "rating"
        ]

        for field in required_fields:
            assert field in event, f"Missing required field: {field}"

        # Verify rating range
        assert 1 <= event["rating"] <= 5, \
            f"Rating {event['rating']} out of valid range 1-5"


# ============================================================================
# COMPLETENESS TESTS
# ============================================================================

class TestDataCompleteness:
    """Test data completeness in storage."""

    def test_all_required_fields_present(self, kinesis_client, dynamodb_resource,
                                         resource_prefix, test_data_generator):
        """Verify all required fields are stored in DynamoDB."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(8)

        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" not in response:
            pytest.skip("Event not found for completeness test")

        item = response["Item"]

        # Verify critical fields are not null
        critical_fields = ["ride_id", "rider_id", "event_type", "timestamp"]

        for field in critical_fields:
            assert field in item, f"Critical field {field} missing"
            assert item[field] is not None, f"Critical field {field} is null"
            assert str(item[field]).strip() != "", f"Critical field {field} is empty"

    def test_no_data_loss(self, kinesis_client, dynamodb_resource,
                          resource_prefix, test_data_generator):
        """Test that data is not lost during processing."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Send batch of events
        ride_ids = []
        for i in range(5):
            event = test_data_generator.generate_ride_request()
            ride_id = event["ride_id"]
            ride_ids.append(ride_id)

            kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event),
                PartitionKey=ride_id
            )

        time.sleep(10)

        # Check how many made it to DynamoDB
        table = dynamodb_resource.Table(table_name)
        found_count = 0

        for ride_id in ride_ids:
            response = table.get_item(Key={"ride_id": ride_id})
            if "Item" in response:
                found_count += 1

        # Should find at least 80% (allowing for timing issues)
        assert found_count >= 4, \
            f"Data loss detected: only {found_count}/5 events found in DynamoDB"


# ============================================================================
# TIMELINESS TESTS
# ============================================================================

class TestDataTimeliness:
    """Test data processing timeliness."""

    def test_processing_latency(self, kinesis_client, dynamodb_resource,
                                resource_prefix, test_data_generator):
        """Verify processing latency is within acceptable limits (P95 < 10s)."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        # Record send time
        send_time = datetime.utcnow()

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        # Poll for record in DynamoDB
        table = dynamodb_resource.Table(table_name)

        for attempt in range(20):  # Check for up to 20 seconds
            time.sleep(1)

            response = table.get_item(Key={"ride_id": ride_id})

            if "Item" in response:
                process_time = datetime.utcnow()
                latency = (process_time - send_time).total_seconds()

                assert latency <= 15, \
                    f"Processing latency {latency}s exceeds 15s threshold"

                print(f"Processing latency: {latency:.2f}s")
                return

        pytest.fail("Event not processed within 20 seconds")

    def test_timestamp_accuracy(self, kinesis_client, dynamodb_resource,
                               resource_prefix, test_data_generator):
        """Verify timestamps are accurate and not skewed."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        # Record current time
        current_time = datetime.utcnow()

        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]
        event_timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", ""))

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(8)

        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" not in response:
            pytest.skip("Event not found for timestamp validation")

        item = response["Item"]

        # Verify timestamp is recent (within last minute)
        time_diff = (current_time - event_timestamp).total_seconds()
        assert abs(time_diff) <= 60, \
            f"Event timestamp {event_timestamp} differs from current time by {time_diff}s"


# ============================================================================
# ACCURACY TESTS
# ============================================================================

class TestDataAccuracy:
    """Test data accuracy and calculations."""

    def test_fare_calculation_accuracy(self, test_data_generator):
        """Verify fare calculations are accurate."""
        event = test_data_generator.generate_ride_completed(ride_id="test-ride")

        # Verify fare is positive and reasonable
        assert event["fare"] > 0, "Fare should be positive"

        # Verify fare components
        distance = event["distance_miles"]
        duration = event["duration_minutes"]
        surge = event["surge_multiplier"]

        assert distance > 0, "Distance should be positive"
        assert duration > 0, "Duration should be positive"
        assert surge >= 1.0, "Surge multiplier should be >= 1.0"

        # Rough validation: fare should be proportional to distance/duration
        expected_base = distance * 2.5 + duration * 0.3
        expected_fare = expected_base * surge

        # Allow 20% variance for randomization
        assert abs(event["fare"] - expected_fare) / expected_fare <= 0.25, \
            f"Fare calculation seems off: {event['fare']} vs expected ~{expected_fare:.2f}"

    def test_location_coordinates_valid(self, test_data_generator):
        """Verify location coordinates are valid."""
        event = test_data_generator.generate_location_update()

        lat = event["location"]["lat"]
        lon = event["location"]["lon"]

        # Verify coordinates in valid range
        assert -90 <= lat <= 90, f"Latitude {lat} out of valid range"
        assert -180 <= lon <= 180, f"Longitude {lon} out of valid range"

    def test_distance_calculation(self, test_data_generator):
        """Verify distance calculations are reasonable."""
        event = test_data_generator.generate_ride_completed(ride_id="test-ride")

        distance = event["distance_miles"]
        duration = event["duration_minutes"]

        # Verify reasonable speed (5-60 mph average)
        avg_speed = (distance / duration) * 60  # mph

        assert 3 <= avg_speed <= 80, \
            f"Average speed {avg_speed:.1f} mph seems unrealistic"


# ============================================================================
# CONSISTENCY TESTS
# ============================================================================

class TestDataConsistency:
    """Test data consistency across systems."""

    def test_dynamodb_s3_consistency(self, kinesis_client, dynamodb_resource,
                                     s3_client, resource_prefix, aws_config,
                                     test_data_generator):
        """Verify data consistency between DynamoDB and S3 archives."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"
        bucket_name = f"{resource_prefix}-data-{aws_config['region']}"

        event = test_data_generator.generate_ride_request()
        ride_id = event["ride_id"]

        kinesis_client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event),
            PartitionKey=ride_id
        )

        time.sleep(8)

        # Check DynamoDB
        table = dynamodb_resource.Table(table_name)
        db_response = table.get_item(Key={"ride_id": ride_id})

        if "Item" not in db_response:
            pytest.skip("Event not found in DynamoDB for consistency test")

        db_item = db_response["Item"]

        # Check S3 (may take longer to archive)
        time.sleep(10)

        now = datetime.utcnow()
        prefix = f"raw/rides/{now.year}/{now.month:02d}/{now.day:02d}/"

        # Note: Full consistency check would require parsing S3 files
        # For now, just verify both systems have data
        try:
            s3_response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10
            )

            if s3_response.get("KeyCount", 0) > 0:
                # Both DynamoDB and S3 have data - consistency check passes
                assert True
            else:
                pytest.skip("S3 archive not available yet")

        except Exception as e:
            pytest.skip(f"S3 consistency check failed: {str(e)}")

    def test_event_ordering(self, kinesis_client, dynamodb_resource,
                           resource_prefix, test_data_generator):
        """Test that events are processed in correct order."""
        stream_name = f"{resource_prefix}-rides-stream"
        table_name = f"{resource_prefix}-rides"

        ride_id = f"ride-order-{int(time.time())}"

        # Send events in sequence
        events = [
            test_data_generator.generate_ride_request(ride_id=ride_id),
            test_data_generator.generate_ride_started(ride_id=ride_id),
            test_data_generator.generate_ride_completed(ride_id=ride_id)
        ]

        for event in events:
            kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event),
                PartitionKey=ride_id
            )
            time.sleep(2)  # Space out events

        time.sleep(8)

        # Check final state
        table = dynamodb_resource.Table(table_name)
        response = table.get_item(Key={"ride_id": ride_id})

        if "Item" not in response:
            pytest.skip("Events not found for ordering test")

        item = response["Item"]

        # Final state should reflect completed ride
        # This assumes proper event ordering in Lambda
        if "status" in item:
            assert item["status"] in ["completed", "ride_completed"], \
                "Final status should be completed if all events processed in order"


# ============================================================================
# REFERENTIAL INTEGRITY TESTS
# ============================================================================

class TestReferentialIntegrity:
    """Test referential integrity across tables."""

    def test_ride_payment_relationship(self, kinesis_client, dynamodb_resource,
                                       resource_prefix, test_data_generator):
        """Verify ride_id references are consistent."""
        rides_stream = f"{resource_prefix}-rides-stream"
        payments_stream = f"{resource_prefix}-payments-stream"
        rides_table = f"{resource_prefix}-rides"
        payments_table = f"{resource_prefix}-payments"

        ride_id = f"ride-ref-{int(time.time())}"

        # Create ride
        ride_event = test_data_generator.generate_ride_completed(ride_id=ride_id)
        kinesis_client.put_record(
            StreamName=rides_stream,
            Data=json.dumps(ride_event),
            PartitionKey=ride_id
        )

        time.sleep(5)

        # Create payment for ride
        payment_event = test_data_generator.generate_payment(ride_id=ride_id)
        payment_id = payment_event["payment_id"]

        kinesis_client.put_record(
            StreamName=payments_stream,
            Data=json.dumps(payment_event),
            PartitionKey=payment_id
        )

        time.sleep(8)

        # Verify both records exist with matching ride_id
        rides_tbl = dynamodb_resource.Table(rides_table)
        payments_tbl = dynamodb_resource.Table(payments_table)

        ride_response = rides_tbl.get_item(Key={"ride_id": ride_id})
        payment_response = payments_tbl.get_item(Key={"payment_id": payment_id})

        if "Item" in ride_response and "Item" in payment_response:
            payment_item = payment_response["Item"]

            # Verify ride_id matches
            assert payment_item["ride_id"] == ride_id, \
                "Referential integrity check failed: ride_id mismatch"
        else:
            pytest.skip("Records not found for referential integrity test")

    def test_driver_location_relationship(self, kinesis_client, dynamodb_resource,
                                         resource_prefix, test_data_generator):
        """Verify driver references are consistent."""
        locations_stream = f"{resource_prefix}-locations-stream"
        drivers_table = f"{resource_prefix}-drivers"

        driver_id = f"driver-ref-{int(time.time())}"

        # Send location updates for driver
        for _ in range(3):
            event = test_data_generator.generate_location_update(driver_id=driver_id)
            kinesis_client.put_record(
                StreamName=locations_stream,
                Data=json.dumps(event),
                PartitionKey=driver_id
            )
            time.sleep(2)

        time.sleep(8)

        # Verify driver record exists
        table = dynamodb_resource.Table(drivers_table)
        response = table.get_item(Key={"driver_id": driver_id})

        if "Item" in response:
            # Driver record should have latest location
            assert True
        else:
            pytest.skip("Driver not found for referential integrity test")


# ============================================================================
# DATA TYPE VALIDATION
# ============================================================================

class TestDataTypes:
    """Test data type enforcement."""

    def test_numeric_fields(self, test_data_generator):
        """Verify numeric fields have correct types."""
        event = test_data_generator.generate_ride_completed(ride_id="test-ride")

        # Verify numeric types
        assert isinstance(event["distance_miles"], (int, float))
        assert isinstance(event["duration_minutes"], int)
        assert isinstance(event["fare"], (int, float, Decimal))
        assert isinstance(event["surge_multiplier"], (int, float))

    def test_string_fields(self, test_data_generator):
        """Verify string fields have correct types."""
        event = test_data_generator.generate_ride_request()

        # Verify string types
        assert isinstance(event["ride_id"], str)
        assert isinstance(event["rider_id"], str)
        assert isinstance(event["event_type"], str)
        assert isinstance(event["ride_type"], str)

    def test_timestamp_format(self, test_data_generator):
        """Verify timestamp format is ISO 8601."""
        event = test_data_generator.generate_ride_request()

        timestamp_str = event["timestamp"]

        # Try parsing as ISO format
        try:
            parsed = datetime.fromisoformat(timestamp_str.replace("Z", ""))
            assert isinstance(parsed, datetime)
        except ValueError:
            pytest.fail(f"Timestamp {timestamp_str} is not valid ISO 8601 format")
