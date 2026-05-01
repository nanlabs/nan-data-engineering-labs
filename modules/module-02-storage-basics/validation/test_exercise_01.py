"""
Validation tests for Exercise 01: Data Lake Design
"""

import pytest
import yaml


class TestExercise01:
    """Test Exercise 01: Medallion Data Lake Design."""

    @pytest.fixture
    def solution_template_path(self, module_root):
        """Get path to solution CloudFormation template."""
        return module_root / 'exercises' / '01-data-lake-design' / 'solution' / 'data-lake-stack.yaml'

    @pytest.fixture
    def solution_template(self, solution_template_path):
        """Load solution CloudFormation template."""
        with open(solution_template_path) as f:
            return yaml.safe_load(f)

    def test_solution_file_exists(self, solution_template_path):
        """Test that solution CloudFormation template exists."""
        assert solution_template_path.exists(), "Solution template not found"

    def test_has_required_parameters(self, solution_template):
        """Test that template has required parameters."""
        assert 'Parameters' in solution_template
        params = solution_template['Parameters']

        assert 'Environment' in params
        assert 'CompanyName' in params
        assert 'CostCenter' in params

    def test_has_all_buckets(self, solution_template):
        """Test that all required S3 buckets are defined."""
        assert 'Resources' in solution_template
        resources = solution_template['Resources']

        # Check for all 4 buckets
        assert 'BronzeBucket' in resources
        assert 'SilverBucket' in resources
        assert 'GoldBucket' in resources
        assert 'LogsBucket' in resources

    def test_buckets_have_versioning(self, solution_template):
        """Test that buckets have versioning enabled."""
        resources = solution_template['Resources']

        for bucket_name in ['BronzeBucket', 'SilverBucket', 'GoldBucket']:
            bucket = resources[bucket_name]
            assert 'Properties' in bucket
            assert 'VersioningConfiguration' in bucket['Properties']
            assert bucket['Properties']['VersioningConfiguration']['Status'] == 'Enabled'

    def test_buckets_have_encryption(self, solution_template):
        """Test that buckets have encryption configured."""
        resources = solution_template['Resources']

        for bucket_name in ['BronzeBucket', 'SilverBucket', 'GoldBucket']:
            bucket = resources[bucket_name]
            assert 'BucketEncryption' in bucket['Properties']
            rules = bucket['Properties']['BucketEncryption']['ServerSideEncryptionConfiguration']
            assert len(rules) > 0
            assert rules[0]['ServerSideEncryptionByDefault']['SSEAlgorithm'] in ['AES256', 'aws:kms']

    def test_buckets_have_lifecycle_policies(self, solution_template):
        """Test that buckets have lifecycle policies."""
        resources = solution_template['Resources']

        # Bronze bucket should have lifecycle policy
        bronze = resources['BronzeBucket']
        assert 'LifecycleConfiguration' in bronze['Properties']
        assert 'Rules' in bronze['Properties']['LifecycleConfiguration']
        assert len(bronze['Properties']['LifecycleConfiguration']['Rules']) > 0

        # Silver bucket should have lifecycle policy
        silver = resources['SilverBucket']
        assert 'LifecycleConfiguration' in silver['Properties']

    def test_buckets_have_logging(self, solution_template):
        """Test that buckets have access logging configured."""
        resources = solution_template['Resources']

        for bucket_name in ['BronzeBucket', 'SilverBucket', 'GoldBucket']:
            bucket = resources[bucket_name]
            assert 'LoggingConfiguration' in bucket['Properties']
            logging = bucket['Properties']['LoggingConfiguration']
            assert 'DestinationBucketName' in logging

    def test_buckets_block_public_access(self, solution_template):
        """Test that all buckets block public access."""
        resources = solution_template['Resources']

        for bucket_name in ['BronzeBucket', 'SilverBucket', 'GoldBucket', 'LogsBucket']:
            bucket = resources[bucket_name]
            assert 'PublicAccessBlockConfiguration' in bucket['Properties']
            public_access = bucket['Properties']['PublicAccessBlockConfiguration']

            assert public_access['BlockPublicAcls'] is True
            assert public_access['BlockPublicPolicy'] is True
            assert public_access['IgnorePublicAcls'] is True
            assert public_access['RestrictPublicBuckets'] is True

    def test_has_iam_roles(self, solution_template):
        """Test that IAM roles are defined."""
        resources = solution_template['Resources']

        assert 'DataEngineerRole' in resources
        assert 'DataScientistRole' in resources
        assert 'AnalystRole' in resources

    def test_has_bucket_policies(self, solution_template):
        """Test that bucket policies are defined."""
        resources = solution_template['Resources']

        assert 'BronzeBucketPolicy' in resources
        assert 'SilverBucketPolicy' in resources
        assert 'GoldBucketPolicy' in resources

    def test_has_outputs(self, solution_template):
        """Test that template has outputs."""
        assert 'Outputs' in solution_template
        outputs = solution_template['Outputs']

        # Check for bucket outputs
        assert 'BronzeBucketName' in outputs
        assert 'SilverBucketName' in outputs
        assert 'GoldBucketName' in outputs

        # Check for role outputs
        assert 'DataEngineerRoleArn' in outputs
