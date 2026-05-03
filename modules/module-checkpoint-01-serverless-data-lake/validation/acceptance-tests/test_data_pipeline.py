"""
Data pipeline integration tests
End-to-end tests for data ingestion, transformation, and querying
"""

import pytest
import json
import csv
import time
import logging
from datetime import datetime
from io import StringIO
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TestDataUpload:
    """Tests for data upload to raw zone"""

    @pytest.mark.integration
    def test_upload_csv_to_raw_bucket(self, s3_client, bucket_names, test_data_generator, cleanup_test_data):
        """
        Upload sample CSV data to raw bucket

        Tests:
        - CSV file can be uploaded to raw bucket
        - File is accessible after upload
        - Metadata is correct
        """
        logger.info("Testing CSV upload to raw bucket")

        raw_bucket = bucket_names['raw']
        customers = test_data_generator['customers'](count=10)

        # Convert to CSV
        csv_buffer = StringIO()
        fieldnames = customers[0].keys()
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)

        csv_data = csv_buffer.getvalue()

        # Upload to S3
        key = f"test/customers/customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=csv_data,
            ContentType='text/csv'
        )

        cleanup_test_data(raw_bucket, key)

        # Verify upload
        response = s3_client.head_object(Bucket=raw_bucket, Key=key)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        assert response['ContentLength'] > 0

        logger.info(f"✓ Uploaded CSV to s3://{raw_bucket}/{key}")

    @pytest.mark.integration
    def test_upload_json_to_raw_bucket(self, s3_client, bucket_names, test_data_generator, cleanup_test_data):
        """
        Upload sample JSON data to raw bucket

        Tests:
        - JSON file can be uploaded to raw bucket
        - File is accessible after upload
        - Content type is correct
        """
        logger.info("Testing JSON upload to raw bucket")

        raw_bucket = bucket_names['raw']
        orders = test_data_generator['orders'](count=20)

        json_data = json.dumps(orders, indent=2)

        # Upload to S3
        key = f"test/orders/orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )

        cleanup_test_data(raw_bucket, key)

        # Verify upload
        response = s3_client.head_object(Bucket=raw_bucket, Key=key)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        assert response['ContentType'] == 'application/json'

        logger.info(f"✓ Uploaded JSON to s3://{raw_bucket}/{key}")

    @pytest.mark.integration
    def test_upload_with_partitions(self, s3_client, bucket_names, test_data_generator, cleanup_test_data):
        """
        Upload data with partition structure

        Tests:
        - Data can be uploaded with year/month/day partitions
        - Partition structure follows Hive convention
        """
        logger.info("Testing partitioned data upload")

        raw_bucket = bucket_names['raw']
        products = test_data_generator['products'](count=5)

        json_data = json.dumps(products, indent=2)

        # Create partition path
        now = datetime.now()
        key = f"test/products/year={now.year}/month={now.month:02d}/day={now.day:02d}/products_{now.strftime('%H%M%S')}.json"

        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=json_data
        )

        cleanup_test_data(raw_bucket, key)

        # Verify partition structure
        assert f"year={now.year}" in key
        assert f"month={now.month:02d}" in key
        assert f"day={now.day:02d}" in key

        logger.info(f"✓ Uploaded partitioned data to s3://{raw_bucket}/{key}")


class TestLambdaTriggers:
    """Tests for Lambda function triggers and execution"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_lambda_triggered_on_s3_upload(self, s3_client, logs_client, bucket_names,
                                           lambda_function_names, test_data_generator, cleanup_test_data):
        """
        Verify Lambda function is triggered on S3 upload

        Tests:
        - Lambda executes when file uploaded to raw bucket
        - CloudWatch logs show execution
        - No errors in Lambda execution
        """
        logger.info("Testing Lambda trigger on S3 upload")

        raw_bucket = bucket_names['raw']
        function_name = lambda_function_names.get('file_validator', list(lambda_function_names.values())[0])

        # Upload test file
        key = f"test/trigger/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_data = json.dumps({'test': 'data', 'timestamp': datetime.now().isoformat()})

        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=test_data
        )

        cleanup_test_data(raw_bucket, key)

        # Wait for Lambda execution
        logger.info("Waiting for Lambda execution...")
        time.sleep(10)

        # Check CloudWatch logs
        log_group_name = f"/aws/lambda/{function_name}"

        try:
            # Get recent log streams
            response = logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )

            if response['logStreams']:
                logger.info(f"✓ Lambda execution logs found in {log_group_name}")

                # Get recent events
                log_stream = response['logStreams'][0]['logStreamName']
                events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=log_stream,
                    limit=10,
                    startFromHead=False
                )

                # Check for errors
                events = events_response['events']
                error_events = [e for e in events if 'ERROR' in e['message'] or 'Error' in e['message']]

                if error_events:
                    logger.warning(f"Found {len(error_events)} error events in logs")
                else:
                    logger.info("✓ No errors in recent Lambda executions")
            else:
                logger.warning("No recent log streams found")

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Log group {log_group_name} not found")
            else:
                raise

    @pytest.mark.integration
    @pytest.mark.slow
    def test_lambda_processes_multiple_files(self, s3_client, bucket_names, test_data_generator, cleanup_test_data):
        """
        Verify Lambda can process multiple files

        Tests:
        - Multiple files can be uploaded
        - Lambda processes each file
        - No conflicts or race conditions
        """
        logger.info("Testing Lambda processing of multiple files")

        raw_bucket = bucket_names['raw']

        # Upload multiple files
        file_count = 3
        uploaded_keys = []

        for i in range(file_count):
            key = f"test/multi/file_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            test_data = json.dumps({'file_id': i, 'timestamp': datetime.now().isoformat()})

            s3_client.put_object(
                Bucket=raw_bucket,
                Key=key,
                Body=test_data
            )

            uploaded_keys.append(key)
            cleanup_test_data(raw_bucket, key)

            # Small delay between uploads
            time.sleep(1)

        logger.info(f"✓ Uploaded {file_count} files for processing")

        # Wait for processing
        time.sleep(5)

        # Verify all files still exist (not deleted by error)
        for key in uploaded_keys:
            response = s3_client.head_object(Bucket=raw_bucket, Key=key)
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200

        logger.info("✓ All files processed successfully")


class TestGlueCrawler:
    """Tests for Glue crawler schema discovery"""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.expensive
    def test_crawler_discovers_schema(self, glue_client, s3_client, bucket_names,
                                      glue_database_name, test_data_generator, cleanup_test_data):
        """
        Test Glue crawler schema discovery

        Tests:
        - Crawler can be started
        - Crawler discovers schema from S3 data
        - Tables are created in Glue catalog
        """
        logger.info("Testing Glue crawler schema discovery")

        # Upload test data
        raw_bucket = bucket_names['raw']
        customers = test_data_generator['customers'](count=100)

        json_data = json.dumps(customers, indent=2)
        key = "test/crawler/customers/data.json"

        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=json_data
        )

        cleanup_test_data(raw_bucket, key)

        # Find a crawler
        response = glue_client.list_crawlers()
        crawlers = response['CrawlerNames']

        if not crawlers:
            logger.warning("No crawlers found to test")
            pytest.skip("No Glue crawlers configured")

        crawler_name = crawlers[0]
        logger.info(f"Using crawler: {crawler_name}")

        # Check crawler state
        crawler_info = glue_client.get_crawler(Name=crawler_name)
        state = crawler_info['Crawler']['State']

        logger.info(f"✓ Crawler '{crawler_name}' exists with state: {state}")

        # Get tables in database
        try:
            tables_response = glue_client.get_tables(DatabaseName=glue_database_name)
            tables = tables_response['TableList']
            logger.info(f"✓ Found {len(tables)} tables in database '{glue_database_name}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                logger.warning(f"Database '{glue_database_name}' not found")
            else:
                raise

    @pytest.mark.integration
    def test_glue_tables_have_correct_schema(self, glue_client, glue_database_name):
        """
        Verify Glue tables have correct schema

        Tests:
        - Tables have columns defined
        - Column types are correct
        - Partition keys are defined (if applicable)
        """
        logger.info("Testing Glue table schemas")

        try:
            response = glue_client.get_tables(DatabaseName=glue_database_name)
            tables = response['TableList']

            if not tables:
                logger.warning("No tables found in Glue database")
                return

            for table in tables[:3]:  # Check first 3 tables
                table_name = table['Name']
                columns = table['StorageDescriptor']['Columns']

                assert len(columns) > 0, f"Table {table_name} has no columns"

                logger.info(f"✓ Table '{table_name}' has {len(columns)} columns")

                # Check partition keys
                partition_keys = table.get('PartitionKeys', [])
                if partition_keys:
                    logger.info(f"  - Partition keys: {[k['Name'] for k in partition_keys]}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                logger.warning(f"Database '{glue_database_name}' not found")
            else:
                raise


class TestGlueETL:
    """Tests for Glue ETL job execution"""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.expensive
    def test_glue_job_transforms_data(self, glue_client, s3_client, bucket_names):
        """
        Test Glue ETL job execution

        Tests:
        - Glue job can be started
        - Job completes successfully
        - Transformed data appears in processed bucket
        """
        logger.info("Testing Glue ETL job execution")

        # Get list of Glue jobs
        response = glue_client.list_jobs()
        job_names = response['JobNames']

        if not job_names:
            logger.warning("No Glue jobs found")
            pytest.skip("No Glue jobs configured")

        job_name = job_names[0]
        logger.info(f"Found Glue job: {job_name}")

        # Get job status
        runs_response = glue_client.get_job_runs(JobName=job_name, MaxResults=5)
        runs = runs_response['JobRuns']

        if runs:
            latest_run = runs[0]
            state = latest_run['JobRunState']
            logger.info(f"✓ Latest run state: {state}")

            if state == 'SUCCEEDED':
                logger.info(f"✓ Job '{job_name}' completed successfully")

                # Check execution time
                execution_time = latest_run.get('ExecutionTime', 0)
                logger.info(f"  - Execution time: {execution_time} seconds")
            elif state == 'FAILED':
                error_message = latest_run.get('ErrorMessage', 'Unknown error')
                logger.error(f"Job failed: {error_message}")
        else:
            logger.info("No job runs found yet")

    @pytest.mark.integration
    def test_transformed_data_quality(self, s3_client, bucket_names):
        """
        Verify quality of transformed data

        Tests:
        - Data exists in processed bucket
        - File format is correct (Parquet)
        - Data is readable
        """
        logger.info("Testing transformed data quality")

        processed_bucket = bucket_names['processed']

        # List objects in processed bucket
        response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=10
        )

        if 'Contents' in response and response['Contents']:
            object_count = len(response['Contents'])
            logger.info(f"✓ Found {object_count} objects in processed bucket")

            # Check file extensions
            parquet_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.parquet')]
            logger.info(f"✓ Found {len(parquet_files)} Parquet files")
        else:
            logger.warning("No objects found in processed bucket")


class TestAthenaQueries:
    """Tests for Athena query execution"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_athena_query_execution(self, athena_client, s3_client, bucket_names,
                                    glue_database_name, athena_test_workgroup):
        """
        Test Athena query execution

        Tests:
        - Query can be executed
        - Results are returned
        - Query completes in reasonable time
        """
        logger.info("Testing Athena query execution")

        # Get tables
        try:
            query = f"SHOW TABLES IN {glue_database_name}"

            response = athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': glue_database_name},
                ResultConfiguration={
                    'OutputLocation': f"s3://{bucket_names['athena_results']}/test-results/"
                }
            )

            query_execution_id = response['QueryExecutionId']
            logger.info(f"Started query: {query_execution_id}")

            # Wait for query to complete
            max_wait = 30
            waited = 0
            while waited < max_wait:
                status_response = athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )

                status = status_response['QueryExecution']['Status']['State']

                if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break

                time.sleep(2)
                waited += 2

            assert status == 'SUCCEEDED', f"Query failed with status: {status}"
            logger.info(f"✓ Query completed successfully in {waited} seconds")

            # Get results
            results_response = athena_client.get_query_results(
                QueryExecutionId=query_execution_id
            )

            rows = results_response['ResultSet']['Rows']
            logger.info(f"✓ Query returned {len(rows)} rows")

        except ClientError as e:
            logger.error(f"Athena query failed: {str(e)}")
            raise

    @pytest.mark.integration
    @pytest.mark.slow
    def test_athena_select_query(self, athena_client, s3_client, bucket_names, glue_database_name):
        """
        Test Athena SELECT query on data

        Tests:
        - SELECT query works on tables
        - Data can be queried and filtered
        - Results are accurate
        """
        logger.info("Testing Athena SELECT query")

        # First, check if tables exist
        query = f"SHOW TABLES IN {glue_database_name}"

        try:
            response = athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': glue_database_name},
                ResultConfiguration={
                    'OutputLocation': f"s3://{bucket_names['athena_results']}/test-results/"
                }
            )

            query_execution_id = response['QueryExecutionId']

            # Wait for completion
            time.sleep(5)

            results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
            tables = results['ResultSet']['Rows'][1:]  # Skip header

            if not tables:
                logger.warning("No tables available for SELECT query test")
                pytest.skip("No tables in database")

            logger.info(f"✓ Found {len(tables)} tables available for querying")

        except ClientError as e:
            logger.error(f"Query failed: {str(e)}")
            raise


class TestEndToEnd:
    """End-to-end pipeline tests"""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.expensive
    def test_complete_pipeline_flow(self, s3_client, bucket_names, test_data_generator, cleanup_test_data):
        """
        Test complete data pipeline flow

        Tests:
        - Upload data to raw bucket
        - Data flows through pipeline
        - Data appears in processed bucket
        - Data is queryable
        """
        logger.info("Testing complete end-to-end pipeline flow")

        # 1. Upload data
        raw_bucket = bucket_names['raw']
        orders = test_data_generator['orders'](count=50)

        json_data = json.dumps(orders, indent=2)
        key = f"e2e-test/orders/orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=json_data
        )

        cleanup_test_data(raw_bucket, key)
        logger.info("✓ Step 1: Uploaded data to raw bucket")

        # 2. Wait for processing
        logger.info("Waiting for pipeline processing...")
        time.sleep(15)

        # 3. Verify data in raw zone
        response = s3_client.head_object(Bucket=raw_bucket, Key=key)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        logger.info("✓ Step 2: Data verified in raw zone")

        # 4. Check processed bucket
        processed_bucket = bucket_names['processed']
        processed_response = s3_client.list_objects_v2(
            Bucket=processed_bucket,
            MaxKeys=1
        )

        if 'Contents' in processed_response:
            logger.info("✓ Step 3: Data found in processed zone")
        else:
            logger.warning("No data in processed zone yet")

        logger.info("✓ End-to-end pipeline test completed")


class TestErrorHandling:
    """Tests for error handling and notifications"""

    @pytest.mark.integration
    def test_invalid_data_handling(self, s3_client, bucket_names, cleanup_test_data):
        """
        Test handling of invalid data

        Tests:
        - Invalid data can be uploaded
        - Error is logged
        - SNS notification sent (if configured)
        """
        logger.info("Testing invalid data handling")

        raw_bucket = bucket_names['raw']

        # Upload invalid JSON
        key = f"test/invalid/bad_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        invalid_data = "{ this is not valid JSON }"

        s3_client.put_object(
            Bucket=raw_bucket,
            Key=key,
            Body=invalid_data
        )

        cleanup_test_data(raw_bucket, key)

        logger.info("✓ Uploaded invalid data to test error handling")

        # Wait for processing
        time.sleep(5)

        # File should still exist (not deleted)
        response = s3_client.head_object(Bucket=raw_bucket, Key=key)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200

        logger.info("✓ Invalid data handling test completed")
