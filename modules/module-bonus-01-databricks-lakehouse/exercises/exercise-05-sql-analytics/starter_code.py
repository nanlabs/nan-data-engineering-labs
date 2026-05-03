"""
Exercise 05: SQL Analytics & Dashboards - Starter Code
=====================================================

Build interactive SQL dashboards using Databricks SQL for business intelligence.

Tasks:
1. Generate sample sales data (10,000 transactions)
2. Write basic analytical queries
3. Implement advanced SQL with window functions
4. Create parameterized queries with widgets
5. Build visualizations
6. Design executive dashboard

Estimated Time: 1.5 hours
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise05-SQL-Analytics") \
    .getOrCreate()

print("=" * 70)
print("EXERCISE 05: SQL ANALYTICS & DASHBOARDS")
print("=" * 70)

# ============================================================================
# TASK 1: Sample Data Generation
# ============================================================================
print("\n📊 TASK 1: Generate Sample Sales Data")
print("-" * 70)

def generate_sales_data(num_records=10000):
    """
    Generate realistic sales data for analysis.

    TODO: Implement data generation with:
    - 10,000 transactions
    - 50 products across 5 categories
    - 10 regions
    - 20 salespeople
    - Date range: Last 12 months
    - Pareto distribution (60% sales from top 20% products)
    - Seasonal trends (Dec +20%, Aug -10%)

    Schema:
    - transaction_id, transaction_date, product_id, product_name,
    - product_category, quantity, unit_price, total_amount,
    - region, salesperson_id, salesperson_name,
    - customer_id, customer_signup_date
    """

    # TODO: Define categories
    categories = []  # ["Electronics", "Clothing", "Home", "Beauty", "Sports"]

    # TODO: Define regions
    regions = []  # ["Northeast", "Southeast", "Midwest", "West", ...]

    # TODO: Generate 50 products with base prices
    products = []

    # TODO: Generate 20 salespeople
    salespeople = []

    # TODO: Generate 10,000 transactions with:
    # - Pareto distribution for products
    # - Seasonal trends
    # - Random dates over 12 months
    # - Customer data for cohort analysis

    transactions = []

    # TODO: Create DataFrame and save as Delta table
    # df = spark.createDataFrame(transactions)
    # df.write.format("delta").mode("overwrite").saveAsTable("sales_transactions")

    print("✅ TODO: Implement generate_sales_data()")
    return None

# TODO: Call the function
# generate_sales_data(10000)

# ============================================================================
# TASK 2: Basic Analytics Queries
# ============================================================================
print("\n📈 TASK 2: Basic Analytics Queries")
print("-" * 70)

# TODO: Query 1 - Revenue by Region
print("\n1. Revenue by Region:")
query_revenue_by_region = """
-- TODO: Write SQL query to calculate:
-- - COUNT(*) as transaction_count
-- - SUM(total_amount) as total_revenue
-- - AVG(total_amount) as avg_transaction_value
-- - SUM(quantity) as total_units_sold
-- GROUP BY region, ORDER BY total_revenue DESC
"""
# spark.sql(query_revenue_by_region).display()

# TODO: Query 2 - Monthly Trends
print("\n2. Monthly Sales Trends:")
query_monthly_trends = """
-- TODO: Write SQL query to calculate:
-- - DATE_TRUNC('month', transaction_date) as sales_month
-- - SUM(total_amount) as monthly_revenue
-- - COUNT(DISTINCT customer_id) as unique_customers
-- - COUNT(*) as transaction_count
-- - AVG(total_amount) as avg_ticket_size
-- GROUP BY sales_month, ORDER BY sales_month
"""
# spark.sql(query_monthly_trends).display()

# TODO: Query 3 - Top 10 Products
print("\n3. Top 10 Products:")
query_top_products = """
-- TODO: Write SQL query to show top 10 products by revenue
-- Include: product_name, product_category, times_sold,
--          units_sold, total_revenue, avg_price
"""
# spark.sql(query_top_products).display()

# TODO: Query 4 - Salesperson Performance
print("\n4. Salesperson Performance:")
query_salesperson_performance = """
-- TODO: Write SQL query for salesperson metrics:
-- - deals_closed, total_sales, avg_deal_size,
-- - largest_deal, unique_customers
-- ORDER BY total_sales DESC
"""
# spark.sql(query_salesperson_performance).display()

# ============================================================================
# TASK 3: Advanced SQL with Window Functions
# ============================================================================
print("\n🔍 TASK 3: Advanced SQL with Window Functions")
print("-" * 70)

# TODO: Query 1 - Running Totals
print("\n1. Running Totals (Cumulative Revenue):")
query_running_totals = """
-- TODO: Use SUM() OVER() for cumulative revenue
-- TODO: Use AVG() OVER() for 7-day moving average
-- OVER (ORDER BY transaction_date
--       ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
"""
# spark.sql(query_running_totals).display()

# TODO: Query 2 - Product Rankings by Category
print("\n2. Product Rankings by Category:")
query_product_rankings = """
-- TODO: Use RANK() OVER (PARTITION BY product_category ...)
-- TODO: Use PERCENT_RANK() OVER (...)
-- TODO: Use QUALIFY to show only top 5 per category
"""
# spark.sql(query_product_rankings).display()

# TODO: Query 3 - Month-over-Month Growth
print("\n3. Month-over-Month Growth:")
query_mom_growth = """
-- TODO: Use LAG() to get previous month's revenue
-- TODO: Calculate difference and percentage growth
"""
# spark.sql(query_mom_growth).display()

# TODO: Query 4 - Salesperson Quota Attainment
print("\n4. Salesperson Quota Attainment:")
query_quota_attainment = """
-- TODO: Use CTE for quotas ($50k/month per salesperson)
-- TODO: Calculate actual_sales vs quota
-- TODO: Use CASE to categorize: Exceeded, Met, Close, Below
"""
# spark.sql(query_quota_attainment).display()

# ============================================================================
# TASK 4: Cohort Analysis
# ============================================================================
print("\n👥 TASK 4: Cohort Analysis")
print("-" * 70)

# TODO: Cohort Retention Analysis
print("\n1. Cohort Retention:")
query_cohort_retention = """
-- TODO: Create CTE for customer_cohorts (signup month)
-- TODO: Join with transactions to get activity_month
-- TODO: Calculate months_since_signup (DATEDIFF)
-- TODO: Calculate retention_rate_pct
"""
# spark.sql(query_cohort_retention).display()

# TODO: Cohort Matrix (PIVOT)
print("\n2. Cohort Retention Matrix (PIVOT):")
query_cohort_matrix = """
-- TODO: Use PIVOT to reshape retention data
-- PIVOT (MAX(retention_rate_pct)
--        FOR months_since_signup IN (0, 1, 2, ..., 11))
"""
# spark.sql(query_cohort_matrix).display()

# ============================================================================
# TASK 5: Parameterized Queries with Widgets
# ============================================================================
print("\n🎛️ TASK 5: Parameterized Queries with Widgets")
print("-" * 70)

# TODO: Create parameter widgets
print("\nCreating parameter widgets...")
# dbutils.widgets.text("start_date", "2025-01-01", "Start Date")
# dbutils.widgets.text("end_date", "2025-12-31", "End Date")
# dbutils.widgets.multiselect("regions", "All",
#     ["All", "Northeast", "Southeast", "Midwest", "West", "Southwest"],
#     "Region")
# dbutils.widgets.dropdown("category", "All",
#     ["All", "Electronics", "Clothing", "Home", "Beauty", "Sports"],
#     "Category")
# dbutils.widgets.text("min_amount", "0", "Min Transaction ($)")

# TODO: Get parameter values
# start_date = dbutils.widgets.get("start_date")
# end_date = dbutils.widgets.get("end_date")
# selected_regions = dbutils.widgets.get("regions")
# selected_category = dbutils.widgets.get("category")
# min_amount = dbutils.widgets.get("min_amount")

# TODO: Parameterized query
query_parameterized = """
-- TODO: Use parameters in WHERE clause
-- WHERE transaction_date BETWEEN '${start_date}' AND '${end_date}'
-- AND ('${regions}' = 'All' OR region IN (${regions}))
-- AND ('${category}' = 'All' OR product_category = '${category}')
-- AND total_amount >= ${min_amount}
"""
# spark.sql(query_parameterized).display()

# ============================================================================
# TASK 6: Dashboard Visualizations
# ============================================================================
print("\n📊 TASK 6: Dashboard Creation")
print("-" * 70)

# TODO: Visualization 1 - Revenue Trend (Line Chart)
print("\n1. Revenue Trend (Line Chart):")
query_revenue_trend = """
-- TODO: Monthly revenue with MoM growth
-- Use DATE_TRUNC, SUM, LAG for growth calculation
"""
# spark.sql(query_revenue_trend).display()

# TODO: Visualization 2 - Top 10 Products (Bar Chart)
print("\n2. Top 10 Products (Bar Chart):")
query_top_products_viz = """
-- TODO: Product revenue for top 10, with category
"""
# spark.sql(query_top_products_viz).display()

# TODO: Visualization 3 - Regional Performance (Pie Chart)
print("\n3. Regional Performance (Pie Chart):")
query_regional_pie = """
-- TODO: Revenue and percentage by region
"""
# spark.sql(query_regional_pie).display()

# TODO: Visualization 4 - KPI Metrics
print("\n4. Key Performance Indicators:")
query_kpis = """
-- TODO: Use UNION ALL to create 5 KPI rows:
-- - Total Revenue
-- - Total Transactions
-- - Avg Transaction Value
-- - Active Salespeople
-- - Avg Discount %
"""
# spark.sql(query_kpis).display()

# TODO: Visualization 5 - Category Matrix (PIVOT)
print("\n5. Category × Region Matrix (PIVOT):")
query_category_matrix = """
-- TODO: PIVOT revenue by category (rows) and region (columns)
"""
# spark.sql(query_category_matrix).display()

# TODO: Visualization 6 - Salesperson Leaderboard
print("\n6. Salesperson Leaderboard:")
query_leaderboard = """
-- TODO: Top 10 salespeople with performance metrics
-- Include: name, sales, deals, avg_deal, quota_pct, status
"""
# spark.sql(query_leaderboard).display()

# ============================================================================
# TASK 7: Performance Optimization
# ============================================================================
print("\n⚡ Bonus: Performance Optimization")
print("-" * 70)

# TODO: Optimize table for query performance
# spark.sql("OPTIMIZE sales_transactions ZORDER BY (transaction_date, region)")

print("\n" + "=" * 70)
print("✅ Exercise 05 Starter Code Complete!")
print("=" * 70)
print("\nNext Steps:")
print("1. Implement all TODO sections")
print("2. Test each query independently")
print("3. Create visualizations in Databricks SQL")
print("4. Build executive dashboard")
print("5. Run validate.py to check your work")
