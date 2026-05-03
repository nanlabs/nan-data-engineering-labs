"""
PII Masking Job
Detects and masks Personally Identifiable Information (PII).
Uses regex patterns, hashing, tokenization, and Lake Formation tags.
Audits PII access and ensures compliance.

Features: PII detection (SSN, email, phone, credit card),
SHA-256 hashing, tokenization, Lake Formation integration, audit logging.
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import hashlib
import json
import boto3

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, udf, lit,
    current_timestamp, md5, sha2
)
from pyspark.sql.types import StringType

from common.spark_utils import (
    create_spark_session, write_to_delta,
    send_notification, write_metadata_to_dynamodb,
    error_handler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PIIPatterns:
    """Regex patterns for PII detection."""

    # US Social Security Number (XXX-XX-XXXX)
    SSN = r'\b\d{3}-\d{2}-\d{4}\b'

    # Email address
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # US Phone numbers (various formats)
    PHONE = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b'

    # Credit card numbers (13-19 digits)
    CREDIT_CARD = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'

    # IP Address
    IP_ADDRESS = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

    # US ZIP Code
    ZIP_CODE = r'\b\d{5}(?:-\d{4})?\b'

    # Driver's License (varies by state, general pattern)
    DRIVERS_LICENSE = r'\b[A-Z]{1,2}\d{5,8}\b'

    # Passport Number (general pattern)
    PASSPORT = r'\b[A-Z]{1,2}\d{6,9}\b'

    # Full Name Pattern (simplified)
    FULL_NAME = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'


class PIIDetector:
    """Detects PII in DataFrames."""

    def __init__(self):
        self.patterns = PIIPatterns()
        self.detected_pii = {}

    def detect_ssn(self, text: str) -> bool:
        """Detect if text contains SSN."""
        if text is None:
            return False
        return bool(re.search(self.patterns.SSN, str(text)))

    def detect_email(self, text: str) -> bool:
        """Detect if text contains email."""
        if text is None:
            return False
        return bool(re.search(self.patterns.EMAIL, str(text)))

    def detect_phone(self, text: str) -> bool:
        """Detect if text contains phone number."""
        if text is None:
            return False
        return bool(re.search(self.patterns.PHONE, str(text)))

    def detect_credit_card(self, text: str) -> bool:
        """Detect if text contains credit card number."""
        if text is None:
            return False
        # Additional Luhn algorithm check for credit cards
        match = re.search(self.patterns.CREDIT_CARD, str(text))
        if match:
            # Remove non-digit characters
            digits = re.sub(r'\D', '', match.group())
            return self._luhn_check(digits)
        return False

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Validate credit card using Luhn algorithm."""
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))

        return checksum % 10 == 0

    def scan_dataframe(
        self,
        df: DataFrame,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, int]]:
        """
        Scan DataFrame for PII in specified columns.

        Args:
            df: DataFrame to scan
            columns: Columns to scan (None = all string columns)

        Returns:
            Dictionary with PII detection results
        """
        logger.info("Scanning DataFrame for PII")

        # Get string columns
        if columns is None:
            columns = [
                field.name for field in df.schema.fields
                if isinstance(field.dataType, StringType)
            ]

        results = {}

        # Sample data for detection (don't scan all rows for performance)
        sample_size = min(1000, df.count())
        df_sample = df.sample(fraction=sample_size/df.count()).limit(sample_size)

        for column in columns:
            logger.info(f"Scanning column: {column}")

            column_results = {
                'ssn': 0,
                'email': 0,
                'phone': 0,
                'credit_card': 0
            }

            # Collect sample values
            values = [row[column] for row in df_sample.select(column).collect() if row[column]]

            for value in values:
                if self.detect_ssn(value):
                    column_results['ssn'] += 1
                if self.detect_email(value):
                    column_results['email'] += 1
                if self.detect_phone(value):
                    column_results['phone'] += 1
                if self.detect_credit_card(value):
                    column_results['credit_card'] += 1

            # If any PII detected, add to results
            if any(count > 0 for count in column_results.values()):
                results[column] = column_results
                logger.warning(f"PII detected in column {column}: {column_results}")

        self.detected_pii = results
        return results


class PIIMasker:
    """Masks PII data using various strategies."""

    @staticmethod
    def hash_value(value: str, algorithm: str = 'sha256', salt: str = '') -> str:
        """
        Hash a value using specified algorithm.

        Args:
            value: Value to hash
            algorithm: Hash algorithm (md5, sha256)
            salt: Optional salt

        Returns:
            Hashed value
        """
        if value is None:
            return None

        salted_value = f"{salt}{value}".encode('utf-8')

        if algorithm == 'md5':
            return hashlib.md5(salted_value).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(salted_value).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    @staticmethod
    def mask_partial(value: str, visible_start: int = 0, visible_end: int = 4, mask_char: str = '*') -> str:
        """
        Partially mask a value, showing only specified characters.

        Args:
            value: Value to mask
            visible_start: Number of characters to show at start
            visible_end: Number of characters to show at end
            mask_char: Character to use for masking

        Returns:
            Masked value
        """
        if value is None or len(value) <= (visible_start + visible_end):
            return value

        start = value[:visible_start] if visible_start > 0 else ''
        end = value[-visible_end:] if visible_end > 0 else ''
        middle = mask_char * (len(value) - visible_start - visible_end)

        return f"{start}{middle}{end}"

    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email address (show first 3 chars of username and domain).

        Args:
            email: Email address to mask

        Returns:
            Masked email
        """
        if email is None or '@' not in email:
            return email

        username, domain = email.split('@')

        masked_username = PIIMasker.mask_partial(username, visible_start=3, visible_end=0)
        masked_domain = PIIMasker.mask_partial(domain, visible_start=3, visible_end=3)

        return f"{masked_username}@{masked_domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number (show only last 4 digits)."""
        if phone is None:
            return None

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        if len(digits) >= 4:
            return f"***-***-{digits[-4:]}"
        return phone

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN (show only last 4 digits)."""
        if ssn is None:
            return None

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', ssn)

        if len(digits) == 9:
            return f"***-**-{digits[-4:]}"
        return ssn

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card (show only last 4 digits)."""
        if card is None:
            return None

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', card)

        if len(digits) >= 4:
            return f"****-****-****-{digits[-4:]}"
        return card

    def apply_masking_to_dataframe(
        self,
        df: DataFrame,
        masking_rules: Dict[str, Dict[str, Any]]
    ) -> DataFrame:
        """
        Apply masking rules to DataFrame.

        Args:
            df: DataFrame to mask
            masking_rules: Dict of {column: {strategy: ..., params: ...}}

        Returns:
            DataFrame with masked columns
        """
        logger.info("Applying masking rules to DataFrame")

        masked_df = df

        for column, rule in masking_rules.items():
            if column not in df.columns:
                logger.warning(f"Column {column} not found in DataFrame")
                continue

            strategy = rule.get('strategy', 'hash')
            params = rule.get('params', {})

            logger.info(f"Masking column {column} with strategy: {strategy}")

            if strategy == 'hash':
                algorithm = params.get('algorithm', 'sha256')
                salt = params.get('salt', '')

                # Use PySpark's built-in hash functions for better performance
                if algorithm == 'sha256':
                    masked_df = masked_df.withColumn(
                        column,
                        sha2(col(column), 256)
                    )
                elif algorithm == 'md5':
                    masked_df = masked_df.withColumn(
                        column,
                        md5(col(column))
                    )

            elif strategy == 'partial':
                visible_start = params.get('visible_start', 0)
                visible_end = params.get('visible_end', 4)

                # Create UDF for partial masking
                mask_partial_udf = udf(
                    lambda x: self.mask_partial(x, visible_start, visible_end),
                    StringType()
                )

                masked_df = masked_df.withColumn(
                    column,
                    mask_partial_udf(col(column))
                )

            elif strategy == 'email':
                mask_email_udf = udf(self.mask_email, StringType())
                masked_df = masked_df.withColumn(column, mask_email_udf(col(column)))

            elif strategy == 'phone':
                mask_phone_udf = udf(self.mask_phone, StringType())
                masked_df = masked_df.withColumn(column, mask_phone_udf(col(column)))

            elif strategy == 'ssn':
                mask_ssn_udf = udf(self.mask_ssn, StringType())
                masked_df = masked_df.withColumn(column, mask_ssn_udf(col(column)))

            elif strategy == 'credit_card':
                mask_cc_udf = udf(self.mask_credit_card, StringType())
                masked_df = masked_df.withColumn(column, mask_cc_udf(col(column)))

            elif strategy == 'redact':
                # Completely redact the value
                masked_df = masked_df.withColumn(column, lit('[REDACTED]'))

            elif strategy == 'null':
                # Replace with NULL
                masked_df = masked_df.withColumn(column, lit(None).cast(StringType()))

        # Add masking metadata
        masked_df = masked_df.withColumn("_pii_masked", lit(True))
        masked_df = masked_df.withColumn("_pii_masked_timestamp", current_timestamp())

        return masked_df


class TokenizationService:
    """Tokenizes PII for reversible masking."""

    def __init__(self, token_table: str):
        self.token_table = token_table
        self.dynamodb = boto3.resource('dynamodb')

    def tokenize_value(self, value: str, field_name: str) -> str:
        """
        Tokenize a value and store mapping in DynamoDB.

        Args:
            value: Value to tokenize
            field_name: Field name

        Returns:
            Token
        """
        import uuid

        if value is None:
            return None

        # Generate token
        token = str(uuid.uuid4())

        # Store mapping in DynamoDB
        table = self.dynamodb.Table(self.token_table)

        # Hash the original value for storage
        value_hash = hashlib.sha256(value.encode()).hexdigest()

        table.put_item(
            Item={
                'token': token,
                'value_hash': value_hash,
                'field_name': field_name,
                'created_timestamp': datetime.now().isoformat(),
                'ttl': int((datetime.now().timestamp() + 90*24*3600))  # 90 days TTL
            }
        )

        return token

    def detokenize_value(self, token: str) -> Optional[str]:
        """
        Retrieve original value from token.

        Args:
            token: Token to detokenize

        Returns:
            Original value hash (not the actual value for security)
        """
        table = self.dynamodb.Table(self.token_table)

        response = table.get_item(Key={'token': token})

        if 'Item' in response:
            return response['Item']['value_hash']

        return None


class PIIAuditor:
    """Audits PII access and masking operations."""

    def __init__(self, audit_table: str):
        self.audit_table = audit_table

    def log_pii_access(
        self,
        spark: SparkSession,
        table_name: str,
        columns_accessed: List[str],
        user: str,
        operation: str
    ) -> None:
        """
        Log PII access to audit table.

        Args:
            spark: SparkSession
            table_name: Table accessed
            columns_accessed: PII columns accessed
            user: User who accessed
            operation: Operation performed
        """
        logger.info(f"Logging PII access: {operation} on {table_name} by {user}")

        audit_record = spark.createDataFrame([{
            'table_name': table_name,
            'columns_accessed': ','.join(columns_accessed),
            'user': user,
            'operation': operation,
            'access_timestamp': datetime.now().isoformat(),
            'ip_address': 'N/A'  # Could be enhanced to capture actual IP
        }])

        # Write to audit table
        audit_record.write.mode("append").saveAsTable(self.audit_table)

        logger.info("PII access logged to audit table")

    def log_masking_operation(
        self,
        spark: SparkSession,
        table_name: str,
        masking_rules: Dict[str, Any],
        records_masked: int
    ) -> None:
        """
        Log PII masking operation.

        Args:
            spark: SparkSession
            table_name: Table masked
            masking_rules: Masking rules applied
            records_masked: Number of records masked
        """
        logger.info(f"Logging masking operation for {table_name}")

        audit_record = spark.createDataFrame([{
            'table_name': table_name,
            'masking_rules': str(masking_rules),
            'records_masked': records_masked,
            'operation': 'PII_MASKING',
            'timestamp': datetime.now().isoformat()
        }])

        audit_record.write.mode("append").saveAsTable(self.audit_table)


class LakeFormationPIIManager:
    """Manages PII using AWS Lake Formation tags."""

    def __init__(self):
        self.lf_client = boto3.client('lakeformation')
        self.glue_client = boto3.client('glue')

    def tag_pii_columns(
        self,
        database: str,
        table: str,
        pii_columns: List[str]
    ) -> None:
        """
        Tag PII columns in Lake Formation.

        Args:
            database: Glue database name
            table: Glue table name
            pii_columns: List of PII column names
        """
        logger.info(f"Tagging PII columns in Lake Formation: {database}.{table}")

        for column in pii_columns:
            try:
                # Add LF-Tag to column
                self.lf_client.add_lf_tags_to_resource(
                    Resource={
                        'TableWithColumns': {
                            'DatabaseName': database,
                            'Name': table,
                            'ColumnNames': [column]
                        }
                    },
                    LFTags=[
                        {
                            'TagKey': 'pii',
                            'TagValues': ['true']
                        },
                        {
                            'TagKey': 'sensitivity',
                            'TagValues': ['high']
                        }
                    ]
                )

                logger.info(f"Tagged column: {column}")

            except Exception as e:
                logger.error(f"Failed to tag column {column}: {str(e)}")


@error_handler(notify_on_error=True)
def main():
    """Main PII masking job."""

    # Parse arguments
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'source_table_path',
        'target_table_path',
        'database',
        'table_name',
        'masking_config',
        'audit_table',
        'metadata_table',
        'sns_topic_arn'
    ])

    job_name = args['JOB_NAME']
    source_table_path = args['source_table_path']
    target_table_path = args['target_table_path']
    database = args['database']
    table_name = args['table_name']
    masking_config = json.loads(args['masking_config'])
    audit_table = args['audit_table']
    metadata_table = args['metadata_table']
    sns_topic_arn = args['sns_topic_arn']

    logger.info(f"Starting PII masking job: {job_name}")
    logger.info(f"Source: {source_table_path}")
    logger.info(f"Target: {target_table_path}")

    # Create Spark session
    spark = create_spark_session(app_name=job_name)

    try:
        # Read source data
        df = spark.read.format("delta").load(source_table_path)
        logger.info(f"Read {df.count():,} records from source")

        # Initialize components
        detector = PIIDetector()
        masker = PIIMasker()
        auditor = PIIAuditor(audit_table)
        lf_manager = LakeFormationPIIManager()

        # Detect PII if not specified in config
        if 'auto_detect' in masking_config and masking_config['auto_detect']:
            logger.info("Auto-detecting PII in DataFrame")
            pii_detection = detector.scan_dataframe(df)
            logger.info(f"PII detection results: {pii_detection}")
        else:
            pii_detection = {}

        # Apply masking rules
        masking_rules = masking_config.get('rules', {})

        if masking_rules:
            df_masked = masker.apply_masking_to_dataframe(df, masking_rules)

            # Write masked data to target
            write_to_delta(
                df_masked,
                target_table_path,
                mode="overwrite",
                optimize_write=True
            )

            logger.info(f"Masked data written to {target_table_path}")

            # Log masking operation
            auditor.log_masking_operation(
                spark,
                table_name,
                masking_rules,
                df.count()
            )

            # Tag PII columns in Lake Formation
            pii_columns = list(masking_rules.keys())
            lf_manager.tag_pii_columns(database, table_name, pii_columns)
        else:
            logger.warning("No masking rules specified")

        # Write metadata
        job_metadata = {
            'job_id': f"{job_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'job_name': job_name,
            'table_name': f"{database}.{table_name}",
            'records_processed': df.count(),
            'pii_columns': list(masking_rules.keys()),
            'pii_detection': str(pii_detection),
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }

        write_metadata_to_dynamodb(metadata_table, job_metadata)

        # Send notification
        send_notification(
            topic_arn=sns_topic_arn,
            subject=f"PII Masking Complete: {table_name}",
            message=f"Successfully masked PII in {table_name}\n"
                   f"Records processed: {df.count():,}\n"
                   f"Columns masked: {list(masking_rules.keys())}",
            attributes={'status': 'SUCCESS', 'job': job_name}
        )

        logger.info("PII masking job completed successfully")

    except Exception as e:
        logger.error(f"PII masking job failed: {str(e)}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
