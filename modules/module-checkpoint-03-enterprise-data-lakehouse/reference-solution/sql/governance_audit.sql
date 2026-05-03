-- =============================================================================
-- GOVERNANCE & AUDIT QUERIES - Enterprise Data Lakehouse
-- =============================================================================
-- Purpose: Lake Formation audit queries for tracking data access, permission
--          changes, PII column access, failed attempts, compliance reporting
--          for GDPR, CCPA, and data lineage tracking
-- Database: lakehouse_gold, lake_formation_logs
-- Compatible: Amazon Athena, Presto, Trino
-- =============================================================================

-- NOTE: These queries assume Lake Formation audit logs are stored in CloudWatch Logs
-- and exported to S3 in a table called `lake_formation_audit_logs`
-- Adjust table names and schemas based on your actual audit log configuration

-- =============================================================================
-- QUERY 1: Data Access by User and Role
-- =============================================================================
-- Purpose: Track who accessed what data and when
-- =============================================================================

SELECT
    event_time,
    principal_id,
    principal_type,
    resource_type,
    database_name,
    table_name,
    column_names,
    action,
    result,
    source_ip_address,
    user_agent,
    -- Access classification
    CASE
        WHEN action IN ('SELECT', 'DESCRIBE') THEN 'Read Access'
        WHEN action IN ('INSERT', 'UPDATE', 'DELETE') THEN 'Write Access'
        WHEN action IN ('ALTER', 'DROP', 'CREATE') THEN 'DDL Operation'
        ELSE 'Other'
    END AS access_type,
    -- Risk level
    CASE
        WHEN result = 'Failed' THEN 'Failed Attempt'
        WHEN action IN ('DROP', 'DELETE') THEN 'High Risk'
        WHEN action IN ('UPDATE', 'ALTER') THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS risk_level
FROM lake_formation_audit_logs
WHERE event_time >= DATE_ADD('day', -30, CURRENT_DATE)
    AND database_name IN ('lakehouse_gold', 'lakehouse_silver', 'lakehouse_bronze')
ORDER BY event_time DESC
LIMIT 10000;

-- =============================================================================
-- QUERY 2: PII Column Access Tracking
-- =============================================================================
-- Purpose: Monitor access to personally identifiable information
-- =============================================================================

WITH pii_columns AS (
    SELECT 'email' AS column_name, 'dim_customer' AS table_name, 'High' AS sensitivity
    UNION ALL
    SELECT 'phone', 'dim_customer', 'High'
    UNION ALL
    SELECT 'address', 'dim_customer', 'Medium'
    UNION ALL
    SELECT 'customer_name', 'dim_customer', 'Low'
),
pii_access_logs AS (
    SELECT
        al.event_time,
        al.principal_id,
        al.principal_type,
        al.database_name,
        al.table_name,
        al.column_names,
        al.action,
        al.result,
        al.source_ip_address,
        pc.column_name AS pii_column,
        pc.sensitivity
    FROM lake_formation_audit_logs al
    CROSS JOIN pii_columns pc
    WHERE al.database_name = 'lakehouse_gold'
        AND al.table_name = pc.table_name
        AND (al.column_names LIKE '%' || pc.column_name || '%' OR al.column_names = '*')
        AND al.event_time >= DATE_ADD('day', -30, CURRENT_DATE)
)
SELECT
    DATE(event_time) AS access_date,
    principal_id,
    principal_type,
    table_name,
    pii_column,
    sensitivity,
    action,
    COUNT(*) AS access_count,
    COUNT(DISTINCT source_ip_address) AS unique_ips,
    MAX(event_time) AS last_access,
    -- Compliance flag
    CASE
        WHEN sensitivity = 'High' AND COUNT(*) > 100 THEN 'Review Required'
        WHEN COUNT(DISTINCT source_ip_address) > 5 THEN 'Multiple IPs - Investigation'
        ELSE 'Normal'
    END AS compliance_flag
FROM pii_access_logs
WHERE result = 'Allowed'
GROUP BY DATE(event_time), principal_id, principal_type, table_name, pii_column, sensitivity, action
ORDER BY access_date DESC, access_count DESC;

-- =============================================================================
-- QUERY 3: Failed Access Attempts - Security Monitoring
-- =============================================================================
-- Purpose: Identify unauthorized access attempts and potential security threats
-- =============================================================================

WITH failed_attempts AS (
    SELECT
        event_time,
        principal_id,
        principal_type,
        database_name,
        table_name,
        column_names,
        action,
        error_message,
        source_ip_address,
        user_agent,
        ROW_NUMBER() OVER (
            PARTITION BY principal_id, DATE(event_time)
            ORDER BY event_time
        ) AS attempt_number
    FROM lake_formation_audit_logs
    WHERE result = 'Failed'
        AND event_time >= DATE_ADD('day', -30, CURRENT_DATE)
),
threat_assessment AS (
    SELECT
        principal_id,
        DATE(event_time) AS attempt_date,
        COUNT(*) AS failed_attempts_count,
        COUNT(DISTINCT table_name) AS tables_attempted,
        COUNT(DISTINCT source_ip_address) AS unique_ips,
        ARRAY_AGG(DISTINCT table_name) AS target_tables,
        MIN(event_time) AS first_attempt,
        MAX(event_time) AS last_attempt,
        -- Threat score
        CASE
            WHEN COUNT(*) >= 50 THEN 10
            WHEN COUNT(*) >= 20 THEN 7
            WHEN COUNT(*) >= 10 THEN 5
            ELSE 3
        END +
        CASE
            WHEN COUNT(DISTINCT table_name) >= 10 THEN 5
            WHEN COUNT(DISTINCT table_name) >= 5 THEN 3
            ELSE 1
        END AS threat_score
    FROM failed_attempts
    GROUP BY principal_id, DATE(event_time)
)
SELECT
    attempt_date,
    principal_id,
    failed_attempts_count,
    tables_attempted,
    unique_ips,
    target_tables,
    first_attempt,
    last_attempt,
    threat_score,
    CASE
        WHEN threat_score >= 15 THEN 'Critical Threat'
        WHEN threat_score >= 10 THEN 'High Risk'
        WHEN threat_score >= 5 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS threat_level,
    CASE
        WHEN threat_score >= 15 THEN 'Immediate investigation required. Block user access.'
        WHEN threat_score >= 10 THEN 'Investigate within 24 hours. Monitor closely.'
        WHEN threat_score >= 5 THEN 'Review user activity. Possible training issue.'
        ELSE 'Monitor for patterns.'
    END AS recommended_action
FROM threat_assessment
WHERE threat_score >= 5
ORDER BY threat_score DESC, attempt_date DESC;

-- =============================================================================
-- QUERY 4: Permission Changes Audit Trail
-- =============================================================================
-- Purpose: Track who modified permissions and what changes were made
-- =============================================================================

SELECT
    event_time,
    principal_id AS modified_by,
    principal_type,
    action,
    database_name,
    table_name,
    resource_type,
    -- Extract permission details (structure depends on your audit log format)
    permissions_granted,
    permissions_revoked,
    grantee_principal,
    -- Change classification
    CASE
        WHEN action = 'GrantPermissions' THEN 'Permission Granted'
        WHEN action = 'RevokePermissions' THEN 'Permission Revoked'
        WHEN action = 'BatchGrantPermissions' THEN 'Bulk Grant'
        WHEN action = 'BatchRevokePermissions' THEN 'Bulk Revoke'
        ELSE 'Other Permission Change'
    END AS change_type,
    -- Audit flag
    CASE
        WHEN permissions_granted LIKE '%ALL%' OR permissions_revoked LIKE '%ALL%' THEN 'High Impact'
        WHEN permissions_granted LIKE '%DROP%' OR permissions_granted LIKE '%DELETE%' THEN 'Sensitive Permission'
        ELSE 'Standard Change'
    END AS impact_level
FROM lake_formation_audit_logs
WHERE action IN ('GrantPermissions', 'RevokePermissions',
                 'BatchGrantPermissions', 'BatchRevokePermissions',
                 'PutDataLakeSettings', 'UpdateResource')
    AND event_time >= DATE_ADD('day', -90, CURRENT_DATE)
ORDER BY event_time DESC
LIMIT 5000;

-- =============================================================================
-- QUERY 5: User Activity Patterns & Behavioral Analysis
-- =============================================================================
-- Purpose: Identify unusual user behavior patterns
-- =============================================================================

WITH daily_activity AS (
    SELECT
        principal_id,
        DATE(event_time) AS activity_date,
        COUNT(*) AS total_queries,
        COUNT(DISTINCT table_name) AS tables_accessed,
        COUNT(DISTINCT database_name) AS databases_accessed,
        SUM(CASE WHEN action IN ('SELECT', 'DESCRIBE') THEN 1 ELSE 0 END) AS read_operations,
        SUM(CASE WHEN action IN ('INSERT', 'UPDATE', 'DELETE') THEN 1 ELSE 0 END) AS write_operations,
        SUM(CASE WHEN result = 'Failed' THEN 1 ELSE 0 END) AS failed_operations,
        MIN(event_time) AS first_activity,
        MAX(event_time) AS last_activity,
        COUNT(DISTINCT source_ip_address) AS unique_ips,
        -- Activity hours
        COUNT(DISTINCT HOUR(event_time)) AS active_hours
    FROM lake_formation_audit_logs
    WHERE event_time >= DATE_ADD('day', -30, CURRENT_DATE)
    GROUP BY principal_id, DATE(event_time)
),
user_baselines AS (
    SELECT
        principal_id,
        AVG(total_queries) AS avg_daily_queries,
        STDDEV(total_queries) AS stddev_queries,
        AVG(tables_accessed) AS avg_tables,
        AVG(active_hours) AS avg_active_hours
    FROM daily_activity
    GROUP BY principal_id
),
anomaly_detection AS (
    SELECT
        da.activity_date,
        da.principal_id,
        da.total_queries,
        da.tables_accessed,
        da.databases_accessed,
        da.read_operations,
        da.write_operations,
        da.failed_operations,
        da.unique_ips,
        da.active_hours,
        ub.avg_daily_queries,
        ub.stddev_queries,
        -- Calculate z-score
        (da.total_queries - ub.avg_daily_queries) / NULLIF(ub.stddev_queries, 0) AS query_volume_z_score
    FROM daily_activity da
    INNER JOIN user_baselines ub ON da.principal_id = ub.principal_id
)
SELECT
    activity_date,
    principal_id,
    total_queries,
    ROUND(avg_daily_queries, 0) AS expected_queries,
    tables_accessed,
    databases_accessed,
    read_operations,
    write_operations,
    failed_operations,
    unique_ips,
    active_hours,
    ROUND(query_volume_z_score, 2) AS query_volume_z_score,
    -- Anomaly classification
    CASE
        WHEN ABS(query_volume_z_score) > 3 THEN 'Extreme Anomaly'
        WHEN ABS(query_volume_z_score) > 2 THEN 'Significant Anomaly'
        WHEN ABS(query_volume_z_score) > 1.5 THEN 'Minor Anomaly'
        ELSE 'Normal'
    END AS anomaly_status,
    CASE
        WHEN query_volume_z_score > 3 AND failed_operations > 10 THEN 'Possible data exfiltration attempt'
        WHEN query_volume_z_score > 3 THEN 'Unusually high activity'
        WHEN query_volume_z_score < -2 THEN 'Unusually low activity'
        WHEN unique_ips > 3 THEN 'Multiple IP addresses - possible account sharing'
        WHEN active_hours > 18 THEN '24/7 activity - possible automation'
        ELSE 'Normal activity pattern'
    END AS behavior_assessment
FROM anomaly_detection
WHERE ABS(query_volume_z_score) > 1.5
    OR unique_ips > 3
    OR failed_operations > 10
ORDER BY query_volume_z_score DESC;

-- =============================================================================
-- QUERY 6: GDPR Right to Access Report
-- =============================================================================
-- Purpose: Generate report showing all data accessed for a specific customer
-- =============================================================================

WITH customer_data_inventory AS (
    SELECT
        'dim_customer' AS table_name,
        'customer_id' AS key_column,
        customer_id AS customer_identifier,
        'PII' AS data_classification,
        email,
        phone,
        address,
        city,
        state,
        country,
        customer_name
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true
        AND customer_id = '${CUSTOMER_ID}'  -- Parameterized for specific customer
),
customer_transactions AS (
    SELECT
        'fact_transactions' AS table_name,
        'transaction_id' AS record_identifier,
        f.transaction_id,
        f.transaction_date,
        f.net_amount,
        f.quantity,
        p.product_name
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_customer c ON f.customer_sk = c.customer_sk
    INNER JOIN lakehouse_gold.dim_product p ON f.product_sk = p.product_sk
    WHERE c.customer_id = '${CUSTOMER_ID}'
),
access_history AS (
    SELECT
        event_time,
        principal_id,
        table_name,
        action,
        column_names
    FROM lake_formation_audit_logs
    WHERE event_time >= DATE_ADD('year', -1, CURRENT_DATE)
        AND (
            (table_name = 'dim_customer' AND column_names LIKE '%email%')
            OR (table_name = 'fact_transactions')
        )
)
SELECT
    'Customer Profile' AS data_category,
    cdi.table_name,
    cdi.data_classification,
    cdi.customer_identifier,
    cdi.customer_name,
    cdi.email,
    cdi.phone,
    cdi.address,
    NULL AS transaction_count,
    CURRENT_TIMESTAMP AS report_generated_at
FROM customer_data_inventory cdi

UNION ALL

SELECT
    'Transaction History' AS data_category,
    'fact_transactions' AS table_name,
    'Financial' AS data_classification,
    '${CUSTOMER_ID}' AS customer_identifier,
    NULL AS customer_name,
    NULL AS email,
    NULL AS phone,
    NULL AS address,
    CAST(COUNT(*) AS VARCHAR) AS transaction_count,
    CURRENT_TIMESTAMP AS report_generated_at
FROM customer_transactions
GROUP BY data_category, table_name, data_classification, customer_identifier;

-- =============================================================================
-- QUERY 7: GDPR Right to Erasure (Right to be Forgotten)
-- =============================================================================
-- Purpose: Identify all records that need to be deleted for a customer
-- =============================================================================

WITH customer_footprint AS (
    SELECT
        'dim_customer' AS table_name,
        customer_sk,
        customer_id,
        'Primary Record' AS record_type,
        1 AS deletion_priority
    FROM lakehouse_gold.dim_customer
    WHERE customer_id = '${CUSTOMER_ID}'
        AND is_current = true
),
transaction_footprint AS (
    SELECT
        'fact_transactions' AS table_name,
        f.transaction_sk AS record_key,
        c.customer_id,
        'Transaction Record' AS record_type,
        2 AS deletion_priority
    FROM lakehouse_gold.fact_transactions f
    INNER JOIN lakehouse_gold.dim_customer c ON f.customer_sk = c.customer_sk
    WHERE c.customer_id = '${CUSTOMER_ID}'
),
anonymization_candidates AS (
    SELECT
        'dim_customer' AS table_name,
        customer_id,
        'Anonymize PII' AS action_required,
        'Set email, phone, address to NULL or anonymized values' AS anonymization_details,
        last_transaction_date,
        CASE
            WHEN DATE_DIFF('day', last_transaction_date, CURRENT_DATE) > 1095 THEN 'Eligible for Deletion'
            WHEN DATE_DIFF('day', last_transaction_date, CURRENT_DATE) > 730 THEN 'Consider Anonymization'
            ELSE 'Retain - Active within 2 years'
        END AS retention_status
    FROM lakehouse_gold.customer_360
    WHERE customer_id = '${CUSTOMER_ID}'
)
SELECT
    table_name,
    customer_id,
    record_type,
    deletion_priority,
    'DELETE FROM ' || table_name || ' WHERE customer_id = ''' || customer_id || '''' AS deletion_sql,
    CURRENT_TIMESTAMP AS erasure_request_date
FROM customer_footprint

UNION ALL

SELECT
    table_name,
    customer_id,
    record_type,
    deletion_priority,
    'DELETE FROM ' || table_name || ' WHERE customer_id = ''' || customer_id || '''' AS deletion_sql,
    CURRENT_TIMESTAMP AS erasure_request_date
FROM transaction_footprint

UNION ALL

SELECT
    table_name,
    customer_id,
    action_required AS record_type,
    3 AS deletion_priority,
    anonymization_details AS deletion_sql,
    CURRENT_TIMESTAMP AS erasure_request_date
FROM anonymization_candidates
ORDER BY deletion_priority;

-- =============================================================================
-- QUERY 8: CCPA Compliance - Data Sold or Shared Report
-- =============================================================================
-- Purpose: Report on customer data shared with third parties
-- =============================================================================

WITH data_sharing_log AS (
    -- This would typically come from an external data sharing tracking table
    SELECT
        share_date,
        customer_id,
        third_party_name,
        data_categories_shared,
        purpose_of_sharing,
        data_retention_period,
        opt_out_available
    FROM data_sharing_audit_log  -- Assuming this table exists
    WHERE share_date >= DATE_ADD('year', -1, CURRENT_DATE)
),
customer_opt_out_status AS (
    SELECT
        customer_id,
        has_opted_out_of_sale,
        opt_out_date,
        communication_preference
    FROM lakehouse_gold.customer_360
)
SELECT
    dsl.customer_id,
    dsl.share_date,
    dsl.third_party_name,
    dsl.data_categories_shared,
    dsl.purpose_of_sharing,
    dsl.data_retention_period,
    cos.has_opted_out_of_sale,
    cos.opt_out_date,
    -- Compliance check
    CASE
        WHEN cos.has_opted_out_of_sale = true AND dsl.share_date > cos.opt_out_date THEN 'VIOLATION - Shared after opt-out'
        WHEN cos.has_opted_out_of_sale = true AND dsl.share_date <= cos.opt_out_date THEN 'Compliant - Shared before opt-out'
        WHEN cos.has_opted_out_of_sale = false THEN 'Compliant - No opt-out'
        ELSE 'Review Required'
    END AS ccpa_compliance_status
FROM data_sharing_log dsl
LEFT JOIN customer_opt_out_status cos ON dsl.customer_id = cos.customer_id
ORDER BY dsl.share_date DESC;

-- =============================================================================
-- QUERY 9: Data Lineage Tracking
-- =============================================================================
-- Purpose: Track data flow from bronze to silver to gold layers
-- =============================================================================

WITH lineage_metadata AS (
    SELECT
        'fact_transactions' AS gold_table,
        'transactions_silver' AS silver_source,
        'transactions_bronze' AS bronze_source,
        MAX(created_timestamp) AS last_load_time,
        COUNT(*) AS record_count
    FROM lakehouse_gold.fact_transactions
    WHERE created_timestamp >= DATE_ADD('day', -7, CURRENT_DATE)
    GROUP BY gold_table, silver_source, bronze_source
),
transformation_summary AS (
    SELECT
        'bronze_to_silver' AS transformation_stage,
        'transactions' AS entity,
        -- Typical transformations
        'Data cleansing, type conversion, deduplication' AS transformations_applied,
        DATE_ADD('day', -1, CURRENT_DATE) AS last_run_date,
        'Success' AS status

    UNION ALL

    SELECT
        'silver_to_gold' AS transformation_stage,
        'fact_transactions' AS entity,
        'Surrogate key generation, dimension lookup, aggregations' AS transformations_applied,
        CURRENT_DATE AS last_run_date,
        'Success' AS status
)
SELECT
    lm.gold_table,
    lm.silver_source,
    lm.bronze_source,
    lm.last_load_time,
    lm.record_count,
    ts.transformation_stage,
    ts.transformations_applied,
    ts.last_run_date,
    ts.status,
    -- Lineage quality
    CASE
        WHEN DATE_DIFF('hour', lm.last_load_time, CURRENT_TIMESTAMP) <= 24 THEN 'Up to date'
        WHEN DATE_DIFF('hour', lm.last_load_time, CURRENT_TIMESTAMP) <= 48 THEN 'Slightly stale'
        ELSE 'Stale - Review pipeline'
    END AS lineage_freshness
FROM lineage_metadata lm
CROSS JOIN transformation_summary ts
ORDER BY lm.last_load_time DESC;

-- =============================================================================
-- QUERY 10: Data Access Compliance Summary Report
-- =============================================================================
-- Purpose: Executive summary of data governance and compliance status
-- =============================================================================

WITH access_summary AS (
    SELECT
        COUNT(*) AS total_access_events,
        COUNT(DISTINCT principal_id) AS unique_users,
        COUNT(DISTINCT table_name) AS tables_accessed,
        SUM(CASE WHEN result = 'Allowed' THEN 1 ELSE 0 END) AS successful_access,
        SUM(CASE WHEN result = 'Failed' THEN 1 ELSE 0 END) AS failed_access,
        SUM(CASE WHEN column_names LIKE '%email%' OR column_names LIKE '%phone%' THEN 1 ELSE 0 END) AS pii_access_count
    FROM lake_formation_audit_logs
    WHERE event_time >= DATE_ADD('day', -30, CURRENT_DATE)
),
permission_changes AS (
    SELECT
        COUNT(*) AS total_permission_changes,
        COUNT(DISTINCT principal_id) AS users_modifying_permissions
    FROM lake_formation_audit_logs
    WHERE action IN ('GrantPermissions', 'RevokePermissions')
        AND event_time >= DATE_ADD('day', -30, CURRENT_DATE)
),
security_incidents AS (
    SELECT
        COUNT(DISTINCT principal_id) AS users_with_failed_attempts,
        SUM(CASE WHEN failed_count >= 10 THEN 1 ELSE 0 END) AS high_risk_users
    FROM (
        SELECT
            principal_id,
            COUNT(*) AS failed_count
        FROM lake_formation_audit_logs
        WHERE result = 'Failed'
            AND event_time >= DATE_ADD('day', -30, CURRENT_DATE)
        GROUP BY principal_id
    ) failed_summary
),
gdpr_requests AS (
    SELECT
        COUNT(*) AS total_gdpr_requests,
        SUM(CASE WHEN request_type = 'Access' THEN 1 ELSE 0 END) AS access_requests,
        SUM(CASE WHEN request_type = 'Erasure' THEN 1 ELSE 0 END) AS erasure_requests,
        SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_requests
    FROM gdpr_request_log  -- Assuming this table exists
    WHERE request_date >= DATE_ADD('day', -30, CURRENT_DATE)
)
SELECT
    CURRENT_DATE AS report_date,
    '30-Day Summary' AS report_period,
    -- Access metrics
    acs.total_access_events,
    acs.unique_users,
    acs.tables_accessed,
    acs.successful_access,
    acs.failed_access,
    ROUND(acs.failed_access * 100.0 / NULLIF(acs.total_access_events, 0), 2) AS failed_access_rate,
    acs.pii_access_count,
    -- Permission management
    pc.total_permission_changes,
    pc.users_modifying_permissions,
    -- Security
    si.users_with_failed_attempts,
    si.high_risk_users,
    -- Compliance
    COALESCE(gr.total_gdpr_requests, 0) AS total_gdpr_requests,
    COALESCE(gr.access_requests, 0) AS gdpr_access_requests,
    COALESCE(gr.erasure_requests, 0) AS gdpr_erasure_requests,
    COALESCE(gr.completed_requests, 0) AS gdpr_completed_requests,
    -- Overall health
    CASE
        WHEN acs.failed_access_rate < 1 AND si.high_risk_users = 0 THEN 'Healthy'
        WHEN acs.failed_access_rate < 5 AND si.high_risk_users <= 2 THEN 'Good'
        WHEN acs.failed_access_rate < 10 THEN 'Fair'
        ELSE 'Needs Attention'
    END AS governance_health_status,
    CURRENT_TIMESTAMP AS report_generated_at
FROM access_summary acs
CROSS JOIN permission_changes pc
CROSS JOIN security_incidents si
LEFT JOIN gdpr_requests gr ON 1=1;

-- =============================================================================
-- QUERY 11: Audit Log Retention & Archival Status
-- =============================================================================
-- Purpose: Monitor audit log retention compliance
-- =============================================================================

WITH log_age_distribution AS (
    SELECT
        DATE_TRUNC('month', event_time) AS log_month,
        COUNT(*) AS event_count,
        MIN(event_time) AS oldest_event,
        MAX(event_time) AS newest_event,
        DATE_DIFF('day', MIN(event_time), CURRENT_DATE) AS days_retained
    FROM lake_formation_audit_logs
    GROUP BY DATE_TRUNC('month', event_time)
)
SELECT
    log_month,
    event_count,
    oldest_event,
    newest_event,
    days_retained,
    -- Compliance with typical retention policies (7 years = 2555 days)
    CASE
        WHEN days_retained <= 2555 THEN 'Within Retention Period'
        ELSE 'eligible for Archival'
    END AS retention_status,
    CASE
        WHEN days_retained <= 90 THEN 'Hot Storage'
        WHEN days_retained <= 365 THEN 'Warm Storage'
        WHEN days_retained <= 2555 THEN 'Cold Storage'
        ELSE 'Archive/Glacier'
    END AS recommended_storage_tier
FROM log_age_distribution
ORDER BY log_month DESC;

-- =============================================================================
-- QUERY 12: Data Classification Inventory
-- =============================================================================
-- Purpose: Inventory of all data assets by classification level
-- =============================================================================

WITH data_classification AS (
    SELECT
        'dim_customer' AS table_name,
        ARRAY['email', 'phone', 'address'] AS pii_columns,
        ARRAY['customer_name'] AS public_columns,
        ARRAY['credit_limit', 'risk_score'] AS confidential_columns,
        COUNT(*) AS record_count
    FROM lakehouse_gold.dim_customer
    WHERE is_current = true

    UNION ALL

    SELECT
        'fact_transactions' AS table_name,
        NULL AS pii_columns,
        ARRAY['transaction_date'] AS public_columns,
        ARRAY['net_amount', 'profit', 'profit_margin'] AS confidential_columns,
        COUNT(*) AS record_count
    FROM lakehouse_gold.fact_transactions

    UNION ALL

    SELECT
        'dim_product' AS table_name,
        NULL AS pii_columns,
        ARRAY['product_name', 'category', 'brand'] AS public_columns,
        ARRAY['cost', 'unit_price', 'product_margin'] AS confidential_columns,
        COUNT(*) AS record_count
    FROM lakehouse_gold.dim_product
)
SELECT
    table_name,
    record_count,
    CARDINALITY(pii_columns) AS pii_column_count,
    CARDINALITY(public_columns) AS public_column_count,
    CARDINALITY(confidential_columns) AS confidential_column_count,
    pii_columns,
    public_columns,
    confidential_columns,
    -- Classification level
    CASE
        WHEN CARDINALITY(pii_columns) > 0 THEN 'Highly Sensitive'
        WHEN CARDINALITY(confidential_columns) > 0 THEN 'Confidential'
        ELSE 'Public'
    END AS overall_classification,
    -- Required controls
    CASE
        WHEN CARDINALITY(pii_columns) > 0 THEN 'Encryption at rest, column-level security, audit logging, data masking'
        WHEN CARDINALITY(confidential_columns) > 0 THEN 'Encryption at rest, role-based access control'
        ELSE 'Standard access controls'
    END AS required_security_controls
FROM data_classification;

-- =============================================================================
-- End of Governance & Audit Queries
-- =============================================================================
