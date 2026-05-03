"""
AWS Glue ETL Job: Silver to Gold - Customer 360 View - STARTER TEMPLATE
Create comprehensive customer analytics combining multiple data sources

COMPLEXITY: HIGH - Customer 360 involves:
- Aggregating customer transaction history
- Calculating RFM metrics (Recency, Frequency, Monetary)
- Customer segmentation
- Product affinity analysis
- Churn risk indicators

TODO SECTIONS:
1. Read Silver orders and customers
2. Calculate RFM metrics
3. Create customer segments
4. Calculate lifetime value
5. Product preferences and category affinity
6. Write Customer 360 to Gold
"""

from pyspark.sql import DataFrame
from awsglue.context import GlueContext


def calculate_rfm_metrics(orders_df: DataFrame) -> DataFrame:
    """
    Calculate RFM (Recency, Frequency, Monetary) metrics per customer

    RFM is a customer segmentation technique:
    - Recency: Days since last purchase
    - Frequency: Number of purchases
    - Monetary: Total amount spent

    TODO: Group by customer_id and calculate:
    - recency = days between current_date and MAX(order_date)
    - frequency = COUNT(order_id)
    - monetary = SUM(total_amount)
    """
    # TODO: Calculate RFM
    # rfm_df = orders_df.groupBy('customer_id').agg(
    #     datediff(current_date(), max('order_date')).alias('recency_days'),
    #     count('order_id').alias('frequency'),
    #     spark_sum('total_amount').alias('monetary')
    # )

    return None  # TODO: Implement


def create_rfm_segments(rfm_df: DataFrame) -> DataFrame:
    """
    Create customer segments based on RFM scores

    TODO: Use ntile() to divide customers into quintiles (1-5) for each metric
    - Lower recency = better (more recent purchase)
    - Higher frequency = better (more purchases)
    - Higher monetary = better (more spend)

    Then create segments like:
    - Champions: High F, High M, Low R
    - Loyal: High F, Medium M
    - At Risk: High F, High M, High R
    - Lost: Low F, High R
    """
    # TODO: Create R, F, M scores (1-5)
    # window = Window.orderBy(col('recency_days'))  # Lower is better
    # rfm_df = rfm_df.withColumn('R_score', ntile(5).over(window))

    # window_f = Window.orderBy(col('frequency').desc())  # Higher is better
    # rfm_df = rfm_df.withColumn('F_score', ntile(5).over(window_f))

    # window_m = Window.orderBy(col('monetary').desc())  # Higher is better
    # rfm_df = rfm_df.withColumn('M_score', ntile(5).over(window_m))

    # TODO: Create segment labels
    # rfm_df = rfm_df.withColumn('segment',
    #     when((col('R_score') >= 4) & (col('F_score') >= 4), 'Champions')
    #     .when((col('F_score') >= 4), 'Loyal')
    #     .when((col('R_score') <= 2) & (col('F_score') >= 3), 'At Risk')
    #     .when(col('R_score') <= 2, 'Lost')
    #     .otherwise('Potential')
    # )

    return None  # TODO: Implement


def calculate_customer_lifetime_value(orders_df: DataFrame) -> DataFrame:
    """
    Calculate Customer Lifetime Value (CLV)

    TODO: Aggregate per customer:
    - total_spent: SUM(total_amount)
    - total_orders: COUNT(*)
    - avg_order_value: AVG(total_amount)
    - first_order_date: MIN(order_date)
    - last_order_date: MAX(order_date)
    - customer_lifetime_days: DATEDIFF(last, first)
    - avg_days_between_orders: customer_lifetime_days / (total_orders - 1)
    """
    # TODO: Calculate CLV metrics
    return None  # TODO: Implement


def calculate_product_affinity(orders_df: DataFrame) -> DataFrame:
    """
    Calculate customer product preferences

    TODO: For each customer:
    - favorite_category: Most purchased category
    - categories_purchased: ARRAY of unique categories
    - favorite_products: TOP 3 products by quantity
    - avg_products_per_order: AVG number of products per order
    """
    # TODO: Product affinity analysis
    # Use collect_list() and array_distinct() for arrays
    # Use Window functions with row_number() for top products
    return None  # TODO: Implement


def join_customer_master_data(customer_metrics_df: DataFrame,
                               customers_df: DataFrame) -> DataFrame:
    """
    Join calculated metrics with customer master data

    TODO: Join all calculated metrics with customer demographics
    - RFM segments
    - CLV metrics
    - Product affinity
    - Customer master data (name, email, country, etc.)
    """
    # TODO: Join all dataframes
    return None  # TODO: Implement


def write_to_gold(glue_context: GlueContext, df: DataFrame, target_s3_path: str):
    """Write Customer 360 view to Gold layer"""
    # TODO: Write comprehensive customer analytics
    # Consider partitioning by segment or country for query performance
    pass  # TODO: Implement


def main():
    """Main ETL execution for Customer 360"""
    # TODO: Initialize Glue context
    # TODO: Read Silver data
    # TODO: Calculate RFM metrics
    # TODO: Create segments
    # TODO: Calculate CLV
    # TODO: Calculate product affinity
    # TODO: Join all metrics
    # TODO: Write to Gold
    # TODO: Commit job
    pass  # TODO: Implement


if __name__ == "__main__":
    main()


# ===============================================================================
# CUSTOMER SEGMENTATION REFERENCE:
# ===============================================================================
# RFM Segments:
# - Champions: R=4-5, F=4-5, M=4-5 (Best customers, buy recently and often)
# - Loyal: F=4-5, M=3-5 (Regular customers, high frequency)
# - Potential Loyalists: R=3-5, F=1-3, M=1-3 (Recent customers, room to grow)
# - At Risk: R=1-2, F=3-5, M=3-5 (Were good customers, haven't purchased recently)
# - Lost: R=1-2, F=1-2, M=1-2 (Lowest engagement, need win-back campaign)
# ===============================================================================
