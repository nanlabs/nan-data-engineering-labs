"""
Locations Processor Lambda Handler

Processes driver location updates from Kinesis stream:
- Update driver_availability table with latest location
- Maintain driver availability status
- Archive location history to S3

Triggered by: Kinesis locations_stream
Tables: driver_availability
S3: location history archives
"""

import json
import logging
import os
import base64
from datetime import datetime
from typing import Dict, Any, List

import boto3

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import common utilities
try:
    from common.dynamodb_utils import put_item, update_item, get_item
    from common.s3_utils import write_records_to_s3
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from common.dynamodb_utils import put_item, update_item, get_item
    from common.s3_utils import write_records_to_s3

# Environment variables
DRIVER_AVAILABILITY_TABLE = os.environ.get('DRIVER_AVAILABILITY_TABLE', 'driver_availability')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'rideshare-archive')
ARCHIVE_THRESHOLD = int(os.environ.get('ARCHIVE_THRESHOLD', '1000'))
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Clients
cloudwatch = boto3.client('cloudwatch', region_name=REGION)

# In-memory buffer for archiving
location_buffer = []


def calculate_geohash(lat: float, lon: float, precision: int = 5) -> str:
    """
    Calculate geohash for location-based indexing.

    Simplified implementation using grid-based hashing.
    Precision 5 = ~5km grid cells.
    """
    # Simple grid-based hash (not a true geohash, but sufficient for demo)
    lat_grid = int((lat + 90) * (10 ** precision) / 180)
    lon_grid = int((lon + 180) * (10 ** precision) / 360)

    return f"{lat_grid:010d}_{lon_grid:010d}"


def process_location_update(location_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process driver location update.

    Updates driver availability table with latest location and status.
    """
    driver_id = location_event['driver_id']
    city = location_event['city']
    lat = location_event['lat']
    lon = location_event['lon']
    available = location_event.get('available', True)
    speed_mph = location_event.get('speed_mph', 0)
    heading = location_event.get('heading', 0)
    current_ride_id = location_event.get('current_ride_id')
    timestamp = location_event.get('timestamp', datetime.utcnow().isoformat() + 'Z')

    logger.debug(f"Processing location for driver {driver_id}: ({lat}, {lon})")

    # Calculate geohash for spatial indexing
    geohash = calculate_geohash(lat, lon)

    # Get existing driver record to preserve other fields
    existing_driver = get_item(
        DRIVER_AVAILABILITY_TABLE,
        {'driver_id': driver_id},
        region_name=REGION
    )

    # Build update expression
    update_expression_parts = [
        'SET city = :city',
        'lat = :lat',
        'lon = :lon',
        'geohash = :geohash',
        'available = :available',
        'speed_mph = :speed',
        'heading = :heading',
        'last_location_update = :timestamp',
        'updated_at = :updated_at',
    ]

    expression_values = {
        ':city': city,
        ':lat': lat,
        ':lon': lon,
        ':geohash': geohash,
        ':available': available,
        ':speed': speed_mph,
        ':heading': heading,
        ':timestamp': timestamp,
        ':updated_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Handle current_ride_id
    if current_ride_id:
        update_expression_parts.append('current_ride_id = :ride_id')
        expression_values[':ride_id'] = current_ride_id
    elif existing_driver and 'current_ride_id' in existing_driver:
        # Remove current_ride_id if driver is now available
        update_expression_parts.append('')
        update_expression = ', '.join(update_expression_parts) + ' REMOVE current_ride_id'
    else:
        update_expression = ', '.join(update_expression_parts)

    if 'REMOVE' not in update_expression:
        update_expression = ', '.join(update_expression_parts)

    # If driver doesn't exist, create record
    if not existing_driver:
        driver_record = {
            'driver_id': driver_id,
            'city': city,
            'lat': lat,
            'lon': lon,
            'geohash': geohash,
            'available': available,
            'speed_mph': speed_mph,
            'heading': heading,
            'last_location_update': timestamp,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'avg_rating': 4.5,  # Default rating
            'total_rides': 0,
        }

        if current_ride_id:
            driver_record['current_ride_id'] = current_ride_id

        success = put_item(DRIVER_AVAILABILITY_TABLE, driver_record, region_name=REGION)

        if success:
            logger.info(f"Created new driver record: {driver_id}")
            return {'status': 'created', 'driver_id': driver_id}
        else:
            logger.error(f"Failed to create driver record: {driver_id}")
            return {'status': 'failed', 'driver_id': driver_id}
    else:
        # Update existing record
        success = update_item(
            DRIVER_AVAILABILITY_TABLE,
            key={'driver_id': driver_id},
            update_expression=update_expression,
            expression_attribute_values=expression_values,
            region_name=REGION
        )

        if success:
            logger.debug(f"Updated driver location: {driver_id}")
            return {'status': 'updated', 'driver_id': driver_id}
        else:
            logger.error(f"Failed to update driver location: {driver_id}")
            return {'status': 'failed', 'driver_id': driver_id}


def archive_locations_to_s3():
    """Archive buffered location updates to S3."""
    global location_buffer

    if not location_buffer:
        return

    try:
        logger.info(f"Archiving {len(location_buffer)} location updates to S3")

        s3_key = write_records_to_s3(
            bucket_name=ARCHIVE_BUCKET,
            prefix='locations/',
            records=location_buffer,
            partition_by_date=True,
            partition_by_hour=True,
            compress=True,
            region_name=REGION
        )

        if s3_key:
            logger.info(f"Archived locations to {s3_key}")
            location_buffer = []  # Clear buffer
            return True

    except Exception as e:
        logger.error(f"Error archiving locations to S3: {e}")
        return False


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
            Namespace='RideShare/Locations',
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Error publishing metrics: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler for Kinesis stream events.

    Processes batches of driver location updates from Kinesis.
    """
    global location_buffer

    logger.info(f"Processing {len(event['Records'])} location records from Kinesis")

    processed = 0
    failed = 0
    failed_records = []

    # Track statistics
    by_city = {}
    available_count = 0
    busy_count = 0

    for record in event['Records']:
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            location_event = json.loads(payload)

            # Process location update
            result = process_location_update(location_event)

            if result.get('status') in ['created', 'updated']:
                processed += 1

                # Add to archive buffer
                location_buffer.append(location_event)

                # Track statistics
                city = location_event.get('city', 'unknown')
                by_city[city] = by_city.get(city, 0) + 1

                if location_event.get('available', True):
                    available_count += 1
                else:
                    busy_count += 1
            else:
                failed += 1
                failed_records.append(record)

        except Exception as e:
            logger.error(f"Error processing location record: {e}", exc_info=True)
            failed += 1
            failed_records.append(record)

    # Archive to S3 if buffer threshold reached
    if len(location_buffer) >= ARCHIVE_THRESHOLD:
        archive_locations_to_s3()

    # Publish metrics
    publish_metrics('LocationUpdatesProcessed', processed)
    publish_metrics('LocationUpdatesFailed', failed)
    publish_metrics('DriversAvailable', available_count)
    publish_metrics('DriversBusy', busy_count)

    # Publish per-city metrics
    for city, count in by_city.items():
        publish_metrics(
            'LocationUpdatesByCity',
            count,
            dimensions=[{'Name': 'City', 'Value': city}]
        )

    logger.info(f"Batch complete: {processed} processed, {failed} failed. "
               f"Buffer size: {len(location_buffer)}")
    logger.info(f"Cities: {by_city}, Available: {available_count}, Busy: {busy_count}")

    # Return failed records for retry (optional)
    if failed_records:
        return {
            'batchItemFailures': [
                {'itemIdentifier': record['kinesis']['sequenceNumber']}
                for record in failed_records
            ]
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'buffer_size': len(location_buffer)
        })
    }
