# Checkpoint 01: Serverless Data Lake - Starter Template

Welcome to the Serverless Data Lake checkpoint project! This starter template provides scaffolding with TODO sections for you to complete. You'll build a production-grade data lake on AWS using serverless technologies.

## 🎯 Project Overview

Build an end-to-end serverless data lake for **CloudMart**, a fictional e-commerce company, implementing the **Medallion Architecture** (Bronze → Silver → Gold) to process orders, customers, products, and events data.

### Architecture Diagram

```
┌─────────────┐
│ Data Sources│ (CSV, JSON, JSONL files)
└──────┬──────┘
       │
       ↓ Upload to S3
┌──────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (Raw)                     │
│  S3 Bucket: Raw ingested data in original formats        │
│  - orders/                                                │
│  - customers/                                             │
│  - products/                                              │
│  - events/                                                │
└──────┬───────────────────────────────────────────────────┘
       │
       ↓ Lambda Functions (Ingestion & Validation)
┌──────────────────────────────────────────────────────────┐
│                   SILVER LAYER (Processed)                │
│  S3 Bucket: Cleaned, validated Parquet files             │
│  Glue Crawlers: Auto-discover schema                     │
│  - orders/ (partitioned by year/month)                   │
│  - customers/                                             │
│  - products/                                              │
└──────┬───────────────────────────────────────────────────┘
       │
       ↓ Glue ETL Jobs (Transformations & Aggregations)
┌──────────────────────────────────────────────────────────┐
│                    GOLD LAYER (Curated)                   │
│  S3 Bucket: Business-ready analytics tables               │
│  - sales_summary/ (daily/monthly metrics)                │
│  - customer_360/ (RFM, segments, CLV)                    │
└──────┬───────────────────────────────────────────────────┘
       │
       ↓ Amazon Athena (SQL Analytics)
┌──────────────────────────────────────────────────────────┐
│              Analytics & Reporting Layer                  │
│  Query data with SQL, create dashboards                  │
└───────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
starter-template/
├── infrastructure/           # Terraform IaC
│   ├── main.tf              # Main infrastructure (TODO sections)
│   ├── variables.tf         # Configuration variables
│   ├── outputs.tf           # Output values
│   └── README.md            # Deployment guide
│
├── pipelines/
│   ├── lambda/              # Lambda ingestion functions
│   │   ├── common/
│   │   │   └── utils.py     # Complete utility functions
│   │   ├── orders_ingestion/
│   │   │   └── handler.py   # TODO: Orders CSV → Parquet
│   │   ├── customers_ingestion/
│   │   │   └── handler.py   # TODO: Customers JSON → Parquet
│   │   ├── products_ingestion/
│   │   │   └── handler.py   # TODO: Products CSV → Parquet
│   │   └── events_ingestion/
│   │       └── handler.py   # TODO: Events JSONL → Parquet
│   │
│   └── glue/                # Glue ETL jobs (PySpark)
│       ├── bronze_to_silver_orders.py      # TODO: Clean & validate
│       ├── bronze_to_silver_customers.py   # TODO: Standardize
│       ├── bronze_to_silver_products.py    # TODO: Categorize
│       ├── silver_to_gold_sales_summary.py # TODO: Aggregate metrics
│       └── silver_to_gold_customer_360.py  # TODO: RFM & segmentation
│
├── sql/
│   ├── 00_setup_database.sql    # Database setup
│   └── 01_exercises.sql         # 15 SQL exercises with TODOs
│
├── README.md                # This file
└── CHECKLIST.md             # Progress tracker

```

## 🎓 Learning Objectives

By completing this project, you will:

1. **Infrastructure as Code**: Deploy AWS resources with Terraform
2. **Serverless Computing**: Build Lambda functions for data ingestion
3. **Data Engineering**: Implement medallion architecture data lake
4. **ETL Processing**: Create PySpark Glue jobs for transformations
5. **Data Quality**: Implement validation and quality checks
6. **SQL Analytics**: Query data lake with Athena
7. **Monitoring**: Set up CloudWatch alarms and SNS alerts
8. **Cloud Architecture**: Design scalable, cost-effective solutions

## 🚀 Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0 installed
- AWS CLI configured with credentials
- Python 3.11+ (for local Lambda testing)
- Basic knowledge of Python, SQL, and PySpark

### Step-by-Step Implementation

#### Phase 1: Infrastructure Setup (Week 1)

1. **Configure Variables**
   ```bash
   cd infrastructure/
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Complete Infrastructure TODOs**
   - Open `infrastructure/main.tf`
   - Follow TODO comments in order
   - Refer to `infrastructure/README.md` for detailed guidance

3. **Deploy Infrastructure**
   ```bash
   terraform init
   terraform validate
   terraform plan
   terraform apply
   ```

4. **Verify Deployment**
   - Check S3 buckets created
   - Confirm IAM roles exist
   - Verify Glue databases

#### Phase 2: Lambda Ingestion (Week 1-2)

1. **Complete Lambda Handlers**
   - Start with `orders_ingestion/handler.py`
   - Complete all 6 TODO sections
   - Test locally with sample data
   - Deploy and test with S3 trigger

2. **Repeat for Other Functions**
   - customers_ingestion (JSON processing)
   - products_ingestion (CSV with categories)
   - events_ingestion (JSONL streaming data)

3. **Test End-to-End**
   ```bash
   # Upload sample data
   aws s3 cp sample-orders.csv s3://your-bucket-raw/orders/

   # Check Lambda logs
   aws logs tail /aws/lambda/cloudmart-orders-ingestion-dev --follow

   # Verify Parquet files created in processed bucket
   aws s3 ls s3://your-bucket-processed/orders/
   ```

#### Phase 3: Glue ETL Jobs (Week 2-3)

1. **Complete Bronze to Silver Jobs**
   - `bronze_to_silver_orders.py` - Most detailed with examples
   - `bronze_to_silver_customers.py` - Customer data cleansing
   - `bronze_to_silver_products.py` - Product categorization

2. **Run Glue Crawlers**
   ```bash
   aws glue start-crawler --name cloudmart-bronze-orders-dev
   aws glue start-crawler --name cloudmart-silver-orders-dev
   ```

3. **Test Glue Jobs**
   ```bash
   aws glue start-job-run --job-name cloudmart-bronze-to-silver-orders-dev
   ```

4. **Complete Silver to Gold Jobs** (Advanced)
   - `silver_to_gold_sales_summary.py` - Aggregations & rankings
   - `silver_to_gold_customer_360.py` - RFM analysis & segmentation

#### Phase 4: SQL Analytics (Week 3-4)

1. **Setup Databases**
   - Run `sql/00_setup_database.sql` in Athena

2. **Complete SQL Exercises**
   - Open `sql/01_exercises.sql`
   - Complete all 15 exercises
   - Validate results make sense
   - Optimize query performance

3. **Create Analytics Views**
   - Build reusable views for common queries
   - Document insights discovered

## 📋 Completion Checklist

See [CHECKLIST.md](./CHECKLIST.md) for detailed progress tracking.

**Summary:**
- [ ] Phase 1: Infrastructure (40 points)
- [ ] Phase 2: Lambda Functions (20 points)
- [ ] Phase 3: Glue ETL Jobs (25 points)
- [ ] Phase 4: SQL Analytics (15 points)

**Total: 100 points**

## 🧪 Testing Your Implementation

### Unit Tests

```bash
# Test Lambda functions locally
cd pipelines/lambda/orders_ingestion/
python -m pytest test_handler.py

# Test Glue scripts locally with PySpark
cd pipelines/glue/
spark-submit bronze_to_silver_orders.py --local-test
```

### Integration Tests

```bash
# End-to-end pipeline test
./test_pipeline.sh
```

### Data Quality Validation

```sql
-- Run in Athena
-- Check record counts match across layers
SELECT
  (SELECT COUNT(*) FROM bronze.orders) as bronze_count,
  (SELECT COUNT(*) FROM silver.orders) as silver_count,
  (SELECT COUNT(*) FROM gold.sales_summary) as gold_count;
```

## 📊 Success Metrics

Your implementation is successful when:

1. ✅ All Terraform resources deploy without errors
2. ✅ Lambda functions process files and write Parquet
3. ✅ Glue jobs run successfully with bookmarks
4. ✅ Data quality checks pass (no invalid records in Silver)
5. ✅ Athena queries return expected results
6. ✅ CloudWatch alarms properly configured
7. ✅ Cost remains under budget ($50/month for dev)

## 📚 Resources

### AWS Documentation
- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/)
- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)

### Training Materials
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Medallion Architecture Pattern](https://www.databricks.com/glossary/medallion-architecture)

### Reference Solution
- Located in `../reference-solution/` (use only if stuck!)

## 🐛 Troubleshooting

### Common Issues

**Issue**: Lambda function timeout
- **Solution**: Increase timeout in `variables.tf` or optimize code

**Issue**: Glue job fails with "Access Denied"
- **Solution**: Check IAM role permissions for S3 buckets

**Issue**: Athena "Table not found"
- **Solution**: Run Glue crawler to discover schema

**Issue**: Parquet files not created
- **Solution**: Check CloudWatch logs for errors

**Issue**: High AWS costs
- **Solution**: Check for orphaned resources, enable lifecycle policies

### Getting Help

1. Review the reference solution (last resort!)
2. Check CloudWatch logs for detailed errors
3. Consult module instructor or peers
4. Search AWS documentation and forums

## 💰 Cost Management

**Expected monthly costs (dev environment):**
- S3 storage: $1-5
- Lambda executions: $0-2 (within free tier)
- Glue crawlers & jobs: $5-20 (pay per use)
- Athena queries: $1-5 ($5/TB scanned)
- CloudWatch logs: $1-3

**Total: ~$10-35/month**

**Cost optimization tips:**
1. Delete resources after testing
2. Use lifecycle policies for S3
3. Enable Glue job bookmarks (avoid reprocessing)
4. Partition large tables for Athena
5. Set CloudWatch log retention to 7 days

## 🎖️ Going Further (Bonus Challenges)

1. **Advanced Transformations**
   - Implement slowly changing dimensions (SCD Type 2)
   - Add data lineage tracking
   - Implement data versioning

2. **Automation**
   - Create Step Functions workflow
   - Add EventBridge schedules for jobs
   - Implement CI/CD for pipeline code

3. **Monitoring & Alerting**
   - Create CloudWatch dashboard
   - Set up data quality metrics
   - Implement data freshness alerts

4. **Optimization**
   - Tune Glue job DPU allocation
   - Implement Z-ordering for Parquet
   - Add caching layer with ElastiCache

5. **Governance**
   - Implement AWS Lake Formation
   - Add data catalog tags
   - Set up cross-account access

## 📝 Submission Guidelines

When ready to submit:

1. ✅ Complete all TODO sections
2. ✅ Test end-to-end pipeline
3. ✅ Fill out CHECKLIST.md
4. ✅Create a summary document with:
   - Architecture diagram
   - Challenges faced and solutions
   - Optimizations implemented
   - Sample query results
   - Cost breakdown
5. ✅ Clean up resources (or keep for portfolio)

## 🏆 Assessment Rubric

| Category | Points | Criteria |
|----------|--------|----------|
| **Infrastructure** | 40 | Terraform complete, resources deployed correctly |
| **Lambda Functions** | 20 | All handlers complete, proper validation |
| **Glue ETL Jobs** | 25 | Transformations working, bookmarks enabled |
| **SQL Analytics** | 15 | Exercises complete, queries optimized |
| **Bonus** | +10 | Extra features, documentation, optimization |

**Total: 100 points (110 with bonus)**

## 🎉 Congratulations!

By completing this project, you've built a production-grade serverless data lake using AWS best practices. This is a significant achievement and demonstrates your cloud data engineering skills.

**Next Steps:**
- Add this project to your portfolio
- Write a blog post about your learnings
- Explore Checkpoint 02: Real-time Analytics Platform
- Share your implementation with the community

Good luck! 🚀

---

**Questions or Issues?** Create an issue in the repository or consult the module instructor.
