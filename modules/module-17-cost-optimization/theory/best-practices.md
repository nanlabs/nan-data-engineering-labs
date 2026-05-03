# Cloud Cost Optimization Best Practices

## Introduction

This document provides actionable best practices for cloud cost optimization based on AWS Well-Architected Framework, FinOps principles, and real-world experience.

## AWS Well-Architected Framework: Cost Optimization Pillar

### Five Design Principles

1. **Practice Cloud Financial Management**
   - Dedicated FinOps team or role
   - Regular cost reviews with stakeholders
   - Cost optimization as continuous practice

2. **Adopt a Consumption Model**
   - Pay only for what you use
   - Scale down in non-peak hours
   - Decommission unused resources

3. **Measure Overall Efficiency**
   - Track unit economics (cost per user/transaction)
   - Benchmark against industry standards
   - Set efficiency improvement goals

4. **Stop Spending on Undifferentiated Heavy Lifting**
   - Use managed services (RDS vs self-managed DB)
   - Serverless over EC2 for variable workloads
   - Eliminate toil with automation

5. **Analyze and Attribute Expenditure**
   - Tag all resources (100% compliance)
   - Chargeback to teams/projects
   - Cost-aware engineering culture

## Best Practices by Phase

### 1. Design Phase

**BP-01: Start Small, Scale Based on Data**
- ✅ Begin with t3.small, not m5.4xlarge
- ✅ Use serverless for new workloads (Lambda, Fargate)
- ✅ Monitor for 2-4 weeks before committing to RIs
- ❌ Don't "future-proof" with oversized resources

**BP-02: Choose the Right Pricing Model**
```python
# Decision framework
def recommend_pricing_model(workload_characteristics):
    """Recommend pricing model based on workload"""

    uptime_pct = workload_characteristics['uptime_percentage']
    predictability = workload_characteristics['predictability']  # high, medium, low
    fault_tolerance = workload_characteristics['fault_tolerant']
    flexibility_needed = workload_characteristics['flexibility_needed']

    if uptime_pct > 80 and predictability == 'high':
        if flexibility_needed:
            return 'Compute Savings Plan (60% savings, flexible)'
        else:
            return 'Reserved Instance (75% savings, locked)'

    elif uptime_pct < 20:
        return 'Lambda or Fargate (serverless, pay per use)'

    elif fault_tolerance and uptime_pct < 70:
        return 'Spot Instances (75% savings, interruptible)'

    else:
        return 'On-Demand (0% savings, full flexibility)'

# Example workloads
workloads = [
    {'name': 'Production API', 'uptime_percentage': 95, 'predictability': 'high',
     'fault_tolerant': False, 'flexibility_needed': True},
    {'name': 'Batch ETL', 'uptime_percentage': 15, 'predictability': 'high',
     'fault_tolerant': True, 'flexibility_needed': False},
    {'name': 'Dev Environment', 'uptime_percentage': 40, 'predictability': 'low',
     'fault_tolerant': True, 'flexibility_needed': True},
]

print("\n🎯 Pricing Model Recommendations:\n")
for workload in workloads:
    rec = recommend_pricing_model(workload)
    print(f"  {workload['name']}: {rec}")
```

**BP-03: Design for Multi-Tenancy**
- Share infrastructure across customers (reduce per-customer cost)
- Use resource tagging for per-tenant cost tracking
- Implement fair-use policies

### 2. Development Phase

**BP-04: Tag Everything from Creation**
```python
# Tag on creation (Terraform example)
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server-${var.environment}"
    CostCenter  = var.cost_center
    Team        = var.team
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "Terraform"
    Owner       = var.owner_email
    CreatedAt   = timestamp()
  }
}

# Enforce with policy
data "aws_iam_policy_document" "require_tags" {
  statement {
    effect = "Deny"
    actions = [
      "ec2:RunInstances",
      "rds:CreateDBInstance",
      "s3:CreateBucket"
    ]
    resources = ["*"]

    condition {
      test     = "StringNotLike"
      variable = "aws:RequestTag/CostCenter"
      values   = ["CC-*"]
    }
  }
}
```

**BP-05: Implement Auto-Shutdown for Dev/Test**
```python
# Lambda to stop dev instances nightly
def lambda_handler(event, context):
    """Stop all dev/test instances at night (8 PM)"""
    ec2 = boto3.client('ec2')

    # Find dev/test instances
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Environment', 'Values': ['dev', 'test']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])

    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopped {len(instance_ids)} dev/test instances")

        # Calculate savings: 14 hours/night * 30 days = 420 hours/month
        # 10 instances * 420 hours * $0.096/hour = $403/month saved

    return {'stopped': len(instance_ids)}

# EventBridge schedule: Mon-Fri 8 PM, start at 8 AM
# Runs 14 hours off, saves 14/24 = 58% on dev infrastructure
```

**BP-06: Use Infrastructure as Code**
- Terraform state tracks all resources (no orphans)
- Destroy entire environments easily (`terraform destroy`)
- Consistent tagging via variables

### 3. Testing Phase

**BP-07: Test on Spot/Smaller Instances**
```bash
# CI/CD pipeline on Spot (GitHub Actions example)
runs-on: ec2-spot-runner  # 70% cheaper than on-demand runners

# Use smaller instance types for testing
test:
  instance_type: t3.small  # $0.0208/hour
  # vs c5.2xlarge ($0.34/hour) for tests
```

**BP-08: Clean Up Test Data Automatically**
```python
# Delete test resources after 7 days
lifecycle_rule = {
    'Rules': [{
        'Id': 'delete-test-data',
        'Status': 'Enabled',
        'Filter': {'Prefix': 'test/'},
        'Expiration': {'Days': 7}
    }]
}
```

### 4. Production Phase

**BP-09: Commit to Savings Plans Gradually**
- Month 1-3: Monitor baseline usage
- Month 4: Purchase 50% coverage (1-year SP)
- Month 7: Increase to 70% coverage
- Review quarterly, adjust coverage

**BP-10: Implement Budget Alerts**
```python
# Budget with graduated alerts
BUDGET_ALERTS = [
    {'threshold': 80, 'type': 'ACTUAL', 'action': 'Notify FinOps'},
    {'threshold': 90, 'type': 'ACTUAL', 'action': 'Notify Engineering Lead'},
    {'threshold': 100, 'type': 'ACTUAL', 'action': 'Stop dev instances'},
    {'threshold': 110, 'type': 'ACTUAL', 'action': 'Deny new EC2 launch'},
    {'threshold': 100, 'type': 'FORECASTED', 'action': 'Notify CFO'}
]
```

**BP-11: Enable Cost Anomaly Detection**
- AWS-managed ML service (no cost)
- Detects unusual spending patterns
- Alerts on anomalies >$100 or >20% deviation

## Service-Specific Best Practices

### EC2

**BP-12: Use Latest Generation Instances**
- m6i 20% better price/performance than m5
- Graviton2/3 (ARM) 20-40% cheaper than Intel
- Network-optimized for high throughput

**BP-13: EBS Optimization**
```python
# Right-size EBS volumes
EBS_BEST_PRACTICES = {
    'general_purpose': {
        'type': 'gp3',  # vs gp2, 20% cheaper
        'baseline_iops': 3000,  # Free (vs gp2 scales with size)
        'baseline_throughput': 125,  # MB/s, free
        'cost_per_gb': 0.08
    },
    'sizing': {
        'check_utilization': 'CloudWatch VolumeReadBytes/VolumeWriteBytes',
        'target_utilization': '60-80%',
        'action': 'Resize volumes <40% utilized'
    },
    'snapshots': {
        'retention': 'Keep 7 daily, 4 weekly, delete >90 days',
        'incremental': 'Only changed blocks stored',
        'cost': '$0.05/GB-month'
    }
}
```

**BP-14: Stop Instead of Terminate**
- Stopped instances: No EC2 charge, EBS charge only ($0.08/GB-month)
- Useful for dev/test environments
- Can start quickly when needed

### Lambda

**BP-15: Optimize Memory Allocation**
```python
# Benchmark different memory configs
MEMORY_CONFIG_RESULTS = {
    128: {'duration_ms': 2000, 'cost_per_invocation': 0.0000004167},
    256: {'duration_ms': 1100, 'cost_per_invocation': 0.0000004583},  # Sweet spot
    512: {'duration_ms': 650, 'cost_per_invocation': 0.0000005417},
    1024: {'duration_ms': 400, 'cost_per_invocation': 0.0000006667},
}

# Optimal: 256 MB (not always highest memory)
# More memory = more CPU = faster = lower duration cost
# But memory cost increases, so there's a sweet spot
```

**BP-16: Minimize Cold Starts**
- Keep functions warm with EventBridge (scheduled invocations)
- Use Provisioned Concurrency sparingly (expensive: $0.000004167 per GB-second)
- Reduce deployment package size (faster cold start)

**BP-17: Use ARM/Graviton2 Runtime**
```python
# 20% discount + 19% better performance
lambda_function = {
    'FunctionName': 'my-function',
    'Runtime': 'python3.11',
    'Architectures': ['arm64'],  # vs ['x86_64']
    'MemorySize': 256
}
# Same code, 20% cheaper, 19% faster
```

### S3

**BP-18: Lifecycle Everything**
```python
# Default lifecycle for all buckets
DEFAULT_LIFECYCLE = {
    'Rules': [
        {
            'Id': 'intelligent-tiering',
            'Status': 'Enabled',
            'Transitions': [
                {'Days': 0, 'StorageClass': 'INTELLIGENT_TIERING'}
            ]
        }
    ]
}

# Intelligent-Tiering: $0.0025/1000 objects (monitoring fee)
# Automatic optimization, no retrieval fees
# Best for unknown access patterns
```

**BP-19: Delete Incomplete Multipart Uploads**
```python
# These can accumulate and cost $$ invisibly
lifecycle_rule = {
    'Rules': [{
        'Id': 'delete-incomplete-multipart',
        'Status': 'Enabled',
        'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 7}
    }]
}

# Check current waste
s3 = boto3.client('s3')
response = s3.list_multipart_uploads(Bucket='my-bucket')
print(f"Incomplete uploads: {len(response.get('Uploads', []))}")
```

**BP-20: Use S3 Select**
- Query CSV/JSON in S3 without downloading
- 80% cheaper than scanning full objects
- Reduce data transfer and Lambda processing time

### RDS

**BP-21: Use Aurora Serverless for Variable Loads**
```python
# Aurora Serverless v2: Scales in 0.5 ACU increments
AURORA_SERVERLESS_COST = {
    'min_capacity': 0.5,  # ACU (Aurora Capacity Units)
    'max_capacity': 16,   # ACU
    'cost_per_acu_hour': 0.12,

    'typical_usage': {
        'off_hours': 0.5,   # 14 hours/day * 30 = 420 hours
        'business': 8,      # 10 hours/day * 30 = 300 hours
        'peak': 16          # 10 hours/week * 4 = 10 hours (rare)
    }
}

monthly_cost = (
    0.5 * 420 * 0.12 +  # Off-hours
    8 * 300 * 0.12 +    # Business hours
    16 * 10 * 0.12      # Peak
)  # = $315/month

# vs Aurora Provisioned db.r6g.2xlarge 24/7: $1,095/month
# Savings: $780/month (71%)
```

**BP-22: Stop RDS Dev Instances**
- Stop: $0.08/GB-month storage only (no instance cost)
- Automated with Lambda (nightly stop, morning start)
- Savings: 58% (14 off-hours / 24 hours)

**BP-23: Use Read Replicas Wisely**
- Each replica = 100% of instance cost
- Evaluate: Can ElastiCache serve reads instead? (90% cheaper)
- Use cross-region replicas only for DR (not reads)

### DynamoDB

**BP-24: Choose Capacity Mode Carefully**
```python
# Break-even analysis
def dynamodb_cost_comparison(requests_per_month):
    """Compare Provisioned vs On-Demand"""

    # Provisioned (assumes 25% utilization of provisioned capacity)
    required_wcu = requests_per_month / (30 * 24 * 3600) / 0.25  # 25% util
    required_rcu = (requests_per_month * 5) / (30 * 24 * 3600) / 0.25  # 5x more reads

    provisioned_cost = (
        required_wcu * 730 * 0.00065 +  # WCU
        required_rcu * 730 * 0.00013    # RCU
    )

    # On-Demand
    writes = requests_per_month * 0.2  # Assume 20% writes
    reads = requests_per_month * 0.8   # 80% reads

    on_demand_cost = (
        (writes / 1_000_000) * 1.25 +   # Write request units
        (reads / 1_000_000) * 0.25       # Read request units
    )

    return {
        'provisioned': provisioned_cost,
        'on_demand': on_demand_cost,
        'recommendation': 'provisioned' if provisioned_cost < on_demand_cost else 'on_demand'
    }

# Test scenarios
for requests in [1_000_000, 10_000_000, 100_000_000]:
    result = dynamodb_cost_comparison(requests)
    print(f"\n{requests:,} requests/month:")
    print(f"  Provisioned: ${result['provisioned']:.2f}")
    print(f"  On-Demand: ${result['on_demand']:.2f}")
    print(f"  ✅ Winner: {result['recommendation'].upper()}")

# Rule of thumb: On-Demand cheaper if <15% utilization
```

**BP-25: Enable Auto-Scaling for DynamoDB**
- Provisioned capacity with auto-scaling (best of both)
- Target 70% utilization
- Scale based on consumed capacity CloudWatch metric

## FinOps Best Practices

### Visibility

**BP-26: Enable Cost Explorer Day 1**
```bash
# Enable Cost Explorer for organization
aws ce update-cost-allocation-tags-status \
  --cost-allocation-tags-status \
  TagKey=CostCenter,Status=Active \
  TagKey=Team,Status=Active \
  TagKey=Project,Status=Active \
  TagKey=Environment,Status=Active

# Create Cost and Usage Report (most detailed)
aws cur put-report-definition \
  --report-definition file://cur-definition.json
```

**BP-27: Set Up Daily Cost Dashboard**
- Slack/email with yesterday's cost vs budget
- Alert on >10% day-over-day increase
- Show top 5 services by cost

### Accountability

**BP-28: Implement Showback First, Chargeback Later**
- Start with monthly cost reports per team (no financial impact)
- After 3-6 months, introduce chargeback (budget from team P&L)
- Drives cost-aware behavior without initial friction

**BP-29: Make Cost Visible to Engineers**
```python
# Add cost to deployment notifications
SLACK_DEPLOYMENT_MESSAGE = """
🚀 Deployment: api-service v1.2.3
  Environment: Production
  Deployed by: @alice

💰 Monthly Cost Impact:
  New Lambda functions: +$45/month
  New DynamoDB table: +$120/month
  Total increase: +$165/month (3% of team budget)

Approval: Auto-approved (<5% budget impact)
"""
```

**BP-30: Include Cost in Architecture Reviews**
- TCO calculation required for new systems
- Cost-benefit analysis in design docs
- Alternative options evaluated (e.g., Lambda vs EC2)

### Optimization

**BP-31: Monthly Right-Sizing Review**
```python
# Automate right-sizing recommendation extraction
def get_monthly_right_sizing_tasks():
    """Get and prioritize right-sizing recommendations"""
    compute_optimizer = boto3.client('compute-optimizer')

    response = compute_optimizer.get_ec2_instance_recommendations()

    recommendations = []
    for rec in response['instanceRecommendations']:
        if rec['finding'] == 'OVER_PROVISIONED':
            current_cost = rec['currentInstanceType']['pricing']['monthlyCost']
            recommended_cost = rec['recommendationOptions'][0]['pricing']['monthlyCost']
            savings = current_cost - recommended_cost

            recommendations.append({
                'instance_id': rec['instanceArn'].split('/')[-1],
                'current': rec['currentInstanceType']['instanceType'],
                'recommended': rec['recommendationOptions'][0]['instanceType'],
                'monthly_savings': savings,
                'risk': rec['recommendationOptions'][0]['performanceRisk']  # 0-4
            })

    # Sort by savings (implement high-savings, low-risk first)
    recommendations.sort(key=lambda x: (-x['monthly_savings'], x['risk']))

    return recommendations

# Run monthly, create Jira tickets for top 20 recommendations
```

**BP-32: Quarterly Commitment Review**
- Review RI/SP utilization (target >85%)
- Review RI/SP coverage (target 65-75%)
- Increase commitments if coverage <60% and util >90%
- Decrease if utilization <75% (wasted commitment)

**BP-33: Weekly Waste Cleanup**
```python
# Automated weekly waste report
WASTE_PATTERNS = [
    {
        'resource': 'Unused Elastic IPs',
        'check': 'EIPs not associated with instance',
        'cost_each': 3.60,  # per month
        'action': 'Release EIP'
    },
    {
        'resource': 'Unattached EBS Volumes',
        'check': 'Volumes in "available" state',
        'cost_each': 8.00,  # per 100 GB, per month
        'action': 'Create snapshot, delete volume'
    },
    {
        'resource': 'Old Snapshots',
        'check': 'Snapshots >90 days without "Keep" tag',
        'cost_each': 5.00,  # per 100 GB, per month
        'action': 'Delete snapshot'
    },
    {
        'resource': 'Idle Load Balancers',
        'check': 'ALB with 0 targets',
        'cost_each': 22.50,  # per month
        'action': 'Delete load balancer'
    },
    {
        'resource': 'Unused NAT Gateways',
        'check': 'NAT Gateway with <100 MB/month',
        'cost_each': 32.85,  # per month (730 hours * $0.045)
        'action': 'Consider VPC endpoints instead'
    }
]
```

### Automation

**BP-34: Auto-Tag on Resource Creation**
```python
# EventBridge rule to tag new resources
def tag_new_resource(event):
    """Auto-tag resources created without required tags"""
    resource_arn = event['detail']['responseElements']['resourceArn']
    creator_identity = event['detail']['userIdentity']['principalId']

    # Extract account/team from IAM role/user
    tags = {
        'CreatedBy': creator_identity,
        'CreatedAt': event['detail']['eventTime'],
        'ManagedBy': 'AWS Console'  # or detect Terraform/CloudFormation
    }

    # Apply tags
    tagging = boto3.client('resourcegroupstaggingapi')
    tagging.tag_resources(
        ResourceARNList=[resource_arn],
        Tags=tags
    )
```

**BP-35: Automated Right-Sizing Actions**
```python
# Auto-resize resources with <20% CPU for 30 days
def auto_right_size(dry_run=True):
    """Automatically right-size under-utilized instances"""
    compute_optimizer = boto3.client('compute-optimizer')
    ec2 = boto3.client('ec2')

    recommendations = compute_optimizer.get_ec2_instance_recommendations()

    actions_taken = []
    for rec in recommendations['instanceRecommendations']:
        if rec['finding'] == 'OVER_PROVISIONED':
            savings = rec['currentInstanceType']['pricing']['monthlyCost'] - \
                     rec['recommendationOptions'][0]['pricing']['monthlyCost']

            # Auto-resize if savings >$20/month and low performance risk
            if savings > 20 and rec['recommendationOptions'][0]['performanceRisk'] < 2:
                instance_id = rec['instanceArn'].split('/')[-1]
                new_type = rec['recommendationOptions'][0]['instanceType']

                if not dry_run:
                    # Stop instance
                    ec2.stop_instances(InstanceIds=[instance_id])

                    # Wait for stopped
                    waiter = ec2.get_waiter('instance_stopped')
                    waiter.wait(InstanceIds=[instance_id])

                    # Modify instance type
                    ec2.modify_instance_attribute(
                        InstanceId=instance_id,
                        InstanceType={'Value': new_type}
                    )

                    # Start instance
                    ec2.start_instances(InstanceIds=[instance_id])

                actions_taken.append({
                    'instance_id': instance_id,
                    'action': f"Resize to {new_type}",
                    'savings': savings
                })

    return actions_taken
```

## Tagging Best Practices

**BP-36: Mandatory Tag Policy**
```python
MANDATORY_TAGS = {
    'CostCenter': {
        'description': 'Financial code for chargeback',
        'format': 'CC-XXXXX',
        'example': 'CC-12345',
        'enforcement': 'SCP deny creation without this tag'
    },
    'Team': {
        'description': 'Owning team',
        'values': ['Engineering', 'Data', 'ML', 'DevOps', 'Security'],
        'enforcement': 'Auto-tag from IAM role'
    },
    'Environment': {
        'description': 'Deployment environment',
        'values': ['prod', 'staging', 'dev', 'test'],
        'enforcement': 'Required by Terraform'
    },
    'Project': {
        'description': 'Product or initiative',
        'format': 'lowercase-hyphenated',
        'example': 'data-platform',
        'enforcement': 'Required in all IaC'
    }
}

# Enforce with AWS Config Rule
def check_required_tags(resource):
    """AWS Config custom rule"""
    tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}

    for required_tag in MANDATORY_TAGS.keys():
        if required_tag not in tags:
            return {
                'compliance_type': 'NON_COMPLIANT',
                'annotation': f'Missing required tag: {required_tag}'
            }

    return {'compliance_type': 'COMPLIANT'}
```

**BP-37: Tag Inheritance**
- Use tag propagation: EBS inherits from EC2, snapshots inherit from volumes
- CloudFormation stacks: Tag stack, all resources inherit
- AWS Organizations: Tag OUs, apply to member accounts

## Data Transfer Best Practices

**BP-38: Use VPC Endpoints**
```python
# Avoid NAT Gateway for AWS services
VPC_ENDPOINT_SAVINGS = {
    's3': {
        'nat_gateway_cost': 32.85,  # $0.045/hour * 730
        'data_transfer_nat': 0.045,  # per GB through NAT
        'vpc_endpoint_cost': 0,      # S3 gateway endpoint is FREE
        'data_transfer_endpoint': 0,
        'monthly_savings': 32.85 + (100 * 0.045)  # Assume 100 GB/month
    },
    'dynamodb': {
        'vpc_endpoint_cost': 0,  # DynamoDB gateway endpoint is FREE
    },
    'other_services': {
        # Interface endpoints (SQS, SNS, etc.)
        'vpc_endpoint_cost': 0.01,  # per hour per AZ
        'data_transfer': 0.01        # per GB (vs $0.045 NAT)
    }
}

# Rule: Always use gateway endpoints (S3, DynamoDB) - they're free
# Evaluate interface endpoints if >100 GB/month to service
```

**BP-39: Use CloudFront for Static Assets**
- Reduce S3 GET requests (90%+ cache hit rate)
- Reduce data transfer (CloudFront charges less than S3 egress)
- Savings: $0.085/GB (S3 transfer) → $0.085/GB (CloudFront) but 90% cached

**BP-40: Keep Data in Same Region**
```python
# Data transfer costs
DATA_TRANSFER_PRICING = {
    'within_az': 0,           # FREE
    'cross_az': 0.01,         # per GB (can add up!)
    'cross_region': 0.02,     # per GB (expensive)
    'internet_egress': 0.09,  # per GB (most expensive)
    'internet_ingress': 0     # FREE
}

# Best practice: Design data locality
# ✅ S3 bucket + Lambda in us-east-1
# ❌ S3 in us-east-1, Lambda in us-west-2 (cross-region transfer)
```

## Monitoring and Alerting

**BP-41: Daily Cost Anomaly Checks**
```python
# Check for anomalies every morning
def daily_cost_anomaly_report():
    """Generate daily anomaly report"""
    ce = boto3.client('ce-anomaly-detection')

    # Get anomalies from last 24 hours
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    response = ce.get_anomalies(
        DateInterval={'StartDate': start_date, 'EndDate': end_date},
        MaxResults=10
    )

    anomalies = response['Anomalies']

    if anomalies:
        report = "🚨 Cost Anomalies Detected:\n\n"
        for anomaly in anomalies:
            impact = anomaly['Impact']['TotalImpact']
            service = anomaly['DimensionValue']
            report += f"  • {service}: +${impact:.2f} ({anomaly['Impact']['TotalImpactPercentage']:.1f}%)\n"

        # Send to Slack
        send_slack_alert(report)
    else:
        print("✅ No cost anomalies detected")
```

**BP-42: Set Up Billing Alarms**
- CloudWatch billing metric (us-east-1 only)
- Alert at 50%, 75%, 90%, 100% of budget
- Escalation: Email → Slack → PagerDuty

## Development Best Practices

**BP-43: Cost-Aware CI/CD**
```yaml
# GitHub Actions: Use Spot runners
runs-on:
  group: spot-runners  # 75% cheaper than standard runners

# Cache dependencies (reduce build time = lower cost)
- uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

# Only run expensive tests on main branch
- name: Integration Tests
  if: github.ref == 'refs/heads/main'
  run: npm run test:integration
```

**BP-44: Ephemeral Environments**
- Create review environments on PR open
- Delete on PR merge/close
- Savings: 80% vs permanent staging environments

**BP-45: Use LocalStack for Local Development**
```yaml
# docker-compose.yml
services:
  localstack:
    image: localstack/localstack
    environment:
      - SERVICES=s3,dynamodb,lambda,sqs
    # Free for core services, avoids AWS dev costs
```

## Cleanup and Hygiene

**BP-46: Automated Resource Tagging Scanner**
```python
# Weekly scan for untagged resources
def scan_untagged_resources():
    """Find resources without required tags"""
    tagging = boto3.client('resourcegroupstaggingapi')

    required_tags = ['CostCenter', 'Team', 'Environment', 'Project']

    # Get all tagged resources
    response = tagging.get_resources(
        TagFilters=[],
        ResourceTypeFilters=['ec2:instance', 'rds:db', 's3:bucket', 'lambda:function']
    )

    untagged = []
    for resource in response['ResourceTagMappingList']:
        tags = {tag['Key']: tag['Value'] for tag in resource['Tags']}

        missing_tags = [t for t in required_tags if t not in tags]
        if missing_tags:
            untagged.append({
                'arn': resource['ResourceARN'],
                'missing_tags': missing_tags
            })

    # Calculate cost of untagged resources (can't allocate)
    print(f"\n⚠️  Untagged Resources: {len(untagged)}")
    print(f"    Target: <5% of resources")

    return untagged
```

**BP-47: Quarterly Access Pattern Review**
- S3 Storage Lens: Check object age and access patterns
- Move infrequently accessed data to IA or Glacier
- Identify and delete abandoned buckets

**BP-48: Annual Architecture Review**
- Re-evaluate technology choices (new services, pricing changes)
- Benchmark against industry standards
- Set next year's cost optimization goals

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Over-Provisioning for "Just in Case"
- **Problem**: Provisioning for theoretical peak load that never happens
- **Impact**: 50-70% waste on idle capacity
- **Solution**: Start small, auto-scale based on actual load

### ❌ Anti-Pattern 2: Ignoring Data Transfer Costs
- **Problem**: Cross-region replication without justification
- **Impact**: 10-20% of total cloud spend
- **Solution**: Keep data and compute in same region, use CloudFront

### ❌ Anti-Pattern 3: Default Instance Types
- **Problem**: Using m5.large for everything without analysis
- **Impact**: 30-50% over-spending (could use t3.small for many workloads)
- **Solution**: Right-size from actual metrics, use Compute Optimizer

### ❌ Anti-Pattern 4: Manual Resource Management
- **Problem**: Creating resources via console, no automation
- **Impact**: Orphaned resources, inconsistent tagging, hidden costs
- **Solution**: Infrastructure as Code (Terraform, CloudFormation)

### ❌ Anti-Pattern 5: No Lifecycle Policies
- **Problem**: All S3 data in Standard storage class forever
- **Impact**: 50-80% wasted storage costs
- **Solution**: Default lifecycle on all buckets, intelligent-tiering minimum

### ❌ Anti-Pattern 6: Buying RIs Too Early
- **Problem**: Committing to 3-year RIs on day 1
- **Impact**: Wrong instance type/size, wasted commitment
- **Solution**: Monitor 3 months, start with 1-year RIs or Savings Plans

### ❌ Anti-Pattern 7: Ignoring Spot for Batch
- **Problem**: Running batch jobs on On-Demand instances
- **Impact**: Paying 3-5x more than necessary
- **Solution**: EMR/Batch with Spot (checkpointing for fault tolerance)

### ❌ Anti-Pattern 8: Not Tracking Unit Economics
- **Problem**: Only looking at total spend, not cost per customer/transaction
- **Impact**: Can't identify efficiency gains or regressions
- **Solution**: Calculate unit economics monthly, track trends

## Security and Compliance Considerations

**BP-49: Principle of Least Privilege for Cost APIs**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:Get*",
        "ce:Describe*",
        "ce:List*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "ce:CreateCostCategoryDefinition",
        "ce:DeleteCostCategoryDefinition"
      ],
      "Resource": "*"
    }
  ]
}
```

**BP-50: Separate Cost Reporting from Resource Management**
- FinOps team: Read-only Cost Explorer access
- Engineering: Resource management but cost visibility
- Finance: Full billing access

## Checklist for New Projects

### Before Launch
- [ ] Cost estimate completed (monthly run rate)
- [ ] Tagging strategy defined and enforced (all 4 mandatory tags)
- [ ] Budget created with alerts (monthly limit + forecasted)
- [ ] Right-sized initial resources (start small)
- [ ] Lifecycle policies configured (S3, snapshots)
- [ ] Auto Scaling configured (EC2, DynamoDB, ECS)
- [ ] Serverless-first evaluation completed

### First Month
- [ ] Monitor actual vs estimated cost (variance analysis)
- [ ] Review CloudWatch metrics (CPU, memory, network)
- [ ] Check for idle resources weekly
- [ ] Calculate unit economics (cost per transaction/user)
- [ ] Cost anomaly detection enabled

### Months 2-3
- [ ] Right-sizing review (Compute Optimizer recommendations)
- [ ] Evaluate commitment options (RI/SP ROI analysis)
- [ ] Optimize storage (access patterns, lifecycle transitions)
- [ ] Review data transfer patterns (reduce cross-region)
- [ ] Set up automated cost reports (weekly to team)

### Month 4+
- [ ] Purchase initial commitments (50-60% coverage)
- [ ] Implement automated cleanup (idle resources)
- [ ] Cost optimization KPIs tracked (coverage, utilization, waste)
- [ ] Quarterly architecture review
- [ ] FinOps maturity assessment

## Organizational Best Practices

**BP-51: Dedicate FinOps Resources**
- 1 FTE per $10M annual cloud spend
- Engineers spend 10% time on cost optimization
- Monthly FinOps meeting (engineering + finance)

**BP-52: Incentivize Cost Optimization**
- Team bonuses tied to cost efficiency improvements
- Cost savings shared: 30% to team budget, 70% to company
- Engineer recognition for significant optimizations

**BP-53: Continuous Education**
- Quarterly cost optimization training
- AWS Well-Architected reviews annually
- FinOps Certified Practitioner for 1-2 team members

## Real-World Case Studies

### Case Study 1: E-Commerce Platform

**Before**:
- 50 EC2 instances (all m5.2xlarge, all On-Demand, 24/7)
- 100 TB S3 (all Standard storage class)
- RDS (db.r5.4xlarge, 24/7)
- **Cost**: $18,500/month

**Optimizations**:
1. Right-sized EC2 (10x m5.2xlarge, 20x m5.xlarge, 20x m5.large)
2. Purchased 3-year RIs for 60% baseline
3. S3 lifecycle: 10 TB Standard, 30 TB IA, 60 TB Glacier
4. RDS: Downsize to db.r5.2xlarge + 2 read replicas (vs 1 huge)
5. EBS: gp2 → gp3 (20% savings)

**After**: $8,200/month
**Savings**: $10,300/month (56%)
**Implementation**: 2 months

### Case Study 2: Data Analytics Startup

**Before**:
- EMR cluster (5x m5.4xlarge, 24/7)
- S3 (50 TB, all Standard)
- Athena queries (1 TB scanned per query, 500 queries/month)
- **Cost**: $15,000/month

**Optimizations**:
1. EMR: Run 6 hours/day (batch processing only)
2. EMR: 80% Spot instances (task nodes)
3. S3: Convert CSV to Parquet (90% size reduction)
4. Athena: Partition by date (scan only needed partitions)
5. Glue Crawler: Weekly instead of daily

**After**: $2,100/month
**Savings**: $12,900/month (86%)
**Payback**: Immediate

### Case Study 3: SaaS Company (500K users)

**Before**:
- API: 20x c5.xlarge (24/7, all On-Demand)
- RDS: db.m5.8xlarge (over-sized for peak only)
- No cost visibility (no tags)
- **Cost**: $25,000/month
- **Unit cost**: $0.05 per user per month

**Optimizations**:
1. API: Migrated to Lambda + API Gateway (500M requests/month)
2. Database: Aurora Serverless v2 (0.5-64 ACU auto-scaling)
3. CloudFront for static assets (90% cache hit rate)
4. DynamoDB for session storage (replaced ElastiCache)
5. Implemented cost allocation tags (team/product)

**After**: $9,500/month
**Savings**: $15,500/month (62%)
**Unit cost**: $0.019 per user per month (62% improvement)
**Business Impact**: Improved margins, lower CAC ratio

## Cost Optimization Roadmap

### Months 1-3: Foundation
- Enable Cost Explorer and CUR
- Implement tagging strategy (80%+ compliance)
- Set up budgets and alerts
- Establish weekly cost reviews

### Months 4-6: Quick Wins
- Stop dev/test instances off-hours (15-30% savings)
- Delete unused resources (5-10% savings)
- S3 lifecycle policies (20-40% storage savings)
- Right-size obvious over-provisioning (10-20% savings)

### Months 7-12: Strategic Optimization
- Purchase initial RIs/SPs (50-60% coverage)
- Implement Auto Scaling (20-30% compute savings)
- Migrate appropriate workloads to serverless
- Establish FinOps KPI dashboard

### Year 2: Continuous Improvement
- Increase commitment coverage to 70-75%
- Automated right-sizing actions
- Cost anomaly detection with auto-remediation
- Achieve FinOps maturity Level 3-4

### Year 2+ Target
- <10% waste ratio
- >85% commitment utilization
- >75% commitment coverage
- Unit economics improving 10-20% YoY

## Common Mistakes and How to Avoid Them

### Mistake 1: Optimizing in Isolation
- **Problem**: Engineering optimizes without talking to finance
- **Solution**: Monthly FinOps meetings with all stakeholders
- **Impact**: Misaligned priorities, duplicate efforts

### Mistake 2: Focus Only on Large Costs
- **Problem**: Ignoring $100/month wastes (1000 of them = $100K/year)
- **Solution**: Automated weekly cleanup of small waste
- **Impact**: Death by a thousand cuts

### Mistake 3: Committing Too Much Too Fast
- **Problem**: 90% RI coverage on month 1, then architecture changes
- **Solution**: Scale commitments gradually (50% → 60% → 70% over 12 months)
- **Impact**: Wasted commitments, <70% utilization

### Mistake 4: No Cost Testing in Pre-Prod
- **Problem**: Deploying to production without cost validation
- **Solution**: Run load tests in staging, extrapolate to production scale
- **Impact**: Bill shock, emergency optimization

### Mistake 5: Manual Optimization Only
- **Problem**: Relying on humans to find and fix waste
- **Solution**: Automate detection and remediation (80% of common patterns)
- **Impact**: Optimization doesn't scale with growth

## Key Performance Indicators

Track these KPIs monthly:

```python
COST_OPTIMIZATION_KPIS = {
    'financial': {
        'total_spend': {'target': '<30% of revenue', 'frequency': 'monthly'},
        'cost_variance': {'target': '±10% of budget', 'frequency': 'monthly'},
        'unit_economics': {'target': 'Decreasing YoY', 'frequency': 'monthly'}
    },
    'efficiency': {
        'waste_ratio': {'target': '<10%', 'calculation': 'idle_cost / total_cost'},
        'commitment_utilization': {'target': '>85%', 'source': 'Cost Explorer'},
        'commitment_coverage': {'target': '70-80%', 'source': 'Cost Explorer'},
        'untagged_resources': {'target': '<5%', 'source': 'AWS Config'}
    },
    'operational': {
        'optimization_velocity': {'target': '>70% implemented in 30d', 'source': 'Jira'},
        'anomaly_detection_time': {'target': '<24 hours', 'source': 'AWS Anomaly Detection'},
        'remediation_time': {'target': '<7 days', 'source': 'Jira'}
    }
}
```

## Tools and Automation

### Cost Optimization Tools

**AWS Native**:
- Cost Explorer: Visualization and filtering
- Compute Optimizer: ML-powered right-sizing
- Trusted Advisor: Best practice checks (Business Support+ plan)
- Cost Anomaly Detection: Automated anomaly identification

**Third-Party**:
- CloudHealth (by VMware): Multi-cloud cost management
- Cloudability (by Apptio): Advanced analytics and forecasting
- Spot.io: Automated Spot instance management
- Vantage: Cost reporting and Slack integration
- Kubecost: Kubernetes cost visibility

### Automation Scripts

**BP-54: Cost Optimization Bot**
```python
# Slack bot for cost queries
@slack_app.command("/cost")
def cost_command(ack, command, say):
    """
    Slack slash command for cost queries
    Usage: /cost service s3
           /cost team engineering
           /cost anomalies
    """
    ack()

    query_type = command['text'].split()[0]
    query_value = ' '.join(command['text'].split()[1:])

    ce = boto3.client('ce')

    if query_type == 'service':
        # Get cost by service
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [query_value]
                }
            }
        )

        cost = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        say(f"💰 {query_value}: ${float(cost):.2f} (last 30 days)")

    elif query_type == 'anomalies':
        # Get recent anomalies
        ced = boto3.client('ce-anomaly-detection')
        # ... anomaly query logic
        pass
```

## Summary

This guide covered 54 best practices across:
- Design (start small, right pricing model, multi-tenancy)
- Development (tag everything, auto-shutdown, IaC)
- Testing (Spot for CI, cleanup test data)
- Production (gradual commitments, budget alerts, anomaly detection)
- Service-specific (EC2, Lambda, S3, RDS, DynamoDB)
- FinOps (visibility, accountability, automation)
- Monitoring (daily anomalies, billing alarms)
- Anti-patterns (over-provisioning, ignoring transfer costs)

**Priority Order**:
1. **Week 1**: Enable Cost Explorer, implement tagging, set budgets
2. **Month 1**: Clean up obvious waste (idle resources, unattached volumes)
3. **Month 2**: Right-size resources based on metrics
4. **Month 3**: Implement S3 lifecycle policies
5. **Month 4+**: Purchase commitments, automate optimization

**Expected Results**:
- Month 1: 10-20% savings (quick wins)
- Month 3: 25-35% savings (right-sizing)
- Month 6: 35-45% savings (commitments)
- Year 1: 40-55% savings (full optimization)

**Next**: Explore resources for further learning.
