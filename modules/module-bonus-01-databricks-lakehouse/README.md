# Bonus Module 01: Databricks Lakehouse Platform

🎁 **Type:** Optional Bonus Module
☁️ **Platform:** Databricks (Cloud-Managed Service)
⏱️ **Estimated Time:** 12-15 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
💰 **Cost:** Free tier available (Community Edition or 14-day trial)

## Prerequisites

- ✅ **Module 05** (Data Lakehouse Architecture) - Must be completed
- ✅ **Module 07** (Batch Processing with Spark) - Must be completed
- ✅ Basic understanding of Apache Spark and distributed computing
- ✅ SQL knowledge (for Databricks SQL Analytics)

**Note:** This is an optional advanced module that complements the core AWS-based learning path. It provides hands-on experience with Databricks, a leading unified data analytics platform.

## ⚠️ Important Notes

- This module uses **Databricks** - a cloud-managed platform with trial limitations
- **Free Options Available:**
  - Databricks Community Edition (free, limited features)
  - 14-day trial of full platform (AWS/Azure/GCP)
- Review [COST-ALERT.md](COST-ALERT.md) for detailed pricing and free tier information
- **Not required** for core learning path completion
- Complements AWS knowledge with industry-leading alternative platform
- Many enterprises use Databricks alongside AWS services

## Module Overview

Learn to build production-grade data platforms using **Databricks Lakehouse**, the unified analytics platform that combines the best of data warehouses and data lakes. Master Delta Lake for ACID transactions, Unity Catalog for data governance, and MLflow for ML lifecycle management.

**Why Databricks?**
- 🏆 Industry leader in unified data analytics
- 🔥 Built by the creators of Apache Spark, Delta Lake, and MLflow
- 🚀 10-50x faster than traditional Spark deployments
- 🎯 Unified platform: Data Engineering + Analytics + ML + Governance
- 💼 Used by 9,000+ companies including Comcast, Shell, 3M, ABN AMRO

**What You'll Learn:**
- Build Delta Lake tables with ACID guarantees
- Create production ETL pipelines with Databricks Workflows
- Implement data governance with Unity Catalog
- Perform real-time streaming analytics with Structured Streaming
- Build ML models with AutoML and MLflow
- Optimize performance with Delta Lake features (Z-ordering, data skipping, liquid clustering)

**Technologies Covered:**
- 🏗️ Databricks Lakehouse Platform (AWS/Azure)
- 📊 Delta Lake (ACID transactions, time travel, schema evolution)
- 🔐 Unity Catalog (data governance, lineage, access control)
- 🔄 Databricks Workflows (job orchestration, scheduling)
- 📈 Databricks SQL (analytics, dashboards, BI integration)
- 🤖 MLflow (ML tracking, registry, deployment)
- ⚡ Photon Engine (vectorized query execution)
- 🔍 Data Explorer (metadata, lineage, permissions)

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Set up and configure Databricks workspaces and clusters
- ✅ Create and manage Delta Lake tables with ACID transactions
- ✅ Build production ETL pipelines using Databricks notebooks and Workflows
- ✅ Implement data governance with Unity Catalog (catalogs, schemas, permissions)
- ✅ Perform real-time streaming analytics with Structured Streaming
- ✅ Optimize Delta Lake tables with Z-ordering, vacuuming, and compaction
- ✅ Create interactive dashboards with Databricks SQL Analytics
- ✅ Train and deploy ML models using AutoML and MLflow
- ✅ Monitor data quality and lineage with Unity Catalog
- ✅ Compare Databricks vs AWS-native solutions (EMR, Glue, Redshift)

## Structure

- **theory/**: Databricks concepts, architecture patterns, best practices
  - `concepts.md` - Databricks architecture, Delta Lake, Unity Catalog fundamentals
  - `setup-guide.md` - Account setup, workspace configuration, cluster creation
  - `best-practices.md` - Development workflows, optimization, cost management
  - `resources.md` - Official docs, certifications, learning materials

- **notebooks/**: Interactive Databricks notebooks (Python/SQL/Scala)
  - `01-delta-lake-basics.py` - Create tables, ACID transactions, time travel
  - `02-etl-pipeline.py` - Bronze/Silver/Gold medallion architecture
  - `03-unity-catalog.py` - Data governance, lineage, access control
  - `04-streaming-analytics.py` - Structured Streaming with Delta Lake
  - `05-sql-analytics.py` - Databricks SQL, dashboards, BI integration
  - `06-ml-with-mlflow.py` - AutoML, experiment tracking, model registry

- **exercises/**: 6 hands-on labs with validation scripts
  - Exercise 01: Delta Lake Fundamentals
  - Exercise 02: Production ETL Pipelines
  - Exercise 03: Unity Catalog Governance
  - Exercise 04: Real-Time Streaming
  - Exercise 05: SQL Analytics & Dashboards
  - Exercise 06: ML with MLflow

- **scripts/**: Setup and deployment automation
  - `setup_databricks_cli.sh` - Install and configure Databricks CLI
  - `deploy_workspace.py` - Automated workspace setup
  - `create_sample_data.py` - Generate sample datasets

- **data/**: Sample datasets for exercises
  - `sample/` - CSV/JSON/Parquet files for ingestion
  - `schemas/` - Table schemas and data contracts

- **assets/diagrams/**: Architecture diagrams
  - Databricks platform architecture
  - Delta Lake internals
  - Unity Catalog three-level namespace
  - Medallion architecture (Bronze/Silver/Gold)
  - Databricks vs AWS comparison

- **validation/**: Self-assessment and automated tests
  - Validation scripts for each exercise
  - Performance benchmarks

## Getting Started

### Step 1: Review Cost Considerations (5 minutes)
```bash
cat COST-ALERT.md
```

**Free Options:**
- **Databricks Community Edition**: Free, runs on AWS, limited to single-node clusters
- **14-Day Trial**: Full platform access on AWS/Azure/GCP

### Step 2: Create Databricks Account (10 minutes)

**Option A: Community Edition (Recommended for learning)**
1. Visit https://www.databricks.com/try-databricks
2. Select "Community Edition"
3. No credit card required
4. Limitations: Single-node, no Unity Catalog, basic features only

**Option B: Full Trial (Recommended for production-like experience)**
1. Visit https://www.databricks.com/try-databricks
2. Select "14-Day Trial" (AWS/Azure/GCP)
3. Credit card required (won't be charged during trial)
4. Full features: Unity Catalog, Workflows, SQL Analytics, ML

### Step 3: Read Theory Documentation (2-3 hours)
```bash
# Core concepts
cat theory/concepts.md

# Setup guide
cat theory/setup-guide.md

# Best practices
cat theory/best-practices.md
```

### Step 4: Complete Notebooks (6-8 hours)

**Recommended Order:**
1. `01-delta-lake-basics.py` (1.5 hours) - Foundation
2. `02-etl-pipeline.py` (2 hours) - Production patterns
3. `03-unity-catalog.py` (1.5 hours) - Governance (Trial only)
4. `04-streaming-analytics.py` (1.5 hours) - Real-time processing
5. `05-sql-analytics.py` (1 hour) - BI and dashboards
6. `06-ml-with-mlflow.py` (2 hours) - ML lifecycle

**Import notebooks into Databricks:**
```bash
# Option 1: Upload via UI
# Workspace → Import → upload .py files

# Option 2: Use Databricks CLI
databricks workspace import_dir ./notebooks /Users/your.email@example.com/training
```

### Step 5: Complete Exercises (4-6 hours)

Each exercise includes:
- Problem statement and requirements
- Starter code and hints
- Validation script to check your solution
- Reference solution (after attempt)

Run exercises in Databricks notebooks or locally with Databricks Connect.

## Exercises

### Exercise 01: Delta Lake Fundamentals
⏱️ **Duration:** 2 hours | 🎯 **Difficulty:** ⭐⭐⭐

Build your first Delta Lake table with ACID transactions, time travel, and schema evolution.

**Key Skills:**
- Create Delta tables with schema enforcement
- Perform UPSERT operations with MERGE
- Time travel to previous versions
- Schema evolution and ALTER TABLE

### Exercise 02: Production ETL Pipelines
⏱️ **Duration:** 2.5 hours | 🎯 **Difficulty:** ⭐⭐⭐⭐

Implement medallion architecture (Bronze → Silver → Gold) for customer 360 data platform.

**Key Skills:**
- Incremental data ingestion from S3/ADLS
- Data quality checks and Error handling
- Slowly Changing Dimensions (SCD Type 2)
- Databricks Workflows for orchestration

### Exercise 03: Unity Catalog Data Governance
⏱️ **Duration:** 2 hours | 🎯 **Difficulty:** ⭐⭐⭐⭐

Implement fine-grained access control, data lineage, and discovery with Unity Catalog.

**Key Skills:**
- Create catalogs, schemas, tables (three-level namespace)
- Grant/revoke permissions by role
- View data lineage and dependencies
- Implement row-level and column-level security

**Note:** Requires full trial or paid account (not Community Edition)

### Exercise 04: Real-Time Streaming Analytics
⏱️ **Duration:** 2 hours | 🎯 **Difficulty:** ⭐⭐⭐⭐

Build real-time streaming pipeline for IoT sensor data with windowed aggregations.

**Key Skills:**
- Structured Streaming with Delta Lake sources/sinks
- Windowed aggregations (tumbling, sliding)
- Watermarking for late data
- Merge streaming updates into Delta tables

### Exercise 05: SQL Analytics & Dashboards
⏱️ **Duration:** 1.5 hours | 🎯 **Difficulty:** ⭐⭐⭐

Create interactive dashboards and BI reports using Databricks SQL.

**Key Skills:**
- Write optimized SQL queries on Delta tables
- Create parameterized visualizations
- Build executive dashboards
- Schedule SQL queries and alerts

### Exercise 06: ML with MLflow
⏱️ **Duration:** 2.5 hours | 🎯 **Difficulty:** ⭐⭐⭐⭐

Train, track, and deploy ML models for customer churn prediction using AutoML and MLflow.

**Key Skills:**
- Feature engineering with Feature Store
- AutoML for rapid prototyping
- Experiment tracking with MLflow
- Model registry and deployment

## Platform Comparison: Databricks vs AWS

| Feature | Databricks | AWS Native |
|---------|-----------|------------|
| **Compute** | Unified clusters (Spark) | EMR, Glue, Lambda |
| **Storage Format** | Delta Lake (ACID) | Parquet, Iceberg, Hudi |
| **Data Warehouse** | Databricks SQL + Photon | Redshift, Athena |
| **Orchestration** | Databricks Workflows | Step Functions, MWAA |
| **Governance** | Unity Catalog | Lake Formation, Glue Catalog |
| **ML Platform** | Built-in ML, MLflow | SageMaker |
| **Notebooks** | Collaborative, versioned | SageMaker Studio |
| **Streaming** | Structured Streaming | Kinesis, MSK, Flink |
| **Cost Model** | DBU + cloud costs | Pay per service |
| **Setup Complexity** | Low (managed) | Medium-High |
| **Performance** | Highly optimized (Photon) | Variable by service |
| **Vendor Lock-in** | Medium (multi-cloud) | High (AWS only) |

**When to use Databricks:**
- ✅ Need unified platform for DE + DS + ML
- ✅ Heavy Spark workloads (10-50x performance vs self-managed)
- ✅ Multi-cloud or hybrid cloud strategy
- ✅ Collaborative data science teams
- ✅ Budget for managed platform ($0.07-0.75/DBU)

**When to use AWS Native:**
- ✅ Already deep in AWS ecosystem
- ✅ Serverless-first architecture (Lambda, Athena)
- ✅ Light analytics workloads
- ✅ Cost optimization priority (pay-per-query)
- ✅ Need tight AWS service integration

**Hybrid Approach (Common in enterprises):**
- Storage: S3/ADLS (both platforms)
- Processing: Databricks for Spark, AWS for serverless
- Orchestration: Databricks Workflows + AWS Step Functions
- Governance: Unity Catalog + Lake Formation
- Cost: Balance performance vs. spend

## Certification Path

After completing this module, consider:

1. **Databricks Certified Data Engineer Associate**
   - Topics: Delta Lake, ETL, Workflows
   - Duration: 90 minutes
   - Cost: $200
   - Validity: 2 years

2. **Databricks Certified Data Engineer Professional**
   - Topics: Advanced optimization, Unity Catalog, production patterns
   - Duration: 120 minutes
   - Cost: $300
   - Validity: 2 years

3. **Databricks Certified Machine Learning Associate**
   - Topics: Feature engineering, MLflow, AutoML
   - Duration: 90 minutes
   - Cost: $200
   - Validity: 2 years

See `theory/resources.md` for exam prep materials.

## Success Criteria

By completing this module, you should be able to:

- [ ] Create and manage Databricks workspaces
- [ ] Build Delta Lake tables with ACID guarantees
- [ ] Implement medallion architecture (Bronze/Silver/Gold)
- [ ] Use Unity Catalog for data governance
- [ ] Create streaming pipelines with Structured Streaming
- [ ] Build interactive SQL dashboards
- [ ] Train and deploy ML models with MLflow
- [ ] Optimize performance with Delta Lake features
- [ ] Compare and choose between Databricks vs AWS solutions

## Cost Management

See [COST-ALERT.md](COST-ALERT.md) for:
- Community Edition limits (free)
- Trial terms and auto-cancellation
- DBU pricing models
- Cost optimization strategies
- How to avoid unexpected charges

## Support & Resources

- **Official Docs**: https://docs.databricks.com
- **Community Forums**: https://community.databricks.com
- **Academy**: https://academy.databricks.com (free courses)
- **YouTube**: Databricks channel (tutorials, webinars)
- **GitHub**: https://github.com/databricks (examples, connectors)

## Instructor Notes

**Time Budget:**
- Theory: 2-3 hours
- Notebooks: 6-8 hours
- Exercises: 4-6 hours
- Total: 12-17 hours

**Common Issues:**
1. Community Edition limitations → Use trial for full features
2. Cluster startup time → Plan for 5-10 minute waits
3. DBU costs → Monitor spend, use auto-termination
4. Unity Catalog access → Requires trial/paid account

**Tips for Success:**
- Start with Community Edition for basics
- Upgrade to trial for Unity Catalog and Workflows
- Use auto-termination (20 minutes) to avoid costs
- Download notebook exports as backup
- Join Databricks Community for help

---

**Module Maintainer**: Data Engineering Training Team
**Last Updated**: March 2026
**Databricks Version**: Runtime 14.3 LTS (Spark 3.5.x)
**Next Module**: [Bonus 02: Snowflake Data Cloud](../module-bonus-02-snowflake-data-cloud/)
