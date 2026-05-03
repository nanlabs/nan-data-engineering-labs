#!/usr/bin/env python3
"""
API Gateway and Serverless Service Costs
Analyze API Gateway, Athena, Step Functions, and other serverless cost patterns
"""

from typing import Dict

class APIGatewayCostCalculator:
    """Calculate API Gateway costs"""

    # API Gateway REST pricing (us-east-1)
    PRICE_PER_MILLION_REQUESTS = 1.00  # First 333M requests
    PRICE_PER_MILLION_AFTER = 0.90     # After 333M requests

    # HTTP API pricing (cheaper alternative)
    HTTP_API_PRICE_PER_MILLION = 0.90

    def calculate_rest_api_cost(self, monthly_requests: int) -> Dict:
        """Calculate REST API Gateway cost"""

        if monthly_requests <= 333_000_000:
            cost = (monthly_requests / 1_000_000) * self.PRICE_PER_MILLION_REQUESTS
        else:
            first_tier = (333_000_000 / 1_000_000) * self.PRICE_PER_MILLION_REQUESTS
            remaining = ((monthly_requests - 333_000_000) / 1_000_000) * self.PRICE_PER_MILLION_AFTER
            cost = first_tier + remaining

        return {
            'api_type': 'REST API',
            'requests': monthly_requests,
            'monthly_cost': cost,
            'cost_per_request': cost / monthly_requests if monthly_requests > 0 else 0
        }

    def calculate_http_api_cost(self, monthly_requests: int) -> Dict:
        """Calculate HTTP API Gateway cost (cheaper alternative)"""
        cost = (monthly_requests / 1_000_000) * self.HTTP_API_PRICE_PER_MILLION

        return {
            'api_type': 'HTTP API',
            'requests': monthly_requests,
            'monthly_cost': cost,
            'cost_per_request': cost / monthly_requests if monthly_requests > 0 else 0
        }

class AthenaCostCalculator:
    """Calculate Amazon Athena query costs"""

    PRICE_PER_TB_SCANNED = 5.0  # $5 per TB scanned

    def calculate_query_cost(self, data_scanned_gb: float) -> float:
        """
        Calculate cost for a single query

        Args:
            data_scanned_gb: Data scanned in GB

        Returns:
            Query cost in dollars
        """
        data_scanned_tb = data_scanned_gb / 1024
        cost = data_scanned_tb * self.PRICE_PER_TB_SCANNED
        return cost

    def calculate_monthly_cost(
        self,
        queries_per_month: int,
        avg_data_scanned_gb: float
    ) -> Dict:
        """
        Calculate monthly Athena cost

        Args:
            queries_per_month: Number of queries per month
            avg_data_scanned_gb: Average data scanned per query

        Returns:
            Cost analysis dict
        """
        cost_per_query = self.calculate_query_cost(avg_data_scanned_gb)
        monthly_cost = cost_per_query * queries_per_month
        total_tb_scanned = (queries_per_month * avg_data_scanned_gb) / 1024

        return {
            'queries_per_month': queries_per_month,
            'avg_data_scanned_gb': avg_data_scanned_gb,
            'total_tb_scanned': total_tb_scanned,
            'cost_per_query': cost_per_query,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

    def calculate_parquet_savings(
        self,
        queries_per_month: int,
        csv_size_gb: float
    ) -> Dict:
        """
        Calculate savings from converting CSV to Parquet
        Parquet typically 10x smaller and scans only needed columns

        Args:
            queries_per_month: Number of queries
            csv_size_gb: Size of data in CSV format

        Returns:
            Savings analysis dict
        """
        # CSV cost (full scan)
        csv_cost = self.calculate_monthly_cost(queries_per_month, csv_size_gb)

        # Parquet cost (10x reduction + columnar = ~15x less scanned)
        parquet_scanned = csv_size_gb / 15
        parquet_cost = self.calculate_monthly_cost(queries_per_month, parquet_scanned)

        savings = csv_cost['monthly_cost'] - parquet_cost['monthly_cost']
        savings_pct = (savings / csv_cost['monthly_cost']) * 100 if csv_cost['monthly_cost'] > 0 else 0

        return {
            'csv_monthly_cost': csv_cost['monthly_cost'],
            'parquet_monthly_cost': parquet_cost['monthly_cost'],
            'monthly_savings': savings,
            'savings_pct': savings_pct,
            'annual_savings': savings * 12,
            'data_reduction': csv_size_gb / parquet_scanned
        }

class EMRCostCalculator:
    """Calculate EMR cluster costs for comparison with Athena"""

    # EMR pricing = EC2 price + EMR price (us-east-1)
    INSTANCE_PRICING = {
        'm5.xlarge': {'ec2_hourly': 0.192, 'emr_hourly': 0.048},   # Total: $0.24/hour
        'm5.2xlarge': {'ec2_hourly': 0.384, 'emr_hourly': 0.096},  # Total: $0.48/hour
        'm5.4xlarge': {'ec2_hourly': 0.768, 'emr_hourly': 0.192}   # Total: $0.96/hour
    }

    def __init__(self, instance_type: str = 'm5.xlarge', num_nodes: int = 3):
        """Initialize EMR calculator"""
        self.instance_type = instance_type
        self.num_nodes = num_nodes
        self.pricing = self.INSTANCE_PRICING.get(instance_type, {})

    def calculate_cost(self, hours_per_month: int) -> Dict:
        """
        Calculate EMR cluster cost

        Args:
            hours_per_month: Hours cluster is running

        Returns:
            Cost analysis dict
        """
        hourly_cost_per_node = self.pricing['ec2_hourly'] + self.pricing['emr_hourly']
        hourly_cost_total = hourly_cost_per_node * self.num_nodes
        monthly_cost = hourly_cost_total * hours_per_month

        return {
            'instance_type': self.instance_type,
            'num_nodes': self.num_nodes,
            'hours_per_month': hours_per_month,
            'hourly_cost': hourly_cost_total,
            'monthly_cost': monthly_cost,
            'annual_cost': monthly_cost * 12
        }

class StepFunctionsCostCalculator:
    """Calculate AWS Step Functions orchestration costs"""

    # Step Functions pricing
    STANDARD_PRICE_PER_TRANSITION = 0.025 / 1000       # $0.025 per 1000 transitions
    EXPRESS_PRICE_PER_REQUEST = 1.00 / 1_000_000      # $1.00 per 1M requests
    EXPRESS_DURATION_PRICE = 0.00001667                # Per GB-second

    def calculate_standard_cost(self, state_transitions: int) -> Dict:
        """Calculate Standard Workflow cost"""
        cost = state_transitions * self.STANDARD_PRICE_PER_TRANSITION

        return {
            'workflow_type': 'Standard',
            'state_transitions': state_transitions,
            'monthly_cost': cost,
            'cost_per_execution': cost / (state_transitions / 5) if state_transitions > 0 else 0  # Assume 5 states per execution
        }

    def calculate_express_cost(
        self,
        executions: int,
        duration_seconds: float = 5,
        memory_gb: float = 0.5
    ) -> Dict:
        """Calculate Express Workflow cost"""
        request_cost = executions * self.EXPRESS_PRICE_PER_REQUEST
        duration_cost = executions * duration_seconds * memory_gb * self.EXPRESS_DURATION_PRICE
        total_cost = request_cost + duration_cost

        return {
            'workflow_type': 'Express',
            'executions': executions,
            'request_cost': request_cost,
            'duration_cost': duration_cost,
            'monthly_cost': total_cost,
            'cost_per_execution': total_cost / executions if executions > 0 else 0
        }

def compare_athena_vs_emr(
    queries_per_month: int,
    avg_data_scanned_gb: float,
    emr_hours_per_month: int,
    emr_instance_type: str = 'm5.xlarge',
    emr_num_nodes: int = 3
) -> Dict:
    """
    Compare Athena serverless queries vs EMR cluster

    Args:
        queries_per_month: Number of queries per month
        avg_data_scanned_gb: Average data scanned per Athena query
        emr_hours_per_month: Hours EMR cluster would run
        emr_instance_type: EMR instance type
        emr_num_nodes: Number of EMR nodes

    Returns:
        Comparison results dict
    """
    print("\n💰 Athena vs EMR Cost Comparison")
    print("=" * 70)

    print("\n📊 Workload:")
    print(f"   Queries: {queries_per_month:,}/month")
    print(f"   Data Scanned (Athena): {avg_data_scanned_gb}GB per query")
    print(f"   EMR Runtime: {emr_hours_per_month} hours/month")

    # Athena cost
    athena_calc = AthenaCostCalculator()
    athena_cost = athena_calc.calculate_monthly_cost(queries_per_month, avg_data_scanned_gb)

    print("\n💵 Athena (Serverless):")
    print(f"   Total Scanned: {athena_cost['total_tb_scanned']:.2f} TB")
    print(f"   Cost per Query: ${athena_cost['cost_per_query']:.4f}")
    print(f"   Monthly Cost: ${athena_cost['monthly_cost']:.2f}")

    # EMR cost
    emr_calc = EMRCostCalculator(emr_instance_type, emr_num_nodes)
    emr_cost = emr_calc.calculate_cost(emr_hours_per_month)

    print(f"\n💵 EMR ({emr_num_nodes}x {emr_instance_type}):")
    print(f"   Hours: {emr_hours_per_month}/month ({emr_hours_per_month/730*100:.0f}%)")
    print(f"   Hourly Cost: ${emr_cost['hourly_cost']:.2f}")
    print(f"   Monthly Cost: ${emr_cost['monthly_cost']:.2f}")

    # Determine winner
    if athena_cost['monthly_cost'] < emr_cost['monthly_cost']:
        winner = 'Athena'
        savings = emr_cost['monthly_cost'] - athena_cost['monthly_cost']
        savings_pct = (savings / emr_cost['monthly_cost']) * 100
    else:
        winner = 'EMR'
        savings = athena_cost['monthly_cost'] - emr_cost['monthly_cost']
        savings_pct = (savings / athena_cost['monthly_cost']) * 100

    print(f"\n🏆 Winner: {winner}")
    print(f"   Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")
    print(f"   Annual Savings: ${savings * 12:.2f}")

    # Parquet optimization
    parquet_savings = athena_calc.calculate_parquet_savings(queries_per_month, avg_data_scanned_gb)

    print("\n💡 Athena Optimization Opportunity (CSV → Parquet):")
    print(f"   Current (CSV): ${parquet_savings['csv_monthly_cost']:.2f}/month")
    print(f"   With Parquet: ${parquet_savings['parquet_monthly_cost']:.2f}/month")
    print(f"   Savings: ${parquet_savings['monthly_savings']:.2f}/month ({parquet_savings['savings_pct']:.1f}%)")
    print(f"   Data Reduction: {parquet_savings['data_reduction']:.1f}x")

    return {
        'athena_monthly': athena_cost['monthly_cost'],
        'emr_monthly': emr_cost['monthly_cost'],
        'winner': winner,
        'savings': savings
    }

def analyze_api_gateway_costs(monthly_requests: int):
    """Compare API Gateway REST vs HTTP APIs"""
    print("\n💰 API Gateway Cost Analysis")
    print("=" * 70)

    print(f"\n📊 Workload: {monthly_requests:,} requests/month")

    apigw = APIGatewayCostCalculator()

    # REST API cost
    rest_cost = apigw.calculate_rest_api_cost(monthly_requests)

    print("\n💵 REST API:")
    print(f"   Monthly Cost: ${rest_cost['monthly_cost']:.2f}")
    print(f"   Cost per Request: ${rest_cost['cost_per_request']:.6f}")

    # HTTP API cost
    http_cost = apigw.calculate_http_api_cost(monthly_requests)

    print("\n💵 HTTP API:")
    print(f"   Monthly Cost: ${http_cost['monthly_cost']:.2f}")
    print(f"   Cost per Request: ${http_cost['cost_per_request']:.6f}")

    # Comparison
    savings = rest_cost['monthly_cost'] - http_cost['monthly_cost']
    savings_pct = (savings / rest_cost['monthly_cost']) * 100

    print(f"\n💡 HTTP API Savings: ${savings:.2f}/month ({savings_pct:.1f}%)")

    print("\n📋 Feature Comparison:")
    print("   REST API: Full features (caching, API keys, usage plans)")
    print("   HTTP API: Simpler, faster, ~11% cheaper")
    print("\n   Choose HTTP API unless you need:")
    print("     • API keys and usage plans")
    print("     • Request/response data transformation")
    print("     • Caching layer")

def analyze_step_functions_costs(workflow_executions: int, states_per_execution: int = 5):
    """Compare Step Functions Standard vs Express"""
    print("\n💰 Step Functions Cost Analysis")
    print("=" * 70)

    print(f"\n📊 Workload: {workflow_executions:,} executions/month, {states_per_execution} states each")

    sf_calc = StepFunctionsCostCalculator()

    # Standard workflow
    total_transitions = workflow_executions * states_per_execution
    standard_cost = sf_calc.calculate_standard_cost(total_transitions)

    print("\n💵 Standard Workflow:")
    print(f"   State Transitions: {standard_cost['state_transitions']:,}")
    print(f"   Monthly Cost: ${standard_cost['monthly_cost']:.4f}")
    print(f"   Cost per Execution: ${standard_cost['cost_per_execution']:.6f}")
    print("   Best for: Long-running workflows (hours/days)")

    # Express workflow
    express_cost = sf_calc.calculate_express_cost(workflow_executions, duration_seconds=5, memory_gb=0.5)

    print("\n💵 Express Workflow:")
    print(f"   Executions: {express_cost['executions']:,}")
    print(f"   Request Cost: ${express_cost['request_cost']:.4f}")
    print(f"   Duration Cost: ${express_cost['duration_cost']:.4f}")
    print(f"   Total Cost: ${express_cost['monthly_cost']:.4f}")
    print(f"   Cost per Execution: ${express_cost['cost_per_execution']:.6f}")
    print("   Best for: High-volume, short workflows (< 5 min)")

    # Comparison
    if standard_cost['monthly_cost'] < express_cost['monthly_cost']:
        winner = 'Standard'
        savings = express_cost['monthly_cost'] - standard_cost['monthly_cost']
    else:
        winner = 'Express'
        savings = standard_cost['monthly_cost'] - express_cost['monthly_cost']

    print(f"\n🏆 Winner: {winner} Workflow")
    print(f"   Savings: ${savings:.2f}/month")

    # Express becomes cheaper at high volume
    break_even = 0.025 / (1.00 / 1_000_000)  # When Express request cost = Standard transition cost
    print("\n📊 Break-Even:")
    print(f"   Express cheaper when > {break_even/states_per_execution:,.0f} executions/month")

def main():
    """Main serverless cost analysis workflow"""
    print("=" * 70)
    print("Serverless Cost Analysis - API Gateway, Athena, Step Functions")
    print("=" * 70)

    # Analysis 1: API Gateway
    print("\n[Analysis 1/3] API Gateway Cost Comparison")
    analyze_api_gateway_costs(monthly_requests=10_000_000)

    # Analysis 2: Athena vs EMR
    print("\n\n[Analysis 2/3] Athena vs EMR")

    scenarios = [
        {
            'name': 'Ad-hoc Analytics (light usage)',
            'queries': 500,
            'data_scanned_gb': 100,
            'emr_hours': 50
        },
        {
            'name': 'Regular Reporting (moderate usage)',
            'queries': 5000,
            'data_scanned_gb': 200,
            'emr_hours': 200
        },
        {
            'name': 'Heavy Analytics (intensive usage)',
            'queries': 20000,
            'data_scanned_gb': 500,
            'emr_hours': 730
        }
    ]

    for scenario in scenarios:
        print(f"\n{'─' * 70}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'─' * 70}")

        compare_athena_vs_emr(
            queries_per_month=scenario['queries'],
            avg_data_scanned_gb=scenario['data_scanned_gb'],
            emr_hours_per_month=scenario['emr_hours']
        )

    # Analysis 3: Step Functions
    print("\n\n[Analysis 3/3] Step Functions Workflow Orchestration")
    analyze_step_functions_costs(workflow_executions=1_000_000, states_per_execution=5)

    # Summary
    print("\n" + "=" * 70)
    print("✅ Serverless Cost Analysis Complete!")
    print("=" * 70)

    print("\n💡 Serverless Cost Optimization Summary:")

    print("\n   API Gateway:")
    print("     • Use HTTP API instead of REST (11% cheaper)")
    print("     • Enable caching only if needed ($0.02/hour)")
    print("     • Consider direct Lambda URL for simple APIs (free)")

    print("\n   Athena:")
    print("     • Convert to Parquet/ORC (90% cost reduction)")
    print("     • Partition by date/category")
    print("     • Use LIMIT for exploratory queries")
    print("     • Compress with Snappy")
    print("     • Break-even: < 1 TB scanned/day vs EMR")

    print("\n   Step Functions:")
    print("     • Use Express for high-volume (< 5 min duration)")
    print("     • Minimize state transitions (combine steps)")
    print("     • Use Map state for parallel processing")
    print("     • Standard for long-running (hours/days)")

    print("\n📊 Typical Serverless Savings:")
    print("   • Lambda vs EC2: 50-80% for sporadic workloads")
    print("   • Athena + Parquet vs EMR: 60-90% for ad-hoc queries")
    print("   • Fargate vs EC2: 20-40% for low-density containers")
    print("   • HTTP API vs REST API: 11% on API Gateway costs")

    print("\n⚠️  When NOT to Use Serverless:")
    print("   ❌ Steady 24/7 workloads (> 300h/month runtime)")
    print("   ❌ High-density packing (> 20 tasks per server)")
    print("   ❌ Persistent connections (websockets, long polling)")
    print("   ❌ Large data transfers (bandwidth costs)")

if __name__ == '__main__':
    main()
