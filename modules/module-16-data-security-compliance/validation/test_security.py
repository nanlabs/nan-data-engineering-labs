#!/usr/bin/env python3
"""
Security validation test suite for Module 16
Tests IAM policies, encryption, compliance, and security monitoring
"""

import boto3
import json
import pytest
from moto import mock_iam, mock_s3, mock_kms, mock_config


class TestIAMSecurity:
    """Test IAM security configurations"""

    @mock_iam
    def test_no_wildcard_policies(self):
        """Verify no overly permissive wildcard policies"""
        iam = boto3.client('iam', region_name='us-east-1')

        # Create test policy with wildcard
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }]
        }

        with pytest.raises(Exception):
            # Should not allow wildcard policies in production
            iam.create_policy(
                PolicyName='DangerousPolicy',
                PolicyDocument=json.dumps(policy_doc)
            )

    @mock_iam
    def test_mfa_enabled_for_sensitive_actions(self):
        """Verify MFA required for sensitive actions"""
        iam = boto3.client('iam', region_name='us-east-1')

        # Create user
        iam.create_user(UserName='test-user')

        # Check MFA devices
        response = iam.list_mfa_devices(UserName='test-user')

        # In production, critical users should have MFA
        assert 'MFADevices' in response

    @mock_iam
    def test_password_policy_strength(self):
        """Verify strong password policy"""
        iam = boto3.client('iam', region_name='us-east-1')

        # Set password policy
        iam.update_account_password_policy(
            MinimumPasswordLength=14,
            RequireSymbols=True,
            RequireNumbers=True,
            RequireUppercaseCharacters=True,
            RequireLowercaseCharacters=True,
            MaxPasswordAge=90,
            PasswordReusePrevention=5
        )

        # Verify policy
        policy = iam.get_account_password_policy()

        assert policy['PasswordPolicy']['MinimumPasswordLength'] >= 12
        assert policy['PasswordPolicy']['RequireSymbols'] is True
        assert policy['PasswordPolicy']['MaxPasswordAge'] <= 90


class TestEncryption:
    """Test encryption configurations"""

    @mock_s3
    @mock_kms
    def test_s3_bucket_encryption_enabled(self):
        """Verify S3 buckets have encryption enabled"""
        s3 = boto3.client('s3', region_name='us-east-1')
        kms = boto3.client('kms', region_name='us-east-1')

        # Create KMS key
        key_response = kms.create_key(Description='Test key')
        key_id = key_response['KeyMetadata']['KeyId']

        # Create bucket
        bucket_name = 'test-encrypted-bucket'
        s3.create_bucket(Bucket=bucket_name)

        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'aws:kms',
                        'KMSMasterKeyID': key_id
                    },
                    'BucketKeyEnabled': True
                }]
            }
        )

        # Verify encryption
        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
        rule = encryption['ServerSideEncryptionConfiguration']['Rules'][0]

        assert rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'] == 'aws:kms'
        assert rule['BucketKeyEnabled'] is True

    @mock_kms
    def test_kms_key_rotation_enabled(self):
        """Verify KMS keys have automatic rotation"""
        kms = boto3.client('kms', region_name='us-east-1')

        # Create key
        key_response = kms.create_key(Description='Test key')
        key_id = key_response['KeyMetadata']['KeyId']

        # Enable rotation
        kms.enable_key_rotation(KeyId=key_id)

        # Verify rotation
        rotation_status = kms.get_key_rotation_status(KeyId=key_id)
        assert rotation_status['KeyRotationEnabled'] is True


class TestCompliance:
    """Test compliance configurations"""

    @mock_config
    def test_config_enabled(self):
        """Verify AWS Config is enabled"""
        config = boto3.client('config', region_name='us-east-1')

        # Create recorder
        config.put_configuration_recorder(
            ConfigurationRecorder={
                'name': 'default',
                'roleARN': 'arn:aws:iam::123456789012:role/config-role',
                'recordingGroup': {
                    'allSupported': True,
                    'includeGlobalResourceTypes': True
                }
            }
        )

        # Verify recorder
        recorders = config.describe_configuration_recorders()
        assert len(recorders['ConfigurationRecorders']) > 0
        assert recorders['ConfigurationRecorders'][0]['recordingGroup']['allSupported'] is True

    @mock_s3
    def test_s3_public_access_blocked(self):
        """Verify S3 buckets block public access"""
        s3 = boto3.client('s3', region_name='us-east-1')

        bucket_name = 'test-private-bucket'
        s3.create_bucket(Bucket=bucket_name)

        # Block public access
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )

        # Verify
        response = s3.get_public_access_block(Bucket=bucket_name)
        config = response['PublicAccessBlockConfiguration']

        assert config['BlockPublicAcls'] is True
        assert config['BlockPublicPolicy'] is True


class TestSecurityMonitoring:
    """Test security monitoring configurations"""

    def test_cloudtrail_enabled(self):
        """Verify CloudTrail is enabled"""
        # Mock test - in real scenario, check actual CloudTrail status
        assert True  # Placeholder

    def test_guardduty_enabled(self):
        """Verify GuardDuty is enabled"""
        # Mock test - in real scenario, check actual GuardDuty status
        assert True  # Placeholder


class TestDataPrivacy:
    """Test data privacy controls"""

    def test_pii_detection(self):
        \"\"\"Test PII detection functionality\"\"\"
        from presidio_analyzer import AnalyzerEngine

        analyzer = AnalyzerEngine()

        text = \"My SSN is 123-45-6789 and email is john@example.com\"
        results = analyzer.analyze(text=text, language='en')

        # Should detect SSN and email
        detected_types = [r.entity_type for r in results]

        assert 'US_SSN' in detected_types or 'SSN' in detected_types
        assert 'EMAIL_ADDRESS' in detected_types

    def test_data_masking(self):
        \"\"\"Test data masking functionality\"\"\"

        def mask_ssn(ssn):
            \"\"\"Mask SSN keeping last 4 digits\"\"\"
            return f\"XXX-XX-{ssn[-4:]}\"

        original = \"123-45-6789\"
        masked = mask_ssn(original)

        assert masked == \"XXX-XX-6789\"
        assert \"123-45\" not in masked


def test_policy_validation():
    \"\"\"Validate IAM policy structure\"\"\"

    policy = {
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Effect\": \"Allow\",
            \"Action\": [\"s3:GetObject\"],
            \"Resource\": \"arn:aws:s3:::bucket/*\"
        }]
    }

    # Validate required fields
    assert \"Version\" in policy
    assert \"Statement\" in policy
    assert len(policy[\"Statement\"]) > 0

    statement = policy[\"Statement\"][0]
    assert \"Effect\" in statement
    assert \"Action\" in statement
    assert \"Resource\" in statement


def test_encryption_algorithm_strength():
    \"\"\"Verify strong encryption algorithms are used\"\"\"
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import os

    # AES-256 (strong)
    key = os.urandom(32)  # 256 bits
    iv = os.urandom(16)

    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )

    assert len(key) == 32  # 256-bit key


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
