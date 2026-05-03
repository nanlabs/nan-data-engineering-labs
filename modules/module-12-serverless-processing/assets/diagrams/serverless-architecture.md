# Arquitectura Serverless para Data Engineering

## Arquitectura Completa Serverless Data Platform

```mermaid
flowchart TB
    subgraph Sources["📥 Data Sources"]
        API[External APIs]
        DB[(Databases)]
        Files[File Uploads]
        Stream[Stream Data]
    end

    subgraph Ingestion["🔄 Data Ingestion"]
        APIGateway[API Gateway<br/>REST/WebSocket]
        EventBridge[EventBridge<br/>Event Bus]
        Kinesis[Kinesis Data<br/>Streams]
        S3Event[S3 Event<br/>Notifications]
    end

    subgraph Processing["⚙️ Processing Layer"]
        Lambda1[Lambda<br/>Data Extractor]
        Lambda2[Lambda<br/>Data Transformer]
        Lambda3[Lambda<br/>Data Validator]
        Lambda4[Lambda<br/>Data Loader]
        Glue[AWS Glue<br/>ETL Jobs]
        Athena[Amazon Athena<br/>Query Engine]
    end

    subgraph Orchestration["🎯 Orchestration"]
        StepFunctions[Step Functions<br/>Workflow Engine]
        EventRule[EventBridge Rules<br/>Cron/Event-driven]
    end

    subgraph Storage["💾 Data Storage"]
        S3Raw[S3 - Raw Data<br/>Landing Zone]
        S3Processed[S3 - Processed<br/>Data Lake]
        DynamoDB[(DynamoDB<br/>Metadata)]
        RDS[(RDS Serverless<br/>Analytics DB)]
    end

    subgraph Analytics["📊 Analytics & Serving"]
        Redshift[(Redshift<br/>Serverless)]
        QuickSight[QuickSight<br/>BI Dashboard]
        AppSync[AppSync<br/>GraphQL API]
    end

    subgraph Monitoring["🔍 Monitoring"]
        CloudWatch[CloudWatch<br/>Logs & Metrics]
        XRay[X-Ray<br/>Distributed Tracing]
        SNS[SNS<br/>Notifications]
    end

    API --> APIGateway
    DB --> EventBridge
    Files --> S3Event
    Stream --> Kinesis

    APIGateway --> Lambda1
    EventBridge --> StepFunctions
    Kinesis --> Lambda1
    S3Event --> Lambda1

    Lambda1 --> S3Raw
    S3Raw --> Lambda2
    Lambda2 --> Lambda3
    Lambda3 --> Lambda4
    Lambda4 --> S3Processed

    StepFunctions --> Lambda1
    StepFunctions --> Lambda2
    StepFunctions --> Lambda3
    StepFunctions --> Lambda4
    StepFunctions --> Glue

    EventRule --> StepFunctions
    EventRule --> Lambda1

    S3Processed --> Athena
    Lambda4 --> DynamoDB
    Lambda4 --> RDS

    Athena --> Redshift
    S3Processed --> Redshift
    Redshift --> QuickSight

    DynamoDB --> AppSync
    AppSync --> QuickSight

    Lambda1 -.-> CloudWatch
    Lambda2 -.-> CloudWatch
    Lambda3 -.-> CloudWatch
    Lambda4 -.-> CloudWatch
    Glue -.-> CloudWatch
    StepFunctions -.-> CloudWatch

    Lambda1 -.-> XRay
    Lambda2 -.-> XRay
    Lambda3 -.-> XRay
    Lambda4 -.-> XRay

    CloudWatch -.-> SNS
    StepFunctions -.-> SNS

    style Sources fill:#E1F5FF
    style Processing fill:#E8F5E9
    style Storage fill:#87CEEB
    style Analytics fill:#FFF3E0
    style Monitoring fill:#FFE1E1
```

## Lambda ETL Pipeline Flow

```mermaid
sequenceDiagram
    participant S3 as S3 Bucket<br/>(Raw Data)
    participant Lambda1 as Lambda<br/>Extractor
    participant Lambda2 as Lambda<br/>Transformer
    participant Lambda3 as Lambda<br/>Validator
    participant Lambda4 as Lambda<br/>Loader
    participant DDB as DynamoDB
    participant S3P as S3 Bucket<br/>(Processed)
    participant SNS as SNS Topic

    Note over S3: New file uploaded
    S3->>Lambda1: S3 Event Trigger
    activate Lambda1
    Lambda1->>Lambda1: Read & Parse Data
    Lambda1->>DDB: Log Extract Metadata
    Lambda1->>Lambda2: Invoke Async
    deactivate Lambda1

    activate Lambda2
    Lambda2->>Lambda2: Transform Data<br/>- Clean nulls<br/>- Type conversion<br/>- Enrichment
    Lambda2->>DDB: Update Processing Status
    Lambda2->>Lambda3: Invoke Sync

    activate Lambda3
    Lambda3->>Lambda3: Validate Data<br/>- Schema check<br/>- Business rules<br/>- Quality checks
    Lambda3-->>Lambda2: Validation Result
    deactivate Lambda3

    Lambda2->>Lambda4: Pass Validated Data
    deactivate Lambda2

    activate Lambda4
    Lambda4->>S3P: Write Parquet Files
    Lambda4->>DDB: Update Final Status
    Lambda4->>SNS: Success Notification
    deactivate Lambda4

    Note over S3P: Data ready for<br/>analytics
```

## Step Functions State Machine para ETL Complejo

```mermaid
flowchart TD
    Start([Start Execution]) --> Extract[Extract State<br/>Lambda: extract-data]

    Extract --> ExtractCheck{Success?}
    ExtractCheck -->|No| ExtractRetry[Retry 3x]
    ExtractRetry --> ExtractCheck
    ExtractCheck -->|Failed| HandleError[Error Handler<br/>Lambda: handle-error]

    ExtractCheck -->|Yes| Parallel[Parallel State<br/>Multiple Transforms]

    Parallel --> Transform1[Transform Sales<br/>Lambda: transform-sales]
    Parallel --> Transform2[Transform Customers<br/>Lambda: transform-customers]
    Parallel --> Transform3[Transform Products<br/>Lambda: transform-products]

    Transform1 --> Wait1[Wait for All]
    Transform2 --> Wait1
    Transform3 --> Wait1

    Wait1 --> Validate[Validate State<br/>Lambda: validate-data]

    Validate --> ValidCheck{Valid Data?}
    ValidCheck -->|No| Quarantine[Move to Quarantine<br/>Lambda: quarantine-data]
    ValidCheck -->|Yes| Load[Load State<br/>Lambda: load-data]

    Load --> LoadCheck{Success?}
    LoadCheck -->|No| LoadRetry[Retry 3x]
    LoadRetry --> LoadCheck
    LoadCheck -->|Failed| HandleError

    LoadCheck -->|Yes| UpdateCatalog[Update Data Catalog<br/>Lambda: update-catalog]

    UpdateCatalog --> Notify[Send Notification<br/>SNS Topic]

    Notify --> Success([Success])

    Quarantine --> NotifyError[Send Error Alert<br/>SNS Topic]
    HandleError --> NotifyError
    NotifyError --> Failed([Failed])

    style Start fill:#90EE90
    style Success fill:#90EE90
    style Failed fill:#FF6347
    style Parallel fill:#FFD700
    style HandleError fill:#FF9800
```

## Event-Driven Architecture con EventBridge

```mermaid
flowchart LR
    subgraph Producers["Event Producers"]
        App1[Application<br/>Microservice]
        S3[S3 Bucket]
        DDB[DynamoDB<br/>Streams]
        Schedule[Scheduled<br/>Events]
    end

    subgraph EventBridge["Amazon EventBridge"]
        Bus[Default Event Bus]
        CustomBus[Custom Event Bus]

        Rule1[Rule: Data Ingestion]
        Rule2[Rule: Data Quality]
        Rule3[Rule: Daily ETL]
        Rule4[Rule: Error Handler]
    end

    subgraph Consumers["Event Consumers"]
        Lambda1[Lambda<br/>Process Data]
        Lambda2[Lambda<br/>Quality Check]
        StepFunc[Step Functions<br/>ETL Workflow]
        SQS[SQS Queue<br/>Dead Letter]
        SNS[SNS Topic<br/>Alerts]
    end

    App1 --> Bus
    S3 --> Bus
    DDB --> Bus
    Schedule --> CustomBus

    Bus --> Rule1
    Bus --> Rule2
    Bus --> Rule4
    CustomBus --> Rule3

    Rule1 --> Lambda1
    Rule2 --> Lambda2
    Rule3 --> StepFunc
    Rule4 --> SQS

    Lambda1 -.-> SNS
    Lambda2 -.-> SNS
    StepFunc -.-> SNS
    SQS -.-> SNS

    style EventBridge fill:#FF9800
    style Producers fill:#E1F5FF
    style Consumers fill:#E8F5E9
```

## Lambda Layer Architecture para Data Processing

```mermaid
graph TB
    subgraph Lambda["Lambda Function"]
        Handler[Handler Code<br/>etl_handler.py]
    end

   subgraph Layers["Lambda Layers (Shared)"]
        Layer1[Data Processing Layer<br/>pandas, numpy<br/>pyarrow]
        Layer2[AWS SDK Layer<br/>boto3, botocore]
        Layer3[Utilities Layer<br/>Common functions<br/>validators]
        Layer4[Connectors Layer<br/>Database drivers<br/>API clients]
    end

    Handler --> Layer1
    Handler --> Layer2
    Handler --> Layer3
    Handler --> Layer4

    subgraph Runtime["Runtime Environment"]
        Python[Python 3.11 Runtime]
        Memory[Memory: 1024 MB]
        Timeout[Timeout: 15 min]
        Ephemeral[Ephemeral Storage:<br/>512 MB - 10 GB]
    end

    Layer1 --> Python
    Layer2 --> Python
    Layer3 --> Python
    Layer4 --> Python

    Handler --> Memory
    Handler --> Timeout
    Handler --> Ephemeral

    style Lambda fill:#FFD700
    style Layers fill:#87CEEB
    style Runtime fill:#E8F5E9
```

## Serverless Data Lake Zones

```mermaid
flowchart TB
    subgraph Raw["🔴 Raw Zone (Bronze)"]
        S3Raw[S3 Bucket: raw-data-lake<br/>- Original format<br/>- Immutable<br/>- Lifecycle: 90 days → Glacier]
    end

    subgraph Curated["🟡 Curated Zone (Silver)"]
        S3Curated[S3 Bucket: curated-data-lake<br/>- Cleaned & validated<br/>- Parquet format<br/>- Partitioned by date]
        GlueCatalog1[Glue Data Catalog<br/>- Schema registry<br/>- Table definitions]
    end

    subgraph Analytics["🟢 Analytics Zone (Gold)"]
        S3Analytics[S3 Bucket: analytics-data-lake<br/>- Aggregated data<br/>- Optimized for queries<br/>- Partitioned by use case]
        GlueCatalog2[Glue Data Catalog<br/>- Business views<br/>- Aggregated tables]
    end

    subgraph Processing["Processing"]
        Lambda[Lambda Functions<br/>Lightweight transforms]
        Glue[Glue ETL Jobs<br/>Heavy processing]
        Athena[Athena<br/>Ad-hoc queries]
    end

    Sources[Data Sources] --> Lambda
    Lambda --> S3Raw

    S3Raw --> Glue
    Glue --> S3Curated
    S3Curated --> GlueCatalog1

    S3Curated --> Glue
    Glue --> S3Analytics
    S3Analytics --> GlueCatalog2

    GlueCatalog1 --> Athena
    GlueCatalog2 --> Athena

    Athena --> Analytics[Analytics Tools]

    style Raw fill:#FFE1E1
    style Curated fill:#FFF3E0
    style Analytics fill:#E8F5E9
```

## Lambda Cost Optimization Strategies

```mermaid
flowchart TD
    Start([Lambda Cost<br/>Optimization]) --> Strategy{Optimization<br/>Strategy}

    Strategy --> RightSize[Right-Sizing]
    Strategy --> ColdStart[Cold Start<br/>Reduction]
    Strategy --> Provisioned[Provisioned<br/>Concurrency]
    Strategy --> Async[Async Invocation]

    RightSize --> Memory[Optimize Memory<br/>128MB - 10GB]
    Memory --> PowerTuning[AWS Lambda<br/>Power Tuning Tool]
    PowerTuning --> Benchmark[Benchmark<br/>Cost vs Performance]

    ColdStart --> Layer[Use Layers<br/>Share Dependencies]
    ColdStart --> Package[Minimize Package<br/>Size]
    ColdStart --> SnapStart[SnapStart<br/>Java/.NET]

    Provisioned --> Critical[Critical Workloads<br/>Guaranteed Performance]
    Critical --> Schedule[Schedule Provisioned<br/>Capacity]

    Async --> SQS[SQS Integration<br/>Buffer & Batch]
    Async --> EventBridge[EventBridge<br/>Decouple]

    Benchmark --> Monitor[Monitor CloudWatch<br/>Cost & Duration]
    Layer --> Monitor
    Package --> Monitor
    SnapStart --> Monitor
    Schedule --> Monitor
    SQS --> Monitor
    EventBridge --> Monitor

    Monitor --> Savings[Cost Savings:<br/>30-50% typical]

    style Start fill:#E1F5FF
    style Savings fill:#90EE90
    style Monitor fill:#FFD700
```

## Serverless Observability Stack

```mermaid
flowchart TB
    subgraph Apps["Serverless Apps"]
        Lambda1[Lambda Functions]
        StepFunc[Step Functions]
        APIGateway[API Gateway]
        AppSync[AppSync]
    end

    subgraph Logging["📝 Logging"]
        CWLogs[CloudWatch Logs]
        LogInsights[CloudWatch Logs<br/>Insights]
        LogGroups[Log Groups<br/>by Function]
    end

    subgraph Metrics["📊 Metrics"]
        CWMetrics[CloudWatch Metrics]
        Dashboard[CloudWatch<br/>Dashboards]
        CustomMetrics[Custom Business<br/>Metrics]
    end

    subgraph Tracing["🔍 Distributed Tracing"]
        XRay[AWS X-Ray]
        ServiceMap[Service Map]
        TraceAnalysis[Trace Analysis]
    end

    subgraph Alerting["🚨 Alerting"]
        Alarms[CloudWatch Alarms]
        SNS[SNS Topics]
        EventBridge[EventBridge Rules]
        PagerDuty[PagerDuty<br/>Integration]
    end

    Lambda1 --> CWLogs
    StepFunc --> CWLogs
    APIGateway --> CWLogs
    AppSync --> CWLogs

    CWLogs --> LogInsights
    CWLogs --> LogGroups

    Lambda1 --> CWMetrics
    StepFunc --> CWMetrics
    APIGateway --> CWMetrics

    CWMetrics --> Dashboard
    CWMetrics --> CustomMetrics

    Lambda1 --> XRay
    StepFunc --> XRay
    APIGateway --> XRay

    XRay --> ServiceMap
    XRay --> TraceAnalysis

    CWMetrics --> Alarms
    CustomMetrics --> Alarms

    Alarms --> SNS
    Alarms --> EventBridge
    SNS --> PagerDuty

    style Logging fill:#E1F5FF
    style Metrics fill:#E8F5E9
    style Tracing fill:#FFF3E0
    style Alerting fill:#FFE1E1
```

## Uso

Estos diagramas muestran:
1. Arquitectura completa de una plataforma de datos serverless
2. Flujo de ejecución de un pipeline ETL con Lambda
3. Step Functions para orquestación compleja con manejo de errores
4. Arquitectura event-driven con EventBridge
5. Estructura de Lambda Layers para compartir código
6. Zonas del data lake (Bronze, Silver, Gold)
7. Estrategias de optimización de costos
8. Stack de observabilidad serverless

Para más información, consulta la [documentación de AWS Lambda](https://docs.aws.amazon.com/lambda/) y [AWS Step Functions](https://docs.aws.amazon.com/step-functions/).
