# Module 01: Cloud Fundamentals - Architecture Diagrams

## S3 Bucket Structure

```mermaid
graph TD
    A[quickmart-data-lake-raw] --> B[logs/]
    A --> C[transactions/]
    A --> D[uploads/]
    A --> E[processed/]

    B --> B1[app-logs-2024-01-15.json]
    B --> B2[app-logs-2024-01-16.json]

    C --> C1[transactions-2024-01-15.csv]
    C --> C2[transactions-2024-01-16.csv]

    D --> D1[incoming files]
    D --> D2[triggers Lambda]

    E --> E1[validated/]
    E --> E2[transformed/]

    style A fill:#f9f,stroke:#333,stroke-width:4px
    style D fill:#ff9,stroke:#333,stroke-width:2px
```

## IAM Hierarchy

```mermaid
graph TB
    subgraph "IAM Groups"
        G1[data-engineers]
        G2[data-analysts]
        G3[ml-scientists]
    end

    subgraph "IAM Policies"
        P1[DataEngineerPolicy]
        P2[DataAnalystPolicy]
        P3[MLScientistPolicy]
    end

    subgraph "IAM Users"
        U1[alice.engineer]
        U2[bob.engineer]
        U3[carol.analyst]
        U4[david.analyst]
        U5[eve.scientist]
    end

    G1 --> P1
    G2 --> P2
    G3 --> P3

    U1 --> G1
    U2 --> G1
    U3 --> G2
    U4 --> G2
    U5 --> G3

    style P1 fill:#9f9,stroke:#333
    style P2 fill:#99f,stroke:#333
    style P3 fill:#f99,stroke:#333
```

## S3 Lifecycle Transitions

```mermaid
graph LR
    A[STANDARD<br/>0-30 days<br/>$0.023/GB] -->|After 30 days| B[STANDARD_IA<br/>30-90 days<br/>$0.0125/GB]
    B -->|After 90 days| C[GLACIER<br/>90-365 days<br/>$0.004/GB]
    C -->|After 365 days| D[DELETED<br/>Expired]

    style A fill:#f66
    style B fill:#f96
    style C fill:#69f
    style D fill:#999
```

## Event-Driven Architecture

```mermaid
sequenceDiagram
    participant U as User/App
    participant S3 as S3 Bucket
    participant SQS as SQS Queue
    participant L as Lambda Function
    participant DB as DynamoDB/RDS

    U->>S3: Upload file
    S3->>SQS: Send ObjectCreated event
    SQS->>L: Trigger Lambda
    L->>S3: Download file
    L->>L: Process data
    L->>DB: Store results
    L->>SQS: Delete message

    Note over S3,L: Async processing
```

## Data Flow - Exercise 01

```mermaid
flowchart TD
    Start([Student begins]) --> Read[Read scenario.md]
    Read --> Copy[Copy starter to my_solution]
    Copy --> Impl[Implement TODOs]

    Impl --> Test{Tests pass?}
    Test -->|No| Hints[Check hints.md]
    Hints --> Impl

    Test -->|Yes| Val[Run validation]
    Val --> Done([Exercise Complete])

    style Start fill:#9f9
    style Done fill:#9f9
    style Test fill:#ff9
```

## CloudFormation Stack Resources

```mermaid
graph TD
    Stack[CloudFormation Stack:<br/>quickmart-data-lake] --> S3[S3 Bucket]
    Stack --> IAM[IAM Role]
    Stack --> Lambda[Lambda Function]
    Stack --> SQS[SQS Queue]

    IAM --> Lambda
    S3 --> Lambda
    Lambda --> SQS

    Stack --> Out1[Output: BucketName]
    Stack --> Out2[Output: LambdaARN]

    style Stack fill:#f9f,stroke:#333,stroke-width:3px
```

## Cost Optimization Strategy

```mermaid
graph TB
    subgraph "Before Optimization"
        B1[10 TB in STANDARD<br/>$230/month]
    end

    subgraph "After Optimization"
        A1[1 TB STANDARD<br/>0-30 days<br/>$23/month]
        A2[2 TB STANDARD_IA<br/>30-90 days<br/>$25/month]
        A3[7 TB GLACIER<br/>90-365 days<br/>$28/month]
        Total[Total: $76/month<br/>67% SAVINGS]
    end

    B1 -.->|Lifecycle Policy| A1
    B1 -.->|Lifecycle Policy| A2
    B1 -.->|Lifecycle Policy| A3

    A1 --> Total
    A2 --> Total
    A3 --> Total

    style B1 fill:#f66
    style Total fill:#9f9,stroke:#333,stroke-width:3px
```

## Module 01 Learning Path

```mermaid
journey
    title Student Journey - Module 01
    section Theory
      Read concepts.md: 5: Student
      Read architecture.md: 4: Student
      Review resources: 3: Student
    section Exercises
      Exercise 01 (S3 Basics): 5: Student
      Exercise 02 (IAM): 4: Student
      Exercise 03 (S3 Advanced): 4: Student
      Exercise 04 (Lambda): 3: Student
      Exercise 05 (CloudFormation): 3: Student
      Exercise 06 (Cost): 4: Student
    section Validation
      Run validate.sh: 5: Student
      Module Complete: 5: Student
```

---

## Usage

These diagrams are rendered automatically in GitHub/GitLab Markdown viewers.

To render locally:
- Use VSCode with Markdown Preview Mermaid Support extension
- Use [Mermaid Live Editor](https://mermaid.live/)
- Export as PNG/SVG for documentation
