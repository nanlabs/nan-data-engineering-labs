# ============================================================================
# AWS EMR Serverless Configuration
# ============================================================================
# Purpose: EMR Serverless for Apache Spark with Delta Lake support
# Components: EMR Application, IAM Roles, Security, Monitoring
# ============================================================================

# ============================================================================
# EMR Serverless Application
# ============================================================================

resource "aws_emrserverless_application" "spark" {
  name          = "${var.project_name}-${var.environment}-spark-app"
  release_label = var.emr_release_label
  type          = "Spark"

  initial_capacity {
    initial_capacity_type = "Driver"

    initial_capacity_config {
      worker_count = var.emr_initial_driver_count

      worker_configuration {
        cpu    = var.emr_driver_cpu
        memory = var.emr_driver_memory
        disk   = var.emr_driver_disk
      }
    }
  }

  initial_capacity {
    initial_capacity_type = "Executor"

    initial_capacity_config {
      worker_count = var.emr_initial_executor_count

      worker_configuration {
        cpu    = var.emr_executor_cpu
        memory = var.emr_executor_memory
        disk   = var.emr_executor_disk
      }
    }
  }

  maximum_capacity {
    cpu    = var.emr_max_cpu
    memory = var.emr_max_memory
    disk   = var.emr_max_disk
  }

  auto_start_configuration {
    enabled = var.emr_auto_start_enabled
  }

  auto_stop_configuration {
    enabled              = var.emr_auto_stop_enabled
    idle_timeout_minutes = var.emr_idle_timeout_minutes
  }

  network_configuration {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.emr_serverless.id]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-spark-app"
  }
}

# ============================================================================
# Security Group for EMR Serverless
# ============================================================================

resource "aws_security_group" "emr_serverless" {
  name_prefix = "${var.project_name}-${var.environment}-emr-serverless-"
  description = "Security group for EMR Serverless"
  vpc_id      = aws_vpc.lakehouse.id

  ingress {
    description = "Allow internal communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-serverless-sg"
  }
}

# ============================================================================
# IAM Roles for EMR Serverless
# ============================================================================

# EMR Serverless Service Role
resource "aws_iam_role" "emr_serverless_service" {
  name = "${var.project_name}-${var.environment}-emr-serverless-service"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "emr-serverless.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-serverless-service"
  }
}

# EMR Serverless Job Runtime Role
resource "aws_iam_role" "emr_job_runtime" {
  name = "${var.project_name}-${var.environment}-emr-job-runtime"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "emr-serverless.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-job-runtime"
  }
}

# S3 Access Policy for EMR Jobs
resource "aws_iam_role_policy" "emr_s3_access" {
  name = "emr-s3-access"
  role = aws_iam_role.emr_job_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.raw.arn}/*",
          "${aws_s3_bucket.bronze.arn}/*",
          "${aws_s3_bucket.silver.arn}/*",
          "${aws_s3_bucket.gold.arn}/*",
          "${aws_s3_bucket.scripts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          aws_s3_bucket.bronze.arn,
          aws_s3_bucket.silver.arn,
          aws_s3_bucket.gold.arn,
          aws_s3_bucket.scripts.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::*.elasticmapreduce/*",
          "arn:aws:s3:::*.elasticmapreduce"
        ]
      }
    ]
  })
}

# Glue Catalog Access Policy
resource "aws_iam_role_policy" "emr_glue_access" {
  name = "emr-glue-access"
  role = aws_iam_role.emr_job_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:BatchCreatePartition",
          "glue:BatchDeletePartition",
          "glue:BatchGetPartition",
          "glue:UpdatePartition"
        ]
        Resource = [
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.raw.name}",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.bronze.name}",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.silver.name}",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.gold.name}",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.raw.name}/*",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.bronze.name}/*",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.silver.name}/*",
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.gold.name}/*"
        ]
      }
    ]
  })
}

# Lake Formation Permissions Policy
resource "aws_iam_role_policy" "emr_lakeformation_access" {
  name = "emr-lakeformation-access"
  role = aws_iam_role.emr_job_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lakeformation:GetDataAccess",
          "lakeformation:GrantPermissions",
          "lakeformation:RevokePermissions",
          "lakeformation:GetDataLakeSettings",
          "lakeformation:PutDataLakeSettings"
        ]
        Resource = "*"
      }
    ]
  })
}

# KMS Encryption Access Policy
resource "aws_iam_role_policy" "emr_kms_access" {
  name = "emr-kms-access"
  role = aws_iam_role.emr_job_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.data.arn,
          aws_kms_key.catalog.arn,
          aws_kms_key.logs.arn
        ]
      }
    ]
  })
}

# CloudWatch Logs Access Policy
resource "aws_iam_role_policy" "emr_logs_access" {
  name = "emr-logs-access"
  role = aws_iam_role.emr_job_runtime.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.emr_serverless.arn}:*"
        ]
      }
    ]
  })
}

# ============================================================================
# Lake Formation Permissions for EMR
# ============================================================================

resource "aws_lakeformation_permissions" "emr_raw_tables" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"]

  table {
    database_name = aws_glue_catalog_database.raw.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "emr_bronze_tables" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"]

  table {
    database_name = aws_glue_catalog_database.bronze.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "emr_silver_tables" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"]

  table {
    database_name = aws_glue_catalog_database.silver.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "emr_gold_tables" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"]

  table {
    database_name = aws_glue_catalog_database.gold.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "emr_raw_location" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = aws_s3_bucket.raw.arn
  }
}

resource "aws_lakeformation_permissions" "emr_bronze_location" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = aws_s3_bucket.bronze.arn
  }
}

resource "aws_lakeformation_permissions" "emr_silver_location" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = aws_s3_bucket.silver.arn
  }
}

resource "aws_lakeformation_permissions" "emr_gold_location" {
  principal   = aws_iam_role.emr_job_runtime.arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = aws_s3_bucket.gold.arn
  }
}

# ============================================================================
# EMR Studio (Optional - for interactive development)
# ============================================================================

resource "aws_emr_studio" "main" {
  count = var.enable_emr_studio ? 1 : 0

  name                        = "${var.project_name}-${var.environment}-emr-studio"
  auth_mode                   = "IAM"
  default_s3_location         = "s3://${aws_s3_bucket.scripts.bucket}/emr-studio/"
  engine_security_group_id    = aws_security_group.emr_studio_engine[0].id
  workspace_security_group_id = aws_security_group.emr_studio_workspace[0].id
  vpc_id                      = aws_vpc.lakehouse.id
  subnet_ids                  = aws_subnet.private[*].id
  service_role                = aws_iam_role.emr_studio_service[0].arn

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-studio"
  }
}

# EMR Studio Engine Security Group
resource "aws_security_group" "emr_studio_engine" {
  count = var.enable_emr_studio ? 1 : 0

  name_prefix = "${var.project_name}-${var.environment}-emr-studio-engine-"
  description = "Security group for EMR Studio engines"
  vpc_id      = aws_vpc.lakehouse.id

  ingress {
    description     = "Allow from workspace"
    from_port       = 18888
    to_port         = 18888
    protocol        = "tcp"
    security_groups = [aws_security_group.emr_studio_workspace[0].id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-studio-engine-sg"
  }
}

# EMR Studio Workspace Security Group
resource "aws_security_group" "emr_studio_workspace" {
  count = var.enable_emr_studio ? 1 : 0

  name_prefix = "${var.project_name}-${var.environment}-emr-studio-workspace-"
  description = "Security group for EMR Studio workspaces"
  vpc_id      = aws_vpc.lakehouse.id

  egress {
    description     = "Allow to engines"
    from_port       = 18888
    to_port         = 18888
    protocol        = "tcp"
    security_groups = [aws_security_group.emr_studio_engine[0].id]
  }

  egress {
    description = "Allow HTTPS to internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-studio-workspace-sg"
  }
}

# EMR Studio Service Role
resource "aws_iam_role" "emr_studio_service" {
  count = var.enable_emr_studio ? 1 : 0

  name = "${var.project_name}-${var.environment}-emr-studio-service"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "emr_studio_service" {
  count = var.enable_emr_studio ? 1 : 0

  role       = aws_iam_role.emr_studio_service[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEMRServicePolicy_v2"
}

# ============================================================================
# CloudWatch Monitoring for EMR Serverless
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "emr_cpu_utilization" {
  alarm_name          = "${var.project_name}-${var.environment}-emr-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EMRServerless"
  period              = "300"
  statistic           = "Average"
  threshold           = var.emr_cpu_alarm_threshold
  alarm_description   = "This metric monitors EMR CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApplicationId = aws_emrserverless_application.spark.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "emr_memory_utilization" {
  alarm_name          = "${var.project_name}-${var.environment}-emr-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EMRServerless"
  period              = "300"
  statistic           = "Average"
  threshold           = var.emr_memory_alarm_threshold
  alarm_description   = "This metric monitors EMR memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApplicationId = aws_emrserverless_application.spark.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-memory-alarm"
  }
}

# ============================================================================
# Delta Lake Configuration Resources
# ============================================================================

# S3 bucket policy for Delta Lake operations
resource "aws_s3_bucket_policy" "delta_lake_access" {
  bucket = aws_s3_bucket.silver.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DeltaLakeAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.emr_job_runtime.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.silver.arn,
          "${aws_s3_bucket.silver.arn}/*"
        ]
      }
    ]
  })
}

# Upload Delta Lake configuration script
resource "aws_s3_object" "delta_lake_init" {
  bucket  = aws_s3_bucket.scripts.bucket
  key     = "config/delta-lake-init.conf"
  content = <<-EOT
    # Delta Lake Configuration for EMR Serverless
    spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension
    spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog
    spark.databricks.delta.retentionDurationCheck.enabled=false
    spark.databricks.delta.schema.autoMerge.enabled=${var.delta_auto_merge_schema}
    spark.databricks.delta.properties.defaults.enableChangeDataFeed=${var.delta_enable_cdf}
    spark.databricks.delta.optimizeWrite.enabled=true
    spark.databricks.delta.autoCompact.enabled=true

    # Performance tuning
    spark.sql.adaptive.enabled=true
    spark.sql.adaptive.coalescePartitions.enabled=true
    spark.sql.adaptive.skewJoin.enabled=true

    # Memory settings
    spark.driver.memory=${var.emr_driver_memory}
    spark.executor.memory=${var.emr_executor_memory}
    spark.executor.cores=${var.emr_executor_cores}
    spark.executor.instances=${var.emr_executor_instances}

    # S3 optimization
    spark.hadoop.fs.s3a.connection.maximum=1000
    spark.hadoop.fs.s3a.fast.upload=true
    spark.hadoop.fs.s3a.fast.upload.buffer=disk
    spark.hadoop.fs.s3a.multipart.size=104857600
    spark.hadoop.fs.s3a.connection.ssl.enabled=true

    # Glue Catalog integration
    spark.sql.catalogImplementation=hive
    spark.hadoop.hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory
  EOT

  content_type = "text/plain"

  tags = {
    Name = "${var.project_name}-${var.environment}-delta-config"
  }
}

# Upload sample EMR job script
resource "aws_s3_object" "emr_job_template" {
  bucket  = aws_s3_bucket.scripts.bucket
  key     = "emr-jobs/delta_lake_etl_template.py"
  content = <<-EOT
    #!/usr/bin/env python3
    """
    EMR Serverless Delta Lake ETL Template
    """
    from pyspark.sql import SparkSession
    from delta import DeltaTable
    import sys

    def main():
        # Initialize Spark session
        spark = SparkSession.builder \
            .appName("DeltaLakeETL") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .enableHiveSupport() \
            .getOrCreate()

        # Get parameters
        source_path = sys.argv[1]
        target_path = sys.argv[2]

        # Read source data
        df = spark.read.format("delta").load(source_path)

        # Transform data
        transformed_df = df.filter("value IS NOT NULL")

        # Write to Delta Lake with merge
        if DeltaTable.isDeltaTable(spark, target_path):
            delta_table = DeltaTable.forPath(spark, target_path)
            delta_table.alias("target").merge(
                transformed_df.alias("source"),
                "target.id = source.id"
            ).whenMatchedUpdateAll() \
             .whenNotMatchedInsertAll() \
             .execute()
        else:
            transformed_df.write.format("delta") \
                .mode("overwrite") \
                .save(target_path)

        # Optimize table
        spark.sql(f"OPTIMIZE delta.`{target_path}`")

        spark.stop()

    if __name__ == "__main__":
        main()
  EOT

  content_type = "text/x-python"

  tags = {
    Name = "${var.project_name}-${var.environment}-emr-template"
  }
}
