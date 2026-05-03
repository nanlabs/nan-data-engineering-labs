#!/usr/bin/env python3
"""
Fargate vs ECS on EC2 Cost Comparison
Compare container hosting options with bin packing analysis
"""

import pandas as pd
import numpy as np
from typing import Dict

class FargateCostCalculator:
    """Calculate AWS Fargate costs"""

    # Fargate pricing (us-east-1, Linux x86)
    VCPU_HOUR_PRICE = 0.04048
    GB_HOUR_PRICE = 0.004445

    # Fargate Spot pricing (70% discount)
    VCPU_HOUR_SPOT = 0.01214
    GB_HOUR_SPOT = 0.001334

    def __init__(self, vcpu: float, memory_gb: float, spot: bool = False):
        """
        Initialize Fargate calculator

        Args:
            vcpu: vCPU allocation (0.25, 0.5, 1, 2, 4, 8, 16)
            memory_gb: Memory allocation (0.5-120 GB, depends on vCPU)
            spot: Use Fargate Spot pricing
        """
        self.vcpu = vcpu
        self.memory_gb = memory_gb
        self.spot = spot

        if spot:
            self.vcpu_price = self.VCPU_HOUR_SPOT
            self.gb_price = self.GB_HOUR_SPOT
        else:
            self.vcpu_price = self.VCPU_HOUR_PRICE
            self.gb_price = self.GB_HOUR_PRICE

    def calculate_cost(self, hours_per_month: int = 730, num_tasks: int = 1) -> Dict:
        """
        Calculate Fargate monthly cost

        Args:
            hours_per_month: Hours tasks run (730 = 24/7)
            num_tasks: Number of concurrent tasks

        Returns:
            Cost breakdown dict
        """
        hourly_cost_per_task = (self.vcpu * self.vcpu_price) + (self.memory_gb * self.gb_price)
        hourly_cost_total = hourly_cost_per_task * num_tasks
        monthly_cost = hourly_cost_total * hours_per_month

        return {
            'vcpu': self.vcpu,
            'memory_gb': self.memory_gb,
            'num_tasks': num_tasks,
            'hours_per_month': hours_per_month,
            'hourly_cost_per_task': hourly_cost_per_task,
            'hourly_cost_total': hourly_cost_total,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12,
            'spot': self.spot
        }

class ECSonEC2Calculator:
    """Calculate ECS on EC2 costs with bin packing optimization"""

    # EC2 instance pricing (us-east-1, On-Demand)
    EC2_PRICING = {
        't3.medium': {'price': 0.0416, 'vcpu': 2, 'memory_gb': 4},
        't3.large': {'price': 0.0832, 'vcpu': 2, 'memory_gb': 8},
        't3.xlarge': {'price': 0.1664, 'vcpu': 4, 'memory_gb': 16},
        'm5.large': {'price': 0.096, 'vcpu': 2, 'memory_gb': 8},
        'm5.xlarge': {'price': 0.192, 'vcpu': 4, 'memory_gb': 16},
        'm5.2xlarge': {'price': 0.384, 'vcpu': 8, 'memory_gb': 32},
        'c5.large': {'price': 0.085, 'vcpu': 2, 'memory_gb': 4},
        'c5.xlarge': {'price': 0.170, 'vcpu': 4, 'memory_gb': 8}
    }

    def __init__(self, instance_type: str = 'm5.large'):
        """Initialize with instance type"""
        self.instance_type = instance_type
        self.instance_config = self.EC2_PRICING.get(instance_type, {})

        if not self.instance_config:
            raise ValueError(f"Unknown instance type: {instance_type}")

    def calculate_bin_packing(
        self,
        task_vcpu: float,
        task_memory_gb: float,
        num_tasks: int
    ) -> Dict:
        """
        Calculate how many tasks fit on instances (bin packing)

        Args:
            task_vcpu: vCPU required per task
            task_memory_gb: Memory required per task
            num_tasks: Total number of tasks to run

        Returns:
            Bin packing analysis dict
        """
        # Reserve 10% for ECS agent overhead
        available_vcpu = self.instance_config['vcpu'] * 0.9
        available_memory = self.instance_config['memory_gb'] * 0.9

        # Tasks per instance (limited by CPU or memory)
        tasks_by_cpu = available_vcpu / task_vcpu
        tasks_by_memory = available_memory / task_memory_gb
        tasks_per_instance = min(tasks_by_cpu, tasks_by_memory)

        # Number of instances needed
        instances_needed = np.ceil(num_tasks / tasks_per_instance)

        # Actual utilization
        actual_tasks = num_tasks
        cpu_utilization = (actual_tasks * task_vcpu) / (instances_needed * available_vcpu) * 100
        mem_utilization = (actual_tasks * task_memory_gb) / (instances_needed * available_memory) * 100

        # Identify bottleneck
        bottleneck = 'CPU' if tasks_by_cpu < tasks_by_memory else 'Memory'

        return {
            'tasks_per_instance': tasks_per_instance,
            'instances_needed': int(instances_needed),
            'cpu_utilization': cpu_utilization,
            'mem_utilization': mem_utilization,
            'bottleneck': bottleneck
        }

    def calculate_cost(
        self,
        task_vcpu: float,
        task_memory_gb: float,
        num_tasks: int,
        hours_per_month: int = 730
    ) -> Dict:
        """
        Calculate ECS on EC2 cost with bin packing

        Args:
            task_vcpu: vCPU per task
            task_memory_gb: Memory per task
            num_tasks: Number of tasks
            hours_per_month: Hours cluster runs

        Returns:
            Cost analysis dict
        """
        # Bin packing calculation
        bin_packing = self.calculate_bin_packing(task_vcpu, task_memory_gb, num_tasks)

        # Cost calculation
        hourly_cost_per_instance = self.instance_config['price']
        hourly_cost_total = hourly_cost_per_instance * bin_packing['instances_needed']
        monthly_cost = hourly_cost_total * hours_per_month

        return {
            'instance_type': self.instance_type,
            'instances_needed': bin_packing['instances_needed'],
            'tasks_per_instance': bin_packing['tasks_per_instance'],
            'cpu_utilization': bin_packing['cpu_utilization'],
            'mem_utilization': bin_packing['mem_utilization'],
            'bottleneck': bin_packing['bottleneck'],
            'hourly_cost': hourly_cost_total,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

def compare_fargate_vs_ecs(
    task_vcpu: float,
    task_memory_gb: float,
    num_tasks: int,
    hours_per_month: int = 730,
    instance_type: str = 'm5.large',
    use_fargate_spot: bool = False
) -> Dict:
    """
    Compare Fargate vs ECS on EC2 for a workload

    Args:
        task_vcpu: vCPU per task
        task_memory_gb: Memory per task
        num_tasks: Number of concurrent tasks
        hours_per_month: Hours running per month
        instance_type: EC2 instance type for ECS
        use_fargate_spot: Use Fargate Spot pricing

    Returns:
        Comparison results dict
    """
    print("\n💰 Fargate vs ECS on EC2 Cost Comparison")
    print("=" * 70)

    print("\n📊 Workload:")
    print(f"   Tasks: {num_tasks}")
    print(f"   vCPU per task: {task_vcpu}")
    print(f"   Memory per task: {task_memory_gb}GB")
    print(f"   Runtime: {hours_per_month} hours/month ({hours_per_month/730*100:.0f}%)")

    # Fargate calculation
    fargate_calc = FargateCostCalculator(task_vcpu, task_memory_gb, spot=use_fargate_spot)
    fargate_cost = fargate_calc.calculate_cost(hours_per_month, num_tasks)

    fargate_type = 'Fargate Spot' if use_fargate_spot else 'Fargate'

    print(f"\n💵 {fargate_type} Cost:")
    print(f"   Hourly per Task: ${fargate_cost['hourly_cost_per_task']:.4f}")
    print(f"   Hourly Total ({num_tasks} tasks): ${fargate_cost['hourly_cost_total']:.2f}")
    print(f"   Monthly Total: ${fargate_cost['monthly_cost']:.2f}")

    # ECS on EC2 calculation
    ecs_calc = ECSonEC2Calculator(instance_type)
    ecs_cost = ecs_calc.calculate_cost(task_vcpu, task_memory_gb, num_tasks, hours_per_month)

    print(f"\n💵 ECS on EC2 ({instance_type}) Cost:")
    print(f"   Instances Needed: {ecs_cost['instances_needed']}")
    print(f"   Tasks per Instance: {ecs_cost['tasks_per_instance']:.1f}")
    print(f"   CPU Utilization: {ecs_cost['cpu_utilization']:.1f}%")
    print(f"   Memory Utilization: {ecs_cost['mem_utilization']:.1f}%")
    print(f"   Bottleneck: {ecs_cost['bottleneck']}")
    print(f"   Hourly Total: ${ecs_cost['hourly_cost']:.2f}")
    print(f"   Monthly Total: ${ecs_cost['monthly_cost']:.2f}")

    # Determine winner
    if fargate_cost['monthly_cost'] < ecs_cost['monthly_cost']:
        winner = fargate_type
        savings = ecs_cost['monthly_cost'] - fargate_cost['monthly_cost']
        savings_pct = (savings / ecs_cost['monthly_cost']) * 100
    else:
        winner = f"ECS on EC2 ({instance_type})"
        savings = fargate_cost['monthly_cost'] - ecs_cost['monthly_cost']
        savings_pct = (savings / fargate_cost['monthly_cost']) * 100

    print(f"\n🏆 Winner: {winner}")
    print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
    print(f"   Annual Savings: ${savings * 12:.2f}")

    # Utilization analysis
    if ecs_cost['cpu_utilization'] < 50 or ecs_cost['mem_utilization'] < 50:
        print(f"\n   💡 Low utilization on EC2 ({ecs_cost['cpu_utilization']:.0f}% CPU, {ecs_cost['mem_utilization']:.0f}% memory)")
        print("      Consider Fargate to avoid paying for idle capacity")

    return {
        'fargate_monthly': fargate_cost['monthly_cost'],
        'ecs_monthly': ecs_cost['monthly_cost'],
        'winner': winner,
        'savings': savings,
        'savings_pct': savings_pct
    }

def analyze_multiple_scenarios():
    """Test different workload scenarios"""
    print("\n" + "=" * 70)
    print("Fargate vs ECS on EC2 - Multiple Scenarios")
    print("=" * 70)

    scenarios = [
        {
            'name': 'Low-density Microservices (3 tasks)',
            'task_vcpu': 0.5,
            'task_memory_gb': 1,
            'num_tasks': 3,
            'hours': 730,
            'instance_type': 't3.medium'
        },
        {
            'name': 'Medium-density API (10 tasks)',
            'task_vcpu': 0.5,
            'task_memory_gb': 1,
            'num_tasks': 10,
            'hours': 730,
            'instance_type': 'm5.large'
        },
        {
            'name': 'High-density Workers (30 tasks)',
            'task_vcpu': 0.25,
            'task_memory_gb': 0.5,
            'num_tasks': 30,
            'hours': 730,
            'instance_type': 'm5.2xlarge'
        },
        {
            'name': 'Intermittent Batch (5 tasks, 4h/day)',
            'task_vcpu': 1,
            'task_memory_gb': 2,
            'num_tasks': 5,
            'hours': 120,  # 4 hours/day * 30 days
            'instance_type': 'm5.large'
        }
    ]

    results = []

    for scenario in scenarios:
        print(f"\n{'─' * 70}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'─' * 70}")

        comparison = compare_fargate_vs_ecs(
            task_vcpu=scenario['task_vcpu'],
            task_memory_gb=scenario['task_memory_gb'],
            num_tasks=scenario['num_tasks'],
            hours_per_month=scenario['hours'],
            instance_type=scenario['instance_type']
        )

        results.append({
            'Scenario': scenario['name'],
            'FargateCost': comparison['fargate_monthly'],
            'ECS_EC2_Cost': comparison['ecs_monthly'],
            'Winner': comparison['winner'],
            'Savings': comparison['savings'],
            'SavingsPercent': comparison['savings_pct']
        })

    # Summary table
    df = pd.DataFrame(results)

    print(f"\n{'=' * 70}")
    print("SUMMARY: Fargate vs ECS on EC2")
    print(f"{'=' * 70}\n")
    print(df.to_string(index=False))

    # Save report
    df.to_csv('fargate-vs-ecs-comparison.csv', index=False)
    print("\n📁 Saved: fargate-vs-ecs-comparison.csv")

def main():
    """Main Fargate vs ECS analysis workflow"""
    print("=" * 70)
    print("Fargate vs ECS on EC2 - Cost Analysis")
    print("=" * 70)

    # Run multiple scenario analysis
    analyze_multiple_scenarios()

    # Additional Fargate Spot analysis
    print(f"\n{'=' * 70}")
    print("Fargate Spot Analysis (70% discount)")
    print(f"{'=' * 70}")

    print("\n💰 Fargate Spot vs Fargate (10 tasks, 0.5 vCPU, 1GB):")

    # Regular Fargate
    fargate_regular = FargateCostCalculator(0.5, 1, spot=False)
    regular_cost = fargate_regular.calculate_cost(730, 10)

    # Fargate Spot
    fargate_spot = FargateCostCalculator(0.5, 1, spot=True)
    spot_cost = fargate_spot.calculate_cost(730, 10)

    print(f"\n   Regular Fargate: ${regular_cost['monthly_cost']:.2f}/month")
    print(f"   Fargate Spot: ${spot_cost['monthly_cost']:.2f}/month")

    savings = regular_cost['monthly_cost'] - spot_cost['monthly_cost']
    savings_pct = (savings / regular_cost['monthly_cost']) * 100

    print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")

    print("\n   💡 Fargate Spot Use Cases:")
    print("     ✅ Fault-tolerant batch processing")
    print("     ✅ Background worker queues")
    print("     ✅ Non-critical development/test environments")
    print("     ❌ Production APIs (interruption risk)")
    print("     ❌ Stateful applications")

    # Summary and recommendations
    print(f"\n{'=' * 70}")
    print("✅ Analysis Complete!")
    print(f"{'=' * 70}")

    print("\n💡 Decision Framework:")
    print("\n   Choose Fargate when:")
    print("     • < 5 tasks running 24/7")
    print("     • Intermittent workloads (< 50% uptime)")
    print("     • Zero ops desired (no patching, scaling)")
    print("     • Quick deployments needed")

    print("\n   Choose ECS on EC2 when:")
    print("     • > 10 tasks running 24/7")
    print("     • High bin packing efficiency (>70% utilization)")
    print("     • Can commit to Savings Plans (30-60% discount)")
    print("     • Need GPU or specialized instances")

    print("\n   Choose Fargate Spot when:")
    print("     • Workload is fault-tolerant")
    print("     • Can handle task interruptions")
    print("     • Batch processing acceptable")

    print("\n📊 Typical Savings:")
    print("   • ECS on EC2 + Savings Plan: 40-60% cheaper than Fargate (high density)")
    print("   • Fargate Spot: 70% cheaper than Fargate (if interruption-tolerant)")
    print("   • Fargate: 20-40% cheaper than EC2 (low density, < 5 tasks)")

    print("\n⚠️  Fargate Limitations:")
    print("   • 20GB max ephemeral storage")
    print("   • No SSH access to containers")
    print("   • Limited instance type flexibility")
    print("   • Can't leverage existing EC2 Reserved Instances")

if __name__ == '__main__':
    main()
