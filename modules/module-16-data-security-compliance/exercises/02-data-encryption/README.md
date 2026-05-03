# Exercise 02: Data Encryption

## Overview
Implement comprehensive encryption for data at rest and in transit using AWS KMS, envelope encryption, and TLS/SSL certificates.

**Difficulty**: ⭐⭐⭐ Advanced
**Duration**: ~3 hours
**Prerequisites**: Understanding of cryptography basics, AWS KMS knowledge

## Learning Objectives

- Create and manage AWS KMS customer-managed keys (CMKs)
- Implement S3 bucket encryption with KMS
- Enable RDS/Redshift encryption at rest
- Configure envelope encryption for large datasets
- Implement TLS/SSL for data in transit
- Set up automatic key rotation
- Monitor key usage with CloudTrail

## Key Concepts

- **KMS (Key Management Service)**: Managed encryption key service
- **CMK (Customer-Managed Key)**: Keys you create and manage
- **Envelope Encryption**: Encrypt data keys with master keys
- **Data Key**: Key used to encrypt data
- **Master Key**: Key used to encrypt data keys
- **Key Rotation**: Automatic yearly key rotation
- **Grant**: Temporary delegation of key permissions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ENCRYPTION ARCHITECTURE                   │
│                                                              │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │     KMS      │         │   CloudTrail    │              │
│  │              │────────>│   Key Usage     │              │
│  │ ┌──────────┐ │         │     Logs        │              │
│  │ │Master Key│ │         └─────────────────┘              │
│  │ │(CMK)     │ │                                          │
│  │ └────┬─────┘ │                                          │
│  └──────┼───────┘                                          │
│         │ Encrypts Data Keys                               │
│         │                                                   │
│  ┌──────▼──────────────────────────────────────┐           │
│  │          ENVELOPE ENCRYPTION                 │           │
│  │                                              │           │
│  │  ┌────────────┐      ┌──────────────┐      │           │
│  │  │ Data Key 1 │      │  Data Key 2  │      │           │
│  │  │ (DEK)      │      │  (DEK)       │      │           │
│  │  └─────┬──────┘      └──────┬───────┘      │           │
│  │        │                    │              │           │
│  └────────┼────────────────────┼──────────────┘           │
│           │                    │                           │
│           ▼                    ▼                           │
│  ┌────────────────┐   ┌───────────────┐                   │
│  │   S3 Bucket    │   │   RDS/Redshift│                   │
│  │   Encrypted    │   │   Encrypted   │                   │
│  │   Objects      │   │   Database    │                   │
│  └────────────────┘   └───────────────┘                   │
│                                                             │
│  ┌──────────────────────────────────────────┐             │
│  │         TLS/SSL IN TRANSIT               │             │
│  │                                          │             │
│  │  Client ──HTTPS──> ALB ──HTTPS──> EC2   │             │
│  │         TLS 1.2+       TLS 1.2+          │             │
│  └──────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Create KMS Customer-Managed Keys (30 minutes)

**File**: `create_kms_keys.py`

```python
#!/usr/bin/env python3
"""Create KMS customer-managed keys for encryption"""

import boto3
import json

kms = boto3.client('kms')
sts = boto3.client('sts')


def get_account_id():
    """Get current AWS account ID"""
    return sts.get_caller_identity()['Account']


def create_key_policy(admins, users):
    """Create KMS key policy"""

    account_id = get_account_id()

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Enable IAM policies",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "kms:*",
                "Resource": "*"
            },
            {
                "Sid": "Allow key administrators",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [f"arn:aws:iam::{account_id}:role/{admin}" for admin in admins]
                },
                "Action": [
                    "kms:Create*",
                    "kms:Describe*",
                    "kms:Enable*",
                    "kms:List*",
                    "kms:Put*",
                    "kms:Update*",
                    "kms:Revoke*",
                    "kms:Disable*",
                    "kms:Get*",
                    "kms:Delete*",
                    "kms:TagResource",
                    "kms:UntagResource",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion"
                ],
                "Resource": "*"
            },
            {
                "Sid": "Allow key users",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [f"arn:aws:iam::{account_id}:role/{user}" for user in users]
                },
                "Action": [
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey"
                ],
                "Resource": "*"
            },
            {
                "Sid": "Allow attachment of persistent resources",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [f"arn:aws:iam::{account_id}:role/{user}" for user in users]
                },
                "Action": [
                    "kms:CreateGrant",
                    "kms:ListGrants",
                    "kms:RevokeGrant"
                ],
                "Resource": "*",
                "Condition": {
                    "Bool": {
                        "kms:GrantIsForAWSResource": "true"
                    }
                }
            }
        ]
    }

    return json.dumps(policy, indent=2)


def create_data_lake_key():
    """Create KMS key for data lake encryption"""

    print("\n1. Creating Data Lake Encryption Key")
    print("="*60)

    admins = ['DataSecurityAdmin']
    users = ['DataEngineerRole', 'DataScientistRole']

    try:
        response = kms.create_key(
            Description='Data Lake encryption key',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            MultiRegion=False,
            Policy=create_key_policy(admins, users),
            Tags=[
                {'TagKey': 'Environment', 'TagValue': 'production'},
                {'TagKey': 'Purpose', 'TagValue': 'data-lake-encryption'},
                {'TagKey': 'ManagedBy', 'TagValue': 'security-team'}
            ]
        )

        key_id = response['KeyMetadata']['KeyId']
        key_arn = response['KeyMetadata']['Arn']

        print(f"✓ Created key")
        print(f"  Key ID: {key_id}")
        print(f"  ARN: {key_arn}")

        # Create alias
        alias_name = 'alias/data-lake-encryption'
        kms.create_alias(
            AliasName=alias_name,
            TargetKeyId=key_id
        )
        print(f"✓ Created alias: {alias_name}")

        # Enable automatic rotation
        kms.enable_key_rotation(KeyId=key_id)
        print(f"✓ Enabled automatic key rotation (yearly)")

        return key_id, key_arn

    except kms.exceptions.AlreadyExistsException:
        print("  Key alias already exists")
        aliases = kms.list_aliases()['Aliases']
        for alias in aliases:
            if alias['AliasName'] == 'alias/data-lake-encryption':
                return alias['TargetKeyId'], None


def create_database_key():
    """Create KMS key for database encryption"""

    print("\n2. Creating Database Encryption Key")
    print("="*60)

    admins = ['DataSecurityAdmin']
    users = ['RDSServiceRole', 'RedshiftServiceRole']

    try:
        response = kms.create_key(
            Description='RDS/Redshift encryption key',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            MultiRegion=False,
            Policy=create_key_policy(admins, users),
            Tags=[
                {'TagKey': 'Environment', 'TagValue': 'production'},
                {'TagKey': 'Purpose', 'TagValue': 'database-encryption'}
            ]
        )

        key_id = response['KeyMetadata']['KeyId']
        key_arn = response['KeyMetadata']['Arn']

        print(f"✓ Created key")
        print(f"  Key ID: {key_id}")
        print(f"  ARN: {key_arn}")

        # Create alias
        alias_name = 'alias/database-encryption'
        kms.create_alias(
            AliasName=alias_name,
            TargetKeyId=key_id
        )
        print(f"✓ Created alias: {alias_name}")

        # Enable rotation
        kms.enable_key_rotation(KeyId=key_id)
        print(f"✓ Enabled automatic key rotation")

        return key_id, key_arn

    except kms.exceptions.AlreadyExistsException:
        aliases = kms.list_aliases()['Aliases']
        for alias in aliases:
            if alias['AliasName'] == 'alias/database-encryption':
                return alias['TargetKeyId'], None


def create_application_key():
    """Create KMS key for application-level encryption"""

    print("\n3. Creating Application Encryption Key")
    print("="*60)

    admins = ['DataSecurityAdmin']
    users = ['ApplicationRole', 'LambdaExecutionRole']

    try:
        response = kms.create_key(
            Description='Application-level encryption key',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            MultiRegion=False,
            Policy=create_key_policy(admins, users),
            Tags=[
                {'TagKey': 'Environment', 'TagValue': 'production'},
                {'TagKey': 'Purpose', 'TagValue': 'application-encryption'}
            ]
        )

        key_id = response['KeyMetadata']['KeyId']
        key_arn = response['KeyMetadata']['Arn']

        print(f"✓ Created key")
        print(f"  Key ID: {key_id}")
        print(f"  ARN: {key_arn}")

        # Create alias
        alias_name = 'alias/application-encryption'
        kms.create_alias(
            AliasName=alias_name,
            TargetKeyId=key_id
        )
        print(f"✓ Created alias: {alias_name}")

        # Enable rotation
        kms.enable_key_rotation(KeyId=key_id)
        print(f"✓ Enabled automatic key rotation")

        return key_id, key_arn

    except kms.exceptions.AlreadyExistsException:
        aliases = kms.list_aliases()['Aliases']
        for alias in aliases:
            if alias['AliasName'] == 'alias/application-encryption':
                return alias['TargetKeyId'], None


def describe_key(key_id):
    """Get key metadata"""

    response = kms.describe_key(KeyId=key_id)
    metadata = response['KeyMetadata']

    print(f"\nKey Details:")
    print(f"  State: {metadata['KeyState']}")
    print(f"  Usage: {metadata['KeyUsage']}")
    print(f"  Manager: {metadata['KeyManager']}")
    print(f"  Created: {metadata['CreationDate']}")

    # Check rotation status
    rotation = kms.get_key_rotation_status(KeyId=key_id)
    print(f"  Rotation Enabled: {rotation['KeyRotationEnabled']}")


if __name__ == '__main__':
    print("="*60)
    print("CREATING KMS CUSTOMER-MANAGED KEYS")
    print("="*60)

    # Create keys
    data_lake_key, _ = create_data_lake_key()
    database_key, _ = create_database_key()
    application_key, _ = create_application_key()

    # Describe keys
    print("\n" + "="*60)
    print("KEY DETAILS")
    print("="*60)
    describe_key(data_lake_key)

    print("\n" + "="*60)
    print("✓ ALL KEYS CREATED")
    print("="*60)
```

## Task 2: S3 Bucket Encryption (30 minutes)

**File**: `configure_s3_encryption.py`

```python
#!/usr/bin/env python3
"""Configure S3 bucket encryption with KMS"""

import boto3
import json

s3 = boto3.client('s3')
kms = boto3.client('kms')


def get_kms_key_id(alias_name):
    """Get KMS key ID from alias"""

    aliases = kms.list_aliases()['Aliases']
    for alias in aliases:
        if alias['AliasName'] == alias_name:
            return alias['TargetKeyId']

    raise ValueError(f"Alias not found: {alias_name}")


def create_encrypted_bucket(bucket_name, kms_key_id):
    """Create S3 bucket with KMS encryption"""

    print(f"\nCreating bucket: {bucket_name}")

    # Create bucket
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✓ Created bucket: {bucket_name}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"  Bucket already exists: {bucket_name}")

    # Enable default encryption
    encryption_config = {
        'Rules': [
            {
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'aws:kms',
                    'KMSMasterKeyID': kms_key_id
                },
                'BucketKeyEnabled': True
            }
        ]
    }

    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration=encryption_config
    )
    print(f"✓ Enabled KMS encryption (SSE-KMS)")
    print(f"  Key ID: {kms_key_id}")
    print(f"  Bucket Key: Enabled (reduces API calls)")

    # Enable versioning for extra protection
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'}
    )
    print(f"✓ Enabled versioning")

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
    print(f"✓ Blocked public access")


def add_bucket_policy_encryption_enforcement(bucket_name):
    """Add bucket policy to enforce encryption"""

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyUnencryptedObjectUploads",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
                "Condition": {
                    "StringNotEquals": {
                        "s3:x-amz-server-side-encryption": "aws:kms"
                    }
                }
            },
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/*",
                    f"arn:aws:s3:::{bucket_name}"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            }
        ]
    }

    s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(policy)
    )
    print(f"✓ Applied encryption enforcement policy")


def test_encrypted_upload(bucket_name, kms_key_id):
    """Test uploading encrypted object"""

    print(f"\nTesting encrypted upload:")

    test_content = b"This is sensitive data that must be encrypted"
    test_key = "test/encrypted-file.txt"

    # Upload with KMS encryption
    s3.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_content,
        ServerSideEncryption='aws:kms',
        SSEKMSKeyId=kms_key_id
    )
    print(f"✓ Uploaded encrypted object: {test_key}")

    # Verify encryption
    response = s3.head_object(Bucket=bucket_name, Key=test_key)
    print(f"  Encryption: {response['ServerSideEncryption']}")
    print(f"  KMS Key ID: {response.get('SSEKMSKeyId', 'N/A')}")

    # Download and decrypt (automatic with proper KMS permissions)
    obj = s3.get_object(Bucket=bucket_name, Key=test_key)
    decrypted_content = obj['Body'].read()

    assert decrypted_content == test_content
    print(f"✓ Successfully decrypted object")


if __name__ == '__main__':
    print("="*60)
    print("CONFIGURING S3 BUCKET ENCRYPTION")
    print("="*60)

    # Get KMS key
    kms_key_id = get_kms_key_id('alias/data-lake-encryption')

    # Create encrypted buckets
    buckets = [
        'data-lake-raw-encrypted',
        'data-lake-processed-encrypted',
        'data-lake-curated-encrypted'
    ]

    for bucket_name in buckets:
        create_encrypted_bucket(bucket_name, kms_key_id)
        add_bucket_policy_encryption_enforcement(bucket_name)

    # Test encryption
    test_encrypted_upload(buckets[0], kms_key_id)

    print("\n" + "="*60)
    print("✓ S3 ENCRYPTION CONFIGURED")
    print("="*60)
```

## Task 3: Envelope Encryption Implementation (45 minutes)

**File**: `envelope_encryption.py`

```python
#!/usr/bin/env python3
"""Implement envelope encryption for large datasets"""

import boto3
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

kms = boto3.client('kms')


class EnvelopeEncryption:
    """Envelope encryption using AWS KMS"""

    def __init__(self, kms_key_id):
        self.kms_key_id = kms_key_id
        self.backend = default_backend()

    def encrypt_file(self, input_file, output_file):
        """Encrypt file using envelope encryption"""

        print(f"\nEncrypting: {input_file}")

        # Step 1: Generate data key from KMS
        response = kms.generate_data_key(
            KeyId=self.kms_key_id,
            KeySpec='AES_256'
        )

        # Plaintext data key (for encryption)
        plaintext_key = response['Plaintext']

        # Encrypted data key (to store with data)
        encrypted_key = response['CiphertextBlob']

        print(f"  ✓ Generated data key from KMS")
        print(f"    Plaintext key length: {len(plaintext_key)} bytes")
        print(f"    Encrypted key length: {len(encrypted_key)} bytes")

        # Step 2: Encrypt file with data key
        iv = os.urandom(16)  # Initialization vector
        cipher = Cipher(
            algorithms.AES(plaintext_key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()

        with open(input_file, 'rb') as f_in:
            plaintext = f_in.read()

        # Pad to AES block size
        padding_length = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([padding_length] * padding_length)

        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

        print(f"  ✓ Encrypted file data")
        print(f"    Original size: {len(plaintext)} bytes")
        print(f"    Encrypted size: {len(ciphertext)} bytes")

        # Step 3: Write encrypted data key + IV + ciphertext
        with open(output_file, 'wb') as f_out:
            # Write encrypted key length (4 bytes)
            f_out.write(len(encrypted_key).to_bytes(4, byteorder='big'))
            # Write encrypted key
            f_out.write(encrypted_key)
            # Write IV
            f_out.write(iv)
            # Write ciphertext
            f_out.write(ciphertext)

        print(f"  ✓ Saved to: {output_file}")

        # Zero out plaintext key from memory
        del plaintext_key

        return output_file

    def decrypt_file(self, input_file, output_file):
        """Decrypt file using envelope encryption"""

        print(f"\nDecrypting: {input_file}")

        with open(input_file, 'rb') as f_in:
            # Read encrypted key length
            key_length = int.from_bytes(f_in.read(4), byteorder='big')

            # Read encrypted data key
            encrypted_key = f_in.read(key_length)

            # Read IV
            iv = f_in.read(16)

            # Read ciphertext
            ciphertext = f_in.read()

        print(f"  Encrypted key length: {key_length} bytes")
        print(f"  IV length: {len(iv)} bytes")
        print(f"  Ciphertext length: {len(ciphertext)} bytes")

        # Step 1: Decrypt data key with KMS
        response = kms.decrypt(
            CiphertextBlob=encrypted_key
        )
        plaintext_key = response['Plaintext']

        print(f"  ✓ Decrypted data key with KMS")

        # Step 2: Decrypt file with data key
        cipher = Cipher(
            algorithms.AES(plaintext_key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()

        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        padding_length = padded_plaintext[-1]
        plaintext = padded_plaintext[:-padding_length]

        print(f"  ✓ Decrypted file data")
        print(f"    Decrypted size: {len(plaintext)} bytes")

        # Step 3: Write plaintext
        with open(output_file, 'wb') as f_out:
            f_out.write(plaintext)

        print(f"  ✓ Saved to: {output_file}")

        # Zero out plaintext key
        del plaintext_key

        return output_file


def generate_test_data(filename, size_mb=10):
    """Generate test data file"""

    print(f"\nGenerating test data: {size_mb}MB")

    with open(filename, 'wb') as f:
        # Write random data
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(size_mb):
            f.write(os.urandom(chunk_size))

    print(f"✓ Generated: {filename}")

    return filename


if __name__ == '__main__':
    print("="*60)
    print("ENVELOPE ENCRYPTION DEMONSTRATION")
    print("="*60)

    # Get KMS key
    aliases = kms.list_aliases()['Aliases']
    kms_key_id = None
    for alias in aliases:
        if alias['AliasName'] == 'alias/application-encryption':
            kms_key_id = alias['TargetKeyId']
            break

    if not kms_key_id:
        print("✗ KMS key not found. Run create_kms_keys.py first.")
        exit(1)

    # Initialize encryptor
    encryptor = EnvelopeEncryption(kms_key_id)

    # Generate test data
    plaintext_file = 'test_data.bin'
    encrypted_file = 'test_data.bin.encrypted'
    decrypted_file = 'test_data_decrypted.bin'

    generate_test_data(plaintext_file, size_mb=10)

    # Encrypt
    encryptor.encrypt_file(plaintext_file, encrypted_file)

    # Decrypt
    encryptor.decrypt_file(encrypted_file, decrypted_file)

    # Verify
    print("\nVerifying:")
    with open(plaintext_file, 'rb') as f1, open(decrypted_file, 'rb') as f2:
        assert f1.read() == f2.read()
    print("✓ Encryption/decryption successful!")

    # Cleanup
    os.remove(plaintext_file)
    os.remove(encrypted_file)
    os.remove(decrypted_file)
    print("\n✓ Cleanup complete")

    print("\n" + "="*60)
    print("✓ ENVELOPE ENCRYPTION COMPLETE")
    print("="*60)
```

## Task 4: RDS/Redshift Encryption (30 minutes)

**File**: `enable_database_encryption.sh`

```bash
#!/bin/bash

# Enable RDS encryption at rest

echo "====================================="
echo "ENABLING DATABASE ENCRYPTION"
echo "====================================="

# Get KMS key ID
KMS_KEY_ID=$(aws kms list-aliases \
    --query "Aliases[?AliasName=='alias/database-encryption'].TargetKeyId" \
    --output text)

echo "Using KMS Key: $KMS_KEY_ID"

# Create encrypted RDS instance
echo -e "\n1. Creating encrypted RDS instance..."
aws rds create-db-instance \
    --db-instance-identifier encrypted-postgres-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.7 \
    --master-username dbadmin \
    --master-user-password 'YourSecurePassword123!' \
    --allocated-storage 20 \
    --storage-type gp2 \
    --storage-encrypted \
    --kms-key-id "$KMS_KEY_ID" \
    --backup-retention-period 7 \
    --no-publicly-accessible \
    --vpc-security-group-ids sg-12345678 \
    --tags Key=Environment,Value=dev Key=Encrypted,Value=true

echo "✓ RDS instance creation initiated"

# Create encrypted Redshift cluster
echo -e "\n2. Creating encrypted Redshift cluster..."
aws redshift create-cluster \
    --cluster-identifier encrypted-redshift-cluster \
    --node-type dc2.large \
    --cluster-type single-node \
    --master-username admin \
    --master-user-password 'YourSecurePassword123!' \
    --encrypted \
    --kms-key-id "$KMS_KEY_ID" \
    --vpc-security-group-ids sg-12345678 \
    --publicly-accessible false \
    --tags Key=Environment,Value=dev Key=Encrypted,Value=true

echo "✓ Redshift cluster creation initiated"

# Wait for instances
echo -e "\n3. Waiting for resources..."
echo "   (This may take 10-15 minutes)"

echo -e "\n====================================="
echo "✓ DATABASE ENCRYPTION ENABLED"
echo "====================================="
```

## Task 5: TLS/SSL Configuration (30 minutes)

**File**: `configure_tls.py`

```python
#!/usr/bin/env python3
"""Configure TLS/SSL for data in transit"""

import boto3
import json

elbv2 = boto3.client('elbv2')
acm = boto3.client('acm')


def request_certificate(domain_name):
    """Request ACM certificate"""

    print(f"\nRequesting certificate for: {domain_name}")

    try:
        response = acm.request_certificate(
            DomainName=domain_name,
            ValidationMethod='DNS',
            SubjectAlternativeNames=[f'*.{domain_name}'],
            Tags=[
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Purpose', 'Value': 'data-api-encryption'}
            ]
        )

        cert_arn = response['CertificateArn']
        print(f"✓ Certificate requested")
        print(f"  ARN: {cert_arn}")
        print(f"  Note: Complete DNS validation to activate")

        return cert_arn

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def create_https_listener(load_balancer_arn, target_group_arn, certificate_arn):
    """Create HTTPS listener with TLS 1.2+"""

    print("\nCreating HTTPS listener...")

    try:
        response = elbv2.create_listener(
            LoadBalancerArn=load_balancer_arn,
            Protocol='HTTPS',
            Port=443,
            Certificates=[{'CertificateArn': certificate_arn}],
            SslPolicy='ELBSecurityPolicy-TLS-1-2-2017-01',  # TLS 1.2+
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': target_group_arn
                }
            ]
        )

        listener_arn = response['Listeners'][0]['ListenerArn']
        print(f"✓ Created HTTPS listener")
        print(f"  ARN: {listener_arn}")
        print(f"  Protocol: HTTPS (TLS 1.2+)")
        print(f"  Port: 443")

        return listener_arn

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def enforce_https_redirection(load_balancer_arn):
    """Redirect HTTP to HTTPS"""

    print("\nEnforcing HTTPS redirection...")

    try:
        # Create HTTP listener that redirects to HTTPS
        response = elbv2.create_listener(
            LoadBalancerArn=load_balancer_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'redirect',
                    'RedirectConfig': {
                        'Protocol': 'HTTPS',
                        'Port': '443',
                        'StatusCode': 'HTTP_301'
                    }
                }
            ]
        )

        print(f"✓ HTTP → HTTPS redirect configured")

    except Exception as e:
        print(f"✗ Error: {e}")


def test_tls_connection(endpoint):
    """Test TLS connection"""

    import ssl
    import socket

    print(f"\nTesting TLS connection to: {endpoint}")

    try:
        context = ssl.create_default_context()

        with socket.create_connection((endpoint, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
                print(f"✓ TLS connection successful")
                print(f"  Protocol: {ssock.version()}")
                print(f"  Cipher: {ssock.cipher()[0]}")

                cert = ssock.getpeercert()
                print(f"  Certificate Subject: {dict(x[0] for x in cert['subject'])}")
                print(f"  Certificate Issuer: {dict(x[0] for x in cert['issuer'])}")

    except Exception as e:
        print(f"✗ Connection failed: {e}")


if __name__ == '__main__':
    print("="*60)
    print("CONFIGURING TLS/SSL")
    print("="*60)

    # Example domain
    domain = 'data-api.example.com'

    # Request certificate
    cert_arn = request_certificate(domain)

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Complete DNS validation for ACM certificate")
    print("2. Create Application Load Balancer")
    print("3. Configure HTTPS listener with certificate")
    print("4. Test TLS connection")

    print("\n" + "="*60)
    print("✓ TLS CONFIGURATION INITIATED")
    print("="*60)
```

## Validation Checklist

- [ ] KMS customer-managed keys created (3 keys)
- [ ] S3 buckets configured with SSE-KMS
- [ ] Bucket policies enforce encryption
- [ ] Envelope encryption tested with sample file
- [ ] RDS/Redshift encryption enabled
- [ ] ACM certificate requested
- [ ] HTTPS listener configured
- [ ] HTTP→HTTPS redirection working
- [ ] Key rotation enabled
- [ ] CloudTrail logging key usage

## Expected Results

**KMS Keys**:
- Data Lake encryption key (with rotation)
- Database encryption key (with rotation)
- Application encryption key (with rotation)

**S3 Encryption**: All buckets use SSE-KMS with bucket key

**Envelope Encryption**: Successfully encrypt/decrypt 10MB file

## Troubleshooting

### Problem: Key access denied

```bash
# Check key policy
aws kms get-key-policy --key-id <KEY_ID> --policy-name default

# Add user to key policy
aws kms put-key-policy --key-id <KEY_ID> --policy-name default --policy file://policy.json
```

### Problem: S3 encryption not working

```python
# Verify bucket encryption
response = s3.get_bucket_encryption(Bucket='bucket-name')
print(response['ServerSideEncryptionConfiguration'])
```

## Key Learnings

1. **Envelope Encryption**: Efficient for large datasets, KMS only encrypts data keys
2. **Key Rotation**: Automatic yearly rotation preserves old versions for decryption
3. **Bucket Key**: Reduces KMS API calls by 99% for S3
4. **TLS 1.2+**: Modern security policy for data in transit
5. **Defense in Depth**: Multiple encryption layers (application, database, storage)

## Next Steps

- **Exercise 03**: Implement data masking and anonymization
- **Advanced**: Configure CloudHSM for HSM-backed keys
- **Production**: Implement CMK key material import

## Resources

- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [Envelope Encryption](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#enveloping)
- [S3 Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingEncryption.html)
