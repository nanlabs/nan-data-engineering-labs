#!/usr/bin/env python3
"""
IAM Setup Script for QuickMart Data Team

Purpose: Create IAM users, groups, roles and policies following least privilege
Author: [YOUR NAME]
Date: [DATE]

Usage: python iam_setup.py
"""

import boto3
from pathlib import Path
from typing import Dict

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"

# Initialize boto3 clients
iam = boto3.client(
    'iam',
    endpoint_url=ENDPOINT_URL,
    region_name=REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

s3 = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    region_name=REGION,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)


def print_step(message: str):
    """Print formatted step message"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


# ============================================================================
# FUNCTION 1: Create IAM Group
# ============================================================================
def create_group(group_name: str) -> bool:
    """
    Create an IAM group

    Args:
        group_name: Name of the group to create

    Returns:
        bool: True if successful, False otherwise

    TODO: Implement using iam.create_group()
    """
    try:
        # TODO: Create the group
        # Hint: iam.create_group(GroupName=group_name)

        # YOUR CODE HERE


        print_success(f"Created group: {group_name}")
        return True

    except iam.exceptions.EntityAlreadyExistsException:
        print_success(f"Group already exists: {group_name}")
        return True

    except Exception as e:
        print_error(f"Failed to create group {group_name}: {str(e)}")
        return False


# ============================================================================
# FUNCTION 2: Create IAM Policy
# ============================================================================
def create_policy(policy_name: str, policy_document: Dict) -> str:
    """
    Create an IAM policy from a policy document

    Args:
        policy_name: Name of the policy
        policy_document: Policy document as dict

    Returns:
        str: Policy ARN if successful, empty string otherwise

    TODO: Implement using iam.create_policy()
    """
    try:
        # TODO: Create the policy
        # Hint: iam.create_policy(
        #     PolicyName=policy_name,
        #     PolicyDocument=json.dumps(policy_document)
        # )

        # YOUR CODE HERE


        policy_arn = "arn:aws:iam::000000000000:policy/" + policy_name  # Placeholder
        print_success(f"Created policy: {policy_name}")
        return policy_arn

    except iam.exceptions.EntityAlreadyExistsException:
        # Policy already exists, get its ARN
        policy_arn = f"arn:aws:iam::000000000000:policy/{policy_name}"
        print_success(f"Policy already exists: {policy_name}")
        return policy_arn

    except Exception as e:
        print_error(f"Failed to create policy {policy_name}: {str(e)}")
        return ""


# ============================================================================
# FUNCTION 3: Attach Policy to Group
# ============================================================================
def attach_policy_to_group(group_name: str, policy_arn: str) -> bool:
    """
    Attach a policy to a group

    Args:
        group_name: Name of the group
        policy_arn: ARN of the policy

    Returns:
        bool: True if successful

    TODO: Implement using iam.attach_group_policy()
    """
    try:
        # TODO: Attach policy to group
        # Hint: iam.attach_group_policy(GroupName=..., PolicyArn=...)

        # YOUR CODE HERE


        print_success(f"Attached policy to {group_name}")
        return True

    except Exception as e:
        print_error(f"Failed to attach policy: {str(e)}")
        return False


# ============================================================================
# FUNCTION 4: Create IAM User
# ============================================================================
def create_user(username: str) -> bool:
    """
    Create an IAM user

    Args:
        username: Username to create

    Returns:
        bool: True if successful

    TODO: Implement using iam.create_user()
    """
    try:
        # TODO: Create user
        # Hint: iam.create_user(UserName=username)

        # YOUR CODE HERE


        print_success(f"Created user: {username}")
        return True

    except iam.exceptions.EntityAlreadyExistsException:
        print_success(f"User already exists: {username}")
        return True

    except Exception as e:
        print_error(f"Failed to create user {username}: {str(e)}")
        return False


# ============================================================================
# FUNCTION 5: Add User to Group
# ============================================================================
def add_user_to_group(username: str, group_name: str) -> bool:
    """
    Add a user to a group

    Args:
        username: Username
        group_name: Group name

    Returns:
        bool: True if successful

    TODO: Implement using iam.add_user_to_group()
    """
    try:
        # TODO: Add user to group
        # Hint: iam.add_user_to_group(UserName=..., GroupName=...)

        # YOUR CODE HERE


        print_success(f"Added {username} to {group_name}")
        return True

    except Exception as e:
        print_error(f"Failed to add user to group: {str(e)}")
        return False


# ============================================================================
# FUNCTION 6: Create IAM Role
# ============================================================================
def create_role(role_name: str, trust_policy: Dict) -> str:
    """
    Create an IAM role with trust policy

    Args:
        role_name: Name of the role
        trust_policy: Trust policy document

    Returns:
        str: Role ARN if successful

    TODO: Implement using iam.create_role()
    """
    try:
        # TODO: Create role with trust policy
        # Hint: iam.create_role(
        #     RoleName=role_name,
        #     AssumeRolePolicyDocument=json.dumps(trust_policy)
        # )

        # YOUR CODE HERE


        role_arn = f"arn:aws:iam::000000000000:role/{role_name}"  # Placeholder
        print_success(f"Created role: {role_name}")
        return role_arn

    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::000000000000:role/{role_name}"
        print_success(f"Role already exists: {role_name}")
        return role_arn

    except Exception as e:
        print_error(f"Failed to create role: {str(e)}")
        return ""


# ============================================================================
# FUNCTION 7: Attach Policy to Role
# ============================================================================
def attach_policy_to_role(role_name: str, policy_arn: str) -> bool:
    """
    Attach a policy to a role

    Args:
        role_name: Name of the role
        policy_arn: ARN of the policy

    Returns:
        bool: True if successful

    TODO: Implement using iam.attach_role_policy()
    """
    try:
        # TODO: Attach policy to role
        # YOUR CODE HERE


        print_success(f"Attached policy to role {role_name}")
        return True

    except Exception as e:
        print_error(f"Failed to attach policy to role: {str(e)}")
        return False


# ============================================================================
# FUNCTION 8: Apply S3 Bucket Policy
# ============================================================================
def apply_bucket_policy(bucket_name: str, policy_document: Dict) -> bool:
    """
    Apply a bucket policy to an S3 bucket

    Args:
        bucket_name: Name of the bucket
        policy_document: Policy document as dict

    Returns:
        bool: True if successful

    TODO: Implement using s3.put_bucket_policy()
    """
    try:
        # Ensure bucket exists first
        try:
            s3.head_bucket(Bucket=bucket_name)
        except:
            print_error(f"Bucket {bucket_name} does not exist")
            return False

        # TODO: Apply bucket policy
        # Hint: s3.put_bucket_policy(
        #     Bucket=bucket_name,
        #     Policy=json.dumps(policy_document)
        # )

        # YOUR CODE HERE


        print_success(f"Applied bucket policy to: {bucket_name}")
        return True

    except Exception as e:
        print_error(f"Failed to apply bucket policy: {str(e)}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Main execution flow"""

    print("\n" + "="*60)
    print("  🔐 IAM Setup for QuickMart Data Team")
    print("="*60)

    # ========================================================================
    # STEP 1: Create IAM Groups
    # ========================================================================
    print_step("Step 1: Creating IAM Groups")

    groups = ['data-engineers', 'data-analysts', 'ml-scientists']

    # TODO: Create all groups
    # YOUR CODE HERE (loop through groups and call create_group)


    # ========================================================================
    # STEP 2: Load and Create IAM Policies
    # ========================================================================
    print_step("Step 2: Creating IAM Policies")

    policies_dir = Path(__file__).parent / 'policies'

    # TODO: Load policy files and create policies
    # Hint: Read JSON files from policies/ directory
    # Hint: Call create_policy() for each

    policy_arns = {}  # Store policy ARNs for later use

    # Example structure:
    # with open(policies_dir / 'data_engineer.json') as f:
    #     policy_doc = json.load(f)
    #     arn = create_policy('DataEngineerPolicy', policy_doc)
    #     policy_arns['engineer'] = arn

    # YOUR CODE HERE


    # ========================================================================
    # STEP 3: Attach Policies to Groups
    # ========================================================================
    print_step("Step 3: Attaching Policies to Groups")

    # TODO: Attach policies to respective groups
    # YOUR CODE HERE


    # ========================================================================
    # STEP 4: Create IAM Users
    # ========================================================================
    print_step("Step 4: Creating IAM Users")

    users = {
        'alice.engineer': 'data-engineers',
        'bob.engineer': 'data-engineers',
        'carol.analyst': 'data-analysts',
        'david.analyst': 'data-analysts',
        'eve.scientist': 'ml-scientists'
    }

    # TODO: Create all users
    # YOUR CODE HERE


    # ========================================================================
    # STEP 5: Add Users to Groups
    # ========================================================================
    print_step("Step 5: Adding Users to Groups")

    # TODO: Add each user to their respective group
    # YOUR CODE HERE


    # ========================================================================
    # STEP 6: Create Lambda Execution Role
    # ========================================================================
    print_step("Step 6: Creating Lambda Execution Role")

    # Trust policy for Lambda service
    lambda_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    # TODO: Create role with trust policy
    # YOUR CODE HERE


    # Lambda execution policy
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::my-data-lake-*/*"
            },
            {
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

    # TODO: Create and attach policy to role
    # YOUR CODE HERE


    # ========================================================================
    # STEP 7: Apply S3 Bucket Policy
    # ========================================================================
    print_step("Step 7: Applying S3 Bucket Policy")

    # TODO: Load bucket_policy.json and apply
    # YOUR CODE HERE


    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*60)
    print("  📊 Summary")
    print("="*60)
    print(f"👥 Users created: {len(users)}")
    print(f"📦 Groups created: {len(groups)}")
    print("📋 Policies created: 3")
    print("🎭 Roles created: 1")
    print("🪣 Buckets secured: 1")
    print("\n✨ IAM setup completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
