"""
Ratings Processor Lambda Handler

Processes rating events from Kinesis stream:
- Update driver average rating (running average)
- Track customer satisfaction trends
- Detect low ratings and send alerts
- Aggregate rating metrics

Triggered by: Kinesis ratings_stream
Tables: driver_availability, aggregated_metrics, ratings
SNS: Low rating alerts
"""

import json
import logging
import os
import base64
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

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

# Environment variables
DRIVER_AVAILABILITY_TABLE = os.environ.get('DRIVER_AVAILABILITY_TABLE', 'driver_availability')
AGGREGATED_METRICS_TABLE = os.environ.get('AGGREGATED_METRICS_TABLE', 'aggregated_metrics')
RATINGS_TABLE = os.environ.get('RATINGS_TABLE', 'ratings')
LOW_RATING_ALERTS_TOPIC = os.environ.get('LOW_RATING_ALERTS_TOPIC', '')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'rideshare-archive')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Rating thresholds
LOW_RATING_THRESHOLD = 3
CONCERNING_PATTERN_COUNT = 3  # 3 low ratings in short time

# Clients
sns = boto3.client('sns', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)


def update_driver_rating(driver_id: str, new_rating: int) -> Dict[str, Any]:
    """
    Update driver's average rating with new rating.

    Uses running average calculation.
    """
    try:
        # Get current driver record
        driver = get_item(
            DRIVER_AVAILABILITY_TABLE,
            {'driver_id': driver_id},
            region_name=REGION
        )

        if driver:
            # Calculate new average
            current_avg = driver.get('avg_rating', 4.5)
            total_ratings = driver.get('total_ratings', 0)

            # Running average: new_avg = (old_avg * old_count + new_rating) / (old_count + 1)
            new_avg = ((current_avg * total_ratings) + new_rating) / (total_ratings + 1)
            new_avg = round(new_avg, 2)
            new_total = total_ratings + 1

            # Update driver record
            update_item(
                DRIVER_AVAILABILITY_TABLE,
                key={'driver_id': driver_id},
                update_expression='SET avg_rating = :avg, total_ratings = :total, last_rating = :rating, updated_at = :updated_at',
                expression_attribute_values={
                    ':avg': new_avg,
                    ':total': new_total,
                    ':rating': new_rating,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z',
                },
                region_name=REGION
            )

            logger.info(f"Updated driver {driver_id} rating: {current_avg} -> {new_avg} "
                       f"(total: {new_total})")

            return {
                'success': True,
                'previous_avg': current_avg,
                'new_avg': new_avg,
                'total_ratings': new_total
            }
        else:
            # Driver doesn't exist, create record
            driver_record = {
                'driver_id': driver_id,
                'avg_rating': new_rating,
                'total_ratings': 1,
                'last_rating': new_rating,
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'available': True,
            }

            put_item(DRIVER_AVAILABILITY_TABLE, driver_record, region_name=REGION)

            logger.info(f"Created new driver record {driver_id} with rating {new_rating}")

            return {
                'success': True,
                'new_driver': True,
                'new_avg': new_rating,
                'total_ratings': 1
            }

    except Exception as e:
        logger.error(f"Error updating driver rating: {e}")
        return {'success': False, 'error': str(e)}


def detect_low_rating_pattern(driver_id: str, rating: int) -> Dict[str, Any]:
    """
    Detect if driver has concerning pattern of low ratings.

    Checks recent ratings history.
    """
    if rating >= LOW_RATING_THRESHOLD:
        return {'concerning': False}

    try:
        # Get driver's current average and total ratings
        driver = get_item(
            DRIVER_AVAILABILITY_TABLE,
            {'driver_id': driver_id},
            region_name=REGION
        )

        if not driver:
            return {'concerning': False}

        avg_rating = driver.get('avg_rating', 4.5)
        total_ratings = driver.get('total_ratings', 0)

        # Check if average is dropping below threshold
        if avg_rating < LOW_RATING_THRESHOLD and total_ratings >= 5:
            return {
                'concerning': True,
                'reason': f'Driver average rating {avg_rating} below threshold',
                'avg_rating': avg_rating,
                'total_ratings': total_ratings
            }

        # Additional check: if rating is 1 or 2, always concerning
        if rating <= 2:
            return {
                'concerning': True,
                'reason': f'Very low rating received: {rating} stars',
                'avg_rating': avg_rating
            }

        return {'concerning': False}

    except Exception as e:
        logger.error(f"Error detecting rating pattern: {e}")
        return {'concerning': False}


def send_low_rating_alert(rating_event: Dict[str, Any], pattern_analysis: Dict[str, Any]):
    """Send alert for concerning low rating."""
    if not LOW_RATING_ALERTS_TOPIC:
        logger.warning("Low rating alerts topic not configured")
        return

    try:
        alert_message = {
            'alert_type': 'low_rating_detected',
            'rating_id': rating_event['rating_id'],
            'ride_id': rating_event['ride_id'],
            'driver_id': rating_event['driver_id'],
            'customer_id': rating_event['customer_id'],
            'rating': rating_event['rating'],
            'comment': rating_event.get('comment', ''),
            'driver_avg_rating': pattern_analysis.get('avg_rating'),
            'reason': pattern_analysis.get('reason', 'Low rating'),
            'timestamp': rating_event['timestamp'],
        }

        sns.publish(
            TopicArn=LOW_RATING_ALERTS_TOPIC,
            Subject=f'Low Rating Alert: Driver {rating_event["driver_id"]}',
            Message=json.dumps(alert_message, indent=2, default=str)
        )

        logger.warning(f"Low rating alert sent for driver {rating_event['driver_id']}: "
                      f"{rating_event['rating']} stars - {pattern_analysis.get('reason')}")

    except Exception as e:
        logger.error(f"Error sending low rating alert: {e}")


def process_rating_event(rating_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process rating event.

    Updates driver rating, detects patterns, sends alerts, aggregates metrics.
    """
    rating_id = rating_event['rating_id']
    ride_id = rating_event['ride_id']
    driver_id = rating_event['driver_id']
    customer_id = rating_event['customer_id']
    rating = rating_event.get('rating', 5)
    comment = rating_event.get('comment', '')

    logger.info(f"Processing rating {rating_id}: {rating} stars for driver {driver_id}")

    # Store rating record
    rating_record = {
        'rating_id': rating_id,
        'ride_id': ride_id,
        'driver_id': driver_id,
        'customer_id': customer_id,
        'rating': rating,
        'timestamp': rating_event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Add optional fields
    if comment:
        rating_record['comment'] = comment
        rating_record['comment_length'] = len(comment)

    for field in ['category_ratings', 'avg_category_rating', 'is_positive',
                  'needs_review', 'tip_given', 'tip_amount', 'time_since_ride_seconds']:
        if field in rating_event:
            rating_record[field] = rating_event[field]

    success = put_item(RATINGS_TABLE, rating_record, region_name=REGION)

    if not success:
        logger.error(f"Failed to store rating record: {rating_id}")
        return {'status': 'failed', 'rating_id': rating_id}

    # Update driver's average rating
    rating_update = update_driver_rating(driver_id, rating)

    if not rating_update.get('success'):
        logger.error(f"Failed to update driver rating: {driver_id}")
        return {'status': 'failed', 'rating_id': rating_id}

    # Detect concerning patterns
    pattern_analysis = detect_low_rating_pattern(driver_id, rating)

    if pattern_analysis.get('concerning'):
        send_low_rating_alert(rating_event, pattern_analysis)

    # Update aggregated metrics
    update_rating_metrics(rating, rating_event.get('tip_given', False))

    logger.info(f"Rating {rating_id} processed: driver avg now {rating_update.get('new_avg')}, "
               f"concerning: {pattern_analysis.get('concerning', False)}")

    return {
        'status': 'processed',
        'rating_id': rating_id,
        'rating_update': rating_update,
        'pattern_analysis': pattern_analysis
    }


def update_rating_metrics(rating: int, tip_given: bool):
    """Update rating metrics in aggregated_metrics table."""
    try:
        now = datetime.utcnow()
        metric_key = f"ratings#{now.strftime('%Y-%m-%d-%H')}"

        # Prepare update expression
        update_parts = [
            'ADD total_ratings :one',
            f'rating_{rating}_star :one',
            'rating_sum :rating'
        ]

        expression_values = {
            ':one': 1,
            ':rating': rating,
            ':hour': now.strftime('%Y-%m-%d-%H'),
            ':updated_at': now.isoformat() + 'Z',
        }

        if tip_given:
            update_parts.append('ratings_with_tips :one')

        if rating <= LOW_RATING_THRESHOLD:
            update_parts.append('low_ratings :one')

        update_parts.append('SET hour = :hour, updated_at = :updated_at')

        update_expression = ', '.join(update_parts)

        update_item(
            AGGREGATED_METRICS_TABLE,
            key={'metric_key': metric_key},
            update_expression=update_expression,
            expression_attribute_values=expression_values,
            region_name=REGION
        )

        logger.debug(f"Updated rating metrics: {rating} stars")

    except Exception as e:
        logger.error(f"Error updating rating metrics: {e}")


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
            Namespace='RideShare/Ratings',
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Error publishing metrics: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler for Kinesis stream events.

    Processes batches of rating events from Kinesis.
    """
    logger.info(f"Processing {len(event['Records'])} rating records from Kinesis")

    processed = 0
    failed = 0
    low_ratings = 0
    ratings_by_star = defaultdict(int)
    total_rating_sum = 0
    with_comments = 0
    with_tips = 0
    failed_records = []

    for record in event['Records']:
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            rating_event = json.loads(payload)

            # Process rating
            result = process_rating_event(rating_event)

            if result.get('status') == 'processed':
                processed += 1

                # Track statistics
                rating = rating_event.get('rating', 5)
                ratings_by_star[rating] += 1
                total_rating_sum += rating

                if rating <= LOW_RATING_THRESHOLD:
                    low_ratings += 1

                if rating_event.get('comment'):
                    with_comments += 1

                if rating_event.get('tip_given', False):
                    with_tips += 1
            else:
                failed += 1
                failed_records.append(record)

        except Exception as e:
            logger.error(f"Error processing rating record: {e}", exc_info=True)
            failed += 1
            failed_records.append(record)

    # Calculate average rating
    avg_rating = total_rating_sum / processed if processed > 0 else 0

    # Publish metrics
    publish_metrics('RatingsProcessed', processed)
    publish_metrics('RatingsFailed', failed)
    publish_metrics('LowRatings', low_ratings)
    publish_metrics('AverageRating', avg_rating)
    publish_metrics('RatingsWithComments', with_comments)
    publish_metrics('RatingsWithTips', with_tips)

    # Per-star metrics
    for star, count in ratings_by_star.items():
        publish_metrics('RatingsByStar', count,
                       dimensions=[{'Name': 'Stars', 'Value': str(star)}])

    logger.info(f"Batch complete: {processed} processed, {failed} failed, "
               f"{low_ratings} low ratings, avg: {avg_rating:.2f} stars")
    logger.info(f"Distribution: {dict(ratings_by_star)}, "
               f"Comments: {with_comments}, Tips: {with_tips}")

    # Return failed records for retry
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
            'avg_rating': round(avg_rating, 2),
            'low_ratings': low_ratings
        })
    }
