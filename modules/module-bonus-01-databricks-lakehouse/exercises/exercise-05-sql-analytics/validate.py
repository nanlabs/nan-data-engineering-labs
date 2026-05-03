"""
Exercise 05: SQL Analytics & Dashboards - Validation Script
=========================================================

Validates that all tasks have been completed correctly.

Run: python validate.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import sys

# Initialize Spark
spark = SparkSession.builder \
    .appName("Exercise05-Validation") \
    .getOrCreate()

print("=" * 70)
print("EXERCISE 05: SQL ANALYTICS & DASHBOARDS - VALIDATION")
print("=" * 70)

score = 0
max_score = 100
checks_passed = 0
total_checks = 0

def check(condition, message, points=10):
    """Helper function to validate conditions"""
    global score, max_score, checks_passed, total_checks
    total_checks += 1
    if condition:
        print(f"✅ {message}")
        score += points
        checks_passed += 1
        return True
    else:
        print(f"❌ {message}")
        return False

# ============================================================================
# TASK 1: Sample Data Validation
# ============================================================================
print("\n📊 TASK 1: Sample Data Generation")
print("-" * 70)

try:
    # Check table exists
    tables = [t.name for t in spark.catalog.listTables()]
    check("sales_transactions" in tables,
          "Table 'sales_transactions' exists", 10)

    if "sales_transactions" in tables:
        df = spark.table("sales_transactions")

        # Check row count
        row_count = df.count()
        check(row_count == 10000,
              f"Table has 10,000 rows (found: {row_count:,})", 10)

        # Check required columns
        required_cols = [
            "transaction_id", "transaction_date", "product_name",
            "product_category", "quantity", "unit_price", "total_amount",
            "region", "salesperson_name", "customer_id", "customer_signup_date"
        ]
        existing_cols = df.columns
        missing_cols = [col for col in required_cols if col not in existing_cols]
        check(len(missing_cols) == 0,
              f"All required columns present (missing: {missing_cols if missing_cols else 'none'})", 5)

        # Check unique products
        unique_products = df.select("product_name").distinct().count()
        check(40 <= unique_products <= 50,
              f"40-50 unique products (found: {unique_products})", 5)

        # Check unique regions
        unique_regions = df.select("region").distinct().count()
        check(8 <= unique_regions <= 12,
              f"8-12 unique regions (found: {unique_regions})", 5)

        # Check unique salespeople
        unique_salespeople = df.select("salesperson_name").distinct().count()
        check(18 <= unique_salespeople <= 22,
              f"18-22 unique salespeople (found: {unique_salespeople})", 5)

        # Check revenue range
        total_revenue = df.agg(sum("net_revenue").alias("total")).collect()[0][0] or \
                       df.agg(sum("total_amount").alias("total")).collect()[0][0]
        revenue_in_millions = total_revenue / 1_000_000
        check(2.0 <= revenue_in_millions <= 5.0,
              f"Total revenue $2M-$5M (found: ${revenue_in_millions:.2f}M)", 5)

except Exception as e:
    print(f"❌ Error validating Task 1: {str(e)}")

# ============================================================================
# TASK 2: Basic Analytics Queries
# ============================================================================
print("\n📈 TASK 2: Basic Analytics Queries")
print("-" * 70)

try:
    # Query 1: Revenue by Region
    result = spark.sql("""
        SELECT region, COUNT(*) as count, SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY region
        ORDER BY revenue DESC
    """)
    check(result.count() >= 8,
          "Revenue by region query works", 5)

    # Query 2: Monthly Trends
    result = spark.sql("""
        SELECT DATE_TRUNC('month', transaction_date) as month,
               SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY month
    """)
    check(result.count() >= 10,
          "Monthly trends query works", 5)

    # Query 3: Top Products
    result = spark.sql("""
        SELECT product_name, SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY product_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    check(result.count() == 10,
          "Top 10 products query works", 5)

    # Query 4: Salesperson Performance
    result = spark.sql("""
        SELECT salesperson_name, COUNT(*) as deals,
               SUM(COALESCE(net_revenue, total_amount)) as sales
        FROM sales_transactions
        GROUP BY salesperson_name
    """)
    check(result.count() >= 18,
          "Salesperson performance query works", 5)

except Exception as e:
    print(f"❌ Error validating Task 2: {str(e)}")

# ============================================================================
# TASK 3: Advanced SQL with Window Functions
# ============================================================================
print("\n🔍 TASK 3: Advanced SQL with Window Functions")
print("-" * 70)

try:
    # Test running totals
    result = spark.sql("""
        SELECT transaction_date,
               SUM(COALESCE(net_revenue, total_amount)) as daily,
               SUM(SUM(COALESCE(net_revenue, total_amount))) OVER (
                   ORDER BY transaction_date
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) as cumulative
        FROM sales_transactions
        GROUP BY transaction_date
        ORDER BY transaction_date
        LIMIT 10
    """)
    check(result.count() == 10 and "cumulative" in result.columns,
          "Running totals with window functions work", 10)

    # Test RANK within partition
    result = spark.sql("""
        SELECT product_category, product_name,
               RANK() OVER (PARTITION BY product_category
                           ORDER BY SUM(COALESCE(net_revenue, total_amount)) DESC) as rank
        FROM sales_transactions
        GROUP BY product_category, product_name
    """)
    check(result.count() > 0 and "rank" in result.columns,
          "RANK with PARTITION BY works", 10)

    # Test LAG function
    result = spark.sql("""
        WITH monthly AS (
            SELECT DATE_TRUNC('month', transaction_date) as month,
                   SUM(COALESCE(net_revenue, total_amount)) as revenue
            FROM sales_transactions
            GROUP BY month
        )
        SELECT month, revenue,
               LAG(revenue) OVER (ORDER BY month) as prev_month
        FROM monthly
    """)
    check(result.count() > 0 and "prev_month" in result.columns,
          "LAG function for MoM growth works", 10)

except Exception as e:
    print(f"❌ Error validating Task 3: {str(e)}")

# ============================================================================
# TASK 4: Cohort Analysis (Optional Check)
# ============================================================================
print("\n👥 TASK 4: Cohort Analysis")
print("-" * 70)

try:
    # Test cohort retention query
    result = spark.sql("""
        WITH customer_cohorts AS (
            SELECT customer_id,
                   MIN(DATE_TRUNC('month', customer_signup_date)) as cohort_month
            FROM sales_transactions
            GROUP BY customer_id
        )
        SELECT cohort_month, COUNT(DISTINCT customer_id) as cohort_size
        FROM customer_cohorts
        GROUP BY cohort_month
    """)
    check(result.count() > 0,
          "Cohort analysis query works", 10)

except Exception as e:
    print(f"❌ Error validating Task 4: {str(e)}")

# ============================================================================
# TASK 6: Dashboard Visualization Queries
# ============================================================================
print("\n📊 TASK 6: Dashboard Visualization Queries")
print("-" * 70)

try:
    # Weekly trend
    result = spark.sql("""
        SELECT DATE_TRUNC('week', transaction_date) as week,
               SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY week
    """)
    check(result.count() >= 50,
          "Weekly revenue trend query works", 5)

    # Category breakdown
    result = spark.sql("""
        SELECT product_category,
               SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY product_category
    """)
    check(result.count() == 5,
          "Category breakdown query works", 5)

    # KPI query
    result = spark.sql("""
        SELECT 'Total Revenue' as metric,
               CONCAT('$', ROUND(SUM(COALESCE(net_revenue, total_amount))/1000000, 2), 'M') as value
        FROM sales_transactions
    """)
    check(result.count() > 0,
          "KPI metrics query works", 5)

    # Regional matrix (simplified check)
    result = spark.sql("""
        SELECT product_category, region,
               SUM(COALESCE(net_revenue, total_amount)) as revenue
        FROM sales_transactions
        GROUP BY product_category, region
    """)
    check(result.count() >= 25,
          "Category × Region matrix data available", 5)

except Exception as e:
    print(f"❌ Error validating Task 6: {str(e)}")

# ============================================================================
# Final Report
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print(f"Checks Passed: {checks_passed}/{total_checks}")
print(f"Total Score: {score}/{max_score}")

if score >= 90:
    print("🎉 EXCELLENT! Exercise completed successfully!")
elif score >= 70:
    print("✅ GOOD! Most requirements met. Review failed checks.")
elif score >= 50:
    print("⚠️  PARTIAL: Significant work remaining. Review all tasks.")
else:
    print("❌ INCOMPLETE: Please complete all tasks and try again.")

print("\n" + "=" * 70)

# Exit with appropriate code
sys.exit(0 if score >= 70 else 1)
