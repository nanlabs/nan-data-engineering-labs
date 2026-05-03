#!/usr/bin/env python3
"""
CloudWatch Metrics Analysis for Right-Sizing
Deep-dive into resource utilization metrics
"""

import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
import matplotlib.pyplot as plt

class CloudWatchMetricsAnalyzer:
    """Analyze CloudWatch metrics for right-sizing decisions"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.redshift = boto3.client('redshift', region_name=region)

    def get_ec2_utilization(self, instance_id: str, days: int = 30) -> Dict:
        """
        Get detailed EC2 utilization metrics

        Args:
            instance_id: EC2 instance ID
            days: Number of days to analyze

        Returns:
            Dictionary with utilization statistics
        """
        print(f"\n📊 Analyzing EC2 instance: {instance_id}")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        metrics = {'instance_id': instance_id}

        # CPU Utilization
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        if cpu_response['Datapoints']:
            cpu_values = sorted([dp['Average'] for dp in cpu_response['Datapoints']])
            metrics['cpu_avg'] = np.mean(cpu_values)
            metrics['cpu_median'] = np.median(cpu_values)
            metrics['cpu_p50'] = np.percentile(cpu_values, 50)
            metrics['cpu_p95'] = np.percentile(cpu_values, 95)
            metrics['cpu_p99'] = np.percentile(cpu_values, 99)
            metrics['cpu_max'] = np.max(cpu_values)
            metrics['cpu_min'] = np.min(cpu_values)
            metrics['cpu_std'] = np.std(cpu_values)

            print(f"   CPU: avg={metrics['cpu_avg']:.1f}%, p95={metrics['cpu_p95']:.1f}%, max={metrics['cpu_max']:.1f}%")
        else:
            print("   ⚠️  No CPU metrics available")

        # Network In/Out
        network_in_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='NetworkIn',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        if network_in_response['Datapoints']:
            network_values = [dp['Average'] / (1024**2) for dp in network_in_response['Datapoints']]  # Convert to MB
            metrics['network_in_avg_mb'] = np.mean(network_values)
            metrics['network_in_p95_mb'] = np.percentile(network_values, 95)

            print(f"   Network In: avg={metrics['network_in_avg_mb']:.2f} MB/s, p95={metrics['network_in_p95_mb']:.2f} MB/s")

        # Disk I/O (EBS)
        disk_read_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='DiskReadOps',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        if disk_read_response['Datapoints']:
            disk_values = [dp['Average'] for dp in disk_read_response['Datapoints']]
            metrics['disk_read_ops_avg'] = np.mean(disk_values)
            metrics['disk_read_ops_p95'] = np.percentile(disk_values, 95)

            print(f"   Disk Read: avg={metrics['disk_read_ops_avg']:.0f} ops/s, p95={metrics['disk_read_ops_p95']:.0f} ops/s")

        return metrics

    def get_rds_utilization(self, db_instance_id: str, days: int = 14) -> Dict:
        """
        Get detailed RDS utilization metrics

        Args:
            db_instance_id: RDS instance identifier
            days: Number of days to analyze

        Returns:
            Dictionary with utilization statistics
        """
        print(f"\n📊 Analyzing RDS instance: {db_instance_id}")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        metrics = {'db_instance_id': db_instance_id}

        # CPU Utilization
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        if cpu_response['Datapoints']:
            cpu_values = sorted([dp['Average'] for dp in cpu_response['Datapoints']])
            metrics['cpu_avg'] = np.mean(cpu_values)
            metrics['cpu_p95'] = np.percentile(cpu_values, 95)
            metrics['cpu_max'] = np.max(cpu_values)

            print(f"   CPU: avg={metrics['cpu_avg']:.1f}%, p95={metrics['cpu_p95']:.1f}%, max={metrics['cpu_max']:.1f}%")

        # Database Connections
        conn_response = self.cloudwatch.get_metric_statistics(
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

            print(f"   Connections: avg={metrics['connections_avg']:.0f}, max={metrics['connections_max']:.0f}")

        # IOPS
        for metric_name in ['ReadIOPS', 'WriteIOPS']:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )

            if response['Datapoints']:
                values = [dp['Average'] for dp in response['Datapoints']]
                key = metric_name.lower().replace('iops', '_iops')
                metrics[f'{key}_avg'] = np.mean(values)
                metrics[f'{key}_p95'] = np.percentile(values, 95)

        if 'readiops_avg' in metrics:
            print(f"   Read IOPS: avg={metrics['readiops_avg']:.0f}, p95={metrics['readiops_p95']:.0f}")
        if 'writeiops_avg' in metrics:
            print(f"   Write IOPS: avg={metrics['writeiops_avg']:.0f}, p95={metrics['writeiops_p95']:.0f}")

        return metrics

    def get_redshift_utilization(self, cluster_id: str, days: int = 14) -> Dict:
        """Get Redshift cluster utilization metrics"""
        print(f"\n📊 Analyzing Redshift cluster: {cluster_id}")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        metrics = {'cluster_id': cluster_id}

        # CPU
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        if cpu_response['Datapoints']:
            cpu_values = sorted([dp['Average'] for dp in cpu_response['Datapoints']])
            metrics['cpu_avg'] = np.mean(cpu_values)
            metrics['cpu_p95'] = np.percentile(cpu_values, 95)

            print(f"   CPU: avg={metrics['cpu_avg']:.1f}%, p95={metrics['cpu_p95']:.1f}%")

        # Disk space usage
        disk_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='PercentageDiskSpaceUsed',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        if disk_response['Datapoints']:
            disk_values = [dp['Average'] for dp in disk_response['Datapoints']]
            metrics['disk_avg'] = np.mean(disk_values)
            metrics['disk_max'] = max(dp['Maximum'] for dp in disk_response['Datapoints'])

            print(f"   Disk: avg={metrics['disk_avg']:.1f}%, max={metrics['disk_max']:.1f}%")

        return metrics

    def analyze_all_ec2_instances(self, days: int = 30) -> pd.DataFrame:
        """Analyze all running EC2 instances"""
        print("\n🔍 Scanning all EC2 instances...")

        instances = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )

        all_metrics = []

        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']

                # Get tags
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                name = tags.get('Name', 'N/A')

                metrics = self.get_ec2_utilization(instance_id, days)
                metrics['instance_type'] = instance_type
                metrics['name'] = name

                all_metrics.append(metrics)

        df = pd.DataFrame(all_metrics)

        if not df.empty:
            print(f"\n✅ Analyzed {len(df)} instances")

            # Summary stats
            print("\n   Average utilization across all instances:")
            if 'cpu_avg' in df.columns:
                print(f"     CPU avg: {df['cpu_avg'].mean():.1f}%")
                print(f"     CPU p95: {df['cpu_p95'].mean():.1f}%")

            # Identify opportunities
            if 'cpu_p95' in df.columns:
                over_prov = df[df['cpu_p95'] < 40]
                under_prov = df[df['cpu_p95'] > 80]

                print(f"\n   📉 Over-provisioned (p95 <40%): {len(over_prov)} instances")
                print(f"   📈 Under-provisioned (p95 >80%): {len(under_prov)} instances")
                print(f"   ✅ Well-sized (p95 40-80%): {len(df) - len(over_prov) - len(under_prov)} instances")

        return df

    def plot_utilization_dashboard(self, instance_id: str, days: int = 30):
        """Create utilization dashboard for an instance"""
        print(f"\n📈 Creating utilization dashboard for {instance_id}...")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Get CPU time series
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )

        if not cpu_response['Datapoints']:
            print("   ⚠️  No data available for dashboard")
            return

        # Prepare data
        datapoints = sorted(cpu_response['Datapoints'], key=lambda x: x['Timestamp'])
        timestamps = [dp['Timestamp'] for dp in datapoints]
        cpu_values = [dp['Average'] for dp in datapoints]

        # Create dashboard
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Resource Utilization: {instance_id}', fontsize=16, fontweight='bold')

        # Plot 1: CPU over time
        axes[0, 0].plot(timestamps, cpu_values, label='CPU %', linewidth=2)
        axes[0, 0].axhline(y=80, color='orange', linestyle='--', label='High (80%)', alpha=0.7)
        axes[0, 0].axhline(y=20, color='red', linestyle='--', label='Low (20%)', alpha=0.7)
        axes[0, 0].fill_between(timestamps, 20, 80, alpha=0.1, color='green', label='Target Range')
        axes[0, 0].set_title('CPU Utilization Over Time', fontsize=12, fontweight='bold')
        axes[0, 0].set_ylabel('Percentage (%)')
        axes[0, 0].legend(loc='upper left')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Plot 2: CPU distribution histogram
        axes[0, 1].hist(cpu_values, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(x=np.mean(cpu_values), color='red', linestyle='--',
                           linewidth=2, label=f'Mean: {np.mean(cpu_values):.1f}%')
        axes[0, 1].axvline(x=np.percentile(cpu_values, 95), color='orange', linestyle='--',
                           linewidth=2, label=f'P95: {np.percentile(cpu_values, 95):.1f}%')
        axes[0, 1].set_title('CPU Distribution', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('CPU Utilization (%)')
        axes[0, 1].set_ylabel('Frequency (hours)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # Plot 3: CPU percentiles box plot
        axes[1, 0].boxplot([cpu_values], labels=['CPU'], patch_artist=True,
                           boxprops=dict(facecolor='lightblue'))
        axes[1, 0].axhline(y=80, color='orange', linestyle='--', alpha=0.7)
        axes[1, 0].axhline(y=20, color='red', linestyle='--', alpha=0.7)
        axes[1, 0].set_title('CPU Box Plot', fontsize=12, fontweight='bold')
        axes[1, 0].set_ylabel('CPU Utilization (%)')
        axes[1, 0].grid(True, alpha=0.3, axis='y')

        # Plot 4: Summary statistics
        axes[1, 1].axis('off')

        summary_text = f"""
        UTILIZATION SUMMARY ({days} days)

        CPU Statistics:
          • Mean:     {np.mean(cpu_values):.1f}%
          • Median:   {np.median(cpu_values):.1f}%
          • Std Dev:  {np.std(cpu_values):.1f}%
          • P50:      {np.percentile(cpu_values, 50):.1f}%
          • P95:      {np.percentile(cpu_values, 95):.1f}%
          • P99:      {np.percentile(cpu_values, 99):.1f}%
          • Min:      {np.min(cpu_values):.1f}%
          • Max:      {np.max(cpu_values):.1f}%

        Right-Sizing Decision:
        """

        p95 = np.percentile(cpu_values, 95)
        avg = np.mean(cpu_values)

        if p95 < 40 and avg < 20:
            recommendation = "  ⚠️  OVER-PROVISIONED\n  → Downsize (2x smaller)\n  → Expected savings: 50%"
        elif p95 > 80 or avg > 70:
            recommendation = "  ⚠️  UNDER-PROVISIONED\n  → Upsize for performance\n  → Risk: Outages possible"
        else:
            recommendation = "  ✅ WELL-SIZED\n  → No action needed\n  → Monitor quarterly"

        summary_text += recommendation

        axes[1, 1].text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                       verticalalignment='center')

        plt.tight_layout()
        output_file = f'utilization-{instance_id}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"   📁 Dashboard saved: {output_file}")

        plt.close()

    def analyze_all_rds_instances(self, days: int = 14) -> pd.DataFrame:
        """Analyze all RDS instances"""
        print("\n🔍 Scanning all RDS instances...")

        db_instances = self.rds.describe_db_instances()

        all_metrics = []

        for db in db_instances['DBInstances']:
            db_id = db['DBInstanceIdentifier']
            instance_class = db['DBInstanceClass']
            engine = db['Engine']

            metrics = self.get_rds_utilization(db_id, days)
            metrics['instance_class'] = instance_class
            metrics['engine'] = engine

            all_metrics.append(metrics)

        df = pd.DataFrame(all_metrics)

        if not df.empty:
            print(f"\n✅ Analyzed {len(df)} RDS instances")

            if 'cpu_avg' in df.columns:
                print(f"   Average CPU: {df['cpu_avg'].mean():.1f}%")
                print(f"   Average P95: {df['cpu_p95'].mean():.1f}%")

            # Recommendations
            if 'cpu_p95' in df.columns:
                over_prov = df[df['cpu_p95'] < 40]
                print(f"\n   💡 Over-provisioned: {len(over_prov)} databases")
                for idx, row in over_prov.iterrows():
                    print(f"     {row['db_instance_id']} ({row['instance_class']}): p95={row['cpu_p95']:.1f}%")

        return df

def main():
    """Main CloudWatch analysis workflow"""
    print("=" * 70)
    print("CloudWatch Metrics Analysis for Right-Sizing")
    print("=" * 70)

    analyzer = CloudWatchMetricsAnalyzer()

    # Step 1: Analyze all EC2 instances
    print("\n[Step 1/3] Analyzing all EC2 instances (30 days)...")
    ec2_df = analyzer.analyze_all_ec2_instances(days=30)

    if not ec2_df.empty:
        ec2_df.to_csv('ec2-utilization-analysis.csv', index=False)
        print("\n   📁 Saved: ec2-utilization-analysis.csv")

        # Create dashboard for most over-provisioned instance
        if 'cpu_p95' in ec2_df.columns:
            lowest_util = ec2_df.nsmallest(1, 'cpu_p95')
            if not lowest_util.empty:
                most_over_prov = lowest_util.iloc[0]['instance_id']
                print(f"\n   Creating dashboard for most over-provisioned: {most_over_prov}")
                analyzer.plot_utilization_dashboard(most_over_prov, days=30)

    # Step 2: Analyze all RDS instances
    print("\n[Step 2/3] Analyzing all RDS instances (14 days)...")
    rds_df = analyzer.analyze_all_rds_instances(days=14)

    if not rds_df.empty:
        rds_df.to_csv('rds-utilization-analysis.csv', index=False)
        print("   📁 Saved: rds-utilization-analysis.csv")

    # Step 3: Analyze Redshift clusters
    print("\n[Step 3/3] Analyzing Redshift clusters...")

    try:
        clusters = analyzer.redshift.describe_clusters()

        for cluster in clusters['Clusters']:
            cluster_id = cluster['ClusterIdentifier']
            metrics = analyzer.get_redshift_utilization(cluster_id, days=14)
    except Exception as e:
        print(f"   ℹ️  No Redshift clusters found or error: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ CloudWatch Analysis Complete!")
    print("=" * 70)

    print("\n📊 Files Generated:")
    print("   • ec2-utilization-analysis.csv")
    print("   • rds-utilization-analysis.csv")
    print("   • utilization-*.png (dashboards)")

    print("\n💡 Next Steps:")
    print("   1. Review CSV files for utilization patterns")
    print("   2. Focus on instances with p95 <40% (over-provisioned)")
    print("   3. Use recommendations.py to generate sizing suggestions")
    print("   4. Test changes in development environment first")

if __name__ == '__main__':
    main()
