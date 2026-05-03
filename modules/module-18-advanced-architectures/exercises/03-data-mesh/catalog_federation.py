"""
Catalog Federation for Data Mesh

This module enables cross-domain data discovery and querying.
Uses Glue Data Catalog and Lake Formation for federated access control.

Key Features:
1. Discover data products across domains
2. Execute federated queries (JOIN across domains)
3. Enforce Lake Formation permissions
4. Track query costs per consumer
5. Provide domain lineage

Author: Training Module 18
"""

import sys
import logging
import argparse
import time
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CatalogFederation:
    """
    Manages federated data catalog for Data Mesh.

    Enables cross-domain discovery and querying.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Catalog Federation.

        Args:
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.glue = boto3.client('glue', region_name=region, endpoint_url=endpoint_url)
        self.athena = boto3.client('athena', region_name=region, endpoint_url=endpoint_url)
        self.lakeformation = boto3.client('lakeformation', region_name=region, endpoint_url=endpoint_url)

        logger.info("CatalogFederation initialized")

    def discover_data_products(
        self,
        domain: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover data products across domains.

        Args:
            domain: Filter by domain (optional)
            tags: Filter by tags (optional)

        Returns:
            List of data product metadata
        """
        logger.info("=== Discovering Data Products ===")

        if domain:
            logger.info(f"   Domain: {domain}")
        if tags:
            logger.info(f"   Tags: {tags}")

        data_products = []

        try:
            # List all databases
            response = self.glue.get_databases()

            for db in response['DatabaseList']:
                db_name = db['Name']

                # Filter by domain
                if domain:
                    db_domain = db.get('Parameters', {}).get('domain', '')
                    if db_domain != domain:
                        continue

                # List tables in database
                tables_response = self.glue.get_tables(DatabaseName=db_name)

                for table in tables_response['TableList']:
                    table_name = table['Name']

                    # Extract metadata
                    product = {
                        'domain': db.get('Parameters', {}).get('domain', 'unknown'),
                        'database': db_name,
                        'data_product': table_name,
                        'location': table['StorageDescriptor']['Location'],
                        'format': table.get('Parameters', {}).get('classification', 'unknown'),
                        'owner': table.get('Parameters', {}).get('owner', 'unknown'),
                        'sla_freshness': table.get('Parameters', {}).get('sla_freshness_minutes', 'N/A'),
                        'created_at': table.get('CreateTime'),
                        'updated_at': table.get('UpdateTime')
                    }

                    # Filter by tags
                    if tags:
                        table_tags = table.get('Parameters', {})
                        if not all(table_tags.get(k) == v for k, v in tags.items()):
                            continue

                    data_products.append(product)

            # Print table
            print("\n" + "=" * 120)
            print("📋 DISCOVERED DATA PRODUCTS")
            print("=" * 120)
            print(f"\n{'Domain':<12} {'Database':<20} {'Data Product':<20} {'Owner':<20} {'SLA Fresh':<12} {'Format':<10}")
            print("-" * 120)

            for dp in data_products:
                print(
                    f"{dp['domain']:<12} "
                    f"{dp['database']:<20} "
                    f"{dp['data_product']:<20} "
                    f"{dp['owner']:<20} "
                    f"< {dp['sla_freshness']} min" if dp['sla_freshness'] != 'N/A' else f"{'N/A':<12} "
                    f"{dp['format']:<10}"
                )

            print("\n" + "=" * 120)
            logger.info(f"Found {len(data_products)} data products")

            return data_products

        except ClientError as e:
            logger.error(f"❌ Discovery failed: {e}")
            return []

    def execute_federated_query(
        self,
        sql: str,
        output_location: str = "s3://athena-results-datamesh/"
    ) -> pd.DataFrame:
        """
        Execute SQL query across multiple domains (federated query).

        Args:
            sql: SQL query
            output_location: S3 location for results

        Returns:
            Query results as DataFrame
        """
        logger.info("=== Executing Federated Query ===")
        logger.info(f"   SQL: {sql[:100]}...")

        start_time = time.time()

        try:
            # Start query execution
            response = self.athena.start_query_execution(
                QueryString=sql,
                ResultConfiguration={'OutputLocation': output_location}
            )

            query_id = response['QueryExecutionId']
            logger.info(f"   Query ID: {query_id}")

            # Wait for completion
            for _ in range(60):  # 60 seconds max
                status_response = self.athena.get_query_execution(QueryExecutionId=query_id)
                status = status_response['QueryExecution']['Status']['State']

                if status == 'SUCCEEDED':
                    break
                elif status == 'FAILED':
                    reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                    raise Exception(f"Query failed: {reason}")

                time.sleep(1)

            # Get statistics
            stats = status_response['QueryExecution']['Statistics']
            data_scanned_mb = stats.get('DataScannedInBytes', 0) / 1024 / 1024
            execution_time_ms = stats.get('EngineExecutionTimeInMillis', 0)

            # Get results
            results_response = self.athena.get_query_results(QueryExecutionId=query_id)

            # Parse to DataFrame
            rows = results_response['ResultSet']['Rows']

            if len(rows) < 2:
                logger.info("✅ Query succeeded (no results)")
                return pd.DataFrame()

            # Extract headers
            headers = [col['VarCharValue'] for col in rows[0]['Data']]

            # Extract data
            data = []
            for row in rows[1:]:
                record = {}
                for i, col in enumerate(row['Data']):
                    record[headers[i]] = col.get('VarCharValue')
                data.append(record)

            df = pd.DataFrame(data)

            duration = time.time() - start_time
            cost = data_scanned_mb / 1024 * 5  # $5 per TB

            logger.info("✅ Query complete")
            logger.info(f"   Rows: {len(df)}")
            logger.info(f"   Data Scanned: {data_scanned_mb:.2f} MB")
            logger.info(f"   Execution Time: {execution_time_ms / 1000:.2f} sec")
            logger.info(f"   Cost: ${cost:.4f}")

            return df

        except ClientError as e:
            logger.error(f"❌ Query failed: {e}")
            return pd.DataFrame()

    def grant_domain_access(
        self,
        consumer_principal: str,
        database: str,
        table: str,
        columns: Optional[List[str]] = None
    ) -> None:
        """
        Grant Lake Formation permissions to consumer.

        Args:
            consumer_principal: IAM role ARN
            database: Database name
            table: Table name
            columns: Specific columns (None = all)
        """
        logger.info("=== Granting Access ===")
        logger.info(f"   Consumer: {consumer_principal}")
        logger.info(f"   Resource: {database}.{table}")

        if columns:
            logger.info(f"   Columns: {', '.join(columns)}")

        try:
            permissions = ['SELECT', 'DESCRIBE']

            if columns:
                # Column-level permissions
                self.lakeformation.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': consumer_principal},
                    Resource={
                        'TableWithColumns': {
                            'DatabaseName': database,
                            'Name': table,
                            'ColumnNames': columns
                        }
                    },
                    Permissions=permissions
                )
            else:
                # Table-level permissions
                self.lakeformation.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': consumer_principal},
                    Resource={
                        'Table': {
                            'DatabaseName': database,
                            'Name': table
                        }
                    },
                    Permissions=permissions
                )

            logger.info("✅ Access granted")

        except ClientError as e:
            logger.error(f"❌ Failed to grant access: {e}")
            raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Data Mesh - Catalog Federation')

    parser.add_argument(
        '--mode',
        choices=['discover', 'query', 'grant'],
        default='discover',
        help='Operation mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--domain',
        type=str,
        help='Domain name (for filtering)'
    )

    parser.add_argument(
        '--sql',
        type=str,
        help='SQL query (for query mode)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='s3://athena-results-datamesh/',
        help='Athena result location'
    )

    args = parser.parse_args()

    # Initialize federation
    federation = CatalogFederation(use_localstack=(args.env == 'localstack'))

    if args.mode == 'discover':
        federation.discover_data_products(domain=args.domain)

    elif args.mode == 'query':
        if not args.sql:
            logger.error("❌ --sql required for query mode")
            sys.exit(1)

        df = federation.execute_federated_query(
            sql=args.sql,
            output_location=args.output
        )

        if not df.empty:
            print("\n" + "=" * 100)
            print("📊 QUERY RESULTS")
            print("=" * 100)
            print()
            print(df.to_string(index=False))
            print()
            print("=" * 100)

    elif args.mode == 'grant':
        logger.info("Grant permissions via Lake Formation console or AWS CLI")
        logger.info("Example:")
        logger.info("  aws lakeformation grant-permissions \\")
        logger.info("    --principal DataLakePrincipalIdentifier=arn:aws:iam::123456789:role/AnalyticsTeam \\")
        logger.info("    --resource '{ \"Table\": { \"DatabaseName\": \"sales_domain_db\", \"Name\": \"orders\" }}' \\")
        logger.info("    --permissions SELECT DESCRIBE")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
