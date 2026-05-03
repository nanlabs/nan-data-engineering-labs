-- ============================================================================
-- Module Bonus 02: Snowflake Data Cloud
-- Notebook 04: Streams and Tasks for CDC
-- ============================================================================
-- Description: Master Snowflake Streams for Change Data Capture (CDC) and
--              Tasks for automated data pipeline orchestration. Build
--              incremental processing workflows with Bronze-Silver-Gold pattern.
--
-- Prerequisites:
--   - Snowflake account with CREATE TASK privilege
--   - Understanding of SQL DML operations
--   - Completed Time Travel notebook
--
-- Estimated Time: 90 minutes
-- ============================================================================

-- ============================================================================
-- SETUP: Create Environment for Streams and Tasks
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Create dedicated warehouse
CREATE OR REPLACE WAREHOUSE streams_tasks_wh
WITH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE streams_tasks_wh;

-- Create database for CDC experiments
CREATE OR REPLACE DATABASE cdc_lab;
USE DATABASE cdc_lab;

CREATE SCHEMA IF NOT EXISTS hr;
USE SCHEMA hr;

-- Create source table: employees
CREATE OR REPLACE TABLE employees (
    emp_id NUMBER(10,0) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    department VARCHAR(50),
    job_title VARCHAR(100),
    salary DECIMAL(12,2),
    hire_date DATE,
    manager_id NUMBER(10,0),
    status VARCHAR(20) DEFAULT 'Active',
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Load initial employee data
INSERT INTO employees
SELECT
    SEQ4() AS emp_id,
    ARRAY_GET(PARSE_JSON('["John","Jane","Michael","Sarah","David","Emily","James","Lisa","Robert","Maria"]'),
              UNIFORM(0, 9, RANDOM())) AS first_name,
    ARRAY_GET(PARSE_JSON('["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]'),
              UNIFORM(0, 9, RANDOM())) AS last_name,
    CONCAT('employee', SEQ4(), '@company.com') AS email,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Engineering'
        WHEN 2 THEN 'Sales'
        WHEN 3 THEN 'Marketing'
        WHEN 4 THEN 'Finance'
        ELSE 'Operations'
    END AS department,
    CASE UNIFORM(1, 5, RANDOM())
        WHEN 1 THEN 'Senior Manager'
        WHEN 2 THEN 'Manager'
        WHEN 3 THEN 'Senior Developer'
        WHEN 4 THEN 'Developer'
        ELSE 'Analyst'
    END AS job_title,
    UNIFORM(50000, 150000, RANDOM()) AS salary,
    DATEADD(DAY, -UNIFORM(0, 1825, RANDOM()), CURRENT_DATE()) AS hire_date,
    CASE WHEN SEQ4() > 10 THEN UNIFORM(0, 9, RANDOM()) ELSE NULL END AS manager_id,
    'Active' AS status,
    DATEADD(MINUTE, -UNIFORM(0, 525600, RANDOM()), CURRENT_TIMESTAMP()) AS updated_at
FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- Verify data loaded
SELECT COUNT(*) AS total_employees FROM employees;
-- Expected: 100

SELECT * FROM employees LIMIT 10;

-- Create target table for processed data
CREATE OR REPLACE TABLE processed_employees (
    emp_id NUMBER(10,0),
    full_name VARCHAR(101),
    email VARCHAR(100),
    department VARCHAR(50),
    job_title VARCHAR(100),
    salary_band VARCHAR(20),
    years_of_service NUMBER,
    status VARCHAR(20),
    processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    change_type VARCHAR(20),
    PRIMARY KEY (emp_id, processed_at)
);

-- Create audit table for tracking all changes
CREATE OR REPLACE TABLE employee_audit_log (
    audit_id NUMBER IDENTITY(1,1),
    emp_id NUMBER(10,0),
    change_type VARCHAR(20),
    old_values VARIANT,
    new_values VARIANT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);


-- ============================================================================
-- SECTION 1: Create Stream on Table
-- ============================================================================
-- Streams capture DML changes (INSERT, UPDATE, DELETE) on source tables.
-- They provide CDC (Change Data Capture) functionality with special metadata columns.
-- ============================================================================

-- Create stream on employees table
CREATE OR REPLACE STREAM employees_stream
ON TABLE employees
COMMENT = 'Captures all changes to employees table';

-- View stream metadata
SHOW STREAMS;
-- Shows: name, database_name, schema_name, table_name, owner, mode, stale, etc.

DESC STREAM employees_stream;
-- Shows columns including METADATA$ columns


-- Query empty stream (no changes yet)
SELECT * FROM employees_stream;
-- Returns empty set (no changes captured yet)

-- Check stream status
SELECT SYSTEM$STREAM_HAS_DATA('employees_stream') AS has_data;
-- Returns FALSE (no data yet)


-- Understand stream metadata columns:
-- METADATA$ACTION: Type of change (INSERT, DELETE)
-- METADATA$ISUPDATE: TRUE if row modified (appears as DELETE + INSERT)
-- METADATA$ROW_ID: Unique identifier for the row
--
-- For UPDATE operations:
--   - Old version: METADATA$ACTION = 'DELETE', METADATA$ISUPDATE = TRUE
--   - New version: METADATA$ACTION = 'INSERT', METADATA$ISUPDATE = TRUE


-- ============================================================================
-- SECTION 2: Generate Changes and Query Stream
-- ============================================================================
-- Make changes to source table and observe how stream captures them.
-- ============================================================================

-- Store employee count before changes
SELECT COUNT(*) AS before_changes FROM employees;
-- Returns: 100

-- CHANGE 1: Insert new employees
INSERT INTO employees (emp_id, first_name, last_name, email, department, job_title, salary, hire_date, status)
VALUES
    (100, 'Alice', 'Cooper', 'alice.cooper@company.com', 'Engineering', 'Senior Developer', 95000, '2026-03-01', 'Active'),
    (101, 'Bob', 'Dylan', 'bob.dylan@company.com', 'Sales', 'Sales Manager', 85000, '2026-03-01', 'Active'),
    (102, 'Carol', 'King', 'carol.king@company.com', 'Marketing', 'Marketing Lead', 90000, '2026-03-01', 'Active'),
    (103, 'David', 'Bowie', 'david.bowie@company.com', 'Finance', 'Financial Analyst', 75000, '2026-03-01', 'Active'),
    (104, 'Emma', 'Stone', 'emma.stone@company.com', 'Operations', 'Operations Manager', 88000, '2026-03-01', 'Active');

-- Verify inserts
SELECT COUNT(*) AS after_inserts FROM employees;
-- Returns: 105


-- Query stream to see captured inserts
SELECT
    emp_id,
    first_name,
    last_name,
    department,
    salary,
    METADATA$ACTION AS change_action,
    METADATA$ISUPDATE AS is_update,
    METADATA$ROW_ID AS row_id
FROM employees_stream
ORDER BY emp_id;
-- Shows 5 new records with METADATA$ACTION = 'INSERT'


-- Check stream has data
SELECT SYSTEM$STREAM_HAS_DATA('employees_stream') AS has_data;
-- Returns TRUE


-- CHANGE 2: Update existing employees
UPDATE employees
SET salary = salary * 1.10,
    updated_at = CURRENT_TIMESTAMP()
WHERE emp_id IN (100, 101);

-- Query stream after updates
SELECT
    emp_id,
    first_name,
    last_name,
    salary,
    METADATA$ACTION AS change_action,
    METADATA$ISUPDATE AS is_update
FROM employees_stream
WHERE emp_id IN (100, 101)
ORDER BY emp_id, METADATA$ACTION;
-- Each UPDATE shows as 2 rows:
-- - DELETE (old values with is_update=TRUE)
-- - INSERT (new values with is_update=TRUE)


-- CHANGE 3: Delete employees
DELETE FROM employees
WHERE emp_id = 102;

-- Query stream after delete
SELECT
    emp_id,
    first_name,
    last_name,
    METADATA$ACTION AS change_action,
    METADATA$ISUPDATE AS is_update
FROM employees_stream
WHERE emp_id = 102;
-- Shows DELETE with is_update=FALSE (true deletion)


-- View all changes in stream
SELECT
    emp_id,
    first_name,
    last_name,
    department,
    salary,
    METADATA$ACTION,
    METADATA$ISUPDATE,
    CASE
        WHEN METADATA$ACTION = 'INSERT' AND METADATA$ISUPDATE = FALSE THEN 'New Record'
        WHEN METADATA$ACTION = 'INSERT' AND METADATA$ISUPDATE = TRUE THEN 'Updated (New Value)'
        WHEN METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE = TRUE THEN 'Updated (Old Value)'
        WHEN METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE = FALSE THEN 'Deleted Record'
    END AS change_type
FROM employees_stream
ORDER BY emp_id, METADATA$ACTION;


-- Count changes by type
SELECT
    CASE
        WHEN METADATA$ACTION = 'INSERT' AND METADATA$ISUPDATE = FALSE THEN 'INSERT'
        WHEN METADATA$ACTION = 'DELETE' AND METADATA$ISUPDATE = FALSE THEN 'DELETE'
        WHEN METADATA$ISUPDATE = TRUE THEN 'UPDATE'
    END AS operation,
    COUNT(*) AS change_count
FROM employees_stream
GROUP BY operation;


-- ============================================================================
-- SECTION 3: Consume Stream Data
-- ============================================================================
-- Consuming stream data automatically advances the stream offset.
-- After consumption, the stream appears empty until new changes occur.
-- ============================================================================

-- Store current stream data count
SELECT COUNT(*) AS changes_before_consumption FROM employees_stream;
-- Returns: ~11 rows (5 inserts + 4 update rows + 2 delete rows)

-- Consume stream: Process only INSERT operations
INSERT INTO processed_employees (
    emp_id,
    full_name,
    email,
    department,
    job_title,
    salary_band,
    years_of_service,
    status,
    change_type
)
SELECT
    emp_id,
    first_name || ' ' || last_name AS full_name,
    email,
    department,
    job_title,
    CASE
        WHEN salary < 60000 THEN 'Entry Level'
        WHEN salary < 80000 THEN 'Mid Level'
        WHEN salary < 100000 THEN 'Senior Level'
        ELSE 'Executive'
    END AS salary_band,
    DATEDIFF(YEAR, hire_date, CURRENT_DATE()) AS years_of_service,
    status,
    'INSERT' AS change_type
FROM employees_stream
WHERE METADATA$ACTION = 'INSERT'
  AND METADATA$ISUPDATE = FALSE;  -- Only true inserts, not updates

-- Verify data processed
SELECT COUNT(*) FROM processed_employees;
-- Returns: 5 (new inserts processed)

SELECT * FROM processed_employees ORDER BY processed_at DESC LIMIT 10;


-- Check stream after partial consumption
-- IMPORTANT: Stream is NOT automatically consumed - it tracks table offset
-- Stream only advances when data is consumed in a DML transaction
SELECT COUNT(*) AS changes_after_partial_consumption FROM employees_stream;
-- Still shows changes because we only consumed INSERTs


-- Consume all remaining stream data
BEGIN TRANSACTION;

-- Log all changes to audit table
INSERT INTO employee_audit_log (emp_id, change_type, old_values, new_values, changed_by)
SELECT
    emp_id,
    METADATA$ACTION,
    OBJECT_CONSTRUCT('salary', salary, 'department', department, 'status', status) AS old_values,
    OBJECT_CONSTRUCT('salary', salary, 'department', department, 'status', status) AS new_values,
    CURRENT_USER() AS changed_by
FROM employees_stream;

COMMIT;

-- Now check stream - should be empty (offset advanced)
SELECT COUNT(*) AS changes_after_full_consumption FROM employees_stream;
-- Returns: 0

-- Stream offset advanced - no pending changes
SELECT SYSTEM$STREAM_HAS_DATA('employees_stream') AS has_data;
-- Returns: FALSE


-- Make new changes to generate more stream data
UPDATE employees
SET department = 'Engineering',
    updated_at = CURRENT_TIMESTAMP()
WHERE emp_id BETWEEN 10 AND 15;

-- Stream captures new changes
SELECT
    emp_id,
    department,
    METADATA$ACTION,
    METADATA$ISUPDATE
FROM employees_stream
ORDER BY emp_id;
-- Shows UPDATE operations (old and new values)


-- ============================================================================
-- SECTION 4: Stream Offset and Management
-- ============================================================================
-- Understanding how streams track position and when they advance.
-- ============================================================================

-- View stream details
SHOW STREAMS LIKE 'employees_stream';
-- Key fields: stale, mode, stale_after

-- Stream becomes "stale" if source table has significant changes that exceed retention
-- Stale streams must be recreated


-- Check stream staleness
SELECT
    name,
    table_name,
    type,
    stale,
    mode,
    stale_after
FROM INFORMATION_SCHEMA.STREAMS
WHERE stream_schema = 'HR';


-- Create multiple streams on same table for different purposes
CREATE OR REPLACE STREAM employees_stream_audit
ON TABLE employees
COMMENT = 'Stream for audit logging';

CREATE OR REPLACE STREAM employees_stream_analytics
ON TABLE employees
COMMENT = 'Stream for analytics processing';

-- All streams capture the same changes independently
INSERT INTO employees (emp_id, first_name, last_name, email, department, job_title, salary, hire_date)
VALUES (105, 'Frank', 'Sinatra', 'frank.sinatra@company.com', 'Sales', 'VP Sales', 120000, '2026-03-01');

-- Both streams see the change
SELECT COUNT(*) FROM employees_stream_audit;
-- Returns: data

SELECT COUNT(*) FROM employees_stream_analytics;
-- Returns: data


-- Consuming one stream doesn't affect others
INSERT INTO employee_audit_log (emp_id, change_type, changed_by)
SELECT
    emp_id,
    METADATA$ACTION,
    CURRENT_USER()
FROM employees_stream_audit;

-- Audit stream consumed, analytics stream still has data
SELECT SYSTEM$STREAM_HAS_DATA('employees_stream_audit');
-- Returns: FALSE

SELECT SYSTEM$STREAM_HAS_DATA('employees_stream_analytics');
-- Returns: TRUE


-- Drop and recreate stream to reset offset
DROP STREAM employees_stream_analytics;

CREATE STREAM employees_stream_analytics
ON TABLE employees;
-- New stream starts from current table state, no historical changes


-- Stream modes:
-- APPEND_ONLY: Only captures INSERT operations (better performance)
CREATE OR REPLACE STREAM employees_stream_append
ON TABLE employees
APPEND_ONLY = TRUE;

-- Standard mode (default): Captures all DML (INSERT, UPDATE, DELETE)
CREATE OR REPLACE STREAM employees_stream_standard
ON TABLE employees
APPEND_ONLY = FALSE;


-- ============================================================================
-- SECTION 5: Create Automated Tasks
-- ============================================================================
-- Tasks enable scheduled execution of SQL statements. Combine with streams
-- for automated incremental processing pipelines.
-- ============================================================================

-- Simple scheduled task (runs every 5 minutes)
CREATE OR REPLACE TASK process_employee_changes
    WAREHOUSE = streams_tasks_wh
    SCHEDULE = '5 MINUTE'
AS
    INSERT INTO processed_employees (
        emp_id,
        full_name,
        email,
        department,
        job_title,
        salary_band,
        years_of_service,
        status,
        change_type
    )
    SELECT
        emp_id,
        first_name || ' ' || last_name AS full_name,
        email,
        department,
        job_title,
        CASE
            WHEN salary < 60000 THEN 'Entry Level'
            WHEN salary < 80000 THEN 'Mid Level'
            WHEN salary < 100000 THEN 'Senior Level'
            ELSE 'Executive'
        END AS salary_band,
        DATEDIFF(YEAR, hire_date, CURRENT_DATE()) AS years_of_service,
        status,
        METADATA$ACTION AS change_type
    FROM employees_stream
    WHERE METADATA$ACTION = 'INSERT';

-- View task definition
SHOW TASKS LIKE 'process_employee_changes';

DESC TASK process_employee_changes;


-- Task with conditional execution (only runs when stream has data)
CREATE OR REPLACE TASK process_employee_changes_smart
    WAREHOUSE = streams_tasks_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('employees_stream')  -- Conditional execution
AS
    INSERT INTO processed_employees (
        emp_id,
        full_name,
        email,
        department,
        job_title,
        salary_band,
        years_of_service,
        status,
        change_type
    )
    SELECT
        emp_id,
        first_name || ' ' || last_name AS full_name,
        email,
        department,
        job_title,
        CASE
            WHEN salary < 60000 THEN 'Entry Level'
            WHEN salary < 80000 THEN 'Mid Level'
            WHEN salary < 100000 THEN 'Senior Level'
            ELSE 'Executive'
        END AS salary_band,
        DATEDIFF(YEAR, hire_date, CURRENT_DATE()) AS years_of_service,
        status,
        METADATA$ACTION AS change_type
    FROM employees_stream
    WHERE METADATA$ACTION = 'INSERT'
      AND METADATA$ISUPDATE = FALSE;


-- Task with CRON schedule (every day at 2 AM UTC)
CREATE OR REPLACE TASK daily_employee_aggregation
    WAREHOUSE = streams_tasks_wh
    SCHEDULE = 'USING CRON 0 2 * * * UTC'
AS
    CREATE OR REPLACE TABLE employee_daily_summary AS
    SELECT
        CURRENT_DATE() AS summary_date,
        department,
        COUNT(*) AS employee_count,
        AVG(salary) AS avg_salary,
        MIN(salary) AS min_salary,
        MAX(salary) AS max_salary
    FROM employees
    WHERE status = 'Active'
    GROUP BY department;


-- Task without schedule (triggered by another task)
CREATE OR REPLACE TASK send_notifications
    WAREHOUSE = streams_tasks_wh
    -- No SCHEDULE clause - will be triggered by parent task
AS
    INSERT INTO employee_audit_log (emp_id, change_type, changed_by)
    SELECT 0, 'NOTIFICATION', 'SYSTEM';


-- View all tasks
SHOW TASKS IN SCHEMA hr;


-- Tasks are created in SUSPENDED state by default
-- Must explicitly RESUME tasks to activate them
-- Note: Tasks cannot be run manually in this notebook - they run on schedule in production
-- ALTER TASK process_employee_changes_smart RESUME;


-- Check task status
SELECT
    name,
    database_name,
    schema_name,
    schedule,
    state,
    condition_text,
    warehouse
FROM INFORMATION_SCHEMA.TASKS
WHERE task_schema = 'HR'
ORDER BY name;


-- Suspend a running task
-- ALTER TASK process_employee_changes_smart SUSPEND;


-- ============================================================================
-- SECTION 6: Task Dependencies and DAG Pipelines
-- ============================================================================
-- Create task graphs (DAGs) where tasks execute in sequence based on
-- dependencies. Build multi-stage data pipelines.
-- ============================================================================

-- Create a 3-stage pipeline: Bronze -> Silver -> Gold

-- Stage 1: Bronze (raw data ingestion) - Root task with schedule
CREATE OR REPLACE TASK bronze_employee_load
    WAREHOUSE = streams_tasks_wh
    SCHEDULE = '10 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('employees_stream')
AS
    -- Load raw changes into bronze table
    CREATE OR REPLACE TABLE bronze_employees AS
    SELECT
        *,
        METADATA$ACTION AS cdc_action,
        METADATA$ISUPDATE AS cdc_is_update,
        CURRENT_TIMESTAMP() AS ingestion_timestamp
    FROM employees_stream;


-- Stage 2: Silver (cleaned/enriched data) - Child of bronze_employee_load
CREATE OR REPLACE TASK silver_employee_transform
    WAREHOUSE = streams_tasks_wh
    AFTER bronze_employee_load  -- Dependency: runs after parent completes
AS
    -- Transform and clean data
    CREATE OR REPLACE TABLE silver_employees AS
    SELECT
        emp_id,
        UPPER(first_name) AS first_name,
        UPPER(last_name) AS last_name,
        LOWER(email) AS email,
        department,
        job_title,
        salary,
        hire_date,
        status,
        DATEDIFF(YEAR, hire_date, CURRENT_DATE()) AS years_of_service,
        CASE
            WHEN salary < 60000 THEN 'Entry Level'
            WHEN salary < 80000 THEN 'Mid Level'
            WHEN salary < 100000 THEN 'Senior Level'
            ELSE 'Executive'
        END AS salary_band,
        CURRENT_TIMESTAMP() AS transform_timestamp
    FROM bronze_employees
    WHERE cdc_action = 'INSERT'
      AND status = 'Active';


-- Stage 3: Gold (aggregated analytics) - Child of silver_employee_transform
CREATE OR REPLACE TASK gold_department_metrics
    WAREHOUSE = streams_tasks_wh
    AFTER silver_employee_transform  -- Dependency: runs after silver
AS
    -- Create aggregated business metrics
    CREATE OR REPLACE TABLE gold_department_metrics AS
    SELECT
        department,
        COUNT(*) AS employee_count,
        AVG(salary) AS avg_salary,
        MIN(salary) AS min_salary,
        MAX(salary) AS max_salary,
        AVG(years_of_service) AS avg_tenure,
        SUM(CASE WHEN salary_band = 'Executive' THEN 1 ELSE 0 END) AS executive_count,
        SUM(CASE WHEN salary_band = 'Senior Level' THEN 1 ELSE 0 END) AS senior_count,
        SUM(CASE WHEN salary_band = 'Mid Level' THEN 1 ELSE 0 END) AS mid_count,
        SUM(CASE WHEN salary_band = 'Entry Level' THEN 1 ELSE 0 END) AS entry_count,
        CURRENT_TIMESTAMP() AS metrics_timestamp
    FROM silver_employees
    GROUP BY department;


-- View task dependencies
SELECT
    name,
    database_name,
    schema_name,
    state,
    schedule,
    predecessors
FROM INFORMATION_SCHEMA.TASKS
WHERE task_schema = 'HR'
  AND name LIKE '%employee%'
ORDER BY name;


-- Task execution flow:
-- 1. bronze_employee_load runs every 10 min IF stream has data
-- 2. silver_employee_transform runs AFTER bronze completes successfully
-- 3. gold_department_metrics runs AFTER silver completes successfully
--
-- Only the root task needs a schedule; child tasks triggered by dependencies


-- Create parallel branches in DAG
CREATE OR REPLACE TASK gold_salary_distribution
    WAREHOUSE = streams_tasks_wh
    AFTER silver_employee_transform  -- Also depends on silver
AS
    CREATE OR REPLACE TABLE gold_salary_distribution AS
    SELECT
        salary_band,
        department,
        COUNT(*) AS employee_count,
        AVG(salary) AS avg_salary,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary
    FROM silver_employees
    GROUP BY salary_band, department;

-- Now we have a DAG with branching:
--                    bronze_employee_load
--                           |
--                 silver_employee_transform
--                      /              \
--        gold_department_metrics  gold_salary_distribution


-- Resume entire task tree (must resume child tasks first, then root)
-- ALTER TASK gold_department_metrics RESUME;
-- ALTER TASK gold_salary_distribution RESUME;
-- ALTER TASK silver_employee_transform RESUME;
-- ALTER TASK bronze_employee_load RESUME;  -- Root task last


-- To suspend, reverse order (root first, then children)
-- ALTER TASK bronze_employee_load SUSPEND;
-- ALTER TASK silver_employee_transform SUSPEND;
-- ALTER TASK gold_department_metrics SUSPEND;
-- ALTER TASK gold_salary_distribution SUSPEND;


-- ============================================================================
-- SECTION 7: Monitor Task Execution
-- ============================================================================
-- Track task runs, success/failure rates, and execution times.
-- ============================================================================

-- Query task execution history (requires ACCOUNTADMIN or TASK_EXECUTION_VIEWER)
SELECT
    name,
    database_name,
    schema_name,
    query_start_time,
    state,
    scheduled_time,
    query_id,
    error_code,
    error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE schema_name = 'HR'
  AND query_start_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
ORDER BY query_start_time DESC
LIMIT 50;


-- From ACCOUNT_USAGE (more historical data, 45-min latency)
SELECT
    name AS task_name,
    database_name,
    schema_name,
    state,
    scheduled_time,
    completed_time,
    DATEDIFF(SECOND, scheduled_time, completed_time) AS execution_seconds,
    error_code,
    error_message
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND scheduled_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY scheduled_time DESC
LIMIT 100;


-- Task success rate analysis
SELECT
    name AS task_name,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) AS failed_runs,
    ROUND(100.0 * SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    AVG(DATEDIFF(SECOND, scheduled_time, completed_time)) AS avg_execution_seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND scheduled_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY name
ORDER BY success_rate_pct DESC;


-- Identify long-running tasks
SELECT
    name AS task_name,
    scheduled_time,
    completed_time,
    DATEDIFF(SECOND, scheduled_time, completed_time) AS execution_seconds,
    state
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND scheduled_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
  AND state = 'SUCCEEDED'
ORDER BY execution_seconds DESC
LIMIT 20;


-- Task scheduling vs actual execution time
SELECT
    name AS task_name,
    scheduled_time,
    query_start_time AS actual_start_time,
    DATEDIFF(SECOND, scheduled_time, query_start_time) AS delay_seconds,
    state
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND scheduled_time >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
ORDER BY scheduled_time DESC
LIMIT 50;


-- Failed task analysis
SELECT
    name AS task_name,
    scheduled_time,
    error_code,
    error_message,
    query_id
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND state = 'FAILED'
  AND scheduled_time >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
ORDER BY scheduled_time DESC;


-- Task credit consumption
SELECT
    task_name,
    DATE(start_time) AS execution_date,
    COUNT(*) AS execution_count,
    SUM(credits_used) AS total_credits,
    AVG(credits_used) AS avg_credits_per_run
FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
WHERE database_name = 'CDC_LAB'
  AND schema_name = 'HR'
  AND start_time >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY task_name, DATE(start_time)
ORDER BY execution_date DESC, total_credits DESC;


-- ============================================================================
-- SECTION 8: Incremental Pipeline Pattern (Bronze-Silver-Gold)
-- ============================================================================
-- Implement complete CDC pipeline using Streams and Tasks for data lakehouse.
-- ============================================================================

-- Create schema for layered architecture
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

USE SCHEMA bronze;

-- BRONZE LAYER: Raw data with CDC metadata
CREATE OR REPLACE TABLE bronze.employee_changes (
    emp_id NUMBER,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    department VARCHAR(50),
    job_title VARCHAR(100),
    salary DECIMAL(12,2),
    hire_date DATE,
    status VARCHAR(20),
    updated_at TIMESTAMP_NTZ,
    cdc_action VARCHAR(20),
    cdc_is_update BOOLEAN,
    cdc_timestamp TIMESTAMP_NTZ,
    ingestion_id NUMBER IDENTITY(1,1)
);

CREATE OR REPLACE STREAM bronze.employee_changes_stream
ON TABLE HR.employees;


-- SILVER LAYER: Cleaned and enriched data
CREATE OR REPLACE TABLE silver.employees_current (
    emp_id NUMBER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    full_name VARCHAR(101),
    email VARCHAR(100),
    department VARCHAR(50),
    job_title VARCHAR(100),
    salary DECIMAL(12,2),
    salary_band VARCHAR(20),
    hire_date DATE,
    years_of_service NUMBER,
    status VARCHAR(20),
    is_manager BOOLEAN,
    last_updated TIMESTAMP_NTZ,
    valid_from TIMESTAMP_NTZ,
    valid_to TIMESTAMP_NTZ,
    is_current BOOLEAN DEFAULT TRUE
);


-- GOLD LAYER: Business aggregates and metrics
CREATE OR REPLACE TABLE gold.department_metrics (
    metric_date DATE,
    department VARCHAR(50),
    active_employees NUMBER,
    total_payroll DECIMAL(15,2),
    avg_salary DECIMAL(12,2),
    avg_tenure NUMBER(10,2),
    turnover_count NUMBER,
    new_hires_count NUMBER,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (metric_date, department)
);

CREATE OR REPLACE TABLE gold.salary_trends (
    metric_date DATE,
    salary_band VARCHAR(20),
    employee_count NUMBER,
    avg_salary DECIMAL(12,2),
    median_salary DECIMAL(12,2),
    min_salary DECIMAL(12,2),
    max_salary DECIMAL(12,2),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (metric_date, salary_band)
);


-- TASK 1: Bronze - Ingest raw CDC data
CREATE OR REPLACE TASK bronze.ingest_employee_changes
    WAREHOUSE = streams_tasks_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('bronze.employee_changes_stream')
AS
    INSERT INTO bronze.employee_changes (
        emp_id, first_name, last_name, email, department,
        job_title, salary, hire_date, status, updated_at,
        cdc_action, cdc_is_update, cdc_timestamp
    )
    SELECT
        emp_id, first_name, last_name, email, department,
        job_title, salary, hire_date, status, updated_at,
        METADATA$ACTION,
        METADATA$ISUPDATE,
        CURRENT_TIMESTAMP()
    FROM bronze.employee_changes_stream;


-- TASK 2: Silver - Transform and merge into current state
CREATE OR REPLACE TASK silver.merge_employee_changes
    WAREHOUSE = streams_tasks_wh
    AFTER bronze.ingest_employee_changes
AS
BEGIN
    -- Merge changes into current employee table
    MERGE INTO silver.employees_current target
    USING (
        SELECT
            emp_id,
            first_name,
            last_name,
            first_name || ' ' || last_name AS full_name,
            LOWER(email) AS email,
            department,
            job_title,
            salary,
            CASE
                WHEN salary < 60000 THEN 'Entry Level'
                WHEN salary < 80000 THEN 'Mid Level'
                WHEN salary < 100000 THEN 'Senior Level'
                ELSE 'Executive'
            END AS salary_band,
            hire_date,
            DATEDIFF(YEAR, hire_date, CURRENT_DATE()) AS years_of_service,
            status,
            CASE WHEN job_title LIKE '%Manager%' OR job_title LIKE '%Director%' OR job_title LIKE '%VP%' THEN TRUE ELSE FALSE END AS is_manager,
            CURRENT_TIMESTAMP() AS last_updated,
            CURRENT_TIMESTAMP() AS valid_from,
            NULL AS valid_to,
            TRUE AS is_current
        FROM bronze.employee_changes
        WHERE cdc_action = 'INSERT'
          AND ingestion_id > (SELECT COALESCE(MAX(ingestion_id), 0) FROM silver.employees_current)
    ) source
    ON target.emp_id = source.emp_id
    WHEN MATCHED THEN UPDATE SET
        target.first_name = source.first_name,
        target.last_name = source.last_name,
        target.full_name = source.full_name,
        target.email = source.email,
        target.department = source.department,
        target.job_title = source.job_title,
        target.salary = source.salary,
        target.salary_band = source.salary_band,
        target.years_of_service = source.years_of_service,
        target.status = source.status,
        target.is_manager = source.is_manager,
        target.last_updated = source.last_updated
    WHEN NOT MATCHED THEN INSERT (
        emp_id, first_name, last_name, full_name, email,
        department, job_title, salary, salary_band, hire_date,
        years_of_service, status, is_manager, last_updated, valid_from, is_current
    ) VALUES (
        source.emp_id, source.first_name, source.last_name, source.full_name, source.email,
        source.department, source.job_title, source.salary, source.salary_band, source.hire_date,
        source.years_of_service, source.status, source.is_manager, source.last_updated, source.valid_from, source.is_current
    );
END;


-- TASK 3: Gold - Calculate department metrics
CREATE OR REPLACE TASK gold.update_department_metrics
    WAREHOUSE = streams_tasks_wh
    AFTER silver.merge_employee_changes
AS
    MERGE INTO gold.department_metrics target
    USING (
        SELECT
            CURRENT_DATE() AS metric_date,
            department,
            COUNT(*) AS active_employees,
            SUM(salary) AS total_payroll,
            AVG(salary) AS avg_salary,
            AVG(years_of_service) AS avg_tenure,
            0 AS turnover_count,  -- Would calculate from historical data
            0 AS new_hires_count  -- Would calculate from hire_date
        FROM silver.employees_current
        WHERE status = 'Active'
          AND is_current = TRUE
        GROUP BY department
    ) source
    ON target.metric_date = source.metric_date
       AND target.department = source.department
    WHEN MATCHED THEN UPDATE SET
        target.active_employees = source.active_employees,
        target.total_payroll = source.total_payroll,
        target.avg_salary = source.avg_salary,
        target.avg_tenure = source.avg_tenure
    WHEN NOT MATCHED THEN INSERT (
        metric_date, department, active_employees, total_payroll,
        avg_salary, avg_tenure, turnover_count, new_hires_count
    ) VALUES (
        source.metric_date, source.department, source.active_employees, source.total_payroll,
        source.avg_salary, source.avg_tenure, source.turnover_count, source.new_hires_count
    );


-- TASK 4: Gold - Calculate salary trends
CREATE OR REPLACE TASK gold.update_salary_trends
    WAREHOUSE = streams_tasks_wh
    AFTER silver.merge_employee_changes
AS
    MERGE INTO gold.salary_trends target
    USING (
        SELECT
            CURRENT_DATE() AS metric_date,
            salary_band,
            COUNT(*) AS employee_count,
            AVG(salary) AS avg_salary,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary,
            MIN(salary) AS min_salary,
            MAX(salary) AS max_salary
        FROM silver.employees_current
        WHERE status = 'Active'
          AND is_current = TRUE
        GROUP BY salary_band
    ) source
    ON target.metric_date = source.metric_date
       AND target.salary_band = source.salary_band
    WHEN MATCHED THEN UPDATE SET
        target.employee_count = source.employee_count,
        target.avg_salary = source.avg_salary,
        target.median_salary = source.median_salary,
        target.min_salary = source.min_salary,
        target.max_salary = source.max_salary
    WHEN NOT MATCHED THEN INSERT (
        metric_date, salary_band, employee_count, avg_salary,
        median_salary, min_salary, max_salary
    ) VALUES (
        source.metric_date, source.salary_band, source.employee_count, source.avg_salary,
        source.median_salary, source.min_salary, source.max_salary
    );


-- View complete task DAG
SELECT
    name,
    state,
    schedule,
    condition_text,
    predecessors
FROM INFORMATION_SCHEMA.TASKS
WHERE task_database = 'CDC_LAB'
ORDER BY
    CASE
        WHEN predecessors IS NULL THEN 1
        WHEN ARRAY_SIZE(predecessors) = 1 THEN 2
        ELSE 3
    END,
    name;


-- Resume task tree (bottom-up)
-- ALTER TASK gold.update_salary_trends RESUME;
-- ALTER TASK gold.update_department_metrics RESUME;
-- ALTER TASK silver.merge_employee_changes RESUME;
-- ALTER TASK bronze.ingest_employee_changes RESUME;


-- Test the pipeline with changes
INSERT INTO hr.employees (emp_id, first_name, last_name, email, department, job_title, salary, hire_date)
VALUES (200, 'Test', 'User', 'test.user@company.com', 'Engineering', 'Developer', 75000, CURRENT_DATE());

-- Check if stream has data
SELECT SYSTEM$STREAM_HAS_DATA('bronze.employee_changes_stream');


-- ============================================================================
-- CLEANUP
-- ============================================================================

/*
-- Suspend all tasks
ALTER TASK IF EXISTS bronze.ingest_employee_changes SUSPEND;
ALTER TASK IF EXISTS silver.merge_employee_changes SUSPEND;
ALTER TASK IF EXISTS gold.update_department_metrics SUSPEND;
ALTER TASK IF EXISTS gold.update_salary_trends SUSPEND;

-- Drop objects
DROP DATABASE IF EXISTS cdc_lab;
DROP WAREHOUSE IF EXISTS streams_tasks_wh;
*/


-- ============================================================================
-- KEY TAKEAWAYS
-- ============================================================================
-- 1. Streams capture DML changes (INSERT, UPDATE, DELETE) using CDC with
--    special METADATA$ columns (ACTION, ISUPDATE, ROW_ID).
--
-- 2. UPDATE operations appear as two rows in stream: DELETE (old) + INSERT (new)
--    with METADATA$ISUPDATE = TRUE for both.
--
-- 3. Streams advance offset only when data is consumed in DML transaction.
--    Querying stream doesn't consume it.
--
-- 4. Multiple streams on same table capture changes independently - each
--    maintains its own offset.
--
-- 5. Tasks automate SQL execution on schedule (CRON or interval) or based
--    on conditions (WHEN SYSTEM$STREAM_HAS_DATA).
--
-- 6. Task DAGs enable multi-stage pipelines with dependencies (AFTER clause).
--    Only root task needs schedule; children triggered by parent completion.
--
-- 7. Bronze-Silver-Gold pattern:
--    - Bronze: Raw CDC data with full history
--    - Silver: Clean, current state with business logic
--    - Gold: Aggregated metrics for analytics
--
-- 8. Monitor tasks using TASK_HISTORY views in INFORMATION_SCHEMA and
--    ACCOUNT_USAGE for success rates, execution times, and failures.
--
-- 9. Best practices:
--    - Use WHEN clause to avoid unnecessary task runs
--    - Create task dependencies for ordered execution
--    - Monitor and alert on failed tasks
--    - Right-size warehouses for task workload
--
-- 10. Use cases: Incremental ETL, real-time analytics, data replication,
--     audit logging, automated data quality checks.
-- ============================================================================
