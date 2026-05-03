# Exercise 05: Cross-Account Data Sharing

## Objective

Learn to securely share data between AWS accounts using Lake Formation cross-account grants and resource links.

## Prerequisites

- Exercises 01-04 completed
- Understanding of Lake Formation permissions
- Multiple AWS accounts or LocalStack account simulation

## Learning Goals

- Set up cross-account S3 bucket policies
- Configure Lake Formation for cross-account sharing
- Create resource links in consumer accounts
- Implement least-privilege access patterns
- Monitor and audit cross-account access

## Exercise Tasks

### Task 1: Configure Producer Account

Set up the data producer account (Account A: 111111111111):

```bash
# As Producer Account Admin

# 1. Register S3 location with Lake Formation
awslocal lakeformation register-resource \
    --resource-arn arn:aws:s3:::training-data-lake/gold/ \
    --use-service-linked-role

# 2. Enable cross-account version of catalog
awslocal glue put-data-catalog-encryption-settings \
    --data-catalog-encryption-settings '{
        "EncryptionAtRest": {
            "CatalogEncryptionMode": "SSE-KMS",
            "SseAwsKmsKeyId": "arn:aws:kms:us-east-1:111111111111:key/12345678"
        },
        "ConnectionPasswordEncryption": {
            "ReturnConnectionPasswordEncrypted": true,
            "AwsKmsKeyId": "arn:aws:kms:us-east-1:111111111111:key/12345678"
        }
    }'

# 3. Update S3 bucket policy to allow consumer account access
cat > /tmp/cross-account-bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowConsumerAccountRead",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:root"
      },
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::training-data-lake/gold/*",
        "arn:aws:s3:::training-data-lake/gold"
      ]
    }
  ]
}
EOF

awslocal s3api put-bucket-policy \
    --bucket training-data-lake \
    --policy file:///tmp/cross-account-bucket-policy.json
```

### Task 2: Grant Cross-Account Permissions

Producer grants access to consumer account:

```bash
# Grant database-level access to consumer account
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}' \
    --resource '{\"Database\":{\"Name\":\"dev_sales_gold_db\"}}' \
    --permissions DESCRIBE

# Grant table access
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}' \
    --resource '{
        \"Table\":{
            \"DatabaseName\":\"dev_sales_gold_db\",
            \"Name\":\"sales_daily_summary\"
        }
    }' \
    --permissions SELECT DESCRIBE \
    --permissions-with-grant-option DESCRIBE

# Grant access with column restrictions
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:role/ConsumerAnalyst\"}' \
    --resource '{
        \"TableWithColumns\":{
            \"DatabaseName\":\"dev_sales_gold_db\",
            \"Name\":\"sales_daily_summary\",
            \"ColumnNames\":[\"date\",\"region\",\"category\",\"total_revenue\",\"total_transactions\"]
        }
    }' \
    --permissions SELECT DESCRIBE

# Verify grants
awslocal lakeformation list-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}'
```

### Task 3: Set Up Consumer Account

Consumer account (Account B: 222222222222) creates resource links:

```bash
# As Consumer Account Admin

# 1. Create IAM role for data access
cat > /tmp/consumer-analyst-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "glue.amazonaws.com",
      "AWS": "arn:aws:iam::222222222222:root"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

awslocal iam create-role \
    --role-name ConsumerAnalyst \
    --assume-role-policy-document file:///tmp/consumer-analyst-trust.json

# 2. Create consumer database to hold resource links
awslocal glue create-database \
    --database-input '{
        "Name": "shared_sales_db",
        "Description": "Database containing resource links to producer account data",
        "Parameters": {
            "producer_account": "111111111111",
            "data_domain": "sales",
            "shared_by": "data-platform-team"
        }
    }'

# 3. Create resource link to producer's table
awslocal glue create-table \
    --database-name shared_sales_db \
    --table-input '{
        "Name": "sales_summary_link",
        "Description": "Resource link to producer sales_daily_summary table",
        "TableType": "RESOURCE_LINK",
        "TargetTable": {
            "CatalogId": "111111111111",
            "DatabaseName": "dev_sales_gold_db",
            "Name": "sales_daily_summary"
        },
        "Parameters": {
            "resource_link": "true",
            "producer_account": "111111111111"
        }
    }'

# 4. Grant local role access to resource link
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:role/ConsumerAnalyst\"}' \
    --resource '{\"Table\":{\"DatabaseName\":\"shared_sales_db\",\"Name\":\"sales_summary_link\"}}' \
    --permissions SELECT DESCRIBE

# Verify resource link
awslocal glue get-table \
    --database-name shared_sales_db \
    --name sales_summary_link
```

### Task 4: Query Shared Data

Consumer queries the shared data:

```python
# query_shared_data.py (Run in Consumer Account)
import boto3

# Consumer account credentials
athena = boto3.client(
    'athena',
    region_name='us-east-1'
    # Credentials for account 222222222222
)

# Query the resource link (transparently accesses producer data)
query = """
SELECT
    date,
    region,
    category,
    total_revenue,
    total_transactions
FROM shared_sales_db.sales_summary_link
WHERE year = '2024' AND month = '03'
ORDER BY total_revenue DESC
LIMIT 20
"""

# Execute query
response = athena.start_query_execution(
    QueryString=query,
    QueryExecutionContext={'Database': 'shared_sales_db'},
    ResultConfiguration={
        'OutputLocation': 's3://consumer-athena-results/'
    }
)

query_execution_id = response['QueryExecutionId']
print(f"Started query: {query_execution_id}")

# Wait for completion
import time
while True:
    status_response = athena.get_query_execution(
        QueryExecutionId=query_execution_id
    )
    status = status_response['QueryExecution']['Status']['State']

    if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        break
    time.sleep(2)

if status == 'SUCCEEDED':
    # Get results
    results = athena.get_query_results(
        QueryExecutionId=query_execution_id
    )

    print("\n=== Query Results ===")
    for row in results['ResultSet']['Rows'][:10]:
        values = [col.get('VarCharValue', '') for col in row['Data']]
        print(' | '.join(values))
else:
    print(f"Query failed: {status}")
```

### Task 5: Implement Tag-Based Cross-Account Sharing

Use LF-Tags for scalable sharing:

```bash
# Producer: Share all Gold tables with specific tags
awslocal lakeformation grant-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}' \
    --resource '{
        \"LFTagPolicy\":{
            \"ResourceType\":\"TABLE\",
            \"Expression\":[
                {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Gold\"]},
                {\"TagKey\":\"DataDomain\",\"TagValues\":[\"Sales\"]},
                {\"TagKey\":\"ShareApproved\",\"TagValues\":[\"true\"]}
            ]
        }
    }' \
    --permissions SELECT DESCRIBE

# Consumer: Accept tag-based grants
awslocal lakeformation list-permissions \
    --resource-type LF_TAG_POLICY \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}'
```

Benefits of tag-based sharing:

```python
# demonstrate_tbac_sharing.py
"""
Tag-Based Cross-Account Sharing Benefits:

1. Automatic Discovery:
   - New tables with matching tags automatically shared
   - No need to grant explicit permissions per table
   - Reduces administrative overhead

2. Centralized Governance:
   - Producer controls sharing via tagging policy
   - Easy to add/remove access by changing tags
   - Consistent security across all shared resources

3. Self-Service Data Discovery:
   - Consumers can discover available datasets via tags
   - Clear classification and ownership
   - Simplified data catalog navigation

4. Scalability:
   - Handles hundreds of tables efficiently
   - One grant covers current and future tables
   - Reduces Lake Formation permission limit issues
"""

import boto3

glue = boto3.client('glue')

# Consumer discovers available tables via tags
response = glue.search_tables(
    SearchText='Gold',
    ResourceShareType='FOREIGN'
)

print("=== Available Shared Tables ===")
for table in response['TableList']:
    print(f"- {table['DatabaseName']}.{table['Name']}")
    print(f"  Owner Account: {table.get('CatalogId')}")
    if 'Parameters' in table:
        for key, value in table['Parameters'].items():
            if 'tag' in key.lower() or 'domain' in key.lower():
                print(f"  {key}: {value}")
```

### Task 6: Monitor Cross-Account Access

Set up audit logging and monitoring:

```python
# monitor_cross_account_access.py
import boto3
from datetime import datetime, timedelta

cloudtrail = boto3.client('cloudtrail')

def audit_cross_account_access(days=7):
    """Audit cross-account Lake Formation access"""

    start_time = datetime.now() - timedelta(days=days)

    # Query CloudTrail for Lake Formation events
    response = cloudtrail.lookup_events(
        LookupAttributes=[
            {'AttributeKey': 'EventName', 'AttributeValue': 'GetQueryData'},
            {'AttributeKey': 'EventName', 'AttributeValue': 'GetTable'},
        ],
        StartTime=start_time
    )

    print(f"\n=== Cross-Account Access Audit (Last {days} days) ===\n")

    access_summary = {}

    for event in response['Events']:
        event_name = event['EventName']
        username = event.get('Username', 'Unknown')
        event_time = event['EventTime']

        # Parse event details
        import json
        details = json.loads(event['CloudTrailEvent'])

        # Check if cross-account
        caller_account = details.get('userIdentity', {}).get('accountId')
        resource_account = details.get('recipientAccountId')

        if caller_account != resource_account:
            key = f"{caller_account} → {resource_account}"
            if key not in access_summary:
                access_summary[key] = {'count': 0, 'users': set(), 'resources': set()}

            access_summary[key]['count'] += 1
            access_summary[key]['users'].add(username)

            # Extract resource info
            if 'requestParameters' in details:
                params = details['requestParameters']
                if 'databaseName' in params and 'tableName' in params:
                    resource = f"{params['databaseName']}.{params['tableName']}"
                    access_summary[key]['resources'].add(resource)

    # Display summary
    for accounts, stats in access_summary.items():
        print(f"\n{accounts}")
        print(f"  Total Accesses: {stats['count']}")
        print(f"  Unique Users: {len(stats['users'])}")
        print(f"  Users: {', '.join(list(stats['users'])[:5])}")
        print(f"  Resources Accessed:")
        for resource in list(stats['resources'])[:10]:
            print(f"    - {resource}")

# Run audit
audit_cross_account_access()
```

### Task 7: Revoke Cross-Account Access

Revoke permissions when no longer needed:

```bash
# Producer revokes table access
awslocal lakeformation revoke-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}' \
    --resource '{\"Table\":{\"DatabaseName\":\"dev_sales_gold_db\",\"Name\":\"sales_daily_summary\"}}' \
    --permissions SELECT DESCRIBE

# Producer revokes tag-based policy access
awslocal lakeformation revoke-permissions \
    --principal '{\"DataLakePrincipalIdentifier\":\"arn:aws:iam::222222222222:root\"}' \
    --resource '{
        \"LFTagPolicy\":{
            \"ResourceType\":\"TABLE\",
            \"Expression\":[
                {\"TagKey\":\"QualityLevel\",\"TagValues\":[\"Gold\"]}
            ]
        }
    }' \
    --permissions SELECT DESCRIBE

# Consumer deletes resource link
awslocal glue delete-table \
    --database-name shared_sales_db \
    --name sales_summary_link
```

## Validation

Test cross-account sharing:

```bash
python validation_05.py
```

Expected results:
- ✅ Producer S3 bucket policy allows consumer access
- ✅ Lake Formation cross-account grants configured
- ✅ Consumer resource links created successfully
- ✅ Consumer can query shared data via resource links
- ✅ Column-level restrictions enforced
- ✅ Tag-based sharing grants work for multiple tables
- ✅ Audit logs capture cross-account access
- ✅ Revocation prevents consumer access

## Key Takeaways

1. **Setup Requirements**: S3 bucket policy + Lake Formation grants + resource links
2. **Resource Links**: Consumer-side pointers to producer catalog
3. **Least Privilege**: Grant minimum necessary permissions
4. **Tag-Based Sharing**: Scalable for many tables
5. **Monitoring**: CloudTrail captures all cross-account access
6. **Revocation**: Producer maintains full control

## Next Steps

Proceed to Exercise 06 for end-to-end governance automation.

## Additional Resources

- [Cross-Account Access](https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-overview.html)
- [Resource Links](https://docs.aws.amazon.com/lake-formation/latest/dg/resource-links.html)
- Theory: `../theory/architecture.md` - Section 5: Cross-Account Data Sharing
