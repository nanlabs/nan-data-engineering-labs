# Exercise 03: Unity Catalog Governance

## Overview
Implement comprehensive data governance using Unity Catalog with three-level namespaces, fine-grained access control, row and column-level security, lineage tracking, and audit logging.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Exercise 02 (ETL Pipelines)

> **⚠️ IMPORTANT**: This exercise requires **Databricks Trial, Premium, or Enterprise** edition. Unity Catalog is **NOT available** in Databricks Community Edition. You can sign up for a 14-day trial at [databricks.com/try-databricks](https://databricks.com/try-databricks).

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create and manage Unity Catalog's three-level namespace (catalog.schema.table)
- Implement fine-grained access control at multiple levels
- Configure row-level security with filter functions
- Implement column-level security and PII masking
- Track data lineage programmatically
- Query audit logs for compliance reporting
- Manage data access across environments (dev/staging/prod)

---

## Scenario
You're implementing governance for a healthcare analytics platform with sensitive patient data. Requirements:
1. Separate dev, staging, and production environments
2. Data scientists can read all data, but analysts see only their region
3. PII fields (SSN, email) must be masked for analysts
4. Compliance team needs to audit all PII access
5. Track lineage from raw data to reports
6. Generate monthly compliance reports

**Data**: Patient records with demographics, medical history, and billing information across 5 regions.

---

## Requirements

### Task 1: Three-Level Namespace (20 min)
Set up Unity Catalog's three-level namespace structure.

**Catalog Structure**:
```
dev_catalog
├── bronze_schema
│   └── patients_raw (table)
├── silver_schema
│   └── patients_clean (table)
└── gold_schema
    └── patient_analytics (table)

staging_catalog
├── bronze_schema
├── silver_schema
└── gold_schema

prod_catalog
├── bronze_schema
├── silver_schema
└── gold_schema
```

**Requirements**:
- Create 3 catalogs: `dev_catalog`, `staging_catalog`, `prod_catalog`
- In each catalog, create 3 schemas: `bronze_schema`, `silver_schema`, `gold_schema`
- Create tables in dev_catalog:
  - `bronze_schema.patients_raw` (5,000 records, raw format)
  - `silver_schema.patients_clean` (cleaned data)
  - `gold_schema.patient_analytics` (aggregations by region)

**Patient Schema**:
```
patient_id: STRING
name: STRING
email: STRING (PII)
ssn: STRING (PII)
region: STRING (US_EAST, US_WEST, EU, APAC, LATAM)
age: INT
diagnosis_code: STRING
treatment_cost: DOUBLE
admission_date: DATE
```

**Success Criteria**:
- ✅ All 3 catalogs exist and are queryable
- ✅ Each catalog has 3 schemas (9 schemas total)
- ✅ Dev catalog has all 3 tables with data
- ✅ Can query fully qualified: `SELECT * FROM dev_catalog.bronze_schema.patients_raw`

---

### Task 2: Access Control (25 min)
Implement fine-grained permissions at catalog, schema, table, and column levels.

**User Roles** (simulate with groups):
1. **data_engineers**: Full access to all catalogs
2. **data_scientists**: Read access to all data
3. **analysts**: Read access only to silver and gold layers
4. **compliance_officers**: Read-only audit access

**Permissions to Grant**:

**Data Engineers**:
```sql
GRANT ALL PRIVILEGES ON CATALOG dev_catalog TO data_engineers;
GRANT ALL PRIVILEGES ON CATALOG staging_catalog TO data_engineers;
GRANT SELECT ON CATALOG prod_catalog TO data_engineers;
```

**Data Scientists**:
```sql
GRANT USAGE ON CATALOG dev_catalog TO data_scientists;
GRANT SELECT ON SCHEMA dev_catalog.silver_schema TO data_scientists;
GRANT SELECT ON SCHEMA dev_catalog.gold_schema TO data_scientists;
```

**Analysts** (limited to specific columns):
```sql
GRANT USAGE ON CATALOG dev_catalog TO analysts;
GRANT SELECT (patient_id, region, age, diagnosis_code)
  ON TABLE dev_catalog.silver_schema.patients_clean TO analysts;
-- Note: email and ssn excluded
```

**Requirements**:
- Create 4 groups with appropriate permissions
- Test access by impersonating each role
- Verify analysts CANNOT access PII columns directly
- Verify analysts CANNOT access bronze layer

**Success Criteria**:
- ✅ All 4 groups created with correct permissions
- ✅ Data scientists can read silver and gold (not bronze)
- ✅ Analysts denied access to email and ssn columns
- ✅ Compliance officers have read-only audit access
- ✅ Permission tests documented

---

### Task 3: Row-Level Security (25 min)
Implement row-level security so analysts only see data from their region.

**Requirements**:
- Create a filter function that restricts by region
- Apply row filter to `patients_clean` table
- Analysts in US_EAST see only US_EAST patients
- Data scientists see all regions (bypass filter)

**Filter Function**:
```sql
CREATE FUNCTION dev_catalog.silver_schema.region_filter()
  RETURNS STRING
  RETURN
    CASE
      WHEN is_member('data_engineers') THEN NULL  -- See all
      WHEN is_member('data_scientists') THEN NULL  -- See all
      WHEN is_member('analysts_us_east') THEN 'US_EAST'
      WHEN is_member('analysts_us_west') THEN 'US_WEST'
      -- ... other regions
      ELSE 'NONE'  -- See nothing
    END;
```

**Apply Row Filter**:
```sql
ALTER TABLE dev_catalog.silver_schema.patients_clean
SET ROW FILTER dev_catalog.silver_schema.region_filter ON (region);
```

**Testing**:
1. As `data_scientist`: Query should return all 5,000 patients
2. As `analyst_us_east`: Query should return ~1,000 patients (US_EAST only)
3. As `analyst_eu`: Query should return ~1,000 patients (EU only)
4. Verify filter is transparent (users don't see filter logic)

**Success Criteria**:
- ✅ Filter function created and tested
- ✅ Row filter applied to table
- ✅ Analysts see only their region
- ✅ Data scientists see all regions
- ✅ Filter cannot be bypassed

---

### Task 4: Column-Level Security (25 min)
Implement dynamic column masking for PII fields.

**Requirements**:
- Create masking view for analysts
- Mask `email` → `***@***.com`
- Mask `ssn` → `***-**-1234` (last 4 digits visible)
- Original values visible to data engineers and data scientists

**Masking Views**:
```sql
CREATE VIEW dev_catalog.silver_schema.patients_masked AS
SELECT
  patient_id,
  name,
  CASE
    WHEN is_member('data_engineers') THEN email
    WHEN is_member('data_scientists') THEN email
    ELSE '***@***.com'
  END AS email,
  CASE
    WHEN is_member('data_engineers') THEN ssn
    WHEN is_member('data_scientists') THEN ssn
    ELSE CONCAT('***-**-', RIGHT(ssn, 4))
  END AS ssn,
  region,
  age,
  diagnosis_code,
  treatment_cost,
  admission_date
FROM dev_catalog.silver_schema.patients_clean;
```

**Advanced Masking**:
- Implement NULL-ing strategy (return NULL instead of masked value)
- Implement hashing strategy (return SHA256 hash for joins without revealing PII)

**Column-Level Grants**:
```sql
-- Grant select on specific non-PII columns
GRANT SELECT (patient_id, region, age, treatment_cost, admission_date)
  ON dev_catalog.silver_schema.patients_clean TO analysts;

-- Deny access to PII columns explicitly
DENY SELECT (email, ssn)
  ON dev_catalog.silver_schema.patients_clean TO analysts;
```

**Success Criteria**:
- ✅ Masking view created with dynamic logic
- ✅ Analysts see masked PII
- ✅ Data scientists see unmasked PII
- ✅ Column grants enforced at table level
- ✅ Three masking strategies implemented (mask, null, hash)

---

### Task 5: Data Lineage (15 min)
Track data lineage from raw sources to final reports.

**Lineage Flow**:
```
External Source → bronze.patients_raw → silver.patients_clean → gold.patient_analytics
```

**Requirements**:
- Use Unity Catalog system tables to query lineage
- Programmatically fetch lineage via API
- Create lineage visualization query

**Lineage Queries**:
```sql
-- View table lineage
SELECT * FROM system.access.table_lineage
WHERE target_table_full_name = 'dev_catalog.gold_schema.patient_analytics';

-- View column lineage
SELECT * FROM system.access.column_lineage
WHERE target_table_full_name = 'dev_catalog.gold_schema.patient_analytics'
  AND target_column_name = 'avg_treatment_cost';
```

**Programmatic Lineage**:
```python
# Get upstream dependencies
lineage = spark.sql("""
    SELECT
      source_table_full_name,
      target_table_full_name,
      source_type,
      created_by
    FROM system.access.table_lineage
    WHERE target_table_full_name LIKE 'dev_catalog.%'
    ORDER BY created_at
""")

lineage.show(truncate=False)
```

**Lineage Diagram**:
- Generate ASCII diagram showing:
  - Source systems
  - Bronze/Silver/Gold tables
  - Transformation types
  - Data consumers (dashboards, ML models)

**Success Criteria**:
- ✅ Table lineage query returns 2+ upstream sources
- ✅ Column lineage traces specific metrics
- ✅ Programmatic API call successful
- ✅ Lineage diagram generated
- ✅ Can identify all downstream consumers

---

### Task 6: Audit Logging (20 min)
Query Unity Catalog audit logs for compliance reporting.

**Requirements**:
- Query `system.access.audit` table
- Generate compliance reports:
  1. All PII access in last 30 days
  2. Failed access attempts
  3. Permission changes
  4. Data exports (CREATE TABLE AS SELECT)

**Audit Queries**:

**1. PII Access Report**:
```sql
SELECT
  user_identity.email as user,
  event_date,
  request_params.table_full_name as table_name,
  request_params.columns_accessed,
  COUNT(*) as access_count
FROM system.access.audit
WHERE
  event_date >= current_date() - 30
  AND request_params.table_full_name = 'dev_catalog.silver_schema.patients_clean'
  AND array_contains(request_params.columns_accessed, 'email')
GROUP BY ALL
ORDER BY access_count DESC;
```

**2. Failed Access Attempts**:
```sql
SELECT
  user_identity.email,
  event_date,
  action_name,
  request_params.table_full_name,
  response.status_code,
  response.error_message
FROM system.access.audit
WHERE
  event_date >= current_date() - 7
  AND response.status_code != '200'
  AND action_name IN ('getTable', 'readTable', 'createTable')
ORDER BY event_date DESC;
```

**3. Permission Changes**:
```sql
SELECT
  user_identity.email as changed_by,
  event_date,
  action_name,
  request_params.securable_full_name,
  request_params.principal,
  request_params.privileges
FROM system.access.audit
WHERE
  event_date >= current_date() - 30
  AND action_name IN ('grantPrivileges', 'revokePrivileges')
ORDER BY event_date DESC;
```

**4. Data Export Tracking**:
```sql
SELECT
  user_identity.email,
  event_date,
  request_params.table_full_name as exported_table,
  request_params.target_location,
  request_params.row_count
FROM system.access.audit
WHERE
  event_date >= current_date() - 30
  AND action_name IN ('createExternalTable', 'exportData')
ORDER BY event_date DESC;
```

**Compliance Dashboard**:
- Create automated report (scheduled notebook)
- Email summary to compliance team
- Alert on suspicious patterns:
  - >100 PII accesses by single user
  - Access attempts outside business hours
  - Repeated failed access attempts

**Success Criteria**:
- ✅ All 4 audit queries working
- ✅ PII access report generated (30-day history)
- ✅ Failed access attempts identified
- ✅ Permission changes tracked
- ✅ Data export audit trail available
- ✅ Alert logic implemented

---

## Hints

<details>
<summary>Hint 1: Creating Catalogs and Schemas</summary>

```sql
-- Create catalogs
CREATE CATALOG IF NOT EXISTS dev_catalog;
CREATE CATALOG IF NOT EXISTS staging_catalog;
CREATE CATALOG IF NOT EXISTS prod_catalog;

-- Create schemas in dev_catalog
USE CATALOG dev_catalog;
CREATE SCHEMA IF NOT EXISTS bronze_schema;
CREATE SCHEMA IF NOT EXISTS silver_schema;
CREATE SCHEMA IF NOT EXISTS gold_schema;

-- Create table with data
CREATE TABLE dev_catalog.bronze_schema.patients_raw
USING delta
AS SELECT * FROM patients_source_data;

-- Verify
SHOW CATALOGS;
SHOW SCHEMAS IN dev_catalog;
SHOW TABLES IN dev_catalog.bronze_schema;
```
</details>

<details>
<summary>Hint 2: Managing Groups and Permissions</summary>

```sql
-- Create groups (if not exists)
-- Note: Groups may need to be created in Databricks admin console

-- Grant catalog permissions
GRANT USE CATALOG ON CATALOG dev_catalog TO `data_scientists`;
GRANT USE SCHEMA ON SCHEMA dev_catalog.silver_schema TO `data_scientists`;
GRANT SELECT ON SCHEMA dev_catalog.silver_schema TO `data_scientists`;

-- Column-level grants
GRANT SELECT (patient_id, region, age)
  ON TABLE dev_catalog.silver_schema.patients_clean
  TO `analysts`;

-- View current permissions
SHOW GRANTS ON CATALOG dev_catalog;
SHOW GRANTS ON TABLE dev_catalog.silver_schema.patients_clean;
```
</details>

<details>
<summary>Hint 3: Row-Level Security Implementation</summary>

```python
# Create filter function
spark.sql("""
CREATE OR REPLACE FUNCTION dev_catalog.silver_schema.region_filter()
  RETURNS STRING
  RETURN
    CASE
      WHEN is_account_group_member('data_engineers') THEN NULL
      WHEN is_account_group_member('data_scientists') THEN NULL
      WHEN is_account_group_member('analysts_us_east') THEN 'US_EAST'
      ELSE 'NONE'
    END
""")

# Apply filter to table
spark.sql("""
ALTER TABLE dev_catalog.silver_schema.patients_clean
SET ROW FILTER dev_catalog.silver_schema.region_filter ON (region)
""")

# Test as different users
# Set session user (simulation in notebook)
spark.conf.set("spark.databricks.session.user", "analyst@company.com")
result = spark.sql("SELECT COUNT(*) FROM dev_catalog.silver_schema.patients_clean")
print(f"Rows visible: {result.first()[0]}")
```
</details>

<details>
<summary>Hint 4: Audit Log Analysis</summary>

```python
from pyspark.sql.functions import col, array_contains, explode

# PII access analysis
pii_access = spark.sql("""
    SELECT
      user_identity.email as user,
      event_date,
      request_params.table_full_name,
      size(filter(request_params.columns_accessed,
                  x -> x IN ('email', 'ssn'))) as pii_column_count,
      COUNT(*) as access_count
    FROM system.access.audit
    WHERE event_date >= current_date() - 30
      AND request_params.table_full_name LIKE '%patients%'
    GROUP BY ALL
    HAVING pii_column_count > 0
    ORDER BY access_count DESC
""")

pii_access.display()

# Export to CSV for compliance report
pii_access.coalesce(1).write.csv("/tmp/pii_access_report.csv", header=True)
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-03-unity-catalog
python validate.py
```

**Expected Output**:
```
✅ Task 1: Namespace created (3 catalogs, 9 schemas, 3 tables with data)
   - dev_catalog: 5,000 patients across 5 regions
   - staging_catalog: Empty (schemas only)
   - prod_catalog: Empty (schemas only)
✅ Task 2: Access control configured (4 groups, 12 grants)
   - data_engineers: Full access to dev/staging
   - data_scientists: Read access to silver/gold
   - analysts: Limited column access
   - compliance_officers: Audit access only
✅ Task 3: Row-level security (filter applied, tested with 3 user roles)
   - Data scientists see 5,000 rows
   - Analysts see ~1,000 rows (region filtered)
✅ Task 4: Column masking (3 strategies: mask, null, hash)
   - Email masked for analysts: ***@***.com
   - SSN partially visible: ***-**-1234
✅ Task 5: Lineage tracked (3 layers, 2 transformations)
   - bronze → silver → gold flow documented
✅ Task 6: Audit logging (4 queries, 237 events in last 30 days)
   - PII access: 42 events (3 users)
   - Failed attempts: 7 events
   - Permission changes: 12 events

🎉 Exercise 03 Complete! Total Score: 100/100
📢 Note: Audit data may vary based on your usage patterns
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All SQL commands for setup and queries
2. Governance documentation (catalogs, schemas, permissions matrix)
3. Audit compliance report (30-day PII access summary)
4. Lineage diagram (manually created or programmatically generated)

---

## Resources
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Row and Column Security](https://docs.databricks.com/security/privacy/row-column-access-control.html)
- [Audit Logging](https://docs.databricks.com/administration-guide/account-settings/audit-logs.html)
- Notebook: `notebooks/03-unity-catalog.py`
- Diagram: `assets/diagrams/unity-catalog-architecture.mmd`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 04: Real-Time Streaming
- ✅ Exercise 05: SQL Analytics & Dashboards
- Review Module 16: Data Security & Compliance
- Consider Databricks certification: Data Engineer Associate
