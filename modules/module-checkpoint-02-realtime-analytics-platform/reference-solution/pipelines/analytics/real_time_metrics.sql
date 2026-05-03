-- Real-Time Metrics Dashboard
-- Flink SQL Application for Comprehensive Analytics
--
-- Purpose:
--   Calculate real-time business metrics across multiple dimensions
--   and time windows for operational dashboards
--
-- Metrics Calculated:
--   - Ride metrics: count, completion rate, cancellation rate
--   - Revenue metrics: total, by payment method, average per ride
--   - Performance metrics: wait time, ride duration, driver utilization
--   - Customer metrics: satisfaction (ratings), retention indicators
--
-- Windows:
--   - 1-minute: Real-time operational metrics
--   - 5-minute: Tactical decision making
--   - 1-hour: Strategic trending
--
-- Output:
--   - DynamoDB aggregated_metrics table (for dashboard queries)
--   - S3 (for historical analysis and reporting)

-- =============================================================================
-- CREATE SOURCE TABLES
-- =============================================================================

-- Rides Stream
CREATE TABLE rides_source (
    ride_id VARCHAR(50),
    event_type VARCHAR(20),
    customer_id VARCHAR(50),
    driver_id VARCHAR(50),
    city VARCHAR(50),
    pickup_lat DOUBLE,
    pickup_lon DOUBLE,
    dropoff_lat DOUBLE,
    dropoff_lon DOUBLE,
    `timestamp` TIMESTAMP(3),
    status VARCHAR(20),
    estimated_fare DOUBLE,
    actual_fare DOUBLE,
    actual_distance_miles DOUBLE,
    actual_duration_minutes DOUBLE,
    wait_time_minutes DOUBLE,
    tip_amount DOUBLE,
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'rides_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- Payments Stream
CREATE TABLE payments_source (
    payment_id VARCHAR(50),
    ride_id VARCHAR(50),
    customer_id VARCHAR(50),
    amount DOUBLE,
    payment_method VARCHAR(20),
    status VARCHAR(20),
    `timestamp` TIMESTAMP(3),
    fraud_score INT,
    transaction_fee DOUBLE,
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'payments_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- Ratings Stream
CREATE TABLE ratings_source (
    rating_id VARCHAR(50),
    ride_id VARCHAR(50),
    customer_id VARCHAR(50),
    driver_id VARCHAR(50),
    rating INT,
    `timestamp` TIMESTAMP(3),
    is_positive BOOLEAN,
    tip_given BOOLEAN,
    tip_amount DOUBLE,
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'ratings_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- =============================================================================
-- CREATE OUTPUT TABLES
-- =============================================================================

-- DynamoDB Sink for Real-Time Dashboard
CREATE TABLE metrics_dynamodb_sink (
    metric_key VARCHAR(200),  -- Format: {metric_type}#{city}#{window_start}
    metric_type VARCHAR(50),
    city VARCHAR(50),
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    window_duration_minutes INT,

    -- Ride metrics
    rides_requested BIGINT,
    rides_started BIGINT,
    rides_completed BIGINT,
    rides_cancelled BIGINT,
    completion_rate DOUBLE,

    -- Revenue metrics
    total_revenue DOUBLE,
    avg_fare DOUBLE,
    total_tips DOUBLE,

    -- Performance metrics
    avg_wait_time_minutes DOUBLE,
    avg_ride_duration_minutes DOUBLE,
    avg_distance_miles DOUBLE,

    -- Customer metrics
    avg_rating DOUBLE,
    positive_rating_rate DOUBLE,

    calculation_timestamp TIMESTAMP(3),
    ttl BIGINT
) WITH (
    'connector' = 'dynamodb',
    'table-name' = 'aggregated_metrics',
    'aws.region' = 'us-east-1'
);

-- S3 Sink for Historical Analysis
CREATE TABLE metrics_s3_sink (
    metric_type VARCHAR(50),
    city VARCHAR(50),
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    window_duration_minutes INT,
    rides_requested BIGINT,
    rides_started BIGINT,
    rides_completed BIGINT,
    rides_cancelled BIGINT,
    completion_rate DOUBLE,
    total_revenue DOUBLE,
    avg_fare DOUBLE,
    total_tips DOUBLE,
    avg_wait_time_minutes DOUBLE,
    avg_ride_duration_minutes DOUBLE,
    avg_distance_miles DOUBLE,
    avg_rating DOUBLE,
    positive_rating_rate DOUBLE,
    calculation_timestamp TIMESTAMP(3),
    `date` VARCHAR(10),
    `hour` VARCHAR(2)
) PARTITIONED BY (`date`, `hour`)
WITH (
    'connector' = 'filesystem',
    'path' = 's3://rideshare-analytics/real-time-metrics/',
    'format' = 'json'
);

-- =============================================================================
-- INTERMEDIATE VIEWS: 1-MINUTE WINDOW METRICS
-- =============================================================================

-- 1-Minute Ride Metrics
CREATE VIEW ride_metrics_1min AS
SELECT
    city,
    TUMBLE_START(`timestamp`, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '1' MINUTE) AS window_end,

    -- Count by event type
    COUNT(CASE WHEN event_type = 'ride_requested' THEN 1 END) AS rides_requested,
    COUNT(CASE WHEN event_type = 'ride_started' THEN 1 END) AS rides_started,
    COUNT(CASE WHEN event_type = 'ride_completed' THEN 1 END) AS rides_completed,

    -- Calculate completion rate (started rides that completed)
    CASE
        WHEN COUNT(CASE WHEN event_type = 'ride_started' THEN 1 END) > 0
        THEN CAST(COUNT(CASE WHEN event_type = 'ride_completed' THEN 1 END) AS DOUBLE) /
             CAST(COUNT(CASE WHEN event_type = 'ride_started' THEN 1 END) AS DOUBLE)
        ELSE 0.0
    END AS completion_rate,

    -- Performance metrics (only for completed rides)
    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_fare END) AS avg_fare,
    SUM(CASE WHEN event_type = 'ride_completed' THEN actual_fare END) AS total_revenue,
    SUM(CASE WHEN event_type = 'ride_completed' THEN tip_amount END) AS total_tips,
    AVG(CASE WHEN event_type = 'ride_started' THEN wait_time_minutes END) AS avg_wait_time,
    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_duration_minutes END) AS avg_duration,
    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_distance_miles END) AS avg_distance

FROM rides_source
GROUP BY
    city,
    TUMBLE(`timestamp`, INTERVAL '1' MINUTE);

-- =============================================================================
-- INTERMEDIATE VIEWS: 5-MINUTE WINDOW METRICS
-- =============================================================================

-- 5-Minute Comprehensive Ride Metrics
CREATE VIEW ride_metrics_5min AS
SELECT
    city,
    TUMBLE_START(`timestamp`, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '5' MINUTE) AS window_end,

    COUNT(CASE WHEN event_type = 'ride_requested' THEN 1 END) AS rides_requested,
    COUNT(CASE WHEN event_type = 'ride_started' THEN 1 END) AS rides_started,
    COUNT(CASE WHEN event_type = 'ride_completed' THEN 1 END) AS rides_completed,

    -- Cancelled = requested but never started (approximate)
    COUNT(CASE WHEN event_type = 'ride_requested' THEN 1 END) -
    COUNT(CASE WHEN event_type = 'ride_started' THEN 1 END) AS rides_cancelled,

    CASE
        WHEN COUNT(CASE WHEN event_type = 'ride_requested' THEN 1 END) > 0
        THEN CAST(COUNT(CASE WHEN event_type = 'ride_completed' THEN 1 END) AS DOUBLE) /
             CAST(COUNT(CASE WHEN event_type = 'ride_requested' THEN 1 END) AS DOUBLE)
        ELSE 0.0
    END AS completion_rate,

    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_fare END) AS avg_fare,
    SUM(CASE WHEN event_type = 'ride_completed' THEN actual_fare END) AS total_revenue,
    SUM(CASE WHEN event_type = 'ride_completed' THEN tip_amount END) AS total_tips,
    AVG(CASE WHEN event_type = 'ride_started' THEN wait_time_minutes END) AS avg_wait_time,
    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_duration_minutes END) AS avg_duration,
    AVG(CASE WHEN event_type = 'ride_completed' THEN actual_distance_miles END) AS avg_distance

FROM rides_source
GROUP BY
    city,
    TUMBLE(`timestamp`, INTERVAL '5' MINUTE);

-- 5-Minute Payment Metrics by Method
CREATE VIEW payment_metrics_5min AS
SELECT
    payment_method,
    TUMBLE_START(`timestamp`, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '5' MINUTE) AS window_end,

    COUNT(*) AS payment_count,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS successful_payments,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) AS failed_payments,

    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) AS total_revenue,
    AVG(CASE WHEN status = 'completed' THEN amount END) AS avg_transaction_amount,
    SUM(transaction_fee) AS total_fees,

    AVG(fraud_score) AS avg_fraud_score,
    COUNT(CASE WHEN fraud_score > 70 THEN 1 END) AS high_risk_count

FROM payments_source
GROUP BY
    payment_method,
    TUMBLE(`timestamp`, INTERVAL '5' MINUTE);

-- 5-Minute Rating Metrics
CREATE VIEW rating_metrics_5min AS
SELECT
    TUMBLE_START(`timestamp`, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '5' MINUTE) AS window_end,

    COUNT(*) AS total_ratings,
    AVG(CAST(rating AS DOUBLE)) AS avg_rating,

    -- Star distribution
    COUNT(CASE WHEN rating = 5 THEN 1 END) AS five_star,
    COUNT(CASE WHEN rating = 4 THEN 1 END) AS four_star,
    COUNT(CASE WHEN rating = 3 THEN 1 END) AS three_star,
    COUNT(CASE WHEN rating = 2 THEN 1 END) AS two_star,
    COUNT(CASE WHEN rating = 1 THEN 1 END) AS one_star,

    -- Positive rate (4-5 stars)
    CASE
        WHEN COUNT(*) > 0
        THEN CAST(COUNT(CASE WHEN rating >= 4 THEN 1 END) AS DOUBLE) / CAST(COUNT(*) AS DOUBLE)
        ELSE 0.0
    END AS positive_rate,

    COUNT(CASE WHEN tip_given = TRUE THEN 1 END) AS ratings_with_tips,
    SUM(CASE WHEN tip_given = TRUE THEN tip_amount ELSE 0 END) AS total_tip_amount

FROM ratings_source
GROUP BY
    TUMBLE(`timestamp`, INTERVAL '5' MINUTE);

-- =============================================================================
-- ENRICHED METRICS: JOIN RIDES WITH PAYMENTS AND RATINGS
-- =============================================================================

-- Join all metrics for comprehensive view (5-minute window)
CREATE VIEW comprehensive_metrics_5min AS
SELECT
    COALESCE(r.city, 'ALL') AS city,
    r.window_start,
    r.window_end,
    5 AS window_duration_minutes,

    -- Ride metrics
    r.rides_requested,
    r.rides_started,
    r.rides_completed,
    r.rides_cancelled,
    r.completion_rate,

    -- Revenue metrics (from rides + payments verification)
    r.total_revenue,
    r.avg_fare,
    r.total_tips,

    -- Performance metrics
    r.avg_wait_time,
    r.avg_duration,
    r.avg_distance,

    -- Customer satisfaction (from ratings)
    rt.avg_rating,
    rt.positive_rate AS positive_rating_rate,

    CURRENT_TIMESTAMP AS calculation_timestamp

FROM ride_metrics_5min r
LEFT JOIN rating_metrics_5min rt
    ON r.window_start = rt.window_start
    AND r.window_end = rt.window_end;

-- =============================================================================
-- TREND ANALYSIS: WEEK-OVER-WEEK COMPARISON
-- =============================================================================

-- Use LAG function to compare with previous week
CREATE VIEW metrics_with_trends AS
SELECT
    city,
    window_start,
    window_end,
    rides_completed,
    total_revenue,
    avg_rating,

    -- Week-over-week comparison
    LAG(rides_completed, 2016) OVER (PARTITION BY city ORDER BY window_start) AS rides_completed_last_week,
    LAG(total_revenue, 2016) OVER (PARTITION BY city ORDER BY window_start) AS revenue_last_week,
    LAG(avg_rating, 2016) OVER (PARTITION BY city ORDER BY window_start) AS rating_last_week,

    -- Calculate WoW change percentage
    -- Note: 2016 = 7 days * 24 hours * 12 (5-minute intervals per hour)
    CASE
        WHEN LAG(rides_completed, 2016) OVER (PARTITION BY city ORDER BY window_start) > 0
        THEN ((CAST(rides_completed AS DOUBLE) -
               CAST(LAG(rides_completed, 2016) OVER (PARTITION BY city ORDER BY window_start) AS DOUBLE)) /
               CAST(LAG(rides_completed, 2016) OVER (PARTITION BY city ORDER BY window_start) AS DOUBLE)) * 100
        ELSE 0.0
    END AS rides_wow_change_pct

FROM comprehensive_metrics_5min;

-- =============================================================================
-- TOP PERFORMING CITIES
-- =============================================================================

-- Rank cities by revenue in each window
CREATE VIEW top_cities_by_revenue AS
SELECT
    city,
    window_start,
    window_end,
    total_revenue,
    rides_completed,
    avg_fare,
    ROW_NUMBER() OVER (PARTITION BY window_start ORDER BY total_revenue DESC) AS revenue_rank
FROM comprehensive_metrics_5min
WHERE city != 'ALL';

-- =============================================================================
-- INSERT INTO OUTPUTS
-- =============================================================================

-- Write 1-minute metrics to DynamoDB (most recent data)
INSERT INTO metrics_dynamodb_sink
SELECT
    CONCAT('1min#', city, '#', CAST(window_start AS VARCHAR)) AS metric_key,
    '1min' AS metric_type,
    city,
    window_start,
    window_end,
    1 AS window_duration_minutes,

    rides_requested,
    rides_started,
    rides_completed,
    0 AS rides_cancelled,  -- Not calculated in 1-min window
    completion_rate,

    COALESCE(total_revenue, 0.0) AS total_revenue,
    COALESCE(avg_fare, 0.0) AS avg_fare,
    COALESCE(total_tips, 0.0) AS total_tips,

    COALESCE(avg_wait_time, 0.0) AS avg_wait_time_minutes,
    COALESCE(avg_duration, 0.0) AS avg_ride_duration_minutes,
    COALESCE(avg_distance, 0.0) AS avg_distance_miles,

    0.0 AS avg_rating,  -- Ratings in separate 5-min aggregation
    0.0 AS positive_rating_rate,

    CURRENT_TIMESTAMP AS calculation_timestamp,
    UNIX_TIMESTAMP(CURRENT_TIMESTAMP) + 3600 AS ttl  -- Expire after 1 hour

FROM ride_metrics_1min;

-- Write 5-minute comprehensive metrics to DynamoDB
INSERT INTO metrics_dynamodb_sink
SELECT
    CONCAT('5min#', city, '#', CAST(window_start AS VARCHAR)) AS metric_key,
    '5min' AS metric_type,
    city,
    window_start,
    window_end,
    window_duration_minutes,

    rides_requested,
    rides_started,
    rides_completed,
    rides_cancelled,
    completion_rate,

    COALESCE(total_revenue, 0.0) AS total_revenue,
    COALESCE(avg_fare, 0.0) AS avg_fare,
    COALESCE(total_tips, 0.0) AS total_tips,

    COALESCE(avg_wait_time, 0.0) AS avg_wait_time_minutes,
    COALESCE(avg_duration, 0.0) AS avg_ride_duration_minutes,
    COALESCE(avg_distance, 0.0) AS avg_distance_miles,

    COALESCE(avg_rating, 0.0) AS avg_rating,
    COALESCE(positive_rating_rate, 0.0) AS positive_rating_rate,

    calculation_timestamp,
    UNIX_TIMESTAMP(calculation_timestamp) + 86400 AS ttl  -- Expire after 24 hours

FROM comprehensive_metrics_5min;

-- Write to S3 for historical analysis
INSERT INTO metrics_s3_sink
SELECT
    '5min' AS metric_type,
    city,
    window_start,
    window_end,
    window_duration_minutes,
    rides_requested,
    rides_started,
    rides_completed,
    rides_cancelled,
    completion_rate,
    COALESCE(total_revenue, 0.0) AS total_revenue,
    COALESCE(avg_fare, 0.0) AS avg_fare,
    COALESCE(total_tips, 0.0) AS total_tips,
    COALESCE(avg_wait_time, 0.0) AS avg_wait_time_minutes,
    COALESCE(avg_duration, 0.0) AS avg_ride_duration_minutes,
    COALESCE(avg_distance, 0.0) AS avg_distance_miles,
    COALESCE(avg_rating, 0.0) AS avg_rating,
    COALESCE(positive_rating_rate, 0.0) AS positive_rating_rate,
    calculation_timestamp,

    CAST(DATE_FORMAT(window_start, 'yyyy-MM-dd') AS VARCHAR) AS `date`,
    CAST(DATE_FORMAT(window_start, 'HH') AS VARCHAR) AS `hour`

FROM comprehensive_metrics_5min;

-- =============================================================================
-- OPERATION NOTES
-- =============================================================================

-- 1. Multiple Windows:
--    - 1-minute: For real-time monitoring and alerting
--    - 5-minute: For operational dashboards
--    - Consider adding 1-hour windows for strategic KPIs
--
-- 2. Join Strategy:
--    - LEFT JOINs preserve ride data even when ratings/payments lag
--    - Watermarks handle late-arriving events (up to 30 seconds)
--
-- 3. Performance:
--    - Parallel execution recommended: parallelism = 8-16
--    - State backend: RocksDB for large state
--
-- 4. Monitoring:
--    - Alert on completion_rate < 0.8 (high cancellation)
--    - Alert on avg_wait_time > 10 minutes
--    - Alert on avg_rating < 4.0 (quality issues)
