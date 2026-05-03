# Step Functions - Patrones de Orquestación

## Patrones Comunes de Step Functions

```mermaid
flowchart TB
    Start([Patrones de<br/>Step Functions]) --> P1[Sequential<br/>Processing]
    Start --> P2[Parallel<br/>Processing]
    Start --> P3[Map State<br/>Dynamic Parallelism]
    Start --> P4[Choice State<br/>Conditional Logic]
    Start --> P5[Wait State<br/>Delays & Polling]
    Start --> P6[Saga Pattern<br/>Distributed Transactions]

    P1 --> S1[Task 1 →<br/>Task 2 →<br/>Task 3]
    P2 --> S2[Task A<br/>Task B ← Parallel<br/>Task C]
    P3 --> S3[Process Array<br/>1000 items<br/>Each in parallel]
    P4 --> S4[If/Else<br/>Switch/Case<br/>Branching]
    P5 --> S5[Scheduled Delay<br/>Wait for Callback<br/>Poll Status]
    P6 --> S6[Transaction +<br/>Compensating<br/>Actions]

    style Start fill:#E1F5FF
    style P1 fill:#E8F5E9
    style P2 fill:#FFF3E0
    style P3 fill:#FFE1E1
    style P4 fill:#E1F5FF
    style P5 fill:#F3E5F5
    style P6 fill:#FFF9C4
```

## Sequential Processing Pattern

```mermaid
stateDiagram-v2
    [*] --> ValidateInput
    ValidateInput --> FetchData: Valid
    ValidateInput --> NotifyError: Invalid
    FetchData --> TransformData
    TransformData --> EnrichData
    EnrichData --> ValidateOutput
    ValidateOutput --> SaveResults: Valid
    ValidateOutput --> NotifyError: Invalid
    SaveResults --> UpdateMetadata
    UpdateMetadata --> SendNotification
    SendNotification --> [*]
    NotifyError --> [*]

    note right of FetchData
        Lambda: fetch-data
        Timeout: 5 min
        Retry: 3 attempts
    end note

    note right of TransformData
        Lambda: transform-data
        Memory: 2048 MB
        Timeout: 10 min
    end note
```

## Parallel Processing Pattern

```mermaid
flowchart TD
    Start([Start]) --> Input[Receive Event]
    Input --> Parallel{Parallel State}

    Parallel -->|Branch 1| Sales[Process Sales Data]
    Parallel -->|Branch 2| Customers[Process Customer Data]
    Parallel -->|Branch 3| Products[Process Product Data]
    Parallel -->|Branch 4| Inventory[Process Inventory Data]

    Sales --> SalesDB[(Write to<br/>Sales Table)]
    Customers --> CustomerDB[(Write to<br/>Customer Table)]
    Products --> ProductDB[(Write to<br/>Product Table)]
    Inventory --> InventoryDB[(Write to<br/>Inventory Table)]

    SalesDB --> Join[Join Results]
    CustomerDB --> Join
    ProductDB --> Join
    InventoryDB --> Join

    Join --> Aggregate[Aggregate Metrics]
    Aggregate --> Notify[Send Completion<br/>Notification]
    Notify --> End([Success])

    Sales -.->|Error| ErrorHandler[Error Handler]
    Customers -.->|Error| ErrorHandler
    Products -.->|Error| ErrorHandler
    Inventory -.->|Error| ErrorHandler

    ErrorHandler --> Failed([Failed])

    style Parallel fill:#FFD700
    style Join fill:#87CEEB
    style ErrorHandler fill:#FF6347
```

## Map State Pattern - Dynamic Parallelism

```mermaid
flowchart TB
    Start([Start]) --> GetList[Get List of Files<br/>Lambda: list-files]
    GetList --> Count{Count Items}

    Count -->|0 items| Empty[Log: No Files]
    Empty --> End1([End])

    Count -->|1-1000 items| Map[Map State<br/>MaxConcurrency: 40]

    Map --> ProcessItem[Process Each File<br/>Lambda: process-file]

    ProcessItem --> Validate{Validate<br/>Result}
    Validate -->|Success| Success[Success Counter]
    Validate -->|Failure| Failure[Failure Counter]

    Success --> Collect[Collect Results]
    Failure --> Quarantine[Move to Quarantine]
    Quarantine --> Collect

    Collect --> Summary[Generate Summary<br/>Lambda: create-summary]
    Summary --> Report[Send Report<br/>SNS Notification]
    Report --> End2([End])

    Count -->|>1000 items| Batch[Batch Processing]
    Batch --> Split[Split into Chunks<br/>of 1000]
    Split --> ChildExec[Start Child<br/>Executions]
    ChildExec --> End3([End])

    style Map fill:#87CEEB
    style ProcessItem fill:#90EE90
    style Batch fill:#FFD700
```

## Choice State Pattern - Conditional Logic

```mermaid
flowchart TD
    Start([Start]) --> Extract[Extract Data<br/>Lambda: extract]
    Extract --> Check{Data Size?}

    Check -->|< 1 MB| Small[Small File Path]
    Check -->|1-100 MB| Medium[Medium File Path]
    Check -->|> 100 MB| Large[Large File Path]

    Small --> LambdaProc[Lambda Processing<br/>Quick transform]
    Medium --> GlueJob[Glue Job<br/>Standard processing]
    Large --> EMR[EMR Cluster<br/>Heavy processing]

    LambdaProc --> ValidateSmall{Valid?}
    GlueJob --> ValidateMed{Valid?}
    EMR --> ValidateLarge{Valid?}

    ValidateSmall -->|Yes| LoadSmall[Load to DynamoDB]
    ValidateSmall -->|No| ErrorSmall[Error Queue]

    ValidateMed -->|Yes| LoadMed[Load to RDS]
    ValidateMed -->|No| ErrorMed[Error Queue]

    ValidateLarge -->|Yes| LoadLarge[Load to Redshift]
    ValidateLarge -->|No| ErrorLarge[Error Queue]

    LoadSmall --> Success([Success])
    LoadMed --> Success
    LoadLarge --> Success

    ErrorSmall --> HandleError[Error Handler]
    ErrorMed --> HandleError
    ErrorLarge --> HandleError
    HandleError --> Failed([Failed])

    style Check fill:#FFD700
    style Small fill:#E8F5E9
    style Medium fill:#FFF3E0
    style Large fill:#FFE1E1
```

## Wait State Pattern - Delays & Callbacks

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Lambda as Lambda
    participant External as External System
    participant SQS as SQS Queue

    Note over SF: Start Execution
    SF->>Lambda: 1. Start Long Process
    activate Lambda
    Lambda->>External: 2. Submit Job
    External-->>Lambda: 3. Job ID
    Lambda-->>SF: 4. Return Job ID + Token
    deactivate Lambda

    Note over SF: Wait for Callback<br/>with Task Token

    External->>External: 5. Process Job<br/>(30 min)

    External->>SQS: 6. Job Complete Event
    SQS->>Lambda: 7. Trigger Lambda
    activate Lambda
    Lambda->>SF: 8. SendTaskSuccess<br/>with Token
    deactivate Lambda

    SF->>Lambda: 9. Validate Results
    activate Lambda
    Lambda-->>SF: 10. Validation OK
    deactivate Lambda

    Note over SF: Continue Execution
    SF->>Lambda: 11. Load Data
    Note over SF: End Execution
```

## Saga Pattern - Distributed Transactions

```mermaid
flowchart TB
    Start([Start Transaction]) --> Reserve[Reserve Inventory<br/>Lambda: reserve-inventory]
    Reserve --> ReserveCheck{Success?}

    ReserveCheck -->|Yes| Charge[Charge Payment<br/>Lambda: charge-payment]
    ReserveCheck -->|No| Fail1[Transaction Failed]

    Charge --> ChargeCheck{Success?}
    ChargeCheck -->|Yes| Ship[Ship Order<br/>Lambda: ship-order]
    ChargeCheck -->|No| Compensate1[Compensate:<br/>Release Inventory]

    Ship --> ShipCheck{Success?}
    ShipCheck -->|Yes| Notify[Notify Customer<br/>Success]
    ShipCheck -->|No| Compensate2[Compensate:<br/>Refund Payment +<br/>Release Inventory]

    Notify --> Success([Success])

    Compensate1 --> Fail2[Transaction Failed<br/>Compensated]
    Compensate2 --> Fail3[Transaction Failed<br/>Compensated]

    Fail1 --> End1([End])
    Fail2 --> End2([End])
    Fail3 --> End3([End])

    style Reserve fill:#E8F5E9
    style Charge fill:#E8F5E9
    style Ship fill:#E8F5E9
    style Compensate1 fill:#FFE1E1
    style Compensate2 fill:#FFE1E1
    style Success fill:#90EE90
```

## Error Handling & Retry Pattern

```mermaid
flowchart TD
    Start([Task Execution]) --> Execute[Execute Lambda]
    Execute --> Result{Result}

    Result -->|Success| Success([Success])
    Result -->|Error| ErrorType{Error Type}

    ErrorType -->|Retryable| Retry{Retry Count}
    ErrorType -->|Non-Retryable| Catch[Catch Block]

    Retry -->|< 3 attempts| Backoff[Exponential<br/>Backoff]
    Backoff --> Wait[Wait<br/>2^attempt seconds]
    Wait --> Execute

    Retry -->|≥ 3 attempts| Catch

    Catch --> Fallback{Fallback<br/>Available?}
    Fallback -->|Yes| Alternative[Execute<br/>Alternative Path]
    Fallback -->|No| Cleanup[Cleanup Resources]

    Alternative --> AltResult{Result}
    AltResult -->|Success| PartialSuccess([Partial Success])
    AltResult -->|Error| Cleanup

    Cleanup --> Log[Log Error Details]
    Log --> Alert[Send Alert<br/>SNS/PagerDuty]
    Alert --> Failed([Failed])

    style Execute fill:#E8F5E9
    style Retry fill:#FFD700
    style Catch fill:#FF9800
    style Failed fill:#FF6347
    style Success fill:#90EE90
```

## Cost Optimization Pattern

```mermaid
flowchart TB
    Start([Start Workflow]) --> Classify[Classify Workload<br/>Lambda: classify]

    Classify --> Priority{Priority<br/>Level?}

    Priority -->|High| SyncPath[Synchronous Path]
    Priority -->|Normal| AsyncPath[Asynchronous Path]
    Priority -->|Low| BatchPath[Batch Path]

    SyncPath --> Express[Express Workflow<br/>< 5 min duration<br/>High throughput]
    Express --> FastProcess[Fast Processing<br/>Small memory]

    AsyncPath --> Standard[Standard Workflow<br/>< 1 year duration<br/>Exactly-once]
    Standard --> NormalProcess[Normal Processing<br/>Optimized memory]

    BatchPath --> Scheduled[EventBridge Schedule<br/>Off-peak hours]
    Scheduled --> BatchProcess[Batch Processing<br/>Larger memory<br/>Longer timeout]

    FastProcess --> Result1[Result]
    NormalProcess --> Result1
    BatchProcess --> Result1

    Result1 --> Cache{Cache<br/>Results?}
    Cache -->|Yes| DynamoDB[(DynamoDB<br/>TTL enabled)]
    Cache -->|No| End

    DynamoDB --> End([End])

    style Express fill:#90EE90
    style Standard fill:#87CEEB
    style Scheduled fill:#FFD700

    Note1[Cost: $$$]
    Note2[Cost: $$]
    Note3[Cost: $]

    Express -.-> Note1
    Standard -.-> Note2
    Scheduled -.-> Note3
```

## Human Approval Pattern

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Lambda as Lambda
    participant SNS as SNS Topic
    participant Human as Human Approver
    participant API as API Gateway

    Note over SF: Start Workflow
    SF->>Lambda: 1. Prepare Approval Request
    activate Lambda
    Lambda-->>SF: 2. Approval Details
    deactivate Lambda

    SF->>SNS: 3. Send Approval Email<br/>with Task Token
    SNS->>Human: 4. Email with Approve/Reject Links

    Note over SF: Wait for Task Token<br/>(Timeout: 24 hours)

    Human->>API: 5. Click Approve/Reject
    API->>Lambda: 6. Process Response
    activate Lambda
    Lambda->>SF: 7. SendTaskSuccess/Failure<br/>with Token
    deactivate Lambda

    alt Approved
        SF->>Lambda: 8a. Execute Approved Action
        Note over SF: Continue normal flow
    else Rejected
        SF->>Lambda: 8b. Execute Rejection Handler
        Note over SF: Cleanup and notify
    else Timeout
        SF->>Lambda: 8c. Execute Timeout Handler
        Note over SF: Escalate to manager
    end

    Note over SF: End Workflow
```

## Comparison: Express vs Standard Workflows

```mermaid
graph TB
    subgraph Express["⚡ Express Workflows"]
        ExpressProps[Properties:<br/>- Duration: ≤ 5 min<br/>- Execution rate: 100k+/sec<br/>- Pricing: Per execution<br/>- History: CloudWatch only<br/>- Execution semantics:<br/>  At-least-once]

        ExpressUse[Use Cases:<br/>- High-volume processes<br/>- IoT data ingestion<br/>- Mobile backends<br/>- Streaming transformations<br/>- Microservices orchestration]
    end

    subgraph Standard["🔒 Standard Workflows"]
        StandardProps[Properties:<br/>- Duration: ≤ 1 year<br/>- Execution rate: 2k/sec<br/>- Pricing: Per state transition<br/>- History: Full audit trail<br/>- Execution semantics:<br/>  Exactly-once]

        StandardUse[Use Cases:<br/>- Long-running processes<br/>- Human approvals<br/>- ETL pipelines<br/>- Order processing<br/>- Complex orchestrations]
    end

    Compare{Choose Based On}

    Compare --> Duration{Duration?}
    Compare --> Rate{Execution<br/>Rate?}
    Compare --> Audit{Audit<br/>Required?}
    Compare --> Cost{Cost<br/>Priority?}

    Duration -->|< 5 min| Express
    Duration -->|> 5 min| Standard

    Rate -->|> 2k/sec| Express
    Rate -->|< 2k/sec| Standard

    Audit -->|Yes| Standard
    Audit -->|No| Express

    Cost -->|Volume| Express
    Cost -->|Complexity| Standard

    style Express fill:#E8F5E9
    style Standard fill:#E1F5FF
```

## Uso

Estos diagramas muestran:
1. Patrones comunes de orquestación con Step Functions
2. Sequential processing para workflows lineales
3. Parallel processing para tareas independientes
4. Map state para procesamiento dinámico de arrays
5. Choice state para lógica condicional
6. Wait state y callbacks para procesos asíncronos
7. Saga pattern para transacciones distribuidas
8. Manejo de errores y reintentos
9. Optimización de costos según prioridad
10. Human approval pattern con task tokens
11. Comparación Express vs Standard workflows

Para más información, consulta la [documentación de AWS Step Functions](https://docs.aws.amazon.com/step-functions/).
