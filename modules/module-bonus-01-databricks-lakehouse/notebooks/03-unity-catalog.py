# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 03: Unity Catalog - Data Governance
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC - Understand Unity Catalog's three-level namespace
# MAGIC - Implement fine-grained access control
# MAGIC - Configure row-level and column-level security
# MAGIC - Track data lineage
# MAGIC - Manage data discovery and metadata
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - **Databricks Trial Account or Enterprise plan** (Unity Catalog not available in Community Edition)
# MAGIC - Unity Catalog metastore enabled
# MAGIC - Admin permissions to create catalogs
# MAGIC
# MAGIC ## Estimated Time: 45-60 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *

print("Unity Catalog Environment Check:")
print(f"✅ Current User: {spark.sql('SELECT current_user()').collect()[0][0]}")
print(f"✅ Current Catalog: {spark.sql('SELECT current_catalog()').collect()[0][0]}")
print(f"✅ Current Schema: {spark.sql('SELECT current_schema()').collect()[0][0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Three-Level Namespace
# MAGIC
# MAGIC Unity Catalog uses: **catalog.schema.table**
# MAGIC
# MAGIC Traditional: **database.table**
# MAGIC
# MAGIC Benefits:
# MAGIC - Environment isolation (dev/staging/prod in same workspace)
# MAGIC - Multi-tenant data sharing
# MAGIC - Centralized governance across workspaces

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create training catalog
# MAGIC CREATE CATALOG IF NOT EXISTS training_uc;
# MAGIC
# MAGIC -- Show all catalogs
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Use the training catalog
# MAGIC USE CATALOG training_uc;
# MAGIC
# MAGIC -- Create schemas for different environments
# MAGIC CREATE SCHEMA IF NOT EXISTS dev COMMENT 'Development environment';
# MAGIC CREATE SCHEMA IF NOT EXISTS staging COMMENT 'Staging environment';
# MAGIC CREATE SCHEMA IF NOT EXISTS prod COMMENT 'Production environment';
# MAGIC
# MAGIC -- Show schemas
# MAGIC SHOW SCHEMAS;

# COMMAND ----------

# Create sample data in different environments
print("Creating sample tables across environments...")

# Sample customer data
customers_data = [
    (1, "Alice Johnson", "alice@company.com", "USA", 50000, "PII", True),
    (2, "Bob Smith", "bob@company.com", "UK", 75000, "SENSITIVE", True),
    (3, "Carol White", "carol@company.com", "Canada", 60000, "PUBLIC", True),
    (4, "David Brown", "david@company.com", "USA", 45000, "PII", False),
    (5, "Emma Davis", "emma@company.com", "Germany", 80000, "SENSITIVE", True)
]

schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), False),
    StructField("country", StringType(), False),
    StructField("revenue", IntegerType(), False),
    StructField("classification", StringType(), False),
    StructField("is_active", BooleanType(), False)
])

customers_df = spark.createDataFrame(customers_data, schema)

# Write to dev
customers_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("training_uc.dev.customers")

# Write to staging (with validation)
customers_df.filter(col("is_active") == True).write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("training_uc.staging.customers")

# Write to prod (only active + revenue > 50k)
customers_df.filter((col("is_active") == True) & (col("revenue") > 50000)).write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("training_uc.prod.customers")

print("✅ Tables created in dev, staging, and prod schemas")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query with fully-qualified names
# MAGIC SELECT 'dev' as environment, COUNT(*) as customer_count FROM training_uc.dev.customers
# MAGIC UNION ALL
# MAGIC SELECT 'staging', COUNT(*) FROM training_uc.staging.customers
# MAGIC UNION ALL
# MAGIC SELECT 'prod', COUNT(*) FROM training_uc.prod.customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Access Control - Permissions Model
# MAGIC
# MAGIC Unity Catalog permissions hierarchy:
# MAGIC ```
# MAGIC Metastore (root)
# MAGIC   └─ Catalog (training_uc)
# MAGIC        └─ Schema (dev, staging, prod)
# MAGIC             └─ Table (customers)
# MAGIC                  └─ Column (email, revenue)
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant catalog permissions
# MAGIC -- Note: You need to be catalog owner or admin
# MAGIC
# MAGIC -- Allow all users to use the catalog
# MAGIC GRANT USE CATALOG ON CATALOG training_uc TO `account users`;
# MAGIC
# MAGIC -- Allow developers to use dev schema
# MAGIC GRANT USE SCHEMA ON SCHEMA training_uc.dev TO `account users`;
# MAGIC GRANT SELECT ON SCHEMA training_uc.dev TO `account users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant table-level permissions
# MAGIC
# MAGIC -- Analysts can read from staging
# MAGIC GRANT SELECT ON TABLE training_uc.staging.customers TO `account users`;
# MAGIC
# MAGIC -- Only specific group can access prod
# MAGIC -- GRANT SELECT ON TABLE training_uc.prod.customers TO `data_engineers`;
# MAGIC
# MAGIC -- Show grants
# MAGIC SHOW GRANTS ON TABLE training_uc.dev.customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Row-Level Security
# MAGIC
# MAGIC Filter which rows users can see based on:
# MAGIC - User identity
# MAGIC - Group membership
# MAGIC - Custom logic

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create row filter function
# MAGIC CREATE OR REPLACE FUNCTION training_uc.dev.customer_region_filter(country STRING)
# MAGIC RETURN
# MAGIC   CASE
# MAGIC     -- Admins see all rows
# MAGIC     WHEN is_account_group_member('admins') THEN TRUE
# MAGIC     -- US team sees only US customers
# MAGIC     WHEN is_account_group_member('us_team') AND country = 'USA' THEN TRUE
# MAGIC     -- EU team sees only EU customers
# MAGIC     WHEN is_account_group_member('eu_team') AND country IN ('UK', 'Germany') THEN TRUE
# MAGIC     -- Default: no access
# MAGIC     ELSE FALSE
# MAGIC   END;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Apply row filter to table
# MAGIC ALTER TABLE training_uc.dev.customers SET ROW FILTER training_uc.dev.customer_region_filter ON (country);
# MAGIC
# MAGIC -- Now queries automatically filter rows based on user's group
# MAGIC -- Users in 'us_team' will only see USA customers
# MAGIC SELECT * FROM training_uc.dev.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Remove row filter (for demonstration)
# MAGIC ALTER TABLE training_uc.dev.customers DROP ROW FILTER;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Column-Level Security (Dynamic Views)
# MAGIC
# MAGIC Mask or hide sensitive columns based on user permissions.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create secure view with column masking
# MAGIC CREATE OR REPLACE VIEW training_uc.dev.customers_secure AS
# MAGIC SELECT
# MAGIC   customer_id,
# MAGIC   name,
# MAGIC   -- Mask email for non-privileged users
# MAGIC   CASE
# MAGIC     WHEN is_account_group_member('data_engineers') THEN email
# MAGIC     ELSE CONCAT(SUBSTRING(email, 1, 3), '***@***.com')
# MAGIC   END AS email,
# MAGIC   country,
# MAGIC   -- Hide revenue from analysts
# MAGIC   CASE
# MAGIC     WHEN is_account_group_member('finance') THEN revenue
# MAGIC     WHEN is_account_group_member('data_engineers') THEN revenue
# MAGIC     ELSE NULL
# MAGIC   END AS revenue,
# MAGIC   classification,
# MAGIC   is_active
# MAGIC FROM training_uc.dev.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query secure view (output depends on user's group)
# MAGIC SELECT * FROM training_uc.dev.customers_secure;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Column-level grants
# MAGIC -- Grant SELECT on specific columns only
# MAGIC GRANT SELECT (customer_id, name, country) ON TABLE training_uc.dev.customers TO `account users`;
# MAGIC
# MAGIC -- Revoke access to sensitive columns (email, revenue)
# MAGIC -- Users can query table but won't see email/revenue columns

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: Data Lineage
# MAGIC
# MAGIC Unity Catalog automatically tracks:
# MAGIC - Table-level lineage (which tables created from which)
# MAGIC - Column-level lineage (how columns are computed)
# MAGIC - Job/notebook that modified data

# COMMAND ----------

# Create derived table to demonstrate lineage
print("Creating derived table for lineage tracking...")

# Aggregation that derives from customers
customer_summary_df = spark.sql("""
    SELECT
        country,
        COUNT(*) as customer_count,
        AVG(revenue) as avg_revenue,
        SUM(revenue) as total_revenue,
        current_timestamp() as updated_at
    FROM training_uc.dev.customers
    GROUP BY country
""")

customer_summary_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("training_uc.dev.customer_summary")

print("✅ Derived table created")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM training_uc.dev.customer_summary;

# COMMAND ----------

# MAGIC %md
# MAGIC **To view lineage:**
# MAGIC 1. Go to Data Explorer in Databricks UI
# MAGIC 2. Navigate to: training_uc > dev > customer_summary
# MAGIC 3. Click "Lineage" tab
# MAGIC 4. You'll see visual graph: customers → customer_summary

# COMMAND ----------

# Programmatic lineage (Python API)
print("📊 Retrieving lineage programmatically...")

# Note: This is illustrative - actual API may vary by DBR version
try:
    lineage_info = spark.sql("""
        SELECT
            table_catalog,
            table_schema,
            table_name,
            table_type
        FROM system.information_schema.tables
        WHERE table_catalog = 'training_uc' AND table_schema = 'dev'
    """)
    display(lineage_info)
except Exception as e:
    print(f"Note: Lineage API access requires appropriate permissions: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: Data Discovery & Metadata
# MAGIC
# MAGIC Unity Catalog provides rich metadata:
# MAGIC - Table comments and descriptions
# MAGIC - Column comments
# MAGIC - Tags for classification
# MAGIC - Search capabilities

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Add table metadata
# MAGIC COMMENT ON TABLE training_uc.dev.customers IS 'Customer dimension table containing PII data. Updated daily via ETL pipeline.';
# MAGIC
# MAGIC -- Add column comments
# MAGIC ALTER TABLE training_uc.dev.customers ALTER COLUMN email COMMENT 'Customer email address (PII - restricted access)';
# MAGIC ALTER TABLE training_uc.dev.customers ALTER COLUMN revenue COMMENT 'Annual revenue in USD (Sensitive - Finance team only)';
# MAGIC ALTER TABLE training_uc.dev.customers ALTER COLUMN classification COMMENT 'Data classification level: PUBLIC, PII, SENSITIVE';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- View table metadata
# MAGIC DESCRIBE EXTENDED training_uc.dev.customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Search for tables (full-text search)
# MAGIC -- In Data Explorer UI, you can search for "customer" and it will find all related tables
# MAGIC
# MAGIC -- Programmatically list tables with metadata
# MAGIC SELECT
# MAGIC     table_catalog,
# MAGIC     table_schema,
# MAGIC     table_name,
# MAGIC     table_type,
# MAGIC     comment
# MAGIC FROM system.information_schema.tables
# MAGIC WHERE table_catalog = 'training_uc'
# MAGIC ORDER BY table_schema, table_name;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 7: Data Sharing (Delta Sharing)
# MAGIC
# MAGIC Unity Catalog enables secure data sharing:
# MAGIC - Share tables with external organizations
# MAGIC - No data duplication
# MAGIC - Centralized access control

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create a share (requires account admin)
# MAGIC -- CREATE SHARE IF NOT EXISTS customer_share;
# MAGIC
# MAGIC -- Add table to share
# MAGIC -- ALTER SHARE customer_share ADD TABLE training_uc.prod.customers;
# MAGIC
# MAGIC -- Grant access to recipient
# MAGIC -- GRANT SELECT ON SHARE customer_share TO RECIPIENT external_partner;
# MAGIC
# MAGIC -- Show shares
# MAGIC -- SHOW SHARES;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 8: Governance Best Practices

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 1. Naming conventions
# MAGIC -- catalog: {environment}_catalog  (e.g., prod_catalog, dev_catalog)
# MAGIC -- schema: {domain}_schema  (e.g., sales_schema, marketing_schema)
# MAGIC -- table: {entity}_table  (e.g., customers_table, orders_table)
# MAGIC
# MAGIC -- 2. Default permissions (least privilege)
# MAGIC -- GRANT USE CATALOG ON CATALOG training_uc TO `account users`;
# MAGIC -- GRANT USAGE ON SCHEMA training_uc.prod TO `analysts`;
# MAGIC -- GRANT SELECT ON TABLE training_uc.prod.customers TO `analysts`;
# MAGIC
# MAGIC -- 3. Audit access
# MAGIC SELECT * FROM system.access.audit
# MAGIC WHERE action_name = 'select'
# MAGIC   AND request_params.table_full_name LIKE 'training_uc%'
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 100;

# COMMAND ----------

# Python: Governance automation
def setup_data_governance(catalog_name, schema_name, table_name):
    """
    Automated governance setup for new tables.
    """
    print(f"Setting up governance for {catalog_name}.{schema_name}.{table_name}...")

    # 1. Add table documentation
    spark.sql(f"""
        COMMENT ON TABLE {catalog_name}.{schema_name}.{table_name}
        IS 'Auto-generated at {datetime.now()}. Contact: data-team@company.com'
    """)

    # 2. Grant default read access to analysts
    spark.sql(f"""
        GRANT SELECT ON TABLE {catalog_name}.{schema_name}.{table_name}
        TO `account users`
    """)

    # 3. Add tags for classification
    # (This would use Unity Catalog tagging API when available)

    # 4. Enable audit logging
    spark.sql(f"""
        ALTER TABLE {catalog_name}.{schema_name}.{table_name}
        SET TBLPROPERTIES ('audit.enabled' = 'true')
    """)

    print("✅ Governance setup complete")

# Example usage
# setup_data_governance("training_uc", "dev", "customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 9: Monitoring & Compliance

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Monitor table access patterns
# MAGIC SELECT
# MAGIC     event_date,
# MAGIC     user_identity.email as user,
# MAGIC     request_params.table_full_name as table_name,
# MAGIC     COUNT(*) as access_count
# MAGIC FROM system.access.audit
# MAGIC WHERE event_date >= CURRENT_DATE - INTERVAL 7 DAYS
# MAGIC   AND request_params.table_full_name LIKE 'training_uc%'
# MAGIC GROUP BY event_date, user_identity.email, request_params.table_full_name
# MAGIC ORDER BY event_date DESC, access_count DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Compliance report: PII data access
# MAGIC SELECT
# MAGIC     user_identity.email as user,
# MAGIC     request_params.table_full_name as table_name,
# MAGIC     COUNT(*) as access_count,
# MAGIC     MIN(event_time) as first_access,
# MAGIC     MAX(event_time) as last_access
# MAGIC FROM system.access.audit
# MAGIC WHERE request_params.table_full_name IN (
# MAGIC     SELECT CONCAT(table_catalog, '.', table_schema, '.', table_name)
# MAGIC     FROM system.information_schema.tables
# MAGIC     WHERE comment LIKE '%PII%'
# MAGIC )
# MAGIC AND event_date >= CURRENT_DATE - INTERVAL 30 DAYS
# MAGIC GROUP BY user_identity.email, request_params.table_full_name
# MAGIC ORDER BY access_count DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC ✅ **Three-Level Namespace**
# MAGIC - catalog.schema.table enables environment isolation
# MAGIC - Better multi-tenancy and governance
# MAGIC
# MAGIC ✅ **Access Control**
# MAGIC - Fine-grained permissions (catalog → schema → table → column)
# MAGIC - Row-level security with filter functions
# MAGIC - Column-level security with dynamic views
# MAGIC
# MAGIC ✅ **Data Lineage**
# MAGIC - Automatic tracking of table dependencies
# MAGIC - Column-level lineage
# MAGIC - Visual lineage graphs in UI
# MAGIC
# MAGIC ✅ **Data Discovery**
# MAGIC - Rich metadata (comments, tags)
# MAGIC - Full-text search
# MAGIC - Data classification
# MAGIC
# MAGIC ✅ **Compliance**
# MAGIC - Audit logging (who accessed what, when)
# MAGIC - Data sharing with external partners
# MAGIC - GDPR/CCPA compliance support
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC Continue to Notebook 04: **Streaming Analytics**

# COMMAND ----------

# Cleanup (optional)
# spark.sql("DROP CATALOG IF EXISTS training_uc CASCADE")
# print("✅ Cleanup complete")
