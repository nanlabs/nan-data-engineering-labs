"""
Rides Processor Lambda Handler

Processes ride events from Kinesis stream:
- ride_requested: Create ride state, find available drivers, calculate fare
- ride_started: Update ride state, mark driver unavailable
- ride_completed: Update ride state, mark driver available, aggregate metrics

Triggered by: Kinesis rides_stream
Tables: rides_state, driver_availability, aggregated_metrics
"""

import json
import logging
import os
import base64
from datetime import datetime
from typing import Dict, Any, List

import boto3
from boto3.dynamodb.conditions import Key, Attr

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import common utilities (ensure these are in Lambda layer or deployment package)
try:
    from common.dynamodb_utils import (
        put_item, update_item, get_item, query_table, atomic_counter_increment
    )
    from common.s3_utils import write_records_to_s3
except ImportError:
    # Fallback for local testing
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from common.dynamodb_utils import (
        put_item, update_item, get_item, query_table
    )

# Environment variables
RIDES_STATE_TABLE = os.environ.get('RIDES_STATE_TABLE', 'rides_state')
DRIVER_AVAILABILITY_TABLE = os.environ.get('DRIVER_AVAILABILITY_TABLE', 'driver_availability')
AGGREGATED_METRICS_TABLE = os.environ.get('AGGREGATED_METRICS_TABLE', 'aggregated_metrics')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'rideshare-archive')
DLQ_URL = os.environ.get('DLQ_URL', '')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sqs = boto3.client('sqs', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula (miles)."""
    from math import radians, cos, sin, asin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    miles = 3956 * c

    return round(miles, 2)


def find_available_drivers(
    lat: float,
    lon: float,
    city: str,
    max_distance_miles: float = 5.0,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Find available drivers near a location.

    Args:
        lat: Pickup latitude
        lon: Pickup longitude
        city: City name
        max_distance_miles: Maximum distance to search
        limit: Maximum number of drivers to return

    Returns:
        List of available drivers sorted by distance
    """
    try:
        # Query drivers in the same city who are available
        drivers = query_table(
            DRIVER_AVAILABILITY_TABLE,
            key_condition_expression=Key('city').eq(city),
            filter_expression=Attr('available').eq(True),
            index_name='city-available-index',  # Assuming GSI exists
            region_name=REGION
        )

        # Calculate distances and filter
        nearby_drivers = []
        for driver in drivers:
            driver_lat = driver.get('lat', 0)
            driver_lon = driver.get('lon', 0)

            distance = calculate_distance(lat, lon, driver_lat, driver_lon)

            if distance <= max_distance_miles:
                driver['distance_miles'] = distance
                nearby_drivers.append(driver)

        # Sort by distance and rating
        nearby_drivers.sort(
            key=lambda d: (d.get('distance_miles', 999), -d.get('avg_rating', 0))
        )

        return nearby_drivers[:limit]

    except Exception as e:
        logger.error(f"Error finding available drivers: {e}")
        return []


def process_ride_requested(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ride_requested event.

    Creates ride state entry, finds available drivers, calculates estimated fare.
    """
    ride_id = event['ride_id']
    customer_id = event['customer_id']
    city = event['city']
    pickup_lat = event['pickup_lat']
    pickup_lon = event['pickup_lon']
    dropoff_lat = event.get('dropoff_lat')
    dropoff_lon = event.get('dropoff_lon')

    logger.info(f"Processing ride_requested: {ride_id}")

    # Check for duplicate (idempotency)
    existing_ride = get_item(
        RIDES_STATE_TABLE,
        {'ride_id': ride_id},
        region_name=REGION
    )

    if existing_ride:
        logger.warning(f"Ride {ride_id} already exists, skipping")
        return {'status': 'duplicate', 'ride_id': ride_id}

    # Find available drivers
    available_drivers = find_available_drivers(pickup_lat, pickup_lon, city)

    # Create ride state
    ride_state = {
        'ride_id': ride_id,
        'customer_id': customer_id,
        'city': city,
        'status': 'requested',
        'pickup_lat': pickup_lat,
        'pickup_lon': pickup_lon,
        'dropoff_lat': dropoff_lat,
        'dropoff_lon': dropoff_lon,
        'estimated_fare': event.get('estimated_fare'),
        'estimated_distance_miles': event.get('estimated_distance_miles'),
        'estimated_duration_minutes': event.get('estimated_duration_minutes'),
        'available_drivers_count': len(available_drivers),
        'requested_at': event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
        'updated_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Store available driver IDs for matching
    if available_drivers:
        ride_state['available_driver_ids'] = [d['driver_id'] for d in available_drivers[:5]]

    # Put to DynamoDB
    success = put_item(RIDES_STATE_TABLE, ride_state, region_name=REGION)

    if success:
        logger.info(f"Created ride state for {ride_id}, found {len(available_drivers)} drivers")

        # Update metrics
        update_aggregated_metrics('rides_requested', city)

        return {'status': 'created', 'ride_id': ride_id, 'drivers_found': len(available_drivers)}
    else:
        logger.error(f"Failed to create ride state for {ride_id}")
        return {'status': 'failed', 'ride_id': ride_id}


def process_ride_started(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ride_started event.

    Updates ride state with driver assignment, marks driver as unavailable.
    """
    ride_id = event['ride_id']
    driver_id = event['driver_id']

    logger.info(f"Processing ride_started: {ride_id}, driver: {driver_id}")

    # Update ride state
    update_success = update_item(
        RIDES_STATE_TABLE,
        key={'ride_id': ride_id},
        update_expression='SET #status = :status, driver_id = :driver_id, started_at = :started_at, updated_at = :updated_at',
        expression_attribute_names={'#status': 'status'},
        expression_attribute_values={
            ':status': 'started',
            ':driver_id': driver_id,
            ':started_at': event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            ':updated_at': datetime.utcnow().isoformat() + 'Z',
        },
        region_name=REGION
    )

    if update_success:
        # Mark driver as unavailable
        update_item(
            DRIVER_AVAILABILITY_TABLE,
            key={'driver_id': driver_id},
            update_expression='SET available = :available, current_ride_id = :ride_id, updated_at = :updated_at',
            expression_attribute_values={
                ':available': False,
                ':ride_id': ride_id,
                ':updated_at': datetime.utcnow().isoformat() + 'Z',
            },
            region_name=REGION
        )

        logger.info(f"Ride {ride_id} started with driver {driver_id}")

        # Update metrics
        city = event.get('city', 'unknown')
        update_aggregated_metrics('rides_started', city)

        return {'status': 'updated', 'ride_id': ride_id}
    else:
        logger.error(f"Failed to update ride {ride_id}")
        return {'status': 'failed', 'ride_id': ride_id}


def process_ride_completed(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ride_completed event.

    Updates ride state with final details, marks driver as available,
    updates aggregated metrics.
    """
    ride_id = event['ride_id']
    driver_id = event.get('driver_id')
    actual_fare = event.get('actual_fare', 0)
    actual_duration = event.get('actual_duration_minutes', 0)

    logger.info(f"Processing ride_completed: {ride_id}, fare: ${actual_fare}")

    # Update ride state
    update_success = update_item(
        RIDES_STATE_TABLE,
        key={'ride_id': ride_id},
        update_expression='SET #status = :status, actual_fare = :fare, actual_duration_minutes = :duration, completed_at = :completed_at, updated_at = :updated_at',
        expression_attribute_names={'#status': 'status'},
        expression_attribute_values={
            ':status': 'completed',
            ':fare': actual_fare,
            ':duration': actual_duration,
            ':completed_at': event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            ':updated_at': datetime.utcnow().isoformat() + 'Z',
        },
        region_name=REGION
    )

    if update_success and driver_id:
        # Mark driver as available
        update_item(
            DRIVER_AVAILABILITY_TABLE,
            key={'driver_id': driver_id},
            update_expression='SET available = :available, updated_at = :updated_at REMOVE current_ride_id',
            expression_attribute_values={
                ':available': True,
                ':updated_at': datetime.utcnow().isoformat() + 'Z',
            },
            region_name=REGION
        )

        logger.info(f"Ride {ride_id} completed, driver {driver_id} now available")

        # Update aggregated metrics
        city = event.get('city', 'unknown')
        update_aggregated_metrics('rides_completed', city, revenue=actual_fare)

        return {'status': 'completed', 'ride_id': ride_id, 'fare': actual_fare}
    else:
        logger.error(f"Failed to complete ride {ride_id}")
        return {'status': 'failed', 'ride_id': ride_id}


def update_aggregated_metrics(metric_type: str, city: str, revenue: float = 0):
    """Update aggregated metrics in DynamoDB."""
    try:
        # Create metric key (by city and hour)
        now = datetime.utcnow()
        metric_key = f"{city}#{now.strftime('%Y-%m-%d-%H')}"

        # Increment counters
        update_expressions = []
        expression_values = {}

        if metric_type == 'rides_requested':
            update_expressions.append('ADD rides_requested :one')
            expression_values[':one'] = 1
        elif metric_type == 'rides_started':
            update_expressions.append('ADD rides_started :one')
            expression_values[':one'] = 1
        elif metric_type == 'rides_completed':
            update_expressions.append('ADD rides_completed :one, total_revenue :revenue')
            expression_values[':one'] = 1
            expression_values[':revenue'] = revenue

        if update_expressions:
            update_expressions.append('SET city = :city, hour = :hour, updated_at = :updated_at')
            expression_values[':city'] = city
            expression_values[':hour'] = now.strftime('%Y-%m-%d-%H')
            expression_values[':updated_at'] = now.isoformat() + 'Z'

            update_item(
                AGGREGATED_METRICS_TABLE,
                key={'metric_key': metric_key},
                update_expression=' '.join(update_expressions),
                expression_attribute_values=expression_values,
                region_name=REGION
            )

            logger.debug(f"Updated metric: {metric_type} for {city}")

    except Exception as e:
        logger.error(f"Error updating metrics: {e}")


def publish_metrics(metric_name: str, value: float, dimensions: List[Dict] = None):
    """Publish custom metrics to CloudWatch."""
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow()
        }

        if dimensions:
            metric_data['Dimensions'] = dimensions

        cloudwatch.put_metric_data(
            Namespace='RideShare/Rides',
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Error publishing metrics: {e}")


def send_to_dlq(record: Dict[str, Any], error: str):
    """Send failed record to DLQ."""
    if not DLQ_URL:
        logger.warning("DLQ URL not configured, skipping DLQ send")
        return

    try:
        message = {
            'record': record,
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }

        sqs.send_message(
            QueueUrl=DLQ_URL,
            MessageBody=json.dumps(message, default=str)
        )

        logger.info(f"Sent record to DLQ: {record.get('ride_id', 'unknown')}")
    except Exception as e:
        logger.error(f"Error sending to DLQ: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler for Kinesis stream events.

    Processes batches of ride events from Kinesis.
    """
    logger.info(f"Processing {len(event['Records'])} records from Kinesis")

    processed = 0
    failed = 0
    failed_records = []

    for record in event['Records']:
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            ride_event = json.loads(payload)

            event_type = ride_event.get('event_type')

            # Route to appropriate processor
            if event_type == 'ride_requested':
                result = process_ride_requested(ride_event)
            elif event_type == 'ride_started':
                result = process_ride_started(ride_event)
            elif event_type == 'ride_completed':
                result = process_ride_completed(ride_event)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                result = {'status': 'unknown_type'}

            if result.get('status') in ['created', 'updated', 'completed', 'duplicate']:
                processed += 1
            else:
                failed += 1
                failed_records.append(record)

        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            failed += 1
            failed_records.append(record)

            # Send to DLQ
            try:
                ride_event = json.loads(base64.b64decode(record['kinesis']['data']))
                send_to_dlq(ride_event, str(e))
            except:
                pass

    # Publish metrics
    publish_metrics('RecordsProcessed', processed)
    publish_metrics('RecordsFailed', failed)

    logger.info(f"Batch complete: {processed} processed, {failed} failed")

    # Return failed records for retry (optional)
    if failed_records:
        return {
            'batchItemFailures': [
                {'itemIdentifier': record['kinesis']['sequenceNumber']}
                for record in failed_records
            ]
        }

    return {'statusCode': 200, 'body': json.dumps({'processed': processed, 'failed': failed})}
