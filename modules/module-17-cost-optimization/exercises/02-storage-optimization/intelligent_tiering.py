#!/usr/bin/env python3
"""
S3 Intelligent-Tiering Configuration
Enable automatic storage class optimization based on access patterns
"""

import boto3
from typing import Dict, List
from datetime import datetime
import sys

class IntelligentTieringManager:
    """Manage S3 Intelligent-Tiering configurations"""

    # Pricing per GB-month
    PRICING = {
        'frequent': 0.023,       # Same as Standard
        'infrequent': 0.0125,    # After 30 days no access
        'archive': 0.004,        # After 90 days no access
        'deep_archive': 0.00099  # After 180 days no access
    }

    MONITORING_FEE = 0.0025 / 1000  # Per object per month

    def __init__(self, region: str = 'us-east-1'):
        """Initialize S3 client"""
        self.s3 = boto3.client('s3', region_name=region)
        self.region = region

    def configure_intelligent_tiering(
        self,
        bucket_name: str,
        prefix: str = '',
        archive_days: int = 90,
        deep_archive_days: int = 180
    ):
        """
        Configure Intelligent-Tiering for a bucket or prefix

        Args:
            bucket_name: S3 bucket name
            prefix: Optional prefix filter
            archive_days: Days before moving to Archive Access tier
            deep_archive_days: Days before moving to Deep Archive Access tier
        """
        print(f"\n⚙️  Configuring Intelligent-Tiering for: {bucket_name}")
        if prefix:
            print(f"   Prefix: {prefix}")

        config_id = f'intelligent-tiering-{prefix.replace("/", "-") if prefix else "entire-bucket"}'

        tiering_config = {
            'Id': config_id,
            'Status': 'Enabled',
            'Tierings': [
                {
                    'Days': archive_days,
                    'AccessTier': 'ARCHIVE_ACCESS'
                },
                {
                    'Days': deep_archive_days,
                    'AccessTier': 'DEEP_ARCHIVE_ACCESS'
                }
            ]
        }

        # Add prefix filter if specified
        if prefix:
            tiering_config['Filter'] = {'Prefix': prefix}

        try:
            self.s3.put_bucket_intelligent_tiering_configuration(
                Bucket=bucket_name,
                Id=config_id,
                IntelligentTieringConfiguration=tiering_config
            )

            print(f"✅ Intelligent-Tiering configured: {config_id}")
            print(f"   Archive Access: After {archive_days} days")
            print(f"   Deep Archive Access: After {deep_archive_days} days")

            return config_id

        except Exception as e:
            print(f"❌ Error configuring Intelligent-Tiering: {e}")
            sys.exit(1)

    def list_intelligent_tiering_configs(self, bucket_name: str) -> List[Dict]:
        """
        List all Intelligent-Tiering configurations for a bucket

        Args:
            bucket_name: S3 bucket name

        Returns:
            List of configurations
        """
        print(f"\n🔍 Listing Intelligent-Tiering configurations for: {bucket_name}")

        try:
            response = self.s3.list_bucket_intelligent_tiering_configurations(
                Bucket=bucket_name
            )

            configs = response.get('IntelligentTieringConfigurationList', [])

            if configs:
                print(f"✅ Found {len(configs)} configuration(s):")
                for config in configs:
                    print(f"\n   ID: {config['Id']}")
                    print(f"   Status: {config['Status']}")
                    if 'Filter' in config:
                        print(f"   Filter: {config['Filter']}")
                    print("   Tierings:")
                    for tier in config['Tierings']:
                        print(f"     - {tier['Days']} days → {tier['AccessTier']}")
            else:
                print("⚠️  No Intelligent-Tiering configurations found")

            return configs

        except Exception as e:
            if 'NoSuchConfiguration' in str(e):
                print("⚠️  No Intelligent-Tiering configurations found")
                return []
            print(f"❌ Error listing configurations: {e}")
            return []

    def calculate_intelligent_tiering_savings(
        self,
        total_size_gb: float,
        access_pattern: Dict[str, float]
    ) -> Dict:
        """
        Calculate potential savings with Intelligent-Tiering

        Args:
            total_size_gb: Total storage size in GB
            access_pattern: Dict with percentage in each tier
                           {'frequent': 0.2, 'infrequent': 0.5, 'archive': 0.2, 'deep_archive': 0.1}

        Returns:
            Cost analysis dict
        """
        # Validate access pattern
        total_pct = sum(access_pattern.values())
        if abs(total_pct - 1.0) > 0.01:
            raise ValueError(f"Access pattern must sum to 1.0, got {total_pct}")

        # Calculate object count (assume average 10 MB per object)
        object_count = int(total_size_gb * 1024 / 10)

        # Current cost (all in Standard)
        current_cost = total_size_gb * self.PRICING['frequent']

        # Intelligent-Tiering cost
        storage_cost = sum(
            total_size_gb * pct * self.PRICING[tier]
            for tier, pct in access_pattern.items()
        )

        monitoring_cost = object_count * self.MONITORING_FEE

        intelligent_tiering_cost = storage_cost + monitoring_cost

        # Savings
        savings = current_cost - intelligent_tiering_cost
        savings_pct = (savings / current_cost) * 100 if current_cost > 0 else 0

        return {
            'total_size_gb': total_size_gb,
            'object_count': object_count,
            'current_cost_standard': current_cost,
            'intelligent_tiering_storage': storage_cost,
            'intelligent_tiering_monitoring': monitoring_cost,
            'intelligent_tiering_total': intelligent_tiering_cost,
            'monthly_savings': savings,
            'savings_percentage': savings_pct,
            'annual_savings': savings * 12
        }

    def analyze_access_patterns(self, bucket_name: str) -> Dict[str, float]:
        """
        Analyze object access patterns to predict tier distribution

        Args:
            bucket_name: S3 bucket name

        Returns:
            Estimated access pattern distribution
        """
        print(f"\n📊 Analyzing access patterns for: {bucket_name}")

        try:
            # List objects and analyze LastModified
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)

            age_distribution = {
                'hot': 0,      # < 30 days
                'warm': 0,     # 30-90 days
                'cool': 0,     # 90-180 days
                'cold': 0      # > 180 days
            }

            total_objects = 0

            for page in pages:
                for obj in page.get('Contents', []):
                    last_modified = obj['LastModified']
                    days_old = (datetime.now(timezone.utc) - last_modified).days

                    if days_old < 30:
                        age_distribution['hot'] += 1
                    elif days_old < 90:
                        age_distribution['warm'] += 1
                    elif days_old < 180:
                        age_distribution['cool'] += 1
                    else:
                        age_distribution['cold'] += 1

                    total_objects += 1

                    # Limit to 1000 objects for performance
                    if total_objects >= 1000:
                        break

                if total_objects >= 1000:
                    break

            if total_objects == 0:
                print("⚠️  Bucket is empty")
                return {'frequent': 1.0, 'infrequent': 0.0, 'archive': 0.0, 'deep_archive': 0.0}

            # Convert to percentages
            access_pattern = {
                'frequent': (age_distribution['hot'] / total_objects),
                'infrequent': (age_distribution['warm'] / total_objects),
                'archive': (age_distribution['cool'] / total_objects),
                'deep_archive': (age_distribution['cold'] / total_objects)
            }

            print(f"✅ Analyzed {total_objects} objects")
            print("\n   Age Distribution:")
            print(f"     Hot (< 30 days): {age_distribution['hot']} ({access_pattern['frequent']*100:.1f}%)")
            print(f"     Warm (30-90 days): {age_distribution['warm']} ({access_pattern['infrequent']*100:.1f}%)")
            print(f"     Cool (90-180 days): {age_distribution['cool']} ({access_pattern['archive']*100:.1f}%)")
            print(f"     Cold (> 180 days): {age_distribution['cold']} ({access_pattern['deep_archive']*100:.1f}%)")

            return access_pattern

        except Exception as e:
            print(f"⚠️  Could not analyze bucket: {e}")
            # Return default pattern
            return {'frequent': 0.3, 'infrequent': 0.4, 'archive': 0.2, 'deep_archive': 0.1}

def main():
    """Main Intelligent-Tiering workflow"""
    print("=" * 70)
    print("S3 Intelligent-Tiering Configuration")
    print("=" * 70)

    manager = IntelligentTieringManager()

    # Get bucket name
    bucket_name = input("\nEnter S3 bucket name (or press Enter for 'analytics-workspace'): ").strip()
    if not bucket_name:
        bucket_name = 'analytics-workspace'

    # Step 1: Check existing configurations
    print("\n[Step 1/4] Checking existing configurations...")
    existing_configs = manager.list_intelligent_tiering_configs(bucket_name)

    # Step 2: Analyze access patterns
    print("\n[Step 2/4] Analyzing access patterns...")
    try:
        access_pattern = manager.analyze_access_patterns(bucket_name)
    except:
        print("⚠️  Using default access pattern (30% frequent, 40% infrequent, 20% archive, 10% deep)")
        access_pattern = {'frequent': 0.3, 'infrequent': 0.4, 'archive': 0.2, 'deep_archive': 0.1}

    # Step 3: Calculate savings
    print("\n[Step 3/4] Calculating potential savings...")

    # Get bucket size (simplified - would use CloudWatch in production)
    size_gb = float(input("Enter total bucket size in GB (or press Enter for 1000): ") or "1000")

    result = manager.calculate_intelligent_tiering_savings(size_gb, access_pattern)

    print("\n💰 Cost Analysis:")
    print(f"   Current (all Standard): ${result['current_cost_standard']:.2f}/month")
    print("   Intelligent-Tiering:")
    print(f"     Storage: ${result['intelligent_tiering_storage']:.2f}")
    print(f"     Monitoring: ${result['intelligent_tiering_monitoring']:.2f}")
    print(f"     Total: ${result['intelligent_tiering_total']:.2f}/month")
    print(f"\n   💵 Monthly Savings: ${result['monthly_savings']:.2f} ({result['savings_percentage']:.1f}%)")
    print(f"   💵 Annual Savings: ${result['annual_savings']:.2f}")

    # Step 4: Configure Intelligent-Tiering
    print("\n[Step 4/4] Configuring Intelligent-Tiering...")

    response = input(f"\nConfigure Intelligent-Tiering for {bucket_name}? (yes/no): ").strip().lower()

    if response == 'yes':
        prefix = input("Enter prefix (or press Enter for entire bucket): ").strip()

        try:
            config_id = manager.configure_intelligent_tiering(
                bucket_name=bucket_name,
                prefix=prefix,
                archive_days=90,
                deep_archive_days=180
            )

            print(f"\n✅ Configuration created: {config_id}")

        except Exception as e:
            print(f"❌ Configuration failed: {e}")
    else:
        print("\n⏭️  Skipped configuration")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Intelligent-Tiering Analysis Complete!")
    print("=" * 70)

    print("\n📊 How Intelligent-Tiering Works:")
    print("   1. Objects start in Frequent Access tier ($0.023/GB)")
    print("   2. Not accessed for 30 days → Infrequent Access ($0.0125/GB)")
    print("   3. Not accessed for 90 days → Archive Access ($0.004/GB)")
    print("   4. Not accessed for 180 days → Deep Archive ($0.00099/GB)")
    print("   5. Accessed again → Automatically moves back to Frequent tier")
    print("\n   Monitoring Fee: $0.0025 per 1,000 objects/month")

    print("\n💡 Best Use Cases:")
    print("   ✓ Unknown or changing access patterns")
    print("   ✓ Long-lived data with sporadic access")
    print("   ✓ Large number of objects (monitoring fee is minimal)")
    print("   ✓ Data that shouldn't be deleted but rarely accessed")

    print("\n⚠️  When NOT to Use:")
    print("   ✗ Objects < 128 KB (minimum size requirement)")
    print("   ✗ Objects deleted within 30 days (minimum billable period)")
    print("   ✗ Objects with predictable access (use lifecycle instead)")

if __name__ == '__main__':
    main()
