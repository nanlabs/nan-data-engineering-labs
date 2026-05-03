# Real-Time Analytics: Core Concepts

## Table of Contents

1. [Introduction to Real-Time Analytics](#introduction-to-real-time-analytics)
2. [AWS Kinesis Analytics Overview](#aws-kinesis-analytics-overview)
3. [Apache Flink for Analytics](#apache-flink-for-analytics)
4. [Stream Analytics Patterns](#stream-analytics-patterns)
5. [Real-Time Aggregations](#real-time-aggregations)
6. [Window Functions](#window-functions)
7. [Complex Event Processing](#complex-event-processing)
8. [Real-Time ML Scoring](#real-time-ml-scoring)

---

## Introduction to Real-Time Analytics

### What is Real-Time Analytics?

Real-time analytics refers to the discipline of analyzing streaming data **as it arrives** to generate insights, detect patterns, and trigger actions with **minimal latency** (seconds to minutes).

**Key Characteristics**:
- **Low Latency**: Results available in seconds, not hours
- **Continuous Processing**: Always-on data processing
- **Incremental Computation**: Update results as new data arrives
- **Event-Driven**: React to patterns and anomalies immediately

### Real-Time vs Near-Real-Time vs Batch

```
┌────────────────────────────────────────────────────────────┐
│                    Processing Paradigms                     │
├────────────────┬──────────────┬───────────────┬────────────┤
│ Paradigm       │ Latency      │ Use Case      │ Complexity │
├────────────────┼──────────────┼───────────────┼────────────┤
│ Real-Time      │ < 1 second   │ Fraud detect  │ High       │
│ Near-Real-Time │ 1-60 seconds │ Dashboards    │ Medium     │
│ Micro-Batch    │ 1-5 minutes  │ Monitoring    │ Medium     │
│ Batch          │ Hours/Days   │ Reporting     │ Low        │
└────────────────┴──────────────┴───────────────┴────────────┘
```

### Benefits of Real-Time Analytics

**Business Value**:
1. **Immediate Insights**: Make data-driven decisions faster
2. **Proactive Actions**: Detect and respond to issues before they escalate
3. **Personalization**: Tailor experiences based on current behavior
4. **Competitive Advantage**: React faster than competitors

**Technical Benefits**:
1. **Always Fresh Data**: No stale reports
2. **Reduced Infrastructure Cost**: Process smaller volumes continuously
3. **Event-Driven Architecture**: Decouple systems
4. **Scalability**: Handle spikes naturally with streaming

### Common Use Cases

**1. Real-Time Dashboards**
```
Web/Mobile Traffic → Kinesis Data Streams → Flink Analytics
                                              ↓
                                    QuickSight Dashboard
                                    (Updated every second)
```
- Website traffic monitoring
- E-commerce sales metrics
- System health dashboards
- Social media trending topics

**2. Fraud Detection**
```
Transactions → Kinesis → Flink (ML Model) → Alert if fraud_score > 0.8
                                           ↓
                                    Block Transaction
                                    Send Alert (SNS)
```
- Credit card fraud
- Account takeover detection
- Bot detection
- Identity theft prevention

**3. Anomaly Detection**
```
IoT Sensors → Kinesis → Flink (Threshold Check) → CloudWatch Alarm
                                                 ↓
                                          Lambda → Auto-remediation
```
- Server performance issues
- Manufacturing defects
- Network intrusions
- Supply chain disruptions

**4. Real-Time Recommendations**
```
User Clicks → Kinesis → Flink (Collaborative Filtering) → DynamoDB
                                                         ↓
                                                   API → Recommendations
```
- Product recommendations
- Content suggestions
- "Customers also bought" features
- Personalized marketing

**5. Live Leaderboards**
```
Game Events → Kinesis → Flink (Aggregation) → ElastiCache
                                             ↓
                                        WebSocket → Real-time UI
```
- Gaming leaderboards
- Sports scores
- Social media engagement metrics
- Trading platform rankings

---

## AWS Kinesis Analytics Overview

### What is AWS Kinesis Data Analytics?

**AWS Kinesis Data Analytics** is a fully managed service for processing and analyzing streaming data using **SQL** or **Apache Flink**.

**Two Flavors**:
1. **Kinesis Data Analytics for SQL**: Simple SQL queries on streams
2. **Kinesis Data Analytics for Apache Flink**: Full Flink applications (Java/Scala/Python)

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Kinesis Data Analytics                      │
│                                                               │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │   Source    │───▶│  Flink Runtime   │───▶│ Destination │ │
│  │  (Kinesis)  │    │  (Managed)       │    │  (Kinesis)  │ │
│  └─────────────┘    │                  │    └─────────────┘ │
│                     │  - Auto-scaling  │                     │
│                     │  - Checkpointing │                     │
│                     │  - Monitoring    │                     │
│                     └──────────────────┘                     │
│                                                               │
│  You only write:                                             │
│  - SQL queries or Flink code                                 │
│                                                               │
│  AWS manages:                                                │
│  - Infrastructure provisioning                               │
│  - Auto-scaling                                              │
│  - Fault tolerance                                           │
│  - Monitoring                                                │
└──────────────────────────────────────────────────────────────┘
```

### Kinesis Analytics for SQL

**Capabilities**:
- Standard SQL syntax (ANSI SQL)
- Streaming extensions (tumbling/sliding windows)
- Built-in functions (aggregations, string manipulation)
- Pattern matching (MATCH_RECOGNIZE)
- Anomaly detection functions

**Example: Real-Time Aggregation**
```sql
CREATE OR REPLACE STREAM "DESTINATION_STREAM" (
    stock_symbol VARCHAR(10),
    avg_price     DOUBLE,
    min_price     DOUBLE,
    max_price     DOUBLE,
    total_volume  BIGINT,
    trade_count   BIGINT,
    window_start  TIMESTAMP,
    window_end    TIMESTAMP
);

CREATE OR REPLACE PUMP "STREAM_PUMP" AS
INSERT INTO "DESTINATION_STREAM"
SELECT STREAM
    stock_symbol,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    SUM(volume) AS total_volume,
    COUNT(*) AS trade_count,
    STEP(stock_trades.ROWTIME BY INTERVAL '1' MINUTE) AS window_start,
    STEP(stock_trades.ROWTIME BY INTERVAL '1' MINUTE) + INTERVAL '1' MINUTE AS window_end
FROM "SOURCE_STREAM_001"
WHERE stock_symbol IS NOT NULL
GROUP BY
    stock_symbol,
    STEP(ROWTIME BY INTERVAL '1' MINUTE);
```

**When to Use SQL**:
- ✅ Simple aggregations and filtering
- ✅ Quick prototyping
- ✅ Business analysts comfort with SQL
- ✅ No complex state management needed
- ❌ Complex CEP (Complex Event Processing)
- ❌ Custom algorithms
- ❌ External API calls

### Kinesis Analytics for Apache Flink

**Capabilities**:
- Full Flink DataStream API
- Flink SQL / Table API
- Stateful processing
- Custom operators
- External integrations
- Advanced windowing
- Machine learning integration

**Example: Flink DataStream API**
```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import WatermarkStrategy, Types
from pyflink.datastream.connectors.kinesis import KinesisSource

env = StreamExecutionEnvironment.get_execution_environment()

# Source: Kinesis Data Stream
kinesis_source = KinesisSource.builder() \
    .set_stream_arn("arn:aws:kinesis:us-east-1:123456789012:stream/stock-trades") \
    .set_starting_position(KinesisSourcePosition.TRIM_HORIZON) \
    .build()

stream = env.from_source(
    kinesis_source,
    WatermarkStrategy.for_monotonous_timestamps(),
    "Kinesis Source"
)

# Transformations
parsed = stream.map(lambda x: json.loads(x))
filtered = parsed.filter(lambda x: x['price'] > 100)

# Windowed aggregation
windowed = filtered \
    .key_by(lambda x: x['stock_symbol']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .aggregate(StockAggregator())

# Sink: Kinesis Data Stream
windowed.sink_to(kinesis_sink)

env.execute("Stock Analysis")
```

**When to Use Flink**:
- ✅ Complex stateful processing
- ✅ Custom business logic
- ✅ High throughput (millions of events/sec)
- ✅ Advanced windowing and CEP
- ✅ Machine learning model scoring
- ✅ External API integrations

### Key Features

**1. Exactly-Once Semantics**
```
┌─────────────────────────────────────────────────────────┐
│                  Fault Tolerance                         │
│                                                          │
│  Checkpoint 1  →  Checkpoint 2  →  Checkpoint 3         │
│  (t=0s)           (t=10s)           (t=20s)             │
│                                                          │
│  If failure at t=15s:                                   │
│  ↓                                                       │
│  Restore from Checkpoint 2                              │
│  Replay from t=10s to t=15s                             │
│  ↓                                                       │
│  No data loss, no duplicates!                           │
└─────────────────────────────────────────────────────────┘
```

**2. Auto-Scaling**
```
Events/sec:
│
│     ┌───┐                              ← Scale out to 4 KPUs
│     │   │   ┌───┐
│     │   │   │   │                      ← Scale out to 3 KPUs
│ ┌───┤   ├───┤   ├───┐
│ │   │   │   │   │   │                  ← Scale out to 2 KPUs
│ │   │   │   │   │   │   ┌──┐          ← Back to 1 KPU
├─┴───┴───┴───┴───┴───┴───┴──┴──────────→ Time
  0   5   10  15  20  25  30

KPU = Kinesis Processing Unit (1 vCPU + 4 GB memory)
```

**3. Application Snapshots**
- Point-in-time application state backup
- Deploy new code without data loss
- Rollback to previous version
- Disaster recovery

---

## Apache Flink for Analytics

### Flink SQL / Table API

**Flink SQL** provides a declarative way to build stream processing applications using standard SQL.

**Architecture**:
```
┌──────────────────────────────────────────┐
│           Flink SQL Engine                │
│                                           │
│  SQL Query                                │
│    ↓                                      │
│  SQL Parser                               │
│    ↓                                      │
│  Logical Plan Optimization                │
│    ↓                                      │
│  Physical Plan Generation                 │
│    ↓                                      │
│  DataStream API Execution                 │
└──────────────────────────────────────────┘
```

### Creating Tables from Streams

**1. Define Source Table**
```sql
CREATE TABLE stock_trades (
    stock_symbol STRING,
    price DOUBLE,
    volume INT,
    trade_time TIMESTAMP(3),
    WATERMARK FOR trade_time AS trade_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'stock-trades',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);
```

**2. Define Sink Table**
```sql
CREATE TABLE aggregated_trades (
    stock_symbol STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    avg_price DOUBLE,
    total_volume BIGINT,
    trade_count BIGINT,
    PRIMARY KEY (stock_symbol, window_start) NOT ENFORCED
) WITH (
    'connector' = 'kinesis',
    'stream' = 'aggregated-trades',
    'aws.region' = 'us-east-1',
    'format' = 'json'
);
```

**3. Query with Windows**
```sql
INSERT INTO aggregated_trades
SELECT
    stock_symbol,
    TUMBLE_START(trade_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(trade_time, INTERVAL '1' MINUTE) AS window_end,
    AVG(price) AS avg_price,
    SUM(volume) AS total_volume,
    COUNT(*) AS trade_count
FROM stock_trades
GROUP BY
    stock_symbol,
    TUMBLE(trade_time, INTERVAL '1' MINUTE);
```

### Window Types in Flink SQL

**1. Tumbling Windows**
```sql
-- Non-overlapping, fixed-size windows
SELECT
    window_start,
    window_end,
    COUNT(*) AS event_count
FROM TABLE(
    TUMBLE(TABLE events, DESCRIPTOR(event_time), INTERVAL '10' MINUTES)
)
GROUP BY window_start, window_end;
```

```
Timeline: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶
         [─────W1────][─────W2────][─────W3────]
         00:00-00:10  00:10-00:20  00:20-00:30
```

**2. Sliding (Hop) Windows**
```sql
-- Overlapping windows with fixed size and slide interval
SELECT
    window_start,
    window_end,
    COUNT(*) AS event_count
FROM TABLE(
    HOP(TABLE events, DESCRIPTOR(event_time), INTERVAL '5' MINUTES, INTERVAL '10' MINUTES)
)
GROUP BY window_start, window_end;
```

```
Timeline: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶
         [──────────W1──────────]
               [──────────W2──────────]
                     [──────────W3──────────]
         00:00               00:10               00:20
```

**3. Session Windows**
```sql
-- Dynamic windows based on inactivity gap
SELECT
    user_id,
    SESSION_START(event_time, INTERVAL '15' MINUTES) AS session_start,
    SESSION_END(event_time, INTERVAL '15' MINUTES) AS session_end,
    COUNT(*) AS events_in_session
FROM user_events
GROUP BY
    user_id,
    SESSION(event_time, INTERVAL '15' MINUTES);
```

```
User Activity:
Events:  ●  ●    ●  ●  ●      (15 min gap)      ●  ●  ●
         │Session 1   │                         │Session 2│
         └─────────────┘                        └─────────┘
```

### Time Semantics

**1. Event Time**
- Time when the event actually occurred
- Embedded in the event payload
- Correct for out-of-order events
- Requires watermarks

**2. Processing Time**
- Time when the event is processed by Flink
- Simple, low latency
- Not deterministic (reprocessing gives different results)

**3. Ingestion Time**
- Time when the event enters Flink
- Middle ground between event and processing time

**Choosing the Right Time**:
```
Use Case              | Time Semantic | Why?
──────────────────────┼───────────────┼──────────────────────────
Financial analytics   | Event Time    | Need accuracy
Low-latency alerts    | Processing    | Speed matters
Log processing        | Event Time    | Out-of-order common
Simple counting       | Processing    | Simplicity
```

### Watermarks

**Watermarks** tell Flink "all events with timestamp < watermark have arrived".

**Types**:
1. **Bounded Out-of-Orderness**
```python
WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(5)) \
    .with_timestamp_assigner(lambda event, ts: event['timestamp'])
```
- Watermark = max_timestamp - 5 seconds
- Allows events up to 5 seconds late

2. **Monotonous Timestamps**
```python
WatermarkStrategy \
    .for_monotonous_timestamps() \
    .with_timestamp_assigner(lambda event, ts: event['timestamp'])
```
- Watermark = max_timestamp
- Assumes events arrive in order (e.g., Kinesis single shard)

3. **With Idleness**
```python
WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(5)) \
    .with_idleness(Duration.of_minutes(1))
```
- Mark source as idle if no events for 1 minute
- Prevents blocking watermark progress

**Late Events Handling**:
```sql
CREATE TABLE events (
    event_id STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'events'
);

-- Events with event_time < (watermark - 10s) are dropped
-- Or: Send to side output for reprocessing
```

---

## Stream Analytics Patterns

### 1. Filtering

**Use Case**: Remove unwanted events to reduce processing cost.

**SQL**:
```sql
SELECT *
FROM stock_trades
WHERE price > 100 AND volume > 1000;
```

**Flink DataStream**:
```python
filtered = stream.filter(lambda x: x['price'] > 100 and x['volume'] > 1000)
```

### 2. Transformation

**Use Case**: Enrich or derive fields.

**SQL**:
```sql
SELECT
    stock_symbol,
    price,
    volume,
    price * volume AS trade_value,
    CASE
        WHEN price > 100 THEN 'HIGH'
        WHEN price > 50 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS price_category
FROM stock_trades;
```

**Flink DataStream**:
```python
enriched = stream.map(lambda x: {
    **x,
    'trade_value': x['price'] * x['volume'],
    'price_category': 'HIGH' if x['price'] > 100 else 'MEDIUM' if x['price'] > 50 else 'LOW'
})
```

### 3. Aggregation

**Use Case**: Calculate metrics over windows.

**SQL**:
```sql
SELECT
    stock_symbol,
    TUMBLE_START(trade_time, INTERVAL '1' MINUTE) AS window_start,
    COUNT(*) AS trade_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    SUM(volume) AS total_volume
FROM stock_trades
GROUP BY
    stock_symbol,
    TUMBLE(trade_time, INTERVAL '1' MINUTE);
```

**Flink DataStream**:
```python
aggregated = stream \
    .key_by(lambda x: x['stock_symbol']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .aggregate(
        avg_price=AverageAggregator('price'),
        min_price=MinAggregator('price'),
        max_price=MaxAggregator('price'),
        total_volume=SumAggregator('volume')
    )
```

### 4. Joining Streams

**Use Case**: Correlate events from multiple streams.

**SQL**:
```sql
-- Join trades with company info
SELECT
    t.stock_symbol,
    c.company_name,
    c.sector,
    t.price,
    t.volume
FROM stock_trades t
JOIN company_info c
    ON t.stock_symbol = c.stock_symbol;
```

**Interval Join** (time-bounded):
```sql
-- Join trades within 5 minutes of orders
SELECT
    o.order_id,
    o.stock_symbol,
    o.order_price,
    t.trade_price,
    ABS(t.trade_price - o.order_price) AS price_diff
FROM orders o
JOIN stock_trades t
    ON o.stock_symbol = t.stock_symbol
    AND t.trade_time BETWEEN o.order_time - INTERVAL '5' MINUTE
                         AND o.order_time + INTERVAL '5' MINUTE;
```

### 5. Deduplication

**Use Case**: Remove duplicate events.

**SQL**:
```sql
SELECT
    stock_symbol,
    price,
    volume,
    trade_time
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY stock_symbol, trade_time
            ORDER BY processing_time DESC
        ) AS row_num
    FROM stock_trades
)
WHERE row_num = 1;
```

### 6. Top-N

**Use Case**: Get top/bottom N records per group.

**SQL**:
```sql
-- Top 5 most traded stocks per minute
SELECT *
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY window_start
            ORDER BY total_volume DESC
        ) AS rank
    FROM (
        SELECT
            stock_symbol,
            TUMBLE_START(trade_time, INTERVAL '1' MINUTE) AS window_start,
            SUM(volume) AS total_volume
        FROM stock_trades
        GROUP BY
            stock_symbol,
            TUMBLE(trade_time, INTERVAL '1' MINUTE)
    )
)
WHERE rank <= 5;
```

### 7. Pattern Detection (CEP)

**Use Case**: Detect sequences of events.

**SQL with MATCH_RECOGNIZE**:
```sql
-- Detect flash crash: price drops >10% in 3 consecutive trades
SELECT *
FROM stock_trades
MATCH_RECOGNIZE (
    PARTITION BY stock_symbol
    ORDER BY trade_time
    MEASURES
        FIRST(A.price) AS initial_price,
        LAST(C.price) AS final_price,
        (FIRST(A.price) - LAST(C.price)) / FIRST(A.price) * 100 AS drop_percent
    ONE ROW PER MATCH
    AFTER MATCH SKIP TO NEXT ROW
    PATTERN (A B+ C)
    DEFINE
        B AS B.price < PREV(B.price, 1),
        C AS C.price < PREV(C.price, 1)
             AND C.price < FIRST(A.price) * 0.9
);
```

**Flink CEP**:
```python
from pyflink.cep import Pattern

# Define pattern
pattern = Pattern.begin("first", AfterMatchSkipStrategy.skip_to_last("first")) \
    .where(SimpleCondition(lambda x: True)) \
    .next("second") \
    .where(SimpleCondition(lambda x: x['price'] < x.prev('price'))) \
    .next("third") \
    .where(SimpleCondition(lambda x:
        x['price'] < x.prev('price') and
        x['price'] < x.first('price') * 0.9
    )) \
    .within(Time.minutes(5))

# Apply pattern
cep_stream = CEP.pattern(stream.key_by(lambda x: x['stock_symbol']), pattern)

# Process matches
alerts = cep_stream.select(FlashCrashDetector())
```

---

## Real-Time Aggregations

### Rolling Aggregations

**Use Case**: Continuously update aggregates as new data arrives.

**Example: Running Total**
```sql
SELECT
    stock_symbol,
    trade_time,
    price,
    volume,
    SUM(volume) OVER (
        PARTITION BY stock_symbol
        ORDER BY trade_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_volume
FROM stock_trades;
```

**Example: Moving Average**
```sql
SELECT
    stock_symbol,
    trade_time,
    price,
    AVG(price) OVER (
        PARTITION BY stock_symbol
        ORDER BY trade_time
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS ma_10
FROM stock_trades;
```

### Stateful Aggregations

**Use Case**: Maintain state across events for complex calculations.

**Flink Rich Function**:
```python
from pyflink.datastream import RuntimeContext
from pyflink.datastream.functions import KeyedProcessFunction, ProcessFunction

class RunningAverageFunction(KeyedProcessFunction):
    def __init__(self):
        self.sum_state = None
        self.count_state = None

    def open(self, runtime_context: RuntimeContext):
        # Initialize state
        from pyflink.datastream.state import ValueStateDescriptor
        from pyflink.common.typeinfo import Types

        self.sum_state = runtime_context.get_state(
            ValueStateDescriptor("sum", Types.DOUBLE())
        )
        self.count_state = runtime_context.get_state(
            ValueStateDescriptor("count", Types.LONG())
        )

    def process_element(self, value, ctx):
        # Get current state
        current_sum = self.sum_state.value() or 0.0
        current_count = self.count_state.value() or 0

        # Update state
        new_sum = current_sum + value['price']
        new_count = current_count + 1

        self.sum_state.update(new_sum)
        self.count_state.update(new_count)

        # Calculate average
        avg = new_sum / new_count

        yield {
            'stock_symbol': value['stock_symbol'],
            'timestamp': value['timestamp'],
            'running_avg': avg,
            'count': new_count
        }
```

### Approximate Aggregations

**Use Case**: Trade accuracy for performance on large datasets.

**1. HyperLogLog (Distinct Count)**
```sql
-- Approximate distinct count with 0.5% error
SELECT
    COUNT(DISTINCT stock_symbol) AS exact_count,
    APPROX_COUNT_DISTINCT(stock_symbol) AS approx_count
FROM stock_trades;
```

**2. T-Digest (Percentiles)**
```sql
-- Approximate median and 95th percentile
SELECT
    PERCENTILE_APPROX(price, 0.5) AS median_price,
    PERCENTILE_APPROX(price, 0.95) AS p95_price
FROM stock_trades;
```

**3. Count-Min Sketch (Frequency)**
- Estimate frequency of items in stream
- Memory-efficient for high-cardinality data

---

## Window Functions

### Types of Windows

**1. Tumbling Windows**
- Fixed size, non-overlapping
- Every event belongs to exactly one window

**Use Case**: Hourly/daily aggregations
```sql
SELECT
    TUMBLE_START(trade_time, INTERVAL '1' HOUR) AS hour,
    COUNT(*) AS trades_per_hour
FROM stock_trades
GROUP BY TUMBLE(trade_time, INTERVAL '1' HOUR);
```

**2. Sliding (Hopping) Windows**
- Fixed size, overlapping
- Every event belongs to multiple windows

**Use Case**: Moving averages, trend detection
```sql
-- 10-minute windows, sliding every 1 minute
SELECT
    HOP_START(trade_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE) AS window_start,
    AVG(price) AS ma_10_min
FROM stock_trades
GROUP BY
    stock_symbol,
    HOP(trade_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE);
```

**3. Session Windows**
- Dynamic size based on inactivity gap
- Each event starts or extends a session

**Use Case**: User sessions, activity bursts
```sql
-- Session ends after 30 minutes of inactivity
SELECT
    user_id,
    SESSION_START(event_time, INTERVAL '30' MINUTE) AS session_start,
    SESSION_END(event_time, INTERVAL '30' MINUTE) AS session_end,
    COUNT(*) AS events_in_session
FROM user_events
GROUP BY
    user_id,
    SESSION(event_time, INTERVAL '30' MINUTE);
```

### Window Triggers

**When does a window emit results?**

**1. Time-Based Triggers**
```python
# Fire when watermark passes window end
stream \
    .key_by(lambda x: x['key']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .trigger(EventTimeTrigger.create())
```

**2. Count-Based Triggers**
```python
# Fire every 100 events
stream \
    .window(...) \
    .trigger(CountTrigger.of(100))
```

**3. Custom Triggers**
```python
class EarlyTrigger(Trigger):
    def on_element(self, element, timestamp, window, ctx):
        # Fire early if specific condition met
        if element['urgent']:
            return TriggerResult.FIRE
        return TriggerResult.CONTINUE
```

### Allowed Lateness

**Handle late events gracefully**:
```python
stream \
    .key_by(lambda x: x['key']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .allowed_lateness(Time.minutes(5)) \  # Accept events up to 5 min late
    .side_output_late_data(late_data_tag) \  # Send very late events to side output
    .aggregate(MyAggregator())
```

**Timeline**:
```
Window: [10:00 - 10:01)
Watermark reaches 10:01 → Window fires (results emitted)
Late event arrives at 10:01:30 → Still accepted, update results
Late event arrives at 10:06:30 → Sent to side output (too late)
```

---

## Complex Event Processing

### What is CEP?

**Complex Event Processing (CEP)** detects patterns and relationships across multiple events over time.

**Capabilities**:
- Sequence detection
- Temporal constraints
- Negation (absence of events)
- Quantifiers (one-or-more, optional)
- Boolean combinations

### Pattern Definition

**Flink CEP Syntax**:
```python
from pyflink.cep import Pattern, AfterMatchSkipStrategy

pattern = Pattern.begin("start", AfterMatchSkipStrategy.skip_to_last("start")) \
    .where(SimpleCondition(lambda x: x['type'] == 'login')) \
    .next("middle") \
    .where(SimpleCondition(lambda x: x['type'] == 'purchase' and x['amount'] > 1000)) \
    .times(2, 5) \  # 2 to 5 occurrences
    .followed_by("end") \
    .where(SimpleCondition(lambda x: x['type'] == 'logout')) \
    .within(Time.hours(1))
```

### Common CEP Patterns

**1. Fraud Detection Pattern**
```python
# Detect: Login → Multiple failed payments → Successful payment
fraud_pattern = Pattern.begin("login") \
    .where(SimpleCondition(lambda x: x['event'] == 'login')) \
    .next("failed_payments") \
    .where(SimpleCondition(lambda x: x['event'] == 'payment' and x['status'] == 'failed')) \
    .times(3, 10) \
    .followed_by("success") \
    .where(SimpleCondition(lambda x: x['event'] == 'payment' and x['status'] == 'success')) \
    .within(Time.minutes(10))
```

**2. User Abandonment Pattern**
```python
# Detect: Add to cart → No purchase within 1 hour
abandonment_pattern = Pattern.begin("cart") \
    .where(SimpleCondition(lambda x: x['event'] == 'add_to_cart')) \
    .followed_by_any("purchase") \
    .where(SimpleCondition(lambda x: x['event'] == 'purchase')) \
    .optional() \
    .within(Time.hours(1))

# Check for missing purchase
def pattern_select(matches):
    if 'purchase' not in matches:
        # Send retargeting campaign
        return {'user_id': matches['cart']['user_id'], 'action': 'retarget'}
```

**3. Anomaly Detection Pattern**
```python
# Detect: Temperature spike (3 consecutive readings > threshold)
anomaly_pattern = Pattern.begin("first") \
    .where(SimpleCondition(lambda x: x['temperature'] > 100)) \
    .next("second") \
    .where(SimpleCondition(lambda x: x['temperature'] > 100)) \
    .next("third") \
    .where(SimpleCondition(lambda x: x['temperature'] > 100)) \
    .within(Time.minutes(5))
```

### SQL Pattern Matching (MATCH_RECOGNIZE)

```sql
-- Detect stock price manipulation (pump and dump)
SELECT *
FROM stock_trades
MATCH_RECOGNIZE (
    PARTITION BY stock_symbol
    ORDER BY trade_time
    MEASURES
        FIRST(A.trade_time) AS pump_start,
        LAST(C.trade_time) AS dump_end,
        FIRST(A.price) AS initial_price,
        MAX(B.price) AS peak_price,
        LAST(C.price) AS final_price
    ONE ROW PER MATCH
    AFTER MATCH SKIP TO NEXT ROW
    PATTERN (A B+ C+)
    WITHIN INTERVAL '2' HOUR
    DEFINE
        -- Pump: price increases
        B AS B.price > PREV(B.price),
        -- Dump: price decreases rapidly
        C AS C.price < PREV(C.price)
             AND LAST(C.price, 1) < MAX(B.price) * 0.8
);
```

---

## Real-Time ML Scoring

### Model Serving Architectures

**1. Embedded Model (In-Process)**
```python
from pyflink.datastream.functions import MapFunction
import joblib

class ModelScorer(MapFunction):
    def __init__(self, model_path):
        self.model = None
        self.model_path = model_path

    def open(self, runtime_context):
        # Load model once
        self.model = joblib.load(self.model_path)

    def map(self, value):
        features = extract_features(value)
        score = self.model.predict_proba([features])[0][1]

        return {
            **value,
            'fraud_score': score,
            'is_fraud': score > 0.8
        }

stream.map(ModelScorer('fraud_model.pkl'))
```

**2. External Model Server (Async I/O)**
```python
from pyflink.datastream.functions import AsyncFunction
import aiohttp

class ModelServerScorer(AsyncFunction):
    def __init__(self, model_endpoint):
        self.endpoint = model_endpoint
        self.session = None

    async def open(self):
        self.session = aiohttp.ClientSession()

    async def async_invoke(self, value, result_future):
        features = extract_features(value)

        async with self.session.post(
            self.endpoint,
            json={'features': features}
        ) as response:
            result = await response.json()

            result_future.complete({
                **value,
                'fraud_score': result['score'],
                'is_fraud': result['score'] > 0.8
            })

# Apply async I/O
scored_stream = AsyncDataStream.unordered_wait(
    stream,
    ModelServerScorer('http://model-server:8080/predict'),
    timeout=1000,  # 1 second timeout
    capacity=100   # Max 100 concurrent requests
)
```

**3. AWS SageMaker Integration**
```python
import boto3

class SageMakerScorer(MapFunction):
    def __init__(self, endpoint_name):
        self.endpoint_name = endpoint_name
        self.client = None

    def open(self, runtime_context):
        self.client = boto3.client('sagemaker-runtime')

    def map(self, value):
        features = extract_features(value)

        response = self.client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps({'instances': [features]})
        )

        prediction = json.loads(response['Body'].read())
        score = prediction['predictions'][0]['score']

        return {
            **value,
            'fraud_score': score,
            'is_fraud': score > 0.8
        }
```

### Feature Engineering in Streams

**Real-Time Feature Computation**:
```python
class FeatureEngineer(KeyedProcessFunction):
    def open(self, runtime_context):
        # State for historical features
        self.transaction_history = runtime_context.get_list_state(
            ListStateDescriptor("history", Types.PICKLED_BYTE_ARRAY())
        )
        self.velocity_state = runtime_context.get_value_state(
            ValueStateDescriptor("velocity", Types.MAP(Types.STRING(), Types.INT()))
        )

    def process_element(self, transaction, ctx):
        user_id = transaction['user_id']

        # Get transaction history
        history = list(self.transaction_history.get())

        # Feature 1: Transaction count in last 1 hour
        one_hour_ago = ctx.timestamp() - 3600000
        recent_count = sum(1 for t in history if t['timestamp'] > one_hour_ago)

        # Feature 2: Average transaction amount
        avg_amount = sum(t['amount'] for t in history) / len(history) if history else 0

        # Feature 3: Transaction velocity (transactions per minute)
        velocity = self.velocity_state.value() or {}
        current_minute = ctx.timestamp() // 60000
        velocity[str(current_minute)] = velocity.get(str(current_minute), 0) + 1

        # Clean old velocity data
        velocity = {k: v for k, v in velocity.items() if int(k) > current_minute - 60}
        self.velocity_state.update(velocity)

        # Feature 4: Deviation from user's average
        amount_deviation = abs(transaction['amount'] - avg_amount) / avg_amount if avg_amount > 0 else 0

        # Feature 5: Time since last transaction
        time_since_last = (ctx.timestamp() - history[-1]['timestamp']) if history else 0

        # Update history (keep last 100 transactions)
        history.append(transaction)
        if len(history) > 100:
            history = history[-100:]
        self.transaction_history.clear()
        for t in history:
            self.transaction_history.add(t)

        # Yield enriched transaction
        yield {
            **transaction,
            'features': {
                'recent_count': recent_count,
                'avg_amount': avg_amount,
                'velocity': sum(velocity.values()),
                'amount_deviation': amount_deviation,
                'time_since_last_ms': time_since_last
            }
        }
```

### Online Learning

**Incremental Model Updates**:
```python
from river import linear_model, metrics, preprocessing

class OnlineLearner(KeyedProcessFunction):
    def __init__(self):
        self.model = None
        self.metric = None

    def open(self, runtime_context):
        # Initialize online learning model
        self.model = preprocessing.StandardScaler() | linear_model.LogisticRegression()
        self.metric = metrics.ROCAUC()

    def process_element(self, event, ctx):
        # Extract features and label
        x = event['features']
        y = event['label']  # Ground truth (if available)

        # Predict
        y_pred = self.model.predict_proba_one(x)

        # Evaluate (if label available)
        if y is not None:
            self.metric.update(y, y_pred[True])

            # Learn from this example
            self.model.learn_one(x, y)

        yield {
            **event,
            'prediction': y_pred[True],
            'model_auc': self.metric.get()
        }
```

---

## Summary

### Key Takeaways

**1. Real-Time Analytics**
- Process streaming data with sub-second latency
- Use SQL or Flink for different complexity levels
- Choose time semantics carefully (event vs processing time)

**2. AWS Kinesis Analytics**
- Fully managed Apache Flink
- Auto-scaling and fault tolerance
- Exactly-once processing guarantees

**3. Windows**
- Tumbling: Non-overlapping, fixed-size
- Sliding: Overlapping, fixed-size with slide interval
- Session: Dynamic, based on inactivity gaps

**4. Complex Event Processing**
- Detect patterns across multiple events
- Temporal constraints and quantifiers
- Essential for fraud detection, anomaly detection

**5. Real-Time ML**
- Embed models or use external servers
- Async I/O for low latency
- Online learning for model adaptation

### Best Practices

1. **Start with SQL**: Prototype quickly, scale to Flink when needed
2. **Use Event Time**: Correct results despite out-of-order events
3. **Set Reasonable Watermarks**: Balance latency vs completeness
4. **Monitor Metrics**: Track lag, throughput, error rates
5. **Test Thoroughly**: Simulate late events, failures, load spikes

### Next Steps

- Read `architecture.md` for AWS architecture patterns
- Complete exercises to build hands-on experience
- Explore `resources.md` for additional learning materials

---

**Previous**: [README.md](../README.md) - Module Overview
**Next**: [architecture.md](./architecture.md) - AWS Real-Time Analytics Architectures
