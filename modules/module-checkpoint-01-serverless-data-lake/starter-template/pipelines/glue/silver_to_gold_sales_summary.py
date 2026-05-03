"""
AWS Glue ETL Job: Silver to Gold - Sales Summary - STARTER TEMPLATE
Create aggregated sales analytics from Silver layer tables

COMPLEXITY: HIGH - This involves:
- Reading from multiple Silver tables
- Joining orders with customers and products
- Performing aggregations (GROUP BY)
- Calculating metrics (revenue, quantity, avg order value)
- Window functions for rankings and trends

TODO SECTIONS:
1. Read from multiple Silver tables
2. Join orders, customers, products
3. Calculate daily/monthly aggregations
4. Add rankings (top products, top customers)
5. Calculate trends (MoM growth, YoY growth)
6. Write aggregated Gold table
"""

from pyspark.sql import DataFrame
from awsglue.context import GlueContext


def read_silver_orders(glue_context: GlueContext, database: str) -> DataFrame:
    """Read orders from Silver layer"""
    # TODO: Read orders table from Silver database
    # df = glue_context.create_dynamic_frame.from_catalog(
    #     database=database,
    #     table_name='orders',
    #     transformation_ctx='read_silver_orders'
    # ).toDF()
    return None  # TODO: Implement


def read_silver_customers(glue_context: GlueContext, database: str) -> DataFrame:
    """Read customers from Silver layer"""
    # TODO: Read customers table
    return None  # TODO: Implement


def read_silver_products(glue_context: GlueContext, database: str) -> DataFrame:
    """Read products from Silver layer"""
    # TODO: Read products table
    return None  # TODO: Implement


def join_tables(orders_df: DataFrame, customers_df: DataFrame,
                products_df: DataFrame) -> DataFrame:
    """
    Join orders with customers and products

    TODO: Perform left joins to enrich orders with customer and product details
    - orders LEFT JOIN customers ON customer_id
    - orders LEFT JOIN products ON product_id
    """
    # TODO: Join orders with customers
    # df = orders_df.join(
    #     customers_df,
    #     orders_df.customer_id == customers_df.customer_id,
    #     'left'
    # )

    # TODO: Join with products
    # df = df.join(
    #     products_df,
    #     df.product_id == products_df.product_id,
    #     'left'
    # )

    return None  # TODO: Implement


def calculate_daily_sales_summary(df: DataFrame) -> DataFrame:
    """
    Calculate daily sales metrics

    TODO: Group by order_date and calculate:
    - total_revenue: SUM(total_amount)
    - total_orders: COUNT(*)
    - total_quantity: SUM(quantity)
    - avg_order_value: AVG(total_amount)
    - unique_customers: COUNT(DISTINCT customer_id)
    """
    # TODO: Group and aggregate
    # daily_summary = df.groupBy('order_date').agg(
    #     spark_sum('total_amount').alias('total_revenue'),
    #     count('*').alias('total_orders'),
    #     spark_sum('quantity').alias('total_quantity'),
    #     avg('total_amount').alias('avg_order_value'),
    #     countDistinct('customer_id').alias('unique_customers')
    # )

    return None  # TODO: Implement


def calculate_product_rankings(df: DataFrame) -> DataFrame:
    """
    Calculate top products by revenue and quantity

    TODO: Group by product and add ranking:
    - Rank products by total revenue
    - Use dense_rank() over window ordered by revenue DESC
    """
    # TODO: Product aggregations
    # product_summary = df.groupBy('product_id', 'product_name', 'category').agg(
    #     spark_sum('total_amount').alias('total_revenue'),
    #     spark_sum('quantity').alias('total_quantity'),
    #     count('*').alias('order_count')
    # )

    # TODO: Add ranking
    # window = Window.orderBy(col('total_revenue').desc())
    # product_summary = product_summary.withColumn(
    #     'revenue_rank',
    #     dense_rank().over(window)
    # )

    return None  # TODO: Implement


def calculate_customer_metrics(df: DataFrame) -> DataFrame:
    """
    Calculate customer-level metrics

    TODO: Group by customer and calculate:
    - Total spend
    - Order count
    - Average order value
    - First order date
    - Last order date
    - Customer lifetime (days between first and last order)
    """
    # TODO: Customer aggregations
    return None  # TODO: Implement


def calculate_trends(df: DataFrame) -> DataFrame:
    """
    Calculate month-over-month and year-over-year trends

    TODO: Use window functions with lag() to calculate:
    - Previous month revenue
    - MoM growth % = (current - previous) / previous * 100
    - Use partition by year for YoY comparisons
    """
    # TODO: Add year and month columns
    # df = df.withColumn('year', year('order_date'))
    # df = df.withColumn('month', month('order_date'))

    # TODO: Calculate MoM trends
    # window = Window.orderBy('year', 'month')
    # df = df.withColumn('prev_month_revenue', lag('total_revenue', 1).over(window))
    # df = df.withColumn('mom_growth_pct',
    #     ((col('total_revenue') - col('prev_month_revenue')) / col('prev_month_revenue')) * 100
    # )

    return None  # TODO: Implement


def write_to_gold(glue_context: GlueContext, df: DataFrame, target_s3_path: str):
    """Write sales summary to Gold layer"""
    # TODO: Write aggregated data to Gold
    # Consider partitioning by year/month for time-series queries
    pass  # TODO: Implement


def main():
    """Main ETL execution for sales summary"""
    # TODO: Initialize Glue context
    # TODO: Read from Silver tables
    # TODO: Join tables
    # TODO: Calculate aggregations
    # TODO: Calculate rankings and trends
    # TODO: Write to Gold
    # TODO: Commit job
    pass  # TODO: Implement


if __name__ == "__main__":
    main()


# ===============================================================================
# HINTS FOR COMPLEX OPERATIONS:
# ===============================================================================
#
# JOIN SYNTAX:
# df_joined = df1.join(df2, df1.key == df2.key, 'inner')  # or 'left', 'right', 'outer'
#
# GROUP BY + AGGREGATION:
# df_agg = df.groupBy('column').agg(
#     sum('amount').alias('total'),
#     avg('price').alias('avg_price'),
#     count('*').alias('count')
# )
#
# WINDOW FUNCTIONS:
# from pyspark.sql.window import Window
# window = Window.partitionBy('category').orderBy(col('sales').desc())
# df = df.withColumn('rank', rank().over(window))
#
# LAG/LEAD for trends:
# df = df.withColumn('prev_value', lag('value', 1).over(window))
#
# FILTERING TOP N:
# df.filter(col('rank') <= 10)
# ===============================================================================
