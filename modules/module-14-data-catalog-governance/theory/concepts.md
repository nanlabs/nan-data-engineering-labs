# Data Catalog & Governance - Core Concepts

## 1. Introduction to Data Governance

### What is Data Governance?

Data governance is the overall management of data availability, usability, integrity, and security in an organization. It establishes processes and responsibilities that ensure quality and security of the data used across an organization.

**Key Principles:**
- **Accountability**: Clear ownership of data assets
- **Transparency**: Documented data lineage and transformations
- **Integrity**: Accurate, consistent, and trustworthy data
- **Security**: Protected access to sensitive information
- **Compliance**: Adherence to regulations (GDPR, HIPAA, SOC2)
- **Quality**: Validation rules and monitoring

### Why Data Governance Matters

1. **Regulatory Compliance**: Meet legal requirements (GDPR, CCPA, HIPAA)
2. **Data Quality**: Ensure accuracy and consistency
3. **Risk Management**: Reduce data breaches and errors
4. **Efficiency**: Reduce time spent searching for data
5. **Trust**: Build confidence in data-driven decisions
6. **Cost Optimization**: Avoid duplicate storage and processing

## 2. AWS Glue Data Catalog

### Overview

The AWS Glue Data Catalog is a centralized metadata repository that stores structural and operational metadata for all your data assets. It acts as a persistent technical metadata store for your data lake.

**Key Components:**

1. **Databases**: Logical grouping of tables
2. **Tables**: Metadata definitions (schema, location, format)
3. **Partitions**: Subdivisions of table data
4. **Crawlers**: Automatic metadata discovery
5. **Classifiers**: Rules to infer schema and format
6. **Connections**: Database and data store connection information

### Table Metadata

Each table in the Data Catalog contains:

```json
{
  "Name": "sales_transactions",
  "DatabaseName": "analytics_db",
  "Owner": "data-team",
  "CreateTime": "2024-01-15T10:30:00Z",
  "UpdateTime": "2024-03-08T14:25:00Z",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "transaction_id", "Type": "string"},
      {"Name": "customer_id", "Type": "string"},
      {"Name": "amount", "Type": "decimal(10,2)"},
      {"Name": "transaction_date", "Type": "date"}
    ],
    "Location": "s3://data-lake/bronze/sales/",
    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
    "SerdeInfo": {
      "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
      "Parameters": {
        "field.delim": ",",
        "serialization.format": ","
      }
    }
  },
  "PartitionKeys": [
    {"Name": "year", "Type": "string"},
    {"Name": "month", "Type": "string"},
    {"Name": "day", "Type": "string"}
  ],
  "TableType": "EXTERNAL_TABLE"
}
```

### Crawlers

Crawlers automatically discover and catalog data:

**Crawler Process:**
1. **Connect**: Access data store (S3, RDS, DynamoDB, JDBC)
2. **Scan**: Read sample data to infer schema
3. **Classify**: Determine format (JSON, CSV, Parquet, Avro)
4. **Create/Update**: Add or modify table metadata
5. **Partition**: Detect partition scheme (year/month/day)

**Crawler Configuration:**
```json
{
  "Name": "sales-data-crawler",
  "Role": "arn:aws:iam::123456789012:role/GlueCrawlerRole",
  "Targets": {
    "S3Targets": [
      {
        "Path": "s3://data-lake/bronze/sales/",
        "Exclusions": ["*/temp/*", "*/archive/*"]
      }
    ]
  },
  "DatabaseName": "analytics_db",
  "Schedule": "cron(0 2 * * ? *)",
  "SchemaChangePolicy": {
    "UpdateBehavior": "UPDATE_IN_DATABASE",
    "DeleteBehavior": "LOG"
  },
  "Configuration": "{\"Version\":1.0,\"CrawlerOutput\":{\"Partitions\":{\"AddOrUpdateBehavior\":\"InheritFromTable\"}}}"
}
```

### Classifiers

Classifiers determine the schema of your data:

**Built-in Classifiers (in order):**
1. Apache Avro
2. Apache Parquet
3. Apache ORC
4. JSON
5. Binary JSON (BSON)
6. XML
7. CSV
8. Apache Log formats

**Custom Classifiers:**
```json
{
  "Name": "custom-csv-classifier",
  "CsvClassifier": {
    "Delimiter": "|",
    "QuoteSymbol": "\"",
    "ContainsHeader": "PRESENT",
    "Header": ["id", "name", "email", "created_at"],
    "DisableValueTrimming": false,
    "AllowSingleColumn": false
  }
}
```

## 3. AWS Lake Formation

### Overview

AWS Lake Formation simplifies building, securing, and managing data lakes. It provides centralized governance, fine-grained access control, and data discoverability.

**Key Features:**

1. **Centralized Permissions**: Grant/revoke access at database, table, column level
2. **Data Filters**: Row-level and cell-level security
3. **Governed Tables**: ACID transactions, time travel, compaction
4. **Cross-Account Sharing**: Share catalogs across AWS accounts
5. **Blueprints**: Pre-built workflows for data ingestion
6. **Data Lineage**: Track data flow and transformations

### Permission Model

Lake Formation implements a layered permission model:

**Permission Types:**

1. **Data Location Permissions**: Access to S3 paths
   ```json
   {
     "DataLocationResource": {
       "S3Resource": "s3://data-lake/bronze/"
     },
     "Permissions": ["DATA_LOCATION_ACCESS"]
   }
   ```

2. **Database Permissions**: Create/drop tables in database
   ```json
   {
     "DatabaseResource": {
       "Name": "analytics_db"
     },
     "Permissions": ["CREATE_TABLE", "ALTER", "DROP"]
   }
   ```

3. **Table Permissions**: Select/insert/delete data
   ```json
   {
     "TableResource": {
       "DatabaseName": "analytics_db",
       "Name": "customer_data"
     },
     "Permissions": ["SELECT", "INSERT", "DELETE"],
     "PermissionsWithGrantOption": []
   }
   ```

4. **Column Permissions**: Fine-grained column access
   ```json
   {
     "TableWithColumnsResource": {
       "DatabaseName": "analytics_db",
       "Name": "customer_data",
       "ColumnNames": ["customer_id", "name", "email"]
     },
     "Permissions": ["SELECT"]
   }
   ```

### Data Filters (Row-Level Security)

Create filters to restrict access to specific rows:

```json
{
  "Name": "regional-sales-filter",
  "TableCatalogId": "123456789012",
  "DatabaseName": "sales_db",
  "TableName": "transactions",
  "RowFilter": {
    "FilterExpression": "region = 'US-WEST'"
  }
}
```

**Use Cases:**
- Regional data segregation
- Multi-tenant data isolation
- Time-based access control
- Role-based data visibility

### Governed Tables

Governed tables provide ACID transactions and automatic optimization:

**Features:**
- **ACID Transactions**: Full transaction support
- **Time Travel**: Query historical versions
- **Automatic Compaction**: Optimize small files
- **Schema Evolution**: Add/modify columns safely

**Creating a Governed Table:**
```sql
CREATE TABLE analytics_db.customer_orders (
  order_id STRING,
  customer_id STRING,
  order_date DATE,
  amount DECIMAL(10,2),
  status STRING
)
USING ICEBERG
LOCATION 's3://data-lake/governed/customer_orders/'
TBLPROPERTIES (
  'table_type'='GOVERNED',
  'format-version'='2'
);
```

## 4. Metadata Management

### Metadata Types

1. **Technical Metadata**
   - Schema (column names, data types)
   - Storage format (Parquet, JSON, CSV)
   - Location (S3 path, database connection)
   - Partitions and indexes
   - Statistics (row count, file size)

2. **Business Metadata**
   - Data owner and steward
   - Business definitions
   - Data quality rules
   - Sensitivity classification
   - Retention policies

3. **Operational Metadata**
   - Create/update timestamps
   - Last access time
   - ETL job information
   - Data lineage
   - Access logs

### Tags and Classification

**AWS Glue Tags:**
```json
{
  "ResourceArn": "arn:aws:glue:us-east-1:123456789012:table/sales_db/transactions",
  "TagsToAdd": {
    "DataClassification": "Confidential",
    "Owner": "FinanceTeam",
    "Environment": "Production",
    "PII": "True",
    "RetentionPeriod": "7years",
    "ComplianceRequirement": "SOX"
  }
}
```

**Lake Formation Tags (LF-Tags):**
```json
{
  "CatalogId": "123456789012",
  "TagKey": "DataSensitivity",
  "TagValues": ["Public", "Internal", "Confidential", "Restricted"]
}
```

**Tag-Based Access Control (TBAC):**
```json
{
  "Resource": {
    "LFTag": {
      "CatalogId": "123456789012",
      "TagKey": "DataSensitivity",
      "TagValues": ["Public", "Internal"]
    }
  },
  "Permissions": ["SELECT", "DESCRIBE"]
}
```

## 5. Data Lineage

### What is Data Lineage?

Data lineage tracks the flow of data from source to destination, including all transformations applied along the way.

**Benefits:**
- **Impact Analysis**: Understand downstream effects of changes
- **Root Cause Analysis**: Trace data quality issues to source
- **Compliance**: Demonstrate data handling for audits
- **Documentation**: Automatic documentation of data flows
- **Optimization**: Identify redundant transformations

### Lineage Components

1. **Data Sources**: Where data originates
2. **Transformations**: How data is modified
3. **Data Targets**: Where data is stored/consumed
4. **Dependencies**: Relationships between datasets
5. **Jobs/Pipelines**: Processes that move/transform data

### Capturing Lineage

**AWS Glue Job Lineage:**
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from catalog (lineage captured automatically)
source_df = glueContext.create_dynamic_frame.from_catalog(
    database="source_db",
    table_name="raw_orders"
)

# Transform
transformed_df = source_df.filter(lambda x: x["status"] == "completed")

# Write to catalog (lineage captured automatically)
glueContext.write_dynamic_frame.from_catalog(
    frame=transformed_df,
    database="target_db",
    table_name="completed_orders"
)

job.commit()
```

## 6. Data Discovery

### Search and Discovery

**AWS Glue Data Catalog Search:**
```python
import boto3

glue = boto3.client('glue')

# Search tables by name pattern
response = glue.search_tables(
    CatalogId='123456789012',
    Filters=[
        {
            'Key': 'TABLE_NAME',
            'Value': 'customer*',
            'Comparator': 'BEGINS_WITH'
        }
    ]
)

# Search by tag
response = glue.search_tables(
    CatalogId='123456789012',
    ResourceShareType='ALL',
    Filters=[
        {
            'Key': 'TAG',
            'Value': 'DataSensitivity=Confidential'
        }
    ]
)
```

### Data Catalog Federation

**Query External Catalogs:**
- AWS Glue Data Catalog
- Apache Hive Metastore
- Amazon Redshift
- AWS Lake Formation
- Third-party catalogs

**Federated Query Example:**
```sql
-- Query across catalogs
SELECT
    glue.sales.transaction_id,
    redshift.customers.customer_name,
    glue.products.product_name
FROM
    glue_catalog.sales_db.transactions AS glue.sales
JOIN
    redshift_catalog.public.customers AS redshift.customers
    ON glue.sales.customer_id = redshift.customers.customer_id
JOIN
    glue_catalog.product_db.products AS glue.products
    ON glue.sales.product_id = glue.products.product_id
WHERE
    glue.sales.transaction_date >= CURRENT_DATE - INTERVAL '30' DAY;
```

## 7. Data Quality and Validation

### Data Quality Rules

**AWS Glue Data Quality:**
```json
{
  "RulesetName": "customer-data-quality",
  "TargetTable": {
    "DatabaseName": "crm_db",
    "TableName": "customers"
  },
  "Rules": [
    {
      "Name": "completeness-check",
      "Description": "Ensure required fields are populated",
      "Rule": "ColumnValues \"email\" matches \"^[\\w.-]+@[\\w.-]+\\.\\w+$\""
    },
    {
      "Name": "uniqueness-check",
      "Description": "Customer ID must be unique",
      "Rule": "ColumnValues \"customer_id\" uniqueness > 0.99"
    },
    {
      "Name": "timeliness-check",
      "Description": "Data must be recent",
      "Rule": "ColumnValues \"last_updated\" >= (current_timestamp - interval '7' day)"
    },
    {
      "Name": "validity-check",
      "Description": "Status must be valid value",
      "Rule": "ColumnValues \"status\" in [\"active\", \"inactive\", \"suspended\"]"
    },
    {
      "Name": "consistency-check",
      "Description": "Total amount must match sum of line items",
      "Rule": "ColumnValues \"total_amount\" = sum(\"line_item_amount\")"
    }
  ]
}
```

### Data Profiling

Automatically analyze data characteristics:

```python
import boto3

glue = boto3.client('glue')

# Start data quality evaluation
response = glue.start_data_quality_ruleset_evaluation_run(
    DataSource={
        'GlueTable': {
            'DatabaseName': 'analytics_db',
            'TableName': 'sales_data'
        }
    },
    RulesetNames=['sales-quality-rules'],
    Role='arn:aws:iam::123456789012:role/GlueDataQualityRole'
)

run_id = response['RunId']

# Get results
results = glue.get_data_quality_ruleset_evaluation_run(
    RunId=run_id
)

print(f"Status: {results['Status']}")
print(f"Started: {results['StartedOn']}")
print(f"Completed: {results['CompletedOn']}")
print(f"Rules Passed: {results['ResultIds']}")
```

## 8. Compliance and Security

### Data Classification

**Sensitivity Levels:**
1. **Public**: Can be shared freely
2. **Internal**: For organizational use only
3. **Confidential**: Restricted access required
4. **Restricted**: Highest protection (PII, PHI, PCI)

### PII Detection

**AWS Glue Sensitive Data Detection:**
```python
import boto3

glue = boto3.client('glue')

# Detect PII in tables
response = glue.create_classifier(
    Name='pii-classifier',
    CsvClassifier={
        'ContainsHeader': 'PRESENT',
        'Delimiter': ',',
        'QuoteSymbol': '"',
        'DisableValueTrimming': False
    }
)

# Run crawler with PII detection
glue.start_crawler(
    Name='pii-detection-crawler'
)
```

### Audit Logging

**CloudTrail Integration:**
- Track all Data Catalog API calls
- Monitor Lake Formation permission changes
- Log data access patterns
- Detect anomalous behavior

**Example Audit Query:**
```sql
SELECT
    eventTime,
    userIdentity.principalId,
    eventName,
    requestParameters.databaseName,
    requestParameters.tableName,
    sourceIPAddress
FROM
    cloudtrail_logs
WHERE
    eventSource = 'glue.amazonaws.com'
    AND eventName IN ('GetTable', 'GetTables', 'GetDatabase')
    AND eventTime > CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY
    eventTime DESC;
```

## Key Takeaways

1. **Data Governance** is essential for managing data as a strategic asset
2. **AWS Glue Data Catalog** provides centralized metadata management
3. **Lake Formation** enables fine-grained access control and governance
4. **Metadata Management** includes technical, business, and operational metadata
5. **Data Lineage** tracks data flow and transformations
6. **Data Discovery** helps users find and understand available data
7. **Data Quality** ensures accuracy and reliability
8. **Compliance** requires classification, auditing, and access controls

## Next Steps

- Read `architecture.md` for AWS service architecture
- Review `best-practices.md` for implementation guidelines
- Check `resources.md` for additional learning materials
- Start with Exercise 01 to apply these concepts
