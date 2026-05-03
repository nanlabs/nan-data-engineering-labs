#!/usr/bin/env python3
"""
S3 Storage Analytics and Optimization
Analyze storage patterns and calculate optimization opportunities
"""

import boto3
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List
import sys

# Set plotting style
sns.set_style('whitegrid')

class StorageAnalyticsManager:
    """Analyze S3 storage patterns and calculate optimization opportunities"""

    PRICING = {
        'STANDARD': 0.023,
        'STANDARD_IA': 0.0125,
        'ONEZONE_IA': 0.01,
        'INTELLIGENT_TIERING': 0.023,
        'GLACIER_IR': 0.004,
        'GLACIER': 0.0036,
        'DEEP_ARCHIVE': 0.00099
    }

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.s3 = boto3.client('s3', region_name=region)
        self.s3control = boto3.client('s3control', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity()['Account']

    def get_bucket_storage_metrics(self, bucket_name: str) -> Dict:
        """
        Get storage metrics for a bucket from CloudWatch

        Args:
            bucket_name: S3 bucket name

        Returns:
            Dict with storage metrics
        """
        # Get bucket size
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=datetime.now() - timedelta(days=2),
                EndTime=datetime.now(),
                Period=86400,
                Statistics=['Average']
            )

            size_bytes = response['Datapoints'][0]['Average'] if response['Datapoints'] else 0
            size_gb = size_bytes / (1024**3)

        except Exception as e:
            print(f"  ⚠️  Could not get size for {bucket_name}: {e}")
            size_gb = 0

        # Get object count
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='NumberOfObjects',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                ],
                StartTime=datetime.now() - timedelta(days=2),
                EndTime=datetime.now(),
                Period=86400,
                Statistics=['Average']
            )

            object_count = int(response['Datapoints'][0]['Average']) if response['Datapoints'] else 0

        except Exception as e:
            print(f"  ⚠️  Could not get object count for {bucket_name}: {e}")
            object_count = 0

        # Calculate current monthly cost
        monthly_cost = size_gb * self.PRICING['STANDARD']

        return {
            'bucket': bucket_name,
            'size_gb': size_gb,
            'object_count': object_count,
            'monthly_cost': monthly_cost
        }

    def analyze_all_buckets(self) -> pd.DataFrame:
        """
        Analyze storage across all S3 buckets

        Returns:
            DataFrame with bucket analytics
        """
        print("\n📦 Analyzing all S3 buckets...")

        try:
            buckets = self.s3.list_buckets()['Buckets']
        except Exception as e:
            print(f"❌ Error listing buckets: {e}")
            return pd.DataFrame()

        analytics = []

        for bucket in buckets:
            bucket_name = bucket['Name']
            print(f"  Processing: {bucket_name}...")

            metrics = self.get_bucket_storage_metrics(bucket_name)

            # Get storage class distribution
            try:
                storage_class = self.analyze_storage_classes(bucket_name)
                metrics['storage_classes'] = storage_class
            except:
                metrics['storage_classes'] = {'STANDARD': 1.0}

            # Check lifecycle policy
            try:
                self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                metrics['has_lifecycle'] = True
            except:
                metrics['has_lifecycle'] = False

            # Check Intelligent-Tiering
            try:
                configs = self.s3.list_bucket_intelligent_tiering_configurations(Bucket=bucket_name)
                metrics['has_intelligent_tiering'] = len(configs.get('IntelligentTieringConfigurationList', [])) > 0
            except:
                metrics['has_intelligent_tiering'] = False

            analytics.append(metrics)

        df = pd.DataFrame(analytics)

        print(f"\n✅ Analyzed {len(df)} buckets")

        return df

    def analyze_storage_classes(self, bucket_name: str) -> Dict[str, float]:
        """
        Analyze distribution of objects across storage classes

        Args:
            bucket_name: S3 bucket name

        Returns:
            Dict with storage class percentages
        """
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)

            storage_classes = {}
            total_objects = 0

            for page in pages:
                for obj in page.get('Contents', []):
                    storage_class = obj.get('StorageClass', 'STANDARD')
                    storage_classes[storage_class] = storage_classes.get(storage_class, 0) + 1
                    total_objects += 1

                    if total_objects >= 1000:
                        break

                if total_objects >= 1000:
                    break

            # Convert to percentages
            if total_objects > 0:
                return {k: v / total_objects for k, v in storage_classes.items()}

        except Exception:
            pass

        return {'STANDARD': 1.0}

    def identify_optimization_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify buckets with optimization opportunities

        Args:
            df: DataFrame with bucket analytics

        Returns:
            List of optimization opportunities
        """
        print("\n🔍 Identifying optimization opportunities...")

        opportunities = []

        for idx, row in df.iterrows():
            bucket = row['bucket']
            size_gb = row['size_gb']
            current_cost = row['monthly_cost']

            # Skip small buckets
            if size_gb < 10:
                continue

            # Opportunity 1: No lifecycle policy
            if not row['has_lifecycle'] and size_gb > 100:
                # Assume 70% savings with lifecycle
                potential_savings = current_cost * 0.70

                opportunities.append({
                    'bucket': bucket,
                    'opportunity': 'Add lifecycle policy',
                    'current_cost': current_cost,
                    'potential_savings': potential_savings,
                    'priority': 'High' if size_gb > 1000 else 'Medium'
                })

            # Opportunity 2: No Intelligent-Tiering for medium buckets
            if not row['has_intelligent_tiering'] and not row['has_lifecycle'] and 10 < size_gb < 1000:
                # Assume 30% savings with Intelligent-Tiering
                potential_savings = current_cost * 0.30

                opportunities.append({
                    'bucket': bucket,
                    'opportunity': 'Enable Intelligent-Tiering',
                    'current_cost': current_cost,
                    'potential_savings': potential_savings,
                    'priority': 'Medium'
                })

            # Opportunity 3: All objects in Standard class
            storage_classes = row.get('storage_classes', {})
            if storage_classes.get('STANDARD', 0) > 0.9 and size_gb > 50:
                # High percentage in Standard, likely optimization opportunity
                potential_savings = current_cost * 0.50

                opportunities.append({
                    'bucket': bucket,
                    'opportunity': 'High % in Standard class',
                    'current_cost': current_cost,
                    'potential_savings': potential_savings,
                    'priority': 'High' if size_gb > 500 else 'Medium'
                })

        # Sort by potential savings
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)

        if opportunities:
            print(f"\n⚡ Found {len(opportunities)} optimization opportunities:\n")

            total_savings = sum(o['potential_savings'] for o in opportunities)

            for opp in opportunities[:10]:  # Show top 10
                print(f"  {opp['priority']} Priority: {opp['bucket']}")
                print(f"    Opportunity: {opp['opportunity']}")
                print(f"    Current Cost: ${opp['current_cost']:.2f}/month")
                print(f"    Potential Savings: ${opp['potential_savings']:.2f}/month")
                print()

            print(f"💰 Total Potential Savings: ${total_savings:.2f}/month (${total_savings * 12:.2f}/year)")
        else:
            print("✅ No major optimization opportunities found")

        return opportunities

    def generate_storage_report(self, df: pd.DataFrame, opportunities: List[Dict]):
        """Generate comprehensive storage optimization report"""
        print("\n📊 Generating storage optimization report...")

        # Overall statistics
        total_size = df['size_gb'].sum()
        total_cost = df['monthly_cost'].sum()
        total_objects = df['object_count'].sum()

        # Optimization status
        with_lifecycle = len(df[df['has_lifecycle'] == True])
        with_intelligent = len(df[df['has_intelligent_tiering'] == True])

        print("\n" + "=" * 70)
        print("STORAGE OPTIMIZATION REPORT")
        print("=" * 70)

        print("\n📊 Overall Statistics:")
        print(f"   Total Buckets: {len(df)}")
        print(f"   Total Storage: {total_size:.2f} GB")
        print(f"   Total Objects: {total_objects:,}")
        print(f"   Current Monthly Cost: ${total_cost:.2f}")

        print("\n⚙️  Optimization Status:")
        print(f"   Buckets with Lifecycle Policies: {with_lifecycle}/{len(df)} ({with_lifecycle/len(df)*100:.1f}%)")
        print(f"   Buckets with Intelligent-Tiering: {with_intelligent}/{len(df)} ({with_intelligent/len(df)*100:.1f}%)")

        if opportunities:
            total_potential = sum(o['potential_savings'] for o in opportunities)
            print("\n💰 Optimization Opportunities:")
            print(f"   Opportunities Found: {len(opportunities)}")
            print(f"   Potential Monthly Savings: ${total_potential:.2f}")
            print(f"   Potential Annual Savings: ${total_potential * 12:.2f}")
            print(f"   Potential Cost Reduction: {total_potential/total_cost*100:.1f}%")

        # Save report
        df.to_csv('storage-optimization-report.csv', index=False)

        if opportunities:
            pd.DataFrame(opportunities).to_csv('storage-opportunities.csv', index=False)

        print("\n📁 Reports saved:")
        print("   - storage-optimization-report.csv")
        if opportunities:
            print("   - storage-opportunities.csv")

def main():
    """Main storage analytics workflow"""
    print("=" * 70)
    print("S3 Storage Analytics and Optimization")
    print("=" * 70)

    manager = StorageAnalyticsManager()

    # Step 1: Analyze all buckets
    print("\n[Step 1/3] Analyzing all S3 buckets...")
    df = manager.analyze_all_buckets()

    if df.empty:
        print("⚠️  No buckets found or unable to analyze")
        sys.exit(0)

    # Show summary
    print("\n📊 Storage Summary:")
    print(f"   Total Storage: {df['size_gb'].sum():,.2f} GB")
    print(f"   Total Cost: ${df['monthly_cost'].sum():,.2f}/month")
    print(f"   Average per bucket: {df['size_gb'].mean():,.2f} GB")

    # Step 2: Identify opportunities
    print("\n[Step 2/3] Identifying optimization opportunities...")
    opportunities = manager.identify_optimization_opportunities(df)

    # Step 3: Generate report
    print("\n[Step 3/3] Generating comprehensive report...")
    manager.generate_storage_report(df, opportunities)

    # Summary
    print("\n" + "=" * 70)
    print("✅ Storage Analytics Complete!")
    print("=" * 70)

    if opportunities:
        print("\n📋 Recommended Actions:")
        high_priority = [o for o in opportunities if o['priority'] == 'High']
        if high_priority:
            print(f"\n   High Priority ({len(high_priority)} buckets):")
            for opp in high_priority[:5]:
                print(f"     1. {opp['bucket']}: {opp['opportunity']}")
                print(f"        Savings: ${opp['potential_savings']:.2f}/month")

        print("\n   Implementation Steps:")
        print("     1. Review opportunities in storage-opportunities.csv")
        print("     2. Start with High priority buckets (largest savings)")
        print("     3. Use lifecycle_policies.py to configure policies")
        print("     4. Use intelligent_tiering.py for unpredictable access")
        print("     5. Monitor with S3 Storage Lens after 24 hours")
    else:
        print("\n✅ Storage is well optimized!")

if __name__ == '__main__':
    main()
