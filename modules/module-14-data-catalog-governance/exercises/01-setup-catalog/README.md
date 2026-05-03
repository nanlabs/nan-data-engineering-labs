# Exercise 01: Data Catalog Setup

## Objective

Learn to create and organize databases, tables, and metadata in AWS Glue Data Catalog using LocalStack.

## Prerequisites

- LocalStack running with Glue service enabled
- AWS CLI configured for LocalStack endpoint
- Sample sales transaction data available

## Learning Goals

- Create databases with proper naming conventions
- Define table schemas programmatically
- Add business metadata and tags
- Understand catalog organization patterns

## Exercise Tasks

### Task 1: Create Database Hierarchy

Create a three-tier database structure following the medallion architecture:

```bash
# 1. Create Bronze database
awslocal glue create-database \
    --database-input '{
        "Name": "dev_sales_bronze_db",
        "Description": "Bronze layer - Raw sales data from various sources",
        "LocationUri": "s3://training-data-lake/bronze/sales/",
        "Parameters": {
            "data_owner": "sales_team@company.com",
            "data_domain": "sales",
            "environment": "development",
            "cost_center": "CC-1001"
        }
    }'

# 2. Create Silver database
awslocal glue create-database \
    --database-input '{
        "Name": "dev_sales_silver_db",
        "Description": "Silver layer - Cleaned and validated sales data",
        "LocationUri": "s3://training-data-lake/silver/sales/",
        "Parameters": {
            "data_owner": "data_engineering@company.com",
            "data_domain": "sales",
            "data_quality_level": "95",
            "environment": "development",
            "cost_center": "CC-2002"
        }
    }'

# 3. Create Gold database
awslocal glue create-database \
    --database-input '{
        "Name": "dev_sales_gold_db",
        "Description": "Gold layer - Business-ready aggregated sales analytics",
        "LocationUri": "s3://training-data-lake/gold/sales/",
        "Parameters": {
            "data_owner": "analytics_team@company.com",
            "data_domain": "sales",
            "data_quality_level": "99",
            "sla_hours": "4",
            "environment": "development",
            "cost_center": "CC-3003"
        }
    }'

# Verify databases were created
awslocal glue get-databases
```

### Task 2: Create Bronze Table for Raw Data

Define a table schema for raw CSV sales transaction data:

```bash
# Create sales_transactions table in Bronze layer
awslocal glue create-table \
    --database-name dev_sales_bronze_db \
    --table-input '{
        "Name": "sales_transactions",
        "Description": "Raw retail transaction data from point-of-sale systems",
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "csv",
            "compressionType": "none",
            "data_owner": "sales_team@company.com",
            "update_frequency": "daily",
            "contains_pii": "true"
        },
        "PartitionKeys": [
            {"Name": "year", "Type": "string", "Comment": "Year from transaction date"},
            {"Name": "month", "Type": "string", "Comment": "Month from transaction date"},
            {"Name": "day", "Type": "string", "Comment": "Day from transaction date"}
        ],
        "StorageDescriptor": {
            "Columns": [
                {"Name": "date", "Type": "string", "Comment": "Transaction date"},
                {"Name": "transaction_id", "Type": "string", "Comment": "Unique transaction identifier"},
                {"Name": "customer_id", "Type": "string", "Comment": "Customer identifier"},
                {"Name": "product_id", "Type": "string", "Comment": "Product SKU"},
                {"Name": "category", "Type": "string", "Comment": "Product category"},
                {"Name": "quantity", "Type": "int", "Comment": "Number of items purchased"},
                {"Name": "unit_price", "Type": "double", "Comment": "Price per unit"},
                {"Name": "total_amount", "Type": "double", "Comment": "Total transaction amount"},
                {"Name": "payment_method", "Type": "string", "Comment": "Payment type"},
                {"Name": "store_location", "Type": "string", "Comment": "Store city and state"},
                {"Name": "region", "Type": "string", "Comment": "Geographic region"},
                {"Name": "customer_email", "Type": "string", "Comment": "Customer email (PII)"},
                {"Name": "customer_phone", "Type": "string", "Comment": "Customer phone (PII)"},
                {"Name": "shipping_address", "Type": "string", "Comment": "Shipping address (PII)"},
                {"Name": "status", "Type": "string", "Comment": "Transaction status"}
            ],
            "Location": "s3://training-data-lake/bronze/sales/transactions/",
            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            "Compressed": false,
            "NumberOfBuckets": 0,
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
                "Parameters": {
                    "field.delim": ",",
                    "skip.header.line.count": "1"
                }
            },
            "StoredAsSubDirectories": false
        }
    }'

# Verify table creation
awslocal glue get-table \
    --database-name dev_sales_bronze_db \
    --name sales_transactions
```

### Task 3: Create Silver Table with Enhanced Schema

Create a cleaned version table with proper data types and masked PII:

```bash
# Create sales_transactions_clean table in Silver layer
awslocal glue create-table \
    --database-name dev_sales_silver_db \
    --table-input '{
        "Name": "sales_transactions_clean",
        "Description": "Validated and cleaned sales transactions with masked PII",
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "parquet",
            "compressionType": "snappy",
            "data_owner": "data_engineering@company.com",
            "update_frequency": "daily",
            "contains_pii": "false",
            "data_quality_level": "95"
        },
        "PartitionKeys": [
            {"Name": "year", "Type": "string", "Comment": "Year from transaction date"},
            {"Name": "month", "Type": "string", "Comment": "Month from transaction date"}
        ],
        "StorageDescriptor": {
            "Columns": [
                {"Name": "date", "Type": "date", "Comment": "Transaction date"},
                {"Name": "transaction_id", "Type": "string", "Comment": "Unique transaction identifier"},
                {"Name": "customer_id", "Type": "string", "Comment": "Customer identifier"},
                {"Name": "product_id", "Type": "string", "Comment": "Product SKU"},
                {"Name": "category", "Type": "string", "Comment": "Product category"},
                {"Name": "quantity", "Type": "int", "Comment": "Number of items purchased"},
                {"Name": "unit_price", "Type": "decimal(10,2)", "Comment": "Price per unit"},
                {"Name": "total_amount", "Type": "decimal(10,2)", "Comment": "Total transaction amount"},
                {"Name": "payment_method", "Type": "string", "Comment": "Payment type"},
                {"Name": "store_location", "Type": "string", "Comment": "Store city and state"},
                {"Name": "region", "Type": "string", "Comment": "Geographic region"},
                {"Name": "customer_email_masked", "Type": "string", "Comment": "Masked customer email"},
                {"Name": "customer_phone_masked", "Type": "string", "Comment": "Masked phone number"},
                {"Name": "shipping_city", "Type": "string", "Comment": "Shipping city only"},
                {"Name": "shipping_state", "Type": "string", "Comment": "Shipping state"},
                {"Name": "shipping_zip", "Type": "string", "Comment": "Shipping ZIP code"},
                {"Name": "status", "Type": "string", "Comment": "Transaction status"},
                {"Name": "data_quality_score", "Type": "double", "Comment": "Quality validation score"},
                {"Name": "ingestion_timestamp", "Type": "timestamp", "Comment": "When data was processed"}
            ],
            "Location": "s3://training-data-lake/silver/sales/transactions/",
            "InputFormat": "org.apache.hadoop.mapred.SequenceFileInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat",
            "Compressed": true,
            "NumberOfBuckets": 0,
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                "Parameters": {
                    "serialization.format": "1"
                }
            },
            "StoredAsSubDirectories": false
        }
    }'
```

### Task 4: Create Gold Aggregation Table

Create a business-ready aggregated table:

```bash
# Create daily summary table in Gold layer
awslocal glue create-table \
    --database-name dev_sales_gold_db \
    --table-input '{
        "Name": "sales_daily_summary",
        "Description": "Daily aggregated sales metrics by region and category",
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "parquet",
            "compressionType": "snappy",
            "data_owner": "analytics_team@company.com",
            "update_frequency": "daily",
            "contains_pii": "false",
            "data_quality_level": "99",
            "certified": "true",
            "sla_hours": "4"
        },
        "PartitionKeys": [
            {"Name": "year", "Type": "string"},
            {"Name": "month", "Type": "string"}
        ],
        "StorageDescriptor": {
            "Columns": [
                {"Name": "date", "Type": "date", "Comment": "Summary date"},
                {"Name": "region", "Type": "string", "Comment": "Geographic region"},
                {"Name": "category", "Type": "string", "Comment": "Product category"},
                {"Name": "total_transactions", "Type": "bigint", "Comment": "Number of transactions"},
                {"Name": "total_revenue", "Type": "decimal(15,2)", "Comment": "Total revenue"},
                {"Name": "avg_transaction_value", "Type": "decimal(10,2)", "Comment": "Average transaction amount"},
                {"Name": "unique_customers", "Type": "bigint", "Comment": "Count of unique customers"},
                {"Name": "total_items_sold", "Type": "bigint", "Comment": "Total quantity sold"},
                {"Name": "completed_transactions", "Type": "bigint", "Comment": "Successful transactions"},
                {"Name": "completion_rate", "Type": "decimal(5,2)", "Comment": "Percentage completed"}
            ],
            "Location": "s3://training-data-lake/gold/sales/daily_summary/",
            "InputFormat": "org.apache.hadoop.mapred.SequenceFileInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat",
            "Compressed": true,
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                "Parameters": {"serialization.format": "1"}
            }
        }
    }'
```

### Task 5: Add Partitions

Add partition metadata to make data queryable:

```bash
# Upload sample data to S3
awslocal s3 cp ../../data/sample/sales-transactions.csv \
    s3://training-data-lake/bronze/sales/transactions/year=2024/month=03/day=08/

# Add partition to Bronze table
awslocal glue create-partition \
    --database-name dev_sales_bronze_db \
    --table-name sales_transactions \
    --partition-input '{
        "Values": ["2024", "03", "08"],
        "StorageDescriptor": {
            "Location": "s3://training-data-lake/bronze/sales/transactions/year=2024/month=03/day=08/",
            "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
            "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            "SerdeInfo": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
                "Parameters": {"field.delim": ","}
            }
        }
    }'

# Verify partition
awslocal glue get-partition \
    --database-name dev_sales_bronze_db \
    --table-name sales_transactions \
    --partition-values "2024" "03" "08"
```

### Task 6: Query the Catalog

Use Python Boto3 to query catalog metadata:

```python
# catalog_query.py
import boto3
import json

# Configure for LocalStack
glue = boto3.client(
    'glue',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# List all databases
databases = glue.get_databases()
print("\n=== Databases ===")
for db in databases['DatabaseList']:
    print(f"- {db['Name']}: {db['Description']}")
    if 'Parameters' in db:
        print(f"  Owner: {db['Parameters'].get('data_owner', 'N/A')}")
        print(f"  Quality Level: {db['Parameters'].get('data_quality_level', 'N/A')}")

# Get tables in Bronze database
tables = glue.get_tables(DatabaseName='dev_sales_bronze_db')
print("\n=== Bronze Tables ===")
for table in tables['TableList']:
    print(f"- {table['Name']}")
    print(f"  Columns: {len(table['StorageDescriptor']['Columns'])}")
    print(f"  Partitions: {len(table.get('PartitionKeys', []))}")
    print(f"  Location: {table['StorageDescriptor']['Location']}")
    print(f"  Contains PII: {table['Parameters'].get('contains_pii', 'N/A')}")

# Get table schema
table = glue.get_table(
    DatabaseName='dev_sales_bronze_db',
    Name='sales_transactions'
)
print("\n=== Table Schema: sales_transactions ===")
for col in table['Table']['StorageDescriptor']['Columns']:
    print(f"- {col['Name']:25} {col['Type']:15} # {col.get('Comment', '')}")

print("\n=== Partition Keys ===")
for pk in table['Table'].get('PartitionKeys', []):
    print(f"- {pk['Name']:10} {pk['Type']}")

# Get partitions
partitions = glue.get_partitions(
    DatabaseName='dev_sales_bronze_db',
    TableName='sales_transactions'
)
print(f"\n=== Partitions ({len(partitions['Partitions'])}) ===")
for partition in partitions['Partitions']:
    values = '/'.join(partition['Values'])
    location = partition['StorageDescriptor']['Location']
    print(f"- {values}: {location}")
```

Run the query script:
```bash
python catalog_query.py
```

## Validation

Test your catalog setup:

```bash
# Run the validation script
python validation_01.py
```

Expected results:
- ✅ 3 databases created (bronze, silver, gold)
- ✅ 3 tables created (one per layer)
- ✅ Bronze table has 15 columns and 3 partition keys
- ✅ Silver table has 19 columns and 2 partition keys
- ✅ Gold table has 10 aggregated columns
- ✅ At least 1 partition exists in bronze table
- ✅ All tables have proper metadata (owner, domain, quality level)

## Key Takeaways

1. **Naming Conventions**: Use `<env>_<domain>_<layer>_db` pattern
2. **Metadata Management**: Store business context in Parameters
3. **PII Tracking**: Mark tables containing sensitive data
4. **Partition Strategy**: Choose appropriate granularity (day vs month)
5. **Schema Evolution**: Use proper data types in Silver/Gold layers
6. **Storage Formats**: CSV for Bronze, Parquet for Silver/Gold

## Next Steps

Proceed to Exercise 02 to automate catalog updates with Glue Crawlers.

## Additional Resources

- [AWS Glue Data Catalog Documentation](https://docs.aws.amazon.com/glue/latest/dg/populate-data-catalog.html)
- [Boto3 Glue Client Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/glue.html)
- Theory: `../theory/concepts.md` - Section 2: AWS Glue Data Catalog
