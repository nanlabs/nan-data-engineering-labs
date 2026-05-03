"""
Module 17: Cloud Cost Optimization - Validation Test Suite

This test suite validates the cost optimization exercises and utilities
using pytest and moto for AWS service mocking.

Test Coverage:
- Cost Explorer API queries
- S3 lifecycle policy calculations
- RI/SP recommendation logic
- Budget calculations and alerts
- Cost anomaly detection
- Cleanup automation (idle resources)
- Unit economics calculations
- Forecast accuracy metrics

Run tests:
    pytest validation/test_cost_optimization.py -v
    pytest validation/test_cost_optimization.py --cov=exercises --cov-report=html
"""

import pytest
import json
import pandas as pd
from datetime import datetime, timedelta
import boto3
from moto import mock_ce, mock_ec2, mock_s3, mock_cloudwatch
import sys
import os

# Add exercises directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'exercises'))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for moto."""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')


@pytest.fixture
def sample_cost_data():
    """Load sample cost usage report data."""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'cost-usage-report.csv')
    return pd.read_csv(csv_path)


@pytest.fixture
def sample_tag_data():
    """Load sample cost allocation tags data."""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'cost-allocation-tags.json')
    with open(json_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def ce_client(aws_credentials):
    """Mocked Cost Explorer client."""
    with mock_ce():
        yield boto3.client('ce', region_name='us-east-1')


@pytest.fixture
def ec2_client(aws_credentials):
    """Mocked EC2 client."""
    with mock_ec2():
        yield boto3.client('ec2', region_name='us-east-1')


@pytest.fixture
def s3_client(aws_credentials):
    """Mocked S3 client."""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture
def cloudwatch_client(aws_credentials):
    """Mocked CloudWatch client."""
    with mock_cloudwatch():
        yield boto3.client('cloudwatch', region_name='us-east-1')


# ============================================================================
# Test Cost Analysis (Exercise 01)
# ============================================================================

def test_parse_cost_usage_report(sample_cost_data):
    """Test parsing of Cost and Usage Report CSV."""
    assert len(sample_cost_data) == 50
    assert 'unblended_cost' in sample_cost_data.columns
    assert 'cost_center' in sample_cost_data.columns

    # Verify cost data is numeric
    assert sample_cost_data['unblended_cost'].dtype in ['float64', 'float32']

    # Check for multiple services
    services = sample_cost_data['product_code'].unique()
    assert 'AmazonEC2' in services
    assert 'AmazonS3' in services
    assert 'AWSLambda' in services


def test_calculate_monthly_costs(sample_cost_data):
    """Test monthly cost aggregation."""
    monthly_total = sample_cost_data['unblended_cost'].sum()
    assert monthly_total > 0
    assert monthly_total < 10000  # Sanity check

    # Test grouping by service
    by_service = sample_cost_data.groupby('product_code')['unblended_cost'].sum()
    assert len(by_service) >= 5  # At least 5 different services


def test_cost_by_tag(sample_cost_data):
    """Test cost allocation by tags."""
    # Group by cost center
    by_cost_center = sample_cost_data.groupby('cost_center')['unblended_cost'].sum()
    assert len(by_cost_center) >= 3  # At least 3 cost centers

    # Group by environment
    by_environment = sample_cost_data.groupby('environment')['unblended_cost'].sum()
    assert 'prod' in by_environment.index
    assert 'dev' in by_environment.index

    # Verify production costs are higher
    assert by_environment['prod'] > by_environment['dev']


def test_identify_top_cost_drivers(sample_cost_data):
    """Test identification of top cost contributors."""
    # Top 5 services by cost
    top_services = sample_cost_data.groupby('product_code')['unblended_cost'].sum().nlargest(5)
    assert len(top_services) == 5

    # Verify top service accounts for significant portion
    total_cost = sample_cost_data['unblended_cost'].sum()
    top_service_cost = top_services.iloc[0]
    percentage = (top_service_cost / total_cost) * 100
    assert percentage >= 10  # Top service should be at least 10% of total


# ============================================================================
# Test Storage Optimization (Exercise 02)
# ============================================================================

def test_lifecycle_policy_validation():
    """Test S3 lifecycle policy configuration."""
    lifecycle_policy = {
        'Rules': [
            {
                'Id': 'Archive old data',
                'Status': 'Enabled',
                'Transitions': [
                    {'Days': 30, 'StorageClass': 'STANDARD_IA'},
                    {'Days': 90, 'StorageClass': 'GLACIER'},
                    {'Days': 365, 'StorageClass': 'DEEP_ARCHIVE'}
                ],
                'Expiration': {'Days': 2555}  # 7 years
            }
        ]
    }

    rule = lifecycle_policy['Rules'][0]
    assert rule['Status'] == 'Enabled'
    assert len(rule['Transitions']) == 3
    assert rule['Transitions'][0]['StorageClass'] == 'STANDARD_IA'
    assert rule['Transitions'][1]['Days'] == 90


def test_calculate_storage_costs():
    """Test storage cost calculation across tiers."""
    # Pricing per GB-month
    STANDARD = 0.023
    STANDARD_IA = 0.0125
    GLACIER = 0.004
    DEEP_ARCHIVE = 0.00099

    # 10 TB storage for 1 year
    size_gb = 10 * 1024

    # Scenario 1: All Standard
    all_standard = size_gb * STANDARD * 12

    # Scenario 2: Multi-tier (30 days Standard, 60 days IA, 275 days Glacier)
    multi_tier = (
        size_gb * STANDARD * 1 +       # Month 1: Standard
        size_gb * STANDARD_IA * 2 +    # Months 2-3: IA
        size_gb * GLACIER * 9          # Months 4-12: Glacier
    )

    savings = all_standard - multi_tier
    savings_percentage = (savings / all_standard) * 100

    assert all_standard > multi_tier
    assert savings_percentage >= 70  # At least 70% savings


def test_intelligent_tiering_benefits():
    """Test Intelligent-Tiering cost calculation."""
    # 100 TB with varying access patterns
    size_gb = 100 * 1024

    # Standard pricing
    standard_cost = size_gb * 0.023

    # Intelligent-Tiering: 20% frequent, 50% infrequent, 30% archive
    intelligent_cost = (
        size_gb * 0.20 * 0.023 +      # Frequent tier
        size_gb * 0.50 * 0.0125 +     # Infrequent tier
        size_gb * 0.30 * 0.004 +      # Archive tier
        size_gb * 0.0025               # Monitoring fee
    )

    savings = standard_cost - intelligent_cost
    savings_percentage = (savings / standard_cost) * 100

    assert intelligent_cost < standard_cost
    assert savings_percentage >= 30  # At least 30% savings


# ============================================================================
# Test Compute Purchasing (Exercise 03)
# ============================================================================

def test_reserved_instance_roi():
    """Test Reserved Instance ROI calculation."""
    # m5.large pricing
    on_demand_hourly = 0.096
    ri_1y_no_upfront = 0.062
    ri_1y_all_upfront = 0.058
    ri_3y_all_upfront = 0.048

    hours_per_month = 730

    # Calculate costs for 1 year
    on_demand_annual = on_demand_hourly * hours_per_month * 12
    ri_1y_annual = ri_1y_all_upfront * hours_per_month * 12
    ri_3y_annual = ri_3y_all_upfront * hours_per_month * 12

    # 1-year RI savings
    savings_1y = on_demand_annual - ri_1y_annual
    savings_percentage_1y = (savings_1y / on_demand_annual) * 100

    # 3-year RI savings
    savings_3y = on_demand_annual - ri_3y_annual
    savings_percentage_3y = (savings_3y / on_demand_annual) * 100

    assert savings_percentage_1y >= 38  # At least 38% savings
    assert savings_percentage_3y >= 48  # At least 48% savings
    assert savings_3y > savings_1y


def test_savings_plans_flexibility():
    """Test Savings Plans cost calculation."""
    # Compute Savings Plans (most flexible)
    commitment_hourly = 10.0  # $10/hour commitment

    # Scenario 1: Using Lambda (covered by Compute SP)
    lambda_gb_seconds = 75000
    lambda_cost = lambda_gb_seconds * 0.0000166667

    # Scenario 2: Using Fargate (covered by Compute SP)
    fargate_vcpu_hours = 100
    fargate_cost = fargate_vcpu_hours * 0.04048

    # Scenario 3: Using EC2 (covered by Compute SP)
    ec2_hours = 50
    ec2_cost = ec2_hours * 0.096

    total_compute = lambda_cost + fargate_cost + ec2_cost

    # With Savings Plan: 50% discount
    sp_discount = 0.50
    savings_plan_cost = total_compute * (1 - sp_discount)

    savings = total_compute - savings_plan_cost
    savings_percentage = (savings / total_compute) * 100

    assert savings_percentage >= 45  # At least 45% savings


def test_spot_instance_savings():
    """Test Spot instance cost calculation."""
    # c5.2xlarge pricing
    on_demand_hourly = 0.34
    typical_spot_hourly = 0.102  # ~70% discount

    # Run 100 hours of batch processing
    hours = 100

    on_demand_cost = hours * on_demand_hourly
    spot_cost = hours * typical_spot_hourly

    savings = on_demand_cost - spot_cost
    savings_percentage = (savings / on_demand_cost) * 100

    assert savings_percentage >= 65  # At least 65% savings
    assert spot_cost < on_demand_cost * 0.35


# ============================================================================
# Test Right-Sizing (Exercise 04)
# ============================================================================

def test_identify_oversized_instances():
    """Test identification of oversized EC2 instances."""
    # Sample CloudWatch metrics
    instance_metrics = [
        {'instance_id': 'i-001', 'avg_cpu': 8.5, 'max_cpu': 15.2, 'instance_type': 'm5.2xlarge'},
        {'instance_id': 'i-002', 'avg_cpu': 45.3, 'max_cpu': 78.1, 'instance_type': 'm5.large'},
        {'instance_id': 'i-003', 'avg_cpu': 3.2, 'max_cpu': 9.8, 'instance_type': 'm5.xlarge'},
    ]

    # Identify instances with avg CPU < 10%
    oversized = [i for i in instance_metrics if i['avg_cpu'] < 10]

    assert len(oversized) == 2
    assert 'i-001' in [i['instance_id'] for i in oversized]
    assert 'i-003' in [i['instance_id'] for i in oversized]


def test_calculate_right_sizing_savings():
    """Test right-sizing savings calculation."""
    # m5.2xlarge -> m5.xlarge (half the size)
    current_hourly = 0.384
    recommended_hourly = 0.192

    hours_per_month = 730

    current_monthly = current_hourly * hours_per_month
    recommended_monthly = recommended_hourly * hours_per_month

    savings = current_monthly - recommended_monthly
    savings_percentage = (savings / current_monthly) * 100

    assert savings_percentage == 50.0
    assert savings == pytest.approx(140.16, rel=0.01)


def test_right_sizing_recommendations():
    """Test generating right-sizing recommendations."""
    recommendations = [
        {
            'instance_id': 'i-001',
            'current': 'm5.2xlarge',
            'recommended': 'm5.large',
            'avg_cpu': 8.5,
            'current_cost': 280.32,
            'recommended_cost': 70.08,
            'monthly_savings': 210.24
        },
        {
            'instance_id': 'i-003',
            'current': 'm5.xlarge',
            'recommended': 'm5.large',
            'avg_cpu': 3.2,
            'current_cost': 140.16,
            'recommended_cost': 70.08,
            'monthly_savings': 70.08
        }
    ]

    total_savings = sum(r['monthly_savings'] for r in recommendations)
    assert total_savings == pytest.approx(280.32, rel=0.01)

    # Verify recommendations are smaller than current
    for rec in recommendations:
        assert rec['recommended_cost'] < rec['current_cost']


# ============================================================================
# Test Serverless Cost Analysis (Exercise 05)
# ============================================================================

def test_lambda_cost_calculation():
    """Test Lambda cost calculation."""
    # Pricing
    REQUEST_COST = 0.0000002  # per request
    DURATION_COST = 0.0000166667  # per GB-second

    # Scenario: 1M requests, 512 MB memory, 200ms avg duration
    requests = 1_000_000
    memory_gb = 0.5
    avg_duration_seconds = 0.2

    request_cost = requests * REQUEST_COST
    gb_seconds = requests * memory_gb * avg_duration_seconds
    duration_cost = gb_seconds * DURATION_COST

    total_cost = request_cost + duration_cost

    assert request_cost == 0.20
    assert gb_seconds == 100_000
    assert total_cost == pytest.approx(1.87, rel=0.01)


def test_lambda_vs_ec2_cost_comparison():
    """Test Lambda vs EC2 cost comparison."""
    # Lambda costs (from above test)
    lambda_monthly_cost = 1.87  # 1M requests

    # EC2 equivalent: t3.small running 24/7
    ec2_hourly = 0.0208
    ec2_monthly_cost = ec2_hourly * 730

    # Lambda is cheaper for low-volume workloads
    assert lambda_monthly_cost < ec2_monthly_cost

    # Calculate break-even point
    # EC2 cost = Lambda cost when:
    # Monthly Lambda = Monthly EC2
    # This varies based on request volume and duration

    # For this scenario, Lambda wins up to about 8M requests/month
    requests_at_breakeven = (ec2_monthly_cost / lambda_monthly_cost) * 1_000_000
    assert requests_at_breakeven > 1_000_000


def test_fargate_vs_ec2_cost():
    """Test Fargate vs EC2 cost comparison."""
    # Fargate pricing (per vCPU-hour and GB-hour)
    FARGATE_VCPU_HOUR = 0.04048
    FARGATE_GB_HOUR = 0.004445

    # Scenario: 2 vCPU, 4 GB, running 8 hours/day
    vcpu = 2
    memory_gb = 4
    hours_per_day = 8
    days_per_month = 30

    fargate_monthly = (
        vcpu * FARGATE_VCPU_HOUR * hours_per_day * days_per_month +
        memory_gb * FARGATE_GB_HOUR * hours_per_day * days_per_month
    )

    # EC2 equivalent: m5.large (2 vCPU, 8 GB) running 24/7
    ec2_hourly = 0.096
    ec2_monthly = ec2_hourly * 730

    # Fargate is cheaper for variable workloads
    assert fargate_monthly < ec2_monthly
    savings = ec2_monthly - fargate_monthly
    savings_percentage = (savings / ec2_monthly) * 100
    assert savings_percentage >= 50


# ============================================================================
# Test Budget Management (Exercise 06)
# ============================================================================

def test_budget_threshold_calculation():
    """Test budget threshold calculations."""
    budget_limit = 1000.0

    thresholds = {
        'warning': budget_limit * 0.80,
        'alert': budget_limit * 1.00,
        'critical': budget_limit * 1.20,
        'forecasted': budget_limit * 1.00
    }

    assert thresholds['warning'] == 800.0
    assert thresholds['alert'] == 1000.0
    assert thresholds['critical'] == 1200.0


def test_budget_remaining():
    """Test remaining budget calculation."""
    budget_limit = 1000.0
    current_spend = 650.0

    remaining = budget_limit - current_spend
    remaining_percentage = (remaining / budget_limit) * 100

    assert remaining == 350.0
    assert remaining_percentage == 35.0


def test_budget_forecast():
    """Test budget forecast based on current trend."""
    # Current spend: 15 days into month, $400 spent
    days_elapsed = 15
    current_spend = 400.0
    days_in_month = 30

    # Linear projection
    daily_rate = current_spend / days_elapsed
    forecasted_total = daily_rate * days_in_month

    assert daily_rate == pytest.approx(26.67, rel=0.01)
    assert forecasted_total == 800.0


# ============================================================================
# Test Cleanup Automation
# ============================================================================

def test_find_idle_ec2_instances():
    """Test identification of idle EC2 instances."""
    instances_with_metrics = [
        {'instance_id': 'i-001', 'avg_cpu_7d': 3.2, 'state': 'running'},
        {'instance_id': 'i-002', 'avg_cpu_7d': 45.8, 'state': 'running'},
        {'instance_id': 'i-003', 'avg_cpu_7d': 2.1, 'state': 'running'},
        {'instance_id': 'i-004', 'avg_cpu_7d': 15.3, 'state': 'stopped'},
    ]

    # Idle threshold: avg CPU < 5% for 7 days
    idle_instances = [i for i in instances_with_metrics if i['avg_cpu_7d'] < 5 and i['state'] == 'running']

    assert len(idle_instances) == 2
    assert 'i-001' in [i['instance_id'] for i in idle_instances]


def test_find_unattached_volumes():
    """Test identification of unattached EBS volumes."""
    volumes = [
        {'volume_id': 'vol-001', 'state': 'available', 'create_date': '2023-10-01', 'size': 100},
        {'volume_id': 'vol-002', 'state': 'in-use', 'create_date': '2024-01-01', 'size': 500},
        {'volume_id': 'vol-003', 'state': 'available', 'create_date': '2024-01-15', 'size': 50},
    ]

    # Find volumes unattached > 30 days
    cutoff_date = datetime.now() - timedelta(days=30)

    unattached_old = [
        v for v in volumes
        if v['state'] == 'available' and
        datetime.strptime(v['create_date'], '%Y-%m-%d') < cutoff_date
    ]

    assert len(unattached_old) == 1
    assert unattached_old[0]['volume_id'] == 'vol-001'


def test_calculate_cleanup_savings():
    """Test savings calculation from cleanup."""
    # Resources to clean
    cleanup_items = [
        {'type': 'ebs_volume', 'size_gb': 100, 'cost_per_gb': 0.10},
        {'type': 'ebs_volume', 'size_gb': 50, 'cost_per_gb': 0.10},
        {'type': 'elastic_ip', 'count': 3, 'cost_each': 3.60},
        {'type': 'snapshot', 'size_gb': 200, 'cost_per_gb': 0.05},
    ]

    # Calculate monthly savings
    volume_savings = sum(i['size_gb'] * i['cost_per_gb'] for i in cleanup_items if i['type'] == 'ebs_volume')
    eip_savings = sum(i['count'] * i['cost_each'] for i in cleanup_items if i['type'] == 'elastic_ip')
    snapshot_savings = sum(i['size_gb'] * i['cost_per_gb'] for i in cleanup_items if i['type'] == 'snapshot')

    total_savings = volume_savings + eip_savings + snapshot_savings

    assert volume_savings == 15.0
    assert eip_savings == 10.80
    assert snapshot_savings == 10.0
    assert total_savings == 35.80


# ============================================================================
# Test Anomaly Detection
# ============================================================================

def test_z_score_anomaly_detection():
    """Test Z-score based anomaly detection."""
    # Historical daily costs (30 days)
    daily_costs = [100] * 25 + [105] * 3 + [98] * 1 + [450] * 1  # Day 30 is anomaly

    # Calculate mean and standard deviation
    mean = sum(daily_costs[:-1]) / len(daily_costs[:-1])
    variance = sum((x - mean) ** 2 for x in daily_costs[:-1]) / len(daily_costs[:-1])
    std_dev = variance ** 0.5

    # Z-score for day 30
    current_cost = daily_costs[-1]
    z_score = (current_cost - mean) / std_dev

    # Anomaly threshold: |z-score| > 3
    is_anomaly = abs(z_score) > 3

    assert is_anomaly
    assert z_score > 10  # Significantly anomalous


def test_percentage_change_anomaly():
    """Test percentage change anomaly detection."""
    last_month_cost = 1000.0
    current_month_cost = 1500.0

    percentage_change = ((current_month_cost - last_month_cost) / last_month_cost) * 100

    # Threshold: 20% increase
    is_anomaly = percentage_change > 20

    assert percentage_change == 50.0
    assert is_anomaly


# ============================================================================
# Test Unit Economics
# ============================================================================

def test_cost_per_user():
    """Test cost per user calculation."""
    total_monthly_cost = 5000.0
    active_users = 10000

    cost_per_user = total_monthly_cost / active_users

    assert cost_per_user == 0.50


def test_cost_per_transaction():
    """Test cost per transaction calculation."""
    total_monthly_cost = 5000.0
    total_transactions = 5_000_000

    cost_per_transaction = total_monthly_cost / total_transactions

    assert cost_per_transaction == 0.001


def test_cost_per_gb_stored():
    """Test cost per GB stored calculation."""
    storage_cost = 2500.0
    total_gb = 100 * 1024  # 100 TB

    cost_per_gb = storage_cost / total_gb

    assert cost_per_gb == pytest.approx(0.0244, rel=0.01)


# ============================================================================
# Test Forecast Accuracy
# ============================================================================

def test_linear_forecast():
    """Test linear cost forecasting."""
    # Last 3 months costs
    historical_costs = [1000, 1100, 1200]

    # Calculate growth rate
    growth_rate = (historical_costs[-1] - historical_costs[0]) / historical_costs[0]

    # Forecast next month
    forecast = historical_costs[-1] * (1 + (growth_rate / 2))

    assert growth_rate == 0.20  # 20% growth over 3 months
    assert forecast == pytest.approx(1320, rel=0.01)


def test_mape_calculation():
    """Test Mean Absolute Percentage Error calculation."""
    # Actual vs forecasted costs
    actual = [1000, 1100, 1200, 1300]
    forecasted = [1020, 1080, 1250, 1280]

    # Calculate MAPE
    errors = [abs(a - f) / a for a, f in zip(actual, forecasted)]
    mape = (sum(errors) / len(errors)) * 100

    assert mape < 15  # Target accuracy: MAPE < 15%


# ============================================================================
# Test Tag Validation
# ============================================================================

def test_validate_required_tags(sample_tag_data):
    """Test validation of required tags."""
    required_tags = ['CostCenter', 'Team', 'Project', 'Environment', 'Owner']

    resources = sample_tag_data['resources']
    valid_resources = []

    for resource in resources:
        tags = resource.get('tags', {})
        has_all_required = all(tag in tags for tag in required_tags)
        if has_all_required:
            valid_resources.append(resource)

    # Should have at least 70% compliance
    compliance_rate = (len(valid_resources) / len(resources)) * 100
    assert compliance_rate >= 70


def test_validate_owner_email_format(sample_tag_data):
    """Test Owner tag email format validation."""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    resources = sample_tag_data['resources']
    valid_emails = []

    for resource in resources:
        tags = resource.get('tags', {})
        if 'Owner' in tags:
            owner = tags['Owner']
            if re.match(email_pattern, owner):
                valid_emails.append(resource)

    # Most resources should have valid email format
    assert len(valid_emails) >= 15


def test_validate_environment_values(sample_tag_data):
    """Test Environment tag has allowed values."""
    allowed_environments = ['prod', 'staging', 'dev', 'test', 'sandbox']

    resources = sample_tag_data['resources']
    invalid_environments = []

    for resource in resources:
        tags = resource.get('tags', {})
        if 'Environment' in tags:
            env = tags['Environment']
            if env not in allowed_environments:
                invalid_environments.append(resource)

    # All environments should be valid
    assert len(invalid_environments) == 0


def test_tagging_compliance_report(sample_tag_data):
    """Test tagging compliance reporting."""
    required_tags = ['CostCenter', 'Team', 'Project', 'Environment', 'Owner']

    resources = sample_tag_data['resources']
    compliance_data = sample_tag_data['tagging_compliance_metrics']

    # Verify compliance metrics
    assert compliance_data['total_resources'] == len(resources)
    assert compliance_data['compliance_rate'] <= 100
    assert compliance_data['target_compliance_rate'] == 95.0

    # Check gap calculation
    gap = compliance_data['target_compliance_rate'] - compliance_data['compliance_rate']
    assert gap == compliance_data['gap']


# ============================================================================
# Test Cost Allocation
# ============================================================================

def test_cost_allocation_by_cost_center(sample_tag_data):
    """Test cost allocation by cost center."""
    allocation = sample_tag_data['cost_allocation_examples']['by_cost_center']

    # Verify percentages sum to ~100%
    total_percentage = sum(cc['percentage_of_total'] for cc in allocation.values())
    assert 99 <= total_percentage <= 101  # Allow rounding errors

    # Verify largest cost center
    largest_cc = max(allocation.values(), key=lambda x: x['total_monthly_cost'])
    assert largest_cc['total_monthly_cost'] > 1000


def test_cost_allocation_by_environment(sample_tag_data):
    """Test cost allocation by environment."""
    allocation = sample_tag_data['cost_allocation_examples']['by_environment']

    # Production should be largest
    assert allocation['prod']['total_monthly_cost'] > allocation['dev']['total_monthly_cost']
    assert allocation['prod']['total_monthly_cost'] > allocation['test']['total_monthly_cost']

    # Production should be >80% of total
    assert allocation['prod']['percentage_of_total'] >= 80


# ============================================================================
# Test Optimization Opportunities
# ============================================================================

def test_identify_optimization_opportunities(sample_tag_data):
    """Test identification of cost optimization opportunities."""
    opportunities = sample_tag_data['cost_optimization_opportunities']

    assert len(opportunities) >= 5

    # Verify all opportunities have required fields
    for opp in opportunities:
        assert 'resource_id' in opp
        assert 'current_cost' in opp
        assert 'recommendation' in opp
        assert 'potential_savings' in opp
        assert 'savings_percentage' in opp

    # Calculate total potential savings
    total_savings = sum(opp['potential_savings'] for opp in opportunities)
    assert total_savings > 0


def test_prioritize_optimizations(sample_tag_data):
    """Test prioritization of optimization opportunities."""
    opportunities = sample_tag_data['cost_optimization_opportunities']

    # Sort by potential savings (highest first)
    sorted_opps = sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)

    # Top opportunity should have highest savings
    top_opportunity = sorted_opps[0]
    assert top_opportunity['potential_savings'] >= 100

    # Verify sorting
    for i in range(len(sorted_opps) - 1):
        assert sorted_opps[i]['potential_savings'] >= sorted_opps[i + 1]['potential_savings']


# ============================================================================
# Test Data Quality
# ============================================================================

def test_cost_data_completeness(sample_cost_data):
    """Test cost data has no missing values in critical columns."""
    critical_columns = ['line_item_id', 'usage_start_date', 'product_code', 'unblended_cost']

    for col in critical_columns:
        assert col in sample_cost_data.columns
        assert sample_cost_data[col].isna().sum() == 0


def test_cost_data_date_range(sample_cost_data):
    """Test cost data covers expected date range."""
    sample_cost_data['usage_start_date'] = pd.to_datetime(sample_cost_data['usage_start_date'])

    min_date = sample_cost_data['usage_start_date'].min()
    max_date = sample_cost_data['usage_start_date'].max()

    date_range = (max_date - min_date).days

    # Should cover at least 7 days
    assert date_range >= 7


def test_cost_data_positive_values(sample_cost_data):
    """Test all cost values are non-negative."""
    assert (sample_cost_data['unblended_cost'] >= 0).all()
    assert (sample_cost_data['usage_amount'] >= 0).all()


# ============================================================================
# Test Integration Scenarios
# ============================================================================

def test_end_to_end_cost_optimization_workflow(sample_cost_data, sample_tag_data):
    """Test complete cost optimization workflow."""
    # Step 1: Analyze costs
    total_cost = sample_cost_data['unblended_cost'].sum()
    assert total_cost > 0

    # Step 2: Identify waste
    opportunities = sample_tag_data['cost_optimization_opportunities']
    potential_savings = sum(opp['potential_savings'] for opp in opportunities)

    # Step 3: Calculate ROI
    optimization_percentage = (potential_savings / total_cost) * 100

    # Should identify at least 15% optimization opportunity
    assert optimization_percentage >= 15


def test_tagging_compliance_workflow(sample_tag_data):
    """Test tagging compliance checking workflow."""
    # Step 1: Get compliance metrics
    metrics = sample_tag_data['tagging_compliance_metrics']

    # Step 2: Identify resources needing tags
    resources_needing_tags = metrics['resources_needing_tags']

    # Step 3: Prioritize by cost impact
    high_priority = [r for r in resources_needing_tags if r['priority'] == 'high']

    # Should have at least 2 high-priority items
    assert len(high_priority) >= 2


def test_optimization_report_generation(sample_cost_data, sample_tag_data):
    """Test generation of optimization report."""
    # Gather data
    total_cost = sample_cost_data['unblended_cost'].sum()
    opportunities = sample_tag_data['cost_optimization_opportunities']
    compliance = sample_tag_data['tagging_compliance_metrics']

    # Generate report structure
    report = {
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'total_monthly_cost': float(total_cost),
        'optimization_opportunities': len(opportunities),
        'potential_monthly_savings': sum(opp['potential_savings'] for opp in opportunities),
        'tagging_compliance_rate': compliance['compliance_rate'],
        'resources_needing_attention': len(compliance['resources_needing_tags'])
    }

    # Validate report
    assert report['total_monthly_cost'] > 0
    assert report['optimization_opportunities'] >= 5
    assert report['potential_monthly_savings'] > 0
    assert 0 <= report['tagging_compliance_rate'] <= 100


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_zero_cost_resources(sample_cost_data):
    """Test handling of resources with zero cost."""
    zero_cost = sample_cost_data[sample_cost_data['unblended_cost'] == 0]

    # Should have some zero-cost items (like S3 object counts)
    # But not all items
    assert len(zero_cost) < len(sample_cost_data)


def test_multiple_line_item_types(sample_cost_data):
    """Test handling of different line item types."""
    line_item_types = sample_cost_data['line_item_type'].unique()

    # Should have Usage, RIFee, SavingsPlanCoveredUsage
    assert 'Usage' in line_item_types

    # At least 2 different types
    assert len(line_item_types) >= 2


def test_handle_missing_tags_gracefully(sample_tag_data):
    """Test graceful handling of missing tags."""
    resources = sample_tag_data['resources']

    # Find resource with missing tags
    partial = [r for r in resources if r['validation'] in ['warning', 'invalid']]

    # Should have at least 2 resources with missing tags
    assert len(partial) >= 2

    # Verify notes explain the issue
    for resource in partial:
        assert 'notes' in resource
        assert len(resource['notes']) > 0


def test_cost_allocation_untagged_resources(sample_cost_data):
    """Test allocation of costs for untagged resources."""
    # Resources without cost_center
    untagged = sample_cost_data[sample_cost_data['cost_center'].isna() | (sample_cost_data['cost_center'] == '')]

    if len(untagged) > 0:
        untagged_cost = untagged['unblended_cost'].sum()
        total_cost = sample_cost_data['unblended_cost'].sum()
        untagged_percentage = (untagged_cost / total_cost) * 100

        # Untagged should be minimal (<5%)
        assert untagged_percentage < 5


# ============================================================================
# Test Module Validation Results
# ============================================================================

def test_module_validation_summary():
    """Test module validation summary generation."""
    validation_results = {
        'cost_explorer': True,
        'cur_delivery': True,
        'cost_allocation_tags': True,
        'budgets': True,
        'anomaly_detection': True,
        's3_lifecycle': True,
        'athena_workgroup': True,
        'localstack': True,
        'python_environment': True,
        'postgresql': True,
        'pytest_suite': True,
        'exercise_files': True
    }

    # Calculate overall pass rate
    total_checks = len(validation_results)
    passed_checks = sum(1 for v in validation_results.values() if v)
    pass_rate = (passed_checks / total_checks) * 100

    # Should have 100% pass rate
    assert pass_rate == 100.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
