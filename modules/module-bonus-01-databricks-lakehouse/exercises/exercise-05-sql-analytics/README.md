# Exercise 05: SQL Analytics & Dashboards

## Overview
Build interactive SQL dashboards using Databricks SQL for business intelligence, featuring parameterized queries, advanced window functions, cohort analysis, and rich visualizations.

**Estimated Time**: 1.5 hours
**Difficulty**: ⭐⭐⭐ Intermediate
**Prerequisites**: Basic SQL knowledge, Exercise 02 (ETL Pipelines)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Write complex analytical SQL queries with window functions
- Create parameterized queries with dynamic filters
- Build cohort analysis and retention reports
- Design effective data visualizations (charts, KPIs, tables)
- Construct executive dashboards with multiple visualizations
- Use PIVOT and UNPIVOT for data reshaping
- Optimize SQL queries for dashboard performance

---

## Scenario
You're the analytics lead for an e-commerce company. The executive team needs dashboards to answer:
1. What are our top-performing products and regions?
2. How do sales trends look month-over-month?
3. Which salespeople are exceeding quota?
4. What's our customer retention by cohort?
5. How does product performance vary by region?

Build a comprehensive SQL analytics solution with interactive dashboards that update daily.

**Data**: 10,000 sales transactions across 50 products, 10 regions, 20 salespeople, spanning 12 months.

---

## Requirements

### Task 1: Sample Data Generation (15 min)
Generate realistic sales data for analysis.

**Requirements**:
- Create `sales_transactions` table with 10,000 records
- Date range: Last 12 months
- 50 unique products across 5 categories
- 10 regions (US regions + international)
- 20 salespeople with quotas

**Schema**:
```
transaction_id: STRING
transaction_date: DATE
product_id: STRING
product_name: STRING
product_category: STRING (Electronics, Clothing, Home, Beauty, Sports)
quantity: INT (1-10)
unit_price: DOUBLE ($10-$500)
total_amount: DOUBLE (quantity * unit_price)
region: STRING (Northeast, Southeast, Midwest, West, Southwest, etc.)
salesperson_id: STRING
salesperson_name: STRING
customer_id: STRING
customer_signup_date: DATE (for cohort analysis)
```

**Data Distribution**:
- 60% of sales from top 20% of products (Pareto principle)
- 40% of sales from top 3 regions
- Seasonal trends (December 20% higher, August 10% lower)
- 15% outlier transactions (very high value)

**Success Criteria**:
- ✅ Table has exactly 10,000 transactions
- ✅ Data spans 12 months evenly
- ✅ 50 unique products, 20 salespeople
- ✅ Realistic distributions (Pareto, seasonal trends)
- ✅ Total revenue between $2M-$5M

---

### Task 2: Basic Analytics Queries (20 min)
Write fundamental analytical queries for business insights.

**Query 1: Revenue by Region**
```sql
SELECT
  region,
  COUNT(*) as transaction_count,
  SUM(total_amount) as total_revenue,
  AVG(total_amount) as avg_transaction_value,
  SUM(quantity) as total_units_sold
FROM sales_transactions
GROUP BY region
ORDER BY total_revenue DESC;
```

**Query 2: Monthly Trends**
```sql
SELECT
  DATE_TRUNC('month', transaction_date) as sales_month,
  SUM(total_amount) as monthly_revenue,
  COUNT(DISTINCT customer_id) as unique_customers,
  COUNT(*) as transaction_count,
  AVG(total_amount) as avg_ticket_size
FROM sales_transactions
GROUP BY sales_month
ORDER BY sales_month;
```

**Query 3: Top 10 Products**
```sql
SELECT
  product_name,
  product_category,
  COUNT(*) as times_sold,
  SUM(quantity) as units_sold,
  SUM(total_amount) as total_revenue,
  AVG(unit_price) as avg_price
FROM sales_transactions
GROUP BY product_name, product_category
ORDER BY total_revenue DESC
LIMIT 10;
```

**Query 4: Salesperson Performance**
```sql
SELECT
  salesperson_name,
  COUNT(*) as deals_closed,
  SUM(total_amount) as total_sales,
  AVG(total_amount) as avg_deal_size,
  MAX(total_amount) as largest_deal,
  COUNT(DISTINCT customer_id) as unique_customers
FROM sales_transactions
GROUP BY salesperson_name
ORDER BY total_sales DESC;
```

**Success Criteria**:
- ✅ All 4 queries execute successfully
- ✅ Results are sorted appropriately
- ✅ Aggregations mathematically correct
- ✅ Query performance < 2 seconds each

---

### Task 3: Advanced SQL with Window Functions (25 min)
Implement sophisticated analytics using window functions.

**Query 1: Running Totals (Cumulative Revenue)**
```sql
SELECT
  transaction_date,
  total_amount,
  SUM(total_amount) OVER (
    ORDER BY transaction_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_revenue,
  AVG(total_amount) OVER (
    ORDER BY transaction_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as moving_avg_7day
FROM sales_transactions
ORDER BY transaction_date;
```

**Query 2: Ranking Products by Category**
```sql
SELECT
  product_category,
  product_name,
  SUM(total_amount) as category_revenue,
  RANK() OVER (
    PARTITION BY product_category
    ORDER BY SUM(total_amount) DESC
  ) as rank_in_category,
  PERCENT_RANK() OVER (
    PARTITION BY product_category
    ORDER BY SUM(total_amount) DESC
  ) as percentile_in_category
FROM sales_transactions
GROUP BY product_category, product_name
QUALIFY rank_in_category <= 5;  -- Top 5 per category
```

**Query 3: Month-over-Month Growth**
```sql
WITH monthly_sales AS (
  SELECT
    DATE_TRUNC('month', transaction_date) as month,
    SUM(total_amount) as revenue
  FROM sales_transactions
  GROUP BY month
)
SELECT
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
  revenue - LAG(revenue) OVER (ORDER BY month) as mom_change,
  ROUND(
    (revenue - LAG(revenue) OVER (ORDER BY month)) /
    LAG(revenue) OVER (ORDER BY month) * 100,
    2
  ) as mom_growth_pct
FROM monthly_sales
ORDER BY month;
```

**Query 4: Salesperson Quota Attainment**
```sql
WITH salesperson_quotas AS (
  SELECT salesperson_name, 50000 as monthly_quota  -- $50k/month
  FROM sales_transactions
  GROUP BY salesperson_name
),
monthly_performance AS (
  SELECT
    DATE_TRUNC('month', transaction_date) as month,
    salesperson_name,
    SUM(total_amount) as actual_sales
  FROM sales_transactions
  GROUP BY month, salesperson_name
)
SELECT
  mp.month,
  mp.salesperson_name,
  mp.actual_sales,
  sq.monthly_quota,
  ROUND(mp.actual_sales / sq.monthly_quota * 100, 1) as quota_attainment_pct,
  CASE
    WHEN mp.actual_sales >= sq.monthly_quota * 1.2 THEN 'Exceeded'
    WHEN mp.actual_sales >= sq.monthly_quota THEN 'Met'
    WHEN mp.actual_sales >= sq.monthly_quota * 0.8 THEN 'Close'
    ELSE 'Below'
  END as performance_status
FROM monthly_performance mp
JOIN salesperson_quotas sq ON mp.salesperson_name = sq.salesperson_name
ORDER BY mp.month DESC, mp.actual_sales DESC;
```

**Success Criteria**:
- ✅ Running totals increase monotonically
- ✅ Rankings correct within each partition
- ✅ MoM growth percentages calculated correctly
- ✅ QUALIFY clause filters correctly (top 5 per category)
- ✅ LAG function works across month boundaries

---

### Task 4: Cohort Analysis (25 min)
Analyze customer retention by signup cohort.

**Requirements**:
- Group customers by signup month (cohort)
- Track purchases in subsequent months (Month 0, 1, 2, ... 11)
- Calculate retention rate per cohort
- Create cohort retention matrix

**Cohort Analysis Query**:
```sql
WITH customer_cohorts AS (
  SELECT
    customer_id,
    DATE_TRUNC('month', customer_signup_date) as cohort_month
  FROM sales_transactions
  GROUP BY customer_id, cohort_month
),
cohort_activity AS (
  SELECT
    c.cohort_month,
    DATE_TRUNC('month', t.transaction_date) as activity_month,
    COUNT(DISTINCT t.customer_id) as active_customers
  FROM customer_cohorts c
  JOIN sales_transactions t ON c.customer_id = t.customer_id
  GROUP BY c.cohort_month, activity_month
),
cohort_sizes AS (
  SELECT
    cohort_month,
    COUNT(DISTINCT customer_id) as cohort_size
  FROM customer_cohorts
  GROUP BY cohort_month
)
SELECT
  ca.cohort_month,
  cs.cohort_size,
  ca.activity_month,
  DATEDIFF(MONTH, ca.cohort_month, ca.activity_month) as months_since_signup,
  ca.active_customers,
  ROUND(ca.active_customers / cs.cohort_size * 100, 1) as retention_rate_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
ORDER BY ca.cohort_month, months_since_signup;
```

**Cohort Matrix (PIVOT)**:
```sql
SELECT * FROM (
  SELECT
    cohort_month,
    months_since_signup,
    retention_rate_pct
  FROM cohort_retention  -- Previous query result
)
PIVOT (
  MAX(retention_rate_pct)
  FOR months_since_signup IN (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
)
ORDER BY cohort_month;
```

**Success Criteria**:
- ✅ Cohorts grouped by signup month
- ✅ Retention tracked for 12 months
- ✅ Month 0 retention = 100% (by definition)
- ✅ Retention decreases over time (realistic pattern)
- ✅ PIVOT table creates readable matrix

---

### Task 5: Parameterized Queries with Widgets (20 min)
Create dynamic queries that respond to user input.

**Requirements**:
- Create 4 input parameters (widgets):
  - Date range (start_date, end_date)
  - Region filter (multi-select)
  - Product category filter
  - Minimum transaction value

**Databricks Widgets**:
```python
# Create widgets
dbutils.widgets.text("start_date", "2025-01-01", "Start Date")
dbutils.widgets.text("end_date", "2025-12-31", "End Date")
dbutils.widgets.multiselect("regions", "All",
  ["All", "Northeast", "Southeast", "Midwest", "West", "Southwest"], "Region")
dbutils.widgets.dropdown("category", "All",
  ["All", "Electronics", "Clothing", "Home", "Beauty", "Sports"], "Category")
dbutils.widgets.text("min_amount", "0", "Min Transaction ($)")

# Get parameter values
start_date = dbutils.widgets.get("start_date")
end_date = dbutils.widgets.get("end_date")
selected_regions = dbutils.widgets.get("regions")
selected_category = dbutils.widgets.get("category")
min_amount = float(dbutils.widgets.get("min_amount"))
```

**Parameterized Query**:
```sql
SELECT
  region,
  product_category,
  COUNT(*) as transaction_count,
  SUM(total_amount) as revenue,
  AVG(total_amount) as avg_transaction
FROM sales_transactions
WHERE
  transaction_date BETWEEN '${start_date}' AND '${end_date}'
  AND (
    '${regions}' = 'All'
    OR region IN (${regions})  -- Handle multi-select
  )
  AND (
    '${category}' = 'All'
    OR product_category = '${category}'
  )
  AND total_amount >= ${min_amount}
GROUP BY region, product_category
ORDER BY revenue DESC;
```

**Dynamic Filtering**:
- Test with different parameter combinations
- Verify "All" option works (shows all data)
- Ensure filters combine correctly (AND logic)

**Success Criteria**:
- ✅ All 4 widgets created and visible
- ✅ Query updates when parameters change
- ✅ "All" option bypasses filter
- ✅ Multi-select works for regions
- ✅ Date range filter works correctly

---

### Task 6: Dashboard Creation (20 min)
Build an executive dashboard with multiple visualizations.

**Requirements**:
Create dashboard with 6 visualizations answering key business questions.

**Visualization 1: Revenue Trend (Line Chart)**
- X-axis: Month
- Y-axis: Revenue ($)
- Line: Monthly revenue
- Add MoM growth % as data labels

**Visualization 2: Top 10 Products (Bar Chart)**
- X-axis: Product name
- Y-axis: Revenue ($)
- Color by category
- Horizontal layout

**Visualization 3: Regional Performance (Pie Chart)**
- Slices: Regions
- Values: Revenue percentage
- Show percentage labels
- Legend on right

**Visualization 4: Key Metrics (KPI Cards)**
- Total Revenue: `$3.2M` (large number)
- Total Transactions: `10,000`
- Avg Transaction: `$320`
- Unique Customers: `2,450`
- Format with colors (green if above target)

**Visualization 5: Category Matrix (Pivot Table)**
- Rows: Product category
- Columns: Region
- Values: Revenue
- Show row and column totals
- Conditional formatting (heatmap)

**Visualization 6: Salesperson Leaderboard (Table)**
- Columns: Name, Sales, Deals, Avg Deal, Quota %, Status
- Sort by Sales descending
- Top 10 only
- Color-code quota attainment:
  - Green: ≥ 100%
  - Yellow: 80-99%
  - Red: < 80%

**Dashboard Layout**:
```
+----------------------------------+----------------------------------+
|     KPI Cards (4 metrics)        |    Revenue Trend (Line Chart)    |
+----------------------------------+----------------------------------+
| Top Products (Bar Chart)         | Regional Performance (Pie)       |
+----------------------------------+----------------------------------+
|  Category Matrix (Pivot Table)   | Salesperson Leaderboard (Table)  |
+----------------------------------+----------------------------------+
```

**Interactivity**:
- Add filters (date range, region, category)
- Enable drill-down on charts (click to filter)
- Auto-refresh daily

**Success Criteria**:
- ✅ Dashboard contains all 6 visualizations
- ✅ Charts render correctly with proper labels
- ✅ KPI cards show large numbers prominently
- ✅ Filters affect all visualizations
- ✅ Colors and formatting enhance readability
- ✅ Dashboard answers all 5 business questions from scenario

---

## Hints

<details>
<summary>Hint 1: Generating Realistic Sales Data</summary>

```python
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random

# Products with Pareto distribution
products = [(f"Product_{i}", random.choice(["Electronics", "Clothing", "Home", "Beauty", "Sports"]),
             random.uniform(10, 500)) for i in range(50)]

# Generate 10,000 transactions
transactions = []
base_date = datetime(2025, 1, 1)

for i in range(10000):
    # Weighted random product (top 20% products get 60% of sales)
    product_idx = random.choices(range(50), weights=[100]*10 + [20]*40)[0]
    product_name, category, base_price = products[product_idx]

    # Random date with seasonal trend
    days_offset = random.randint(0, 365)
    trans_date = base_date + timedelta(days=days_offset)
    month = trans_date.month
    seasonal_multiplier = 1.2 if month == 12 else (0.9 if month == 8 else 1.0)

    transactions.append({
        "transaction_id": f"TXN_{i:05d}",
        "transaction_date": trans_date,
        "product_name": product_name,
        "product_category": category,
        "quantity": random.randint(1, 10),
        "unit_price": base_price * seasonal_multiplier,
        # ... more fields
    })

df = spark.createDataFrame(transactions)
df.write.format("delta").mode("overwrite").saveAsTable("sales_transactions")
```
</details>

<details>
<summary>Hint 2: Window Functions for Rankings</summary>

```sql
-- Multiple window functions in one query
SELECT
  product_name,
  category,
  revenue,
  -- Rank within category
  RANK() OVER (PARTITION BY category ORDER BY revenue DESC) as rank_in_category,
  -- Running total
  SUM(revenue) OVER (PARTITION BY category ORDER BY revenue DESC) as running_total,
  -- Percent of category total
  revenue / SUM(revenue) OVER (PARTITION BY category) * 100 as pct_of_category,
  -- Lag (previous product in ranking)
  LAG(revenue) OVER (PARTITION BY category ORDER BY revenue DESC) as next_highest_revenue
FROM product_revenue
QUALIFY rank_in_category <= 10;
```
</details>

<details>
<summary>Hint 3: Creating Parameter Widgets and Dynamic Queries</summary>

```python
# Python: Create widgets
dbutils.widgets.removeAll()  # Clear existing
dbutils.widgets.text("start_date", "2025-01-01")
dbutils.widgets.text("end_date", "2025-12-31")
dbutils.widgets.multiselect("regions", "All",
    ["All", "Northeast", "Southeast", "Midwest", "West"])

# Get values
start = dbutils.widgets.get("start_date")
end = dbutils.widgets.get("end_date")
regions = dbutils.widgets.get("regions")

# SQL: Use in query
query = f"""
SELECT * FROM sales_transactions
WHERE transaction_date BETWEEN '{start}' AND '{end}'
  AND ('{regions}' = 'All' OR region = '{regions}')
"""
spark.sql(query).display()
```
</details>

<details>
<summary>Hint 4: Cohort Retention Analysis</summary>

```sql
-- Simplified cohort retention
WITH cohorts AS (
  SELECT
    customer_id,
    MIN(DATE_TRUNC('month', transaction_date)) as cohort_month
  FROM sales_transactions
  GROUP BY customer_id
)
SELECT
  c.cohort_month,
  DATE_TRUNC('month', t.transaction_date) as activity_month,
  DATEDIFF(MONTH, c.cohort_month, DATE_TRUNC('month', t.transaction_date)) as period,
  COUNT(DISTINCT t.customer_id) as customers,
  COUNT(DISTINCT t.customer_id) /
    MAX(COUNT(DISTINCT c.customer_id)) OVER (PARTITION BY c.cohort_month) * 100 as retention_pct
FROM cohorts c
JOIN sales_transactions t ON c.customer_id = t.customer_id
GROUP BY c.cohort_month, activity_month
ORDER BY c.cohort_month, period;
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-05-sql-analytics
python validate.py
```

**Expected Output**:
```
✅ Task 1: Sample data generated (10,000 transactions, $3.45M revenue)
   - 50 products, 20 salespeople, 10 regions
   - Date range: 2025-01-01 to 2025-12-31
   - Seasonal trend detected (Dec: +18.2%, Aug: -9.7%)
✅ Task 2: Basic queries (4/4 executed successfully)
   - Top region: West ($687k revenue)
   - Best month: December 2025 ($342k)
   - Top product: Product_7 ($89k revenue)
✅ Task 3: Advanced SQL (4/4 window function queries working)
   - Running total reaches $3.45M
   - MoM growth: avg +8.3% (range: -15% to +25%)
   - Quota attainment: 12/20 salespeople met quota
✅ Task 4: Cohort analysis (retention matrix generated)
   - Month 0: 100% retention
   - Month 6: 42.3% retention
   - Month 12: 28.7% retention
✅ Task 5: Parameterized queries (4 widgets, dynamic filtering works)
   - Tested 5 parameter combinations
✅ Task 6: Dashboard created (6 visualizations, answers 5 business questions)
   - All charts render correctly
   - Filters propagate to all visualizations

🎉 Exercise 05 Complete! Total Score: 100/100
```

---

## Deliverables
Submit the following:
1. `solution.sql` - All SQL queries from Tasks 1-5
2. Dashboard screenshot (with all 6 visualizations)
3. Cohort retention matrix (exported to CSV or screenshot)
4. Business insights document (3-5 key findings from data)

---

## Resources
- [Databricks SQL Guide](https://docs.databricks.com/sql/index.html)
- [SQL Window Functions](https://docs.databricks.com/sql/language-manual/sql-ref-functions-builtin.html#window-functions)
- [SQL Widgets (Parameters)](https://docs.databricks.com/notebooks/widgets.html)
- Notebook: `notebooks/05-sql-analytics.sql`
- Sample dashboard template: `assets/templates/executive-dashboard.json`

---

## Next Steps
After completing this exercise:
- ✅ Exercise 06: ML with MLflow
- Explore Databricks SQL Warehouses for production BI
- Review Module 15: Real-Time Analytics for streaming dashboards
- Consider Tableau/Power BI integration with Databricks
