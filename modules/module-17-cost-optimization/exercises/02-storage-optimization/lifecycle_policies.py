#!/usr/bin/env python3
"""
S3 Lifecycle Policies for Storage Optimization
Automate transitions to cheaper storage classes
"""

import boto3
import json
from typing import Dict
import sys

class LifecyclePolicyManager:
    """Manage S3 lifecycle policies for cost optimization"""

    # Storage class pricing per GB-month
    PRICING = {
        'STANDARD': 0.023,
        'STANDARD_IA': 0.0125,
        'ONEZONE_IA': 0.01,
        'INTELLIGENT_TIERING': 0.023,  # Starts at Standard pricing
        'GLACIER_IR': 0.004,
        'GLACIER': 0.0036,
        'DEEP_ARCHIVE': 0.00099
    }

    def __init__(self, region: str = 'us-east-1'):
        """Initialize S3 client"""
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)

    def create_data_lake_policy(self, bucket_name: str) -> Dict:
        """
        Create lifecycle policy for data lake bucket

        Args:
            bucket_name: S3 bucket name

        Returns:
            Lifecycle configuration dict
        """
        print(f"\n📋 Creating lifecycle policy for: {bucket_name}")

        lifecycle_config = {
            'Rules': [
                {
                    'Id': 'raw-data-aggressive-archival',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'raw/'},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'  # Save ~46% after 30 days
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER_IR'  # Save ~83% after 90 days
                        },
                        {
                            'Days': 180,
                            'StorageClass': 'DEEP_ARCHIVE'  # Save ~96% after 180 days
                        }
                    ],
                    'NoncurrentVersionTransitions': [
                        {
                            'NoncurrentDays': 7,
                            'StorageClass': 'GLACIER_IR'
                        }
                    ],
                    'Expiration': {
                        'Days': 365  # Delete after 1 year
                    },
                    'NoncurrentVersionExpiration': {
                        'NoncurrentDays': 90
                    }
                },
                {
                    'Id': 'curated-data-moderate-archival',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'curated/'},
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'STANDARD_IA'  # Keep accessible longer
                        },
                        {
                            'Days': 365,
                            'StorageClass': 'GLACIER_IR'  # Archive after 1 year
                        }
                    ]
                },
                {
                    'Id': 'logs-aggressive-cleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'logs/'},
                    'Transitions': [
                        {
                            'Days': 7,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 30,
                            'StorageClass': 'GLACIER_IR'
                        }
                    ],
                    'Expiration': {
                        'Days': 90  # Delete logs after 90 days
                    }
                },
                {
                    'Id': 'temp-data-immediate-cleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'temp/'},
                    'Expiration': {
                        'Days': 7  # Auto-delete temp files
                    }
                },
                {
                    'Id': 'multipart-upload-cleanup',
                    'Status': 'Enabled',
                    'Filter': {},
                    'AbortIncompleteMultipartUpload': {
                        'DaysAfterInitiation': 1  # Clean up failed uploads
                    }
                }
            ]
        }

        return lifecycle_config

    def apply_lifecycle_policy(self, bucket_name: str, dry_run: bool = False):
        """
        Apply lifecycle policy to bucket

        Args:
            bucket_name: S3 bucket name
            dry_run: If True, only show policy without applying
        """
        config = self.create_data_lake_policy(bucket_name)

        if dry_run:
            print("\n[DRY RUN] Would apply lifecycle policy:")
            print(json.dumps(config, indent=2))
            return

        try:
            self.s3.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=config
            )

            print(f"✅ Lifecycle policy applied to {bucket_name}")
            print(f"   Rules: {len(config['Rules'])}")
            for rule in config['Rules']:
                print(f"   - {rule['Id']}: {rule['Status']}")

        except Exception as e:
            print(f"❌ Error applying lifecycle policy: {e}")
            sys.exit(1)

    def calculate_lifecycle_savings(
        self,
        size_gb: float,
        days_standard: int = 30,
        days_ia: int = 60,
        days_glacier: int = 90,
        days_deep: int = 185
    ) -> Dict:
        """
        Calculate monthly savings from lifecycle policy

        Args:
            size_gb: Total storage size in GB
            days_standard: Days in Standard class
            days_ia: Days in Standard-IA
            days_glacier: Days in Glacier Instant Retrieval
            days_deep: Days in Deep Archive

        Returns:
            Dict with cost analysis
        """
        days_total = days_standard + days_ia + days_glacier + days_deep

        # Current cost (all in Standard)
        current_cost = size_gb * self.PRICING['STANDARD']

        # Optimized cost (lifecycle transitions)
        optimized_cost = (
            size_gb * self.PRICING['STANDARD'] * (days_standard / days_total) +
            size_gb * self.PRICING['STANDARD_IA'] * (days_ia / days_total) +
            size_gb * self.PRICING['GLACIER_IR'] * (days_glacier / days_total) +
            size_gb * self.PRICING['DEEP_ARCHIVE'] * (days_deep / days_total)
        )

        savings = current_cost - optimized_cost
        savings_pct = (savings / current_cost) * 100

        return {
            'size_gb': size_gb,
            'current_cost': current_cost,
            'optimized_cost': optimized_cost,
            'monthly_savings': savings,
            'savings_percentage': savings_pct,
            'annual_savings': savings * 12
        }

    def analyze_bucket_lifecycle(self, bucket_name: str):
        """Analyze existing lifecycle configuration"""
        print(f"\n🔍 Analyzing lifecycle policy for: {bucket_name}")

        try:
            config = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)

            print("✅ Lifecycle policy active")
            print(f"   Rules: {len(config['Rules'])}")

            for rule in config['Rules']:
                print(f"\n   Rule: {rule['Id']}")
                print(f"   Status: {rule['Status']}")
                print(f"   Filter: {rule.get('Filter', {})}")

                if 'Transitions' in rule:
                    print("   Transitions:")
                    for trans in rule['Transitions']:
                        print(f"     - Day {trans['Days']}: → {trans['StorageClass']}")

                if 'Expiration' in rule:
                    print(f"   Expiration: Day {rule['Expiration'].get('Days', 'N/A')}")

            return config

        except self.s3.exceptions.NoSuchLifecycleConfiguration:
            print(f"⚠️  No lifecycle policy exists for {bucket_name}")
            return None
        except Exception as e:
            print(f"❌ Error retrieving lifecycle policy: {e}")
            return None

def main():
    """Main lifecycle policy workflow"""
    print("=" * 70)
    print("S3 Lifecycle Policy Management")
    print("=" * 70)

    manager = LifecyclePolicyManager()

    # Get bucket name from user or use default
    bucket_name = input("\nEnter S3 bucket name (or press Enter for 'data-lake-bucket'): ").strip()
    if not bucket_name:
        bucket_name = 'data-lake-bucket'

    # Step 1: Check existing policy
    print("\n[Step 1/4] Checking existing lifecycle policy...")
    existing_config = manager.analyze_bucket_lifecycle(bucket_name)

    # Step 2: Create new policy
    print("\n[Step 2/4] Creating optimized lifecycle policy...")
    new_config = manager.create_data_lake_policy(bucket_name)

    print("\n📋 New Policy Summary:")
    print(f"   Total rules: {len(new_config['Rules'])}")
    for rule in new_config['Rules']:
        transitions = rule.get('Transitions', [])
        expiration = rule.get('Expiration', {})
        print(f"   - {rule['Id']}: {len(transitions)} transitions", end='')
        if expiration:
            print(f", expires day {expiration.get('Days', 'N/A')}")
        else:
            print()

    # Step 3: Calculate projected savings
    print("\n[Step 3/4] Calculating projected savings...")

    # Example scenarios
    scenarios = [
        {'name': 'Small (100 GB)', 'size': 100},
        {'name': 'Medium (1 TB)', 'size': 1024},
        {'name': 'Large (10 TB)', 'size': 10240},
        {'name': 'X-Large (100 TB)', 'size': 102400}
    ]

    print("\n💰 Projected Savings (with lifecycle policy):\n")
    print(f"{'Scenario':<20} {'Current':<15} {'Optimized':<15} {'Savings':<15} {'%'}")
    print("-" * 70)

    for scenario in scenarios:
        result = manager.calculate_lifecycle_savings(scenario['size'])
        print(f"{scenario['name']:<20} ${result['current_cost']:>12,.2f}  "
              f"${result['optimized_cost']:>12,.2f}  "
              f"${result['monthly_savings']:>12,.2f}  "
              f"{result['savings_percentage']:>5.1f}%")

    # Step 4: Apply policy
    print("\n[Step 4/4] Applying lifecycle policy...")

    response = input(f"\nApply lifecycle policy to {bucket_name}? (yes/no/dry-run): ").strip().lower()

    if response == 'yes':
        manager.apply_lifecycle_policy(bucket_name, dry_run=False)
        print("\n✅ Policy applied successfully!")
    elif response == 'dry-run':
        manager.apply_lifecycle_policy(bucket_name, dry_run=True)
    else:
        print("\n⏭️  Skipped policy application")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Lifecycle Policy Management Complete!")
    print("=" * 70)

    print("\n📊 Key Takeaways:")
    print("  - Lifecycle policies automate cost optimization")
    print("  - 70-80% savings possible with proper transitions")
    print("  - Transitions occur 24-48 hours after policy creation")
    print("  - Monitor with S3 Storage Lens and CloudWatch metrics")

    print("\n📋 Next Steps:")
    print("  1. Monitor first transition (24-48 hours)")
    print("  2. Verify objects are transitioning correctly")
    print("  3. Adjust policy based on access patterns")
    print("  4. Implement for remaining buckets")

if __name__ == '__main__':
    main()
