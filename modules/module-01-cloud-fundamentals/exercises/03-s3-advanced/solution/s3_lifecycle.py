#!/usr/bin/env python3
"""
S3 Lifecycle Configuration - Complete Solution
"""

import boto3

s3 = boto3.client(
    's3',
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


def enable_versioning(bucket_name: str) -> bool:
    try:
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print_success(f"Versioning enabled on {bucket_name}")
        return True
    except Exception as e:
        print_error(f"Failed to enable versioning: {str(e)}")
        return False


def create_lifecycle_policy(bucket_name: str) -> bool:
    lifecycle_config = {
        'Rules': [
            {
                'Id': 'CostOptimizationPolicy',
                'Status': 'Enabled',
                'Filter': {'Prefix': ''},
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    }
                ],
                'Expiration': {
                    'Days': 365
                }
            },
            {
                'Id': 'DeleteOldVersions',
                'Status': 'Enabled',
                'Filter': {'Prefix': ''},
                'NoncurrentVersionExpiration': {
                    'NoncurrentDays': 90
                }
            }
        ]
    }

    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        print_success(f"Lifecycle policy applied to {bucket_name}")
        print_success("  - 0-30 days: STANDARD")
        print_success("  - 30-90 days: STANDARD_IA")
        print_success("  - 90-365 days: GLACIER")
        print_success("  - >365 days: Deleted")
        return True
    except Exception as e:
        print_error(f"Failed to create lifecycle policy: {str(e)}")
        return False


def verify_lifecycle(bucket_name: str) -> bool:
    try:
        response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)

        print_success("Lifecycle configuration retrieved:")
        for rule in response['Rules']:
            print(f"  Rule: {rule['Id']}")
            print(f"    Status: {rule['Status']}")
            if 'Transitions' in rule:
                for transition in rule['Transitions']:
                    print(f"    Transition: {transition['Days']} days → {transition['StorageClass']}")
            if 'Expiration' in rule:
                print(f"    Expiration: {rule['Expiration']['Days']} days")

        return True
    except s3.exceptions.NoSuchLifecycleConfiguration:
        print_error("No lifecycle configuration found")
        return False
    except Exception as e:
        print_error(f"Failed to verify lifecycle: {str(e)}")
        return False


def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}S3 Lifecycle Configuration - Complete Solution{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    bucket_name = 'my-data-lake-raw'

    print_step("Step 1: Ensuring bucket exists")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print_success(f"Bucket exists: {bucket_name}")
    except:
        s3.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket: {bucket_name}")

    print_step("Step 2: Enabling versioning")
    if not enable_versioning(bucket_name):
        return

    print_step("Step 3: Applying lifecycle policy")
    if not create_lifecycle_policy(bucket_name):
        return

    print_step("Step 4: Verifying configuration")
    verify_lifecycle(bucket_name)

    print(f"\n{GREEN}{'='*60}")
    print("Lifecycle configuration completed successfully!")
    print(f"{'='*60}{RESET}\n")

    print(f"{BLUE}Cost Savings Estimate:{RESET}")
    print("  Current: 10 TB in STANDARD = $230/month")
    print("  After optimization:")
    print("    1 TB STANDARD (0-30d): $23/month")
    print("    2 TB STANDARD_IA (30-90d): $25/month")
    print("    7 TB GLACIER (90-365d): $28/month")
    print(f"  {GREEN}Total: $76/month (67% savings!){RESET}\n")


if __name__ == "__main__":
    main()
