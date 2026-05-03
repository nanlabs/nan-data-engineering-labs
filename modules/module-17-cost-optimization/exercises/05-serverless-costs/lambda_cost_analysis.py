#!/usr/bin/env python3
"""
Lambda Cost Analysis
Compare Lambda vs EC2 TCO and optimize Lambda memory allocation
"""

import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
import time
import json

class LambdaCostCalculator:
    """Calculate Lambda costs based on usage patterns"""

    # Lambda pricing (us-east-1)
    REQUEST_PRICE = 0.20 / 1_000_000  # $0.20 per 1M requests
    DURATION_PRICE = 0.0000166667     # $0.0000166667 per GB-second
    FREE_TIER_REQUESTS = 1_000_000    # per month
    FREE_TIER_GB_SECONDS = 400_000    # per month

    def __init__(self, memory_mb: int, avg_duration_ms: float):
        """
        Initialize calculator

        Args:
            memory_mb: Lambda memory allocation (128-10240 MB)
            avg_duration_ms: Average execution duration in milliseconds
        """
        self.memory_mb = memory_mb
        self.memory_gb = memory_mb / 1024
        self.duration_seconds = avg_duration_ms / 1000

    def calculate_monthly_cost(
        self,
        monthly_invocations: int,
        include_free_tier: bool = True
    ) -> Dict:
        """
        Calculate Lambda monthly cost

        Args:
            monthly_invocations: Number of function invocations per month
            include_free_tier: Whether to apply free tier

        Returns:
            Cost breakdown dict
        """
        # Requests cost
        if include_free_tier:
            billable_requests = max(0, monthly_invocations - self.FREE_TIER_REQUESTS)
        else:
            billable_requests = monthly_invocations

        request_cost = billable_requests * self.REQUEST_PRICE

        # Duration cost
        total_gb_seconds = monthly_invocations * self.memory_gb * self.duration_seconds

        if include_free_tier:
            billable_gb_seconds = max(0, total_gb_seconds - self.FREE_TIER_GB_SECONDS)
        else:
            billable_gb_seconds = total_gb_seconds

        duration_cost = billable_gb_seconds * self.DURATION_PRICE

        total_cost = request_cost + duration_cost

        return {
            'memory_mb': self.memory_mb,
            'duration_ms': self.duration_seconds * 1000,
            'invocations': monthly_invocations,
            'request_cost': request_cost,
            'duration_cost': duration_cost,
            'total_cost': total_cost,
            'cost_per_invocation': total_cost / monthly_invocations if monthly_invocations > 0 else 0,
            'total_gb_seconds': total_gb_seconds
        }

    def calculate_break_even_vs_ec2(
        self,
        ec2_monthly_cost: float,
        cost_per_invocation: float
    ) -> int:
        """
        Calculate break-even invocations where Lambda = EC2 cost

        Args:
            ec2_monthly_cost: Monthly cost of equivalent EC2 instance
            cost_per_invocation: Lambda cost per invocation

        Returns:
            Break-even number of invocations
        """
        if cost_per_invocation == 0:
            return float('inf')

        break_even = ec2_monthly_cost / cost_per_invocation
        return int(break_even)

class EC2WorkerCostCalculator:
    """Calculate EC2 worker cost for equivalent processing"""

    # EC2 pricing (us-east-1, On-Demand)
    PRICING = {
        't3.micro': 0.0104,     # $7.59/month
        't3.small': 0.0208,     # $15.18/month
        't3.medium': 0.0416,    # $30.37/month
        't3.large': 0.0832,     # $60.74/month
        'm5.large': 0.096,      # $70.08/month
        'm5.xlarge': 0.192      # $140.16/month
    }

    def __init__(self, instance_type: str = 't3.medium'):
        """Initialize with instance type"""
        self.instance_type = instance_type
        self.hourly_rate = self.PRICING.get(instance_type, 0.0416)

    def calculate_monthly_cost(
        self,
        utilization_pct: float = 50,
        hours_per_month: int = 730
    ) -> Dict:
        """
        Calculate EC2 monthly cost

        Args:
            utilization_pct: Percentage of time actively processing
            hours_per_month: Hours instance is running (730 = 24/7)

        Returns:
            Cost breakdown dict
        """
        base_cost = self.hourly_rate * hours_per_month
        effective_hours = hours_per_month * (utilization_pct / 100)
        waste_hours = hours_per_month - effective_hours
        waste_cost = waste_hours * self.hourly_rate

        return {
            'instance_type': self.instance_type,
            'hours_per_month': hours_per_month,
            'hourly_rate': self.hourly_rate,
            'base_cost': base_cost,
            'utilization_pct': utilization_pct,
            'effective_hours': effective_hours,
            'waste_hours': waste_hours,
            'waste_cost': waste_cost
        }

class LambdaMemoryOptimizer:
    """Optimize Lambda memory for cost/performance trade-off"""

    MEMORY_CONFIGS = [128, 256, 512, 1024, 1536, 2048, 3008]

    def __init__(self, region: str = 'us-east-1'):
        """Initialize Lambda client"""
        self.lambda_client = boto3.client('lambda', region_name=region)

    def test_memory_configurations(
        self,
        function_name: str,
        test_invocations: int = 10
    ) -> pd.DataFrame:
        """
        Test Lambda with different memory allocations
        Find optimal cost/performance configuration

        Args:
            function_name: Lambda function name
            test_invocations: Number of test invocations per config

        Returns:
            DataFrame with results
        """
        print("\n🧪 Lambda Memory Optimization Test")
        print(f"   Function: {function_name}")
        print(f"   Configurations: {len(self.MEMORY_CONFIGS)}")
        print(f"   Test invocations: {test_invocations} per config\n")

        results = []

        for memory in self.MEMORY_CONFIGS:
            print(f"   Testing {memory}MB...", end=' ')

            try:
                # Update memory
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    MemorySize=memory
                )

                # Wait for update to complete
                time.sleep(3)

                # Run test invocations
                durations = []

                for i in range(test_invocations):
                    start = time.time()

                    response = self.lambda_client.invoke(
                        FunctionName=function_name,
                        InvocationType='RequestResponse',
                        Payload=json.dumps({'test_iteration': i})
                    )

                    # Get billed duration from logs
                    log_result = response.get('LogResult', '')

                    duration_ms = (time.time() - start) * 1000
                    durations.append(duration_ms)

                avg_duration = np.mean(durations)
                p95_duration = np.percentile(durations, 95)

                # Calculate cost for 1M invocations
                calc = LambdaCostCalculator(memory, avg_duration)
                cost_analysis = calc.calculate_monthly_cost(1_000_000, include_free_tier=False)

                results.append({
                    'memory_mb': memory,
                    'avg_duration_ms': avg_duration,
                    'p95_duration_ms': p95_duration,
                    'cost_per_1m': cost_analysis['total_cost'],
                    'cost_per_invocation': cost_analysis['cost_per_invocation']
                })

                print(f"avg={avg_duration:.0f}ms, cost=${cost_analysis['total_cost']:.2f}/1M")

            except Exception as e:
                print(f"❌ Error: {e}")

        df = pd.DataFrame(results)

        if not df.empty:
            # Find optimal configuration
            optimal_idx = df['cost_per_1m'].idxmin()
            optimal = df.loc[optimal_idx]

            print("\n✅ Test Complete!")
            print("\n🎯 Optimal Configuration:")
            print(f"   Memory: {optimal['memory_mb']:.0f}MB")
            print(f"   Avg Duration: {optimal['avg_duration_ms']:.0f}ms")
            print(f"   Cost per 1M: ${optimal['cost_per_1m']:.2f}")

            # Compare to baseline (128MB)
            baseline = df[df['memory_mb'] == 128].iloc[0]
            savings = baseline['cost_per_1m'] - optimal['cost_per_1m']
            savings_pct = (savings / baseline['cost_per_1m']) * 100 if baseline['cost_per_1m'] > 0 else 0

            if savings > 0:
                print("\n💰 Savings vs 128MB:")
                print(f"   ${savings:.2f} per 1M invocations ({savings_pct:.1f}%)")

            # Save results
            df.to_csv(f'lambda-memory-optimization-{function_name}.csv', index=False)
            print(f"\n📁 Saved: lambda-memory-optimization-{function_name}.csv")

        return df

def compare_lambda_vs_ec2(
    monthly_invocations: int,
    avg_duration_ms: float,
    memory_mb: int = 256,
    ec2_instance_type: str = 't3.medium'
) -> Dict:
    """
    Compare Lambda vs EC2 total cost of ownership

    Args:
        monthly_invocations: Number of Lambda invocations per month
        avg_duration_ms: Average Lambda execution time
        memory_mb: Lambda memory allocation
        ec2_instance_type: Equivalent EC2 instance type

    Returns:
        Comparison results dict
    """
    print("\n💰 Lambda vs EC2 Cost Comparison")
    print("=" * 60)

    # Lambda costs
    lambda_calc = LambdaCostCalculator(memory_mb, avg_duration_ms)
    lambda_cost = lambda_calc.calculate_monthly_cost(monthly_invocations)

    # Calculate Lambda total runtime
    total_runtime_hours = (monthly_invocations * avg_duration_ms / 1000) / 3600
    ec2_utilization = (total_runtime_hours / 730) * 100

    # EC2 costs (24/7)
    ec2_calc = EC2WorkerCostCalculator(ec2_instance_type)
    ec2_cost = ec2_calc.calculate_monthly_cost(ec2_utilization, hours_per_month=730)

    print("\n📊 Workload:")
    print(f"   Invocations: {monthly_invocations:,}/month")
    print(f"   Avg Duration: {avg_duration_ms:.0f}ms")
    print(f"   Memory: {memory_mb}MB")
    print(f"   Total Runtime: {total_runtime_hours:.1f} hours/month")

    print("\n💵 Lambda Cost:")
    print(f"   Request Cost: ${lambda_cost['request_cost']:.2f}")
    print(f"   Duration Cost: ${lambda_cost['duration_cost']:.2f}")
    print(f"   Total: ${lambda_cost['total_cost']:.2f}/month")
    print(f"   Cost per Invocation: ${lambda_cost['cost_per_invocation']:.6f}")

    print(f"\n💵 EC2 Cost ({ec2_instance_type}, 24/7):")
    print(f"   Monthly Cost: ${ec2_cost['base_cost']:.2f}")
    print(f"   Utilization: {ec2_utilization:.1f}%")
    print(f"   Waste: ${ec2_cost['waste_cost']:.2f} ({100 - ec2_utilization:.1f}% idle time)")

    # Determine winner
    if lambda_cost['total_cost'] < ec2_cost['base_cost']:
        winner = 'Lambda'
        savings = ec2_cost['base_cost'] - lambda_cost['total_cost']
        savings_pct = (savings / ec2_cost['base_cost']) * 100

        print("\n🏆 Winner: Lambda")
        print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
        print(f"   Annual: ${savings * 12:.2f}")
    else:
        winner = 'EC2'
        savings = lambda_cost['total_cost'] - ec2_cost['base_cost']
        savings_pct = (savings / lambda_cost['total_cost']) * 100

        print("\n🏆 Winner: EC2")
        print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
        print(f"   Annual: ${savings * 12:.2f}")

    # Break-even analysis
    break_even = lambda_calc.calculate_break_even_vs_ec2(
        ec2_cost['base_cost'],
        lambda_cost['cost_per_invocation']
    )

    print("\n📊 Break-Even Point:")
    print(f"   {break_even:,} invocations/month")

    if monthly_invocations < break_even:
        print(f"   Current: {monthly_invocations:,} (below break-even → Lambda cheaper)")
    else:
        print(f"   Current: {monthly_invocations:,} (above break-even → EC2 cheaper)")

    # Runtime break-even
    runtime_break_even_hours = 300  # Typical Lambda break-even
    print(f"\n   Runtime Break-Even: ~{runtime_break_even_hours} hours/month")
    print(f"   Current Runtime: {total_runtime_hours:.1f} hours/month")

    return {
        'lambda_cost': lambda_cost['total_cost'],
        'ec2_cost': ec2_cost['base_cost'],
        'winner': winner,
        'savings': savings,
        'savings_pct': savings_pct,
        'break_even_invocations': break_even,
        'ec2_utilization': ec2_utilization
    }

class LambdaAnalyzer:
    """Analyze Lambda function costs and performance"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)

    def analyze_function_costs(self, function_name: str, days: int = 30) -> Dict:
        """
        Analyze Lambda function costs from CloudWatch metrics

        Args:
            function_name: Lambda function name
            days: Number of days to analyze

        Returns:
            Cost analysis dict
        """
        print(f"\n📊 Analyzing Lambda function: {function_name}")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Get invocations
        invocations_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # Daily
            Statistics=['Sum']
        )

        # Get duration
        duration_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Average']
        )

        if not invocations_response['Datapoints'] or not duration_response['Datapoints']:
            print(f"   ⚠️  No metrics available for {function_name}")
            return {}

        # Calculate totals
        total_invocations = sum(dp['Sum'] for dp in invocations_response['Datapoints'])
        avg_duration = np.mean([dp['Average'] for dp in duration_response['Datapoints']])

        # Get function configuration
        func_config = self.lambda_client.get_function_configuration(FunctionName=function_name)
        memory_mb = func_config['MemorySize']

        # Calculate costs
        monthly_invocations = (total_invocations / days) * 30

        calc = LambdaCostCalculator(memory_mb, avg_duration)
        cost_analysis = calc.calculate_monthly_cost(int(monthly_invocations))

        print(f"   Invocations: {monthly_invocations:,.0f}/month")
        print(f"   Avg Duration: {avg_duration:.0f}ms")
        print(f"   Memory: {memory_mb}MB")
        print(f"   Monthly Cost: ${cost_analysis['total_cost']:.2f}")

        return cost_analysis

    def list_expensive_functions(self, min_cost: float = 10.0) -> pd.DataFrame:
        """
        List Lambda functions costing more than threshold

        Args:
            min_cost: Minimum monthly cost threshold

        Returns:
            DataFrame with expensive functions
        """
        print(f"\n🔍 Finding expensive Lambda functions (>${min_cost}/month)...")

        # List all functions
        functions = []
        paginator = self.lambda_client.get_paginator('list_functions')

        for page in paginator.paginate():
            functions.extend(page['Functions'])

        print(f"   Found {len(functions)} functions")

        expensive_functions = []

        for func in functions:
            func_name = func['FunctionName']
            cost_analysis = self.analyze_function_costs(func_name, days=30)

            if cost_analysis and cost_analysis.get('total_cost', 0) >= min_cost:
                expensive_functions.append({
                    'FunctionName': func_name,
                    'Memory': cost_analysis['memory_mb'],
                    'Invocations': cost_analysis['invocations'],
                    'MonthlyCost': cost_analysis['total_cost'],
                    'CostPerInvocation': cost_analysis['cost_per_invocation']
                })

        df = pd.DataFrame(expensive_functions)

        if not df.empty:
            df = df.sort_values('MonthlyCost', ascending=False)
            print(f"\n✅ Found {len(df)} expensive functions:")
            print(df.to_string(index=False))
        else:
            print(f"\n✅ No functions exceed ${min_cost}/month")

        return df

def main():
    """Main Lambda cost analysis workflow"""
    print("=" * 70)
    print("Lambda vs EC2 Cost Analysis")
    print("=" * 70)

    # Scenario 1: Event-driven processing (5M events/month)
    print("\n[Scenario 1] Event-driven API processing")
    comparison1 = compare_lambda_vs_ec2(
        monthly_invocations=5_000_000,
        avg_duration_ms=200,
        memory_mb=256,
        ec2_instance_type='t3.medium'
    )

    # Scenario 2: Batch processing (100K jobs/month)
    print("\n\n[Scenario 2] Batch data processing")
    comparison2 = compare_lambda_vs_ec2(
        monthly_invocations=100_000,
        avg_duration_ms=5000,
        memory_mb=1024,
        ec2_instance_type='t3.large'
    )

    # Scenario 3: Scheduled tasks (daily cron jobs)
    print("\n\n[Scenario 3] Scheduled maintenance tasks")
    comparison3 = compare_lambda_vs_ec2(
        monthly_invocations=30,  # Once per day
        avg_duration_ms=60000,  # 1 minute
        memory_mb=512,
        ec2_instance_type='t3.small'
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ Lambda Cost Analysis Complete!")
    print("=" * 70)

    print("\n💡 Lambda Cost Optimization Tips:")
    print("   1. Right-size memory (test 128MB to 3008MB)")
    print("   2. Reduce execution time (optimize code)")
    print("   3. Use ARM (Graviton2) for 20% discount")
    print("   4. Avoid Provisioned Concurrency unless required")
    print("   5. Set appropriate timeouts (don't pay for hangs)")

    print("\n📊 When to Choose Lambda:")
    print("   ✅ < 300 hours/month total runtime")
    print("   ✅ Sporadic or event-driven workloads")
    print("   ✅ Need automatic scaling")
    print("   ✅ Want zero infrastructure management")

    print("\n📊 When to Choose EC2:")
    print("   ✅ > 300 hours/month total runtime")
    print("   ✅ Steady 24/7 workloads")
    print("   ✅ Need persistent connections")
    print("   ✅ Can leverage Reserved Instances/Savings Plans")

if __name__ == '__main__':
    main()
