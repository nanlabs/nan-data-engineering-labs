# Checkpoint 01: Serverless Data Lake - Completion Checklist

Track your progress through the project with this checklist. Check off items as you complete them.

## 📊 Overall Progress

- [ ] Phase 1: Infrastructure Setup (40 points)
- [ ] Phase 2: Lambda Ingestion (20 points)
- [ ] Phase 3: Glue ETL Jobs (25 points)
- [ ] Phase 4: SQL Analytics (15 points)
- [ ] Bonus: Advanced Features (+10 points)

**Target Score: 100 points** (110 with bonus)

---

## Phase 1: Infrastructure Setup (40 points)

### Terraform Configuration (10 points)

- [ ] Cloned starter template
- [ ] Created `terraform.tfvars` with custom values
- [ ] Updated `s3_bucket_prefix` to be globally unique
- [ ] Set `alert_email` for SNS notifications
- [ ] Reviewed all variables in `variables.tf`

### S3 Buckets & Lifecycle (5 points)

- [ ] Completed S3 lifecycle configuration TODO in `main.tf`
  - [ ] Added transition to STANDARD_IA (90 days)
  - [ ] Added transition to GLACIER (180 days)
  - [ ] Added expiration rule (365 days)
  - [ ] Added multipart upload cleanup rule

### IAM Roles & Policies (10 points)

- [ ] Completed Lambda IAM role trust policy
- [ ] Completed Lambda S3 access policy
  - [ ] GetObject on raw bucket
  - [ ] PutObject on processed bucket
  - [ ] ListBucket permissions
  - [ ] SNS publish permissions
- [ ] Attached Lambda basic execution policy
- [ ] Completed Glue IAM role trust policy
- [ ] Completed Glue S3 access policy (all three layers)
- [ ] Attached Glue service role policy

### Lambda Functions (7 points)

- [ ] Created deployment package data sources
- [ ] Defined orders_ingestion Lambda function
- [ ] Defined customers_ingestion Lambda function
- [ ] Defined products_ingestion Lambda function
- [ ] Defined events_ingestion Lambda function
- [ ] Configured environment variables for all functions
- [ ] Created S3 bucket notifications (triggers)
- [ ] Created Lambda permissions for S3

### Glue Resources (5 points)

- [ ] Created Glue crawlers for Bronze layer
  - [ ] bronze_orders
  - [ ] bronze_customers
  - [ ] bronze_products
  - [ ] bronze_events
- [ ] Created Glue crawlers for Silver layer
  - [ ] silver_orders
  - [ ] silver_customers
  - [ ] silver_products
- [ ] Created Glue crawlers for Gold layer
  - [ ] gold_sales_summary
  - [ ] gold_customer_360
- [ ] Uploaded Glue ETL scripts to S3
- [ ] Created Glue job: bronze_to_silver_orders
- [ ] Created Glue job: bronze_to_silver_customers
- [ ] Created Glue job: bronze_to_silver_products
- [ ] Created Glue job: silver_to_gold_sales_summary
- [ ] Created Glue job: silver_to_gold_customer_360

### CloudWatch & Monitoring (3 points)

- [ ] Configured SNS email subscription
- [ ] Confirmed SNS subscription email
- [ ] Created CloudWatch alarm for Lambda errors
- [ ] Created CloudWatch alarm for Glue job failures
- [ ] Set appropriate log retention periods

### Deployment (0 points - required)

- [ ] Ran `terraform init` successfully
- [ ] Ran `terraform validate` with no errors
- [ ] Ran `terraform plan` and reviewed changes
- [ ] Ran `terraform apply` successfully
- [ ] Verified all resources created in AWS Console
- [ ] Saved Terraform outputs

---

## Phase 2: Lambda Ingestion Functions (20 points)

### orders_ingestion/handler.py (6 points)

- [ ] TODO 1: Parse S3 event - extract bucket and key
- [ ] TODO 2: Download file from S3 using boto3
- [ ] TODO 3: Parse CSV and validate schema
- [ ] TODO 4: Transform orders data with pandas
- [ ] TODO 5: Write Parquet file to processed bucket
- [ ] TODO 6: Send SNS alert on errors
- [ ] Tested with sample orders.csv file
- [ ] Verified Parquet file created in S3

### customers_ingestion/handler.py (5 points)

- [ ] TODO 1: Parse S3 event
- [ ] TODO 2: Download and parse JSON file
- [ ] TODO 3: Validate customer schema (email format, required fields)
- [ ] TODO 4: Transform data (flatten nested JSON, standardize)
- [ ] TODO 5: Write Parquet to processed bucket
- [ ] Tested with sample customers.json file

### products_ingestion/handler.py (5 points)

- [ ] TODO 1: Parse S3 event
- [ ] TODO 2: Download CSV file
- [ ] TODO 3: Validate product schema (price > 0, valid category)
- [ ] TODO 4: Transform data (categorize, add price tiers)
- [ ] TODO 5: Write Parquet to processed bucket
- [ ] Tested with sample products.csv file

### events_ingestion/handler.py (4 points)

- [ ] TODO 1: Parse S3 event
- [ ] TODO 2: Download and parse JSONL file (newline-delimited JSON)
- [ ] TODO 3: Validate event schema (timestamp, event_type)
- [ ] TODO 4: Transform events data
- [ ] TODO 5: Write Parquet to processed bucket
- [ ] Tested with sample events.jsonl file

### Integration Testing (0 points - required)

- [ ] Uploaded sample data to raw bucket
- [ ] Verified Lambda functions triggered automatically
- [ ] Checked CloudWatch logs for successful execution
- [ ] Verified Parquet files in processed bucket
- [ ] Validated Parquet file schema matches expectations
- [ ] Tested error scenarios (invalid data, missing columns)

---

## Phase 3: Glue ETL Jobs (25 points)

### bronze_to_silver_orders.py (8 points)

- [ ] TODO 1: Read from Bronze catalog table
- [ ] TODO 2: Apply schema mapping and type conversions
- [ ] TODO 3: Implement data quality checks
  - [ ] Filter null order_ids
  - [ ] Filter negative amounts
  - [ ] Filter future dates
  - [ ] Filter invalid statuses
- [ ] TODO 4: Enrich data with calculated fields
  - [ ] Add processing timestamp
  - [ ] Extract year/month/day
  - [ ] Add business logic columns
- [ ] TODO 5: Write to Silver with partitioning
- [ ] Initialized Glue context and job
- [ ] Enabled job bookmarks
- [ ] Tested with sample data
- [ ] Verified output in Silver bucket

### bronze_to_silver_customers.py (5 points)

- [ ] Read customers from Bronze catalog
- [ ] Flatten nested JSON structures (address fields)
- [ ] Apply customer quality checks (email validation, dedup)
- [ ] Standardize names and contact info
- [ ] Write to Silver without time partitions
- [ ] Tested and verified output

### bronze_to_silver_products.py (4 points)

- [ ] Read products from Bronze catalog
- [ ] Standardize product categories
- [ ] Calculate price tiers (budget, mid, premium, luxury)
- [ ] Apply product quality checks
- [ ] Write to Silver (partition by category recommended)
- [ ] Tested and verified output

### silver_to_gold_sales_summary.py (5 points)

- [ ] Read from multiple Silver tables (orders, customers, products)
- [ ] Join tables on appropriate keys
- [ ] Calculate daily sales aggregations
  - [ ] Total revenue
  - [ ] Total orders
  - [ ] Avg order value
  - [ ] Unique customers
- [ ] Calculate product rankings (by revenue, quantity)
- [ ] Calculate customer metrics (spend, frequency)
- [ ] Calculate trends (MoM, YoY growth with LAG)
- [ ] Write aggregated Gold table
- [ ] Tested and verified output

### silver_to_gold_customer_360.py (3 points)

- [ ] Calculate RFM metrics (Recency, Frequency, Monetary)
- [ ] Create customer segments using RFM scores
  - [ ] Champions
  - [ ] Loyal
  - [ ] At Risk
  - [ ] Lost
- [ ] Calculate customer lifetime value
- [ ] Calculate product affinity
- [ ] Join all metrics with customer master data
- [ ] Write Customer 360 to Gold
- [ ] Tested and verified output

### Glue Job Execution (0 points - required)

- [ ] Ran all Glue crawlers to discover schemas
- [ ] Started bronze_to_silver_orders job successfully
- [ ] Started bronze_to_silver_customers job successfully
- [ ] Started bronze_to_silver_products job successfully
- [ ] Started silver_to_gold_sales_summary job successfully
- [ ] Started silver_to_gold_customer_360 job successfully
- [ ] Verified job bookmarks working (no reprocessing)
- [ ] Checked job metrics in Glue console

---

## Phase 4: SQL Analytics (15 points)

### Database Setup (2 points)

- [ ] Ran `00_setup_database.sql` in Athena
- [ ] Created Bronze, Silver, Gold databases
- [ ] Defined table schemas (or let crawlers do it)
- [ ] Ran MSCK REPAIR TABLE for partitioned tables
- [ ] Verified tables accessible in Athena

### SQL Exercises (13 points)

- [ ] Exercise 1: Count orders by date (1 point)
- [ ] Exercise 2: Total revenue by country (1 point)
- [ ] Exercise 3: Top 10 customers by spend (1 point)
- [ ] Exercise 4: Average order value by month (1 point)
- [ ] Exercise 5: Orders above average (1 point)
- [ ] Exercise 6: Month-over-month growth (LAG function) (2 points)
- [ ] Exercise 7: Customer retention analysis (1 point)
- [ ] Exercise 8: Product category performance (1 point)
- [ ] Exercise 9: Identify dormant customers (1 point)
- [ ] Exercise 10: Customer LTV percentiles (1 point)
- [ ] Exercise 11: Weekly sales trend with moving average (1 point)
- [ ] Exercise 12: RFM segmentation (1 point)
- [ ] Exercise 13: Year-over-year comparison (2 points)
- [ ] Exercise 14: Cohort analysis (2 points)
- [ ] Exercise 15: Product recommendation pairs (2 points)

### Query Optimization (0 points - required)

- [ ] Used partition filters in queries
- [ ] Selected only needed columns (avoided SELECT *)
- [ ] Used LIMIT for large result sets
- [ ] Validated query results make sense
- [ ] Documented query performance (time, data scanned)

---

## Bonus: Advanced Features (+10 points)

- [ ] Implemented SCD Type 2 for customers (+2 points)
- [ ] Added Step Functions workflow orchestration (+2 points)
- [ ] Created CloudWatch dashboard (+1 point)
- [ ] Implemented data quality framework (+2 points)
- [ ] Added CI/CD pipeline for code deployment (+2 points)
- [ ] Optimized Parquet with Z-ordering (+1 point)
- [ ] Documented architecture and learnings (+1 point)
- [ ] Created portfolio blog post (+1 point)

---

## Final Validation & Submission

### Pre-Submission Checklist

- [ ] All TODO sections completed
- [ ] Code follows Python/SQL best practices
- [ ] No hardcoded values (use variables/parameters)
- [ ] Error handling implemented
- [ ] Logging configured appropriately
- [ ] Documentation complete and accurate
- [ ] Tests passing (if written)
- [ ] Resources tagged appropriately

### Testing Validation

- [ ] End-to-end pipeline tested successfully
- [ ] Data quality checks passing
- [ ] No data loss between layers
- [ ] Performance acceptable (jobs complete in reasonable time)
- [ ] Costs within budget ($50/month)

### Documentation

- [ ] Created architecture diagram
- [ ] Documented challenges and solutions
- [ ] Included sample query results
- [ ] Documented cost breakdown
- [ ] Completed summary document

### Resource Cleanup (if not keeping for portfolio)

- [ ] Ran `terraform destroy` to remove all resources
- [ ] Verified S3 buckets deleted (or kept intentionally)
- [ ] Checked no orphaned resources in AWS Console
- [ ] Reviewed final AWS bill

---

## Self-Assessment

### Strengths
What parts of the project went well?
```
[Your reflection here]
```

### Challenges
What was difficult? How did you overcome it?
```
[Your reflection here]
```

### Learnings
What did you learn from this project?
```
[Your reflection here]
```

### Improvements
If you were to do it again, what would you do differently?
```
[Your reflection here]
```

---

## Scoring Summary

| Phase | Possible Points | Your Score |
|-------|----------------|------------|
| Phase 1: Infrastructure | 40 | ___ |
| Phase 2: Lambda Functions | 20 | ___ |
| Phase 3: Glue ETL Jobs | 25 | ___ |
| Phase 4: SQL Analytics | 15 | ___ |
| Bonus Features | +10 | ___ |
| **TOTAL** | **100 (+10)** | **___** |

---

**Date Started:** _______________

**Date Completed:** _______________

**Total Time Spent:** _______________ hours

**Final Grade:** _____ / 100

**Status:** ⬜ In Progress | ⬜ Completed | ⬜ Submitted

---

**Congratulations on completing Checkpoint 01!** 🎉

This checklist demonstrates your proficiency in cloud data engineering with AWS serverless technologies.
