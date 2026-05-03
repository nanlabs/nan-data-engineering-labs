# Exercise 04: CDC with Streams & Tasks

## Overview
Build an automated Change Data Capture (CDC) pipeline using Snowflake Streams and Tasks to process data changes in real-time and maintain a multi-layer analytics architecture.

**Estimated Time**: 2.5 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Module 03 (SQL basics), Exercise 01 (Virtual Warehouses), understanding of ETL concepts

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create and manage Streams for change data capture
- Query streams to identify INSERT, UPDATE, and DELETE operations
- Build automated pipelines using Tasks
- Implement task dependencies and DAGs
- Monitor task execution and handle failures
- Design Bronze→Silver→Gold architecture with automated processing

---

## Scenario
You're building a real-time order processing system for an e-commerce platform. Orders are continuously created, updated, and occasionally canceled in the bronze layer. Your goal is to:
- Track all changes to the orders table
- Automatically process completed orders to the silver layer
- Generate daily aggregations in the gold layer
- Monitor the entire pipeline for failures

The system must run without manual intervention and handle incremental processing efficiently.

---

## Requirements

### Task 1: Setup Source Tables (20 min)
Create the bronze layer and populate with initial order data.

**Create Bronze Orders Table**:
```sql
CREATE OR REPLACE TABLE bronze_orders (
    order_id INT,
    customer_id INT,
    product VARCHAR(100),
    amount DECIMAL(10,2),
    status VARCHAR(20),  -- PENDING, COMPLETED, CANCELLED
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Load Initial Data** (1,000 orders):
```sql
INSERT INTO bronze_orders
SELECT
    seq4() as order_id,
    uniform(1, 200, random()) as customer_id,
    CASE uniform(1, 5, random())
        WHEN 1 THEN 'Laptop'
        WHEN 2 THEN 'Phone'
        WHEN 3 THEN 'Tablet'
        WHEN 4 THEN 'Monitor'
        ELSE 'Keyboard'
    END as product,
    uniform(50, 2000, random()) as amount,
    CASE uniform(1, 3, random())
        WHEN 1 THEN 'PENDING'
        WHEN 2 THEN 'COMPLETED'
        ELSE 'CANCELLED'
    END as status,
    dateadd(hour, -uniform(1, 720, random()), current_timestamp()) as created_at,
    dateadd(hour, -uniform(1, 720, random()), current_timestamp()) as updated_at
FROM table(generator(rowcount => 1000));
```

**Verification Queries**:
```sql
-- Check data distribution
SELECT status, COUNT(*) as count, AVG(amount) as avg_amount
FROM bronze_orders
GROUP BY status;

-- Sample records
SELECT * FROM bronze_orders LIMIT 10;
```

**Success Criteria**:
- ✅ `bronze_orders` table created with 1,000 rows
- ✅ Data distributed across PENDING, COMPLETED, CANCELLED statuses
- ✅ Timestamps properly generated (last 30 days)
- ✅ Amount ranges from $50 to $2,000

---

### Task 2: Create Streams (25 min)
Set up a stream to track changes to the bronze_orders table.

**Create Stream**:
```sql
CREATE OR REPLACE STREAM orders_stream
ON TABLE bronze_orders
COMMENT = 'Track all changes to bronze_orders for CDC processing';
```

**Generate Change Data**:
```sql
-- INSERT: 100 new orders
INSERT INTO bronze_orders
SELECT
    seq4() + 1000 as order_id,
    uniform(1, 200, random()) as customer_id,
    'NewProduct' as product,
    uniform(100, 500, random()) as amount,
    'PENDING' as status,
    current_timestamp() as created_at,
    current_timestamp() as updated_at
FROM table(generator(rowcount => 100));

-- UPDATE: 50 orders to COMPLETED
UPDATE bronze_orders
SET status = 'COMPLETED',
    updated_at = current_timestamp()
WHERE status = 'PENDING'
LIMIT 50;

-- DELETE: 10 cancelled orders
DELETE FROM bronze_orders
WHERE status = 'CANCELLED'
LIMIT 10;
```

**Query Stream with Metadata**:
```sql
-- View stream contents
SELECT
    order_id,
    customer_id,
    product,
    amount,
    status,
    METADATA$ACTION as action_type,  -- INSERT, DELETE
    METADATA$ISUPDATE as is_update,   -- TRUE for updates
    METADATA$ROW_ID as row_id
FROM orders_stream
ORDER BY METADATA$ACTION, order_id
LIMIT 100;

-- Count changes by type
SELECT
    METADATA$ACTION as action,
    METADATA$ISUPDATE as is_update,
    COUNT(*) as change_count
FROM orders_stream
GROUP BY METADATA$ACTION, METADATA$ISUPDATE;
```

**Understanding Streams**:
- Updates appear as DELETE (old) + INSERT (new) rows
- Stream offset only advances when consumed (via DML)
- Records remain in stream until consumed

**Success Criteria**:
- ✅ Stream `orders_stream` created successfully
- ✅ Stream shows ~160 rows (100 INSERT, 50 UPDATE=100 rows, 10 DELETE)
- ✅ Can query `METADATA$ACTION` and `METADATA$ISUPDATE` columns
- ✅ Stream offset has not advanced yet (data still visible)

---

### Task 3: Manual Stream Consumption (30 min)
Process the stream to silver layer and verify offset behavior.

**Create Silver Table**:
```sql
CREATE OR REPLACE TABLE silver_orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product VARCHAR(100),
    amount DECIMAL(10,2),
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    processed_at TIMESTAMP DEFAULT current_timestamp()
);
```

**Manual Stream Processing**:
```sql
-- Process only COMPLETED orders from stream
INSERT INTO silver_orders (order_id, customer_id, product, amount, created_at, completed_at)
SELECT
    order_id,
    customer_id,
    product,
    amount,
    created_at,
    updated_at as completed_at
FROM orders_stream
WHERE status = 'COMPLETED'
    AND METADATA$ACTION = 'INSERT'
    AND METADATA$ISUPDATE = FALSE;
```

**Verify Stream Offset Advanced**:
```sql
-- Stream should now be empty (offset advanced)
SELECT COUNT(*) as remaining_records FROM orders_stream;
-- Expected: 0

-- Check silver table
SELECT COUNT(*) as processed_orders FROM silver_orders;

-- Generate more changes
UPDATE bronze_orders
SET status = 'COMPLETED'
WHERE status = 'PENDING'
LIMIT 20;

-- Stream should show new data
SELECT COUNT(*) as new_changes FROM orders_stream;
-- Expected: ~40 (20 UPDATE = 40 rows)
```

**Success Criteria**:
- ✅ Silver table created and populated with completed orders
- ✅ Stream offset advanced after consumption (became empty)
- ✅ New changes appear in stream after additional updates
- ✅ Documented how stream offset works (advances on DML consumption)

---

### Task 4: Automated Task (30 min)
Create a Task to automatically process the stream every 5 minutes.

**Create Processing Task**:
```sql
-- Create warehouse for tasks
CREATE WAREHOUSE IF NOT EXISTS WH_TASK_SMALL
WITH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Create task with schedule
CREATE OR REPLACE TASK process_orders_task
    WAREHOUSE = WH_TASK_SMALL
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
    AS
INSERT INTO silver_orders (order_id, customer_id, product, amount, created_at, completed_at)
SELECT
    order_id,
    customer_id,
    product,
    amount,
    created_at,
    updated_at as completed_at
FROM orders_stream
WHERE status = 'COMPLETED'
    AND METADATA$ACTION = 'INSERT'
    AND METADATA$ISUPDATE = FALSE;
```

**Resume Task** (tasks created in suspended state):
```sql
ALTER TASK process_orders_task RESUME;

-- Verify task is running
SHOW TASKS LIKE 'process_orders_task';
```

**Test Automated Execution**:
```sql
-- Generate new completed orders
INSERT INTO bronze_orders (order_id, customer_id, product, amount, status, created_at, updated_at)
SELECT
    seq4() + 2000,
    uniform(1, 200, random()),
    'TestProduct',
    uniform(100, 500, random()),
    'COMPLETED',
    current_timestamp(),
    current_timestamp()
FROM table(generator(rowcount => 25));

-- Wait 5+ minutes, then check if task processed the data
SELECT
    name,
    state,
    scheduled_time,
    query_start_time,
    next_scheduled_time,
    completed_time,
    error_code,
    error_message
FROM table(information_schema.task_history())
WHERE name = 'PROCESS_ORDERS_TASK'
ORDER BY scheduled_time DESC
LIMIT 10;

-- Verify silver table updated
SELECT MAX(processed_at) as last_processed FROM silver_orders;
```

**Success Criteria**:
- ✅ Task created with SCHEDULE='5 MINUTE'
- ✅ WHEN condition checks for stream data
- ✅ Task resumed and shows STATE='started'
- ✅ Task executes successfully (visible in TASK_HISTORY)
- ✅ Silver table automatically updated with new orders

---

### Task 5: Task DAG Pipeline (30 min)
Build a 3-task pipeline with dependencies: Bronze→Silver→Gold.

**Create Gold Aggregation Table**:
```sql
CREATE OR REPLACE TABLE gold_daily_sales (
    sales_date DATE,
    total_orders INT,
    total_revenue DECIMAL(15,2),
    avg_order_value DECIMAL(10,2),
    unique_customers INT,
    last_updated TIMESTAMP DEFAULT current_timestamp()
);
```

**Suspend Existing Task**:
```sql
ALTER TASK process_orders_task SUSPEND;
```

**Create Task DAG**:
```sql
-- Root task: Process stream to silver
CREATE OR REPLACE TASK bronze_to_silver_task
    WAREHOUSE = WH_TASK_SMALL
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
    AS
INSERT INTO silver_orders (order_id, customer_id, product, amount, created_at, completed_at)
SELECT
    order_id, customer_id, product, amount, created_at, updated_at
FROM orders_stream
WHERE status = 'COMPLETED'
    AND METADATA$ACTION = 'INSERT'
    AND METADATA$ISUPDATE = FALSE;

-- Child task 1: Silver to Gold daily aggregation
CREATE OR REPLACE TASK silver_to_gold_task
    WAREHOUSE = WH_TASK_SMALL
    AFTER bronze_to_silver_task  -- Dependency
    AS
MERGE INTO gold_daily_sales g
USING (
    SELECT
        DATE(completed_at) as sales_date,
        COUNT(*) as total_orders,
        SUM(amount) as total_revenue,
        AVG(amount) as avg_order_value,
        COUNT(DISTINCT customer_id) as unique_customers
    FROM silver_orders
    WHERE DATE(completed_at) = CURRENT_DATE()
    GROUP BY DATE(completed_at)
) s
ON g.sales_date = s.sales_date
WHEN MATCHED THEN
    UPDATE SET
        total_orders = s.total_orders,
        total_revenue = s.total_revenue,
        avg_order_value = s.avg_order_value,
        unique_customers = s.unique_customers,
        last_updated = current_timestamp()
WHEN NOT MATCHED THEN
    INSERT (sales_date, total_orders, total_revenue, avg_order_value, unique_customers)
    VALUES (s.sales_date, s.total_orders, s.total_revenue, s.avg_order_value, s.unique_customers);

-- Child task 2: Data quality check
CREATE OR REPLACE TASK data_quality_task
    WAREHOUSE = WH_TASK_SMALL
    AFTER silver_to_gold_task  -- Runs after gold update
    AS
INSERT INTO data_quality_log (check_date, check_name, status, detail)
SELECT
    current_timestamp(),
    'gold_daily_sales_completeness',
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
    'Today sales: ' || COUNT(*)::VARCHAR
FROM gold_daily_sales
WHERE sales_date = CURRENT_DATE();
```

**Create Quality Log Table**:
```sql
CREATE OR REPLACE TABLE data_quality_log (
    check_date TIMESTAMP,
    check_name VARCHAR(100),
    status VARCHAR(20),
    detail VARCHAR(500)
);
```

**Resume Task DAG** (resume in reverse dependency order):
```sql
-- Resume child tasks first
ALTER TASK data_quality_task RESUME;
ALTER TASK silver_to_gold_task RESUME;

-- Resume root task last (starts entire DAG)
ALTER TASK bronze_to_silver_task RESUME;

-- View task tree
SHOW TASKS;
```

**Monitor Task Execution**:
```sql
-- View task hierarchy and execution history
SELECT
    name,
    state,
    predecessors,
    schedule,
    warehouse,
    query_text
FROM table(information_schema.task_history())
WHERE scheduled_time >= DATEADD(hour, -1, current_timestamp())
ORDER BY scheduled_time DESC, name;
```

**Success Criteria**:
- ✅ 3 tasks created with proper dependencies (AFTER clause)
- ✅ Task DAG visualized: bronze_to_silver → silver_to_gold → data_quality
- ✅ All tasks resumed in correct order
- ✅ Gold table populated with daily aggregations
- ✅ Data quality checks logged successfully

---

### Task 6: Error Handling & Monitoring (25 min)
Implement error detection, monitoring, and retry logic.

**Introduce Erroneous Data**:
```sql
-- Insert order with invalid data (negative amount)
INSERT INTO bronze_orders VALUES
    (9999, 100, 'ErrorProduct', -500.00, 'COMPLETED', current_timestamp(), current_timestamp());
```

**Add Validation to Task**:
```sql
ALTER TASK bronze_to_silver_task SUSPEND;

CREATE OR REPLACE TASK bronze_to_silver_task
    WAREHOUSE = WH_TASK_SMALL
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
    AS
BEGIN
    -- Insert valid orders
    INSERT INTO silver_orders (order_id, customer_id, product, amount, created_at, completed_at)
    SELECT
        order_id, customer_id, product, amount, created_at, updated_at
    FROM orders_stream
    WHERE status = 'COMPLETED'
        AND METADATA$ACTION = 'INSERT'
        AND METADATA$ISUPDATE = FALSE
        AND amount > 0;  -- Validation

    -- Log rejected orders
    INSERT INTO rejected_orders (order_id, rejection_reason, rejected_at)
    SELECT
        order_id,
        'Invalid amount: ' || amount::VARCHAR,
        current_timestamp()
    FROM orders_stream
    WHERE status = 'COMPLETED'
        AND amount <= 0;
END;
```

**Create Rejected Orders Table**:
```sql
CREATE OR REPLACE TABLE rejected_orders (
    order_id INT,
    rejection_reason VARCHAR(500),
    rejected_at TIMESTAMP
);
```

**Monitor Task Health**:
```sql
-- Query task execution history
SELECT
    name,
    state,
    scheduled_time,
    completed_time,
    error_code,
    error_message,
    TIMESTAMPDIFF(second, query_start_time, completed_time) as execution_seconds
FROM table(information_schema.task_history())
WHERE scheduled_time >= DATEADD(day, -7, current_timestamp())
ORDER BY scheduled_time DESC;

-- Failed tasks only
SELECT
    name,
    scheduled_time,
    error_code,
    error_message
FROM table(information_schema.task_history())
WHERE state = 'FAILED'
    AND scheduled_time >= DATEADD(day, -7, current_timestamp())
ORDER BY scheduled_time DESC;

-- Task success rate
SELECT
    name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) as failed_runs,
    (successful_runs::FLOAT / total_runs * 100)::DECIMAL(5,2) as success_rate_pct
FROM table(information_schema.task_history())
WHERE scheduled_time >= DATEADD(day, -7, current_timestamp())
GROUP BY name;
```

**Stream Monitoring**:
```sql
-- Check stream lag
SELECT
    'orders_stream' as stream_name,
    COUNT(*) as pending_records,
    current_timestamp() as check_time
FROM orders_stream;

-- Monitor stream metadata
SHOW STREAMS LIKE 'orders_stream';
```

**Create Alert Query** (run periodically):
```sql
-- Alert if tasks haven't run in 30 minutes
SELECT
    name,
    MAX(scheduled_time) as last_run,
    TIMESTAMPDIFF(minute, MAX(scheduled_time), current_timestamp()) as minutes_since_run
FROM table(information_schema.task_history())
WHERE name IN ('BRONZE_TO_SILVER_TASK', 'SILVER_TO_GOLD_TASK', 'DATA_QUALITY_TASK')
GROUP BY name
HAVING minutes_since_run > 30;
```

**Success Criteria**:
- ✅ Error handling implemented (validation + rejected orders table)
- ✅ Invalid data logged to rejected_orders table
- ✅ Task execution history queried (success/failure tracking)
- ✅ Stream lag monitoring query created
- ✅ Alert query identifies stale tasks
- ✅ Documented 3 best practices for task monitoring

---

## Hints

<details>
<summary>Hint 1: Understanding Stream Metadata</summary>

Streams track changes with special metadata columns:
```sql
-- METADATA$ACTION values:
-- 'INSERT' = new row or updated row (new version)
-- 'DELETE' = deleted row or updated row (old version)

-- For UPDATE operations:
-- METADATA$ISUPDATE = TRUE for both DELETE and INSERT rows
-- METADATA$ACTION = 'DELETE' for old version, 'INSERT' for new version

-- Example: Query only true inserts (not updates)
SELECT *
FROM orders_stream
WHERE METADATA$ACTION = 'INSERT'
    AND METADATA$ISUPDATE = FALSE;

-- Example: Query only deletes (not updates)
SELECT *
FROM orders_stream
WHERE METADATA$ACTION = 'DELETE'
    AND METADATA$ISUPDATE = FALSE;
```
</details>

<details>
<summary>Hint 2: Stream Offset Behavior</summary>

```sql
-- Stream offset advances when:
-- 1. DML consumes data (INSERT, UPDATE, DELETE, MERGE using stream)
-- 2. Within a transaction that commits

-- Check if stream has data (before scheduling task)
SELECT SYSTEM$STREAM_HAS_DATA('orders_stream');
-- Returns: TRUE or FALSE

-- Stream shows same data until consumed
SELECT COUNT(*) FROM orders_stream;  -- Returns N
SELECT COUNT(*) FROM orders_stream;  -- Still returns N (no consumption)

-- Consume stream
INSERT INTO target_table SELECT * FROM orders_stream;

-- Stream now empty
SELECT COUNT(*) FROM orders_stream;  -- Returns 0
```
</details>

<details>
<summary>Hint 3: Task Management</summary>

```sql
-- Create task (automatically suspended)
CREATE TASK my_task
    WAREHOUSE = WH_TASK_SMALL
    SCHEDULE = '5 MINUTE'
    AS SELECT 1;

-- Resume task (starts execution)
ALTER TASK my_task RESUME;

-- Suspend task (stops execution)
ALTER TASK my_task SUSPEND;

-- Modify task schedule
ALTER TASK my_task SET SCHEDULE = '10 MINUTE';

-- Force execute task immediately (for testing)
EXECUTE TASK my_task;

-- Delete task
DROP TASK my_task;

-- Show all tasks
SHOW TASKS;

-- Describe task details
DESCRIBE TASK my_task;
```
</details>

<details>
<summary>Hint 4: Task Dependencies</summary>

```sql
-- Root task (scheduled)
CREATE TASK root_task
    WAREHOUSE = WH
    SCHEDULE = '5 MINUTE'
    AS SELECT 1;

-- Child task (AFTER clause, no SCHEDULE)
CREATE TASK child_task_1
    WAREHOUSE = WH
    AFTER root_task  -- Dependency
    AS SELECT 2;

-- Grandchild task
CREATE TASK child_task_2
    WAREHOUSE = WH
    AFTER child_task_1  -- Runs after child_task_1
    AS SELECT 3;

-- Resume in reverse order
ALTER TASK child_task_2 RESUME;
ALTER TASK child_task_1 RESUME;
ALTER TASK root_task RESUME;  -- Starts entire DAG
```
</details>

<details>
<summary>Hint 5: Monitoring Queries</summary>

```sql
-- Task execution history
SELECT *
FROM table(information_schema.task_history(
    scheduled_time_range_start => DATEADD(hour, -24, current_timestamp()),
    task_name => 'BRONZE_TO_SILVER_TASK'
))
ORDER BY scheduled_time DESC;

-- Current task state
SELECT
    name,
    database_name,
    schema_name,
    state,  -- 'started' or 'suspended'
    schedule,
    warehouse,
    predecessors  -- Shows dependencies
FROM table(information_schema.tasks)
WHERE name LIKE '%TASK%';

-- Credits consumed by tasks
SELECT
    name,
    SUM(TIMESTAMPDIFF(second, query_start_time, completed_time)) as total_seconds,
    COUNT(*) as execution_count
FROM table(information_schema.task_history())
WHERE scheduled_time >= DATEADD(day, -7, current_timestamp())
    AND state = 'SUCCEEDED'
GROUP BY name;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-04-cdc-streams-tasks
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: bronze_orders table created with 1,000 rows
✅ Task 2: orders_stream created and shows change records
✅ Task 3: Stream consumed, offset advanced correctly
✅ Task 4: Automated task created and executed successfully
✅ Task 5: 3-task DAG created with dependencies
✅ Task 6: Error handling and monitoring implemented

🎉 Exercise 04 Complete! CDC Pipeline fully automated.
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All stream and task creation commands
2. `task-dag-diagram.mmd` - Mermaid diagram of task dependencies
3. `monitoring-queries.sql` - Save your monitoring queries
4. `pipeline-documentation.md` - Document pipeline behavior, error handling, expected SLA

---

## Resources
- Snowflake Documentation: [Streams](https://docs.snowflake.com/en/user-guide/streams)
- Snowflake Documentation: [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
- Notebook: `notebooks/04-streams-tasks.sql`
- Diagram: `assets/diagrams/streams-tasks-pipeline.mmd`
- Theory: `theory/concepts.md#streams-and-tasks`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 05: Snowpipe Auto-Ingestion (event-driven loading)
- ✅ Exercise 06: Secure Data Sharing (partner data distribution)
- Explore Snowflake's Task Observability Interface (UI monitoring)
- Consider implementing alerting with external systems (email, Slack)
