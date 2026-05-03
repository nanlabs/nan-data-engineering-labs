# Data Catalog & Governance Architecture Diagrams

This document contains architectural diagrams for AWS Glue Data Catalog and Lake Formation using Mermaid syntax.

## 1. Complete Data Governance Platform

```mermaid
graph TB
    subgraph "Data Producers"
        Apps[Applications]
        APIs[APIs]
        Batch[Batch Jobs]
        Stream[Stream Processors]
    end

    subgraph "AWS Lake Formation"
        LF[Lake Formation]
        FGAC[Fine-Grained Access Control]
        TBAC[Tag-Based Access Control]
        XAcct[Cross-Account Sharing]
        Audit[Audit Logging]
    end

    subgraph "AWS Glue Data Catalog"
        Catalog[Data Catalog]
        DB[Databases]
        Tables[Tables]
        Parts[Partitions]
        Crawlers[Crawlers]
        Class[Classifiers]
        Conn[Connections]
    end

    subgraph "Data Storage"
        S3[S3 Data Lake]
        RDS[(RDS Databases)]
        DDB[(DynamoDB)]
        RS[(Redshift)]
    end

    subgraph "Compute & Analytics"
        Glue[AWS Glue ETL]
        EMR[Amazon EMR]
        Lambda[AWS Lambda]
        Athena[Amazon Athena]
        QS[QuickSight]
        SM[SageMaker]
    end

    subgraph "Data Consumers"
        Analysts[Data Analysts]
        DS[Data Scientists]
        BU[Business Users]
        ConsumerAPI[Consumer APIs]
    end

    Apps --> LF
    APIs --> LF
    Batch --> LF
    Stream --> LF

    LF --> FGAC
    LF --> TBAC
    LF --> XAcct
    LF --> Audit

    LF --> Catalog
    Catalog --> DB
    Catalog --> Tables
    Catalog --> Parts
    Catalog --> Crawlers
    Catalog --> Class
    Catalog --> Conn

    Crawlers --> S3
    Crawlers --> RDS
    Crawlers --> DDB
    Crawlers --> RS

    Catalog --> Glue
    Catalog --> EMR
    Catalog --> Lambda
    Catalog --> Athena
    Catalog --> QS
    Catalog --> SM

    Athena --> Analysts
    QS --> BU
    SM --> DS
    Glue --> ConsumerAPI

    style LF fill:#FF9900
    style Catalog fill:#FF9900
    style S3 fill:#569A31
    style Athena fill:#8C4FFF
```

## 2. Data Catalog Organization

```mermaid
graph TD
    Root[Data Catalog]

    Root --> DB1[analytics_db]
    Root --> DB2[sales_db]
    Root --> DB3[marketing_db]

    DB1 --> T1[customer_transactions]
    DB1 --> T2[customer_profiles]
    DB1 --> T3[product_catalog]

    T1 --> Schema1[Schema]
    T1 --> Loc1[Location: s3://lake/bronze/]
    T1 --> Format1[Format: Parquet]
    T1 --> Part1[Partitions]
    T1 --> Stats1[Statistics]
    T1 --> Tags1[Tags]

    Part1 --> P1[year=2024/month=01/]
    Part1 --> P2[year=2024/month=02/]
    Part1 --> P3[year=2024/month=03/]

    Schema1 --> C1[transaction_id: STRING]
    Schema1 --> C2[customer_id: STRING]
    Schema1 --> C3[amount: DECIMAL]
    Schema1 --> C4[date: DATE]

    Tags1 --> Tag1[Owner: FinanceTeam]
    Tags1 --> Tag2[Sensitivity: Confidential]
    Tags1 --> Tag3[Compliance: SOX]

    DB2 --> T4[daily_sales]
    DB2 --> T5[sales_targets]

    DB3 --> T6[campaigns]
    DB3 --> T7[email_events]

    style Root fill:#FF9900
    style DB1 fill:#146EB4
    style DB2 fill:#146EB4
    style DB3 fill:#146EB4
    style T1 fill:#569A31
```

## 3. Crawler Execution Flow

```mermaid
sequenceDiagram
    actor User
    participant Trigger as Scheduled/Event Trigger
    participant Crawler as AWS Glue Crawler
    participant Source as Data Source<br/>(S3/RDS/DynamoDB)
    participant Classifier as Classifiers
    participant Policy as Schema Change Policy
    participant Catalog as Data Catalog
    participant SNS as SNS Notification

    User->>Trigger: Configure schedule/event
    activate Trigger
    Trigger->>Crawler: Start crawler execution
    deactivate Trigger

    activate Crawler
    Crawler->>Source: Connect to data source
    activate Source
    Source-->>Crawler: Return sample data
    deactivate Source

    Crawler->>Classifier: Run classifiers
    activate Classifier
    Classifier-->>Crawler: Infer schema & format
    deactivate Classifier

    Crawler->>Crawler: Detect partitions
    Crawler->>Crawler: Identify changes

    Crawler->>Policy: Apply schema change policy
    activate Policy
    Policy-->>Crawler: Approve/log changes
    deactivate Policy

    Crawler->>Catalog: Update tables & partitions
    activate Catalog
    Catalog-->>Crawler: Confirm update
    deactivate Catalog

    Crawler->>SNS: Send notification
    deactivate Crawler

    SNS-->>User: Crawler completed

    Note over Crawler,Catalog: UpdateBehavior: UPDATE_IN_DATABASE<br/>DeleteBehavior: DEPRECATE_IN_DATABASE
```

## 4. Lake Formation Permission Model

```mermaid
graph TD
    Request[Data Access Request]

    Request --> L1{Layer 1:<br/>IAM Policy}
    L1 -->|Deny| Denied1[Access Denied]
    L1 -->|Allow| L2{Layer 2:<br/>Data Location<br/>Permission}

    L2 -->|Deny| Denied2[Access Denied]
    L2 -->|Allow| L3{Layer 3:<br/>Database<br/>Permission}

    L3 -->|Deny| Denied3[Access Denied]
    L3 -->|Allow| L4{Layer 4:<br/>Table<br/>Permission}

    L4 -->|Deny| Denied4[Access Denied]
    L4 -->|Allow| L5{Layer 5:<br/>Column<br/>Permission}

    L5 -->|Deny| Denied5[Access Denied]
    L5 -->|Allow| L6{Layer 6:<br/>Data Filter<br/>Row-level}

    L6 --> Filter[Apply Row Filter]
    Filter --> L7{Layer 7:<br/>Tag-Based<br/>Access}

    L7 -->|Deny| Denied7[Access Denied]
    L7 -->|Allow| Granted[Access Granted<br/>with filtered data]

    style Request fill:#FF9900
    style Granted fill:#00C853
    style Denied1 fill:#D32F2F
    style Denied2 fill:#D32F2F
    style Denied3 fill:#D32F2F
    style Denied4 fill:#D32F2F
    style Denied5 fill:#D32F2F
    style Denied7 fill:#D32F2F
```

## 5. Data Lineage Flow

```mermaid
graph LR
    subgraph "Source Systems"
        SF[Salesforce API]
        S3Raw[S3 Landing Zone]
        RDS[(RDS Database)]
    end

    subgraph "Bronze Layer"
        Bronze1[raw_sales_data]
        Bronze2[raw_customer_data]
    end

    subgraph "Silver Layer"
        Silver1[silver_sales_data]
        Silver2[silver_customer_data]
        Silver3[silver_enriched_sales]
    end

    subgraph "Gold Layer"
        Gold1[daily_sales_summary]
        Gold2[customer_purchase_patterns]
        Gold3[customer_lifetime_value]
    end

    subgraph "Consumption"
        Dashboard[QuickSight Dashboard]
        ML[ML Model: Churn Prediction]
        API[Analytics API]
    end

    subgraph "Glue Jobs"
        Job1[glue_job_ingest]
        Job2[glue_job_bronze_to_silver]
        Job3[glue_job_silver_aggregation]
        Job4[glue_job_customer_analytics]
    end

    SF -->|Job1| Bronze1
    S3Raw -->|Job1| Bronze1
    RDS -->|Job1| Bronze2

    Bronze1 -->|Job2<br/>filter, deduplicate| Silver1
    Bronze2 -->|Job2<br/>clean, standardize| Silver2

    Silver1 -->|Job4<br/>join| Silver3
    Silver2 -->|Job4<br/>join| Silver3

    Silver1 -->|Job3<br/>aggregate| Gold1
    Silver3 -->|Job4<br/>compute metrics| Gold2
    Gold2 -->|calculate| Gold3

    Gold1 --> Dashboard
    Gold2 --> ML
    Gold3 --> API

    style Bronze1 fill:#CD7F32
    style Bronze2 fill:#CD7F32
    style Silver1 fill:#C0C0C0
    style Silver2 fill:#C0C0C0
    style Silver3 fill:#C0C0C0
    style Gold1 fill:#FFD700
    style Gold2 fill:#FFD700
    style Gold3 fill:#FFD700
```

## 6. Cross-Account Data Sharing

```mermaid
sequenceDiagram
    participant PA as Producer Account<br/>(111111111111)
    participant LF_P as Lake Formation<br/>(Producer)
    participant Cat_P as Data Catalog<br/>(Producer)
    participant S3_P as S3 Bucket<br/>(Producer)
    participant LF_C as Lake Formation<br/>(Consumer)
    participant Cat_C as Data Catalog<br/>(Consumer)
    participant CA as Consumer Account<br/>(222222222222)
    participant Athena as Athena<br/>(Consumer)

    PA->>LF_P: Register S3 location
    PA->>Cat_P: Create database & tables
    PA->>LF_P: Grant permissions to account 222222222222

    Note over LF_P: Grant: SELECT, DESCRIBE<br/>Database: shared_analytics_db<br/>Grant Option: True

    LF_P->>LF_C: Cross-account grant

    CA->>LF_C: Accept resource share
    CA->>Cat_C: Create resource link

    Note over Cat_C: Resource Link points to<br/>producer's database

    CA->>LF_C: Grant permissions to local roles

    Note over LF_C: Principal: DataAnalystRole<br/>Resource: Resource Link<br/>Permissions: SELECT

    CA->>Athena: Run query on shared table
    Athena->>Cat_C: Get table metadata
    Cat_C->>Cat_P: Resolve resource link
    Cat_P-->>Athena: Return metadata
    Athena->>LF_C: Check permissions
    LF_C->>LF_P: Validate cross-account access
    LF_P-->>LF_C: Access granted
    Athena->>S3_P: Read data
    S3_P-->>Athena: Return data
    Athena-->>CA: Query results

    Note over PA,CA: Data stays in producer account<br/>Consumer reads via Lake Formation permissions
```

## 7. Data Quality Pipeline

```mermaid
flowchart TD
    Start[S3 Object Created<br/>Landing Zone] --> EventBridge[EventBridge Rule]
    EventBridge --> Lambda[Lambda: Trigger Quality Check]

    Lambda --> Crawler[Start Glue Crawler]
    Lambda --> Quality[Start Data Quality Evaluation]

    Crawler --> UpdateCatalog[Update Data Catalog]

    Quality --> Rules{Evaluate Rules}

    Rules --> Completeness[Completeness Check<br/>No null values in required fields]
    Rules --> Uniqueness[Uniqueness Check<br/>Primary key uniqueness > 99.9%]
    Rules --> Validity[Validity Check<br/>Values match expected patterns]
    Rules --> Consistency[Consistency Check<br/>Foreign keys exist]
    Rules --> Timeliness[Timeliness Check<br/>Data freshness < 24 hours]

    Completeness --> Aggregate{Aggregate Results}
    Uniqueness --> Aggregate
    Validity --> Aggregate
    Consistency --> Aggregate
    Timeliness --> Aggregate

    Aggregate -->|Quality Score >= 95%| Pass[Pass: Move to Bronze]
    Aggregate -->|Quality Score < 95%| Fail[Fail: Move to Quarantine]

    Pass --> Bronze[s3://lake/bronze/]
    Pass --> TagPass[Tag: quality=pass]
    Pass --> MetricsPass[CloudWatch Metrics]

    Fail --> Quarantine[s3://lake/quarantine/]
    Fail --> LogFail[Log Failures]
    Fail --> SNS[SNS Notification]
    Fail --> Ticket[Create Incident Ticket]

    MetricsPass --> Dashboard[QuickSight Dashboard<br/>Quality Trends]
    SNS --> Engineers[Notify Data Engineers]

    style Pass fill:#00C853
    style Fail fill:#D32F2F
    style Bronze fill:#CD7F32
    style Quarantine fill:#F57C00
```

## 8. Governed Tables Architecture (Apache Iceberg)

```mermaid
graph TD
    subgraph "Governed Table Structure"
        Root[s3://lake/governed/customer_orders/]

        Root --> Meta[metadata/]
        Root --> Data[data/]
        Root --> Manifests[manifests/]

        Meta --> Hint[version-hint.text]
        Meta --> V1[v1.metadata.json]
        Meta --> V2[v2.metadata.json]
        Meta --> V3[v3.metadata.json<br/>Current]
        Meta --> Snap[snap-123456789-1.avro]

        Data --> Y24[year=2024/]
        Y24 --> M01[month=01/]
        Y24 --> M02[month=02/]

        M01 --> D1[data-file-001.parquet]
        M01 --> D2[data-file-002.parquet]
        M01 --> Del1[delete-file-001.parquet<br/>Row-level deletes]

        M02 --> D3[data-file-003.parquet]
        M02 --> D4[data-file-004.parquet]

        Manifests --> ML[manifest-list-001.avro]
        Manifests --> M[manifest-002.avro]
    end

    subgraph "Features"
        ACID[ACID Transactions<br/>Serializable isolation]
        TimeTravel[Time Travel<br/>Query historical versions]
        SchemaEvo[Schema Evolution<br/>Backward compatible]
        Compact[Automatic Compaction<br/>Optimize small files]
        Incremental[Incremental Reads<br/>Process only new data]
    end

    V3 --> ACID
    V3 --> TimeTravel
    V3 --> SchemaEvo
    V3 --> Compact
    V3 --> Incremental

    style V3 fill:#00C853
    style ACID fill:#2196F3
    style TimeTravel fill:#2196F3
    style SchemaEvo fill:#2196F3
    style Compact fill:#2196F3
    style Incremental fill:#2196F3
```

## 9. Tag-Based Access Control (TBAC)

```mermaid
graph TD
    subgraph "Step 1: Define LF-Tags"
        LFTag1[DataSensitivity<br/>Public, Internal,<br/>Confidential, Restricted]
        LFTag2[DataDomain<br/>Sales, Marketing,<br/>Finance, HR]
        LFTag3[Environment<br/>Dev, Test,<br/>Staging, Prod]
    end

    subgraph "Step 2: Tag Resources"
        DB1[Database: sales_db] -->|Tags| DBTags1[DataDomain: Sales<br/>Environment: Prod]
        T1[Table: transactions] -->|Tags| TTags1[DataSensitivity: Confidential]
        T2[Table: public_metrics] -->|Tags| TTags2[DataSensitivity: Public]
        T3[Table: customer_pii] -->|Tags| TTags3[DataSensitivity: Restricted]
    end

    subgraph "Step 3: Grant Permissions by Tags"
        Role1[DataAnalystRole] -->|Access| TagFilter1[Resources with:<br/>DataSensitivity = Public/Internal]
        Role2[DataEngineerRole] -->|Access| TagFilter2[Resources with:<br/>DataDomain = Sales<br/>DataSensitivity = Public/Internal/Confidential]
        Role3[AdminRole] -->|Access| TagFilter3[Resources with:<br/>ALL tags]
    end

    subgraph "Step 4: Automatic Inheritance"
        NewTable[New Table Created] -->|Auto-inherit| ParentDB[Parent Database Tags]
        ParentDB -->|Applied| AutoPerm[Permissions automatically apply]
    end

    TagFilter1 --> T2
    TagFilter2 --> T1
    TagFilter2 --> T2
    TagFilter3 --> T1
    TagFilter3 --> T2
    TagFilter3 --> T3

    style LFTag1 fill:#FF9900
    style LFTag2 fill:#FF9900
    style LFTag3 fill:#FF9900
    style TagFilter1 fill:#00C853
    style TagFilter2 fill:#00C853
    style TagFilter3 fill:#00C853
    style AutoPerm fill:#2196F3
```

## 10. Monitoring and Observability

```mermaid
graph TB
    subgraph "Data Sources"
        Crawlers[Glue Crawlers]
        Jobs[Glue Jobs]
        LF[Lake Formation]
        Quality[Data Quality]
        Catalog[Data Catalog]
    end

    subgraph "CloudWatch Metrics"
        M1[Crawler Metrics<br/>RunTime, TablesCreated,<br/>PartitionsCreated]
        M2[Job Metrics<br/>ExecutionTime, CPUUsage,<br/>MemoryUsage]
        M3[Lake Formation Metrics<br/>PermissionRequests,<br/>PermissionDenials]
        M4[Quality Metrics<br/>QualityScore, RulesPassed,<br/>DataFreshness]
        M5[Catalog Metrics<br/>TableCount, AccessCount,<br/>QueryDuration]
    end

    subgraph "CloudWatch Alarms"
        A1[Crawler Failures > 2/day]
        A2[Quality Score < 95%]
        A3[Permission Denials > threshold]
        A4[Data Freshness > 24 hours]
        A5[Table Count Anomaly]
    end

    subgraph "Notifications & Actions"
        SNS[SNS Topic]
        Slack[Slack Channel]
        PD[PagerDuty]
        Email[Engineering Team Email]
    end

    subgraph "Audit & Compliance"
        CT[CloudTrail Logs]
        Athena[Athena Queries]
        Reports[Compliance Reports]
    end

    subgraph "Dashboards"
        CW_Dash[CloudWatch Dashboard]
        QS_Dash[QuickSight Dashboard<br/>Quality Trends<br/>Access Patterns<br/>Cost Analysis]
    end

    Crawlers --> M1
    Jobs --> M2
    LF --> M3
    Quality --> M4
    Catalog --> M5

    M1 --> A1
    M4 --> A2
    M3 --> A3
    M4 --> A4
    M5 --> A5

    A1 --> SNS
    A2 --> SNS
    A3 --> SNS
    A4 --> SNS
    A5 --> SNS

    SNS --> Slack
    SNS --> PD
    SNS --> Email

    M1 --> CW_Dash
    M2 --> CW_Dash
    M3 --> CW_Dash
    M4 --> CW_Dash
    M5 --> CW_Dash

    M1 --> QS_Dash
    M4 --> QS_Dash
    M5 --> QS_Dash

    Crawlers --> CT
    Jobs --> CT
    LF --> CT

    CT --> Athena
    Athena --> Reports

    style A1 fill:#F57C00
    style A2 fill:#F57C00
    style A3 fill:#F57C00
    style A4 fill:#F57C00
    style A5 fill:#F57C00
    style CW_Dash fill:#2196F3
    style QS_Dash fill:#2196F3
```

## Usage Notes

These diagrams illustrate key architectural patterns for Data Catalog and Governance:

1. **Complete Platform**: End-to-end governance architecture
2. **Catalog Organization**: How databases, tables, and metadata are structured
3. **Crawler Execution**: Step-by-step crawler process flow
4. **Permission Model**: Multi-layer security and access control
5. **Data Lineage**: Tracking data flow from source to consumption
6. **Cross-Account Sharing**: Secure data sharing between AWS accounts
7. **Quality Pipeline**: Automated data quality validation workflow
8. **Governed Tables**: Apache Iceberg table structure and features
9. **TBAC**: Tag-based access control implementation
10. **Monitoring**: Comprehensive observability and alerting

To render these diagrams:
- Use VS Code with the Mermaid extension
- View in GitHub (native Mermaid support)
- Use online tools like [Mermaid Live Editor](https://mermaid.live/)
- Export to PNG/SVG for documentation
