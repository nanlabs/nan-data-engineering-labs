#!/usr/bin/env python3
"""
Automated Resource Cleanup
Lambda-based automation to clean up unused resources and reduce waste
"""

import boto3
from datetime import datetime, timedelta, timezone
from typing import Dict, List

class ResourceCleanupAutomation:
    """Automate cleanup of unused AWS resources"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.ec2 = boto3.client('ec2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.elb = boto3.client('elbv2', region_name=region)
        self.region = region

    def find_idle_ec2_instances(self, days: int = 7, cpu_threshold: float = 5.0) -> List[Dict]:
        """
        Find EC2 instances with CPU utilization below threshold

        Args:
            days: Number of days to analyze
            cpu_threshold: CPU percentage threshold (default 5%)

        Returns:
            List of idle instances with metadata
        """
        print("\n🔍 Finding Idle EC2 Instances")
        print(f"   Criteria: CPU < {cpu_threshold}% for {days} days (dev/test only)")

        idle_instances = []

        # Get running dev/test instances
        response = self.ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'tag:Environment', 'Values': ['dev', 'test']}
            ]
        )

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                launch_time = instance['LaunchTime']

                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                environment = tags.get('Environment', 'unknown')
                name = tags.get('Name', 'unnamed')

                # Query CPU metrics
                try:
                    metrics_response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=datetime.now(timezone.utc) - timedelta(days=days),
                        EndTime=datetime.now(timezone.utc),
                        Period=86400,  # Daily
                        Statistics=['Average']
                    )

                    datapoints = metrics_response.get('Datapoints', [])

                    if datapoints:
                        avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)

                        if avg_cpu < cpu_threshold:
                            # Calculate estimated savings
                            pricing_estimate = self._estimate_ec2_monthly_cost(instance_type)

                            idle_instances.append({
                                'instance_id': instance_id,
                                'name': name,
                                'instance_type': instance_type,
                                'environment': environment,
                                'avg_cpu': avg_cpu,
                                'days_analyzed': days,
                                'launch_time': launch_time,
                                'estimated_monthly_cost': pricing_estimate,
                                'recommended_action': 'STOP'
                            })

                            print(f"   ⚠️  {instance_id} ({name}): {avg_cpu:.1f}% CPU → ${pricing_estimate:.2f}/month")

                except Exception as e:
                    print(f"   ❌ Error checking {instance_id}: {e}")

        print(f"\n   Found {len(idle_instances)} idle instances")
        return idle_instances

    def find_unattached_volumes(self, age_days: int = 30) -> List[Dict]:
        """
        Find EBS volumes not attached to instances

        Args:
            age_days: Minimum age in days

        Returns:
            List of unattached volumes
        """
        print("\n🔍 Finding Unattached EBS Volumes")
        print(f"   Criteria: Unattached > {age_days} days")

        unattached_volumes = []

        response = self.ec2.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )

        for volume in response['Volumes']:
            volume_id = volume['VolumeId']
            size_gb = volume['Size']
            volume_type = volume['VolumeType']
            create_time = volume['CreateTime']

            age = (datetime.now(timezone.utc) - create_time).days

            if age >= age_days:
                # Calculate cost
                pricing = {'gp3': 0.08, 'gp2': 0.10, 'io1': 0.125, 'io2': 0.125, 'st1': 0.045, 'sc1': 0.015}
                monthly_cost = size_gb * pricing.get(volume_type, 0.10)

                unattached_volumes.append({
                    'volume_id': volume_id,
                    'size_gb': size_gb,
                    'volume_type': volume_type,
                    'age_days': age,
                    'monthly_cost': monthly_cost,
                    'recommended_action': 'DELETE'
                })

                print(f"   ⚠️  {volume_id}: {size_gb}GB {volume_type}, {age} days old → ${monthly_cost:.2f}/month")

        print(f"\n   Found {len(unattached_volumes)} unattached volumes")
        return unattached_volumes

    def find_old_snapshots(self, age_days: int = 90) -> List[Dict]:
        """
        Find old snapshots without "Keep" tag

        Args:
            age_days: Minimum age in days

        Returns:
            List of old snapshots
        """
        print("\n🔍 Finding Old Snapshots")
        print(f"   Criteria: > {age_days} days, no 'Keep' tag")

        old_snapshots = []

        # Get account snapshots
        response = self.ec2.describe_snapshots(OwnerIds=['self'])

        for snapshot in response['Snapshots']:
            snapshot_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']
            volume_size = snapshot.get('VolumeSize', 0)

            age = (datetime.now(timezone.utc) - start_time).days

            # Check tags
            tags = {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
            keep_tag = tags.get('Keep', '').lower() == 'true'

            if age >= age_days and not keep_tag:
                monthly_cost = volume_size * 0.05  # $0.05/GB-month

                old_snapshots.append({
                    'snapshot_id': snapshot_id,
                    'volume_size': volume_size,
                    'age_days': age,
                    'monthly_cost': monthly_cost,
                    'recommended_action': 'DELETE'
                })

                print(f"   ⚠️  {snapshot_id}: {volume_size}GB, {age} days old → ${monthly_cost:.2f}/month")

        print(f"\n   Found {len(old_snapshots)} old snapshots")
        return old_snapshots

    def find_idle_rds_instances(self, days: int = 7) -> List[Dict]:
        """
        Find RDS instances with no connections

        Args:
            days: Number of days to analyze

        Returns:
            List of idle RDS instances
        """
        print("\n🔍 Finding Idle RDS Instances")
        print(f"   Criteria: < 1 avg connection for {days} days (dev/test only)")

        idle_databases = []

        # Get RDS instances
        response = self.rds.describe_db_instances()

        for db in response['DBInstances']:
            db_id = db['DBInstanceIdentifier']
            db_class = db['DBInstanceClass']
            engine = db['Engine']
            status = db['DBInstanceStatus']

            if status != 'available':
                continue

            # Get tags
            tags = {tag['Key']: tag['Value'] for tag in db.get('TagList', [])}
            environment = tags.get('Environment', 'unknown')

            # Only check dev/test
            if environment not in ['dev', 'test']:
                continue

            # Query connection metrics
            try:
                conn_response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='DatabaseConnections',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                    StartTime=datetime.now(timezone.utc) - timedelta(days=days),
                    EndTime=datetime.now(timezone.utc),
                    Period=86400,  # Daily
                    Statistics=['Average']
                )

                datapoints = conn_response.get('Datapoints', [])

                if datapoints:
                    avg_connections = sum(dp['Average'] for dp in datapoints) / len(datapoints)

                    if avg_connections < 1:
                        # Estimate cost
                        estimated_cost = self._estimate_rds_monthly_cost(db_class)

                        idle_databases.append({
                            'db_id': db_id,
                            'db_class': db_class,
                            'engine': engine,
                            'environment': environment,
                            'avg_connections': avg_connections,
                            'estimated_monthly_cost': estimated_cost,
                            'recommended_action': 'STOP'
                        })

                        print(f"   ⚠️  {db_id}: {avg_connections:.1f} avg connections → ${estimated_cost:.2f}/month")

            except Exception as e:
                print(f"   ❌ Error checking {db_id}: {e}")

        print(f"\n   Found {len(idle_databases)} idle databases")
        return idle_databases

    def execute_cleanup(
        self,
        idle_instances: List[Dict],
        unattached_volumes: List[Dict],
        old_snapshots: List[Dict],
        idle_databases: List[Dict],
        dry_run: bool = True
    ) -> Dict:
        """
        Execute cleanup actions

        Args:
            idle_instances: List of instances to stop
            unattached_volumes: List of volumes to delete
            old_snapshots: List of snapshots to delete
            idle_databases: List of databases to stop
            dry_run: If True, only simulate actions

        Returns:
            Cleanup summary dict
        """
        print(f"\n🧹 Executing Cleanup {'(DRY RUN)' if dry_run else '(LIVE)'}")
        print("=" * 60)

        summary = {
            'stopped_instances': [],
            'deleted_volumes': [],
            'deleted_snapshots': [],
            'stopped_databases': [],
            'total_monthly_savings': 0,
            'errors': []
        }

        # 1. Stop idle EC2 instances
        if idle_instances:
            print(f"\n   Stopping {len(idle_instances)} EC2 instances...")
            for inst in idle_instances:
                try:
                    if not dry_run:
                        self.ec2.stop_instances(InstanceIds=[inst['instance_id']])

                    summary['stopped_instances'].append(inst)
                    summary['total_monthly_savings'] += inst['estimated_monthly_cost']
                    print(f"      ✅ {inst['instance_id']}: ${inst['estimated_monthly_cost']:.2f}/month saved")

                except Exception as e:
                    summary['errors'].append(f"Stop {inst['instance_id']}: {e}")
                    print(f"      ❌ {inst['instance_id']}: {e}")

        # 2. Delete unattached volumes
        if unattached_volumes:
            print(f"\n   Deleting {len(unattached_volumes)} EBS volumes...")
            for vol in unattached_volumes:
                try:
                    if not dry_run:
                        self.ec2.delete_volume(VolumeId=vol['volume_id'])

                    summary['deleted_volumes'].append(vol)
                    summary['total_monthly_savings'] += vol['monthly_cost']
                    print(f"      ✅ {vol['volume_id']}: ${vol['monthly_cost']:.2f}/month saved")

                except Exception as e:
                    summary['errors'].append(f"Delete {vol['volume_id']}: {e}")
                    print(f"      ❌ {vol['volume_id']}: {e}")

        # 3. Delete old snapshots
        if old_snapshots:
            print(f"\n   Deleting {len(old_snapshots)} snapshots...")
            for snap in old_snapshots:
                try:
                    if not dry_run:
                        self.ec2.delete_snapshot(SnapshotId=snap['snapshot_id'])

                    summary['deleted_snapshots'].append(snap)
                    summary['total_monthly_savings'] += snap['monthly_cost']
                    print(f"      ✅ {snap['snapshot_id']}: ${snap['monthly_cost']:.2f}/month saved")

                except Exception as e:
                    summary['errors'].append(f"Delete {snap['snapshot_id']}: {e}")
                    print(f"      ❌ {snap['snapshot_id']}: {e}")

        # 4. Stop idle RDS instances
        if idle_databases:
            print(f"\n   Stopping {len(idle_databases)} RDS instances...")
            for db in idle_databases:
                try:
                    if not dry_run:
                        self.rds.stop_db_instance(DBInstanceIdentifier=db['db_id'])

                    summary['stopped_databases'].append(db)
                    summary['total_monthly_savings'] += db['estimated_monthly_cost']
                    print(f"      ✅ {db['db_id']}: ${db['estimated_monthly_cost']:.2f}/month saved")

                except Exception as e:
                    summary['errors'].append(f"Stop {db['db_id']}: {e}")
                    print(f"      ❌ {db['db_id']}: {e}")

        # Print summary
        print("\n" + "=" * 60)
        print("🧹 Cleanup Summary")
        print("=" * 60)
        print(f"   EC2 Instances Stopped: {len(summary['stopped_instances'])}")
        print(f"   EBS Volumes Deleted: {len(summary['deleted_volumes'])}")
        print(f"   Snapshots Deleted: {len(summary['deleted_snapshots'])}")
        print(f"   RDS Instances Stopped: {len(summary['stopped_databases'])}")
        print(f"\n💰 Total Monthly Savings: ${summary['total_monthly_savings']:.2f}")
        print(f"💰 Annual Savings: ${summary['total_monthly_savings'] * 12:.2f}")

        if summary['errors']:
            print(f"\n⚠️  Errors: {len(summary['errors'])}")
            for error in summary['errors'][:5]:
                print(f"      • {error}")

        return summary

    def _estimate_ec2_monthly_cost(self, instance_type: str) -> float:
        """Estimate EC2 monthly cost (simplified pricing)"""
        pricing = {
            't3.micro': 7.59,
            't3.small': 15.18,
            't3.medium': 30.37,
            't3.large': 60.74,
            't3.xlarge': 121.47,
            'm5.large': 70.08,
            'm5.xlarge': 140.16,
            'm5.2xlarge': 280.32,
            'm5.4xlarge': 560.64,
            'c5.large': 62.05,
            'c5.xlarge': 124.10,
            'r5.large': 91.98,
            'r5.xlarge': 183.96
        }
        return pricing.get(instance_type, 70.0)  # Default estimate

    def _estimate_rds_monthly_cost(self, db_class: str) -> float:
        """Estimate RDS monthly cost (simplified pricing)"""
        pricing = {
            'db.t3.micro': 10.95,
            'db.t3.small': 21.90,
            'db.t3.medium': 43.80,
            'db.m5.large': 122.63,
            'db.m5.xlarge': 245.25,
            'db.r5.large': 183.96,
            'db.r5.xlarge': 367.92
        }
        return pricing.get(db_class, 100.0)  # Default estimate

def lambda_handler(event, context):
    """
    Lambda handler for automated cleanup
    Triggered daily by EventBridge: cron(0 2 * * ? *)

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Cleanup summary
    """
    print(f"🕐 Cleanup Job Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    cleanup = ResourceCleanupAutomation()

    # Find candidates
    idle_instances = cleanup.find_idle_ec2_instances(days=7, cpu_threshold=5.0)
    unattached_volumes = cleanup.find_unattached_volumes(age_days=30)
    old_snapshots = cleanup.find_old_snapshots(age_days=90)
    idle_databases = cleanup.find_idle_rds_instances(days=7)

    # Execute cleanup (change dry_run=False to actually clean up)
    summary = cleanup.execute_cleanup(
        idle_instances=idle_instances,
        unattached_volumes=unattached_volumes,
        old_snapshots=old_snapshots,
        idle_databases=idle_databases,
        dry_run=True  # Set to False for actual cleanup
    )

    # Send SNS notification with summary
    try:
        sns = boto3.client('sns')
        message = f"""
AWS Cleanup Automation Summary

Stopped EC2 Instances: {len(summary['stopped_instances'])}
Deleted EBS Volumes: {len(summary['deleted_volumes'])}
Deleted Snapshots: {len(summary['deleted_snapshots'])}
Stopped RDS Instances: {len(summary['stopped_databases'])}

💰 Monthly Savings: ${summary['total_monthly_savings']:.2f}
💰 Annual Savings: ${summary['total_monthly_savings'] * 12:.2f}

Errors: {len(summary['errors'])}
"""

        # Uncomment to send notification
        # sns.publish(
        #     TopicArn=f"arn:aws:sns:us-east-1:{context.invoked_function_arn.split(':')[4]}:cleanup-alerts",
        #     Subject='AWS Cleanup Job Complete',
        #     Message=message
        # )

    except Exception as e:
        print(f"⚠️  Could not send SNS notification: {e}")

    return summary

def main():
    """Main cleanup workflow (local testing)"""
    print("=" * 70)
    print("AWS Automated Resource Cleanup")
    print("=" * 70)

    cleanup = ResourceCleanupAutomation()

    # Find cleanup candidates
    print("\n[Step 1/2] Identifying Cleanup Candidates")

    idle_instances = cleanup.find_idle_ec2_instances(days=7, cpu_threshold=5.0)
    unattached_volumes = cleanup.find_unattached_volumes(age_days=30)
    old_snapshots = cleanup.find_old_snapshots(age_days=90)
    idle_databases = cleanup.find_idle_rds_instances(days=7)

    # Execute cleanup
    print("\n\n[Step 2/2] Executing Cleanup (DRY RUN)")

    summary = cleanup.execute_cleanup(
        idle_instances=idle_instances,
        unattached_volumes=unattached_volumes,
        old_snapshots=old_snapshots,
        idle_databases=idle_databases,
        dry_run=True  # Change to False to actually clean up
    )

    # Final summary
    print("\n" + "=" * 70)
    print("✅ Cleanup Analysis Complete!")
    print("=" * 70)

    print("\n💡 Cleanup Automation Best Practices:")
    print("   1. Start with DRY RUN mode (test for 1-2 weeks)")
    print("   2. Target dev/test environments only initially")
    print("   3. Use tag-based scoping (Environment=dev)")
    print("   4. Schedule during low-activity hours (2-4 AM)")
    print("   5. Send notifications to team Slack channels")
    print("   6. Keep 'Keep' tag exception for critical resources")

    print("\n📅 Recommended Cleanup Schedule:")
    print("   • Daily: Stop idle dev/test EC2 instances")
    print("   • Weekly: Delete unattached volumes >30 days")
    print("   • Monthly: Delete old snapshots >90 days")
    print("   • Quarterly: Review and cleanup unused AMIs")

    print("\n⚡ Deploy as Lambda:")
    print("   Runtime: Python 3.11")
    print("   Memory: 256 MB")
    print("   Timeout: 300 seconds (5 minutes)")
    print("   Trigger: EventBridge cron(0 2 * * ? *) - Daily 2 AM UTC")
    print("   IAM: Limited to dev/test resources with tag conditions")

    print("\n📊 Expected Savings:")
    print("   • 10-20% reduction in total AWS spend")
    print("   • Typical org: $50K/month → $5-10K/month saved")
    print("   • ROI: Implementation 8 hours, continuous savings")

if __name__ == '__main__':
    main()
