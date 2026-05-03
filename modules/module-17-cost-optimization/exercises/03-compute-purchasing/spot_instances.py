#!/usr/bin/env python3
"""
Spot Instance Strategies
Implement cost-optimized Spot Instance strategies for EMR and batch workloads
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import sys

class SpotInstanceManager:
    """Manage Spot Instance strategies for cost optimization"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.ec2 = boto3.client('ec2', region_name=region)
        self.emr = boto3.client('emr', region_name=region)
        self.pricing = boto3.client('pricing', region_name='us-east-1')
        self.region = region

    def get_spot_price_history(
        self,
        instance_types: List[str],
        days: int = 7
    ) -> Dict:
        """
        Get Spot price history for instance types

        Args:
            instance_types: List of EC2 instance types
            days: Number of days of history

        Returns:
            Dict with price statistics
        """
        print("\n💵 Retrieving Spot price history...")
        print(f"   Instance types: {', '.join(instance_types)}")
        print(f"   Period: Last {days} days")

        start_time = datetime.now() - timedelta(days=days)

        price_history = {}

        for instance_type in instance_types:
            try:
                response = self.ec2.describe_spot_price_history(
                    InstanceTypes=[instance_type],
                    ProductDescriptions=['Linux/UNIX'],
                    StartTime=start_time,
                    MaxResults=1000
                )

                prices = [float(item['SpotPrice']) for item in response['SpotPriceHistory']]

                if prices:
                    price_history[instance_type] = {
                        'current': prices[0],
                        'avg': sum(prices) / len(prices),
                        'min': min(prices),
                        'max': max(prices),
                        'samples': len(prices)
                    }

            except Exception as e:
                print(f"  ⚠️  Could not get price for {instance_type}: {e}")

        # Display results
        if price_history:
            print("\n✅ Spot Price Analysis:\n")
            for instance_type, stats in price_history.items():
                print(f"  {instance_type}:")
                print(f"    Current: ${stats['current']:.4f}/hour")
                print(f"    Average: ${stats['avg']:.4f}/hour")
                print(f"    Range: ${stats['min']:.4f} - ${stats['max']:.4f}")
                print(f"    Samples: {stats['samples']}")

        return price_history

    def calculate_spot_savings(
        self,
        instance_type: str,
        on_demand_price: float,
        spot_price: float,
        hours_per_month: int = 730
    ) -> Dict:
        """
        Calculate savings from using Spot vs On-Demand

        Args:
            instance_type: EC2 instance type
            on_demand_price: On-Demand hourly rate
            spot_price: Average Spot hourly rate
            hours_per_month: Expected monthly usage

        Returns:
            Savings analysis dict
        """
        on_demand_monthly = on_demand_price * hours_per_month
        spot_monthly = spot_price * hours_per_month

        savings = on_demand_monthly - spot_monthly
        savings_pct = (savings / on_demand_monthly) * 100 if on_demand_monthly > 0 else 0

        return {
            'instance_type': instance_type,
            'on_demand_monthly': on_demand_monthly,
            'spot_monthly': spot_monthly,
            'monthly_savings': savings,
            'savings_percentage': savings_pct,
            'annual_savings': savings * 12
        }

    def create_spot_emr_cluster(
        self,
        cluster_name: str,
        master_instance: str = 'm5.xlarge',
        core_instance: str = 'm5.xlarge',
        core_count: int = 2,
        task_instance: str = 'm5.xlarge',
        task_count: int = 4,
        subnet_id: str = None,
        dry_run: bool = False
    ) -> str:
        """
        Create cost-optimized EMR cluster with Spot task nodes

        Args:
            cluster_name: Name for the EMR cluster
            master_instance: Master node instance type
            core_instance: Core node instance type
            core_count: Number of core nodes
            task_instance: Task node instance type
            task_count: Number of task nodes (Spot)
            subnet_id: EC2 subnet ID
            dry_run: If True, only show configuration

        Returns:
            Cluster ID (or config if dry_run)
        """
        print("\n🚀 Creating Spot-optimized EMR cluster...")

        # Get on-demand price for spot bid
        on_demand_price = self.get_on_demand_price(task_instance)
        spot_bid = on_demand_price  # Bid at on-demand price for best availability

        cluster_config = {
            'Name': cluster_name,
            'ReleaseLabel': 'emr-6.15.0',
            'Applications': [
                {'Name': 'Spark'},
                {'Name': 'Hadoop'},
                {'Name': 'Hive'},
                {'Name': 'Ganglia'}
            ],
            'Instances': {
                'InstanceGroups': [
                    {
                        'Name': 'Master',
                        'Market': 'ON_DEMAND',
                        'InstanceRole': 'MASTER',
                        'InstanceType': master_instance,
                        'InstanceCount': 1
                    },
                    {
                        'Name': 'Core',
                        'Market': 'ON_DEMAND',  # Core on-demand for data persistence
                        'InstanceRole': 'CORE',
                        'InstanceType': core_instance,
                        'InstanceCount': core_count
                    },
                    {
                        'Name': 'Task-Spot',
                        'Market': 'SPOT',
                        'InstanceRole': 'TASK',
                        'InstanceType': task_instance,
                        'InstanceCount': task_count,
                        'BidPrice': str(spot_bid)
                    }
                ],
                'KeepJobFlowAliveWhenNoSteps': False,
                'TerminationProtected': False
            },
            'ServiceRole': 'EMR_DefaultRole',
            'JobFlowRole': 'EMR_EC2_DefaultRole',
            'VisibleToAllUsers': True,
            'Tags': [
                {'Key': 'CostOptimization', 'Value': 'Spot'},
                {'Key': 'Environment', 'Value': 'Production'},
                {'Key': 'ManagedBy', 'Value': 'SpotInstanceManager'}
            ],
            'Configurations': [
                {
                    'Classification': 'spark',
                    'Properties': {
                        'maximizeResourceAllocation': 'true'
                    }
                },
                {
                    'Classification': 'spark-defaults',
                    'Properties': {
                        'spark.speculation': 'true',  # Re-run slow tasks
                        'spark.dynamicAllocation.enabled': 'true',
                        'spark.shuffle.service.enabled': 'true',
                        'spark.task.maxFailures': '10'  # Retry on interruptions
                    }
                }
            ]
        }

        if subnet_id:
            cluster_config['Instances']['Ec2SubnetId'] = subnet_id

        if dry_run:
            print("\n[DRY RUN] EMR Cluster Configuration:")
            print(json.dumps(cluster_config, indent=2, default=str))
            return None

        try:
            response = self.emr.run_job_flow(**cluster_config)
            cluster_id = response['JobFlowId']

            print(f"✅ EMR cluster created: {cluster_id}")
            print("\n   Configuration:")
            print(f"     Master: 1x {master_instance} (On-Demand)")
            print(f"     Core: {core_count}x {core_instance} (On-Demand)")
            print(f"     Task: {task_count}x {task_instance} (Spot, bid ${spot_bid:.4f})")

            # Calculate cost savings
            total_on_demand = (
                on_demand_price +  # Master
                on_demand_price * core_count +  # Core
                on_demand_price * task_count  # Task if on-demand
            )

            total_hybrid = (
                on_demand_price +  # Master
                on_demand_price * core_count +  # Core
                spot_bid * 0.3 * task_count  # Task at ~30% of on-demand
            )

            savings_pct = (1 - total_hybrid / total_on_demand) * 100

            print("\n   💰 Cost Comparison:")
            print(f"     All On-Demand: ${total_on_demand:.2f}/hour (${total_on_demand * 730:,.2f}/month)")
            print(f"     Hybrid (Spot tasks): ${total_hybrid:.2f}/hour (${total_hybrid * 730:,.2f}/month)")
            print(f"     Estimated Savings: {savings_pct:.1f}%")

            return cluster_id

        except Exception as e:
            print(f"❌ Error creating cluster: {e}")
            sys.exit(1)

    def get_on_demand_price(self, instance_type: str) -> float:
        """Get On-Demand price for instance type"""
        # Simplified pricing (would use Pricing API in production)
        pricing_map = {
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'm5.4xlarge': 0.768,
            'c5.xlarge': 0.170,
            'c5.2xlarge': 0.340,
            'r5.xlarge': 0.252,
            'r5.2xlarge': 0.504
        }

        return pricing_map.get(instance_type, 0.20)  # Default estimate

    def implement_spot_best_practices(self):
        """Display Spot Instance best practices"""
        print("\n📋 Spot Instance Best Practices:")
        print("\n   1. Diversification:")
        print("      • Use multiple instance types (m5, m5a, m4)")
        print("      • Spread across availability zones")
        print("      • Use capacity-optimized allocation strategy")

        print("\n   2. Interruption Handling:")
        print("      • Enable Spark speculation (re-run slow tasks)")
        print("      • Checkpoint to S3 every 5-10 minutes")
        print("      • Set task retries (maxFailures=10)")
        print("      • Use EMR Managed Scaling")

        print("\n   3. Bidding Strategy:")
        print("      • Bid at On-Demand price for best availability")
        print("      • Don't bid low to save (causes frequent interruptions)")
        print("      • Use capacity-optimized vs lowest-price")

        print("\n   4. Architecture:")
        print("      • Master: Always On-Demand (cluster stability)")
        print("      • Core: On-Demand (data persistence in HDFS)")
        print("      • Task: Spot (processing only, no data storage)")

        print("\n   5. Monitoring:")
        print("      • Track interruption rate (target <5%)")
        print("      • Monitor spot price trends")
        print("      • Set CloudWatch alarms for capacity issues")

def main():
    """Main Spot Instance workflow"""
    print("=" * 70)
    print("Spot Instance Cost Optimization")
    print("=" * 70)

    manager = SpotInstanceManager()

    # Step 1: Analyze Spot prices
    print("\n[Step 1/4] Analyzing Spot prices...")

    instance_types = ['m5.xlarge', 'm5.2xlarge', 'c5.xlarge', 'r5.xlarge']
    price_history = manager.get_spot_price_history(instance_types, days=7)

    # Step 2: Calculate savings
    print("\n[Step 2/4] Calculating potential savings...")

    if price_history:
        print("\n💰 Spot vs On-Demand Savings:\n")

        for instance_type, stats in price_history.items():
            on_demand = manager.get_on_demand_price(instance_type)
            savings_analysis = manager.calculate_spot_savings(
                instance_type=instance_type,
                on_demand_price=on_demand,
                spot_price=stats['avg'],
                hours_per_month=730
            )

            print(f"  {instance_type}:")
            print(f"    On-Demand: ${savings_analysis['on_demand_monthly']:,.2f}/month")
            print(f"    Spot (avg): ${savings_analysis['spot_monthly']:,.2f}/month")
            print(f"    Savings: ${savings_analysis['monthly_savings']:,.2f}/month ({savings_analysis['savings_percentage']:.1f}%)")
            print()

    # Step 3: Best practices guide
    print("\n[Step 3/4] Spot Instance best practices...")
    manager.implement_spot_best_practices()

    # Step 4: Create sample EMR cluster
    print("\n[Step 4/4] EMR cluster creation (dry run)...")

    cluster_id = manager.create_spot_emr_cluster(
        cluster_name='cost-optimized-analytics',
        master_instance='m5.xlarge',
        core_instance='m5.xlarge',
        core_count=2,
        task_instance='m5.xlarge',
        task_count=6,
        dry_run=True  # Set to False to actually create
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ Spot Instance Analysis Complete!")
    print("=" * 70)

    print("\n📊 Key Takeaways:")
    print("   • Spot Instances: 70-90% cheaper than On-Demand")
    print("   • Best for: Batch processing, EMR, containerized workloads")
    print("   • Interruption rate: <5% with capacity-optimized strategy")
    print("   • Diversification: Use 3-5 instance types for resilience")

    print("\n💡 Implementation Steps:")
    print("   1. Start with non-critical batch workloads")
    print("   2. Implement checkpointing and retries")
    print("   3. Monitor interruptions and adjust")
    print("   4. Gradually increase Spot percentage (target 70-80%)")
    print("   5. Keep 20-30% On-Demand for stability")

    print("\n⚠️  When NOT to Use Spot:")
    print("   ❌ Production APIs (latency-sensitive)")
    print("   ❌ Stateful applications (databases with local storage)")
    print("   ❌ Jobs that can't tolerate interruptions")
    print("   ❌ Workloads requiring SLA guarantees")

if __name__ == '__main__':
    main()
