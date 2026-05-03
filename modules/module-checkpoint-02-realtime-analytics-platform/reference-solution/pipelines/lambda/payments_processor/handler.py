"""
Payments Processor Lambda Handler

Processes payment events from Kinesis stream:
- Fraud detection based on amount, patterns, rapid succession
- Update ride state with payment status
- Send SNS alerts for fraud detection
- Track revenue metrics by payment method

Triggered by: Kinesis payments_stream
Tables: rides_state, aggregated_metrics
SNS: Fraud alerts
"""

import json
import logging
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict

import boto3

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import common utilities
try:
    from common.dynamodb_utils import put_item, update_item, get_item, query_table
    from common.s3_utils import write_records_to_s3
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from common.dynamodb_utils import put_item, update_item

# Environment variables
RIDES_STATE_TABLE = os.environ.get('RIDES_STATE_TABLE', 'rides_state')
AGGREGATED_METRICS_TABLE = os.environ.get('AGGREGATED_METRICS_TABLE', 'aggregated_metrics')
PAYMENTS_TABLE = os.environ.get('PAYMENTS_TABLE', 'payments')
FRAUD_ALERTS_TOPIC = os.environ.get('FRAUD_ALERTS_TOPIC', '')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'rideshare-archive')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Fraud detection thresholds
LARGE_TRANSACTION_THRESHOLD = 500.0
HIGH_FRAUD_SCORE_THRESHOLD = 70
MAX_FAILED_ATTEMPTS = 5

# Clients
sns = boto3.client('sns', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)

# In-memory tracking for fraud detection (within Lambda execution context)
customer_payment_attempts = defaultdict(list)


def detect_fraud(payment_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect potential fraud based on payment patterns.

    Returns fraud analysis with is_suspicious flag and reasons.
    """
    fraud_indicators = []
    fraud_score = payment_event.get('fraud_score', 0)
    amount = payment_event.get('amount', 0)
    customer_id = payment_event['customer_id']
    payment_method = payment_event.get('payment_method', '')
    status = payment_event.get('status', '')
    timestamp = datetime.fromisoformat(payment_event['timestamp'].replace('Z', '+00:00'))

    # Track attempt
    customer_payment_attempts[customer_id].append({
        'timestamp': timestamp,
        'amount': amount,
        'status': status,
        'method': payment_method
    })

    # Clean old attempts (keep last hour)
    cutoff = datetime.utcnow() - timedelta(hours=1)
    customer_payment_attempts[customer_id] = [
        a for a in customer_payment_attempts[customer_id]
        if a['timestamp'].replace(tzinfo=None) > cutoff
    ]

    attempts = customer_payment_attempts[customer_id]

    # Indicator 1: Large transaction amount
    if amount > LARGE_TRANSACTION_THRESHOLD:
        fraud_indicators.append(f"Large transaction: ${amount}")
        fraud_score += 20

    # Indicator 2: High fraud score from payment provider
    if fraud_score >= HIGH_FRAUD_SCORE_THRESHOLD:
        fraud_indicators.append(f"High fraud score: {fraud_score}")

    # Indicator 3: Multiple failed attempts
    failed_attempts = [a for a in attempts if a['status'] == 'failed']
    if len(failed_attempts) >= MAX_FAILED_ATTEMPTS:
        fraud_indicators.append(f"{len(failed_attempts)} failed attempts in last hour")
        fraud_score += 25

    # Indicator 4: Rapid succession of payments
    if len(attempts) >= 5:
        recent_attempts = [a for a in attempts
                          if (datetime.utcnow() - a['timestamp'].replace(tzinfo=None)).seconds < 300]
        if len(recent_attempts) >= 3:
            fraud_indicators.append(f"{len(recent_attempts)} payments in 5 minutes")
            fraud_score += 20

    # Indicator 5: Multiple payment methods in short time
    unique_methods = set(a['method'] for a in attempts)
    if len(unique_methods) >= 3:
        fraud_indicators.append(f"{len(unique_methods)} different payment methods")
        fraud_score += 15

    # Indicator 6: Failed payment flag
    if status == 'failed':
        failure_reason = payment_event.get('failure_reason', '')
        if 'fraud' in failure_reason.lower():
            fraud_indicators.append(f"Payment flagged as fraud: {failure_reason}")
            fraud_score += 30

    is_suspicious = len(fraud_indicators) > 0 or fraud_score >= HIGH_FRAUD_SCORE_THRESHOLD

    return {
        'is_suspicious': is_suspicious,
        'fraud_score': min(fraud_score, 100),
        'indicators': fraud_indicators,
        'total_attempts': len(attempts),
        'failed_attempts': len(failed_attempts),
    }


def send_fraud_alert(payment_event: Dict[str, Any], fraud_analysis: Dict[str, Any]):
    """Send fraud alert via SNS."""
    if not FRAUD_ALERTS_TOPIC:
        logger.warning("Fraud alerts topic not configured")
        return

    try:
        alert_message = {
            'alert_type': 'fraud_detected',
            'payment_id': payment_event['payment_id'],
            'ride_id': payment_event['ride_id'],
            'customer_id': payment_event['customer_id'],
            'amount': payment_event['amount'],
            'payment_method': payment_event.get('payment_method'),
            'fraud_score': fraud_analysis['fraud_score'],
            'indicators': fraud_analysis['indicators'],
            'timestamp': payment_event['timestamp'],
        }

        sns.publish(
            TopicArn=FRAUD_ALERTS_TOPIC,
            Subject='Fraud Alert: Suspicious Payment Detected',
            Message=json.dumps(alert_message, indent=2, default=str)
        )

        logger.warning(f"Fraud alert sent for payment {payment_event['payment_id']}: "
                      f"Score {fraud_analysis['fraud_score']}, "
                      f"Indicators: {fraud_analysis['indicators']}")

    except Exception as e:
        logger.error(f"Error sending fraud alert: {e}")


def process_payment_event(payment_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process payment event.

    Performs fraud detection, updates ride state, aggregates metrics.
    """
    payment_id = payment_event['payment_id']
    ride_id = payment_event['ride_id']
    customer_id = payment_event['customer_id']
    amount = payment_event.get('amount', 0)
    payment_method = payment_event.get('payment_method', 'unknown')
    status = payment_event.get('status', 'pending')

    logger.info(f"Processing payment {payment_id} for ride {ride_id}: ${amount} via {payment_method}")

    # Fraud detection
    fraud_analysis = detect_fraud(payment_event)

    # Send alert if suspicious
    if fraud_analysis['is_suspicious']:
        send_fraud_alert(payment_event, fraud_analysis)

    # Store payment record
    payment_record = {
        'payment_id': payment_id,
        'ride_id': ride_id,
        'customer_id': customer_id,
        'amount': amount,
        'payment_method': payment_method,
        'status': status,
        'fraud_score': fraud_analysis['fraud_score'],
        'is_suspicious': fraud_analysis['is_suspicious'],
        'fraud_indicators': fraud_analysis['indicators'],
        'timestamp': payment_event.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Add optional fields
    for field in ['card_provider', 'card_last_4', 'wallet_provider',
                  'failure_reason', 'processing_time_ms', 'transaction_fee']:
        if field in payment_event:
            payment_record[field] = payment_event[field]

    success = put_item(PAYMENTS_TABLE, payment_record, region_name=REGION)

    if not success:
        logger.error(f"Failed to store payment record: {payment_id}")
        return {'status': 'failed', 'payment_id': payment_id}

    # Update ride state with payment info
    if status == 'completed':
        update_item(
            RIDES_STATE_TABLE,
            key={'ride_id': ride_id},
            update_expression='SET payment_status = :status, payment_id = :payment_id, payment_method = :method, updated_at = :updated_at',
            expression_attribute_values={
                ':status': status,
                ':payment_id': payment_id,
                ':method': payment_method,
                ':updated_at': datetime.utcnow().isoformat() + 'Z',
            },
            region_name=REGION
        )

    # Update aggregated metrics
    if status == 'completed':
        update_revenue_metrics(payment_method, amount)

    logger.info(f"Payment {payment_id} processed: status={status}, "
               f"fraud_score={fraud_analysis['fraud_score']}, "
               f"suspicious={fraud_analysis['is_suspicious']}")

    return {
        'status': 'processed',
        'payment_id': payment_id,
        'fraud_analysis': fraud_analysis
    }


def update_revenue_metrics(payment_method: str, amount: float):
    """Update revenue metrics in aggregated_metrics table."""
    try:
        now = datetime.utcnow()
        metric_key = f"revenue#{now.strftime('%Y-%m-%d-%H')}"

        update_item(
            AGGREGATED_METRICS_TABLE,
            key={'metric_key': metric_key},
            update_expression=f'ADD revenue_{payment_method} :amount, total_revenue :amount, payment_count_{payment_method} :one SET hour = :hour, updated_at = :updated_at',
            expression_attribute_values={
                ':amount': amount,
                ':one': 1,
                ':hour': now.strftime('%Y-%m-%d-%H'),
                ':updated_at': now.isoformat() + 'Z',
            },
            region_name=REGION
        )

        logger.debug(f"Updated revenue metrics: {payment_method} ${amount}")

    except Exception as e:
        logger.error(f"Error updating revenue metrics: {e}")


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
            Namespace='RideShare/Payments',
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Error publishing metrics: {e}")


def lambda_handler(event, context):
    """
    Main Lambda handler for Kinesis stream events.

    Processes batches of payment events from Kinesis.
    """
    logger.info(f"Processing {len(event['Records'])} payment records from Kinesis")

    processed = 0
    failed = 0
    fraud_detected = 0
    total_revenue = 0.0
    by_method = defaultdict(lambda: {'count': 0, 'amount': 0.0})
    failed_records = []

    for record in event['Records']:
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            payment_event = json.loads(payload)

            # Process payment
            result = process_payment_event(payment_event)

            if result.get('status') == 'processed':
                processed += 1

                # Track fraud
                if result['fraud_analysis']['is_suspicious']:
                    fraud_detected += 1

                # Track revenue (only completed payments)
                if payment_event.get('status') == 'completed':
                    amount = payment_event.get('amount', 0)
                    method = payment_event.get('payment_method', 'unknown')
                    total_revenue += amount
                    by_method[method]['count'] += 1
                    by_method[method]['amount'] += amount
            else:
                failed += 1
                failed_records.append(record)

        except Exception as e:
            logger.error(f"Error processing payment record: {e}", exc_info=True)
            failed += 1
            failed_records.append(record)

    # Publish metrics
    publish_metrics('PaymentsProcessed', processed)
    publish_metrics('PaymentsFailed', failed)
    publish_metrics('FraudDetected', fraud_detected)
    publish_metrics('TotalRevenue', total_revenue,
                   dimensions=[{'Name': 'Unit', 'Value': 'USD'}])

    # Per-method metrics
    for method, stats in by_method.items():
        publish_metrics('PaymentsByMethod', stats['count'],
                       dimensions=[{'Name': 'PaymentMethod', 'Value': method}])
        publish_metrics('RevenueByMethod', stats['amount'],
                       dimensions=[{'Name': 'PaymentMethod', 'Value': method}])

    logger.info(f"Batch complete: {processed} processed, {failed} failed, "
               f"{fraud_detected} fraud detected, ${total_revenue:.2f} revenue")
    logger.info(f"By method: {dict(by_method)}")

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
            'fraud_detected': fraud_detected,
            'revenue': round(total_revenue, 2)
        })
    }
