# Data Catalog & Governance Pattern Diagrams

## 1. Bronze-Silver-Gold with Governance

```mermaid
graph LR
    subgraph "Raw Zone"
        Raw[Raw Data<br/>S3 Landing]
    end

    subgraph "Bronze Layer - Basic Governance"
        Bronze[Bronze Tables]
        BronzeMeta[Metadata:<br/>- Raw schema<br/>- Source info<br/>- Load timestamp]
        BronzeQuality[Quality: 85%+<br/>- Completeness<br/>- Format validation]
        BronzePerm[Permissions:<br/>Data Engineers only]
    end

    subgraph "Silver Layer - Enhanced Governance"
        Silver[Silver Tables]
        SilverMeta[Metadata:<br/>- Business terms<br/>- Data owner<br/>- Lineage tracked]
        SilverQuality[Quality: 95%+<br/>- Uniqueness<br/>- Referential integrity<br/>- Business rules]
        SilverPerm[Permissions:<br/>Engineers + Analysts<br/>Column-level security]
    end

    subgraph "Gold Layer - Full Governance"
        Gold[Gold Tables]
        GoldMeta[Metadata:<br/>- SLA defined<br/>- Certified dataset<br/>- Full documentation]
        GoldQuality[Quality: 99%+<br/>- Accuracy validated<br/>- Consistency guaranteed<br/>- Timeliness tracked]
        GoldPerm[Permissions:<br/>All users<br/>TBAC enabled<br/>Row filters applied]
    end

    Raw -->|Ingest| Bronze
    Bronze --> BronzeMeta
    Bronze --> BronzeQuality
    Bronze --> BronzePerm

    Bronze -->|Clean, deduplicate| Silver
    Silver --> SilverMeta
    Silver --> SilverQuality
    Silver --> SilverPerm

    Silver -->|Aggregate, enrich| Gold
    Gold --> GoldMeta
    Gold --> GoldQuality
    Gold --> GoldPerm

    style Bronze fill:#CD7F32
    style Silver fill:#C0C0C0
    style Gold fill:#FFD700
```

## 2. Multi-Account Data Mesh Architecture

```mermaid
graph TD
    subgraph "Central Governance Account"
        CentralLF[Central Lake Formation]
        PolicyEngine[Policy Engine]
        CentralCatalog[Central Catalog]
        Monitoring[Monitoring & Audit]
    end

    subgraph "Sales Domain Account"
        SalesLF[Lake Formation]
        SalesDB[(Sales Database)]
        SalesTables[- customer_orders<br/>- sales_pipeline<br/>- revenue_metrics]
        SalesOwner[Domain Owner:<br/>Sales Team]
    end

    subgraph "Marketing Domain Account"
        MarketingLF[Lake Formation]
        MarketingDB[(Marketing Database)]
        MarketingTables[- campaigns<br/>- email_events<br/>- attribution]
        MarketingOwner[Domain Owner:<br/>Marketing Team]
    end

    subgraph "Finance Domain Account"
        FinanceLF[Lake Formation]
        FinanceDB[(Finance Database)]
        FinanceTables[- transactions<br/>- invoices<br/>- payments]
        FinanceOwner[Domain Owner:<br/>Finance Team]
    end

    subgraph "Analytics Consumer Account"
        ConsumerLF[Lake Formation]
        ResourceLinks[Resource Links<br/>to all domains]
        Athena[Amazon Athena]
        QuickSight[QuickSight]
        Analysts[Data Analysts]
    end

    PolicyEngine --> SalesLF
    PolicyEngine --> MarketingLF
    PolicyEngine --> FinanceLF

    SalesDB --> SalesTables
    SalesTables --> SalesOwner
    MarketingDB --> MarketingTables
    MarketingTables --> MarketingOwner
    FinanceDB --> FinanceTables
    FinanceTables --> FinanceOwner

    SalesLF -.->|Share| ConsumerLF
    MarketingLF -.->|Share| ConsumerLF
    FinanceLF -.->|Share| ConsumerLF

    ConsumerLF --> ResourceLinks
    ResourceLinks --> Athena
    ResourceLinks --> QuickSight
    Athena --> Analysts
    QuickSight --> Analysts

    SalesLF --> Monitoring
    MarketingLF --> Monitoring
    FinanceLF --> Monitoring
    ConsumerLF --> Monitoring

    CentralCatalog -.->|Federate| SalesDB
    CentralCatalog -.->|Federate| MarketingDB
    CentralCatalog -.->|Federate| FinanceDB

    style CentralLF fill:#FF9900
    style SalesLF fill:#4CAF50
    style MarketingLF fill:#2196F3
    style FinanceLF fill:#9C27B0
    style ConsumerLF fill:#FF5722
```

## 3. Compliance and Audit Pattern

```mermaid
graph TB
    subgraph "Data Operations"
        User[User/Service]
        Query[Execute Query]
        Update[Modify Data]
        Admin[Admin Action]
    end

    subgraph "Lake Formation"
        LF[Permission Check]
        Filter[Apply Data Filters]
        Grant[Grant/Revoke]
    end

    subgraph "Audit Trail"
        CloudTrail[CloudTrail Logs]
        S3Logs[S3 Access Logs]
        LFLogs[Lake Formation Logs]
    end

    subgraph "Compliance Analysis"
        Athena[Athena Queries]
        Glue[Glue ETL]
        Reports[Compliance Reports]
    end

    subgraph "Alerting"
        CW[CloudWatch]
        Alarms[Alarms]
        SNS[SNS Notifications]
        SOC[SOC Team]
    end

    User --> Query
    User --> Update
    User --> Admin

    Query --> LF
    Update --> LF
    Admin --> Grant

    LF --> Filter
    Filter --> CloudTrail
    Grant --> LFLogs

    Query -.->|Access logs| S3Logs
    Update -.->|Access logs| S3Logs

    CloudTrail --> Athena
    S3Logs --> Glue
    LFLogs --> Athena

    Athena --> Reports
    Glue --> Reports

    Reports --> CW
    CW --> Alarms
    Alarms --> SNS
    SNS --> SOC

    subgraph "Compliance Requirements"
        GDPR[GDPR<br/>- Right to be forgotten<br/>- Data minimization<br/>- Consent tracking]
        HIPAA[HIPAA<br/>- Access logs<br/>- Encryption<br/>- Audit trail]
        SOX[SOX<br/>- Financial controls<br/>- Change management<br/>- Retention policies]
    end

    Reports --> GDPR
    Reports --> HIPAA
    Reports --> SOX

    style CloudTrail fill:#FF9900
    style Reports fill:#4CAF50
    style SOC fill:#F44336
```

## 4. PII Detection and Masking Pattern

```mermaid
flowchart TD
    Start[Raw Data Ingested]

    Start --> Crawler[Glue Crawler]
    Crawler --> Catalog[Update Catalog]

    Catalog --> PIIDetect[PII Detection Job]

    PIIDetect --> Scan[Scan columns for:<br/>- Email patterns<br/>- Phone numbers<br/>- SSN patterns<br/>- Credit cards<br/>- IP addresses]

    Scan --> Found{PII Found?}

    Found -->|Yes| TagPII[Tag columns as PII]
    Found -->|No| NoPII[Tag as non-PII]

    TagPII --> ClassifySensitivity[Classify sensitivity:<br/>- Restricted: SSN, CC<br/>- Confidential: Email<br/>- Internal: Phone]

    ClassifySensitivity --> ApplyStrategy{Masking Strategy}

    ApplyStrategy -->|Restricted| FullMask[Full masking or hashing]
    ApplyStrategy -->|Confidential| PartialMask[Partial masking]
    ApplyStrategy -->|Internal| ConditionalMask[Role-based masking]

    FullMask --> Transform[ETL Transformation]
    PartialMask --> Transform
    ConditionalMask --> Transform
    NoPII --> NoTransform[No transformation needed]

    Transform --> SilverMasked[Silver Layer<br/>Masked Data]
    NoTransform --> SilverClean[Silver Layer<br/>Clean Data]

    SilverMasked --> Permissions[Set Lake Formation<br/>Column Permissions]
    SilverClean --> Permissions

    Permissions --> Role1[Analysts:<br/>Can only see masked data]
    Permissions --> Role2[Data Engineers:<br/>Can see partial data]
    Permissions --> Role3[Compliance Team:<br/>Can see raw data with audit]

    Role1 --> Audit[All access audited]
    Role2 --> Audit
    Role3 --> Audit

    Audit --> ComplianceReport[Generate compliance report:<br/>- Who accessed PII<br/>- When and why<br/>- Data retention status]

    style PIIDetect fill:#F44336
    style FullMask fill:#F44336
    style Audit fill:#FF9900
```

## 5. Disaster Recovery Pattern

```mermaid
graph TB
    subgraph "Primary Region us-east-1"
        PR_S3[(S3 us-east-1<br/>Primary Data Lake)]
        PR_Catalog[Glue Catalog<br/>us-east-1]
        PR_LF[Lake Formation<br/>us-east-1]
        PR_Jobs[Glue Jobs<br/>us-east-1]
    end

    subgraph "DR Region us-west-2"
        DR_S3[(S3 us-west-2<br/>Replica Data Lake)]
        DR_Catalog[Glue Catalog<br/>us-west-2]
        DR_LF[Lake Formation<br/>us-west-2]
        DR_Jobs[Glue Jobs<br/>us-west-2]
    end

    subgraph "Replication Strategy"
        S3_CRR[S3 Cross-Region<br/>Replication]
        Catalog_Export[Catalog Export<br/>to S3]
        Catalog_Import[Catalog Import<br/>from S3]
        LF_Backup[Lake Formation<br/>Permissions Backup]
    end

    subgraph "Monitoring"
        Health[Health Checks]
        RPO[RPO: 15 minutes]
        RTO[RTO: 1 hour]
        Failover[Automated Failover]
    end

    PR_S3 -->|Continuous| S3_CRR
    S3_CRR --> DR_S3

    PR_Catalog -->|Daily| Catalog_Export
    Catalog_Export --> DR_Catalog

    PR_LF -->|Daily| LF_Backup
    LF_Backup --> DR_LF

    PR_Jobs -->|Code in Git| DR_Jobs

    Health --> PR_S3
    Health --> PR_Catalog
    Health --> PR_LF

    Health --> Failover
    Failover -->|Region failure| DR_S3
    Failover --> DR_Catalog
    Failover --> DR_LF

    DR_S3 -.->|Reverse replication| PR_S3

    style PR_S3 fill:#4CAF50
    style DR_S3 fill:#2196F3
    style Failover fill:#FF5722
```

## 6. Data Retention and Archival Pattern

```mermaid
stateDiagram-v2
    [*] --> Active: Data ingested

    Active --> Hot: Days 0-30
    Hot --> Warm: Days 31-90
    Warm --> Cool: Days 91-365
    Cool --> Cold: Days 366-2555
    Cold --> Archive: Year 8+

    state Hot {
        [*] --> FrequentAccess
        FrequentAccess --> S3_Standard
        S3_Standard --> FullCatalog
        FullCatalog --> NoCompression
    }

    state Warm {
        [*] --> ModerateAccess
        ModerateAccess --> S3_InfrequentAccess
        S3_InfrequentAccess --> ActiveCatalog
        ActiveCatalog --> PartitionPruning
    }

    state Cool {
        [*] --> RareAccess
        RareAccess --> S3_Glacier_IR
        S3_Glacier_IR --> ArchiveCatalog
        ArchiveCatalog --> HighCompression
    }

    state Cold {
        [*] --> VeryRareAccess
        VeryRareAccess --> S3_Glacier
        S3_Glacier --> MinimalCatalog
        MinimalCatalog --> MaxCompression
    }

    state Archive {
        [*] --> ComplianceOnly
        ComplianceOnly --> S3_Deep_Archive
        S3_Deep_Archive --> OfflineCatalog
        OfflineCatalog --> LegalHold
    }

    Archive --> Deletion: Retention period expired
    Deletion --> [*]

    note right of Active
        Lifecycle policies:
        - Automatic transitions
        - Cost optimization
        - Compliance rules
    end note

    note right of Archive
        Legal hold:
        - Cannot be deleted
        - Audit required
        - Court order only
    end note
```

## 7. Schema Evolution Pattern

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant Git as Git Repository
    participant CI as CI/CD Pipeline
    participant Test as Test Catalog
    participant Prod as Production Catalog
    participant Consumers as Data Consumers
    participant Monitor as Monitoring

    Dev->>Git: Commit schema change<br/>(add column: customer_segment)
    Git->>CI: Trigger pipeline

    CI->>CI: Run schema validation
    Note over CI: Check:<br/>- Backward compatibility<br/>- Data types valid<br/>- Naming conventions<br/>- Documentation present

    CI->>Test: Apply to test catalog
    Test->>Test: Run test queries
    Test-->>CI: Tests passed

    CI->>Dev: Request approval
    Dev->>CI: Approve deployment

    CI->>Prod: Update table schema (version bump v2 → v3)

    Note over Prod: Schema change policy:<br/>UpdateBehavior: UPDATE_IN_DATABASE<br/>New column: customer_segment STRING<br/>Default: NULL (backward compatible)

    Prod->>Consumers: Notify of schema change

    par Consumer A
        Consumers->>Prod: SELECT * (gets new column)
        Prod-->>Consumers: Returns data with customer_segment
    and Consumer B
        Consumers->>Prod: SELECT id, name (no change needed)
        Prod-->>Consumers: Works as before
    end

    Prod->>Monitor: Log schema change
    Monitor->>Monitor: Track:<br/>- Version history<br/>- Downstream impact<br/>- Query compatibility

    Note over Dev,Monitor: Rollback available:<br/>Can revert to v2 if issues detected
```

## 8. Federated Query Pattern

```mermaid
graph TD
    Query[User Query:<br/>Join data from<br/>multiple sources]

    Query --> Athena[Amazon Athena<br/>Federated Query]

    Athena --> Catalog1[Glue Catalog<br/>S3 Data Lake]
    Athena --> Catalog2[Redshift Catalog<br/>Data Warehouse]
    Athena --> Catalog3[RDS Catalog<br/>Transactional DB]
    Athena --> Catalog4[External Hive<br/>On-Prem Metastore]

    Catalog1 --> Data1[(S3 Tables<br/>sales_transactions)]
    Catalog2 --> Data2[(Redshift Tables<br/>customer_dim)]
    Catalog3 --> Data3[(RDS Tables<br/>product_catalog)]
    Catalog4 --> Data4[(HDFS Tables<br/>legacy_data)]

    Data1 --> Join[Distributed Join<br/>in Athena]
    Data2 --> Join
    Data3 --> Join
    Data4 --> Join

    Join --> Optimize[Query Optimization:<br/>- Predicate pushdown<br/>- Partition pruning<br/>- Column selection]

    Optimize --> Results[Unified Results]

    Results --> Cache{Cache Results?}
    Cache -->|Yes| SPICE[QuickSight SPICE<br/>In-memory cache]
    Cache -->|No| Direct[Direct query]

    SPICE --> User[User gets results]
    Direct --> User

    subgraph "LakeFormation Governance"
        Permissions[Permission Check<br/>at each source]
        ColumnFilter[Column-level<br/>filtering]
        RowFilter[Row-level<br/>filtering]
    end

    Athena -.->|Check before query| Permissions
    Permissions --> ColumnFilter
    ColumnFilter --> RowFilter
    RowFilter --> Join

    style Athena fill:#8C4FFF
    style Join fill:#FF9900
    style Permissions fill:#4CAF50
```

## 9. Real-Time Catalog Updates Pattern

```mermaid
sequenceDiagram
    participant S3
    participant EventBridge
    participant Lambda
    participant Glue
    participant Catalog
    participant DynamoDB
    participant SNS

    Note over S3,SNS: Real-time metadata updates

    S3->>EventBridge: S3 PutObject event<br/>s3://lake/bronze/sales/2024/03/08/

    EventBridge->>Lambda: Trigger update function
    activate Lambda

    Lambda->>DynamoDB: Check if partition exists
    DynamoDB-->>Lambda: Partition not found

    Lambda->>Glue: AddPartition API
    Note over Glue: Add partition:<br/>year=2024, month=03, day=08<br/>location: s3://.../2024/03/08/

    Glue->>Catalog: Update table metadata
    Catalog-->>Glue: Partition added

    Glue-->>Lambda: Success

    Lambda->>DynamoDB: Record partition<br/>(avoid duplicates)
    Lambda->>SNS: Publish notification
    deactivate Lambda

    SNS->>SNS: Notify subscribers:<br/>- Data engineers<br/>- Monitoring dashboard<br/>- Downstream ETL jobs

    Note over S3,SNS: Total latency: < 5 seconds<br/>Data available for immediate query

    alt Large File Upload (> 1GB)
        S3->>EventBridge: Multipart upload complete
        EventBridge->>Lambda: Trigger with delay
        Lambda->>Lambda: Wait for all parts
        Lambda->>Glue: Update partition + statistics
    else Small File Upload
        S3->>EventBridge: Single PutObject
        EventBridge->>Lambda: Immediate trigger
        Lambda->>Glue: Quick partition add
    end
```

## 10. Cost Allocation and Chargeback Pattern

```mermaid
graph TD
    subgraph "Resource Tagging"
        Catalog[Data Catalog]
        Tables[Tables]

        Catalog --> Tag1[CostCenter: CC-001]
        Catalog --> Tag2[Department: Sales]
        Catalog --> Tag3[Project: Q1-Analytics]

        Tables --> Tag1
        Tables --> Tag2
        Tables --> Tag3
    end

    subgraph "Usage Tracking"
        Queries[Athena Queries]
        Jobs[Glue Jobs]
        Storage[S3 Storage]

        Queries --> QueryLogs[CloudWatch Logs]
        Jobs --> JobMetrics[Glue Metrics]
        Storage --> StorageMetrics[S3 Metrics]
    end

    subgraph "Cost Allocation"
        QueryLogs --> CostExplorer[AWS Cost Explorer]
        JobMetrics --> CostExplorer
        StorageMetrics --> CostExplorer

        Tag1 --> CostExplorer
        Tag2 --> CostExplorer
        Tag3 --> CostExplorer
    end

    subgraph "Reporting"
        CostExplorer --> Reports[Cost Reports]

        Reports --> ByDept[By Department:<br/>Sales: $1,234<br/>Marketing: $987<br/>Finance: $765]

        Reports --> ByProject[By Project:<br/>Q1-Analytics: $543<br/>ML-Pipeline: $432<br/>BI-Dashboard: $321]

        Reports --> ByResource[By Resource:<br/>Storage: $800<br/>Queries: $600<br/>ETL: $400]
    end

    subgraph "Chargeback"
        ByDept --> Invoice1[Sales Invoice]
        ByProject --> Invoice2[Project Budget]

        Invoice1 --> Finance[Finance System]
        Invoice2 --> Finance

        Finance --> Billing[Monthly Billing]
    end

    subgraph "Optimization"
        Reports --> Analysis[Cost Analysis]
        Analysis --> Recommendations[Recommendations:<br/>- Compress data<br/>- Reduce scans<br/>- Optimize partitions<br/>- Archive old data]

        Recommendations --> Action[Take Action]
        Action --> Savings[Cost Savings]
    end

    style CostExplorer fill:#FF9900
    style Savings fill:#4CAF50
```

## Usage

These pattern diagrams demonstrate advanced Data Catalog and Governance architectures:

1. **Bronze-Silver-Gold**: Governance evolution across layers
2. **Data Mesh**: Multi-account domain-driven architecture
3. **Compliance**: Audit trail and regulatory compliance
4. **PII Detection**: Automated sensitive data handling
5. **Disaster Recovery**: Cross-region resilience
6. **Data Retention**: Lifecycle management and archival
7. **Schema Evolution**: Safe schema changes with versioning
8. **Federated Query**: Query across multiple catalogs
9. **Real-Time Updates**: Event-driven catalog updates
10. **Cost Allocation**: Usage tracking and chargeback
