# Data Catalog & Governance - AWS Architecture

## 1. Reference Architecture

### Complete Data Governance Platform

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Data Producers                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Applications  │  APIs  │  Batch Jobs  │  Stream Processors  │  Users   │
└───────┬──────────────────┬───────────────────┬────────────────┬─────────┘
        │                  │                   │                │
        ▼                  ▼                   ▼                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        AWS Lake Formation                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │              Centralized Access Control & Governance                 │  │
│  │  • Fine-grained permissions (database, table, column, row)          │  │
│  │  • Tag-based access control (TBAC)                                  │  │
│  │  │  • Cross-account sharing                                           │  │
│  │  • Audit logging with CloudTrail                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      AWS Glue Data Catalog                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │   Databases      │  │     Tables       │  │   Partitions     │        │
│  │  • analytics_db  │  │  • customers     │  │  • year=2024     │        │
│  │  • sales_db      │  │  • transactions  │  │  • month=03      │        │
│  │  • marketing_db  │  │  • products      │  │  • day=08        │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
│                                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        │
│  │    Crawlers      │  │   Classifiers    │  │   Connections    │        │
│  │  • Auto-discover │  │  • CSV, JSON     │  │  • RDS           │        │
│  │  • Schedule runs │  │  • Parquet, Avro │  │  • Redshift      │        │
│  │  • Update schema │  │  • Custom rules  │  │  • MongoDB       │        │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘        │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
        ┌─────────────────────┐  ┌──────────────┐  ┌──────────────────┐
        │    Data Storage     │  │  Compute     │  │   Analytics      │
        │  • S3 Data Lake     │  │  • Glue ETL  │  │  • Athena        │
        │  • RDS Databases    │  │  • EMR       │  │  • Redshift      │
        │  • DynamoDB         │  │  • Lambda    │  │  • QuickSight    │
        │  • Redshift         │  │  • Step Fn   │  │  • SageMaker     │
        └─────────────────────┘  └──────────────┘  └──────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │   Data Consumers      │
                            │  • Analytics Teams    │
                            │  • Data Scientists    │
                            │  • Business Users     │
                            │  • APIs & Apps        │
                            └───────────────────────┘
```

## 2. AWS Glue Data Catalog Architecture

### Catalog Organization

```
Data Catalog
│
├── Database: analytics_db
│   ├── Table: customer_transactions
│   │   ├── Schema: (transaction_id STRING, customer_id STRING, ...)
│   │   ├── Location: s3://data-lake/bronze/transactions/
│   │   ├── Format: Parquet
│   │   ├── Partitions:
│   │   │   ├── year=2024/month=01/
│   │   │   ├── year=2024/month=02/
│   │   │   └── year=2024/month=03/
│   │   ├── Statistics: (rowCount, sizeInBytes, lastAccessTime)
│   │   └── Tags: (Owner=FinanceTeam, Sensitivity=Confidential)
│   │
│   ├── Table: customer_profiles
│   └── Table: product_catalog
│
├── Database: sales_db
│   ├── Table: daily_sales
│   ├── Table: sales_targets
│   └── Table: sales_representatives
│
└── Database: marketing_db
    ├── Table: campaigns
    ├── Table: email_events
    └── Table: attribution_data
```

### Crawler Architecture

```
                    ┌─────────────────────────────┐
                    │   Scheduled Trigger         │
                    │   • Cron: 0 2 * * ? *       │
                    │   • On-demand               │
                    │   • Event-driven (S3)       │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │   AWS Glue Crawler          │
                    │   • Name: sales-crawler     │
                    │   • IAM Role: CrawlerRole   │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │   Data Source Targets       │
                    ├─────────────────────────────┤
                    │  S3: s3://lake/bronze/sales/│
                    │  RDS: prod-db.region.rds... │
                    │  DynamoDB: sales-table      │
                    └──────────────┬──────────────┘
                                   ▼
        ┌──────────────────────────┴──────────────────────────┐
        │              Crawler Execution                       │
        ├──────────────────────────────────────────────────────┤
        │  1. Connect to data source                           │
        │  2. Sample data (configurable percentage)            │
        │  3. Run classifiers (built-in + custom)              │
        │  4. Infer schema and partitions                      │
        │  5. Detect changes (new tables, columns, types)      │
        └──────────────────────────┬──────────────────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │   Schema Change Policy      │
                    ├─────────────────────────────┤
                    │  UpdateBehavior:            │
                    │   • UPDATE_IN_DATABASE      │
                    │   • LOG                     │
                    │                             │
                    │  DeleteBehavior:            │
                    │   • DELETE_FROM_DATABASE    │
                    │   • DEPRECATE_IN_DATABASE   │
                    │   • LOG                     │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │   Data Catalog Update       │
                    ├─────────────────────────────┤
                    │  • Create new tables        │
                    │  • Add new partitions       │
                    │  • Update table schema      │
                    │  • Update statistics        │
                    │  • Apply tags               │
                    └─────────────────────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │   Notifications             │
                    │   • CloudWatch Events       │
                    │   • SNS Topic               │
                    │   • Lambda Trigger          │
                    └─────────────────────────────┘
```

## 3. Lake Formation Permission Model

### Multi-Layer Security

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 1: IAM Policies                             │
│  • Basic AWS service access                                         │
│  • S3 bucket policies                                               │
│  • KMS encryption keys                                              │
└─────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 2: Lake Formation Data Location Permissions       │
│  • Register S3 locations with Lake Formation                        │
│  • Grant "DATA_LOCATION_ACCESS" permission                          │
│  • Required for any catalog table operations                        │
│                                                                      │
│  Resource: s3://data-lake/bronze/                                   │
│  Principal: arn:aws:iam::123456789012:role/AnalystRole             │
│  Permission: DATA_LOCATION_ACCESS                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 3: Lake Formation Catalog Permissions             │
│                                                                      │
│  Database Level:                                                    │
│  • CREATE_TABLE, ALTER, DROP, DESCRIBE                             │
│                                                                      │
│  Table Level:                                                       │
│  • SELECT, INSERT, DELETE, DESCRIBE, ALTER                          │
│                                                                      │
│  Column Level:                                                      │
│  • SELECT specific columns                                          │
│  • Exclude sensitive columns (PII)                                  │
│                                                                      │
│  Example:                                                           │
│  Database: sales_db                                                 │
│  Table: customer_transactions                                       │
│  Columns: [transaction_id, amount, date]                            │
│  Excluded: [ssn, credit_card, email]                                │
│  Principal: AnalystRole                                             │
│  Permission: SELECT                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 4: Lake Formation Data Filters                    │
│  • Row-level security                                               │
│  • Dynamic filtering based on session context                       │
│                                                                      │
│  Filter Name: regional-access-filter                                │
│  Table: sales_db.transactions                                       │
│  Expression: region = '${aws:PrincipalTag/Region}'                  │
│                                                                      │
│  Result: Users only see rows matching their assigned region         │
└─────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 5: Tag-Based Access Control (TBAC)                │
│  • Assign tags to resources                                         │
│  • Grant permissions based on tag matching                          │
│                                                                      │
│  LF-Tag: DataSensitivity                                            │
│  Values: [Public, Internal, Confidential, Restricted]               │
│                                                                      │
│  Policy:                                                            │
│  Principal: DataAnalystRole                                         │
│  Resource with tags: DataSensitivity = [Public, Internal]           │
│  Permission: SELECT, DESCRIBE                                       │
│                                                                      │
│  Benefit: Automatic permission inheritance for new resources        │
└─────────────────────────────────────────────────────────────────────┘
```

### Permission Resolution Flow

```
User Access Request (Athena query on sales_db.transactions)
    │
    ├─ Check IAM Policy ──────────────────→ Deny? → Access Denied
    │                                       Allow? ↓
    │
    ├─ Check Lake Formation ──────────────→ Deny? → Access Denied
    │  Data Location Permission             Allow? ↓
    │
    ├─ Check Lake Formation ──────────────→ Deny? → Access Denied
    │  Database Permission                  Allow? ↓
    │
    ├─ Check Lake Formation ──────────────→ Deny? → Access Denied
    │  Table Permission                     Allow? ↓
    │
    ├─ Check Lake Formation ──────────────→ Deny? → Access Denied
    │  Column Permission                    Allow? ↓
    │
    ├─ Apply Data Filters ────────────────→ Filter rows based on criteria
    │  (Row-level security)                        ↓
    │
    ├─ Check TBAC ────────────────────────→ Deny? → Access Denied
    │  (Tag-based access)                   Allow? ↓
    │
    └─→ Access Granted (with filtered data)
```

## 4. Data Lineage Architecture

### Lineage Capture Points

```
┌───────────────────────────────────────────────────────────────────────┐
│                         Source Systems                                 │
│  • S3 Data Lake    • RDS Databases    • DynamoDB    • API Sources     │
└─────────────────────────────┬─────────────────────────────────────────┘
                              │
                              ▼ (Lineage Point 1: Data Ingestion)
                  ┌───────────────────────────┐
                  │   AWS Glue Crawlers       │
                  │   • Discover sources      │
                  │   • Create catalog        │
                  └─────────────┬─────────────┘
                                │
                                ▼ (Lineage Point 2: ETL Processing)
                  ┌───────────────────────────┐
                  │   AWS Glue ETL Jobs       │
                  │   • Read from catalog     │
                  │   • Transform data        │
                  │   • Write to catalog      │
                  │                           │
                  │   Lineage captured:       │
                  │   • Input tables          │
                  │   • Output tables         │
                  │   • Transformations       │
                  │   • Job metadata          │
                  └─────────────┬─────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
        ┌────────────────┐ ┌─────────┐ ┌────────────────┐
        │ AWS Glue Data  │ │  EMR    │ │ Step Functions │
        │ Catalog Tables │ │ (Spark) │ │   Workflows    │
        └────────┬───────┘ └────┬────┘ └───────┬────────┘
                 │              │              │
                 └──────────────┼──────────────┘
                                │ (Lineage Point 3: Analytics)
                                ▼
                  ┌───────────────────────────┐
                  │   Analytics Services      │
                  │   • Amazon Athena         │
                  │   • Amazon Redshift       │
                  │   • Amazon QuickSight     │
                  │   • SageMaker             │
                  └─────────────┬─────────────┘
                                │
                                ▼ (Lineage Point 4: Consumption)
                  ┌───────────────────────────┐
                  │   Data Consumers          │
                  │   • BI Dashboards         │
                  │   • ML Models             │
                  │   • APIs                  │
                  │   • Reports               │
                  └───────────────────────────┘

                 All lineage tracked in:
            ┌──────────────────────────────────┐
            │   AWS Glue Data Lineage          │
            │   • DAG visualization            │
            │   • Upstream dependencies        │
            │   • Downstream impacts           │
            │   • Transformation details       │
            └──────────────────────────────────┘
```

### Lineage Data Model

```
┌───────────────────────────────────────────────────────────────┐
│                      Lineage Graph                             │
└───────────────────────────────────────────────────────────────┘

Source Table: raw_sales_data
    │
    │ consumed_by: glue_job_bronze_to_silver
    │ transformation: filter, deduplicate, type_cast
    │ timestamp: 2024-03-08T02:00:00Z
    │
    ▼
Intermediate Table: silver_sales_data
    │
    ├─ consumed_by: glue_job_daily_aggregation
    │  transformation: group_by, sum, average
    │  timestamp: 2024-03-08T03:00:00Z
    │  │
    │  ▼
    │  Output Table: daily_sales_summary
    │      │
    │      │ consumed_by: athena_query_sales_dashboard
    │      │ query: SELECT * FROM daily_sales_summary WHERE date = '2024-03-08'
    │      │ timestamp: 2024-03-08T09:15:23Z
    │      │
    │      ▼
    │      Dashboard: Sales Executive Dashboard (QuickSight)
    │
    └─ consumed_by: glue_job_customer_analytics
       transformation: join(customers), aggregate
       timestamp: 2024-03-08T04:00:00Z
       │
       ▼
       Output Table: customer_purchase_patterns
           │
           │ consumed_by: sagemaker_training_job_churn_model
           │ model: customer_churn_predictor_v2
           │ timestamp: 2024-03-08T10:30:00Z
           │
           ▼
           ML Model Endpoint: /predict-churn
```

## 5. Cross-Account Data Sharing

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    Producer Account (111111111111)               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              AWS Lake Formation (Producer)                  │ │
│  │                                                             │ │
│  │  Data Catalog:                                              │ │
│  │  • Database: shared_analytics_db                            │ │
│  │  • Tables: customer_data, transaction_data                  │ │
│  │                                                             │ │
│  │  Grant Permissions:                                         │ │
│  │  • Database: shared_analytics_db                            │ │
│  │  • Grantee: AWS Account 222222222222                        │ │
│  │  • Permissions: SELECT, DESCRIBE                            │ │
│  │  • Grant Option: True (allow re-sharing)                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              S3 Data Lake (Producer)                        │ │
│  │  Location: s3://producer-data-lake/                         │ │
│  │  • /bronze/customers/                                       │ │
│  │  • /bronze/transactions/                                    │ │
│  │                                                             │ │
│  │  Bucket Policy: Allow Lake Formation service                │ │
│  │  KMS Key Policy: Allow consumer account                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                         Cross-Account Grant
                         (Lake Formation)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Consumer Account (222222222222)               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              AWS Lake Formation (Consumer)                  │ │
│  │                                                             │ │
│  │  Accept Resource Share                                      │ │
│  │  • Create Resource Link to shared database                  │ │
│  │  • Grant permissions to local IAM roles/users               │ │
│  │                                                             │ │
│  │  Local Catalog:                                             │ │
│  │  • Database (Resource Link): shared_analytics_db            │ │
│  │    → Points to producer's database                          │ │
│  │                                                             │ │
│  │  Local Permissions:                                         │ │
│  │  • Principal: DataAnalystRole                               │ │
│  │  • Resource: Resource Link shared_analytics_db              │ │
│  │  • Permissions: SELECT, DESCRIBE                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         Analytics Services (Consumer)                       │ │
│  │  • Amazon Athena: Query shared tables                       │ │
│  │  • Amazon Redshift Spectrum: External tables                │ │
│  │  • AWS Glue ETL: Read and transform shared data             │ │
│  │  • Amazon QuickSight: Build dashboards                      │ │
│  │                                                             │ │
│  │  Data reads from: s3://producer-data-lake/                  │ │
│  │  (via Lake Formation permissions)                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Data Quality Architecture

### Quality Pipeline

```
┌───────────────────────────────────────────────────────────────────┐
│                      Data Ingestion                                │
│  S3 Landing Zone: s3://data-lake/landing/sales-data/               │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
                ┌──────────────────────────────┐
                │   EventBridge Rule           │
                │   Event: S3 ObjectCreated    │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   Lambda: Trigger Quality    │
                │   • Start Glue crawler       │
                │   • Start quality evaluation │
                └──────────────┬───────────────┘
                               ▼
        ┌──────────────────────────────────────────────┐
        │      AWS Glue Data Quality Evaluation        │
        ├──────────────────────────────────────────────┤
        │  Ruleset: sales-data-quality                 │
        │                                              │
        │  Rules:                                      │
        │  1. Completeness                             │
        │     - No null values in required columns     │
        │     - RowCount > 0                           │
        │                                              │
        │  2. Uniqueness                               │
        │     - Primary key uniqueness > 99.9%         │
        │     - No duplicate records                   │
        │                                              │
        │  3. Validity                                 │
        │     - Status in [valid_values]               │
        │     - Email matches regex                    │
        │     - Date ranges are logical                │
        │                                              │
        │  4. Consistency                              │
        │     - Foreign keys exist                     │
        │     - Totals match sum of details            │
        │                                              │
        │  5. Timeliness                               │
        │     - Data freshness < 24 hours              │
        │     - Timestamps within expected range       │
        └──────────────────┬───────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼ (Pass)                      ▼ (Fail)
┌────────────────────────┐    ┌────────────────────────┐
│  Move to Bronze Zone   │    │  Move to Quarantine    │
│  s3://lake/bronze/     │    │  s3://lake/quarantine/ │
│                        │    │                        │
│  • Update catalog      │    │  • Log failures        │
│  • Tag: quality=pass   │    │  • Send notifications  │
│  • Enable for use      │    │  • Create ticket       │
└────────┬───────────────┘    └────────┬───────────────┘
         │                              │
         ▼                              ▼
┌────────────────────────┐    ┌────────────────────────┐
│  CloudWatch Metrics    │    │  SNS Notification      │
│  • Quality score       │    │  • Data Engineers      │
│  • Rules passed/failed │    │  • Data Owners         │
│  • Data volume         │    │  • Incident ticket     │
└────────────────────────┘    └────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  QuickSight Dashboard                  │
│  • Quality trends over time            │
│  • Failed rules breakdown              │
│  • Data freshness monitoring           │
│  • Compliance reporting                │
└────────────────────────────────────────┘
```

## 7. Governed Tables Architecture

### Apache Iceberg Integration

```
┌───────────────────────────────────────────────────────────────────┐
│               Lake Formation Governed Tables                       │
│                    (Apache Iceberg Format)                         │
└───────────────────────────────────────────────────────────────────┘

Table Structure:
s3://data-lake/governed/customer_orders/
├── metadata/
│   ├── version-hint.text                  (Points to current version)
│   ├── v1.metadata.json                   (Table metadata version 1)
│   ├── v2.metadata.json                   (Table metadata version 2)
│   ├── v3.metadata.json                   (Current version)
│   └── snap-123456789-1.avro               (Snapshot manifest)
│
├── data/
│   ├── year=2024/month=01/
│   │   ├── data-file-001.parquet          (Immutable data file)
│   │   ├── data-file-002.parquet
│   │   └── delete-file-001.parquet        (Row-level deletes)
│   │
│   └── year=2024/month=02/
│       ├── data-file-003.parquet
│       └── data-file-004.parquet
│
└── manifests/
    ├── manifest-list-001.avro             (List of manifest files)
    └── manifest-002.avro                   (File-level metadata)

Features:

1. ACID Transactions
   ┌─────────────────────────────────────────────┐
   │  Transaction 1: INSERT new orders           │
   │  Transaction 2: UPDATE order status         │
   │  Transaction 3: DELETE cancelled orders     │
   │                                             │
   │  Isolation: Snapshot isolation              │
   │  Consistency: Serializable writes           │
   │  Durability: Atomic metadata updates        │
   └─────────────────────────────────────────────┘

2. Time Travel
   ┌─────────────────────────────────────────────┐
   │  SELECT * FROM customer_orders              │
   │  AS OF TIMESTAMP '2024-03-07 10:00:00'      │
   │                                             │
   │  SELECT * FROM customer_orders              │
   │  VERSION AS OF 'v2'                         │
   │                                             │
   │  Benefit: Query historical versions         │
   │  Use case: Debugging, auditing, rollback    │
   └─────────────────────────────────────────────┘

3. Schema Evolution
   ┌─────────────────────────────────────────────┐
   │  ALTER TABLE customer_orders                │
   │  ADD COLUMN shipping_address STRING         │
   │                                             │
   │  ALTER TABLE customer_orders                │
   │  CHANGE COLUMN status                       │
   │  TYPE STRING COMMENT 'Order status'         │
   │                                             │
   │  Benefit: Safe schema changes               │
   │  Backward compatible: Old queries still work│
   └─────────────────────────────────────────────┘

4. Automatic Compaction
   ┌─────────────────────────────────────────────┐
   │  Small files: 1000 files × 10 MB each       │
   │             ↓                               │
   │  Compaction: Automatic merge                │
   │             ↓                               │
   │  Large files: 10 files × 1 GB each          │
   │                                             │
   │  Benefit: Better query performance          │
   │  Trigger: Scheduled or automatic            │
   └─────────────────────────────────────────────┘

5. Incremental Reads
   ┌─────────────────────────────────────────────┐
   │  Read only new data since last checkpoint   │
   │                                             │
   │  SELECT * FROM customer_orders              │
   │  WHERE _change_type = 'INSERT'              │
   │  AND _commit_timestamp > '2024-03-07'       │
   │                                             │
   │  Benefit: Efficient incremental processing  │
   │  Use case: Streaming, CDC, incremental ETL  │
   └─────────────────────────────────────────────┘
```

## 8. Monitoring and Observability

### Comprehensive Monitoring

```
┌───────────────────────────────────────────────────────────────────┐
│                         CloudWatch Metrics                         │
├───────────────────────────────────────────────────────────────────┤
│  Glue Crawlers:                                                    │
│  • RunTime, TablesCreated, TablesUpdated, PartitionsCreated       │
│                                                                    │
│  Glue Jobs:                                                        │
│  • ExecutionTime, CPUUsage, MemoryUsage, DataShuffleSize          │
│                                                                    │
│  Lake Formation:                                                   │
│  • PermissionRequests, PermissionDenials, CrossAccountAccess      │
│                                                                    │
│  Data Quality:                                                     │
│  • QualityScore, RulesPassed, RulesFailed, DataFreshness          │
└───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                      CloudWatch Alarms                             │
├───────────────────────────────────────────────────────────────────┤
│  • Crawler failures > 2 in 24 hours                                │
│  • Data quality score < 95%                                        │
│  • Permission denials > threshold                                  │
│  • Data freshness > 24 hours                                       │
│  • Catalog table count anomaly                                     │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                      SNS Notifications                             │
│  • Send to data engineering team                                   │
│  • Create PagerDuty incident                                       │
│  • Post to Slack channel                                           │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                      CloudTrail Audit Logs                         │
├───────────────────────────────────────────────────────────────────┤
│  Log all API calls:                                                │
│  • GetTable, GetDatabase, GetTables                                │
│  • CreateTable, UpdateTable, DeleteTable                           │
│  • GrantPermissions, RevokePermissions                             │
│  • StartCrawler, UpdateCrawler                                     │
│                                                                    │
│  Analyze with Athena:                                              │
│  SELECT useridentity, eventname, COUNT(*)                          │
│  FROM cloudtrail_logs                                              │
│  WHERE eventsource = 'glue.amazonaws.com'                          │
│  GROUP BY useridentity, eventname                                  │
└───────────────────────────────────────────────────────────────────┘
```

## Key Architecture Principles

1. **Centralization**: Single Data Catalog for all data assets
2. **Fine-Grained Control**: Column and row-level permissions
3. **Automation**: Crawlers for metadata discovery
4. **Scalability**: Handle petabyte-scale data lakes
5. **Integration**: Works with Athena, Redshift, EMR, Glue
6. **Security**: Multiple layers of access control
7. **Compliance**: Audit logging and data lineage
8. **Quality**: Built-in data quality validation

## Next Steps

- Review `best-practices.md` for implementation guidelines
- Check `resources.md` for AWS documentation
- Begin with Exercise 01 to build a Data Catalog
