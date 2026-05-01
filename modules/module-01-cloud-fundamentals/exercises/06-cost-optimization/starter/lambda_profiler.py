#!/usr/bin/env python3
"""
Lambda Performance Profiler - Analyze Lambda execution and suggest right-sizing
"""

import boto3
from datetime import datetime, timedelta

lambda_client = boto3.client('lambda')
logs = boto3.client('logs')
cloudwatch = boto3.client('cloudwatch')

def get_lambda_functions():
    """
    List all Lambda functions

    TODO: Get function list with memory configuration
    """

    functions = []

    # TODO: List functions
    # paginator = lambda_client.get_paginator('list_functions')
    # for page in paginator.paginate():
    #     functions.extend(page['Functions'])

    return functions


def analyze_function_performance(function_name, days=7):
    """
    Analyze Lambda performance metrics

    TODO: Query CloudWatch metrics:
    - Duration (p50, p95, p99)
    - Memory usage (average, max)
    - Invocation count
    - Error rate
    """

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    metrics = {
        'duration': {},
        'memory': {},
        'invocations': 0,
        'errors': 0
    }

    # TODO: Get CloudWatch metrics
    # response = cloudwatch.get_metric_statistics(
    #     Namespace='AWS/Lambda',
    #     MetricName='Duration',
    #     Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
    #     StartTime=start_time,
    #     EndTime=end_time,
    #     Period=86400,
    #     Statistics=['Average', 'Maximum']
    # )

    return metrics


def calculate_cost(memory_mb, duration_ms, invocations):
    """
    Calculate Lambda cost

    Formula:
    Cost = invocations × (memory/1024) × (duration/1000) × $0.0000166667
    """

    # TODO: Implement cost calculation

    return 0


def recommend_memory(current_memory, avg_memory_used):
    """
    Recommend optimal memory configuration

    Rule: Set memory to avg_used + 20% buffer
    Must be multiple of 64MB between 128MB and 10GB
    """

    # TODO: Calculate recommendation

    recommended = current_memory

    return recommended


def main():
    # TODO: Get all Lambda functions
    functions = get_lambda_functions()

    print("=== Lambda Performance Analysis ===\n")
    print(f"Analyzing {len(functions)} functions...\n")

    total_current_cost = 0
    total_optimized_cost = 0

    # TODO: For each function:
    # 1. Analyze performance
    # 2. Calculate current cost
    # 3. Recommend memory
    # 4. Calculate optimized cost
    # 5. Print report

    print("\n=== Summary ===")
    print(f"Current monthly cost: ${total_current_cost:.2f}")
    print(f"Optimized monthly cost: ${total_optimized_cost:.2f}")
    print(f"Savings: ${total_current_cost - total_optimized_cost:.2f} ({(total_current_cost - total_optimized_cost) / total_current_cost * 100:.1f}%)")


if __name__ == '__main__':
    main()
