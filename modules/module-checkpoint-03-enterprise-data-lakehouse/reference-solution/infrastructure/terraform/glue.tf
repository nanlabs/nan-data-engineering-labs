# ============================================================================
# AWS Glue Configuration - Crawlers, ETL Jobs, Triggers, Data Quality
# ============================================================================
# Purpose: Complete Glue infrastructure for data lakehouse ETL pipeline
# Components: Crawlers, PySpark jobs, Triggers, Data Quality, Connections
# ============================================================================

# ============================================================================
# Glue Crawlers Configuration
# ============================================================================

# Raw Zone Crawler
resource "aws_glue_crawler" "raw" {
  name          = "${var.project_name}-${var.environment}-raw-crawler"
  database_name = aws_glue_catalog_database.raw.name
  role          = aws_iam_role.glue_crawler.arn
  description   = "Crawler for raw data ingestion layer"

  schedule = var.glue_crawler_schedule_raw

  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}/"

    exclusions = [
      "**/_temporary/**",
      "**/.spark/**",
      "**/_SUCCESS",
      "**/*.crc"
    ]
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }

  lineage_configuration {
    crawler_lineage_settings = "ENABLE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
    }
  })

  tags = {
    Name  = "${var.project_name}-${var.environment}-raw-crawler"
    Layer = "raw"
  }
}

# Bronze Zone Crawler
resource "aws_glue_crawler" "bronze" {
  name          = "${var.project_name}-${var.environment}-bronze-crawler"
  database_name = aws_glue_catalog_database.bronze.name
  role          = aws_iam_role.glue_crawler.arn
  description   = "Crawler for bronze validated data layer"

  schedule = var.glue_crawler_schedule_bronze

  s3_target {
    path = "s3://${aws_s3_bucket.bronze.bucket}/"

    exclusions = [
      "**/_temporary/**",
      "**/.spark/**",
      "**/_SUCCESS",
      "**/*.crc",
      "**/_delta_log/**"
    ]
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  lineage_configuration {
    crawler_lineage_settings = "ENABLE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  tags = {
    Name  = "${var.project_name}-${var.environment}-bronze-crawler"
    Layer = "bronze"
  }
}

# Silver Zone Crawler
resource "aws_glue_crawler" "silver" {
  name          = "${var.project_name}-${var.environment}-silver-crawler"
  database_name = aws_glue_catalog_database.silver.name
  role          = aws_iam_role.glue_crawler.arn
  description   = "Crawler for silver cleansed data layer"

  schedule = var.glue_crawler_schedule_silver

  s3_target {
    path = "s3://${aws_s3_bucket.silver.bucket}/"

    exclusions = [
      "**/_temporary/**",
      "**/.spark/**",
      "**/_SUCCESS",
      "**/*.crc",
      "**/_delta_log/**"
    ]
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  lineage_configuration {
    crawler_lineage_settings = "ENABLE"
  }

  lake_formation_configuration {
    use_lake_formation_credentials = true
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  tags = {
    Name  = "${var.project_name}-${var.environment}-silver-crawler"
    Layer = "silver"
  }
}

# Gold Zone Crawler
resource "aws_glue_crawler" "gold" {
  name          = "${var.project_name}-${var.environment}-gold-crawler"
  database_name = aws_glue_catalog_database.gold.name
  role          = aws_iam_role.glue_crawler.arn
  description   = "Crawler for gold aggregated data layer"

  schedule = var.glue_crawler_schedule_gold

  s3_target {
    path = "s3://${aws_s3_bucket.gold.bucket}/"

    exclusions = [
      "**/_temporary/**",
      "**/.spark/**",
      "**/_SUCCESS",
      "**/*.crc",
      "**/_delta_log/**"
    ]
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  lineage_configuration {
    crawler_lineage_settings = "ENABLE"
  }

  lake_formation_configuration {
    use_lake_formation_credentials = true
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })

  tags = {
    Name  = "${var.project_name}-${var.environment}-gold-crawler"
    Layer = "gold"
  }
}

# ============================================================================
# IAM Role for Glue Crawlers
# ============================================================================

resource "aws_iam_role" "glue_crawler" {
  name = "${var.project_name}-${var.environment}-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_crawler_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_crawler_s3" {
  name = "glue-crawler-s3-policy"
  role = aws_iam_role.glue_crawler.id

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
          "${aws_s3_bucket.raw.arn}",
          "${aws_s3_bucket.raw.arn}/*",
          "${aws_s3_bucket.bronze.arn}",
          "${aws_s3_bucket.bronze.arn}/*",
          "${aws_s3_bucket.silver.arn}",
          "${aws_s3_bucket.silver.arn}/*",
          "${aws_s3_bucket.gold.arn}",
          "${aws_s3_bucket.gold.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.data.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["${aws_cloudwatch_log_group.glue_crawlers.arn}:*"]
      },
      {
        Effect = "Allow"
        Action = [
          "lakeformation:GetDataAccess"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# Glue ETL Jobs - PySpark
# ============================================================================

# Job 1: Raw to Bronze - Data Ingestion and Validation
resource "aws_glue_job" "raw_to_bronze" {
  name         = "${var.project_name}-${var.environment}-raw-to-bronze"
  role_arn     = aws_iam_role.glue_service.arn
  description  = "ETL job to ingest raw data, validate, deduplicate, and write to bronze layer"
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue-jobs/raw_to_bronze.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.bucket}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.glue_jobs.name
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/temp/"
    "--enable-glue-datacatalog"          = "true"

    # Custom job parameters
    "--SOURCE_DATABASE"      = aws_glue_catalog_database.raw.name
    "--TARGET_DATABASE"      = aws_glue_catalog_database.bronze.name
    "--SOURCE_BUCKET"        = aws_s3_bucket.raw.bucket
    "--TARGET_BUCKET"        = aws_s3_bucket.bronze.bucket
    "--DATA_QUALITY_ENABLED" = "true"
    "--DEDUPLICATION_KEYS"   = var.deduplication_keys
  }

  execution_property {
    max_concurrent_runs = var.glue_max_concurrent_runs
  }

  max_retries       = var.glue_max_retries
  timeout           = var.glue_job_timeout
  number_of_workers = var.glue_number_of_workers
  worker_type       = var.glue_worker_type

  tags = {
    Name      = "${var.project_name}-${var.environment}-raw-to-bronze"
    JobType   = "ETL"
    Layer     = "bronze"
    Schedule  = "scheduled"
  }
}

# Job 2: Bronze to Silver - Data Cleansing and Transformation
resource "aws_glue_job" "bronze_to_silver" {
  name         = "${var.project_name}-${var.environment}-bronze-to-silver"
  role_arn     = aws_iam_role.glue_service.arn
  description  = "ETL job to cleanse bronze data, apply business rules, and write to silver layer"
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue-jobs/bronze_to_silver.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.bucket}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.glue_jobs.name
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/temp/"
    "--enable-glue-datacatalog"          = "true"
    "--datalake-formats"                 = "delta"

    # Custom job parameters
    "--SOURCE_DATABASE"         = aws_glue_catalog_database.bronze.name
    "--TARGET_DATABASE"         = aws_glue_catalog_database.silver.name
    "--SOURCE_BUCKET"           = aws_s3_bucket.bronze.bucket
    "--TARGET_BUCKET"           = aws_s3_bucket.silver.bucket
    "--CLEANSING_RULES_ENABLED" = "true"
    "--PARTITION_KEYS"          = var.partition_keys
    "--DELTA_LAKE_ENABLED"      = "true"
  }

  execution_property {
    max_concurrent_runs = var.glue_max_concurrent_runs
  }

  max_retries       = var.glue_max_retries
  timeout           = var.glue_job_timeout
  number_of_workers = var.glue_number_of_workers * 2
  worker_type       = var.glue_worker_type

  tags = {
    Name     = "${var.project_name}-${var.environment}-bronze-to-silver"
    JobType  = "ETL"
    Layer    = "silver"
    Schedule = "scheduled"
  }
}

# Job 3: Silver to Gold - Aggregation and Feature Generation
resource "aws_glue_job" "silver_to_gold" {
  name         = "${var.project_name}-${var.environment}-silver-to-gold"
  role_arn     = aws_iam_role.glue_service.arn
  description  = "ETL job to aggregate silver data and create business-level features for gold layer"
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue-jobs/silver_to_gold.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.bucket}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.glue_jobs.name
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/temp/"
    "--enable-glue-datacatalog"          = "true"
    "--datalake-formats"                 = "delta"

    # Custom job parameters
    "--SOURCE_DATABASE"       = aws_glue_catalog_database.silver.name
    "--TARGET_DATABASE"       = aws_glue_catalog_database.gold.name
    "--SOURCE_BUCKET"         = aws_s3_bucket.silver.bucket
    "--TARGET_BUCKET"         = aws_s3_bucket.gold.bucket
    "--AGGREGATION_ENABLED"   = "true"
    "--AGGREGATION_LEVEL"     = var.gold_aggregation_level
    "--DELTA_LAKE_ENABLED"    = "true"
    "--OPTIMIZE_ENABLED"      = "true"
    "--VACUUM_RETENTION_DAYS" = var.delta_vacuum_retention_days
  }

  execution_property {
    max_concurrent_runs = var.glue_max_concurrent_runs
  }

  max_retries       = var.glue_max_retries
  timeout           = var.glue_job_timeout * 2
  number_of_workers = var.glue_number_of_workers * 3
  worker_type       = var.glue_worker_type

  tags = {
    Name     = "${var.project_name}-${var.environment}-silver-to-gold"
    JobType  = "ETL"
    Layer    = "gold"
    Schedule = "scheduled"
  }
}

# Job 4: Data Quality Assessment
resource "aws_glue_job" "data_quality" {
  name         = "${var.project_name}-${var.environment}-data-quality"
  role_arn     = aws_iam_role.glue_service.arn
  description  = "Job to assess data quality across all layers and publish metrics"
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue-jobs/data_quality.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.bucket}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.glue_jobs.name
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/temp/"
    "--enable-glue-datacatalog"          = "true"

    # Custom job parameters
    "--BRONZE_DATABASE"          = aws_glue_catalog_database.bronze.name
    "--SILVER_DATABASE"          = aws_glue_catalog_database.silver.name
    "--GOLD_DATABASE"            = aws_glue_catalog_database.gold.name
    "--DQ_RESULTS_BUCKET"        = aws_s3_bucket.logs.bucket
    "--DQ_RESULTS_PREFIX"        = "data-quality/"
    "--SNS_TOPIC_ARN"            = aws_sns_topic.data_quality.arn
    "--CRITICAL_THRESHOLD"       = var.dq_critical_threshold
    "--WARNING_THRESHOLD"        = var.dq_warning_threshold
    "--ENABLE_DQ_NOTIFICATIONS"  = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  max_retries       = 1
  timeout           = 120
  number_of_workers = var.glue_number_of_workers
  worker_type       = var.glue_worker_type

  tags = {
    Name     = "${var.project_name}-${var.environment}-data-quality"
    JobType  = "DataQuality"
    Schedule = "scheduled"
  }
}

# Job 5: Schema Evolution Handler
resource "aws_glue_job" "schema_evolution" {
  name         = "${var.project_name}-${var.environment}-schema-evolution"
  role_arn     = aws_iam_role.glue_service.arn
  description  = "Job to handle schema changes and evolution across layers"
  glue_version = var.glue_version

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue-jobs/schema_evolution.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.bucket}/spark-logs/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--continuous-log-logGroup"          = aws_cloudwatch_log_group.glue_jobs.name
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/temp/"
    "--enable-glue-datacatalog"          = "true"
    "--datalake-formats"                 = "delta"

    # Custom job parameters
    "--RAW_DATABASE"             = aws_glue_catalog_database.raw.name
    "--BRONZE_DATABASE"          = aws_glue_catalog_database.bronze.name
    "--SILVER_DATABASE"          = aws_glue_catalog_database.silver.name
    "--SCHEMA_CHANGES_BUCKET"    = aws_s3_bucket.logs.bucket
    "--SCHEMA_CHANGES_PREFIX"    = "schema-changes/"
    "--ENABLE_AUTO_MERGE"        = var.schema_evolution_auto_merge
    "--SNS_TOPIC_ARN"            = aws_sns_topic.alerts.arn
    "--DELTA_LAKE_ENABLED"       = "true"
    "--MERGE_SCHEMA"             = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  max_retries       = 2
  timeout           = 180
  number_of_workers = var.glue_number_of_workers
  worker_type       = var.glue_worker_type

  tags = {
    Name     = "${var.project_name}-${var.environment}-schema-evolution"
    JobType  = "SchemaManagement"
    Schedule = "on-demand"
  }
}

# ============================================================================
# Glue Triggers - Workflow Orchestration
# ============================================================================

# Scheduled Trigger for Raw to Bronze (Daily at 2 AM)
resource "aws_glue_trigger" "raw_to_bronze_scheduled" {
  name     = "${var.project_name}-${var.environment}-raw-to-bronze-trigger"
  type     = "SCHEDULED"
  schedule = var.raw_to_bronze_schedule
  enabled  = var.enable_scheduled_triggers

  actions {
    job_name = aws_glue_job.raw_to_bronze.name

    notification_property {
      notify_delay_after = 30
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-raw-to-bronze-trigger"
  }
}

# Conditional Trigger for Bronze to Silver (After Raw to Bronze Success)
resource "aws_glue_trigger" "bronze_to_silver_conditional" {
  name    = "${var.project_name}-${var.environment}-bronze-to-silver-trigger"
  type    = "CONDITIONAL"
  enabled = var.enable_conditional_triggers

  actions {
    job_name = aws_glue_job.bronze_to_silver.name

    notification_property {
      notify_delay_after = 30
    }
  }

  predicate {
    conditions {
      job_name = aws_glue_job.raw_to_bronze.name
      state    = "SUCCEEDED"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-bronze-to-silver-trigger"
  }
}

# Conditional Trigger for Silver to Gold (After Bronze to Silver Success)
resource "aws_glue_trigger" "silver_to_gold_conditional" {
  name    = "${var.project_name}-${var.environment}-silver-to-gold-trigger"
  type    = "CONDITIONAL"
  enabled = var.enable_conditional_triggers

  actions {
    job_name = aws_glue_job.silver_to_gold.name

    notification_property {
      notify_delay_after = 30
    }
  }

  predicate {
    conditions {
      job_name = aws_glue_job.bronze_to_silver.name
      state    = "SUCCEEDED"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-silver-to-gold-trigger"
  }
}

# Scheduled Trigger for Data Quality (Daily at 8 AM)
resource "aws_glue_trigger" "data_quality_scheduled" {
  name     = "${var.project_name}-${var.environment}-data-quality-trigger"
  type     = "SCHEDULED"
  schedule = var.data_quality_schedule
  enabled  = var.enable_scheduled_triggers

  actions {
    job_name = aws_glue_job.data_quality.name

    notification_property {
      notify_delay_after = 15
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-data-quality-trigger"
  }
}

# On-Demand Trigger for Schema Evolution
resource "aws_glue_trigger" "schema_evolution_on_demand" {
  name    = "${var.project_name}-${var.environment}-schema-evolution-trigger"
  type    = "ON_DEMAND"
  enabled = true

  actions {
    job_name = aws_glue_job.schema_evolution.name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-schema-evolution-trigger"
  }
}

# Crawler Triggers
resource "aws_glue_trigger" "crawlers_scheduled" {
  name     = "${var.project_name}-${var.environment}-crawlers-trigger"
  type     = "SCHEDULED"
  schedule = var.crawlers_schedule
  enabled  = var.enable_crawler_triggers

  actions {
    crawler_name = aws_glue_crawler.raw.name
  }

  actions {
    crawler_name = aws_glue_crawler.bronze.name
  }

  actions {
    crawler_name = aws_glue_crawler.silver.name
  }

  actions {
    crawler_name = aws_glue_crawler.gold.name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-crawlers-trigger"
  }
}

# ============================================================================
# Glue Data Quality Rulesets
# ============================================================================

# Bronze Layer Data Quality Ruleset
resource "aws_glue_data_quality_ruleset" "bronze" {
  name        = "${var.project_name}-${var.environment}-bronze-dq-ruleset"
  description = "Data quality rules for bronze layer validation"

  ruleset = <<-EOT
    Rules = [
      # Completeness checks
      ColumnExists "id",
      IsComplete "id",
      IsUnique "id",

      # Primary key validation
      IsPrimaryKey "id",

      # Timestamp validation
      ColumnExists "ingestion_timestamp",
      IsComplete "ingestion_timestamp",
      ColumnValues "ingestion_timestamp" matches "[0-9]{4}-[0-9]{2}-[0-9]{2}.*",

      # Row count validation
      RowCount between 1 and 10000000,

      # Duplicate detection
      DistinctValuesCount "id" > 0.95 * RowCount,

      # Column correlation
      ColumnCorrelation "id" "ingestion_timestamp" < 0.9
    ]
  EOT

  target_table {
    database_name = aws_glue_catalog_database.bronze.name
    table_name    = "bronze_table"
  }

  tags = {
    Name  = "${var.project_name}-${var.environment}-bronze-dq"
    Layer = "bronze"
  }
}

# Silver Layer Data Quality Ruleset
resource "aws_glue_data_quality_ruleset" "silver" {
  name        = "${var.project_name}-${var.environment}-silver-dq-ruleset"
  description = "Data quality rules for silver layer validation"

  ruleset = <<-EOT
    Rules = [
      # Schema validation
      ColumnExists "id",
      ColumnExists "created_at",
      ColumnExists "updated_at",

      # Data type validation
      ColumnDataType "id" = "STRING",
      ColumnDataType "created_at" = "TIMESTAMP",

      # Null checks
      IsComplete "id",
      IsComplete "created_at",

      # Value constraints
      ColumnLength "id" between 1 and 100,

      # Referential integrity
      IsUnique "id",

      # Date range validation
      ColumnValues "created_at" <= NOW(),
      CustomSql "SELECT COUNT(*) FROM primary WHERE updated_at < created_at" = 0,

      # Statistical checks
      StandardDeviation "numeric_column" < 100,
      Mean "numeric_column" between 0 and 1000,

      # Anomaly detection
      AnomalyDetection "numeric_column" with threshold 3.0
    ]
  EOT

  target_table {
    database_name = aws_glue_catalog_database.silver.name
    table_name    = "silver_table"
  }

  tags = {
    Name  = "${var.project_name}-${var.environment}-silver-dq"
    Layer = "silver"
  }
}

# Gold Layer Data Quality Ruleset
resource "aws_glue_data_quality_ruleset" "gold" {
  name        = "${var.project_name}-${var.environment}-gold-dq-ruleset"
  description = "Data quality rules for gold layer validation"

  ruleset = <<-EOT
    Rules = [
      # Aggregation validation
      ColumnExists "aggregation_key",
      ColumnExists "metric_value",
      ColumnExists "calculation_date",

      # Completeness
      IsComplete "aggregation_key",
      IsComplete "metric_value",

      # Value ranges
      ColumnValues "metric_value" >= 0,

      # Uniqueness per aggregation
      IsUnique "aggregation_key" "calculation_date",

      # Temporal consistency
      CustomSql "SELECT COUNT(*) FROM primary WHERE calculation_date > NOW()" = 0,

      # Business rules
      ColumnValues "metric_value" <= ColumnExpression("metric_value * 1.5"),

      # Row count thresholds
      RowCount > 100,

      # Freshness check
      ColumnValues "calculation_date" >= (NOW() - INTERVAL '7' DAY)
    ]
  EOT

  target_table {
    database_name = aws_glue_catalog_database.gold.name
    table_name    = "gold_table"
  }

  tags = {
    Name  = "${var.project_name}-${var.environment}-gold-dq"
    Layer = "gold"
  }
}

# ============================================================================
# Glue Connections (RDS, Redshift, etc.)
# ============================================================================

# Connection to RDS (if needed for source data)
resource "aws_glue_connection" "rds" {
  count = var.enable_rds_connection ? 1 : 0

  name            = "${var.project_name}-${var.environment}-rds-connection"
  description     = "Connection to RDS database for data ingestion"
  connection_type = "JDBC"

  physical_connection_requirements {
    availability_zone      = data.aws_availability_zones.available.names[0]
    security_group_id_list = [aws_security_group.glue_connection[0].id]
    subnet_id              = aws_subnet.private[0].id
  }

  connection_properties = {
    JDBC_CONNECTION_URL = var.rds_jdbc_url
    USERNAME            = var.rds_username
    PASSWORD            = var.rds_password
    JDBC_ENFORCE_SSL    = "true"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-connection"
  }
}

# Connection to Redshift (for analytics)
resource "aws_glue_connection" "redshift" {
  count = var.enable_redshift_connection ? 1 : 0

  name            = "${var.project_name}-${var.environment}-redshift-connection"
  description     = "Connection to Redshift data warehouse"
  connection_type = "JDBC"

  physical_connection_requirements {
    availability_zone      = data.aws_availability_zones.available.names[0]
    security_group_id_list = [aws_security_group.glue_connection[0].id]
    subnet_id              = aws_subnet.private[0].id
  }

  connection_properties = {
    JDBC_CONNECTION_URL = var.redshift_jdbc_url
    USERNAME            = var.redshift_username
    PASSWORD            = var.redshift_password
    JDBC_ENFORCE_SSL    = "true"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redshift-connection"
  }
}

# Security Group for Glue Connections
resource "aws_security_group" "glue_connection" {
  count = var.enable_rds_connection || var.enable_redshift_connection ? 1 : 0

  name_prefix = "${var.project_name}-${var.environment}-glue-conn-"
  description = "Security group for Glue connections"
  vpc_id      = aws_vpc.lakehouse.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-glue-conn-sg"
  }
}

# ============================================================================
# Glue Workflow
# ============================================================================

resource "aws_glue_workflow" "main" {
  name        = "${var.project_name}-${var.environment}-etl-workflow"
  description = "Main ETL workflow for data lakehouse pipeline"

  max_concurrent_runs = var.workflow_max_concurrent_runs

  default_run_properties = {
    environment        = var.environment
    project            = var.project_name
    enable_monitoring  = "true"
    notification_topic = aws_sns_topic.alerts.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-etl-workflow"
  }
}
