-- Surge Pricing Calculator
-- Flink SQL Application for Real-Time Surge Pricing
--
-- Purpose:
--   Calculate dynamic surge pricing multipliers based on real-time
--   demand (ride requests) vs supply (available drivers)
--
-- Input Streams:
--   - rides_stream: Ride events (ride_requested, ride_started, ride_completed)
--   - locations_stream: Driver location updates
--
-- Logic:
--   1. Count ride requests per city in 5-minute tumbling windows
--   2. Count available drivers per city in same windows
--   3. Calculate demand/supply ratio
--   4. Apply surge multiplier based on ratio:
--      - Ratio > 2.0: 1.5x surge
--      - Ratio > 1.5: 1.3x surge
--      - Ratio > 1.2: 1.2x surge
--      - Otherwise: 1.0x (no surge)
--
-- Output:
--   - S3 for historical analysis (partitioned by date/hour)
--   - DynamoDB surge_pricing table for real-time lookups
--
-- Windowing Strategy:
--   - TUMBLE windows of 5 minutes
--   - Aligned to clock time (00:00, 00:05, 00:10, etc.)
--   - Allows for predictable, non-overlapping surge periods

-- =============================================================================
-- CREATE SOURCE TABLES
-- =============================================================================

-- Rides Stream Source
-- Reads from Kinesis rides_stream
CREATE TABLE rides_kinesis_source (
    ride_id VARCHAR(50),
    event_type VARCHAR(20),
    customer_id VARCHAR(50),
    city VARCHAR(50),
    pickup_lat DOUBLE,
    pickup_lon DOUBLE,
    dropoff_lat DOUBLE,
    dropoff_lon DOUBLE,
    `timestamp` TIMESTAMP(3),
    status VARCHAR(20),
    estimated_fare DOUBLE,
    driver_id VARCHAR(50),
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'rides_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

-- Driver Locations Stream Source
-- Reads from Kinesis locations_stream
CREATE TABLE locations_kinesis_source (
    driver_id VARCHAR(50),
    city VARCHAR(50),
    lat DOUBLE,
    lon DOUBLE,
    available BOOLEAN,
    speed_mph DOUBLE,
    heading DOUBLE,
    `timestamp` TIMESTAMP(3),
    current_ride_id VARCHAR(50),
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'locations_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json',
    'json.timestamp-format.standard' = 'ISO-8601'
);

-- =============================================================================
-- CREATE OUTPUT TABLES
-- =============================================================================

-- S3 Sink for Historical Data
-- Partitioned by date and hour for efficient querying
CREATE TABLE surge_pricing_s3_sink (
    city VARCHAR(50),
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    ride_requests BIGINT,
    available_drivers BIGINT,
    demand_supply_ratio DOUBLE,
    surge_multiplier DOUBLE,
    calculation_timestamp TIMESTAMP(3),
    `date` VARCHAR(10),
    `hour` VARCHAR(2)
) PARTITIONED BY (`date`, `hour`)
WITH (
    'connector' = 'filesystem',
    'path' = 's3://rideshare-analytics/surge-pricing/',
    'format' = 'json',
    'sink.partition-commit.policy.kind' = 'success-file',
    'sink.partition-commit.delay' = '1 min'
);

-- DynamoDB Sink for Real-Time Lookups
-- Used by ride matching service to apply surge pricing
CREATE TABLE surge_pricing_dynamodb_sink (
    surge_key VARCHAR(100),  -- Format: city#timestamp
    city VARCHAR(50),
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    ride_requests BIGINT,
    available_drivers BIGINT,
    demand_supply_ratio DOUBLE,
    surge_multiplier DOUBLE,
    calculation_timestamp TIMESTAMP(3),
    ttl BIGINT  -- DynamoDB TTL (expire after 24 hours)
) WITH (
    'connector' = 'dynamodb',
    'table-name' = 'surge_pricing',
    'aws.region' = 'us-east-1'
);

-- =============================================================================
-- INTERMEDIATE VIEWS
-- =============================================================================

-- View: Ride Requests per City
-- Counts ride_requested events in 5-minute windows by city
CREATE VIEW ride_demand AS
SELECT
    city,
    TUMBLE_START(`timestamp`, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '5' MINUTE) AS window_end,
    COUNT(*) AS ride_requests
FROM rides_kinesis_source
WHERE event_type = 'ride_requested'
GROUP BY
    city,
    TUMBLE(`timestamp`, INTERVAL '5' MINUTE);

-- View: Available Drivers per City
-- Counts available drivers in 5-minute windows by city
-- Uses deduplicated latest location per driver
CREATE VIEW driver_supply AS
SELECT
    city,
    TUMBLE_START(`timestamp`, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '5' MINUTE) AS window_end,
    COUNT(DISTINCT CASE WHEN available = TRUE THEN driver_id END) AS available_drivers,
    COUNT(DISTINCT driver_id) AS total_drivers
FROM locations_kinesis_source
GROUP BY
    city,
    TUMBLE(`timestamp`, INTERVAL '5' MINUTE);

-- =============================================================================
-- MAIN SURGE PRICING CALCULATION
-- =============================================================================

-- Join demand and supply, calculate surge multiplier
CREATE VIEW surge_pricing_calculated AS
SELECT
    COALESCE(d.city, s.city) AS city,
    COALESCE(d.window_start, s.window_start) AS window_start,
    COALESCE(d.window_end, s.window_end) AS window_end,

    -- Demand and supply metrics
    COALESCE(d.ride_requests, 0) AS ride_requests,
    COALESCE(s.available_drivers, 0) AS available_drivers,

    -- Calculate demand/supply ratio
    -- Prevent division by zero: if no drivers, ratio = 10 (extreme demand)
    CASE
        WHEN COALESCE(s.available_drivers, 0) = 0 THEN 10.0
        ELSE CAST(COALESCE(d.ride_requests, 0) AS DOUBLE) /
             CAST(s.available_drivers AS DOUBLE)
    END AS demand_supply_ratio,

    -- Apply surge multiplier based on ratio
    -- Reasoning:
    --   - Ratio > 2.0: Severe shortage, 1.5x to incentivize drivers
    --   - Ratio > 1.5: High demand, 1.3x surge
    --   - Ratio > 1.2: Moderate demand, 1.2x surge
    --   - Otherwise: Normal conditions, no surge
    CASE
        WHEN COALESCE(s.available_drivers, 0) = 0 THEN 2.0  -- No drivers = max surge
        WHEN (CAST(COALESCE(d.ride_requests, 0) AS DOUBLE) /
              CAST(s.available_drivers AS DOUBLE)) > 2.0 THEN 1.5
        WHEN (CAST(COALESCE(d.ride_requests, 0) AS DOUBLE) /
              CAST(s.available_drivers AS DOUBLE)) > 1.5 THEN 1.3
        WHEN (CAST(COALESCE(d.ride_requests, 0) AS DOUBLE) /
              CAST(s.available_drivers AS DOUBLE)) > 1.2 THEN 1.2
        ELSE 1.0
    END AS surge_multiplier,

    CURRENT_TIMESTAMP AS calculation_timestamp

FROM ride_demand d
FULL OUTER JOIN driver_supply s
    ON d.city = s.city
    AND d.window_start = s.window_start
    AND d.window_end = s.window_end;

-- =============================================================================
-- INSERT INTO OUTPUTS
-- =============================================================================

-- Write to S3 for historical analysis
INSERT INTO surge_pricing_s3_sink
SELECT
    city,
    window_start,
    window_end,
    ride_requests,
    available_drivers,
    demand_supply_ratio,
    surge_multiplier,
    calculation_timestamp,

    -- Partition columns
    CAST(DATE_FORMAT(window_start, 'yyyy-MM-dd') AS VARCHAR) AS `date`,
    CAST(DATE_FORMAT(window_start, 'HH') AS VARCHAR) AS `hour`

FROM surge_pricing_calculated;

-- Write to DynamoDB for real-time lookups
INSERT INTO surge_pricing_dynamodb_sink
SELECT
    CONCAT(city, '#', CAST(window_start AS VARCHAR)) AS surge_key,
    city,
    window_start,
    window_end,
    ride_requests,
    available_drivers,
    demand_supply_ratio,
    surge_multiplier,
    calculation_timestamp,

    -- DynamoDB TTL: expire after 24 hours
    -- Convert timestamp to epoch seconds and add 86400 (24 hours)
    UNIX_TIMESTAMP(calculation_timestamp) + 86400 AS ttl

FROM surge_pricing_calculated;

-- =============================================================================
-- MONITORING QUERIES (for testing/debugging)
-- =============================================================================

-- Query to check current surge pricing (use in Flink SQL CLI)
-- SELECT city, window_start, window_end, ride_requests, available_drivers,
--        demand_supply_ratio, surge_multiplier
-- FROM surge_pricing_calculated
-- ORDER BY window_start DESC
-- LIMIT 10;

-- Query to find cities with highest surge
-- SELECT city, surge_multiplier, demand_supply_ratio, ride_requests, available_drivers
-- FROM surge_pricing_calculated
-- WHERE surge_multiplier > 1.0
-- ORDER BY surge_multiplier DESC, demand_supply_ratio DESC
-- LIMIT 5;

-- =============================================================================
-- OPERATION NOTES
-- =============================================================================

-- 1. Deployment:
--    - Deploy as Kinesis Data Analytics for Apache Flink application
--    - Configure parallelism based on stream throughput
--    - Recommended: parallelism = 4 for moderate load
--
-- 2. Monitoring:
--    - Watch CloudWatch metrics: InputRecords, OutputRecords, Errors
--    - Alert on surge_multiplier > 1.5 (high demand)
--    - Monitor available_drivers = 0 (critical shortage)
--
-- 3. Tuning:
--    - Adjust watermark delay based on event lateness
--    - Modify surge thresholds based on business requirements
--    - Consider adding geographic zones within cities
--
-- 4. Windowing Trade-offs:
--    - 5-minute windows balance responsiveness vs stability
--    - Shorter windows (1-2 min) = more reactive but noisy
--    - Longer windows (10-15 min) = smoother but less responsive
--
-- 5. Future Enhancements:
--    - Add weather data to adjust surge logic
--    - Implement zone-based pricing (downtown vs suburbs)
--    - Add predictive surge based on historical patterns
--    - Include event-driven surge (concerts, sports events)
