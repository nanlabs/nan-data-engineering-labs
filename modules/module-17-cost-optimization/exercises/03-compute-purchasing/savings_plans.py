#!/usr/bin/env python3
"""
Savings Plans Analysis
Analyze Savings Plans recommendations, utilization, and coverage
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

class SavingsPlansAnalyzer:
    """Analyze Savings Plans opportunities and performance"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize Cost Explorer client"""
        self.ce = boto3.client('ce', region_name=region)
        self.savingsplans = boto3.client('savingsplans', region_name=region)

    def get_sp_recommendations(
        self,
        sp_type: str = 'COMPUTE_SP',
        lookback_days: str = 'SIXTY_DAYS',
        term: str = 'ONE_YEAR',
        payment: str = 'NO_UPFRONT'
    ) -> List[Dict]:
        """
        Get Savings Plans purchase recommendations

        Args:
            sp_type: COMPUTE_SP or EC2_INSTANCE_SP
            lookback_days: SEVEN_DAYS, THIRTY_DAYS, SIXTY_DAYS
            term: ONE_YEAR or THREE_YEARS
            payment: NO_UPFRONT, PARTIAL_UPFRONT, ALL_UPFRONT

        Returns:
            List of recommendations
        """
        print("\n💡 Getting Savings Plans recommendations...")
        print(f"   Type: {sp_type}")
        print(f"   Lookback: {lookback_days}")
        print(f"   Term: {term}, Payment: {payment}")

        try:
            response = self.ce.get_savings_plans_purchase_recommendation(
                SavingsPlansType=sp_type,
                LookbackPeriodInDays=lookback_days,
                TermInYears=term,
                PaymentOption=payment
            )
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            return []

        metadata = response.get('Metadata', {})
        rec_id = metadata.get('RecommendationId', 'N/A')
        generation_time = metadata.get('GenerationTimestamp', 'N/A')

        print(f"✅ Recommendation ID: {rec_id}")
        print(f"   Generated: {generation_time}")

        # Parse recommendations
        sp_rec = response.get('SavingsPlansPurchaseRecommendation', {})
        details = sp_rec.get('SavingsPlansPurchaseRecommendationDetails', [])

        recommendations = []

        for detail in details[:5]:  # Top 5
            hourly_commit = float(detail.get('HourlyCommitmentToPurchase', 0))
            estimated_savings = float(detail.get('EstimatedSavingsAmount', 0))
            estimated_pct = float(detail.get('EstimatedSavingsPercentage', 0))
            on_demand_cost = float(detail.get('EstimatedOnDemandCost', 0))
            sp_cost = float(detail.get('EstimatedSPCost', 0))

            recommendations.append({
                'hourly_commitment': hourly_commit,
                'monthly_commitment': hourly_commit * 730,
                'annual_commitment': hourly_commit * 8760,
                'on_demand_cost': on_demand_cost,
                'sp_cost': sp_cost,
                'savings_amount': estimated_savings,
                'savings_percentage': estimated_pct
            })

        return recommendations

    def display_sp_recommendations(self, recommendations: List[Dict], sp_type: str):
        """Display Savings Plans recommendations"""
        if not recommendations:
            print("✅ No recommendations (optimal coverage already)")
            return

        print(f"\n💰 Savings Plans Recommendations ({sp_type}):\n")

        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. Hourly Commitment: ${rec['hourly_commitment']:.2f}/hour")
            print(f"     Monthly: ${rec['monthly_commitment']:,.2f}")
            print(f"     Annual: ${rec['annual_commitment']:,.2f}")
            print(f"     Current (On-Demand): ${rec['on_demand_cost']:,.2f}")
            print(f"     With Savings Plan: ${rec['sp_cost']:,.2f}")
            print(f"     Annual Savings: ${rec['savings_amount']:,.2f} ({rec['savings_percentage']:.1f}%)")
            print()

    def get_sp_utilization(self, days: int = 30) -> pd.DataFrame:
        """
        Get Savings Plans utilization

        Args:
            days: Number of days to analyze

        Returns:
            DataFrame with utilization data
        """
        print(f"\n📊 Analyzing Savings Plans utilization (last {days} days)...")

        end = datetime.now().date()
        start = end - timedelta(days=days)

        try:
            response = self.ce.get_savings_plans_utilization(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='DAILY'
            )
        except Exception as e:
            print(f"⚠️  No Savings Plans data: {e}")
            print("   (Normal if you don't have any Savings Plans)")
            return pd.DataFrame()

        # Parse results
        utilization_data = []

        for day in response['SavingsPlansUtilizationsByTime']:
            date = day['TimePeriod']['Start']
            util = day['Utilization']

            utilization_data.append({
                'Date': date,
                'TotalCommitment': float(util.get('TotalCommitment', 0)),
                'UsedCommitment': float(util.get('UsedCommitment', 0)),
                'UnusedCommitment': float(util.get('UnusedCommitment', 0)),
                'UtilizationPercentage': float(util.get('UtilizationPercentage', 0))
            })

        df = pd.DataFrame(utilization_data)

        if not df.empty:
            avg_utilization = df['UtilizationPercentage'].mean()
            total_wasted = df['UnusedCommitment'].sum()

            print(f"✅ Retrieved {len(df)} days of data")
            print(f"\n   Average Utilization: {avg_utilization:.1f}%")
            print(f"   Total Wasted Commitment: ${total_wasted:.2f}")

            if avg_utilization < 80:
                print("\n   ⚠️  LOW UTILIZATION ALERT")
                print(f"   Wasted spend: ${total_wasted:.2f} over {days} days")
                print("   Action: Reduce commitment or increase workload")
            elif avg_utilization > 95:
                print("\n   ⚡ HIGH UTILIZATION ALERT")
                print("   Consider purchasing additional Savings Plans")
            else:
                print("\n   ✅ Utilization is optimal (80-95% range)")

        return df

    def get_sp_coverage(self, days: int = 30) -> pd.DataFrame:
        """Get Savings Plans coverage"""
        print(f"\n📊 Analyzing Savings Plans coverage (last {days} days)...")

        end = datetime.now().date()
        start = end - timedelta(days=days)

        try:
            response = self.ce.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
        except Exception as e:
            print(f"⚠️  No coverage data: {e}")
            return pd.DataFrame()

        # Parse results
        coverage_data = []

        for period in response['SavingsPlansCoverages']:
            coverage = period.get('Coverage', {})

            spend_covered = float(coverage.get('SpendCoveredBySavingsPlans', 0))
            on_demand_cost = float(coverage.get('OnDemandCost', 0))
            total = spend_covered + on_demand_cost
            coverage_pct = (spend_covered / total * 100) if total > 0 else 0

            coverage_data.append({
                'Period': period['TimePeriod']['Start'],
                'CoveredByShortfall': spend_covered,
                'OnDemandCost': on_demand_cost,
                'TotalCost': total,
                'CoveragePercentage': coverage_pct
            })

        df = pd.DataFrame(coverage_data)

        if not df.empty:
            avg_coverage = df['CoveragePercentage'].mean()
            total_on_demand = df['OnDemandCost'].sum()

            print(f"✅ Coverage: {avg_coverage:.1f}%")
            print(f"   On-Demand Cost: ${total_on_demand:,.2f}")

            if avg_coverage < 70:
                # Opportunity to purchase more
                uncovered = total_on_demand
                potential_commit = uncovered * 0.6  # Cover 60% more
                potential_savings = potential_commit * 0.33  # 33% discount (1Y SP)

                print("\n   💡 Opportunity:")
                print(f"   Uncovered On-Demand: ${uncovered:,.2f}")
                print(f"   Recommended additional commitment: ${potential_commit:,.2f}/month")
                print(f"   Potential monthly savings: ${potential_savings:,.2f} (33% discount)")
                print(f"   Annual savings: ${potential_savings * 12:,.2f}")
            else:
                print("\n   ✅ Coverage is good (target: 70-80%)")

        return df

    def compare_sp_vs_ri(self):
        """Compare flexibility and savings between Savings Plans and RIs"""
        print("\n⚖️  Savings Plans vs Reserved Instances:\n")

        comparison = pd.DataFrame([
            {
                'Feature': 'Discount (1Y)',
                'Savings Plans': '33% (Compute SP)',
                'Reserved Instances': '35-42%',
                'Winner': 'RI'
            },
            {
                'Feature': 'Discount (3Y)',
                'Savings Plans': '60% (Compute SP)',
                'Reserved Instances': '56-63%',
                'Winner': 'Tie'
            },
            {
                'Feature': 'Instance Type Flexibility',
                'Savings Plans': '✅ Any instance (Compute SP)',
                'Reserved Instances': '❌ Fixed instance type',
                'Winner': 'SP'
            },
            {
                'Feature': 'Region Flexibility',
                'Savings Plans': '✅ Any region (Compute SP)',
                'Reserved Instances': '❌ Fixed region',
                'Winner': 'SP'
            },
            {
                'Feature': 'Service Coverage',
                'Savings Plans': '✅ EC2, Fargate, Lambda',
                'Reserved Instances': '❌ EC2 only',
                'Winner': 'SP'
            },
            {
                'Feature': 'Marketplace',
                'Savings Plans': '❌ No marketplace',
                'Reserved Instances': '✅ Can sell unused RIs',
                'Winner': 'RI'
            }
        ])

        print(comparison.to_string(index=False))

        print("\n💡 Decision Guide:")
        print("   Choose Savings Plans if:")
        print("     • Instance types change frequently")
        print("     • Multi-region workloads")
        print("     • Using Fargate or Lambda alongside EC2")
        print("     • Want operational flexibility")

        print("\n   Choose Reserved Instances if:")
        print("     • Instance type is fixed and predictable")
        print("     • Single region deployment")
        print("     • Want slightly higher discount (1-2% more)")
        print("     • May want to sell unused capacity later")

def main():
    """Main Savings Plans analysis workflow"""
    print("=" * 70)
    print("Savings Plans Analysis")
    print("=" * 70)

    analyzer = SavingsPlansAnalyzer()

    # Step 1: Get recommendations
    print("\n[Step 1/4] Retrieving Savings Plans recommendations...")

    for sp_type in ['COMPUTE_SP', 'EC2_INSTANCE_SP']:
        print(f"\n{'─' * 70}")
        print(f"{sp_type}")
        print(f"{'─' * 70}")

        for term in ['ONE_YEAR', 'THREE_YEARS']:
            recommendations = analyzer.get_sp_recommendations(
                sp_type=sp_type,
                lookback_days='SIXTY_DAYS',
                term=term,
                payment='NO_UPFRONT'
            )
            analyzer.display_sp_recommendations(recommendations, sp_type)

    # Step 2: Analyze utilization
    print("\n[Step 2/4] Analyzing Savings Plans utilization...")
    util_df = analyzer.get_sp_utilization(days=30)

    if not util_df.empty:
        util_df.to_csv('sp-utilization-report.csv', index=False)
        print("   📁 Saved: sp-utilization-report.csv")

    # Step 3: Analyze coverage
    print("\n[Step 3/4] Analyzing Savings Plans coverage...")
    coverage_df = analyzer.get_sp_coverage(days=30)

    if not coverage_df.empty:
        coverage_df.to_csv('sp-coverage-report.csv', index=False)
        print("   📁 Saved: sp-coverage-report.csv")

    # Step 4: Compare SP vs RI
    print("\n[Step 4/4] Comparing Savings Plans vs Reserved Instances...")
    analyzer.compare_sp_vs_ri()

    # Summary
    print("\n" + "=" * 70)
    print("✅ Savings Plans Analysis Complete!")
    print("=" * 70)

    print("\n📊 Savings Plans Benefits:")
    print("   ✅ Flexibility: Any instance type, any region")
    print("   ✅ Coverage: EC2, Fargate, Lambda")
    print("   ✅ Discounts: 33% (1Y), 60% (3Y) for Compute SP")
    print("   ✅ Simple: One commitment covers all compute")

    print("\n💡 Best Practices:")
    print("   1. Start with Compute SP for maximum flexibility")
    print("   2. Target 70-80% coverage (leave room for growth)")
    print("   3. Monitor utilization weekly (target >85%)")
    print("   4. Use No Upfront for operational simplicity")
    print("   5. Consider 3Y for long-term stable workloads")

if __name__ == '__main__':
    main()
