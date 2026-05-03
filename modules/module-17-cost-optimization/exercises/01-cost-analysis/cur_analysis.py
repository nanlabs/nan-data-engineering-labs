#!/usr/bin/env python3
"""
Cost and Usage Report (CUR) Analysis
Set up CUR and query with Athena for detailed cost analysis
"""

import boto3
import json
import time
import pandas as pd
from datetime import datetime
import sys

class CURAnalyzer:
    """Manage Cost and Usage Reports and query with Athena"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.s3 = boto3.client('s3', region_name=region)
        self.cur = boto3.client('cur', region_name='us-east-1')  # CUR only in us-east-1
        self.athena = boto3.client('athena', region_name=region)
        self.glue = boto3.client('glue', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        self.bucket_name = f'cur-reports-{self.account_id}'
        self.report_name = 'hourly-cost-usage-report'

    def setup_cur_bucket(self) -> str:
        """
        Create S3 bucket for CUR with proper permissions

        Returns:
            Bucket name
        """
        print(f"\n📦 Setting up CUR bucket: {self.bucket_name}")

        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket already exists: {self.bucket_name}")
            return self.bucket_name
        except:
            pass

        # Create bucket
        try:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"✅ Created bucket: {self.bucket_name}")
        except Exception as e:
            if 'BucketAlreadyOwnedByYou' not in str(e):
                print(f"❌ Error creating bucket: {e}")
                sys.exit(1)

        # Set bucket policy for CUR
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCURGetBucketAcl",
                    "Effect": "Allow",
                    "Principal": {"Service": "billingreports.amazonaws.com"},
                    "Action": ["s3:GetBucketAcl", "s3:GetBucketPolicy"],
                    "Resource": f"arn:aws:s3:::{self.bucket_name}"
                },
                {
                    "Sid": "AllowCURPutObject",
                    "Effect": "Allow",
                    "Principal": {"Service": "billingreports.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                }
            ]
        }

        self.s3.put_bucket_policy(Bucket=self.bucket_name, Policy=json.dumps(policy))
        print("✅ Bucket policy configured")

        return self.bucket_name

    def create_cur_report(self):
        """Create Cost and Usage Report definition"""
        print(f"\n📋 Creating CUR report: {self.report_name}")

        try:
            # Check if report exists
            reports = self.cur.describe_report_definitions()['ReportDefinitions']
            if any(r['ReportName'] == self.report_name for r in reports):
                print(f"✅ CUR report already exists: {self.report_name}")
                return
        except Exception as e:
            print(f"⚠️  Could not check existing reports: {e}")

        # Create CUR report
        try:
            self.cur.put_report_definition(
                ReportDefinition={
                    'ReportName': self.report_name,
                    'TimeUnit': 'HOURLY',
                    'Format': 'Parquet',  # Parquet for better Athena performance
                    'Compression': 'Parquet',
                    'AdditionalSchemaElements': ['RESOURCES'],
                    'S3Bucket': self.bucket_name,
                    'S3Prefix': 'cur-data',
                    'S3Region': 'us-east-1',
                    'AdditionalArtifacts': ['ATHENA'],  # Enable Athena integration
                    'RefreshClosedReports': True,
                    'ReportVersioning': 'OVERWRITE_REPORT'
                }
            )

            print("✅ CUR report created successfully")
            print(f"   Report Name: {self.report_name}")
            print("   Format: Parquet (optimized for Athena)")
            print("   Frequency: Hourly updates")
            print("   Athena: Enabled")
            print("\n⏰ Note: First report available in 24 hours")

        except Exception as e:
            if 'DuplicateReportNameException' in str(e):
                print(f"✅ CUR report already exists: {self.report_name}")
            else:
                print(f"❌ Error creating CUR: {e}")
                sys.exit(1)

    def execute_athena_query(self, query: str, database: str) -> pd.DataFrame:
        """
        Execute Athena query and return results as DataFrame

        Args:
            query: SQL query string
            database: Glue database name

        Returns:
            DataFrame with query results
        """
        output_location = f's3://{self.bucket_name}/athena-results/'

        # Start query execution
        response = self.athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': output_location}
        )

        query_id = response['QueryExecutionId']
        print(f"  Query ID: {query_id}")

        # Wait for completion
        max_attempts = 30
        attempt = 0
        while attempt < max_attempts:
            status = self.athena.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']

            if state == 'SUCCEEDED':
                break
            elif state in ['FAILED', 'CANCELLED']:
                reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                raise Exception(f"Query {state}: {reason}")

            time.sleep(2)
            attempt += 1

        if attempt >= max_attempts:
            raise Exception(f"Query timeout after {max_attempts * 2} seconds")

        # Get results
        results = self.athena.get_query_results(QueryExecutionId=query_id)

        # Parse to DataFrame
        rows = results['ResultSet']['Rows']
        if len(rows) <= 1:
            return pd.DataFrame()

        # Extract column names from first row
        columns = [col.get('VarCharValue', '') for col in rows[0]['Data']]

        # Extract data from remaining rows
        data = []
        for row in rows[1:]:
            data.append([col.get('VarCharValue', '') for col in row['Data']])

        df = pd.DataFrame(data, columns=columns)

        return df

    def query_cur_top_services(self) -> pd.DataFrame:
        """Query CUR for top services by cost"""
        print("\n🔍 Querying CUR for top services...")

        # Database and table created automatically by CUR
        database = f'athenacurcfn_{self.report_name.replace("-", "_")}'
        table = self.report_name.replace('-', '_')

        query = f"""
        SELECT
            line_item_product_code AS service,
            ROUND(SUM(line_item_unblended_cost), 2) AS total_cost,
            COUNT(*) AS line_items
        FROM {table}
        WHERE year='{datetime.now().year}'
          AND month='{datetime.now().month:02d}'
        GROUP BY line_item_product_code
        ORDER BY total_cost DESC
        LIMIT 10;
        """

        try:
            df = self.execute_athena_query(query, database)

            if not df.empty:
                print("\n💰 Top Services (Current Month):")
                for idx, row in df.iterrows():
                    print(f"  {row['service']}: ${row['total_cost']} ({row['line_items']} line items)")

            return df
        except Exception as e:
            print(f"⚠️  Query failed: {e}")
            print("   Ensure CUR data exists and Glue table is created")
            return pd.DataFrame()

    def query_cur_by_tag(self, tag_key: str) -> pd.DataFrame:
        """Query CUR for costs grouped by tag"""
        print(f"\n🏷️  Querying CUR by tag: {tag_key}")

        database = f'athenacurcfn_{self.report_name.replace("-", "_")}'
        table = self.report_name.replace('-', '_')

        # Map tag key to CUR column name
        tag_column_map = {
            'Team': 'resource_tags_user_team',
            'Environment': 'resource_tags_user_environment',
            'Project': 'resource_tags_user_project',
            'CostCenter': 'resource_tags_user_cost_center'
        }

        tag_column = tag_column_map.get(tag_key, f'resource_tags_user_{tag_key.lower()}')

        query = f"""
        SELECT
            {tag_column} AS tag_value,
            ROUND(SUM(line_item_unblended_cost), 2) AS total_cost
        FROM {table}
        WHERE year='{datetime.now().year}'
          AND month='{datetime.now().month:02d}'
          AND {tag_column} IS NOT NULL
        GROUP BY {tag_column}
        ORDER BY total_cost DESC;
        """

        try:
            df = self.execute_athena_query(query, database)

            if not df.empty:
                print(f"\n💰 Cost by {tag_key}:")
                for idx, row in df.iterrows():
                    print(f"  {row['tag_value']}: ${row['total_cost']}")

            return df
        except Exception as e:
            print(f"⚠️  Query failed: {e}")
            return pd.DataFrame()

def main():
    """Main CUR analysis workflow"""
    print("=" * 70)
    print("Cost and Usage Report (CUR) Analysis")
    print("=" * 70)

    analyzer = CURAnalyzer()

    # Step 1: Setup CUR infrastructure
    print("\n[Step 1/4] Setting up CUR infrastructure...")
    analyzer.setup_cur_bucket()
    analyzer.create_cur_report()

    # Step 2: Query CUR data (if available)
    print("\n[Step 2/4] Querying CUR data...")
    print("⏰ Note: If CUR was just created, wait 24 hours for first report")

    try:
        df_services = analyzer.query_cur_top_services()

        # Step 3: Query by tags
        if not df_services.empty:
            print("\n[Step 3/4] Querying costs by tags...")
            for tag in ['Team', 'Environment', 'Project']:
                analyzer.query_cur_by_tag(tag)

        # Step 4: Summary
        print("\n[Step 4/4] Summary")
        print("=" * 70)
        print("\n✅ CUR Setup Complete!")
        print(f"   Bucket: s3://{analyzer.bucket_name}/")
        print(f"   Report: {analyzer.report_name}")
        print(f"   Athena Database: athenacurcfn_{analyzer.report_name.replace('-', '_')}")
        print("\n📊 Next Steps:")
        print("  1. Wait 24 hours for first CUR delivery")
        print("  2. Run MSCK REPAIR TABLE to update partitions")
        print("  3. Query CUR data with Athena for detailed analysis")
        print("  4. Create QuickSight dashboard for visualization")

    except Exception as e:
        print("\n⚠️  CUR querying skipped (data not available yet)")
        print(f"   Error: {e}")

if __name__ == '__main__':
    main()
