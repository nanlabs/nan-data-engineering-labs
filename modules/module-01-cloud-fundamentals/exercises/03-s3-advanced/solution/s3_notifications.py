#!/usr/bin/env python3
"""
S3 Event Notifications - Complete Solution
"""

import boto3
import json
import time

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

sqs = boto3.client(
    'sqs',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(message: str):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    print(f"{RED}✗ {message}{RESET}")


def print_step(message: str):
    print(f"\n{BLUE}═══ {message} ═══{RESET}")


def create_sqs_queue(queue_name: str) -> tuple:
    try:
        response = sqs.create_queue(QueueName=queue_name)
        queue_url = response['QueueUrl']
        print_success(f"Created queue: {queue_name}")

        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']

        return (queue_url, queue_arn)
    except sqs.exceptions.QueueNameExists:
        queue_url = f"http://localhost:4566/000000000000/{queue_name}"
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']
        print_success(f"Queue already exists: {queue_name}")
        return (queue_url, queue_arn)
    except Exception as e:
        print_error(f"Failed to create queue: {str(e)}")
        return (None, None)


def configure_queue_policy(queue_url: str, queue_arn: str, bucket_name: str) -> bool:
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "sqs:SendMessage",
            "Resource": queue_arn,
            "Condition": {
                "ArnEquals": {
                    "aws:SourceArn": f"arn:aws:s3:::{bucket_name}"
                }
            }
        }]
    }

    try:
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={'Policy': json.dumps(policy)}
        )
        print_success("Queue policy configured (allows S3 to send messages)")
        return True
    except Exception as e:
        print_error(f"Failed to configure queue policy: {str(e)}")
        return False


def configure_bucket_notification(bucket_name: str, queue_arn: str) -> bool:
    notification_config = {
        'QueueConfigurations': [
            {
                'Id': 'S3UploadsNotification',
                'QueueArn': queue_arn,
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'prefix', 'Value': 'uploads/'}
                        ]
                    }
                }
            }
        ]
    }

    try:
        s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_config
        )
        print_success(f"Bucket notifications configured for {bucket_name}")
        print_success("  Event: s3:ObjectCreated:*")
        print_success("  Filter: uploads/* prefix")
        return True
    except Exception as e:
        print_error(f"Failed to configure notifications: {str(e)}")
        return False


def test_notifications(bucket_name: str, queue_url: str) -> bool:
    test_key = 'uploads/test-notification.txt'
    test_content = b'Testing S3 event notifications'

    try:
        # Clear any old messages
        sqs.purge_queue(QueueUrl=queue_url)
        time.sleep(2)

        # Upload test file
        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content
        )
        print_success(f"Uploaded test file: {test_key}")

        # Wait for event propagation
        print("Waiting 5 seconds for event to propagate...")
        time.sleep(5)

        # Receive message from queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5
        )

        if 'Messages' in response:
            message = json.loads(response['Messages'][0]['Body'])

            if 'Records' in message:
                event = message['Records'][0]
                print_success("Event notification received!")
                print(f"  Event Name: {event['eventName']}")
                print(f"  Bucket: {event['s3']['bucket']['name']}")
                print(f"  Object Key: {event['s3']['object']['key']}")
                print(f"  Object Size: {event['s3']['object']['size']} bytes")

                # Delete message
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=response['Messages'][0]['ReceiptHandle']
                )

                return True

        print_error("No message received from SQS")
        return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False


def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}S3 Event Notifications - Complete Solution{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    bucket_name = 'my-data-lake-raw'
    queue_name = 's3-events-queue'

    print_step("Step 1: Ensuring bucket exists")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print_success(f"Bucket exists: {bucket_name}")
    except:
        s3.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket: {bucket_name}")

    print_step("Step 2: Creating SQS queue")
    queue_url, queue_arn = create_sqs_queue(queue_name)
    if not queue_url or not queue_arn:
        return

    print(f"  Queue URL: {queue_url}")
    print(f"  Queue ARN: {queue_arn}")

    print_step("Step 3: Configuring queue policy")
    if not configure_queue_policy(queue_url, queue_arn, bucket_name):
        return

    print_step("Step 4: Configuring bucket notifications")
    if not configure_bucket_notification(bucket_name, queue_arn):
        return

    print_step("Step 5: Testing notifications")
    test_notifications(bucket_name, queue_url)

    print(f"\n{GREEN}{'='*60}")
    print("Event notifications setup completed!")
    print(f"{'='*60}{RESET}\n")

    print(f"{BLUE}Event-Driven Architecture Benefits:{RESET}")
    print("  ✓ Real-time processing triggers")
    print("  ✓ Decoupled components (S3 → SQS → Lambda)")
    print("  ✓ Scalable event handling")
    print("  ✓ Automatic retry on failures")
    print()

    print(f"{BLUE}Verification Commands:{RESET}")
    print("# Upload file to trigger event:")
    print(f"echo 'test' | aws --endpoint-url=http://localhost:4566 s3 cp - s3://{bucket_name}/uploads/test.txt")
    print()
    print("# Check for messages:")
    print(f"aws --endpoint-url=http://localhost:4566 sqs receive-message --queue-url {queue_url}")
    print()


if __name__ == "__main__":
    main()
