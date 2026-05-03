-- Hot Spots Detector
-- Flink SQL Application for Geospatial Analysis
--
-- Purpose:
--   Identify geographic hot spots (high activity areas) based on
--   pickup and dropoff locations in real-time
--
-- Analysis:
--   - Grid-based spatial partitioning using geohash
--   - 15-minute tumbling windows for temporal aggregation
--   - Density calculation per grid cell
--   - Ranking to identify top hot spots
--
-- Use Cases:
--   - Driver positioning recommendations
--   - Dynamic pricing zone definition
--   - Infrastructure planning (more pickup points)
--   - Marketing and promotions targeting
--
-- Output:
--   - S3 for historical analysis and visualization
--   - DynamoDB hot_spots table for real-time driver app queries

-- =============================================================================
-- CREATE SOURCE TABLES
-- =============================================================================

-- Rides Stream (focused on location data)
CREATE TABLE rides_location_source (
    ride_id VARCHAR(50),
    event_type VARCHAR(20),
    city VARCHAR(50),
    pickup_lat DOUBLE,
    pickup_lon DOUBLE,
    dropoff_lat DOUBLE,
    dropoff_lon DOUBLE,
    `timestamp` TIMESTAMP(3),
    status VARCHAR(20),
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '30' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'rides_stream',
    'aws.region' = 'us-east-1',
    'scan.stream.initpos' = 'LATEST',
    'format' = 'json'
);

-- =============================================================================
-- USER-DEFINED FUNCTIONS (Conceptual - would need implementation)
-- =============================================================================

-- Note: In production, these would be implemented as Java/Scala UDFs
-- For this example, we use simplified geohash calculation

-- Geohash Function (simplified grid-based implementation)
-- Precision 5 = approximately 5km x 5km grid cells
-- Format: "lat_grid_lon_grid" where grids are 5-digit numbers
--
-- Example geohash calculation in SQL (approximation):
-- CONCAT(
--     CAST(FLOOR((lat + 90) * 11111) AS VARCHAR),
--     '_',
--     CAST(FLOOR((lon + 180) * 11111) AS VARCHAR)
-- )

-- =============================================================================
-- CREATE OUTPUT TABLES
-- =============================================================================

-- S3 Sink for Historical Hot Spots
CREATE TABLE hotspots_s3_sink (
    city VARCHAR(50),
    geohash VARCHAR(50),
    center_lat DOUBLE,
    center_lon DOUBLE,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),

    -- Activity counts
    pickup_count BIGINT,
    dropoff_count BIGINT,
    total_activity BIGINT,

    -- Density metrics
    activity_density DOUBLE,  -- Activity per square km
    hotspot_rank INT,
    hotspot_score DOUBLE,

    -- Characteristics
    avg_wait_time_minutes DOUBLE,
    avg_fare DOUBLE,
    unique_customers BIGINT,

    calculation_timestamp TIMESTAMP(3),
    `date` VARCHAR(10),
    `hour` VARCHAR(2)
) PARTITIONED BY (`date`, `hour`)
WITH (
    'connector' = 'filesystem',
    'path' = 's3://rideshare-analytics/hot-spots/',
    'format' = 'json'
);

-- DynamoDB Sink for Real-Time Queries
CREATE TABLE hotspots_dynamodb_sink (
    hotspot_key VARCHAR(200),  -- Format: city#geohash#timestamp
    city VARCHAR(50),
    geohash VARCHAR(50),
    center_lat DOUBLE,
    center_lon DOUBLE,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    pickup_count BIGINT,
    dropoff_count BIGINT,
    total_activity BIGINT,
    activity_density DOUBLE,
    hotspot_rank INT,
    hotspot_score DOUBLE,
    calculation_timestamp TIMESTAMP(3),
    ttl BIGINT
) WITH (
    'connector' = 'dynamodb',
    'table-name' = 'hot_spots',
    'aws.region' = 'us-east-1'
);

-- =============================================================================
-- GEOHASH CALCULATION FUNCTIONS
-- =============================================================================

-- Simplified geohash using grid-based approach
-- Precision: 0.01 degrees ≈ 1.1 km
-- This creates grid cells of approximately 1km x 1km
CREATE TEMPORARY FUNCTION calculate_geohash AS
'
    -- Geohash precision 5 = ~5km grid
    -- Grid size: 0.05 degrees (approximately 5.5 km at equator)
    CONCAT(
        CAST(FLOOR(lat / 0.05) * 0.05 AS VARCHAR),
        "_",
        CAST(FLOOR(lon / 0.05) * 0.05 AS VARCHAR)
    )
';

-- =============================================================================
-- INTERMEDIATE VIEWS: PICKUP HOT SPOTS
-- =============================================================================

-- Analyze pickup locations (ride_requested and ride_started events)
CREATE VIEW pickup_hotspots AS
SELECT
    city,

    -- Calculate geohash for spatial grouping
    -- Grid cell: ~5km x 5km
    CONCAT(
        CAST(CAST(FLOOR(pickup_lat / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR),
        '_',
        CAST(CAST(FLOOR(pickup_lon / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR)
    ) AS geohash,

    -- Center coordinates of the grid cell
    CAST(FLOOR(pickup_lat / 0.05) * 0.05 AS DOUBLE) + 0.025 AS center_lat,
    CAST(FLOOR(pickup_lon / 0.05) * 0.05 AS DOUBLE) + 0.025 AS center_lon,

    -- Window boundaries
    TUMBLE_START(`timestamp`, INTERVAL '15' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '15' MINUTE) AS window_end,

    -- Activity metrics
    COUNT(*) AS pickup_count,
    COUNT(DISTINCT ride_id) AS unique_rides,

    -- Calculate approximate grid cell area (km²)
    -- At equator: 1 degree ≈ 111 km
    -- Grid cell: 0.05 degrees ≈ 5.5 km
    -- Area ≈ 5.5 * 5.5 = 30.25 km²
    30.25 AS grid_area_km2

FROM rides_location_source
WHERE event_type IN ('ride_requested', 'ride_started')
    AND pickup_lat IS NOT NULL
    AND pickup_lon IS NOT NULL
    AND pickup_lat BETWEEN -90 AND 90
    AND pickup_lon BETWEEN -180 AND 180
GROUP BY
    city,
    CONCAT(
        CAST(CAST(FLOOR(pickup_lat / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR),
        '_',
        CAST(CAST(FLOOR(pickup_lon / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR)
    ),
    CAST(FLOOR(pickup_lat / 0.05) * 0.05 AS DOUBLE) + 0.025,
    CAST(FLOOR(pickup_lon / 0.05) * 0.05 AS DOUBLE) + 0.025,
    TUMBLE(`timestamp`, INTERVAL '15' MINUTE);

-- =============================================================================
-- INTERMEDIATE VIEWS: DROPOFF HOT SPOTS
-- =============================================================================

-- Analyze dropoff locations (ride_completed events)
CREATE VIEW dropoff_hotspots AS
SELECT
    city,

    CONCAT(
        CAST(CAST(FLOOR(dropoff_lat / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR),
        '_',
        CAST(CAST(FLOOR(dropoff_lon / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR)
    ) AS geohash,

    CAST(FLOOR(dropoff_lat / 0.05) * 0.05 AS DOUBLE) + 0.025 AS center_lat,
    CAST(FLOOR(dropoff_lon / 0.05) * 0.05 AS DOUBLE) + 0.025 AS center_lon,

    TUMBLE_START(`timestamp`, INTERVAL '15' MINUTE) AS window_start,
    TUMBLE_END(`timestamp`, INTERVAL '15' MINUTE) AS window_end,

    COUNT(*) AS dropoff_count,
    30.25 AS grid_area_km2

FROM rides_location_source
WHERE event_type = 'ride_completed'
    AND dropoff_lat IS NOT NULL
    AND dropoff_lon IS NOT NULL
    AND dropoff_lat BETWEEN -90 AND 90
    AND dropoff_lon BETWEEN -180 AND 180
GROUP BY
    city,
    CONCAT(
        CAST(CAST(FLOOR(dropoff_lat / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR),
        '_',
        CAST(CAST(FLOOR(dropoff_lon / 0.05) * 0.05 AS DECIMAL(10,6)) AS VARCHAR)
    ),
    CAST(FLOOR(dropoff_lat / 0.05) * 0.05 AS DOUBLE) + 0.025,
    CAST(FLOOR(dropoff_lon / 0.05) * 0.05 AS DOUBLE) + 0.025,
    TUMBLE(`timestamp`, INTERVAL '15' MINUTE);

-- =============================================================================
-- COMBINED HOT SPOTS ANALYSIS
-- =============================================================================

-- Merge pickup and dropoff hot spots
CREATE VIEW combined_hotspots AS
SELECT
    COALESCE(p.city, d.city) AS city,
    COALESCE(p.geohash, d.geohash) AS geohash,
    COALESCE(p.center_lat, d.center_lat) AS center_lat,
    COALESCE(p.center_lon, d.center_lon) AS center_lon,
    COALESCE(p.window_start, d.window_start) AS window_start,
    COALESCE(p.window_end, d.window_end) AS window_end,

    -- Activity counts
    COALESCE(p.pickup_count, 0) AS pickup_count,
    COALESCE(d.dropoff_count, 0) AS dropoff_count,
    COALESCE(p.pickup_count, 0) + COALESCE(d.dropoff_count, 0) AS total_activity,

    -- Grid area for density calculation
    COALESCE(p.grid_area_km2, d.grid_area_km2, 30.25) AS grid_area_km2

FROM pickup_hotspots p
FULL OUTER JOIN dropoff_hotspots d
    ON p.city = d.city
    AND p.geohash = d.geohash
    AND p.window_start = d.window_start
    AND p.window_end = d.window_end;

-- =============================================================================
-- HOT SPOT SCORING AND RANKING
-- =============================================================================

-- Calculate density and rank hot spots
CREATE VIEW ranked_hotspots AS
SELECT
    city,
    geohash,
    center_lat,
    center_lon,
    window_start,
    window_end,
    pickup_count,
    dropoff_count,
    total_activity,

    -- Calculate activity density (events per km² per hour)
    -- 15-minute window = 0.25 hours, so multiply by 4 for hourly rate
    (CAST(total_activity AS DOUBLE) / grid_area_km2) * 4.0 AS activity_density,

    -- Calculate hotspot score (weighted combination of factors)
    -- Weights: 60% total activity, 30% pickup density, 10% balance
    (
        (CAST(total_activity AS DOUBLE) * 0.6) +
        (CAST(pickup_count AS DOUBLE) * 0.3) +
        (CASE
            WHEN pickup_count + dropoff_count > 0
            THEN (1.0 - ABS(CAST(pickup_count AS DOUBLE) - CAST(dropoff_count AS DOUBLE)) /
                         CAST(pickup_count + dropoff_count AS DOUBLE)) * total_activity * 0.1
            ELSE 0.0
        END)
    ) AS hotspot_score,

    -- Rank within city and time window
    ROW_NUMBER() OVER (
        PARTITION BY city, window_start
        ORDER BY total_activity DESC, pickup_count DESC
    ) AS hotspot_rank,

    CURRENT_TIMESTAMP AS calculation_timestamp

FROM combined_hotspots
WHERE total_activity > 0;  -- Filter out empty cells

-- =============================================================================
-- ENRICHED HOT SPOTS WITH RIDE CHARACTERISTICS
-- =============================================================================

-- Add additional context from ride data
CREATE VIEW enriched_hotspots AS
SELECT
    h.city,
    h.geohash,
    h.center_lat,
    h.center_lon,
    h.window_start,
    h.window_end,
    h.pickup_count,
    h.dropoff_count,
    h.total_activity,
    h.activity_density,
    h.hotspot_score,
    h.hotspot_rank,
    h.calculation_timestamp,

    -- Additional characteristics from ride data
    COUNT(DISTINCT r.ride_id) AS unique_rides_in_area,
    AVG(
        CASE
            WHEN r.event_type = 'ride_started' AND r.pickup_lat IS NOT NULL
            THEN
                CASE
                    WHEN ABS(r.pickup_lat - h.center_lat) < 0.025 AND
                         ABS(r.pickup_lon - h.center_lon) < 0.025
                    THEN 1
                    ELSE 0
                END
            ELSE 0
        END
    ) AS area_match_ratio

FROM ranked_hotspots h
LEFT JOIN rides_location_source r
    ON h.city = r.city
    AND r.`timestamp` BETWEEN h.window_start AND h.window_end
    AND (
        (ABS(r.pickup_lat - h.center_lat) < 0.05 AND ABS(r.pickup_lon - h.center_lon) < 0.05) OR
        (ABS(r.dropoff_lat - h.center_lat) < 0.05 AND ABS(r.dropoff_lon - h.center_lon) < 0.05)
    )
GROUP BY
    h.city, h.geohash, h.center_lat, h.center_lon,
    h.window_start, h.window_end, h.pickup_count, h.dropoff_count,
    h.total_activity, h.activity_density, h.hotspot_score,
    h.hotspot_rank, h.calculation_timestamp;

-- =============================================================================
-- INSERT INTO OUTPUTS
-- =============================================================================

-- Write top 100 hot spots per city to S3
INSERT INTO hotspots_s3_sink
SELECT
    city,
    geohash,
    center_lat,
    center_lon,
    window_start,
    window_end,
    pickup_count,
    dropoff_count,
    total_activity,
    activity_density,
    hotspot_rank,
    hotspot_score,

    -- Placeholder for characteristics (would be enriched in production)
    0.0 AS avg_wait_time_minutes,
    0.0 AS avg_fare,
    0 AS unique_customers,

    calculation_timestamp,

    -- Partition columns
    CAST(DATE_FORMAT(window_start, 'yyyy-MM-dd') AS VARCHAR) AS `date`,
    CAST(DATE_FORMAT(window_start, 'HH') AS VARCHAR) AS `hour`

FROM ranked_hotspots
WHERE hotspot_rank <= 100;  -- Top 100 per city

-- Write top 20 hot spots per city to DynamoDB for real-time queries
INSERT INTO hotspots_dynamodb_sink
SELECT
    CONCAT(city, '#', geohash, '#', CAST(window_start AS VARCHAR)) AS hotspot_key,
    city,
    geohash,
    center_lat,
    center_lon,
    window_start,
    window_end,
    pickup_count,
    dropoff_count,
    total_activity,
    activity_density,
    hotspot_rank,
    hotspot_score,
    calculation_timestamp,

    -- DynamoDB TTL: expire after 4 hours (enough for historical comparison)
    UNIX_TIMESTAMP(calculation_timestamp) + 14400 AS ttl

FROM ranked_hotspots
WHERE hotspot_rank <= 20;  -- Top 20 per city for real-time driver recommendations

-- =============================================================================
-- MONITORING QUERIES (for testing/debugging)
-- =============================================================================

-- Query to see current top hot spots (use in Flink SQL CLI)
-- SELECT city, geohash, center_lat, center_lon, pickup_count, dropoff_count,
--        total_activity, activity_density, hotspot_rank, hotspot_score
-- FROM ranked_hotspots
-- WHERE hotspot_rank <= 10
-- ORDER BY city, hotspot_rank;

-- Query to find highly imbalanced areas (pickup != dropoff)
-- SELECT city, geohash, pickup_count, dropoff_count,
--        ABS(pickup_count - dropoff_count) AS imbalance,
--        CASE
--            WHEN pickup_count > dropoff_count THEN 'NEEDS_MORE_DROPOFF_ZONES'
--            WHEN dropoff_count > pickup_count THEN 'NEEDS_MORE_PICKUP_ZONES'
--            ELSE 'BALANCED'
--        END AS recommendation
-- FROM combined_hotspots
-- WHERE ABS(pickup_count - dropoff_count) > 10
-- ORDER BY imbalance DESC
-- LIMIT 20;

-- =============================================================================
-- OPERATION NOTES
-- =============================================================================

-- 1. Geohash Precision:
--    - Current: 0.05 degrees ≈ 5.5 km grid cells
--    - Adjust based on city density:
--      * Dense cities (NYC, SF): 0.01 degrees ≈ 1 km
--      * Suburban areas: 0.1 degrees ≈ 11 km
--
-- 2. Window Selection:
--    - 15 minutes: Balance between responsiveness and statistical significance
--    - Shorter windows (5-10 min): More reactive but noisier
--    - Longer windows (30-60 min): Smoother but less adaptive
--
-- 3. Hot Spot Score:
--    - Weights (60/30/10) favor total activity but consider balance
--    - Adjust weights based on business priorities:
--      * Driver positioning: Higher weight on pickups
--      * Infrastructure planning: Higher weight on total activity
--
-- 4. Performance:
--    - Grid-based approach is more efficient than true geohashing
--    - Consider spatial indexes for very high-throughput scenarios
--    - Parallelism: 4-8 based on data volume
--
-- 5. Use Cases:
--    - Driver App: "Drive to hot spot X (3km away) with 15 pickups/15min"
--    - Operations: "Deploy more drivers to downtown (geohash ABC)"
--    - Marketing: "Offer promotions in low-activity zones"
--
-- 6. Future Enhancements:
--    - Predictive hot spots (based on historical patterns)
--    - Time-of-day specific hot spots (morning commute vs evening)
--    - Event-driven hot spots (concerts, sports games)
--    - Route optimization between hot spots
--
-- 7. Visualization:
--    - Export to GeoJSON for mapping
--    - Heat map overlays on driver apps
--    - Time-lapse animations of hot spot evolution
