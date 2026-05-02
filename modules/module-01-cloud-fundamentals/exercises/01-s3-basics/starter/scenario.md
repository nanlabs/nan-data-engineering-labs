# Real-World Scenario: Startup Data Lake

## Business Context

You work as a **Data Engineer** at **QuickMart**, a fast-growing e-commerce startup.

### The Problem

QuickMart has multiple data sources:
- **Application Logs:** JSON logs from web application (errors, user events)
- **Transactional Data:** Daily CSV exports from sales database
- **External APIs:** Data from third-party services (inventory, shipping)

Currently, this data is:
- ❌ On different servers with no structure
- ❌ Without versioning
- ❌ Hard to access for the analytics team
- ❌ No systematic backup

### Your Mission

The CTO asked you to create a **centralized storage system** using S3 as the foundation of the future Data Lake.

### Specific Requirements

1. **Organized Structure**
   ```
   my-data-lake-raw/
   ├── source=app-logs/
   │   └── year=2024/month=01/day=15/
   │       └── app-logs-2024-01-15.json
   ├── source=transactions/
   │   └── year=2024/month=01/day=15/
   │       └── transactions-2024-01-15.csv
   └── source=external-apis/
       └── year=2024/month=01/day=15/
           └── inventory-2024-01-15.json
   ```

   **Why this structure:**
   - `source=X`: Allows filtering by data source
   - `year=YYYY/month=MM/day=DD`: Partitioning for efficient queries
   - Hive-style format: Compatible with Athena, Glue, Spark

2. **Two Buckets**
   - `my-data-lake-raw`: Original data, immutable
   - `my-data-lake-processed`: Clean data after ETL

3. **Required Operations**
   - Upload files daily
   - List files from a specific source
   - Copy files between raw → processed
   - Download files for local analysis
   - Check metadata (size, type, date)

### Example Data

The team provided sample data in `test_data/`:

**app-logs-2024-01-15.json**
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "service": "checkout",
  "message": "Payment processed successfully",
  "user_id": "user_12345",
  "order_id": "ord_67890",
  "amount": 129.99
}
```

**transactions-2024-01-15.csv**
```csv
order_id,customer_id,product_id,quantity,amount,timestamp
ord_67890,cust_123,prod_456,2,129.99,2024-01-15T10:30:45Z
ord_67891,cust_124,prod_457,1,49.99,2024-01-15T11:15:20Z
```

### Deliverables

By the end of this exercise, you should have:

1. **Automated Script** (`s3_operations.sh`) that:
   - Creates the necessary buckets
   - Uploads files with runct structure
   - Lists objects with filters
   - Copies between buckets
   - Downloads for verification

2. **Documentation** of commands used

3. **Validation** that everything works runctly

### Success Metrics

- ✅ Buckets created and accessible
- ✅ Files uploaded with runct paths (partitioned)
- ✅ You can list only application logs (without seeing transactions)
- ✅ Files copied to processed bucket maintain metadata
- ✅ Analytics team can easily download files

### Constraints

- 💰 **Cost:** Use LocalStack (free) for development
- 🔒 **Security:** For now only you have access (IAM in next exercise)
- ⏱️ **Time:** Implementation should take <1 hour

---

## Your Task

Implement `s3_operations.sh` in `my_solution/` that automates all these operations.

**Initial hint:** Start by creating a bucket, then upload a simple file, and expand from there.

**Remember:** In a real environment, this script would be part of a pipeline that runs automatically every night. For now, you will run it manually to understand each step.

---

## Reflection

After implementing, ask yourself:

1. What happens if I upload the same file twice to the same path?
2. How would I prevent accidentally overwriting files?
3. What would happen if I needed to process only January logs without downloading the ENTIRE bucket?

You will answer these questions in future exercises (versioning, lifecycle policies, Athena queries).

**Let's go!** 🚀
