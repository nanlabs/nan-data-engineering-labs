# Data Catalog & Governance - Best Practices

## 1. Data Catalog Organization

### Database Naming Conventions

**Recommended Structure:**
```
<environment>_<domain>_<layer>_db

Examples:
- prod_sales_bronze_db
- prod_sales_silver_db
- prod_sales_gold_db
- dev_analytics_bronze_db
- staging_marketing_silver_db
```

**Benefits:**
- Clear environment separation
- Logical domain grouping
- Data lake layer identification
- Easy to understand and maintain

### Table Naming Conventions

**Recommended Structure:**
```
<domain>_<entity>_<version>

Examples:
- customer_transactions_v2
- product_catalog_v1
- sales_daily_summary_v3
```

**Guidelines:**
- Use lowercase with underscores
- Be descriptive but concise
- Include version for schema changes
- Avoid special characters
- Use singular for dimension tables, plural for fact tables

### Column Naming Standards

```python
# Good examples
customer_id          # Clear primary key
transaction_date     # Descriptive
total_amount_usd     # Includes unit
is_active           # Boolean prefix
created_at          # Timestamp suffix
updated_at          # Consistent naming

# Avoid
custID              # Abbreviated
TransactionDate     # CamelCase
amt                 # Unclear
active              # Not obviously boolean
creation            # Inconsistent with updated_at
```

## 2. Crawler Configuration Best Practices

### Scheduling Strategy

**Recommended Patterns:**

1. **Time-Based Scheduling**
   ```json
   {
     "Schedule": "cron(0 2 * * ? *)",
     "Description": "Daily at 2 AM UTC"
   }
   ```
   - Run during off-peak hours
   - After ETL jobs complete
   - Consider time zones

2. **Event-Driven Crawling**
   ```json
   {
     "EventBridgeRule": {
       "EventPattern": {
         "source": ["aws.s3"],
         "detail-type": ["Object Created"],
         "detail": {
           "bucket": {"name": ["data-lake"]},
           "object": {"key": [{"prefix": "bronze/sales/"}]}
         }
       }
     }
   }
   ```
   - Immediate metadata updates
   - Efficient for real-time needs
   - Reduces unnecessary crawls

3. **On-Demand Crawling**
   - Triggered by Step Functions
   - Part of ETL workflow
   - After manual data uploads

### Performance Optimization

**Partition Detection:**
```json
{
  "Configuration": {
    "Version": 1.0,
    "CrawlerOutput": {
      "Partitions": {
        "AddOrUpdateBehavior": "InheritFromTable"
      }
    },
    "Grouping": {
      "TableGroupingPolicy": "CombineCompatibleSchemas"
    }
  }
}
```

**Exclusion Patterns:**
```json
{
  "Exclusions": [
    "*/temp/*",
    "*/archive/*",
    "*/_spark_metadata/*",
    "*/_SUCCESS",
    "*.log",
    "*/_temporary/*"
  ]
}
```

**Sampling Configuration:**
```json
{
  "SampleSize": 100,
  "SamplePercentage": 5
}
```
- For large datasets, limit sampling
- Trade-off: Speed vs. accuracy
- 5-10% is typically sufficient

### Schema Change Handling

```json
{
  "SchemaChangePolicy": {
    "UpdateBehavior": "UPDATE_IN_DATABASE",
    "DeleteBehavior": "DEPRECATE_IN_DATABASE"
  }
}
```

**UpdateBehavior Options:**
- `UPDATE_IN_DATABASE`: Automatically update schema (recommended for bronze layer)
- `LOG`: Only log changes, don't update (recommended for gold layer)

**DeleteBehavior Options:**
- `DEPRECATE_IN_DATABASE`: Mark as deprecated (recommended)
- `DELETE_FROM_DATABASE`: Remove completely (use with caution)
- `LOG`: Only log deletion

## 3. Lake Formation Access Control

### Permission Hierarchy

**Principle:** Grant least privilege required

```
Level 1: Data Location (Required)
    ↓
Level 2: Database (Organizational)
    ↓
Level 3: Table (Workload-specific)
    ↓
Level 4: Column (Sensitive data)
    ↓
Level 5: Row Filter (Multi-tenancy)
```

### Role-Based Access Pattern

**Data Roles:**

1. **Data Engineers**
   ```json
   {
     "Principal": "arn:aws:iam::123456789012:role/DataEngineerRole",
     "Permissions": {
       "Database": ["CREATE_TABLE", "ALTER", "DROP"],
       "Table": ["SELECT", "INSERT", "DELETE", "ALTER"],
       "DataLocation": ["DATA_LOCATION_ACCESS"]
     }
   }
   ```

2. **Data Analysts**
   ```json
   {
     "Principal": "arn:aws:iam::123456789012:role/DataAnalystRole",
     "Permissions": {
       "Database": ["DESCRIBE"],
       "Table": ["SELECT", "DESCRIBE"],
       "Columns": ["customer_id", "name", "purchase_amount"]
     },
     "ExcludedColumns": ["ssn", "credit_card", "email"]
   }
   ```

3. **Data Scientists**
   ```json
   {
     "Principal": "arn:aws:iam::123456789012:role/DataScienceRole",
     "Permissions": {
       "Table": ["SELECT"],
       "RowFilter": "anonymized = true"
     }
   }
   ```

4. **External Partners**
   ```json
   {
     "Principal": "arn:aws:iam::234567890123:root",
     "Permissions": {
       "Table": ["SELECT"],
       "Columns": ["aggregated_metrics"],
       "RowFilter": "partner_id = '${aws:PrincipalTag/PartnerId}'"
     }
   }
   ```

### Tag-Based Access Control (TBAC)

**Define LF-Tags:**
```bash
# Create tags
aws lakeformation create-lf-tag \
  --tag-key DataSensitivity \
  --tag-values "Public,Internal,Confidential,Restricted"

aws lakeformation create-lf-tag \
  --tag-key DataDomain \
  --tag-values "Sales,Marketing,Finance,HR"

aws lakeformation create-lf-tag \
  --tag-key Environment \
  --tag-values "Dev,Test,Staging,Prod"
```

**Assign Tags to Resources:**
```bash
# Tag a database
aws lakeformation add-lf-tags-to-resource \
  --resource '{"Database":{"Name":"sales_db"}}' \
  --lf-tags '[{"TagKey":"DataDomain","TagValues":["Sales"]},
              {"TagKey":"DataSensitivity","TagValues":["Confidential"]}]'

# Tag a table
aws lakeformation add-lf-tags-to-resource \
  --resource '{"Table":{"DatabaseName":"sales_db","Name":"transactions"}}' \
  --lf-tags '[{"TagKey":"DataSensitivity","TagValues":["Restricted"]}]'
```

**Grant Permissions by Tags:**
```bash
aws lakeformation grant-permissions \
  --principal DataLakeAdministrator:arn:aws:iam::123456789012:role/AnalystRole \
  --resource '{"LFTag":{"TagKey":"DataSensitivity","TagValues":["Public","Internal"]}}' \
  --permissions SELECT DESCRIBE
```

**Benefits:**
- Automatic permission inheritance
- Simplified permission management
- Scalable for large catalogs
- Easier auditing and compliance

## 4. Data Quality Standards

### Quality Validation Rules

**Completeness Checks:**
```python
COMPLETENESS_RULES = [
    "ColumnValues 'customer_id' must be present",
    "ColumnValues 'email' completeness > 0.95",
    "RowCount > 0",
]
```

**Uniqueness Checks:**
```python
UNIQUENESS_RULES = [
    "ColumnValues 'transaction_id' uniqueness = 1.0",
    "ColumnValues 'customer_id' + 'order_date' uniqueness > 0.99",
]
```

**Validity Checks:**
```python
VALIDITY_RULES = [
    "ColumnValues 'email' matches '^[\\w.-]+@[\\w.-]+\\.\\w+$'",
    "ColumnValues 'status' in ['active', 'inactive', 'pending']",
    "ColumnValues 'amount' > 0",
    "ColumnValues 'created_at' <= current_timestamp",
]
```

**Consistency Checks:**
```python
CONSISTENCY_RULES = [
    "ColumnValues 'total_amount' = sum('line_item_amount')",
    "ColumnValues 'end_date' >= 'start_date'",
    "ColumnValues 'customer_id' exists in 'customers.customer_id'",
]
```

**Timeliness Checks:**
```python
TIMELINESS_RULES = [
    "ColumnValues 'updated_at' >= (current_timestamp - interval '24' hour)",
    "DataFreshness < 86400",  # Less than 24 hours old
]
```

### Quality Thresholds

**Define acceptable ranges:**
```python
QUALITY_THRESHOLDS = {
    "bronze": {
        "completeness": 0.90,        # 90% complete data
        "uniqueness": 0.95,           # 95% unique keys
        "validity": 0.85,             # 85% valid values
        "action": "warn"              # Warn but allow processing
    },
    "silver": {
        "completeness": 0.98,        # 98% complete data
        "uniqueness": 0.99,           # 99% unique keys
        "validity": 0.95,             # 95% valid values
        "action": "quarantine"        # Move to quarantine
    },
    "gold": {
        "completeness": 1.00,        # 100% complete data
        "uniqueness": 1.00,           # 100% unique keys
        "validity": 1.00,             # 100% valid values
        "action": "block"             # Block from gold layer
    }
}
```

### Automated Remediation

**Quality failure handling:**
```python
def handle_quality_failure(result, threshold):
    """Handle data quality failures based on layer and severity."""

    if result.score >= threshold["completeness"]:
        # Pass - move to next layer
        move_to_layer(result.data, next_layer)
        update_catalog(status="quality_passed")

    elif result.score >= threshold["completeness"] * 0.8:
        # Warning - process but flag
        move_to_layer(result.data, next_layer)
        send_notification("quality_warning", result.failed_rules)
        update_catalog(status="quality_warning")

    else:
        # Failure - quarantine
        move_to_quarantine(result.data)
        create_incident_ticket(result.failed_rules)
        send_notification("quality_failure", result.failed_rules)
        update_catalog(status="quality_failed")
```

## 5. Metadata Management

### Technical Metadata

**Always include:**
```json
{
  "table_metadata": {
    "source_system": "salesforce",
    "ingestion_method": "api_pull",
    "ingestion_frequency": "hourly",
    "data_format": "parquet",
    "compression": "snappy",
    "partition_keys": ["year", "month", "day"],
    "row_count": 1250000,
    "size_bytes": 45000000,
    "last_updated": "2024-03-08T14:30:00Z",
    "update_frequency": "daily",
    "retention_period_days": 2555
  }
}
```

### Business Metadata

**Document business context:**
```json
{
  "business_metadata": {
    "owner": "sales-team@company.com",
    "data_steward": "john.doe@company.com",
    "business_definition": "Daily sales transactions including order details and customer information",
    "use_cases": [
      "Sales reporting",
      "Revenue forecasting",
      "Customer segmentation"
    ],
    "sla": {
      "freshness": "4 hours",
      "availability": "99.9%",
      "quality_threshold": "98%"
    },
    "data_classification": "Confidential",
    "pii_fields": ["customer_email", "customer_phone"],
    "compliance": ["GDPR", "CCPA"]
  }
}
```

### Operational Metadata

**Track operational details:**
```json
{
  "operational_metadata": {
    "created_by": "data-ingestion-pipeline-v2",
    "created_at": "2024-01-15T10:00:00Z",
    "last_accessed_by": "analytics-team",
    "last_accessed_at": "2024-03-08T09:15:23Z",
    "access_count_30d": 15420,
    "avg_query_duration_ms": 3500,
    "downstream_dependencies": [
      "gold_sales_summary",
      "ml_customer_churn_model",
      "dashboard_executive_sales"
    ],
    "upstream_dependencies": [
      "salesforce_api",
      "product_catalog_db"
    ]
  }
}
```

## 6. Data Lineage Best Practices

### Capture Lineage Automatically

**In Glue ETL Jobs:**
```python
from awsglue.transforms import *
from awsglue.context import GlueContext

# Always use catalog integration for automatic lineage
source_df = glueContext.create_dynamic_frame.from_catalog(
    database="source_db",
    table_name="raw_sales",
    transformation_ctx="source_df"  # Important for lineage tracking
)

# Transform with named contexts
filtered_df = source_df.filter(
    f=lambda x: x["amount"] > 0,
    transformation_ctx="filter_invalid_amounts"
)

# Write with catalog integration
glueContext.write_dynamic_frame.from_catalog(
    frame=filtered_df,
    database="target_db",
    table_name="clean_sales",
    transformation_ctx="write_clean_sales"
)
```

### Document Transformations

**Add comments and descriptions:**
```python
# Document complex transformations
def calculate_customer_lifetime_value(df):
    """
    Calculate customer lifetime value (CLV).

    Formula: (Average Order Value) × (Purchase Frequency) × (Customer Lifespan)

    Lineage:
    - Input: silver_transactions, silver_customers
    - Output: gold_customer_metrics
    - Dependencies: date_dimension
    """
    return df.groupBy("customer_id").agg(
        sum("order_value").alias("total_value"),
        count("order_id").alias("order_count"),
        datediff(max("order_date"), min("order_date")).alias("customer_age_days")
    )
```

### Version Control Lineage

**Track schema versions:**
```json
{
  "lineage": {
    "source_table": "bronze_sales_v1",
    "target_table": "silver_sales_v2",
    "transformation": "deduplicate_and_enrich",
    "schema_version": {
      "input": "v1.2.0",
      "output": "v2.0.0"
    },
    "breaking_changes": [
      "Renamed column: 'cust_id' -> 'customer_id'",
      "Changed type: 'amount' from INTEGER to DECIMAL(10,2)",
      "Added column: 'currency_code'"
    ]
  }
}
```

## 7. Partition Strategy

### Partition Key Selection

**Choose based on query patterns:**

1. **Time-Based Partitioning** (Most Common)
   ```
   s3://data-lake/bronze/sales/year=2024/month=03/day=08/

   Pros:
   - Efficient for time-range queries
   - Natural data organization
   - Supports partition pruning

   Cons:
   - Can create too many small partitions
   - Inefficient for non-time queries
   ```

2. **Category-Based Partitioning**
   ```
   s3://data-lake/bronze/sales/region=us-west/product_category=electronics/

   Pros:
   - Good for analytical queries by category
   - Balanced partition sizes

   Cons:
   - Requires knowing categories upfront
   - Can have skewed partition sizes
   ```

3. **Hybrid Partitioning**
   ```
   s3://data-lake/bronze/sales/date=2024-03-08/region=us-west/

   Pros:
   - Combines benefits of multiple strategies
   - Flexible query patterns

   Cons:
   - More complex management
   - Deeper directory structure
   ```

### Partition Size Guidelines

```
Optimal partition sizes:
- Minimum: 128 MB per partition
- Maximum: 1 GB per partition
- Target: 256-512 MB per partition

Number of partitions:
- Minimum: At least 1 partition
- Maximum: < 10,000 partitions per table
- Target: 100-1,000 partitions for most tables
```

**Anti-Patterns:**
```
# Too many partitions (avoid)
year=2024/month=03/day=08/hour=14/minute=30/second=15/

# Too few partitions (avoid)
year=2024/

# Just right
year=2024/month=03/day=08/
```

## 8. Security Best Practices

### Encryption

**At Rest:**
```json
{
  "Encryption": {
    "S3": {
      "SSEAlgorithm": "aws:kms",
      "KMSKeyId": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    },
    "CatalogEncryption": {
      "EncryptionAtRest": {
        "CatalogEncryptionMode": "SSE-KMS",
        "SseAwsKmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/catalog-key"
      }
    }
  }
}
```

**In Transit:**
```json
{
  "SecurityConfiguration": {
    "EncryptionConfiguration": {
      "JobBookmarksEncryption": {
        "JobBookmarksEncryptionMode": "CSE-KMS",
        "KmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/job-bookmark-key"
      },
      "S3Encryption": [
        {
          "S3EncryptionMode": "SSE-KMS",
          "KmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/s3-key"
        }
      ]
    }
  }
}
```

### Access Logging

**Enable logging everywhere:**
```json
{
  "Logging": {
    "S3": {
      "LoggingEnabled": true,
      "TargetBucket": "audit-logs-bucket",
      "TargetPrefix": "s3-access-logs/"
    },
    "CloudTrail": {
      "EventSelectors": [
        {
          "ReadWriteType": "All",
          "IncludeManagementEvents": true,
          "DataResources": [
            {
              "Type": "AWS::Glue::Table",
              "Values": ["arn:aws:glue:*:*:table/*/*"]
            }
          ]
        }
      ]
    }
  }
}
```

### PII Handling

**Detection and masking:**
```python
from awsglue.transforms import Map

def mask_pii(record):
    """Mask PII fields based on user role."""

    # Mask email: john.doe@example.com -> j***@example.com
    if 'email' in record:
        email_parts = record['email'].split('@')
        record['email'] = f"{email_parts[0][0]}***@{email_parts[1]}"

    # Mask phone: +1-555-123-4567 -> +1-555-***-****
    if 'phone' in record:
        record['phone'] = record['phone'][:8] + '***-****'

    # Hash SSN
    if 'ssn' in record:
        import hashlib
        record['ssn'] = hashlib.sha256(record['ssn'].encode()).hexdigest()

    return record

# Apply masking
masked_df = Map.apply(
    frame=source_df,
    f=mask_pii,
    transformation_ctx="mask_pii_fields"
)
```

## 9. Cost Optimization

### Crawler Optimization

**Reduce crawler costs:**
```
1. Use exclusion patterns to skip unnecessary paths
2. Schedule crawlers during off-peak hours
3. Use event-driven crawling instead of frequent schedules
4. Group similar tables with CombineCompatibleSchemas
5. Limit sample size for large datasets
6. Disable crawlers for static datasets
```

### Storage Optimization

**Table storage:**
```
1. Use Parquet or ORC instead of JSON/CSV (5-10x compression)
2. Enable compression (Snappy, GZIP, Zstandard)
3. Partition data appropriately (avoid over-partitioning)
4. Use Glue governed tables for automatic compaction
5. Implement lifecycle policies (S3 Intelligent-Tiering)
6. Delete outdated partitions regularly
```

### Query Optimization

**Reduce query costs:**
```sql
-- Use partition filters (reduces data scanned)
SELECT * FROM sales
WHERE year = '2024' AND month = '03' AND day = '08'

-- Select only needed columns (columnar format benefit)
SELECT transaction_id, amount, customer_id
FROM sales
WHERE year = '2024'

-- Use CTAS for frequently accessed aggregations
CREATE TABLE sales_summary AS
SELECT date, SUM(amount) as total_sales
FROM sales
GROUP BY date;
```

## 10. Monitoring and Alerting

### Key Metrics to Track

**Catalog Health:**
```
- Table count and growth rate
- Tables without recent updates (stale data)
- Crawler success/failure rate
- Crawler duration trends
- Schema change frequency
```

**Data Quality:**
```
- Overall quality score by database/table
- Failed rules by category (completeness, validity, etc.)
- Data freshness (time since last update)
- Row count anomalies (sudden drops/spikes)
- Partition imbalance (skewed sizes)
```

**Access Patterns:**
```
- Most/least accessed tables
- Permission denial rate
- Cross-account access frequency
- Query performance (duration, scanned bytes)
- Concurrent query count
```

**Cost Metrics:**
```
- Crawler execution costs
- Storage costs by database
- Query costs (Athena, Redshift Spectrum)
- Data transfer costs
```

### Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "crawler_failure_rate": {
        "warning": 0.05,   # 5% failure rate
        "critical": 0.10   # 10% failure rate
    },
    "data_freshness_hours": {
        "warning": 24,     # Data older than 24 hours
        "critical": 48     # Data older than 48 hours
    },
    "quality_score": {
        "warning": 0.95,   # Quality score below 95%
        "critical": 0.90   # Quality score below 90%
    },
    "permission_denials": {
        "warning": 100,    # 100 denials per day
        "critical": 500    # 500 denials per day
    }
}
```

## Key Takeaways

1. **Organization**: Use consistent naming conventions for databases, tables, and columns
2. **Automation**: Configure crawlers with appropriate schedules and exclusions
3. **Security**: Implement fine-grained permissions with Lake Formation
4. **Quality**: Define and enforce data quality rules at each layer
5. **Metadata**: Capture technical, business, and operational metadata
6. **Lineage**: Track data flow automatically through catalog integration
7. **Partitioning**: Choose partition strategy based on query patterns
8. **Encryption**: Enable encryption at rest and in transit
9. **Cost**: Optimize crawler runs, storage formats, and queries
10. **Monitoring**: Track key metrics and set up appropriate alerts

## Next Steps

- Review `resources.md` for additional documentation
- Begin Exercise 01 to implement these best practices
- Set up monitoring dashboards for your catalog
