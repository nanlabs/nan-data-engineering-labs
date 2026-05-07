# Module Bonus 02: Snowflake Data Cloud ❄️

## 📚 Overview

Welcome to the **Snowflake Data Cloud** training module! Learn to build modern data platforms using Snowflake's cloud-native data warehouse architecture.

Snowflake is a fully-managed platform built for the cloud with three-layer architecture separating storage, compute, and services. This enables elastic scaling, zero-copy cloning, Time Travel up to 90 days, and secure data sharing without moving data.

🎁 **Type:** Optional Bonus Module
☁️ **Platform:** Cloud-Managed (AWS/Azure/GCP)
⏱️ **Estimated Time:** 12-15 hours
⭐ **Difficulty:** Advanced

---

## 🎯 Learning Objectives

By completing this module, you will:

1. ✅ Understand Snowflake's three-layer architecture (Storage/Compute/Services)
2. ✅ Manage Virtual Warehouses with auto-suspend/resume and multi-cluster scaling
3. ✅ Implement Zero-Copy Cloning for instant dev/test environments
4. ✅ Configure Time Travel for historical queries and data recovery (1-90 days)
5. ✅ Share data securely with partners using Secure Data Sharing
6. ✅ Build CDC pipelines with Streams and orchestrate with Tasks
7. ✅ Automate data ingestion with Snowpipe (event-driven loading)
8. ✅ Optimize costs with Resource Monitors and best practices

---

## 📋 Prerequisites

### Required Modules

- ✅ **Module 03**: SQL Foundations
- ✅ **Module 05**: Data Lakehouse Architecture
- ✅ **Module 06**: ETL Fundamentals (recommended)

### Technical Requirements

- 💳 Snowflake Trial Account (30 days FREE, $400 credits)
- 🌐 Modern web browser (Chrome/Firefox/Safari)
- 🖥️ SnowSQL CLI (optional)
- 🐍 Python 3.8+ with snowflake-connector-python (optional)

**💰 Cost**: $0-25 (see [COST-ALERT.md](COST-ALERT.md))

---

## 🏗️ Snowflake Architecture

### Three-Layer Design

```text
┌──────────────────────────────────────────┐
│       Cloud Services Layer               │
│  Query Optimization │ Metadata │ Security│
└──────────────────────────────────────────┘
                   ↕
┌──────────────────────────────────────────┐
│       Compute Layer                      │
│  Virtual Warehouses (Elastic Scaling)    │
│  [ETL-WH] [BI-WH] [DS-WH] ... [n-WH]    │
└──────────────────────────────────────────┘
                   ↕
┌──────────────────────────────────────────┐
│       Storage Layer                      │
│  Micro-partitions │ Columnar │ Compressed│
└──────────────────────────────────────────┘
```text

### Key Benefits

- **Elastic Scaling**: Spin up/down warehouses in seconds
- **Zero Administration**: Fully managed, no infrastructure
- **Separation of Concerns**: Independent scaling of storage/compute
- **Pay-per-Second Billing**: Cost-efficient for variable workloads
- **Multi-Cloud**: AWS, Azure, GCP (consistent experience)

---

## 🚀 Key Features

### 1. Virtual Warehouses

- **Independent compute clusters** (X-Small to 6X-Large)
- **Auto-suspend**: Idle timeout (60s-60min)
- **Auto-resume**: Automatic on query
- **Multi-cluster**: Handle high concurrency
- **Cost**: 1-512 credits/hour ($2-4 per credit)

### 2. Zero-Copy Cloning

- **Instant clones**: No data duplication
- **FREE**: Until clone diverges
- **Use cases**: Dev/test, backups, experimentation

```sql
CREATE DATABASE dev_db CLONE prod_db;  -- Instant!
```text

### 3. Time Travel

- **Query historical data**: 1-90 days
- **Restore dropped objects**: UNDROP TABLE
- **Point-in-time recovery**: Clone from timestamp

```sql
SELECT * FROM orders AT(OFFSET => -3600);  -- 1 hour ago
UNDROP TABLE customers;
```

### 4. Secure Data Sharing

- **No data movement**: Live access
- **Provider/Consumer model**: Granular control
- **Data Marketplace**: Public datasets

### 5. Streams & Tasks (CDC)

- **Streams**: Track INSERT/UPDATE/DELETE
- **Tasks**: Scheduled SQL (cron or triggered)
- **Serverless**: No dedicated warehouse

### 6. Snowpipe

- **Event-driven**: Auto-load from S3/Azure/GCS
- **Near real-time**: <1 minute latency
- **Cost-efficient**: 0.06 credits per 1,000 files

---

## 📁 Module Structure

```text
module-bonus-02-snowflake-data-cloud/
├── README.md                    # This file
├── COST-ALERT.md                # Cost management
│
├── theory/
│   ├── concepts.md              # Architecture deep-dive
│   ├── setup-guide.md           # Trial setup
│   ├── best-practices.md        # Performance & cost
│   └── resources.md             # Certifications & links
│
├── notebooks/                   # 6 SQL notebooks
│   ├── 01-virtual-warehouses.sql
│   ├── 02-zero-copy-cloning.sql
│   ├── 03-time-travel.sql
│   ├── 04-streams-tasks.sql
│   ├── 05-snowpipe.sql
│   └── 06-data-sharing.sql
│
├── assets/diagrams/             # 6 Mermaid diagrams
│   ├── snowflake-architecture.mmd
│   ├── virtual-warehouse-scaling.mmd
│   ├── zero-copy-cloning.mmd
│   ├── time-travel-failsafe.mmd
│   ├── streams-tasks-pipeline.mmd
│   └── data-sharing-model.mmd
│
├── exercises/                   # 6 hands-on labs
│   ├── exercise-01-warehouse-optimization/
│   ├── exercise-02-zero-copy-dev/
│   ├── exercise-03-time-travel-recovery/
│   ├── exercise-04-cdc-streams-tasks/
│   ├── exercise-05-snowpipe-ingestion/
│   └── exercise-06-data-sharing/
│
├── scripts/
│   ├── create_sample_data.py
│   ├── setup_snowflake.sh
│   └── monitor_costs.py
│
└── data/sample/
    ├── customers.csv
    ├── orders.csv
    └── events.json
```text

---

## 💰 Cost Overview

| Component | Cost | Module Usage |
|-----------|------|--------------|
| **Trial** | FREE 30 days ($400 credits) | Covers all exercises |
| **X-Small Warehouse** | 1 credit/hour ($2-4) | Development |
| **Storage** | $23-40/TB/month | <1GB for exercises |
| **Module Total** | **$0-25** | **$0 with trial** |

See [COST-ALERT.md](COST-ALERT.md) for:

- Trial signup steps
- Resource Monitor setup
- Credit usage tracking
- Optimization strategies

---

## 🎓 Certifications

### SnowPro Core ($175)

- **Topics**: Architecture, Warehouses, Loading, Security
- **Duration**: 2 hours, 100 questions
- **This module prepares you** ✅

### SnowPro Advanced: Data Engineer ($375)

- **Prerequisites**: SnowPro Core
- **Topics**: Streams/Tasks, Snowpipe, Performance tuning

---

## 📖 Getting Started

### Step 1: Setup (30 min)

1. Sign up for trial: <https://signup.snowflake.com/>
2. Follow [theory/setup-guide.md](theory/setup-guide.md)
3. Create training database & warehouse
4. Set Resource Monitor (optional)

### Step 2: Notebooks (6-8 hours)

Complete 6 SQL notebooks in order:

1. Virtual Warehouses (sizing, auto-suspend)
2. Zero-Copy Cloning (dev environments)
3. Time Travel (historical queries)
4. Streams & Tasks (CDC pipelines)
5. Snowpipe (auto-ingestion)
6. Data Sharing (provider/consumer)

### Step 3: Exercises (12-15 hours)

Practice with 6 hands-on labs:

1. **Warehouse Optimization** (⭐⭐⭐, 2h)
2. **Zero-Copy Dev Environments** (⭐⭐⭐, 2h)
3. **Time Travel Recovery** (⭐⭐⭐⭐, 2.5h)
4. **CDC with Streams/Tasks** (⭐⭐⭐⭐, 2.5h)
5. **Snowpipe Ingestion** (⭐⭐⭐⭐, 2h)
6. **Secure Data Sharing** (⭐⭐⭐, 2h)

---

## 🆚 Snowflake vs Competitors

| Feature | Snowflake | Databricks | Redshift |
|---------|-----------|------------|----------|
| Architecture | 3-layer separated | Lakehouse (Spark) | Coupled |
| Zero-Copy Clone | ✅ Yes | ❌ No | ❌ No |
| Time Travel | 1-90 days | 30 days | ❌ No |
| Data Sharing | Native | Delta Sharing | Complex |
| Scaling | Elastic (seconds) | Manual | Resize (hours) |
| Cost (small) | $2-4/hour | $5-8/hour | $0.25/hour |

**Choose Snowflake for**:

- SQL-heavy analytics
- Instant dev/test clones
- Secure data sharing
- Multi-cloud strategy

---

## 📚 Resources

### Official Docs

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Virtual Warehouses](https://docs.snowflake.com/en/user-guide/warehouses.html)
- [Zero-Copy Cloning](https://docs.snowflake.com/en/user-guide/tables-cloning.html)
- [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel.html)

### Community

- [Snowflake Community](https://community.snowflake.com/)

---

## Validation

Use this section as module success criteria:

1. Complete all six notebooks in `notebooks/`.
2. Complete all six exercise folders in `exercises/`.
3. Document cost controls and results in your notes.
4. Verify output artifacts and expected query behavior.

For repository contract checks, run from project root:

```bash
PYTHON=python
$PYTHON scripts/validate_learning_labs.py --module module-bonus-02-snowflake-data-cloud
```text

- [Snowflake University](https://learn.snowflake.com/) (free courses)
- [Quick Starts](https://quickstarts.snowflake.com/)

---

## 🎯 Next Steps

After completing this module:

1. ✅ Build a real-world Snowflake project
2. ✅ Explore Snowflake Marketplace datasets
3. ✅ Study for SnowPro Core certification
4. ✅ Continue to **Module Checkpoint 02**: Real-Time Analytics

---

**Happy Learning!** ❄️ 🚀
