# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 05: SQL Analytics & Dashboards
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC - Use Databricks SQL for analytics
# MAGIC - Create parameterized queries
# MAGIC - Build visualizations
# MAGIC - Design dashboards
# MAGIC - Schedule queries and alerts
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - SQL Warehouse created
# MAGIC - Data from previous notebooks
# MAGIC
# MAGIC ## Estimated Time: 45-60 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *
import random
from datetime import datetime, timedelta

# Create sample sales data for analytics
database_name = "training_sql_analytics"
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
spark.sql(f"USE {database_name}")

print(f"✅ Using database: {database_name}")

# COMMAND ----------

# Generate comprehensive sales data
print("Generating sample sales data...")

def generate_sales_data(num_records=10000):
    """Generate realistic sales data."""
    sales = []
    base_date = datetime(2024, 1, 1)

    products = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headphones", "Webcam"]
    categories = ["Electronics", "Electronics", "Electronics", "Electronics", "Accessories", "Accessories", "Accessories", "Accessories"]
    regions = ["North", "South", "East", "West"]
    salespeople = ["Alice", "Bob", "Carol", "David", "Emma", "Frank"]

    for i in range(num_records):
        sale_date = base_date + timedelta(days=random.randint(0, 365))
        product_idx = random.randint(0, len(products) - 1)

        sales.append({
            "sale_id": i + 1,
            "sale_date": sale_date.strftime("%Y-%m-%d"),
            "sale_timestamp": sale_date.strftime("%Y-%m-%d %H:%M:%S"),
            "product": products[product_idx],
            "category": categories[product_idx],
            "quantity": random.randint(1, 10),
            "unit_price": round(random.uniform(20, 2000), 2),
            "region": random.choice(regions),
            "salesperson": random.choice(salespeople),
            "customer_segment": random.choice(["Enterprise", "SMB", "Consumer"]),
            "discount_pct": round(random.uniform(0, 0.3), 2)
        })

    return sales

sales_data = generate_sales_data(10000)

# Create DataFrame
sales_df = spark.createDataFrame(sales_data)

# Add calculated columns
sales_df = sales_df \
    .withColumn("total_price", col("quantity") * col("unit_price")) \
    .withColumn("discount_amount", col("total_price") * col("discount_pct")) \
    .withColumn("net_revenue", col("total_price") - col("discount_amount")) \
    .withColumn("year", year(col("sale_date"))) \
    .withColumn("month", month(col("sale_date"))) \
    .withColumn("quarter", quarter(col("sale_date")))

# Save as Delta table
sales_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("sales_fact")

print(f"✅ Generated {sales_df.count():,} sales records")
display(sales_df.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Basic SQL Analytics

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Total revenue by region
# MAGIC SELECT
# MAGIC   region,
# MAGIC   COUNT(*) as total_sales,
# MAGIC   SUM(quantity) as total_units,
# MAGIC   ROUND(SUM(net_revenue), 2) as total_revenue,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_revenue_per_sale,
# MAGIC   ROUND(AVG(discount_pct) * 100, 2) as avg_discount_pct
# MAGIC FROM sales_fact
# MAGIC GROUP BY region
# MAGIC ORDER BY total_revenue DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Monthly revenue trend
# MAGIC SELECT
# MAGIC   DATE_TRUNC('month', sale_date) as month,
# MAGIC   COUNT(DISTINCT salesperson) as active_salespeople,
# MAGIC   COUNT(*) as total_sales,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_sale_value
# MAGIC FROM sales_fact
# MAGIC GROUP BY DATE_TRUNC('month', sale_date)
# MAGIC ORDER BY month;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Top products by revenue
# MAGIC SELECT
# MAGIC   product,
# MAGIC   category,
# MAGIC   COUNT(*) as units_sold,
# MAGIC   ROUND(SUM(net_revenue), 2) as total_revenue,
# MAGIC   ROUND(AVG(unit_price), 2) as avg_price,
# MAGIC   ROUND(AVG(discount_pct) * 100, 2) as avg_discount
# MAGIC FROM sales_fact
# MAGIC GROUP BY product, category
# MAGIC ORDER BY total_revenue DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Advanced SQL Patterns

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Window functions: Running totals and ranks
# MAGIC SELECT
# MAGIC   salesperson,
# MAGIC   DATE_TRUNC('month', sale_date) as month,
# MAGIC   COUNT(*) as monthly_sales,
# MAGIC   ROUND(SUM(net_revenue), 2) as monthly_revenue,
# MAGIC   ROUND(SUM(SUM(net_revenue)) OVER (
# MAGIC     PARTITION BY salesperson
# MAGIC     ORDER BY DATE_TRUNC('month', sale_date)
# MAGIC     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC   ), 2) as running_total,
# MAGIC   RANK() OVER (
# MAGIC     PARTITION BY DATE_TRUNC('month', sale_date)
# MAGIC     ORDER BY SUM(net_revenue) DESC
# MAGIC   ) as monthly_rank
# MAGIC FROM sales_fact
# MAGIC GROUP BY salesperson, DATE_TRUNC('month', sale_date)
# MAGIC ORDER BY salesperson, month;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Cohort analysis: Customer segments over time
# MAGIC SELECT
# MAGIC   customer_segment,
# MAGIC   quarter,
# MAGIC   COUNT(*) as sales_count,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_sale,
# MAGIC   -- Percentage of total revenue
# MAGIC   ROUND(SUM(net_revenue) * 100.0 / SUM(SUM(net_revenue)) OVER (PARTITION BY quarter), 2) as pct_of_total
# MAGIC FROM sales_fact
# MAGIC GROUP BY customer_segment, quarter
# MAGIC ORDER BY quarter, revenue DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Pivot table: Revenue by region and category
# MAGIC SELECT * FROM (
# MAGIC   SELECT
# MAGIC     region,
# MAGIC     category,
# MAGIC     net_revenue
# MAGIC   FROM sales_fact
# MAGIC )
# MAGIC PIVOT (
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue
# MAGIC   FOR category IN ('Electronics', 'Accessories')
# MAGIC )
# MAGIC ORDER BY region;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Parameterized Queries (Widgets)

# COMMAND ----------

# Create widgets for interactive parameters
dbutils.widgets.text("start_date", "2024-01-01", "Start Date")
dbutils.widgets.text("end_date", "2024-12-31", "End Date")
dbutils.widgets.dropdown("region", "All", ["All", "North", "South", "East", "West"], "Region")
dbutils.widgets.dropdown("category", "All", ["All", "Electronics", "Accessories"], "Category")

print("✅ Widgets created")
print("\nCurrent parameters:")
print(f"  Start Date: {dbutils.widgets.get('start_date')}")
print(f"  End Date: {dbutils.widgets.get('end_date')}")
print(f"  Region: {dbutils.widgets.get('region')}")
print(f"  Category: {dbutils.widgets.get('category')}")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Parameterized query using widgets
# MAGIC SELECT
# MAGIC   sale_date,
# MAGIC   region,
# MAGIC   category,
# MAGIC   product,
# MAGIC   COUNT(*) as sales_count,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue
# MAGIC FROM sales_fact
# MAGIC WHERE sale_date BETWEEN getArgument('start_date') AND getArgument('end_date')
# MAGIC   AND (getArgument('region') = 'All' OR region = getArgument('region'))
# MAGIC   AND (getArgument('category') = 'All' OR category = getArgument('category'))
# MAGIC GROUP BY sale_date, region, category, product
# MAGIC ORDER BY sale_date DESC, revenue DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# Python version with parameters
start_date = dbutils.widgets.get("start_date")
end_date = dbutils.widgets.get("end_date")
selected_region = dbutils.widgets.get("region")
selected_category = dbutils.widgets.get("category")

# Build dynamic query
filtered_df = spark.table("sales_fact") \
    .filter(col("sale_date").between(start_date, end_date))

if selected_region != "All":
    filtered_df = filtered_df.filter(col("region") == selected_region)

if selected_category != "All":
    filtered_df = filtered_df.filter(col("category") == selected_category)

# Aggregate
summary = filtered_df.groupBy("region", "category") \
    .agg(
        count("*").alias("sales_count"),
        round(sum("net_revenue"), 2).alias("total_revenue"),
        round(avg("net_revenue"), 2).alias("avg_revenue")
    ) \
    .orderBy(col("total_revenue").desc())

display(summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Visualization Examples
# MAGIC
# MAGIC Databricks supports multiple visualization types:
# MAGIC - Line charts (trends)
# MAGIC - Bar charts (comparisons)
# MAGIC - Pie charts (proportions)
# MAGIC - Scatter plots (correlations)
# MAGIC - Maps (geospatial)

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Time series for line chart
# MAGIC SELECT
# MAGIC   DATE_TRUNC('week', sale_date) as week,
# MAGIC   region,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue
# MAGIC FROM sales_fact
# MAGIC WHERE sale_date >= '2024-01-01'
# MAGIC GROUP BY DATE_TRUNC('week', sale_date), region
# MAGIC ORDER BY week, region;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Category breakdown for pie chart
# MAGIC SELECT
# MAGIC   category,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue
# MAGIC FROM sales_fact
# MAGIC GROUP BY category;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Salesperson performance for bar chart
# MAGIC SELECT
# MAGIC   salesperson,
# MAGIC   ROUND(SUM(net_revenue), 2) as total_revenue,
# MAGIC   COUNT(*) as total_sales,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_sale_value
# MAGIC FROM sales_fact
# MAGIC GROUP BY salesperson
# MAGIC ORDER BY total_revenue DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: KPI Calculations

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Key Performance Indicators (KPIs)
# MAGIC SELECT
# MAGIC   'Total Revenue' as metric,
# MAGIC   CONCAT('$', FORMAT_NUMBER(SUM(net_revenue), 2)) as value
# MAGIC FROM sales_fact
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Total Sales',
# MAGIC   FORMAT_NUMBER(COUNT(*), 0)
# MAGIC FROM sales_fact
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Average Sale Value',
# MAGIC   CONCAT('$', FORMAT_NUMBER(AVG(net_revenue), 2))
# MAGIC FROM sales_fact
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Active Salespeople',
# MAGIC   FORMAT_NUMBER(COUNT(DISTINCT salesperson), 0)
# MAGIC FROM sales_fact
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT
# MAGIC   'Average Discount',
# MAGIC   CONCAT(FORMAT_NUMBER(AVG(discount_pct) * 100, 2), '%')
# MAGIC FROM sales_fact;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Month-over-Month growth
# MAGIC WITH monthly_revenue AS (
# MAGIC   SELECT
# MAGIC     DATE_TRUNC('month', sale_date) as month,
# MAGIC     SUM(net_revenue) as revenue
# MAGIC   FROM sales_fact
# MAGIC   GROUP BY DATE_TRUNC('month', sale_date)
# MAGIC )
# MAGIC SELECT
# MAGIC   month,
# MAGIC   ROUND(revenue, 2) as revenue,
# MAGIC   ROUND(LAG(revenue) OVER (ORDER BY month), 2) as prev_month_revenue,
# MAGIC   ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) as revenue_change,
# MAGIC   ROUND((revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month) * 100, 2) as growth_pct
# MAGIC FROM monthly_revenue
# MAGIC ORDER BY month;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: Creating Views and Materialized Results

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create view for common query pattern
# MAGIC CREATE OR REPLACE VIEW sales_summary AS
# MAGIC SELECT
# MAGIC   DATE_TRUNC('month', sale_date) as month,
# MAGIC   region,
# MAGIC   category,
# MAGIC   COUNT(*) as sales_count,
# MAGIC   SUM(quantity) as units_sold,
# MAGIC   ROUND(SUM(net_revenue), 2) as revenue,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_sale,
# MAGIC   ROUND(AVG(discount_pct), 4) as avg_discount
# MAGIC FROM sales_fact
# MAGIC GROUP BY DATE_TRUNC('month', sale_date), region, category;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Query the view
# MAGIC SELECT * FROM sales_summary
# MAGIC ORDER BY month DESC, revenue DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# Create materialized aggregate table (for performance)
print("Creating materialized aggregate table...")

# Pre-aggregate for dashboard performance
daily_metrics = spark.sql("""
    SELECT
        sale_date,
        region,
        category,
        salesperson,
        COUNT(*) as sales_count,
        SUM(quantity) as units_sold,
        ROUND(SUM(net_revenue), 2) as revenue,
        ROUND(AVG(unit_price), 2) as avg_price,
        ROUND(AVG(discount_pct), 4) as avg_discount
    FROM sales_fact
    GROUP BY sale_date, region, category, salesperson
""")

daily_metrics.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("daily_metrics")

# Optimize for fast queries
spark.sql("OPTIMIZE daily_metrics ZORDER BY (sale_date, region)")

print("✅ Materialized table created and optimized")
display(spark.table("daily_metrics").limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 7: Dashboard Query Patterns

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Dashboard Query 1: Executive Summary (Current Month)
# MAGIC WITH current_month AS (
# MAGIC   SELECT
# MAGIC     SUM(net_revenue) as revenue,
# MAGIC     COUNT(*) as sales,
# MAGIC     AVG(net_revenue) as avg_sale
# MAGIC   FROM sales_fact
# MAGIC   WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
# MAGIC ),
# MAGIC previous_month AS (
# MAGIC   SELECT
# MAGIC     SUM(net_revenue) as revenue,
# MAGIC     COUNT(*) as sales
# MAGIC   FROM sales_fact
# MAGIC   WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL 1 MONTH)
# MAGIC )
# MAGIC SELECT
# MAGIC   ROUND(c.revenue, 2) as current_revenue,
# MAGIC   ROUND(p.revenue, 2) as previous_revenue,
# MAGIC   ROUND((c.revenue - p.revenue) / p.revenue * 100, 2) as revenue_growth_pct,
# MAGIC   c.sales as current_sales,
# MAGIC   p.sales as previous_sales,
# MAGIC   ROUND((c.sales - p.sales) * 100.0 / p.sales, 2) as sales_growth_pct,
# MAGIC   ROUND(c.avg_sale, 2) as avg_sale_value
# MAGIC FROM current_month c, previous_month p;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Dashboard Query 2: Top Performers
# MAGIC SELECT
# MAGIC   salesperson,
# MAGIC   ROUND(SUM(net_revenue), 2) as total_revenue,
# MAGIC   COUNT(*) as total_sales,
# MAGIC   ROUND(AVG(net_revenue), 2) as avg_sale,
# MAGIC   RANK() OVER (ORDER BY SUM(net_revenue) DESC) as revenue_rank
# MAGIC FROM sales_fact
# MAGIC WHERE DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
# MAGIC GROUP BY salesperson
# MAGIC ORDER BY total_revenue DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Dashboard Query 3: Regional Performance Matrix
# MAGIC SELECT
# MAGIC   region,
# MAGIC   SUM(CASE WHEN category = 'Electronics' THEN net_revenue ELSE 0 END) as electronics_revenue,
# MAGIC   SUM(CASE WHEN category = 'Accessories' THEN net_revenue ELSE 0 END) as accessories_revenue,
# MAGIC   SUM(net_revenue) as total_revenue,
# MAGIC   COUNT(DISTINCT salesperson) as active_salespeople,
# MAGIC   COUNT(*) as total_sales
# MAGIC FROM sales_fact
# MAGIC WHERE DATE_TRUNC('quarter', sale_date) = DATE_TRUNC('quarter', CURRENT_DATE)
# MAGIC GROUP BY region
# MAGIC ORDER BY total_revenue DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 8: Query Scheduling & Alerts
# MAGIC
# MAGIC **To schedule queries in Databricks SQL:**
# MAGIC
# MAGIC 1. **Create Query** in Databricks SQL Editor
# MAGIC 2. **Save Query** with descriptive name
# MAGIC 3. **Schedule**:
# MAGIC    - Click "Schedule" button
# MAGIC    - Set frequency (hourly, daily, weekly)
# MAGIC    - Set timezone
# MAGIC    - Optional: Send results via email
# MAGIC 4. **Create Alerts**:
# MAGIC    - Define alert condition (e.g., revenue < threshold)
# MAGIC    - Set notification channels (email, Slack, PagerDuty)
# MAGIC    - Configure alert frequency

# COMMAND ----------

# Example: Alert query for monitoring
# MAGIC %sql
# MAGIC -- Alert: Daily revenue drop detection
# MAGIC WITH today_revenue AS (
# MAGIC   SELECT SUM(net_revenue) as revenue
# MAGIC   FROM sales_fact
# MAGIC   WHERE sale_date = CURRENT_DATE
# MAGIC ),
# MAGIC avg_revenue AS (
# MAGIC   SELECT AVG(daily_revenue) as avg_daily
# MAGIC   FROM (
# MAGIC     SELECT sale_date, SUM(net_revenue) as daily_revenue
# MAGIC     FROM sales_fact
# MAGIC     WHERE sale_date >= CURRENT_DATE - INTERVAL 30 DAYS
# MAGIC     GROUP BY sale_date
# MAGIC   )
# MAGIC )
# MAGIC SELECT
# MAGIC   t.revenue as today_revenue,
# MAGIC   a.avg_daily as avg_revenue_30d,
# MAGIC   ROUND((t.revenue - a.avg_daily) / a.avg_daily * 100, 2) as pct_change,
# MAGIC   CASE
# MAGIC     WHEN t.revenue < a.avg_daily * 0.7 THEN '🚨 CRITICAL: Revenue down >30%'
# MAGIC     WHEN t.revenue < a.avg_daily * 0.85 THEN '⚠️ WARNING: Revenue down >15%'
# MAGIC     ELSE '✅ OK'
# MAGIC   END as alert_status
# MAGIC FROM today_revenue t, avg_revenue a;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC ✅ **SQL Analytics**
# MAGIC - Standard SQL with Delta Lake tables
# MAGIC - Window functions for advanced analysis
# MAGIC - Pivot tables and cohort analysis
# MAGIC
# MAGIC ✅ **Parameterized Queries**
# MAGIC - Widgets for interactive parameters
# MAGIC - Dynamic filtering and aggregation
# MAGIC - Reusable query templates
# MAGIC
# MAGIC ✅ **Visualizations**
# MAGIC - Line charts for trends
# MAGIC - Bar charts for comparisons
# MAGIC - Pie charts for proportions
# MAGIC - Built-in Databricks visualizations
# MAGIC
# MAGIC ✅ **Performance Optimization**
# MAGIC - Materialized aggregate tables
# MAGIC - OPTIMIZE and ZORDER
# MAGIC - Views for common patterns
# MAGIC
# MAGIC ✅ **Production Patterns**
# MAGIC - Scheduled queries
# MAGIC - Alerts and monitoring
# MAGIC - Dashboard design principles
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC Continue to Notebook 06: **Machine Learning with MLflow**

# COMMAND ----------

# Cleanup widgets
dbutils.widgets.removeAll()

# Cleanup database (optional)
# spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
# print("✅ Cleanup complete")
