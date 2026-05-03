"""
Exercise 05: SQL Analytics & Dashboards - Complete Solution
=========================================================

Build interactive SQL dashboards using Databricks SQL for business intelligence.

Author: Training Team
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise05-SQL-Analytics-Solution") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .getOrCreate()

print("=" * 70)
print("EXERCISE 05: SQL ANALYTICS & DASHBOARDS - SOLUTION")
print("=" * 70)

# ============================================================================
# TASK 1: Sample Data Generation
# ============================================================================
print("\n📊 TASK 1: Generate Sample Sales Data")
print("-" * 70)

def generate_sales_data(num_records=10000):
    """
    Generate realistic sales data for analysis with Pareto distribution
    and seasonal trends.
    """
    print(f"Generating {num_records:,} sales transactions...")

    # Define categories
    categories = ["Electronics", "Clothing", "Home", "Beauty", "Sports"]

    # Define regions
    regions = [
        "Northeast", "Southeast", "Midwest", "West", "Southwest",
        "Northwest", "Central", "Canada", "Mexico", "Europe"
    ]

    # Generate 50 products with base prices
    products = []
    for i in range(50):
        category = random.choice(categories)
        base_price = random.uniform(10, 500)
        products.append({
            "id": f"PROD_{i:03d}",
            "name": f"Product_{i}",
            "category": category,
            "base_price": base_price
        })

    # Generate 20 salespeople
    salespeople = []
    first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica",
                   "James", "Lisa", "Robert", "Maria", "William", "Jennifer",
                   "Richard", "Linda", "Joseph", "Patricia", "Thomas", "Nancy",
                   "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor",
                  "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson",
                  "White", "Harris"]

    for i in range(20):
        salespeople.append({
            "id": f"SALES_{i:03d}",
            "name": f"{first_names[i]} {last_names[i]}"
        })

    # Generate customer pool
    num_customers = 2500
    customers = []
    base_date = datetime(2025, 1, 1)

    for i in range(num_customers):
        # Random signup date over past 18 months
        signup_days_back = random.randint(0, 540)
        signup_date = base_date - timedelta(days=signup_days_back)

        customers.append({
            "id": f"CUST_{i:04d}",
            "signup_date": signup_date
        })

    # Generate transactions with Pareto distribution
    transactions = []

    # Pareto weights: top 20% products (10 products) get 60% of sales
    product_weights = [6] * 10 + [1] * 40

    for i in range(num_records):
        # Weighted random product selection (Pareto principle)
        product_idx = random.choices(range(50), weights=product_weights)[0]
        product = products[product_idx]

        # Random date within last 12 months
        days_offset = random.randint(0, 364)
        trans_date = base_date + timedelta(days=days_offset)

        # Seasonal adjustment
        month = trans_date.month
        if month == 12:  # December boost
            seasonal_multiplier = 1.20
        elif month == 8:  # August dip
            seasonal_multiplier = 0.90
        elif month in [11, 1]:  # Holiday season
            seasonal_multiplier = 1.10
        else:
            seasonal_multiplier = 1.0

        # Quantity and pricing
        quantity = random.randint(1, 10)
        unit_price = round(product["base_price"] * seasonal_multiplier, 2)

        # Discount (15% of transactions have discounts)
        discount_pct = random.uniform(5, 25) if random.random() < 0.15 else 0
        discount_amount = round(unit_price * quantity * (discount_pct / 100), 2)
        total_amount = round(unit_price * quantity, 2)
        net_revenue = round(total_amount - discount_amount, 2)

        # Regional distribution (40% from top 3 regions)
        if random.random() < 0.40:
            region = random.choice(["West", "Northeast", "Southeast"])
        else:
            region = random.choice(regions)

        # Random salesperson and customer
        salesperson = random.choice(salespeople)
        customer = random.choice(customers)

        transactions.append({
            "transaction_id": f"TXN_{i:06d}",
            "transaction_date": trans_date.date(),
            "product_id": product["id"],
            "product_name": product["name"],
            "product_category": product["category"],
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_pct": round(discount_pct, 2),
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "net_revenue": net_revenue,
            "region": region,
            "salesperson_id": salesperson["id"],
            "salesperson_name": salesperson["name"],
            "customer_id": customer["id"],
            "customer_signup_date": customer["signup_date"].date()
        })

    # Create DataFrame with proper schema
    schema = StructType([
        StructField("transaction_id", StringType(), False),
        StructField("transaction_date", DateType(), False),
        StructField("product_id", StringType(), False),
        StructField("product_name", StringType(), False),
        StructField("product_category", StringType(), False),
        StructField("quantity", IntegerType(), False),
        StructField("unit_price", DoubleType(), False),
        StructField("discount_pct", DoubleType(), False),
        StructField("discount_amount", DoubleType(), False),
        StructField("total_amount", DoubleType(), False),
        StructField("net_revenue", DoubleType(), False),
        StructField("region", StringType(), False),
        StructField("salesperson_id", StringType(), False),
        StructField("salesperson_name", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("customer_signup_date", DateType(), False)
    ])

    df = spark.createDataFrame(transactions, schema=schema)

    # Write as Delta table
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable("sales_transactions")

    # Calculate summary statistics
    total_revenue = sum(t["net_revenue"] for t in transactions)
    unique_products = len(set(t["product_id"] for t in transactions))
    unique_salespeople = len(set(t["salesperson_name"] for t in transactions))
    unique_regions = len(set(t["region"] for t in transactions))

    print(f"✅ Generated {num_records:,} transactions")
    print(f"   Total Revenue: ${total_revenue:,.2f}")
    print(f"   Unique Products: {unique_products}")
    print(f"   Unique Salespeople: {unique_salespeople}")
    print(f"   Unique Regions: {unique_regions}")
    print(f"   Date Range: {min(t['transaction_date'] for t in transactions)} to "
          f"{max(t['transaction_date'] for t in transactions)}")

    return df

# Generate the data
sales_df = generate_sales_data(10000)

# ============================================================================
# TASK 2: Basic Analytics Queries
# ============================================================================
print("\n📈 TASK 2: Basic Analytics Queries")
print("-" * 70)

# Query 1: Revenue by Region
print("\n1. Revenue by Region:")
query_revenue_by_region = """
SELECT
    region,
    COUNT(*) as transaction_count,
    SUM(net_revenue) as total_revenue,
    AVG(net_revenue) as avg_transaction_value,
    SUM(quantity) as total_units_sold
FROM sales_transactions
GROUP BY region
ORDER BY total_revenue DESC
"""
result_region = spark.sql(query_revenue_by_region)
result_region.show(10, truncate=False)

# Query 2: Monthly Trends
print("\n2. Monthly Sales Trends:")
query_monthly_trends = """
SELECT
    DATE_TRUNC('month', transaction_date) as sales_month,
    SUM(net_revenue) as monthly_revenue,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(*) as transaction_count,
    AVG(net_revenue) as avg_ticket_size
FROM sales_transactions
GROUP BY sales_month
ORDER BY sales_month
"""
result_monthly = spark.sql(query_monthly_trends)
result_monthly.show(12, truncate=False)

# Query 3: Top 10 Products
print("\n3. Top 10 Products by Revenue:")
query_top_products = """
SELECT
    product_name,
    product_category,
    COUNT(*) as times_sold,
    SUM(quantity) as units_sold,
    SUM(net_revenue) as total_revenue,
    AVG(unit_price) as avg_price
FROM sales_transactions
GROUP BY product_name, product_category
ORDER BY total_revenue DESC
LIMIT 10
"""
result_products = spark.sql(query_top_products)
result_products.show(10, truncate=False)

# Query 4: Salesperson Performance
print("\n4. Salesperson Performance:")
query_salesperson_performance = """
SELECT
    salesperson_name,
    COUNT(*) as deals_closed,
    SUM(net_revenue) as total_sales,
    AVG(net_revenue) as avg_deal_size,
    MAX(net_revenue) as largest_deal,
    COUNT(DISTINCT customer_id) as unique_customers
FROM sales_transactions
GROUP BY salesperson_name
ORDER BY total_sales DESC
"""
result_salespeople = spark.sql(query_salesperson_performance)
result_salespeople.show(10, truncate=False)

# ============================================================================
# TASK 3: Advanced SQL with Window Functions
# ============================================================================
print("\n🔍 TASK 3: Advanced SQL with Window Functions")
print("-" * 70)

# Query 1: Running Totals
print("\n1. Running Totals (First 20 days):")
query_running_totals = """
SELECT
    transaction_date,
    SUM(net_revenue) as daily_revenue,
    SUM(SUM(net_revenue)) OVER (
        ORDER BY transaction_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_revenue,
    AVG(SUM(net_revenue)) OVER (
        ORDER BY transaction_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day
FROM sales_transactions
GROUP BY transaction_date
ORDER BY transaction_date
LIMIT 20
"""
result_running = spark.sql(query_running_totals)
result_running.show(20, truncate=False)

# Query 2: Product Rankings by Category
print("\n2. Top 5 Products per Category:")
query_product_rankings = """
SELECT
    product_category,
    product_name,
    category_revenue,
    rank_in_category,
    ROUND(percentile_in_category * 100, 1) as percentile_pct
FROM (
    SELECT
        product_category,
        product_name,
        SUM(net_revenue) as category_revenue,
        RANK() OVER (
            PARTITION BY product_category
            ORDER BY SUM(net_revenue) DESC
        ) as rank_in_category,
        PERCENT_RANK() OVER (
            PARTITION BY product_category
            ORDER BY SUM(net_revenue) DESC
        ) as percentile_in_category
    FROM sales_transactions
    GROUP BY product_category, product_name
) ranked
WHERE rank_in_category <= 5
ORDER BY product_category, rank_in_category
"""
result_rankings = spark.sql(query_product_rankings)
result_rankings.show(25, truncate=False)

# Query 3: Month-over-Month Growth
print("\n3. Month-over-Month Growth:")
query_mom_growth = """
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', transaction_date) as month,
        SUM(net_revenue) as revenue
    FROM sales_transactions
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2) as revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month), 2) as prev_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) as mom_change,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month)) /
        LAG(revenue) OVER (ORDER BY month) * 100,
        2
    ) as mom_growth_pct
FROM monthly_sales
ORDER BY month
"""
result_mom = spark.sql(query_mom_growth)
result_mom.show(12, truncate=False)

# Query 4: Salesperson Quota Attainment
print("\n4. Salesperson Quota Attainment (Last 3 months):")
query_quota_attainment = """
WITH salesperson_quotas AS (
    SELECT salesperson_name, 50000 as monthly_quota
    FROM sales_transactions
    GROUP BY salesperson_name
),
monthly_performance AS (
    SELECT
        DATE_TRUNC('month', transaction_date) as month,
        salesperson_name,
        SUM(net_revenue) as actual_sales
    FROM sales_transactions
    GROUP BY month, salesperson_name
)
SELECT
    mp.month,
    mp.salesperson_name,
    ROUND(mp.actual_sales, 2) as actual_sales,
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
ORDER BY mp.month DESC, mp.actual_sales DESC
LIMIT 30
"""
result_quota = spark.sql(query_quota_attainment)
result_quota.show(30, truncate=False)

# ============================================================================
# TASK 4: Cohort Analysis
# ============================================================================
print("\n👥 TASK 4: Cohort Analysis")
print("-" * 70)

# Cohort Retention Analysis
print("\n1. Cohort Retention Analysis:")
query_cohort_retention = """
WITH customer_cohorts AS (
    SELECT
        customer_id,
        MIN(DATE_TRUNC('month', customer_signup_date)) as cohort_month
    FROM sales_transactions
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', t.transaction_date) as activity_month,
        COUNT(DISTINCT t.customer_id) as active_customers
    FROM customer_cohorts c
    JOIN sales_transactions t ON c.customer_id = t.customer_id
    WHERE t.transaction_date >= c.cohort_month
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
    CAST(MONTHS_BETWEEN(ca.activity_month, ca.cohort_month) AS INT) as months_since_signup,
    ca.active_customers,
    ROUND(ca.active_customers * 100.0 / cs.cohort_size, 1) as retention_rate_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
WHERE ca.cohort_month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL 12 MONTHS)
ORDER BY ca.cohort_month, months_since_signup
"""
result_cohort = spark.sql(query_cohort_retention)
result_cohort.show(50, truncate=False)

# ============================================================================
# TASK 5: Dashboard Visualizations
# ============================================================================
print("\n📊 TASK 6: Dashboard Visualization Queries")
print("-" * 70)

# Visualization 1: Weekly Revenue Trend (Line Chart)
print("\n1. Weekly Revenue Trend:")
query_revenue_trend = """
SELECT
    DATE_TRUNC('week', transaction_date) as week,
    SUM(net_revenue) as weekly_revenue,
    COUNT(*) as transaction_count,
    AVG(net_revenue) as avg_transaction
FROM sales_transactions
GROUP BY week
ORDER BY week
"""
result_trend = spark.sql(query_revenue_trend)
result_trend.show(10, truncate=False)

# Visualization 2: Category Breakdown (Pie Chart)
print("\n2. Revenue by Category:")
query_category_breakdown = """
SELECT
    product_category,
    SUM(net_revenue) as category_revenue,
    COUNT(*) as transaction_count,
    ROUND(SUM(net_revenue) * 100.0 / SUM(SUM(net_revenue)) OVER (), 1) as revenue_pct
FROM sales_transactions
GROUP BY product_category
ORDER BY category_revenue DESC
"""
result_category = spark.sql(query_category_breakdown)
result_category.show(truncate=False)

# Visualization 3: Salesperson Performance (Bar Chart)
print("\n3. Top 10 Salespeople:")
query_salesperson_viz = """
SELECT
    salesperson_name,
    SUM(net_revenue) as total_sales,
    COUNT(*) as deals_closed,
    AVG(net_revenue) as avg_deal_size
FROM sales_transactions
GROUP BY salesperson_name
ORDER BY total_sales DESC
LIMIT 10
"""
result_sales_viz = spark.sql(query_salesperson_viz)
result_sales_viz.show(10, truncate=False)

# Visualization 4: KPI Metrics
print("\n4. Key Performance Indicators:")
query_kpis = """
SELECT 'Total Revenue' as metric, CONCAT('$', ROUND(SUM(net_revenue)/1000000, 2), 'M') as value
FROM sales_transactions
UNION ALL
SELECT 'Total Sales', CAST(COUNT(*) AS STRING)
FROM sales_transactions
UNION ALL
SELECT 'Avg Sale Value', CONCAT('$', ROUND(AVG(net_revenue), 2))
FROM sales_transactions
UNION ALL
SELECT 'Active Salespeople', CAST(COUNT(DISTINCT salesperson_name) AS STRING)
FROM sales_transactions
UNION ALL
SELECT 'Avg Discount', CONCAT(ROUND(AVG(discount_pct), 1), '%')
FROM sales_transactions
"""
result_kpis = spark.sql(query_kpis)
result_kpis.show(truncate=False)

# Visualization 5: Regional Performance Matrix (PIVOT)
print("\n5. Category × Region Matrix (PIVOT):")
query_category_matrix = """
SELECT *
FROM (
    SELECT
        product_category,
        region,
        ROUND(SUM(net_revenue), 0) as revenue
    FROM sales_transactions
    GROUP BY product_category, region
)
PIVOT (
    SUM(revenue)
    FOR region IN ('West', 'Northeast', 'Southeast', 'Midwest', 'Southwest')
)
ORDER BY product_category
"""
result_matrix = spark.sql(query_category_matrix)
result_matrix.show(truncate=False)

# Visualization 6: Executive Dashboard Queries
print("\n6. Executive Summary - Current vs Previous Month:")
query_executive = """
WITH current_month AS (
    SELECT
        SUM(net_revenue) as current_revenue,
        COUNT(*) as current_transactions,
        COUNT(DISTINCT customer_id) as current_customers
    FROM sales_transactions
    WHERE DATE_TRUNC('month', transaction_date) =
          DATE_TRUNC('month', (SELECT MAX(transaction_date) FROM sales_transactions))
),
previous_month AS (
    SELECT
        SUM(net_revenue) as previous_revenue,
        COUNT(*) as previous_transactions,
        COUNT(DISTINCT customer_id) as previous_customers
    FROM sales_transactions
    WHERE DATE_TRUNC('month', transaction_date) =
          DATE_TRUNC('month', (SELECT MAX(transaction_date) FROM sales_transactions)) - INTERVAL 1 MONTH
)
SELECT
    ROUND(cm.current_revenue, 2) as current_month_revenue,
    ROUND(pm.previous_revenue, 2) as previous_month_revenue,
    ROUND((cm.current_revenue - pm.previous_revenue) / pm.previous_revenue * 100, 1) as revenue_growth_pct,
    cm.current_transactions,
    pm.previous_transactions,
    ROUND((cm.current_customers - pm.previous_customers) * 100.0 / pm.previous_customers, 1) as customer_growth_pct
FROM current_month cm, previous_month pm
"""
result_executive = spark.sql(query_executive)
result_executive.show(truncate=False)

# ============================================================================
# Performance Optimization
# ============================================================================
print("\n⚡ Performance Optimization")
print("-" * 70)

print("Optimizing table with ZORDER...")
spark.sql("OPTIMIZE sales_transactions ZORDER BY (transaction_date, region)")
print("✅ Table optimized for query performance")

# Display table statistics
print("\nTable Statistics:")
spark.sql("DESCRIBE EXTENDED sales_transactions").show(truncate=False)

print("\n" + "=" * 70)
print("✅ EXERCISE 05 COMPLETE!")
print("=" * 70)
print("\nKey Achievements:")
print("- ✅ Generated 10,000 realistic sales transactions")
print("- ✅ Implemented 15+ analytical SQL queries")
print("- ✅ Used window functions (RANK, LAG, SUM OVER, etc.)")
print("- ✅ Created cohort retention analysis")
print("- ✅ Built dashboard visualization queries")
print("- ✅ Optimized table for performance (ZORDER)")
print("\nNext: Create visualizations in Databricks SQL dashboards!")
