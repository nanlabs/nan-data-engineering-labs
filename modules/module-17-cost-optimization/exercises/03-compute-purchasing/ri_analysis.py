#!/usr/bin/env python3
"""
Reserved Instance (RI) Analysis
Analyze RI purchase recommendations, utilization, and coverage
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

class ReservedInstanceAnalyzer:
    """Analyze Reserved Instance opportunities and performance"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize Cost Explorer client"""
        self.ce = boto3.client('ce', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)

    def get_ri_recommendations(
        self,
        service: str = 'Amazon Elastic Compute Cloud - Compute',
        lookback_days: str = 'SIXTY_DAYS',
        term: str = 'ONE_YEAR',
        payment: str = 'ALL_UPFRONT'
    ) -> List[Dict]:
        """
        Get RI purchase recommendations from Cost Explorer

        Args:
            service: AWS service name
            lookback_days: SEVEN_DAYS, THIRTY_DAYS, SIXTY_DAYS
            term: ONE_YEAR or THREE_YEARS
            payment: NO_UPFRONT, PARTIAL_UPFRONT, ALL_UPFRONT

        Returns:
            List of recommendations
        """
        print("\n💡 Getting RI recommendations...")
        print(f"   Service: {service}")
        print(f"   Lookback: {lookback_days}")
        print(f"   Term: {term}, Payment: {payment}")

        try:
            response = self.ce.get_reservation_purchase_recommendation(
                Service=service,
                LookbackPeriodInDays=lookback_days,
                TermInYears=term,
                PaymentOption=payment
            )
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            print("   Ensure you have ce:GetReservationPurchaseRecommendation permission")
            return []

        recommendations = response.get('Recommendations', [])

        if not recommendations:
            print("✅ No RI recommendations (you may already have optimal coverage)")
            return []

        print(f"✅ Found {len(recommendations)} recommendations\n")

        parsed = []
        for rec in recommendations[:10]:  # Limit to top 10
            summary = rec.get('RecommendationSummary', {})

            parsed.append({
                'instance_count': summary.get('TotalRecommendedUnits', 0),
                'on_demand_cost': float(summary.get('TotalRegionalOnDemandCost', 0)),
                'ri_cost': float(summary.get('TotalRegionalReservedInstanceCost', 0)),
                'savings_percentage': float(summary.get('SavingsPercentage', 0)),
                'savings_amount': float(summary.get('EstimatedMonthlySavingsAmount', 0))
            })

        return parsed

    def display_ri_recommendations(self, recommendations: List[Dict]):
        """Display RI recommendations in readable format"""
        if not recommendations:
            return

        print("💰 Reserved Instance Purchase Recommendations:\n")

        total_savings = 0

        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. Recommendation:")
            print(f"     Instances to purchase: {rec['instance_count']}")
            print(f"     Current (On-Demand): ${rec['on_demand_cost']:,.2f}/year")
            print(f"     With RIs: ${rec['ri_cost']:,.2f}/year")
            print(f"     Annual Savings: ${rec['on_demand_cost'] - rec['ri_cost']:,.2f} ({rec['savings_percentage']:.1f}%)")
            print(f"     Monthly Savings: ${rec['savings_amount']:,.2f}")
            print()

            total_savings += rec['savings_amount']

        print(f"💵 Total Potential Monthly Savings: ${total_savings:,.2f}")
        print(f"💵 Total Potential Annual Savings: ${total_savings * 12:,.2f}")

    def get_ri_utilization(self, days: int = 30) -> pd.DataFrame:
        """
        Get RI utilization for the last N days

        Args:
            days: Number of days to analyze

        Returns:
            DataFrame with daily utilization
        """
        print(f"\n📊 Analyzing RI utilization (last {days} days)...")

        end = datetime.now().date()
        start = end - timedelta(days=days)

        try:
            response = self.ce.get_reservation_utilization(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='DAILY'
            )
        except Exception as e:
            print(f"⚠️  No RI utilization data: {e}")
            print("   (Normal if you don't have any RIs purchased)")
            return pd.DataFrame()

        # Parse results
        utilization_data = []

        for day in response['UtilizationsByTime']:
            date = day['TimePeriod']['Start']
            util = day['Total']

            utilization_data.append({
                'Date': date,
                'PurchasedHours': float(util.get('TotalActualHours', 0)),
                'UsedHours': float(util.get('UtilizedHours', 0)),
                'UnusedHours': float(util.get('UnusedHours', 0)),
                'UtilizationPercentage': float(util.get('UtilizationPercentage', 0))
            })

        df = pd.DataFrame(utilization_data)

        if not df.empty:
            avg_utilization = df['UtilizationPercentage'].mean()

            print(f"✅ Retrieved {len(df)} days of data")
            print(f"\n   Average Utilization: {avg_utilization:.1f}%")
            print(f"   Best Day: {df['UtilizationPercentage'].max():.1f}%")
            print(f"   Worst Day: {df['UtilizationPercentage'].min():.1f}%")

            # Show low utilization days
            low_util_days = df[df['UtilizationPercentage'] < 80]
            if not low_util_days.empty:
                print(f"\n   ⚠️  Days with <80% utilization: {len(low_util_days)}")
                for idx, row in low_util_days.head(5).iterrows():
                    print(f"     {row['Date']}: {row['UtilizationPercentage']:.1f}% (wasted ${row['UnusedHours'] * 0.062:.2f})")

            # Recommendations
            if avg_utilization < 80:
                print("\n   💡 Recommendation: Reduce RI count or switch to Savings Plans (more flexible)")
            elif avg_utilization > 95:
                print("\n   💡 Recommendation: Consider purchasing more RIs (high demand)")
            else:
                print("\n   ✅ Utilization is good (80-95% target range)")

        return df

    def get_ri_coverage(self, days: int = 30) -> pd.DataFrame:
        """
        Get RI coverage for the last N days

        Args:
            days: Number of days to analyze

        Returns:
            DataFrame with coverage data
        """
        print(f"\n📊 Analyzing RI coverage (last {days} days)...")

        end = datetime.now().date()
        start = end - timedelta(days=days)

        try:
            response = self.ce.get_reservation_coverage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
                ]
            )
        except Exception as e:
            print(f"⚠️  No RI coverage data: {e}")
            return pd.DataFrame()

        # Parse results
        coverage_data = []

        for period in response['CoveragesByTime']:
            for group in period.get('Groups', []):
                instance_type = group['Attributes'].get('instanceType', 'Unknown')
                coverage = group.get('Coverage', {})

                coverage_hours = coverage.get('CoverageHours', {})
                coverage_pct = float(coverage_hours.get('CoverageHoursPercentage', 0))
                on_demand_hours = float(coverage_hours.get('OnDemandHours', 0))
                reserved_hours = float(coverage_hours.get('ReservedHours', 0))

                coverage_cost = coverage.get('CoverageCost', {})
                on_demand_cost = float(coverage_cost.get('OnDemandCost', 0))

                coverage_data.append({
                    'InstanceType': instance_type,
                    'CoveragePercentage': coverage_pct,
                    'OnDemandHours': on_demand_hours,
                    'ReservedHours': reserved_hours,
                    'OnDemandCost': on_demand_cost
                })

        df = pd.DataFrame(coverage_data)

        if not df.empty:
            # Sort by on-demand cost to find biggest opportunities
            df = df.sort_values('OnDemandCost', ascending=False)

            overall_coverage = df['ReservedHours'].sum() / (df['ReservedHours'].sum() + df['OnDemandHours'].sum()) * 100

            print(f"✅ Overall RI Coverage: {overall_coverage:.1f}%")
            print("\n   Top instances by On-Demand cost:")

            for idx, row in df.head(5).iterrows():
                print(f"     {row['InstanceType']}: {row['CoveragePercentage']:.1f}% covered (${row['OnDemandCost']:.2f} on-demand)")

            # Find opportunities
            low_coverage = df[df['CoveragePercentage'] < 70]
            if not low_coverage.empty:
                print("\n   💡 Opportunities (coverage <70%):")
                for idx, row in low_coverage.head(3).iterrows():
                    potential_savings = row['OnDemandCost'] * 0.6  # Assume 60% RI discount
                    print(f"     {row['InstanceType']}: Buy more RIs → save ${potential_savings:.2f}/month")

        return df

    def calculate_ri_roi(
        self,
        instance_type: str,
        instance_count: int,
        on_demand_hourly: float,
        ri_hourly: float,
        ri_upfront: float = 0,
        months_usage: int = 12
    ) -> Dict:
        """
        Calculate ROI for RI purchase

        Args:
            instance_type: EC2 instance type
            instance_count: Number of instances
            on_demand_hourly: On-Demand hourly rate
            ri_hourly: RI hourly rate
            ri_upfront: RI upfront payment
            months_usage: Months to calculate over

        Returns:
            ROI analysis dict
        """
        hours_per_month = 730
        total_hours = hours_per_month * months_usage

        # Calculate costs
        on_demand_total = on_demand_hourly * total_hours * instance_count
        ri_total = (ri_hourly * total_hours * instance_count) + (ri_upfront * instance_count)

        savings = on_demand_total - ri_total
        savings_pct = (savings / on_demand_total) * 100 if on_demand_total > 0 else 0

        # Calculate break-even
        if ri_upfront > 0:
            hourly_savings = (on_demand_hourly - ri_hourly) * instance_count
            break_even_hours = (ri_upfront * instance_count) / hourly_savings if hourly_savings > 0 else 0
            break_even_months = break_even_hours / hours_per_month
        else:
            break_even_months = 0  # Immediate savings with no upfront

        return {
            'instance_type': instance_type,
            'instance_count': instance_count,
            'months': months_usage,
            'on_demand_total': on_demand_total,
            'ri_total': ri_total,
            'savings_total': savings,
            'savings_percentage': savings_pct,
            'monthly_savings': savings / months_usage,
            'break_even_months': break_even_months
        }

def main():
    """Main RI analysis workflow"""
    print("=" * 70)
    print("Reserved Instance Analysis")
    print("=" * 70)

    analyzer = ReservedInstanceAnalyzer()

    # Step 1: Get RI recommendations
    print("\n[Step 1/4] Retrieving RI purchase recommendations...")

    # Try different options
    for term in ['ONE_YEAR', 'THREE_YEARS']:
        for payment in ['NO_UPFRONT', 'ALL_UPFRONT']:
            print(f"\n--- {term}, {payment} ---")
            recommendations = analyzer.get_ri_recommendations(
                lookback_days='SIXTY_DAYS',
                term=term,
                payment=payment
            )
            analyzer.display_ri_recommendations(recommendations)

    # Step 2: Analyze current RI utilization
    print("\n[Step 2/4] Analyzing current RI utilization...")
    util_df = analyzer.get_ri_utilization(days=30)

    if not util_df.empty:
        util_df.to_csv('ri-utilization-report.csv', index=False)
        print("\n   📁 Saved: ri-utilization-report.csv")

    # Step 3: Analyze RI coverage
    print("\n[Step 3/4] Analyzing RI coverage...")
    coverage_df = analyzer.get_ri_coverage(days=30)

    if not coverage_df.empty:
        coverage_df.to_csv('ri-coverage-report.csv', index=False)
        print("\n   📁 Saved: ri-coverage-report.csv")

    # Step 4: ROI calculation example
    print("\n[Step 4/4] Calculating ROI example...")

    # Example: m5.xlarge
    roi = analyzer.calculate_ri_roi(
        instance_type='m5.xlarge',
        instance_count=10,
        on_demand_hourly=0.192,
        ri_hourly=0.0,
        ri_upfront=1045,  # 1Y All Upfront per instance
        months_usage=12
    )

    print("\n💰 RI ROI Analysis (m5.xlarge, 10 instances, 1 year):")
    print(f"   On-Demand Total: ${roi['on_demand_total']:,.2f}")
    print(f"   RI Total: ${roi['ri_total']:,.2f}")
    print(f"   Total Savings: ${roi['savings_total']:,.2f} ({roi['savings_percentage']:.1f}%)")
    print(f"   Monthly Savings: ${roi['monthly_savings']:,.2f}")
    print(f"   Break-Even: {roi['break_even_months']:.1f} months")

    # Summary
    print("\n" + "=" * 70)
    print("✅ RI Analysis Complete!")
    print("=" * 70)

    print("\n📋 Key Insights:")
    print("   • Target RI Utilization: >85%")
    print("   • Target Coverage: 70-80% (leave 20-30% for flexibility)")
    print("   • 1Y All Upfront typically breaks even in 4-5 months")
    print("   • 3Y All Upfront provides maximum discount (55-75%)")

    print("\n💡 Recommendations:")
    print("   1. Start with 1Y commitment to test usage patterns")
    print("   2. Use All Upfront for maximum discount (if cash available)")
    print("   3. Consider Savings Plans for more flexibility")
    print("   4. Monitor utilization weekly, adjust as needed")

if __name__ == '__main__':
    main()
