#!/usr/bin/env python3
"""
Cost Allocation Tagging
Implement and validate cost allocation tagging strategy
"""

import boto3
import pandas as pd
import re
from typing import Dict, List, Tuple

class CostTaggingManager:
    """Manage cost allocation tagging strategy"""

    # Tagging schema
    REQUIRED_TAGS = {
        'Environment': ['prod', 'staging', 'dev', 'test'],
        'Team': ['data-engineering', 'data-science', 'analytics', 'devops'],
        'Project': [],  # Any value allowed
        'CostCenter': [],  # Pattern: CC-XXXXX
        'Owner': []  # Email address
    }

    TAG_PATTERNS = {
        'CostCenter': r'^CC-\d{5}$',
        'Owner': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    }

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.ce = boto3.client('ce', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.region = region

    def validate_tags(self, resource_tags: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """
        Validate resource tags against schema

        Args:
            resource_tags: Dictionary of tag key-value pairs

        Returns:
            Tuple of (missing_tags, invalid_tags)
        """
        missing = []
        invalid = []

        # Check required tags
        for tag_key in self.REQUIRED_TAGS:
            if tag_key not in resource_tags:
                missing.append(tag_key)
            else:
                value = resource_tags[tag_key]

                # Check against allowed values (if specified)
                if self.REQUIRED_TAGS[tag_key] and value not in self.REQUIRED_TAGS[tag_key]:
                    invalid.append(f"{tag_key}={value} (allowed: {', '.join(self.REQUIRED_TAGS[tag_key])})")

                # Check against regex patterns (if specified)
                if tag_key in self.TAG_PATTERNS:
                    pattern = self.TAG_PATTERNS[tag_key]
                    if not re.match(pattern, value):
                        invalid.append(f"{tag_key}={value} (pattern: {pattern})")

        return missing, invalid

    def activate_cost_allocation_tags(self):
        """Activate cost allocation tags in billing console"""
        print("\n🔌 Activating cost allocation tags...")

        tags_to_activate = list(self.REQUIRED_TAGS.keys())

        # Note: boto3 doesn't have direct API for tag activation
        # Must be done via Billing Console or AWS Organizations API
        print(f"  Tags to activate: {', '.join(tags_to_activate)}")
        print("\n⚠️  Manual Step Required:")
        print("  1. Go to AWS Billing Console")
        print("  2. Navigate to Cost Allocation Tags")
        print(f"  3. Activate these user-defined tags: {', '.join(tags_to_activate)}")
        print("  4. Wait 24 hours for tags to appear in Cost Explorer and CUR")

    def tag_ec2_instances(self, dry_run: bool = False) -> Dict:
        """
        Apply cost allocation tags to EC2 instances

        Args:
            dry_run: If True, only show what would be tagged

        Returns:
            Summary statistics
        """
        print(f"\n🖥️  Tagging EC2 instances (dry_run={dry_run})...")

        instances = self.ec2.describe_instances()

        tagged_count = 0
        missing_tags_count = 0

        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                existing_tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

                # Determine tags based on instance attributes
                new_tags = {}

                # Determine environment from instance name or existing tags
                name = existing_tags.get('Name', '')
                if 'prod' in name.lower():
                    new_tags['Environment'] = 'prod'
                elif 'staging' in name.lower() or 'stg' in name.lower():
                    new_tags['Environment'] = 'staging'
                elif 'dev' in name.lower():
                    new_tags['Environment'] = 'dev'
                else:
                    new_tags['Environment'] = 'dev'  # Default to dev

                # Add default tags if missing
                if 'Team' not in existing_tags:
                    new_tags['Team'] = 'data-engineering'  # Default team
                if 'Project' not in existing_tags:
                    new_tags['Project'] = 'infrastructure'
                if 'CostCenter' not in existing_tags:
                    new_tags['CostCenter'] = 'CC-12345'
                if 'Owner' not in existing_tags:
                    new_tags['Owner'] = 'data-team@example.com'

                # Check if tags are needed
                missing, invalid = self.validate_tags({**existing_tags, **new_tags})

                if new_tags:
                    if not dry_run:
                        try:
                            self.ec2.create_tags(
                                Resources=[instance_id],
                                Tags=[{'Key': k, 'Value': v} for k, v in new_tags.items()]
                            )
                            print(f"  ✅ Tagged {instance_id}: {list(new_tags.keys())}")
                            tagged_count += 1
                        except Exception as e:
                            print(f"  ❌ Failed to tag {instance_id}: {e}")
                    else:
                        print(f"  [DRY RUN] Would tag {instance_id}: {new_tags}")
                        tagged_count += 1
                else:
                    if missing:
                        print(f"  ⚠️  {instance_id} missing tags: {missing}")
                        missing_tags_count += 1

        return {
            'tagged': tagged_count,
            'missing_tags': missing_tags_count
        }

    def tag_s3_buckets(self, dry_run: bool = False) -> Dict:
        """Apply cost allocation tags to S3 buckets"""
        print(f"\n🪣 Tagging S3 buckets (dry_run={dry_run})...")

        buckets = self.s3.list_buckets()['Buckets']

        tagged_count = 0

        for bucket in buckets:
            bucket_name = bucket['Name']

            # Get existing tags
            try:
                tagging = self.s3.get_bucket_tagging(Bucket=bucket_name)
                existing_tags = {tag['Key']: tag['Value'] for tag in tagging['TagSet']}
            except self.s3.exceptions.ClientError:
                existing_tags = {}

            # Determine tags based on bucket name
            new_tags = {}

            if 'prod' in bucket_name:
                new_tags['Environment'] = 'prod'
            elif 'staging' in bucket_name or 'stg' in bucket_name:
                new_tags['Environment'] = 'staging'
            else:
                new_tags['Environment'] = 'dev'

            # Default tags
            if 'Team' not in existing_tags:
                new_tags['Team'] = 'data-engineering'
            if 'Project' not in existing_tags:
                new_tags['Project'] = 'data-platform'
            if 'CostCenter' not in existing_tags:
                new_tags['CostCenter'] = 'CC-67890'
            if 'Owner' not in existing_tags:
                new_tags['Owner'] = 'data-team@example.com'

            if new_tags:
                merged_tags = {**existing_tags, **new_tags}

                if not dry_run:
                    try:
                        self.s3.put_bucket_tagging(
                            Bucket=bucket_name,
                            Tagging={
                                'TagSet': [{'Key': k, 'Value': v} for k, v in merged_tags.items()]
                            }
                        )
                        print(f"  ✅ Tagged {bucket_name}: {list(new_tags.keys())}")
                        tagged_count += 1
                    except Exception as e:
                        print(f"  ❌ Failed to tag {bucket_name}: {e}")
                else:
                    print(f"  [DRY RUN] Would tag {bucket_name}: {new_tags}")
                    tagged_count += 1

        return {'tagged': tagged_count}

    def generate_tagging_compliance_report(self) -> pd.DataFrame:
        """Generate report of tagging compliance across resources"""
        print("\n📋 Generating tagging compliance report...")

        resources = []

        # Check EC2 instances
        try:
            instances = self.ec2.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    missing, invalid = self.validate_tags(tags)

                    resources.append({
                        'ResourceType': 'EC2',
                        'ResourceId': instance['InstanceId'],
                        'HasAllRequiredTags': len(missing) == 0,
                        'MissingTags': ', '.join(missing) if missing else 'None',
                        'InvalidTags': ', '.join(invalid) if invalid else 'None',
                        'ComplianceStatus': 'Compliant' if not missing and not invalid else 'Non-Compliant'
                    })
        except Exception as e:
            print(f"  ⚠️  Could not check EC2 instances: {e}")

        # Check S3 buckets
        try:
            buckets = self.s3.list_buckets()['Buckets']
            for bucket in buckets:
                bucket_name = bucket['Name']
                try:
                    tagging = self.s3.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tagging['TagSet']}
                except:
                    tags = {}

                missing, invalid = self.validate_tags(tags)

                resources.append({
                    'ResourceType': 'S3',
                    'ResourceId': bucket_name,
                    'HasAllRequiredTags': len(missing) == 0,
                    'MissingTags': ', '.join(missing) if missing else 'None',
                    'InvalidTags': ', '.join(invalid) if invalid else 'None',
                    'ComplianceStatus': 'Compliant' if not missing and not invalid else 'Non-Compliant'
                })
        except Exception as e:
            print(f"  ⚠️  Could not check S3 buckets: {e}")

        # Create DataFrame
        df = pd.DataFrame(resources)

        if not df.empty:
            # Calculate compliance metrics
            total = len(df)
            compliant = len(df[df['ComplianceStatus'] == 'Compliant'])
            compliance_rate = (compliant / total * 100) if total > 0 else 0

            print("\n📊 Tagging Compliance Report:")
            print(f"  Total resources checked: {total}")
            print(f"  Compliant: {compliant} ({compliance_rate:.1f}%)")
            print(f"  Non-compliant: {total - compliant}")

            # Show non-compliant resources
            non_compliant = df[df['ComplianceStatus'] == 'Non-Compliant']
            if not non_compliant.empty:
                print("\n⚠️  Non-Compliant Resources:")
                for idx, row in non_compliant.head(10).iterrows():
                    print(f"  {row['ResourceType']}: {row['ResourceId']}")
                    print(f"    Missing: {row['MissingTags']}")
                    if row['InvalidTags'] != 'None':
                        print(f"    Invalid: {row['InvalidTags']}")

            # Save report
            df.to_csv('tagging-compliance-report.csv', index=False)
            print("\n✅ Report saved: tagging-compliance-report.csv")

        return df

def main():
    """Main tagging workflow"""
    print("=" * 70)
    print("Cost Allocation Tagging Management")
    print("=" * 70)

    manager = CostTaggingManager()

    # Step 1: Activate tags in billing console
    print("\n[Step 1/4] Activating cost allocation tags...")
    manager.activate_cost_allocation_tags()

    # Step 2: Tag EC2 instances (dry run first)
    print("\n[Step 2/4] Tagging EC2 instances...")
    ec2_stats = manager.tag_ec2_instances(dry_run=True)
    print(f"  Would tag {ec2_stats['tagged']} instances")
    print(f"  {ec2_stats['missing_tags']} instances with missing tags")

    # Ask for confirmation
    response = input("\n  Apply tags to EC2 instances? (yes/no): ")
    if response.lower() == 'yes':
        ec2_stats = manager.tag_ec2_instances(dry_run=False)
        print(f"  ✅ Tagged {ec2_stats['tagged']} EC2 instances")

    # Step 3: Tag S3 buckets (dry run first)
    print("\n[Step 3/4] Tagging S3 buckets...")
    s3_stats = manager.tag_s3_buckets(dry_run=True)
    print(f"  Would tag {s3_stats['tagged']} buckets")

    response = input("\n  Apply tags to S3 buckets? (yes/no): ")
    if response.lower() == 'yes':
        s3_stats = manager.tag_s3_buckets(dry_run=False)
        print(f"  ✅ Tagged {s3_stats['tagged']} S3 buckets")

    # Step 4: Generate compliance report
    print("\n[Step 4/4] Generating compliance report...")
    df = manager.generate_tagging_compliance_report()

    # Summary
    print("\n" + "=" * 70)
    print("✅ Tagging Management Complete!")
    print("=" * 70)

    if not df.empty:
        compliant = len(df[df['ComplianceStatus'] == 'Compliant'])
        total = len(df)
        compliance_rate = (compliant / total * 100) if total > 0 else 0

        print("\n📊 Summary:")
        print(f"  Resources checked: {total}")
        print(f"  Compliance rate: {compliance_rate:.1f}%")
        print("  Target: 95%")

        if compliance_rate < 95:
            print("\n📋 Action Items:")
            print(f"  1. Tag {total - compliant} non-compliant resources")
            print("  2. Implement tag enforcement policy (SCP or Lambda)")
            print("  3. Schedule weekly compliance checks")

if __name__ == '__main__':
    main()
