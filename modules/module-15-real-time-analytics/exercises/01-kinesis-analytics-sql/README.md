# Exercise 01: Kinesis Analytics SQL

## Overview
Build your first Kinesis Data Analytics application using Flink SQL to analyze streaming clickstream data with tumbling windows.

**Difficulty**: ⭐⭐ Intermediate
**Duration**: ~2 hours
**Prerequisites**: Module 08 (Streaming Basics), basic SQL knowledge

## Learning Objectives

By completing this exercise, you will:
- Create Kinesis Data Streams for input and output
- Define source and sink tables in Flink SQL
- Implement tumbling window aggregations
- Filter and transform streaming events
- Deploy and monitor a Flink SQL application

## Key Concepts

- **Flink SQL on Streams**: SQL queries on continuous data streams
- **Tumbling Windows**: Fixed, non-overlapping time windows (e.g., 1-minute intervals)
- **Continuous Queries**: Queries that run indefinitely, producing results for each window
- **Watermarks**: Track event time progress and handle out-of-order events

## Architecture

```
┌─────────────┐      ┌──────────────────────┐      ┌─────────────┐
│   Events    │      │  Kinesis Analytics   │      │ Aggregated  │
│   Stream    │─────>│   (Flink SQL)        │─────>│   Stream    │
│             │      │                      │      │             │
│ 4 shards    │      │  - Tumbling windows  │      │  2 shards   │
└─────────────┘      │  - Aggregations      │      └─────────────┘
                     │  - Filtering          │              │
                     └──────────────────────┘              │
                                                            v
                                                    ┌──────────────┐
                                                    │  DynamoDB    │
                                                    │  (Results)   │
                                                    └──────────────┘
```

## Setup

### Prerequisites Check

```bash
# Verify environment is running
docker ps | grep module15

# Check Kinesis streams exist
awslocal kinesis list-streams --region us-east-1

# Check Flink is accessible
curl http://localhost:8081/overview
```

### Create Required Streams

```bash
# Create input stream (if not exists)
awslocal kinesis create-stream \
    --stream-name clickstream-input \
    --shard-count 4 \
    --region us-east-1

# Create output stream
awslocal kinesis create-stream \
    --stream-name aggregated-output \
    --shard-count 2 \
    --region us-east-1

# Verify streams
awslocal kinesis list-streams --region us-east-1
```

## Task 1: Define Source Table (15 minutes)

Create a Flink SQL source table that reads from the Kinesis input stream.

**File**: `source_table.sql`

```sql
-- Source table definition for clickstream events
CREATE TABLE clickstream_events (
    event_id VARCHAR,
    event_type VARCHAR,
    event_timestamp TIMESTAMP(3),
    user_id VARCHAR,
    session_id VARCHAR,
    page_url VARCHAR,
    product_id VARCHAR,
    product_name VARCHAR,
    product_price DOUBLE,
    quantity INT,
    device VARCHAR,
    browser VARCHAR,
    country VARCHAR,
    city VARCHAR,
    -- Define watermark strategy (5 seconds max out-of-order)
    WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'clickstream-input',
    'aws.region' = 'us-east-1',
    'aws.endpoint' = 'http://localstack:4566',  -- For LocalStack
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);
```

**Key Points**:
- `WATERMARK`: Defines event time semantics (5-second tolerance for late events)
- `TIMESTAMP(3)`: Millisecond precision timestamps
- `connector = 'kinesis'`: Uses Kinesis connector
- `scan.stream.initpos = 'LATEST'`: Start reading from latest records

## Task 2: Define Sink Table (10 minutes)

Create a sink table for aggregated results.

**File**: `sink_table.sql`

```sql
-- Sink table for aggregated metrics
CREATE TABLE page_view_metrics (
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    page_url VARCHAR,
    view_count BIGINT,
    unique_users BIGINT,
    avg_session_duration DOUBLE,
    PRIMARY KEY (window_start, page_url) NOT ENFORCED
) WITH (
    'connector' = 'kinesis',
    'stream' = 'aggregated-output',
    'aws.region' = 'us-east-1',
    'aws.endpoint' = 'http://localstack:4566',
    'format' = 'json'
);

-- Alternative: Sink to DynamoDB for dashboard queries
CREATE TABLE realtime_dashboard (
    metric_name VARCHAR,
    metric_timestamp TIMESTAMP(3),
    metric_value DOUBLE,
    dimensions VARCHAR,
    PRIMARY KEY (metric_name, metric_timestamp) NOT ENFORCED
) WITH (
    'connector' = 'dynamodb',
    'table-name' = 'realtime-aggregates',
    'aws.region' = 'us-east-1',
    'aws.endpoint' = 'http://localstack:4566'
);
```

## Task 3: Implement Tumbling Window Aggregation (30 minutes)

Write SQL queries to aggregate page views in 1-minute tumbling windows.

**File**: `aggregation_query.sql`

```sql
-- Query 1: Page views per minute
INSERT INTO page_view_metrics
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
    TUMBLE_END(event_timestamp, INTERVAL '1' MINUTE) as window_end,
    page_url,
    COUNT(*) as view_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(CAST(
        EXTRACT(EPOCH FROM (event_timestamp - LAG(event_timestamp) OVER (PARTITION BY session_id ORDER BY event_timestamp)))
        AS DOUBLE
    )) as avg_session_duration
FROM clickstream_events
WHERE event_type = 'page_view'
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
    page_url;
```

**Breakdown**:
- `TUMBLE_START/END`: Get window boundaries
- `TUMBLE(event_timestamp, INTERVAL '1' MINUTE)`: Define 1-minute non-overlapping windows
- `COUNT(DISTINCT user_id)`: Count unique users within each window
- `GROUP BY TUMBLE(...)`: Group events into tumbling windows

**Additional Queries**:

```sql
-- Query 2: Revenue per minute by country
INSERT INTO realtime_dashboard
SELECT
    'revenue_per_minute' as metric_name,
    TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as metric_timestamp,
    SUM(product_price * quantity) as metric_value,
    JSON_OBJECT('country' VALUE country) as dimensions
FROM clickstream_events
WHERE event_type = 'purchase'
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
    country;

-- Query 3: Top 5 products per 5-minute window
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
    product_id,
    product_name,
    COUNT(*) as purchase_count,
    SUM(product_price * quantity) as total_revenue,
    ROW_NUMBER() OVER (
        PARTITION BY TUMBLE(event_timestamp, INTERVAL '5' MINUTE)
        ORDER BY SUM(product_price * quantity) DESC
    ) as revenue_rank
FROM clickstream_events
WHERE event_type = 'purchase'
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '5' MINUTE),
    product_id,
    product_name
HAVING revenue_rank <= 5;
```

## Task 4: Deploy SQL Application (20 minutes)

### Option A: Deploy via Flink SQL CLI

```bash
# Enter Flink SQL CLI
docker exec -it module15-flink-jobmanager ./bin/sql-client.sh

# In SQL CLI, execute:
-- 1. Create tables
SOURCE '/opt/flink/jobs/source_table.sql';
SOURCE '/opt/flink/jobs/sink_table.sql';

-- 2. Submit query
SOURCE '/opt/flink/jobs/aggregation_query.sql';

-- 3. Verify job is running
SHOW JOBS;
```

### Option B: Deploy via Flink Web UI

1. Open Flink UI: http://localhost:8081
2. Click "Submit New Job"
3. Upload SQL file: `combined_application.sql`
4. Set Entry Class: `org.apache.flink.table.client.SqlClient`
5. Click "Submit"

### Option C: Deploy Python Script

**File**: `deploy_sql_app.py`

```python
#!/usr/bin/env python3
"""Deploy Flink SQL application"""

import boto3
import json
import time

def create_kinesis_analytics_app():
    """Create Kinesis Data Analytics application"""
    client = boto3.client('kinesisanalyticsv2',
                         endpoint_url='http://localhost:4566',
                         region_name='us-east-1')

    # Read SQL code
    with open('aggregation_query.sql', 'r') as f:
        sql_code = f.read()

    # Create application
    response = client.create_application(
        ApplicationName='PageViewAnalytics',
        RuntimeEnvironment='FLINK-1_18',
        ServiceExecutionRole='arn:aws:iam::000000000000:role/KinesisAnalyticsRole',
        ApplicationConfiguration={
            'SqlApplicationConfiguration': {
                'Inputs': [{
                    'NamePrefix': 'SOURCE_SQL_STREAM',
                    'KinesisStreamsInput': {
                        'ResourceARN': 'arn:aws:kinesis:us-east-1:000000000000:stream/clickstream-input'
                    },
                    'InputSchema': {
                        'RecordFormat': {
                            'RecordFormatType': 'JSON',
                            'MappingParameters': {
                                'JSONMappingParameters': {
                                    'RecordRowPath': '$'
                                }
                            }
                        },
                        'RecordColumns': [
                            {'Name': 'event_timestamp', 'SqlType': 'TIMESTAMP', 'Mapping': '$.timestamp'},
                            {'Name': 'event_type', 'SqlType': 'VARCHAR(64)', 'Mapping': '$.event_type'},
                            {'Name': 'user_id', 'SqlType': 'VARCHAR(128)', 'Mapping': '$.user_id'},
                            # ... add other columns
                        ]
                    }
                }],
                'Outputs': [{
                    'Name': 'DESTINATION_SQL_STREAM',
                    'KinesisStreamsOutput': {
                        'ResourceARN': 'arn:aws:kinesis:us-east-1:000000000000:stream/aggregated-output'
                    },
                    'DestinationSchema': {
                        'RecordFormatType': 'JSON'
                    }
                }]
            },
            'ApplicationCodeConfiguration': {
                'CodeContent': {
                    'TextContent': sql_code
                },
                'CodeContentType': 'PLAINTEXT'
            },
            'FlinkApplicationConfiguration': {
                'CheckpointConfiguration': {
                    'ConfigurationType': 'DEFAULT'
                },
                'MonitoringConfiguration': {
                    'ConfigurationType': 'CUSTOM',
                    'MetricsLevel': 'APPLICATION',
                    'LogLevel': 'INFO'
                },
                'ParallelismConfiguration': {
                    'ConfigurationType': 'CUSTOM',
                    'Parallelism': 2,
                    'ParallelismPerKPU': 1,
                    'AutoScalingEnabled': True
                }
            }
        }
    )

    print(f"✓ Application created: {response['ApplicationDetail']['ApplicationARN']}")

    # Start application
    client.start_application(
        ApplicationName='PageViewAnalytics',
        RunConfiguration={
            'SqlRunConfigurations': [{
                'InputId': response['ApplicationDetail']['ApplicationConfigurationDescription']['SqlApplicationConfigurationDescription']['Inputs'][0]['InputId'],
                'InputStartingPositionConfiguration': {
                    'InputStartingPosition': 'NOW'
                }
            }]
        }
    )

    print("✓ Application started")
    return response

if __name__ == '__main__':
    create_kinesis_analytics_app()
```

## Task 5: Generate Test Data (15 minutes)

Create a data generator to send events to the input stream.

**File**: `generate_events.py`

```python
#!/usr/bin/env python3
"""Generate clickstream events for testing"""

import boto3
import json
import time
import random
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

# Initialize Kinesis client
kinesis = boto3.client('kinesis',
                       endpoint_url='http://localhost:4566',
                       region_name='us-east-1')

STREAM_NAME = 'clickstream-input'

EVENT_TYPES = ['page_view', 'click', 'add_to_cart', 'purchase']
PAGES = ['/products/laptop', '/products/phone', '/products/tablet', '/cart', '/checkout']
PRODUCTS = [
    {'id': 'prod_001', 'name': 'Laptop Pro', 'price': 1299.99},
    {'id': 'prod_002', 'name': 'Smartphone X', 'price': 899.99},
    {'id': 'prod_003', 'name': 'Tablet Max', 'price': 599.99},
]

def generate_event():
    """Generate a random clickstream event"""
    event_type = random.choice(EVENT_TYPES)
    product = random.choice(PRODUCTS)

    event = {
        'event_id': fake.uuid4(),
        'event_type': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_id': f"user_{random.randint(1, 100):03d}",
        'session_id': f"sess_{random.randint(1, 50):03d}",
        'page_url': random.choice(PAGES),
        'device': random.choice(['desktop', 'mobile', 'tablet']),
        'browser': random.choice(['Chrome', 'Firefox', 'Safari']),
        'country': random.choice(['US', 'CA', 'UK', 'DE', 'FR']),
        'city': fake.city()
    }

    if event_type in ['add_to_cart', 'purchase']:
        event.update({
            'product_id': product['id'],
            'product_name': product['name'],
            'product_price': product['price'],
            'quantity': random.randint(1, 3)
        })

    return event

def send_events(count=1000, rate=10):
    """Send events to Kinesis stream

    Args:
        count: Number of events to send
        rate: Events per second
    """
    print(f"Sending {count} events at {rate} events/sec to {STREAM_NAME}...")

    sent = 0
    start_time = time.time()

    for i in range(count):
        event = generate_event()

        try:
            response = kinesis.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(event).encode('utf-8'),
                PartitionKey=event['user_id']
            )
            sent += 1

            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                current_rate = sent / elapsed
                print(f"  Sent {sent}/{count} events ({current_rate:.1f} events/sec)")

        except Exception as e:
            print(f"  Error sending event: {e}")

        # Rate limiting
        time.sleep(1.0 / rate)

    elapsed = time.time() - start_time
    print(f"✓ Sent {sent} events in {elapsed:.1f}s ({sent/elapsed:.1f} events/sec)")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=1000, help='Number of events')
    parser.add_argument('--rate', type=int, default=10, help='Events per second')
    args = parser.parse_args()

    send_events(args.count, args.rate)
```

**Run the generator**:

```bash
# Install dependencies
pip install boto3 faker

# Generate 1000 events at 10 events/sec
python generate_events.py --count 1000 --rate 10

# Generate continuous stream (for testing)
python generate_events.py --count 100000 --rate 50
```

## Task 6: Verify Results (20 minutes)

### Check Flink Job Status

```bash
# Via curl
curl http://localhost:8081/jobs

# Via Flink CLI
docker exec module15-flink-jobmanager ./bin/flink list
```

### Read Output Stream

```bash
# Get shard iterator
SHARD_ITERATOR=$(awslocal kinesis get-shard-iterator \
    --stream-name aggregated-output \
    --shard-id shardId-000000000000 \
    --shard-iterator-type LATEST \
    --region us-east-1 \
    --query 'ShardIterator' \
    --output text)

# Read records
awslocal kinesis get-records \
    --shard-iterator "$SHARD_ITERATOR" \
    --region us-east-1 | jq '.Records[].Data' | base64 -d | jq .
```

### Query DynamoDB Results

```bash
# Scan realtime-aggregates table
awslocal dynamodb scan \
    --table-name realtime-aggregates \
    --region us-east-1 | jq '.Items'

# Query specific metric
awslocal dynamodb query \
    --table-name realtime-aggregates \
    --key-condition-expression "metric_name = :name" \
    --expression-attribute-values '{":name":{"S":"revenue_per_minute"}}' \
    --region us-east-1
```

### Monitor in Flink UI

1. Open http://localhost:8081
2. Click on your running job
3. View:
   - **Overview**: Job status, uptime, parallelism
   - **Metrics**: Records in/out, checkpoint duration
   - **Checkpoints**: Last checkpoint size and duration
   - **Timeline**: Visual execution timeline

## Validation Checklist

- [ ] Source table created successfully
- [ ] Sink table(s) created successfully
- [ ] SQL query syntax is valid
- [ ] Flink job is running (check UI)
- [ ] Events are being sent to input stream
- [ ] Aggregated results appear in output stream
- [ ] Results are written to DynamoDB (if applicable)
- [ ] Window boundaries are correct (1-minute tumbling)
- [ ] Aggregations are accurate (compare with raw data)
- [ ] Checkpoints are completing successfully

## Expected Results

After running for 5 minutes with 10 events/sec:

```json
{
  "window_start": "2024-03-08T10:15:00.000Z",
  "window_end": "2024-03-08T10:16:00.000Z",
  "page_url": "/products/laptop",
  "view_count": 120,
  "unique_users": 35,
  "avg_session_duration": 45.2
}
```

## Troubleshooting

### Problem: Job fails to start

**Solution**:
```bash
# Check Flink logs
docker logs module15-flink-jobmanager

# Check for syntax errors in SQL
# Verify connector JARs are available
docker exec module15-flink-jobmanager ls /opt/flink/lib/ | grep kinesis
```

### Problem: No results in output stream

**Checklist**:
- [ ] Input stream has data (check with get-records)
- [ ] Watermarks are progressing (check Flink metrics)
- [ ] Window duration has passed (wait at least 1 minute)
- [ ] Sink connector is configured correctly

### Problem: Late data not included

**Solution**: Increase allowed lateness:
```sql
-- Allow 30 seconds of lateness
WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '30' SECOND
```

## Key Learnings

1. **Tumbling Windows**: Create non-overlapping fixed-duration windows for aggregation
2. **Watermarks**: Enable event-time processing and handle out-of-order data
3. **Continuous Queries**: SQL queries run indefinitely, emitting results per window
4. **Kinesis Connector**: Seamlessly read/write from Kinesis streams with SQL
5. **Monitoring**: Use Flink UI to track job health and performance

## Next Steps

- **Exercise 02**: Implement sliding windows and stream joins with Flink Table API
- **Theory**: Read `theory/concepts.md` sections 5-6 for window details
- **Advanced**: Add late data handling and custom trigger logic

## Additional Resources

- [Flink SQL Time Windows](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/dev/table/sql/queries/window-tvf/)
- [Kinesis Analytics SQL Reference](https://docs.aws.amazon.com/kinesisanalytics/latest/dev/sql-reference.html)
- [Watermarks and Event Time](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/concepts/time/)
