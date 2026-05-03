# Exercise 03: Lake Formation Permissions

## Objective

Learn to implement fine-grained access control using AWS Lake Formation, including database/table/column/row-level permissions and Tag-Based Access Control (TBAC).

## Prerequisites

- Exercises 01 and 02 completed
- Data Catalog databases and tables created
- LocalStack with Lake Formation support (limited)
- Understanding of IAM roles and policies

## Learning Goals

- Configure Lake Formation data lake location permissions
- Implement database and table-level permissions
- Apply column-level security to mask sensitive data
- Configure row-level security with data filters
- Set up Tag-Based Access Control (TBAC)
- Manage cross-account data sharing

## Exercise Tasks

### Task 1: Register S3 Locations with Lake Formation

Register your S3 bucket as a Lake Formation data lake location:

```bash
# Register S3 location for Bronze layer
awslocal lakeformation register-resource \
    --resource-arn arn:aws:s3:::training-data-lake/bronze/ \
    --use-service-linked-role

# Register Silver layer
awslocal lakeformation register-resource \
    --resource-arn arn:aws:s3:::training-data-lake/silver/ \
    --use-service-linked-role

# Register Gold layer
awslocal lakeformation register-resource \
    --resource-arn arn:aws:s3:::training-data-lake/gold/ \
    --use-service-linked-role

# Verify registered locations
awslocal lakeformation list-resources
```

### Task 2: Create IAM Roles for Different Personas

Create roles representing different user types:

```bash
# 1. Data Engineer Role (full access to Bronze and Silver)
cat > /tmp/data-engineer-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "glue.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

awslocal iam create-role \
    --role-name DataEngineer \
    --assume-role-policy-document file:///tmp/data-engineer-trust.json \
    --tags Key=Role,Value=Engineer Key=Department,Value=DataPlatform

# 2. Data Analyst Role (read access to Silver and Gold)
awslocal iam create-role \
    --role-name DataAnalyst \
    --assume-role-policy-document file:///tmp/data-engineer-trust.json \
    --tags Key=Role,Value=Analyst Key=Department,Value=Analytics

# 3. Data Scientist Role (read access to Gold only)
awslocal iam create-role \
    --role-name DataScientist \
    --assume-role-policy-document file:///tmp/data-engineer-trust.json \
    --tags Key=Role,Value=Scientist Key=Department,Value=ML

# 4. External Partner Role (limited read access)
awslocal iam create-role \
    --role-name ExternalPartner \
    --assume-role-policy-document file:///tmp/data-engineer-trust.json \
    --tags Key=Role,Value=External Key=Department,Value=ThirdParty

# Verify roles
awslocal iam list-roles --query 'Roles[?contains(RoleName, `Data`) || contains(RoleName, `External`)].RoleName'
```

### Task 3: Grant Data Location Permissions

Grant S3 location access to roles:

```bash
# Grant Data Engineer access to all layers
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataEngineer\"}' \
    --resource '{\"DataLocation\":{\"ResourceArn\":\"arn:aws:s3:::training-data-lake/\"}}' \
    --permissions DATA_LOCATION_ACCESS

# Grant Data Analyst access to Silver and Gold
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataAnalyst\"}' \
    --resource '{\"DataLocation\":{\"ResourceArn\":\"arn:aws:s3:::training-data-lake/silver/\"}}' \
    --permissions DATA_LOCATION_ACCESS

awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataAnalyst\"}' \
    --resource '{\"DataLocation\":{\"ResourceArn\":\"arn:aws:s3:::training-data-lake/gold/\"}}' \
    --permissions DATA_LOCATION_ACCESS

# Grant Data Scientist access to Gold only
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataScientist\"}' \
    --resource '{\"DataLocation\":{\"ResourceArn\":\"arn:aws:s3:::training-data-lake/gold/\"}}' \
    --permissions DATA_LOCATION_ACCESS
```

### Task 4: Grant Database-Level Permissions

Configure database access for each role:

```bash
# Data Engineer: Full access to Bronze and Silver databases
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataEngineer\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_bronze_db\"}}' \
    --permissions ALL \
    --permissions-with-grant-option CREATE_TABLE DROP ALTER

awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataEngineer\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_silver_db\"}}' \
    --permissions ALL \
    --permissions-with-grant-option CREATE_TABLE ALTER

# Data Analyst: Select and Describe on Silver and Gold
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataAnalyst\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_silver_db\"}}' \
    --permissions SELECT DESCRIBE

awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataAnalyst\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_gold_db\"}}' \
    --permissions SELECT DESCRIBE

# Data Scientist: Select only on Gold
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataScientist\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_gold_db\"}}' \
    --permissions SELECT DESCRIBE
```

### Task 5: Implement Column-Level Security

Grant access to specific columns, excluding PII:

```bash
# Data Analyst: Access to all columns EXCEPT PII fields in Silver table
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataAnalyst\"}' \
    --resource '{
        \"TableWithColumns\":{
            \"DatabaseName\":\"dev_sales_silver_db\",
            \"Name\":\"sales_transactions_clean\",
            \"ColumnWildcard\":{
                \"ExcludedColumnNames\":[\"customer_email_masked\",\"customer_phone_masked\"]
            }
        }
    }' \
    --permissions SELECT DESCRIBE

# External Partner: Very limited columns only
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/ExternalPartner\"}' \
    --resource '{
        \"TableWithColumns\":{
            \"DatabaseName\":\"dev_sales_gold_db\",
            \"Name\":\"sales_daily_summary\",
            \"ColumnNames\":[\"date\",\"region\",\"category\",\"total_revenue\"]
        }
    }' \
    --permissions SELECT DESCRIBE
```

Test column-level security:

```python
# test_column_security.py
import boto3

# Simulate Data Analyst querying (can see most columns, not PII)
athena = boto3.client(
    'athena',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Query 1: Allowed columns (should succeed)
query1 = """
SELECT date, transaction_id, category, total_amount, region
FROM dev_sales_silver_db.sales_transactions_clean
LIMIT 10
"""

# Query 2: Attempt to access excluded PII columns (should fail)
query2 = """
SELECT customer_email_masked, customer_phone_masked
FROM dev_sales_silver_db.sales_transactions_clean
LIMIT 10
"""

# Query 3: External Partner with very limited columns (should succeed)
query3 = """
SELECT date, region, category, total_revenue
FROM dev_sales_gold_db.sales_daily_summary
WHERE year = '2024' AND month = '03'
"""

print("Testing column-level security...")
# In real AWS, these queries would be executed through Athena
# In LocalStack, Lake Formation column filtering may be limited
```

### Task 6: Implement Row-Level Security with Data Filters

Create data cell filters for row-level access control:

```bash
# Create data filter for US-EAST region only
awslocal lakeformation create-data-cells-filter \
    --table-data '{
        \"TableCatalogId\":\"000000000000\",
        \"DatabaseName\":\"dev_sales_silver_db\",
        \"TableName\":\"sales_transactions_clean\",
        \"Name\":\"east_region_only\",
        \"RowFilter\":{
            \"FilterExpression\":\"region = '"'"'US-EAST'"'"'\"
        },
        \"ColumnWildcard\":{}
    }'

# Create filter for high-value transactions only
awslocal lakeformation create-data-cells-filter \
    --table-data '{
        \"TableCatalogId\":\"000000000000\",
        \"DatabaseName\":\"dev_sales_silver_db\",
        \"TableName\":\"sales_transactions_clean\",
        \"Name\":\"high_value_only\",
        \"RowFilter\":{
            \"FilterExpression\":\"total_amount > 500\"
        },
        \"ColumnWildcard\":{}
    }'

# Grant External Partner access with row filter
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/ExternalPartner\"}' \
    --resource '{
        \"DataCellsFilter\":{
            \"TableCatalogId\":\"000000000000\",
            \"DatabaseName\":\"dev_sales_silver_db\",
            \"TableName\":\"sales_transactions_clean\",
            \"Name\":\"east_region_only\"
        }
    }' \
    --permissions SELECT

# List all data cell filters
awslocal lakeformation list-data-cells-filter \
    --table '{\"DatabaseName\":\"dev_sales_silver_db\",\"TableName\":\"sales_transactions_clean\"}'
```

Row filter examples:

```sql
-- Filter Example 1: Region-based access
region = 'US-EAST'

-- Filter Example 2: Date range
year = '2024' AND month IN ('01', '02', '03')

-- Filter Example 3: Value threshold
total_amount >= 100 AND total_amount <= 10000

-- Filter Example 4: Status-based
status = 'completed'

-- Filter Example 5: Complex conditions
region IN ('US-EAST', 'US-WEST') AND total_amount > 100 AND category != 'Grocery'

-- Filter Example 6: Current year only
year = CAST(year(current_date) AS VARCHAR)
```

### Task 7: Configure Tag-Based Access Control (TBAC)

Create LF-Tags for policy-based permissions:

```bash
# Create LF-Tags
awslocal lakeformation create-lf-tag \
    --tag-key DataSensitivity \
    --tag-values Public Internal Confidential Restricted

awslocal lakeformation create-lf-tag \
    --tag-key DataDomain \
    --tag-values Sales Marketing Finance Operations

awslocal lakeformation create-lf-tag \
    --tag-key CostCenter \
    --tag-values CC-1001 CC-2002 CC-3003 CC-4004

awslocal lakeformation create-lf-tag \
    --tag-key QualityLevel \
    --tag-values Bronze Silver Gold

# Tag databases
awslocal lakeformation add-lf-tags-to-resource \
    --resource '{\"Database\":{\"Name\":\"dev_sales_bronze_db\"}}' \
    --lf-tags '[
        {\"TagKey\":\"DataSensitivity\",\"TagValues\":[\"Confidential\"]},
        {\"TagKey\":\"DataDomain\",\"TagValues\":[\"Sales\"]},
        {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Bronze\"]}
    ]'

awslocal lakeformation add-lf-tags-to-resource \
    --resource '{\"Database\":{\"Name\":\"dev_sales_silver_db\"}}' \
    --lf-tags '[
        {\"TagKey\":\"DataSensitivity\",\"TagValues\":[\"Internal\"]},
        {\"TagKey\":\"DataDomain\",\"TagValues\":[\"Sales\"]},
        {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Silver\"]}
    ]'

awslocal lakeformation add-lf-tags-to-resource \
    --resource '{\"Database\":{\"Name\":\"dev_sales_gold_db\"}}' \
    --lf-tags '[
        {\"TagKey\":\"DataSensitivity\",\"TagValues\":[\"Internal\"]},
        {\"TagKey\":\"DataDomain\",\"TagValues\":[\"Sales\"]},
        {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Gold\"]}
    ]'

# Grant permissions based on tags
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::000000000000:role/DataScientist\"}' \
    --resource '{
        \"LFTagPolicy\":{
            \"ResourceType\":\"DATABASE\",
            \"Expression\":[
                {\"TagKey\":\"DataDomain\",\"TagValues\":[\"Sales\"]},
                {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Gold\"]}
            ]
        }
    }' \
    --permissions SELECT DESCRIBE
```

Benefits of TBAC:

```python
# demonstrate_tbac_benefits.py
"""
Tag-Based Access Control Benefits:

1. Automatic Inheritance:
   - New tables in Gold database automatically get Gold tag
   - No need to grant explicit permissions for new tables
   - Reduces IAM policy management overhead

2. Dynamic Access:
   - Change tag values without modifying IAM policies
   - Instantly propagate permission changes
   - Centralized governance

3. Simplified Multi-Account Sharing:
   - Share by tags instead of explicit table names
   - New tables automatically available to consumers
   - Scalable for large catalogs

4. Compliance and Auditing:
   - Clear classification with tags
   - Easy to identify sensitive data
   - Audit who has access to what sensitivity level
"""

import boto3

lf = boto3.client(
    'lakeformation',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# List all LF-Tags
print("=== LF-Tags ===")
response = lf.list_lf_tags()
for tag in response.get('LFTags', []):
    print(f"{tag['TagKey']}: {', '.join(tag['TagValues'])}")

# Get resources by tag
print("\n=== Resources tagged with QualityLevel=Gold ===")
response = lf.search_tables_by_lf_tags(
    Expression=[{
        'TagKey': 'QualityLevel',
        'TagValues': ['Gold']
    }]
)
for table in response.get('TableList', []):
    print(f"- {table['DatabaseName']}.{table['Name']}")

# Show tag-based permissions
print("\n=== Tag-Based Permissions for DataScientist ===")
response = lf.list_permissions(
    Principal={'DataLakePrincipalIdentifier': 'arn:aws:iam::000000000000:role/DataScientist'},
    ResourceType='LF_TAG_POLICY'
)
for perm in response.get('PrincipalResourcePermissions', []):
    resource = perm['Resource']
    if 'LFTagPolicy' in resource:
        policy = resource['LFTagPolicy']
        print(f"Resource Type: {policy['ResourceType']}")
        for expr in policy['Expression']:
            print(f"  {expr['TagKey']} in {expr['TagValues']}")
        print(f"  Permissions: {', '.join(perm['Permissions'])}")
```

### Task 8: List and Audit Permissions

Create an audit script to review all granted permissions:

```python
# audit_permissions.py
import boto3
import json
from collections import defaultdict

lf = boto3.client(
    'lakeformation',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def audit_all_permissions():
    """Comprehensive permission audit"""

    print("=" * 80)
    print("LAKE FORMATION PERMISSIONS AUDIT")
    print("=" * 80)

    # Group by principal
    permissions_by_principal = defaultdict(list)

    # Get all permissions (iterate through different resource types)
    for resource_type in ['CATALOG', 'DATABASE', 'TABLE', 'DATA_LOCATION']:
        try:
            response = lf.list_permissions(ResourceType=resource_type)
            for perm in response.get('PrincipalResourcePermissions', []):
                principal = perm['Principal']['DataLakePrincipalIdentifier']
                permissions_by_principal[principal].append(perm)
        except Exception as e:
            print(f"Error listing {resource_type}: {e}")

    # Display by principal
    for principal, perms in permissions_by_principal.items():
        role_name = principal.split('/')[-1] if '/' in principal else principal
        print(f"\n{'='*80}")
        print(f"Principal: {role_name}")
        print(f"{'='*80}")

        for perm in perms:
            resource = perm['Resource']

            if 'Database' in resource:
                print(f"\n  Resource: Database")
                print(f"  Name: {resource['Database']['Name']}")
            elif 'Table' in resource:
                print(f"\n  Resource: Table")
                print(f"  Database: {resource['Table']['DatabaseName']}")
                print(f"  Table: {resource['Table'].get('Name', 'ALL_TABLES')}")
            elif 'TableWithColumns' in resource:
                twc = resource['TableWithColumns']
                print(f"\n  Resource: Table with Columns")
                print(f"  Database: {twc['DatabaseName']}")
                print(f"  Table: {twc['Name']}")
                if 'ColumnNames' in twc:
                    print(f"  Columns: {', '.join(twc['ColumnNames'])}")
                elif 'ColumnWildcard' in twc:
                    excluded = twc['ColumnWildcard'].get('ExcludedColumnNames', [])
                    if excluded:
                        print(f"  Columns: ALL EXCEPT {', '.join(excluded)}")
                    else:
                        print(f"  Columns: ALL")
            elif 'DataLocation' in resource:
                print(f"\n  Resource: Data Location")
                print(f"  ARN: {resource['DataLocation']['ResourceArn']}")
            elif 'LFTagPolicy' in resource:
                policy = resource['LFTagPolicy']
                print(f"\n  Resource: LF-Tag Policy")
                print(f"  Resource Type: {policy['ResourceType']}")
                print(f"  Tag Expression:")
                for expr in policy['Expression']:
                    print(f"    {expr['TagKey']} IN {expr['TagValues']}")

            print(f"  Permissions: {', '.join(perm['Permissions'])}")
            if perm.get('PermissionsWithGrantOption'):
                print(f"  Grant Options: {', '.join(perm['PermissionsWithGrantOption'])}")

    # Summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total Principals: {len(permissions_by_principal)}")
    total_permissions = sum(len(perms) for perms in permissions_by_principal.values())
    print(f"Total Permission Grants: {total_permissions}")

if __name__ == '__main__':
    audit_all_permissions()
```

Run the audit:
```bash
python audit_permissions.py
```

### Task 9: Test Permission Enforcement

Create test scripts to verify permissions work correctly:

```python
# test_permissions.py
import boto3
from botocore.exceptions import ClientError

def test_permissions(role_arn, database, table, query):
    """Test if a role can execute a specific query"""

    # Assume the role
    sts = boto3.client(
        'sts',
        endpoint_url='http://localhost:4566',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    try:
        # In real AWS, you would assume role
        # credentials = sts.assume_role(
        #     RoleArn=role_arn,
        #     RoleSessionName='test-session'
        # )

        athena = boto3.client(
            'athena',
            endpoint_url='http://localhost:4566',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )

        # Execute query
        response = athena.start_query_execution(
            QueryString=query,
            ResultConfiguration={'OutputLocation': 's3://athena-results/'}
        )

        print(f"✅ SUCCESS: {role_arn.split('/')[-1]} can execute query")
        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ DENIED: {role_arn.split('/')[-1]} cannot execute query")
        else:
            print(f"⚠️  ERROR: {error_code}")
        return False

# Test cases
test_cases = [
    {
        'role': 'arn:aws:iam::000000000000:role/DataEngineer',
        'database': 'dev_sales_bronze_db',
        'table': 'sales_transactions',
        'query': 'SELECT * FROM dev_sales_bronze_db.sales_transactions LIMIT 10',
        'expected': 'ALLOW'
    },
    {
        'role': 'arn:aws:iam::000000000000:role/DataAnalyst',
        'database': 'dev_sales_bronze_db',
        'table': 'sales_transactions',
        'query': 'SELECT * FROM dev_sales_bronze_db.sales_transactions LIMIT 10',
        'expected': 'DENY'  # Analysts don't have Bronze access
    },
    {
        'role': 'arn:aws:iam::000000000000:role/DataAnalyst',
        'database': 'dev_sales_silver_db',
        'table': 'sales_transactions_clean',
        'query': 'SELECT date, category, total_amount FROM dev_sales_silver_db.sales_transactions_clean LIMIT 10',
        'expected': 'ALLOW'
    },
    {
        'role': 'arn:aws:iam::000000000000:role/DataAnalyst',
        'database': 'dev_sales_silver_db',
        'table': 'sales_transactions_clean',
        'query': 'SELECT customer_email_masked FROM dev_sales_silver_db.sales_transactions_clean LIMIT 10',
        'expected': 'DENY'  # Excluded column
    },
    {
        'role': 'arn:aws:iam::000000000000:role/ExternalPartner',
        'database': 'dev_sales_gold_db',
        'table': 'sales_daily_summary',
        'query': 'SELECT date, region, total_revenue FROM dev_sales_gold_db.sales_daily_summary LIMIT 10',
        'expected': 'ALLOW'  # Limited columns
    }
]

print("\n=== Permission Tests ===\n")
for test in test_cases:
    print(f"Test: {test['role'].split('/')[-1]} → {test['database']}.{test['table']}")
    print(f"Expected: {test['expected']}")
    test_permissions(test['role'], test['database'], test['table'], test['query'])
    print()
```

## Validation

Test your Lake Formation setup:

```bash
python validation_03.py
```

Expected results:
- ✅ S3 locations registered with Lake Formation
- ✅ 4 IAM roles created (Engineer, Analyst, Scientist, Partner)
- ✅ Data location permissions granted correctly
- ✅ Database-level permissions configured
- ✅ Column-level exclusions working
- ✅ Row-level filters created and applied
- ✅ LF-Tags created and resources tagged
- ✅ Tag-based permissions granted
- ✅ Permission audit shows correct access matrix

## Key Takeaways

1. **Permission Layers**:
   - Data Location → Database → Table → Column → Row
   - Each layer must be granted explicitly

2. **Column-Level Security**:
   - Use ColumnWildcard with ExcludedColumnNames for most columns
   - Use specific ColumnNames for very restricted access

3. **Row-Level Security**:
   - Data cell filters support SQL WHERE expressions
   - Filters are transparent to users
   - Performance impact on large tables

4. **TBAC Benefits**:
   - Automatic inheritance for new resources
   - Simplified policy management at scale
   - Better compliance tracking

5. **Best Practices**:
   - Register S3 locations before granting permissions
   - Use IAM roles, not users
   - Test permissions before production deployment
   - Regular audits of permission grants
   - Document why permissions were granted

## Next Steps

Proceed to Exercise 04 to implement automated data quality validation.

## Additional Resources

- [Lake Formation Permissions](https://docs.aws.amazon.com/lake-formation/latest/dg/lake-formation-permissions.html)
- [Tag-Based Access Control](https://docs.aws.amazon.com/lake-formation/latest/dg/tag-based-access-control.html)
- [Data Filters](https://docs.aws.amazon.com/lake-formation/latest/dg/data-filters.html)
- Theory: `../theory/architecture.md` - Section 3: Lake Formation Permission Model
