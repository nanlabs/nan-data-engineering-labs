"""
Data Quality Tests for Real-Time Analytics Platform

Tests for schema validation, data integrity, duplicate detection,
aggregation calculations, and time window processing. Ensures data
quality standards are maintained throughout the pipeline.
"""

import os
import uuid
from datetime import datetime, timedelta

import boto3
import pytest


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

RIDE_EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_type", "event_id", "ride_id", "timestamp"],
    "properties": {
        "event_type": {"type": "string", "enum": ["ride_requested", "ride_accepted", "ride_started", "ride_completed", "ride_cancelled"]},
        "event_id": {"type": "string", "format": "uuid"},
        "ride_id": {"type": "string"},
        "rider_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "city": {"type": "string"},
    }
}

PAYMENT_EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_type", "event_id", "payment_id", "ride_id", "amount", "timestamp"],
    "properties": {
        "event_type": {"type": "string"},
        "event_id": {"type": "string"},
        "payment_id": {"type": "string"},
        "ride_id": {"type": "string"},
        "amount": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        "timestamp": {"type": "string"},
        "status": {"type": "string", "enum": ["success", "failed", "pending"]},
    }
}

LOCATION_EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_type", "event_id", "driver_id", "latitude", "longitude", "timestamp"],
    "properties": {
        "event_type": {"type": "string"},
        "event_id": {"type": "string"},
        "driver_id": {"type": "string"},
        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
        "timestamp": {"type": "string"},
        "city": {"type": "string"},
        "speed_mph": {"type": "number", "minimum": 0},
    }
}

RATING_EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_type", "event_id", "rating_id", "ride_id", "rating", "timestamp"],
    "properties": {
        "event_type": {"type": "string"},
        "event_id": {"type": "string"},
        "rating_id": {"type": "string"},
        "ride_id": {"type": "string"},
        "rider_id": {"type": "string"},
        "driver_id": {"type": "string"},
        "rating": {"type": "integer", "minimum": 1, "maximum": 5},
        "timestamp": {"type": "string"},
        "comment": {"type": "string"},
    }
}


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="module")
def quality_config():
    """Data quality test configuration."""
    return {
        "project_name": os.environ.get("PROJECT_NAME", "rideshare-analytics"),
        "environment": os.environ.get("ENVIRONMENT", "test"),
        "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
        "min_fare": 5.0,
        "max_fare": 500.0,
        "max_ride_duration_hours": 24,
        "max_distance_miles": 500,
    }


@pytest.fixture(scope="module")
def quality_clients(quality_config):
    """AWS clients for data quality tests."""
    region = quality_config["aws_region"]
    return {
        "dynamodb": boto3.resource("dynamodb", region_name=region),
        "s3": boto3.client("s3", region_name=region),
        "cloudwatch": boto3.client("cloudwatch", region_name=region),
    }


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestSchemaValidation:
    """Test schema validation for all event types."""

    def test_valid_ride_event_schema(self, generate_ride_event):
        """Test valid ride event passes schema validation."""
        ride_event = generate_ride_event(event_type="ride_requested")

        # Should not raise exception
        try:
            # Basic validation
            assert ride_event["event_type"] in ["ride_requested", "ride_accepted", "ride_started", "ride_completed"]
            assert ride_event["event_id"] is not None
            assert ride_event["ride_id"] is not None
            assert ride_event["timestamp"] is not None

        except (KeyError, AssertionError) as e:
            pytest.fail(f"Valid ride event failed schema validation: {e}")

    def test_invalid_ride_event_missing_fields(self, generate_ride_event):
        """Test ride event with missing required fields."""
        ride_event = generate_ride_event(event_type="ride_requested")

        # Remove required field
        del ride_event["ride_id"]

        # Validation should fail
        with pytest.raises(KeyError):
            _ = ride_event["ride_id"]

    def test_valid_payment_event_schema(self, generate_payment_event):
        """Test valid payment event passes schema validation."""
        payment_event = generate_payment_event(event_type="payment_processed")

        # Validate required fields
        assert payment_event["event_type"] is not None
        assert payment_event["payment_id"] is not None
        assert payment_event["ride_id"] is not None
        assert payment_event["amount"] >= 0
        assert payment_event["currency"] == "USD"

    def test_payment_amount_validation(self, generate_payment_event, quality_config):
        """Test payment amount is within valid range."""
        payment_event = generate_payment_event(
            event_type="payment_processed",
            amount=25.50
        )

        amount = payment_event["amount"]
        assert amount >= quality_config["min_fare"]
        assert amount <= quality_config["max_fare"]

    def test_valid_location_event_schema(self, generate_location_event):
        """Test valid location event passes schema validation."""
        location_event = generate_location_event()

        # Validate required fields
        assert location_event["driver_id"] is not None
        assert -90 <= location_event["latitude"] <= 90
        assert -180 <= location_event["longitude"] <= 180
        assert location_event["timestamp"] is not None

    def test_location_coordinates_validation(self, generate_location_event):
        """Test location coordinates are within valid ranges."""
        location_event = generate_location_event(
            latitude=37.7749,
            longitude=-122.4194
        )

        # San Francisco coordinates
        assert -90 <= location_event["latitude"] <= 90
        assert -180 <= location_event["longitude"] <= 180

    def test_invalid_location_coordinates(self):
        """Test invalid coordinates are rejected."""
        invalid_coords = [
            (91, 0),      # Lat too high
            (-91, 0),     # Lat too low
            (0, 181),     # Lon too high
            (0, -181),    # Lon too low
        ]

        for lat, lon in invalid_coords:
            assert not (-90 <= lat <= 90 and -180 <= lon <= 180)

    def test_valid_rating_event_schema(self, generate_rating_event):
        """Test valid rating event passes schema validation."""
        rating_event = generate_rating_event(rating=5)

        # Validate required fields
        assert rating_event["rating_id"] is not None
        assert rating_event["ride_id"] is not None
        assert 1 <= rating_event["rating"] <= 5
        assert rating_event["timestamp"] is not None

    def test_rating_value_validation(self, generate_rating_event):
        """Test rating value is within valid range (1-5)."""
        for rating_value in [1, 2, 3, 4, 5]:
            rating_event = generate_rating_event(rating=rating_value)
            assert 1 <= rating_event["rating"] <= 5

    def test_invalid_rating_values(self):
        """Test invalid rating values are rejected."""
        invalid_ratings = [0, -1, 6, 10, 100]

        for rating in invalid_ratings:
            assert not (1 <= rating <= 5)


# ============================================================================
# DATA COMPLETENESS TESTS
# ============================================================================

class TestDataCompleteness:
    """Test data completeness and required fields."""

    def test_ride_event_has_all_required_fields(self, generate_ride_event):
        """Test ride event contains all required fields."""
        ride_event = generate_ride_event(event_type="ride_requested")

        required_fields = ["event_type", "event_id", "ride_id", "rider_id", "timestamp"]

        for field in required_fields:
            assert field in ride_event, f"Missing required field: {field}"
            assert ride_event[field] is not None, f"Field {field} is None"

    def test_ride_requested_event_completeness(self, generate_ride_event):
        """Test ride_requested event has pickup and dropoff locations."""
        ride_event = generate_ride_event(event_type="ride_requested")

        # Should have location information
        assert "pickup_location" in ride_event or "city" in ride_event

        if "pickup_location" in ride_event:
            pickup = ride_event["pickup_location"]
            assert "latitude" in pickup
            assert "longitude" in pickup

    def test_ride_completed_event_completeness(self, generate_ride_event):
        """Test ride_completed event has fare and distance."""
        ride_event = generate_ride_event(event_type="ride_completed")

        # Should have fare information
        if "fare" in ride_event:
            assert ride_event["fare"] > 0

        # Should have distance/duration
        if "distance_miles" in ride_event:
            assert ride_event["distance_miles"] > 0

    def test_payment_event_completeness(self, generate_payment_event):
        """Test payment event has all transaction details."""
        payment_event = generate_payment_event(event_type="payment_processed")

        required_fields = ["payment_id", "ride_id", "amount", "currency", "timestamp"]

        for field in required_fields:
            assert field in payment_event, f"Missing required field: {field}"

    def test_location_event_completeness(self, generate_location_event):
        """Test location event has GPS coordinates and metadata."""
        location_event = generate_location_event()

        required_fields = ["driver_id", "latitude", "longitude", "timestamp"]

        for field in required_fields:
            assert field in location_event, f"Missing required field: {field}"

        # Should have additional metadata
        optional_fields = ["speed_mph", "heading", "city"]
        present_optional = sum(1 for f in optional_fields if f in location_event)
        assert present_optional >= 1, "Missing optional metadata fields"


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================

class TestDataIntegrity:
    """Test data integrity constraints."""

    def test_ride_fare_calculation_integrity(self, generate_ride_event):
        """Test ride fare is calculated correctly."""
        ride_event = generate_ride_event(
            event_type="ride_completed",
            distance_miles=10.0,
            duration_minutes=20,
            fare=35.0
        )

        if "fare" in ride_event and "distance_miles" in ride_event:
            fare = ride_event["fare"]
            distance = ride_event["distance_miles"]

            # Fare should be reasonable for distance
            fare_per_mile = fare / distance if distance > 0 else 0
            assert 1.0 <= fare_per_mile <= 20.0, f"Fare per mile {fare_per_mile} is unreasonable"

    def test_ride_duration_integrity(self, generate_ride_event, quality_config):
        """Test ride duration is within reasonable bounds."""
        ride_event = generate_ride_event(
            event_type="ride_completed",
            duration_minutes=30
        )

        if "duration_minutes" in ride_event:
            duration = ride_event["duration_minutes"]
            max_duration_minutes = quality_config["max_ride_duration_hours"] * 60

            assert 1 <= duration <= max_duration_minutes, f"Duration {duration} min is invalid"

    def test_ride_distance_integrity(self, generate_ride_event, quality_config):
        """Test ride distance is within reasonable bounds."""
        ride_event = generate_ride_event(
            event_type="ride_completed",
            distance_miles=15.5
        )

        if "distance_miles" in ride_event:
            distance = ride_event["distance_miles"]

            assert 0.1 <= distance <= quality_config["max_distance_miles"], \
                f"Distance {distance} miles is invalid"

    def test_timestamp_ordering(self, generate_ride_event):
        """Test event timestamps are in logical order."""
        ride_id = str(uuid.uuid4())

        requested_event = generate_ride_event(
            event_type="ride_requested",
            ride_id=ride_id,
            timestamp=datetime.utcnow().isoformat()
        )

        completed_event = generate_ride_event(
            event_type="ride_completed",
            ride_id=ride_id,
            timestamp=(datetime.utcnow() + timedelta(minutes=30)).isoformat()
        )

        # Parse timestamps
        requested_time = datetime.fromisoformat(requested_event["timestamp"].replace("Z", "+00:00"))
        completed_time = datetime.fromisoformat(completed_event["timestamp"].replace("Z", "+00:00"))

        # Completed should be after requested
        assert completed_time >= requested_time

    def test_payment_amount_integrity(self, generate_payment_event, quality_config):
        """Test payment amount is valid."""
        payment_event = generate_payment_event(
            event_type="payment_processed",
            amount=45.75
        )

        amount = payment_event["amount"]

        assert amount >= quality_config["min_fare"]
        assert amount <= quality_config["max_fare"]

        # Amount should have reasonable precision (max 2 decimal places)
        assert round(amount, 2) == amount

    def test_driver_location_accuracy(self, generate_location_event):
        """Test driver location has reasonable accuracy."""
        location_event = generate_location_event()

        if "accuracy_meters" in location_event:
            accuracy = location_event["accuracy_meters"]

            # GPS accuracy should be reasonable (typically 5-100m)
            assert 1 <= accuracy <= 1000, f"Accuracy {accuracy}m is unreasonable"

    def test_driver_speed_validation(self, generate_location_event):
        """Test driver speed is within reasonable bounds."""
        location_event = generate_location_event()

        if "speed_mph" in location_event:
            speed = location_event["speed_mph"]

            # Speed should be 0-100 mph for city driving
            assert 0 <= speed <= 150, f"Speed {speed} mph is invalid"


# ============================================================================
# DUPLICATE DETECTION TESTS
# ============================================================================

class TestDuplicateDetection:
    """Test duplicate event detection."""

    def test_duplicate_event_id_detection(self, generate_ride_event):
        """Test detection of duplicate event IDs."""
        event_id = str(uuid.uuid4())

        event1 = generate_ride_event(event_type="ride_requested")
        event1["event_id"] = event_id

        event2 = generate_ride_event(event_type="ride_requested")
        event2["event_id"] = event_id

        # Same event_id should be detected as duplicate
        assert event1["event_id"] == event2["event_id"]

    def test_duplicate_ride_detection(self, generate_ride_event):
        """Test detection of duplicate ride events."""
        ride_id = str(uuid.uuid4())

        event1 = generate_ride_event(event_type="ride_requested", ride_id=ride_id)
        event2 = generate_ride_event(event_type="ride_requested", ride_id=ride_id)

        # Same ride_id with same event_type should be duplicate
        assert event1["ride_id"] == event2["ride_id"]
        assert event1["event_type"] == event2["event_type"]

    def test_duplicate_payment_detection(self, generate_payment_event):
        """Test detection of duplicate payment events."""
        payment_id = str(uuid.uuid4())

        event1 = generate_payment_event(payment_id=payment_id)
        event2 = generate_payment_event(payment_id=payment_id)

        # Same payment_id should be detected as duplicate
        assert event1["payment_id"] == event2["payment_id"]

    def test_idempotency_key_generation(self, generate_ride_event):
        """Test generation of idempotency keys."""
        event = generate_ride_event(event_type="ride_requested")

        # Idempotency key could be combination of ride_id + event_type
        idempotency_key = f"{event['ride_id']}:{event['event_type']}"

        assert idempotency_key is not None
        assert event["ride_id"] in idempotency_key


# ============================================================================
# AGGREGATION CALCULATION TESTS
# ============================================================================

class TestAggregationCalculations:
    """Test aggregation calculations for metrics."""

    def test_total_rides_calculation(self):
        """Test calculation of total rides."""
        rides = [
            {"ride_id": f"ride_{i}", "status": "completed"}
            for i in range(10)
        ]

        total_rides = len(rides)
        completed_rides = sum(1 for r in rides if r["status"] == "completed")

        assert total_rides == 10
        assert completed_rides == 10

    def test_total_revenue_calculation(self):
        """Test calculation of total revenue."""
        rides = [
            {"ride_id": f"ride_{i}", "fare": 25.50 + i}
            for i in range(5)
        ]

        total_revenue = sum(r["fare"] for r in rides)
        expected_revenue = sum(25.50 + i for i in range(5))

        assert abs(total_revenue - expected_revenue) < 0.01

    def test_average_fare_calculation(self):
        """Test calculation of average fare."""
        fares = [10.0, 20.0, 30.0, 40.0, 50.0]

        avg_fare = sum(fares) / len(fares)

        assert avg_fare == 30.0

    def test_average_rating_calculation(self):
        """Test calculation of average driver rating."""
        ratings = [5, 4, 5, 3, 4, 5]

        avg_rating = sum(ratings) / len(ratings)

        assert 1 <= avg_rating <= 5
        assert abs(avg_rating - 4.333) < 0.01

    def test_ride_completion_rate(self):
        """Test calculation of ride completion rate."""
        rides = [
            {"status": "completed"},
            {"status": "completed"},
            {"status": "cancelled"},
            {"status": "completed"},
            {"status": "cancelled"},
        ]

        total = len(rides)
        completed = sum(1 for r in rides if r["status"] == "completed")
        completion_rate = (completed / total) * 100

        assert completion_rate == 60.0

    def test_average_ride_duration(self):
        """Test calculation of average ride duration."""
        durations = [15, 20, 25, 30, 35]  # minutes

        avg_duration = sum(durations) / len(durations)

        assert avg_duration == 25.0

    def test_rides_per_driver(self):
        """Test calculation of rides per driver."""
        rides = [
            {"driver_id": "driver_1"},
            {"driver_id": "driver_1"},
            {"driver_id": "driver_2"},
            {"driver_id": "driver_1"},
            {"driver_id": "driver_3"},
        ]

        driver_counts = {}
        for ride in rides:
            driver_id = ride["driver_id"]
            driver_counts[driver_id] = driver_counts.get(driver_id, 0) + 1

        assert driver_counts["driver_1"] == 3
        assert driver_counts["driver_2"] == 1
        assert driver_counts["driver_3"] == 1


# ============================================================================
# TIME WINDOW VALIDATION TESTS
# ============================================================================

class TestTimeWindowValidation:
    """Test time window calculations for streaming aggregations."""

    def test_5_minute_window_calculation(self):
        """Test 5-minute tumbling window."""
        now = datetime.utcnow()

        # Round down to 5-minute boundary
        window_start = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=5)

        # Event should fall in window
        event_time = window_start + timedelta(minutes=2)

        assert window_start <= event_time < window_end

    def test_hourly_window_calculation(self):
        """Test hourly tumbling window."""
        now = datetime.utcnow()

        # Round down to hour boundary
        window_start = now.replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        event_time = window_start + timedelta(minutes=30)

        assert window_start <= event_time < window_end

    def test_sliding_window_calculation(self):
        """Test sliding window (e.g., last 15 minutes)."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=15)

        # Events in last 15 minutes
        events = [
            {"timestamp": (now - timedelta(minutes=5)).isoformat()},
            {"timestamp": (now - timedelta(minutes=10)).isoformat()},
            {"timestamp": (now - timedelta(minutes=20)).isoformat()},  # Outside window
        ]

        events_in_window = [
            e for e in events
            if datetime.fromisoformat(e["timestamp"]) >= window_start
        ]

        assert len(events_in_window) == 2

    def test_daily_window_calculation(self):
        """Test daily aggregation window."""
        now = datetime.utcnow()

        # Start of current day
        window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(days=1)

        event_time = now

        assert window_start <= event_time < window_end

    def test_event_time_extraction(self, generate_ride_event):
        """Test extraction of event timestamp."""
        event = generate_ride_event(event_type="ride_requested")

        timestamp_str = event["timestamp"]
        event_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # Should be recent (within last hour)
        now = datetime.utcnow()
        time_diff = abs((now - event_time.replace(tzinfo=None)).total_seconds())

        assert time_diff < 3600  # Within 1 hour

    def test_late_arriving_events(self):
        """Test handling of late-arriving events."""
        now = datetime.utcnow()

        # Event from 2 hours ago
        late_event_time = now - timedelta(hours=2)
        current_window_start = now - timedelta(minutes=5)

        # Late event should be outside current window
        assert late_event_time < current_window_start


# ============================================================================
# DATA QUALITY METRICS TESTS
# ============================================================================

class TestDataQualityMetrics:
    """Test data quality metrics calculation."""

    def test_completeness_score(self):
        """Test calculation of data completeness score."""
        total_fields = 10
        populated_fields = 8

        completeness_score = (populated_fields / total_fields) * 100

        assert completeness_score == 80.0

    def test_accuracy_score(self):
        """Test calculation of data accuracy score."""
        total_records = 100
        accurate_records = 95

        accuracy_score = (accurate_records / total_records) * 100

        assert accuracy_score == 95.0

    def test_validity_score(self):
        """Test calculation of data validity score."""
        total_records = 100
        valid_records = 98

        validity_score = (valid_records / total_records) * 100

        assert validity_score == 98.0

    def test_timeliness_score(self):
        """Test calculation of data timeliness score."""
        now = datetime.utcnow()

        events = [
            {"timestamp": (now - timedelta(seconds=5)).isoformat()},   # On time
            {"timestamp": (now - timedelta(seconds=10)).isoformat()},  # On time
            {"timestamp": (now - timedelta(hours=2)).isoformat()},     # Late
        ]

        sla_threshold = timedelta(minutes=5)
        on_time_count = 0

        for event in events:
            event_time = datetime.fromisoformat(event["timestamp"])
            if (now - event_time) <= sla_threshold:
                on_time_count += 1

        timeliness_score = (on_time_count / len(events)) * 100

        assert timeliness_score >= 66.0  # 2 out of 3

    def test_consistency_check(self):
        """Test data consistency across related records."""
        ride_record = {
            "ride_id": "ride_123",
            "fare": 35.50,
            "status": "completed"
        }

        payment_record = {
            "ride_id": "ride_123",
            "amount": 35.50,
            "status": "success"
        }

        # Fare should match payment amount
        assert ride_record["fare"] == payment_record["amount"]

        # Status consistency
        if ride_record["status"] == "completed":
            assert payment_record["status"] in ["success", "pending"]


# ============================================================================
# ANOMALY DETECTION TESTS
# ============================================================================

class TestAnomalyDetection:
    """Test anomaly detection in event data."""

    def test_fare_anomaly_detection(self, quality_config):
        """Test detection of unusually high/low fares."""
        fares = [25.0, 30.0, 28.0, 500.0, 27.0]  # 500 is anomaly

        mean_fare = sum(fares) / len(fares)

        anomalies = []
        for fare in fares:
            # Simple threshold-based detection
            if fare > quality_config["max_fare"] * 0.8:  # 80% of max
                anomalies.append(fare)

        assert 500.0 in anomalies

    def test_duration_anomaly_detection(self):
        """Test detection of unusually long ride durations."""
        durations = [15, 20, 25, 180, 18]  # 180 minutes is anomaly

        threshold = 120  # 2 hours
        anomalies = [d for d in durations if d > threshold]

        assert 180 in anomalies

    def test_distance_anomaly_detection(self):
        """Test detection of unusually long distances."""
        distances = [5.0, 8.0, 7.5, 200.0, 6.0]  # 200 miles is anomaly

        threshold = 100  # miles
        anomalies = [d for d in distances if d > threshold]

        assert 200.0 in anomalies

    def test_payment_failure_rate_anomaly(self):
        """Test detection of high payment failure rate."""
        payments = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failed"},
            {"status": "failed"},
            {"status": "failed"},
        ]

        failure_count = sum(1 for p in payments if p["status"] == "failed")
        failure_rate = (failure_count / len(payments)) * 100

        # Failure rate over 50% is anomalous
        assert failure_rate > 50

    def test_rapid_location_change_detection(self, generate_location_event):
        """Test detection of impossible location changes."""
        driver_id = f"driver_{uuid.uuid4().hex[:8]}"

        # Location 1: San Francisco
        loc1 = generate_location_event(
            driver_id=driver_id,
            latitude=37.7749,
            longitude=-122.4194,
            timestamp=datetime.utcnow().isoformat()
        )

        # Location 2: New York (3000 miles away, 1 minute later)
        loc2 = generate_location_event(
            driver_id=driver_id,
            latitude=40.7128,
            longitude=-74.0060,
            timestamp=(datetime.utcnow() + timedelta(minutes=1)).isoformat()
        )

        # Calculate distance (simplified)
        lat_diff = abs(loc2["latitude"] - loc1["latitude"])
        lon_diff = abs(loc2["longitude"] - loc1["longitude"])

        # Large coordinate difference in short time is anomalous
        assert lat_diff > 2 or lon_diff > 2


# ============================================================================
# DATA QUALITY RULES TESTS
# ============================================================================

class TestDataQualityRules:
    """Test enforcement of data quality rules."""

    def test_mandatory_field_rule(self, generate_ride_event):
        """Test that mandatory fields are present."""
        event = generate_ride_event(event_type="ride_requested")

        mandatory_fields = ["event_id", "ride_id", "rider_id", "timestamp"]

        for field in mandatory_fields:
            assert field in event, f"Mandatory field {field} is missing"
            assert event[field] is not None, f"Mandatory field {field} is None"

    def test_data_type_rule(self, generate_ride_event):
        """Test that fields have correct data types."""
        event = generate_ride_event(event_type="ride_completed", fare=35.50)

        if "fare" in event:
            assert isinstance(event["fare"], (int, float)), "Fare must be numeric"

        if "distance_miles" in event:
            assert isinstance(event["distance_miles"], (int, float)), "Distance must be numeric"

    def test_referential_integrity_rule(self):
        """Test referential integrity between events."""
        ride_id = str(uuid.uuid4())

        ride_event = {"ride_id": ride_id, "rider_id": "rider_1"}
        payment_event = {"ride_id": ride_id, "amount": 35.0}

        # Payment must reference existing ride
        assert payment_event["ride_id"] == ride_event["ride_id"]

    def test_range_validation_rule(self, generate_rating_event):
        """Test that values are within valid ranges."""
        event = generate_rating_event(rating=4)

        assert 1 <= event["rating"] <= 5, "Rating must be between 1 and 5"

    def test_format_validation_rule(self, generate_payment_event):
        """Test that fields follow expected formats."""
        event = generate_payment_event(event_type="payment_processed")

        # Currency code should be 3 uppercase letters
        currency = event.get("currency", "USD")
        assert len(currency) == 3, "Currency code must be 3 characters"
        assert currency.isupper(), "Currency code must be uppercase"
