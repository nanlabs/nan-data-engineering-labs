-- ============================================================================
-- Checkpoint 02: Real-Time Analytics Platform
-- Athena View Definitions
-- ============================================================================
-- Description: Creates reusable analytical views over S3 data
-- Location: s3://rideshare-analytics-{account_id}-{region}/warehouse/
-- ============================================================================

-- ============================================================================
-- 1. Daily Rides Summary View
-- ============================================================================
CREATE OR REPLACE VIEW daily_rides AS
SELECT
    DATE(from_unixtime(timestamp)) AS ride_date,
    ride_id,
    rider_id,
    driver_id,
    status,
    pickup_location_city,
    dropoff_location_city,
    CAST(json_extract_scalar(pickup_location, '$.lat') AS DOUBLE) AS pickup_lat,
    CAST(json_extract_scalar(pickup_location, '$.lng') AS DOUBLE) AS pickup_lng,
    CAST(json_extract_scalar(dropoff_location, '$.lat') AS DOUBLE) AS dropoff_lat,
    CAST(json_extract_scalar(dropoff_location, '$.lng') AS DOUBLE) AS dropoff_lng,
    pickup_timestamp,
    dropoff_timestamp,
    duration_seconds,
    duration_seconds / 60.0 AS duration_minutes,
    distance_km,
    CASE
        WHEN distance_km > 0 AND duration_seconds > 0
        THEN (distance_km / (duration_seconds / 3600.0))
        ELSE 0
    END AS avg_speed_kmh,
    base_fare,
    surge_multiplier,
    total_fare,
    vehicle_type,
    from_unixtime(timestamp) AS event_timestamp,
    date_partition,
    hour_partition
FROM rideshare_rides
WHERE status = 'completed'
    AND total_fare > 0
    AND duration_seconds > 0;

-- ============================================================================
-- 2. Driver Performance View
-- ============================================================================
CREATE OR REPLACE VIEW driver_performance AS
WITH driver_stats AS (
    SELECT
        driver_id,
        COUNT(DISTINCT ride_id) AS total_rides,
        SUM(total_fare) AS total_earnings,
        AVG(total_fare) AS avg_fare_per_ride,
        SUM(distance_km) AS total_distance_km,
        SUM(duration_seconds) / 3600.0 AS total_hours_driving,
        AVG(duration_seconds) / 60.0 AS avg_ride_duration_minutes,
        AVG(distance_km) AS avg_distance_per_ride,
        MIN(from_unixtime(timestamp)) AS first_ride_date,
        MAX(from_unixtime(timestamp)) AS last_ride_date,
        DATE_DIFF('day', DATE(MIN(from_unixtime(timestamp))), DATE(MAX(from_unixtime(timestamp)))) + 1 AS days_active
    FROM rideshare_rides
    WHERE status = 'completed'
    GROUP BY driver_id
),
driver_ratings AS (
    SELECT
        driver_id,
        COUNT(*) AS rating_count,
        AVG(overall_rating) AS avg_rating,
        AVG(cleanliness_rating) AS avg_cleanliness,
        AVG(communication_rating) AS avg_communication,
        AVG(driving_rating) AS avg_driving,
        SUM(CASE WHEN overall_rating = 5 THEN 1 ELSE 0 END) AS five_star_count,
        SUM(CASE WHEN overall_rating <= 2 THEN 1 ELSE 0 END) AS low_rating_count,
        SUM(tip_amount) AS total_tips,
        AVG(tip_amount) AS avg_tip
    FROM rideshare_ratings
    GROUP BY driver_id
)
SELECT
    ds.driver_id,
    ds.total_rides,
    ds.total_earnings,
    ds.avg_fare_per_ride,
    ds.total_distance_km,
    ds.total_hours_driving,
    CASE
        WHEN ds.total_hours_driving > 0
        THEN ds.total_earnings / ds.total_hours_driving
        ELSE 0
    END AS earnings_per_hour,
    ds.avg_ride_duration_minutes,
    ds.avg_distance_per_ride,
    ds.first_ride_date,
    ds.last_ride_date,
    ds.days_active,
    CASE
        WHEN ds.days_active > 0
        THEN CAST(ds.total_rides AS DOUBLE) / ds.days_active
        ELSE 0
    END AS rides_per_day,
    COALESCE(dr.rating_count, 0) AS rating_count,
    COALESCE(dr.avg_rating, 0.0) AS avg_rating,
    COALESCE(dr.avg_cleanliness, 0.0) AS avg_cleanliness,
    COALESCE(dr.avg_communication, 0.0) AS avg_communication,
    COALESCE(dr.avg_driving, 0.0) AS avg_driving,
    COALESCE(dr.five_star_count, 0) AS five_star_count,
    COALESCE(dr.low_rating_count, 0) AS low_rating_count,
    COALESCE(dr.total_tips, 0.0) AS total_tips,
    COALESCE(dr.avg_tip, 0.0) AS avg_tip,
    CASE
        WHEN dr.rating_count > 0
        THEN CAST(dr.five_star_count AS DOUBLE) / dr.rating_count
        ELSE 0
    END AS five_star_rate
FROM driver_stats ds
LEFT JOIN driver_ratings dr ON ds.driver_id = dr.driver_id;

-- ============================================================================
-- 3. Revenue Analysis View
-- ============================================================================
CREATE OR REPLACE VIEW revenue_analysis AS
WITH daily_revenue AS (
    SELECT
        DATE(from_unixtime(timestamp)) AS revenue_date,
        pickup_location_city AS city,
        COUNT(DISTINCT ride_id) AS ride_count,
        SUM(base_fare) AS total_base_fare,
        SUM(total_fare - base_fare) AS total_surge_fee,
        SUM(total_fare) AS total_revenue,
        AVG(total_fare) AS avg_fare,
        AVG(surge_multiplier) AS avg_surge_multiplier,
        SUM(CASE WHEN surge_multiplier > 1.0 THEN 1 ELSE 0 END) AS surge_ride_count,
        AVG(distance_km) AS avg_distance,
        AVG(duration_seconds) / 60.0 AS avg_duration_minutes
    FROM rideshare_rides
    WHERE status = 'completed'
        AND total_fare > 0
    GROUP BY DATE(from_unixtime(timestamp)), pickup_location_city
),
payment_breakdown AS (
    SELECT
        DATE(from_unixtime(timestamp)) AS payment_date,
        payment_method,
        COUNT(*) AS transaction_count,
        SUM(amount) AS total_amount,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
        SUM(CASE WHEN fraud_detected = true THEN 1 ELSE 0 END) AS fraud_count
    FROM rideshare_payments
    GROUP BY DATE(from_unixtime(timestamp)), payment_method
)
SELECT
    dr.revenue_date,
    dr.city,
    dr.ride_count,
    dr.total_base_fare,
    dr.total_surge_fee,
    dr.total_revenue,
    dr.avg_fare,
    dr.avg_surge_multiplier,
    dr.surge_ride_count,
    CASE
        WHEN dr.ride_count > 0
        THEN CAST(dr.surge_ride_count AS DOUBLE) / dr.ride_count
        ELSE 0
    END AS surge_ride_percentage,
    dr.avg_distance,
    dr.avg_duration_minutes,
    CASE
        WHEN dr.avg_distance > 0
        THEN dr.total_revenue / dr.avg_distance
        ELSE 0
    END AS revenue_per_km,
    CASE
        WHEN dr.avg_duration_minutes > 0
        THEN dr.total_revenue / dr.avg_duration_minutes
        ELSE 0
    END AS revenue_per_minute
FROM daily_revenue dr;

-- ============================================================================
-- 4. Customer Insights View
-- ============================================================================
CREATE OR REPLACE VIEW customer_insights AS
WITH rider_activity AS (
    SELECT
        rider_id,
        COUNT(DISTINCT ride_id) AS total_rides,
        SUM(total_fare) AS total_spent,
        AVG(total_fare) AS avg_fare_paid,
        MIN(from_unixtime(timestamp)) AS first_ride_date,
        MAX(from_unixtime(timestamp)) AS last_ride_date,
        DATE_DIFF('day', DATE(MIN(from_unixtime(timestamp))), DATE(MAX(from_unixtime(timestamp)))) + 1 AS customer_lifetime_days,
        COUNT(DISTINCT pickup_location_city) AS cities_used,
        COUNT(DISTINCT vehicle_type) AS vehicle_types_used,
        SUM(CASE WHEN surge_multiplier > 1.0 THEN 1 ELSE 0 END) AS surge_rides,
        AVG(distance_km) AS avg_ride_distance
    FROM rideshare_rides
    WHERE status = 'completed'
    GROUP BY rider_id
),
rider_ratings AS (
    SELECT
        rider_id,
        COUNT(*) AS ratings_given,
        AVG(overall_rating) AS avg_rating_given,
        SUM(tip_amount) AS total_tips_given,
        AVG(tip_amount) AS avg_tip
    FROM rideshare_ratings
    GROUP BY rider_id
),
rider_segments AS (
    SELECT
        rider_id,
        total_rides,
        total_spent,
        CASE
            WHEN total_rides >= 50 THEN 'Power User'
            WHEN total_rides >= 20 THEN 'Frequent'
            WHEN total_rides >= 5 THEN 'Regular'
            ELSE 'Occasional'
        END AS rider_segment,
        CASE
            WHEN total_spent >= 500 THEN 'High Value'
            WHEN total_spent >= 200 THEN 'Medium Value'
            ELSE 'Low Value'
        END AS value_segment
    FROM rider_activity
)
SELECT
    ra.rider_id,
    ra.total_rides,
    ra.total_spent,
    ra.avg_fare_paid,
    ra.first_ride_date,
    ra.last_ride_date,
    ra.customer_lifetime_days,
    CASE
        WHEN ra.customer_lifetime_days > 0
        THEN CAST(ra.total_spent AS DOUBLE) / ra.customer_lifetime_days
        ELSE 0
    END AS daily_spending_rate,
    ra.cities_used,
    ra.vehicle_types_used,
    ra.surge_rides,
    CASE
        WHEN ra.total_rides > 0
        THEN CAST(ra.surge_rides AS DOUBLE) / ra.total_rides
        ELSE 0
    END AS surge_acceptance_rate,
    ra.avg_ride_distance,
    COALESCE(rr.ratings_given, 0) AS ratings_given,
    COALESCE(rr.avg_rating_given, 0.0) AS avg_rating_given,
    COALESCE(rr.total_tips_given, 0.0) AS total_tips_given,
    COALESCE(rr.avg_tip, 0.0) AS avg_tip,
    rs.rider_segment,
    rs.value_segment,
    DATE_DIFF('day', DATE(ra.last_ride_date), CURRENT_DATE) AS days_since_last_ride,
    CASE
        WHEN DATE_DIFF('day', DATE(ra.last_ride_date), CURRENT_DATE) > 30 THEN 'At Risk'
        WHEN DATE_DIFF('day', DATE(ra.last_ride_date), CURRENT_DATE) > 14 THEN 'Declining'
        ELSE 'Active'
    END AS churn_risk
FROM rider_activity ra
LEFT JOIN rider_ratings rr ON ra.rider_id = rr.rider_id
LEFT JOIN rider_segments rs ON ra.rider_id = rs.rider_id;

-- ============================================================================
-- 5. Hot Spots Historical View
-- ============================================================================
CREATE OR REPLACE VIEW hot_spots_history AS
WITH location_activity AS (
    SELECT
        DATE(from_unixtime(timestamp)) AS activity_date,
        HOUR(from_unixtime(timestamp)) AS activity_hour,
        pickup_location_city AS city,
        FLOOR(CAST(json_extract_scalar(pickup_location, '$.lat') AS DOUBLE) / 0.05) * 0.05 AS grid_lat,
        FLOOR(CAST(json_extract_scalar(pickup_location, '$.lng') AS DOUBLE) / 0.05) * 0.05 AS grid_lng,
        COUNT(*) AS pickup_count,
        0 AS dropoff_count
    FROM rideshare_rides
    WHERE status = 'completed'
    GROUP BY
        DATE(from_unixtime(timestamp)),
        HOUR(from_unixtime(timestamp)),
        pickup_location_city,
        FLOOR(CAST(json_extract_scalar(pickup_location, '$.lat') AS DOUBLE) / 0.05) * 0.05,
        FLOOR(CAST(json_extract_scalar(pickup_location, '$.lng') AS DOUBLE) / 0.05) * 0.05

    UNION ALL

    SELECT
        DATE(from_unixtime(timestamp)) AS activity_date,
        HOUR(from_unixtime(timestamp)) AS activity_hour,
        dropoff_location_city AS city,
        FLOOR(CAST(json_extract_scalar(dropoff_location, '$.lat') AS DOUBLE) / 0.05) * 0.05 AS grid_lat,
        FLOOR(CAST(json_extract_scalar(dropoff_location, '$.lng') AS DOUBLE) / 0.05) * 0.05 AS grid_lng,
        0 AS pickup_count,
        COUNT(*) AS dropoff_count
    FROM rideshare_rides
    WHERE status = 'completed'
    GROUP BY
        DATE(from_unixtime(timestamp)),
        HOUR(from_unixtime(timestamp)),
        dropoff_location_city,
        FLOOR(CAST(json_extract_scalar(dropoff_location, '$.lat') AS DOUBLE) / 0.05) * 0.05,
        FLOOR(CAST(json_extract_scalar(dropoff_location, '$.lng') AS DOUBLE) / 0.05) * 0.05
)
SELECT
    activity_date,
    activity_hour,
    city,
    grid_lat,
    grid_lng,
    SUM(pickup_count) AS total_pickups,
    SUM(dropoff_count) AS total_dropoffs,
    SUM(pickup_count) + SUM(dropoff_count) AS total_activity,
    SUM(pickup_count) - SUM(dropoff_count) AS net_demand,
    CASE
        WHEN SUM(pickup_count) + SUM(dropoff_count) >= 100 THEN 'Very High'
        WHEN SUM(pickup_count) + SUM(dropoff_count) >= 50 THEN 'High'
        WHEN SUM(pickup_count) + SUM(dropoff_count) >= 20 THEN 'Medium'
        ELSE 'Low'
    END AS activity_level,
    -- Approximate cell area: 0.05° × 0.05° ≈ 25 km²
    (SUM(pickup_count) + SUM(dropoff_count)) / 25.0 AS activity_density_per_km2
FROM location_activity
GROUP BY
    activity_date,
    activity_hour,
    city,
    grid_lat,
    grid_lng;

-- ============================================================================
-- End of View Definitions
-- ============================================================================
