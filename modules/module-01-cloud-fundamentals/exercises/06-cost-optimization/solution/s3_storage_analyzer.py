#!/usr/bin/env python3
"""
S3 Storage Analyzer - Complete Solution
Analyzes S3 storage patterns and generates cost-optimized lifecycle recommendations
"""

import boto3
from datetime import datetime, timezone
import csv
from tabulate import tabulate

s3 = boto3.client('s3', endpoint_url='http://localhost:4566')


def analyze_bucket(bucket_name):
    """Analyze object age distribution in S3 bucket"""

    print(f"📊 Analyzing bucket: {bucket_name}")

    age_buckets = {
        'hot': {'count': 0, 'size': 0, 'age_range': '0-30 days', 'storage_class': 'STANDARD'},
        'warm': {'count': 0, 'size': 0, 'age_range': '31-90 days', 'storage_class': 'STANDARD_IA'},
        'cold': {'count': 0, 'size': 0, 'age_range': '91-365 days', 'storage_class': 'GLACIER'},
        'archive': {'count': 0, 'size': 0, 'age_range': '365+ days', 'storage_class': 'DEEP_ARCHIVE'}
    }

    total_objects = 0
    total_size = 0

    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get('Contents', []):
                last_modified = obj['LastModified']
                age_days = (datetime.now(timezone.utc) - last_modified).days
                size = obj['Size']

                total_objects += 1
                total_size += size

                if age_days <= 30:
                    age_buckets['hot']['count'] += 1
                    age_buckets['hot']['size'] += size
                elif age_days <= 90:
                    age_buckets['warm']['count'] += 1
                    age_buckets['warm']['size'] += size
                elif age_days <= 365:
                    age_buckets['cold']['count'] += 1
                    age_buckets['cold']['size'] += size
                else:
                    age_buckets['archive']['count'] += 1
                    age_buckets['archive']['size'] += size

        print(f"✓ Analyzed {total_objects} objects ({total_size / (1024**3):.2f} GB)\n")

    except Exception as e:
        print(f"✗ Error analyzing bucket: {e}")
        return None

    return age_buckets


def calculate_costs(age_buckets):
    """Calculate current vs. optimized storage costs"""

    pricing = {
        'STANDARD': 0.023,
        'STANDARD_IA': 0.0125,
        'GLACIER': 0.004,
        'DEEP_ARCHIVE': 0.00099
    }

    # Convert sizes to GB
    sizes_gb = {}
    for category, data in age_buckets.items():
        sizes_gb[category] = data['size'] / (1024**3)

    # Current cost: all STANDARD
    current_cost = sum(sizes_gb.values()) * pricing['STANDARD']

    # Optimized cost: tiered storage
    optimized_cost = (
        sizes_gb['hot'] * pricing['STANDARD'] +
        sizes_gb['warm'] * pricing['STANDARD_IA'] +
        sizes_gb['cold'] * pricing['GLACIER'] +
        sizes_gb['archive'] * pricing['DEEP_ARCHIVE']
    )

    savings = current_cost - optimized_cost
    savings_percent = (savings / current_cost) * 100 if current_cost > 0 else 0

    return {
        'current': current_cost,
        'optimized': optimized_cost,
        'savings': savings,
        'savings_percent': savings_percent,
        'sizes_gb': sizes_gb,
        'pricing': pricing
    }


def generate_lifecycle_policy(age_buckets):
    """Generate S3 lifecycle policy"""

    policy = {
        'Rules': [
            {
                'Id': 'intelligent-tiering',
                'Status': 'Enabled',
                'Filter': {'Prefix': ''},
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    },
                    {
                        'Days': 365,
                        'StorageClass': 'DEEP_ARCHIVE'
                    }
                ]
            },
            {
                'Id': 'delete-old-versions',
                'Status': 'Enabled',
                'NoncurrentVersionExpiration': {
                    'NoncurrentDays': 90
                }
            },
            {
                'Id': 'cleanup-incomplete-uploads',
                'Status': 'Enabled',
                'AbortIncompleteMultipartUpload': {
                    'DaysAfterInitiation': 7
                }
            }
        ]
    }

    return policy


def print_report(bucket_name, age_buckets, costs):
    """Print detailed analysis report"""

    print("=" * 70)
    print(f"  S3 STORAGE ANALYSIS REPORT - {bucket_name}")
    print("=" * 70)
    print()

    # Age distribution table
    print("📦 AGE DISTRIBUTION")
    print("-" * 70)

    table_data = []
    for category, data in age_buckets.items():
        size_gb = data['size'] / (1024**3)
        storage_class = data['storage_class']
        age_range = data['age_range']
        count = data['count']

        table_data.append([
            category.capitalize(),
            age_range,
            storage_class,
            f"{count:,}",
            f"{size_gb:.2f} GB"
        ])

    print(tabulate(table_data,
                   headers=['Category', 'Age Range', 'Recommended Class', 'Objects', 'Size'],
                   tablefmt='grid'))

    print()

    # Cost analysis table
    print("💰 COST ANALYSIS")
    print("-" * 70)

    cost_table = [
        ['Current (all STANDARD)', f"${costs['current']:.2f}/month"],
        ['Optimized (tiered)', f"${costs['optimized']:.2f}/month"],
        ['Monthly Savings', f"${costs['savings']:.2f}"],
        ['Annual Savings', f"${costs['savings'] * 12:.2f}"],
        ['Savings Percentage', f"{costs['savings_percent']:.1f}%"]
    ]

    print(tabulate(cost_table, tablefmt='grid'))

    print()

    # Detailed breakdown
    print("📊 COST BREAKDOWN BY CATEGORY")
    print("-" * 70)

    breakdown_table = []
    for category, size_gb in costs['sizes_gb'].items():
        storage_class = age_buckets[category]['storage_class']
        price = costs['pricing'][storage_class]
        optimized_cost = size_gb * price
        current_cost_category = size_gb * costs['pricing']['STANDARD']
        savings_category = current_cost_category - optimized_cost

        breakdown_table.append([
            category.capitalize(),
            f"{size_gb:.2f} GB",
            storage_class,
            f"${current_cost_category:.2f}",
            f"${optimized_cost:.2f}",
            f"${savings_category:.2f}"
        ])

    print(tabulate(breakdown_table,
                   headers=['Category', 'Size', 'Optimized Class', 'Current Cost', 'Optimized Cost', 'Savings'],
                   tablefmt='grid'))

    print()
    print("=" * 70)


def export_to_csv(bucket_name, age_buckets, costs, filename='storage-analysis.csv'):
    """Export analysis to CSV"""

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['S3 Storage Analysis Report'])
        writer.writerow(['Bucket', bucket_name])
        writer.writerow(['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])

        writer.writerow(['Category', 'Age Range', 'Object Count', 'Size (GB)', 'Recommended Class'])
        for category, data in age_buckets.items():
            size_gb = data['size'] / (1024**3)
            writer.writerow([
                category.capitalize(),
                data['age_range'],
                data['count'],
                f"{size_gb:.2f}",
                data['storage_class']
            ])

        writer.writerow([])
        writer.writerow(['Cost Analysis'])
        writer.writerow(['Current Monthly Cost', f"${costs['current']:.2f}"])
        writer.writerow(['Optimized Monthly Cost', f"${costs['optimized']:.2f}"])
        writer.writerow(['Monthly Savings', f"${costs['savings']:.2f}"])
        writer.writerow(['Annual Savings', f"${costs['savings'] * 12:.2f}"])
        writer.writerow(['Savings Percentage', f"{costs['savings_percent']:.1f}%"])

    print(f"✓ Report exported to {filename}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze S3 storage costs')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--export', action='store_true', help='Export to CSV')
    parser.add_argument('--apply', action='store_true', help='Apply lifecycle policy')

    args = parser.parse_args()

    # Analyze bucket
    age_buckets = analyze_bucket(args.bucket)

    if not age_buckets:
        return

    # Calculate costs
    costs = calculate_costs(age_buckets)

    # Print report
    print_report(args.bucket, age_buckets, costs)

    # Export to CSV
    if args.export:
        export_to_csv(args.bucket, age_buckets, costs)

    # Apply lifecycle policy
    if args.apply:
        policy = generate_lifecycle_policy(age_buckets)
        print("\n📝 Applying lifecycle policy...")

        try:
            s3.put_bucket_lifecycle_configuration(
                Bucket=args.bucket,
                LifecycleConfiguration=policy
            )
            print("✓ Lifecycle policy applied successfully")
        except Exception as e:
            print(f"✗ Error applying policy: {e}")

    print("\n💡 Recommendations:")
    print("  1. Review the lifecycle policy before applying")
    print("  2. Test with a small dataset first")
    print("  3. Monitor retrieval costs for IA/GLACIER")
    print("  4. Set up CloudWatch alarms for cost anomalies")


if __name__ == '__main__':
    main()
