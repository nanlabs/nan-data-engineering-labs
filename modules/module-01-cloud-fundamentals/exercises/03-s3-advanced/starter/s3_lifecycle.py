#!/usr/bin/env python3
"""
S3 Lifecycle Configuration
Implements cost optimization with lifecycle policies
"""

import boto3

# Initialize S3 client
s3 = boto3.client(
    's3',
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


def enable_versioning(bucket_name: str) -> bool:
    """
    Enable versioning on an S3 bucket

    Args:
        bucket_name: Name of the bucket

    Returns:
        True if successful, False otherwise

    Hint: Use s3.put_bucket_versioning() with VersioningConfiguration
    """
    # TODO: Implement versioning enablement
    # Your code here
    pass


def create_lifecycle_policy(bucket_name: str) -> bool:
    """
    Create and apply lifecycle policy to bucket

    The policy should:
    - Transition to STANDARD_IA after 30 days
    - Transition to GLACIER after 90 days
    - Expire (delete) after 365 days

    Args:
        bucket_name: Name of the bucket

    Returns:
        True if successful, False otherwise

    Hint: Use s3.put_bucket_lifecycle_configuration() with Rules list
    """

    lifecycle_config = {
        'Rules': [
            {
                # TODO: Define lifecycle rule
                # 'Id': 'CostOptimization',
                # 'Status': 'Enabled' or 'Disabled',
                # 'Filter': {'Prefix': ''},  # Apply to all objects
                # 'Transitions': [...],
                # 'Expiration': {...}
            }
        ]
    }

    # TODO: Apply lifecycle configuration
    # Your code here
    pass


def verify_lifecycle(bucket_name: str) -> bool:
    """
    Verify that lifecycle policy is configured correctly

    Args:
        bucket_name: Name of the bucket

    Returns:
        True if lifecycle is configured, False otherwise

    Hint: Use s3.get_bucket_lifecycle_configuration()
    """
    # TODO: Get and print lifecycle configuration
    # Your code here
    pass


def main():
    """Main execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}S3 Lifecycle Configuration{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    bucket_name = 'my-data-lake-raw'

    # Step 1: Create bucket if not exists
    print_step("Step 1: Ensuring bucket exists")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print_success(f"Bucket exists: {bucket_name}")
    except:
        s3.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket: {bucket_name}")

    # Step 2: Enable versioning
    print_step("Step 2: Enabling versioning")
    if enable_versioning(bucket_name):
        print_success("Versioning enabled")
    else:
        print_error("Failed to enable versioning")
        return

    # Step 3: Create lifecycle policy
    print_step("Step 3: Applying lifecycle policy")
    if create_lifecycle_policy(bucket_name):
        print_success("Lifecycle policy applied")
    else:
        print_error("Failed to apply lifecycle policy")
        return

    # Step 4: Verify configuration
    print_step("Step 4: Verifying configuration")
    if verify_lifecycle(bucket_name):
        print_success("Configuration verified")
    else:
        print_error("Verification failed")

    print(f"\n{GREEN}Lifecycle configuration completed!{RESET}\n")


if __name__ == "__main__":
    main()
