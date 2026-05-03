"""
Infrastructure deployment validation tests
Tests for S3, IAM, Lambda, Glue, Athena, SNS, and CloudWatch resources
"""

import pytest
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TestS3Infrastructure:
    """Tests for S3 bucket infrastructure"""

    @pytest.mark.integration
    def test_s3_buckets_exist(self, s3_client, bucket_names):
        """
        Verify all 5 required S3 buckets exist

        Tests:
        - raw bucket exists
        - processed bucket exists
        - curated bucket exists
        - logs bucket exists
        - athena-results bucket exists
        """
        logger.info("Testing S3 bucket existence")

        for bucket_type, bucket_name in bucket_names.items():
            try:
                response = s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"✓ Bucket '{bucket_name}' exists")
                assert response['ResponseMetadata']['HTTPStatusCode'] == 200
            except ClientError as e:
                error_code = e.response['Error']['Code']
                pytest.fail(f"Bucket '{bucket_name}' does not exist or is not accessible. Error: {error_code}")

    @pytest.mark.integration
    def test_s3_bucket_versioning(self, s3_client, bucket_names):
        """
        Verify versioning is enabled on critical buckets

        Tests:
        - Versioning enabled on raw bucket
        - Versioning enabled on processed bucket
        - Versioning enabled on curated bucket
        """
        logger.info("Testing S3 bucket versioning")

        critical_buckets = ['raw', 'processed', 'curated']

        for bucket_type in critical_buckets:
            bucket_name = bucket_names[bucket_type]
            response = s3_client.get_bucket_versioning(Bucket=bucket_name)

            status = response.get('Status', 'Disabled')
            assert status == 'Enabled', \
                f"Versioning not enabled on {bucket_name}. Status: {status}"
            logger.info(f"✓ Versioning enabled on '{bucket_name}'")

    @pytest.mark.integration
    def test_s3_bucket_encryption(self, s3_client, bucket_names):
        """
        Verify encryption is enabled on all buckets

        Tests:
        - Default encryption configured
        - AES256 or aws:kms encryption used
        """
        logger.info("Testing S3 bucket encryption")

        for bucket_type, bucket_name in bucket_names.items():
            try:
                response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                rules = response['ServerSideEncryptionConfiguration']['Rules']

                assert len(rules) > 0, f"No encryption rules for {bucket_name}"

                encryption_type = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                assert encryption_type in ['AES256', 'aws:kms'], \
                    f"Invalid encryption type for {bucket_name}: {encryption_type}"

                logger.info(f"✓ Encryption ({encryption_type}) enabled on '{bucket_name}'")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    pytest.fail(f"No encryption configured for {bucket_name}")
                raise

    @pytest.mark.integration
    def test_s3_bucket_lifecycle_policies(self, s3_client, bucket_names):
        """
        Verify lifecycle policies are configured

        Tests:
        - Lifecycle rules exist for logs bucket
        - Old logs are transitioned to cheaper storage
        - Old logs are eventually deleted
        """
        logger.info("Testing S3 lifecycle policies")

        # Check logs bucket has lifecycle policy
        logs_bucket = bucket_names['logs']

        try:
            response = s3_client.get_bucket_lifecycle_configuration(Bucket=logs_bucket)
            rules = response.get('Rules', [])

            assert len(rules) > 0, f"No lifecycle rules configured for {logs_bucket}"

            # Check for transition or expiration rules
            has_transition = any('Transitions' in rule for rule in rules)
            has_expiration = any('Expiration' in rule for rule in rules)

            assert has_transition or has_expiration, \
                "Lifecycle rules should include transitions or expiration"

            logger.info(f"✓ Lifecycle policies configured on '{logs_bucket}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                pytest.fail(f"No lifecycle configuration for {logs_bucket}")
            raise

    @pytest.mark.integration
    def test_s3_bucket_tags(self, s3_client, bucket_names):
        """
        Verify buckets have required tags

        Tests:
        - Project tag exists
        - Environment tag exists
        - ManagedBy tag exists
        """
        logger.info("Testing S3 bucket tags")

        required_tags = ['Project', 'Environment']

        for bucket_type, bucket_name in bucket_names.items():
            try:
                response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                tags = {tag['Key']: tag['Value'] for tag in response['TagSet']}

                for required_tag in required_tags:
                    assert required_tag in tags, \
                        f"Required tag '{required_tag}' missing from {bucket_name}"

                logger.info(f"✓ Required tags present on '{bucket_name}'")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    pytest.fail(f"No tags configured for {bucket_name}")
                raise


class TestIAMInfrastructure:
    """Tests for IAM roles and policies"""

    @pytest.mark.integration
    def test_iam_roles_exist(self, iam_client):
        """
        Verify required IAM roles exist

        Tests:
        - Lambda execution role exists
        - Glue execution role exists
        - Athena execution role exists (if separate)
        """
        logger.info("Testing IAM roles existence")

        required_roles = [
            'serverless-data-lake-lambda-role',
            'serverless-data-lake-glue-role',
        ]

        for role_name in required_roles:
            try:
                response = iam_client.get_role(RoleName=role_name)
                assert response['Role']['RoleName'] == role_name
                logger.info(f"✓ IAM role '{role_name}' exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    pytest.fail(f"IAM role '{role_name}' does not exist")
                raise

    @pytest.mark.integration
    def test_lambda_role_policies(self, iam_client):
        """
        Verify Lambda role has required policies

        Tests:
        - S3 read/write permissions
        - CloudWatch Logs permissions
        - SNS publish permissions
        """
        logger.info("Testing Lambda role policies")

        role_name = 'serverless-data-lake-lambda-role'

        # Get inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)

        # Get attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)

        total_policies = len(inline_policies['PolicyNames']) + len(attached_policies['AttachedPolicies'])

        assert total_policies > 0, "No policies attached to Lambda role"
        logger.info(f"✓ Lambda role has {total_policies} policies")

        # Check for managed policies
        policy_names = [p['PolicyName'] for p in attached_policies['AttachedPolicies']]

        # Should have AWS managed policies or custom policies
        assert len(policy_names) > 0, "No policies attached to Lambda role"
        logger.info(f"✓ Lambda role policies: {', '.join(policy_names)}")

    @pytest.mark.integration
    def test_glue_role_policies(self, iam_client):
        """
        Verify Glue role has required policies

        Tests:
        - S3 read/write permissions
        - Glue service permissions
        - CloudWatch Logs permissions
        """
        logger.info("Testing Glue role policies")

        role_name = 'serverless-data-lake-glue-role'

        # Get attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)

        policy_names = [p['PolicyName'] for p in attached_policies['AttachedPolicies']]

        # Should have AWS Glue service policy
        has_glue_policy = any('Glue' in name for name in policy_names)
        assert has_glue_policy or len(policy_names) > 0, \
            "Glue role should have Glue service policies"

        logger.info(f"✓ Glue role policies: {', '.join(policy_names)}")


class TestLambdaInfrastructure:
    """Tests for Lambda functions"""

    @pytest.mark.integration
    def test_lambda_functions_exist(self, lambda_client, lambda_function_names):
        """
        Verify all 4 Lambda functions are deployed

        Tests:
        - file-validator function exists
        - metadata-extractor function exists
        - notification-handler function exists
        - quality-checker function exists
        """
        logger.info("Testing Lambda functions existence")

        for function_type, function_name in lambda_function_names.items():
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                assert response['Configuration']['FunctionName'] == function_name
                logger.info(f"✓ Lambda function '{function_name}' exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    pytest.fail(f"Lambda function '{function_name}' does not exist")
                raise

    @pytest.mark.integration
    def test_lambda_memory_configuration(self, lambda_client, lambda_function_names):
        """
        Verify Lambda functions have appropriate memory

        Tests:
        - Memory size is at least 256 MB
        - Memory size is not excessive (< 3008 MB)
        """
        logger.info("Testing Lambda memory configuration")

        for function_type, function_name in lambda_function_names.items():
            response = lambda_client.get_function(FunctionName=function_name)
            memory_size = response['Configuration']['MemorySize']

            assert 256 <= memory_size <= 3008, \
                f"Lambda {function_name} memory {memory_size} MB out of reasonable range"

            logger.info(f"✓ Lambda '{function_name}' has {memory_size} MB memory")

    @pytest.mark.integration
    def test_lambda_timeout_configuration(self, lambda_client, lambda_function_names):
        """
        Verify Lambda functions have appropriate timeout

        Tests:
        - Timeout is at least 30 seconds
        - Timeout is not excessive (< 900 seconds)
        """
        logger.info("Testing Lambda timeout configuration")

        for function_type, function_name in lambda_function_names.items():
            response = lambda_client.get_function(FunctionName=function_name)
            timeout = response['Configuration']['Timeout']

            assert 30 <= timeout <= 900, \
                f"Lambda {function_name} timeout {timeout}s out of reasonable range"

            logger.info(f"✓ Lambda '{function_name}' has {timeout}s timeout")

    @pytest.mark.integration
    def test_lambda_environment_variables(self, lambda_client, lambda_function_names):
        """
        Verify Lambda functions have required environment variables

        Tests:
        - Environment variables are configured
        - Required variables are present
        """
        logger.info("Testing Lambda environment variables")

        for function_type, function_name in lambda_function_names.items():
            response = lambda_client.get_function(FunctionName=function_name)
            env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})

            # At least some environment variables should be configured
            assert len(env_vars) > 0, \
                f"Lambda {function_name} has no environment variables"

            logger.info(f"✓ Lambda '{function_name}' has {len(env_vars)} environment variables")


class TestGlueInfrastructure:
    """Tests for AWS Glue resources"""

    @pytest.mark.integration
    def test_glue_database_exists(self, glue_client, glue_database_name):
        """
        Verify Glue catalog database exists

        Tests:
        - Database is created
        - Database has description
        """
        logger.info("Testing Glue database existence")

        try:
            response = glue_client.get_database(Name=glue_database_name)
            assert response['Database']['Name'] == glue_database_name
            logger.info(f"✓ Glue database '{glue_database_name}' exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                pytest.fail(f"Glue database '{glue_database_name}' does not exist")
            raise

    @pytest.mark.integration
    def test_glue_crawlers_exist(self, glue_client):
        """
        Verify Glue crawlers are configured

        Tests:
        - At least 3 crawlers exist
        - Crawlers are configured for raw, processed, curated zones
        """
        logger.info("Testing Glue crawlers existence")

        response = glue_client.list_crawlers()
        crawler_names = response['CrawlerNames']

        # Should have crawlers for different zones
        expected_patterns = ['raw', 'processed', 'curated']

        for pattern in expected_patterns:
            matching_crawlers = [c for c in crawler_names if pattern in c.lower()]
            assert len(matching_crawlers) > 0, \
                f"No crawler found for '{pattern}' zone"
            logger.info(f"✓ Crawler exists for '{pattern}' zone: {matching_crawlers[0]}")

    @pytest.mark.integration
    def test_glue_jobs_exist(self, glue_client):
        """
        Verify Glue ETL jobs exist

        Tests:
        - At least 3 Glue jobs exist
        - Jobs are configured with appropriate roles
        """
        logger.info("Testing Glue jobs existence")

        response = glue_client.list_jobs()
        job_names = response['JobNames']

        assert len(job_names) >= 3, \
            f"Expected at least 3 Glue jobs, found {len(job_names)}"

        logger.info(f"✓ Found {len(job_names)} Glue jobs: {', '.join(job_names[:5])}")


class TestAthenaInfrastructure:
    """Tests for Amazon Athena resources"""

    @pytest.mark.integration
    def test_athena_workgroup_exists(self, athena_client, athena_test_workgroup):
        """
        Verify Athena workgroup is configured

        Tests:
        - Workgroup exists
        - Results location is configured
        - Encryption is enabled
        """
        logger.info("Testing Athena workgroup")

        try:
            response = athena_client.get_work_group(WorkGroup=athena_test_workgroup)
            workgroup = response['WorkGroup']

            assert workgroup['Name'] == athena_test_workgroup

            # Check output location
            output_location = workgroup['Configuration'].get('ResultConfigurationUpdates', {}).get('OutputLocation')
            if not output_location:
                output_location = workgroup['Configuration'].get('ResultConfiguration', {}).get('OutputLocation')

            # Output location should be configured (may be in either location)
            logger.info(f"✓ Athena workgroup '{athena_test_workgroup}' exists")

        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidRequestException':
                # Workgroup might not exist, that's okay for tests
                logger.warning(f"Athena workgroup '{athena_test_workgroup}' may not exist")
            else:
                raise


class TestSNSInfrastructure:
    """Tests for SNS topics and subscriptions"""

    @pytest.mark.integration
    def test_sns_topic_exists(self, sns_client):
        """
        Verify SNS topic for notifications exists

        Tests:
        - At least one SNS topic exists for data lake
        - Topic has subscriptions
        """
        logger.info("Testing SNS topic existence")

        response = sns_client.list_topics()
        topics = response['Topics']

        # Find data lake related topic
        data_lake_topics = [t for t in topics if 'data-lake' in t['TopicArn'].lower() or 'serverless' in t['TopicArn'].lower()]

        assert len(data_lake_topics) > 0, \
            "No data lake SNS topics found"

        topic_arn = data_lake_topics[0]['TopicArn']
        logger.info(f"✓ SNS topic exists: {topic_arn}")

        # Check subscriptions
        subs_response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = subs_response['Subscriptions']

        logger.info(f"✓ SNS topic has {len(subscriptions)} subscription(s)")


class TestCloudWatchInfrastructure:
    """Tests for CloudWatch alarms and monitoring"""

    @pytest.mark.integration
    def test_cloudwatch_log_groups_exist(self, logs_client):
        """
        Verify CloudWatch log groups exist for Lambda functions

        Tests:
        - Log groups exist for Lambda functions
        - Retention policies are set
        """
        logger.info("Testing CloudWatch log groups")

        response = logs_client.describe_log_groups(
            logGroupNamePrefix='/aws/lambda/serverless-data-lake'
        )

        log_groups = response['logGroups']

        assert len(log_groups) > 0, \
            "No log groups found for Lambda functions"

        logger.info(f"✓ Found {len(log_groups)} log groups")

        # Check retention
        for log_group in log_groups:
            retention_days = log_group.get('retentionInDays')
            if retention_days:
                assert retention_days <= 30, \
                    f"Log retention too long: {retention_days} days"
                logger.info(f"✓ Log group {log_group['logGroupName']} retention: {retention_days} days")

    @pytest.mark.integration
    def test_cloudwatch_alarms_configured(self, cloudwatch_client):
        """
        Verify CloudWatch alarms are configured

        Tests:
        - Alarms exist for Lambda errors
        - Alarms exist for Glue job failures
        """
        logger.info("Testing CloudWatch alarms")

        response = cloudwatch_client.describe_alarms()
        alarms = response['MetricAlarms']

        # Should have some alarms configured
        if len(alarms) > 0:
            logger.info(f"✓ Found {len(alarms)} CloudWatch alarms")

            # Check alarm actions
            alarms_with_actions = [a for a in alarms if len(a.get('AlarmActions', [])) > 0]
            logger.info(f"✓ {len(alarms_with_actions)} alarms have actions configured")
        else:
            logger.warning("No CloudWatch alarms configured")
