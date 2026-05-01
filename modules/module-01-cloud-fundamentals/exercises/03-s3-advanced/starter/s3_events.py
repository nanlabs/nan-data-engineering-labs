#!/usr/bin/env python3
"""
S3 Replication Configuration
Implements disaster recovery with cross-region replication
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

iam = boto3.client(
    'iam',
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


def create_backup_bucket(bucket_name: str) -> bool:
    """
    Create backup/destination bucket for replication

    Args:
        bucket_name: Name of backup bucket

    Returns:
        True if successful, False otherwise

    Hint: Versioning must be enabled on destination bucket too!
    """
    # TODO: Create backup bucket
    # TODO: Enable versioning on backup bucket
    # Your code here
    pass


def create_replication_role() -> str:
    """
    Create IAM role for S3 replication

    Returns:
        Role ARN if successful, empty string otherwise

    Hint: Role needs trust policy for s3.amazonaws.com
    and permissions for s3:ReplicateObject
    """

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            # TODO: Define trust relationship for S3 service
            # "Effect": "Allow",
            # "Principal": {"Service": "s3.amazonaws.com"},
            # "Action": "sts:AssumeRole"
        }]
    }

    replication_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                # TODO: Define permissions for replication
                # "Effect": "Allow",
                # "Action": ["s3:GetReplicationConfiguration", "s3:ListBucket"],
                # "Resource": "arn:aws:s3:::SOURCE_BUCKET"
            },
            {
                # TODO: Define permissions for reading source objects
                # "Action": ["s3:GetObjectVersionForReplication", ...],
                # "Resource": "arn:aws:s3:::SOURCE_BUCKET/*"
            },
            {
                # TODO: Define permissions for writing to destination
                # "Action": ["s3:ReplicateObject", "s3:ReplicateDelete"],
                # "Resource": "arn:aws:s3:::BACKUP_BUCKET/*"
            }
        ]
    }

    # TODO: Create role and attach policy
    # Your code here
    pass


def setup_replication(source_bucket: str, dest_bucket: str, role_arn: str) -> bool:
    """
    Configure replication from source to destination bucket

    Args:
        source_bucket: Source bucket name
        dest_bucket: Destination bucket name
        role_arn: ARN of replication role

    Returns:
        True if successful, False otherwise

    Hint: Use s3.put_bucket_replication() with ReplicationConfiguration
    """

    replication_config = {
        'Role': role_arn,
        'Rules': [
            {
                # TODO: Define replication rule
                # 'Status': 'Enabled',
                # 'Priority': 1,
                # 'Filter': {'Prefix': ''},  # Replicate all objects
                # 'Destination': {
                #     'Bucket': f'arn:aws:s3:::{dest_bucket}'
                # }
            }
        ]
    }

    # TODO: Apply replication configuration
    # Your code here
    pass


def test_replication(source_bucket: str, dest_bucket: str) -> bool:
    """
    Test that replication is working

    Args:
        source_bucket: Source bucket name
        dest_bucket: Destination bucket name

    Returns:
        True if replication works, False otherwise

    Hint: Upload file to source, check if it appears in destination
    """

    test_key = 'replication-test.txt'
    test_content = b'Testing replication'

    # TODO: Upload test file to source bucket
    # TODO: Wait a few seconds
    # TODO: Check if file exists in destination bucket
    # Your code here
    pass


def main():
    """Main execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}S3 Replication Configuration{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    source_bucket = 'my-data-lake-raw'
    backup_bucket = 'my-data-lake-backup'

    # Step 1: Create source bucket
    print_step("Step 1: Ensuring source bucket exists")
    try:
        s3.head_bucket(Bucket=source_bucket)
        print_success(f"Source bucket exists: {source_bucket}")
    except:
        s3.create_bucket(Bucket=source_bucket)
        s3.put_bucket_versioning(
            Bucket=source_bucket,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print_success(f"Created source bucket: {source_bucket}")

    # Step 2: Create backup bucket
    print_step("Step 2: Creating backup bucket")
    if create_backup_bucket(backup_bucket):
        print_success(f"Backup bucket ready: {backup_bucket}")
    else:
        print_error("Failed to create backup bucket")
        return

    # Step 3: Create IAM role for replication
    print_step("Step 3: Creating replication role")
    role_arn = create_replication_role()
    if role_arn:
        print_success(f"Replication role created: {role_arn}")
    else:
        print_error("Failed to create replication role")
        return

    # Step 4: Setup replication
    print_step("Step 4: Configuring replication")
    if setup_replication(source_bucket, backup_bucket, role_arn):
        print_success("Replication configured")
    else:
        print_error("Failed to configure replication")
        return

    # Step 5: Test replication
    print_step("Step 5: Testing replication")
    if test_replication(source_bucket, backup_bucket):
        print_success("Replication is working!")
    else:
        print_error("Replication test failed")

    print(f"\n{GREEN}Replication setup completed!{RESET}\n")


if __name__ == "__main__":
    main()
