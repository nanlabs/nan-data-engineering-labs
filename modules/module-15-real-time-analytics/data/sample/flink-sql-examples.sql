-- Module 15: Real-Time Analytics - Flink SQL Examples
-- Complete SQL examples for all window types and analytics patterns

-- ============================================================================
-- SECTION 1: TABLE DEFINITIONS
-- ============================================================================

-- Source table: Events from Kinesis Data Stream
CREATE TABLE events_source (
    event_type VARCHAR,
    event_timestamp TIMESTAMP(3),
    user_id VARCHAR,
    session_id VARCHAR,
    page_url VARCHAR,
    product_id VARCHAR,
    product_price DOUBLE,
    quantity INT,
    device VARCHAR,
    country VARCHAR,
    WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'events-stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

-- Sink table: Aggregated results to Kinesis
CREATE TABLE aggregated_sink (
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    event_type VARCHAR,
    event_count BIGINT,
    unique_users BIGINT,
    total_revenue DOUBLE,
    avg_price DOUBLE
) WITH (
    'connector' = 'kinesis',
    'stream' = 'aggregated-stream',
    'aws.region' = 'us-east-1',
    'format' = 'json'
);

-- Sink table: Results to DynamoDB
CREATE TABLE realtime_metrics (
    metric_name VARCHAR,
    metric_timestamp TIMESTAMP(3),
    metric_value DOUBLE,
    metadata STRING,
    PRIMARY KEY (metric_name, metric_timestamp) NOT ENFORCED
) WITH (
    'connector' = 'dynamodb',
    'table-name' = 'realtime-aggregates',
    'aws.region' = 'us-east-1'
);

-- ============================================================================
-- SECTION 2: TUMBLING WINDOW QUERIES (Non-overlapping fixed windows)
-- ============================================================================

-- Example 1: Count events per minute by type
INSERT INTO aggregated_sink
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
    TUMBLE_END(event_timestamp, INTERVAL '1' MINUTE) as window_end,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(product_price * quantity) as total_revenue,
    AVG(product_price) as avg_price
FROM events_source
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
    event_type;

-- Example 2: Top pages per 5-minute window
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
    page_url,
    COUNT(*) as views,
    COUNT(DISTINCT user_id) as unique_visitors
FROM events_source
WHERE event_type = 'page_view'
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '5' MINUTE),
    page_url
ORDER BY views DESC
LIMIT 10;

-- Example 3: Revenue by country per hour
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '1' HOUR) as hour_start,
    country,
    COUNT(*) as total_purchases,
    SUM(product_price * quantity) as total_revenue,
    AVG(product_price * quantity) as avg_order_value
FROM events_source
WHERE event_type = 'purchase'
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' HOUR),
    country;

-- ============================================================================
-- SECTION 3: SLIDING (HOP) WINDOW QUERIES (Overlapping windows)
-- ============================================================================

-- Example 4: Moving average of events over 5 minutes, updated every minute
SELECT
    HOP_START(event_timestamp, INTERVAL '1' MINUTE, INTERVAL '5' MINUTE) as window_start,
    HOP_END(event_timestamp, INTERVAL '1' MINUTE, INTERVAL '5' MINUTE) as window_end,
    event_type,
    COUNT(*) as event_count,
    COUNT(*) / 5.0 as events_per_minute,
    COUNT(DISTINCT user_id) as unique_users
FROM events_source
GROUP BY
    HOP(event_timestamp, INTERVAL '1' MINUTE, INTERVAL '5' MINUTE),
    event_type;

-- Example 5: Sliding window for anomaly detection (sudden traffic spikes)
WITH traffic_metrics AS (
    SELECT
        HOP_START(event_timestamp, INTERVAL '30' SECOND, INTERVAL '2' MINUTE) as window_start,
        COUNT(*) as event_count,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT session_id) as unique_sessions
    FROM events_source
    GROUP BY HOP(event_timestamp, INTERVAL '30' SECOND, INTERVAL '2' MINUTE)
)
SELECT
    window_start,
    event_count,
    unique_users,
    CASE
        WHEN event_count > 1000 THEN 'HIGH_TRAFFIC'
        WHEN event_count > 500 THEN 'MEDIUM_TRAFFIC'
        ELSE 'NORMAL_TRAFFIC'
    END as traffic_level
FROM traffic_metrics;

-- Example 6: Rolling conversion rate (add_to_cart -> purchase)
WITH cart_events AS (
    SELECT
        HOP_START(event_timestamp, INTERVAL '5' MINUTE, INTERVAL '15' MINUTE) as window_start,
        COUNT(*) FILTER (WHERE event_type = 'add_to_cart') as add_to_cart_count,
        COUNT(*) FILTER (WHERE event_type = 'purchase') as purchase_count
    FROM events_source
    GROUP BY HOP(event_timestamp, INTERVAL '5' MINUTE, INTERVAL '15' MINUTE)
)
SELECT
    window_start,
    add_to_cart_count,
    purchase_count,
    CAST(purchase_count AS DOUBLE) / NULLIF(add_to_cart_count, 0) * 100 as conversion_rate_pct
FROM cart_events
WHERE add_to_cart_count > 0;

-- ============================================================================
-- SECTION 4: SESSION WINDOW QUERIES (Activity-based dynamic windows)
-- ============================================================================

-- Example 7: User sessions with 10-minute inactivity gap
SELECT
    SESSION_START(event_timestamp, INTERVAL '10' MINUTE) as session_start,
    SESSION_END(event_timestamp, INTERVAL '10' MINUTE) as session_end,
    user_id,
    COUNT(*) as event_count,
    COUNT(DISTINCT page_url) as pages_visited,
    MAX(event_timestamp) - MIN(event_timestamp) as session_duration,
    SUM(product_price * quantity) as session_revenue
FROM events_source
GROUP BY
    SESSION(event_timestamp, INTERVAL '10' MINUTE),
    user_id;

-- Example 8: Abandoned cart detection (session ended without purchase)
WITH user_sessions AS (
    SELECT
        SESSION_START(event_timestamp, INTERVAL '10' MINUTE) as session_start,
        SESSION_END(event_timestamp, INTERVAL '10' MINUTE) as session_end,
        user_id,
        session_id,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as has_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as has_purchase
    FROM events_source
    GROUP BY
        SESSION(event_timestamp, INTERVAL '10' MINUTE),
        user_id,
        session_id
)
SELECT
    session_start,
    session_end,
    user_id,
    session_id,
    'ABANDONED_CART' as event_type
FROM user_sessions
WHERE has_cart = 1 AND has_purchase = 0;

-- ============================================================================
-- SECTION 5: STREAM JOINS
-- ============================================================================

-- Example 9: Regular join between two streams (within same window)
-- Join page views with purchases within same 1-hour window
SELECT
    v.user_id,
    v.page_url,
    v.event_timestamp as view_time,
    p.event_timestamp as purchase_time,
    p.product_id,
    p.product_price
FROM
    (SELECT * FROM events_source WHERE event_type = 'page_view') v
JOIN
    (SELECT * FROM events_source WHERE event_type = 'purchase') p
ON v.user_id = p.user_id
WHERE v.event_timestamp BETWEEN p.event_timestamp - INTERVAL '1' HOUR
                            AND p.event_timestamp;

-- Example 10: Interval join for click-to-purchase attribution
SELECT
    c.user_id,
    c.product_id as clicked_product,
    c.event_timestamp as click_time,
    p.product_id as purchased_product,
    p.event_timestamp as purchase_time,
    TIMESTAMPDIFF(SECOND, c.event_timestamp, p.event_timestamp) as seconds_to_purchase
FROM
    (SELECT * FROM events_source WHERE event_type = 'click') c
JOIN
    (SELECT * FROM events_source WHERE event_type = 'purchase') p
ON c.user_id = p.user_id AND c.product_id = p.product_id
WHERE p.event_timestamp BETWEEN c.event_timestamp
                            AND c.event_timestamp + INTERVAL '30' MINUTE;

-- ============================================================================
-- SECTION 6: TOP-N QUERIES
-- ============================================================================

-- Example 11: Top 5 products by revenue in last 1 hour (continuous query)
SELECT *
FROM (
    SELECT
        product_id,
        product_name,
        COUNT(*) as purchase_count,
        SUM(product_price * quantity) as total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY TUMBLE(event_timestamp, INTERVAL '1' HOUR)
            ORDER BY SUM(product_price * quantity) DESC
        ) as revenue_rank
    FROM events_source
    WHERE event_type = 'purchase'
    GROUP BY
        TUMBLE(event_timestamp, INTERVAL '1' HOUR),
        product_id,
        product_name
)
WHERE revenue_rank <= 5;

-- Example 12: Most active users per 5-minute window
SELECT *
FROM (
    SELECT
        TUMBLE_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
        user_id,
        COUNT(*) as event_count,
        ROW_NUMBER() OVER (
            PARTITION BY TUMBLE(event_timestamp, INTERVAL '5' MINUTE)
            ORDER BY COUNT(*) DESC
        ) as activity_rank
    FROM events_source
    GROUP BY
        TUMBLE(event_timestamp, INTERVAL '5' MINUTE),
        user_id
)
WHERE activity_rank <= 10;

-- ============================================================================
-- SECTION 7: DEDUPLICATION
-- ============================================================================

-- Example 13: Deduplicate events by user and timestamp (keep first occurrence)
SELECT
    user_id,
    event_type,
    event_timestamp,
    product_id,
    product_price
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, event_type,
                         DATE_FORMAT(event_timestamp, 'yyyy-MM-dd HH:mm')
            ORDER BY event_timestamp ASC
        ) as rn
    FROM events_source
)
WHERE rn = 1;

-- ============================================================================
-- SECTION 8: COMPLEX EVENT PROCESSING WITH MATCH_RECOGNIZE
-- ============================================================================

-- Example 14: Detect fraud pattern - multiple failed payments then success
SELECT *
FROM events_source
MATCH_RECOGNIZE (
    PARTITION BY user_id
    ORDER BY event_timestamp
    MEASURES
        FIRST(A.event_timestamp) as first_attempt,
        LAST(C.event_timestamp) as final_success,
        COUNT(B.*) as failed_attempts
    ONE ROW PER MATCH
    AFTER MATCH SKIP TO LAST C
    PATTERN (A B{3,5} C)
    WITHIN INTERVAL '10' MINUTE
    DEFINE
        A AS A.event_type = 'login',
        B AS B.event_type = 'payment_attempt' AND B.success = false,
        C AS C.event_type = 'payment_attempt' AND C.success = true
) AS fraud_patterns;

-- Example 15: Detect temperature anomaly - 3 consecutive high readings
SELECT *
FROM events_source
MATCH_RECOGNIZE (
    PARTITION BY device_id
    ORDER BY event_timestamp
    MEASURES
        FIRST(A.event_timestamp) as anomaly_start,
        LAST(C.event_timestamp) as anomaly_end,
        FIRST(A.value) as first_value,
        LAST(C.value) as last_value
    ONE ROW PER MATCH
    AFTER MATCH SKIP PAST LAST ROW
    PATTERN (A B C)
    WITHIN INTERVAL '5' MINUTE
    DEFINE
        A AS A.event_type = 'sensor_reading'
             AND A.sensor_type = 'temperature'
             AND A.value > 80,
        B AS B.event_type = 'sensor_reading'
             AND B.sensor_type = 'temperature'
             AND B.value > 80,
        C AS C.event_type = 'sensor_reading'
             AND C.sensor_type = 'temperature'
             AND C.value > 80
) AS temperature_anomalies;

-- Example 16: User abandonment pattern - view product but no action in 5 minutes
SELECT *
FROM events_source
MATCH_RECOGNIZE (
    PARTITION BY user_id
    ORDER BY event_timestamp
    MEASURES
        A.product_id as viewed_product,
        A.event_timestamp as view_time
    ONE ROW PER MATCH
    AFTER MATCH SKIP TO LAST A
    PATTERN (A)
    WITHIN INTERVAL '5' MINUTE
    DEFINE
        A AS A.event_type = 'page_view'
             AND A.page_url LIKE '/products/%'
) AS potential_abandonment;

-- ============================================================================
-- SECTION 9: LATE DATA HANDLING
-- ============================================================================

-- Example 17: Handle late events with allowed lateness
CREATE TABLE events_with_lateness (
    event_type VARCHAR,
    event_timestamp TIMESTAMP(3),
    user_id VARCHAR,
    product_price DOUBLE,
    WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'events-stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- Query with allowed lateness in Flink configuration
-- SET 'table.exec.state.ttl' = '1 h';
-- SET 'pipeline.time-characteristic' = 'EventTime';

SELECT
    TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
    event_type,
    COUNT(*) as event_count,
    SUM(product_price) as total_revenue
FROM events_with_lateness
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' MINUTE),
    event_type;

-- ============================================================================
-- SECTION 10: PRODUCTION MONITORING QUERIES
-- ============================================================================

-- Example 18: Real-time quality metrics
INSERT INTO realtime_metrics
SELECT
    'events_per_second' as metric_name,
    TUMBLE_START(event_timestamp, INTERVAL '1' SECOND) as metric_timestamp,
    CAST(COUNT(*) AS DOUBLE) as metric_value,
    JSON_OBJECT('event_type' VALUE event_type) as metadata
FROM events_source
GROUP BY
    TUMBLE(event_timestamp, INTERVAL '1' SECOND),
    event_type;

-- Example 19: Revenue monitoring with alerting threshold
SELECT
    TUMBLE_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
    SUM(product_price * quantity) as revenue,
    CASE
        WHEN SUM(product_price * quantity) < 1000 THEN 'ALERT_LOW_REVENUE'
        WHEN SUM(product_price * quantity) > 50000 THEN 'ALERT_HIGH_REVENUE'
        ELSE 'NORMAL'
    END as alert_status
FROM events_source
WHERE event_type = 'purchase'
GROUP BY TUMBLE(event_timestamp, INTERVAL '5' MINUTE);

-- Example 20: Error rate monitoring
WITH event_stats AS (
    SELECT
        TUMBLE_START(event_timestamp, INTERVAL '1' MINUTE) as window_start,
        COUNT(*) as total_events,
        COUNT(*) FILTER (WHERE event_type = 'error') as error_events
    FROM events_source
    GROUP BY TUMBLE(event_timestamp, INTERVAL '1' MINUTE)
)
SELECT
    window_start,
    total_events,
    error_events,
    CAST(error_events AS DOUBLE) / total_events * 100 as error_rate_pct,
    CASE
        WHEN CAST(error_events AS DOUBLE) / total_events > 0.05 THEN 'CRITICAL'
        WHEN CAST(error_events AS DOUBLE) / total_events > 0.01 THEN 'WARNING'
        ELSE 'OK'
    END as health_status
FROM event_stats
WHERE total_events > 0;
