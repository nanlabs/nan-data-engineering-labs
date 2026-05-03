# Exercise 05: Serverless Cost Analysis

⏱️ **Estimated Time:** 2.5 hours
🎯 **Difficulty:** ⭐⭐⭐⭐ Advanced
💰 **Potential Impact:** 30-80% savings (workload dependent)

## Learning Objectives

- Compare Lambda vs EC2 total cost of ownership (TCO)
- Analyze Fargate vs ECS on EC2 cost trade-offs
- Calculate Athena vs EMR query costs
- Optimize Lambda memory allocation for cost/performance
- Build serverless vs traditional TCO calculator

## Serverless Pricing Models

| Service | Pricing Model | Break-Even Point | Best For |
|---------|---------------|------------------|----------|
| **Lambda** | $0.20 per 1M requests + $0.0000166667/GB-second | ~300 hours/month runtime | Event-driven, sporadic |
| **Fargate** | $0.04048/vCPU-hour + $0.004445/GB-hour | Always cheaper than 24/7 EC2 | Containers, no mgmt |
| **Athena** | $5 per TB scanned | < 1 TB/day queries | Ad-hoc SQL queries |
| **Step Functions** | $0.025 per 1000 state transitions | Low orchestration | Workflow coordination |

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│            Serverless vs Traditional TCO                   │
│                                                            │
│  Scenario 1: Event Processing (5M events/month)           │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │   EC2 Worker     │   vs    │  Lambda Function │        │
│  │  t3.medium 24/7  │         │  256MB, 200ms    │        │
│  │  $30/month       │         │  $5/month        │        │
│  │  (30% utilized)  │         │  (pay per invoke)│        │
│  └──────────────────┘         └──────────────────┘        │
│      Cheaper for > 15M events/month                       │
│                                                            │
│  Scenario 2: ETL Jobs (2 hours/day)                       │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │   EMR Cluster    │   vs    │  Glue Jobs       │        │
│  │  3x m5.xlarge    │         │  10 DPU          │        │
│  │  $345/month      │         │  $110/month      │        │
│  │  (8% utilized)   │         │  (pay per run)   │        │
│  └──────────────────┘         └──────────────────┘        │
│      Cheaper for > 8 hours/day runtime                    │
└────────────────────────────────────────────────────────────┘
```

## Tasks

### Task 1: Lambda vs EC2 Cost Comparison

**Objective**: Calculate break-even point between Lambda and EC2.

**Steps**:

1. **Build Lambda cost calculator**:

```python
import numpy as np
import pandas as pd

class LambdaCostCalculator:
    """Calculate Lambda costs based on usage patterns"""

    # Lambda pricing (us-east-1)
    REQUEST_PRICE = 0.20 / 1_000_000  # per request
    DURATION_PRICE = 0.0000166667  # per GB-second
    FREE_TIER_REQUESTS = 1_000_000  # per month
    FREE_TIER_GB_SECONDS = 400_000  # per month

    def __init__(self, memory_mb, avg_duration_ms):
        self.memory_gb = memory_mb / 1024
        self.duration_seconds = avg_duration_ms / 1000

    def calculate_monthly_cost(self, monthly_invocations):
        """Calculate Lambda monthly cost"""
        # Requests cost
        billable_requests = max(0, monthly_invocations - self.FREE_TIER_REQUESTS)
        request_cost = billable_requests * self.REQUEST_PRICE

        # Duration cost
        total_gb_seconds = monthly_invocations * self.memory_gb * self.duration_seconds
        billable_gb_seconds = max(0, total_gb_seconds - self.FREE_TIER_GB_SECONDS)
        duration_cost = billable_gb_seconds * self.DURATION_PRICE

        total_cost = request_cost + duration_cost

        return {
            'request_cost': request_cost,
            'duration_cost': duration_cost,
            'total_cost': total_cost,
            'cost_per_invocation': total_cost / monthly_invocations if monthly_invocations > 0 else 0
        }

class EC2WorkerCostCalculator:
    """Calculate EC2 worker cost for equivalent processing"""

    # EC2 pricing (us-east-1, On-Demand)
    PRICING = {
        't3.micro': 0.0104,    # per hour
        't3.small': 0.0208,
        't3.medium': 0.0416,
        't3.large': 0.0832,
        'm5.large': 0.096,
        'm5.xlarge': 0.192
    }

    def __init__(self, instance_type='t3.medium'):
        self.instance_type = instance_type
        self.hourly_rate = self.PRICING.get(instance_type, 0.0416)

    def calculate_monthly_cost(self, utilization_pct=50, hours_per_month=730):
        """
        Calculate EC2 cost

        utilization_pct: How much of the time instance is actively processing
        hours_per_month: How many hours instance runs (730 = 24/7)
        """
        base_cost = self.hourly_rate * hours_per_month

        # If utilization is low, factor in waste
        effective_hours = hours_per_month * (utilization_pct / 100)
        waste_hours = hours_per_month - effective_hours
        waste_cost = waste_hours * self.hourly_rate

        return {
            'base_cost': base_cost,
            'effective_hours': effective_hours,
            'waste_cost': waste_cost,
            'utilization_pct': utilization_pct
        }

def compare_lambda_vs_ec2(monthly_invocations, avg_duration_ms, memory_mb=256):
    """Compare Lambda vs EC2 costs for a workload"""

    # Lambda calculation
    lambda_calc = LambdaCostCalculator(memory_mb, avg_duration_ms)
    lambda_cost = lambda_calc.calculate_monthly_cost(monthly_invocations)

    # EC2 calculation (assume we need t3.medium running 24/7)
    # Calculate utilization based on Lambda runtime
    total_lambda_runtime_hours = (monthly_invocations * avg_duration_ms / 1000) / 3600
    ec2_utilization = (total_lambda_runtime_hours / 730) * 100  # % of month

    ec2_calc = EC2WorkerCostCalculator('t3.medium')
    ec2_cost = ec2_calc.calculate_monthly_cost(ec2_utilization, hours_per_month=730)

    # Comparison
    winner = 'Lambda' if lambda_cost['total_cost'] < ec2_cost['base_cost'] else 'EC2'
    savings = abs(lambda_cost['total_cost'] - ec2_cost['base_cost'])
    savings_pct = (savings / max(lambda_cost['total_cost'], ec2_cost['base_cost'])) * 100

    results = {
        'lambda': lambda_cost,
        'ec2': ec2_cost,
        'winner': winner,
        'savings': savings,
        'savings_pct': savings_pct,
        'ec2_utilization': ec2_utilization
    }

    return results

# Example: API processing workload
print("\n💰 Lambda vs EC2 Cost Comparison:\n")
print("Workload: API request processing")
print("  Invocations: 5,000,000/month")
print("  Avg Duration: 200ms")
print("  Memory: 256MB")
print()

comparison = compare_lambda_vs_ec2(
    monthly_invocations=5_000_000,
    avg_duration_ms=200,
    memory_mb=256
)

print(f"Lambda Cost:")
print(f"  Request Cost: ${comparison['lambda']['request_cost']:.2f}")
print(f"  Duration Cost: ${comparison['lambda']['duration_cost']:.2f}")
print(f"  Total: ${comparison['lambda']['total_cost']:.2f}/month")
print(f"  Per Invocation: ${comparison['lambda']['cost_per_invocation']:.6f}")

print(f"\nEC2 Cost (t3.medium 24/7):")
print(f"  Monthly Cost: ${comparison['ec2']['base_cost']:.2f}")
print(f"  Utilization: {comparison['ec2_utilization']:.1f}%")
print(f"  Waste Cost: ${comparison['ec2']['waste_cost']:.2f} ({100 - comparison['ec2_utilization']:.1f}% idle)")

print(f"\n🏆 Winner: {comparison['winner']}")
print(f"   Savings: ${comparison['savings']:.2f}/month ({comparison['savings_pct']:.1f}%)")

# Break-even analysis
print(f"\n📊 Break-Even Point:")
# Lambda becomes more expensive when runtime exceeds EC2 cost
break_even_invocations = comparison['ec2']['base_cost'] / comparison['lambda']['cost_per_invocation']
print(f"  {break_even_invocations:,.0f} invocations/month")
print(f"  Below this → Lambda cheaper")
print(f"  Above this → EC2 cheaper")
```

### Task 2: Optimize Lambda Memory Allocation

**Objective**: Find optimal memory for cost/performance trade-off.

**Steps**:

1. **Lambda Power Tuning experiment**:

```python
# Simulate Lambda invocations with different memory configurations
memory_configs = [128, 256, 512, 1024, 1536, 2048, 3008]

def benchmark_lambda_memory(function_name, memory_configs):
    """
    Test Lambda function with different memory allocations
    Returns optimal configuration for cost/performance
    """
    lambda_client = boto3.client('lambda')

    results = []

    for memory in memory_configs:
        print(f"\n  Testing {memory}MB configuration...")

        # Update function memory
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            MemorySize=memory
        )

        # Wait for update
        time.sleep(5)

        # Run test invocations
        durations = []
        for i in range(10):
            start = time.time()

            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps({'test': 'data'})
            )

            duration_ms = time.time() - start * 1000
            durations.append(duration_ms)

        avg_duration = np.mean(durations)

        # Calculate cost for 1M invocations
        gb_seconds = memory / 1024 * (avg_duration / 1000)
        duration_cost = gb_seconds * 0.0000166667 * 1_000_000
        request_cost = 0.20  # $0.20 per 1M
        total_cost_per_million = duration_cost + request_cost

        results.append({
            'memory_mb': memory,
            'avg_duration_ms': avg_duration,
            'cost_per_1m': total_cost_per_million,
            'cost_per_invocation': total_cost_per_million / 1_000_000
        })

        print(f"    Avg Duration: {avg_duration:.0f}ms")
        print(f"    Cost per 1M: ${total_cost_per_million:.2f}")

    # Find optimal (lowest cost)
    df = pd.DataFrame(results)
    optimal = df.loc[df['cost_per_1m'].idxmin()]

    print(f"\n🎯 Optimal Configuration:")
    print(f"  Memory: {optimal['memory_mb']:.0f}MB")
    print(f"  Duration: {optimal['avg_duration_ms']:.0f}ms")
    print(f"  Cost per 1M: ${optimal['cost_per_1m']:.2f}")

    # Calculate savings vs default (128MB)
    baseline = df[df['memory_mb'] == 128].iloc[0]
    savings = baseline['cost_per_1m'] - optimal['cost_per_1m']
    savings_pct = (savings / baseline['cost_per_1m']) * 100

    print(f"\n💰 Savings vs 128MB:")
    print(f"  ${savings:.2f} per 1M invocations ({savings_pct:.1f}%)")

    return df

# Note: This requires an existing Lambda function
# results = benchmark_lambda_memory('data-processing-function', memory_configs)
```

2. **Lambda cost optimization guidelines**:

```python
# Common Lambda optimization patterns
OPTIMIZATION_PATTERNS = {
    'cpu_bound': {
        'recommendation': 'Increase memory (more CPU allocated)',
        'sweet_spot': '1536-3008 MB',
        'reasoning': 'More memory = faster execution = lower duration cost'
    },
    'io_bound': {
        'recommendation': 'Lower memory (CPU not bottleneck)',
        'sweet_spot': '256-512 MB',
        'reasoning': 'Waiting on I/O, extra CPU wasted'
    },
    'quick_tasks': {
        'recommendation': 'Minimum memory if < 100ms',
        'sweet_spot': '128 MB',
        'reasoning': 'Duration cost minimal for short tasks'
    },
    'parallel_processing': {
        'recommendation': 'Use Step Functions + smaller functions',
        'sweet_spot': '512 MB per function',
        'reasoning': 'Parallel execution cheaper than single large function'
    }
}

def recommend_lambda_memory(workload_type, current_memory, current_duration_ms):
    """Recommend optimal memory based on workload characteristics"""
    pattern = OPTIMIZATION_PATTERNS.get(workload_type, {})

    print(f"\n💡 Lambda Optimization Recommendation:")
    print(f"  Workload Type: {workload_type}")
    print(f"  Current: {current_memory}MB, {current_duration_ms}ms")
    print(f"\n  Recommendation: {pattern.get('recommendation', 'Unknown')}")
    print(f"  Sweet Spot: {pattern.get('sweet_spot', 'Test required')}")
    print(f"  Reasoning: {pattern.get('reasoning', '')}")

# Example
recommend_lambda_memory('cpu_bound', 512, 5000)
```

### Task 2: Fargate vs ECS on EC2 Cost Analysis

**Objective**: Compare container hosting options.

**Steps**:

1. **Calculate Fargate costs**:

```python
class FargateCostCalculator:
    """Calculate AWS Fargate costs"""

    # Fargate pricing (us-east-1, Linux)
    VCPU_HOUR_PRICE = 0.04048
    GB_HOUR_PRICE = 0.004445

    def __init__(self, vcpu, memory_gb):
        self.vcpu = vcpu
        self.memory_gb = memory_gb

    def calculate_cost(self, hours_per_month=730):
        """Calculate monthly Fargate cost"""
        hourly_cost = (self.vcpu * self.VCPU_HOUR_PRICE +
                      self.memory_gb * self.GB_HOUR_PRICE)
        monthly_cost = hourly_cost * hours_per_month

        return {
            'hourly_cost': hourly_cost,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

class ECSonEC2Calculator:
    """Calculate ECS on EC2 costs with bin packing"""

    EC2_PRICING = {
        't3.medium': {'price': 0.0416, 'vcpu': 2, 'memory_gb': 4},
        't3.large': {'price': 0.0832, 'vcpu': 2, 'memory_gb': 8},
        'm5.large': {'price': 0.096, 'vcpu': 2, 'memory_gb': 8},
        'm5.xlarge': {'price': 0.192, 'vcpu': 4, 'memory_gb': 16},
        'm5.2xlarge': {'price': 0.384, 'vcpu': 8, 'memory_gb': 32}
    }

    def __init__(self, instance_type='m5.large'):
        self.instance_type = instance_type
        self.instance_config = self.EC2_PRICING[instance_type]

    def calculate_cost(self, task_vcpu, task_memory_gb, num_tasks, hours_per_month=730):
        """
        Calculate ECS on EC2 cost with bin packing

        Bin packing: How many tasks fit on one instance?
        """
        # Tasks per instance (limited by CPU or memory)
        tasks_by_cpu = self.instance_config['vcpu'] / task_vcpu
        tasks_by_memory = self.instance_config['memory_gb'] / task_memory_gb
        tasks_per_instance = min(tasks_by_cpu, tasks_by_memory)

        # Number of instances needed
        instances_needed = np.ceil(num_tasks / tasks_per_instance)

        # Cost calculation
        hourly_cost = instances_needed * self.instance_config['price']
        monthly_cost = hourly_cost * hours_per_month

        # Utilization
        cpu_utilization = (num_tasks * task_vcpu) / (instances_needed * self.instance_config['vcpu']) * 100
        mem_utilization = (num_tasks * task_memory_gb) / (instances_needed * self.instance_config['memory_gb']) * 100

        return {
            'instances_needed': instances_needed,
            'tasks_per_instance': tasks_per_instance,
            'hourly_cost': hourly_cost,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12,
            'cpu_utilization': cpu_utilization,
            'mem_utilization': mem_utilization
        }

# Compare Fargate vs ECS on EC2
print("\n💰 Fargate vs ECS on EC2 Comparison:\n")
print("Workload: 10 microservices, 0.5 vCPU, 1GB RAM each, 24/7")
print()

# Fargate cost for 10 tasks
fargate_calc = FargateCostCalculator(vcpu=0.5, memory_gb=1)
fargate_total = fargate_calc.calculate_cost(730)
fargate_cost_10_tasks = fargate_total['monthly_cost'] * 10

print(f"Fargate (10 tasks):")
print(f"  Cost per task: ${fargate_total['monthly_cost']:.2f}/month")
print(f"  Total (10 tasks): ${fargate_cost_10_tasks:.2f}/month")

# ECS on EC2 with bin packing
ec2_calc = ECSonEC2Calculator('m5.large')
ecs_cost = ec2_calc.calculate_cost(
    task_vcpu=0.5,
    task_memory_gb=1,
    num_tasks=10,
    hours_per_month=730
)

print(f"\nECS on EC2 (m5.large):")
print(f"  Instances Needed: {ecs_cost['instances_needed']:.0f}")
print(f"  Tasks per Instance: {ecs_cost['tasks_per_instance']:.1f}")
print(f"  CPU Utilization: {ecs_cost['cpu_utilization']:.1f}%")
print(f"  Memory Utilization: {ecs_cost['mem_utilization']:.1f}%")
print(f"  Total Cost: ${ecs_cost['monthly_cost']:.2f}/month")

# Winner
if fargate_cost_10_tasks < ecs_cost['monthly_cost']:
    savings = ecs_cost['monthly_cost'] - fargate_cost_10_tasks
    savings_pct = (savings / ecs_cost['monthly_cost']) * 100
    print(f"\n🏆 Winner: Fargate")
    print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
else:
    savings = fargate_cost_10_tasks - ecs_cost['monthly_cost']
    savings_pct = (savings / fargate_cost_10_tasks) * 100
    print(f"\n🏆 Winner: ECS on EC2")
    print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")

print(f"\n💡 General Rule:")
print(f"   • < 5 tasks OR sporadic → Fargate (no management)")
print(f"   • > 20 tasks 24/7 → ECS on EC2 with Savings Plan (better bin packing)")
print(f"   • Variable workload → Fargate + Auto Scaling")
```

### Task 3: Athena vs EMR Query Cost Analysis

**Objective**: Compare SQL query costs for different patterns.

**Steps**:

```python
class AthenaCostCalculator:
    """Calculate Athena query costs"""

    PRICE_PER_TB_SCANNED = 5.0  # $5 per TB

    def calculate_query_cost(self, data_scanned_gb):
        """Calculate cost for a single query"""
        data_scanned_tb = data_scanned_gb / 1024
        cost = data_scanned_tb * self.PRICE_PER_TB_SCANNED
        return cost

    def calculate_monthly_cost(self, queries_per_month, avg_data_scanned_gb):
        """Calculate monthly Athena cost"""
        cost_per_query = self.calculate_query_cost(avg_data_scanned_gb)
        monthly_cost = cost_per_query * queries_per_month

        return {
            'cost_per_query': cost_per_query,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

class EMRCostCalculator:
    """Calculate EMR cluster costs"""

    # EMR pricing (us-east-1) = EC2 price + EMR price
    INSTANCE_PRICING = {
        'm5.xlarge': {'ec2': 0.192, 'emr': 0.048},  # Total: $0.24/hour
        'm5.2xlarge': {'ec2': 0.384, 'emr': 0.096}  # Total: $0.48/hour
    }

    def __init__(self, instance_type='m5.xlarge', num_nodes=3):
        self.instance_type = instance_type
        self.num_nodes = num_nodes
        self.pricing = self.INSTANCE_PRICING[instance_type]

    def calculate_cost(self, hours_per_month):
        """Calculate EMR cluster cost"""
        hourly_cost = (self.pricing['ec2'] + self.pricing['emr']) * self.num_nodes
        monthly_cost = hourly_cost * hours_per_month

        return {
            'hourly_cost': hourly_cost,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

# Comparison scenarios
print("\n💰 Athena vs EMR Cost Comparison:\n")

scenarios = [
    {
        'name': 'Ad-hoc Analytics',
        'queries_per_month': 500,
        'avg_data_scanned_gb': 100,
        'emr_hours_per_month': 50  # Only run when needed
    },
    {
        'name': 'Regular Reporting',
        'queries_per_month': 5000,
        'avg_data_scanned_gb': 200,
        'emr_hours_per_month': 200  # Daily jobs
    },
    {
        'name': 'Heavy Analytics',
        'queries_per_month': 20000,
        'avg_data_scanned_gb': 500,
        'emr_hours_per_month': 730  # 24/7 cluster
    }
]

athena_calc = AthenaCostCalculator()
emr_calc = EMRCostCalculator('m5.xlarge', num_nodes=3)

for scenario in scenarios:
    print(f"\nScenario: {scenario['name']}")
    print(f"  Queries: {scenario['queries_per_month']:,}/month")
    print(f"  Data Scanned: {scenario['avg_data_scanned_gb']}GB per query")

    # Athena cost
    athena_cost = athena_calc.calculate_monthly_cost(
        scenario['queries_per_month'],
        scenario['avg_data_scanned_gb']
    )

    # EMR cost
    emr_cost = emr_calc.calculate_cost(scenario['emr_hours_per_month'])

    print(f"\n  Athena:")
    print(f"    Cost per Query: ${athena_cost['cost_per_query']:.4f}")
    print(f"    Monthly Cost: ${athena_cost['monthly_cost']:.2f}")

    print(f"\n  EMR (3x m5.xlarge):")
    print(f"    Hours: {scenario['emr_hours_per_month']}/month")
    print(f"    Monthly Cost: ${emr_cost['monthly_cost']:.2f}")

    # Winner
    if athena_cost['monthly_cost'] < emr_cost['monthly_cost']:
        savings = emr_cost['monthly_cost'] - athena_cost['monthly_cost']
        savings_pct = (savings / emr_cost['monthly_cost']) * 100
        print(f"\n  🏆 Winner: Athena (${savings:.2f} savings, {savings_pct:.1f}%)")
    else:
        savings = athena_cost['monthly_cost'] - emr_cost['monthly_cost']
        savings_pct = (savings / athena_cost['monthly_cost']) * 100
        print(f"\n  🏆 Winner: EMR (${savings:.2f} savings, {savings_pct:.1f}%)")

    print(f"  " + "-"*50)

print(f"\n💡 Decision Framework:")
print(f"  • < 1 TB scanned/day → Athena (serverless, no overhead)")
print(f"  • > 5 TB scanned/day → EMR with Spot (better for large volumes)")
print(f"  • Parquet/ORC format → Athena (10x less data scanned)")
```

### Task 3: Build Comprehensive TCO Calculator

**Objective**: Create tool for comparing all serverless options.

**Steps**:

```python
class ServerlessTCOCalculator:
    """
    Comprehensive Total Cost of Ownership calculator
    Compares Serverless vs Traditional for common workloads
    """

    def __init__(self):
        self.results = {}

    def calculate_etl_pipeline_tco(self, daily_runtime_hours, data_volume_gb):
        """
        Compare: AWS Glue vs Spark on EMR

        Typical ETL: Extract → Transform → Load
        """
        # AWS Glue (serverless)
        dpu_hours = daily_runtime_hours * 10  # 10 DPU typical
        glue_hourly_cost = 0.44  # $0.44 per DPU-hour
        glue_monthly_cost = dpu_hours * glue_hourly_cost * 30

        # EMR (managed cluster)
        # 3x m5.xlarge: 1 master + 2 core
        emr_hourly_cost = 0.24 * 3  # $0.24/hour per node (EC2 + EMR)
        emr_monthly_cost = emr_hourly_cost * daily_runtime_hours * 30

        # EMR with Spot (80% discount on task nodes)
        # 1 master + 2 core On-Demand + 4 task Spot
        emr_spot_hourly = (0.24 * 3) + (0.24 * 0.2 * 4)  # 80% discount on spot
        emr_spot_monthly = emr_spot_hourly * daily_runtime_hours * 30

        results = {
            'glue_monthly': glue_monthly_cost,
            'emr_monthly': emr_monthly_cost,
            'emr_spot_monthly': emr_spot_monthly,
            'winner': 'Glue' if glue_monthly_cost < min(emr_monthly_cost, emr_spot_monthly) else 'EMR'
        }

        print(f"\n💰 ETL Pipeline TCO ({daily_runtime_hours}h/day, {data_volume_gb}GB/day):\n")
        print(f"  AWS Glue (10 DPU): ${glue_monthly_cost:.2f}/month")
        print(f"  EMR (3 On-Demand): ${emr_monthly_cost:.2f}/month")
        print(f"  EMR (Spot hybrid): ${emr_spot_monthly:.2f}/month")
        print(f"\n  🏆 Winner: {results['winner']}")

        return results

    def calculate_api_tco(self, requests_per_month, avg_duration_ms):
        """
        Compare: Lambda + API Gateway vs EC2 + ALB
        """
        # Lambda + API Gateway
        lambda_requests_cost = (requests_per_month * 0.20) / 1_000_000
        lambda_duration_cost = (requests_per_month * (256/1024) * (avg_duration_ms/1000) * 0.0000166667)
        apigw_cost = (requests_per_month * 1.0) / 1_000_000  # $1 per million requests
        serverless_monthly = lambda_requests_cost + lambda_duration_cost + apigw_cost

        # EC2 + ALB (2x t3.medium for HA)
        ec2_monthly = 0.0416 * 730 * 2  # 2 instances for redundancy
        alb_monthly = 22.5 + (requests_per_month * 0.008 / 1_000_000)  # $22.5 base + LCU
        traditional_monthly = ec2_monthly + alb_monthly

        print(f"\n💰 API Hosting TCO ({requests_per_month:,} requests/month):\n")
        print(f"  Lambda + API Gateway: ${serverless_monthly:.2f}/month")
        print(f"    • Lambda: ${lambda_requests_cost + lambda_duration_cost:.2f}")
        print(f"    • API Gateway: ${apigw_cost:.2f}")
        print(f"\n  EC2 + ALB: ${traditional_monthly:.2f}/month")
        print(f"    • EC2 (2x t3.medium): ${ec2_monthly:.2f}")
        print(f"    • ALB: ${alb_monthly:.2f}")

        if serverless_monthly < traditional_monthly:
            savings = traditional_monthly - serverless_monthly
            savings_pct = (savings / traditional_monthly) * 100
            print(f"\n  🏆 Winner: Lambda + API Gateway")
            print(f"     Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
        else:
            savings = serverless_monthly - traditional_monthly
            savings_pct = (savings / serverless_monthly) * 100
            print(f"\n  🏆 Winner: EC2 + ALB")
            print(f"     Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")

        return {
            'serverless_monthly': serverless_monthly,
            'traditional_monthly': traditional_monthly
        }

    def calculate_data_processing_tco(self, gb_processed_per_month):
        """
        Compare: Lambda vs Glue vs EMR for data processing
        """
        # Lambda (charged per invocation + duration)
        # Assume 1000 objects, 200ms per object, 512MB
        lambda_invocations = 1000
        lambda_cost = lambda_invocations * (512/1024) * 0.2 * 0.0000166667
        lambda_monthly = lambda_cost * (gb_processed_per_month / 100)  # Scale with volume

        # Glue (10 DPU, 2 hours/day)
        glue_monthly = 0.44 * 10 * 2 * 30  # DPU-hours

        # EMR (3x m5.xlarge, 2 hours/day with Spot)
        emr_hourly = (0.24 * 1) + (0.24 * 2 * 0.2)  # Master + 2 Spot core
        emr_monthly = emr_hourly * 2 * 30

        print(f"\n💰 Data Processing TCO ({gb_processed_per_month}GB/month):\n")
        print(f"  Lambda: ${lambda_monthly:.2f}/month (event-driven)")
        print(f"  Glue: ${glue_monthly:.2f}/month (2h/day, 10 DPU)")
        print(f"  EMR Spot: ${emr_monthly:.2f}/month (2h/day, 3 nodes)")

        winner_cost = min(lambda_monthly, glue_monthly, emr_monthly)
        winner = 'Lambda' if winner_cost == lambda_monthly else ('Glue' if winner_cost == glue_monthly else 'EMR')

        print(f"\n  🏆 Winner: {winner} (${winner_cost:.2f}/month)")

# Run TCO calculations
tco = ServerlessTCOCalculator()

tco.calculate_etl_pipeline_tco(daily_runtime_hours=2, data_volume_gb=500)
tco.calculate_api_tco(requests_per_month=10_000_000, avg_duration_ms=150)
tco.calculate_data_processing_tco(gb_processed_per_month=1000)
```

### Task 4: Optimize Step Functions Costs

**Objective**: Reduce orchestration costs with efficient workflows.

**Steps**:

```python
# Step Functions pricing
STANDARD_WORKFLOW_PRICE = 0.025 / 1000  # per state transition
EXPRESS_WORKFLOW_PRICE = 1.00 / 1_000_000  # per request
EXPRESS_DURATION_PRICE = 0.00001667  # per GB-second

def calculate_step_functions_cost(workflow_type, state_transitions, duration_seconds=5):
    """Calculate Step Functions cost"""

    if workflow_type == 'standard':
        cost = state_transitions * STANDARD_WORKFLOW_PRICE

        print(f"\n💰 Step Functions (Standard Workflow):")
        print(f"  State Transitions: {state_transitions:,}")
        print(f"  Cost: ${cost:.4f}")
        print(f"  Best for: Long-running, durable workflows")

    elif workflow_type == 'express':
        request_cost = state_transitions * EXPRESS_WORKFLOW_PRICE
        duration_cost = (state_transitions * duration_seconds * 0.5) * EXPRESS_DURATION_PRICE  # 0.5 GB
        cost = request_cost + duration_cost

        print(f"\n💰 Step Functions (Express Workflow):")
        print(f"  Executions: {state_transitions:,}")
        print(f"  Request Cost: ${request_cost:.4f}")
        print(f"  Duration Cost: ${duration_cost:.4f}")
        print(f"  Total: ${cost:.4f}")
        print(f"  Best for: High-volume, short-duration (< 5 min)")

    return cost

# Compare workflow types
print("Scenario: 1,000,000 workflow executions/month, 5 states each")

standard_cost = calculate_step_functions_cost('standard', 1_000_000 * 5)
express_cost = calculate_step_functions_cost('express', 1_000_000, duration_seconds=10)

if standard_cost < express_cost:
    print(f"\n🏆 Winner: Standard Workflow (${standard_cost:.2f} vs ${express_cost:.2f})")
else:
    print(f"\n🏆 Winner: Express Workflow (${express_cost:.2f} vs ${standard_cost:.2f})")

# Optimization tip
print(f"\n💡 Optimization:")
print(f"  • Minimize state transitions (combine Lambda calls)")
print(f"  • Use Express for < 5 min workflows")
print(f"  • Use Standard for long-running (hours/days)")
```

## Validation Checklist

- [ ] Calculated Lambda vs EC2 break-even point
- [ ] Optimized Lambda memory allocation (tested 3+ configs)
- [ ] Compared Fargate vs ECS on EC2 (with bin packing analysis)
- [ ] Analyzed Athena query costs vs EMR for your workload
- [ ] Built TCO calculator for at least 2 scenarios
- [ ] Identified workloads suited for serverless migration
- [ ] Calculated projected savings from serverless adoption

## Troubleshooting

**Issue**: Lambda cost higher than expected
- **Solution**: Check memory allocation (over-provisioned?)
- Reduce timeout (avoid paying for idle time)
- Optimize code (reduce duration)
- Consider Provisioned Concurrency cost if enabled

**Issue**: Fargate more expensive than EC2
- **Solution**: Normal for high-density workloads (>10 tasks)
- Consider ECS on EC2 with Savings Plan
- Use Fargate Spot (70% discount, for fault-tolerant)

**Issue**: Athena queries scanning too much data
- **Solution**: Partition data by date
- Convert to Parquet/ORC (10x reduction)
- Use LIMIT and WHERE clauses
- Compress data with Snappy/Gzip

## Key Learnings

✅ **Lambda Break-Even**: ~300 hours/month runtime (vs 24/7 EC2)
✅ **Memory = CPU**: More memory = faster execution = often lower cost
✅ **Fargate Premium**: Pay 20-30% more for zero management
✅ **Athena Efficiency**: 10x cheaper with Parquet vs CSV
✅ **Step Functions**: Express workflows 60x cheaper than Standard for high volume

## Serverless Adoption Decision Matrix

| Workload Characteristic | Serverless Score | Traditional Score |
|-------------------------|------------------|-------------------|
| Sporadic usage (< 30% uptime) | ✅ +5 | ❌ 0 |
| Unpredictable spikes | ✅ +4 | ❌ +1 |
| Event-driven | ✅ +5 | ❌ +1 |
| < 15 min execution time | ✅ +3 | ⭐ +2 |
| Stateless processing | ✅ +4 | ⭐ +2 |
| High-density (>20 tasks 24/7) | ❌ +1 | ✅ +5 |
| Complex networking | ❌ +1 | ✅ +4 |
| > 15 min execution | ❌ 0 | ✅ +4 |

**Score > 20**: Strong serverless candidate
**Score 10-20**: Evaluate based on total cost
**Score < 10**: Traditional likely better

## Real-World TCO Examples

### Example 1: Image Processing API
- **Workload**: 50M API calls/month, 300ms avg duration, 512MB memory
- **Lambda + API Gateway**: $123/month
- **EC2 + ALB** (m5.large 24/7): $95/month
- **Winner**: EC2 (28% cheaper)
- **But**: Lambda requires zero ops, no patching, auto-scales
- **Decision**: Lambda (ops cost > $28/month savings)

### Example 2: Batch ETL (2 hours/day)
- **Workload**: Daily Spark ETL, 500GB data
- **Glue** (10 DPU, 2h/day): $264/month
- **EMR On-Demand** (3x m5.xlarge, 2h/day): $43/month
- **EMR Spot** (same): $15/month
- **Winner**: EMR Spot (94% cheaper than Glue)
- **Decision**: EMR Spot (huge savings, acceptable complexity)

### Example 3: SQL Analytics
- **Workload**: 1000 queries/month, 50GB scanned per query
- **Athena**: $244/month ($5/TB * 50TB total)
- **Redshift** (dc2.large, 1 node 24/7): $180/month
- **Winner**: Redshift (26% cheaper)
- **But**: Athena scans reduce to 5GB with Parquet → $24/month
- **Decision**: Athena + Parquet (90% cheaper than Redshift)

## Serverless Cost Optimization Checklist

### Lambda:
- [ ] Right-size memory (test 128MB to 3008MB)
- [ ] Reduce cold starts (Provisioned Concurrency only if needed)
- [ ] Optimize code (reduce duration)
- [ ] Use ARM architecture (Graviton2, 20% cheaper)
- [ ] Set appropriate timeout (don't pay for hangs)

### Fargate:
- [ ] Use Fargate Spot (70% discount if fault-tolerant)
- [ ] Right-size task definitions (don't over-provision CPU/memory)
- [ ] Consider ECS on EC2 for high-density (>10 tasks 24/7)
- [ ] Use Savings Plans for predictable workloads

### Athena:
- [ ] Partition data by date/category
- [ ] Convert to Parquet/ORC (columnar + compression)
- [ ] Use LIMIT in exploratory queries
- [ ] Compress with Snappy (good balance)
- [ ] Filter early in WHERE clause

### Step Functions:
- [ ] Use Express workflows for < 5 min executions
- [ ] Minimize state transitions (combine steps)
- [ ] Use Map state for parallel processing (single transition)
- [ ] Avoid Catch/Retry on every state (group error handling)

## Next Steps

- **Exercise 06**: Cost governance and automated policies
- **Theory**: FinOps principles and best practices

## Additional Resources

- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [Athena Pricing](https://aws.amazon.com/athena/pricing/)
- [Lambda Power Tuning Tool](https://github.com/alexcasalboni/aws-lambda-power-tuning)
- [Serverless TCO Whitepaper](https://d1.awsstatic.com/whitepapers/aws-lambda-economics.pdf)
