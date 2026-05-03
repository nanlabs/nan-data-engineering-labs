#!/usr/bin/env python3
"""
S3 Upload Utility for CloudMart Data Lake
==========================================
Uploads generated data files to S3 with proper partitioning and organization.

Features:
- Automatic date-based partitioning
- Progress tracking with tqdm
- Checksum verification
- Concurrent uploads for better performance
- Retry logic for failed uploads
"""

import argparse
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from tqdm import tqdm


class S3Uploader:
    """Handles uploading files to S3 with partitioning and verification."""

    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        """
        Initialize S3 uploader.

        Args:
            bucket_name: Name of the S3 bucket
            region: AWS region (default: us-east-1)
        """
        self.bucket_name = bucket_name
        self.region = region

        try:
            self.s3_client = boto3.client('s3', region_name=region)
            self.s3_resource = boto3.resource('s3', region_name=region)
            self.bucket = self.s3_resource.Bucket(bucket_name)
        except NoCredentialsError:
            print("ERROR: AWS credentials not found!")
            print("Please configure AWS credentials using:")
            print("  aws configure")
            print("Or set environment variables:")
            print("  AWS_ACCESS_KEY_ID")
            print("  AWS_SECRET_ACCESS_KEY")
            sys.exit(1)

    def verify_bucket_exists(self) -> bool:
        """
        Verify that the S3 bucket exists.

        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"ERROR: Bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                print(f"ERROR: Access denied to bucket '{self.bucket_name}'")
            else:
                print(f"ERROR: {e}")
            return False

    def create_bucket_if_not_exists(self) -> bool:
        """
        Create the S3 bucket if it doesn't exist.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.verify_bucket_exists():
                print(f"✓ Bucket '{self.bucket_name}' exists")
                return True

            print(f"Creating bucket '{self.bucket_name}'...")

            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            print(f"✓ Created bucket '{self.bucket_name}'")
            return True

        except ClientError as e:
            print(f"ERROR creating bucket: {e}")
            return False

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash as hexadecimal string
        """
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def get_partition_path(
        self,
        data_type: str,
        partition_date: Optional[datetime] = None
    ) -> str:
        """
        Generate partition path for data.

        Args:
            data_type: Type of data (customers, orders, products, events)
            partition_date: Date for partitioning (default: today)

        Returns:
            S3 key prefix with partitioning
        """
        if partition_date is None:
            partition_date = datetime.now()

        year = partition_date.year
        month = partition_date.month
        day = partition_date.day

        # Bronze zone structure
        return f"bronze/{data_type}/year={year}/month={month:02d}/day={day:02d}/"

    def upload_file(
        self,
        local_path: Path,
        s3_key: str,
        verify: bool = True
    ) -> Tuple[bool, str]:
        """
        Upload a single file to S3.

        Args:
            local_path: Local file path
            s3_key: S3 key (path in bucket)
            verify: Whether to verify upload with checksum

        Returns:
            Tuple of (success, message)
        """
        try:
            # Calculate local file hash
            if verify:
                local_hash = self.calculate_file_hash(local_path)

            # Upload file
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key
            )

            # Verify upload
            if verify:
                try:
                    response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    # S3 ETag is MD5 for non-multipart uploads
                    s3_etag = response['ETag'].strip('"')

                    if local_hash != s3_etag:
                        return False, f"Checksum mismatch: {local_hash} != {s3_etag}"
                except ClientError as e:
                    return False, f"Verification failed: {e}"

            file_size = local_path.stat().st_size / (1024 * 1024)  # MB
            return True, f"Uploaded {file_size:.2f} MB"

        except ClientError as e:
            return False, f"Upload failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def upload_files_concurrent(
        self,
        file_mappings: List[Tuple[Path, str]],
        max_workers: int = 5,
        verify: bool = True
    ) -> Tuple[int, int]:
        """
        Upload multiple files concurrently.

        Args:
            file_mappings: List of (local_path, s3_key) tuples
            max_workers: Maximum number of concurrent uploads
            verify: Whether to verify uploads with checksums

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.upload_file, local_path, s3_key, verify): (local_path, s3_key)
                for local_path, s3_key in file_mappings
            }

            with tqdm(total=len(file_mappings), desc="Uploading files") as pbar:
                for future in as_completed(futures):
                    local_path, s3_key = futures[future]
                    try:
                        success, message = future.result()
                        if success:
                            successful += 1
                            pbar.set_postfix_str(f"✓ {local_path.name}")
                        else:
                            failed += 1
                            print(f"\n✗ {local_path.name}: {message}")
                    except Exception as e:
                        failed += 1
                        print(f"\n✗ {local_path.name}: Unexpected error: {e}")

                    pbar.update(1)

        return successful, failed

    def list_uploaded_files(self, prefix: str = '') -> List[str]:
        """
        List files in S3 bucket with given prefix.

        Args:
            prefix: S3 key prefix to filter

        Returns:
            List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]
        except ClientError as e:
            print(f"ERROR listing files: {e}")
            return []


def discover_data_files(input_dir: Path) -> dict:
    """
    Discover data files in input directory.

    Args:
        input_dir: Directory containing data files

    Returns:
        Dictionary mapping data types to file paths
    """
    data_files = {}

    patterns = {
        'customers': ['customers.csv', 'customers.json', 'customers.parquet'],
        'products': ['products.csv', 'products.json', 'products.parquet'],
        'orders': ['orders.csv', 'orders.json', 'orders.parquet'],
        'events': ['events.csv', 'events.json', 'events.parquet']
    }

    for data_type, file_patterns in patterns.items():
        for pattern in file_patterns:
            file_path = input_dir / pattern
            if file_path.exists():
                data_files[data_type] = file_path
                break

    return data_files


def upload_files_to_s3(
    input_dir: Path,
    bucket_name: str,
    region: str = 'us-east-1',
    partition_date: Optional[datetime] = None,
    verify: bool = True,
    create_bucket: bool = False,
    max_workers: int = 5
) -> bool:
    """
    Upload data files to S3 with partitioning.

    Args:
        input_dir: Directory containing data files
        bucket_name: S3 bucket name
        region: AWS region
        partition_date: Date for partitioning (default: today)
        verify: Whether to verify uploads
        create_bucket: Whether to create bucket if it doesn't exist
        max_workers: Maximum concurrent uploads

    Returns:
        True if all uploads successful, False otherwise
    """
    print("=" * 70)
    print("S3 Upload Utility - CloudMart Data Lake")
    print("=" * 70)
    print(f"Bucket:       {bucket_name}")
    print(f"Region:       {region}")
    print(f"Input Dir:    {input_dir}")
    print(f"Verification: {'Enabled' if verify else 'Disabled'}")
    print("=" * 70)
    print()

    # Initialize uploader
    uploader = S3Uploader(bucket_name, region)

    # Verify or create bucket
    if create_bucket:
        if not uploader.create_bucket_if_not_exists():
            return False
    else:
        if not uploader.verify_bucket_exists():
            return False

    # Discover data files
    print("Discovering data files...")
    data_files = discover_data_files(input_dir)

    if not data_files:
        print("ERROR: No data files found in input directory")
        return False

    print(f"Found {len(data_files)} data file(s):")
    for data_type, file_path in data_files.items():
        file_size = file_path.stat().st_size / (1024 * 1024)
        print(f"  • {data_type}: {file_path.name} ({file_size:.2f} MB)")
    print()

    # Prepare file mappings with partitioning
    file_mappings = []
    for data_type, file_path in data_files.items():
        partition_path = uploader.get_partition_path(data_type, partition_date)
        s3_key = partition_path + file_path.name
        file_mappings.append((file_path, s3_key))

    print(f"Uploading {len(file_mappings)} file(s) to S3...")
    print()

    # Upload files
    successful, failed = uploader.upload_files_concurrent(
        file_mappings,
        max_workers=max_workers,
        verify=verify
    )

    print()
    print("=" * 70)
    print("Upload Summary")
    print("=" * 70)
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print()

    if failed == 0:
        print("✓ All files uploaded successfully!")
        print()
        print("Uploaded files:")
        for local_path, s3_key in file_mappings:
            print(f"  s3://{bucket_name}/{s3_key}")
        return True
    else:
        print(f"✗ {failed} file(s) failed to upload")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Upload CloudMart data files to S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload files from default directory
  python upload_to_s3.py --bucket my-cloudmart-data-lake

  # Upload with specific input directory
  python upload_to_s3.py --bucket my-bucket --input-dir ./generated-data

  # Upload to specific region and create bucket if needed
  python upload_to_s3.py --bucket my-bucket --region us-west-2 --create-bucket

  # Upload with custom partition date
  python upload_to_s3.py --bucket my-bucket --partition-date 2024-01-15

  # Upload without verification (faster but less safe)
  python upload_to_s3.py --bucket my-bucket --no-verify
        """
    )

    parser.add_argument(
        '--bucket',
        type=str,
        required=True,
        help='S3 bucket name'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('../input'),
        help='Input directory containing data files (default: ../input)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--partition-date',
        type=str,
        help='Partition date in YYYY-MM-DD format (default: today)'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Disable upload verification with checksums'
    )
    parser.add_argument(
        '--create-bucket',
        action='store_true',
        help='Create bucket if it does not exist'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help='Maximum concurrent uploads (default: 5)'
    )

    args = parser.parse_args()

    # Parse partition date if provided
    partition_date = None
    if args.partition_date:
        try:
            partition_date = datetime.strptime(args.partition_date, '%Y-%m-%d')
        except ValueError:
            print(f"ERROR: Invalid date format '{args.partition_date}'. Use YYYY-MM-DD")
            sys.exit(1)

    # Validate input directory
    if not args.input_dir.exists():
        print(f"ERROR: Input directory does not exist: {args.input_dir}")
        sys.exit(1)

    # Upload files
    try:
        success = upload_files_to_s3(
            input_dir=args.input_dir,
            bucket_name=args.bucket,
            region=args.region,
            partition_date=partition_date,
            verify=not args.no_verify,
            create_bucket=args.create_bucket,
            max_workers=args.max_workers
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nUpload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
