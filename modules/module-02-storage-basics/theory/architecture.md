# Storage Architecture Patterns

**Visual Guide to Data Storage Architectures**

## Table of Contents

1. [Medallion Architecture Diagram](#medallion-architecture-diagram)
2. [File Format Decision Tree](#file-format-decision-tree)
3. [Partitioning Strategies](#partitioning-strategies)
4. [S3 Storage Classes](#s3-storage-classes)
5. [Data Flow Patterns](#data-flow-patterns)
6. [Compression Pipeline](#compression-pipeline)
7. [Schema Evolution Workflow](#schema-evolution-workflow)

## Medallion Architecture Diagram

```mermaid
graph TB
    subgraph Sources
        API[REST APIs]
        DB[(Databases)]
        FILES[File Uploads]
        STREAM[Event Streams]
    end

    subgraph Bronze["🥉 BRONZE LAYER (Raw Zone)"]
        direction TB
        B_S3[("S3: Raw Data<br/>Format: CSV, JSON<br/>Compression: Gzip<br/>Retention: 2 years")]
        B_SCHEMA["Schema: Flexible<br/>Validation: None<br/>Dedup: No"]

        B_S3 --> B_SCHEMA
    end

    subgraph Silver["🥈 SILVER LAYER (Cleaned Zone)"]
        direction TB
        S_S3[("S3: Validated Data<br/>Format: Parquet<br/>Compression: Snappy<br/>Retention: 1 year")]
        S_SCHEMA["Schema: Enforced<br/>Validation: ✓<br/>Dedup: ✓"]
        S_PARTITION["Partitioning:<br/>year/month/day"]

        S_S3 --> S_SCHEMA --> S_PARTITION
    end

    subgraph Gold["🥇 GOLD LAYER (Curated Zone)"]
        direction TB
        G_S3[("S3: Analytics-Ready<br/>Format: Parquet<br/>Compression: Snappy<br/>Retention: 3 years")]
        G_AGG["Aggregations<br/>Business Logic<br/>Feature Engineering"]
        G_OPT["Optimization:<br/>Z-ordering<br/>Compaction"]

        G_S3 --> G_AGG --> G_OPT
    end

    subgraph Consumers
        ATHENA[Athena<br/>SQL Queries]
        SPARK[Spark<br/>Processing]
        ML[ML Models<br/>Training]
        BI[BI Tools<br/>Dashboards]
    end

    API --> Bronze
    DB --> Bronze
    FILES --> Bronze
    STREAM --> Bronze

    Bronze --> |ETL<br/>Validation| Silver
    Silver --> |ETL<br/>Aggregation| Gold

    Gold --> ATHENA
    Gold --> SPARK
    Gold --> ML
    Gold --> BI

    style Bronze fill:#cd7f32,stroke:#8b4513,stroke-width:3px,color:#000
    style Silver fill:#c0c0c0,stroke:#808080,stroke-width:3px,color:#000
    style Gold fill:#ffd700,stroke:#daa520,stroke-width:3px,color:#000
```

## File Format Decision Tree

```mermaid
graph TD
    START[Choose File Format]

    START --> Q1{Data Structure?}

    Q1 -->|Structured| Q2{Primary Workload?}
    Q1 -->|Semi-Structured| JSON[JSON/JSONL<br/>✓ Nested data<br/>✓ Flexible schema<br/>⚠️ Large size]
    Q1 -->|Unstructured| BINARY[Binary Formats<br/>Avro/Protobuf]

    Q2 -->|Analytics<br/>Read-Heavy| Q3{Ecosystem?}
    Q2 -->|Streaming<br/>Write-Heavy| AVRO[Apache Avro<br/>✓ Schema evolution<br/>✓ Compact<br/>✓ Fast writes]
    Q2 -->|Exchange<br/>Compatibility| CSV[CSV<br/>✓ Universal<br/>✓ Human-readable<br/>⚠️ No schema]

    Q3 -->|Spark/Athena<br/>AWS| PARQUET[Apache Parquet ⭐<br/>✓ Columnar<br/>✓ Excellent compression<br/>✓ Predicate pushdown<br/>✓ Column pruning]
    Q3 -->|Hive/Hadoop<br/>On-prem| ORC[Apache ORC<br/>✓ ACID support<br/>✓ Better compression<br/>⚠️ Less tooling]

    PARQUET --> USE_PARQUET[RECOMMENDED<br/>for Data Lakes]

    style PARQUET fill:#90ee90,stroke:#006400,stroke-width:4px
    style USE_PARQUET fill:#32cd32,stroke:#006400,stroke-width:3px
    style AVRO fill:#87ceeb,stroke:#00008b,stroke-width:2px
    style JSON fill:#fffacd,stroke:#daa520,stroke-width:2px
    style CSV fill:#ffb6c1,stroke:#c71585,stroke-width:2px
    style ORC fill:#dda0dd,stroke:#8b008b,stroke-width:2px
```

## Partitioning Strategies

### Strategy 1: Time-Based Partitioning

```mermaid
graph LR
    ROOT[s3://bucket/table/]

    ROOT --> Y2023[year=2023/]
    ROOT --> Y2024[year=2024/]

    Y2024 --> M01[month=01/]
    Y2024 --> M02[month=02/]

    M02 --> D01[day=01/<br/>data.parquet<br/>Size: 500MB]
    M02 --> D02[day=02/<br/>data.parquet<br/>Size: 520MB]
    M02 --> D03[day=03/<br/>data.parquet<br/>Size: 480MB]

    style D01 fill:#90ee90
    style D02 fill:#90ee90
    style D03 fill:#90ee90
```

**SQL Query with Partition Pruning:**
```sql
SELECT * FROM transactions
WHERE year = 2024
  AND month = 02
  AND day = 02;

-- Scans only: year=2024/month=02/day=02/
-- Skips: All other partitions (99% of data)
```

### Strategy 2: Multi-Dimensional Partitioning

```mermaid
graph TB
    ROOT[s3://bucket/events/]

    ROOT --> E1[event_type=purchase/]
    ROOT --> E2[event_type=click/]
    ROOT --> E3[event_type=view/]

    E1 --> C1[country=US/]
    E1 --> C2[country=UK/]

    C1 --> Y1[year=2024/]
    C1 --> Y2[year=2023/]

    Y1 --> M1[month=02/]
    M1 --> DATA[data.parquet]

    style DATA fill:#ffd700
```

**Benefits:**
- Query by event type: Skip 66% data
- Query by country: Skip 50% data
- Query by date: Skip 98% data
- Query by all three: Skip 99.9% data ✅

### Strategy 3: Hash Partitioning (Avoid Over-Partitioning)

```mermaid
graph LR
    ROOT[s3://bucket/users/]

    ROOT --> H0[hash_bucket=00/]
    ROOT --> H1[hash_bucket=01/]
    ROOT --> H2[hash_bucket=02/]
    ROOT --> DOTS[...]
    ROOT --> H99[hash_bucket=99/]

    H0 --> D1[data.parquet<br/>Users: 10,000<br/>Size: 50MB]
    H1 --> D2[data.parquet<br/>Users: 10,050<br/>Size: 50MB]

    style D1 fill:#87ceeb
    style D2 fill:#87ceeb
```

**Use Case:** Millions of high-cardinality values (user_id)
```python
# Generate hash bucket
user_hash = hash(user_id) % 100  # 100 buckets
partition_path = f"hash_bucket={user_hash:02d}/"
```

## S3 Storage Classes

```mermaid
graph LR
    subgraph Hot["🔥 HOT DATA (Frequent Access)"]
        S3_STD["S3 Standard<br/>$0.023/GB/month<br/>ms latency<br/>Use: < 30 days"]
    end

    subgraph Warm["🌡️ WARM DATA (Infrequent Access)"]
        S3_IA["S3 Standard-IA<br/>$0.0125/GB/month<br/>ms latency<br/>Use: 30-90 days"]
        S3_ITO["S3 Intelligent-Tiering<br/>$0.0025 monitoring<br/>Auto-optimization"]
    end

    subgraph Cold["❄️ COLD DATA (Archive)"]
        GLACIER["S3 Glacier Instant<br/>$0.004/GB/month<br/>ms latency<br/>Use: 90-365 days"]
        GLACIER_FLEX["Glacier Flexible<br/>$0.0036/GB/month<br/>1-5min retrieval"]
        DEEP["Glacier Deep Archive<br/>$0.00099/GB/month<br/>12hr retrieval<br/>Use: > 1 year"]
    end

    S3_STD -->|30 days| S3_IA
    S3_IA -->|90 days| GLACIER
    GLACIER -->|365 days| DEEP

    style S3_STD fill:#ff6b6b,stroke:#c92a2a
    style S3_IA fill:#ffd93d,stroke:#f08c00
    style GLACIER fill:#6bcfff,stroke:#1c7ed6
    style DEEP fill:#a5d8ff,stroke:#1864ab
```

**Lifecycle Policy:**
```python
lifecycle_rules = [
    {
        'Id': 'Bronze-to-Archive',
        'Filter': {'Prefix': 'bronze/'},
        'Status': 'Enabled',
        'Transitions': [
            {'Days': 30, 'StorageClass': 'STANDARD_IA'},
            {'Days': 90, 'StorageClass': 'GLACIER'}
        ]
    },
    {
        'Id': 'Silver-retain-warm',
        'Filter': {'Prefix': 'silver/'},
        'Status': 'Enabled',
        'Transitions': [
            {'Days': 90, 'StorageClass': 'GLACIER'}
        ]
    }
]
```

## Data Flow Patterns

### Pattern 1: Batch ETL pipeline

```mermaid
sequenceDiagram
    participant Source as Data Source
    participant Bronze as Bronze Layer
    participant Silver as Silver Layer
    participant Gold as Gold Layer
    participant Consumer as Analytics

    Note over Source,Consumer: Daily Batch Process (2 AM)

    Source->>Bronze: 1. Upload raw files<br/>Format: CSV<br/>Size: 10GB
    Note over Bronze: Stored as-is<br/>No transformation

    Bronze->>Silver: 2. ETL Job<br/>- Validate schema<br/>- Deduplicate<br/>- Convert to Parquet
    Note over Silver: Size: 2GB (80% reduction)

    Silver->>Gold: 3. Aggregation<br/>- Daily summaries<br/>- Join dimensions<br/>- Feature engineering
    Note over Gold: Size: 500MB<br/>Pre-aggregated

    Gold->>Consumer: 4. Query<br/>Athena/Presto<br/>< 5 seconds
```

### Pattern 2: Streaming Ingestion

```mermaid
sequenceDiagram
    participant Events as Event Stream<br/>(Kinesis)
    participant Lambda as Lambda<br/>Processor
    participant Firehose as Kinesis Firehose
    participant Bronze as Bronze S3
    participant Silver as Silver S3

    loop Every event
        Events->>Lambda: 1. Event (JSON)
    end

    Lambda->>Firehose: 2. Batch events<br/>(1MB or 60s)

    Firehose->>Bronze: 3. Write to S3<br/>Format: JSONL.gz<br/>Partition: hour

    Note over Bronze,Silver: Hourly ETL Job

    Bronze->>Silver: 4. Convert to Parquet<br/>Partition: day<br/>Deduplicate
```

### Pattern 3: Change Data Capture (CDC)

```mermaid
graph LR
    subgraph Database
        DB[(PostgreSQL)]
        CDC[CDC Tool<br/>Debezium]
        DB --> CDC
    end

    subgraph Streaming
        KAFKA[Kafka Topic<br/>db_changes]
        CDC --> KAFKA
    end

    subgraph Bronze
        B_S3[("Bronze S3<br/>Avro files<br/>All changes")]
        KAFKA --> B_S3
    end

    subgraph Silver
        S_S3[("Silver S3<br/>Parquet<br/>Latest state")]
        B_S3 -->|Merge| S_S3
    end

    style DB fill:#4a90e2
    style KAFKA fill:#ff6b6b
    style B_S3 fill:#cd7f32
    style S_S3 fill:#c0c0c0
```

## Compression pipeline

```mermaid
graph TB
    INPUT[Raw Data<br/>CSV 10GB]

    INPUT --> CONVERT{Convert Format}

    CONVERT -->|Option 1| CSV_GZIP[CSV + Gzip<br/>2.5GB 75%<br/>⏱️ Slow queries]
    CONVERT -->|Option 2| PARQUET_NONE[Parquet Uncompressed<br/>3.5GB 65%<br/>⚡ Fast queries]
    CONVERT -->|Option 3| PARQUET_SNAPPY[Parquet + Snappy<br/>1.4GB 86%<br/>⚡ Fast + Small]
    CONVERT -->|Option 4| PARQUET_GZIP[Parquet + Gzip<br/>900MB 91%<br/>⏱️ Slower queries]
    CONVERT -->|Option 5| PARQUET_ZSTD[Parquet + Zstd<br/>1.0GB 90%<br/>⚡ Balanced]

    PARQUET_SNAPPY --> WINNER[✅ WINNER<br/>Best Balance]

    style INPUT fill:#ffcccc
    style PARQUET_SNAPPY fill:#90ee90,stroke:#006400,stroke-width:4px
    style WINNER fill:#32cd32,stroke:#006400,stroke-width:3px
    style CSV_GZIP fill:#ffb6c1
    style PARQUET_GZIP fill:#fffacd
```

**Benchmark Results:**
| Format | Size | Write Time | Read Time (Scan) | Read Time (Filter) | Cost/Month |
|--------|------|-------------|--------|----------|-----------|
| CSV | 10GB | 2 min | 45 sec | 45 sec | $0.23 |
| CSV + Gzip | 2.5GB | 8 min | 60 sec | 60 sec | $0.06 |
| Parquet | 3.5GB | 5 min | 10 sec | 3 sec | $0.08 |
| **Parquet + Snappy** | **1.4GB** | **6 min** | **8 sec** | **2 sec** | **$0.03** ✅ |
| Parquet + Gzip | 900MB | 15 min | 25 sec | 8 sec | $0.02 |

## Schema Evolution Workflow

```mermaid
stateDiagram-v2
    [*] --> v1: Initial Schema

    state v1 {
        [*] --> Schema_v1
        Schema_v1: id: int
        Schema_v1: name: string
        Schema_v1: amount: float
    }

    v1 --> v2: Add Optional Column<br/>✅ Backward Compatible

    state v2 {
        [*] --> Schema_v2
        Schema_v2: id: int
        Schema_v2: name: string
        Schema_v2: amount: float
        Schema_v2: email: string (optional)
    }

    v2 --> v3: Add with Default<br/>✅ Full Compatible

    state v3 {
        [*] --> Schema_v3
        Schema_v3: id: int
        Schema_v3: name: string
        Schema_v3: amount: float
        Schema_v3: email: string
        Schema_v3: status: string (default="active")
    }

    v3 --> v4_bad: Rename Column<br/>❌ BREAKING CHANGE
    v3 --> v4_good: Add New Column<br/>✅ Safe

    state v4_bad {
        note left of v4_bad
            DON'T DO THIS:
            name → full_name
            Breaks old readers!
        end note
    }

    state v4_good {
        [*] --> Schema_v4
        Schema_v4: id: int
        Schema_v4: name: string
        Schema_v4: full_name: string (computed)
        note right of Schema_v4
            Keep both columns
            during migration
        end note
    }

    v4_good --> [*]
```

### Schema Evolution Rules

```mermaid
graph TD
    START[Schema Change Request]

    START --> CHECK{Change Type?}

    CHECK -->|Add Column| SAFE1[✅ SAFE<br/>Add as optional<br/>with default value]
    CHECK -->|Delete Column| SAFE2[✅ SAFE<br/>Mark deprecated first<br/>Remove after 2 versions]
    CHECK -->|Rename Column| UNSAFE1[❌ UNSAFE<br/>Add new column<br/>Keep old temporarily]
    CHECK -->|Change Type| UNSAFE2[❌ UNSAFE<br/>Add new typed column<br/>Migrate data]

    SAFE1 --> TEST[Test Compatibility]
    SAFE2 --> TEST
    UNSAFE1 --> MIGRATE[Migration Plan]
    UNSAFE2 --> MIGRATE

    TEST --> DEPLOY[✅ Deploy]
    MIGRATE --> TEST

    style SAFE1 fill:#90ee90
    style SAFE2 fill:#90ee90
    style UNSAFE1 fill:#ffb6c1
    style UNSAFE2 fill:#ffb6c1
    style DEPLOY fill:#32cd32
```

## Partitioning Performance Comparison

```mermaid
graph TB
    subgraph Scenario["Query: SELECT * WHERE date = '2024-02-02'"]
        direction TB
    end

    subgraph NoPartition["❌ No Partitioning"]
        NP_SCAN[Scan: 1 TB<br/>Time: 5 minutes<br/>Cost: $5.00]
        NP_FILES[1000 files read]
    end

    subgraph DatePartition["✅ Date Partitioning"]
        DP_SCAN[Scan: 3 GB<br/>Time: 2 seconds<br/>Cost: $0.015]
        DP_FILES[1 file read]
    end

    subgraph HybridPartition["✅✅ Hybrid Partitioning<br/>(date + country)"]
        HP_SCAN[Scan: 500 MB<br/>Time: 0.5 seconds<br/>Cost: $0.0025]
        HP_FILES[1 file read<br/>Perfect pruning]
    end

    Scenario --> NoPartition
    Scenario --> DatePartition
    Scenario --> HybridPartition

    style NoPartition fill:#ffcccc,stroke:#cc0000
    style DatePartition fill:#ffffcc,stroke:#cccc00
    style HybridPartition fill:#ccffcc,stroke:#00cc00,stroke-width:3px
```

## Data Lake Monitoring Dashboard

```mermaid
graph TB
    subgraph Metrics["Key Metrics to Monitor"]
        M1[Storage Size<br/>Bronze: 50 TB<br/>Silver: 12 TB<br/>Gold: 3 TB]
        M2[File Count<br/>Bronze: 500K files<br/>Silver: 50K files<br/>Gold: 5K files]
        M3[Query Performance<br/>Avg: 2.5s<br/>P95: 8s<br/>P99: 15s]
        M4[Costs<br/>Storage: $1,500/mo<br/>Queries: $800/mo<br/>Total: $2,300/mo]
    end

    subgraph Alerts["Automated Alerts"]
        A1[⚠️ Small Files<br/>Trigger: > 100 files < 10MB<br/>Action: Run compaction]
        A2[⚠️ Large Partitions<br/>Trigger: Partition > 5GB<br/>Action: Review strategy]
        A3[⚠️ Slow Queries<br/>Trigger: Query > 30s<br/>Action: Optimize]
        A4[⚠️ Cost Spike<br/>Trigger: Cost +20%<br/>Action: Investigate]
    end

    Metrics --> Alerts

    style M1 fill:#e3f2fd
    style M2 fill:#e8f5e9
    style M3 fill:#fff3e0
    style M4 fill:#fce4ec
    style A1 fill:#fff176
    style A2 fill:#fff176
    style A3 fill:#ff8a65
    style A4 fill:#ff8a65
```

## Architecture Decision Tree

```mermaid
graph TD
    START{New Data Lake?}

    START -->|Yes| Q1{Data Volume?}
    START -->|No| MIGRATE[Migration Strategy]

    Q1 -->|< 1 TB| SIMPLE[Simple Architecture<br/>- Single bucket<br/>- Basic partitioning<br/>- Standard tier]
    Q1 -->|1-100 TB| STANDARD[Standard Architecture<br/>- Medallion layers<br/>- Multi-dimensional partitioning<br/>- Lifecycle policies]
    Q1 -->|> 100 TB| ADVANCED[Advanced Architecture<br/>- Multi-region<br/>- Lake Formation<br/>- Advanced optimization]

    STANDARD --> FORMAT{Choose Format?}

    FORMAT -->|Analytics| PARQUET_STD[Parquet + Snappy<br/>✅ Recommended]
    FORMAT -->|Streaming| AVRO_STD[Avro<br/>✅ For Kafka]
    FORMAT -->|Archive| CSV_GZIP[CSV + Gzip<br/>⚠️ Bronze only]

    PARQUET_STD --> PARTITION{Partition Strategy?}

    PARTITION -->|Time-series| TIME_PART[year/month/day<br/>✅ Most common]
    PARTITION -->|Multi-dimensional| HYBRID_PART[type/country/date<br/>✅ Complex queries]
    PARTITION -->|High cardinality| HASH_PART[hash buckets<br/>⚠️ Advanced]

    TIME_PART --> SUCCESS[✅ Data Lake Ready]

    style PARQUET_STD fill:#90ee90,stroke:#006400,stroke-width:3px
    style TIME_PART fill:#90ee90,stroke:#006400,stroke-width:2px
    style SUCCESS fill:#32cd32,stroke:#006400,stroke-width:4px
```

## Summary

### Key Architecture Decisions

1. **Layers:** Use Medallion (Bronze → Silver → Gold) for progressive refinement
2. **Format:** Parquet + Snappy for analytics (primary choice)
3. **Partitioning:** Date-based for time-series, hybrid for complex queries
4. **Compression:** Snappy (balance), Gzip (archive), Zstd (modern)
5. **Storage Classes:** Lifecycle policies to move cold data to cheaper tiers
6. **Monitoring:** Track size, file count, query performance, costs

### Reference Implementation

See exercises for hands-on implementation of these architectures:
- Exercise 01: Medallion data lake design
- Exercise 02: Format conversion pipeline
- Exercise 03: Partitioning strategies
- Exercise 04: Compression benchmarking
- Exercise 05: Schema evolution
- Exercise 06: Glue Catalog integration

---

*These diagrams represent production-grade architectures used by companies processing petabytes of data daily.*
