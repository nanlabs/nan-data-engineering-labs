#!/usr/bin/env python3
"""
Right-Sizing Recommendations and Implementation
Generate recommendations and apply instance resizing
"""

import boto3
import pandas as pd
from typing import Dict

class RightSizingRecommender:
    """Generate and apply right-sizing recommendations"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.ec2 = boto3.client('ec2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.redshift = boto3.client('redshift', region_name=region)
        self.autoscaling = boto3.client('autoscaling', region_name=region)

    # EC2 instance family pricing (simplified for m5, c5, r5 families)
    EC2_PRICING = {
        # m5 family (general purpose)
        'm5.large': 70.08,      # $0.096/hour
        'm5.xlarge': 140.16,    # $0.192/hour
        'm5.2xlarge': 280.32,
        'm5.4xlarge': 560.64,
        # c5 family (compute optimized)
        'c5.large': 62.05,      # $0.085/hour
        'c5.xlarge': 124.10,    # $0.170/hour
        'c5.2xlarge': 248.20,
        'c5.4xlarge': 496.40,
        # r5 family (memory optimized)
        'r5.large': 91.98,      # $0.126/hour
        'r5.xlarge': 183.96,    # $0.252/hour
        'r5.2xlarge': 367.92,
        'r5.4xlarge': 735.84
    }

    RDS_PRICING = {
        # db.m5 family
        'db.m5.large': 122.63,
        'db.m5.xlarge': 245.25,
        'db.m5.2xlarge': 490.50,
        'db.m5.4xlarge': 981.00,
        # db.r5 family
        'db.r5.large': 183.96,
        'db.r5.xlarge': 367.92,
        'db.r5.2xlarge': 735.84,
        'db.r5.4xlarge': 1471.68
    }

    def generate_ec2_recommendations(self, utilization_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate EC2 right-sizing recommendations based on utilization

        Args:
            utilization_df: DataFrame from CloudWatchMetricsAnalyzer

        Returns:
            DataFrame with recommendations
        """
        print("\n🔍 Generating EC2 right-sizing recommendations...")

        recommendations = []

        for idx, row in utilization_df.iterrows():
            instance_id = row.get('instance_id', 'Unknown')
            current_type = row.get('instance_type', 'Unknown')
            cpu_avg = row.get('cpu_avg', 50)
            cpu_p95 = row.get('cpu_p95', 50)
            name = row.get('name', 'N/A')

            # Decision logic based on utilization
            recommendation = self._get_sizing_recommendation(current_type, cpu_avg, cpu_p95)

            if recommendation['action'] != 'keep':
                current_cost = self.EC2_PRICING.get(current_type, 0)
                new_cost = self.EC2_PRICING.get(recommendation['new_type'], 0)
                monthly_savings = current_cost - new_cost
                savings_pct = (monthly_savings / current_cost * 100) if current_cost > 0 else 0

                recommendations.append({
                    'InstanceId': instance_id,
                    'Name': name,
                    'CurrentType': current_type,
                    'RecommendedType': recommendation['new_type'],
                    'Action': recommendation['action'],
                    'Reason': recommendation['reason'],
                    'CPU_Avg': cpu_avg,
                    'CPU_P95': cpu_p95,
                    'CurrentCost': current_cost,
                    'NewCost': new_cost,
                    'MonthlySavings': monthly_savings,
                    'SavingsPercent': savings_pct,
                    'Risk': recommendation['risk']
                })

        df = pd.DataFrame(recommendations)

        if not df.empty:
            # Sort by savings
            df = df.sort_values('MonthlySavings', ascending=False)

            print(f"✅ Generated {len(df)} recommendations")
            print(f"   Total potential savings: ${df['MonthlySavings'].sum():,.2f}/month")
            print("\n   Top 5 opportunities:\n")

            for idx, row in df.head(5).iterrows():
                print(f"     {row['InstanceId']} ({row['Name']}):")
                print(f"       {row['CurrentType']} → {row['RecommendedType']}")
                print(f"       Savings: ${row['MonthlySavings']:.2f}/month ({row['SavingsPercent']:.1f}%)")
                print(f"       Risk: {row['Risk']}")
        else:
            print("✅ All instances are well-sized!")

        return df

    def _get_sizing_recommendation(self, current_type: str, cpu_avg: float, cpu_p95: float) -> Dict:
        """Determine right-sizing recommendation"""

        # Over-provisioned: Low CPU usage
        if cpu_p95 < 40 and cpu_avg < 20:
            new_type = self._downsize_instance(current_type)
            return {
                'action': 'downsize',
                'new_type': new_type,
                'reason': f'Low utilization (avg={cpu_avg:.1f}%, p95={cpu_p95:.1f}%)',
                'risk': 'Low'
            }

        # Under-provisioned: High CPU usage
        elif cpu_p95 > 85:
            new_type = self._upsize_instance(current_type)
            return {
                'action': 'upsize',
                'new_type': new_type,
                'reason': f'High utilization (p95={cpu_p95:.1f}%) - performance risk',
                'risk': 'Medium'
            }

        # Well-sized
        else:
            return {
                'action': 'keep',
                'new_type': current_type,
                'reason': 'Well-sized',
                'risk': 'None'
            }

    def _downsize_instance(self, current_type: str) -> str:
        """Determine one size smaller instance type"""
        size_map = {
            '4xlarge': '2xlarge',
            '2xlarge': 'xlarge',
            'xlarge': 'large',
            'large': 'medium'
        }

        for size, smaller in size_map.items():
            if size in current_type:
                return current_type.replace(size, smaller)

        return current_type  # Can't downsize further

    def _upsize_instance(self, current_type: str) -> str:
        """Determine one size larger instance type"""
        size_map = {
            'medium': 'large',
            'large': 'xlarge',
            'xlarge': '2xlarge',
            '2xlarge': '4xlarge'
        }

        for size, larger in size_map.items():
            if size in current_type and larger not in current_type:
                return current_type.replace(size, larger)

        return current_type  # Already at max size we support

    def right_size_instance(
        self,
        instance_id: str,
        new_instance_type: str,
        dry_run: bool = True
    ) -> bool:
        """
        Resize EC2 instance (stop, modify, start)

        Args:
            instance_id: EC2 instance ID
            new_instance_type: Target instance type
            dry_run: If True, only show what would be done

        Returns:
            True if successful
        """
        print(f"\n🔧 Right-sizing instance: {instance_id}")

        # Get current state
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            current_type = instance['InstanceType']
            current_state = instance['State']['Name']

            print(f"   Current: {current_type} ({current_state})")
            print(f"   Target: {new_instance_type}")

        except Exception as e:
            print(f"❌ Instance not found: {e}")
            return False

        if dry_run:
            print("\n   [DRY RUN] No changes made")
            print("   To apply: Set dry_run=False")
            return True

        try:
            # Step 1: Stop instance if running
            if current_state == 'running':
                print("\n   Step 1/3: Stopping instance...")
                self.ec2.stop_instances(InstanceIds=[instance_id])

                waiter = self.ec2.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[instance_id])
                print("   ✅ Instance stopped")

            # Step 2: Modify instance type
            print(f"\n   Step 2/3: Changing type to {new_instance_type}...")
            self.ec2.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceType={'Value': new_instance_type}
            )
            print("   ✅ Instance type modified")

            # Step 3: Start instance
            print("\n   Step 3/3: Starting instance...")
            self.ec2.start_instances(InstanceIds=[instance_id])

            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            print("   ✅ Instance running")

            print("\n✅ Right-sizing complete!")
            return True

        except Exception as e:
            print(f"❌ Error during right-sizing: {e}")
            return False

    def bulk_right_size(
        self,
        recommendations_df: pd.DataFrame,
        auto_approve: bool = False,
        dry_run: bool = True
    ) -> Dict:
        """
        Apply multiple right-sizing changes with confirmation

        Args:
            recommendations_df: DataFrame with recommendations
            auto_approve: Skip confirmation prompt
            dry_run: Only simulate changes

        Returns:
            Summary dict
        """
        if recommendations_df.empty:
            print("✅ No recommendations to apply")
            return {'applied': 0, 'failed': 0, 'savings': 0}

        # Filter to only downsize actions (safer)
        downsizes = recommendations_df[recommendations_df['Action'] == 'downsize']

        if downsizes.empty:
            print("✅ No downsize recommendations")
            return {'applied': 0, 'failed': 0, 'savings': 0}

        print("\n📋 Bulk Right-Sizing Plan:\n")

        total_savings = downsizes['MonthlySavings'].sum()

        for idx, row in downsizes.iterrows():
            print(f"  • {row['InstanceId']} ({row['Name']})")
            print(f"    {row['CurrentType']} → {row['RecommendedType']}")
            print(f"    Savings: ${row['MonthlySavings']:.2f}/month")
            print(f"    Risk: {row['Risk']}")
            print()

        print(f"💰 Total Monthly Savings: ${total_savings:.2f}")
        print(f"💰 Annual Savings: ${total_savings * 12:.2f}")

        if not auto_approve:
            response = input(f"\n  Proceed with {len(downsizes)} changes? (yes/no): ")
            if response.lower() != 'yes':
                print("  ❌ Cancelled by user")
                return {'applied': 0, 'failed': 0, 'savings': 0}

        # Apply changes
        print("\n  🚀 Applying right-sizing changes...")

        applied = 0
        failed = 0

        for idx, row in downsizes.iterrows():
            success = self.right_size_instance(
                row['InstanceId'],
                row['RecommendedType'],
                dry_run=dry_run
            )

            if success:
                applied += 1
                print(f"  ✅ {row['InstanceId']}")
            else:
                failed += 1
                print(f"  ❌ {row['InstanceId']}")

        return {
            'applied': applied,
            'failed': failed,
            'monthly_savings': total_savings,
            'annual_savings': total_savings * 12
        }

    def generate_savings_report(
        self,
        before_analysis: Dict,
        after_analysis: Dict
    ):
        """
        Generate comprehensive savings report

        Args:
            before_analysis: Cost breakdown before right-sizing
            after_analysis: Cost breakdown after right-sizing
        """
        print("\n" + "=" * 70)
        print("         RIGHT-SIZING SAVINGS REPORT")
        print("=" * 70)

        # EC2 Savings
        ec2_before = sum(item['monthly_cost'] for item in before_analysis.get('ec2', []))
        ec2_after = sum(item['monthly_cost'] for item in after_analysis.get('ec2', []))
        ec2_savings = ec2_before - ec2_after
        ec2_pct = (ec2_savings / ec2_before * 100) if ec2_before > 0 else 0

        print("\n1. EC2 Instances:")
        print(f"   Before:  ${ec2_before:,.2f}/month")
        print(f"   After:   ${ec2_after:,.2f}/month")
        print(f"   Savings: ${ec2_savings:,.2f}/month ({ec2_pct:.1f}%)")

        if len(before_analysis.get('ec2', [])) > 0:
            print("\n   Details:")
            for i, (before_item, after_item) in enumerate(zip(before_analysis['ec2'], after_analysis['ec2']), 1):
                before_cost = before_item['monthly_cost']
                after_cost = after_item['monthly_cost']
                savings = before_cost - after_cost
                print(f"     {i}. {before_item['instance_id']}: {before_item['type']} → {after_item['type']}")
                print(f"        ${before_cost:.2f} → ${after_cost:.2f} (save ${savings:.2f})")

        # RDS Savings
        rds_before = sum(item['monthly_cost'] for item in before_analysis.get('rds', []))
        rds_after = sum(item['monthly_cost'] for item in after_analysis.get('rds', []))
        rds_savings = rds_before - rds_after
        rds_pct = (rds_savings / rds_before * 100) if rds_before > 0 else 0

        print("\n2. RDS Instances:")
        print(f"   Before:  ${rds_before:,.2f}/month")
        print(f"   After:   ${rds_after:,.2f}/month")
        print(f"   Savings: ${rds_savings:,.2f}/month ({rds_pct:.1f}%)")

        # Redshift Savings
        redshift_before = sum(item['monthly_cost'] for item in before_analysis.get('redshift', []))
        redshift_after = sum(item['monthly_cost'] for item in after_analysis.get('redshift', []))
        redshift_savings = redshift_before - redshift_after
        redshift_pct = (redshift_savings / redshift_before * 100) if redshift_before > 0 else 0

        print("\n3. Redshift Clusters:")
        print(f"   Before:  ${redshift_before:,.2f}/month")
        print(f"   After:   ${redshift_after:,.2f}/month")
        print(f"   Savings: ${redshift_savings:,.2f}/month ({redshift_pct:.1f}%)")

        # Total
        total_before = ec2_before + rds_before + redshift_before
        total_after = ec2_after + rds_after + redshift_after
        total_savings = total_before - total_after
        total_pct = (total_savings / total_before * 100) if total_before > 0 else 0

        print("\n" + "=" * 70)
        print("TOTAL SAVINGS")
        print("=" * 70)
        print(f"  Monthly Before:  ${total_before:,.2f}")
        print(f"  Monthly After:   ${total_after:,.2f}")
        print(f"  Monthly Savings: ${total_savings:,.2f} ({total_pct:.1f}%)")
        print(f"  Annual Savings:  ${total_savings * 12:,.2f}")
        print("=" * 70)

        # ROI Analysis
        implementation_hours = 8
        hourly_rate = 100
        implementation_cost = implementation_hours * hourly_rate

        if total_savings > 0:
            payback_months = implementation_cost / total_savings
            first_year_roi = ((total_savings * 12) - implementation_cost) / implementation_cost * 100

            print("\n📊 ROI Analysis:")
            print(f"   Implementation Cost: ${implementation_cost:.2f} ({implementation_hours} hours)")
            print(f"   Payback Period: {payback_months:.1f} months")
            print(f"   First Year ROI: {first_year_roi:.0f}%")
            print(f"   3-Year Savings: ${total_savings * 36:,.2f}")

        # Export report
        report_data = {
            'Category': ['EC2', 'RDS', 'Redshift', 'TOTAL'],
            'Before_Monthly': [ec2_before, rds_before, redshift_before, total_before],
            'After_Monthly': [ec2_after, rds_after, redshift_after, total_after],
            'Monthly_Savings': [ec2_savings, rds_savings, redshift_savings, total_savings],
            'Savings_Percent': [ec2_pct, rds_pct, redshift_pct, total_pct],
            'Annual_Savings': [ec2_savings * 12, rds_savings * 12, redshift_savings * 12, total_savings * 12]
        }

        report_df = pd.DataFrame(report_data)
        report_df.to_csv('right-sizing-savings-report.csv', index=False)
        print("\n   📁 Report saved: right-sizing-savings-report.csv")

    def create_auto_scaling_policy(
        self,
        asg_name: str,
        target_cpu: int = 70,
        scale_out_cooldown: int = 60,
        scale_in_cooldown: int = 300
    ):
        """
        Create target tracking Auto Scaling policy

        Args:
            asg_name: Auto Scaling Group name
            target_cpu: Target CPU percentage
            scale_out_cooldown: Seconds before scaling out again
            scale_in_cooldown: Seconds before scaling in again
        """
        print(f"\n⚙️  Creating Auto Scaling policy for {asg_name}...")

        try:
            response = self.autoscaling.put_scaling_policy(
                AutoScalingGroupName=asg_name,
                PolicyName='target-tracking-cpu',
                PolicyType='TargetTrackingScaling',
                TargetTrackingConfiguration={
                    'PredefinedMetricSpecification': {
                        'PredefinedMetricType': 'ASGAverageCPUUtilization'
                    },
                    'TargetValue': float(target_cpu),
                    'ScaleInCooldown': scale_in_cooldown,
                    'ScaleOutCooldown': scale_out_cooldown
                }
            )

            print("✅ Target tracking policy created")
            print(f"   Target: {target_cpu}% CPU")
            print(f"   Scale out: When CPU > {target_cpu}% (cooldown: {scale_out_cooldown}s)")
            print(f"   Scale in: When CPU < {target_cpu}% (cooldown: {scale_in_cooldown}s)")
            print("\n   💰 Auto Scaling Benefits:")
            print("     • Pay only for capacity you need")
            print("     • Typical savings: 20-40% vs fixed capacity")
            print("     • Automatic adjustment to demand")

            return response

        except Exception as e:
            print(f"❌ Error creating policy: {e}")
            return None

def main():
    """Main right-sizing workflow"""
    print("=" * 70)
    print("Right-Sizing Recommendations and Implementation")
    print("=" * 70)

    recommender = RightSizingRecommender()

    # Note: This would normally read from cloudwatch_metrics.py output
    # For demo, using sample data

    print("\n[Step 1/3] Loading utilization data...")

    # Sample utilization data (would come from CloudWatch analysis)
    sample_utilization = pd.DataFrame([
        {'instance_id': 'i-001', 'name': 'web-server-01', 'instance_type': 'm5.2xlarge', 'cpu_avg': 18, 'cpu_p95': 35},
        {'instance_id': 'i-002', 'name': 'api-server-01', 'instance_type': 'm5.xlarge', 'cpu_avg': 15, 'cpu_p95': 28},
        {'instance_id': 'i-003', 'name': 'worker-01', 'instance_type': 'c5.2xlarge', 'cpu_avg': 55, 'cpu_p95': 75},
        {'instance_id': 'i-004', 'name': 'db-cache-01', 'instance_type': 'r5.xlarge', 'cpu_avg': 12, 'cpu_p95': 22}
    ])

    print(f"✅ Loaded {len(sample_utilization)} instances")

    # Step 2: Generate recommendations
    print("\n[Step 2/3] Generating right-sizing recommendations...")
    recommendations_df = recommender.generate_ec2_recommendations(sample_utilization)

    if not recommendations_df.empty:
        recommendations_df.to_csv('right-sizing-recommendations.csv', index=False)
        print("\n   📁 Saved: right-sizing-recommendations.csv")

    # Step 3: Generate savings report
    print("\n[Step 3/3] Generating savings report...")

    before = {
        'ec2': [
            {'instance_id': 'i-001', 'type': 'm5.2xlarge', 'monthly_cost': 280.32},
            {'instance_id': 'i-002', 'type': 'm5.xlarge', 'monthly_cost': 140.16},
            {'instance_id': 'i-003', 'type': 'c5.2xlarge', 'monthly_cost': 248.20},
            {'instance_id': 'i-004', 'type': 'r5.xlarge', 'monthly_cost': 183.96}
        ],
        'rds': [
            {'db_id': 'prod-db', 'class': 'db.r5.2xlarge', 'monthly_cost': 735.84}
        ],
        'redshift': []
    }

    after = {
        'ec2': [
            {'instance_id': 'i-001', 'type': 'm5.xlarge', 'monthly_cost': 140.16},  # -50%
            {'instance_id': 'i-002', 'type': 'm5.large', 'monthly_cost': 70.08},    # -50%
            {'instance_id': 'i-003', 'type': 'c5.2xlarge', 'monthly_cost': 248.20}, # No change
            {'instance_id': 'i-004', 'type': 'r5.large', 'monthly_cost': 91.98}     # -50%
        ],
        'rds': [
            {'db_id': 'prod-db', 'class': 'db.r5.xlarge', 'monthly_cost': 367.92}  # -50%
        ],
        'redshift': []
    }

    recommender.generate_savings_report(before, after)

    # Summary
    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)

    print("\n💡 Right-Sizing Best Practices:")
    print("   1. Use P95 metrics (not average) for sizing decisions")
    print("   2. Test changes in development first")
    print("   3. Monitor performance for 1 week after changes")
    print("   4. Downsize gradually (2xl → xl → large)")
    print("   5. Keep CloudWatch alarms active")

    print("\n⚠️  When to Right-Size:")
    print("   ✅ Non-production (dev/test): Aggressive downsizing")
    print("   ✅ Batch workloads: Match size to workload")
    print("   ⚠️  Production APIs: Conservative, test thoroughly")
    print("   ❌ Critical databases: Only if CPU consistently <30%")

if __name__ == '__main__':
    main()
