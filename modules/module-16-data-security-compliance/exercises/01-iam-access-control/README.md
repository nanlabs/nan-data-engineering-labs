# Exercise 01: IAM & Access Control

## Overview
Implement least-privilege IAM policies for data teams, configure cross-account access, set up permission boundaries, and validate policies with IAM Access Analyzer.

**Difficulty**: ⭐⭐⭐ Advanced
**Duration**: ~3 hours
**Prerequisites**: Basic AWS IAM knowledge, AWS CLI configured

## Learning Objectives

- Design IAM policies following the principle of least privilege
- Implement resource-based and identity-based policies
- Configure cross-account IAM roles
- Use permission boundaries to delegate permissions safely
- Validate policies with IAM Access Analyzer
- Implement service control policies (SCPs)

## Key Concepts

- **IAM Policy**: JSON document defining permissions
- **Principal**: Entity (user, role, service) requesting access
- **Resource-Based Policy**: Attached to resources (S3 bucket policy)
- **Identity-Based Policy**: Attached to IAM identities
- **Permission Boundary**: Maximum permissions an identity can have
- **Service Control Policy (SCP)**: AWS Organizations policy restricting account actions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS ORGANIZATION                        │
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐          │
│  │  Master Account │         │  Data Account   │          │
│  │                 │         │                 │          │
│  │  - SCPs         │────────>│  - IAM Roles    │          │
│  │  - Billing      │         │  - Permissions  │          │
│  └─────────────────┘         │  - Resources    │          │
│                              └─────────────────┘          │
│                                     │                      │
│                              ┌──────┴──────┐              │
│                              │             │              │
│                       ┌──────▼─────┐ ┌────▼──────┐       │
│                       │DataEngineer│ │DataScience│       │
│                       │   Role     │ │   Role    │       │
│                       │            │ │           │       │
│                       │- Glue  ✓   │ │- Athena ✓ │       │
│                       │- S3    ✓   │ │- S3 Read✓ │       │
│                       │- EMR   ✓   │ │- Redshift✓│       │
│                       └────────────┘ └───────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Design IAM Policies for Personas (45 minutes)

Create IAM policies for three data team personas.

**File**: `policies/data-engineer-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GlueFullAccess",
      "Effect": "Allow",
      "Action": [
        "glue:CreateJob",
        "glue:StartJobRun",
        "glue:GetJob",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:UpdateJob",
        "glue:DeleteJob",
        "glue:CreateCrawler",
        "glue:StartCrawler",
        "glue:GetCrawler",
        "glue:DeleteCrawler",
        "glue:CreateDatabase",
        "glue:GetDatabase",
        "glue:UpdateDatabase",
        "glue:DeleteDatabase",
        "glue:CreateTable",
        "glue:GetTable",
        "glue:UpdateTable",
        "glue:DeleteTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:CreatePartition",
        "glue:BatchCreatePartition",
        "glue:UpdatePartition",
        "glue:DeletePartition"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "S3DataLakeAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::data-lake-raw/*",
        "arn:aws:s3:::data-lake-processed/*",
        "arn:aws:s3:::data-lake-curated/*",
        "arn:aws:s3:::data-lake-raw",
        "arn:aws:s3:::data-lake-processed",
        "arn:aws:s3:::data-lake-curated"
      ],
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    },
    {
      "Sid": "EMRClusterManagement",
      "Effect": "Allow",
      "Action": [
        "elasticmapreduce:RunJobFlow",
        "elasticmapreduce:TerminateJobFlows",
        "elasticmapreduce:AddJobFlowSteps",
        "elasticmapreduce:DescribeCluster",
        "elasticmapreduce:ListClusters",
        "elasticmapreduce:ListInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "elasticmapreduce:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "PassRoleToServices",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::*:role/GlueServiceRole",
        "arn:aws:iam::*:role/EMRServiceRole"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "glue.amazonaws.com",
            "elasticmapreduce.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "KMSDecryption",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:*:key/*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.us-east-1.amazonaws.com",
            "glue.us-east-1.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/aws/glue/*"
    }
  ]
}
```

**File**: `policies/data-scientist-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AthenaQueryExecution",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution",
        "athena:GetWorkGroup",
        "athena:ListWorkGroups",
        "athena:CreateNamedQuery",
        "athena:GetNamedQuery",
        "athena:ListNamedQueries"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadOnlyAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::data-lake-curated/*",
        "arn:aws:s3:::data-lake-curated",
        "arn:aws:s3:::athena-query-results/*",
        "arn:aws:s3:::athena-query-results"
      ]
    },
    {
      "Sid": "S3QueryResultsWrite",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::athena-query-results/${aws:username}/*"
    },
    {
      "Sid": "GlueDataCatalogRead",
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RedshiftReadAccess",
      "Effect": "Allow",
      "Action": [
        "redshift:DescribeClusters",
        "redshift:GetClusterCredentials"
      ],
"Resource": "arn:aws:redshift:us-east-1:*:cluster:data-warehouse"
    },
    {
      "Sid": "RedshiftDataAPI",
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult",
        "redshift-data:ListStatements"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SageMakerNotebooks",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateNotebookInstance",
        "sagemaker:DescribeNotebookInstance",
        "sagemaker:StartNotebookInstance",
        "sagemaker:StopNotebookInstance",
        "sagemaker:DeleteNotebookInstance"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:*:notebook-instance/${aws:username}-*"
    }
  ]
}
```

**File**: `policies/data-analyst-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "QuickSightAccess",
      "Effect": "Allow",
      "Action": [
        "quicksight:CreateDataSet",
        "quicksight:DescribeDataSet",
        "quicksight:UpdateDataSet",
        "quicksight:DeleteDataSet",
        "quicksight:CreateAnalysis",
        "quicksight:DescribeAnalysis",
        "quicksight:UpdateAnalysis",
        "quicksight:DeleteAnalysis",
        "quicksight:CreateDashboard",
        "quicksight:DescribeDashboard",
        "quicksight:UpdateDashboard"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AthenaReadOnlyQueries",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:ListQueryExecutions"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "athena:WorkGroup": "analyst-workgroup"
        }
      }
    },
    {
      "Sid": "S3AnalystDataRead",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::data-lake-curated/public/*",
        "arn:aws:s3:::data-lake-curated"
      ]
    },
    {
      "Sid": "GlueCatalogReadOnly",
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetTables"
      ],
      "Resource": "*"
    }
  ]
}
```

## Task 2: Create IAM Roles (30 minutes)

**File**: `create_iam_roles.py`

```python
#!/usr/bin/env python3
"""Create IAM roles for data personas"""

import boto3
import json

iam = boto3.client('iam')


def create_role_with_policy(role_name, assume_role_policy, policy_file):
    """Create IAM role and attach custom policy"""

    # Create role
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description=f'Role for {role_name}',
            MaxSessionDuration=3600,
            Tags=[
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'Team', 'Value': 'data'}
            ]
        )
        print(f"✓ Created role: {role_name}")
        print(f"  ARN: {response['Role']['Arn']}")

    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  Role already exists: {role_name}")

    # Create policy
    with open(policy_file, 'r') as f:
        policy_document = json.load(f)

    policy_name = f"{role_name}-policy"

    try:
        policy_response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description=f'Policy for {role_name}'
        )
        policy_arn = policy_response['Policy']['Arn']
        print(f"✓ Created policy: {policy_name}")

    except iam.exceptions.EntityAlreadyExistsException:
        # Get existing policy ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
        print(f"  Policy already exists: {policy_name}")

    # Attach policy to role
    try:
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✓ Attached policy to role")
    except Exception as e:
        print(f"  Policy already attached: {e}")

    return role_name


def create_data_engineer_role():
    """Create Data Engineer role"""

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "glue.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::*:root"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "sts:ExternalId": "data-engineer-access"
                    }
                }
            }
        ]
    }

    return create_role_with_policy(
        'DataEngineerRole',
        assume_role_policy,
        'policies/data-engineer-policy.json'
    )


def create_data_scientist_role():
    """Create Data Scientist role"""

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sagemaker.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::*:root"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "sts:ExternalId": "data-scientist-access"
                    }
                }
            }
        ]
    }

    return create_role_with_policy(
        'DataScientistRole',
        assume_role_policy,
        'policies/data-scientist-policy.json'
    )


def create_data_analyst_role():
    """Create Data Analyst role"""

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "quicksight.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::*:root"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    return create_role_with_policy(
        'DataAnalystRole',
        assume_role_policy,
        'policies/data-analyst-policy.json'
    )


if __name__ == '__main__':
    print("="*60)
    print("CREATING IAM ROLES FOR DATA PERSONAS")
    print("="*60)

    print("\n1. Data Engineer Role:")
    create_data_engineer_role()

    print("\n2. Data Scientist Role:")
    create_data_scientist_role()

    print("\n3. Data Analyst Role:")
    create_data_analyst_role()

    print("\n" + "="*60)
    print("✓ ALL ROLES CREATED")
    print("="*60)
```

## Task 3: Configure Permission Boundaries (30 minutes)

**File**: `permission_boundary.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowedServices",
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "glue:*",
        "athena:*",
        "redshift:*",
        "sagemaker:*",
        "quicksight:*",
        "emr:*",
        "cloudwatch:*",
        "logs:*",
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:GenerateDataKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDangerousActions",
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser",
        "iam:DeleteUser",
        "iam:CreateAccessKey",
        "iam:DeleteAccessKey",
        "iam:PutUserPolicy",
        "iam:AttachUserPolicy",
        "iam:DeleteUserPolicy",
        "iam:DetachUserPolicy",
        "kms:ScheduleKeyDeletion",
        "kms:DeleteAlias",
        "s3:DeleteBucket",
        "s3:DeleteBucketPolicy",
        "rds:DeleteDBInstance",
        "rds:DeleteDBCluster"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyRegionRestriction",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "organizations:*",
        "route53:*",
        "cloudfront:*",
        "waf:*",
        "support:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2"
          ]
        }
      }
    }
  ]
}
```

**File**: `apply_permission_boundary.py`

```python
#!/usr/bin/env python3
"""Apply permission boundaries to roles"""

import boto3
import json

iam = boto3.client('iam')


def create_permission_boundary():
    """Create permission boundary policy"""

    with open('permission_boundary.json', 'r') as f:
        policy_document = json.load(f)

    policy_name = 'DataTeamPermissionBoundary'

    try:
        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description='Permission boundary for data team roles'
        )
        policy_arn = response['Policy']['Arn']
        print(f"✓ Created permission boundary: {policy_name}")
        return policy_arn

    except iam.exceptions.EntityAlreadyExistsException:
        account_id = boto3.client('sts').get_caller_identity()['Account']
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
        print(f"  Permission boundary already exists")
        return policy_arn


def apply_boundary_to_role(role_name, boundary_arn):
    """Apply permission boundary to role"""

    try:
        iam.put_role_permissions_boundary(
            RoleName=role_name,
            PermissionsBoundary=boundary_arn
        )
        print(f"✓ Applied boundary to {role_name}")

    except Exception as e:
        print(f"✗ Error applying boundary: {e}")


if __name__ == '__main__':
    print("="*60)
    print("APPLYING PERMISSION BOUNDARIES")
    print("="*60)

    # Create boundary
    boundary_arn = create_permission_boundary()

    # Apply to all data roles
    roles = ['DataEngineerRole', 'DataScientistRole', 'DataAnalystRole']

    print("\nApplying to roles:")
    for role in roles:
        apply_boundary_to_role(role, boundary_arn)

    print("\n" + "="*60)
    print("✓ PERMISSION BOUNDARIES APPLIED")
    print("="*60)
```

## Task 4: Cross-Account Access (30 minutes)

**File**: `cross_account_role.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id-12345"
        },
        "IpAddress": {
          "aws:SourceIp": [
            "203.0.113.0/24",
            "198.51.100.0/24"
          ]
        }
      }
    }
  ]
}
```

**File**: `setup_cross_account.py`

```python
#!/usr/bin/env python3
"""Setup cross-account access"""

import boto3
import json

iam = boto3.client('iam')


def create_cross_account_role(trusted_account_id, external_id):
    """Create role for cross-account access"""

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{trusted_account_id}:root"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "sts:ExternalId": external_id
                    }
                }
            }
        ]
    }

    role_name = 'CrossAccountDataAccess'

    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description='Cross-account role for data access',
            MaxSessionDuration=3600
        )
        print(f"✓ Created cross-account role: {role_name}")
        print(f"  ARN: {response['Role']['Arn']}")

        return response['Role']['Arn']

    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  Role already exists: {role_name}")
        role = iam.get_role(RoleName=role_name)
        return role['Role']['Arn']


def attach_s3_read_policy(role_name):
    """Attach S3 read-only policy"""

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::data-lake-curated/*",
                    "arn:aws:s3:::data-lake-curated"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "kms:Decrypt",
                    "kms:DescribeKey"
                ],
                "Resource": "arn:aws:kms:us-east-1:*:key/*"
            }
        ]
    }

    policy_name = 'CrossAccountS3ReadPolicy'

    try:
        policy_response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        policy_arn = policy_response['Policy']['Arn']

    except iam.exceptions.EntityAlreadyExistsException:
        account_id = boto3.client('sts').get_caller_identity()['Account']
        policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy_arn
    )

    print(f"✓ Attached S3 read policy to {role_name}")


def test_assume_role(role_arn, external_id):
    """Test assuming the cross-account role"""

    sts = boto3.client('sts')

    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName='test-session',
            ExternalId=external_id,
            DurationSeconds=3600
        )

        print("\n✓ Successfully assumed role")
        print(f"  Access Key: {response['Credentials']['AccessKeyId']}")
        print(f"  Session Token: {response['Credentials']['SessionToken'][:50]}...")
        print(f"  Expiration: {response['Credentials']['Expiration']}")

        return response['Credentials']

    except Exception as e:
        print(f"\n✗ Failed to assume role: {e}")
        return None


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--trusted-account', required=True,
                       help='AWS account ID to trust')
    parser.add_argument('--external-id', required=True,
                       help='External ID for added security')

    args = parser.parse_args()

    print("="*60)
    print("SETUP CROSS-ACCOUNT ACCESS")
    print("="*60)

    # Create role
    role_arn = create_cross_account_role(
        args.trusted_account,
        args.external_id
    )

    # Attach policies
    attach_s3_read_policy('CrossAccountDataAccess')

    # Test
    print("\nTesting role assumption:")
    test_assume_role(role_arn, args.external_id)

    print("\n" + "="*60)
    print("✓ CROSS-ACCOUNT ACCESS CONFIGURED")
    print("="*60)
```

## Task 5: IAM Access Analyzer (30 minutes)

**File**: `analyze_policies.py`

```python
#!/usr/bin/env python3
"""Analyze IAM policies with Access Analyzer"""

import boto3
import json
from datetime import datetime

accessanalyzer = boto3.client('accessanalyzer')
iam = boto3.client('iam')


def create_analyzer():
    """Create IAM Access Analyzer"""

    analyzer_name = 'DataSecurityAnalyzer'

    try:
        response = accessanalyzer.create_analyzer(
            analyzerName=analyzer_name,
            type='ACCOUNT',
            tags={'Environment': 'dev', 'Purpose': 'security'}
        )
        print(f"✓ Created analyzer: {analyzer_name}")
        print(f"  ARN: {response['arn']}")

        return response['arn']

    except accessanalyzer.exceptions.ConflictException:
        print(f"  Analyzer already exists: {analyzer_name}")
        analyzers = accessanalyzer.list_analyzers()['analyzers']
        for analyzer in analyzers:
            if analyzer['name'] == analyzer_name:
                return analyzer['arn']


def validate_policy(policy_document, policy_type='IDENTITY_POLICY'):
    """Validate IAM policy"""

    print(f"\nValidating policy:")

    try:
        response = accessanalyzer.validate_policy(
            policyDocument=json.dumps(policy_document),
            policyType=policy_type
        )

        findings = response.get('findings', [])

        if not findings:
            print("  ✓ No issues found")
            return True

        print(f"  Found {len(findings)} issue(s):")
        for finding in findings:
            severity = finding.get('findingType', 'UNKNOWN')
            message = finding.get('issueCode', 'No message')
            print(f"    [{severity}] {message}")

            if 'learnMoreLink' in finding:
                print(f"      Learn more: {finding['learnMoreLink']}")

        return len(findings) == 0

    except Exception as e:
        print(f"  ✗ Validation error: {e}")
        return False


def analyze_all_roles():
    """Analyze all IAM roles"""

    print("\nAnalyzing IAM Roles:")
    print("="*60)

    roles = iam.list_roles()['Roles']

    for role in roles:
        role_name = role['RoleName']

        # Skip AWS service roles
        if role_name.startswith('AWS'):
            continue

        print(f"\n{role_name}:")

        # Get attached policies
        attached_policies = iam.list_attached_role_policies(
            RoleName=role_name
        )['AttachedPolicies']

        for policy in attached_policies:
            print(f"  Attached Policy: {policy['PolicyName']}")

            # Get policy document
            policy_arn = policy['PolicyArn']
            policy_version = iam.get_policy(PolicyArn=policy_arn)['Policy']['DefaultVersionId']
            policy_doc = iam.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=policy_version
            )['PolicyVersion']['Document']

            # Validate
            validate_policy(policy_doc)


def check_external_access():
    """Check for external access findings"""

    print("\nChecking for External Access:")
    print("="*60)

    try:
        analyzers = accessanalyzer.list_analyzers()['analyzers']

        for analyzer in analyzers:
            analyzer_arn = analyzer['arn']

            findings = accessanalyzer.list_findings(
                analyzerArn=analyzer_arn,
                filter={
                    'status': {'eq': ['ACTIVE']}
                }
            )['findings']

            if not findings:
                print("✓ No external access findings")
                continue

            print(f"\nFound {len(findings)} finding(s):")

            for finding in findings:
                print(f"\n  Resource: {finding.get('resource', 'Unknown')}")
                print(f"  Type: {finding.get('resourceType', 'Unknown')}")
                print(f"  External Principal: {finding.get('principal', {}).get('AWS', 'Unknown')}")
                print(f"  Action: {finding.get('action', [])}")
                print(f"  Condition: {finding.get('condition', {})}")

    except Exception as e:
        print(f"✗ Error checking findings: {e}")


if __name__ == '__main__':
    print("="*60)
    print("IAM ACCESS ANALYZER")
    print("="*60)

    # Create analyzer
    create_analyzer()

    # Analyze roles
    analyze_all_roles()

    # Check external access
    check_external_access()

    print("\n" + "="*60)
    print("✓ ANALYSIS COMPLETE")
    print("="*60)
```

## Task 6: Service Control Policies (30 minutes)

**File**: `scp_deny_unencrypted_s3.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedS3Uploads",
      "Effect": "Deny",
      "Action": "s3:PutObject",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": [
            "aws:kms",
            "AES256"
          ]
        }
      }
    },
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": "*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

## Validation Checklist

- [ ] All 3 persona policies created (Engineer, Scientist, Analyst)
- [ ] IAM roles created successfully
- [ ] Permission boundaries applied
- [ ] Cross-account role configured
- [ ] IAM Access Analyzer findings reviewed
- [ ] No overly permissive policies detected
- [ ] All policies follow least privilege
- [ ] External access properly restricted

## Expected Results

**IAM Roles Created**:
- DataEngineerRole (full Glue/EMR access)
- DataScientistRole (Athena/Redshift/SageMaker)
- DataAnalystRole (QuickSight/read-only)

**Permission Boundary Applied**: Limits maximum permissions

**Cross-Account Access**: Secure role for external account

## Troubleshooting

### Problem: Policy validation fails

```python
# Check policy syntax
import json

with open('policies/data-engineer-policy.json') as f:
    policy = json.load(f)
    print(json.dumps(policy, indent=2))
```

### Problem: Cannot assume role

Check trust policy and external ID:
```bash
aws iam get-role --role-name DataEngineerRole

# Test assume role
aws sts assume-role \
    --role-arn arn:aws:iam::ACCOUNT:role/DataEngineerRole \
    --role-session-name test \
    --external-id data-engineer-access
```

## Key Learnings

1. **Least Privilege**: Grant only necessary permissions
2. **Permission Boundaries**: Enforce maximum permissions limit
3. **External ID**: Prevents confused deputy problem
4. **Access Analyzer**: Automated policy validation
5. **Service Control Policies**: Organization-wide guardrails

## Next Steps

- **Exercise 02**: Implement data encryption
- **Advanced**: Implement attribute-based access control (ABAC)
- **Production**: Integrate with CI/CD for policy testing

## Resources

- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Permission Boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
