"""
Domain Data Product API for Data Mesh

This module implements a data product API following Data Mesh principles:
- Domain ownership (each domain owns its data)
- Data as a product (API, SLAs, documentation)
- Self-serve platform (reusable infrastructure)
- Quality metrics and monitoring

Author: Training Module 18
"""

import sys
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, Query
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DomainDataProduct:
    """
    Represents a data product owned by a domain team.

    Provides API access, tracks SLAs, integrates with Glue Catalog.
    """

    def __init__(
        self,
        domain_name: str,
        data_products: List[str],
        s3_bucket: str,
        glue_database: str,
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Domain Data Product.

        Args:
            domain_name: Domain name (product, sales, customer)
            data_products: List of data product names
            s3_bucket: S3 bucket for domain data
            glue_database: Glue database name
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.domain_name = domain_name
        self.data_products = data_products
        self.s3_bucket = s3_bucket
        self.glue_database = glue_database
        self.region = region

        # AWS clients
        endpoint_url = "http://localhost:4566" if use_localstack else None

        self.s3 = boto3.client('s3', region_name=region, endpoint_url=endpoint_url)
        self.glue = boto3.client('glue', region_name=region, endpoint_url=endpoint_url)
        self.athena = boto3.client('athena', region_name=region, endpoint_url=endpoint_url)
        self.dynamodb = boto3.client('dynamodb', region_name=region, endpoint_url=endpoint_url)

        # SLA configuration
        self.slas = {
            'product': {'freshness_minutes': 60, 'availability_pct': 99.9, 'completeness_pct': 95},
            'sales': {'freshness_minutes': 5, 'availability_pct': 99.95, 'completeness_pct': 100},
            'customer': {'freshness_minutes': 15, 'availability_pct': 99.9, 'completeness_pct': 95}
        }

        logger.info(f"DomainDataProduct initialized: {domain_name}")
        logger.info(f"   Data Products: {', '.join(data_products)}")
        logger.info(f"   Storage: s3://{s3_bucket}")
        logger.info(f"   Catalog: {glue_database}")

    def setup_infrastructure(self) -> Dict[str, Any]:
        """
        Create domain infrastructure (S3, Glue, DynamoDB).

        Returns:
            Dict with created resources
        """
        logger.info(f"=== Setting Up {self.domain_name.title()} Domain ===")

        results = {}

        # Create S3 bucket
        try:
            self.s3.create_bucket(Bucket=self.s3_bucket)
            logger.info(f"✅ Created S3 bucket: {self.s3_bucket}")
            results['s3_bucket'] = self.s3_bucket

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"✅ S3 bucket exists: {self.s3_bucket}")
                results['s3_bucket'] = self.s3_bucket
            else:
                raise

        # Create Glue database
        try:
            self.glue.create_database(
                DatabaseInput={
                    'Name': self.glue_database,
                    'Description': f'{self.domain_name.title()} Domain Data Catalog',
                    'Parameters': {
                        'domain': self.domain_name,
                        'created_at': datetime.now().isoformat()
                    }
                }
            )
            logger.info(f"✅ Created Glue database: {self.glue_database}")
            results['glue_database'] = self.glue_database

        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info(f"✅ Glue database exists: {self.glue_database}")
                results['glue_database'] = self.glue_database
            else:
                raise

        # Create usage tracking table (DynamoDB)
        usage_table = f"{self.domain_name}_api_usage"

        try:
            self.dynamodb.create_table(
                TableName=usage_table,
                KeySchema=[
                    {'AttributeName': 'consumer', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'consumer', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            logger.info(f"✅ Created usage table: {usage_table}")
            results['usage_table'] = usage_table

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                logger.info(f"✅ Usage table exists: {usage_table}")
                results['usage_table'] = usage_table
            else:
                raise

        return results

    def generate_sample_data(
        self,
        data_product: str,
        num_records: int = 10000
    ) -> str:
        """
        Generate sample data for data product.

        Args:
            data_product: Data product name
            num_records: Number of records to generate

        Returns:
            S3 path to data
        """
        logger.info(f"=== Generating Sample Data: {data_product} ===")
        logger.info(f"   Records: {num_records:,}")

        import pandas as pd

        # Generate data based on domain
        if self.domain_name == 'product' and data_product == 'catalog':
            categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Toys']
            brands = ['Brand_A', 'Brand_B', 'Brand_C', 'Brand_D', 'Brand_E']

            data = {
                'product_id': [f"PROD_{i:05d}" for i in range(1, num_records + 1)],
                'name': [f"Product {i}" for i in range(1, num_records + 1)],
                'category': [random.choice(categories) for _ in range(num_records)],
                'brand': [random.choice(brands) for _ in range(num_records)],
                'price': [round(random.uniform(10, 500), 2) for _ in range(num_records)],
                'in_stock': [random.choice([True, False]) for _ in range(num_records)],
                'created_at': datetime.now().isoformat()
            }

        elif self.domain_name == 'sales' and data_product == 'orders':
            data = {
                'order_id': [f"ORD_{i:06d}" for i in range(1, num_records + 1)],
                'customer_id': [f"CUST_{random.randint(1, 1000):04d}" for _ in range(num_records)],
                'product_id': [f"PROD_{random.randint(1, 10000):05d}" for _ in range(num_records)],
                'amount': [round(random.uniform(20, 800), 2) for _ in range(num_records)],
                'order_date': [
                    (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
                    for _ in range(num_records)
                ],
                'status': [random.choice(['completed', 'pending', 'cancelled']) for _ in range(num_records)]
            }

        elif self.domain_name == 'customer' and data_product == 'profiles':
            data = {
                'customer_id': [f"CUST_{i:04d}" for i in range(1, num_records + 1)],
                'email': [f"user{i}@example.com" for i in range(1, num_records + 1)],
                'segment': [random.choice(['high_value', 'medium_value', 'low_value']) for _ in range(num_records)],
                'lifetime_value': [round(random.uniform(100, 10000), 2) for _ in range(num_records)],
                'signup_date': [
                    (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
                    for _ in range(num_records)
                ],
                'is_active': [random.choice([True, False]) for _ in range(num_records)]
            }

        else:
            raise ValueError(f"Unknown data product: {data_product}")

        df = pd.DataFrame(data)

        # Write to S3 (Parquet)
        s3_key = f"{data_product}/data.parquet"
        local_file = f"/tmp/{data_product}.parquet"

        df.to_parquet(local_file, index=False)

        self.s3.upload_file(local_file, self.s3_bucket, s3_key)

        logger.info(f"✅ Generated {num_records:,} records")
        logger.info(f"   Location: s3://{self.s3_bucket}/{s3_key}")

        # Register in Glue Catalog
        self._register_data_product(data_product, s3_key, df)

        return f"s3://{self.s3_bucket}/{s3_key}"

    def _register_data_product(
        self,
        data_product: str,
        s3_key: str,
        df
    ) -> None:
        """Register data product in Glue Catalog."""
        logger.info(f"📋 Registering in Glue Catalog: {data_product}")

        # Infer schema from DataFrame
        type_map = {
            'int64': 'bigint',
            'float64': 'double',
            'object': 'string',
            'bool': 'boolean'
        }

        columns = [
            {
                'Name': col,
                'Type': type_map.get(str(df[col].dtype), 'string')
            }
            for col in df.columns
        ]

        try:
            self.glue.create_table(
                DatabaseName=self.glue_database,
                TableInput={
                    'Name': data_product,
                    'Description': f'{data_product} data product',
                    'StorageDescriptor': {
                        'Columns': columns,
                        'Location': f"s3://{self.s3_bucket}/{data_product}/",
                        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                        'SerdeInfo': {
                            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                        }
                    },
                    'Parameters': {
                        'classification': 'parquet',
                        'domain': self.domain_name,
                        'owner': f'{self.domain_name.title()} Team',
                        'sla_freshness_minutes': str(self.slas[self.domain_name]['freshness_minutes'])
                    }
                }
            )
            logger.info(f"✅ Registered: {self.glue_database}.{data_product}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                logger.info(f"✅ Table already exists: {data_product}")
            else:
                raise

    def query_data_product(
        self,
        data_product: str,
        filters: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query data product via Athena.

        Args:
            data_product: Data product name
            filters: Filter conditions
            limit: Max records

        Returns:
            List of records
        """
        logger.info(f"🔍 Querying: {self.domain_name}.{data_product}")

        # Build SQL
        sql = f"SELECT * FROM {self.glue_database}.{data_product}"

        if filters:
            conditions = []
            for field, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{field} = '{value}'")
                else:
                    conditions.append(f"{field} = {value}")

            sql += " WHERE " + " AND ".join(conditions)

        sql += f" LIMIT {limit}"

        # Execute query
        result_location = f"s3://{self.s3_bucket}/athena-results/"

        try:
            response = self.athena.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': self.glue_database},
                ResultConfiguration={'OutputLocation': result_location}
            )

            query_id = response['QueryExecutionId']

            # Wait for completion
            for _ in range(30):  # 30 seconds max
                status_response = self.athena.get_query_execution(QueryExecutionId=query_id)
                status = status_response['QueryExecution']['Status']['State']

                if status == 'SUCCEEDED':
                    break
                elif status == 'FAILED':
                    reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                    raise Exception(f"Query failed: {reason}")

                time.sleep(1)

            # Get results
            results_response = self.athena.get_query_results(QueryExecutionId=query_id)

            # Parse results
            rows = results_response['ResultSet']['Rows']

            if len(rows) < 2:
                return []

            # Extract column names
            headers = [col['VarCharValue'] for col in rows[0]['Data']]

            # Extract data rows
            records = []
            for row in rows[1:]:
                record = {}
                for i, col in enumerate(row['Data']):
                    value = col.get('VarCharValue')
                    record[headers[i]] = value
                records.append(record)

            logger.info(f"✅ Retrieved {len(records)} records")

            return records

        except ClientError as e:
            logger.error(f"❌ Query failed: {e}")
            return []

    def track_api_usage(
        self,
        consumer: str,
        endpoint: str,
        records_returned: int,
        latency_ms: int
    ) -> None:
        """
        Track API usage for analytics and billing.

        Args:
            consumer: Consumer identifier
            endpoint: API endpoint
            records_returned: Number of records
            latency_ms: Response time
        """
        usage_table = f"{self.domain_name}_api_usage"

        try:
            self.dynamodb.put_item(
                TableName=usage_table,
                Item={
                    'consumer': {'S': consumer},
                    'timestamp': {'S': datetime.now().isoformat()},
                    'endpoint': {'S': endpoint},
                    'records_returned': {'N': str(records_returned)},
                    'latency_ms': {'N': str(latency_ms)},
                    'domain': {'S': self.domain_name}
                }
            )

        except ClientError:
            pass  # Don't fail request if tracking fails

    def check_sla_compliance(self) -> Dict[str, Any]:
        """
        Check SLA compliance for all data products.

        Returns:
            Dict with SLA metrics
        """
        logger.info(f"=== Checking SLAs: {self.domain_name.title()} Domain ===")

        sla_config = self.slas[self.domain_name]

        results = {
            'domain': self.domain_name,
            'sla_config': sla_config,
            'metrics': {},
            'violations': []
        }

        for data_product in self.data_products:
            # Check freshness (last update time)
            freshness_minutes = self._check_freshness(data_product)

            # Check availability (simulated - in production, use CloudWatch)
            availability_pct = random.uniform(99.85, 99.99)

            # Check completeness (% non-null values)
            completeness_pct = random.uniform(95, 99.5)

            metrics = {
                'freshness_minutes': freshness_minutes,
                'availability_pct': availability_pct,
                'completeness_pct': completeness_pct,
                'sla_compliant': (
                    freshness_minutes <= sla_config['freshness_minutes'] and
                    availability_pct >= sla_config['availability_pct'] and
                    completeness_pct >= sla_config['completeness_pct']
                )
            }

            results['metrics'][data_product] = metrics

            # Log violations
            if not metrics['sla_compliant']:
                if freshness_minutes > sla_config['freshness_minutes']:
                    results['violations'].append({
                        'data_product': data_product,
                        'sla': 'freshness',
                        'expected': f"< {sla_config['freshness_minutes']} min",
                        'actual': f"{freshness_minutes:.0f} min"
                    })

                if availability_pct < sla_config['availability_pct']:
                    results['violations'].append({
                        'data_product': data_product,
                        'sla': 'availability',
                        'expected': f"> {sla_config['availability_pct']}%",
                        'actual': f"{availability_pct:.2f}%"
                    })

                if completeness_pct < sla_config['completeness_pct']:
                    results['violations'].append({
                        'data_product': data_product,
                        'sla': 'completeness',
                        'expected': f"> {sla_config['completeness_pct']}%",
                        'actual': f"{completeness_pct:.2f}%"
                    })

        # Print report
        self._print_sla_report(results)

        return results

    def _check_freshness(self, data_product: str) -> float:
        """Calculate data freshness (minutes since last update)."""
        try:
            # Get last modified time from S3
            response = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=f"{data_product}/",
                MaxKeys=1
            )

            if 'Contents' in response and response['Contents']:
                last_modified = response['Contents'][0]['LastModified']
                now = datetime.now(last_modified.tzinfo)
                freshness = (now - last_modified).total_seconds() / 60

                return freshness
            else:
                return 999  # Data product not found → very stale

        except ClientError:
            return 999

    def _print_sla_report(self, results: Dict[str, Any]) -> None:
        """Print formatted SLA report."""
        print("\n" + "=" * 80)
        print(f"📊 SLA COMPLIANCE REPORT: {self.domain_name.upper()} DOMAIN")
        print("=" * 80)

        for data_product, metrics in results['metrics'].items():
            status_icon = "✅" if metrics['sla_compliant'] else "❌"

            print(f"\n{status_icon} {data_product.upper()}")
            print(f"   Freshness: {metrics['freshness_minutes']:.0f} min (SLA: < {results['sla_config']['freshness_minutes']} min)")
            print(f"   Availability: {metrics['availability_pct']:.2f}% (SLA: > {results['sla_config']['availability_pct']}%)")
            print(f"   Completeness: {metrics['completeness_pct']:.1f}% (SLA: > {results['sla_config']['completeness_pct']}%)")

        if results['violations']:
            print(f"\n⚠️  SLA VIOLATIONS: {len(results['violations'])}")
            for v in results['violations']:
                print(f"   • {v['data_product']}.{v['sla']}: Expected {v['expected']}, Got {v['actual']}")
        else:
            print(f"\n✅ All SLAs met ({len(results['metrics'])}/{len(results['metrics'])})")

        print("=" * 80)

    def create_fastapi_app(self) -> FastAPI:
        """
        Create FastAPI application for data product API.

        Returns:
            FastAPI app
        """
        app = FastAPI(
            title=f"{self.domain_name.title()} Domain API",
            description=f"Data products: {', '.join(self.data_products)}",
            version="1.0.0"
        )

        # Health endpoint
        @app.get("/health")
        def health():
            return {"status": "healthy", "domain": self.domain_name}

        # Data product endpoints (dynamic)
        for data_product in self.data_products:
            self._add_data_product_endpoint(app, data_product)

        # SLA endpoint
        @app.get("/sla")
        def get_slas():
            return self.check_sla_compliance()

        return app

    def _add_data_product_endpoint(self, app: FastAPI, data_product: str) -> None:
        """Add endpoint for data product."""

        @app.get(f"/{data_product}")
        def query_product(
            limit: int = Query(100, ge=1, le=1000),
            **filters
        ):
            """Query data product with filters."""
            start_time = time.time()

            records = self.query_data_product(
                data_product=data_product,
                filters=filters if filters else None,
                limit=limit
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Track usage
            self.track_api_usage(
                consumer="unknown",  # In production: extract from API key
                endpoint=f"/{data_product}",
                records_returned=len(records),
                latency_ms=latency_ms
            )

            return {
                'data_product': data_product,
                'domain': self.domain_name,
                'records': records,
                'count': len(records),
                'latency_ms': latency_ms,
                'timestamp': datetime.now().isoformat()
            }

    def serve(self, port: int = 8000) -> None:
        """
        Start FastAPI server.

        Args:
            port: Port to listen on
        """
        logger.info(f"🚀 Starting API server: http://localhost:{port}")
        logger.info(f"   Domain: {self.domain_name}")
        logger.info(f"   Data Products: {', '.join(self.data_products)}")
        logger.info(f"   Docs: http://localhost:{port}/docs")

        app = self.create_fastapi_app()

        uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Data Mesh - Domain Data Product API')

    parser.add_argument(
        '--mode',
        choices=['setup', 'generate-data', 'query', 'serve', 'check-slas'],
        default='serve',
        help='Operation mode'
    )

    parser.add_argument(
        '--domain',
        choices=['product', 'sales', 'customer'],
        required=True,
        help='Domain name'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--data-product',
        type=str,
        help='Data product name (for generate/query modes)'
    )

    parser.add_argument(
        '--num-records',
        type=int,
        default=10000,
        help='Number of records to generate'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port'
    )

    args = parser.parse_args()

    # Domain configuration
    domain_config = {
        'product': {
            'data_products': ['catalog', 'inventory'],
            's3_bucket': 'product-domain-prod',
            'glue_database': 'product_domain_db'
        },
        'sales': {
            'data_products': ['orders', 'revenue'],
            's3_bucket': 'sales-domain-prod',
            'glue_database': 'sales_domain_db'
        },
        'customer': {
            'data_products': ['profiles', 'segments'],
            's3_bucket': 'customer-domain-prod',
            'glue_database': 'customer_domain_db'
        }
    }

    config = domain_config[args.domain]

    # Initialize data product
    dp = DomainDataProduct(
        domain_name=args.domain,
        data_products=config['data_products'],
        s3_bucket=config['s3_bucket'],
        glue_database=config['glue_database'],
        use_localstack=(args.env == 'localstack')
    )

    if args.mode == 'setup':
        resources = dp.setup_infrastructure()
        print(json.dumps(resources, indent=2))

    elif args.mode == 'generate-data':
        if not args.data_product:
            logger.error("❌ --data-product required")
            sys.exit(1)

        s3_path = dp.generate_sample_data(
            data_product=args.data_product,
            num_records=args.num_records
        )

        print(f"✅ Data generated: {s3_path}")

    elif args.mode == 'query':
        if not args.data_product:
            logger.error("❌ --data-product required")
            sys.exit(1)

        records = dp.query_data_product(
            data_product=args.data_product,
            limit=10
        )

        print(json.dumps(records[:5], indent=2, default=str))

    elif args.mode == 'serve':
        dp.serve(port=args.port)

    elif args.mode == 'check-slas':
        dp.check_sla_compliance()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
