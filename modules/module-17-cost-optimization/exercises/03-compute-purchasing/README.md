# Exercise 03: Compute Purchasing Options

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
💰 **Potential Savings:** 30-75% on compute costs

## Learning Objectives

- Analyze Reserved Instance (RI) vs Savings Plans
- Compare compute purchasing options (On-Demand, RI, SP, Spot)
- Calculate ROI for commitment-based discounts
- Implement Spot Instance strategies for EMR
- Build compute cost optimization calculator

## Compute Pricing Comparison

| Option | Discount | Commitment | Flexibility | Use Case |
|--------|----------|------------|-------------|----------|
| **On-Demand** | 0% | None | Full | Spiky workloads |
| **Savings Plans** | 33-72% | 1-3 years | Moderate | Consistent compute |
| **Reserved Instances** | 30-75% | 1-3 years | Limited | Predictable workloads |
| **Spot Instances** | 70-90% | None | Low | Fault-tolerant batch |

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│              Compute Cost Optimization                    │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐     │
│  │ Production  │  │ Development  │  │   Batch     │     │
│  │             │  │              │  │ Processing  │     │
│  │ Reserved    │  │  On-Demand   │  │    Spot     │     │
│  │ Instances   │  │  (schedule)  │  │ Instances   │     │
│  │             │  │              │  │             │     │
│  │ -60% cost   │  │  Full price  │  │ -80% cost   │     │
│  └─────────────┘  └──────────────┘  └─────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │         Compute Savings Plans                    │     │
│  │  $X/hour commitment → 66% discount across:       │     │
│  │  • EC2 (any instance type, any region)          │     │
│  │  • Fargate                                       │     │
│  │  • Lambda                                        │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Analyze RI and Savings Plans Recommendations

**Objective**: Use AWS Cost Explorer to identify savings opportunities.

**Steps**:

1. **Get RI recommendations**:

```python
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce')

# Get Reserved Instance recommendations
response = ce.get_reservation_purchase_recommendation(
    Service='Amazon Elastic Compute Cloud - Compute',
    LookbackPeriodInDays='SIXTY_DAYS',
    TermInYears='ONE_YEAR',
    PaymentOption='NO_UPFRONT'  # or 'PARTIAL_UPFRONT', 'ALL_UPFRONT'
)

print("\n💡 Reserved Instance Recommendations:\n")

for rec in response['Recommendations'][:5]:  # Top 5
    details = rec['RecommendationDetails'][0]
    instance_type = details['InstanceDetails']['EC2InstanceDetails']['InstanceType']

    # Cost comparison
    on_demand_cost = float(rec['RecommendationSummary']['TotalRegionalOnDemandCost'])
    ri_cost = float(rec['RecommendationSummary']['TotalRegionalReservedInstanceCost'])
    savings = on_demand_cost - ri_cost
    savings_pct = (savings / on_demand_cost) * 100

    print(f"  Instance: {instance_type}")
    print(f"    On-Demand Annual Cost: ${on_demand_cost:,.2f}")
    print(f"    RI Annual Cost: ${ri_cost:,.2f}")
    print(f"    Annual Savings: ${savings:,.2f} ({savings_pct:.1f}%)")
    print(f"    Recommended Quantity: {rec['RecommendationSummary']['TotalRecommendedUnits']}")
    print()

total_savings = float(response['Recommendations'][0]['RecommendationSummary']['SavingsPercentage'])
print(f"📊 Total Potential Savings: {total_savings:.1f}%")
```

2. **Get Savings Plans recommendations**:

```python
# Get Savings Plans recommendations
sp_response = ce.get_savings_plans_purchase_recommendation(
    SavingsPlansType='COMPUTE_SP',  # or 'EC2_INSTANCE_SP'
    LookbackPeriodInDays='SIXTY_DAYS',
    TermInYears='ONE_YEAR',
    PaymentOption='NO_UPFRONT'
)

print("\n💡 Savings Plans Recommendations:\n")

for rec in sp_response['SavingsPlansEstimatedCommitmentRecommendation']['SavingsPlansEstimatedCommitmentRecommendationDetails'][:3]:
    hourly_commit = float(rec['HourlyCommitmentToPurchase'])
    estimated_savings = float(rec['EstimatedSavingsAmount'])
    savings_pct = float(rec['EstimatedSavingsPercentage'])

    print(f"  Hourly Commitment: ${hourly_commit:.2f}/hour")
    print(f"    Annual Cost: ${hourly_commit * 24 * 365:,.2f}")
    print(f"    Estimated Annual Savings: ${estimated_savings:,.2f} ({savings_pct:.1f}%)")
    print(f"    ROI: {savings_pct:.1f}%")
    print()
```

### Task 2: Compare Purchase Options (ROI Calculator)

**Objective**: Build calculator to compare all purchasing options.

**Steps**:

```python
import pandas as pd

class ComputePricingCalculator:
    """Calculate costs for different EC2 purchasing options"""

    # Example: m5.large pricing (us-east-1)
    PRICING = {
        'on_demand': 0.096,  # per hour
        'ri_1y_no_upfront': 0.062,  # per hour (35% discount)
        'ri_1y_partial_upfront': 0.059,  # per hour (39% discount) + $330 upfront
        'ri_1y_all_upfront': 0.056,  # per hour (42% discount) + $490 upfront
        'ri_3y_no_upfront': 0.042,  # per hour (56% discount)
        'ri_3y_all_upfront': 0.036,  # per hour (63% discount) + $1,050 upfront
        'spot_avg': 0.029,  # per hour (70% discount, variable)
        'savings_plan_1y': 0.064,  # per hour (33% discount)
        'savings_plan_3y': 0.038,  # per hour (60% discount)
    }

    def __init__(self, instance_type='m5.large', region='us-east-1'):
        self.instance_type = instance_type
        self.region = region

    def calculate_annual_cost(self, option, hours_per_month=730):
        """Calculate annual cost for a purchasing option"""
        hours_per_year = hours_per_month * 12

        if option == 'on_demand':
            return self.PRICING['on_demand'] * hours_per_year

        elif option == 'ri_1y_no_upfront':
            return self.PRICING['ri_1y_no_upfront'] * hours_per_year

        elif option == 'ri_1y_partial_upfront':
            return (self.PRICING['ri_1y_partial_upfront'] * hours_per_year) + 330

        elif option == 'ri_1y_all_upfront':
            return 490  # All upfront

        elif option == 'ri_3y_all_upfront':
            return 1050  # All upfront (divide by 3 for annual)

        elif option == 'spot_avg':
            return self.PRICING['spot_avg'] * hours_per_year

        elif option == 'savings_plan_1y':
            return self.PRICING['savings_plan_1y'] * hours_per_year

        elif option == 'savings_plan_3y':
            return self.PRICING['savings_plan_3y'] * hours_per_year

        return 0

    def compare_all_options(self, hours_per_month=730):
        """Compare all purchasing options"""
        results = []

        on_demand_cost = self.calculate_annual_cost('on_demand', hours_per_month)

        options = [
            'on_demand',
            'ri_1y_no_upfront',
            'ri_1y_partial_upfront',
            'ri_1y_all_upfront',
            'ri_3y_all_upfront',
            'spot_avg',
            'savings_plan_1y',
            'savings_plan_3y'
        ]

        for option in options:
            annual_cost = self.calculate_annual_cost(option, hours_per_month)
            savings = on_demand_cost - annual_cost
            savings_pct = (savings / on_demand_cost) * 100

            results.append({
                'Option': option.replace('_', ' ').title(),
                'Annual Cost': f'${annual_cost:,.2f}',
                'vs On-Demand': f'-${savings:,.2f}',
                'Savings %': f'{savings_pct:.1f}%',
                'Commitment': self._get_commitment(option),
                'Flexibility': self._get_flexibility(option)
            })

        return pd.DataFrame(results)

    def _get_commitment(self, option):
        if 'on_demand' in option or 'spot' in option:
            return 'None'
        elif '1y' in option:
            return '1 Year'
        elif '3y' in option:
            return '3 Years'
        return 'Variable'

    def _get_flexibility(self, option):
        if 'on_demand' in option:
            return 'Full'
        elif 'savings_plan' in option:
            return 'High (any instance)'
        elif 'ri' in option:
            return 'Low (fixed instance)'
        elif 'spot' in option:
            return 'Low (interruptible)'
        return 'Medium'

# Run comparison
calculator = ComputePricingCalculator('m5.large')
comparison = calculator.compare_all_options(hours_per_month=730)

print("\n💰 Compute Pricing Comparison (m5.large, 730 hours/month):\n")
print(comparison.to_string(index=False))
print("\n💡 Recommendation:")
print("  • Steady prod workload → RI 3Y All Upfront (63% savings)")
print("  • Flexible compute → Compute Savings Plan (60% savings)")
print("  • Batch processing → Spot Instances (70% savings)")
```

### Task 3: Implement Spot Instance Strategy for EMR

**Objective**: Run EMR clusters with 70-90% cost savings using Spot.

**Steps**:

1. **Create EMR cluster with Spot Instances**:

```python
emr = boto3.client('emr')

# Best practice: Core nodes on-demand, Task nodes on Spot
cluster_config = {
    'Name': 'cost-optimized-emr',
    'ReleaseLabel': 'emr-6.15.0',
    'Applications': [{'Name': 'Spark'}, {'Name': 'Hadoop'}],
    'Instances': {
        'MasterInstanceGroup': {
            'InstanceType': 'm5.xlarge',
            'InstanceCount': 1,
            'Market': 'ON_DEMAND'  # Master always on-demand for stability
        },
        'CoreInstanceGroup': {
            'InstanceType': 'm5.xlarge',
            'InstanceCount': 2,
            'Market': 'ON_DEMAND'  # Core on-demand for data storage
        },
        'TaskInstanceGroups': [
            {
                'Name': 'task-spot-primary',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 4,
                'Market': 'SPOT',
                'BidPrice': '0.05',  # Max price (on-demand is $0.192)
                'InstanceRole': 'TASK'
            },
            {
                'Name': 'task-spot-diversified',
                'InstanceTypes': ['m5.xlarge', 'm5a.xlarge', 'm4.xlarge'],  # Diversification
                'InstanceCount': 4,
                'Market': 'SPOT',
                'AllocationStrategy': 'capacity-optimized',  # Best for availability
                'InstanceRole': 'TASK'
            }
        ],
        'Ec2SubnetId': 'subnet-xxx',
        'KeepJobFlowAliveWhenNoSteps': False
    },
    'ServiceRole': 'EMR_DefaultRole',
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'VisibleToAllUsers': True,
    'Tags': [
        {'Key': 'CostCenter', 'Value': 'Analytics'},
        {'Key': 'Environment', 'Value': 'Production'}
    ]
}

response = emr.run_job_flow(**cluster_config)
cluster_id = response['JobFlowId']

print(f"✓ EMR cluster created: {cluster_id}")
print("  Master: 1x m5.xlarge On-Demand")
print("  Core: 2x m5.xlarge On-Demand")
print("  Task: 8x m5.xlarge Spot (diversified)")
print("\n💰 Cost Comparison:")
print("  All On-Demand: $0.192 * 11 = $2.11/hour = $1,542/month")
print("  Hybrid (3 On-Demand + 8 Spot): $0.58 + $0.38 = $0.96/hour = $701/month")
print("  Savings: $841/month (54%)")
```

2. **Implement Spot interruption handling**:

```python
# EMR step with checkpoint/retry logic
step = {
    'Name': 'spark-etl-spot-resilient',
    'ActionOnFailure': 'CONTINUE',  # Don't fail cluster on task failure
    'HadoopJarStep': {
        'Jar': 'command-runner.jar',
        'Args': [
            'spark-submit',
            '--deploy-mode', 'cluster',
            '--conf', 'spark.speculation=true',  # Re-run slow tasks
            '--conf', 'spark.dynamicAllocation.enabled=true',  # Scale with spot availability
            '--conf', 'spark.shuffle.service.enabled=true',
            '--conf', 'spark.task.maxFailures=10',  # Retry on spot interruptions
            's3://scripts/etl-job.py'
        ]
    }
}

emr.add_job_flow_steps(
    JobFlowId=cluster_id,
    Steps=[step]
)

print("✓ Spot-resilient Spark job submitted")
print("  Features:")
print("  • Speculative execution (detect slow tasks)")
print("  • Dynamic allocation (adjust to spot availability)")
print("  • Checkpoint to S3 (recover from interruptions)")
print("  • Max 10 retries per task")
```

### Task 2: Calculate ROI for Commitment Purchases

**Objective**: Build financial model to justify RI/SP purchases.

**Steps**:

```python
class CommitmentROICalculator:
    """Calculate ROI for Reserved Instances and Savings Plans"""

    def __init__(self, instance_type='m5.xlarge', hours_per_month=730):
        self.instance_type = instance_type
        self.hours_per_month = hours_per_month

        # m5.xlarge pricing (us-east-1)
        self.on_demand_rate = 0.192

        # RI pricing (1-year)
        self.ri_1y_no_upfront = {'hourly': 0.125, 'upfront': 0}
        self.ri_1y_partial = {'hourly': 0.119, 'upfront': 330}
        self.ri_1y_all = {'hourly': 0.0, 'upfront': 1045}

        # RI pricing (3-year)
        self.ri_3y_no_upfront = {'hourly': 0.083, 'upfront': 0}
        self.ri_3y_partial = {'hourly': 0.079, 'upfront': 550}
        self.ri_3y_all = {'hourly': 0.0, 'upfront': 2073}

        # Savings Plans (more flexible)
        self.sp_1y_rate = 0.128  # 33% discount
        self.sp_3y_rate = 0.077  # 60% discount

    def calculate_option_cost(self, option_name, term_years=1):
        """Calculate total cost for an option"""
        hours = self.hours_per_month * 12 * term_years

        if option_name == 'on_demand':
            return self.on_demand_rate * hours

        elif option_name == 'ri_1y_no_upfront':
            return (self.ri_1y_no_upfront['hourly'] * hours +
                    self.ri_1y_no_upfront['upfront'])

        elif option_name == 'ri_1y_partial':
            return (self.ri_1y_partial['hourly'] * hours +
                    self.ri_1y_partial['upfront'])

        elif option_name == 'ri_1y_all':
            return self.ri_1y_all['upfront']

        elif option_name == 'ri_3y_all':
            return self.ri_3y_all['upfront']

        elif option_name == 'sp_1y':
            return self.sp_1y_rate * hours

        elif option_name == 'sp_3y':
            return self.sp_3y_rate * hours

        return 0

    def calculate_break_even(self, option_name):
        """Calculate break-even point in months"""
        if option_name == 'on_demand':
            return 0

        on_demand_monthly = self.on_demand_rate * self.hours_per_month
        option_cost_1y = self.calculate_option_cost(option_name, term_years=1)
        option_monthly = option_cost_1y / 12

        # If upfront payment, factor that in
        upfront = 0
        if 'partial' in option_name:
            upfront = 330 if '1y' in option_name else 550
        elif 'all' in option_name:
            upfront = 1045 if '1y' in option_name else 2073

        # Break-even when cumulative savings = upfront cost
        if upfront > 0:
            monthly_savings = on_demand_monthly - option_monthly
            break_even_months = upfront / monthly_savings if monthly_savings > 0 else 12
        else:
            break_even_months = 0  # Immediate savings

        return break_even_months

    def compare_all_options(self):
        """Generate comparison table"""
        options = [
            ('on_demand', 'On-Demand'),
            ('ri_1y_no_upfront', 'RI 1Y No Upfront'),
            ('ri_1y_partial', 'RI 1Y Partial'),
            ('ri_1y_all', 'RI 1Y All Upfront'),
            ('ri_3y_all', 'RI 3Y All Upfront'),
            ('sp_1y', 'Savings Plan 1Y'),
            ('sp_3y', 'Savings Plan 3Y')
        ]

        results = []
        on_demand_1y = self.calculate_option_cost('on_demand', 1)

        for option_key, option_label in options:
            term = 3 if '3y' in option_key else 1
            cost = self.calculate_option_cost(option_key, term)
            annual_cost = cost / term
            savings = on_demand_1y - annual_cost
            savings_pct = (savings / on_demand_1y) * 100
            break_even = self.calculate_break_even(option_key)

            results.append({
                'Option': option_label,
                'Annual Cost': f'${annual_cost:,.2f}',
                'Savings': f'${savings:,.2f}',
                'Savings %': f'{savings_pct:.1f}%',
                'Break-Even': f'{break_even:.1f} months' if break_even > 0 else 'Immediate',
                'Flexibility': self._get_flexibility(option_key)
            })

        return pd.DataFrame(results)

    def _get_flexibility(self, option):
        if 'on_demand' in option:
            return '⭐⭐⭐⭐⭐'
        elif 'sp' in option:
            return '⭐⭐⭐⭐'
        elif 'ri' in option:
            return '⭐⭐'
        return '⭐⭐⭐'

# Run comparison
calc = CommitmentROICalculator('m5.xlarge', hours_per_month=730)
comparison = calc.compare_all_options()

print("\n💰 Purchasing Options Comparison (m5.xlarge, 730h/month):\n")
print(comparison.to_string(index=False))

print("\n💡 Decision Framework:")
print("  • Predictable 24/7 workload + 1Y commitment → RI 1Y All Upfront (55% savings)")
print("  • Predictable 24/7 workload + 3Y commitment → RI 3Y All Upfront (76% savings)")
print("  • Flexible compute types → Compute Savings Plan (60% savings)")
print("  • Fault-tolerant batch → Spot Instances (70-90% savings)")
print("  • Variable workload → On-Demand or Savings Plan")
```

### Task 3: Coverage and Utilization Analysis

**Objective**: Monitor RI/SP effectiveness with Cost Explorer.

**Steps**:

```python
# Get RI utilization
ri_utilization = ce.get_reservation_utilization(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='DAILY'
)

print("\n📊 Reserved Instance Utilization (Last 30 Days):\n")

total_hours = 0
used_hours = 0

for day in ri_utilization['UtilizationsByTime']:
    date = day['TimePeriod']['Start']
    util = day['Total']

    purchased = float(util.get('PurchasedHours', 0))
    used = float(util.get('UsedHours', 0))
    utilization_pct = float(util.get('UtilizationPercentage', 0))

    total_hours += purchased
    used_hours += used

    if utilization_pct < 90:
        print(f"  ⚠️  {date}: {utilization_pct:.1f}% utilization")

avg_utilization = (used_hours / total_hours * 100) if total_hours > 0 else 0
print(f"\n  Average Utilization: {avg_utilization:.1f}%")

if avg_utilization < 80:
    print(f"  ⚠️  WARNING: Low utilization → Consider reducing RI count or switching to Savings Plans")
elif avg_utilization > 95:
    print(f"  ✓ Excellent utilization → Consider purchasing more RIs")
else:
    print(f"  ✓ Good utilization → Maintain current strategy")

# Get RI coverage
ri_coverage = ce.get_reservation_coverage(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY'
)

print("\n📊 Reserved Instance Coverage:\n")

for period in ri_coverage['CoveragesByTime']:
    coverage = period['Total']
    covered_pct = float(coverage.get('CoverageHours', {}).get('CoverageHoursPercentage', 0))
    on_demand_cost = float(coverage.get('CoverageCost', {}).get('OnDemandCost', 0))

    print(f"  Coverage: {covered_pct:.1f}%")
    print(f"  On-Demand Cost: ${on_demand_cost:.2f}")

    if covered_pct < 70:
        print(f"  💡 Opportunity: {100 - covered_pct:.1f}% still on On-Demand")
        print(f"     Potential savings: ${on_demand_cost * 0.6:.2f} with RIs")
```

### Task 4: Build Purchase Decision Tool

**Objective**: Automate RI/SP purchase recommendations.

**Steps**:

```python
import numpy as np

def recommend_purchase_strategy(workload_analysis):
    """
    Recommend optimal purchase strategy based on workload characteristics

    workload_analysis = {
        'monthly_cost': 5000,
        'usage_pattern': 'steady|variable|spiky|batch',
        'instance_consistency': 0.8,  # 0-1, same instance types
        'commitment_flexibility': 1-3,  # years willing to commit
        'fault_tolerance': True|False  # can handle Spot interruptions
    }
    """
    monthly_cost = workload_analysis['monthly_cost']
    pattern = workload_analysis['usage_pattern']
    consistency = workload_analysis['instance_consistency']
    commitment = workload_analysis['commitment_flexibility']
    fault_tolerant = workload_analysis.get('fault_tolerance', False)

    recommendations = []

    # Rule 1: Batch workloads → Spot first
    if pattern == 'batch' and fault_tolerant:
        spot_allocation = 0.8  # 80% on Spot
        savings = monthly_cost * spot_allocation * 0.75  # 75% discount

        recommendations.append({
            'strategy': 'Spot Instances (80%) + On-Demand (20%)',
            'allocation': f'${monthly_cost * spot_allocation:.2f} Spot, ${monthly_cost * 0.2:.2f} On-Demand',
            'monthly_savings': savings,
            'annual_savings': savings * 12,
            'risk': 'Medium (interruptions possible)',
            'implementation': 'Use EMR with capacity-optimized strategy'
        })

    # Rule 2: Steady workload + high consistency → RIs
    if pattern == 'steady' and consistency > 0.7:
        discount = 0.63 if commitment >= 3 else 0.42  # 3Y vs 1Y
        savings = monthly_cost * discount

        recommendations.append({
            'strategy': f'Reserved Instances ({commitment}Y)',
            'allocation': f'${monthly_cost:.2f} commitment',
            'monthly_savings': savings,
            'annual_savings': savings * 12,
            'risk': 'Low (predictable)',
            'implementation': f'Purchase {commitment}Y RI All Upfront for max discount'
        })

    # Rule 3: Flexible compute → Savings Plans
    if consistency < 0.7 or pattern == 'variable':
        discount = 0.60 if commitment >= 3 else 0.33  # 3Y vs 1Y
        savings = monthly_cost * discount

        recommendations.append({
            'strategy': f'Compute Savings Plans ({commitment}Y)',
            'allocation': f'${monthly_cost:.2f} hourly commitment',
            'monthly_savings': savings,
            'annual_savings': savings * 12,
            'risk': 'Low (flexible across instances)',
            'implementation': 'Purchase Compute SP for EC2, Fargate, Lambda coverage'
        })

    # Rule 4: Spiky workload → Schedule On-Demand + Savings Plan base
    if pattern == 'spiky':
        base_cost = monthly_cost * 0.6  # 60% baseline
        peak_cost = monthly_cost * 0.4  # 40% On-Demand for peaks
        discount = 0.33
        savings = base_cost * discount

        recommendations.append({
            'strategy': 'Hybrid: Savings Plan (base) + On-Demand (peaks)',
            'allocation': f'${base_cost:.2f} Savings Plan, ${peak_cost:.2f} On-Demand',
            'monthly_savings': savings,
            'annual_savings': savings * 12,
            'risk': 'Low (covered for peaks)',
            'implementation': 'Buy Savings Plan for minimum usage, scale with On-Demand'
        })

    # Sort by savings
    recommendations.sort(key=lambda x: x['annual_savings'], reverse=True)

    return recommendations

# Example: Analyze your workload
workload = {
    'monthly_cost': 5000,
    'usage_pattern': 'steady',  # Change based on your analysis
    'instance_consistency': 0.85,  # 85% m5.xlarge instances
    'commitment_flexibility': 3,  # Willing to commit 3 years
    'fault_tolerance': False
}

recommendations = recommend_purchase_strategy(workload)

print("\n🎯 Purchase Recommendations (ranked by savings):\n")
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec['strategy']}")
    print(f"   Allocation: {rec['allocation']}")
    print(f"   Monthly Savings: ${rec['monthly_savings']:,.2f}")
    print(f"   Annual Savings: ${rec['annual_savings']:,.2f}")
    print(f"   Risk Level: {rec['risk']}")
    print(f"   Implementation: {rec['implementation']}")
    print()
```

### Task 5: Monitor Savings Plans Performance

**Objective**: Track Savings Plans utilization and coverage.

**Steps**:

```python
# Get Savings Plans utilization
sp_utilization = ce.get_savings_plans_utilization(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY'
)

print("\n📊 Savings Plans Utilization:\n")

for period in sp_utilization['SavingsPlansUtilizationsByTime']:
    util = period['Utilization']

    utilization_pct = float(util.get('UtilizationPercentage', 0))
    used_commitment = float(util.get('UsedCommitment', 0))
    total_commitment = float(util.get('TotalCommitment', 0))
    unused = total_commitment - used_commitment

    print(f"  Period: {period['TimePeriod']['Start']} to {period['TimePeriod']['End']}")
    print(f"  Utilization: {utilization_pct:.1f}%")
    print(f"  Used: ${used_commitment:.2f} / ${total_commitment:.2f}")

    if utilization_pct < 80:
        print(f"  ⚠️  Wasted commitment: ${unused:.2f}")
        print(f"     Consider reducing commitment or increasing workload")
    else:
        print(f"  ✓ Good utilization")

# Get Savings Plans coverage
sp_coverage = ce.get_savings_plans_coverage(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY'
)

print("\n📊 Savings Plans Coverage:\n")

for period in sp_coverage['SavingsPlansCoverages']:
    coverage = period.get('Coverage', {})
    spend_covered = float(coverage.get('SpendCoveredBySavingsPlans', 0))
    on_demand_spend = float(coverage.get('OnDemandCost', 0))
    total_spend = spend_covered + on_demand_spend
    coverage_pct = (spend_covered / total_spend * 100) if total_spend > 0 else 0

    print(f"  Coverage: {coverage_pct:.1f}%")
    print(f"  Covered by SP: ${spend_covered:.2f}")
    print(f"  On-Demand: ${on_demand_spend:.2f}")

    if coverage_pct < 70:
        # Opportunity to purchase more
        additional_commitment = on_demand_spend * 0.6  # Cover 60% of on-demand
        potential_savings = additional_commitment * 0.33  # 33% discount

        print(f"\n  💡 Opportunity:")
        print(f"     Increase commitment by ${additional_commitment:.2f}/month")
        print(f"     Potential additional savings: ${potential_savings:.2f}/month")
```

## Validation Checklist

- [ ] Retrieved RI recommendations from Cost Explorer
- [ ] Retrieved Savings Plans recommendations
- [ ] Built ROI calculator comparing all options
- [ ] Calculated break-even point for upfront payments
- [ ] Created Spot Instance EMR cluster with diversification
- [ ] Implemented Spot interruption handling (retries, checkpoints)
- [ ] Monitored RI/SP utilization (aim for >80%)
- [ ] Analyzed coverage (aim for >70% of compute spend)

## Troubleshooting

**Issue**: No RI recommendations returned
- **Solution**: Need at least 60 days of usage history
- Ensure account has EC2 instances running consistently
- Check if already have high RI coverage

**Issue**: Spot Instances frequently interrupted
- **Solution**: Use `capacity-optimized` allocation strategy
- Diversify instance types (m5, m5a, m4)
- Set max spot price at on-demand price
- Implement checkpointing in Spark jobs

**Issue**: Savings Plans utilization < 80%
- **Solution**: Reduce commitment amount
- Consider shorter term (1Y instead of 3Y)
- Increase workload to match commitment

**Issue**: Break-even calculation seems wrong
- **Solution**: Factor in time value of money for upfront payments
- Consider opportunity cost of upfront capital
- Use Net Present Value (NPV) for accurate comparison

## Key Learnings

✅ **Commitment Hierarchy**: 3Y All Upfront (highest discount) → 1Y Partial → No Upfront
✅ **Flexibility Trade-off**: Savings Plans (flexible) vs RIs (locked to instance type)
✅ **Spot Strategies**: Diversification + capacity-optimized = 95%+ availability
✅ **Break-Even**: Upfront RIs break even in 4-6 months with consistent usage
✅ **80/20 Rule**: Cover 70-80% with commitments, leave 20-30% On-Demand for flexibility

## Purchase Strategy Decision Tree

```
Is workload steady (24/7)?
│
├─ YES: Can commit for 1-3 years?
│   │
│   ├─ YES: Same instance type always?
│   │   │
│   │   ├─ YES → Reserved Instances (63% savings)
│   │   │
│   │   └─ NO → Compute Savings Plans (60% savings)
│   │
│   └─ NO → Savings Plans 1Y (33% savings)
│
└─ NO: Is workload fault-tolerant?
    │
    ├─ YES → Spot Instances (70-90% savings)
    │
    └─ NO → On-Demand + Savings Plan for baseline
```

## Real-World ROI Example

**Company**: Mid-sized analytics team
**Compute Spend**: $10,000/month On-Demand
**Workload**: 70% steady (data pipelines), 30% batch (ML training)

**Optimization**:
- 70% covered by Compute Savings Plan 3Y: $7,000 → $2,800/month (60% savings)
- 30% batch moved to Spot: $3,000 → $750/month (75% savings)

**Results**:
- **New Monthly Cost**: $3,550
- **Monthly Savings**: $6,450 (64.5% reduction)
- **Annual Savings**: $77,400
- **Implementation Time**: 2 weeks

## Next Steps

- **Exercise 04**: Right-sizing over-provisioned instances
- **Exercise 05**: Serverless cost analysis (Lambda, Fargate)

## Additional Resources

- [AWS Reserved Instances](https://aws.amazon.com/ec2/pricing/reserved-instances/)
- [AWS Savings Plans](https://aws.amazon.com/savingsplans/)
- [EC2 Spot Instances](https://aws.amazon.com/ec2/spot/)
- [EMR Best Practices with Spot](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-instances-guidelines.html)
