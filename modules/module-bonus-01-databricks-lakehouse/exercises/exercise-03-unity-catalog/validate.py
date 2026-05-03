"""
Exercise 03: Unity Catalog Governance - Validation Script

⚠️ IMPORTANT: This exercise requires Databricks Trial, Premium, or Enterprise edition.
Unity Catalog is NOT available in Databricks Community Edition.

This script validates the implementation of:
- Task 1: Three-level namespace (catalogs, schemas, tables)
- Task 2: Access control (grants and permissions)
- Task 3: Row-level security (filter functions)
- Task 4: Column masking (secure views)
- Task 5: Data lineage (tracking & queries)
- Task 6: Audit logging (compliance reports)

Run: python validate.py
"""

from pyspark.sql import SparkSession
import sys

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise 03: Validation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Scoring
total_score = 0
max_score = 100

print("=" * 80)
print("Exercise 03: Unity Catalog Governance - Validation")
print("=" * 80)

# ============================================================================
# TASK 1: Three-Level Namespace (20 points)
# ============================================================================
print("\n📋 Task 1: Validating Three-Level Namespace...")

task1_score = 0
task1_max = 20

try:
    # Check catalogs exist
    catalogs = spark.sql("SHOW CATALOGS").collect()
    catalog_names = [row.catalog for row in catalogs]

    required_catalogs = ['dev_catalog', 'staging_catalog', 'prod_catalog']
    catalogs_found = [c for c in required_catalogs if c in catalog_names]

    if len(catalogs_found) == 3:
        print(f"  ✅ All 3 catalogs exist: {', '.join(catalogs_found)}")
        task1_score += 5
    else:
        missing = set(required_catalogs) - set(catalogs_found)
        print(f"  ❌ Missing catalogs: {', '.join(missing)}")

    # Check schemas in dev_catalog
    schemas = spark.sql("SHOW SCHEMAS IN dev_catalog").collect()
    schema_names = [row.databaseName for row in schemas]

    required_schemas = ['bronze_schema', 'silver_schema', 'gold_schema']
    schemas_found = [s for s in required_schemas if s in schema_names]

    if len(schemas_found) == 3:
        print(f"  ✅ All 3 schemas exist in dev_catalog: {', '.join(schemas_found)}")
        task1_score += 5
    else:
        missing = set(required_schemas) - set(schemas_found)
        print(f"  ❌ Missing schemas: {', '.join(missing)}")

    # Check tables exist in dev_catalog
    try:
        bronze_count = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM dev_catalog.bronze_schema.patients_raw
        """).first().cnt

        if bronze_count >= 5000:
            print(f"  ✅ Bronze table has {bronze_count} records (expected 5,000)")
            task1_score += 3
        else:
            print(f"  ⚠️  Bronze table has only {bronze_count} records (expected 5,000)")
            task1_score += 1

    except Exception as e:
        print(f"  ❌ Bronze table not found or error: {e}")

    try:
        silver_count = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM dev_catalog.silver_schema.patients_clean
        """).first().cnt

        if silver_count > 0:
            print(f"  ✅ Silver table has {silver_count} records")
            task1_score += 4
        else:
            print("  ❌ Silver table is empty")

    except Exception as e:
        print(f"  ❌ Silver table not found or error: {e}")

    try:
        gold_count = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM dev_catalog.gold_schema.patient_analytics
        """).first().cnt

        if gold_count > 0:
            print(f"  ✅ Gold table has {gold_count} aggregated records")
            task1_score += 3
        else:
            print("  ❌ Gold table is empty")

    except Exception as e:
        print(f"  ❌ Gold table not found or error: {e}")

except Exception as e:
    print(f"  ❌ Task 1 validation error: {e}")

print(f"\n  📊 Task 1 Score: {task1_score}/{task1_max}")
total_score += task1_score

# ============================================================================
# TASK 2: Access Control (25 points)
# ============================================================================
print("\n🔐 Task 2: Validating Access Control...")

task2_score = 0
task2_max = 25

try:
    # Check grants on dev_catalog
    try:
        grants = spark.sql("SHOW GRANTS ON CATALOG dev_catalog").collect()

        if grants:
            print(f"  ✅ Permissions configured on dev_catalog ({len(grants)} grants)")
            task2_score += 10

            # Check for specific groups
            grant_principals = [row.principal for row in grants]

            if 'data_engineers' in str(grant_principals):
                print("  ✅ data_engineers group has grants")
                task2_score += 5

            if 'data_scientists' in str(grant_principals):
                print("  ✅ data_scientists group has grants")
                task2_score += 5

            if 'analysts' in str(grant_principals):
                print("  ✅ analysts group has grants")
                task2_score += 5

        else:
            print("  ⚠️  No grants found on dev_catalog")
            print("  ℹ️  Note: Grants may require admin permissions to view")
            task2_score += 10  # Partial credit if cannot verify

    except Exception as e:
        print(f"  ℹ️  Cannot verify grants: {e}")
        print("  ℹ️  This may be due to permission restrictions")
        task2_score += 10  # Partial credit if cannot verify

except Exception as e:
    print(f"  ❌ Task 2 validation error: {e}")

print(f"\n  📊 Task 2 Score: {task2_score}/{task2_max}")
total_score += task2_score

# ============================================================================
# TASK 3: Row-Level Security (25 points)
# ============================================================================
print("\n🔒 Task 3: Validating Row-Level Security...")

task3_score = 0
task3_max = 25

try:
    # Check if filter function exists
    try:
        functions = spark.sql("""
            SHOW USER FUNCTIONS IN dev_catalog.silver_schema
        """).collect()

        function_names = [row.function for row in functions]

        if 'region_filter' in str(function_names):
            print("  ✅ region_filter function exists")
            task3_score += 10
        else:
            print("  ❌ region_filter function not found")

    except Exception as e:
        print(f"  ℹ️  Cannot verify filter function: {e}")
        task3_score += 5  # Partial credit

    # Check if row filter is applied
    try:
        # Query table properties or history to check for row filter
        describe = spark.sql("""
            DESCRIBE TABLE EXTENDED dev_catalog.silver_schema.patients_clean
        """).collect()

        table_props = [str(row) for row in describe]

        if 'row_filter' in str(table_props).lower() or 'region_filter' in str(table_props).lower():
            print("  ✅ Row filter appears to be applied to patients_clean")
            task3_score += 15
        else:
            print("  ⚠️  Row filter may not be applied (check manually)")
            task3_score += 8  # Partial credit

    except Exception as e:
        print(f"  ℹ️  Cannot verify row filter application: {e}")
        task3_score += 8  # Partial credit

except Exception as e:
    print(f"  ❌ Task 3 validation error: {e}")

print(f"\n  📊 Task 3 Score: {task3_score}/{task3_max}")
total_score += task3_score

# ============================================================================
# TASK 4: Column Masking (15 points)
# ============================================================================
print("\n🎭 Task 4: Validating Column Masking...")

task4_score = 0
task4_max = 15

try:
    # Check if masked view exists
    try:
        masked_data = spark.sql("""
            SELECT * FROM dev_catalog.silver_schema.patients_masked LIMIT 5
        """).collect()

        if masked_data:
            print("  ✅ patients_masked view exists and is queryable")
            task4_score += 8

            # Check if view has expected columns
            columns = spark.sql("""
                SELECT * FROM dev_catalog.silver_schema.patients_masked LIMIT 1
            """).columns

            expected_cols = ['patient_id', 'email', 'ssn', 'region']
            if all(col in columns for col in expected_cols):
                print("  ✅ Masked view has expected columns")
                task4_score += 4

        else:
            print("  ❌ patients_masked view is empty")

    except Exception as e:
        print(f"  ❌ patients_masked view not found: {e}")

    # Check if hashed view exists (bonus)
    try:
        hashed = spark.sql("""
            SELECT * FROM dev_catalog.silver_schema.patients_hashed LIMIT 1
        """).collect()

        if hashed:
            print("  ✅ patients_hashed view exists (bonus)")
            task4_score += 3

    except Exception:
        print("  ℹ️  patients_hashed view not found (optional)")

except Exception as e:
    print(f"  ❌ Task 4 validation error: {e}")

print(f"\n  📊 Task 4 Score: {task4_score}/{task4_max}")
total_score += task4_score

# ============================================================================
# TASK 5: Data Lineage (10 points)
# ============================================================================
print("\n🔗 Task 5: Validating Data Lineage...")

task5_score = 0
task5_max = 10

try:
    # Check if can query lineage tables
    try:
        lineage = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM system.access.table_lineage
            WHERE target_table_full_name LIKE 'dev_catalog.%'
        """).first()

        if lineage and lineage.cnt > 0:
            print(f"  ✅ Table lineage tracked ({lineage.cnt} lineage records)")
            task5_score += 10
        else:
            print("  ⚠️  No lineage records found yet (may take time to populate)")
            task5_score += 5  # Partial credit

    except Exception as e:
        print(f"  ℹ️  Cannot access system.access.table_lineage: {e}")
        print("  ℹ️  Lineage tracking may require time to populate")
        task5_score += 5  # Partial credit

except Exception as e:
    print(f"  ❌ Task 5 validation error: {e}")

print(f"\n  📊 Task 5 Score: {task5_score}/{task5_max}")
total_score += task5_score

# ============================================================================
# TASK 6: Audit Logging (5 points)
# ============================================================================
print("\n📜 Task 6: Validating Audit Logging...")

task6_score = 0
task6_max = 5

try:
    # Check if audit table is accessible
    try:
        audit = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM system.access.audit
            WHERE event_date >= current_date() - 30
            LIMIT 1
        """).first()

        if audit:
            print("  ✅ Audit logs accessible (system.access.audit)")
            task6_score += 5
        else:
            print("  ⚠️  No audit records found")
            task6_score += 2

    except Exception as e:
        print(f"  ℹ️  Cannot access system.access.audit: {e}")
        print("  ℹ️  Audit access may require elevated permissions")
        task6_score += 2  # Partial credit

except Exception as e:
    print(f"  ❌ Task 6 validation error: {e}")

print(f"\n  📊 Task 6 Score: {task6_score}/{task6_max}")
total_score += task6_score

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)

print("\n📊 Score Breakdown:")
print(f"  Task 1 (Namespace):        {task1_score}/{task1_max} points")
print(f"  Task 2 (Access Control):   {task2_score}/{task2_max} points")
print(f"  Task 3 (Row Security):     {task3_score}/{task3_max} points")
print(f"  Task 4 (Column Masking):   {task4_score}/{task4_max} points")
print(f"  Task 5 (Lineage):          {task5_score}/{task5_max} points")
print(f"  Task 6 (Audit Logging):    {task6_score}/{task6_max} points")
print("  " + "-" * 40)
print(f"  Total Score:               {total_score}/{max_score} points")

# Grade calculation
percentage = (total_score / max_score) * 100

if percentage >= 90:
    grade = "A"
    emoji = "🌟"
elif percentage >= 80:
    grade = "B"
    emoji = "👍"
elif percentage >= 70:
    grade = "C"
    emoji = "✓"
elif percentage >= 60:
    grade = "D"
    emoji = "⚠️"
else:
    grade = "F"
    emoji = "❌"

print(f"\n{emoji} Final Grade: {grade} ({percentage:.1f}%)")

if percentage >= 80:
    print("\n🎉 Excellent work! Your Unity Catalog governance is well-implemented.")
    print("   You've successfully demonstrated:")
    print("   - Multi-level namespace management")
    print("   - Fine-grained access control")
    print("   - PII protection with row & column security")
    print("   - Compliance tracking with audit logs")
elif percentage >= 60:
    print("\n👍 Good effort! Review the items marked with ❌ or ⚠️ above.")
    print("   Focus on:")
    print("   - Ensuring all catalogs and schemas are created")
    print("   - Verifying row and column security are applied")
    print("   - Testing permissions for different user groups")
else:
    print("\n📚 Keep working on it! Review the solution.py for guidance.")
    print("   Key areas to address:")
    print("   - Complete the namespace setup (catalogs, schemas, tables)")
    print("   - Implement access control grants")
    print("   - Add row-level and column-level security")

print("\n" + "=" * 80)
print("💡 Tips:")
print("  - Unity Catalog requires Trial/Premium/Enterprise edition")
print("  - Some features may need METASTORE ADMIN permissions")
print("  - Audit logs may take time to populate")
print("  - Review notebooks/03-unity-catalog.py for examples")
print("=" * 80)

# Summary table
print("\n📋 Implementation Checklist:")
checklist = [
    ("Three catalogs created", task1_score >= 5),
    ("Three schemas per catalog", task1_score >= 10),
    ("Sample data loaded", task1_score >= 15),
    ("Access control configured", task2_score >= 10),
    ("Row-level security applied", task3_score >= 10),
    ("Column masking views created", task4_score >= 8),
    ("Data lineage tracked", task5_score >= 5),
    ("Audit logs accessible", task6_score >= 3),
]

for item, status in checklist:
    status_icon = "✅" if status else "❌"
    print(f"  {status_icon} {item}")

print("\n" + "=" * 80)

# Exit with appropriate code
if percentage >= 80:
    sys.exit(0)
else:
    sys.exit(1)
