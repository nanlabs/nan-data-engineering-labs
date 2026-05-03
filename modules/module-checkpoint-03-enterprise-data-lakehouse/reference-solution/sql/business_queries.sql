-- =============================================================================
-- BUSINESS INTELLIGENCE QUERIES - Enterprise Data Lakehouse
-- =============================================================================
-- Purpose: 25 comprehensive BI queries leveraging gold layer views for
--          revenue analysis, customer segmentation, churn prediction,
--          product recommendations, and executive dashboards
-- Database: lakehouse_gold
-- Compatible: Amazon Athena, Presto, Trino
-- =============================================================================

-- =============================================================================
-- QUERY 1: Revenue Trend Analysis - Daily, Weekly, Monthly Patterns
-- =============================================================================
-- Business Question: What are our revenue trends across different time periods?
-- =============================================================================

WITH daily_revenue AS (
    SELECT
        date,
        year,
        quarter,
        month,
        week_of_year,
        SUM(net_revenue) AS daily_revenue,
        SUM(gross_profit) AS daily_profit,
        AVG(avg_transaction_value) AS avg_transaction_value,
        SUM(transaction_count) AS transaction_count
    FROM lakehouse_gold.financial_summary
    WHERE date >= DATE_ADD('day', -90, CURRENT_DATE)
    GROUP BY date, year, quarter, month, week_of_year
),
trend_metrics AS (
    SELECT
        dr.*,
        AVG(dr.daily_revenue) OVER (
            ORDER BY dr.date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS ma_7day,
        LAG(dr.daily_revenue, 7) OVER (ORDER BY dr.date) AS revenue_week_ago,
        LAG(dr.daily_revenue, 30) OVER (ORDER BY dr.date) AS revenue_month_ago
    FROM daily_revenue dr
)
SELECT
    date,
    year,
    quarter,
    month,
    week_of_year,
    daily_revenue,
    daily_profit,
    avg_transaction_value,
    transaction_count,
    ma_7day,
    daily_revenue - revenue_week_ago AS wow_change,
    CASE
        WHEN revenue_week_ago > 0
        THEN ((daily_revenue - revenue_week_ago) / revenue_week_ago) * 100
        ELSE 0
    END AS wow_change_pct,
    daily_revenue - revenue_month_ago AS mom_change,
    CASE
        WHEN revenue_month_ago > 0
        THEN ((daily_revenue - revenue_month_ago) / revenue_month_ago) * 100
        ELSE 0
    END AS mom_change_pct
FROM trend_metrics
ORDER BY date DESC;

-- =============================================================================
-- QUERY 2: Customer Segmentation - RFM Analysis Deep Dive
-- =============================================================================
-- Business Question: How should we segment our customers for targeted marketing?
-- =============================================================================

SELECT
    rfm_segment,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    SUM(net_spent_lifetime) AS total_revenue,
    AVG(net_spent_lifetime) AS avg_revenue_per_customer,
    AVG(total_transactions) AS avg_transactions,
    AVG(customer_lifetime_value) AS avg_clv,
    AVG(engagement_score) AS avg_engagement,
    AVG(days_since_last_purchase) AS avg_days_since_purchase,
    -- Recommended actions
    CASE
        WHEN rfm_segment = 'Champions' THEN 'Reward loyalty, VIP treatment, early access'
        WHEN rfm_segment = 'Loyal Customers' THEN 'Upsell, ask for reviews, engagement programs'
        WHEN rfm_segment = 'New Customers' THEN 'Onboarding campaigns, build relationship'
        WHEN rfm_segment = 'At Risk' THEN 'Re-engagement campaigns, special offers'
        WHEN rfm_segment = 'Cannot Lose Them' THEN 'Aggressive win-back campaigns, personalized outreach'
        WHEN rfm_segment = 'Lost' THEN 'Ignore or send limited re-activation attempts'
        WHEN rfm_segment = 'Promising' THEN 'Build frequency, offer incentives'
        WHEN rfm_segment = 'Potential Loyalists' THEN 'Increase engagement, membership programs'
        ELSE 'Standard retention campaigns'
    END AS recommended_action
FROM lakehouse_gold.customer_360
GROUP BY rfm_segment
ORDER BY total_revenue DESC;

-- =============================================================================
-- QUERY 3: High-Value Customer Identification
-- =============================================================================
-- Business Question: Who are our most valuable customers and what do they buy?
-- =============================================================================

WITH top_customers AS (
    SELECT
        c.*,
        ROW_NUMBER() OVER (ORDER BY c.customer_lifetime_value DESC) AS clv_rank
    FROM lakehouse_gold.customer_360 c
    WHERE c.is_churned = false
),
top_customer_products AS (
    SELECT
        f.customer_sk,
        p.category,
        p.brand,
        COUNT(DISTINCT f.transaction_id) AS transactions,
        SUM(f.net_amount) AS category_spend,
        ROW_NUMBER() OVER (PARTITION BY f.customer_sk ORDER BY SUM(f.net_amount) DESC) AS category_rank
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    INNER JOIN top_customers tc ON f.customer_sk = tc.customer_sk
    WHERE tc.clv_rank <= 100
    GROUP BY f.customer_sk, p.category, p.brand
)
SELECT
    tc.customer_id,
    tc.customer_name,
    tc.email,
    tc.customer_segment,
    tc.loyalty_tier,
    tc.customer_lifetime_value,
    tc.net_spent_lifetime,
    tc.total_transactions,
    tc.avg_transaction_value,
    tc.days_since_last_purchase,
    tcp.category AS top_category,
    tcp.brand AS top_brand,
    tcp.category_spend,
    tcp.transactions AS category_transactions
FROM top_customers tc
LEFT JOIN top_customer_products tcp ON tc.customer_sk = tcp.customer_sk AND tcp.category_rank = 1
WHERE tc.clv_rank <= 100
ORDER BY tc.customer_lifetime_value DESC;

-- =============================================================================
-- QUERY 4: Churn Risk Analysis & Prevention
-- =============================================================================
-- Business Question: Which customers are at risk of churning and why?
-- =============================================================================

SELECT
    churn_risk,
    customer_segment,
    COUNT(*) AS customer_count,
    AVG(customer_lifetime_value) AS avg_clv,
    AVG(days_since_last_purchase) AS avg_days_inactive,
    AVG(net_spent_lifetime) AS avg_lifetime_spend,
    AVG(total_transactions) AS avg_transaction_count,
    AVG(engagement_score) AS avg_engagement_score,
    SUM(net_spent_lifetime) AS at_risk_revenue,
    -- Churn indicators
    SUM(CASE WHEN days_since_last_purchase > 90 THEN 1 ELSE 0 END) AS inactive_90_days,
    SUM(CASE WHEN days_since_last_purchase > 180 THEN 1 ELSE 0 END) AS inactive_180_days,
    SUM(CASE WHEN transactions_last_90d = 0 THEN 1 ELSE 0 END) AS no_recent_transactions,
    -- Recommended intervention
    CASE
        WHEN churn_risk = 'High Risk' THEN 'Immediate personalized outreach + special offer'
        WHEN churn_risk = 'Medium Risk' THEN 'Re-engagement email campaign + discount'
        WHEN churn_risk = 'Low Risk' THEN 'Standard retention communication'
        ELSE 'Continue normal engagement'
    END AS intervention_strategy
FROM lakehouse_gold.customer_360
WHERE is_churned = false
GROUP BY churn_risk, customer_segment
ORDER BY at_risk_revenue DESC;

-- =============================================================================
-- QUERY 5: Product Recommendation Engine - Collaborative Filtering
-- =============================================================================
-- Business Question: What products should we recommend to each customer?
-- =============================================================================

WITH customer_purchase_history AS (
    SELECT
        f.customer_sk,
        f.product_sk,
        p.category,
        SUM(f.net_amount) AS total_spent,
        COUNT(*) AS purchase_frequency
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    WHERE f.transaction_date >= DATE_ADD('month', -12, CURRENT_DATE)
    GROUP BY f.customer_sk, f.product_sk, p.category
),
similar_customers AS (
    SELECT
        cph1.customer_sk AS customer_a,
        cph2.customer_sk AS customer_b,
        COUNT(DISTINCT cph1.product_sk) AS common_products,
        AVG(ABS(cph1.total_spent - cph2.total_spent)) AS avg_spend_diff
    FROM customer_purchase_history cph1
    INNER JOIN customer_purchase_history cph2
        ON cph1.product_sk = cph2.product_sk
        AND cph1.customer_sk <> cph2.customer_sk
    GROUP BY cph1.customer_sk, cph2.customer_sk
    HAVING COUNT(DISTINCT cph1.product_sk) >= 3
),
recommendations AS (
    SELECT
        sc.customer_a AS target_customer_sk,
        cph.product_sk AS recommended_product_sk,
        p.product_name,
        p.category,
        COUNT(DISTINCT sc.customer_b) AS recommendation_strength,
        AVG(cph.total_spent) AS avg_spend_on_product
    FROM similar_customers sc
    INNER JOIN customer_purchase_history cph ON sc.customer_b = cph.customer_sk
    INNER JOIN lakehouse_gold.dim_product p ON cph.product_sk = p.product_sk
    WHERE NOT EXISTS (
        SELECT 1
        FROM customer_purchase_history cph2
        WHERE cph2.customer_sk = sc.customer_a
        AND cph2.product_sk = cph.product_sk
    )
    GROUP BY sc.customer_a, cph.product_sk, p.product_name, p.category
)
SELECT
    c.customer_id,
    c.customer_name,
    c.email,
    r.recommended_product_sk,
    r.product_name,
    r.category,
    r.recommendation_strength,
    r.avg_spend_on_product,
    ROW_NUMBER() OVER (PARTITION BY r.target_customer_sk ORDER BY r.recommendation_strength DESC) AS recommendation_rank
FROM recommendations r
INNER JOIN lakehouse_gold.customer_360 c ON r.target_customer_sk = c.customer_sk
WHERE c.is_churned = false
  AND c.engagement_score > 50
QUALIFY recommendation_rank <= 5
ORDER BY c.customer_lifetime_value DESC, recommendation_rank;

-- =============================================================================
-- QUERY 6: Geographic Performance Analysis
-- =============================================================================
-- Business Question: Which regions are performing best and worst?
-- =============================================================================

WITH geographic_metrics AS (
    SELECT
        country,
        state,
        COUNT(DISTINCT customer_id) AS total_customers,
        SUM(net_spent_lifetime) AS total_revenue,
        AVG(customer_lifetime_value) AS avg_clv,
        AVG(total_transactions) AS avg_transactions_per_customer,
        AVG(engagement_score) AS avg_engagement,
        SUM(CASE WHEN churn_risk IN ('High Risk', 'Medium Risk') THEN 1 ELSE 0 END) AS at_risk_customers,
        SUM(CASE WHEN rfm_segment IN ('Champions', 'Loyal Customers') THEN 1 ELSE 0 END) AS high_value_customers
    FROM lakehouse_gold.customer_360
    WHERE country IS NOT NULL
    GROUP BY country, state
),
rankings AS (
    SELECT
        gm.*,
        ROW_NUMBER() OVER (PARTITION BY gm.country ORDER BY gm.total_revenue DESC) AS state_revenue_rank,
        total_revenue / NULLIF(total_customers, 0) AS revenue_per_customer,
        CAST(at_risk_customers AS DOUBLE) / NULLIF(total_customers, 0) * 100 AS churn_risk_pct,
        CAST(high_value_customers AS DOUBLE) / NULLIF(total_customers, 0) * 100 AS high_value_pct
    FROM geographic_metrics gm
)
SELECT
    country,
    state,
    total_customers,
    total_revenue,
    revenue_per_customer,
    avg_clv,
    avg_transactions_per_customer,
    avg_engagement,
    at_risk_customers,
    churn_risk_pct,
    high_value_customers,
    high_value_pct,
    state_revenue_rank,
    CASE
        WHEN state_revenue_rank = 1 THEN 'Top Performing State'
        WHEN churn_risk_pct > 30 THEN 'High Churn Risk Region'
        WHEN high_value_pct > 40 THEN 'Premium Market'
        ELSE 'Standard Market'
    END AS market_classification
FROM rankings
ORDER BY country, total_revenue DESC;

-- =============================================================================
-- QUERY 7: Seasonality & Time-Based Patterns
-- =============================================================================
-- Business Question: What are our seasonal trends and patterns?
-- =============================================================================

WITH seasonal_revenue AS (
    SELECT
        year,
        quarter,
        month,
        day_of_week,
        is_weekend,
        is_holiday,
        category,
        SUM(net_revenue) AS total_revenue,
        AVG(avg_transaction_value) AS avg_order_value,
        SUM(transaction_count) AS total_transactions
    FROM lakehouse_gold.financial_summary
    WHERE date >= DATE_ADD('year', -2, CURRENT_DATE)
    GROUP BY year, quarter, month, day_of_week, is_weekend, is_holiday, category
),
aggregated_patterns AS (
    SELECT
        quarter,
        AVG(total_revenue) AS avg_quarterly_revenue,
        STDDEV(total_revenue) AS revenue_volatility
    FROM seasonal_revenue
    GROUP BY quarter
)
SELECT
    sr.year,
    sr.quarter,
    sr.month,
    sr.day_of_week,
    sr.is_weekend,
    sr.is_holiday,
    sr.category,
    sr.total_revenue,
    sr.avg_order_value,
    sr.total_transactions,
    ap.avg_quarterly_revenue,
    ap.revenue_volatility,
    -- Seasonality index
    sr.total_revenue / NULLIF(ap.avg_quarterly_revenue, 0) AS seasonality_index,
    -- Day performance
    CASE
        WHEN sr.is_weekend = true THEN 'Weekend'
        WHEN sr.day_of_week IN (1, 5) THEN 'Peak Weekday'
        ELSE 'Standard Weekday'
    END AS day_type
FROM seasonal_revenue sr
LEFT JOIN aggregated_patterns ap ON sr.quarter = ap.quarter
ORDER BY sr.year DESC, sr.month DESC, sr.total_revenue DESC;

-- =============================================================================
-- QUERY 8: Cohort Analysis - Customer Acquisition Performance
-- =============================================================================
-- Business Question: How do different customer cohorts perform over time?
-- =============================================================================

WITH customer_cohorts AS (
    SELECT
        customer_sk,
        customer_id,
        DATE_TRUNC('month', registration_date) AS cohort_month,
        registration_date,
        first_transaction_date,
        net_spent_lifetime,
        total_transactions,
        customer_lifetime_value
    FROM lakehouse_gold.customer_360
    WHERE registration_date IS NOT NULL
),
cohort_metrics AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size,
        AVG(net_spent_lifetime) AS avg_ltv,
        AVG(total_transactions) AS avg_transactions,
        AVG(customer_lifetime_value) AS avg_clv,
        SUM(net_spent_lifetime) AS total_cohort_revenue,
        -- Retention metrics
        SUM(CASE WHEN DATE_DIFF('day', first_transaction_date, CURRENT_DATE) >= 30 THEN 1 ELSE 0 END) AS retained_30d,
        SUM(CASE WHEN DATE_DIFF('day', first_transaction_date, CURRENT_DATE) >= 90 THEN 1 ELSE 0 END) AS retained_90d,
        SUM(CASE WHEN DATE_DIFF('day', first_transaction_date, CURRENT_DATE) >= 365 THEN 1 ELSE 0 END) AS retained_365d
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT
    cohort_month,
    cohort_size,
    avg_ltv,
    avg_transactions,
    avg_clv,
    total_cohort_revenue,
    -- Retention rates
    CAST(retained_30d AS DOUBLE) / NULLIF(cohort_size, 0) * 100 AS retention_rate_30d,
    CAST(retained_90d AS DOUBLE) / NULLIF(cohort_size, 0) * 100 AS retention_rate_90d,
    CAST(retained_365d AS DOUBLE) / NULLIF(cohort_size, 0) * 100 AS retention_rate_365d,
    -- Cohort comparison
    avg_ltv - LAG(avg_ltv) OVER (ORDER BY cohort_month) AS ltv_change_from_prev_cohort,
    RANK() OVER (ORDER BY avg_clv DESC) AS cohort_rank_by_clv
FROM cohort_metrics
WHERE cohort_month >= DATE_ADD('year', -2, CURRENT_DATE)
ORDER BY cohort_month DESC;

-- =============================================================================
-- QUERY 9: Product Performance & Cross-Sell Opportunities
-- =============================================================================
-- Business Question: Which products are frequently bought together?
-- =============================================================================

WITH product_pairs AS (
    SELECT
        f1.product_sk AS product_a,
        f2.product_sk AS product_b,
        p1.product_name AS product_a_name,
        p2.product_name AS product_b_name,
        p1.category AS category_a,
        p2.category AS category_b,
        COUNT(DISTINCT f1.customer_sk) AS customers_bought_both,
        AVG(f1.net_amount + f2.net_amount) AS avg_combined_value
    FROM lakehouse_gold.fact_transactions f1
    INNER JOIN lakehouse_gold.fact_transactions f2
        ON f1.customer_sk = f2.customer_sk
        AND f1.product_sk < f2.product_sk
        AND ABS(DATE_DIFF('day', f1.transaction_date, f2.transaction_date)) <= 30
    INNER JOIN lakehouse_gold.dim_product p1 ON f1.product_sk = p1.product_sk
    INNER JOIN lakehouse_gold.dim_product p2 ON f2.product_sk = p2.product_sk
    WHERE f1.transaction_date >= DATE_ADD('month', -6, CURRENT_DATE)
    GROUP BY f1.product_sk, f2.product_sk, p1.product_name, p2.product_name, p1.category, p2.category
    HAVING COUNT(DISTINCT f1.customer_sk) >= 10
),
support_metrics AS (
    SELECT
        pp.*,
        -- Calculate support (how popular is this combination)
        CAST(customers_bought_both AS DOUBLE) /
            (SELECT COUNT(DISTINCT customer_sk) FROM lakehouse_gold.fact_transactions) AS support,
        -- Rank combinations
        ROW_NUMBER() OVER (ORDER BY pp.customers_bought_both DESC) AS popularity_rank
    FROM product_pairs pp
)
SELECT
    product_a_name,
    product_b_name,
    category_a,
    category_b,
    customers_bought_both,
    avg_combined_value,
    ROUND(support * 100, 4) AS support_pct,
    popularity_rank,
    -- Recommendation
    CASE
        WHEN category_a = category_b THEN 'Same-Category Bundle'
        ELSE 'Cross-Category Bundle'
    END AS bundle_type
FROM support_metrics
WHERE popularity_rank <= 50
ORDER BY customers_bought_both DESC;

-- =============================================================================
-- QUERY 10: Anomaly Detection - Revenue & Transaction Outliers
-- =============================================================================
-- Business Question: What unusual patterns exist in our data?
-- =============================================================================

WITH daily_stats AS (
    SELECT
        date,
        SUM(net_revenue) AS daily_revenue,
        SUM(transaction_count) AS daily_transactions,
        AVG(avg_transaction_value) AS avg_order_value
    FROM lakehouse_gold.financial_summary
    WHERE date >= DATE_ADD('day', -90, CURRENT_DATE)
    GROUP BY date
),
stats_with_bounds AS (
    SELECT
        ds.*,
        AVG(daily_revenue) OVER () AS avg_revenue,
        STDDEV(daily_revenue) OVER () AS stddev_revenue,
        AVG(daily_transactions) OVER () AS avg_transactions,
        STDDEV(daily_transactions) OVER () AS stddev_transactions
    FROM daily_stats ds
),
anomalies AS (
    SELECT
        swb.*,
        -- Z-score for revenue
        (swb.daily_revenue - swb.avg_revenue) / NULLIF(swb.stddev_revenue, 0) AS revenue_z_score,
        -- Z-score for transactions
        (swb.daily_transactions - swb.avg_transactions) / NULLIF(swb.stddev_transactions, 0) AS transaction_z_score
    FROM stats_with_bounds swb
)
SELECT
    date,
    daily_revenue,
    avg_revenue,
    daily_transactions,
    avg_transactions,
    avg_order_value,
    revenue_z_score,
    transaction_z_score,
    -- Classify anomaly
    CASE
        WHEN ABS(revenue_z_score) > 3 THEN 'Extreme Anomaly'
        WHEN ABS(revenue_z_score) > 2 THEN 'Significant Anomaly'
        WHEN ABS(revenue_z_score) > 1.5 THEN 'Moderate Anomaly'
        ELSE 'Normal'
    END AS anomaly_classification,
    CASE
        WHEN revenue_z_score > 0 THEN 'Positive (Higher than expected)'
        ELSE 'Negative (Lower than expected)'
    END AS anomaly_direction
FROM anomalies
WHERE ABS(revenue_z_score) > 1.5
ORDER BY ABS(revenue_z_score) DESC;

-- =============================================================================
-- QUERY 11: Customer Purchase Frequency Analysis
-- =============================================================================
-- Business Question: How often do customers purchase and what affects frequency?
-- =============================================================================

WITH purchase_intervals AS (
    SELECT
        f.customer_sk,
        f.transaction_date,
        LAG(f.transaction_date) OVER (PARTITION BY f.customer_sk ORDER BY f.transaction_date) AS prev_transaction_date,
        DATE_DIFF('day',
            LAG(f.transaction_date) OVER (PARTITION BY f.customer_sk ORDER BY f.transaction_date),
            f.transaction_date
        ) AS days_between_purchases
    FROM lakehouse_gold.fact_transactions f
),
frequency_metrics AS (
    SELECT
        pi.customer_sk,
        COUNT(*) AS total_intervals,
        AVG(pi.days_between_purchases) AS avg_days_between_purchases,
        STDDEV(pi.days_between_purchases) AS purchase_frequency_stddev,
        MIN(pi.days_between_purchases) AS min_days_between,
        MAX(pi.days_between_purchases) AS max_days_between
    FROM purchase_intervals pi
    WHERE pi.days_between_purchases IS NOT NULL
    GROUP BY pi.customer_sk
)
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.rfm_segment,
    c.total_transactions,
    c.net_spent_lifetime,
    fm.avg_days_between_purchases,
    fm.purchase_frequency_stddev,
    fm.min_days_between,
    fm.max_days_between,
    -- Frequency category
    CASE
        WHEN fm.avg_days_between_purchases <= 7 THEN 'Very Frequent (Weekly)'
        WHEN fm.avg_days_between_purchases <= 30 THEN 'Frequent (Monthly)'
        WHEN fm.avg_days_between_purchases <= 90 THEN 'Moderate (Quarterly)'
        WHEN fm.avg_days_between_purchases <= 180 THEN 'Occasional (Biannual)'
        ELSE 'Rare (Annual+)'
    END AS frequency_category,
    -- Consistency score (lower stddev = more consistent)
    CASE
        WHEN fm.purchase_frequency_stddev <= fm.avg_days_between_purchases * 0.3 THEN 'Highly Consistent'
        WHEN fm.purchase_frequency_stddev <= fm.avg_days_between_purchases * 0.6 THEN 'Moderately Consistent'
        ELSE 'Inconsistent'
    END AS purchase_consistency
FROM lakehouse_gold.customer_360 c
INNER JOIN frequency_metrics fm ON c.customer_sk = fm.customer_sk
WHERE c.total_transactions >= 3
ORDER BY c.customer_lifetime_value DESC;

-- =============================================================================
-- QUERY 12: Product Portfolio Analysis
-- =============================================================================
-- Business Question: How should we optimize our product portfolio?
-- =============================================================================

WITH product_classification AS (
    SELECT
        pp.product_id,
        pp.product_name,
        pp.category,
        pp.brand,
        pp.net_revenue,
        pp.total_profit,
        pp.avg_profit_margin,
        pp.total_quantity_sold,
        pp.revenue_rank,
        -- BCG Matrix Classification
        CASE
            WHEN pp.revenue_rank <= 100 AND pp.yoy_growth_rate > 20 THEN 'Star'
            WHEN pp.revenue_rank <= 100 AND pp.yoy_growth_rate <= 20 THEN 'Cash Cow'
            WHEN pp.revenue_rank > 100 AND pp.yoy_growth_rate > 20 THEN 'Question Mark'
            ELSE 'Dog'
        END AS bcg_classification,
        pp.yoy_growth_rate,
        pp.days_since_last_sale,
        pp.inventory_classification
    FROM lakehouse_gold.product_performance pp
),
category_summary AS (
    SELECT
        category,
        COUNT(*) AS products_in_category,
        SUM(net_revenue) AS category_revenue,
        AVG(avg_profit_margin) AS avg_category_margin,
        SUM(CASE WHEN bcg_classification = 'Star' THEN 1 ELSE 0 END) AS stars,
        SUM(CASE WHEN bcg_classification = 'Cash Cow' THEN 1 ELSE 0 END) AS cash_cows,
        SUM(CASE WHEN bcg_classification = 'Question Mark' THEN 1 ELSE 0 END) AS question_marks,
        SUM(CASE WHEN bcg_classification = 'Dog' THEN 1 ELSE 0 END) AS dogs
    FROM product_classification
    GROUP BY category
)
SELECT
    pc.category,
    pc.product_name,
    pc.brand,
    pc.bcg_classification,
    pc.net_revenue,
    pc.total_profit,
    pc.avg_profit_margin,
    pc.yoy_growth_rate,
    pc.revenue_rank,
    pc.inventory_classification,
    cs.category_revenue,
    -- Strategic recommendation
    CASE
        WHEN pc.bcg_classification = 'Star' THEN 'Invest & Grow - High potential'
        WHEN pc.bcg_classification = 'Cash Cow' THEN 'Maintain & Extract - Stable revenue'
        WHEN pc.bcg_classification = 'Question Mark' THEN 'Test & Decide - Monitor closely'
        WHEN pc.bcg_classification = 'Dog' THEN 'Divest or Discontinue - Low value'
    END AS strategic_action
FROM product_classification pc
INNER JOIN category_summary cs ON pc.category = cs.category
ORDER BY pc.category, pc.net_revenue DESC;

-- =============================================================================
-- QUERY 13: Customer Winback Campaign Targeting
-- =============================================================================
-- Business Question: Which churned customers should we target for winback?
-- =============================================================================

SELECT
    customer_id,
    customer_name,
    email,
    customer_segment,
    net_spent_lifetime,
    customer_lifetime_value,
    total_transactions,
    avg_transaction_value,
    last_transaction_date,
    days_since_last_purchase,
    most_frequent_category,
    most_frequent_brand,
    -- Winback priority score
    CASE
        WHEN customer_lifetime_value >= 5000 AND days_since_last_purchase BETWEEN 90 AND 180 THEN 100
        WHEN customer_lifetime_value >= 2000 AND days_since_last_purchase BETWEEN 90 AND 270 THEN 80
        WHEN net_spent_lifetime >= 1000 AND days_since_last_purchase BETWEEN 180 AND 365 THEN 60
        WHEN total_transactions >= 10 AND days_since_last_purchase BETWEEN 180 AND 365 THEN 50
        ELSE 30
    END AS winback_priority_score,
    -- Recommended offer
    CASE
        WHEN days_since_last_purchase <= 120 THEN '15% discount + free shipping'
        WHEN days_since_last_purchase <= 180 THEN '25% discount on favorite category'
        WHEN days_since_last_purchase <= 270 THEN '30% discount + exclusive access'
        ELSE '40% winback offer + gift'
    END AS recommended_offer,
    -- Channel recommendation
    CASE
        WHEN customer_lifetime_value >= 3000 THEN 'Personal phone call'
        WHEN total_transactions >= 15 THEN 'Personalized email series'
        ELSE 'Standard email campaign'
    END AS outreach_channel
FROM lakehouse_gold.customer_360
WHERE is_churned = true
    AND customer_lifetime_value >= 500
    AND days_since_last_purchase BETWEEN 90 AND 365
ORDER BY customer_lifetime_value DESC, days_since_last_purchase
LIMIT 1000;

-- =============================================================================
-- QUERY 14: Revenue Attribution by Channel & Touchpoint
-- =============================================================================
-- Business Question: Which channels drive the most revenue?
-- =============================================================================

SELECT
    c.preferred_channel,
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    SUM(c.net_spent_lifetime) AS total_revenue,
    AVG(c.customer_lifetime_value) AS avg_clv,
    AVG(c.total_transactions) AS avg_transactions,
    AVG(c.avg_transaction_value) AS avg_order_value,
    -- Channel performance
    SUM(c.net_spent_lifetime) / NULLIF(COUNT(DISTINCT c.customer_id), 0) AS revenue_per_customer,
    -- Retention metrics
    AVG(c.engagement_score) AS avg_engagement,
    SUM(CASE WHEN c.churn_risk IN ('High Risk', 'Medium Risk') THEN 1 ELSE 0 END) AS at_risk_count,
    CAST(SUM(CASE WHEN c.churn_risk IN ('High Risk', 'Medium Risk') THEN 1 ELSE 0 END) AS DOUBLE) /
        NULLIF(COUNT(DISTINCT c.customer_id), 0) * 100 AS churn_risk_pct,
    -- Channel effectiveness score
    (SUM(c.net_spent_lifetime) * AVG(c.engagement_score) / 100) /
        NULLIF(COUNT(DISTINCT c.customer_id), 0) AS channel_effectiveness_score
FROM lakehouse_gold.customer_360 c
WHERE c.preferred_channel IS NOT NULL
GROUP BY c.preferred_channel, c.customer_segment
ORDER BY total_revenue DESC;

-- =============================================================================
-- QUERY 15: Price Sensitivity & Discount Impact Analysis
-- =============================================================================
-- Business Question: How do discounts impact sales and profitability?
-- =============================================================================

WITH discount_buckets AS (
    SELECT
        f.transaction_id,
        f.product_sk,
        f.customer_sk,
        f.net_amount,
        f.discount_amount,
        f.profit,
        f.profit_margin,
        CASE
            WHEN f.discount_amount = 0 THEN 'No Discount'
            WHEN (f.discount_amount / NULLIF(f.total_amount, 0)) <= 0.05 THEN '1-5%'
            WHEN (f.discount_amount / NULLIF(f.total_amount, 0)) <= 0.10 THEN '6-10%'
            WHEN (f.discount_amount / NULLIF(f.total_amount, 0)) <= 0.20 THEN '11-20%'
            WHEN (f.discount_amount / NULLIF(f.total_amount, 0)) <= 0.30 THEN '21-30%'
            ELSE '30%+'
        END AS discount_bucket,
        p.category,
        c.customer_segment
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    INNER JOIN lakehouse_gold.dim_customer c ON f.customer_sk = c.customer_sk
    WHERE f.transaction_date >= DATE_ADD('month', -6, CURRENT_DATE)
)
SELECT
    discount_bucket,
    category,
    customer_segment,
    COUNT(*) AS transaction_count,
    SUM(net_amount) AS total_revenue,
    SUM(discount_amount) AS total_discounts_given,
    SUM(profit) AS total_profit,
    AVG(profit_margin) AS avg_profit_margin,
    AVG(net_amount) AS avg_transaction_value,
    -- Efficiency metrics
    SUM(profit) / NULLIF(SUM(discount_amount), 0) AS profit_per_discount_dollar,
    -- Recommendations
    CASE
        WHEN AVG(profit_margin) < 10 THEN 'Reduce discount depth'
        WHEN AVG(profit_margin) > 30 AND COUNT(*) < 100 THEN 'Increase discount to drive volume'
        ELSE 'Current discount strategy effective'
    END AS recommendation
FROM discount_buckets
GROUP BY discount_bucket, category, customer_segment
ORDER BY discount_bucket, total_revenue DESC;

-- =============================================================================
-- QUERY 16: Market Basket Analysis - Advanced
-- =============================================================================
-- Business Question: What are the strongest product associations?
-- =============================================================================

WITH transaction_products AS (
    SELECT
        f.transaction_id,
        f.customer_sk,
        f.product_sk,
        p.category,
        p.brand,
        f.net_amount
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    WHERE f.transaction_date >= DATE_ADD('month', -3, CURRENT_DATE)
),
product_associations AS (
    SELECT
        tp1.product_sk AS product_a,
        tp2.product_sk AS product_b,
        COUNT(DISTINCT tp1.transaction_id) AS co_occurrence_count,
        AVG(tp1.net_amount + tp2.net_amount) AS avg_basket_value
    FROM transaction_products tp1
    INNER JOIN transaction_products tp2
        ON tp1.transaction_id = tp2.transaction_id
        AND tp1.product_sk < tp2.product_sk
    GROUP BY tp1.product_sk, tp2.product_sk
),
product_counts AS (
    SELECT
        product_sk,
        COUNT(DISTINCT transaction_id) AS product_transaction_count
    FROM transaction_products
    GROUP BY product_sk
),
association_rules AS (
    SELECT
        pa.product_a,
        pa.product_b,
        pa1.product_name AS product_a_name,
        pa2.product_name AS product_b_name,
        pa.co_occurrence_count,
        pc1.product_transaction_count AS product_a_count,
        pc2.product_transaction_count AS product_b_count,
        -- Calculate lift
        CAST(pa.co_occurrence_count AS DOUBLE) /
            (CAST(pc1.product_transaction_count AS DOUBLE) *
             CAST(pc2.product_transaction_count AS DOUBLE) /
             POWER((SELECT COUNT(DISTINCT transaction_id) FROM transaction_products), 2)) AS lift,
        pa.avg_basket_value
    FROM product_associations pa
    INNER JOIN product_counts pc1 ON pa.product_a = pc1.product_sk
    INNER JOIN product_counts pc2 ON pa.product_b = pc2.product_sk
    INNER JOIN lakehouse_gold.product_performance pa1 ON pa.product_a = pa1.product_sk
    INNER JOIN lakehouse_gold.product_performance pa2 ON pa.product_b = pa2.product_sk
    WHERE pa.co_occurrence_count >= 5
)
SELECT
    product_a_name,
    product_b_name,
    co_occurrence_count,
    product_a_count,
    product_b_count,
    ROUND(lift, 2) AS lift,
    avg_basket_value,
    -- Interpretation
    CASE
        WHEN lift > 3 THEN 'Very Strong Association'
        WHEN lift > 2 THEN 'Strong Association'
        WHEN lift > 1.5 THEN 'Moderate Association'
        ELSE 'Weak Association'
    END AS association_strength
FROM association_rules
WHERE lift > 1.5
ORDER BY lift DESC
LIMIT 100;

-- =============================================================================
-- QUERY 17: Customer Lifetime Value Prediction
-- =============================================================================
-- Business Question: What will be the future value of our customers?
-- =============================================================================

WITH historical_spending AS (
    SELECT
        c.customer_sk,
        c.customer_id,
        c.customer_name,
        c.registration_date,
        c.days_since_registration,
        c.total_transactions,
        c.net_spent_lifetime,
        c.avg_transaction_value,
        -- Calculate monthly spend rate
        CASE
            WHEN c.days_since_registration > 0
            THEN c.net_spent_lifetime / (c.days_since_registration / 30.0)
            ELSE 0
        END AS monthly_spend_rate,
        -- Transaction frequency (transactions per month)
        CASE
            WHEN c.days_since_registration > 0
            THEN c.total_transactions * 30.0 / c.days_since_registration
            ELSE 0
        END AS monthly_transaction_frequency,
        c.engagement_score,
        c.churn_risk
    FROM lakehouse_gold.customer_360 c
    WHERE c.is_churned = false
        AND c.days_since_registration >= 30
),
predicted_ltv AS (
    SELECT
        hs.*,
        -- Predict 12-month LTV
        hs.monthly_spend_rate * 12 AS predicted_12m_ltv,
        -- Predict 24-month LTV with decay factor
        hs.monthly_spend_rate * 24 *
            (CASE
                WHEN hs.churn_risk = 'Active' THEN 0.95
                WHEN hs.churn_risk = 'Low Risk' THEN 0.85
                WHEN hs.churn_risk = 'Medium Risk' THEN 0.65
                ELSE 0.40
            END) AS predicted_24m_ltv,
        -- Confidence score
        LEAST(100,
            (hs.engagement_score * 0.4) +
            (LEAST(hs.total_transactions * 5, 50) * 0.3) +
            (CASE WHEN hs.days_since_registration >= 90 THEN 30 ELSE hs.days_since_registration / 3 END * 0.3)
        ) AS prediction_confidence
    FROM historical_spending hs
)
SELECT
    customer_id,
    customer_name,
    days_since_registration,
    total_transactions,
    net_spent_lifetime,
    monthly_spend_rate,
    monthly_transaction_frequency,
    engagement_score,
    churn_risk,
    ROUND(predicted_12m_ltv, 2) AS predicted_12m_ltv,
    ROUND(predicted_24m_ltv, 2) AS predicted_24m_ltv,
    ROUND(prediction_confidence, 1) AS prediction_confidence,
    -- Investment priority
    CASE
        WHEN predicted_24m_ltv >= 10000 AND prediction_confidence >= 70 THEN 'High Priority'
        WHEN predicted_24m_ltv >= 5000 AND prediction_confidence >= 60 THEN 'Medium Priority'
        WHEN predicted_24m_ltv >= 2000 THEN 'Low Priority'
        ELSE 'Monitor'
    END AS investment_priority
FROM predicted_ltv
ORDER BY predicted_24m_ltv DESC;

-- =============================================================================
-- QUERY 18: Product Launch Performance Tracking
-- =============================================================================
-- Business Question: How are new products performing after launch?
-- =============================================================================

WITH new_products AS (
    SELECT
        pp.product_sk,
        pp.product_name,
        pp.category,
        pp.brand,
        pp.launch_date,
        pp.days_since_launch,
        pp.net_revenue,
        pp.total_quantity_sold,
        pp.unique_customers,
        pp.revenue_rank,
        -- Launch performance metrics
        CASE
            WHEN pp.days_since_launch <= 30 THEN '0-30 days'
            WHEN pp.days_since_launch <= 90 THEN '31-90 days'
            WHEN pp.days_since_launch <= 180 THEN '91-180 days'
            ELSE '180+ days'
        END AS launch_phase
    FROM lakehouse_gold.product_performance pp
    WHERE pp.launch_date >= DATE_ADD('year', -1, CURRENT_DATE)
),
phase_benchmarks AS (
    SELECT
        launch_phase,
        AVG(net_revenue) AS avg_phase_revenue,
        AVG(total_quantity_sold) AS avg_phase_volume,
        AVG(unique_customers) AS avg_phase_customers
    FROM new_products
    GROUP BY launch_phase
)
SELECT
    np.product_name,
    np.category,
    np.brand,
    np.launch_date,
    np.days_since_launch,
    np.launch_phase,
    np.net_revenue,
    np.total_quantity_sold,
    np.unique_customers,
    np.revenue_rank,
    pb.avg_phase_revenue,
    -- Performance vs benchmark
    (np.net_revenue - pb.avg_phase_revenue) / NULLIF(pb.avg_phase_revenue, 0) * 100 AS revenue_vs_benchmark_pct,
    -- Launch success indicator
    CASE
        WHEN np.revenue_rank <= 100 THEN 'Blockbuster Launch'
        WHEN np.net_revenue > pb.avg_phase_revenue * 1.5 THEN 'Strong Launch'
        WHEN np.net_revenue > pb.avg_phase_revenue THEN 'Moderate Launch'
        ELSE 'Weak Launch'
    END AS launch_performance
FROM new_products np
INNER JOIN phase_benchmarks pb ON np.launch_phase = pb.launch_phase
ORDER BY np.launch_date DESC, np.net_revenue DESC;

-- =============================================================================
-- QUERY 19: Customer Engagement Trends
-- =============================================================================
-- Business Question: How is customer engagement evolving?
-- =============================================================================

WITH monthly_engagement AS (
    SELECT
        DATE_TRUNC('month', f.transaction_date) AS month,
        COUNT(DISTINCT f.customer_sk) AS active_customers,
        AVG(c.engagement_score) AS avg_engagement_score,
        AVG(f.net_amount) AS avg_transaction_value,
        SUM(f.net_amount) AS monthly_revenue,
        COUNT(f.transaction_id) AS total_transactions
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.customer_360 c ON f.customer_sk = c.customer_sk
    WHERE f.transaction_date >= DATE_ADD('year', -2, CURRENT_DATE)
    GROUP BY DATE_TRUNC('month', f.transaction_date)
),
engagement_trends AS (
    SELECT
        me.*,
        LAG(me.active_customers, 1) OVER (ORDER BY me.month) AS prev_month_customers,
        LAG(me.avg_engagement_score, 1) OVER (ORDER BY me.month) AS prev_month_engagement,
        LAG(me.monthly_revenue, 1) OVER (ORDER BY me.month) AS prev_month_revenue
    FROM monthly_engagement me
)
SELECT
    month,
    active_customers,
    avg_engagement_score,
    avg_transaction_value,
    monthly_revenue,
    total_transactions,
    -- Month-over-month changes
    active_customers - prev_month_customers AS customer_change,
    CASE
        WHEN prev_month_customers > 0
        THEN ((active_customers - prev_month_customers) * 100.0 / prev_month_customers)
        ELSE 0
    END AS customer_growth_pct,
    avg_engagement_score - prev_month_engagement AS engagement_change,
    CASE
        WHEN prev_month_revenue > 0
        THEN ((monthly_revenue - prev_month_revenue) * 100.0 / prev_month_revenue)
        ELSE 0
    END AS revenue_growth_pct,
    -- Trend indicator
    CASE
        WHEN avg_engagement_score > prev_month_engagement AND active_customers > prev_month_customers THEN 'Growing & Engaging'
        WHEN avg_engagement_score > prev_month_engagement AND active_customers <= prev_month_customers THEN 'Higher Quality'
        WHEN avg_engagement_score <= prev_month_engagement AND active_customers > prev_month_customers THEN 'Growing but Disengaging'
        ELSE 'Declining'
    END AS trend_status
FROM engagement_trends
ORDER BY month DESC;

-- =============================================================================
-- QUERY 20: Premium Customer Identification & Nurturing
-- =============================================================================
-- Business Question: Who should we target for premium programs?
-- =============================================================================

SELECT
    customer_id,
    customer_name,
    email,
    customer_segment,
    loyalty_tier,
    net_spent_lifetime,
    customer_lifetime_value,
    total_transactions,
    avg_transaction_value,
    engagement_score,
    rfm_segment,
    most_frequent_category,
    -- Premium eligibility score
    LEAST(100,
        (CASE
            WHEN net_spent_lifetime >= 10000 THEN 40
            WHEN net_spent_lifetime >= 5000 THEN 30
            WHEN net_spent_lifetime >= 2000 THEN 20
            ELSE 10
        END) +
        (CASE
            WHEN total_transactions >= 50 THEN 30
            WHEN total_transactions >= 20 THEN 20
            WHEN total_transactions >= 10 THEN 10
            ELSE 5
        END) +
        (engagement_score * 0.3)
    ) AS premium_eligibility_score,
    -- Benefits recommendation
    CASE
        WHEN customer_lifetime_value >= 15000 THEN 'Platinum: Concierge service, 25% discount, free expedited shipping'
        WHEN customer_lifetime_value >= 7500 THEN 'Gold: Priority support, 15% discount, free shipping'
        WHEN customer_lifetime_value >= 3000 THEN 'Silver: 10% discount, early access to sales'
        ELSE 'Bronze: 5% discount, special promotions'
    END AS recommended_tier_benefits
FROM lakehouse_gold.customer_360
WHERE is_churned = false
    AND engagement_score >= 50
    AND (net_spent_lifetime >= 2000 OR total_transactions >= 10)
ORDER BY customer_lifetime_value DESC
LIMIT 500;

-- =============================================================================
-- QUERY 21: Territory & Sales Rep Performance
-- =============================================================================
-- Business Question: Which geographic territories are most profitable?
-- =============================================================================

WITH territory_performance AS (
    SELECT
        c.country,
        c.state,
        COUNT(DISTINCT c.customer_id) AS total_customers,
        SUM(c.net_spent_lifetime) AS total_revenue,
        SUM(CASE WHEN f.profit IS NOT NULL THEN f.profit ELSE 0 END) AS total_profit,
        AVG(c.customer_lifetime_value) AS avg_clv,
        AVG(c.engagement_score) AS avg_engagement,
        SUM(c.transactions_last_year) AS transactions_last_year,
        COUNT(DISTINCT c.most_frequent_category) AS category_diversity
    FROM lakehouse_gold.customer_360 c
    LEFT JOIN lakehouse_gold.fact_transactions f ON c.customer_sk = f.customer_sk
    WHERE c.country IS NOT NULL AND c.state IS NOT NULL
    GROUP BY c.country, c.state
),
territory_ranks AS (
    SELECT
        tp.*,
        ROW_NUMBER() OVER (PARTITION BY tp.country ORDER BY tp.total_revenue DESC) AS state_rank,
        total_revenue / NULLIF(total_customers, 0) AS revenue_per_customer,
        total_profit / NULLIF(total_revenue, 0) * 100 AS profit_margin_pct
    FROM territory_performance tp
)
SELECT
    country,
    state,
    total_customers,
    total_revenue,
    total_profit,
    revenue_per_customer,
    profit_margin_pct,
    avg_clv,
    avg_engagement,
    transactions_last_year,
    state_rank,
    -- Territory classification
    CASE
        WHEN state_rank <= 3 AND profit_margin_pct > 25 THEN 'Premium Territory'
        WHEN total_revenue > 100000 THEN 'High-Value Territory'
        WHEN avg_engagement < 40 THEN 'Needs Attention'
        ELSE 'Standard Territory'
    END AS territory_class,
    -- Growth opportunity
    CASE
        WHEN total_customers < 100 AND revenue_per_customer > 500 THEN 'High potential for expansion'
        WHEN avg_engagement < 50 THEN 'Focus on retention'
        ELSE 'Maintain and grow'
    END AS growth_opportunity
FROM territory_ranks
ORDER BY country, total_revenue DESC;

-- =============================================================================
-- QUERY 22: What-If Scenario Analysis
-- =============================================================================
-- Business Question: What if we change pricing or discount strategies?
-- =============================================================================

WITH current_metrics AS (
    SELECT
        category,
        SUM(net_revenue) AS current_revenue,
        SUM(profit) AS current_profit,
        AVG(profit_margin) AS current_margin,
        SUM(quantity) AS current_volume
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    WHERE f.transaction_date >= DATE_ADD('month', -3, CURRENT_DATE)
    GROUP BY category
),
scenarios AS (
    SELECT
        cm.category,
        cm.current_revenue,
        cm.current_profit,
        cm.current_margin,
        cm.current_volume,
        -- Scenario 1: 10% price increase
        cm.current_revenue * 1.10 * 0.90 AS scenario1_revenue,  -- Assume 10% volume drop
        (cm.current_revenue * 1.10 * 0.90) - (cm.current_revenue - cm.current_profit) AS scenario1_profit,
        -- Scenario 2: 15% discount to drive volume
        cm.current_revenue * 0.85 * 1.30 AS scenario2_revenue,  -- Assume 30% volume increase
        (cm.current_revenue * 0.85 * 1.30) - (cm.current_revenue - cm.current_profit) * 1.30 AS scenario2_profit,
        -- Scenario 3: Premium positioning (20% price increase, 20% volume drop)
        cm.current_revenue * 1.20 * 0.80 AS scenario3_revenue,
        (cm.current_revenue * 1.20 * 0.80) - (cm.current_revenue - cm.current_profit) * 0.80 AS scenario3_profit
    FROM current_metrics cm
)
SELECT
    category,
    -- Current state
    ROUND(current_revenue, 2) AS current_revenue,
    ROUND(current_profit, 2) AS current_profit,
    ROUND(current_margin, 2) AS current_margin_pct,
    -- Scenario 1: Price increase
    ROUND(scenario1_revenue, 2) AS price_increase_revenue,
    ROUND(scenario1_profit, 2) AS price_increase_profit,
    ROUND((scenario1_profit - current_profit) / NULLIF(current_profit, 0) * 100, 2) AS s1_profit_change_pct,
    -- Scenario 2: Discount strategy
    ROUND(scenario2_revenue, 2) AS discount_strategy_revenue,
    ROUND(scenario2_profit, 2) AS discount_strategy_profit,
    ROUND((scenario2_profit - current_profit) / NULLIF(current_profit, 0) * 100, 2) AS s2_profit_change_pct,
    -- Scenario 3: Premium positioning
    ROUND(scenario3_revenue, 2) AS premium_position_revenue,
    ROUND(scenario3_profit, 2) AS premium_position_profit,
    ROUND((scenario3_profit - current_profit) / NULLIF(current_profit, 0) * 100, 2) AS s3_profit_change_pct,
    -- Best scenario
    CASE
        WHEN scenario1_profit > scenario2_profit AND scenario1_profit > scenario3_profit THEN 'Price Increase'
        WHEN scenario2_profit > scenario3_profit THEN 'Discount Strategy'
        ELSE 'Premium Positioning'
    END AS recommended_strategy
FROM scenarios
ORDER BY current_revenue DESC;

-- =============================================================================
-- QUERY 23: Customer Acquisition Cost vs Lifetime Value
-- =============================================================================
-- Business Question: Are we acquiring customers profitably?
-- =============================================================================

WITH customer_cohorts AS (
    SELECT
        DATE_TRUNC('month', registration_date) AS cohort_month,
        customer_sk,
        customer_id,
        net_spent_lifetime,
        customer_lifetime_value,
        total_transactions,
        days_since_registration
    FROM lakehouse_gold.customer_360
    WHERE registration_date IS NOT NULL
        AND registration_date >= DATE_ADD('year', -2, CURRENT_DATE)
),
cohort_metrics AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size,
        SUM(net_spent_lifetime) AS total_cohort_revenue,
        AVG(customer_lifetime_value) AS avg_predicted_clv,
        AVG(net_spent_lifetime) AS avg_actual_revenue,
        AVG(total_transactions) AS avg_transactions,
        AVG(days_since_registration) AS avg_tenure_days,
        -- Assume CAC of $50 per customer (would come from marketing data)
        COUNT(DISTINCT customer_id) * 50 AS estimated_acquisition_cost
    FROM customer_cohorts
    GROUP BY cohort_month
)
SELECT
    cohort_month,
    cohort_size,
    total_cohort_revenue,
    avg_predicted_clv,
    avg_actual_revenue,
    avg_transactions,
    avg_tenure_days,
    estimated_acquisition_cost,
    -- ROI calculations
    (total_cohort_revenue - estimated_acquisition_cost) AS net_profit,
    (total_cohort_revenue - estimated_acquisition_cost) / NULLIF(estimated_acquisition_cost, 0) * 100 AS roi_pct,
    avg_actual_revenue / 50 AS ltv_to_cac_ratio,
    -- Payback period (days to recover CAC)
    CASE
        WHEN avg_actual_revenue > 50
        THEN CAST((50 / (avg_actual_revenue / avg_tenure_days)) AS INTEGER)
        ELSE NULL
    END AS payback_period_days,
    -- Cohort health
    CASE
        WHEN (avg_actual_revenue / 50) >= 3 THEN 'Excellent'
        WHEN (avg_actual_revenue / 50) >= 2 THEN 'Good'
        WHEN (avg_actual_revenue / 50) >= 1 THEN 'Break-even'
        ELSE 'Unprofitable'
    END AS cohort_health
FROM cohort_metrics
ORDER BY cohort_month DESC;

-- =============================================================================
-- QUERY 24: Inventory Optimization Recommendations
-- =============================================================================
-- Business Question: Which products should we stock more/less of?
-- =============================================================================

SELECT
    pp.product_id,
    pp.product_name,
    pp.category,
    pp.brand,
    pp.inventory_classification,
    pp.quantity_last_30d,
    pp.quantity_last_90d,
    pp.revenue_last_30d,
    pp.total_profit,
    pp.avg_profit_margin,
    pp.days_since_last_sale,
    -- Velocity metrics
    pp.quantity_last_30d / 30.0 AS daily_velocity,
    pp.quantity_last_90d / 90.0 AS avg_daily_velocity,
    -- Stock recommendation
    CASE
        WHEN pp.inventory_classification = 'Fast Moving' AND pp.days_since_last_sale <= 3
            THEN pp.quantity_last_30d * 2
        WHEN pp.inventory_classification = 'Moderate Moving'
            THEN pp.quantity_last_30d * 1.5
        WHEN pp.inventory_classification = 'Slow Moving' AND pp.days_since_last_sale > 30
            THEN pp.quantity_last_30d * 0.5
        ELSE pp.quantity_last_30d
    END AS recommended_stock_level,
    -- Action items
    CASE
        WHEN pp.inventory_classification = 'Fast Moving' AND pp.days_since_last_sale <= 3 THEN 'Increase Stock - High Demand'
        WHEN pp.days_since_last_sale > 90 THEN 'Clearance Sale - Slow Moving'
        WHEN pp.avg_profit_margin < 10 THEN 'Review Pricing - Low Margin'
        WHEN pp.revenue_rank <= 100 THEN 'Maintain Stock - Top Seller'
        ELSE 'Standard Replenishment'
    END AS action_item,
    -- Priority
    CASE
        WHEN pp.revenue_rank <= 50 THEN 'Critical'
        WHEN pp.revenue_rank <= 200 THEN 'High'
        WHEN pp.revenue_rank <= 500 THEN 'Medium'
        ELSE 'Low'
    END AS priority
FROM lakehouse_gold.product_performance pp
ORDER BY pp.revenue_rank;

-- =============================================================================
-- QUERY 25: Executive Dashboard - Key Business Metrics
-- =============================================================================
-- Business Question: What are our critical business metrics at a glance?
-- =============================================================================

WITH current_period AS (
    SELECT
        SUM(net_revenue) AS current_revenue,
        SUM(gross_profit) AS current_profit,
        AVG(avg_transaction_value) AS current_aov,
        SUM(transaction_count) AS current_transactions,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM lakehouse_gold.financial_summary fs
    INNER JOIN lakehouse_gold.customer_360 c ON fs.customer_segment = c.customer_segment
    WHERE fs.date >= DATE_TRUNC('month', CURRENT_DATE)
),
previous_period AS (
    SELECT
        SUM(net_revenue) AS prev_revenue,
        SUM(gross_profit) AS prev_profit,
        AVG(avg_transaction_value) AS prev_aov,
        SUM(transaction_count) AS prev_transactions
    FROM lakehouse_gold.financial_summary
    WHERE date >= DATE_ADD('month', -1, DATE_TRUNC('month', CURRENT_DATE))
        AND date < DATE_TRUNC('month', CURRENT_DATE)
),
customer_metrics AS (
    SELECT
        COUNT(*) AS total_customers,
        AVG(customer_lifetime_value) AS avg_clv,
        SUM(CASE WHEN rfm_segment IN ('Champions', 'Loyal Customers') THEN 1 ELSE 0 END) AS high_value_customers,
        SUM(CASE WHEN churn_risk IN ('High Risk', 'Medium Risk') THEN 1 ELSE 0 END) AS at_risk_customers,
        AVG(engagement_score) AS avg_engagement
    FROM lakehouse_gold.customer_360
    WHERE is_churned = false
)
SELECT
    -- Revenue Metrics
    ROUND(cp.current_revenue, 2) AS mtd_revenue,
    ROUND(pp.prev_revenue, 2) AS prev_month_revenue,
    ROUND((cp.current_revenue - pp.prev_revenue) / NULLIF(pp.prev_revenue, 0) * 100, 2) AS revenue_mom_change_pct,

    -- Profitability
    ROUND(cp.current_profit, 2) AS mtd_profit,
    ROUND(cp.current_profit / NULLIF(cp.current_revenue, 0) * 100, 2) AS profit_margin_pct,

    -- Transaction Metrics
    cp.current_transactions AS mtd_transactions,
    ROUND(cp.current_aov, 2) AS avg_order_value,
    ROUND((cp.current_aov - pp.prev_aov) / NULLIF(pp.prev_aov, 0) * 100, 2) AS aov_change_pct,

    -- Customer Metrics
    cp.active_customers AS mtd_active_customers,
    cm.total_customers,
    ROUND(cm.avg_clv, 2) AS avg_customer_lifetime_value,
    cm.high_value_customers,
    ROUND(CAST(cm.high_value_customers AS DOUBLE) / cm.total_customers * 100, 2) AS high_value_customer_pct,
    cm.at_risk_customers,
    ROUND(cm.avg_engagement, 1) AS avg_engagement_score,

    -- Health Indicators
    CASE
        WHEN (cp.current_revenue - pp.prev_revenue) / NULLIF(pp.prev_revenue, 0) > 0.05 THEN '🟢 Growing'
        WHEN (cp.current_revenue - pp.prev_revenue) / NULLIF(pp.prev_revenue, 0) > -0.05 THEN '🟡 Stable'
        ELSE '🔴 Declining'
    END AS revenue_health,
    CASE
        WHEN cm.avg_engagement >= 70 THEN '🟢 High'
        WHEN cm.avg_engagement >= 50 THEN '🟡 Moderate'
        ELSE '🔴 Low'
    END AS engagement_health,

    -- Generated timestamp
    CURRENT_TIMESTAMP AS dashboard_generated_at
FROM current_period cp
CROSS JOIN previous_period pp
CROSS JOIN customer_metrics cm;

-- =============================================================================
-- End of Business Intelligence Queries
-- =============================================================================
