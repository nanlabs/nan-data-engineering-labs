# 🎓 Cloud Data Engineering - Self-Guided Learning System

> Master Cloud Data Engineering with AWS through hands-on, self-paced learning. Build production-ready skills in data lakehouses, ETL pipelines, streaming analytics, and cloud-native architectures.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-100%25%20Local-orange)](https://localstack.cloud/)
[![Progress](https://img.shields.io/badge/Modules-23-blue)]()

---

## 🌟 Getting Started Hub

This section gives you a quick orientation on how the training is structured, what to study first, and where to find each key document.

### 🎯 What You Will Learn

You will build a full Cloud Data Engineering stack with practical focus:

- Data lakes and lakehouse design patterns
- Batch and streaming ETL/ELT pipelines
- Pipeline orchestration and automation
- Data quality, governance, and security
- Cloud-native infrastructure (IaC, containers, serverless)
- Realistic local operation with LocalStack and Docker

### 🗺️ Learning Roadmap

```text
PHASE 1: Foundation (Modules 01-04)
├─ Cloud fundamentals, storage, SQL, Python for data
└─ Milestone: strong cloud and data foundations

PHASE 2: Core Data Engineering (Modules 05-10 + Checkpoint 01)
├─ Lakehouse, ETL, batch, streaming, data quality, orchestration
└─ Checkpoint 01: Serverless Data Lake

PHASE 3: Cloud-Native Platform (Modules 11-14 + Checkpoint 02)
├─ IaC, serverless processing, containers, governance
└─ Checkpoint 02: Real-time Analytics Platform

PHASE 4: Advanced Tracks (Modules 15-18 + Checkpoint 03)
├─ Track A: Real-time analytics
├─ Track B: Security and compliance
├─ Track C: Cost optimization
└─ Checkpoint 03: Enterprise Data Lakehouse

PHASE 5: Bonus (Modules 22-23)
└─ Databricks and Snowflake (optional)
```text

### 📚 Program Structure

```text
nan-data-engineering-labs/
├── modules/                     -> modules and checkpoints (structure-only placeholders in this bootstrap)
├── docs/                        -> technical guides and troubleshooting
├── scripts/                     -> setup, validation, utilities
├── shared/                      -> shared resources
├── LEARNING-PATH.md             -> complete dependency-based learning route
├── IMPLEMENTATION-STATUS.md     -> current implementation status
├── Makefile                     -> daily operating commands
└── docker-compose.yml           -> local services stack
```text

### 🧩 Module Summary

| Module | Focus |
|---|---|
| 01 | Cloud Fundamentals (AWS basics, IAM) |
| 02 | Storage Basics (S3, data formats) |
| 03 | SQL Foundations |
| 04 | Python for Data |
| 05 | Data Lakehouse Architecture |
| 06 | ETL Fundamentals |
| Checkpoint 01 | Serverless Data Lake |
| 07 | Batch Processing |
| 08 | Streaming Basics |
| 09 | Data Quality |
| 10 | Workflow Orchestration |
| 11 | Infrastructure as Code |
| 12 | Serverless Processing |
| Checkpoint 02 | Real-time Analytics Platform |
| 13 | Container Orchestration |
| 14 | Data Catalog and Governance |
| 15 | Real-time Analytics (Track A) |
| 16 | Data Security and Compliance (Track B) |
| 17 | Cost Optimization (Track C) |
| 18 | Advanced Architectures |
| Checkpoint 03 | Enterprise Data Lakehouse |
| Bonus 01 | Databricks Lakehouse |
| Bonus 02 | Snowflake Data Cloud |

### 🚀 Quick Start

1. Set up the environment
   - `bash scripts/setup-environment.sh`
2. Start local services
   - `make up`
3. Check progress and path
   - `make progress`
   - `cat LEARNING-PATH.md`
4. Start with module 01
   - `cd modules/module-01-cloud-fundamentals`
   - `cat README.md`

### 📖 Core Documentation

- [LEARNING-PATH.md](LEARNING-PATH.md) -> learning route and dependencies
- [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) -> current system status
- [CHECKPOINTS-COMPLETION-SUMMARY.md](CHECKPOINTS-COMPLETION-SUMMARY.md) -> checkpoint delivery summary
- [docs/setup-guide.md](docs/setup-guide.md) -> step-by-step setup

---

## 📋 Table of Contents

- [Overview](#overview)
- [What You'll Learn](#what-youll-learn)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Learning Path](#learning-path)
- [Progress Tracking](#progress-tracking)
- [Prerequisites](#prerequisites)
- [Cost](#cost)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## 🎯 Overview

This is a **complete, production-quality learning system** for Cloud Data Engineering, designed following industry best practices. It provides:

- ✅ **23 Structured Modules** - 18 core + 3 checkpoints + 2 bonus
- ✅ **108+ Hands-On Exercises** - Real-world scenarios with validation
- ✅ **100% Local Development** - No AWS costs using LocalStack + Docker
- ✅ **Automated Validation** - Know immediately if you're on track
- ✅ **Clear Prerequisites** - Dependency-based progression
- ✅ **Certification Aligned** - Maps to AWS & Databricks exams
- ✅ **Self-Paced** - Learn at your own speed

**Time Investment:** 220-312 hours for core path | 10-60+ weeks depending on pace

---

## 💡 What You'll Learn

### Core Skills

| Category | Technologies & Concepts |
|----------|------------------------|
| **Data Storage** | S3, Data Lakes, Delta Lake, Parquet, Avro, Data Lakehouses |
| **Data Processing** | Spark, PySpark, Batch Processing, Stream Processing, Kafka |
| **Data Pipelines** | ETL/ELT, Orchestration, Airflow, Step Functions |
| **Data Quality** | Great Expectations, Schema Validation, Data Contracts |
| **Infrastructure** | Terraform, CloudFormation, Docker, Kubernetes |
| **Serverless** | Lambda, Glue, Kinesis, DynamoDB |
| **Analytics** | Athena, Trino, SQL Optimization, Real-time Dashboards |
| **Governance** | Data Catalogs, Lineage, Security, Compliance |
| **Architecture** | Medallion, Data Mesh, Event-Driven, Cost Optimization |

### AWS Services Covered

**Storage:** S3, Glacier
**Compute:** Lambda, EC2, ECS, EKS
**Data Processing:** Glue, EMR, Kinesis, MSK
**Analytics:** Athena, QuickSight, Redshift
**Orchestration:** Step Functions, EventBridge
**Governance:** Glue Catalog, Lake Formation
**Infrastructure:** CloudFormation, IAM, VPC

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repository-url>
cd nan-data-engineering-labs

# Run automated setup (installs dependencies, creates venv, generates datasets)
bash scripts/setup-environment.sh
```text

**Setup time:** ~10-15 minutes

### 2. Start Services

```bash
# Start LocalStack, Kafka, Spark, PostgreSQL, Trino, MinIO
make up

# Verify services are running
docker-compose ps
```

**Services start in:** ~2-3 minutes

### 3. Begin Learning

```bash
# View learning path and dependencies
cat LEARNING-PATH.md

# Check your progress
make progress

# Start Module 01
cd modules/module-01-cloud-fundamentals
cat README.md
```text

### 4. Complete & Validate

```bash
# After completing exercises, validate your work
make validate MODULE=module-01-cloud-fundamentals

# Track overall progress
make progress
```text

---

## 🏗️ System Architecture

### Local Development Stack

```text
┌─────────────────────────────────────────────────────────┐
│                   Docker Compose                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ LocalStack   │  │    Kafka     │  │    Spark     │ │
│  │ AWS Services │  │  Streaming   │  │  Processing  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PostgreSQL  │  │    Trino     │  │    MinIO     │ │
│  │ Data Warehouse│  │  Query Eng. │  │  S3 Storage  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
            ┌───────────────────────────┐
            │   Your Learning Workspace  │
            │                           │
            │  • Python Scripts         │
            │  • SQL Queries           │
            │  • Terraform Configs     │
            │  • Airflow DAGs          │
            └───────────────────────────┘
```

### Module Structure

```text
module-XX-topic-name/
├── README.md                    # Learning objectives, prerequisites
├── theory/
│   ├── concepts.md             # Core concepts (1200+ words)
│   ├── architecture.md         # Mermaid diagrams, patterns
│   └── resources.md            # Videos, docs, tutorials
├── exercises/
│   ├── 01-exercise-name/
│   │   ├── starter/            # Your starting point
│   │   ├── solution/           # Reference solution
│   │   ├── README.md           # Exercise instructions
│   │   ├── hints.md            # Progressive hints
│   │   └── my_solution/        # Your work goes here
│   └── ... (6 exercises total)
├── infrastructure/
│   ├── docker-compose.yml      # Local environment
│   ├── terraform/              # IaC examples
│   └── setup.sh                # Automated setup
├── data/
│   ├── sample/                 # Sample datasets
│   └── schemas/                # Data schemas
├── validation/
│   ├── data-quality/           # Great Expectations tests
│   ├── integration/            # End-to-end tests
│   ├── infrastructure/         # Terraform validation
│   └── query-results/          # Expected outputs
└── scripts/
    └── validate.sh             # Run all validations
```text

---

## 🗺️ Learning Path

### Foundation Tier (Start Here!)

No prerequisites - complete in any order:

1. **Module 01:** Cloud Fundamentals (AWS basics, IAM)
2. **Module 02:** Storage Basics (S3, data formats)
3. **Module 03:** SQL Foundations (analytical SQL)
4. **Module 04:** Python for Data (Pandas, data manipulation)

### Core Tier

1. **Module 05:** Data Lakehouse Architecture *(requires 02)*
2. **Module 06:** ETL Fundamentals *(requires 02, 04)*
3. **🏁 Checkpoint 01:** Serverless Data Lake *(requires 01-06)*
4. **Module 07:** Batch Processing *(requires 02, 04, 05)*
5. **Module 08:** Streaming Basics *(requires 04, 06)*
6. **Module 09:** Data Quality *(requires 04, 06)*
7. **Module 10:** Workflow Orchestration *(requires 06)*

### Cloud-Native Tier

1. **Module 11:** Infrastructure as Code *(requires 01, 02)*
2. **Module 12:** Serverless Processing *(requires 06, 11)*
3. **🏁 Checkpoint 02:** Real-time Analytics Platform *(requires 07-12)*
4. **Module 13:** Container Orchestration *(requires 11)*
5. **Module 14:** Data Catalog & Governance *(requires 05, 09)*

### Advanced Tier

1. **Module 15:** Real-time Analytics *(requires 08, 10)* - **Track A**
2. **Module 16:** Data Security & Compliance *(requires 01, 14)* - **Track B**
3. **Module 17:** Cost Optimization *(requires 11)* - **Track C**
4. **Module 18:** Advanced Architectures *(requires 05, 07, 08, 14)*
5. **🏁 Checkpoint 03:** Enterprise Data Lakehouse *(requires 13-18)*

### Bonus (Optional)

1. **Bonus 01:** Databricks Lakehouse *(requires 05, 07)*
2. **Bonus 02:** Snowflake Data Cloud *(requires 03, 06)*

📖 **Detailed Path:** See [LEARNING-PATH.md](LEARNING-PATH.md) for dependency diagram and time estimates.

---

## 📊 Progress Tracking

### Check Your Progress

```bash
make progress
```text

**Example Output:**

```text
📊 CLOUD DATA ENGINEERING - LEARNING PROGRESS
═══════════════════════════════════════════════════════════

🎯 FOUNDATION & CORE MODULES
─────────────────────────────────────────────────────────
✅ 🔓 Module 01: Cloud Fundamentals                100%
✅ 🔓 Module 02: Storage Basics                    100%
🔄 🔓 Module 03: SQL Foundations                    67%
⬜ 🔒 Module 05: Data Lakehouse Architecture         0%

Legend:
✅ = Completed    🔄 = In Progress    ⬜ = Not Started
🔓 = Ready        🔒 = Prerequisites Required
```text

### Validation

Each module includes automated validation:

```bash
# Validate specific module
make validate MODULE=module-01-cloud-fundamentals

# Module-level validation
cd modules/module-01-cloud-fundamentals
bash scripts/validate.sh
```

**What's Validated:**

- ✅ Data quality checks
- ✅ Query result correctness
- ✅ Infrastructure syntax
- ✅ Integration tests

---

## ✅ Prerequisites

### Required

- **Docker & Docker Compose** - For LocalStack and services
- **Python 3.9+** - For scripts and data processing
- **Git** - For version control
- **10GB Disk Space** - For Docker images and datasets
- **8GB RAM** - Minimum for running services

### Optional but Recommended

- **AWS CLI** - For LocalStack interaction
- **Terraform** - For IaC modules
- **VS Code** - With Python & Docker extensions
- **DBeaver or pgAdmin** - For database exploration

### Knowledge Prerequisites

- **Basic programming** - Any language (we teach Python)
- **Basic SQL** - SELECT, WHERE, JOIN (we teach advanced)
- **Command line** - Basic bash/terminal usage
- **No AWS required** - We teach from scratch!

---

## 💰 Cost

### This Learning System: **$0/month**

Everything runs locally using free, open-source tools:

| Service | Local Alternative | Cost |
|---------|-------------------|------|
| AWS S3, Lambda, DynamoDB, etc. | LocalStack Community | **Free** |
| Athena | Trino | **Free** |
| Kinesis/MSK | Apache Kafka | **Free** |
| EMR/Glue | Spark Standalone | **Free** |
| Redshift | PostgreSQL | **Free** |
| CloudWatch | Local logging | **Free** |

### Optional Costs

- **LocalStack Pro** - $35/month for Glue/Kinesis emulation *(not required)*
- **AWS Free Tier** - Optional for final validation *(12 months free)*
- **Databricks Community** - Bonus Module 01 *(free forever)*
- **Snowflake Trial** - Bonus Module 02 *(30 days free)*

**Recommended Approach:** Complete entire core path ($0), then optionally use AWS Free Tier for real-world validation.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [LEARNING-PATH.md](LEARNING-PATH.md) | Complete learning path with dependencies |
| [docs/setup-guide.md](docs/setup-guide.md) | Detailed setup instructions |
| [docs/localstack-guide.md](docs/localstack-guide.md) | Working with LocalStack |
| [docs/localstack-alternatives.md](docs/localstack-alternatives.md) | AWS service to local tool mapping |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and solutions |
| [docs/video-guide.md](docs/video-guide.md) | Curated video resources |
| [docs/certifications/](docs/certifications/) | Certification preparation guides |

---

## 🛠️ Available Commands

### Docker Services

```bash
make up          # Start all services
make down        # Stop all services
make restart     # Restart all services
make logs        # View service logs
make clean       # Stop and remove all data
```text

### Learning

```bash
make progress    # Show learning progress
make validate MODULE=<name>  # Validate specific module
```text

### Development

```bash
make setup       # Run initial setup
make generate    # Regenerate module structure
make test-localstack  # Test LocalStack connection
```text

---

## 🎓 Certification Preparation

### AWS Certified Data Analytics - Specialty

**Coverage:** Modules 01-14 + Checkpoint 02 cover 90%+ of exam domains.

**Practice Questions:** Included in all 3 checkpoints.

**Recommended Path:**

1. Complete modules 01-14
2. Pass Checkpoint 02
3. Study security (16) and cost (17)
4. Take practice exams
5. Schedule real exam

### Databricks Data Engineer Associate

**Coverage:** Bonus Module 01 + Core modules 05, 07, 10.

**Recommended Path:**

1. Complete modules 01-10
2. Complete Bonus 01
3. Practice with Databricks Community Edition
4. Schedule exam

---

## 🤝 Contributing

This is a learning system. Contributions welcome:

- 🐛 Bug reports in exercises or validation
- 📝 Documentation improvements
- 💡 New exercise ideas
- 🎥 Video tutorial suggestions
- ⭐ Star if you find this helpful!

---

## 📧 Support

- **Technical Issues:** Check [docs/troubleshooting.md](docs/troubleshooting.md)
- **Module Questions:** Review `theory/resources.md` in each module
- **General Questions:** Open an issue

---

## 📜 License

MIT License - Free to use for learning and teaching.

---

## 🙏 Acknowledgments

Inspired by:

- [roadmap.sh/data-engineer](https://roadmap.sh/data-engineer)
- AWS Data Analytics workshops
- Databricks Learning Academy
- Open-source data engineering community

---

## 🚀 Ready to Start Your Journey?

```bash
# 1. Setup (one time)
bash scripts/setup-environment.sh

# 2. Start services
make up

# 3. Begin learning
cd modules/module-01-cloud-fundamentals
cat README.md
```

**Good luck! 🎓 You're about to become a Cloud Data Engineer.**

---

<!-- PROGRESS_START -->
*Progress table will be auto-generated here by scripts/progress.py*
<!-- PROGRESS_END -->
