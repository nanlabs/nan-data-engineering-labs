# Cloud Data Engineering Labs

> Master Cloud Data Engineering with AWS through hands-on, self-paced learning. Build production-ready skills in data lakehouses, ETL pipelines, streaming analytics, and cloud-native architectures.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI: Validate Modules](https://github.com/nanlabs/nan-data-engineering-labs/actions/workflows/validate-modules.yml/badge.svg)](https://github.com/nanlabs/nan-data-engineering-labs/actions/workflows/validate-modules.yml)
[![Modules: 23](https://img.shields.io/badge/Modules-23-blue)]()

---

## Quick Navigation

This section gives you a quick orientation on how the training is structured, what to study first, and where to find each key document.

### What You Will Learn

You will build a full Cloud Data Engineering stack with practical focus:

- Data lakes and lakehouse design patterns
- Batch and streaming ETL/ELT pipelines
- Pipeline orchestration and automation
- Data quality, governance, and security
- Cloud-native infrastructure (IaC, containers, serverless)
- Realistic local operation with LocalStack and Docker

### Learning Roadmap

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
```

### Program Structure

```text
nan-data-engineering-labs/
├── modules/                     -> modules and checkpoints
├── docs/                        -> technical guides and troubleshooting
├── scripts/                     -> setup, validation, utilities
├── shared/                      -> shared resources
├── LEARNING-PATH.md             -> complete dependency-based learning route
├── GETTING_STARTED.md           -> onboarding guide
├── STATUS.md                    -> project progress
├── Makefile                     -> daily operating commands
└── docker-compose.yml           -> local services stack
```

### Module Summary

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

### Quick Start

**Option A -- DevContainer (recommended)**

```bash
git clone git@github.com:nanlabs/nan-data-engineering-labs.git
cd nan-data-engineering-labs
code .
# Command Palette -> "Dev Containers: Reopen in Container"
```

**Option B -- Local**

```bash
git clone git@github.com:nanlabs/nan-data-engineering-labs.git
cd nan-data-engineering-labs

bash scripts/setup-environment.sh

# Start local services (LocalStack, Kafka, Spark, PostgreSQL, Trino, MinIO)
make up

# Check progress
make progress

# Start Module 01
cd modules/module-01-cloud-fundamentals
cat README.md
```

---

## Full Documentation

| Document | Description |
|----------|-------------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Onboarding and setup |
| [LEARNING-PATH.md](LEARNING-PATH.md) | Complete learning path with dependencies |
| [STATUS.md](STATUS.md) | Project progress |
| [docs/CHARTER.md](docs/CHARTER.md) | NaNLABS Lab Charter v1 |
| [docs/setup-guide.md](docs/setup-guide.md) | Detailed setup instructions |
| [docs/localstack-guide.md](docs/localstack-guide.md) | Working with LocalStack |
| [docs/localstack-alternatives.md](docs/localstack-alternatives.md) | AWS service to local tool mapping |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and solutions |

---

## What You Will Learn

### Core Skills

| Category | Technologies and Concepts |
|----------|--------------------------|
| **Data Storage** | S3, Data Lakes, Delta Lake, Parquet, Avro, Data Lakehouses |
| **Data Processing** | Spark, PySpark, Batch Processing, Stream Processing, Kafka |
| **Data Pipelines** | ETL/ELT, Orchestration, Airflow, Step Functions |
| **Data Quality** | Great Expectations, Schema Validation, Data Contracts |
| **Infrastructure** | Terraform, CloudFormation, Docker, Kubernetes |
| **Serverless** | Lambda, Glue, Kinesis, DynamoDB |
| **Analytics** | Athena, Trino, SQL Optimization, Real-time Dashboards |
| **Governance** | Data Catalogs, Lineage, Security, Compliance |
| **Architecture** | Medallion, Data Mesh, Event-Driven, Cost Optimization |

### System Architecture

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
```

---

## Learning Path

### Foundation Tier (Start Here)

No prerequisites -- complete in any order:

1. **Module 01:** Cloud Fundamentals (AWS basics, IAM)
2. **Module 02:** Storage Basics (S3, data formats)
3. **Module 03:** SQL Foundations (analytical SQL)
4. **Module 04:** Python for Data (Pandas, data manipulation)

### Core Tier

1. **Module 05:** Data Lakehouse Architecture *(requires 02)*
2. **Module 06:** ETL Fundamentals *(requires 02, 04)*
3. **Checkpoint 01:** Serverless Data Lake *(requires 01-06)*
4. **Module 07:** Batch Processing *(requires 02, 04, 05)*
5. **Module 08:** Streaming Basics *(requires 04, 06)*
6. **Module 09:** Data Quality *(requires 04, 06)*
7. **Module 10:** Workflow Orchestration *(requires 06)*

### Cloud-Native Tier

1. **Module 11:** Infrastructure as Code *(requires 01, 02)*
2. **Module 12:** Serverless Processing *(requires 06, 11)*
3. **Checkpoint 02:** Real-time Analytics Platform *(requires 07-12)*
4. **Module 13:** Container Orchestration *(requires 11)*
5. **Module 14:** Data Catalog and Governance *(requires 05, 09)*

### Advanced Tier

1. **Module 15:** Real-time Analytics *(requires 08, 10)* -- Track A
2. **Module 16:** Data Security and Compliance *(requires 01, 14)* -- Track B
3. **Module 17:** Cost Optimization *(requires 11)* -- Track C
4. **Module 18:** Advanced Architectures *(requires 05, 07, 08, 14)*
5. **Checkpoint 03:** Enterprise Data Lakehouse *(requires 13-18)*

### Bonus (Optional)

1. **Bonus 01:** Databricks Lakehouse *(requires 05, 07)*
2. **Bonus 02:** Snowflake Data Cloud *(requires 03, 06)*

See [LEARNING-PATH.md](LEARNING-PATH.md) for dependency diagram.

---

## Progress Tracking

```bash
make progress
```

---

## Available Commands

### Docker Services

```bash
make up          # Start all services
make down        # Stop all services
make restart     # Restart all services
make logs        # View service logs
make clean       # Stop and remove all data
```

### Learning

```bash
make progress                        # Show learning progress
make validate MODULE=<name>          # Validate specific module
```

### Development

```bash
make setup                           # Run initial setup
python scripts/validate_learning_labs.py --strict-core --strict-headings
```

---

## Prerequisites

### Required

- **Docker and Docker Compose** -- For LocalStack and services
- **Python 3.9+** -- For scripts and data processing
- **Git** -- For version control
- **10 GB Disk Space** -- For Docker images and datasets
- **8 GB RAM** -- Minimum for running services

### Optional but Recommended

- **AWS CLI** -- For LocalStack interaction
- **Terraform** -- For IaC modules
- **VS Code** -- With Python and Docker extensions

### Knowledge Prerequisites

- Basic programming (any language -- we teach Python)
- Basic SQL (SELECT, WHERE, JOIN -- we teach advanced)
- Command line usage (bash/terminal)
- No AWS account required -- everything runs locally

---

## Cost

Everything runs locally using free, open-source tools:

| Service | Local Alternative | Cost |
|---------|-------------------|------|
| AWS S3, Lambda, DynamoDB, etc. | LocalStack Community | Free |
| Athena | Trino | Free |
| Kinesis/MSK | Apache Kafka | Free |
| EMR/Glue | Spark Standalone | Free |
| Redshift | PostgreSQL | Free |

---

## Contributing

Contributions welcome:

- Bug reports in exercises or validation
- Documentation improvements
- New exercise ideas

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Sibling Labs

| Lab | Focus |
|-----|-------|
| [nan-python-engineering-labs](https://github.com/nanlabs/nan-python-engineering-labs) | Python engineering fundamentals |
| [nan-ai-engineering-labs](https://github.com/nanlabs/nan-ai-engineering-labs) | AI/ML engineering |
| [nan-ai-native-engineering-labs](https://github.com/nanlabs/nan-ai-native-engineering-labs) | AI-native workflows and tooling |

---

## License

MIT License -- Free to use for learning and teaching. See [LICENSE](LICENSE).

---

<!-- PROGRESS_START -->
*Progress table will be auto-generated here by scripts/progress.py*
<!-- PROGRESS_END -->

## 👥 Contributors

<a href="https://github.com/nanlabs/nan-data-engineering-labs/contributors">
  <img src="https://contrib.rocks/image?repo=nanlabs/nan-data-engineering-labs"/>
</a>

Made with [contributors-img](https://contrib.rocks).