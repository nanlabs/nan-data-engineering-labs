# Exercise 02: Flink Table API with Python

## Overview
Build advanced streaming analytics using Flink's Table API in Python, implementing sliding windows, stream joins, top-N queries, and late data handling.

**Difficulty**: ⭐⭐⭐ Advanced
**Duration**: ~2 hours
**Prerequisites**: Exercise 01, Python 3.8+, PyFlink basics

## Learning Objectives

- Use PyFlink Table API for stream processing
- Implement sliding (HOP) windows for moving averages
- Perform stream joins (regular and interval joins)
- Create top-N queries with windowed ranking
- Handle late-arriving data with watermarks
- Deploy Python-based Flink applications

## Key Concepts

- **Table API**: Declarative API for stream and batch processing
- **Sliding Windows**: Overlapping windows with slide size < window size
- **Interval Joins**: Time-bound joins between streams
- **Top-N**: Windowed ranking to find top records
- **Late Data**: Events arriving after watermark with allowed lateness

## Architecture

```
┌──────────────┐      ┌─────────────────────────┐      ┌──────────────┐
│  Kinesis     │      │   PyFlink Application   │      │   Kinesis    │
│  events      │─────>│                         │─────>│   results    │
│  stream      │      │  - Sliding windows      │      │   stream     │
└──────────────┘      │  - Stream joins         │      └──────────────┘
                      │  - Top-N queries        │              │
                      │  - Late data handling   │              v
                      └─────────────────────────┘      ┌──────────────┐
                               │                        │  DynamoDB    │
                               │ checkpoints            │  (Results)   │
                               v                        └──────────────┘
                      ┌─────────────────┐
                      │  S3 Checkpoints │
                      └─────────────────┘
```

## Setup

### Prerequisites Check

```bash
# Verify environment
make status

# Install PyFlink dependencies
pip install apache-flink==1.18.0 apache-flink-libraries

# Verify Python version
python3 --version  # Should be 3.8+
```

### Create Exercise Directory

```bash
cd exercises/02-flink-table-api
mkdir -p src tests output logs
```

## Task 1: Setup PyFlink Environment (15 minutes)

Create the base PyFlink application structure.

**File**: `src/flink_config.py`

```python
"""Flink environment configuration"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.table.expressions import col, lit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_table_environment():
    """Create and configure Flink Table Environment"""

    # Create stream execution environment
    env = StreamExecutionEnvironment.get_execution_environment()

    # Configure environment
    env.set_parallelism(2)
    env.enable_checkpointing(60000)  # Checkpoint every 60 seconds

    # Create table environment
    settings = EnvironmentSettings.new_instance() \
        .in_streaming_mode() \
        .build()

    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    # Configuration
    t_env.get_config().set(
        "pipeline.name", "PyFlink Analytics App"
    )
    t_env.get_config().set(
        "state.backend", "rocksdb"
    )
    t_env.get_config().set(
        "execution.checkpointing.interval", "60s"
    )
    t_env.get_config().set(
        "execution.checkpointing.mode", "EXACTLY_ONCE"
    )

    # Enable event time
    t_env.get_config().set(
        "table.exec.source.idle-timeout", "30s"
    )

    logger.info("✓ Flink Table Environment created")
    return t_env


def register_kinesis_source(t_env, stream_name='events-stream'):
    """Register Kinesis source table"""

    ddl = f"""
        CREATE TABLE kinesis_source (
            event_id STRING,
            event_type STRING,
            event_timestamp TIMESTAMP(3),
            user_id STRING,
            session_id STRING,
            page_url STRING,
            product_id STRING,
            product_name STRING,
            product_price DOUBLE,
            quantity INT,
            device STRING,
            country STRING,
            WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kinesis',
            'stream' = '{stream_name}',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566',
            'scan.stream.initpos' = 'LATEST',
            'format' = 'json'
        )
    """

    t_env.execute_sql(ddl)
    logger.info(f"✓ Registered Kinesis source: {stream_name}")


def register_kinesis_sink(t_env, stream_name='aggregated-stream'):
    """Register Kinesis sink table"""

    ddl = f"""
        CREATE TABLE kinesis_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            metric_name STRING,
            metric_value DOUBLE,
            dimensions STRING
        ) WITH (
            'connector' = 'kinesis',
            'stream' = '{stream_name}',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566',
            'format' = 'json'
        )
    """

    t_env.execute_sql(ddl)
    logger.info(f"✓ Registered Kinesis sink: {stream_name}")


def register_dynamodb_sink(t_env, table_name='realtime-aggregates'):
    """Register DynamoDB sink table"""

    ddl = f"""
        CREATE TABLE dynamodb_sink (
            metric_name STRING,
            metric_timestamp TIMESTAMP(3),
            metric_value DOUBLE,
            metadata STRING,
            PRIMARY KEY (metric_name, metric_timestamp) NOT ENFORCED
        ) WITH (
            'connector' = 'dynamodb',
            'table-name' = '{table_name}',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566'
        )
    """

    t_env.execute_sql(ddl)
    logger.info(f"✓ Registered DynamoDB sink: {table_name}")
```

## Task 2: Implement Sliding Windows (20 minutes)

Create sliding window aggregations for moving averages.

**File**: `src/sliding_windows.py`

```python
"""Sliding window analytics with PyFlink Table API"""

from pyflink.table import TableEnvironment
from pyflink.table.window import Slide
from pyflink.table.expressions import col, lit
import logging

logger = logging.getLogger(__name__)


def compute_moving_averages(t_env: TableEnvironment):
    """
    Compute moving averages using sliding windows
    Window size: 5 minutes
    Slide: 1 minute (updates every minute)
    """

    # Get source table
    source = t_env.from_path('kinesis_source')

    # Filter purchase events
    purchases = source.filter(col('event_type') == lit('purchase'))

    # Sliding window aggregation
    result = purchases \
        .window(
            Slide.over(lit(5).minutes)
                 .every(lit(1).minutes)
                 .on(col('event_timestamp'))
                 .alias('w')
        ) \
        .group_by(col('w'), col('country')) \
        .select(
            col('w').start.alias('window_start'),
            col('w').end.alias('window_end'),
            col('country'),
            col('product_price').avg.alias('avg_price'),
            col('product_price').sum.alias('total_revenue'),
            col('product_price').count.alias('purchase_count')
        )

    logger.info("✓ Sliding window query created")
    return result


def compute_traffic_rate(t_env: TableEnvironment):
    """
    Compute event rate per second using small sliding windows
    Window size: 10 seconds
    Slide: 2 seconds
    """

    source = t_env.from_path('kinesis_source')

    result = source \
        .window(
            Slide.over(lit(10).seconds)
                 .every(lit(2).seconds)
                 .on(col('event_timestamp'))
                 .alias('w')
        ) \
        .group_by(col('w'), col('event_type')) \
        .select(
            col('w').start.alias('window_start'),
            col('w').end.alias('window_end'),
            col('event_type'),
            col('event_id').count.alias('event_count'),
            (col('event_id').count / lit(10.0)).alias('events_per_second')
        )

    logger.info("✓ Traffic rate query created")
    return result


def run_sliding_windows_job(t_env: TableEnvironment):
    """Execute sliding window analytics job"""

    # Compute moving averages
    moving_avg = compute_moving_averages(t_env)

    # Create view for output
    t_env.create_temporary_view('moving_averages', moving_avg)

    # Insert into sink
    insert_sql = """
        INSERT INTO kinesis_sink
        SELECT
            window_start,
            window_end,
            CONCAT('moving_avg_', country) as metric_name,
            avg_price as metric_value,
            CONCAT('country:', country, ',count:', CAST(purchase_count AS STRING)) as dimensions
        FROM moving_averages
    """

    table_result = t_env.execute_sql(insert_sql)
    logger.info("✓ Sliding window job submitted")

    return table_result
```

## Task 3: Implement Stream Joins (25 minutes)

Perform joins between multiple streams.

**File**: `src/stream_joins.py`

```python
"""Stream joins with PyFlink Table API"""

from pyflink.table import TableEnvironment
from pyflink.table.expressions import col, lit
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def register_inventory_table(t_env: TableEnvironment):
    """Register inventory lookup table (dimension table)"""

    ddl = """
        CREATE TABLE product_inventory (
            product_id STRING,
            product_name STRING,
            stock_quantity INT,
            last_updated TIMESTAMP(3),
            PRIMARY KEY (product_id) NOT ENFORCED
        ) WITH (
            'connector' = 'dynamodb',
            'table-name' = 'product-inventory',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566'
        )
    """

    t_env.execute_sql(ddl)
    logger.info("✓ Registered inventory table")


def regular_join_with_inventory(t_env: TableEnvironment):
    """
    Regular join: Enrich events with inventory data
    """

    source = t_env.from_path('kinesis_source')
    inventory = t_env.from_path('product_inventory')

    # Filter add_to_cart events
    cart_events = source.filter(col('event_type') == lit('add_to_cart'))

    # Join with inventory
    result = cart_events \
        .join(inventory) \
        .where(cart_events.product_id == inventory.product_id) \
        .select(
            cart_events.event_timestamp,
            cart_events.user_id,
            cart_events.product_id,
            inventory.product_name,
            cart_events.quantity,
            inventory.stock_quantity,
            (inventory.stock_quantity >= cart_events.quantity).alias('in_stock')
        )

    logger.info("✓ Regular join query created")
    return result


def interval_join_click_to_purchase(t_env: TableEnvironment):
    """
    Interval join: Find purchases within 30 minutes of click
    """

    source = t_env.from_path('kinesis_source')

    # Create views for clicks and purchases
    clicks = source.filter(col('event_type') == lit('click'))
    purchases = source.filter(col('event_type') == lit('purchase'))

    t_env.create_temporary_view('clicks', clicks)
    t_env.create_temporary_view('purchases', purchases)

    # Interval join using SQL (easier for time constraints)
    join_sql = """
        SELECT
            c.event_timestamp as click_time,
            p.event_timestamp as purchase_time,
            c.user_id,
            c.product_id,
            p.product_price,
            TIMESTAMPDIFF(SECOND, c.event_timestamp, p.event_timestamp) as seconds_to_purchase
        FROM clicks c
        JOIN purchases p
            ON c.user_id = p.user_id
            AND c.product_id = p.product_id
            AND p.event_timestamp BETWEEN c.event_timestamp
                AND c.event_timestamp + INTERVAL '30' MINUTE
    """

    result = t_env.sql_query(join_sql)

    logger.info("✓ Interval join query created")
    return result


def temporal_join_with_rates(t_env: TableEnvironment):
    """
    Temporal join: Join with versioned exchange rate table
    """

    # Register exchange rates table
    ddl = """
        CREATE TABLE exchange_rates (
            currency_code STRING,
            rate_to_usd DOUBLE,
            valid_from TIMESTAMP(3),
            PRIMARY KEY (currency_code) NOT ENFORCED
        ) WITH (
            'connector' = 'dynamodb',
            'table-name' = 'exchange-rates',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566'
        )
    """
    t_env.execute_sql(ddl)

    source = t_env.from_path('kinesis_source')
    purchases = source.filter(col('event_type') == lit('purchase'))

    # For temporal join in PyFlink, use SQL
    temporal_join_sql = """
        SELECT
            p.event_timestamp,
            p.user_id,
            p.product_price as price_local,
            er.rate_to_usd,
            p.product_price * er.rate_to_usd as price_usd
        FROM purchases p
        LEFT JOIN exchange_rates FOR SYSTEM_TIME AS OF p.event_timestamp AS er
            ON p.country = er.currency_code
    """

    result = t_env.sql_query(temporal_join_sql)

    logger.info("✓ Temporal join query created")
    return result


def run_join_analytics_job(t_env: TableEnvironment):
    """Execute stream join analytics"""

    # Setup tables
    register_inventory_table(t_env)

    # Click-to-purchase attribution
    attribution = interval_join_click_to_purchase(t_env)

    # Create output view
    t_env.create_temporary_view('attribution', attribution)

    # Aggregate attribution metrics
    insert_sql = """
        INSERT INTO dynamodb_sink
        SELECT
            'click_to_purchase' as metric_name,
            click_time as metric_timestamp,
            AVG(seconds_to_purchase) as metric_value,
            CONCAT('product:', product_id) as metadata
        FROM attribution
        GROUP BY click_time, product_id
    """

    table_result = t_env.execute_sql(insert_sql)
    logger.info("✓ Join analytics job submitted")

    return table_result
```

## Task 4: Implement Top-N Queries (20 minutes)

Find top products by revenue in each window.

**File**: `src/top_n_queries.py`

```python
"""Top-N queries with PyFlink Table API"""

from pyflink.table import TableEnvironment
from pyflink.table.window import Tumble
from pyflink.table.expressions import col, lit
import logging

logger = logging.getLogger(__name__)


def top_products_by_revenue(t_env: TableEnvironment, n=5):
    """
    Find top N products by revenue per 5-minute window
    """

    # Using SQL for easier ROW_NUMBER implementation
    top_n_sql = f"""
        SELECT *
        FROM (
            SELECT
                window_start,
                window_end,
                product_id,
                product_name,
                total_revenue,
                purchase_count,
                ROW_NUMBER() OVER (
                    PARTITION BY window_start
                    ORDER BY total_revenue DESC
                ) as revenue_rank
            FROM (
                SELECT
                    TUMBLE_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
                    TUMBLE_END(event_timestamp, INTERVAL '5' MINUTE) as window_end,
                    product_id,
                    product_name,
                    SUM(product_price * quantity) as total_revenue,
                    COUNT(*) as purchase_count
                FROM kinesis_source
                WHERE event_type = 'purchase'
                GROUP BY
                    TUMBLE(event_timestamp, INTERVAL '5' MINUTE),
                    product_id,
                    product_name
            )
        )
        WHERE revenue_rank <= {n}
    """

    result = t_env.sql_query(top_n_sql)
    logger.info(f"✓ Top-{n} products query created")

    return result


def top_pages_by_traffic(t_env: TableEnvironment, n=10):
    """
    Find top N pages by view count per minute
    """

    top_n_sql = f"""
        SELECT *
        FROM (
            SELECT
                window_start,
                page_url,
                view_count,
                unique_visitors,
                ROW_NUMBER() OVER (
                    PARTITION BY window_start
                    ORDER BY view_count DESC
                ) as traffic_rank
            FROM (
                SELECT
                    TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
                    page_url,
                    COUNT(*) as view_count,
                    COUNT(DISTINCT user_id) as unique_visitors
                FROM kinesis_source
                WHERE event_type = 'page_view'
                GROUP BY
                    TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
                    page_url
            )
        )
        WHERE traffic_rank <= {n}
    """

    result = t_env.sql_query(top_n_sql)
    logger.info(f"✓ Top-{n} pages query created")

    return result


def top_users_by_activity(t_env: TableEnvironment, n=20):
    """
    Find top N most active users per hour
    """

    top_n_sql = f"""
        SELECT
            window_start,
            user_id,
            event_count,
            unique_pages,
            activity_rank
        FROM (
            SELECT
                window_start,
                user_id,
                event_count,
                unique_pages,
                ROW_NUMBER() OVER (
                    PARTITION BY window_start
                    ORDER BY event_count DESC
                ) as activity_rank
            FROM (
                SELECT
                    TUMBLE_START(event_timestamp, INTERVAL '1' HOUR) as window_start,
                    user_id,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT page_url) as unique_pages
                FROM kinesis_source
                GROUP BY
                    TUMBLE(event_timestamp, INTERVAL '1' HOUR),
                    user_id
            )
        )
        WHERE activity_rank <= {n}
    """

    result = t_env.sql_query(top_n_sql)
    logger.info(f"✓ Top-{n} users query created")

    return result


def run_top_n_job(t_env: TableEnvironment):
    """Execute Top-N analytics job"""

    # Get top products
    top_products = top_products_by_revenue(t_env, n=5)

    # Output to sink
    t_env.create_temporary_view('top_products', top_products)

    insert_sql = """
        INSERT INTO kinesis_sink
        SELECT
            window_start,
            window_end,
            CONCAT('top_product_rank_', CAST(revenue_rank AS STRING)) as metric_name,
            total_revenue as metric_value,
            CONCAT('product:', product_id, ',name:', product_name) as dimensions
        FROM top_products
    """

    table_result = t_env.execute_sql(insert_sql)
    logger.info("✓ Top-N job submitted")

    return table_result
```

## Task 5: Handle Late Data (20 minutes)

Implement watermark strategies for late-arriving events.

**File**: `src/late_data_handling.py`

```python
"""Late data handling with watermarks"""

from pyflink.table import TableEnvironment
from pyflink.table.expressions import col, lit
import logging

logger = logging.getLogger(__name__)


def create_source_with_lateness(t_env: TableEnvironment, allowed_lateness_sec=30):
    """
    Create source table with allowed lateness
    """

    ddl = f"""
        CREATE TABLE kinesis_source_late (
            event_id STRING,
            event_type STRING,
            event_timestamp TIMESTAMP(3),
            user_id STRING,
            product_id STRING,
            product_price DOUBLE,
            quantity INT,
            -- Watermark allows {allowed_lateness_sec} seconds of lateness
            WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '{allowed_lateness_sec}' SECOND
        ) WITH (
            'connector' = 'kinesis',
            'stream' = 'events-stream',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566',
            'scan.stream.initpos' = 'LATEST',
            'format' = 'json'
        )
    """

    t_env.execute_sql(ddl)
    logger.info(f"✓ Source with {allowed_lateness_sec}s lateness tolerance created")


def aggregation_with_late_data(t_env: TableEnvironment):
    """
    Aggregation that handles late data
    """

    # Configure state TTL (keep state for 1 hour after window closes)
    t_env.get_config().set("table.exec.state.ttl", "1 h")

    agg_sql = """
        SELECT
            TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
            TUMBLE_END(event_timestamp, INTERVAL '1' MINUTE) as window_end,
            event_type,
            COUNT(*) as event_count,
            SUM(product_price * quantity) as total_revenue,
            -- Track if window was updated due to late data
            MAX(PROCTIME()) as last_update_time
        FROM kinesis_source_late
        WHERE event_type = 'purchase'
        GROUP BY
            TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
            event_type
    """

    result = t_env.sql_query(agg_sql)
    logger.info("✓ Aggregation with late data handling created")

    return result


def create_side_output_for_late_events(t_env: TableEnvironment):
    """
    Route extremely late events to side output (DLQ)
    """

    # Note: True side outputs require DataStream API
    # This is a table-based approximation

    late_events_sql = """
        SELECT
            event_id,
            event_type,
            event_timestamp,
            CURRENT_TIMESTAMP as processing_time,
            TIMESTAMPDIFF(
                SECOND,
                event_timestamp,
                CURRENT_TIMESTAMP
            ) as lateness_seconds
        FROM kinesis_source
        WHERE TIMESTAMPDIFF(SECOND, event_timestamp, CURRENT_TIMESTAMP) > 60
    """

    late_events = t_env.sql_query(late_events_sql)

    # Register DLQ sink
    ddl = """
        CREATE TABLE late_events_dlq (
            event_id STRING,
            event_type STRING,
            event_timestamp TIMESTAMP(3),
            processing_time TIMESTAMP(3),
            lateness_seconds BIGINT
        ) WITH (
            'connector' = 'kinesis',
            'stream' = 'dlq-stream',
            'aws.region' = 'us-east-1',
            'aws.endpoint' = 'http://localhost:4566',
            'format' = 'json'
        )
    """
    t_env.execute_sql(ddl)

    logger.info("✓ Late events DLQ configured")
    return late_events


def run_late_data_job(t_env: TableEnvironment):
    """Execute late data handling job"""

    # Create source with lateness tolerance
    create_source_with_lateness(t_env, allowed_lateness_sec=30)

    # Run aggregation
    aggregates = aggregation_with_late_data(t_env)

    # Output results
    t_env.create_temporary_view('aggregates_with_late', aggregates)

    insert_sql = """
        INSERT INTO dynamodb_sink
        SELECT
            'revenue_with_late_data' as metric_name,
            window_start as metric_timestamp,
            total_revenue as metric_value,
            CONCAT('type:', event_type, ',updates:', CAST(last_update_time AS STRING)) as metadata
        FROM aggregates_with_late
    """

    table_result = t_env.execute_sql(insert_sql)
    logger.info("✓ Late data handling job submitted")

    return table_result
```

## Task 6: Main Application (15 minutes)

Create the main application that runs all analytics.

**File**: `src/main.py`

```python
#!/usr/bin/env python3
"""
PyFlink Table API Analytics Application
Runs multiple streaming analytics jobs
"""

import sys
import logging
from flink_config import (
    create_table_environment,
    register_kinesis_source,
    register_kinesis_sink,
    register_dynamodb_sink
)
from sliding_windows import run_sliding_windows_job
from stream_joins import run_join_analytics_job
from top_n_queries import run_top_n_job
from late_data_handling import run_late_data_job

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(job_type='all'):
    """
    Run PyFlink analytics jobs

    Args:
        job_type: 'sliding', 'joins', 'topn', 'late', or 'all'
    """

    logger.info("="*60)
    logger.info("Starting PyFlink Table API Analytics Application")
    logger.info("="*60)

    try:
        # Create table environment
        t_env = create_table_environment()

        # Register tables
        register_kinesis_source(t_env, 'events-stream')
        register_kinesis_sink(t_env, 'aggregated-stream')
        register_dynamodb_sink(t_env, 'realtime-aggregates')

        # Run selected job(s)
        if job_type == 'sliding' or job_type == 'all':
            logger.info("\n[1/4] Running Sliding Windows Job...")
            run_sliding_windows_job(t_env)

        if job_type == 'joins' or job_type == 'all':
            logger.info("\n[2/4] Running Stream Joins Job...")
            run_join_analytics_job(t_env)

        if job_type == 'topn' or job_type == 'all':
            logger.info("\n[3/4] Running Top-N Job...")
            run_top_n_job(t_env)

        if job_type == 'late' or job_type == 'all':
            logger.info("\n[4/4] Running Late Data Handling Job...")
            run_late_data_job(t_env)

        logger.info("\n" + "="*60)
        logger.info("✓ All jobs submitted successfully")
        logger.info("Monitor at: http://localhost:8081")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"✗ Application failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PyFlink Analytics Application')
    parser.add_argument(
        '--job',
        choices=['sliding', 'joins', 'topn', 'late', 'all'],
        default='all',
        help='Job type to run'
    )

    args = parser.parse_args()

    main(args.job)
```

## Task 7: Deploy and Test (20 minutes)

### Deploy Application

```bash
# Install dependencies
pip install -r ../../requirements.txt

# Run specific job
python src/main.py --job sliding

# Run all jobs
python src/main.py --job all

# Submit to Flink cluster
flink run -py src/main.py
```

### Generate Test Data

```bash
# Use Exercise 01 data generator
cd ../01-kinesis-analytics-sql
python generate_events.py --count 5000 --rate 50
```

### Verify Results

```bash
# Check Flink jobs
curl http://localhost:8081/jobs | jq

# Query DynamoDB results
awslocal dynamodb scan \
    --table-name realtime-aggregates \
    --region us-east-1 | jq '.Items[] | select(.metric_name.S | contains("moving_avg"))'

# Read from output stream
awslocal kinesis get-records \
    --shard-iterator $(awslocal kinesis get-shard-iterator \
        --stream-name aggregated-stream \
        --shard-id shardId-000000000000 \
        --shard-iterator-type LATEST \
        --region us-east-1 \
        --query 'ShardIterator' \
        --output text) \
    --region us-east-1 | jq '.Records[].Data' | base64 -d | jq
```

## Validation Checklist

- [ ] PyFlink environment configured
- [ ] Sliding windows compute moving averages
- [ ] Interval join finds click-to-purchase within 30 min
- [ ] Top-N query returns top 5 products
- [ ] Late data is handled correctly (within 30s tolerance)
- [ ] Results appear in DynamoDB
- [ ] Results appear in Kinesis output stream
- [ ] Checkpoints complete successfully
- [ ] No errors in Flink logs

## Expected Results

**Sliding Window Output**:
```json
{
  "window_start": "2024-03-08T10:15:00.000Z",
  "window_end": "2024-03-08T10:20:00.000Z",
  "metric_name": "moving_avg_US",
  "metric_value": 899.99,
  "dimensions": "country:US,count:45"
}
```

**Top-N Output**:
```json
{
  "window_start": "2024-03-08T10:15:00.000Z",
  "window_end": "2024-03-08T10:20:00.000Z",
  "metric_name": "top_product_rank_1",
  "metric_value": 58499.50,
  "dimensions": "product:prod_1001,name:Laptop Pro"
}
```

## Troubleshooting

### Problem: PyFlink connector not found

```bash
# Install Flink SQL connectors
pip install apache-flink-libraries==1.18.0

# Download Kinesis connector JAR
wget https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kinesis/1.18.0/flink-sql-connector-kinesis-1.18.0.jar \
    -P $FLINK_HOME/lib/
```

### Problem: Sliding windows not updating

- Check watermark is progressing: Look at Flink UI → Job → Metrics → currentInputWatermark
- Ensure events have timestamps
- Verify clock sync if using event time

### Problem: Joins produce no results

- Verify both sides have data
- Check join condition (ON clause)
- For interval joins, verify time constraints are reasonable

## Key Learnings

1. **Table API**: Declarative, easier than DataStream API for standard analytics
2. **Sliding Windows**: Provide smooth, overlapping metrics updates
3. **Interval Joins**: Essential for attribution and correlation analysis
4. **Top-N**: Use window aggregation + ROW_NUMBER for rankings
5. **Late Data**: Watermarks + allowed lateness balance accuracy vs latency

## Next Steps

- **Exercise 03**: Build real-time dashboards with QuickSight
- **Advanced**: Convert to DataStream API for custom operators
- **Optimization**: Tune parallelism and checkpoint intervals

## Additional Resources

- [PyFlink Table API Docs](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/dev/python/table/intro_to_table_api/)
- [Flink SQL Windows](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/dev/table/sql/queries/window-tvf/)
- [Stream Joins Guide](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/dev/table/sql/queries/joins/)
