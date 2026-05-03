#!/usr/bin/env python3
"""
QuickSight Dashboard Setup Script
Automates the creation of data sources, datasets, and dashboards for the real-time analytics platform.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuickSightDashboardManager:
    """Manages QuickSight dashboard creation and configuration."""

    def __init__(
        self,
        region: str,
        account_id: str,
        user_name: str,
        dynamodb_tables: Dict[str, str],
        athena_database: str,
        athena_workgroup: str = "primary"
    ):
        """
        Initialize the dashboard manager.

        Args:
            region: AWS region
            account_id: AWS account ID
            user_name: QuickSight user name
            dynamodb_tables: Dictionary mapping dataset names to DynamoDB table names
            athena_database: Athena database name
            athena_workgroup: Athena workgroup name
        """
        self.region = region
        self.account_id = account_id
        self.user_name = user_name
        self.dynamodb_tables = dynamodb_tables
        self.athena_database = athena_database
        self.athena_workgroup = athena_workgroup

        self.quicksight_client = boto3.client('quicksight', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)

        # Verify account ID
        if not account_id:
            response = self.sts_client.get_caller_identity()
            self.account_id = response['Account']
            logger.info(f"Detected AWS Account ID: {self.account_id}")

    def create_data_sources(self) -> Dict[str, str]:
        """
        Create QuickSight data sources for DynamoDB and Athena.

        Returns:
            Dictionary mapping data source names to their ARNs
        """
        data_source_arns = {}

        # Create DynamoDB data sources
        for dataset_name, table_name in self.dynamodb_tables.items():
            source_id = f"{dataset_name}-dynamodb"
            source_name = f"{dataset_name.replace('_', ' ').title()} DynamoDB"

            try:
                logger.info(f"Creating DynamoDB data source: {source_name}")
                response = self.quicksight_client.create_data_source(
                    AwsAccountId=self.account_id,
                    DataSourceId=source_id,
                    Name=source_name,
                    Type='DYNAMODB',
                    DataSourceParameters={
                        'DynamoDbParameters': {
                            'TableName': table_name,
                            'Region': self.region
                        }
                    },
                    Permissions=[
                        {
                            'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/{self.user_name}',
                            'Actions': [
                                'quicksight:DescribeDataSource',
                                'quicksight:DescribeDataSourcePermissions',
                                'quicksight:PassDataSource',
                                'quicksight:UpdateDataSource',
                                'quicksight:DeleteDataSource',
                                'quicksight:UpdateDataSourcePermissions'
                            ]
                        }
                    ],
                    SslProperties={
                        'DisableSsl': False
                    }
                )
                data_source_arns[source_id] = response['Arn']
                logger.info(f"Created data source: {response['Arn']}")

            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceExistsException':
                    logger.warning(f"Data source {source_id} already exists")
                    # Get existing data source ARN
                    response = self.quicksight_client.describe_data_source(
                        AwsAccountId=self.account_id,
                        DataSourceId=source_id
                    )
                    data_source_arns[source_id] = response['DataSource']['Arn']
                else:
                    logger.error(f"Error creating data source {source_id}: {e}")
                    raise

        # Create Athena data source
        athena_source_id = "sales-analytics-athena"
        athena_source_name = "Sales Analytics Athena"

        try:
            logger.info(f"Creating Athena data source: {athena_source_name}")
            response = self.quicksight_client.create_data_source(
                AwsAccountId=self.account_id,
                DataSourceId=athena_source_id,
                Name=athena_source_name,
                Type='ATHENA',
                DataSourceParameters={
                    'AthenaParameters': {
                        'WorkGroup': self.athena_workgroup
                    }
                },
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/{self.user_name}',
                        'Actions': [
                            'quicksight:DescribeDataSource',
                            'quicksight:DescribeDataSourcePermissions',
                            'quicksight:PassDataSource',
                            'quicksight:UpdateDataSource',
                            'quicksight:DeleteDataSource',
                            'quicksight:UpdateDataSourcePermissions'
                        ]
                    }
                ],
                SslProperties={
                    'DisableSsl': False
                }
            )
            data_source_arns[athena_source_id] = response['Arn']
            logger.info(f"Created Athena data source: {response['Arn']}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                logger.warning(f"Data source {athena_source_id} already exists")
                response = self.quicksight_client.describe_data_source(
                    AwsAccountId=self.account_id,
                    DataSourceId=athena_source_id
                )
                data_source_arns[athena_source_id] = response['DataSource']['Arn']
            else:
                logger.error(f"Error creating Athena data source: {e}")
                raise

        return data_source_arns

    def create_datasets(self, data_source_arns: Dict[str, str]) -> Dict[str, str]:
        """
        Create QuickSight datasets with SPICE configuration.

        Args:
            data_source_arns: Dictionary of data source ARNs

        Returns:
            Dictionary mapping dataset IDs to their ARNs
        """
        dataset_arns = {}

        # Dataset configurations
        datasets = [
            {
                'dataset_id': 'rides-state-realtime',
                'name': 'Rides State Real-Time',
                'import_mode': 'SPICE',
                'data_source_id': 'rides_state-dynamodb',
                'refresh_interval': 5  # minutes
            },
            {
                'dataset_id': 'aggregated-metrics-realtime',
                'name': 'Aggregated Metrics Real-Time',
                'import_mode': 'SPICE',
                'data_source_id': 'aggregated_metrics-dynamodb',
                'refresh_interval': 5  # minutes
            },
            {
                'dataset_id': 'sales-analytics-athena',
                'name': 'Sales Analytics',
                'import_mode': 'SPICE',
                'data_source_id': 'sales-analytics-athena',
                'refresh_interval': 60  # minutes
            }
        ]

        for dataset_config in datasets:
            dataset_id = dataset_config['dataset_id']
            data_source_id = dataset_config['data_source_id']

            if data_source_id not in data_source_arns:
                logger.warning(f"Data source {data_source_id} not found, skipping dataset {dataset_id}")
                continue

            try:
                logger.info(f"Creating dataset: {dataset_config['name']}")

                physical_table_map = {
                    'physical-table-1': {
                        'CustomSql': {
                            'DataSourceArn': data_source_arns[data_source_id],
                            'Name': dataset_config['name'],
                            'SqlQuery': f"SELECT * FROM {dataset_id.replace('-', '_')}"
                        }
                    }
                }

                response = self.quicksight_client.create_data_set(
                    AwsAccountId=self.account_id,
                    DataSetId=dataset_id,
                    Name=dataset_config['name'],
                    PhysicalTableMap=physical_table_map,
                    ImportMode=dataset_config['import_mode'],
                    Permissions=[
                        {
                            'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/{self.user_name}',
                            'Actions': [
                                'quicksight:DescribeDataSet',
                                'quicksight:DescribeDataSetPermissions',
                                'quicksight:PassDataSet',
                                'quicksight:DescribeIngestion',
                                'quicksight:ListIngestions',
                                'quicksight:UpdateDataSet',
                                'quicksight:DeleteDataSet',
                                'quicksight:CreateIngestion',
                                'quicksight:CancelIngestion',
                                'quicksight:UpdateDataSetPermissions'
                            ]
                        }
                    ]
                )
                dataset_arns[dataset_id] = response['Arn']
                logger.info(f"Created dataset: {response['Arn']}")

                # Configure SPICE refresh schedule if applicable
                if dataset_config['import_mode'] == 'SPICE':
                    self._configure_refresh_schedule(
                        dataset_id,
                        dataset_config['refresh_interval']
                    )

            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceExistsException':
                    logger.warning(f"Dataset {dataset_id} already exists")
                    response = self.quicksight_client.describe_data_set(
                        AwsAccountId=self.account_id,
                        DataSetId=dataset_id
                    )
                    dataset_arns[dataset_id] = response['DataSet']['Arn']
                else:
                    logger.error(f"Error creating dataset {dataset_id}: {e}")
                    raise

        return dataset_arns

    def _configure_refresh_schedule(self, dataset_id: str, interval_minutes: int):
        """
        Configure SPICE refresh schedule for a dataset.

        Args:
            dataset_id: Dataset ID
            interval_minutes: Refresh interval in minutes
        """
        schedule_id = f"{dataset_id}-auto-refresh"

        try:
            logger.info(f"Creating refresh schedule for dataset {dataset_id} (every {interval_minutes} minutes)")

            self.quicksight_client.create_refresh_schedule(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Schedule={
                    'ScheduleId': schedule_id,
                    'ScheduleFrequency': {
                        'Interval': 'MINUTE' if interval_minutes < 60 else 'HOURLY',
                        'RefreshOnDay': {
                            'DayOfWeek': 'SUNDAY'
                        } if interval_minutes >= 1440 else None,
                        'TimeOfTheDay': '00:00',
                        'Timezone': 'UTC'
                    },
                    'RefreshType': 'FULL_REFRESH'
                }
            )
            logger.info(f"Refresh schedule created: {schedule_id}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                logger.warning(f"Refresh schedule {schedule_id} already exists")
            else:
                logger.error(f"Error creating refresh schedule: {e}")

    def create_dashboard(
        self,
        dashboard_id: str,
        dashboard_name: str,
        template_path: str,
        dataset_arns: Dict[str, str]
    ) -> str:
        """
        Create a QuickSight dashboard from a template file.

        Args:
            dashboard_id: Dashboard identifier
            dashboard_name: Dashboard display name
            template_path: Path to dashboard template JSON file
            dataset_arns: Dictionary of dataset ARNs

        Returns:
            Dashboard ARN
        """
        try:
            logger.info(f"Creating dashboard: {dashboard_name}")

            # Load template
            with open(template_path, 'r') as f:
                template = json.load(f)

            # Replace placeholders in template
            template_str = json.dumps(template)
            template_str = template_str.replace('${AWS_REGION}', self.region)
            template_str = template_str.replace('${AWS_ACCOUNT_ID}', self.account_id)
            template_str = template_str.replace('${USER_NAME}', self.user_name)
            template = json.loads(template_str)

            # Create dashboard
            response = self.quicksight_client.create_dashboard(
                AwsAccountId=self.account_id,
                DashboardId=dashboard_id,
                Name=dashboard_name,
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:{self.region}:{self.account_id}:user/default/{self.user_name}',
                        'Actions': [
                            'quicksight:DescribeDashboard',
                            'quicksight:ListDashboardVersions',
                            'quicksight:UpdateDashboardPermissions',
                            'quicksight:QueryDashboard',
                            'quicksight:UpdateDashboard',
                            'quicksight:DeleteDashboard',
                            'quicksight:DescribeDashboardPermissions',
                            'quicksight:UpdateDashboardPublishedVersion'
                        ]
                    }
                ],
                SourceEntity={
                    'SourceTemplate': {
                        'DataSetReferences': self._build_dataset_references(template, dataset_arns),
                        'Arn': template.get('TemplateId', f'arn:aws:quicksight:{self.region}:{self.account_id}:template/{dashboard_id}-template')
                    }
                }
            )

            logger.info(f"Dashboard created: {response['Arn']}")
            return response['Arn']

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                logger.warning(f"Dashboard {dashboard_id} already exists")
                response = self.quicksight_client.describe_dashboard(
                    AwsAccountId=self.account_id,
                    DashboardId=dashboard_id
                )
                return response['Dashboard']['Arn']
            else:
                logger.error(f"Error creating dashboard {dashboard_id}: {e}")
                raise

    def _build_dataset_references(
        self,
        template: Dict,
        dataset_arns: Dict[str, str]
    ) -> List[Dict]:
        """
        Build dataset references for dashboard creation.

        Args:
            template: Dashboard template
            dataset_arns: Dictionary of dataset ARNs

        Returns:
            List of dataset references
        """
        references = []

        for dataset_ref in template.get('DataSetReferences', []):
            placeholder = dataset_ref.get('DataSetPlaceholder')
            dataset_id = dataset_ref.get('DataSetArn', '').split('/')[-1]

            if dataset_id in dataset_arns:
                references.append({
                    'DataSetPlaceholder': placeholder,
                    'DataSetArn': dataset_arns[dataset_id]
                })

        return references


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Setup QuickSight dashboards for real-time analytics platform'
    )
    parser.add_argument(
        '--region',
        default=os.environ.get('AWS_REGION', 'us-east-1'),
        help='AWS region'
    )
    parser.add_argument(
        '--account-id',
        default=os.environ.get('AWS_ACCOUNT_ID'),
        help='AWS account ID'
    )
    parser.add_argument(
        '--user-name',
        required=True,
        help='QuickSight user name'
    )
    parser.add_argument(
        '--dynamodb-rides-table',
        default='rides_state',
        help='DynamoDB rides state table name'
    )
    parser.add_argument(
        '--dynamodb-metrics-table',
        default='aggregated_metrics',
        help='DynamoDB aggregated metrics table name'
    )
    parser.add_argument(
        '--athena-database',
        default='ride_analytics',
        help='Athena database name'
    )
    parser.add_argument(
        '--athena-workgroup',
        default='primary',
        help='Athena workgroup name'
    )
    parser.add_argument(
        '--template-dir',
        default='.',
        help='Directory containing dashboard template JSON files'
    )
    parser.add_argument(
        '--skip-data-sources',
        action='store_true',
        help='Skip data source creation'
    )
    parser.add_argument(
        '--skip-datasets',
        action='store_true',
        help='Skip dataset creation'
    )

    args = parser.parse_args()

    try:
        # Initialize manager
        dynamodb_tables = {
            'rides_state': args.dynamodb_rides_table,
            'aggregated_metrics': args.dynamodb_metrics_table
        }

        manager = QuickSightDashboardManager(
            region=args.region,
            account_id=args.account_id,
            user_name=args.user_name,
            dynamodb_tables=dynamodb_tables,
            athena_database=args.athena_database,
            athena_workgroup=args.athena_workgroup
        )

        # Create data sources
        data_source_arns = {}
        if not args.skip_data_sources:
            logger.info("Creating data sources...")
            data_source_arns = manager.create_data_sources()
            logger.info(f"Created {len(data_source_arns)} data sources")
            time.sleep(5)  # Wait for resources to be ready

        # Create datasets
        dataset_arns = {}
        if not args.skip_datasets:
            logger.info("Creating datasets...")
            dataset_arns = manager.create_datasets(data_source_arns)
            logger.info(f"Created {len(dataset_arns)} datasets")
            time.sleep(5)  # Wait for SPICE ingestion

        # Create dashboards
        logger.info("Creating dashboards...")

        dashboards = [
            {
                'id': 'operational-dashboard',
                'name': 'Real-Time Ride Operations Dashboard',
                'template': os.path.join(args.template_dir, 'operational_dashboard.json')
            },
            {
                'id': 'executive-dashboard',
                'name': 'Executive Analytics Dashboard',
                'template': os.path.join(args.template_dir, 'executive_dashboard.json')
            }
        ]

        created_dashboards = []
        for dashboard in dashboards:
            if os.path.exists(dashboard['template']):
                arn = manager.create_dashboard(
                    dashboard['id'],
                    dashboard['name'],
                    dashboard['template'],
                    dataset_arns
                )
                created_dashboards.append(arn)
            else:
                logger.warning(f"Template not found: {dashboard['template']}")

        logger.info(f"\n{'='*80}")
        logger.info("Dashboard setup complete!")
        logger.info(f"Created {len(created_dashboards)} dashboards")
        logger.info(f"{'='*80}\n")

        return 0

    except Exception as e:
        logger.error(f"Error setting up dashboards: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
