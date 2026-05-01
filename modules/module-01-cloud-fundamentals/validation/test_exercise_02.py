#!/usr/bin/env python3
"""
Validation tests for Exercise 02: IAM Policies
"""

import boto3
import pytest

ENDPOINT_URL = 'http://localhost:4566'

iam = boto3.client(
    'iam',
    endpoint_url=ENDPOINT_URL,
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)


def test_groups_created():
    """Test that required IAM groups exist"""
    response = iam.list_groups()
    group_names = [g['GroupName'] for g in response['Groups']]

    assert 'data-engineers' in group_names, "data-engineers group not found"
    assert 'data-analysts' in group_names, "data-analysts group not found"
    assert 'ml-scientists' in group_names, "ml-scientists group not found"


def test_policies_created():
    """Test that custom policies were created"""
    response = iam.list_policies(Scope='Local')
    policy_names = [p['PolicyName'] for p in response['Policies']]

    assert 'DataEngineerPolicy' in policy_names, "DataEngineerPolicy not found"
    assert 'DataAnalystPolicy' in policy_names, "DataAnalystPolicy not found"
    assert 'MLScientistPolicy' in policy_names, "MLScientistPolicy not found"


def test_users_created():
    """Test that all users were created"""
    response = iam.list_users()
    usernames = [u['UserName'] for u in response['Users']]

    expected_users = [
        'alice.engineer',
        'bob.engineer',
        'carol.analyst',
        'david.analyst',
        'eve.scientist'
    ]

    for user in expected_users:
        assert user in usernames, f"User {user} not found"


def test_users_in_groups():
    """Test that users are assigned to correct groups"""
    # Check data-engineers group
    response = iam.get_group(GroupName='data-engineers')
    engineers = [u['UserName'] for u in response['Users']]
    assert 'alice.engineer' in engineers
    assert 'bob.engineer' in engineers

    # Check data-analysts group
    response = iam.get_group(GroupName='data-analysts')
    analysts = [u['UserName'] for u in response['Users']]
    assert 'carol.analyst' in analysts
    assert 'david.analyst' in analysts

    # Check ml-scientists group
    response = iam.get_group(GroupName='ml-scientists')
    scientists = [u['UserName'] for u in response['Users']]
    assert 'eve.scientist' in scientists


def test_policies_attached_to_groups():
    """Test that policies are attached to groups"""
    # Check data-engineers
    response = iam.list_attached_group_policies(GroupName='data-engineers')
    policies = [p['PolicyName'] for p in response['AttachedPolicies']]
    assert 'DataEngineerPolicy' in policies

    # Check data-analysts
    response = iam.list_attached_group_policies(GroupName='data-analysts')
    policies = [p['PolicyName'] for p in response['AttachedPolicies']]
    assert 'DataAnalystPolicy' in policies

    # Check ml-scientists
    response = iam.list_attached_group_policies(GroupName='ml-scientists')
    policies = [p['PolicyName'] for p in response['AttachedPolicies']]
    assert 'MLScientistPolicy' in policies


def test_lambda_role_created():
    """Test that Lambda execution role exists"""
    response = iam.list_roles()
    role_names = [r['RoleName'] for r in response['Roles']]
    assert 'lambda-data-processor-role' in role_names


def test_policy_content_data_engineer():
    """Test that DataEngineerPolicy has correct permissions"""
    # Get policy ARN
    response = iam.list_policies(Scope='Local')
    policy_arn = None
    for p in response['Policies']:
        if p['PolicyName'] == 'DataEngineerPolicy':
            policy_arn = p['Arn']
            break

    assert policy_arn is not None, "DataEngineerPolicy not found"

    # Get policy version
    response = iam.get_policy(PolicyArn=policy_arn)
    version_id = response['Policy']['DefaultVersionId']

    # Get policy document
    response = iam.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)
    doc = response['PolicyVersion']['Document']

    # Check for S3 permissions
    actions = []
    for statement in doc['Statement']:
        if isinstance(statement['Action'], list):
            actions.extend(statement['Action'])
        else:
            actions.append(statement['Action'])

    assert any('s3:' in action for action in actions), "No S3 permissions found"


def test_policy_content_data_analyst():
    """Test that DataAnalystPolicy has read-only permissions"""
    response = iam.list_policies(Scope='Local')
    policy_arn = None
    for p in response['Policies']:
        if p['PolicyName'] == 'DataAnalystPolicy':
            policy_arn = p['Arn']
            break

    assert policy_arn is not None

    response = iam.get_policy(PolicyArn=policy_arn)
    version_id = response['Policy']['DefaultVersionId']

    response = iam.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)
    doc = response['PolicyVersion']['Document']

    # Check for read-only actions
    actions = []
    for statement in doc['Statement']:
        if isinstance(statement['Action'], list):
            actions.extend(statement['Action'])
        else:
            actions.append(statement['Action'])

    has_get = any('Get' in action for action in actions)
    has_list = any('List' in action for action in actions)

    assert has_get or has_list, "No read permissions found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
