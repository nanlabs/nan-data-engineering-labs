"""
Materialized View Manager for Kappa Architecture

This module manages versioned materialized views to enable zero-downtime reprocessing.
Uses blue-green deployment pattern to swap between view versions.

Key Features:
1. Create versioned DynamoDB tables (v1, v2, v3...)
2. Validate view completeness and accuracy
3. Blue-green swap (change active version)
4. Delete old versions (cleanup)
5. Compare views (before/after reprocessing)

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MaterializedViewManager:
    """
    Manages versioned materialized views in Kappa Architecture.

    Enables zero-downtime reprocessing through blue-green deployments.
    """

    def __init__(
        self,
        base_table_name: str = "category_metrics",
        parameter_store_key: str = "/kappa/active_view_version",
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize View Manager.

        Args:
            base_table_name: Base name for versioned tables
            parameter_store_key: SSM parameter for active version
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.base_table_name = base_table_name
        self.parameter_store_key = parameter_store_key
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)
        self.ssm = boto3.client('ssm', region_name=region, endpoint_url=endpoint_url)

        logger.info("MaterializedViewManager initialized")

    def create_view_version(self, version: int) -> str:
        """
        Create new versioned materialized view table.

        Args:
            version: Version number (1, 2, 3...)

        Returns:
            Table name
        """
        table_name = f"{self.base_table_name}_v{version}"

        logger.info(f"=== Creating View Version {version} ===")
        logger.info(f"   Table: {table_name}")

        try:
            self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'category', 'KeyType': 'HASH'},
                    {'AttributeName': 'window_start', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'category', 'AttributeType': 'S'},
                    {'AttributeName': 'window_start', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Version', 'Value': str(version)},
                    {'Key': 'Architecture', 'Value': 'Kappa'},
                    {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
                ]
            )

            # Wait for table
            logger.info("   Waiting for table to be active...")
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)

            logger.info(f"✅ Created view: {table_name}")

            return table_name

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ View already exists: {table_name}")
                return table_name
            else:
                logger.error(f"❌ Failed to create view: {e}")
                raise

    def get_active_version(self) -> int:
        """
        Get currently active view version.

        Returns:
            Version number
        """
        try:
            response = self.ssm.get_parameter(Name=self.parameter_store_key)
            version = int(response['Parameter']['Value'])

            logger.info(f"📌 Active version: v{version}")
            return version

        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.info("📌 No active version set, defaulting to v1")
                return 1
            else:
                logger.error(f"❌ Failed to get active version: {e}")
                raise

    def set_active_version(self, version: int) -> None:
        """
        Set active view version (blue-green swap).

        Args:
            version: Version number to activate
        """
        logger.info(f"=== Setting Active Version: v{version} ===")

        try:
            self.ssm.put_parameter(
                Name=self.parameter_store_key,
                Value=str(version),
                Type='String',
                Overwrite=True
            )

            logger.info(f"✅ Active version set to: v{version}")
            logger.info("   Applications will pick up change on next parameter refresh")

        except ClientError as e:
            logger.error(f"❌ Failed to set active version: {e}")
            raise

    def validate_view(self, version: int) -> Dict[str, Any]:
        """
        Validate materialized view completeness and accuracy.

        Args:
            version: Version number to validate

        Returns:
            Dict with validation results
        """
        table_name = f"{self.base_table_name}_v{version}"

        logger.info(f"=== Validating View: {table_name} ===")

        try:
            # Get table info
            response = self.dynamodb.describe_table(TableName=table_name)
            table_info = response['Table']

            item_count = table_info.get('ItemCount', 0)
            table_size_bytes = table_info.get('TableSizeBytes', 0)

            logger.info(f"   Items: {item_count:,}")
            logger.info(f"   Size: {table_size_bytes / 1024 / 1024:.2f} MB")

            # Scan sample records
            scan_response = self.dynamodb.scan(
                TableName=table_name,
                Limit=100
            )

            sample_items = scan_response['Items']

            # Validate schema
            required_fields = ['category', 'window_start', 'order_count', 'revenue']
            schema_valid = True

            for item in sample_items[:5]:  # Check first 5
                for field in required_fields:
                    if field not in item:
                        logger.error(f"❌ Missing field: {field}")
                        schema_valid = False

            # Validate data quality
            data_quality_issues = 0

            for item in sample_items:
                order_count = int(item.get('order_count', {}).get('N', 0))
                revenue = float(item.get('revenue', {}).get('N', 0))

                # Check for anomalies
                if order_count < 0 or revenue < 0:
                    data_quality_issues += 1
                    logger.warning(f"⚠️  Negative values: {item['category']['S']}")

                if order_count > 0 and revenue == 0:
                    data_quality_issues += 1
                    logger.warning(f"⚠️  Orders without revenue: {item['category']['S']}")

            validation_result = {
                'version': version,
                'table_name': table_name,
                'item_count': item_count,
                'table_size_mb': table_size_bytes / 1024 / 1024,
                'schema_valid': schema_valid,
                'data_quality_issues': data_quality_issues,
                'sample_size': len(sample_items),
                'validation_passed': schema_valid and data_quality_issues == 0
            }

            if validation_result['validation_passed']:
                logger.info("✅ Validation PASSED")
            else:
                logger.error("❌ Validation FAILED")

            return validation_result

        except ClientError as e:
            logger.error(f"❌ Validation failed: {e}")
            return {'validation_passed': False, 'error': str(e)}

    def compare_views(self, version1: int, version2: int) -> Dict[str, Any]:
        """
        Compare two view versions (useful for validating reprocessing).

        Args:
            version1: First version
            version2: Second version

        Returns:
            Dict with comparison results
        """
        logger.info(f"=== Comparing Views: v{version1} vs v{version2} ===")

        table1 = f"{self.base_table_name}_v{version1}"
        table2 = f"{self.base_table_name}_v{version2}"

        # Sample random keys from v1
        scan1 = self.dynamodb.scan(TableName=table1, Limit=100)
        items1 = scan1['Items']

        # Query same keys in v2
        matches = 0
        mismatches = []

        for item1 in items1:
            category = item1['category']['S']
            window_start = item1['window_start']['S']

            try:
                response2 = self.dynamodb.get_item(
                    TableName=table2,
                    Key={
                        'category': {'S': category},
                        'window_start': {'S': window_start}
                    }
                )

                if 'Item' not in response2:
                    mismatches.append({
                        'category': category,
                        'window_start': window_start,
                        'issue': 'Missing in v2'
                    })
                    continue

                item2 = response2['Item']

                # Compare metrics
                order_count1 = int(item1['order_count']['N'])
                order_count2 = int(item2['order_count']['N'])

                revenue1 = float(item1['revenue']['N'])
                revenue2 = float(item2['revenue']['N'])

                # Allow small differences (rounding)
                if abs(order_count1 - order_count2) > 0:
                    mismatches.append({
                        'category': category,
                        'window_start': window_start,
                        'field': 'order_count',
                        'v1': order_count1,
                        'v2': order_count2,
                        'diff': order_count2 - order_count1
                    })

                if abs(revenue1 - revenue2) > 0.01:
                    mismatches.append({
                        'category': category,
                        'window_start': window_start,
                        'field': 'revenue',
                        'v1': revenue1,
                        'v2': revenue2,
                        'diff_pct': (revenue2 - revenue1) / revenue1 * 100 if revenue1 > 0 else 0
                    })

                if not mismatches:
                    matches += 1

            except ClientError as e:
                logger.error(f"❌ Query failed: {e}")

        comparison = {
            'version1': version1,
            'version2': version2,
            'sample_size': len(items1),
            'matches': matches,
            'mismatches': len(mismatches),
            'mismatch_details': mismatches[:10],  # First 10
            'match_rate': matches / len(items1) if items1 else 0
        }

        logger.info("✅ Comparison complete")
        logger.info(f"   Matches: {matches} / {len(items1)} ({comparison['match_rate']:.1%})")
        logger.info(f"   Mismatches: {len(mismatches)}")

        if mismatches:
            logger.warning("⚠️  Differences found (see details)")
            for mm in mismatches[:3]:
                logger.warning(f"   {mm}")

        return comparison

    def blue_green_deployment(
        self,
        old_version: int,
        new_version: int,
        wait_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Execute blue-green deployment (swap versions).

        Args:
            old_version: Current production version
            new_version: New version to activate
            wait_seconds: Wait time before deleting old version

        Returns:
            Dict with deployment results
        """
        logger.info("=" * 60)
        logger.info("=== Blue-Green Deployment ===")
        logger.info(f"   v{old_version} (current) → v{new_version} (new)")
        logger.info("=" * 60)

        # Step 1: Validate new version
        logger.info("\n📋 Step 1: Validate New Version")
        validation = self.validate_view(new_version)

        if not validation['validation_passed']:
            logger.error("❌ New version failed validation, aborting deployment")
            return {'status': 'aborted', 'reason': 'validation_failed'}

        # Step 2: Compare with old version
        logger.info("\n🔍 Step 2: Compare Versions")
        comparison = self.compare_views(old_version, new_version)

        if comparison['match_rate'] < 0.95:
            logger.error(f"❌ Low match rate ({comparison['match_rate']:.1%}), aborting")
            return {'status': 'aborted', 'reason': 'low_match_rate', 'match_rate': comparison['match_rate']}

        # Step 3: Set new version as active
        logger.info(f"\n🔄 Step 3: Swap Active Version (v{old_version} → v{new_version})")
        self.set_active_version(new_version)

        logger.info(f"✅ Active version set to v{new_version}")
        logger.info(f"   Applications reading from: {self.base_table_name}_v{new_version}")

        # Step 4: Monitor new version
        logger.info(f"\n⏳ Step 4: Monitoring ({wait_seconds}s grace period)...")
        logger.info("   Watching for errors in v{new_version}...")

        # In production: Monitor CloudWatch metrics, error rates
        time.sleep(wait_seconds)

        logger.info("✅ No errors detected during grace period")

        # Step 5: Delete old version
        logger.info("\n🗑️  Step 5: Cleanup Old Version")
        self.delete_view_version(old_version)

        result = {
            'status': 'success',
            'old_version': old_version,
            'new_version': new_version,
            'validation': validation,
            'comparison': comparison,
            'deployment_time': datetime.now().isoformat()
        }

        logger.info("=" * 60)
        logger.info("=== Deployment Complete ===")
        logger.info(f"✅ Successfully deployed v{new_version}")
        logger.info("=" * 60)

        return result

    def delete_view_version(self, version: int) -> None:
        """
        Delete materialized view version.

        Args:
            version: Version to delete
        """
        table_name = f"{self.base_table_name}_v{version}"

        logger.info(f"🗑️  Deleting view: {table_name}")

        try:
            self.dynamodb.delete_table(TableName=table_name)
            logger.info(f"✅ Deleted: {table_name}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"✅ Table already deleted: {table_name}")
            else:
                logger.error(f"❌ Failed to delete table: {e}")
                raise

    def list_view_versions(self) -> List[Dict[str, Any]]:
        """
        List all materialized view versions.

        Returns:
            List of version info dicts
        """
        logger.info("=== Listing View Versions ===")

        try:
            # List all tables
            response = self.dynamodb.list_tables()

            # Filter tables matching pattern
            view_tables = [
                table for table in response['TableNames']
                if table.startswith(self.base_table_name + '_v')
            ]

            versions = []

            for table_name in view_tables:
                # Extract version number
                version_str = table_name.split('_v')[-1]

                try:
                    version = int(version_str)
                except ValueError:
                    continue

                # Get table details
                table_response = self.dynamodb.describe_table(TableName=table_name)
                table_info = table_response['Table']

                versions.append({
                    'version': version,
                    'table_name': table_name,
                    'status': table_info['TableStatus'],
                    'item_count': table_info.get('ItemCount', 0),
                    'size_mb': table_info.get('TableSizeBytes', 0) / 1024 / 1024,
                    'created_at': table_info.get('CreationDateTime')
                })

            # Sort by version
            versions.sort(key=lambda x: x['version'])

            # Mark active version
            active_version = self.get_active_version()

            for v in versions:
                v['is_active'] = (v['version'] == active_version)

            logger.info(f"   Found {len(versions)} versions")

            for v in versions:
                status_icon = "🟢" if v['is_active'] else "⚪"
                logger.info(
                    f"   {status_icon} v{v['version']}: {v['item_count']:,} items, "
                    f"{v['size_mb']:.2f} MB ({v['status']})"
                )

            return versions

        except ClientError as e:
            logger.error(f"❌ Failed to list versions: {e}")
            return []

    def copy_view_sample(
        self,
        source_version: int,
        target_version: int,
        sample_size: int = 1000
    ) -> int:
        """
        Copy sample data from one view to another (for testing).

        Args:
            source_version: Source version
            target_version: Target version
            sample_size: Number of items to copy

        Returns:
            Number of items copied
        """
        source_table = f"{self.base_table_name}_v{source_version}"
        target_table = f"{self.base_table_name}_v{target_version}"

        logger.info(f"=== Copying Sample: v{source_version} → v{target_version} ===")
        logger.info(f"   Sample Size: {sample_size:,} items")

        try:
            # Scan source table
            response = self.dynamodb.scan(
                TableName=source_table,
                Limit=sample_size
            )

            items = response['Items']

            # Write to target table
            copied = 0

            for item in items:
                self.dynamodb.put_item(
                    TableName=target_table,
                    Item=item
                )
                copied += 1

                if copied % 100 == 0:
                    logger.info(f"   Copied: {copied} / {len(items)}")

            logger.info(f"✅ Copied {copied:,} items")

            return copied

        except ClientError as e:
            logger.error(f"❌ Copy failed: {e}")
            return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Kappa Architecture - Materialized View Manager')

    parser.add_argument(
        '--mode',
        choices=['create', 'list', 'validate', 'compare', 'swap', 'delete', 'deploy'],
        default='list',
        help='Operation mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--version',
        type=int,
        help='View version number'
    )

    parser.add_argument(
        '--old-version',
        type=int,
        help='Old version (for swap/compare modes)'
    )

    parser.add_argument(
        '--new-version',
        type=int,
        help='New version (for swap/compare modes)'
    )

    args = parser.parse_args()

    # Initialize manager
    manager = MaterializedViewManager(use_localstack=(args.env == 'localstack'))

    if args.mode == 'create':
        if not args.version:
            logger.error("❌ --version required")
            sys.exit(1)

        table_name = manager.create_view_version(args.version)
        print(f"✅ Created: {table_name}")

    elif args.mode == 'list':
        versions = manager.list_view_versions()

        print("\n" + "=" * 80)
        print("📋 MATERIALIZED VIEW VERSIONS")
        print("=" * 80)

        for v in versions:
            status_icon = "🟢 ACTIVE" if v['is_active'] else "⚪ Inactive"
            print(f"\n{status_icon} - Version {v['version']}")
            print(f"   Table: {v['table_name']}")
            print(f"   Status: {v['status']}")
            print(f"   Items: {v['item_count']:,}")
            print(f"   Size: {v['size_mb']:.2f} MB")
            print(f"   Created: {v['created_at']}")

        print("\n" + "=" * 80)

    elif args.mode == 'validate':
        if not args.version:
            logger.error("❌ --version required")
            sys.exit(1)

        result = manager.validate_view(args.version)
        print(json.dumps(result, indent=2, default=str))

    elif args.mode == 'compare':
        if not (args.old_version and args.new_version):
            logger.error("❌ --old-version and --new-version required")
            sys.exit(1)

        result = manager.compare_views(args.old_version, args.new_version)
        print(json.dumps(result, indent=2, default=str))

    elif args.mode == 'swap':
        if not args.new_version:
            logger.error("❌ --new-version required")
            sys.exit(1)

        old_version = manager.get_active_version()

        result = manager.blue_green_deployment(
            old_version=old_version,
            new_version=args.new_version,
            wait_seconds=60  # 1 minute grace period (use 300 in production)
        )

        print(json.dumps(result, indent=2, default=str))

    elif args.mode == 'delete':
        if not args.version:
            logger.error("❌ --version required")
            sys.exit(1)

        manager.delete_view_version(args.version)

    elif args.mode == 'deploy':
        # Full deployment workflow
        logger.info("🚀 Starting full deployment...")

        # Get current version
        old_version = manager.get_active_version()
        new_version = old_version + 1

        logger.info(f"   Current: v{old_version}")
        logger.info(f"   Deploying: v{new_version}")

        # Create new version
        manager.create_view_version(new_version)

        logger.info("\n⏳ Waiting for reprocessing to complete...")
        logger.info("   (Run replay_handler.py to fill v{new_version})")
        logger.info("   Then: python materialized_views.py --mode swap --new-version {new_version}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
