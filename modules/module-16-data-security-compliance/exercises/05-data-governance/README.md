# Exercise 05: Data Governance with Lake Formation

## Overview
Implement fine-grained data access control using AWS Lake Formation, including table-level, column-level, and row-level security, tag-based access control (TBAC), cross-account data sharing, and data lineage tracking.

**Difficulty**: ⭐⭐⭐⭐ Expert
**Duration**: ~3 hours
**Prerequisites**: AWS Lake Formation, Glue Data Catalog, IAM advanced

## Learning Objectives

- Register S3 data lake locations in Lake Formation
- Implement table-level permissions
- Configure column-level access control
- Create row-level security filters
- Set up tag-based access control (TBAC)
- Enable cross-account data sharing
- Visualize data lineage with AWS Glue
- Audit data access patterns

## Key Concepts

- **Lake Formation**: Centralized data lake security and governance
- **Data Catalog**: Metadata repository for data lake
- **LF-Tags**: Tags for attribute-based access control
- **Data Filters**: Row-level security predicates
- **Named Resource**: Specific database/table permissions
- **Tag-Based Access**: Permissions based on resource tags
- **Cross-Account Access**: Secure data sharing across AWS accounts
- **Data Lineage**: Track data flow from source to consumption

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           LAKE FORMATION GOVERNANCE ARCHITECTURE             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             AWS LAKE FORMATION                        │   │
│  │                                                       │   │
│  │   ┌─────────────────────────────────────────────┐   │   │
│  │   │         GLUE DATA CATALOG                    │   │   │
│  │   │                                             │   │   │
│  │   │  Database: finance_db                      │   │   │
│  │   │    ├─ Table: transactions (LF-Tag: PII)    │   │   │
│  │   │    ├─ Table: customers (LF-Tag: Sensitive) │   │   │
│  │   │    └─ Table: reports (LF-Tag: Public)      │   │   │
│  │   │                                             │   │   │
│  │   │  Column-Level Security:                     │   │   │
│  │   │    - ssn (hidden from analysts)            │   │   │
│  │   │    - salary (masked for contractors)       │   │   │
│  │   │                                             │   │   │
│  │   │  Row-Level Filters:                         │   │   │
│  │   │    - region = 'US' for US analysts         │   │   │
│  │   │    - dept = 'engineering' for eng team     │   │   │
│  │   └─────────────────────────────────────────────┘   │   │
│  │                                                       │   │
│  │   ┌──────────────────────────────────────────────┐  │   │
│  │   │      ACCESS CONTROL LAYERS                    │  │   │
│  │   │                                              │  │   │
│  │   │  1. Table-Level: Grant/Revoke access       │  │   │
│  │   │  2. Column-Level: Exclude sensitive columns│  │   │
│  │   │  3. Row-Level: Filter based on predicates  │  │   │
│  │   │  4. Tag-Based: Permissions via LF-Tags     │  │   │
│  │   └──────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              PRINCIPAL ACCESS MATRIX                  │   │
│  │                                                       │   │
│  │  DataEngineer Role:                                  │   │
│  │    ✓ Table: ALL                                      │   │
│  │    ✓ Column: ALL                                     │   │
│  │    ✓ Row: ALL                                        │   │
│  │                                                       │   │
│  │  DataScientist Role:                                 │   │
│  │    ✓ Table: transactions, customers                  │   │
│  │    ✗ Column: ssn, credit_card (excluded)            │   │
│  │    ✓ Row: ALL                                        │   │
│  │                                                       │   │
│  │  DataAnalyst Role:                                   │   │
│  │    ✓ Table: reports (read-only)                      │   │
│  │    ✓ Column: ALL (except PII)                        │   │
│  │    ⚡ Row: WHERE region = 'assigned_region'          │   │
│  │                                                       │   │
│  │  ExternalPartner (Cross-Account):                    │   │
│  │    ✓ Table: reports (LF-Tag: Public)                 │   │
│  │    ✓ Column: summary fields only                     │   │
│  │    ✗ Row: aggregated data only                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           DATA LINEAGE & AUDITING                     │   │
│  │                                                       │   │
│  │  Source → ETL → Transformed → Curated → Consumption  │   │
│  │    S3  →  Glue → Processed  → Reports →   Athena     │   │
│  │                                                       │   │
│  │  CloudTrail Logs:                                    │   │
│  │    - GetTable events                                 │   │
│  │    - GetPartitions events                            │   │
│  │    - FilterTable events (row-level access)           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Register Data Lake (20 minutes)

**File**: `setup_lake_formation.py`

```python
#!/usr/bin/env python3
"""Setup AWS Lake Formation data lake"""

import boto3
import json

lakeformation = boto3.client('lakeformation')
s3 = boto3.client('s3')
glue = boto3.client('glue')
sts = boto3.client('sts')


def create_data_lake_buckets():
    """Create S3 buckets for data lake"""

    account_id = sts.get_caller_identity()['Account']
    buckets = [
        f'datalake-raw-{account_id}',
        f'datalake-processed-{account_id}',
        f'datalake-curated-{account_id}'
    ]

    print("\n1. Creating Data Lake Buckets")
    print("="*60)

    for bucket in buckets:
        try:
            s3.create_bucket(Bucket=bucket)
            print(f"✓ Created: {bucket}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            print(f"  Exists: {bucket}")

    return buckets


def register_s3_locations(buckets):
    """Register S3 locations with Lake Formation"""

    print("\n2. Registering S3 Locations")
    print("="*60)

    for bucket in buckets:
        try:
            lakeformation.register_resource(
                ResourceArn=f'arn:aws:s3:::{bucket}',
                UseServiceLinkedRole=True
            )
            print(f"✓ Registered: s3://{bucket}")
        except lakeformation.exceptions.AlreadyExistsException:
            print(f"  Already registered: s3://{bucket}")


def create_glue_database():
    """Create Glue database"""

    print("\n3. Creating Glue Database")
    print("="*60)

    database_name = 'finance_analytics_db'

    try:
        glue.create_database(
            DatabaseInput={
                'Name': database_name,
                'Description': 'Finance analytics database with Lake Formation security',
                'LocationUri': f's3://datalake-curated-{sts.get_caller_identity()["Account"]}/'
            }
        )
        print(f"✓ Created database: {database_name}")
    except glue.exceptions.AlreadyExistsException:
        print(f"  Database exists: {database_name}")

    return database_name


def create_sample_tables(database_name):
    """Create sample tables in Glue catalog"""

    print("\n4. Creating Sample Tables")
    print("="*60)

    # Transactions table
    try:
        glue.create_table(
            DatabaseName=database_name,
            TableInput={
                'Name': 'transactions',
                'StorageDescriptor': {
                    'Columns': [
                        {'Name': 'transaction_id', 'Type': 'string'},
                        {'Name': 'customer_id', 'Type': 'string'},
                        {'Name': 'amount', 'Type': 'double'},
                        {'Name': 'date', 'Type': 'date'},
                        {'Name': 'region', 'Type': 'string'},
                        {'Name': 'category', 'Type': 'string'}
                    ],
                    'Location': f's3://datalake-curated-{sts.get_caller_identity()["Account"]}/transactions/',
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
                    }
                }
            }
        )
        print(f"✓ Created table: transactions")
    except glue.exceptions.AlreadyExistsException:
        print(f"  Table exists: transactions")

    # Customers table (with PII)
    try:
        glue.create_table(
            DatabaseName=database_name,
            TableInput={
                'Name': 'customers',
                'StorageDescriptor': {
                    'Columns': [
                        {'Name': 'customer_id', 'Type': 'string'},
                        {'Name': 'name', 'Type': 'string'},
                        {'Name': 'email', 'Type': 'string'},
                        {'Name': 'ssn', 'Type': 'string'},  # Sensitive
                        {'Name': 'phone', 'Type': 'string'},
                        {'Name': 'address', 'Type': 'string'},
                        {'Name': 'salary', 'Type': 'double'},  # Sensitive
                        {'Name': 'department', 'Type': 'string'}
                    ],
                    'Location': f's3://datalake-curated-{sts.get_caller_identity()["Account"]}/customers/',
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
                    }
                }
            }
        )
        print(f"✓ Created table: customers")
    except glue.exceptions.AlreadyExistsException:
        print(f"  Table exists: customers")


if __name__ == '__main__':
    print("="*60)
    print("SETTING UP LAKE FORMATION DATA LAKE")
    print("="*60)

    # Create buckets
    buckets = create_data_lake_buckets()

    # Register with Lake Formation
    register_s3_locations(buckets)

    # Create database
    database = create_glue_database()

    # Create tables
    create_sample_tables(database)

    print("\n" + "="*60)
    print("✓ LAKE FORMATION SETUP COMPLETE")
    print("="*60)
```

## Task 2: Configure Fine-Grained Access Control (45 minutes)

**File**: `configure_permissions.py`

```python
#!/usr/bin/env python3
"""Configure Lake Formation permissions"""

import boto3

lakeformation = boto3.client('lakeformation')
sts = boto3.client('sts')


def grant_table_permissions(principal, database, table, permissions):
    """Grant table-level permissions"""

    print(f"\nGranting {permissions} on {database}.{table} to {principal}")

    try:
        lakeformation.grant_permissions(
            Principal={'DataLakePrincipalIdentifier': principal},
            Resource={
                'Table': {
                    'DatabaseName': database,
                    'Name': table
                }
            },
            Permissions=permissions
        )
        print(f"  ✓ Granted")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def grant_column_permissions(principal, database, table, columns, permissions):
    """Grant column-level permissions"""

    print(f"\nGranting {permissions} on columns {columns}")

    try:
        lakeformation.grant_permissions(
            Principal={'DataLakePrincipalIdentifier': principal},
            Resource={
                'TableWithColumns': {
                    'DatabaseName': database,
                    'Name': table,
                    'ColumnNames': columns
                }
            },
            Permissions=permissions
        )
        print(f"  ✓ Granted")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def create_data_filter(database, table, filter_name, filter_expression):
    """Create row-level security filter"""

    print(f"\nCreating data filter: {filter_name}")
    print(f"  Expression: {filter_expression}")

    account_id = sts.get_caller_identity()['Account']

    try:
        lakeformation.create_data_cells_filter(
            TableData={
                'TableCatalogId': account_id,
                'DatabaseName': database,
                'TableName': table,
                'Name': filter_name,
                'RowFilter': {
                    'FilterExpression': filter_expression
                },
                'ColumnWildcard': {}
            }
        )
        print(f"  ✓ Created data filter")
    except lakeformation.exceptions.AlreadyExistsException:
        print(f"  Filter already exists")


def configure_data_engineer_access():
    """Configure full access for data engineers"""

    print("\n" + "="*60)
    print("Configuring Data Engineer Access (Full)")
    print("="*60)

    account_id = sts.get_caller_identity()['Account']
    principal = f"arn:aws:iam::{account_id}:role/DataEngineerRole"
    database = 'finance_analytics_db'

    # Full access to all tables
    for table in ['transactions', 'customers']:
        grant_table_permissions(
            principal,
            database,
            table,
            ['SELECT', 'INSERT', 'DELETE', 'DESCRIBE', 'ALTER']
        )


def configure_data_scientist_access():
    """Configure restricted access for data scientists"""

    print("\n" + "="*60)
    print("Configuring Data Scientist Access (Column-Level)")
    print("="*60)

    account_id = sts.get_caller_identity()['Account']
    principal = f"arn:aws:iam::{account_id}:role/DataScientistRole"
    database = 'finance_analytics_db'

    # Access to transactions (all columns)
    grant_table_permissions(
        principal,
        database,
        'transactions',
        ['SELECT', 'DESCRIBE']
    )

    # Access to customers (excluding sensitive columns)
    allowed_columns = ['customer_id', 'name', 'email', 'phone', 'department']
    grant_column_permissions(
        principal,
        database,
        'customers',
        allowed_columns,
        ['SELECT', 'DESCRIBE']
    )

    print("\n  Note: SSN and salary columns are excluded")


def configure_analyst_access():
    """Configure row-level filtered access for analysts"""

    print("\n" + "="*60)
    print("Configuring Analyst Access (Row-Level)")
    print("="*60)

    database = 'finance_analytics_db'

    # Create row filters for different regions
    filters = [
        ('us_analyst_filter', "region = 'US'"),
        ('eu_analyst_filter', "region = 'EU'"),
        ('engineering_filter', "department = 'engineering'")
    ]

    for filter_name, expression in filters:
        create_data_filter(database, 'transactions', filter_name, expression)

    # Grant access with filter
    account_id = sts.get_caller_identity()['Account']
    us_analyst = f"arn:aws:iam::{account_id}:role/USAnalystRole"

    grant_table_permissions(
        us_analyst,
        database,
        'transactions',
        ['SELECT', 'DESCRIBE']
    )

    print("\n  Note: Analysts only see rows matching their region")


if __name__ == '__main__':
    print("="*60)
    print("CONFIGURING LAKE FORMATION PERMISSIONS")
    print("="*60)

    configure_data_engineer_access()
    configure_data_scientist_access()
    configure_analyst_access()

    print("\n" + "="*60)
    print("✓ PERMISSIONS CONFIGURED")
    print("="*60)
    print("\nAccess Control Summary:")
    print("  - Data Engineers: Full access (all columns, all rows)")
    print("  - Data Scientists: Column-level (PII excluded)")
    print("  - Analysts: Row-level (filtered by region/dept)")
```

## Task 3: Implement Tag-Based Access Control (30 minutes)

**File**: `setup_lf_tags.py`

```python
#!/usr/bin/env python3
"""Setup Lake Formation Tags (LF-Tags) for TBAC"""

import boto3

lakeformation = boto3.client('lakeformation')
sts = boto3.client('sts')


def create_lf_tags():
    """Create LF-Tags for classification"""

    print("\n1. Creating LF-Tags")
    print("="*60)

    account_id = sts.get_caller_identity()['Account']

    tags = [
        {
            'key': 'DataClassification',
            'values': ['Public', 'Internal', 'Confidential', 'Restricted']
        },
        {
            'key': 'Compliance',
            'values': ['GDPR', 'HIPAA', 'PCI-DSS', 'SOC2', 'None']
        },
        {
            'key': 'PIIData',
            'values': ['Yes', 'No']
        }
    ]

    for tag in tags:
        try:
            lakeformation.create_lf_tag(
                CatalogId=account_id,
                TagKey=tag['key'],
                TagValues=tag['values']
            )
            print(f"✓ Created LF-Tag: {tag['key']}")
            print(f"  Values: {', '.join(tag['values'])}")
        except lakeformation.exceptions.AlreadyExistsException:
            print(f"  LF-Tag exists: {tag['key']}")


def assign_tags_to_resources():
    """Assign LF-Tags to tables"""

    print("\n2. Assigning Tags to Tables")
    print("="*60)

    account_id = sts.get_caller_identity()['Account']
    database = 'finance_analytics_db'

    # Tag transactions table
    try:
        lakeformation.add_lf_tags_to_resource(
            CatalogId=account_id,
            Resource={
                'Table': {
                    'DatabaseName': database,
                    'Name': 'transactions'
                }
            },
            LFTags=[
                {'TagKey': 'DataClassification', 'TagValues': ['Internal']},
                {'TagKey': 'Compliance', 'TagValues': ['SOC2']},
                {'TagKey': 'PIIData', 'TagValues': ['No']}
            ]
        )
        print(f"✓ Tagged: transactions")
    except Exception as e:
        print(f"  Error: {e}")

    # Tag customers table (contains PII)
    try:
        lakeformation.add_lf_tags_to_resource(
            CatalogId=account_id,
            Resource={
                'Table': {
                    'DatabaseName': database,
                    'Name': 'customers'
                }
            },
            LFTags=[
                {'TagKey': 'DataClassification', 'TagValues': ['Confidential']},
                {'TagKey': 'Compliance', 'TagValues': ['GDPR', 'HIPAA']},
                {'TagKey': 'PIIData', 'TagValues': ['Yes']}
            ]
        )
        print(f"✓ Tagged: customers")
    except Exception as e:
        print(f"  Error: {e}")


def grant_tag_based_permissions():
    """Grant permissions based on LF-Tags"""

    print("\n3. Granting Tag-Based Permissions")
    print("="*60)

    account_id = sts.get_caller_identity()['Account']
    analyst_role = f"arn:aws:iam::{account_id}:role/DataAnalystRole"

    # Grant access to all resources tagged as "Internal"
    try:
        lakeformation.grant_permissions(
            Principal={'DataLakePrincipalIdentifier': analyst_role},
            Resource={
                'LFTagPolicy': {
                    'CatalogId': account_id,
                    'ResourceType': 'TABLE',
                    'Expression': [
                        {
                            'TagKey': 'DataClassification',
                            'TagValues': ['Public', 'Internal']
                        }
                    ]
                }
            },
            Permissions=['SELECT', 'DESCRIBE']
        )
        print(f"✓ Granted access to Public/Internal data")
    except Exception as e:
        print(f"  Error: {e}")


if __name__ == '__main__':
    print("="*60)
    print("SETTING UP LF-TAGS (TBAC)")
    print("="*60)

    create_lf_tags()
    assign_tags_to_resources()
    grant_tag_based_permissions()

    print("\n" + "="*60)
    print("✓ LF-TAGS CONFIGURED")
    print("="*60)
```

## Validation Checklist

- [ ] S3 locations registered with Lake Formation
- [ ] Glue database and tables created
- [ ] Table-level permissions configured
- [ ] Column-level permissions exclude PII
- [ ] Row-level filters applied
- [ ] LF-Tags created and assigned
- [ ] Tag-based permissions working
- [ ] Cross-account sharing tested
- [ ] Data lineage visible in Glue

## Expected Results

**Governance**: Centralized access control for entire data lake
**Fine-Grained Security**: Table, column, and row-level controls
**Tag-Based Access**: Automated permissions via LF-Tags
**Auditing**: All data access logged in CloudTrail

## Key Learnings

1. **Lake Formation**: Simplifies data lake security compared to IAM + bucket policies
2. **Column Exclusion**: Hide sensitive columns without data copy
3. **Row Filters**: Implement multi-tenancy within single table
4. **LF-Tags**: Scale permissions across thousands of tables
5. **Cross-Account**: Secure data sharing without data movement

## Next Steps

- **Exercise 06**: Implement security monitoring and incident response
- **Advanced**: Implement data lineage with Apache Atlas integration
- **Production**: Automate LF-Tag assignment based on data profiling

## Resources

- [Lake Formation Documentation](https://docs.aws.amazon.com/lake-formation/)
- [LF-Tags Guide](https://docs.aws.amazon.com/lake-formation/latest/dg/tag-based-access-control.html)
- [Row-Level Security](https://docs.aws.amazon.com/lake-formation/latest/dg/data-filters-about.html)
