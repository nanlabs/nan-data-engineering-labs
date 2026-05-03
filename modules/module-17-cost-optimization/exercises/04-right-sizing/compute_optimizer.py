#!/usr/bin/env python3
"""
AWS Compute Optimizer Integration
Get AI-powered right-sizing recommendations for EC2, EBS, Lambda, and Auto Scaling
"""

import boto3
import pandas as pd

class ComputeOptimizerAnalyzer:
    """Analyze AWS Compute Optimizer recommendations"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize Compute Optimizer client"""
        self.compute_optimizer = boto3.client('compute-optimizer', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)

    def enable_compute_optimizer(self, include_member_accounts: bool = False):
        """
        Enable AWS Compute Optimizer (requires 30 days of metrics)

        Args:
            include_member_accounts: Enable for organization member accounts
        """
        print("\n🔧 Enabling AWS Compute Optimizer...")

        try:
            response = self.compute_optimizer.update_enrollment_status(
                status='Active',
                includeMemberAccounts=include_member_accounts
            )

            print("✅ Compute Optimizer enabled")
            print(f"   Status: {response.get('status', 'Active')}")
            print("\n   ⏱️  Note: Recommendations available after 30 days of CloudWatch metrics")
            print("   📊 Analysis includes: CPU, memory, network, disk metrics")

        except Exception as e:
            if 'already enrolled' in str(e).lower():
                print("✅ Compute Optimizer already enabled")
            else:
                print(f"❌ Error enabling Compute Optimizer: {e}")
                print("   Ensure you have compute-optimizer:UpdateEnrollmentStatus permission")

    def get_ec2_recommendations(self, max_results: int = 100) -> pd.DataFrame:
        """
        Get EC2 instance right-sizing recommendations

        Args:
            max_results: Maximum recommendations to retrieve

        Returns:
            DataFrame with recommendations
        """
        print("\n💡 Retrieving EC2 recommendations from Compute Optimizer...")

        try:
            response = self.compute_optimizer.get_ec2_instance_recommendations(
                maxResults=max_results
            )
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            print("   Common causes:")
            print("     • Compute Optimizer not enabled (run enable_compute_optimizer())")
            print("     • Less than 30 days of metrics collected")
            print("     • No EC2 instances found")
            return pd.DataFrame()

        recommendations = response.get('instanceRecommendations', [])

        if not recommendations:
            print("✅ No recommendations found (all instances well-sized)")
            return pd.DataFrame()

        print(f"✅ Found {len(recommendations)} recommendations\n")

        # Parse recommendations
        parsed = []

        for rec in recommendations:
            # Extract instance details
            instance_arn = rec['instanceArn']
            instance_id = instance_arn.split('/')[-1]
            current_type = rec['currentInstanceType']
            finding = rec['finding']  # OVER_PROVISIONED, UNDER_PROVISIONED, OPTIMIZED

            # Get utilization metrics
            utilization = rec.get('utilizationMetrics', [])
            cpu_avg = next((float(m['value']) for m in utilization if m['name'] == 'CPU'), 0)
            mem_avg = next((float(m['value']) for m in utilization if m['name'] == 'MEMORY'), 0)
            ebs_read = next((float(m['value']) for m in utilization if m['name'] == 'EBS_READ_OPS_PER_SECOND'), 0)
            ebs_write = next((float(m['value']) for m in utilization if m['name'] == 'EBS_WRITE_OPS_PER_SECOND'), 0)
            network_in = next((float(m['value']) for m in utilization if m['name'] == 'NETWORK_IN_BYTES_PER_SECOND'), 0)
            network_out = next((float(m['value']) for m in utilization if m['name'] == 'NETWORK_OUT_BYTES_PER_SECOND'), 0)

            # Get best recommendation option
            options = rec.get('recommendationOptions', [])

            if options and finding != 'OPTIMIZED':
                best_option = options[0]  # First option is usually best
                recommended_type = best_option['instanceType']

                # Get savings opportunity
                savings_opp = best_option.get('savingsOpportunity', {})
                monthly_savings = float(savings_opp.get('estimatedMonthlySavings', {}).get('value', 0))
                savings_pct = float(savings_opp.get('savingsOpportunityPercentage', 0))

                # Performance risk (1-5, 1=very low, 5=very high)
                perf_risk = best_option.get('performanceRisk', 1)

                parsed.append({
                    'InstanceId': instance_id,
                    'Finding': finding,
                    'CurrentType': current_type,
                    'RecommendedType': recommended_type,
                    'CPU_Avg': cpu_avg,
                    'Memory_Avg': mem_avg,
                    'MonthlySavings': monthly_savings,
                    'SavingsPercent': savings_pct,
                    'PerformanceRisk': perf_risk,
                    'EBS_Read_IOPS': ebs_read,
                    'EBS_Write_IOPS': ebs_write,
                    'Network_In_MB': network_in / (1024**2),
                    'Network_Out_MB': network_out / (1024**2)
                })

        df = pd.DataFrame(parsed)

        if not df.empty:
            # Display summary
            print("📊 Recommendations Summary:\n")

            over_prov = df[df['Finding'] == 'OVER_PROVISIONED']
            under_prov = df[df['Finding'] == 'UNDER_PROVISIONED']

            print(f"   Over-provisioned: {len(over_prov)} instances")
            if len(over_prov) > 0:
                print(f"     Potential savings: ${over_prov['MonthlySavings'].sum():,.2f}/month")

            print(f"   Under-provisioned: {len(under_prov)} instances")
            print(f"   Total potential savings: ${df['MonthlySavings'].sum():,.2f}/month (${df['MonthlySavings'].sum() * 12:,.2f}/year)")

            # Show top opportunities
            print("\n   Top 5 savings opportunities:\n")
            top5 = df.nlargest(5, 'MonthlySavings')

            for idx, row in top5.iterrows():
                risk_label = {1: 'Very Low', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Very High'}
                risk = risk_label.get(row['PerformanceRisk'], 'Unknown')

                print(f"     {row['InstanceId']}:")
                print(f"       {row['CurrentType']} → {row['RecommendedType']}")
                print(f"       CPU: {row['CPU_Avg']:.1f}%, Memory: {row['Memory_Avg']:.1f}%")
                print(f"       Savings: ${row['MonthlySavings']:.2f}/month ({row['SavingsPercent']:.1f}%)")
                print(f"       Performance Risk: {risk}")
                print()

        return df

    def get_auto_scaling_recommendations(self) -> pd.DataFrame:
        """Get Auto Scaling Group recommendations"""
        print("\n💡 Retrieving Auto Scaling Group recommendations...")

        try:
            response = self.compute_optimizer.get_auto_scaling_group_recommendations(
                maxResults=100
            )
        except Exception as e:
            print(f"❌ Error getting ASG recommendations: {e}")
            return pd.DataFrame()

        recommendations = response.get('autoScalingGroupRecommendations', [])

        if not recommendations:
            print("✅ No ASG recommendations")
            return pd.DataFrame()

        print(f"✅ Found {len(recommendations)} ASG recommendations\n")

        parsed = []

        for rec in recommendations:
            asg_arn = rec['autoScalingGroupArn']
            asg_name = rec['autoScalingGroupName']
            current_config = rec['currentConfiguration']

            current_type = current_config['instanceType']

            finding = rec.get('finding', 'OPTIMIZED')

            options = rec.get('recommendationOptions', [])
            if options:
                best_option = options[0]
                recommended_type = best_option['configuration']['instanceType']

                savings_opp = best_option.get('savingsOpportunity', {})
                monthly_savings = float(savings_opp.get('estimatedMonthlySavings', {}).get('value', 0))

                parsed.append({
                    'ASG_Name': asg_name,
                    'Finding': finding,
                    'CurrentType': current_type,
                    'RecommendedType': recommended_type,
                    'MonthlySavings': monthly_savings
                })

        df = pd.DataFrame(parsed)

        if not df.empty:
            print(f"   Total ASG savings: ${df['MonthlySavings'].sum():,.2f}/month")

        return df

    def get_lambda_recommendations(self) -> pd.DataFrame:
        """Get Lambda function right-sizing recommendations"""
        print("\n💡 Retrieving Lambda recommendations...")

        try:
            response = self.compute_optimizer.get_lambda_function_recommendations(
                maxResults=100
            )
        except Exception as e:
            print(f"❌ Error getting Lambda recommendations: {e}")
            return pd.DataFrame()

        recommendations = response.get('lambdaFunctionRecommendations', [])

        if not recommendations:
            print("✅ No Lambda recommendations")
            return pd.DataFrame()

        print(f"✅ Found {len(recommendations)} Lambda recommendations\n")

        parsed = []

        for rec in recommendations:
            function_arn = rec['functionArn']
            function_name = function_arn.split(':')[-1]
            current_memory = rec['currentMemorySize']

            finding = rec.get('finding', 'OPTIMIZED')

            options = rec.get('memorySizeRecommendationOptions', [])
            if options:
                best_option = options[0]
                recommended_memory = best_option['memorySize']

                savings_opp = best_option.get('savingsOpportunity', {})
                monthly_savings = float(savings_opp.get('estimatedMonthlySavings', {}).get('value', 0))

                parsed.append({
                    'FunctionName': function_name,
                    'Finding': finding,
                    'CurrentMemory': current_memory,
                    'RecommendedMemory': recommended_memory,
                    'MonthlySavings': monthly_savings
                })

        df = pd.DataFrame(parsed)

        if not df.empty:
            print(f"   Total Lambda savings: ${df['MonthlySavings'].sum():,.2f}/month")

        return df

def main():
    """Main Compute Optimizer workflow"""
    print("=" * 70)
    print("AWS Compute Optimizer - Right-Sizing Analysis")
    print("=" * 70)

    analyzer = ComputeOptimizerAnalyzer()

    # Step 1: Enable Compute Optimizer
    print("\n[Step 1/4] Checking Compute Optimizer status...")
    analyzer.enable_compute_optimizer()

    # Step 2: Get EC2 recommendations
    print("\n[Step 2/4] Analyzing EC2 instances...")
    ec2_df = analyzer.get_ec2_recommendations()

    if not ec2_df.empty:
        ec2_df.to_csv('compute-optimizer-ec2-recommendations.csv', index=False)
        print("\n   📁 Saved: compute-optimizer-ec2-recommendations.csv")

    # Step 3: Get Auto Scaling recommendations
    print("\n[Step 3/4] Analyzing Auto Scaling Groups...")
    asg_df = analyzer.get_auto_scaling_recommendations()

    if not asg_df.empty:
        asg_df.to_csv('compute-optimizer-asg-recommendations.csv', index=False)
        print("   📁 Saved: compute-optimizer-asg-recommendations.csv")

    # Step 4: Get Lambda recommendations
    print("\n[Step 4/4] Analyzing Lambda functions...")
    lambda_df = analyzer.get_lambda_recommendations()

    if not lambda_df.empty:
        lambda_df.to_csv('compute-optimizer-lambda-recommendations.csv', index=False)
        print("   📁 Saved: compute-optimizer-lambda-recommendations.csv")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Compute Optimizer Analysis Complete!")
    print("=" * 70)

    total_monthly = 0
    if not ec2_df.empty:
        total_monthly += ec2_df['MonthlySavings'].sum()
    if not asg_df.empty:
        total_monthly += asg_df['MonthlySavings'].sum()
    if not lambda_df.empty:
        total_monthly += lambda_df['MonthlySavings'].sum()

    print("\n💰 Total Optimization Potential:")
    print(f"   Monthly: ${total_monthly:,.2f}")
    print(f"   Annual: ${total_monthly * 12:,.2f}")

    print("\n📋 Next Steps:")
    print("   1. Review recommendations in CSV files")
    print("   2. Test changes in non-production environments")
    print("   3. Monitor performance after changes")
    print("   4. Gradually apply to production instances")

    print("\n⚠️  Important:")
    print("   • Performance Risk levels indicate confidence")
    print("   • Start with 'Very Low' risk recommendations")
    print("   • Monitor closely after resizing")
    print("   • Keep CloudWatch alarms active")

if __name__ == '__main__':
    main()
