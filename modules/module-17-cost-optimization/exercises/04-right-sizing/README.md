# Exercise 04: Resource Right-Sizing

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐ Intermediate
💰 **Potential Savings:** 20-40% on compute costs

## Learning Objectives

- Use AWS Compute Optimizer for right-sizing recommendations
- Analyze CloudWatch metrics to identify over-provisioned resources
- Right-size EC2, RDS, and Redshift instances
- Implement Auto Scaling for dynamic workloads
- Calculate cost savings from right-sizing

## Right-Sizing Process

```
┌──────────────────────────────────────────────────────────┐
│                 Right-Sizing Workflow                    │
│                                                          │
│  1. Monitor      2. Analyze      3. Recommend    4. Act │
│     ↓                ↓                ↓             ↓    │
│  ┌────────┐     ┌────────┐     ┌──────────┐  ┌───────┐ │
│  │CloudWtch│ ─→ │Compute │ ─→ │Downsize  │→│Resize │ │
│  │Metrics │     │Optimizer│    │or Scale  │  │Save $ │ │
│  └────────┘     └────────┘     └──────────┘  └───────┘ │
│   CPU 20%        Over-sized     m5.2xl→m5.xl   -50%    │
│   Mem 40%        by 2x          $0.384→$0.192  cost    │
└──────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Enable AWS Compute Optimizer

**Objective**: Get AI-powered right-sizing recommendations.

**Steps**:

1. **Opt-in to Compute Optimizer**:

```python
import boto3

compute_optimizer = boto3.client('compute-optimizer')

# Opt-in (requires 30 days of metrics)
try:
    response = compute_optimizer.update_enrollment_status(
        status='Active',
        includeMemberAccounts=True
    )
    print("✓ Compute Optimizer enabled")
    print("  Note: Requires 30 days of CloudWatch metrics")
    print("  Recommendations available after analysis period")
except Exception as e:
    print(f"Already enrolled or error: {e}")
```

2. **Get EC2 recommendations**:

```python
# Get right-sizing recommendations for EC2
rec_response = compute_optimizer.get_ec2_instance_recommendations(
    maxResults=100
)

print("\n💡 EC2 Right-Sizing Recommendations:\n")

total_savings = 0
recommendations_list = []

for rec in rec_response.get('instanceRecommendations', []):
    instance_arn = rec['instanceArn']
    instance_id = instance_arn.split('/')[-1]
    current_type = rec['currentInstanceType']

    # Get current utilization
    utilization = rec['utilizationMetrics']
    cpu_avg = next((m['value'] for m in utilization if m['name'] == 'CPU'), 0)
    mem_avg = next((m['value'] for m in utilization if m['name'] == 'MEMORY'), 0)

    # Get recommendation
    if rec['finding'] == 'OVER_PROVISIONED':
        options = rec['recommendationOptions']
        best_option = options[0]  # Usually lowest cost option
        recommended_type = best_option['instanceType']

        # Parse savings
        savings_opportunity = best_option.get('savingsOpportunity', {})
        estimated_monthly_savings = float(savings_opportunity.get('estimatedMonthlySavings', 0))
        savings_pct = float(savings_opportunity.get('savingsOpportunityPercentage', 0))

        total_savings += estimated_monthly_savings

        recommendations_list.append({
            'instance_id': instance_id,
            'current': current_type,
            'recommended': recommended_type,
            'cpu_avg': cpu_avg,
            'mem_avg': mem_avg,
            'monthly_savings': estimated_monthly_savings,
            'savings_pct': savings_pct
        })

        print(f"  Instance: {instance_id}")
        print(f"    Current: {current_type} (CPU: {cpu_avg:.1f}%, Mem: {mem_avg:.1f}%)")
        print(f"    Recommended: {recommended_type}")
        print(f"    Savings: ${estimated_monthly_savings:.2f}/month ({savings_pct:.1f}%)")
        print()

print(f"📊 Total Potential Savings: ${total_savings:,.2f}/month (${total_savings * 12:,.2f}/year)")

# Export to CSV for review
import pandas as pd
df = pd.DataFrame(recommendations_list)
df.to_csv('ec2-right-sizing-recommendations.csv', index=False)
print(f"\n✓ Recommendations exported to ec2-right-sizing-recommendations.csv")
```

### Task 2: Analyze CloudWatch Metrics

**Objective**: Deep-dive into resource utilization to validate recommendations.

**Steps**:

1. **Collect 30-day metrics**:

```python
cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')

def get_instance_utilization(instance_id, days=30):
    """Get detailed utilization metrics for EC2 instance"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    metrics = {}

    # CPU Utilization
    cpu_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # 1 hour
        Statistics=['Average', 'Maximum']
    )

    if cpu_response['Datapoints']:
        cpu_values = [dp['Average'] for dp in cpu_response['Datapoints']]
        metrics['cpu_avg'] = sum(cpu_values) / len(cpu_values)
        metrics['cpu_max'] = max(dp['Maximum'] for dp in cpu_response['Datapoints'])
        metrics['cpu_p95'] = np.percentile(cpu_values, 95)

    # Network In (for right-sizing network-intensive workloads)
    network_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='NetworkIn',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )

    if network_response['Datapoints']:
        network_values = [dp['Average'] / (1024**2) for dp in network_response['Datapoints']]  # MB
        metrics['network_avg_mbps'] = sum(network_values) / len(network_values)
        metrics['network_max_mbps'] = max(dp['Maximum'] / (1024**2) for dp in network_response['Datapoints'])

    return metrics

# Analyze all running instances
instances = ec2.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)

print("\n📊 Instance Utilization Analysis (30 days):\n")

for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']

        metrics = get_instance_utilization(instance_id)

        print(f"  {instance_id} ({instance_type}):")
        print(f"    CPU Avg/P95/Max: {metrics.get('cpu_avg', 0):.1f}% / {metrics.get('cpu_p95', 0):.1f}% / {metrics.get('cpu_max', 0):.1f}%")

        # Right-sizing recommendation logic
        if metrics.get('cpu_avg', 0) < 20 and metrics.get('cpu_p95', 0) < 40:
            print(f"    ⚠️  OVER-PROVISIONED: Consider downsizing")
        elif metrics.get('cpu_avg', 0) > 70 or metrics.get('cpu_p95', 0) > 90:
            print(f"    ⚠️  UNDER-PROVISIONED: Consider upsizing")
        else:
            print(f"    ✓ Well-sized")
        print()
```

2. **Create utilization dashboard**:

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_utilization_dashboard(instance_id, metrics_data):
    """Create utilization dashboard for an instance"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Resource Utilization: {instance_id}', fontsize=16)

    # CPU utilization over time
    axes[0, 0].plot(metrics_data['timestamps'], metrics_data['cpu'], label='CPU %')
    axes[0, 0].axhline(y=80, color='orange', linestyle='--', label='Target Max (80%)')
    axes[0, 0].axhline(y=20, color='red', linestyle='--', label='Under-utilized (20%)')
    axes[0, 0].set_title('CPU Utilization')
    axes[0, 0].set_ylabel('Percentage')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Memory utilization (requires CloudWatch agent)
    if 'memory' in metrics_data:
        axes[0, 1].plot(metrics_data['timestamps'], metrics_data['memory'], label='Memory %', color='green')
        axes[0, 1].axhline(y=80, color='orange', linestyle='--')
        axes[0, 1].set_title('Memory Utilization')
        axes[0, 1].set_ylabel('Percentage')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

    # Network throughput
    axes[1, 0].plot(metrics_data['timestamps'], metrics_data['network_in'], label='Network In')
    axes[1, 0].set_title('Network Throughput')
    axes[1, 0].set_ylabel('MB/s')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Utilization distribution (histogram)
    axes[1, 1].hist(metrics_data['cpu'], bins=20, color='skyblue', edgecolor='black')
    axes[1, 1].axvline(x=np.mean(metrics_data['cpu']), color='red',
                       linestyle='--', label=f'Mean: {np.mean(metrics_data["cpu"]):.1f}%')
    axes[1, 1].set_title('CPU Distribution')
    axes[1, 1].set_xlabel('CPU %')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig(f'utilization-{instance_id}.png', dpi=300)
    print(f"✓ Dashboard saved: utilization-{instance_id}.png")
```

### Task 3: Right-Size RDS Instances

**Objective**: Optimize database instance sizes based on actual usage.

**Steps**:

```python
rds = boto3.client('rds')

def analyze_rds_utilization(db_instance_id, days=14):
    """Analyze RDS instance utilization"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    metrics = {}

    # CPU
    cpu_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )

    if cpu_response['Datapoints']:
        cpu_values = [dp['Average'] for dp in cpu_response['Datapoints']]
        metrics['cpu_avg'] = np.mean(cpu_values)
        metrics['cpu_p95'] = np.percentile(cpu_values, 95)
        metrics['cpu_max'] = max(dp['Maximum'] for dp in cpu_response['Datapoints'])

    # Connections
    conn_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='DatabaseConnections',
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )

    if conn_response['Datapoints']:
        conn_values = [dp['Average'] for dp in conn_response['Datapoints']]
        metrics['connections_avg'] = np.mean(conn_values)
        metrics['connections_max'] = max(dp['Maximum'] for dp in conn_response['Datapoints'])

    # Read/Write IOPS
    iops_read = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='ReadIOPS',
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )

    if iops_read['Datapoints']:
        metrics['read_iops_avg'] = np.mean([dp['Average'] for dp in iops_read['Datapoints']])

    return metrics

# Analyze RDS instances
db_instances = rds.describe_db_instances()

print("\n📊 RDS Right-Sizing Analysis:\n")

for db in db_instances['DBInstances']:
    db_id = db['DBInstanceIdentifier']
    instance_class = db['DBInstanceClass']
    engine = db['Engine']

    metrics = analyze_rds_utilization(db_id)

    print(f"  {db_id} ({instance_class} - {engine}):")
    print(f"    CPU Avg/P95/Max: {metrics.get('cpu_avg', 0):.1f}% / {metrics.get('cpu_p95', 0):.1f}% / {metrics.get('cpu_max', 0):.1f}%")
    print(f"    Connections Avg/Max: {metrics.get('connections_avg', 0):.0f} / {metrics.get('connections_max', 0):.0f}")
    print(f"    IOPS Avg: {metrics.get('read_iops_avg', 0):.0f}")

    # Recommendation logic
    if metrics.get('cpu_p95', 0) < 40:
        # Over-provisioned
        current_size = instance_class.split('.')[-1]  # e.g., 'xlarge'

        if current_size == '2xlarge':
            suggested = instance_class.replace('2xlarge', 'xlarge')
            savings_pct = 50
        elif current_size == 'xlarge':
            suggested = instance_class.replace('xlarge', 'large')
            savings_pct = 50
        elif current_size == 'large':
            suggested = instance_class.replace('large', 'medium')
            savings_pct = 50
        else:
            suggested = instance_class
            savings_pct = 0

        if suggested != instance_class:
            print(f"    💡 RECOMMENDATION: Downsize to {suggested}")
            print(f"       Expected Savings: ~{savings_pct}%")
            total_savings += savings_pct

    elif metrics.get('cpu_p95', 0) > 80:
        print(f"    ⚠️  HIGH UTILIZATION: Consider upsizing")
    else:
        print(f"    ✓ Well-sized")
    print()
```

### Task 2: Implement EC2 Right-Sizing

**Objective**: Programmatically modify instance types.

**Steps**:

1. **Create right-sizing function**:

```python
def right_size_instance(instance_id, new_instance_type, dry_run=True):
    """
    Resize EC2 instance to optimize costs

    Steps:
    1. Stop instance
    2. Change instance type
    3. Start instance
    4. Verify new type
    """
    ec2 = boto3.client('ec2')

    # Get current instance details
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    current_type = instance['InstanceType']
    current_state = instance['State']['Name']

    print(f"\n🔧 Right-Sizing: {instance_id}")
    print(f"  Current Type: {current_type}")
    print(f"  New Type: {new_instance_type}")
    print(f"  Current State: {current_state}")

    if dry_run:
        print(f"\n  ⚠️  DRY RUN MODE - No changes made")
        print(f"  To apply: Set dry_run=False")
        return

    try:
        # Step 1: Stop instance
        if current_state == 'running':
            print(f"\n  Stopping instance...")
            ec2.stop_instances(InstanceIds=[instance_id])

            # Wait for stopped state
            waiter = ec2.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[instance_id])
            print(f"  ✓ Instance stopped")

        # Step 2: Modify instance type
        print(f"\n  Changing instance type to {new_instance_type}...")
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={'Value': new_instance_type}
        )
        print(f"  ✓ Instance type modified")

        # Step 3: Start instance
        print(f"\n  Starting instance...")
        ec2.start_instances(InstanceIds=[instance_id])

        # Wait for running state
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f"  ✓ Instance running")

        # Step 4: Verify
        response = ec2.describe_instances(InstanceIds=[instance_id])
        new_type = response['Reservations'][0]['Instances'][0]['InstanceType']

        print(f"\n✓ Right-sizing complete!")
        print(f"  Verified Type: {new_type}")

        return True

    except Exception as e:
        print(f"\n❌ Error during right-sizing: {e}")
        return False

# Example: Right-size over-provisioned instance (DRY RUN)
right_size_instance('i-0123456789abcdef', 'm5.large', dry_run=True)
```

2. **Bulk right-sizing with approval**:

```python
def bulk_right_size_instances(recommendations, auto_approve=False):
    """Apply right-sizing to multiple instances with confirmation"""
    print("\n📋 Bulk Right-Sizing Plan:\n")

    total_monthly_savings = 0

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['instance_id']}: {rec['current']} → {rec['recommended']}")
        print(f"   Savings: ${rec['monthly_savings']:.2f}/month")
        total_monthly_savings += rec['monthly_savings']

    print(f"\n💰 Total Monthly Savings: ${total_monthly_savings:.2f}")
    print(f"💰 Annual Savings: ${total_monthly_savings * 12:.2f}")

    if not auto_approve:
        response = input("\n  Proceed with right-sizing? (yes/no): ")
        if response.lower() != 'yes':
            print("  Cancelled")
            return

    # Apply changes
    print("\n  Applying changes...")
    for rec in recommendations:
        success = right_size_instance(
            rec['instance_id'],
            rec['recommended'],
            dry_run=False
        )

        if success:
            print(f"  ✓ {rec['instance_id']} resized")
        else:
            print(f"  ❌ {rec['instance_id']} failed")

    print(f"\n✓ Bulk right-sizing complete")

# Apply recommendations (DRY RUN by default)
# bulk_right_size_instances(recommendations_list[:3], auto_approve=False)
```

### Task 3: Right-Size Redshift Clusters

**Objective**: Optimize data warehouse cluster size.

**Steps**:

```python
redshift = boto3.client('redshift')

def analyze_redshift_utilization(cluster_id, days=14):
    """Analyze Redshift cluster utilization"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    metrics = {}

    # CPU
    cpu_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Redshift',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average', 'Maximum']
    )

    if cpu_response['Datapoints']:
        cpu_values = [dp['Average'] for dp in cpu_response['Datapoints']]
        metrics['cpu_avg'] = np.mean(cpu_values)
        metrics['cpu_p95'] = np.percentile(cpu_values, 95)

    # Disk space
    disk_response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Redshift',
        MetricName='PercentageDiskSpaceUsed',
        Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )

    if disk_response['Datapoints']:
        disk_values = [dp['Average'] for dp in disk_response['Datapoints']]
        metrics['disk_avg'] = np.mean(disk_values)

    return metrics

# Analyze Redshift clusters
clusters = redshift.describe_clusters()

print("\n📊 Redshift Right-Sizing Analysis:\n")

for cluster in clusters['Clusters']:
    cluster_id = cluster['ClusterIdentifier']
    node_type = cluster['NodeType']
    num_nodes = cluster['NumberOfNodes']

    metrics = analyze_redshift_utilization(cluster_id)

    print(f"  {cluster_id}:")
    print(f"    Configuration: {num_nodes}x {node_type}")
    print(f"    CPU Avg/P95: {metrics.get('cpu_avg', 0):.1f}% / {metrics.get('cpu_p95', 0):.1f}%")
    print(f"    Disk Usage: {metrics.get('disk_avg', 0):.1f}%")

    # Recommendations
    if metrics.get('cpu_p95', 0) < 40 and num_nodes > 2:
        new_nodes = max(2, num_nodes // 2)
        print(f"    💡 RECOMMENDATION: Reduce to {new_nodes} nodes (50% savings)")
    elif metrics.get('cpu_p95', 0) < 40:
        print(f"    💡 RECOMMENDATION: Downsize node type or use RA3 with managed storage")
    elif metrics.get('disk_avg', 0) > 80:
        print(f"    ⚠️  HIGH DISK USAGE: Add nodes or migrate to RA3")
    else:
        print(f"    ✓ Well-sized")
    print()

# Elastic resize (minutes, not hours)
def elastic_resize_redshift(cluster_id, new_node_count):
    """Perform elastic resize (fast, minimal downtime)"""
    print(f"\n🔧 Elastic Resize: {cluster_id}")
    print(f"  New Node Count: {new_node_count}")

    response = redshift.resize_cluster(
        ClusterIdentifier=cluster_id,
        NumberOfNodes=new_node_count,
        Classic=False  # Elastic resize (fast)
    )

    print(f"  ✓ Resize initiated (5-15 minutes)")
    print(f"  Cluster will be read-only during resize")

    return response
```

### Task 4: Implement Auto Scaling

**Objective**: Dynamically adjust capacity based on demand.

**Steps**:

```python
autoscaling = boto3.client('autoscaling')
app_autoscaling = boto3.client('application-autoscaling')

# Example 1: EC2 Auto Scaling with target tracking
def create_target_tracking_policy(asg_name, target_cpu=70):
    """Create target tracking policy for Auto Scaling Group"""
    response = autoscaling.put_scaling_policy(
        AutoScalingGroupName=asg_name,
        PolicyName='target-tracking-cpu',
        PolicyType='TargetTrackingScaling',
        TargetTrackingConfiguration={
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'ASGAverageCPUUtilization'
            },
            'TargetValue': target_cpu,
            'ScaleInCooldown': 300,  # 5 minutes
            'ScaleOutCooldown': 60   # 1 minute
        }
    )

    print(f"✓ Target tracking policy created")
    print(f"  Target: {target_cpu}% CPU")
    print(f"  Scale out when CPU > {target_cpu}%")
    print(f"  Scale in when CPU < {target_cpu}%")

    return response['PolicyARN']

# Example 2: DynamoDB Auto Scaling (similar for ECS, Aurora, EMR)
def setup_dynamodb_autoscaling(table_name):
    """Configure auto scaling for DynamoDB table"""
    # Register scalable target
    app_autoscaling.register_scalable_target(
        ServiceNamespace='dynamodb',
        ResourceId=f'table/{table_name}',
        ScalableDimension='dynamodb:table:ReadCapacityUnits',
        MinCapacity=5,
        MaxCapacity=100
    )

    # Target tracking policy
    app_autoscaling.put_scaling_policy(
        PolicyName='ddb-read-scaling',
        ServiceNamespace='dynamodb',
        ResourceId=f'table/{table_name}',
        ScalableDimension='dynamodb:table:ReadCapacityUnits',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70.0,  # 70% utilization
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
            },
            'ScaleInCooldown': 300,
            'ScaleOutCooldown': 60
        }
    )

    print(f"✓ DynamoDB auto scaling configured")
    print(f"  Table: {table_name}")
    print(f"  Read Capacity: 5-100 units (auto-adjust)")
    print(f"  Target: 70% utilization")
    print(f"\n  Cost Impact:")
    print(f"    Without auto-scaling: 100 RCU * $0.00013/hour = $9.36/month")
    print(f"    With auto-scaling (avg 30 RCU): $2.81/month")
    print(f"    Savings: $6.55/month (70%)")
```

### Task 5: Generate Savings Report

**Objective**: Calculate total savings from right-sizing.

**Steps**:

```python
def generate_right_sizing_report(before_analysis, after_analysis):
    """Generate comprehensive savings report"""

    print("\n" + "="*60)
    print("          RIGHT-SIZING SAVINGS REPORT")
    print("="*60)

    # EC2 Savings
    ec2_before_cost = sum(a['monthly_cost'] for a in before_analysis['ec2'])
    ec2_after_cost = sum(a['monthly_cost'] for a in after_analysis['ec2'])
    ec2_savings = ec2_before_cost - ec2_after_cost
    ec2_savings_pct = (ec2_savings / ec2_before_cost * 100) if ec2_before_cost > 0 else 0

    print(f"\n1. EC2 Instances:")
    print(f"   Before: ${ec2_before_cost:,.2f}/month")
    print(f"   After:  ${ec2_after_cost:,.2f}/month")
    print(f"   Savings: ${ec2_savings:,.2f}/month ({ec2_savings_pct:.1f}%)")

    # RDS Savings
    rds_before_cost = sum(a['monthly_cost'] for a in before_analysis['rds'])
    rds_after_cost = sum(a['monthly_cost'] for a in after_analysis['rds'])
    rds_savings = rds_before_cost - rds_after_cost
    rds_savings_pct = (rds_savings / rds_before_cost * 100) if rds_before_cost > 0 else 0

    print(f"\n2. RDS Instances:")
    print(f"   Before: ${rds_before_cost:,.2f}/month")
    print(f"   After:  ${rds_after_cost:,.2f}/month")
    print(f"   Savings: ${rds_savings:,.2f}/month ({rds_savings_pct:.1f}%)")

    # Redshift Savings
    redshift_before_cost = sum(a['monthly_cost'] for a in before_analysis.get('redshift', []))
    redshift_after_cost = sum(a['monthly_cost'] for a in after_analysis.get('redshift', []))
    redshift_savings = redshift_before_cost - redshift_after_cost

    print(f"\n3. Redshift Clusters:")
    print(f"   Before: ${redshift_before_cost:,.2f}/month")
    print(f"   After:  ${redshift_after_cost:,.2f}/month")
    print(f"   Savings: ${redshift_savings:,.2f}/month")

    # Total
    total_before = ec2_before_cost + rds_before_cost + redshift_before_cost
    total_after = ec2_after_cost + rds_after_cost + redshift_after_cost
    total_savings = total_before - total_after
    total_savings_pct = (total_savings / total_before * 100) if total_before > 0 else 0

    print(f"\n" + "="*60)
    print(f"TOTAL SAVINGS")
    print(f"="*60)
    print(f"  Before: ${total_before:,.2f}/month")
    print(f"  After:  ${total_after:,.2f}/month")
    print(f"  Monthly Savings: ${total_savings:,.2f} ({total_savings_pct:.1f}%)")
    print(f"  Annual Savings: ${total_savings * 12:,.2f}")
    print(f"="*60)

    # ROI calculation
    implementation_time = 8  # hours
    hourly_rate = 100  # $/hour for engineer
    implementation_cost = implementation_time * hourly_rate
    payback_period = implementation_cost / total_savings if total_savings > 0 else 999

    print(f"\n📊 ROI Analysis:")
    print(f"  Implementation Cost: ${implementation_cost:.2f} ({implementation_time}h)")
    print(f"  Payback Period: {payback_period:.1f} months")
    print(f"  1-Year ROI: {(total_savings * 12 - implementation_cost) / implementation_cost * 100:.0f}%")

# Example report
before = {
    'ec2': [
        {'instance_id': 'i-001', 'type': 'm5.2xlarge', 'monthly_cost': 280},
        {'instance_id': 'i-002', 'type': 'm5.xlarge', 'monthly_cost': 140}
    ],
    'rds': [
        {'db_id': 'prod-db', 'class': 'db.r5.2xlarge', 'monthly_cost': 730}
    ],
    'redshift': [
        {'cluster_id': 'dwh', 'nodes': '4x dc2.large', 'monthly_cost': 1000}
    ]
}

after = {
    'ec2': [
        {'instance_id': 'i-001', 'type': 'm5.xlarge', 'monthly_cost': 140},  # -50%
        {'instance_id': 'i-002', 'type': 'm5.large', 'monthly_cost': 70}     # -50%
    ],
    'rds': [
        {'db_id': 'prod-db', 'class': 'db.r5.xlarge', 'monthly_cost': 365}  # -50%
    ],
    'redshift': [
        {'cluster_id': 'dwh', 'nodes': '2x dc2.large', 'monthly_cost': 500}  # -50%
    ]
}

generate_right_sizing_report(before, after)
```

## Validation Checklist

- [ ] Enabled AWS Compute Optimizer
- [ ] Retrieved EC2 right-sizing recommendations
- [ ] Retrieved RDS right-sizing recommendations
- [ ] Analyzed 30-day CloudWatch metrics (CPU, memory, network)
- [ ] Identified over-provisioned instances (CPU < 20% avg)
- [ ] Resized at least 1 instance (dry run acceptable)
- [ ] Configured Auto Scaling for dynamic workloads
- [ ] Generated savings report with ROI calculation

## Troubleshooting

**Issue**: Compute Optimizer shows no recommendations
- **Solution**: Need 30 days of CloudWatch metrics
- Enable CloudWatch detailed monitoring
- Ensure instances are running consistently

**Issue**: Memory metrics not available
- **Solution**: Install CloudWatch Agent on EC2 instances
- Configure agent to collect memory, disk metrics
- Wait 24 hours for data collection

**Issue**: Instance resize failed (InsufficientInstanceCapacity)
- **Solution**: Try different AZ
- Use different instance type in the same family
- Schedule resize during low-traffic period

**Issue**: Redshift elastic resize not available
- **Solution**: Some node type changes require classic resize
- Check supported resize paths in documentation
- Consider snapshot → restore with new cluster

## Key Learnings

✅ **Over-provisioning Common**: 40-60% of instances over-provisioned by 2x
✅ **P95 Metrics**: Use 95th percentile, not average, for sizing decisions
✅ **Gradual Approach**: Downsize incrementally (2xl → xl → large)
✅ **Auto Scaling**: Better than manual right-sizing for variable workloads
✅ **Quick Wins**: Development environments often 2-4x over-sized

## Right-Sizing Best Practices

1. **Use P95 metrics**: Don't rely on averages alone
2. **Monitor after changes**: Verify performance maintained
3. **Test in dev first**: Validate sizing before prod changes
4. **Schedule downsizing**: During maintenance windows
5. **Enable detailed monitoring**: CloudWatch agent for memory metrics
6. **Document baselines**: Know normal vs peak utilization
7. **Automate alerts**: Notify when utilization crosses thresholds

## Real-World Impact

**Case Study**: SaaS company with 50 EC2 instances
- **Before**: $15,000/month (mix of m5.2xlarge, m5.xlarge)
- **Analysis**: Avg CPU 25%, P95 CPU 45%
- **Action**: Downsized 30 instances (2xlarge → xlarge), 15 instances (xlarge → large)
- **After**: $8,500/month
- **Savings**: $6,500/month (43% reduction, $78,000/year)
- **Implementation**: 3 days with zero downtime

## Next Steps

- **Exercise 05**: Serverless cost analysis (Lambda vs EC2 TCO)
- **Exercise 06**: Cost governance (budgets, automated policies)

## Additional Resources

- [AWS Compute Optimizer](https://aws.amazon.com/compute-optimizer/)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [RDS Instance Classes](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html)
- [Redshift Resize Guide](https://docs.aws.amazon.com/redshift/latest/mgmt/managing-cluster-operations.html)
