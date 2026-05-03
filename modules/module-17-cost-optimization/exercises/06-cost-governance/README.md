# Exercise 06: Cost Governance and Automation

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
💰 **Potential Savings:** 15-30% through proactive controls

## Learning Objectives

- Implement AWS Budgets with automated actions
- Create automated resource cleanup policies
- Build cost anomaly alerts with SNS
- Design Service Control Policies (SCPs) for cost limits
- Establish FinOps dashboard and KPIs

## Cost Governance Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Cost Governance Framework                   │
│                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │   Budgets    │  │  Anomaly    │  │   Automated    │ │
│  │   & Alerts   │  │  Detection  │  │    Cleanup     │ │
│  │              │  │             │  │                │ │
│  │  Threshold   │  │  ML-based   │  │  Lambda cron   │ │
│  │  Monitoring  │  │  Alerts     │  │  Idle resource │ │
│  └──────┬───────┘  └──────┬──────┘  └───────┬────────┘ │
│         │                 │                  │          │
│         ▼                 ▼                  ▼          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              SNS → Email/Slack                     │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                              │
│                          ▼                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Budget Actions (Automated Response)        │ │
│  │  • Stop dev/test EC2 instances                     │ │
│  │  • Deny new resource creation (IAM policy)         │ │
│  │  • Scale down Auto Scaling groups                  │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Create AWS Budgets with Actions

**Objective**: Set up proactive cost controls with automated responses.

**Steps**:

1. **Create monthly budget with alerts**:

```python
import boto3
import json

budgets = boto3.client('budgets')
account_id = boto3.client('sts').get_caller_identity()['Account']

def create_monthly_budget(budget_amount, alert_emails):
    """
    Create monthly budget with multiple alert thresholds
    """
    budget_name = f'Monthly-AWS-Budget-{budget_amount}'

    budget = {
        'BudgetName': budget_name,
        'BudgetLimit': {
            'Amount': str(budget_amount),
            'Unit': 'USD'
        },
        'TimeUnit': 'MONTHLY',
        'BudgetType': 'COST',
        'CostFilters': {},
        'CostTypes': {
            'IncludeTax': True,
            'IncludeSubscription': True,
            'UseBlended': False,
            'IncludeRefund': False,
            'IncludeCredit': False,
            'IncludeUpfront': True,
            'IncludeRecurring': True,
            'IncludeOtherSubscription': True,
            'IncludeSupport': True,
            'IncludeDiscount': True,
            'UseAmortized': False
        }
    }

    # Create budget
    budgets.create_budget(
        AccountId=account_id,
        Budget=budget
    )

    print(f"✓ Budget created: {budget_name}")
    print(f"  Amount: ${budget_amount}/month")

    # Create alert thresholds: 80%, 100%, 120%
    thresholds = [
        (80, 'ACTUAL', 'WARNING: 80% budget consumed'),
        (100, 'ACTUAL', 'ALERT: Budget exceeded'),
        (120, 'ACTUAL', 'CRITICAL: 120% over budget'),
        (100, 'FORECASTED', 'FORECAST: Projected to exceed budget')
    ]

    for threshold_pct, comparison, description in thresholds:
        notification = {
            'NotificationType': comparison,
            'ComparisonOperator': 'GREATER_THAN',
            'Threshold': threshold_pct,
            'ThresholdType': 'PERCENTAGE',
            'NotificationState': 'ALARM'
        }

        subscribers = [
            {'SubscriptionType': 'EMAIL', 'Address': email}
            for email in alert_emails
        ]

        budgets.create_notification(
            AccountId=account_id,
            BudgetName=budget_name,
            Notification=notification,
            Subscribers=subscribers
        )

        print(f"  ✓ Alert: {threshold_pct}% threshold ({comparison})")

# Create budget
create_monthly_budget(
    budget_amount=5000,
    alert_emails=['devops@company.com', 'finance@company.com']
)
```

2. **Create budget with automated actions**:

```python
# Budget action: Stop EC2 instances in dev when 90% budget reached
def create_budget_action(budget_name, action_threshold=90):
    """
    Create budget action to automatically stop dev instances
    """
    # IAM role for budget actions
    iam = boto3.client('iam')

    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "budgets.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    # Create role
    role_name = 'BudgetActionRole'
    try:
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description='Role for AWS Budget automated actions'
        )
        role_arn = role_response['Role']['Arn']

        # Attach policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonEC2FullAccess'
        )

        print(f"✓ IAM role created: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'
        print(f"  Role already exists: {role_name}")

    # Create budget action: Stop dev EC2 instances
    action_config = {
        'ActionType': 'APPLY_IAM_POLICY',
        'ActionThreshold': {
            'ActionThresholdValue': action_threshold,
            'ActionThresholdType': 'PERCENTAGE'
        },
        'Definition': {
            'IamActionDefinition': {
                'PolicyArn': 'arn:aws:iam::aws:policy/AWSBudgetsActions_EC2DenyRunningInstances',
                'Roles': [role_arn],
                'Groups': [],
                'Users': []
            }
        },
        'ExecutionRoleArn': role_arn,
        'ApprovalModel': 'AUTOMATIC',  # or 'MANUAL' for approval required
        'NotificationType': 'ACTUAL',
        'SubscriberArns': [f'arn:aws:sns:us-east-1:{account_id}:budget-alerts']
    }

    response = budgets.create_budget_action(
        AccountId=account_id,
        BudgetName=budget_name,
        **action_config
    )

    print(f"\n✓ Budget Action Created:")
    print(f"  Trigger: {action_threshold}% of budget")
    print(f"  Action: Deny launching new EC2 instances")
    print(f"  Approval: Automatic")
    print(f"\n  ⚠️  Use carefully in production!")

# Create action (example - modify for your needs)
# create_budget_action('Monthly-AWS-Budget-5000', action_threshold=90)
```

### Task 2: Automated Resource Cleanup

**Objective**: Build Lambda function to clean up unused resources.

**Steps**:

1. **Create cleanup Lambda function**:

```python
# Lambda function code: cleanup_unused_resources.py
import boto3
from datetime import datetime, timedelta, timezone

ec2 = boto3.client('ec2')
rds = boto3.client('rds')

def lambda_handler(event, context):
    """
    Identify and stop/delete unused resources

    Runs daily via EventBridge cron: cron(0 2 * * ? *)
    """
    cleanup_summary = {
        'stopped_instances': [],
        'deleted_volumes': [],
        'deleted_snapshots': [],
        'stopped_databases': [],
        'total_savings': 0
    }

    # 1. Stop idle EC2 instances (CPU < 5% for 7 days)
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Environment', 'Values': ['dev', 'test']}  # Only dev/test
        ]
    )

    cloudwatch = boto3.client('cloudwatch')

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']

            # Check CPU last 7 days
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.now(timezone.utc) - timedelta(days=7),
                EndTime=datetime.now(timezone.utc),
                Period=86400,  # Daily
                Statistics=['Average']
            )

            if response['Datapoints']:
                avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])

                if avg_cpu < 5:
                    # Idle instance - stop it
                    ec2.stop_instances(InstanceIds=[instance_id])

                    # Estimate savings (assume m5.large ~ $70/month)
                    estimated_savings = 70  # Simplified
                    cleanup_summary['stopped_instances'].append({
                        'instance_id': instance_id,
                        'instance_type': instance_type,
                        'avg_cpu': avg_cpu,
                        'savings': estimated_savings
                    })
                    cleanup_summary['total_savings'] += estimated_savings

    # 2. Delete unattached EBS volumes (older than 30 days)
    volumes = ec2.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )

    for volume in volumes['Volumes']:
        volume_id = volume['VolumeId']
        create_time = volume['CreateTime']
        size_gb = volume['Size']

        age_days = (datetime.now(timezone.utc) - create_time).days

        if age_days > 30:
            # Delete old unattached volume
            # Uncomment to actually delete (DRY RUN mode)
            # ec2.delete_volume(VolumeId=volume_id)

            monthly_savings = size_gb * 0.10  # $0.10/GB-month for gp3
            cleanup_summary['deleted_volumes'].append({
                'volume_id': volume_id,
                'size_gb': size_gb,
                'age_days': age_days,
                'savings': monthly_savings
            })
            cleanup_summary['total_savings'] += monthly_savings

    # 3. Delete old snapshots (> 90 days, not tagged as "Keep")
    snapshots = ec2.describe_snapshots(OwnerIds=[context.invoked_function_arn.split(':')[4]])

    for snapshot in snapshots['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        start_time = snapshot['StartTime']
        age_days = (datetime.now(timezone.utc) - start_time).days

        # Check for "Keep" tag
        tags = {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}

        if age_days > 90 and tags.get('Keep') != 'true':
            # Delete old snapshot
            # ec2.delete_snapshot(SnapshotId=snapshot_id)

            # Estimate savings (avg snapshot ~50GB)
            estimated_savings = 50 * 0.05  # $0.05/GB-month
            cleanup_summary['deleted_snapshots'].append({
                'snapshot_id': snapshot_id,
                'age_days': age_days,
                'savings': estimated_savings
            })
            cleanup_summary['total_savings'] += estimated_savings

    # 4. Stop idle RDS instances (dev/test only)
    db_instances = rds.describe_db_instances()

    for db in db_instances['DBInstances']:
        db_id = db['DBInstanceIdentifier']
        tags = {tag['Key']: tag['Value'] for tag in db.get('TagList', [])}

        if tags.get('Environment') in ['dev', 'test']:
            # Check connections last 7 days
            conn_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=datetime.now(timezone.utc) - timedelta(days=7),
                EndTime=datetime.now(timezone.utc),
                Period=86400,
                Statistics=['Average']
            )

            if conn_response['Datapoints']:
                avg_connections = sum(dp['Average'] for dp in conn_response['Datapoints']) / len(conn_response['Datapoints'])

                if avg_connections < 1:
                    # No connections - stop database
                    rds.stop_db_instance(DBInstanceIdentifier=db_id)

                    estimated_savings = 100  # Simplified
                    cleanup_summary['stopped_databases'].append({
                        'db_id': db_id,
                        'avg_connections': avg_connections,
                        'savings': estimated_savings
                    })
                    cleanup_summary['total_savings'] += estimated_savings

    # Summary report
    print(f"\n🧹 Cleanup Summary:")
    print(f"  Stopped Instances: {len(cleanup_summary['stopped_instances'])}")
    print(f"  Deleted Volumes: {len(cleanup_summary['deleted_volumes'])}")
    print(f"  Deleted Snapshots: {len(cleanup_summary['deleted_snapshots'])}")
    print(f"  Stopped Databases: {len(cleanup_summary['stopped_databases'])}")
    print(f"\n💰 Estimated Monthly Savings: ${cleanup_summary['total_savings']:.2f}")

    return cleanup_summary

# Deploy as Lambda function with EventBridge trigger
# Schedule: Daily at 2 AM UTC
```

2. **Deploy cleanup Lambda**:

```python
# Deploy the cleanup function
lambda_client = boto3.client('lambda')
events = boto3.client('events')
iam = boto3.client('iam')

# Create IAM role for Lambda
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role_name = 'CostCleanupLambdaRole'
try:
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    role_arn = role_response['Role']['Arn']

    # Attach policies
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess')

    # Custom policy for stop/delete actions
    cleanup_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ec2:StopInstances",
                "ec2:DeleteVolume",
                "ec2:DeleteSnapshot",
                "rds:StopDBInstance"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/Environment": ["dev", "test"]
                }
            }
        }]
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='CleanupActions',
        PolicyDocument=json.dumps(cleanup_policy)
    )

    print(f"✓ IAM role created: {role_name}")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'

# Create Lambda function (assumes code is in lambda_function.zip)
# lambda_response = lambda_client.create_function(
#     FunctionName='cost-cleanup-automation',
#     Runtime='python3.11',
#     Role=role_arn,
#     Handler='lambda_function.lambda_handler',
#     Code={'ZipFile': open('cleanup_lambda.zip', 'rb').read()},
#     Timeout=300,
#     MemorySize=256
# )

print(f"✓ Lambda function deployed: cost-cleanup-automation")

# Create EventBridge rule (daily at 2 AM UTC)
rule_response = events.put_rule(
    Name='daily-cost-cleanup',
    ScheduleExpression='cron(0 2 * * ? *)',
    State='ENABLED',
    Description='Run cost cleanup automation daily'
)

# Add Lambda as target
events.put_targets(
    Rule='daily-cost-cleanup',
    Targets=[{
        'Id': '1',
        'Arn': f'arn:aws:lambda:us-east-1:{account_id}:function:cost-cleanup-automation'
    }]
)

print(f"✓ EventBridge rule created: daily-cost-cleanup (daily 2 AM UTC)")
```

### Task 2: Implement Service Control Policies (SCPs)

**Objective**: Prevent costly resource creation at organization level.

**Steps**:

```python
organizations = boto3.client('organizations')

# SCP Example 1: Deny expensive instance types
deny_expensive_instances_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "DenyExpensiveEC2",
        "Effect": "Deny",
        "Action": [
            "ec2:RunInstances",
            "ec2:StartInstances"
        ],
        "Resource": "arn:aws:ec2:*:*:instance/*",
        "Condition": {
            "StringLike": {
                "ec2:InstanceType": [
                    "*.8xlarge",
                    "*.16xlarge",
                    "*.24xlarge",
                    "*.metal"
                ]
            }
        }
    }]
}

# SCP Example 2: Deny resource creation outside allowed regions
deny_non_approved_regions_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "DenyNonApprovedRegions",
        "Effect": "Deny",
        "Action": [
            "ec2:RunInstances",
            "rds:CreateDBInstance",
            "s3:CreateBucket"
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
    }]
}

# SCP Example 3: Require cost allocation tags
require_tags_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "RequireCostAllocationTags",
        "Effect": "Deny",
        "Action": [
            "ec2:RunInstances",
            "rds:CreateDBInstance"
        ],
        "Resource": "*",
        "Condition": {
            "StringNotLike": {
                "aws:RequestTag/CostCenter": "*"
            }
        }
    }]
}

print("\n📋 Service Control Policy Examples:\n")
print("1. Deny Expensive Instances:")
print("   Prevents *.8xlarge, *.16xlarge, *.24xlarge, *.metal")
print("   Estimated Prevention: $5,000-50,000/month accidental launches")
print("\n2. Region Restrictions:")
print("   Only allow us-east-1, us-west-2")
print("   Prevents shadow IT and reduces complexity")
print("\n3. Required Cost Tags:")
print("   Must have CostCenter tag on EC2/RDS")
print("   Ensures proper cost attribution")

# Note: Applying SCPs requires AWS Organizations
# organizations.create_policy(
#     Content=json.dumps(deny_expensive_instances_policy),
#     Description='Prevent expensive instance types',
#     Name='DenyExpensiveInstances',
#     Type='SERVICE_CONTROL_POLICY'
# )
```

### Task 3: Cost Anomaly Detection Dashboard

**Objective**: Build real-time cost monitoring dashboard.

**Steps**:

1. **Query cost anomalies**:

```python
ce = boto3.client('ce')

def get_cost_anomalies(days=30):
    """Retrieve detected cost anomalies"""
    response = ce.get_anomalies(
        DateInterval={
            'StartDate': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
            'EndDate': datetime.now().strftime('%Y-%m-%d')
        },
        MaxResults=100
    )

    anomalies = response.get('Anomalies', [])

    print(f"\n🚨 Cost Anomalies (Last {days} Days):\n")

    if not anomalies:
        print("  ✓ No anomalies detected")
        return []

    for anomaly in anomalies:
        anomaly_id = anomaly['AnomalyId']
        impact = anomaly['Impact']

        total_impact = float(impact['TotalImpact'])
        max_impact = float(impact['MaxImpact'])

        # Root causes
        root_causes = anomaly.get('RootCauses', [])
        service = root_causes[0].get('Service', 'Unknown') if root_causes else 'Unknown'

        # Date
        start_date = anomaly['AnomalyStartDate']

        print(f"  Anomaly: {anomaly_id}")
        print(f"    Date: {start_date}")
        print(f"    Service: {service}")
        print(f"    Impact: ${total_impact:,.2f} (${max_impact:,.2f} max)")
        print(f"    Status: {anomaly['AnomalyScore']['CurrentScore']:.0f}% confidence")
        print()

    return anomalies

anomalies = get_cost_anomalies(days=30)
```

2. **Create cost governance dashboard**:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def create_governance_dashboard(budget_data, anomalies, cleanup_summary):
    """Create comprehensive cost governance dashboard"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Cost Governance Dashboard', fontsize=18, fontweight='bold')

    # 1. Budget consumption
    budget_consumed_pct = (budget_data['current_spend'] / budget_data['budget_amount']) * 100

    axes[0, 0].barh(['Budget\nConsumption'], [budget_consumed_pct], color='green' if budget_consumed_pct < 80 else 'orange' if budget_consumed_pct < 100 else 'red')
    axes[0, 0].set_xlim(0, 120)
    axes[0, 0].axvline(x=80, color='orange', linestyle='--', alpha=0.5, label='80% Warning')
    axes[0, 0].axvline(x=100, color='red', linestyle='--', alpha=0.5, label='100% Limit')
    axes[0, 0].set_xlabel('Percentage')
    axes[0, 0].set_title(f'Budget Status: {budget_consumed_pct:.1f}% (${budget_data["current_spend"]:,.0f}/${budget_data["budget_amount"]:,.0f})')
    axes[0, 0].legend()

    # 2. Anomaly timeline
    if anomalies:
        anomaly_dates = [a['AnomalyStartDate'] for a in anomalies]
        anomaly_impacts = [float(a['Impact']['TotalImpact']) for a in anomalies]

        axes[0, 1].scatter(range(len(anomalies)), anomaly_impacts, s=100, color='red', alpha=0.6)
        axes[0, 1].set_title(f'Cost Anomalies: {len(anomalies)} detected')
        axes[0, 1].set_ylabel('Impact ($)')
        axes[0, 1].set_xlabel('Anomaly Index')
        axes[0, 1].grid(True, alpha=0.3)
    else:
        axes[0, 1].text(0.5, 0.5, 'No Anomalies\nDetected ✓',
                       ha='center', va='center', fontsize=16, color='green')
        axes[0, 1].set_title('Cost Anomalies')
        axes[0, 1].axis('off')

    # 3. Cleanup savings
    cleanup_categories = ['Stopped\nInstances', 'Deleted\nVolumes', 'Deleted\nSnapshots', 'Stopped\nDatabases']
    cleanup_savings = [
        sum(i['savings'] for i in cleanup_summary['stopped_instances']),
        sum(v['savings'] for v in cleanup_summary['deleted_volumes']),
        sum(s['savings'] for s in cleanup_summary['deleted_snapshots']),
        sum(d['savings'] for d in cleanup_summary['stopped_databases'])
    ]

    axes[1, 0].bar(cleanup_categories, cleanup_savings, color='skyblue', edgecolor='black')
    axes[1, 0].set_title(f'Automated Cleanup Savings: ${sum(cleanup_savings):.2f}/month')
    axes[1, 0].set_ylabel('Monthly Savings ($)')
    axes[1, 0].grid(axis='y', alpha=0.3)

    # 4. Cost by category
    cost_categories = ['Compute', 'Storage', 'Database', 'Networking', 'Other']
    cost_values = budget_data['cost_by_category']

    axes[1, 1].pie(cost_values, labels=cost_categories, autopct='%1.1f%%', startangle=90)
    axes[1, 1].set_title('Cost Distribution by Category')

    plt.tight_layout()
    plt.savefig('cost-governance-dashboard.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Dashboard saved: cost-governance-dashboard.png")

# Example usage
budget_data = {
    'budget_amount': 5000,
    'current_spend': 4200,
    'cost_by_category': [2100, 800, 900, 300, 100]  # Compute, Storage, DB, Network, Other
}

cleanup_summary = {
    'stopped_instances': [{'savings': 70}, {'savings': 140}],
    'deleted_volumes': [{'savings': 20}, {'savings': 15}],
    'deleted_snapshots': [{'savings': 10}],
    'stopped_databases': [{'savings': 100}]
}

create_governance_dashboard(budget_data, anomalies, cleanup_summary)
```

### Task 4: Build FinOps KPI Dashboard

**Objective**: Track key cost optimization metrics over time.

**Steps**:

```python
class FinOpsKPICalculator:
    """Calculate FinOps key performance indicators"""

    def __init__(self, ce_client):
        self.ce = ce_client

    def calculate_unit_economics(self, metric_name, metric_value, cost):
        """Calculate cost per unit (e.g., cost per user, per transaction)"""
        unit_cost = cost / metric_value if metric_value > 0 else 0
        return unit_cost

    def calculate_cost_optimization_kpis(self):
        """Calculate standard FinOps KPIs"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        kpis = {}

        # 1. Commitment Coverage (RI + SP)
        coverage = self.ce.get_reservation_coverage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY'
        )

        covered_pct = float(coverage['CoveragesByTime'][0]['Total']['CoverageHours']['CoverageHoursPercentage'])
        kpis['commitment_coverage'] = covered_pct

        # 2. Commitment Utilization
        utilization = self.ce.get_reservation_utilization(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY'
        )

        util_pct = float(utilization['UtilizationsByTime'][0]['Total']['UtilizationPercentage'])
        kpis['commitment_utilization'] = util_pct

        # 3. Untagged Resources Percentage
        # Get costs with and without tags
        tagged_response = self.ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={
                'Tags': {
                    'Key': 'CostCenter',
                    'Values': ['*']
                }
            }
        )

        total_response = self.ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )

        tagged_cost = float(tagged_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        total_cost = float(total_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

        untagged_pct = ((total_cost - tagged_cost) / total_cost) * 100 if total_cost > 0 else 0
        kpis['untagged_resources_pct'] = untagged_pct

        # 4. Month-over-Month Growth
        prev_month_start = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        prev_month_end = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        prev_response = self.ce.get_cost_and_usage(
            TimePeriod={'Start': prev_month_start, 'End': prev_month_end},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )

        prev_cost = float(prev_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        current_month_cost = float(total_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

        mom_growth = ((current_month_cost - prev_cost) / prev_cost) * 100 if prev_cost > 0 else 0
        kpis['mom_growth_pct'] = mom_growth

        # 5. Waste Ratio (idle resources)
        # Simplified: Assume cleanup savings represent waste
        kpis['waste_ratio_pct'] = 15  # Placeholder - would calculate from actual cleanup

        return kpis

    def display_kpi_dashboard(self, kpis):
        """Display FinOps KPIs"""
        print("\n" + "="*60)
        print("           FINOPS KEY PERFORMANCE INDICATORS")
        print("="*60)

        # KPI 1: Commitment Coverage
        print(f"\n1. Commitment Coverage: {kpis['commitment_coverage']:.1f}%")
        if kpis['commitment_coverage'] < 70:
            print(f"   ⚠️  Target: >70% (Opportunity for RI/SP)")
        else:
            print(f"   ✓ Good coverage")

        # KPI 2: Commitment Utilization
        print(f"\n2. Commitment Utilization: {kpis['commitment_utilization']:.1f}%")
        if kpis['commitment_utilization'] < 80:
            print(f"   ⚠️  Target: >80% (Reduce commitments or increase usage)")
        else:
            print(f"   ✓ High utilization")

        # KPI 3: Untagged Resources
        print(f"\n3. Untagged Resources: {kpis['untagged_resources_pct']:.1f}%")
        if kpis['untagged_resources_pct'] > 10:
            print(f"   ⚠️  Target: <5% (Improve tagging compliance)")
        else:
            print(f"   ✓ Good tagging hygiene")

        # KPI 4: MoM Growth
        print(f"\n4. Month-over-Month Growth: {kpis['mom_growth_pct']:+.1f}%")
        if kpis['mom_growth_pct'] > 20:
            print(f"   ⚠️  High growth - Investigate drivers")
        elif kpis['mom_growth_pct'] < 0:
            print(f"   ✓ Cost reduction achieved!")
        else:
            print(f"   ✓ Controlled growth")

        # KPI 5: Waste Ratio
        print(f"\n5. Waste Ratio: {kpis['waste_ratio_pct']:.1f}%")
        if kpis['waste_ratio_pct'] > 10:
            print(f"   ⚠️  Target: <10% (Increase cleanup automation)")
        else:
            print(f"   ✓ Efficient resource usage")

        print("\n" + "="*60)

        # Overall health score
        score = 0
        if kpis['commitment_coverage'] >= 70: score += 20
        if kpis['commitment_utilization'] >= 80: score += 20
        if kpis['untagged_resources_pct'] < 5: score += 20
        if -5 < kpis['mom_growth_pct'] < 15: score += 20
        if kpis['waste_ratio_pct'] < 10: score += 20

        print(f"\n🎯 FinOps Maturity Score: {score}/100")

        if score >= 80:
            print(f"   ✓ Excellent - Run state")
        elif score >= 60:
            print(f"   ⭐ Good - Optimize state")
        elif score >= 40:
            print(f"   ⚠️  Fair - Inform state (focus on visibility)")
        else:
            print(f"   ❌ Needs improvement - Establish basics")

# Calculate and display KPIs
ce_client = boto3.client('ce')
kpi_calc = FinOpsKPICalculator(ce_client)
kpis = kpi_calc.calculate_cost_optimization_kpis()
kpi_calc.display_kpi_dashboard(kpis)
```

### Task 5: Slack/Email Cost Alerts Integration

**Objective**: Send cost alerts to team communication channels.

**Steps**:

```python
# Lambda function: Send cost alerts to Slack
import json
import urllib3

http = urllib3.PoolManager()

def send_slack_alert(webhook_url, message, severity='warning'):
    """Send cost alert to Slack"""

    colors = {
        'info': '#36a64f',      # Green
        'warning': '#ff9900',   # Orange
        'critical': '#ff0000'   # Red
    }

    slack_message = {
        'attachments': [{
            'color': colors.get(severity, '#808080'),
            'title': '💰 AWS Cost Alert',
            'text': message,
            'footer': 'AWS Cost Governance',
            'ts': int(datetime.now().timestamp())
        }]
    }

    response = http.request(
        'POST',
        webhook_url,
        body=json.dumps(slack_message),
        headers={'Content-Type': 'application/json'}
    )

    return response.status == 200

# Example alerts
def lambda_handler(event, context):
    """Process budget or anomaly alert and forward to Slack"""

    webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

    # Parse SNS message from Budget or Cost Anomaly Detection
    message = json.loads(event['Records'][0]['Sns']['Message'])

    if 'budgetName' in message:
        # Budget alert
        budget_name = message['budgetName']
        current = float(message['currentSpend'])
        limit = float(message['budgetLimit'])
        pct = (current / limit) * 100

        alert_message = f"""
*Budget Alert: {budget_name}*
Current Spend: ${current:,.2f} / ${limit:,.2f} ({pct:.1f}%)
Status: {'⚠️ Over budget' if pct > 100 else '⚠️ Approaching limit'}

Action Required: Review and optimize costs
"""

        severity = 'critical' if pct > 100 else 'warning'
        send_slack_alert(webhook_url, alert_message, severity)

    elif 'anomalyId' in message:
        # Cost anomaly
        service = message.get('service', 'Unknown')
        impact = float(message.get('totalImpact', 0))

        alert_message = f"""
*Cost Anomaly Detected*
Service: {service}
Impact: ${impact:,.2f}
Confidence: High

Investigate immediately: Unusual spending pattern detected
"""

        send_slack_alert(webhook_url, alert_message, 'warning')

    return {'statusCode': 200}
```

## Validation Checklist

- [ ] Created AWS Budget with 3+ alert thresholds
- [ ] Configured budget actions (at least dry-run mode)
- [ ] Deployed automated cleanup Lambda function
- [ ] Scheduled cleanup to run daily
- [ ] Tested cost anomaly detection alerts
- [ ] Implemented at least 1 Service Control Policy (if using Organizations)
- [ ] Built FinOps KPI dashboard with 5+ metrics
- [ ] Integrated cost alerts with Slack/email

## Troubleshooting

**Issue**: Budget alerts not sending
- **Solution**: Verify SNS subscription confirmed
- Check SNS topic permissions
- Ensure budget notification thresholds are correct

**Issue**: Budget action not executing
- **Solution**: Check IAM role permissions for budget actions
- Verify approval model (AUTOMATIC vs MANUAL)
- Test with lower threshold first

**Issue**: Cleanup Lambda failed to stop resources
- **Solution**: Add proper IAM permissions (ec2:StopInstances)
- Use resource tags to scope permissions (Environment=dev)
- Check CloudWatch Logs for detailed error

**Issue**: SCP blocking legitimate actions
- **Solution**: Test SCPs in non-production OU first
- Add exception for specific roles/users
- Use Condition keys to allow based on tags

## Key Learnings

✅ **Budgets**: Forecasted alerts prevent surprises 2-3 weeks early
✅ **Automation**: Daily cleanup saves 10-20% without manual effort
✅ **SCPs**: Organization-level guardrails better than account-level policies
✅ **KPIs**: Track 5 key metrics (coverage, utilization, tagging, growth, waste)
✅ **Alerts**: Real-time Slack notifications reduce response time from days to hours

## FinOps Maturity Model

### Level 1: **Inform** (Visibility)
- Cost Explorer enabled ✓
- Basic tagging (>50% coverage)
- Monthly cost reports
- **Time**: 1-3 months

### Level 2: **Optimize** (Efficiency)
- RI/SP coverage >60%
- Lifecycle policies implemented
- Right-sizing recommendations applied
- **Time**: 3-6 months

### Level 3: **Operate** (Continuous Improvement)
- Automated cleanup >80% coverage
- Commitment utilization >85%
- Anomaly detection with auto-remediation
- FinOps culture embedded
- **Time**: 6-12 months

**Your Goal**: Reach Level 3 (Operate) within 6 months

## Cost Governance Best Practices

1. **Budgets**: Set at team/project level, not just account-level
2. **Alerts**: Use forecasted alerts (prevents surprises)
3. **Actions**: Start with notifications, then automate gradually
4. **Cleanup**: Run daily, target dev/test first
5. **SCPs**: Test in sandbox OU before production
6. **Dashboards**: Real-time visibility for entire organization
7. **Reviews**: Monthly FinOps meetings with engineering teams

## Real-World Implementation

**Company**: 200-person engineering org, $50K/month AWS spend

**Governance Measures Implemented**:
1. **Budgets**: Team-level budgets ($5K each, 10 teams)
2. **Cleanup**: Daily Lambda (saves $3K/month on idle resources)
3. **SCPs**: Deny >4xlarge instances, require tags
4. **Alerts**: Slack notifications (90% of team sees alerts)
5. **KPIs**: Weekly dashboard review

**Results After 6 Months**:
- Untagged resources: 40% → 3%
- Commitment coverage: 45% → 78%
- Waste ratio: 22% → 8%
- Monthly savings: $12K (24% reduction)
- Engineering time: 2 hours/week (down from 8 hours/week firefighting)

**ROI**:
- Implementation: 120 hours ($12K)
- Annual savings: $144K
- Payback: 1 month
- 3-year ROI: 3,500%

## Automation Examples

### 1. Stop Dev Instances Nightly
```bash
# Lambda function triggered by EventBridge
# cron(0 20 * * ? *) - 8 PM daily
aws ec2 stop-instances --instance-ids $(aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=dev" "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].InstanceId" --output text)
```

### 2. Delete Old Snapshots
```bash
# Delete snapshots older than 90 days (without "Keep" tag)
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[?StartTime<='$(date -d '90 days ago' --iso-8601)'] | [?!Tags || !contains(Tags[?Key=='Keep'].Value, 'true')].[SnapshotId]" \
  --output text | xargs -n1 aws ec2 delete-snapshot --snapshot-id
```

### 3. Right-Size Underutilized Instances
```python
# Weekly check: Flag instances with CPU < 20% for 7 days
# Send recommendations to Slack
# Auto-resize after 14 days of low utilization (with approval)
```

## Next Steps

Congratulations! You've completed all 6 cost optimization exercises:
1. ✅ Cost analysis and visibility
2. ✅ S3 storage optimization
3. ✅ Compute purchasing strategies
4. ✅ Resource right-sizing
5. ✅ Serverless cost analysis
6. ✅ Cost governance automation

**Continue to**:
- **Theory**: FinOps principles and best practices
- **Module 18**: Advanced data architectures
- **Checkpoint**: Enterprise Data Lakehouse project

## Additional Resources

- [AWS Budgets Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Budget Actions Guide](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/)
- [FinOps Foundation](https://www.finops.org/)
- [AWS Well-Architected Cost Optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
- [Cloud FinOps Book](https://www.oreilly.com/library/view/cloud-finops/9781492054610/)
