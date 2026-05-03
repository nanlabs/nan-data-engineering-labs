"""
Exercise 03: Unity Catalog Governance - Starter Code

⚠️ IMPORTANT: This exercise requires Databricks Trial, Premium, or Enterprise edition.
Unity Catalog is NOT available in Databricks Community Edition.

Implement comprehensive data governance with:
- Three-level namespace (catalog.schema.table)
- Fine-grained access control
- Row-level security
- Column-level security (PII masking)
- Data lineage tracking
- Audit logging

Estimated Time: 2 hours
"""

from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise 03: Unity Catalog Governance") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("=" * 80)
print("Exercise 03: Unity Catalog Governance")
print("=" * 80)

# ============================================================================
# TASK 1: Three-Level Namespace (20 points)
# ============================================================================
print("\n📋 Task 1: Setting up Three-Level Namespace...")

def task_1_create_namespace():
    """
    Create Unity Catalog structure with 3 catalogs and schemas.

    Structure:
    - dev_catalog (bronze_schema, silver_schema, gold_schema)
    - staging_catalog (bronze_schema, silver_schema, gold_schema)
    - prod_catalog (bronze_schema, silver_schema, gold_schema)
    """

    # TODO: Create catalogs
    # Hint: CREATE CATALOG IF NOT EXISTS catalog_name

    # TODO: Create dev_catalog
    # spark.sql("""
    #     CREATE CATALOG IF NOT EXISTS dev_catalog
    # """)

    # TODO: Create staging_catalog

    # TODO: Create prod_catalog

    print("✅ Catalogs created (dev, staging, prod)")

    # TODO: Create schemas in dev_catalog
    # Hint: USE CATALOG dev_catalog; CREATE SCHEMA IF NOT EXISTS schema_name

    # TODO: Create bronze_schema

    # TODO: Create silver_schema

    # TODO: Create gold_schema

    # TODO: Repeat for staging_catalog and prod_catalog

    print("✅ Schemas created in all catalogs")

    # Verify namespaces
    # spark.sql("SHOW CATALOGS").show()
    # spark.sql("SHOW SCHEMAS IN dev_catalog").show()


def task_1_create_sample_data():
    """
    Create sample patient data with 5,000 records across 5 regions.
    """

    print("\n📊 Creating sample patient data...")

    # TODO: Generate sample patient data
    # Hint: Create DataFrame with columns:
    # - patient_id, name, email, ssn, region, age, diagnosis_code,
    #   treatment_cost, admission_date

    # Sample structure:
    # regions = ['US_EAST', 'US_WEST', 'EU', 'APAC', 'LATAM']
    # diagnosis_codes = ['A01', 'B02', 'C03', 'D04', 'E05']

    # TODO: Create bronze table with raw data
    # patients_df.write.format("delta") \
    #     .mode("overwrite") \
    #     .saveAsTable("dev_catalog.bronze_schema.patients_raw")

    # TODO: Create silver table with cleaned data
    # (Add data quality checks, standardization)

    # TODO: Create gold table with aggregations
    # (Group by region, calculate averages, counts)

    print("✅ Sample data created in dev_catalog")


# ============================================================================
# TASK 2: Access Control (25 points)
# ============================================================================
print("\n🔐 Task 2: Implementing Access Control...")

def task_2_create_groups_and_permissions():
    """
    Create user groups and grant appropriate permissions.

    Groups:
    - data_engineers: Full access to all catalogs
    - data_scientists: Read access to all data
    - analysts: Read access to silver/gold only (no PII)
    - compliance_officers: Audit access only
    """

    # TODO: Grant permissions to data_engineers
    # Hint: GRANT ALL PRIVILEGES ON CATALOG catalog_name TO `group_name`

    # TODO: Grant full access to dev and staging catalogs
    # spark.sql("""
    #     GRANT ALL PRIVILEGES ON CATALOG dev_catalog TO `data_engineers`
    # """)

    # TODO: Grant permissions to data_scientists
    # Hint: GRANT USAGE, SELECT permissions on specific schemas

    # TODO: Grant USAGE on dev_catalog

    # TODO: Grant SELECT on silver_schema and gold_schema

    # TODO: Grant permissions to analysts (column-level)
    # Hint: GRANT SELECT (column1, column2, ...) ON TABLE table_name TO `group`

    # TODO: Grant limited column access (exclude email, ssn)
    # spark.sql("""
    #     GRANT SELECT (patient_id, region, age, diagnosis_code, treatment_cost)
    #     ON TABLE dev_catalog.silver_schema.patients_clean TO `analysts`
    # """)

    # TODO: Grant permissions to compliance_officers
    # Hint: Grant access to system.access.audit table

    print("✅ Access control configured for 4 user groups")

    # Verify permissions
    # spark.sql("SHOW GRANTS ON CATALOG dev_catalog").show()


# ============================================================================
# TASK 3: Row-Level Security (25 points)
# ============================================================================
print("\n🔒 Task 3: Implementing Row-Level Security...")

def task_3_create_row_filter():
    """
    Create filter function to restrict data by region based on user role.

    Logic:
    - data_engineers: See all regions
    - data_scientists: See all regions
    - analysts_us_east: See only US_EAST
    - analysts_us_west: See only US_WEST
    - Others: See nothing
    """

    # TODO: Create filter function
    # Hint: Use is_account_group_member() to check group membership

    # spark.sql("""
    #     CREATE OR REPLACE FUNCTION dev_catalog.silver_schema.region_filter()
    #     RETURNS STRING
    #     RETURN
    #         CASE
    #             WHEN is_account_group_member('data_engineers') THEN NULL
    #             WHEN is_account_group_member('data_scientists') THEN NULL
    #             WHEN is_account_group_member('analysts_us_east') THEN 'US_EAST'
    #             WHEN is_account_group_member('analysts_us_west') THEN 'US_WEST'
    #             WHEN is_account_group_member('analysts_eu') THEN 'EU'
    #             WHEN is_account_group_member('analysts_apac') THEN 'APAC'
    #             WHEN is_account_group_member('analysts_latam') THEN 'LATAM'
    #             ELSE 'NONE'
    #         END
    # """)

    # TODO: Apply row filter to patients_clean table
    # Hint: ALTER TABLE table_name SET ROW FILTER function_name ON (column)

    # spark.sql("""
    #     ALTER TABLE dev_catalog.silver_schema.patients_clean
    #     SET ROW FILTER dev_catalog.silver_schema.region_filter ON (region)
    # """)

    print("✅ Row-level security configured")


# ============================================================================
# TASK 4: Column-Level Security (25 points)
# ============================================================================
print("\n🎭 Task 4: Implementing Column Masking...")

def task_4_create_masking_view():
    """
    Create view with dynamic column masking for PII fields.

    Masking strategies:
    1. Email: Show '***@***.com' for analysts
    2. SSN: Show '***-**-1234' (last 4 digits) for analysts
    3. Revenue: NULL for analysts (nulling strategy)
    """

    # TODO: Create masking view with CASE WHEN logic
    # Hint: Use is_account_group_member() to determine masking level

    # spark.sql("""
    #     CREATE OR REPLACE VIEW dev_catalog.silver_schema.patients_masked AS
    #     SELECT
    #         patient_id,
    #         name,
    #         CASE
    #             WHEN is_account_group_member('data_engineers') THEN email
    #             WHEN is_account_group_member('data_scientists') THEN email
    #             ELSE '***@***.com'
    #         END AS email,
    #         CASE
    #             WHEN is_account_group_member('data_engineers') THEN ssn
    #             WHEN is_account_group_member('data_scientists') THEN ssn
    #             ELSE CONCAT('***-**-', RIGHT(ssn, 4))
    #         END AS ssn,
    #         region,
    #         age,
    #         diagnosis_code,
    #         treatment_cost,
    #         admission_date
    #     FROM dev_catalog.silver_schema.patients_clean
    # """)

    # TODO: Create hashed view for joins without revealing PII
    # Hint: Use SHA256 hash for email/ssn

    print("✅ Column masking views created")


# ============================================================================
# TASK 5: Data Lineage (15 points)
# ============================================================================
print("\n🔗 Task 5: Tracking Data Lineage...")

def task_5_query_lineage():
    """
    Query Unity Catalog system tables to track data lineage.

    Track flow:
    bronze.patients_raw → silver.patients_clean → gold.patient_analytics
    """

    # TODO: Query table lineage
    # Hint: Query system.access.table_lineage table

    # lineage_df = spark.sql("""
    #     SELECT
    #         source_table_full_name,
    #         target_table_full_name,
    #         source_type,
    #         created_by,
    #         created_at
    #     FROM system.access.table_lineage
    #     WHERE target_table_full_name LIKE 'dev_catalog.%'
    #     ORDER BY created_at DESC
    # """)

    # TODO: Query column lineage
    # Hint: Query system.access.column_lineage for specific columns

    # TODO: Generate lineage diagram (ASCII or programmatic)

    print("✅ Data lineage tracked and documented")


# ============================================================================
# TASK 6: Audit Logging (25 points)
# ============================================================================
print("\n📜 Task 6: Querying Audit Logs...")

def task_6_generate_audit_reports():
    """
    Generate compliance reports from audit logs.

    Reports:
    1. PII access in last 30 days
    2. Failed access attempts
    3. Permission changes
    4. Data exports
    """

    # TODO: Report 1 - PII Access
    # Hint: Query system.access.audit for columns_accessed containing 'email' or 'ssn'

    # pii_access = spark.sql("""
    #     SELECT
    #         user_identity.email as user,
    #         event_date,
    #         request_params.table_full_name,
    #         COUNT(*) as access_count
    #     FROM system.access.audit
    #     WHERE event_date >= current_date() - 30
    #       AND request_params.table_full_name LIKE '%patients%'
    #       AND (array_contains(request_params.columns_accessed, 'email')
    #            OR array_contains(request_params.columns_accessed, 'ssn'))
    #     GROUP BY ALL
    #     ORDER BY access_count DESC
    # """)

    # TODO: Report 2 - Failed Access Attempts

    # TODO: Report 3 - Permission Changes

    # TODO: Report 4 - Data Exports

    print("✅ Audit reports generated")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Starting Unity Catalog Governance Implementation...")

    try:
        # Task 1: Create namespace
        # task_1_create_namespace()
        # task_1_create_sample_data()

        # Task 2: Access control
        # task_2_create_groups_and_permissions()

        # Task 3: Row-level security
        # task_3_create_row_filter()

        # Task 4: Column masking
        # task_4_create_masking_view()

        # Task 5: Data lineage
        # task_5_query_lineage()

        # Task 6: Audit logging
        # task_6_generate_audit_reports()

        print("\n" + "=" * 80)
        print("✅ Implementation complete! Run validate.py to check your work.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Unity Catalog requires Trial/Premium/Enterprise edition.")
        print("Community Edition is not supported.")
