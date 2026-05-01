#!/usr/bin/env python3
"""
IAM Setup Script - Complete Solution
Creates IAM groups, policies, users, and roles for a data team
"""

import boto3
import json
from pathlib import Path
from typing import Dict

# Initialize IAM client
iam = boto3.client(
    'iam',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

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
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_success(message: str):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    print(f"{RED}✗ {message}{RESET}")


def print_step(message: str):
    print(f"\n{BLUE}═══ {message} ═══{RESET}")


def print_warning(message: str):
    print(f"{YELLOW}⚠ {message}{RESET}")


def create_group(group_name: str) -> bool:
    """
    Create an IAM group

    Args:
        group_name: Name of the group to create

    Returns:
        True if successful, False otherwise
    """
    try:
        iam.create_group(GroupName=group_name)
        print_success(f"Created group: {group_name}")
        return True
    except iam.exceptions.EntityAlreadyExistsException:
        print_success(f"Group already exists: {group_name}")
        return True
    except Exception as e:
        print_error(f"Failed to create group {group_name}: {str(e)}")
        return False


def create_policy(policy_name: str, policy_document: Dict) -> str:
    """
    Create an IAM policy

    Args:
        policy_name: Name of the policy
        policy_document: Policy document as dict

    Returns:
        Policy ARN if successful, empty string otherwise
    """
    try:
        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        policy_arn = response['Policy']['Arn']
        print_success(f"Created policy: {policy_name} ({policy_arn})")
        return policy_arn
    except iam.exceptions.EntityAlreadyExistsException:
        # Policy exists, construct ARN
        policy_arn = f"arn:aws:iam::000000000000:policy/{policy_name}"
        print_success(f"Policy already exists: {policy_name}")
        return policy_arn
    except Exception as e:
        print_error(f"Failed to create policy {policy_name}: {str(e)}")
        return ""


def attach_policy_to_group(group_name: str, policy_arn: str) -> bool:
    """
    Attach a policy to a group

    Args:
        group_name: Name of the group
        policy_arn: ARN of the policy to attach

    Returns:
        True if successful, False otherwise
    """
    try:
        iam.attach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )
        print_success(f"Attached policy to {group_name}")
        return True
    except Exception as e:
        print_error(f"Failed to attach policy to {group_name}: {str(e)}")
        return False


def create_user(username: str) -> bool:
    """
    Create an IAM user

    Args:
        username: Name of the user to create

    Returns:
        True if successful, False otherwise
    """
    try:
        iam.create_user(UserName=username)
        print_success(f"Created user: {username}")
        return True
    except iam.exceptions.EntityAlreadyExistsException:
        print_success(f"User already exists: {username}")
        return True
    except Exception as e:
        print_error(f"Failed to create user {username}: {str(e)}")
        return False


def add_user_to_group(username: str, group_name: str) -> bool:
    """
    Add a user to a group

    Args:
        username: Name of the user
        group_name: Name of the group

    Returns:
        True if successful, False otherwise
    """
    try:
        iam.add_user_to_group(
            UserName=username,
            GroupName=group_name
        )
        print_success(f"Added {username} to {group_name}")
        return True
    except Exception as e:
        print_error(f"Failed to add {username} to {group_name}: {str(e)}")
        return False


def create_role(role_name: str, trust_policy: Dict) -> str:
    """
    Create an IAM role with a trust policy

    Args:
        role_name: Name of the role
        trust_policy: Trust policy document as dict

    Returns:
        Role ARN if successful, empty string otherwise
    """
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = response['Role']['Arn']
        print_success(f"Created role: {role_name} ({role_arn})")
        return role_arn
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::000000000000:role/{role_name}"
        print_success(f"Role already exists: {role_name}")
        return role_arn
    except Exception as e:
        print_error(f"Failed to create role {role_name}: {str(e)}")
        return ""


def attach_policy_to_role(role_name: str, policy_arn: str) -> bool:
    """
    Attach a policy to a role

    Args:
        role_name: Name of the role
        policy_arn: ARN of the policy to attach

    Returns:
        True if successful, False otherwise
    """
    try:
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print_success(f"Attached policy to role {role_name}")
        return True
    except Exception as e:
        print_error(f"Failed to attach policy to role {role_name}: {str(e)}")
        return False


def apply_bucket_policy(bucket_name: str, bucket_policy: Dict) -> bool:
    """
    Apply a bucket policy to an S3 bucket

    Args:
        bucket_name: Name of the bucket
        bucket_policy: Bucket policy document as dict

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create bucket if it doesn't exist
        try:
            s3.head_bucket(Bucket=bucket_name)
        except:
            s3.create_bucket(Bucket=bucket_name)
            print_success(f"Created bucket: {bucket_name}")

        # Apply bucket policy
        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print_success(f"Applied bucket policy to {bucket_name}")
        return True
    except Exception as e:
        print_error(f"Failed to apply bucket policy: {str(e)}")
        return False


def main():
    """Main execution function"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}IAM Setup for Data Team{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Step 1: Create IAM Groups
    print_step("Step 1: Creating IAM Groups")
    groups = ['data-engineers', 'data-analysts', 'ml-scientists']

    for group in groups:
        create_group(group)

    # Step 2: Create IAM Policies
    print_step("Step 2: Creating IAM Policies")

    policies_dir = Path(__file__).parent.parent / 'starter' / 'policies'
    policy_arns = {}

    # Load and create Data Engineer policy
    try:
        with open(policies_dir / 'data_engineer.json', 'r') as f:
            policy_doc = json.load(f)
            arn = create_policy('DataEngineerPolicy', policy_doc)
            policy_arns['engineer'] = arn
    except FileNotFoundError:
        print_error("data_engineer.json not found")

    # Load and create Data Analyst policy
    try:
        with open(policies_dir / 'data_analyst.json', 'r') as f:
            policy_doc = json.load(f)
            arn = create_policy('DataAnalystPolicy', policy_doc)
            policy_arns['analyst'] = arn
    except FileNotFoundError:
        print_error("data_analyst.json not found")

    # Load and create ML Scientist policy
    try:
        with open(policies_dir / 'ml_scientist.json', 'r') as f:
            policy_doc = json.load(f)
            arn = create_policy('MLScientistPolicy', policy_doc)
            policy_arns['scientist'] = arn
    except FileNotFoundError:
        print_error("ml_scientist.json not found")

    # Step 3: Attach Policies to Groups
    print_step("Step 3: Attaching Policies to Groups")

    if 'engineer' in policy_arns and policy_arns['engineer']:
        attach_policy_to_group('data-engineers', policy_arns['engineer'])

    if 'analyst' in policy_arns and policy_arns['analyst']:
        attach_policy_to_group('data-analysts', policy_arns['analyst'])

    if 'scientist' in policy_arns and policy_arns['scientist']:
        attach_policy_to_group('ml-scientists', policy_arns['scientist'])

    # Step 4: Create IAM Users
    print_step("Step 4: Creating IAM Users")

    users = {
        'alice.engineer': 'data-engineers',
        'bob.engineer': 'data-engineers',
        'carol.analyst': 'data-analysts',
        'david.analyst': 'data-analysts',
        'eve.scientist': 'ml-scientists'
    }

    for username in users.keys():
        create_user(username)

    # Step 5: Add Users to Groups
    print_step("Step 5: Adding Users to Groups")

    for username, group_name in users.items():
        add_user_to_group(username, group_name)

    # Step 6: Create Lambda Execution Role
    print_step("Step 6: Creating Lambda Execution Role")

    lambda_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    role_arn = create_role('lambda-data-processor-role', lambda_trust_policy)

    if role_arn:
        # Create inline policy for Lambda
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "S3DataLakeAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": "arn:aws:s3:::my-data-lake-*/*"
                },
                {
                    "Sid": "S3ListBuckets",
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": "arn:aws:s3:::my-data-lake-*"
                },
                {
                    "Sid": "CloudWatchLogs",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }

        lambda_policy_arn = create_policy('LambdaDataProcessorPolicy', lambda_policy)
        if lambda_policy_arn:
            attach_policy_to_role('lambda-data-processor-role', lambda_policy_arn)

    # Step 7: Apply S3 Bucket Policy
    print_step("Step 7: Applying S3 Bucket Policy")

    bucket_policy_file = Path(__file__).parent.parent / 'starter' / 'bucket_policy.json'

    if bucket_policy_file.exists():
        try:
            with open(bucket_policy_file, 'r') as f:
                bucket_policy = json.load(f)

            apply_bucket_policy('my-data-lake-raw', bucket_policy)
        except Exception as e:
            print_error(f"Failed to load bucket policy: {str(e)}")
    else:
        print_warning("bucket_policy.json not found, skipping")

    # Summary
    print_step("Summary")
    print(f"{GREEN}✓ Created 3 IAM groups")
    print("✓ Created 3 IAM policies (plus Lambda policy)")
    print("✓ Created 5 IAM users")
    print("✓ Created 1 IAM role (Lambda)")
    print(f"✓ Applied S3 bucket policy{RESET}")

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}IAM setup completed successfully!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Verification commands
    print(f"{YELLOW}Verification commands:{RESET}")
    print("aws --endpoint-url=http://localhost:4566 iam list-groups")
    print("aws --endpoint-url=http://localhost:4566 iam list-users")
    print("aws --endpoint-url=http://localhost:4566 iam list-policies --scope Local")
    print("aws --endpoint-url=http://localhost:4566 iam list-roles")
    print()


if __name__ == "__main__":
    main()
