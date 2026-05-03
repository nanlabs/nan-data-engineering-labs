# Data Catalog & Governance Workflow Diagrams

## 1. Crawler Scheduling Patterns

```mermaid
graph TD
    Start[Data Arrives]

    Start --> Pattern1[Pattern 1:<br/>Time-Based]
    Start --> Pattern2[Pattern 2:<br/>Event-Driven]
    Start --> Pattern3[Pattern 3:<br/>Workflow-Based]

    Pattern1 --> Cron[Cron Schedule<br/>cron 0 2 * * ? *]
    Cron --> CrawlerRun1[Crawler Executes Daily]
    CrawlerRun1 --> Pros1[Pros:<br/>- Predictable<br/>- Simple]
    CrawlerRun1 --> Cons1[Cons:<br/>- May miss data<br/>- Unnecessary runs]

    Pattern2 --> S3Event[S3 Event:<br/>ObjectCreated]
    S3Event --> EventBridge[EventBridge Rule]
    EventBridge --> Lambda[Lambda Trigger]
    Lambda --> CrawlerRun2[Crawler Executes]
    CrawlerRun2 --> Pros2[Pros:<br/>- Real-time<br/>- Efficient]
    CrawlerRun2 --> Cons2[Cons:<br/>- Complex setup<br/>- Can be chatty]

    Pattern3 --> StepFn[Step Functions]
    StepFn --> ETLJob[ETL Job Completes]
    ETLJob --> CrawlerRun3[Crawler Executes]
    CrawlerRun3 --> Pros3[Pros:<br/>- Coordinated<br/>- Guaranteed order]
    CrawlerRun3 --> Cons3[Cons:<br/>- Coupled to workflow]

    style CrawlerRun1 fill:#FF9900
    style CrawlerRun2 fill:#FF9900
    style CrawlerRun3 fill:#FF9900
```

## 2. Permission Grant Workflow

```mermaid
sequenceDiagram
    actor Admin as Lake Formation Admin
    participant LF as Lake Formation
    participant IAM as IAM
    participant Catalog as Data Catalog
    actor User as Data Analyst
    participant Athena as Athena
    participant S3 as S3

    Admin->>LF: Register S3 location
    LF->>S3: Validate access
    S3-->>LF: Access confirmed

    Admin->>Catalog: Create database & table
    Catalog-->>Admin: Table created

    Admin->>LF: Grant data location permission
    Note over LF: Principal: DataAnalystRole<br/>Resource: s3://lake/sales/<br/>Permission: DATA_LOCATION_ACCESS

    Admin->>LF: Grant database permission
    Note over LF: Database: sales_db<br/>Permission: DESCRIBE

    Admin->>LF: Grant table permission
    Note over LF: Table: transactions<br/>Columns: [id, amount, date]<br/>Excluded: [ssn, credit_card]<br/>Permission: SELECT

    Admin->>LF: Apply data filter (optional)
    Note over LF: Filter: region = 'US-WEST'

    LF-->>Admin: Permissions granted

    User->>IAM: Assume DataAnalystRole
    IAM-->>User: Temporary credentials

    User->>Athena: SELECT * FROM sales_db.transactions
    Athena->>Catalog: Get table metadata
    Catalog-->>Athena: Schema + location

    Athena->>LF: Check permissions
    LF->>LF: Validate IAM → Location → DB → Table → Column
    LF->>LF: Apply data filter
    LF-->>Athena: Access granted (filtered)

    Athena->>S3: Read data from s3://lake/sales/
    S3-->>Athena: Data (region='US-WEST' only)
    Athena-->>User: Query results (filtered columns)
```

## 3. Data Quality Validation Flow

```mermaid
stateDiagram-v2
    [*] --> DataArrival: New data lands in S3

    DataArrival --> TriggerCrawler: EventBridge trigger
    TriggerCrawler --> CrawlerRunning: Crawler starts

    CrawlerRunning --> CatalogUpdated: Schema discovered
    CatalogUpdated --> QualityCheck: Start quality evaluation

    QualityCheck --> RunRules: Execute ruleset

    RunRules --> CheckCompleteness: Rule 1: Completeness
    RunRules --> CheckUniqueness: Rule 2: Uniqueness
    RunRules --> CheckValidity: Rule 3: Validity
    RunRules --> CheckConsistency: Rule 4: Consistency
    RunRules --> CheckTimeliness: Rule 5: Timeliness

    CheckCompleteness --> AggregateScores
    CheckUniqueness --> AggregateScores
    CheckValidity --> AggregateScores
    CheckConsistency --> AggregateScores
    CheckTimeliness --> AggregateScores

    AggregateScores --> EvaluateThreshold: Calculate overall score

    EvaluateThreshold --> PassedValidation: Score >= 95%
    EvaluateThreshold --> WarningLevel: 90% <= Score < 95%
    EvaluateThreshold --> FailedValidation: Score < 90%

    PassedValidation --> MoveToBronze: Promote to Bronze layer
    MoveToBronze --> TagQualityPass: Add tag: quality=pass
    TagQualityPass --> UpdateMetrics: Log CloudWatch metrics
    UpdateMetrics --> [*]

    WarningLevel --> MoveToBronzeWarning: Promote with warning tag
    MoveToBronzeWarning --> SendWarning: SNS notification
    SendWarning --> LogWarning: Log to CloudWatch
    LogWarning --> [*]

    FailedValidation --> MoveToQuarantine: Move to quarantine
    MoveToQuarantine --> CreateTicket: Create Jira ticket
    CreateTicket --> SendAlert: SNS critical alert
    SendAlert --> BlockPromotion: Block from Silver layer
    BlockPromotion --> [*]
```

## 4. Tag-Based Access Control Setup

```mermaid
flowchart TD
    Start([Start TBAC Setup])

    Start --> Step1[Step 1: Define LF-Tags]
    Step1 --> Tag1[Create tag: DataSensitivity<br/>Values: Public, Internal,<br/>Confidential, Restricted]
    Step1 --> Tag2[Create tag: DataDomain<br/>Values: Sales, Marketing,<br/>Finance, HR]
    Step1 --> Tag3[Create tag: CostCenter<br/>Values: CC-001, CC-002, etc.]

    Tag1 --> Step2[Step 2: Tag Resources]
    Tag2 --> Step2
    Tag3 --> Step2

    Step2 --> TagDB[Tag databases]
    Step2 --> TagTable[Tag tables]
    Step2 --> TagColumn[Tag columns]

    TagDB --> Example1[sales_db:<br/>DataDomain=Sales<br/>CostCenter=CC-001]
    TagTable --> Example2[transactions:<br/>DataSensitivity=Confidential]
    TagColumn --> Example3[ssn column:<br/>DataSensitivity=Restricted]

    Example1 --> Step3[Step 3: Create IAM Roles]
    Example2 --> Step3
    Example3 --> Step3

    Step3 --> Role1[AnalystRole<br/>Principal tags:<br/>CostCenter=CC-001]
    Step3 --> Role2[EngineerRole<br/>Principal tags:<br/>DataDomain=Sales]

    Role1 --> Step4[Step 4: Grant Permissions by Tags]
    Role2 --> Step4

    Step4 --> Grant1[Grant to AnalystRole:<br/>Resources with CostCenter=CC-001<br/>Permission: SELECT]
    Step4 --> Grant2[Grant to EngineerRole:<br/>Resources with DataDomain=Sales<br/>AND DataSensitivity IN<br/>Public, Internal, Confidential<br/>Permission: SELECT, ALTER]

    Grant1 --> Step5[Step 5: Test Access]
    Grant2 --> Step5

    Step5 --> Test1[Analyst queries sales_db]
    Step5 --> Test2[Engineer modifies tables]

    Test1 --> Verify1{Access Check}
    Test2 --> Verify2{Access Check}

    Verify1 -->|CostCenter match| Allow1[Access Granted]
    Verify1 -->|No match| Deny1[Access Denied]

    Verify2 -->|Tags match & level allowed| Allow2[Access Granted]
    Verify2 -->|No match| Deny2[Access Denied]

    Allow1 --> Step6[Step 6: Auto-Inheritance]
    Allow2 --> Step6
    Deny1 --> Review[Review & Adjust]
    Deny2 --> Review

    Step6 --> NewRes[New table created in sales_db]
    NewRes --> Inherit[Automatically inherits parent tags]
    Inherit --> AutoAccess[Permissions apply immediately]

    AutoAccess --> End([TBAC Setup Complete])
    Review --> Step4

    style Step1 fill:#FF9900
    style Step2 fill:#FF9900
    style Step3 fill:#FF9900
    style Step4 fill:#FF9900
    style Step5 fill:#FF9900
    style Step6 fill:#FF9900
```

## 5. Data Lineage Capture

```mermaid
graph LR
    subgraph "Lineage Capture Points"
        CP1[Capture Point 1:<br/>Data Ingestion]
        CP2[Capture Point 2:<br/>ETL Processing]
        CP3[Capture Point 3:<br/>Data Consumption]
    end

    subgraph "Point 1 Details"
        Source[Source System]
        Ingest[Ingestion Job]
        Bronze[Bronze Layer]

        Source -->|API/DB/File| Ingest
        Ingest -->|Glue Job| Bronze

        Ingest -.->|Lineage| L1[Captured:<br/>- Source location<br/>- Source schema<br/>- Ingestion timestamp<br/>- Job name]
    end

    subgraph "Point 2 Details"
        BronzeRead[Read Bronze]
        Transform[Transform]
        Silver[Write Silver]

        BronzeRead -->|DataFrame| Transform
        Transform -->|clean, filter, join| Silver

        Transform -.->|Lineage| L2[Captured:<br/>- Input tables<br/>- Transformations<br/>- Output tables<br/>- Job parameters]
    end

    subgraph "Point 3 Details"
        SilverRead[Read Silver/Gold]
        Analytics[Analytics Query]
        Results[Results/Dashboard]

        SilverRead -->|Athena/Redshift| Analytics
        Analytics -->|Aggregate| Results

        Analytics -.->|Lineage| L3[Captured:<br/>- Consumed tables<br/>- Query patterns<br/>- User/Service<br/>- Access timestamp]
    end

    CP1 --> Point1Details
    CP2 --> Point2Details
    CP3 --> Point3Details

    L1 --> Catalog[AWS Glue<br/>Data Lineage]
    L2 --> Catalog
    L3 --> Catalog

    Catalog --> Viz[Lineage<br/>Visualization]
    Catalog --> Impact[Impact<br/>Analysis]
    Catalog --> Root[Root Cause<br/>Analysis]

    style CP1 fill:#FF9900
    style CP2 fill:#FF9900
    style CP3 fill:#FF9900
    style Catalog fill:#146EB4
```

## 6. Cross-Account Sharing Workflow

```mermaid
flowchart TD
    Start([Producer wants to share data])

    Start --> Check1{Is Lake Formation<br/>enabled?}
    Check1 -->|No| EnableLF[Enable Lake Formation<br/>in both accounts]
    Check1 -->|Yes| Check2
    EnableLF --> Check2

    Check2{Are S3 locations<br/>registered?}
    Check2 -->|No| RegisterS3[Register S3 locations<br/>with Lake Formation]
    Check2 -->|Yes| CreateCatalog
    RegisterS3 --> CreateCatalog

    CreateCatalog[Create database & tables<br/>in Data Catalog]
    CreateCatalog --> VerifySchema{Schema correct?}
    VerifySchema -->|No| FixSchema[Run crawler or<br/>update schema manually]
    VerifySchema -->|Yes| GrantCrossAccount
    FixSchema --> GrantCrossAccount

    GrantCrossAccount[Grant permissions to<br/>consumer account]
    GrantCrossAccount --> SelectGrant{What to grant?}

    SelectGrant -->|Full database| GrantDB[Grant database:<br/>SELECT, DESCRIBE]
    SelectGrant -->|Specific tables| GrantTable[Grant table:<br/>SELECT, DESCRIBE]
    SelectGrant -->|Filtered data| GrantFilter[Grant table + data filter:<br/>Row-level security]

    GrantDB --> SetGrantOption
    GrantTable --> SetGrantOption
    GrantFilter --> SetGrantOption

    SetGrantOption{Allow consumer<br/>to re-grant?}
    SetGrantOption -->|Yes| EnableGrantOption[Enable grant option]
    SetGrantOption -->|No| DisableGrantOption[Disable grant option]

    EnableGrantOption --> NotifyConsumer
    DisableGrantOption --> NotifyConsumer

    NotifyConsumer[Notify consumer account<br/>via AWS RAM]

    NotifyConsumer --> ConsumerSide[Consumer Account Actions]

    ConsumerSide --> AcceptShare[Accept resource share<br/>in AWS RAM]
    AcceptShare --> CreateResourceLink[Create resource link<br/>in consumer's catalog]
    CreateResourceLink --> GrantLocal[Grant permissions to<br/>local IAM roles/users]
    GrantLocal --> TestQuery[Test query with Athena]

    TestQuery --> CheckResults{Query successful?}
    CheckResults -->|Yes| Success([Sharing Complete])
    CheckResults -->|No| Debug[Debug:<br/>Check permissions,<br/>KMS keys, bucket policy]
    Debug --> TestQuery

    Success --> Monitor[Monitor:<br/>- Access patterns<br/>- Query costs<br/>- Data freshness]

    style Start fill:#4CAF50
    style Success fill:#4CAF50
    style Debug fill:#F57C00
```

## 7. Metadata Management Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: Table created

    Created --> Discovered: Crawler discovers
    Discovered --> Classified: Schema inferred
    Classified --> Tagged: Tags applied

    Tagged --> Active: Ready for use

    Active --> Queried: Users query data
    Queried --> Active: Continue usage

    Active --> Modified: Schema changed
    Modified --> Validated: Validate changes
    Validated --> Active: Changes approved
    Validated --> Deprecated: Breaking changes

    Active --> Enhanced: Add metadata
    Enhanced --> Active: Metadata updated

    note right of Enhanced
        Enhanced with:
        - Business definitions
        - Owner information
        - Quality metrics
        - Usage statistics
    end note

    Active --> Archived: Data aged out
    Archived --> Deleted: Retention expired

    Deprecated --> Archived: Grace period ended

    Deleted --> [*]

    note left of Active
        Active state includes:
        - Regular queries
        - ETL processing
        - Quality checks
        - Access audits
    end note
```

## 8. Governed Table Operations

```mermaid
sequenceDiagram
    actor User
    participant Spark as Spark/Athena
    participant LF as Lake Formation
    participant Catalog as Data Catalog
    participant S3 as S3 (Iceberg Format)
    participant TxnLog as Transaction Log

    Note over User,TxnLog: INSERT Operation with ACID

    User->>Spark: INSERT INTO governed_table VALUES (...)
    Spark->>LF: Check permissions
    LF-->>Spark: Granted

    Spark->>TxnLog: Begin transaction
    TxnLog-->>Spark: Transaction ID: 12345

    Spark->>Catalog: Get table metadata
    Catalog-->>Spark: Current snapshot ID

    Spark->>S3: Write new data files
    Note over S3: data-file-005.parquet<br/>data-file-006.parquet

    Spark->>S3: Write new manifest
    Note over S3: manifest-003.avro

    Spark->>S3: Write new metadata
    Note over S3: v4.metadata.json<br/>(atomic update)

    Spark->>TxnLog: Commit transaction
    TxnLog->>TxnLog: Validate no conflicts
    TxnLog-->>Spark: Committed

    Spark-->>User: Success

    Note over User,TxnLog: Time Travel Query

    User->>Spark: SELECT * FROM governed_table<br/>AS OF TIMESTAMP '2024-03-07'
    Spark->>Catalog: Get table metadata
    Catalog-->>Spark: Metadata versions

    Spark->>S3: Read v2.metadata.json<br/>(historical version)
    S3-->>Spark: Snapshot from 2024-03-07

    Spark->>S3: Read data files from that snapshot
    S3-->>Spark: Historical data

    Spark-->>User: Results from past version

    Note over User,TxnLog: Concurrent Updates (ACID)

    par User 1 and User 2
        User->>Spark: UPDATE governed_table<br/>SET status='completed'
        Spark->>TxnLog: Begin transaction (T1)
    and
        User->>Spark: UPDATE governed_table<br/>SET amount=amount*1.1
        Spark->>TxnLog: Begin transaction (T2)
    end

    TxnLog->>TxnLog: T1 commits first
    TxnLog-->>Spark: T2 detects conflict
    Spark->>Spark: Retry T2 with latest version
    TxnLog-->>Spark: T2 commits successfully

    Note over User,TxnLog: Both transactions completed<br/>without data corruption
```

## 9. Data Discovery Flow

```mermaid
graph TD
    User[Data Consumer] --> Search{How to find data?}

    Search -->|Browse| Browse[Browse Catalog]
    Search -->|Search| SearchBar[Search by keyword]
    Search -->|Filter| Filter[Filter by tags]

    Browse --> DB[View databases]
    DB --> Tables[View tables]
    Tables --> Schema[View schema]

    SearchBar --> Keywords[Enter: customer, sales, transactions]
    Keywords --> SearchResults[Search results:<br/>10 matching tables]
    SearchResults --> Relevance[Sorted by relevance]

    Filter --> SelectTags[Select filters:<br/>- DataDomain: Sales<br/>- DataSensitivity: Internal<br/>- Owner: FinanceTeam]
    SelectTags --> FilterResults[Filtered results:<br/>5 matching tables]

    Schema --> Review{Suitable?}
    Relevance --> Review
    FilterResults --> Review

    Review -->|No| Search
    Review -->|Yes| CheckAccess{Do I have access?}

    CheckAccess -->|Yes| QueryData[Query data with Athena]
    CheckAccess -->|No| RequestAccess[Request access]

    RequestAccess --> Ticket[Create access ticket]
    Ticket --> Approval{Approved?}
    Approval -->|Yes| GrantAccess[Admin grants permissions]
    Approval -->|No| Denied[Access denied]
    GrantAccess --> QueryData

    QueryData --> SampleQuery[Run sample query]
    SampleQuery --> Validate{Data quality OK?}

    Validate -->|Yes| UseData[Use in analysis/ML/BI]
    Validate -->|No| ReportIssue[Report data quality issue]

    UseData --> Lineage[Check data lineage]
    Lineage --> Understanding[Understand upstream<br/>dependencies]

    Understanding --> Production[Use in production]

    style User fill:#4CAF50
    style QueryData fill:#2196F3
    style UseData fill:#4CAF50
    style Denied fill:#F44336
```

## 10. Cost Optimization Workflow

```mermaid
flowchart TD
    Start([Monitor Costs])

    Start --> Analyze[Analyze cost drivers]

    Analyze --> Crawler[Crawler costs]
    Analyze --> Storage[Storage costs]
    Analyze --> Query[Query costs]

    Crawler --> C1{Crawler running<br/>too frequently?}
    C1 -->|Yes| C1_Fix[Reduce schedule frequency<br/>Use event-driven crawling]
    C1 -->|No| C2{Crawling unnecessary<br/>files?}

    C2 -->|Yes| C2_Fix[Add exclusion patterns<br/>Skip temp directories]
    C2 -->|No| C3{Sampling too high?}

    C3 -->|Yes| C3_Fix[Reduce sample size<br/>5-10% is sufficient]
    C3 -->|No| C_OK[Crawler optimized]

    Storage --> S1{Using efficient<br/>format?}
    S1 -->|No| S1_Fix[Convert to Parquet/ORC<br/>5-10x compression]
    S1 -->|Yes| S2{Partitioning<br/>optimal?}

    S2 -->|No| S2_Fix[Adjust partition strategy<br/>Target 256-512 MB files]
    S2 -->|Yes| S3{Old data<br/>still in hot tier?}

    S3 -->|Yes| S3_Fix[Implement lifecycle policy<br/>Archive to Glacier]
    S3 -->|No| S4{Too many<br/>small files?}

    S4 -->|Yes| S4_Fix[Use governed tables<br/>Automatic compaction]
    S4 -->|No| S_OK[Storage optimized]

    Query --> Q1{Scanning too<br/>much data?}
    Q1 -->|Yes| Q1_Fix[Add partition filters<br/>Select only needed columns]
    Q1 -->|No| Q2{Frequent<br/>aggregations?}

    Q2 -->|Yes| Q2_Fix[Create materialized views<br/>Pre-aggregate in gold layer]
    Q2 -->|No| Q3{Repeated<br/>queries?}

    Q3 -->|Yes| Q3_Fix[Cache results<br/>Use QuickSight SPICE]
    Q3 -->|No| Q_OK[Query optimized]

    C1_Fix --> Measure1[Measure impact]
    C2_Fix --> Measure1
    C3_Fix --> Measure1
    S1_Fix --> Measure1
    S2_Fix --> Measure1
    S3_Fix --> Measure1
    S4_Fix --> Measure1
    Q1_Fix --> Measure1
    Q2_Fix --> Measure1
    Q3_Fix --> Measure1

    C_OK --> Report
    S_OK --> Report
    Q_OK --> Report

    Measure1 --> Report[Generate cost report]

    Report --> Review{Cost reduced<br/>significantly?}
    Review -->|Yes| Success([Cost Optimized])
    Review -->|No| DeepDive[Deep dive analysis<br/>Consider Reserved Capacity]

    DeepDive --> Success

    style Start fill:#FF9900
    style Success fill:#4CAF50
    style C1_Fix fill:#2196F3
    style S1_Fix fill:#2196F3
    style Q1_Fix fill:#2196F3
```

## Usage

These workflow diagrams provide step-by-step guidance for common Data Catalog and Governance operations:

1. **Crawler Scheduling**: Compare different trigger patterns
2. **Permission Grant**: Understand the permission granting sequence
3. **Quality Validation**: Automated data quality workflow
4. **TBAC Setup**: Implement tag-based access control
5. **Lineage Capture**: Where and how lineage is captured
6. **Cross-Account Sharing**: Complete sharing workflow
7. **Metadata Lifecycle**: How metadata evolves over time
8. **Governed Tables**: ACID transactions and time travel
9. **Data Discovery**: How users find and access data
10. **Cost Optimization**: Systematic cost reduction approach
