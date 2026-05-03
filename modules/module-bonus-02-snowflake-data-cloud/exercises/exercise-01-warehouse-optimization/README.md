# Exercise 01: Warehouse Optimization

## Overview
Master Virtual Warehouse sizing, auto-suspend/resume, and cost optimization strategies to build efficient compute infrastructure.

**Estimated Time**: 2 hours
**Difficulty**: ⭐⭐⭐ Intermediate
**Prerequisites**: Module 03 (SQL basics), Snowflake account with ACCOUNTADMIN access

---

## Learning Objectives
By completing this exercise, you will be able to:
- Create and configure virtual warehouses with different sizes
- Compare performance and cost across warehouse sizes
- Configure auto-suspend and auto-resume settings
- Monitor credit usage and calculate costs
- Set up multi-cluster warehouses for auto-scaling
- Optimize compute costs while maintaining performance

---

## Scenario
You're building a data platform for your organization. Different workloads have different compute requirements:
- ETL pipelines need large warehouses for fast processing
- Interactive dashboards need small warehouses with instant availability
- Ad-hoc queries can tolerate slower performance for lower cost

Your goal is to optimize compute costs while maintaining acceptable performance for each use case.

---

## Requirements

### Task 1: Create Warehouses (15 min)
Create three virtual warehouses with different configurations:

**Warehouse Specifications**:
1. **`WH_XSMALL_DEV`**: X-Small warehouse
   - Auto-suspend: 60 seconds
   - Auto-resume: Enabled
   - Purpose: Development and testing

2. **`WH_MEDIUM_ETL`**: Medium warehouse
   - Auto-suspend: 300 seconds (5 minutes)
   - Auto-resume: Enabled
   - Purpose: ETL pipelines

3. **`WH_LARGE_ANALYTICS`**: Large warehouse
   - Auto-suspend: 600 seconds (10 minutes)
   - Auto-resume: Enabled
   - Purpose: Complex analytics queries

**Success Criteria**:
- ✅ All 3 warehouses created successfully
- ✅ Each has correct size and auto-suspend settings
- ✅ All warehouses set to auto-resume
- ✅ Verified with `SHOW WAREHOUSES`

---

### Task 2: Performance Testing (25 min)
Compare performance and cost between X-Small and Large warehouses.

**Test Query**: Load 1M rows and perform aggregations
```sql
-- Create test table
CREATE OR REPLACE TABLE performance_test AS
SELECT
    seq4() as id,
    uniform(1, 100, random()) as category,
    uniform(1, 1000, random()) as amount,
    dateadd(day, uniform(1, 365, random()), '2023-01-01'::date) as transaction_date
FROM table(generator(rowcount => 1000000));

-- Test query
SELECT
    category,
    COUNT(*) as transaction_count,
    AVG(amount) as avg_amount,
    SUM(amount) as total_amount,
    MIN(transaction_date) as first_transaction,
    MAX(transaction_date) as last_transaction
FROM performance_test
GROUP BY category
ORDER BY total_amount DESC;
```

**Measurements Required**:
1. Run query on `WH_XSMALL_DEV`:
   - Record execution time (from QUERY_HISTORY)
   - Calculate credits consumed

2. Run query on `WH_LARGE_ANALYTICS`:
   - Record execution time
   - Calculate credits consumed

3. Create comparison table:
   - Execution time difference (% faster)
   - Cost difference ($ if using on-demand pricing)
   - Cost per second metric

**Success Criteria**:
- ✅ Query executed on both warehouses
- ✅ Performance metrics documented in comparison table
- ✅ Cost difference calculated (Large = 8x credits vs X-Small)
- ✅ Analysis: Is the performance gain worth the cost increase?

---

### Task 3: Auto-Suspend Configuration (15 min)
Configure and verify auto-suspend behavior.

**Tasks**:
1. **Modify Auto-Suspend**: Change `WH_XSMALL_DEV` to 30 seconds
   ```sql
   ALTER WAREHOUSE WH_XSMALL_DEV SET AUTO_SUSPEND = 30;
   ```

2. **Test Suspension**:
   - Run a quick query
   - Wait 35 seconds
   - Verify warehouse suspended using `SHOW WAREHOUSES`

3. **Test Auto-Resume**:
   - Run another query (warehouse should auto-resume)
   - Verify query completes successfully
   - Check QUERY_HISTORY for queue time

4. **Disable Auto-Suspend** (testing only):
   - Set AUTO_SUSPEND = NULL on test warehouse
   - Observe continuous credit consumption
   - Re-enable auto-suspend

**Success Criteria**:
- ✅ Warehouse suspends after idle timeout
- ✅ Warehouse auto-resumes on new query
- ✅ Observed cost of disabled auto-suspend
- ✅ Documented optimal auto-suspend settings for each use case

---

### Task 4: Multi-Cluster Setup (25 min)
Configure multi-cluster warehouse for auto-scaling workloads.

**Scenario**: Dashboard cluster with variable load (5-50 concurrent users).

**Create Multi-Cluster Warehouse**:
```sql
CREATE WAREHOUSE WH_DASHBOARD_MULTI
WITH
    WAREHOUSE_SIZE = SMALL
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'ECONOMY';  -- or 'STANDARD'
```

**Test Scaling**:
1. **Economy Mode**:
   - Requires 6 minutes of queuing before adding cluster
   - Test with simulated concurrent queries
   - Observe scaling behavior in QUERY_HISTORY

2. **Standard Mode**:
   - Change to SCALING_POLICY = 'STANDARD'
   - More aggressive scaling (prevents queuing)
   - Compare cost vs economy mode

**Cost Analysis**:
- Economy mode: Lower cost, some queuing
- Standard mode: Higher cost, minimal queuing
- Calculate break-even point based on query volume

**Success Criteria**:
- ✅ Multi-cluster warehouse created with 1-3 clusters
- ✅ Tested both ECONOMY and STANDARD scaling policies
- ✅ Observed cluster scaling in action
- ✅ Documented when to use each policy (cost vs performance)

---

### Task 5: Credit Monitoring (20 min)
Query warehouse credit usage and calculate costs.

**Queries to Implement**:

1. **Daily Credit Usage by Warehouse**:
```sql
SELECT
    warehouse_name,
    DATE(start_time) as usage_date,
    SUM(credits_used) as total_credits,
    SUM(credits_used) * 2.00 as estimated_cost_usd  -- Adjust rate
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, usage_date
ORDER BY usage_date DESC, total_credits DESC;
```

2. **Hourly Usage Pattern** (identify peak times):
```sql
SELECT
    warehouse_name,
    HOUR(start_time) as hour_of_day,
    AVG(credits_used) as avg_credits_per_hour
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, hour_of_day
ORDER BY warehouse_name, hour_of_day;
```

3. **Monthly Cost Projection**:
```sql
-- Based on last 7 days of usage
SELECT
    warehouse_name,
    SUM(credits_used) as credits_last_7_days,
    (SUM(credits_used) / 7 * 30) as projected_monthly_credits,
    (SUM(credits_used) / 7 * 30) * 2.00 as projected_monthly_cost_usd
FROM snowflake.account_usage.warehouse_metering_history
WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY projected_monthly_cost_usd DESC;
```

**Create Dashboard Query**: Combine metrics into single view for monitoring.

**Success Criteria**:
- ✅ Daily credit usage query working
- ✅ Identified peak usage hours
- ✅ Monthly cost projection calculated
- ✅ Dashboard query created for ongoing monitoring

---

### Task 6: Optimization (20 min)
Implement cost-saving strategies and document expected savings.

**Identify and Implement 5 Optimizations**:

1. **Right-Size Warehouses**:
   - Find over-provisioned warehouses (low utilization)
   - Downsize by 1-2 levels
   - Document expected savings (% reduction)

2. **Optimize Auto-Suspend**:
   - Find warehouses with auto-suspend > 5 minutes
   - Reduce to 60-120 seconds for dev/test
   - Calculate idle time savings

3. **Consolidate Small Warehouses**:
   - Identify underutilized warehouses (<10 queries/day)
   - Consolidate onto shared warehouse
   - Eliminate unnecessary warehouse costs

4. **Schedule Warehouse Suspension**:
   - Create CRON job to suspend warehouses after hours
   - Resume before business hours
   - Calculate 16-hour daily savings (nights/weekends)

5. **Implement Resource Monitors**:
   - Create quota alerts at 80%, 90%, 100%
   - Prevent runaway costs
   - Set up notifications

**Documentation Required**:
- Before/after warehouse sizes
- Expected credit reduction per month
- Total expected savings (% and $)
- Implementation timeline

**Success Criteria**:
- ✅ Implemented 5 cost-saving strategies
- ✅ Documented expected savings for each (% reduction)
- ✅ Created resource monitors with alerts
- ✅ Total expected savings: 20-30% reduction in compute costs

---

## Hints

<details>
<summary>Hint 1: Creating Warehouses</summary>

```sql
-- Create X-Small warehouse
CREATE WAREHOUSE WH_XSMALL_DEV
WITH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Verify configuration
SHOW WAREHOUSES LIKE 'WH_%';

-- Describe specific warehouse
DESCRIBE WAREHOUSE WH_XSMALL_DEV;
```
</details>

<details>
<summary>Hint 2: Performance Testing</summary>

```sql
-- Set warehouse and record start time
USE WAREHOUSE WH_XSMALL_DEV;
SET start_time = CURRENT_TIMESTAMP();

-- Run test query
SELECT category, COUNT(*), AVG(amount), SUM(amount)
FROM performance_test
GROUP BY category;

-- Check execution time in QUERY_HISTORY
SELECT
    query_id,
    query_text,
    warehouse_name,
    warehouse_size,
    execution_time / 1000 as execution_seconds,
    credits_used_cloud_services,
    bytes_scanned
FROM snowflake.account_usage.query_history
WHERE query_text LIKE '%performance_test%'
    AND start_time >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 10;
```
</details>

<details>
<summary>Hint 3: Warehouse Scaling and Modes</summary>

```sql
-- Create multi-cluster warehouse
CREATE WAREHOUSE WH_MULTI_CLUSTER
WITH
    WAREHOUSE_SIZE = SMALL
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3
    SCALING_POLICY = 'ECONOMY';  -- Wait 6 min before scaling

-- Modify scaling policy
ALTER WAREHOUSE WH_MULTI_CLUSTER SET SCALING_POLICY = 'STANDARD';

-- Check cluster activity
SHOW WAREHOUSES LIKE 'WH_MULTI_CLUSTER';

-- View warehouse load
SELECT
    warehouse_name,
    AVG(avg_running) as avg_queries_running,
    AVG(avg_queued_load) as avg_queries_queued
FROM snowflake.account_usage.warehouse_load_history
WHERE warehouse_name = 'WH_MULTI_CLUSTER'
    AND start_time >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
GROUP BY warehouse_name;
```
</details>

<details>
<summary>Hint 4: Resource Monitors</summary>

```sql
-- Create resource monitor
CREATE RESOURCE MONITOR monthly_quota
WITH
    CREDIT_QUOTA = 1000  -- Maximum credits per month
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 80 PERCENT DO NOTIFY
        ON 90 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND
        ON 110 PERCENT DO SUSPEND_IMMEDIATE;

-- Assign to warehouse
ALTER WAREHOUSE WH_MEDIUM_ETL SET RESOURCE_MONITOR = monthly_quota;

-- Check resource monitor status
SHOW RESOURCE MONITORS;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-01-warehouse-optimization
bash validate.sh
```

**Expected Output**:
```
✅ Task 1: 3 warehouses created with correct configurations
✅ Task 2: Performance comparison documented (Large = 3.5x faster)
✅ Task 3: Auto-suspend verified (suspended after timeout)
✅ Task 4: Multi-cluster warehouse configured (1-3 clusters)
✅ Task 5: Credit monitoring queries working
✅ Task 6: 5 optimizations implemented (28% cost reduction)

🎉 Exercise 01 Complete! Estimated Monthly Savings: $840
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All warehouse creation and configuration commands
2. `performance-comparison.md` - Performance test results table
3. `cost-optimization-plan.md` - Document with 5 strategies and expected savings
4. Screenshot of WAREHOUSE_METERING_HISTORY query results

---

## Resources
- Snowflake Documentation: [Virtual Warehouses](https://docs.snowflake.com/en/user-guide/warehouses)
- Snowflake Documentation: [Credit Usage](https://docs.snowflake.com/en/user-guide/credits)
- Notebook: `notebooks/01-virtual-warehouses.sql`
- Diagram: `assets/diagrams/virtual-warehouse-scaling.mmd`
- Theory: `theory/concepts.md#virtual-warehouses`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 02: Zero-Copy Dev Environments (instant cloning)
- ✅ Exercise 03: Time Travel Recovery (disaster recovery)
- Review Module 17: Cost Optimization for cloud cost patterns
