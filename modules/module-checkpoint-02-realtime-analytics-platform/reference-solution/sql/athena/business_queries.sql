-- ============================================================================
-- Checkpoint 02: Real-Time Analytics Platform
-- Business Intelligence Queries
-- ============================================================================
-- Description: 20 analytical queries for business insights
-- Use Case: Ad-hoc analysis, dashboards, reporting
-- ============================================================================

-- ============================================================================
-- 1. Daily Volume Trends (Last 30 Days)
-- ============================================================================
-- Purpose: Identify growth patterns and seasonality
SELECT
    revenue_date,
    city,
    ride_count,
    total_revenue,
    avg_fare,
    surge_ride_percentage * 100 AS surge_ride_pct,
    revenue_per_km,
    LAG(ride_count) OVER (PARTITION BY city ORDER BY revenue_date) AS prev_day_rides,
    ((ride_count - LAG(ride_count) OVER (PARTITION BY city ORDER BY revenue_date)) * 100.0) /
        NULLIF(LAG(ride_count) OVER (PARTITION BY city ORDER BY revenue_date), 0) AS day_over_day_growth_pct
FROM revenue_analysis
WHERE revenue_date >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY revenue_date DESC, ride_count DESC;

-- ============================================================================
-- 2. Revenue by City (Current Month)
-- ============================================================================
-- Purpose: Compare city performance for resource allocation
WITH monthly_city_stats AS (
    SELECT
        city,
        SUM(ride_count) AS total_rides,
        SUM(total_revenue) AS total_revenue,
        AVG(avg_fare) AS avg_fare,
        SUM(surge_ride_count) AS surge_rides,
        AVG(avg_surge_multiplier) AS avg_surge
    FROM revenue_analysis
    WHERE revenue_date >= DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY city
),
city_rankings AS (
    SELECT
        city,
        total_rides,
        total_revenue,
        avg_fare,
        surge_rides,
        avg_surge,
        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
        total_revenue * 100.0 / SUM(total_revenue) OVER () AS revenue_share_pct
    FROM monthly_city_stats
)
SELECT
    revenue_rank,
    city,
    total_rides,
    total_revenue,
    ROUND(revenue_share_pct, 2) AS revenue_share_pct,
    avg_fare,
    surge_rides,
    ROUND(surge_rides * 100.0 / NULLIF(total_rides, 0), 2) AS surge_rate_pct,
    ROUND(avg_surge, 2) AS avg_surge_multiplier
FROM city_rankings
ORDER BY revenue_rank;

-- ============================================================================
-- 3. Surge Pricing Effectiveness
-- ============================================================================
-- Purpose: Analyze impact of surge pricing on revenue
SELECT
    CASE
        WHEN avg_surge_multiplier >= 2.0 THEN '2.0x+'
        WHEN avg_surge_multiplier >= 1.5 THEN '1.5x-2.0x'
        WHEN avg_surge_multiplier >= 1.2 THEN '1.2x-1.5x'
        ELSE 'No Surge (<1.2x)'
    END AS surge_tier,
    COUNT(*) AS days_count,
    SUM(ride_count) AS total_rides,
    SUM(total_revenue) AS total_revenue,
    AVG(avg_fare) AS avg_fare,
    SUM(total_surge_fee) AS total_surge_revenue,
    SUM(total_surge_fee) * 100.0 / NULLIF(SUM(total_revenue), 0) AS surge_revenue_share_pct,
    AVG(surge_ride_percentage) * 100 AS avg_surge_ride_pct
FROM revenue_analysis
WHERE revenue_date >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY
    CASE
        WHEN avg_surge_multiplier >= 2.0 THEN '2.0x+'
        WHEN avg_surge_multiplier >= 1.5 THEN '1.5x-2.0x'
        WHEN avg_surge_multiplier >= 1.2 THEN '1.2x-1.5x'
        ELSE 'No Surge (<1.2x)'
    END
ORDER BY avg_fare DESC;

-- ============================================================================
-- 4. Driver Utilization and Efficiency
-- ============================================================================
-- Purpose: Identify top and underperforming drivers
SELECT
    driver_id,
    total_rides,
    total_earnings,
    ROUND(earnings_per_hour, 2) AS earnings_per_hour,
    ROUND(rides_per_day, 2) AS rides_per_day,
    ROUND(avg_rating, 2) AS avg_rating,
    five_star_rate * 100 AS five_star_rate_pct,
    ROUND(total_distance_km, 2) AS total_km,
    ROUND(total_hours_driving, 2) AS total_hours,
    ROUND(avg_tip, 2) AS avg_tip,
    CASE
        WHEN earnings_per_hour >= 30 AND avg_rating >= 4.7 THEN 'Top Performer'
        WHEN earnings_per_hour >= 20 AND avg_rating >= 4.5 THEN 'High Performer'
        WHEN earnings_per_hour >= 15 AND avg_rating >= 4.0 THEN 'Average'
        ELSE 'Needs Improvement'
    END AS performance_tier,
    DATE_DIFF('day', DATE(last_ride_date), CURRENT_DATE) AS days_since_last_ride
FROM driver_performance
WHERE total_rides >= 10
ORDER BY earnings_per_hour DESC
LIMIT 100;

-- ============================================================================
-- 5. Customer Churn Analysis
-- ============================================================================
-- Purpose: Identify at-risk customers for retention campaigns
SELECT
    churn_risk,
    rider_segment,
    value_segment,
    COUNT(*) AS customer_count,
    SUM(total_spent) AS total_lifetime_value,
    AVG(total_spent) AS avg_lifetime_value,
    AVG(total_rides) AS avg_rides,
    AVG(days_since_last_ride) AS avg_days_since_last_ride,
    AVG(avg_rating_given) AS avg_rating_given,
    SUM(total_spent) * 100.0 / SUM(SUM(total_spent)) OVER () AS ltv_share_pct
FROM customer_insights
GROUP BY churn_risk, rider_segment, value_segment
ORDER BY
    CASE churn_risk
        WHEN 'At Risk' THEN 1
        WHEN 'Declining' THEN 2
        ELSE 3
    END,
    total_lifetime_value DESC;

-- ============================================================================
-- 6. Top 20 Drivers by Revenue (Last 90 Days)
-- ============================================================================
SELECT
    driver_id,
    total_rides,
    ROUND(total_earnings, 2) AS total_earnings,
    ROUND(avg_fare_per_ride, 2) AS avg_fare,
    ROUND(earnings_per_hour, 2) AS earnings_per_hour,
    ROUND(avg_rating, 2) AS avg_rating,
    rating_count,
    ROUND(five_star_rate * 100, 1) AS five_star_rate_pct,
    ROUND(total_tips, 2) AS total_tips,
    days_active,
    ROUND(rides_per_day, 1) AS rides_per_day
FROM driver_performance
WHERE last_ride_date >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY total_earnings DESC
LIMIT 20;

-- ============================================================================
-- 7. Peak Hours Analysis by City
-- ============================================================================
-- Purpose: Optimize driver availability by time of day
SELECT
    city,
    activity_hour,
    AVG(total_activity) AS avg_hourly_activity,
    SUM(total_pickups) AS total_pickups,
    SUM(total_dropoffs) AS total_dropoffs,
    AVG(net_demand) AS avg_net_demand,
    COUNT(DISTINCT activity_date) AS days_observed,
    AVG(activity_density_per_km2) AS avg_density_per_km2,
    CASE
        WHEN AVG(total_activity) >= 80 THEN 'Peak'
        WHEN AVG(total_activity) >= 50 THEN 'High'
        WHEN AVG(total_activity) >= 20 THEN 'Medium'
        ELSE 'Low'
    END AS demand_level
FROM hot_spots_history
WHERE activity_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY city, activity_hour
ORDER BY city, activity_hour;

-- ============================================================================
-- 8. Week-over-Week Growth Analysis
-- ============================================================================
-- Purpose: Track business growth trends
WITH weekly_metrics AS (
    SELECT
        DATE_TRUNC('week', revenue_date) AS week_start,
        city,
        SUM(ride_count) AS weekly_rides,
        SUM(total_revenue) AS weekly_revenue,
        AVG(avg_fare) AS weekly_avg_fare
    FROM revenue_analysis
    WHERE revenue_date >= CURRENT_DATE - INTERVAL '12' WEEK
    GROUP BY DATE_TRUNC('week', revenue_date), city
)
SELECT
    week_start,
    city,
    weekly_rides,
    weekly_revenue,
    ROUND(weekly_avg_fare, 2) AS weekly_avg_fare,
    LAG(weekly_rides) OVER (PARTITION BY city ORDER BY week_start) AS prev_week_rides,
    LAG(weekly_revenue) OVER (PARTITION BY city ORDER BY week_start) AS prev_week_revenue,
    ROUND(
        ((weekly_rides - LAG(weekly_rides) OVER (PARTITION BY city ORDER BY week_start)) * 100.0) /
        NULLIF(LAG(weekly_rides) OVER (PARTITION BY city ORDER BY week_start), 0),
        2
    ) AS rides_wow_growth_pct,
    ROUND(
        ((weekly_revenue - LAG(weekly_revenue) OVER (PARTITION BY city ORDER BY week_start)) * 100.0) /
        NULLIF(LAG(weekly_revenue) OVER (PARTITION BY city ORDER BY week_start), 0),
        2
    ) AS revenue_wow_growth_pct
FROM weekly_metrics
ORDER BY week_start DESC, city;

-- ============================================================================
-- 9. Payment Method Performance
-- ============================================================================
-- Purpose: Analyze payment preferences and failure rates
SELECT
    payment_method,
    COUNT(*) AS total_transactions,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_transaction_amount,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS failure_rate_pct,
    SUM(CASE WHEN fraud_detected = true THEN 1 ELSE 0 END) AS fraud_count,
    ROUND(
        SUM(CASE WHEN fraud_detected = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS fraud_rate_pct,
    SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () AS revenue_share_pct
FROM rideshare_payments
WHERE DATE(from_unixtime(timestamp)) >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY payment_method
ORDER BY total_amount DESC;

-- ============================================================================
-- 10. Customer Satisfaction by Vehicle Type
-- ============================================================================
SELECT
    r.vehicle_type,
    COUNT(DISTINCT r.ride_id) AS ride_count,
    COUNT(DISTINCT rt.rating_id) AS rating_count,
    AVG(r.total_fare) AS avg_fare,
    AVG(rt.overall_rating) AS avg_overall_rating,
    AVG(rt.cleanliness_rating) AS avg_cleanliness,
    AVG(rt.communication_rating) AS avg_communication,
    AVG(rt.driving_rating) AS avg_driving,
    SUM(CASE WHEN rt.overall_rating = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(rt.rating_id) AS five_star_pct,
    SUM(CASE WHEN rt.overall_rating <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(rt.rating_id) AS low_rating_pct,
    AVG(rt.tip_amount) AS avg_tip
FROM rideshare_rides r
LEFT JOIN rideshare_ratings rt ON r.ride_id = rt.ride_id
WHERE DATE(from_unixtime(r.timestamp)) >= CURRENT_DATE - INTERVAL '30' DAY
    AND r.status = 'completed'
GROUP BY r.vehicle_type
ORDER BY avg_overall_rating DESC;

-- ============================================================================
-- 11. Hot Spots - Top 30 Most Active Locations
-- ============================================================================
SELECT
    city,
    grid_lat,
    grid_lng,
    SUM(total_activity) AS total_activity,
    SUM(total_pickups) AS total_pickups,
    SUM(total_dropoffs) AS total_dropoffs,
    AVG(activity_density_per_km2) AS avg_density,
    AVG(net_demand) AS avg_net_demand,
    CASE
        WHEN AVG(net_demand) > 20 THEN 'High Pickup Demand'
        WHEN AVG(net_demand) < -20 THEN 'High Dropoff Volume'
        ELSE 'Balanced'
    END AS demand_pattern
FROM hot_spots_history
WHERE activity_date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY city, grid_lat, grid_lng
ORDER BY total_activity DESC
LIMIT 30;

-- ============================================================================
-- 12. Driver Retention Analysis
-- ============================================================================
-- Purpose: Understand driver lifecycle and attrition
WITH driver_cohorts AS (
    SELECT
        driver_id,
        DATE_TRUNC('month', first_ride_date) AS cohort_month,
        days_active,
        total_rides,
        total_earnings,
        DATE_DIFF('day', DATE(last_ride_date), CURRENT_DATE) AS days_inactive
    FROM driver_performance
)
SELECT
    cohort_month,
    COUNT(*) AS drivers_in_cohort,
    AVG(days_active) AS avg_days_active,
    AVG(total_rides) AS avg_rides_per_driver,
    AVG(total_earnings) AS avg_earnings_per_driver,
    SUM(CASE WHEN days_inactive <= 7 THEN 1 ELSE 0 END) AS active_drivers,
    SUM(CASE WHEN days_inactive > 30 THEN 1 ELSE 0 END) AS churned_drivers,
    ROUND(
        SUM(CASE WHEN days_inactive <= 7 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS retention_rate_pct
FROM driver_cohorts
GROUP BY cohort_month
ORDER BY cohort_month DESC;

-- ============================================================================
-- 13. Fraud Detection Summary
-- ============================================================================
SELECT
    DATE(from_unixtime(timestamp)) AS fraud_date,
    payment_method,
    COUNT(*) AS total_attempts,
    SUM(CASE WHEN fraud_detected = true THEN 1 ELSE 0 END) AS fraud_detected_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    SUM(CASE WHEN fraud_detected = true THEN amount ELSE 0 END) AS potential_fraud_amount,
    AVG(fraud_score) AS avg_fraud_score,
    MAX(fraud_score) AS max_fraud_score
FROM rideshare_payments
WHERE DATE(from_unixtime(timestamp)) >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY DATE(from_unixtime(timestamp)), payment_method
HAVING SUM(CASE WHEN fraud_detected = true THEN 1 ELSE 0 END) > 0
ORDER BY fraud_date DESC, fraud_detected_count DESC;

-- ============================================================================
-- 14. Customer Lifetime Value Distribution
-- ============================================================================
SELECT
    value_segment,
    rider_segment,
    COUNT(*) AS customer_count,
    AVG(total_spent) AS avg_ltv,
    SUM(total_spent) AS total_revenue,
    AVG(total_rides) AS avg_rides,
    AVG(avg_fare_paid) AS avg_fare,
    AVG(customer_lifetime_days) AS avg_customer_age_days,
    AVG(total_tips_given) AS avg_total_tips,
    SUM(total_spent) * 100.0 / SUM(SUM(total_spent)) OVER () AS revenue_contribution_pct
FROM customer_insights
GROUP BY value_segment, rider_segment
ORDER BY total_revenue DESC;

-- ============================================================================
-- 15. Distance and Duration Analysis
-- ============================================================================
SELECT
    CASE
        WHEN distance_km < 5 THEN '0-5 km'
        WHEN distance_km < 10 THEN '5-10 km'
        WHEN distance_km < 20 THEN '10-20 km'
        WHEN distance_km < 30 THEN '20-30 km'
        ELSE '30+ km'
    END AS distance_bucket,
    COUNT(*) AS ride_count,
    AVG(distance_km) AS avg_distance,
    AVG(duration_minutes) AS avg_duration,
    AVG(total_fare) AS avg_fare,
    AVG(total_fare / NULLIF(distance_km, 0)) AS avg_fare_per_km,
    AVG(avg_speed_kmh) AS avg_speed,
    SUM(total_fare) AS total_revenue
FROM daily_rides
WHERE ride_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY
    CASE
        WHEN distance_km < 5 THEN '0-5 km'
        WHEN distance_km < 10 THEN '5-10 km'
        WHEN distance_km < 20 THEN '10-20 km'
        WHEN distance_km < 30 THEN '20-30 km'
        ELSE '30+ km'
    END
ORDER BY avg_distance;

-- ============================================================================
-- 16. Top Revenue Routes (City Pairs)
-- ============================================================================
SELECT
    pickup_location_city AS origin,
    dropoff_location_city AS destination,
    COUNT(*) AS ride_count,
    AVG(distance_km) AS avg_distance,
    AVG(duration_minutes) AS avg_duration,
    AVG(total_fare) AS avg_fare,
    SUM(total_fare) AS total_revenue,
    AVG(surge_multiplier) AS avg_surge,
    SUM(CASE WHEN surge_multiplier > 1.0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS surge_ride_pct
FROM daily_rides
WHERE ride_date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY pickup_location_city, dropoff_location_city
HAVING COUNT(*) >= 10
ORDER BY total_revenue DESC
LIMIT 20;

-- ============================================================================
-- 17. Driver Performance Trends
-- ============================================================================
WITH monthly_driver_metrics AS (
    SELECT
        driver_id,
        DATE_TRUNC('month', from_unixtime(timestamp)) AS month,
        COUNT(*) AS monthly_rides,
        SUM(total_fare) AS monthly_earnings,
        AVG(total_fare) AS avg_fare
    FROM rideshare_rides
    WHERE status = 'completed'
        AND from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '6' MONTH
    GROUP BY driver_id, DATE_TRUNC('month', from_unixtime(timestamp))
)
SELECT
    driver_id,
    month,
    monthly_rides,
    monthly_earnings,
    avg_fare,
    LAG(monthly_rides) OVER (PARTITION BY driver_id ORDER BY month) AS prev_month_rides,
    ROUND(
        ((monthly_rides - LAG(monthly_rides) OVER (PARTITION BY driver_id ORDER BY month)) * 100.0) /
        NULLIF(LAG(monthly_rides) OVER (PARTITION BY driver_id ORDER BY month), 0),
        2
    ) AS ride_mom_growth_pct,
    ROUND(
        ((monthly_earnings - LAG(monthly_earnings) OVER (PARTITION BY driver_id ORDER BY month)) * 100.0) /
        NULLIF(LAG(monthly_earnings) OVER (PARTITION BY driver_id ORDER BY month), 0),
        2
    ) AS earnings_mom_growth_pct
FROM monthly_driver_metrics
WHERE monthly_rides >= 20
ORDER BY driver_id, month DESC;

-- ============================================================================
-- 18. Customer Acquisition and Retention
-- ============================================================================
WITH monthly_riders AS (
    SELECT
        DATE_TRUNC('month', from_unixtime(timestamp)) AS month,
        rider_id,
        MIN(from_unixtime(timestamp)) AS first_ride_in_month
    FROM rideshare_rides
    WHERE status = 'completed'
    GROUP BY DATE_TRUNC('month', from_unixtime(timestamp)), rider_id
),
cohort_analysis AS (
    SELECT
        m1.month,
        COUNT(DISTINCT m1.rider_id) AS total_riders,
        COUNT(DISTINCT CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM monthly_riders m2
                WHERE m2.rider_id = m1.rider_id
                AND m2.month < m1.month
            ) THEN m1.rider_id
        END) AS new_riders,
        COUNT(DISTINCT CASE
            WHEN EXISTS (
                SELECT 1 FROM monthly_riders m2
                WHERE m2.rider_id = m1.rider_id
                AND m2.month = m1.month - INTERVAL '1' MONTH
            ) THEN m1.rider_id
        END) AS retained_riders
    FROM monthly_riders m1
    GROUP BY m1.month
)
SELECT
    month,
    total_riders,
    new_riders,
    retained_riders,
    ROUND(new_riders * 100.0 / total_riders, 2) AS new_rider_pct,
    ROUND(retained_riders * 100.0 / total_riders, 2) AS retention_rate_pct
FROM cohort_analysis
WHERE month >= CURRENT_DATE - INTERVAL '12' MONTH
ORDER BY month DESC;

-- ============================================================================
-- 19. Surge Pricing Patterns by Location and Time
-- ============================================================================
SELECT
    pickup_location_city AS city,
    CASE
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 6 AND 9 THEN 'Morning Rush (6-9 AM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 17 AND 20 THEN 'Evening Rush (5-8 PM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 21 AND 23 THEN 'Late Night (9-11 PM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 0 AND 5 THEN 'Overnight (12-5 AM)'
        ELSE 'Off-Peak (9 AM-5 PM)'
    END AS time_period,
    COUNT(*) AS ride_count,
    AVG(surge_multiplier) AS avg_surge,
    MAX(surge_multiplier) AS max_surge,
    SUM(CASE WHEN surge_multiplier >= 2.0 THEN 1 ELSE 0 END) AS high_surge_count,
    AVG(total_fare) AS avg_fare,
    SUM(total_fare - base_fare) AS total_surge_revenue
FROM rideshare_rides
WHERE status = 'completed'
    AND DATE(from_unixtime(timestamp)) >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY
    pickup_location_city,
    CASE
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 6 AND 9 THEN 'Morning Rush (6-9 AM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 17 AND 20 THEN 'Evening Rush (5-8 PM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 21 AND 23 THEN 'Late Night (9-11 PM)'
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 0 AND 5 THEN 'Overnight (12-5 AM)'
        ELSE 'Off-Peak (9 AM-5 PM)'
    END
ORDER BY city, avg_surge DESC;

-- ============================================================================
-- 20. Overall Business Health Dashboard
-- ============================================================================
-- Purpose: Executive summary of key metrics
WITH current_month AS (
    SELECT
        SUM(ride_count) AS total_rides,
        SUM(total_revenue) AS total_revenue,
        AVG(avg_fare) AS avg_fare,
        COUNT(DISTINCT city) AS cities_active
    FROM revenue_analysis
    WHERE revenue_date >= DATE_TRUNC('month', CURRENT_DATE)
),
prev_month AS (
    SELECT
        SUM(ride_count) AS total_rides,
        SUM(total_revenue) AS total_revenue,
        AVG(avg_fare) AS avg_fare
    FROM revenue_analysis
    WHERE revenue_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1' MONTH)
        AND revenue_date < DATE_TRUNC('month', CURRENT_DATE)
),
driver_stats AS (
    SELECT
        COUNT(*) AS total_drivers,
        SUM(CASE WHEN days_since_last_ride <= 7 THEN 1 ELSE 0 END) AS active_drivers,
        AVG(avg_rating) AS avg_driver_rating
    FROM driver_performance
),
customer_stats AS (
    SELECT
        COUNT(*) AS total_customers,
        SUM(CASE WHEN days_since_last_ride <= 30 THEN 1 ELSE 0 END) AS active_customers,
        AVG(avg_rating_given) AS avg_customer_rating
    FROM customer_insights
)
SELECT
    'Current Month' AS metric_period,
    cm.total_rides,
    cm.total_revenue,
    ROUND(cm.avg_fare, 2) AS avg_fare,
    cm.cities_active,
    ROUND((cm.total_rides - pm.total_rides) * 100.0 / NULLIF(pm.total_rides, 0), 2) AS rides_mom_growth_pct,
    ROUND((cm.total_revenue - pm.total_revenue) * 100.0 / NULLIF(pm.total_revenue, 0), 2) AS revenue_mom_growth_pct,
    ds.total_drivers,
    ds.active_drivers,
    ROUND(ds.avg_driver_rating, 2) AS avg_driver_rating,
    cs.total_customers,
    cs.active_customers,
    ROUND(cs.avg_customer_rating, 2) AS avg_customer_satisfaction
FROM current_month cm
CROSS JOIN prev_month pm
CROSS JOIN driver_stats ds
CROSS JOIN customer_stats cs;

-- ============================================================================
-- End of Business Queries
-- ============================================================================
