"""
Daily Aggregation Lambda for RideShare Analytics Platform

This Lambda function is invoked by AWS Step Functions to aggregate ride, payment,
and rating data for the past 24 hours. It queries DynamoDB tables to calculate
key metrics and returns structured data for storage and reporting.

Functions:
- aggregate_rides: Total rides, completed, cancelled, avg duration, revenue
- aggregate_payments: Revenue by payment method, fraud detection
- aggregate_ratings: Average ratings, distribution, alerts

Author: RideShare Analytics Team
Version: 1.0.0
"""

import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
import boto3
from boto3.dynamodb.conditions import Attr

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# DynamoDB table names from environment variables
RIDES_TABLE = os.environ.get('RIDES_TABLE', 'rideshare_rides_state')
METRICS_TABLE = os.environ.get('METRICS_TABLE', 'rideshare_aggregated_metrics')

# Constants
HOURS_BACK = 24
RATING_THRESHOLD_LOW = 3.0


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON-serializable types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler invoked by Step Functions

    Args:
        event: Input from Step Functions containing aggregation_type and parameters
        context: Lambda execution context

    Returns:
        Dictionary with aggregated metrics and timestamp
    """
    try:
        logger.info(f"Starting aggregation with event: {json.dumps(event, cls=DecimalEncoder)}")

        aggregation_type = event.get('aggregation_type')
        time_window_hours = event.get('time_window_hours', HOURS_BACK)
        execution_id = event.get('execution_id', 'unknown')

        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)

        # Route to appropriate aggregation function
        if aggregation_type == 'rides':
            metrics = aggregate_rides(start_time, end_time)
        elif aggregation_type == 'payments':
            metrics = aggregate_payments(start_time, end_time)
        elif aggregation_type == 'ratings':
            metrics = aggregate_ratings(start_time, end_time)
        else:
            raise ValueError(f"Unknown aggregation type: {aggregation_type}")

        # Publish metrics to CloudWatch
        publish_cloudwatch_metrics(aggregation_type, metrics)

        result = {
            'statusCode': 200,
            'metrics': metrics,
            'timestamp': int(end_time.timestamp()),
            'execution_id': execution_id,
            'time_window': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': time_window_hours
            }
        }

        logger.info(f"Aggregation completed successfully: {json.dumps(result, cls=DecimalEncoder)}")
        return result

    except Exception as e:
        logger.error(f"Error in aggregation: {str(e)}", exc_info=True)
        raise


def aggregate_rides(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Aggregate ride metrics for the time window

    Calculates:
    - Total rides created
    - Completed rides
    - Cancelled rides
    - Average ride duration
    - Total revenue (fare + surge)
    - Rides by city

    Args:
        start_time: Start of time window
        end_time: End of time window

    Returns:
        Dictionary with ride metrics
    """
    logger.info(f"Aggregating rides from {start_time} to {end_time}")

    table = dynamodb.Table(RIDES_TABLE)

    # Query rides within time window
    # Note: In production, you'd use a GSI on timestamp for efficient queries
    response = table.scan(
        FilterExpression=Attr('ride_timestamp').between(
            int(start_time.timestamp()),
            int(end_time.timestamp())
        )
    )

    rides = response.get('Items', [])

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=Attr('ride_timestamp').between(
                int(start_time.timestamp()),
                int(end_time.timestamp())
            ),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        rides.extend(response.get('Items', []))

    logger.info(f"Retrieved {len(rides)} rides for aggregation")

    # Initialize counters
    total_rides = len(rides)
    completed_rides = 0
    cancelled_rides = 0
    total_duration = 0
    total_revenue = Decimal('0')
    rides_by_city = {}
    rides_with_duration = 0

    # Aggregate metrics
    for ride in rides:
        status = ride.get('status', 'unknown')

        if status == 'completed':
            completed_rides += 1

            # Sum duration
            if 'duration_minutes' in ride:
                total_duration += float(ride['duration_minutes'])
                rides_with_duration += 1

            # Sum revenue
            fare = Decimal(str(ride.get('fare_amount', 0)))
            surge = Decimal(str(ride.get('surge_amount', 0)))
            total_revenue += fare + surge

        elif status == 'cancelled':
            cancelled_rides += 1

        # Count by city
        city = ride.get('city', 'unknown')
        rides_by_city[city] = rides_by_city.get(city, 0) + 1

    # Calculate averages
    avg_duration = total_duration / rides_with_duration if rides_with_duration > 0 else 0
    completion_rate = (completed_rides / total_rides * 100) if total_rides > 0 else 0
    cancellation_rate = (cancelled_rides / total_rides * 100) if total_rides > 0 else 0

    # Get top cities
    top_cities = sorted(rides_by_city.items(), key=lambda x: x[1], reverse=True)[:10]

    metrics = {
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'cancelled_rides': cancelled_rides,
        'in_progress_rides': total_rides - completed_rides - cancelled_rides,
        'avg_duration': round(avg_duration, 2),
        'total_revenue': float(total_revenue),
        'completion_rate_pct': round(completion_rate, 2),
        'cancellation_rate_pct': round(cancellation_rate, 2),
        'top_cities': [{'city': city, 'rides': count} for city, count in top_cities]
    }

    logger.info(f"Ride aggregation completed: {json.dumps(metrics, cls=DecimalEncoder)}")
    return metrics


def aggregate_payments(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Aggregate payment metrics for the time window

    Calculates:
    - Total revenue
    - Revenue by payment method (credit card, cash, digital wallet)
    - Transaction count by payment method
    - Fraud detected count
    - Average transaction amount

    Args:
        start_time: Start of time window
        end_time: End of time window

    Returns:
        Dictionary with payment metrics
    """
    logger.info(f"Aggregating payments from {start_time} to {end_time}")

    # In a real implementation, this would query a payments table
    # For this example, we'll query the metrics table for payment data
    table = dynamodb.Table(METRICS_TABLE)

    # Query payment records
    response = table.scan(
        FilterExpression=Attr('metric_type').eq('payment') &
                         Attr('timestamp').between(
                             int(start_time.timestamp()),
                             int(end_time.timestamp())
                         )
    )

    payments = response.get('Items', [])

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=Attr('metric_type').eq('payment') &
                           Attr('timestamp').between(
                               int(start_time.timestamp()),
                               int(end_time.timestamp())
                           ),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        payments.extend(response.get('Items', []))

    logger.info(f"Retrieved {len(payments)} payment records for aggregation")

    # Initialize counters
    total_revenue = Decimal('0')
    payment_methods = {
        'credit_card': {'count': 0, 'amount': Decimal('0')},
        'cash': {'count': 0, 'amount': Decimal('0')},
        'digital_wallet': {'count': 0, 'amount': Decimal('0')}
    }
    fraud_detected = 0

    # Aggregate metrics
    for payment in payments:
        amount = Decimal(str(payment.get('amount', 0)))
        method = payment.get('payment_method', 'unknown')

        total_revenue += amount

        if method in payment_methods:
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += amount

        if payment.get('fraud_detected', False):
            fraud_detected += 1

    total_transactions = sum(m['count'] for m in payment_methods.values())
    avg_transaction = float(total_revenue / total_transactions) if total_transactions > 0 else 0

    metrics = {
        'total_revenue': float(total_revenue),
        'total_transactions': total_transactions,
        'avg_transaction_amount': round(avg_transaction, 2),
        'by_payment_method': {
            'credit_card': float(payment_methods['credit_card']['amount']),
            'cash': float(payment_methods['cash']['amount']),
            'digital_wallet': float(payment_methods['digital_wallet']['amount'])
        },
        'transaction_count_by_method': {
            'credit_card': payment_methods['credit_card']['count'],
            'cash': payment_methods['cash']['count'],
            'digital_wallet': payment_methods['digital_wallet']['count']
        },
        'fraud_detected': fraud_detected,
        'fraud_rate_pct': round((fraud_detected / total_transactions * 100) if total_transactions > 0 else 0, 2)
    }

    logger.info(f"Payment aggregation completed: {json.dumps(metrics, cls=DecimalEncoder)}")
    return metrics


def aggregate_ratings(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Aggregate rating metrics for the time window

    Calculates:
    - Average rating
    - Total ratings count
    - Rating distribution (5-star: X%, 4-star: Y%, etc.)
    - Low rating alerts (ratings below threshold)
    - Top and bottom rated drivers

    Args:
        start_time: Start of time window
        end_time: End of time window

    Returns:
        Dictionary with rating metrics
    """
    logger.info(f"Aggregating ratings from {start_time} to {end_time}")

    # In a real implementation, this would query a ratings table
    # For this example, we'll query the metrics table for rating data
    table = dynamodb.Table(METRICS_TABLE)

    # Query rating records
    response = table.scan(
        FilterExpression=Attr('metric_type').eq('rating') &
                         Attr('timestamp').between(
                             int(start_time.timestamp()),
                             int(end_time.timestamp())
                         )
    )

    ratings = response.get('Items', [])

    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=Attr('metric_type').eq('rating') &
                           Attr('timestamp').between(
                               int(start_time.timestamp()),
                               int(end_time.timestamp())
                           ),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        ratings.extend(response.get('Items', []))

    logger.info(f"Retrieved {len(ratings)} rating records for aggregation")

    # Initialize counters
    total_ratings = len(ratings)
    sum_ratings = 0
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    low_rating_alerts = 0
    driver_ratings = {}

    # Aggregate metrics
    for rating in ratings:
        rating_value = int(rating.get('rating', 0))
        driver_id = rating.get('driver_id', 'unknown')

        if 1 <= rating_value <= 5:
            sum_ratings += rating_value
            rating_distribution[rating_value] += 1

            if rating_value <= RATING_THRESHOLD_LOW:
                low_rating_alerts += 1

            # Track driver ratings
            if driver_id not in driver_ratings:
                driver_ratings[driver_id] = {'sum': 0, 'count': 0}
            driver_ratings[driver_id]['sum'] += rating_value
            driver_ratings[driver_id]['count'] += 1

    # Calculate metrics
    avg_rating = sum_ratings / total_ratings if total_ratings > 0 else 0

    # Calculate distribution percentages
    distribution_pct = {
        'five_star_pct': round((rating_distribution[5] / total_ratings * 100) if total_ratings > 0 else 0, 2),
        'four_star_pct': round((rating_distribution[4] / total_ratings * 100) if total_ratings > 0 else 0, 2),
        'three_star_pct': round((rating_distribution[3] / total_ratings * 100) if total_ratings > 0 else 0, 2),
        'two_star_pct': round((rating_distribution[2] / total_ratings * 100) if total_ratings > 0 else 0, 2),
        'one_star_pct': round((rating_distribution[1] / total_ratings * 100) if total_ratings > 0 else 0, 2)
    }

    # Calculate driver averages
    driver_averages = [
        {
            'driver_id': driver_id,
            'avg_rating': round(stats['sum'] / stats['count'], 2),
            'rating_count': stats['count']
        }
        for driver_id, stats in driver_ratings.items()
    ]

    # Get top and bottom drivers
    top_drivers = sorted(driver_averages, key=lambda x: x['avg_rating'], reverse=True)[:10]
    bottom_drivers = sorted(driver_averages, key=lambda x: x['avg_rating'])[:10]

    metrics = {
        'avg_rating': round(avg_rating, 2),
        'total_ratings': total_ratings,
        'distribution': {
            'five_star': rating_distribution[5],
            'four_star': rating_distribution[4],
            'three_star': rating_distribution[3],
            'two_star': rating_distribution[2],
            'one_star': rating_distribution[1]
        },
        'distribution_pct': distribution_pct,
        'low_rating_alerts': low_rating_alerts,
        'top_drivers': top_drivers,
        'bottom_drivers': bottom_drivers,
        'unique_drivers_rated': len(driver_ratings)
    }

    logger.info(f"Rating aggregation completed: {json.dumps(metrics, cls=DecimalEncoder)}")
    return metrics


def publish_cloudwatch_metrics(aggregation_type: str, metrics: Dict[str, Any]) -> None:
    """
    Publish key metrics to CloudWatch for monitoring and alerting

    Args:
        aggregation_type: Type of aggregation (rides, payments, ratings)
        metrics: Aggregated metrics to publish
    """
    try:
        metric_data = []
        namespace = 'RideShare/DailyAggregation'

        if aggregation_type == 'rides':
            metric_data.extend([
                {
                    'MetricName': 'TotalRides',
                    'Value': metrics['total_rides'],
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'CompletionRate',
                    'Value': metrics['completion_rate_pct'],
                    'Unit': 'Percent'
                },
                {
                    'MetricName': 'TotalRevenue',
                    'Value': metrics['total_revenue'],
                    'Unit': 'None'
                }
            ])
        elif aggregation_type == 'payments':
            metric_data.extend([
                {
                    'MetricName': 'TotalTransactions',
                    'Value': metrics['total_transactions'],
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'FraudRate',
                    'Value': metrics['fraud_rate_pct'],
                    'Unit': 'Percent'
                }
            ])
        elif aggregation_type == 'ratings':
            metric_data.extend([
                {
                    'MetricName': 'AverageRating',
                    'Value': metrics['avg_rating'],
                    'Unit': 'None'
                },
                {
                    'MetricName': 'LowRatingAlerts',
                    'Value': metrics['low_rating_alerts'],
                    'Unit': 'Count'
                }
            ])

        if metric_data:
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=metric_data
            )
            logger.info(f"Published {len(metric_data)} metrics to CloudWatch")

    except Exception as e:
        logger.warning(f"Failed to publish CloudWatch metrics: {str(e)}")
        # Don't fail the Lambda if CloudWatch publishing fails
