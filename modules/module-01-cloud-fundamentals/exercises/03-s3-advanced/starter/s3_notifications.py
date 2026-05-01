#!/usr/bin/env python3
"""
S3 Event Notifications
Implements event-driven architecture with S3 and SQS
"""

import boto3

# Initialize clients
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

# Color codes
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
    """
    Create SQS queue for S3 event notifications

    Args:
        queue_name: Name of the queue

    Returns:
        Tuple of (queue_url, queue_arn) if successful, (None, None) otherwise

    Hint: Use sqs.create_queue() then sqs.get_queue_attributes() to get ARN
    """
    # TODO: Create SQS queue
    # TODO: Get queue attributes to retrieve ARN
    # Your code here
    pass


def configure_queue_policy(queue_url: str, queue_arn: str, bucket_name: str) -> bool:
    """
    Configure SQS queue policy to allow S3 to send messages

    Args:
        queue_url: URL of the queue
        queue_arn: ARN of the queue
        bucket_name: Name of S3 bucket that will send events

    Returns:
        True if successful, False otherwise

    Hint: Queue policy must allow s3.amazonaws.com to sqs:SendMessage
    """

    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            # TODO: Define policy allowing S3 to send messages
            # "Effect": "Allow",
            # "Principal": {"Service": "s3.amazonaws.com"},
            # "Action": "sqs:SendMessage",
            # "Resource": queue_arn,
            # "Condition": {
            #     "ArnEquals": {"aws:SourceArn": f"arn:aws:s3:::{bucket_name}"}
            # }
        }]
    }

    # TODO: Set queue attributes with policy
    # Your code here
    pass


def configure_bucket_notification(bucket_name: str, queue_arn: str) -> bool:
    """
    Configure S3 bucket to send notifications to SQS on ObjectCreated events

    Args:
        bucket_name: Name of the bucket
        queue_arn: ARN of the SQS queue

    Returns:
        True if successful, False otherwise

    Hint: Use s3.put_bucket_notification_configuration() with QueueConfigurations
    """

    notification_config = {
        'QueueConfigurations': [
            {
                # TODO: Define queue configuration
                # 'QueueArn': queue_arn,
                # 'Events': ['s3:ObjectCreated:*'],
                # 'Filter': {
                #     'Key': {
                #         'FilterRules': [
                #             {'Name': 'prefix', 'Value': 'uploads/'}
                #         ]
                #     }
                # }
            }
        ]
    }

    # TODO: Apply notification configuration
    # Your code here
    pass


def test_notifications(bucket_name: str, queue_url: str) -> bool:
    """
    Test that notifications are working

    Args:
        bucket_name: Name of the bucket
        queue_url: URL of the SQS queue

    Returns:
        True if notification received, False otherwise

    Hint: Upload file, wait, then receive message from queue
    """

    test_key = 'uploads/test-notification.txt'
    test_content = b'Testing event notifications'

    # TODO: Upload test file to trigger event
    # TODO: Wait a few seconds for event to propagate
    # TODO: Receive message from SQS
    # TODO: Verify message contains S3 event data
    # Your code here
    pass


def main():
    """Main execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}S3 Event Notifications Configuration{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    bucket_name = 'my-data-lake-raw'
    queue_name = 's3-events-queue'

    # Step 1: Ensure bucket exists
    print_step("Step 1: Ensuring bucket exists")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print_success(f"Bucket exists: {bucket_name}")
    except:
        s3.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket: {bucket_name}")

    # Step 2: Create SQS queue
    print_step("Step 2: Creating SQS queue")
    queue_url, queue_arn = create_sqs_queue(queue_name)
    if queue_url and queue_arn:
        print_success(f"Queue created: {queue_name}")
        print_success(f"Queue URL: {queue_url}")
        print_success(f"Queue ARN: {queue_arn}")
    else:
        print_error("Failed to create queue")
        return

    # Step 3: Configure queue policy
    print_step("Step 3: Configuring queue policy")
    if configure_queue_policy(queue_url, queue_arn, bucket_name):
        print_success("Queue policy configured")
    else:
        print_error("Failed to configure queue policy")
        return

    # Step 4: Configure bucket notifications
    print_step("Step 4: Configuring bucket notifications")
    if configure_bucket_notification(bucket_name, queue_arn):
        print_success("Bucket notifications configured")
    else:
        print_error("Failed to configure notifications")
        return

    # Step 5: Test notifications
    print_step("Step 5: Testing notifications")
    if test_notifications(bucket_name, queue_url):
        print_success("Notifications are working!")
    else:
        print_error("Notification test failed")

    print(f"\n{GREEN}Event notifications setup completed!{RESET}\n")

    # Print verification commands
    print(f"\n{BLUE}Verification Commands:{RESET}")
    print("# Upload test file:")
    print(f"aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://{bucket_name}/uploads/")
    print("\n# Check for messages:")
    print(f"aws --endpoint-url=http://localhost:4566 sqs receive-message --queue-url {queue_url}")
    print()


if __name__ == "__main__":
    main()
