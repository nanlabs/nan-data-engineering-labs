# Exercise 03: Data Masking & Anonymization

## Overview
Implement PII detection, data masking, tokenization, and anonymization techniques using Amazon Macie, Comprehend, Presidio, and custom algorithms including k-anonymity and differential privacy.

**Difficulty**: ⭐⭐⭐⭐ Expert
**Duration**: ~3 hours
**Prerequisites**: Python, data processing, privacy concepts

## Learning Objectives

- Detect PII automatically with Amazon Macie
- Use Amazon Comprehend for entity recognition
- Implement static and dynamic data masking
- Build tokenization service for reversible masking
- Apply k-anonymity for dataset anonymization
- Implement differential privacy mechanisms
- Create data masking pipelines with AWS Glue

## Key Concepts

- **PII (Personally Identifiable Information)**: Data that can identify individuals
- **Static Masking**: Permanent replacement of sensitive data
- **Dynamic Masking**: Runtime masking based on user permissions
- **Tokenization**: Replace sensitive data with reversible tokens
- **K-Anonymity**: Each record indistinguishable from k-1 others
- **Differential Privacy**: Add statistical noise to protect privacy
- **Golden Record**: Original unmasked data stored securely

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              DATA MASKING ARCHITECTURE                       │
│                                                              │
│   ┌──────────────┐                                          │
│   │  Raw Data    │                                          │
│   │   (S3)       │                                          │
│   └──────┬───────┘                                          │
│          │                                                   │
│          ▼                                                   │
│   ┌──────────────────────────────────────┐                 │
│   │        PII DETECTION                  │                 │
│   │  ┌──────────┐  ┌────────────────┐   │                 │
│   │  │  Macie   │  │   Comprehend   │   │                 │
│   │  │ S3 Scan  │  │  NER Detection │   │                 │
│   │  └────┬─────┘  └────────┬───────┘   │                 │
│   │       │                 │           │                 │
│   │       └────────┬────────┘           │                 │
│   └────────────────┼────────────────────┘                 │
│                    │                                        │
│                    ▼                                        │
│   ┌────────────────────────────────────────┐              │
│   │         MASKING STRATEGIES              │              │
│   │                                        │              │
│   │  ┌────────────┐   ┌───────────────┐   │              │
│   │  │   Static   │   │    Dynamic    │   │              │
│   │  │  Masking   │   │   Masking     │   │              │
│   │  │ (Glue ETL) │   │   (Lambda)    │   │              │
│   │  └─────┬──────┘   └───────┬───────┘   │              │
│   │        │                  │           │              │
│   │        │   ┌──────────────┴──────┐   │              │
│   │        │   │  Tokenization       │   │              │
│   │        │   │  (DynamoDB          │   │              │
│   │        │   │   Token Store)      │   │              │
│   │        │   └──────────────┬──────┘   │              │
│   │        │                  │           │              │
│   └────────┼──────────────────┼───────────┘              │
│            │                  │                           │
│            ▼                  ▼                           │
│   ┌────────────────┐  ┌──────────────────┐              │
│   │ Masked         │  │  Dynamically     │              │
│   │ Dataset (S3)   │  │  Masked API      │              │
│   │                │  │  Response        │              │
│   └────────────────┘  └──────────────────┘              │
│                                                            │
│   ┌────────────────────────────────────┐                 │
│   │       ANONYMIZATION                 │                 │
│   │                                    │                 │
│   │  ┌──────────────┐  ┌─────────────┐│                 │
│   │  │ K-Anonymity  │  │ Differential││                 │
│   │  │ Generalize   │  │   Privacy   ││                 │
│   │  │  Suppress    │  │  Add Noise  ││                 │
│   │  └──────────────┘  └─────────────┘│                 │
│   └────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Automated PII Detection with Macie (30 minutes)

**File**: `setup_macie_scan.py`

```python
#!/usr/bin/env python3
"""Configure Amazon Macie for PII detection"""

import boto3
import json
import time

macie = boto3.client('macie2')
s3 = boto3.client('s3')


def enable_macie():
    """Enable Amazon Macie"""

    print("\n1. Enabling Amazon Macie")
    print("="*60)

    try:
        response = macie.enable_macie(
            findingPublishingFrequency='FIFTEEN_MINUTES',
            status='ENABLED'
        )
        print("✓ Macie enabled")

    except macie.exceptions.ConflictException:
        print("  Macie already enabled")

    # Get Macie status
    status = macie.get_macie_session()
    print(f"  Status: {status['status']}")
    print(f"  Service Role: {status['serviceRole']}")
    print(f"  Finding Frequency: {status['findingPublishingFrequency']}")


def create_classification_job(bucket_name):
    """Create classification job for S3 bucket"""

    print(f"\n2. Creating Classification Job")
    print("="*60)

    job_name = f"pii-scan-{bucket_name}-{int(time.time())}"

    try:
        response = macie.create_classification_job(
            jobType='ONE_TIME',
            name=job_name,
            description=f'PII detection for {bucket_name}',
            s3JobDefinition={
                'bucketDefinitions': [
                    {
                        'accountId': boto3.client('sts').get_caller_identity()['Account'],
                        'buckets': [bucket_name]
                    }
                ]
            },
            managedDataIdentifierSelector='ALL',
            customDataIdentifierIds=[],
            tags={'Environment': 'production', 'Purpose': 'pii-detection'}
        )

        job_id = response['jobId']
        job_arn = response['jobArn']

        print(f"✓ Classification job created")
        print(f"  Job ID: {job_id}")
        print(f"  Job ARN: {job_arn}")
        print(f"  Status: RUNNING")

        return job_id

    except Exception as e:
        print(f"✗ Error creating job: {e}")
        return None


def create_custom_data_identifier():
    """Create custom data identifier for specific patterns"""

    print(f"\n3. Creating Custom Data Identifier")
    print("="*60)

    # Example: Custom pattern for employee IDs
    try:
        response = macie.create_custom_data_identifier(
            name='EmployeeID',
            description='Detects employee IDs in format EMP-XXXXX',
            regex='EMP-[0-9]{5}',
            keywords=['employee', 'staff', 'worker', 'emp'],
            maximumMatchDistance=50,
            tags={'Type': 'custom-identifier'}
        )

        identifier_id = response['customDataIdentifierId']
        print(f"✓ Custom identifier created")
        print(f"  ID: {identifier_id}")
        print(f"  Pattern: EMP-[0-9]{{5}}")

        return identifier_id

    except macie.exceptions.ConflictException:
        print("  Custom identifier already exists")
        return None


def get_findings(job_id):
    """Retrieve Macie findings"""

    print(f"\n4. Retrieving Findings")
    print("="*60)

    try:
        # List findings
        response = macie.list_findings(
            findingCriteria={
                'criterion': {
                    'classificationDetails.jobId': {
                        'eq': [job_id]
                    }
                }
            },
            maxResults=50
        )

        finding_ids = response.get('findingIds', [])

        if not finding_ids:
            print("  No findings yet (job may still be running)")
            return []

        # Get finding details
        findings_response = macie.get_findings(findingIds=finding_ids)
        findings = findings_response.get('findings', [])

        print(f"✓ Found {len(findings)} PII findings")

        for i, finding in enumerate(findings, 1):
            print(f"\nFinding {i}:")
            print(f"  Severity: {finding.get('severity', {}).get('description', 'UNKNOWN')}")
            print(f"  Type: {finding.get('type', 'UNKNOWN')}")

            # S3 object details
            s3_obj = finding.get('resourcesAffected', {}).get('s3Object', {})
            print(f"  Bucket: {s3_obj.get('bucketName', 'N/A')}")
            print(f"  Key: {s3_obj.get('key', 'N/A')}")

            # PII types found
            sensitive_data = finding.get('classificationDetails', {}).get('result', {}).get('sensitiveData', [])
            for data in sensitive_data:
                category = data.get('category', 'UNKNOWN')
                detections = data.get('detections', [])
                print(f"  Category: {category}")
                for detection in detections:
                    pii_type = detection.get('type', 'UNKNOWN')
                    count = detection.get('count', 0)
                    print(f"    - {pii_type}: {count} occurrences")

        return findings

    except Exception as e:
        print(f"✗ Error retrieving findings: {e}")
        return []


def generate_pii_test_data(bucket_name):
    """Generate test data with PII"""

    print(f"\nGenerating test data with PII...")

    test_data = {
        "records": [
            {
                "id": "EMP-10001",
                "name": "John Smith",
                "email": "john.smith@company.com",
                "ssn": "123-45-6789",
                "phone": "+1-555-123-4567",
                "credit_card": "4532-1234-5678-9010",
                "address": "123 Main St, New York, NY 10001",
                "ip_address": "192.168.1.100",
                "birthdate": "1985-03-15"
            },
            {
                "id": "EMP-10002",
                "name": "Jane Doe",
                "email": "jane.doe@company.com",
                "ssn": "987-65-4321",
                "phone": "+1-555-987-6543",
                "credit_card": "5425-2334-3010-9876",
                "address": "456 Oak Ave, Los Angeles, CA 90001",
                "ip_address": "10.0.0.50",
                "birthdate": "1990-07-22"
            }
        ]
    }

    # Upload to S3
    s3.put_object(
        Bucket=bucket_name,
        Key='raw/pii-test-data.json',
        Body=json.dumps(test_data, indent=2),
        ContentType='application/json'
    )

    print(f"✓ Uploaded test data to s3://{bucket_name}/raw/pii-test-data.json")
    print(f"  Contains: SSN, Credit Cards, Emails, Phone Numbers")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', required=True, help='S3 bucket to scan')
    args = parser.parse_args()

    print("="*60)
    print("AMAZON MACIE PII DETECTION")
    print("="*60)

    # Generate test data
    generate_pii_test_data(args.bucket)

    # Enable Macie
    enable_macie()

    # Create custom identifier
    custom_id = create_custom_data_identifier()

    # Create classification job
    job_id = create_classification_job(args.bucket)

    if job_id:
        print(f"\n⏳ Job running. Wait 5-10 minutes, then run:")
        print(f"   python get_macie_findings.py --job-id {job_id}")

    print("\n" + "="*60)
    print("✓ MACIE SCAN INITIATED")
    print("="*60)
```

## Task 2: PII Detection with Presidio (45 minutes)

**File**: `presidio_pii_detection.py`

```python
#!/usr/bin/env python3
"""PII detection using Microsoft Presidio"""

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import json


class PIIDetector:
    """PII detection and anonymization"""

    def __init__(self):
        # Initialize analyzer with all recognizers
        self.analyzer = AnalyzerEngine()

        # Initialize anonymizer
        self.anonymizer = AnonymizerEngine()

        # Supported PII types
        self.pii_types = [
            "CREDIT_CARD", "CRYPTO", "DATE_TIME", "EMAIL_ADDRESS",
            "IBAN_CODE", "IP_ADDRESS", "NRP", "LOCATION", "PERSON",
            "PHONE_NUMBER", "MEDICAL_LICENSE", "URL", "US_BANK_NUMBER",
            "US_DRIVER_LICENSE", "US_ITIN", "US_PASSPORT", "US_SSN"
        ]

    def detect_pii(self, text, language='en'):
        """Detect PII in text"""

        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=self.pii_types
        )

        return results

    def anonymize_text(self, text, analysis_results):
        """Anonymize detected PII"""

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results
        )

        return anonymized_result.text

    def mask_with_type(self, text, analysis_results):
        """Replace PII with entity type"""

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "<{entity_type}>"})
            }
        )

        return anonymized_result.text

    def mask_with_hash(self, text, analysis_results):
        """Replace PII with hash"""

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators={
                "DEFAULT": OperatorConfig("hash", {})
            }
        )

        return anonymized_result.text

    def redact(self, text, analysis_results):
        """Completely redact PII"""

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analysis_results,
            operators={
                "DEFAULT": OperatorConfig("redact", {})
            }
        )

        return anonymized_result.text

    def analyze_structured_data(self, data_dict):
        """Analyze dictionary/JSON for PII"""

        pii_found = {}

        def traverse(obj, path=""):
            """Recursively traverse dictionary"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    traverse(value, new_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    traverse(item, new_path)

            elif isinstance(obj, str):
                results = self.detect_pii(obj)
                if results:
                    pii_found[path] = [
                        {
                            'type': r.entity_type,
                            'score': r.score,
                            'start': r.start,
                            'end': r.end,
                            'text': obj[r.start:r.end]
                        }
                        for r in results
                    ]

        traverse(data_dict)
        return pii_found


def demonstrate_pii_detection():
    """Demonstrate PII detection capabilities"""

    detector = PIIDetector()

    # Test data
    test_text = """
    Employee Record:
    Name: John Smith
    SSN: 123-45-6789
    Email: john.smith@company.com
    Phone: +1-555-123-4567
    Credit Card: 4532-1234-5678-9010
    IP Address: 192.168.1.100
    Address: 123 Main St, New York, NY 10001
    """

    print("="*60)
    print("PII DETECTION WITH PRESIDIO")
    print("="*60)

    # Detect PII
    print("\n1. Detecting PII...")
    results = detector.detect_pii(test_text)

    if results:
        print(f"✓ Found {len(results)} PII entities:\n")
        for result in results:
            detected_text = test_text[result.start:result.end]
            print(f"  Type: {result.entity_type}")
            print(f"  Text: {detected_text}")
            print(f"  Score: {result.score:.2f}")
            print(f"  Position: {result.start}-{result.end}\n")

    # Anonymization strategies
    print("\n2. Anonymization Strategies:")
    print("="*60)

    print("\n▸ Strategy: Default (asterisks)")
    print(detector.anonymize_text(test_text, results))

    print("\n▸ Strategy: Replace with type")
    print(detector.mask_with_type(test_text, results))

    print("\n▸ Strategy: Hash")
    print(detector.mask_with_hash(test_text, results))

    print("\n▸ Strategy: Redact")
    print(detector.redact(test_text, results))

    # Structured data
    print("\n3. Analyzing Structured Data:")
    print("="*60)

    employee_data = {
        "employee": {
            "id": "EMP-10001",
            "personal": {
                "name": "John Smith",
                "ssn": "123-45-6789",
                "email": "john.smith@company.com"
            },
            "contact": {
                "phone": "+1-555-123-4567",
                "address": "123 Main St, New York, NY 10001"
            }
        }
    }

    pii_locations = detector.analyze_structured_data(employee_data)

    if pii_locations:
        print(f"✓ Found PII in {len(pii_locations)} fields:\n")
        for path, entities in pii_locations.items():
            print(f"  Field: {path}")
            for entity in entities:
                print(f"    - {entity['type']} (score: {entity['score']:.2f}): {entity['text']}")
            print()


if __name__ == '__main__':
    demonstrate_pii_detection()

    print("="*60)
    print("✓ PII DETECTION COMPLETE")
    print("="*60)
```

## Task 3: Tokenization Service (45 minutes)

**File**: `tokenization_service.py`

```python
#!/usr/bin/env python3
"""Tokenization service using DynamoDB for reversible masking"""

import boto3
import hashlib
import secrets
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')


class TokenizationService:
    """Bidirectional tokenization service"""

    def __init__(self, table_name='tokenization-store'):
        self.table_name = table_name
        self.table = self._create_table()

    def _create_table(self):
        """Create DynamoDB table for tokens"""

        try:
            table = dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'token', 'KeyType': 'HASH'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'token', 'AttributeType': 'S'},
                    {'AttributeName': 'original_hash', 'AttributeType': 'S'},
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'original_hash-index',
                        'KeySchema': [
                            {'AttributeName': 'original_hash', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                SSESpecification={'Enabled': True}
            )

            # Wait for table creation
            table.wait_until_exists()
            print(f"✓ Created tokenization table: {self.table_name}")

        except dynamodb.meta.client.exceptions.ResourceInUseException:
            table = dynamodb.Table(self.table_name)

        return table

    def generate_token(self, original_value, entity_type, ttl_days=365):
        """Generate token for sensitive value"""

        # Create deterministic hash of original value
        original_hash = hashlib.sha256(original_value.encode()).hexdigest()

        # Check if token already exists
        response = self.table.query(
            IndexName='original_hash-index',
            KeyConditionExpression='original_hash = :hash',
            ExpressionAttributeValues={':hash': original_hash}
        )

        if response['Items']:
            # Return existing token
            token = response['Items'][0]['token']
            print(f"  ↻ Reusing existing token for {entity_type}")
            return token

        # Generate new token
        token = f"TKN-{entity_type}-{secrets.token_urlsafe(16)}"

        # Calculate TTL
        ttl = int((datetime.now() + timedelta(days=ttl_days)).timestamp())

        # Store in DynamoDB
        self.table.put_item(
            Item={
                'token': token,
                'original_hash': original_hash,
                'entity_type': entity_type,
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
        )

        print(f"  ✓ Generated token for {entity_type}")
        return token

    def detokenize(self, token):
        """Retrieve original value (in production, this would be encrypted)"""

        response = self.table.get_item(Key={'token': token})

        if 'Item' not in response:
            raise ValueError(f"Token not found: {token}")

        item = response['Item']

        # In production, this would decrypt and return the original value
        # For demo, we return the hash
        return {
            'entity_type': item['entity_type'],
            'original_hash': item['original_hash'],
            'created_at': item['created_at']
        }

    def tokenize_dataset(self, records, pii_fields):
        """Tokenize PII fields in dataset"""

        tokenized_records = []
        token_mapping = {}

        for record in records:
            tokenized_record = record.copy()

            for field, entity_type in pii_fields.items():
                if field in record and record[field]:
                    original_value = str(record[field])
                    token = self.generate_token(original_value, entity_type)

                    tokenized_record[field] = token
                    token_mapping[token] = original_value

            tokenized_records.append(tokenized_record)

        return tokenized_records, token_mapping


def demonstrate_tokenization():
    """Demonstrate tokenization service"""

    service = TokenizationService()

    print("="*60)
    print("TOKENIZATION SERVICE")
    print("="*60)

    # Sample data
    employees = [
        {
            "id": "EMP-001",
            "name": "John Smith",
            "ssn": "123-45-6789",
            "email": "john.smith@company.com",
            "salary": 75000
        },
        {
            "id": "EMP-002",
            "name": "Jane Doe",
            "ssn": "987-65-4321",
            "email": "jane.doe@company.com",
            "salary": 82000
        }
    ]

    # Define PII fields
    pii_fields = {
        'name': 'PERSON',
        'ssn': 'SSN',
        'email': 'EMAIL'
    }

    print("\n1. Tokenizing Dataset:")
    print("="*60)

    tokenized, mapping = service.tokenize_dataset(employees, pii_fields)

    print("\nOriginal Data:")
    for emp in employees:
        print(f"  {emp}")

    print("\nTokenized Data:")
    for emp in tokenized:
        print(f"  {emp}")

    print("\n2. Detokenization:")
    print("="*60)

    # Test detokenization
    sample_token = tokenized[0]['name']
    print(f"\nToken: {sample_token}")

    try:
        original_info = service.detokenize(sample_token)
        print(f"Entity Type: {original_info['entity_type']}")
        print(f"Hash: {original_info['original_hash'][:16]}...")
        print(f"Created: {original_info['created_at']}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    demonstrate_tokenization()

    print("\n" + "="*60)
    print("✓ TOKENIZATION COMPLETE")
    print("="*60)
```

## Task 4: K-Anonymity Implementation (30 minutes)

**File**: `k_anonymity.py`

```python
#!/usr/bin/env python3
"""K-anonymity implementation for dataset anonymization"""

import pandas as pd
from typing import List, Dict


class KAnonymizer:
    """Implement k-anonymity through generalization and suppression"""

    def __init__(self, k=5):
        """
        Initialize k-anonymizer

        Args:
            k: Minimum group size for anonymity
        """
        self.k = k

    def generalize_age(self, age):
        """Generalize age into brackets"""
        if age < 20:
            return "0-19"
        elif age < 30:
            return "20-29"
        elif age < 40:
            return "30-39"
        elif age < 50:
            return "40-49"
        elif age < 60:
            return "50-59"
        else:
            return "60+"

    def generalize_zipcode(self, zipcode):
        """Generalize zipcode (keep first 3 digits)"""
        return str(zipcode)[:3] + "**"

    def generalize_salary(self, salary):
        """Generalize salary into brackets"""
        if salary < 50000:
            return "< $50k"
        elif salary < 75000:
            return "$50k-$75k"
        elif salary < 100000:
            return "$75k-$100k"
        else:
            return "> $100k"

    def apply_generalization(self, df, quasi_identifiers):
        """Apply generalization to quasi-identifiers"""

        df_anonymized = df.copy()

        for column, method in quasi_identifiers.items():
            if method == 'age':
                df_anonymized[column] = df[column].apply(self.generalize_age)
            elif method == 'zipcode':
                df_anonymized[column] = df[column].apply(self.generalize_zipcode)
            elif method == 'salary':
                df_anonymized[column] = df[column].apply(self.generalize_salary)

        return df_anonymized

    def suppress_identifiers(self, df, identifiers):
        """Suppress direct identifiers"""

        df_suppressed = df.copy()

        for identifier in identifiers:
            if identifier in df_suppressed.columns:
                df_suppressed = df_suppressed.drop(columns=[identifier])

        return df_suppressed

    def check_k_anonymity(self, df, quasi_identifiers):
        """Check if dataset satisfies k-anonymity"""

        # Group by quasi-identifiers
        groups = df.groupby(list(quasi_identifiers.keys())).size()

        # Find minimum group size
        min_group_size = groups.min()

        # Check violations
        violations = groups[groups < self.k]

        return {
            'satisfies_k_anonymity': min_group_size >= self.k,
            'min_group_size': min_group_size,
            'num_violations': len(violations),
            'k': self.k,
            'violations': violations.to_dict() if len(violations) > 0 else {}
        }

    def anonymize(self, df, identifiers, quasi_identifiers):
        """Complete k-anonymity process"""

        print(f"Starting k-anonymization (k={self.k})")
        print("="*60)

        # Step 1: Suppress direct identifiers
        print("\n1. Suppressing direct identifiers...")
        df_step1 = self.suppress_identifiers(df, identifiers)
        print(f"   Removed columns: {identifiers}")

        # Step 2: Generalize quasi-identifiers
        print("\n2. Generalizing quasi-identifiers...")
        df_step2 = self.apply_generalization(df_step1, quasi_identifiers)
        print(f"   Generalized columns: {list(quasi_identifiers.keys())}")

        # Step 3: Check k-anonymity
        print("\n3. Checking k-anonymity...")
        check_result = self.check_k_anonymity(df_step2, quasi_identifiers)

        print(f"   Satisfies {self.k}-anonymity: {check_result['satisfies_k_anonymity']}")
        print(f"   Min group size: {check_result['min_group_size']}")

        if check_result['num_violations'] > 0:
            print(f"   ⚠ Found {check_result['num_violations']} violations")
            print(f"   Consider:")
            print(f"     - Increasing generalization level")
            print(f"     - Lowering k value")
            print(f"     - Removing more records")
        else:
            print(f"   ✓ Dataset satisfies {self.k}-anonymity")

        return df_step2, check_result


def demonstrate_k_anonymity():
    """Demonstrate k-anonymity"""

    # Sample dataset
    data = {
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry'],
        'ssn': ['111-11-1111', '222-22-2222', '333-33-3333', '444-44-4444',
                '555-55-5555', '666-66-6666', '777-77-7777', '888-88-8888'],
        'age': [25, 27, 35, 36, 45, 47, 52, 55],
        'zipcode': ['10001', '10002', '10001', '10002', '20001', '20002', '20001', '20002'],
        'salary': [60000, 65000, 80000, 85000, 95000, 100000, 110000, 120000],
        'diagnosis': ['Flu', 'Cold', 'Diabetes', 'Hypertension', 'Flu', 'Cold', 'Diabetes', 'Hypertension']
    }

    df = pd.DataFrame(data)

    print("="*60)
    print("K-ANONYMITY DEMONSTRATION")
    print("="*60)

    print("\nOriginal Dataset:")
    print(df.to_string(index=False))

    # Define identifiers
    direct_identifiers = ['name', 'ssn']
    quasi_identifiers = {
        'age': 'age',
        'zipcode': 'zipcode',
        'salary': 'salary'
    }

    # Apply k-anonymity
    anonymizer = KAnonymizer(k=2)
    df_anonymized, check_result = anonymizer.anonymize(
        df, direct_identifiers, quasi_identifiers
    )

    print("\nAnonymized Dataset:")
    print(df_anonymized.to_string(index=False))

    # Show group sizes
    print("\nGroup Sizes:")
    groups = df_anonymized.groupby(list(quasi_identifiers.keys())).size()
    print(groups.to_string())


if __name__ == '__main__':
    demonstrate_k_anonymity()

    print("\n" + "="*60)
    print("✓ K-ANONYMITY COMPLETE")
    print("="*60)
```

## Validation Checklist

- [ ] Macie classification job completed successfully
- [ ] Custom data identifiers created
- [ ] Presidio detects all common PII types
- [ ] Tokenization service stores tokens securely
- [ ] Detokenization works correctly
- [ ] K-anonymity satisfies k≥2 constraint
- [ ] Anonymized data retains analytical value
- [ ] No PII exposed in logs

## Expected Results

**Macie Findings**:
- SSN detected (HIGH severity)
- Credit cards detected (HIGH severity)
- Email addresses detected (MEDIUM severity)
- Phone numbers detected (MEDIUM severity)

**Tokenization**:
- Reversible tokens stored in encrypted DynamoDB
- Same values get same tokens (deterministic)

**K-Anonymity**:
- Each group has at least k=2 records
- No individual uniquely identifiable

## Troubleshooting

### Problem: Macie not finding PII

```python
# Verify test data has PII
import json

with open('test-data.json') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))

# Check Macie job status
response = macie.describe_classification_job(jobId='job-id')
print(response['jobStatus'])
```

### Problem: Presidio not detecting entity

```python
# Check available recognizers
from presidio_analyzer import RecognizerRegistry

registry = RecognizerRegistry()
recognizers = registry.get_recognizers()

for rec in recognizers:
    print(f"{rec.name}: {rec.supported_entities}")
```

## Key Learnings

1. **Defense in Depth**: Use multiple PII detection methods
2. **Tokenization**: Enables analytics while protecting PII
3. **K-Anonymity**: Balance privacy with data utility
4. **Irreversibility**: Static masking cannot be undone
5. **Context Matters**: Some fields may be quasi-identifiers

## Next Steps

- **Exercise 04**: Implement audit and compliance logging
- **Advanced**: Implement l-diversity and t-closeness
- **Production**: Build real-time masking API gateway

## Resources

- [Amazon Macie](https://docs.aws.amazon.com/macie/)
- [Presidio](https://microsoft.github.io/presidio/)
- [K-Anonymity Paper](https://dataprivacylab.org/dataprivacy/projects/kanonymity/)
