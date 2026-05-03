-- ============================================================================
-- ATHENA BUSINESS QUERIES FOR RIDE ANALYTICS
-- TODO: Complete these queries to analyze ride-sharing data
-- ============================================================================

-- NOTE: Replace 'ride_analytics_db' and table names with your actual names
-- Run these queries in Amazon Athena console or via AWS CLI

-- ============================================================================
-- QUERY 1: DAILY RIDE STATISTICS
-- Purpose: Calculate daily metrics including total rides, revenue, and averages
-- TODO: Complete this query to show comprehensive daily statistics
-- ============================================================================

-- TODO: Write query to:
-- - Count total rides per day
-- - Calculate total revenue (sum of fares)
-- - Calculate average fare per ride
-- - Calculate average distance per ride
-- - Calculate average duration per ride
-- - Group by date and status (completed, cancelled)
-- - Show results for the last 30 days
-- - Order by date descending

/*
SELECT
    -- TODO: Extract date from timestamp
    -- DATE(from_iso8601_timestamp(timestamp)) as ride_date,

    -- TODO: Add status column
    -- status,

    -- TODO: Count total rides
    -- COUNT(*) as total_rides,

    -- TODO: Sum total revenue
    -- SUM(fare) as total_revenue,

    -- TODO: Average fare
    -- AVG(fare) as avg_fare,

    -- TODO: Average distance
    -- AVG(distance_km) as avg_distance_km,

    -- TODO: Average duration
    -- AVG(duration_minutes) as avg_duration_minutes,

    -- TODO: Max fare
    -- MAX(fare) as max_fare,

    -- TODO: Min fare
    -- MIN(fare) as min_fare

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Filter for last 30 days
    -- DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day

    -- TODO: Only include completed and cancelled rides
    -- AND status IN ('completed', 'cancelled')

-- GROUP BY
    -- TODO: Group by date and status
    -- DATE(from_iso8601_timestamp(timestamp)),
    -- status

-- ORDER BY
    -- TODO: Order by date descending
    -- ride_date DESC,
    -- status;
*/


-- ============================================================================
-- QUERY 2: PEAK HOURS ANALYSIS
-- Purpose: Identify busiest hours of the day and calculate hourly metrics
-- TODO: Complete this query to show hourly patterns
-- ============================================================================

-- TODO: Write query to:
-- - Extract hour from timestamp
-- - Count rides per hour
-- - Calculate total revenue per hour
-- - Calculate average fare per hour
-- - Show average rating per hour
-- - Order by ride count descending to identify peak hours

/*
SELECT
    -- TODO: Extract hour from timestamp
    -- HOUR(from_iso8601_timestamp(timestamp)) as hour_of_day,

    -- TODO: Count rides
    -- COUNT(*) as ride_count,

    -- TODO: Total revenue
    -- SUM(fare) as hourly_revenue,

    -- TODO: Average fare
    -- ROUND(AVG(fare), 2) as avg_fare,

    -- TODO: Average rating
    -- ROUND(AVG(rating), 2) as avg_rating,

    -- TODO: Average duration
    -- ROUND(AVG(duration_minutes), 1) as avg_duration_minutes

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Only completed rides
    -- status = 'completed'

    -- TODO: Last 7 days of data
    -- AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '7' day

-- GROUP BY
    -- TODO: Group by hour
    -- HOUR(from_iso8601_timestamp(timestamp))

-- ORDER BY
    -- TODO: Order by ride count descending
    -- ride_count DESC;
*/


-- ============================================================================
-- QUERY 3: DRIVER PERFORMANCE RANKINGS
-- Purpose: Rank drivers by performance metrics
-- TODO: Complete this query to show top-performing drivers
-- ============================================================================

-- TODO: Write query to:
-- - Group by driver_id
-- - Count total rides completed
-- - Calculate total earnings
-- - Calculate average rating
-- - Calculate acceptance rate (completed vs cancelled)
-- - Rank drivers using RANK() window function
-- - Show top 20 drivers

/*
SELECT
    -- TODO: Add ranking
    -- RANK() OVER (ORDER BY COUNT(*) DESC) as driver_rank,

    -- TODO: Driver ID
    -- driver_id,

    -- TODO: Count completed rides
    -- COUNT(*) as completed_rides,

    -- TODO: Total earnings
    -- ROUND(SUM(fare + COALESCE(tip, 0)), 2) as total_earnings,

    -- TODO: Average fare
    -- ROUND(AVG(fare), 2) as avg_fare,

    -- TODO: Average rating
    -- ROUND(AVG(rating), 2) as avg_rating,

    -- TODO: Total distance driven
    -- ROUND(SUM(distance_km), 1) as total_distance_km,

    -- TODO: Average ride duration
    -- ROUND(AVG(duration_minutes), 1) as avg_duration_minutes,

    -- TODO: Calculate earnings per hour
    -- ROUND(SUM(fare + COALESCE(tip, 0)) / (SUM(duration_minutes) / 60.0), 2) as earnings_per_hour

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Only completed rides
    -- status = 'completed'

    -- TODO: Last 30 days
    -- AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day

-- GROUP BY
    -- TODO: Group by driver
    -- driver_id

-- HAVING
    -- TODO: Only drivers with at least 10 rides
    -- COUNT(*) >= 10

-- ORDER BY
    -- TODO: Order by completed rides descending
    -- completed_rides DESC

-- LIMIT 20;
*/


-- ============================================================================
-- QUERY 4: CANCELLATION ANALYSIS
-- Purpose: Analyze ride cancellations to identify patterns and reasons
-- TODO: Complete this query to understand cancellation behavior
-- ============================================================================

-- TODO: Write query showing:
-- - Overall cancellation rate
-- - Cancellation reasons breakdown with counts
-- - Percentage of total for each reason
-- - Average cancellation fee collected
-- - Cancellation trend over time (daily)

/*
-- Part A: Overall Cancellation Rate
SELECT
    -- TODO: Total rides (started)
    -- COUNT(*) as total_rides,

    -- TODO: Cancelled rides
    -- SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_rides,

    -- TODO: Completed rides
    -- SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_rides,

    -- TODO: Cancellation rate as percentage
    -- ROUND(
    --     100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*),
    --     2
    -- ) as cancellation_rate_pct,

    -- TODO: Completion rate as percentage
    -- ROUND(
    --     100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*),
    --     2
    -- ) as completion_rate_pct

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Last 30 days
    -- DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day

    -- TODO: Only terminal statuses
    -- AND status IN ('completed', 'cancelled');


-- Part B: Cancellation Reasons Breakdown
SELECT
    -- TODO: Cancellation reason
    -- cancellation_reason,

    -- TODO: Count
    -- COUNT(*) as cancellation_count,

    -- TODO: Percentage of total cancellations
    -- ROUND(
    --     100.0 * COUNT(*) / SUM(COUNT(*)) OVER(),
    --     2
    -- ) as percentage_of_cancellations,

    -- TODO: Average cancellation fee
    -- ROUND(AVG(cancellation_fee), 2) as avg_cancellation_fee,

    -- TODO: Total fees collected
    -- ROUND(SUM(cancellation_fee), 2) as total_fees_collected

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Only cancelled rides
    -- status = 'cancelled'

    -- TODO: Last 30 days
    -- AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day

-- GROUP BY
    -- TODO: Group by reason
    -- cancellation_reason

-- ORDER BY
    -- TODO: Order by count descending
    -- cancellation_count DESC;


-- Part C: Daily Cancellation Trend
SELECT
    -- TODO: Date
    -- DATE(from_iso8601_timestamp(timestamp)) as date,

    -- TODO: Total rides
    -- COUNT(*) as total_rides,

    -- TODO: Cancelled rides
    -- SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_rides,

    -- TODO: Cancellation rate
    -- ROUND(
    --     100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*),
    --     2
    -- ) as cancellation_rate_pct

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Last 30 days
    -- DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day
    -- AND status IN ('completed', 'cancelled')

-- GROUP BY
    -- DATE(from_iso8601_timestamp(timestamp))

-- ORDER BY
    -- date DESC;
*/


-- ============================================================================
-- QUERY 5: REAL-TIME ACTIVE RIDES DASHBOARD
-- Purpose: Show currently active rides with duration and estimated completion
-- TODO: Complete this query for real-time monitoring
-- ============================================================================

-- TODO: Write query to:
-- - Show all active rides
-- - Calculate how long ride has been active
-- - Estimate completion time based on average duration
-- - Show pickup and destination locations
-- - Show driver and passenger info

/*
SELECT
    -- TODO: Ride ID
    -- ride_id,

    -- TODO: Driver and passenger
    -- driver_id,
    -- passenger_id,

    -- TODO: Start time
    -- start_time,

    -- TODO: Calculate current duration
    -- ROUND(
    --     date_diff('minute',
    --         from_iso8601_timestamp(start_time),
    --         current_timestamp
    --     ),
    --     0
    -- ) as current_duration_minutes,

    -- TODO: Pickup location (formatted)
    -- CONCAT(
    --     'Lat: ', CAST(pickup_location.lat AS VARCHAR),
    --     ', Lon: ', CAST(pickup_location.lon AS VARCHAR)
    -- ) as pickup_location,

    -- TODO: Destination location (formatted)
    -- CONCAT(
    --     'Lat: ', CAST(destination_location.lat AS VARCHAR),
    --     ', Lon: ', CAST(destination_location.lon AS VARCHAR)
    -- ) as destination_location,

    -- TODO: Vehicle type
    -- vehicle_type,

    -- TODO: Payment method
    -- payment_method,

    -- TODO: Status
    -- status

-- FROM ride_analytics_db.ride_events
-- WHERE
    -- TODO: Only active rides
    -- status = 'active'

-- ORDER BY
    -- TODO: Order by start time (oldest first)
    -- start_time ASC;
*/


-- ============================================================================
-- BONUS QUERIES
-- ============================================================================

-- BONUS QUERY 1: Revenue by Vehicle Type
-- TODO: Calculate total revenue and average fare by vehicle type

/*
SELECT
    vehicle_type,
    COUNT(*) as ride_count,
    ROUND(SUM(fare), 2) as total_revenue,
    ROUND(AVG(fare), 2) as avg_fare,
    ROUND(AVG(distance_km), 1) as avg_distance,
    ROUND(AVG(rating), 2) as avg_rating
FROM ride_analytics_db.ride_events
WHERE
    status = 'completed'
    AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day
GROUP BY vehicle_type
ORDER BY total_revenue DESC;
*/


-- BONUS QUERY 2: Geographic Analysis - Popular Pickup Locations
-- TODO: Find most common pickup areas (rounded to 2 decimal places for grouping)

/*
SELECT
    ROUND(pickup_location.lat, 2) as pickup_lat,
    ROUND(pickup_location.lon, 2) as pickup_lon,
    COUNT(*) as pickup_count,
    ROUND(AVG(fare), 2) as avg_fare_from_location
FROM ride_analytics_db.ride_events
WHERE
    status = 'completed'
    AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '7' day
GROUP BY
    ROUND(pickup_location.lat, 2),
    ROUND(pickup_location.lon, 2)
HAVING COUNT(*) >= 10
ORDER BY pickup_count DESC
LIMIT 20;
*/


-- BONUS QUERY 3: Payment Method Analysis
-- TODO: Analyze ride distribution and revenue by payment method

/*
SELECT
    payment_method,
    COUNT(*) as ride_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(SUM(fare), 2) as total_revenue,
    ROUND(AVG(fare), 2) as avg_fare,
    ROUND(AVG(tip), 2) as avg_tip
FROM ride_analytics_db.ride_events
WHERE
    status = 'completed'
    AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day
GROUP BY payment_method
ORDER BY ride_count DESC;
*/


-- BONUS QUERY 4: Rating Distribution
-- TODO: Show distribution of ratings

/*
SELECT
    rating,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM ride_analytics_db.ride_events
WHERE
    status = 'completed'
    AND rating IS NOT NULL
    AND DATE(from_iso8601_timestamp(timestamp)) >= current_date - interval '30' day
GROUP BY rating
ORDER BY rating DESC;
*/


-- BONUS QUERY 5: Time to First Ride by Driver (New Driver Analysis)
-- TODO: For new drivers, analyze their first rides

/*
WITH driver_first_ride AS (
    SELECT
        driver_id,
        MIN(from_iso8601_timestamp(start_time)) as first_ride_time
    FROM ride_analytics_db.ride_events
    WHERE status IN ('completed', 'cancelled')
    GROUP BY driver_id
)
SELECT
    d.driver_id,
    d.first_ride_time,
    DATE(d.first_ride_time) as first_ride_date,
    COUNT(r.ride_id) as total_rides,
    ROUND(AVG(r.rating), 2) as avg_rating,
    ROUND(SUM(r.fare), 2) as total_earnings
FROM driver_first_ride d
LEFT JOIN ride_analytics_db.ride_events r
    ON d.driver_id = r.driver_id
    AND r.status = 'completed'
WHERE d.first_ride_time >= current_timestamp - interval '30' day
GROUP BY d.driver_id, d.first_ride_time
ORDER BY d.first_ride_time DESC;
*/


-- ============================================================================
-- QUERY EXECUTION NOTES FOR STUDENTS
-- ============================================================================

-- HOW TO RUN THESE QUERIES:
--
-- Method 1: AWS Console
-- 1. Go to Amazon Athena in AWS Console
-- 2. Select your workgroup
-- 3. Copy and paste query
-- 4. Click "Run query"
-- 5. View results in the console
--
-- Method 2: AWS CLI
-- aws athena start-query-execution \
--   --query-string "YOUR_QUERY_HERE" \
--   --result-configuration "OutputLocation=s3://your-athena-results-bucket/" \
--   --query-execution-context "Database=ride_analytics_db"
--
-- Method 3: Python (boto3)
-- import boto3
--
-- client = boto3.client('athena')
-- response = client.start_query_execution(
--     QueryString='YOUR_QUERY',
--     QueryExecutionContext={'Database': 'ride_analytics_db'},
--     ResultConfiguration={'OutputLocation': 's3://bucket/path/'}
-- )
--
-- QUERY OPTIMIZATION TIPS:
--
-- 1. Use partitioning:
--    - Partition S3 data by date (year/month/day)
--    - Always filter on partition columns
--    - This reduces data scanned and cost
--
-- 2. Use appropriate data formats:
--    - Parquet is better than JSON (columnar, compressed)
--    - CSV is acceptable for small datasets
--
-- 3. Limit data scanned:
--    - Use WHERE clauses effectively
--    - Select only needed columns
--    - Use LIMIT for testing queries
--
-- 4. Use CTAS (Create Table As Select):
--    - Materialize frequently used aggregations
--    - Store results in Parquet format
--
-- 5. Use approximate functions for large datasets:
--    - approx_distinct() instead of COUNT(DISTINCT)
--    - approx_percentile() for percentile calculations
--
-- COST CONSIDERATIONS:
--
-- Athena charges $5 per TB of data scanned
-- - Partition your data to reduce scans
-- - Use columnar formats (Parquet)
-- - Compress your data
-- - Only select needed columns
--
-- EXAMPLE COSTS:
-- - 1 GB scanned = $0.005
-- - 100 GB scanned = $0.50
-- - 1 TB scanned = $5.00
--
-- TESTING QUERIES:
--
-- 1. Start with LIMIT 10 to test syntax
-- 2. Add EXPLAIN or EXPLAIN ANALYZE to see query plan
-- 3. Check bytes scanned in query results
-- 4. Optimize before running on full dataset
--
-- COMMON ATHENA FUNCTIONS:
--
-- Date/Time:
-- - from_iso8601_timestamp() - Parse ISO8601 string to timestamp
-- - date() - Extract date from timestamp
-- - date_format() - Format date
-- - date_diff() - Difference between dates
-- - current_timestamp - Get current time
--
-- Aggregation:
-- - COUNT(), SUM(), AVG(), MIN(), MAX()
-- - approx_distinct() - Approximate count distinct
-- - approx_percentile() - Approximate percentile
--
-- Window Functions:
-- - ROW_NUMBER(), RANK(), DENSE_RANK()
-- - LEAD(), LAG()
-- - FIRST_VALUE(), LAST_VALUE()
--
-- String Functions:
-- - CONCAT(), SUBSTR(), UPPER(), LOWER()
-- - REGEXP_EXTRACT(), REGEXP_REPLACE()
--
-- ATHENA LIMITATIONS:
--
-- - Query timeout: 30 minutes
-- - Result set size: 1 GB (can use CTAS for larger results)
-- - DML statements are limited
-- - No stored procedures
-- - No indexes (use partitioning instead)
--
-- CREATING VIEWS:
--
-- You can create views for frequently used queries:
--
-- CREATE OR REPLACE VIEW daily_summary AS
-- SELECT
--     DATE(from_iso8601_timestamp(timestamp)) as date,
--     COUNT(*) as rides,
--     SUM(fare) as revenue
-- FROM ride_analytics_db.ride_events
-- WHERE status = 'completed'
-- GROUP BY DATE(from_iso8601_timestamp(timestamp));
--
-- Then query the view:
-- SELECT * FROM daily_summary WHERE date >= current_date - interval '7' day;
