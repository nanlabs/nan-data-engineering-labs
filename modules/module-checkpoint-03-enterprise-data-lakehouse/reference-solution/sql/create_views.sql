-- =============================================================================
-- CREATE VIEWS - Enterprise Data Lakehouse Gold Layer Views
-- =============================================================================
-- Purpose: Create business-ready views on top of gold layer tables using
--          Athena/Presto SQL. Views implement complex business logic with
--          extensive JOINs, window functions, and aggregations.
-- Database: lakehouse_gold
-- Compatible: Amazon Athena, Presto, Trino
-- =============================================================================

-- =============================================================================
-- VIEW 1: customer_360
-- =============================================================================
-- Purpose: Unified customer profile with all dimensions including transaction
--          history, lifetime value, RFM scores, segment analysis, and behavior
-- =============================================================================

CREATE OR REPLACE VIEW lakehouse_gold.customer_360 AS
WITH customer_base AS (
    SELECT
        c.customer_sk,
        c.customer_id,
        c.customer_name,
        c.email,
        c.phone,
        c.address,
        c.city,
        c.state,
        c.country,
        c.postal_code,
        c.customer_segment,
        c.registration_date,
        c.account_status,
        c.preferred_channel,
        c.communication_preference,
        c.credit_limit,
        c.risk_score,
        c.loyalty_tier,
        c.birth_date,
        YEAR(CURRENT_DATE) - YEAR(c.birth_date) AS customer_age,
        DATE_DIFF('day', c.registration_date, CURRENT_DATE) AS days_since_registration,
        c.is_current,
        c.effective_date,
        c.end_date
    FROM lakehouse_gold.dim_customer c
    WHERE c.is_current = true
),

transaction_summary AS (
    SELECT
        f.customer_sk,
        COUNT(DISTINCT f.transaction_id) AS total_transactions,
        COUNT(DISTINCT f.product_sk) AS unique_products_purchased,
        COUNT(DISTINCT d.year) AS active_years,
        COUNT(DISTINCT d.year || '-' || d.month) AS active_months,
        SUM(f.quantity) AS total_items_purchased,
        SUM(f.total_amount) AS total_spent_lifetime,
        SUM(f.net_amount) AS net_spent_lifetime,
        SUM(f.discount_amount) AS total_discounts_received,
        SUM(f.profit) AS total_profit_generated,
        AVG(f.net_amount) AS avg_transaction_value,
        AVG(f.profit_margin) AS avg_profit_margin,
        MIN(f.transaction_date) AS first_transaction_date,
        MAX(f.transaction_date) AS last_transaction_date,
        DATE_DIFF('day', MIN(f.transaction_date), MAX(f.transaction_date)) AS customer_lifetime_days,
        DATE_DIFF('day', MAX(f.transaction_date), CURRENT_DATE) AS days_since_last_purchase
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.customer_sk
),

recent_activity AS (
    SELECT
        f.customer_sk,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -30, CURRENT_DATE) THEN f.transaction_id END) AS transactions_last_30d,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -90, CURRENT_DATE) THEN f.transaction_id END) AS transactions_last_90d,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -365, CURRENT_DATE) THEN f.transaction_id END) AS transactions_last_year,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -30, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS spent_last_30d,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -90, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS spent_last_90d,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -365, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS spent_last_year
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.customer_sk
),

rfm_scores AS (
    SELECT
        ts.customer_sk,
        -- Recency Score (1-5, 5 being most recent)
        CASE
            WHEN ts.days_since_last_purchase <= 30 THEN 5
            WHEN ts.days_since_last_purchase <= 60 THEN 4
            WHEN ts.days_since_last_purchase <= 90 THEN 3
            WHEN ts.days_since_last_purchase <= 180 THEN 2
            ELSE 1
        END AS recency_score,
        -- Frequency Score (1-5, 5 being most frequent)
        CASE
            WHEN ts.total_transactions >= 50 THEN 5
            WHEN ts.total_transactions >= 20 THEN 4
            WHEN ts.total_transactions >= 10 THEN 3
            WHEN ts.total_transactions >= 5 THEN 2
            ELSE 1
        END AS frequency_score,
        -- Monetary Score (1-5, 5 being highest spender)
        NTILE(5) OVER (ORDER BY ts.net_spent_lifetime) AS monetary_score
    FROM transaction_summary ts
),

customer_segments AS (
    SELECT
        rfm.customer_sk,
        rfm.recency_score * 100 + rfm.frequency_score * 10 + rfm.monetary_score AS rfm_combined_score,
        CASE
            WHEN rfm.recency_score >= 4 AND rfm.frequency_score >= 4 AND rfm.monetary_score >= 4 THEN 'Champions'
            WHEN rfm.recency_score >= 3 AND rfm.frequency_score >= 3 AND rfm.monetary_score >= 3 THEN 'Loyal Customers'
            WHEN rfm.recency_score >= 4 AND rfm.frequency_score <= 2 THEN 'New Customers'
            WHEN rfm.recency_score <= 2 AND rfm.frequency_score >= 4 AND rfm.monetary_score >= 4 THEN 'At Risk'
            WHEN rfm.recency_score <= 2 AND rfm.frequency_score >= 3 THEN 'Cannot Lose Them'
            WHEN rfm.recency_score <= 2 AND rfm.frequency_score <= 2 AND rfm.monetary_score <= 2 THEN 'Lost'
            WHEN rfm.recency_score >= 3 AND rfm.frequency_score <= 2 AND rfm.monetary_score <= 2 THEN 'Promising'
            WHEN rfm.recency_score >= 2 AND rfm.frequency_score >= 2 AND rfm.monetary_score >= 3 THEN 'Potential Loyalists'
            ELSE 'Needs Attention'
        END AS rfm_segment
    FROM rfm_scores rfm
),

product_preferences AS (
    SELECT
        f.customer_sk,
        ARRAY_AGG(DISTINCT p.category) AS preferred_categories,
        ARRAY_AGG(DISTINCT p.brand) AS preferred_brands,
        MODE() WITHIN GROUP (ORDER BY p.category) AS most_frequent_category,
        MODE() WITHIN GROUP (ORDER BY p.brand) AS most_frequent_brand
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    GROUP BY f.customer_sk
),

seasonal_behavior AS (
    SELECT
        f.customer_sk,
        AVG(CASE WHEN d.quarter = 1 THEN f.net_amount ELSE 0 END) AS avg_spend_q1,
        AVG(CASE WHEN d.quarter = 2 THEN f.net_amount ELSE 0 END) AS avg_spend_q2,
        AVG(CASE WHEN d.quarter = 3 THEN f.net_amount ELSE 0 END) AS avg_spend_q3,
        AVG(CASE WHEN d.quarter = 4 THEN f.net_amount ELSE 0 END) AS avg_spend_q4,
        COUNT(DISTINCT CASE WHEN d.is_weekend = true THEN f.transaction_id END) AS weekend_transactions,
        COUNT(DISTINCT CASE WHEN d.is_weekend = false THEN f.transaction_id END) AS weekday_transactions
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.customer_sk
),

lifetime_value AS (
    SELECT
        ts.customer_sk,
        -- CLV = Avg Transaction Value * Purchase Frequency * Customer Lifetime (estimated 3 years)
        CASE
            WHEN ts.customer_lifetime_days > 0
            THEN ts.avg_transaction_value *
                 (ts.total_transactions * 1.0 / (ts.customer_lifetime_days / 365.0)) * 3
            ELSE ts.avg_transaction_value * ts.total_transactions
        END AS customer_lifetime_value,
        -- Predicted next purchase date (based on average days between purchases)
        CASE
            WHEN ts.total_transactions > 1
            THEN DATE_ADD('day',
                 CAST(ts.customer_lifetime_days * 1.0 / (ts.total_transactions - 1) AS INTEGER),
                 ts.last_transaction_date)
            ELSE NULL
        END AS predicted_next_purchase_date
    FROM transaction_summary ts
),

churn_indicators AS (
    SELECT
        ts.customer_sk,
        CASE
            WHEN ts.days_since_last_purchase > 180 THEN 'High Risk'
            WHEN ts.days_since_last_purchase > 90 THEN 'Medium Risk'
            WHEN ts.days_since_last_purchase > 60 THEN 'Low Risk'
            ELSE 'Active'
        END AS churn_risk,
        CASE
            WHEN ts.days_since_last_purchase > ts.customer_lifetime_days * 0.5 THEN true
            ELSE false
        END AS is_churned,
        -- Engagement score (0-100)
        LEAST(100,
            (ra.transactions_last_90d * 10) +
            (LEAST(ra.spent_last_90d / NULLIF(ts.avg_transaction_value, 0), 10) * 10) +
            (CASE WHEN ts.days_since_last_purchase <= 30 THEN 30 ELSE 0 END)
        ) AS engagement_score
    FROM transaction_summary ts
    LEFT JOIN recent_activity ra ON ts.customer_sk = ra.customer_sk
)

-- Final SELECT combining all CTEs
SELECT
    -- Customer Identifiers
    cb.customer_sk,
    cb.customer_id,
    cb.customer_name,
    cb.email,
    cb.phone,

    -- Demographic Information
    cb.customer_age,
    cb.birth_date,
    cb.address,
    cb.city,
    cb.state,
    cb.country,
    cb.postal_code,
    cb.registration_date,
    cb.days_since_registration,

    -- Customer Status & Attributes
    cb.account_status,
    cb.customer_segment,
    cb.loyalty_tier,
    cb.preferred_channel,
    cb.communication_preference,
    cb.credit_limit,
    cb.risk_score,

    -- Transaction Summary
    COALESCE(ts.total_transactions, 0) AS total_transactions,
    COALESCE(ts.unique_products_purchased, 0) AS unique_products_purchased,
    COALESCE(ts.active_years, 0) AS active_years,
    COALESCE(ts.active_months, 0) AS active_months,
    COALESCE(ts.total_items_purchased, 0) AS total_items_purchased,
    COALESCE(ts.total_spent_lifetime, 0.0) AS total_spent_lifetime,
    COALESCE(ts.net_spent_lifetime, 0.0) AS net_spent_lifetime,
    COALESCE(ts.total_discounts_received, 0.0) AS total_discounts_received,
    COALESCE(ts.total_profit_generated, 0.0) AS total_profit_generated,
    COALESCE(ts.avg_transaction_value, 0.0) AS avg_transaction_value,
    COALESCE(ts.avg_profit_margin, 0.0) AS avg_profit_margin,
    ts.first_transaction_date,
    ts.last_transaction_date,
    ts.customer_lifetime_days,
    ts.days_since_last_purchase,

    -- Recent Activity
    COALESCE(ra.transactions_last_30d, 0) AS transactions_last_30d,
    COALESCE(ra.transactions_last_90d, 0) AS transactions_last_90d,
    COALESCE(ra.transactions_last_year, 0) AS transactions_last_year,
    COALESCE(ra.spent_last_30d, 0.0) AS spent_last_30d,
    COALESCE(ra.spent_last_90d, 0.0) AS spent_last_90d,
    COALESCE(ra.spent_last_year, 0.0) AS spent_last_year,

    -- RFM Analysis
    rfm.recency_score,
    rfm.frequency_score,
    rfm.monetary_score,
    cs.rfm_combined_score,
    cs.rfm_segment,

    -- Product Preferences
    pp.preferred_categories,
    pp.preferred_brands,
    pp.most_frequent_category,
    pp.most_frequent_brand,

    -- Seasonal Behavior
    sb.avg_spend_q1,
    sb.avg_spend_q2,
    sb.avg_spend_q3,
    sb.avg_spend_q4,
    sb.weekend_transactions,
    sb.weekday_transactions,
    CASE
        WHEN sb.weekday_transactions > 0
        THEN CAST(sb.weekend_transactions AS DOUBLE) / sb.weekday_transactions
        ELSE 0.0
    END AS weekend_to_weekday_ratio,

    -- Lifetime Value & Predictions
    COALESCE(ltv.customer_lifetime_value, 0.0) AS customer_lifetime_value,
    ltv.predicted_next_purchase_date,
    DATE_DIFF('day', CURRENT_DATE, ltv.predicted_next_purchase_date) AS days_until_predicted_purchase,

    -- Churn Analysis
    ci.churn_risk,
    ci.is_churned,
    ci.engagement_score,

    -- Metadata
    cb.effective_date,
    cb.end_date,
    cb.is_current,
    CURRENT_TIMESTAMP AS view_generated_at

FROM customer_base cb
LEFT JOIN transaction_summary ts ON cb.customer_sk = ts.customer_sk
LEFT JOIN recent_activity ra ON cb.customer_sk = ra.customer_sk
LEFT JOIN rfm_scores rfm ON cb.customer_sk = rfm.customer_sk
LEFT JOIN customer_segments cs ON cb.customer_sk = cs.customer_sk
LEFT JOIN product_preferences pp ON cb.customer_sk = pp.customer_sk
LEFT JOIN seasonal_behavior sb ON cb.customer_sk = sb.customer_sk
LEFT JOIN lifetime_value ltv ON cb.customer_sk = ltv.customer_sk
LEFT JOIN churn_indicators ci ON cb.customer_sk = ci.customer_sk;

-- =============================================================================
-- VIEW 2: product_performance
-- =============================================================================
-- Purpose: Comprehensive product performance metrics including sales, rankings,
--          trends, inventory velocity, and profitability analysis
-- =============================================================================

CREATE OR REPLACE VIEW lakehouse_gold.product_performance AS
WITH product_base AS (
    SELECT
        p.product_sk,
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.brand,
        p.unit_price,
        p.cost,
        p.product_margin,
        p.status,
        p.launch_date,
        p.discontinue_date,
        DATE_DIFF('day', p.launch_date, CURRENT_DATE) AS days_since_launch
    FROM lakehouse_gold.dim_product p
),

sales_metrics AS (
    SELECT
        f.product_sk,
        COUNT(DISTINCT f.transaction_id) AS total_transactions,
        COUNT(DISTINCT f.customer_sk) AS unique_customers,
        SUM(f.quantity) AS total_quantity_sold,
        SUM(f.total_amount) AS total_revenue,
        SUM(f.net_amount) AS net_revenue,
        SUM(f.discount_amount) AS total_discounts_given,
        SUM(f.profit) AS total_profit,
        AVG(f.profit_margin) AS avg_profit_margin,
        AVG(f.unit_price) AS avg_selling_price,
        AVG(f.quantity) AS avg_quantity_per_transaction,
        MIN(f.transaction_date) AS first_sale_date,
        MAX(f.transaction_date) AS last_sale_date,
        DATE_DIFF('day', MIN(f.transaction_date), MAX(f.transaction_date)) AS sales_lifetime_days,
        DATE_DIFF('day', MAX(f.transaction_date), CURRENT_DATE) AS days_since_last_sale
    FROM lakehouse_gold.fact_transactions f
    GROUP BY f.product_sk
),

recent_trends AS (
    SELECT
        f.product_sk,
        -- Last 30 days
        SUM(CASE WHEN d.date >= DATE_ADD('day', -30, CURRENT_DATE) THEN f.quantity ELSE 0 END) AS quantity_last_30d,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -30, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS revenue_last_30d,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -30, CURRENT_DATE) THEN f.customer_sk END) AS customers_last_30d,
        -- Last 90 days
        SUM(CASE WHEN d.date >= DATE_ADD('day', -90, CURRENT_DATE) THEN f.quantity ELSE 0 END) AS quantity_last_90d,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -90, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS revenue_last_90d,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -90, CURRENT_DATE) THEN f.customer_sk END) AS customers_last_90d,
        -- Last 365 days
        SUM(CASE WHEN d.date >= DATE_ADD('day', -365, CURRENT_DATE) THEN f.quantity ELSE 0 END) AS quantity_last_year,
        SUM(CASE WHEN d.date >= DATE_ADD('day', -365, CURRENT_DATE) THEN f.net_amount ELSE 0 END) AS revenue_last_year,
        COUNT(DISTINCT CASE WHEN d.date >= DATE_ADD('day', -365, CURRENT_DATE) THEN f.customer_sk END) AS customers_last_year
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.product_sk
),

rankings AS (
    SELECT
        sm.product_sk,
        -- Overall rankings
        ROW_NUMBER() OVER (ORDER BY sm.net_revenue DESC) AS revenue_rank,
        ROW_NUMBER() OVER (ORDER BY sm.total_quantity_sold DESC) AS volume_rank,
        ROW_NUMBER() OVER (ORDER BY sm.total_profit DESC) AS profit_rank,
        ROW_NUMBER() OVER (ORDER BY sm.unique_customers DESC) AS customer_reach_rank,
        -- Category rankings
        ROW_NUMBER() OVER (PARTITION BY pb.category ORDER BY sm.net_revenue DESC) AS category_revenue_rank,
        ROW_NUMBER() OVER (PARTITION BY pb.category ORDER BY sm.total_quantity_sold DESC) AS category_volume_rank,
        -- Brand rankings
        ROW_NUMBER() OVER (PARTITION BY pb.brand ORDER BY sm.net_revenue DESC) AS brand_revenue_rank
    FROM sales_metrics sm
    INNER JOIN product_base pb ON sm.product_sk = pb.product_sk
),

growth_metrics AS (
    SELECT
        f.product_sk,
        -- Month-over-month growth
        SUM(CASE WHEN d.year_month = FORMAT_DATETIME(DATE_ADD('month', -1, CURRENT_DATE), 'yyyy-MM')
            THEN f.net_amount ELSE 0 END) AS revenue_prev_month,
        SUM(CASE WHEN d.year_month = FORMAT_DATETIME(CURRENT_DATE, 'yyyy-MM')
            THEN f.net_amount ELSE 0 END) AS revenue_current_month,
        -- Quarter-over-quarter growth
        SUM(CASE WHEN d.year = YEAR(DATE_ADD('month', -3, CURRENT_DATE))
            AND d.quarter = QUARTER(DATE_ADD('month', -3, CURRENT_DATE))
            THEN f.net_amount ELSE 0 END) AS revenue_prev_quarter,
        SUM(CASE WHEN d.year = YEAR(CURRENT_DATE) AND d.quarter = QUARTER(CURRENT_DATE)
            THEN f.net_amount ELSE 0 END) AS revenue_current_quarter,
        -- Year-over-year growth
        SUM(CASE WHEN d.year = YEAR(DATE_ADD('year', -1, CURRENT_DATE))
            THEN f.net_amount ELSE 0 END) AS revenue_prev_year,
        SUM(CASE WHEN d.year = YEAR(CURRENT_DATE)
            THEN f.net_amount ELSE 0 END) AS revenue_current_year
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.product_sk
),

seasonal_patterns AS (
    SELECT
        f.product_sk,
        AVG(CASE WHEN d.quarter = 1 THEN f.net_amount ELSE NULL END) AS avg_revenue_q1,
        AVG(CASE WHEN d.quarter = 2 THEN f.net_amount ELSE NULL END) AS avg_revenue_q2,
        AVG(CASE WHEN d.quarter = 3 THEN f.net_amount ELSE NULL END) AS avg_revenue_q3,
        AVG(CASE WHEN d.quarter = 4 THEN f.net_amount ELSE NULL END) AS avg_revenue_q4,
        STDDEV(f.net_amount) AS revenue_volatility,
        MAX(f.net_amount) - MIN(f.net_amount) AS revenue_range
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    GROUP BY f.product_sk
)

-- Final SELECT
SELECT
    -- Product Identifiers & Attributes
    pb.product_sk,
    pb.product_id,
    pb.product_name,
    pb.category,
    pb.subcategory,
    pb.brand,
    pb.status,
    pb.launch_date,
    pb.discontinue_date,
    pb.days_since_launch,

    -- Pricing & Margin
    pb.unit_price,
    pb.cost,
    pb.product_margin,

    -- Sales Metrics
    COALESCE(sm.total_transactions, 0) AS total_transactions,
    COALESCE(sm.unique_customers, 0) AS unique_customers,
    COALESCE(sm.total_quantity_sold, 0) AS total_quantity_sold,
    COALESCE(sm.total_revenue, 0.0) AS total_revenue,
    COALESCE(sm.net_revenue, 0.0) AS net_revenue,
    COALESCE(sm.total_discounts_given, 0.0) AS total_discounts_given,
    COALESCE(sm.total_profit, 0.0) AS total_profit,
    COALESCE(sm.avg_profit_margin, 0.0) AS avg_profit_margin,
    COALESCE(sm.avg_selling_price, 0.0) AS avg_selling_price,
    COALESCE(sm.avg_quantity_per_transaction, 0.0) AS avg_quantity_per_transaction,
    sm.first_sale_date,
    sm.last_sale_date,
    sm.sales_lifetime_days,
    sm.days_since_last_sale,

    -- Velocity Metrics
    CASE
        WHEN sm.sales_lifetime_days > 0
        THEN CAST(sm.total_quantity_sold AS DOUBLE) / (sm.sales_lifetime_days / 30.0)
        ELSE 0.0
    END AS avg_monthly_velocity,

    -- Recent Trends
    rt.quantity_last_30d,
    rt.revenue_last_30d,
    rt.customers_last_30d,
    rt.quantity_last_90d,
    rt.revenue_last_90d,
    rt.customers_last_90d,
    rt.quantity_last_year,
    rt.revenue_last_year,
    rt.customers_last_year,

    -- Rankings
    r.revenue_rank,
    r.volume_rank,
    r.profit_rank,
    r.customer_reach_rank,
    r.category_revenue_rank,
    r.category_volume_rank,
    r.brand_revenue_rank,

    -- Growth Rates
    CASE
        WHEN gm.revenue_prev_month > 0
        THEN ((gm.revenue_current_month - gm.revenue_prev_month) / gm.revenue_prev_month) * 100
        ELSE 0.0
    END AS mom_growth_rate,
    CASE
        WHEN gm.revenue_prev_quarter > 0
        THEN ((gm.revenue_current_quarter - gm.revenue_prev_quarter) / gm.revenue_prev_quarter) * 100
        ELSE 0.0
    END AS qoq_growth_rate,
    CASE
        WHEN gm.revenue_prev_year > 0
        THEN ((gm.revenue_current_year - gm.revenue_prev_year) / gm.revenue_prev_year) * 100
        ELSE 0.0
    END AS yoy_growth_rate,

    -- Seasonal Patterns
    sp.avg_revenue_q1,
    sp.avg_revenue_q2,
    sp.avg_revenue_q3,
    sp.avg_revenue_q4,
    sp.revenue_volatility,
    sp.revenue_range,

    -- Performance Indicators
    CASE
        WHEN sm.days_since_last_sale > 90 THEN 'Slow Moving'
        WHEN rt.quantity_last_30d >= 100 THEN 'Fast Moving'
        WHEN rt.quantity_last_30d >= 50 THEN 'Moderate Moving'
        ELSE 'Slow Moving'
    END AS inventory_classification,

    CASE
        WHEN r.revenue_rank <= 100 THEN 'Top Performer'
        WHEN r.revenue_rank <= 500 THEN 'Good Performer'
        WHEN sm.days_since_last_sale > 180 THEN 'Underperformer'
        ELSE 'Average Performer'
    END AS performance_category,

    -- Metadata
    CURRENT_TIMESTAMP AS view_generated_at

FROM product_base pb
LEFT JOIN sales_metrics sm ON pb.product_sk = sm.product_sk
LEFT JOIN recent_trends rt ON pb.product_sk = rt.product_sk
LEFT JOIN rankings r ON pb.product_sk = r.product_sk
LEFT JOIN growth_metrics gm ON pb.product_sk = gm.product_sk
LEFT JOIN seasonal_patterns sp ON pb.product_sk = sp.product_sk;

-- =============================================================================
-- VIEW 3: financial_summary
-- =============================================================================
-- Purpose: Comprehensive financial metrics with revenue, profit, margins
--          analyzed by multiple dimensions (time, geography, product, customer)
-- =============================================================================

CREATE OR REPLACE VIEW lakehouse_gold.financial_summary AS
WITH daily_financials AS (
    SELECT
        d.date,
        d.year,
        d.quarter,
        d.month,
        d.week_of_year,
        d.day_of_week,
        d.year_month,
        d.is_weekend,
        d.is_holiday,
        -- Product dimensions
        p.category,
        p.subcategory,
        p.brand,
        -- Customer dimensions
        c.customer_segment,
        c.state,
        c.country,
        -- Financial metrics
        COUNT(DISTINCT f.transaction_id) AS transaction_count,
        COUNT(DISTINCT f.customer_sk) AS unique_customers,
        COUNT(DISTINCT f.product_sk) AS unique_products,
        SUM(f.quantity) AS total_quantity,
        SUM(f.total_amount) AS gross_revenue,
        SUM(f.discount_amount) AS total_discounts,
        SUM(f.net_amount) AS net_revenue,
        SUM(f.cost * f.quantity) AS total_cost,
        SUM(f.profit) AS gross_profit,
        AVG(f.profit_margin) AS avg_profit_margin,
        AVG(f.net_amount) AS avg_transaction_value
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_date d ON f.date_sk = d.date_sk
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    INNER JOIN lakehouse_gold.dim_customer c ON f.customer_sk = c.customer_sk
    GROUP BY
        d.date, d.year, d.quarter, d.month, d.week_of_year, d.day_of_week,
        d.year_month, d.is_weekend, d.is_holiday,
        p.category, p.subcategory, p.brand,
        c.customer_segment, c.state, c.country
),

running_totals AS (
    SELECT
        df.*,
        -- Running totals by date
        SUM(df.net_revenue) OVER (
            PARTITION BY df.year
            ORDER BY df.date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ytd_revenue,
        SUM(df.gross_profit) OVER (
            PARTITION BY df.year
            ORDER BY df.date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ytd_profit,
        -- Moving averages
        AVG(df.net_revenue) OVER (
            ORDER BY df.date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS ma_7day_revenue,
        AVG(df.net_revenue) OVER (
            ORDER BY df.date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS ma_30day_revenue,
        AVG(df.net_revenue) OVER (
            ORDER BY df.date
            ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) AS ma_90day_revenue
    FROM daily_financials df
)

SELECT
    -- Time Dimensions
    rt.date,
    rt.year,
    rt.quarter,
    rt.month,
    rt.week_of_year,
    rt.day_of_week,
    rt.year_month,
    rt.is_weekend,
    rt.is_holiday,

    -- Product Dimensions
    rt.category,
    rt.subcategory,
    rt.brand,

    -- Customer Dimensions
    rt.customer_segment,
    rt.state,
    rt.country,

    -- Volume Metrics
    rt.transaction_count,
    rt.unique_customers,
    rt.unique_products,
    rt.total_quantity,

    -- Revenue Metrics
    rt.gross_revenue,
    rt.total_discounts,
    rt.net_revenue,
    rt.total_cost,

    -- Profitability Metrics
    rt.gross_profit,
    (rt.gross_profit / NULLIF(rt.net_revenue, 0)) * 100 AS gross_profit_margin_pct,
    rt.avg_profit_margin,

    -- Average Metrics
    rt.avg_transaction_value,
    rt.net_revenue / NULLIF(rt.transaction_count, 0) AS revenue_per_transaction,
    rt.net_revenue / NULLIF(rt.unique_customers, 0) AS revenue_per_customer,

    -- Discount Analysis
    (rt.total_discounts / NULLIF(rt.gross_revenue, 0)) * 100 AS discount_rate_pct,

    -- Running Totals & Trends
    rt.ytd_revenue,
    rt.ytd_profit,
    rt.ma_7day_revenue,
    rt.ma_30day_revenue,
    rt.ma_90day_revenue,

    -- Metadata
    CURRENT_TIMESTAMP AS view_generated_at

FROM running_totals rt;

-- =============================================================================
-- VIEW 4: operational_metrics
-- =============================================================================
-- Purpose: Monitor processing times, data freshness, pipeline health,
--          and data quality scores across the lakehouse
-- =============================================================================

CREATE OR REPLACE VIEW lakehouse_gold.operational_metrics AS
WITH table_freshness AS (
    SELECT
        'dim_customer' AS table_name,
        MAX(updated_timestamp) AS last_updated,
        DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    SELECT
        'dim_product' AS table_name,
        MAX(updated_timestamp) AS last_updated,
        DATE_DIFF('hour', MAX(updated_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count
    FROM lakehouse_gold.dim_product

    UNION ALL

    SELECT
        'fact_transactions' AS table_name,
        MAX(created_timestamp) AS last_updated,
        DATE_DIFF('hour', MAX(created_timestamp), CURRENT_TIMESTAMP) AS hours_since_update,
        COUNT(*) AS record_count
    FROM lakehouse_gold.fact_transactions
),

processing_stats AS (
    SELECT
        DATE_TRUNC('hour', f.created_timestamp) AS processing_hour,
        COUNT(*) AS records_processed,
        MIN(f.created_timestamp) AS batch_start_time,
        MAX(f.created_timestamp) AS batch_end_time,
        DATE_DIFF('second', MIN(f.created_timestamp), MAX(f.created_timestamp)) AS processing_duration_seconds
    FROM lakehouse_gold.fact_transactions f
    WHERE f.created_timestamp >= DATE_ADD('day', -7, CURRENT_DATE)
    GROUP BY DATE_TRUNC('hour', f.created_timestamp)
),

data_quality_summary AS (
    SELECT
        'fact_transactions' AS table_name,
        COUNT(*) AS total_records,
        COUNT(DISTINCT customer_sk) AS unique_customers,
        COUNT(DISTINCT product_sk) AS unique_products,
        SUM(CASE WHEN net_amount IS NULL THEN 1 ELSE 0 END) AS null_revenue_count,
        SUM(CASE WHEN net_amount < 0 THEN 1 ELSE 0 END) AS negative_revenue_count,
        SUM(CASE WHEN quantity <= 0 THEN 1 ELSE 0 END) AS invalid_quantity_count,
        100.0 * SUM(CASE WHEN net_amount IS NULL OR net_amount < 0 OR quantity <= 0 THEN 0 ELSE 1 END) / COUNT(*) AS quality_score
    FROM lakehouse_gold.fact_transactions
)

SELECT
    -- Table Information
    tf.table_name,
    tf.record_count,
    tf.last_updated,
    tf.hours_since_update,

    -- Freshness Status
    CASE
        WHEN tf.hours_since_update <= 1 THEN 'Fresh'
        WHEN tf.hours_since_update <= 6 THEN 'Acceptable'
        WHEN tf.hours_since_update <= 24 THEN 'Stale'
        ELSE 'Critical'
    END AS freshness_status,

    -- Processing Metrics (from recent processing stats)
    ps.processing_hour,
    ps.records_processed,
    ps.processing_duration_seconds,
    ps.records_processed / NULLIF(ps.processing_duration_seconds, 0) AS records_per_second,

    -- Data Quality
    dq.unique_customers,
    dq.unique_products,
    dq.null_revenue_count,
    dq.negative_revenue_count,
    dq.invalid_quantity_count,
    dq.quality_score,

    -- Metadata
    CURRENT_TIMESTAMP AS view_generated_at

FROM table_freshness tf
LEFT JOIN processing_stats ps ON tf.table_name = 'fact_transactions'
LEFT JOIN data_quality_summary dq ON tf.table_name = dq.table_name;

-- =============================================================================
-- VIEW 5: compliance_report
-- =============================================================================
-- Purpose: Track PII access, audit trails, data governance compliance
--          for GDPR, CCPA, and other regulatory requirements
-- =============================================================================

CREATE OR REPLACE VIEW lakehouse_gold.compliance_report AS
WITH pii_columns_inventory AS (
    SELECT
        'dim_customer' AS table_name,
        'email' AS column_name,
        'PII' AS data_classification,
        'Email Address' AS pii_type,
        COUNT(DISTINCT email) AS unique_values,
        SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) AS non_null_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    SELECT
        'dim_customer' AS table_name,
        'phone' AS column_name,
        'PII' AS data_classification,
        'Phone Number' AS pii_type,
        COUNT(DISTINCT phone) AS unique_values,
        SUM(CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END) AS non_null_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true
),

customer_data_retention AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.registration_date,
        DATE_DIFF('day', c.registration_date, CURRENT_DATE) AS days_since_registration,
        MAX(f.transaction_date) AS last_transaction_date,
        DATE_DIFF('day', MAX(f.transaction_date), CURRENT_DATE) AS days_since_last_activity,
        COUNT(f.transaction_id) AS transaction_count,
        CASE
            WHEN DATE_DIFF('day', MAX(f.transaction_date), CURRENT_DATE) > 1095 THEN 'Eligible for Deletion'
            WHEN DATE_DIFF('day', MAX(f.transaction_date), CURRENT_DATE) > 730 THEN 'Review Required'
            ELSE 'Active Retention'
        END AS retention_status
    FROM lakehouse_gold.dim_customer c
    LEFT JOIN lakehouse_gold.fact_transactions f ON c.customer_sk = f.customer_sk
    WHERE c.is_current = true
    GROUP BY c.customer_id, c.customer_name, c.registration_date
)

SELECT
    -- PII Inventory
    pii.table_name,
    pii.column_name,
    pii.data_classification,
    pii.pii_type,
    pii.unique_values,
    pii.non_null_count,

    -- Data Retention
    cdr.customer_id,
    cdr.registration_date,
    cdr.days_since_registration,
    cdr.last_transaction_date,
    cdr.days_since_last_activity,
    cdr.transaction_count,
    cdr.retention_status,

    -- Compliance Indicators
    CASE
        WHEN cdr.days_since_last_activity > 1095 THEN true
        ELSE false
    END AS gdpr_right_to_deletion,

    -- Metadata
    CURRENT_TIMESTAMP AS report_generated_at

FROM pii_columns_inventory pii
CROSS JOIN customer_data_retention cdr;

-- =============================================================================
-- End of View Definitions
-- =============================================================================
