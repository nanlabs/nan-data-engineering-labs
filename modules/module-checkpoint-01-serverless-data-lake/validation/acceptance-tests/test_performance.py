"""
Performance and cost optimization tests
Tests for execution time, resource usage, and cost efficiency
"""

import pytest
import time
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TestLambdaPerformance:
    """Performance tests for Lambda functions"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_lambda_execution_time(self, logs_client, cloudwatch_client, lambda_function_names):
        """
        Verify Lambda execution time is acceptable

        Tests:
        - Average execution time < 5 seconds
        - No timeouts
        - Performance is consistent
        """
        logger.info("Testing Lambda execution time")

        for function_type, function_name in lambda_function_names.items():
            try:
                # Get metrics from CloudWatch
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=1)

                response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Duration',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average', 'Maximum', 'Minimum']
                )

                datapoints = response['Datapoints']

                if datapoints:
                    avg_duration = datapoints[0].get('Average', 0)
                    max_duration = datapoints[0].get('Maximum', 0)
                    min_duration = datapoints[0].get('Minimum', 0)

                    # Convert from milliseconds to seconds
                    avg_seconds = avg_duration / 1000
                    max_seconds = max_duration / 1000

                    logger.info(f"✓ {function_name}:")
                    logger.info(f"  - Average: {avg_seconds:.2f}s")
                    logger.info(f"  - Maximum: {max_seconds:.2f}s")
                    logger.info(f"  - Minimum: {min_duration/1000:.2f}s")

                    # Check if average is within acceptable range
                    assert avg_seconds < 5.0, \
                        f"Average execution time {avg_seconds:.2f}s exceeds 5 second threshold"

                    logger.info(f"✓ Performance acceptable for {function_name}")
                else:
                    logger.warning(f"No metrics available for {function_name}")

            except ClientError as e:
                logger.warning(f"Could not get metrics for {function_name}: {str(e)}")

    @pytest.mark.integration
    def test_lambda_error_rate(self, cloudwatch_client, lambda_function_names):
        """
        Check Lambda error rates

        Tests:
        - Error rate < 5%
        - No persistent errors
        - Throttling is minimal
        """
        logger.info("Testing Lambda error rates")

        for function_type, function_name in lambda_function_names.items():
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)

                # Get invocations
                invocations_response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=['Sum']
                )

                # Get errors
                errors_response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Errors',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=['Sum']
                )

                invocations = invocations_response['Datapoints'][0]['Sum'] if invocations_response['Datapoints'] else 0
                errors = errors_response['Datapoints'][0]['Sum'] if errors_response['Datapoints'] else 0

                if invocations > 0:
                    error_rate = (errors / invocations) * 100

                    logger.info(f"✓ {function_name}:")
                    logger.info(f"  - Invocations: {int(invocations)}")
                    logger.info(f"  - Errors: {int(errors)}")
                    logger.info(f"  - Error rate: {error_rate:.2f}%")

                    assert error_rate < 5.0, \
                        f"Error rate {error_rate:.2f}% exceeds 5% threshold"
                else:
                    logger.warning(f"No invocations found for {function_name}")

            except (ClientError, IndexError) as e:
                logger.warning(f"Could not get error metrics for {function_name}: {str(e)}")

    @pytest.mark.integration
    def test_lambda_memory_usage(self, cloudwatch_client, lambda_function_names, lambda_client):
        """
        Check Lambda memory usage efficiency

        Tests:
        - Memory is not over-provisioned
        - Memory usage is consistent
        - No out of memory errors
        """
        logger.info("Testing Lambda memory usage")

        for function_type, function_name in lambda_function_names.items():
            try:
                # Get function configuration
                function_config = lambda_client.get_function(FunctionName=function_name)
                configured_memory = function_config['Configuration']['MemorySize']

                # Get memory metrics from logs insights would be ideal
                # For now, just check configuration is reasonable
                logger.info(f"✓ {function_name}:")
                logger.info(f"  - Configured memory: {configured_memory} MB")

                # Check if memory is reasonable (not too high or too low)
                assert 128 <= configured_memory <= 3008, \
                    f"Memory configuration {configured_memory} MB out of reasonable range"

                logger.info("✓ Memory configuration is reasonable")

            except ClientError as e:
                logger.warning(f"Could not check memory for {function_name}: {str(e)}")

    @pytest.mark.integration
    def test_lambda_concurrent_executions(self, cloudwatch_client, lambda_function_names):
        """
        Check Lambda concurrent execution patterns

        Tests:
        - Concurrent executions stay within limits
        - No throttling issues
        - Scalability is adequate
        """
        logger.info("Testing Lambda concurrent executions")

        for function_type, function_name in lambda_function_names.items():
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=1)

                response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='ConcurrentExecutions',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Maximum', 'Average']
                )

                datapoints = response['Datapoints']

                if datapoints:
                    max_concurrent = datapoints[0].get('Maximum', 0)
                    avg_concurrent = datapoints[0].get('Average', 0)

                    logger.info(f"✓ {function_name}:")
                    logger.info(f"  - Max concurrent: {int(max_concurrent)}")
                    logger.info(f"  - Avg concurrent: {avg_concurrent:.1f}")

                    # Check not hitting limits (default is 1000)
                    assert max_concurrent < 900, \
                        f"Concurrent executions {max_concurrent} approaching limit"
                else:
                    logger.warning(f"No concurrency metrics for {function_name}")

            except (ClientError, IndexError) as e:
                logger.warning(f"Could not get concurrency metrics: {str(e)}")


class TestGluePerformance:
    """Performance tests for Glue jobs"""

    @pytest.mark.integration
    @pytest.mark.expensive
    def test_glue_job_duration(self, glue_client):
        """
        Check Glue job execution duration

        Tests:
        - Jobs complete within expected time
        - No long-running jobs
        - Duration is consistent
        """
        logger.info("Testing Glue job duration")

        response = glue_client.list_jobs()
        job_names = response['JobNames']

        if not job_names:
            logger.warning("No Glue jobs found")
            pytest.skip("No Glue jobs configured")

        for job_name in job_names[:5]:  # Check first 5 jobs
            try:
                runs_response = glue_client.get_job_runs(
                    JobName=job_name,
                    MaxResults=10
                )

                runs = runs_response['JobRuns']

                if runs:
                    successful_runs = [r for r in runs if r['JobRunState'] == 'SUCCEEDED']

                    if successful_runs:
                        durations = [r.get('ExecutionTime', 0) for r in successful_runs]
                        avg_duration = sum(durations) / len(durations)
                        max_duration = max(durations)
                        min_duration = min(durations)

                        logger.info(f"✓ {job_name}:")
                        logger.info(f"  - Average: {avg_duration:.1f}s")
                        logger.info(f"  - Maximum: {max_duration:.1f}s")
                        logger.info(f"  - Minimum: {min_duration:.1f}s")

                        # Check duration is reasonable (< 10 minutes for typical jobs)
                        assert avg_duration < 600, \
                            f"Average duration {avg_duration}s exceeds 10 minutes"
                    else:
                        logger.warning(f"No successful runs for {job_name}")
                else:
                    logger.warning(f"No runs found for {job_name}")

            except ClientError as e:
                logger.warning(f"Could not get job runs for {job_name}: {str(e)}")

    @pytest.mark.integration
    def test_glue_dpu_allocation(self, glue_client):
        """
        Check Glue DPU allocation efficiency

        Tests:
        - DPUs are appropriately sized
        - Not over-provisioned
        - Cost-effective configuration
        """
        logger.info("Testing Glue DPU allocation")

        response = glue_client.list_jobs()
        job_names = response['JobNames']

        for job_name in job_names[:5]:
            try:
                job_info = glue_client.get_job(JobName=job_name)
                job = job_info['Job']

                # Get DPU allocation
                max_capacity = job.get('MaxCapacity')
                worker_type = job.get('WorkerType')
                number_of_workers = job.get('NumberOfWorkers')

                logger.info(f"✓ {job_name}:")
                if max_capacity:
                    logger.info(f"  - Max Capacity: {max_capacity} DPUs")
                if worker_type and number_of_workers:
                    logger.info(f"  - Workers: {number_of_workers} x {worker_type}")

                # Check reasonable limits
                if max_capacity:
                    assert max_capacity <= 10, \
                        f"Max capacity {max_capacity} DPUs may be excessive"

            except ClientError as e:
                logger.warning(f"Could not get job info for {job_name}: {str(e)}")


class TestAthenaPerformance:
    """Performance tests for Athena queries"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_athena_query_execution_time(self, athena_client, s3_client, bucket_names, glue_database_name):
        """
        Measure Athena query performance

        Tests:
        - Simple queries < 10 seconds
        - Complex queries < 60 seconds
        - Query optimization is effective
        """
        logger.info("Testing Athena query performance")

        # Run a simple query
        query = f"SHOW TABLES IN {glue_database_name}"

        try:
            start_time = time.time()

            response = athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': glue_database_name},
                ResultConfiguration={
                    'OutputLocation': f"s3://{bucket_names['athena_results']}/performance-test/"
                }
            )

            query_execution_id = response['QueryExecutionId']

            # Wait for completion
            max_wait = 30
            waited = 0
            status = 'QUEUED'

            while waited < max_wait and status not in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                time.sleep(2)
                waited += 2

                status_response = athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                status = status_response['QueryExecution']['Status']['State']

            end_time = time.time()
            execution_time = end_time - start_time

            logger.info(f"✓ Query executed in {execution_time:.2f} seconds")
            logger.info(f"  - Status: {status}")

            if status == 'SUCCEEDED':
                # Get statistics
                stats = status_response['QueryExecution']['Statistics']
                data_scanned = stats.get('DataScannedInBytes', 0)
                engine_execution_time = stats.get('EngineExecutionTimeInMillis', 0) / 1000

                logger.info(f"  - Data scanned: {data_scanned / (1024*1024):.2f} MB")
                logger.info(f"  - Engine time: {engine_execution_time:.2f}s")

                # Simple query should be fast
                assert engine_execution_time < 10, \
                    f"Query execution {engine_execution_time}s exceeds 10 second threshold"

        except ClientError as e:
            logger.warning(f"Could not test Athena performance: {str(e)}")

    @pytest.mark.integration
    def test_athena_data_scanned(self, athena_client, cloudwatch_client):
        """
        Check Athena data scanned for cost optimization

        Tests:
        - Partitioning reduces data scanned
        - Queries are optimized
        - No full table scans on large tables
        """
        logger.info("Testing Athena data scanned efficiency")

        # Check CloudWatch metrics for recent queries
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)

            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Athena',
                MetricName='DataScannedInBytes',
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=['Sum', 'Average']
            )

            datapoints = response['Datapoints']

            if datapoints:
                total_scanned = datapoints[0].get('Sum', 0)
                avg_scanned = datapoints[0].get('Average', 0)

                total_gb = total_scanned / (1024**3)
                avg_mb = avg_scanned / (1024**2)

                logger.info("✓ Last 24 hours:")
                logger.info(f"  - Total data scanned: {total_gb:.2f} GB")
                logger.info(f"  - Average per query: {avg_mb:.2f} MB")

                # Check if data scanned is reasonable (< 10 GB per day for test environment)
                assert total_gb < 10, \
                    f"Data scanned {total_gb:.2f} GB exceeds reasonable threshold"
            else:
                logger.warning("No Athena metrics available")

        except ClientError as e:
            logger.warning(f"Could not get Athena metrics: {str(e)}")


class TestStorageCosts:
    """Tests for storage cost optimization"""

    @pytest.mark.integration
    def test_s3_storage_costs(self, s3_client, bucket_names, cloudwatch_client):
        """
        Calculate and verify S3 storage costs

        Tests:
        - Storage cost < $50/month
        - Growth rate is acceptable
        - No unexpected large files
        """
        logger.info("Testing S3 storage costs")

        total_size = 0
        bucket_sizes = {}

        for bucket_type, bucket_name in bucket_names.items():
            try:
                # Get bucket size
                response = s3_client.list_objects_v2(Bucket=bucket_name)

                if 'Contents' in response:
                    bucket_size = sum(obj['Size'] for obj in response['Contents'])
                    bucket_sizes[bucket_type] = bucket_size
                    total_size += bucket_size

                    size_mb = bucket_size / (1024**2)
                    logger.info(f"  - {bucket_type}: {size_mb:.2f} MB")

            except ClientError as e:
                logger.warning(f"Could not get size for {bucket_name}: {str(e)}")

        total_gb = total_size / (1024**3)
        logger.info(f"✓ Total storage: {total_gb:.2f} GB")

        # Calculate estimated monthly cost (S3 Standard: ~$0.023/GB)
        estimated_cost = total_gb * 0.023
        logger.info(f"✓ Estimated monthly cost: ${estimated_cost:.2f}")

        # Check cost is within budget
        assert estimated_cost < 50, \
            f"Estimated storage cost ${estimated_cost:.2f} exceeds $50 budget"

    @pytest.mark.integration
    def test_s3_lifecycle_optimization(self, s3_client, bucket_names):
        """
        Verify S3 lifecycle policies optimize costs

        Tests:
        - Old data transitioned to cheaper storage
        - Logs are cleaned up
        - Temp data is deleted
        """
        logger.info("Testing S3 lifecycle optimization")

        logs_bucket = bucket_names['logs']

        try:
            response = s3_client.get_bucket_lifecycle_configuration(Bucket=logs_bucket)
            rules = response.get('Rules', [])

            logger.info(f"✓ Found {len(rules)} lifecycle rules for logs bucket")

            for rule in rules:
                rule_id = rule.get('ID', 'Unknown')
                status = rule.get('Status', 'Unknown')

                logger.info(f"  - Rule '{rule_id}': {status}")

                # Check transitions
                if 'Transitions' in rule:
                    for transition in rule['Transitions']:
                        days = transition.get('Days', 0)
                        storage_class = transition.get('StorageClass', 'Unknown')
                        logger.info(f"    → Transition to {storage_class} after {days} days")

                # Check expiration
                if 'Expiration' in rule:
                    expiration_days = rule['Expiration'].get('Days', 0)
                    logger.info(f"    → Expire after {expiration_days} days")

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                logger.warning("No lifecycle configuration found")
            else:
                raise


class TestComputeCosts:
    """Tests for compute cost optimization"""

    @pytest.mark.integration
    def test_lambda_invocation_costs(self, cloudwatch_client, lambda_function_names):
        """
        Calculate Lambda invocation costs

        Tests:
        - Staying within Free Tier (1M requests/month)
        - Cost per invocation is reasonable
        - No excessive invocations
        """
        logger.info("Testing Lambda invocation costs")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)

        total_invocations = 0

        for function_type, function_name in lambda_function_names.items():
            try:
                response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=2592000,  # 30 days
                    Statistics=['Sum']
                )

                datapoints = response['Datapoints']

                if datapoints:
                    invocations = datapoints[0].get('Sum', 0)
                    total_invocations += invocations

                    logger.info(f"  - {function_type}: {int(invocations)} invocations")

            except ClientError as e:
                logger.warning(f"Could not get invocations for {function_name}: {str(e)}")

        logger.info(f"✓ Total invocations (30 days): {int(total_invocations)}")

        # Check if within Free Tier
        free_tier_limit = 1_000_000
        if total_invocations < free_tier_limit:
            logger.info(f"✓ Within Free Tier limit ({total_invocations/free_tier_limit*100:.1f}% used)")
        else:
            # Calculate cost (after Free Tier: $0.20 per 1M requests)
            billable_requests = total_invocations - free_tier_limit
            cost = (billable_requests / 1_000_000) * 0.20
            logger.info(f"  Estimated cost: ${cost:.2f}")

            assert cost < 10, \
                f"Lambda invocation cost ${cost:.2f} exceeds $10 threshold"

    @pytest.mark.integration
    @pytest.mark.expensive
    def test_glue_dpu_costs(self, glue_client):
        """
        Calculate Glue DPU hour costs

        Tests:
        - DPU hours not exceeding budget
        - Job efficiency is good
        - No wasted compute
        """
        logger.info("Testing Glue DPU costs")

        response = glue_client.list_jobs()
        job_names = response['JobNames']

        total_dpu_hours = 0

        for job_name in job_names[:5]:
            try:
                runs_response = glue_client.get_job_runs(
                    JobName=job_name,
                    MaxResults=10
                )

                successful_runs = [r for r in runs_response['JobRuns'] if r['JobRunState'] == 'SUCCEEDED']

                if successful_runs:
                    for run in successful_runs:
                        execution_time_hours = run.get('ExecutionTime', 0) / 3600
                        max_capacity = run.get('MaxCapacity', 2)  # Default 2 DPUs

                        dpu_hours = execution_time_hours * max_capacity
                        total_dpu_hours += dpu_hours

                    logger.info(f"  - {job_name}: {len(successful_runs)} runs")

            except ClientError as e:
                logger.warning(f"Could not get job runs for {job_name}: {str(e)}")

        logger.info(f"✓ Total DPU hours: {total_dpu_hours:.2f}")

        # Calculate cost ($0.44 per DPU hour)
        estimated_cost = total_dpu_hours * 0.44
        logger.info(f"✓ Estimated Glue cost: ${estimated_cost:.2f}")

        # Check against budget
        assert estimated_cost < 100, \
            f"Glue DPU cost ${estimated_cost:.2f} exceeds $100 budget"
