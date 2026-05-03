# Infrastructure Setup Guide - Starter Template

This guide walks you through completing and deploying the CloudMart Serverless Data Lake infrastructure using Terraform.

## Overview

You will create a complete serverless data lake on AWS implementing the **Medallion Architecture** with three layers:
- **Bronze (Raw)**: Unprocessed data from source systems
- **Silver (Processed)**: Cleaned, validated, and transformed data
- **Gold (Curated)**: Business-ready aggregated and analytical data

## Architecture Components

The infrastructure includes:
- **S3 Buckets**: Storage for each medallion layer + logs and Athena results
- **AWS Lambda**: Serverless functions for data ingestion
- **AWS Glue**: Crawlers for schema discovery, ETL jobs for transformations
- **Amazon Athena**: SQL query engine for analytics
- **IAM Roles & Policies**: Security and access control
- **SNS Topics**: Alerting and notifications
- **CloudWatch**: Monitoring, logging, and alarms

## Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with appropriate permissions
2. **Terraform** installed (v1.0+)
   ```bash
   terraform --version
   ```
3. **AWS CLI** configured with credentials
   ```bash
   aws configure
   aws sts get-caller-identity
   ```
4. **Python 3.11+** for Lambda development
5. Basic understanding of Terraform, S3, Lambda, and Glue

## Step-by-Step Completion Guide

### Step 1: Configure Variables

1. Review `variables.tf` to understand all configurable parameters
2. Create `terraform.tfvars` with your custom values:

```hcl
# terraform.tfvars
project_name     = "cloudmart-data-lake"
environment      = "dev"
aws_region       = "us-east-1"
s3_bucket_prefix = "your-unique-prefix"  # Change this!
alert_email      = "your-email@example.com"

# Optional: Adjust compute resources
lambda_memory_mb         = 512
glue_number_of_workers   = 2
```

### Step 2: Complete TODOs in main.tf

Work through each TODO comment in `main.tf`. Recommended order:

#### A. S3 Lifecycle Configuration (~Line 90)
**TODO**: Add lifecycle rules for raw_data bucket

**Learning Objective**: Understand S3 storage class transitions for cost optimization

**Solution Hint**:
```hcl
rule {
  id     = "archive-old-raw-data"
  status = "Enabled"

  transition {
    days          = 90
    storage_class = "STANDARD_IA"
  }

  transition {
    days          = 180
    storage_class = "GLACIER"
  }

  expiration {
    days = 365
  }
}

rule {
  id     = "delete-incomplete-multipart-uploads"
  status = "Enabled"

  abort_incomplete_multipart_upload {
    days_after_initiation = 7
  }
}
```

**Reference**: [S3 Lifecycle Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration)

#### B. Lambda IAM Policy (~Line 240)
**TODO**: Complete IAM policy for Lambda S3 access

**Learning Objective**: Understand least-privilege IAM policies

**What Lambda needs**:
- Read from raw_data bucket
- Write to processed_data bucket
- Publish to SNS topic
- Write CloudWatch logs

**Solution Hint**:
```hcl
policy = jsonencode({
  Version = "2012-10-17"
  Statement = [
    {
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        "${aws_s3_bucket.raw_data.arn}",
        "${aws_s3_bucket.raw_data.arn}/*"
      ]
    },
    {
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      Resource = [
        "${aws_s3_bucket.processed_data.arn}/*"
      ]
    },
    {
      Effect = "Allow"
      Action = [
        "sns:Publish"
      ]
      Resource = [
        aws_sns_topic.data_pipeline_alerts.arn
      ]
    }
  ]
})
```

#### C. Glue IAM Role and Policy (~Line 275)
**TODO**: Configure Glue service role and S3 access

**Learning Objective**: Understand Glue permissions requirements

**What Glue needs**:
- Read/write all three S3 layers (bronze, silver, gold)
- Access to logs bucket for scripts and temp files
- Glue Data Catalog access (provided by AWS managed policy)

#### D. SNS Email Subscription (~Line 320)
**TODO**: Create email subscription for alerts

**Solution Hint**:
```hcl
resource "aws_sns_topic_subscription" "pipeline_alerts_email" {
  topic_arn = aws_sns_topic.data_pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
```

**Note**: You'll receive a confirmation email - click the link to activate

#### E. Lambda Functions (~Line 335)
**TODO**: Create Lambda functions for data ingestion

**Learning Objective**: Deploy Lambda functions with Terraform

**Steps for each function** (orders, customers, products, events):

1. Create deployment package data source:
```hcl
data "archive_file" "orders_ingestion_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../pipelines/lambda/orders_ingestion"
  output_path = "${path.module}/lambda_packages/orders_ingestion.zip"
}
```

2. Create Lambda function:
```hcl
resource "aws_lambda_function" "orders_ingestion" {
  function_name = "${var.project_name}-orders-ingestion-${var.environment}"
  role          = aws_iam_role.lambda_ingestion.arn

  filename         = data.archive_file.orders_ingestion_lambda.output_path
  source_code_hash = data.archive_file.orders_ingestion_lambda.output_base64sha256

  runtime = var.lambda_runtime
  handler = "handler.lambda_handler"

  timeout     = var.lambda_timeout_seconds
  memory_size = var.lambda_memory_mb

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_data.id
      SNS_TOPIC_ARN    = aws_sns_topic.data_pipeline_alerts.arn
      CLOUDWATCH_NAMESPACE = "DataLake/Orders"
    }
  }
}
```

3. Create S3 trigger:
```hcl
resource "aws_lambda_permission" "allow_s3_orders" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orders_ingestion.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_data.arn
}

resource "aws_s3_bucket_notification" "orders_trigger" {
  bucket = aws_s3_bucket.raw_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.orders_ingestion.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "orders/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3_orders]
}
```

Repeat for customers (JSON), products (CSV), and events (JSONL).

#### F. Glue Crawlers (~Line 420)
**TODO**: Create Glue crawlers for automatic schema discovery

**Learning Objective**: Automate data catalog updates

**Example for orders**:
```hcl
resource "aws_glue_crawler" "bronze_orders" {
  name          = "${var.project_name}-bronze-orders-${var.environment}"
  role          = aws_iam_role.glue_etl.arn
  database_name = aws_glue_catalog_database.bronze.name

  s3_target {
    path = "s3://${aws_s3_bucket.raw_data.id}/orders/"
  }

  schedule = var.enable_crawler_schedules ? var.raw_crawler_schedule : null

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }
}
```

Create crawlers for:
- Bronze: orders, customers, products, events
- Silver: orders, customers, products
- Gold: sales_summary, customer_360

#### G. Glue ETL Jobs (~Line 465)
**TODO**: Create Glue jobs for data transformations

**Learning Objective**: Orchestrate PySpark ETL jobs

**Steps**:

1. Upload script to S3:
```hcl
resource "aws_s3_object" "glue_script_bronze_to_silver_orders" {
  bucket = aws_s3_bucket.logs.id
  key    = "glue-scripts/bronze_to_silver_orders.py"
  source = "${path.module}/../pipelines/glue/bronze_to_silver_orders.py"
  etag   = filemd5("${path.module}/../pipelines/glue/bronze_to_silver_orders.py")
}
```

2. Create Glue job:
```hcl
resource "aws_glue_job" "bronze_to_silver_orders" {
  name     = "${var.project_name}-bronze-to-silver-orders-${var.environment}"
  role_arn = aws_iam_role.glue_etl.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.logs.id}/glue-scripts/bronze_to_silver_orders.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--job-bookmark-option" = var.enable_glue_job_bookmarks ? "job-bookmark-enable" : "job-bookmark-disable"
    "--enable-metrics"      = "true"
    "--enable-spark-ui"     = "true"
    "--source_database"     = aws_glue_catalog_database.bronze.name
    "--source_table"        = "orders"
    "--target_s3_path"      = "s3://${aws_s3_bucket.processed_data.id}/orders/"
    "--target_database"     = aws_glue_catalog_database.silver.name
    "--target_table"        = "orders"
  }

  glue_version      = var.glue_version
  worker_type       = var.glue_worker_type
  number_of_workers = var.glue_number_of_workers
  timeout           = var.glue_job_timeout_minutes
}
```

Create jobs for:
- bronze_to_silver_orders
- bronze_to_silver_customers
- bronze_to_silver_products
- silver_to_gold_sales_summary
- silver_to_gold_customer_360

#### H. CloudWatch Alarms (~Line 530)
**TODO**: Create monitoring alarms

**Example**:
```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_orders_errors" {
  alarm_name          = "${var.project_name}-lambda-orders-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  alarm_description   = "Alert on Lambda orders ingestion errors"

  dimensions = {
    FunctionName = aws_lambda_function.orders_ingestion.function_name
  }

  alarm_actions = [aws_sns_topic.data_pipeline_alerts.arn]
}
```

### Step 3: Initialize and Validate Terraform

```bash
# Initialize Terraform (downloads providers)
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt

# Review what will be created
terraform plan
```

### Step 4: Deploy Infrastructure

```bash
# Apply configuration
terraform apply

# Review the plan and type 'yes' to confirm
```

**Expected resources**: ~40-50 resources depending on how many TODOs you completed.

### Step 5: Verify Deployment

1. **Check S3 buckets**:
   ```bash
   aws s3 ls | grep cloudmart
   ```

2. **Verify Lambda functions**:
   ```bash
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `cloudmart`)].FunctionName'
   ```

3. **Check Glue databases**:
   ```bash
   aws glue get-databases --query 'DatabaseList[].Name'
   ```

4. **Confirm SNS subscription**:
   - Check your email for confirmation message
   - Click the confirmation link

### Step 6: Test the Pipeline

1. **Upload sample data**:
   ```bash
   # Orders (CSV)
   aws s3 cp sample-orders.csv s3://your-bucket-raw/orders/

   # Customers (JSON)
   aws s3 cp sample-customers.json s3://your-bucket-raw/customers/
   ```

2. **Monitor Lambda execution**:
   ```bash
   aws logs tail /aws/lambda/cloudmart-data-lake-orders-ingestion-dev --follow
   ```

3. **Run Glue crawler**:
   ```bash
   aws glue start-crawler --name cloudmart-data-lake-bronze-orders-dev
   ```

4. **Query with Athena**:
   - Open AWS Athena console
   - Select workgroup: cloudmart-data-lake-primary-dev
   - Query: `SELECT * FROM bronze.orders LIMIT 10;`

## Troubleshooting

### Common Issues

**1. S3 bucket already exists**
- Error: `BucketAlreadyExists`
- Solution: Change `s3_bucket_prefix` in terraform.tfvars to something unique

**2. Lambda deployment package too large**
- Error: `InvalidParameterValueException`
- Solution: Ensure you're not including unnecessary files in lambda source_dir

**3. Glue job fails with "Access Denied"**
- Solution: Verify Glue IAM role has S3 read/write permissions for all layers

**4. Crawler finds no tables**
- Solution: Ensure data exists in S3 path, check folder structure matches expected format

**5. Terraform apply hangs**
- Solution: Check AWS CLI credentials are valid: `aws sts get-caller-identity`

### Validation Commands

```bash
# List all resources
terraform state list

# Show specific resource
terraform state show aws_s3_bucket.raw_data

# View outputs
terraform output

# Destroy infrastructure (careful!)
terraform destroy
```

## Cost Optimization Tips

1. **Use lifecycle policies** to move old data to cheaper storage
2. **Set Glue job bookmarks** to avoid reprocessing data
3. **Configure Lambda reserved concurrency** to limit parallel executions
4. **Use Athena query result location** lifecycle rules
5. **Enable CloudWatch log retention limits** to avoid indefinite log storage

## Expected Costs (Estimate)

With light usage (dev environment):
- S3 storage: $1-5/month
- Lambda executions: $0-2/month (within free tier)
- Glue crawler: $0.44/hour (only when running)
- Glue ETL jobs: $0.44/DPU-hour
- Athena queries: $5/TB scanned
- **Total**: ~$10-30/month for light development

## Next Steps

After successful deployment:

1. Complete the Lambda handler TODO sections
2. Complete the Glue ETL script TODO sections
3. Create sample datasets for testing
4. Complete the SQL exercises in `sql/01_exercises.sql`
5. Document your learnings and challenges

## Learning Resources

- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [PySpark Programming Guide](https://spark.apache.org/docs/latest/api/python/)
- [Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)

## Self-Assessment

- [ ] Can you explain the medallion architecture?
- [ ] Do you understand IAM least-privilege policies?
- [ ] Can you debug Lambda function errors using CloudWatch?
- [ ] Do you know when to use Glue crawlers vs manual table definitions?
- [ ] Can you optimize S3 lifecycle policies for your use case?

## Support

- Review reference-solution/ for complete implementations
- Check CHECKLIST.md to track your progress
- Consult module README.md for project contextGood luck with your implementation! 🚀
