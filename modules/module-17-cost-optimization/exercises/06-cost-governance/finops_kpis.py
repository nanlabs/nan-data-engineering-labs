#!/usr/bin/env python3
"""
FinOps Key Performance Indicators (KPIs)
Track and report on cost optimization maturity and effectiveness
"""

import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict

class FinOpsKPICalculator:
    """Calculate FinOps key performance indicators"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.ce = boto3.client('ce', region_name=region)
        self.organizations = None  # boto3.client('organizations')

    def calculate_commitment_coverage(self, days: int = 90) -> float:
        """
        Calculate RI + Savings Plans coverage percentage
        Target: > 70%

        Args:
            days: Number of days to analyze

        Returns:
            Coverage percentage (0-100)
        """
        print("\n📊 Calculating Commitment Coverage...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            response = self.ce.get_reservation_coverage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY'
            )

            if response.get('CoveragesByTime'):
                coverage_data = response['CoveragesByTime'][0]['Total']
                covered_hours = float(coverage_data['CoverageHours']['CoverageHoursPercentage'])

                print(f"   Coverage: {covered_hours:.1f}%")
                return covered_hours

        except Exception as e:
            print(f"   ⚠️  Could not retrieve coverage: {e}")

        return 0.0

    def calculate_commitment_utilization(self, days: int = 90) -> float:
        """
        Calculate RI + Savings Plans utilization percentage
        Target: > 85%

        Args:
            days: Number of days to analyze

        Returns:
            Utilization percentage (0-100)
        """
        print("   Calculating Commitment Utilization...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            response = self.ce.get_reservation_utilization(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY'
            )

            if response.get('UtilizationsByTime'):
                util_data = response['UtilizationsByTime'][0]['Total']
                utilization = float(util_data['UtilizationPercentage'])

                print(f"   Utilization: {utilization:.1f}%")
                return utilization

        except Exception as e:
            print(f"   ⚠️  Could not retrieve utilization: {e}")

        return 0.0

    def calculate_tagging_compliance(self, required_tag: str = 'CostCenter') -> float:
        """
        Calculate percentage of costs from untagged resources
        Target: < 5% untagged

        Args:
            required_tag: Tag key to check for compliance

        Returns:
            Untagged resource percentage (0-100)
        """
        print(f"   Calculating Tagging Compliance ({required_tag})...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        try:
            # Get total cost
            total_response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )

            total_cost = float(total_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

            # Get tagged cost
            tagged_response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Tags': {
                        'Key': required_tag
                    }
                }
            )

            tagged_cost = float(tagged_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

            # Calculate untagged percentage
            untagged_pct = ((total_cost - tagged_cost) / total_cost) * 100 if total_cost > 0 else 0

            print(f"   Untagged: {untagged_pct:.1f}% (${total_cost - tagged_cost:,.2f})")
            return untagged_pct

        except Exception as e:
            print(f"   ⚠️  Could not retrieve tagging compliance: {e}")

        return 100.0  # Assume worst case

    def calculate_cost_growth(self) -> float:
        """
        Calculate month-over-month cost growth
        Target: < 15% monthly growth

        Returns:
            Growth percentage (positive = increase, negative = decrease)
        """
        print("   Calculating Month-over-Month Growth...")

        # Current month
        current_month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        current_month_end = datetime.now().strftime('%Y-%m-%d')

        # Previous month
        prev_month_end = (datetime.now().replace(day=1) - timedelta(days=1))
        prev_month_start = prev_month_end.replace(day=1).strftime('%Y-%m-%d')
        prev_month_end = prev_month_end.strftime('%Y-%m-%d')

        try:
            # Get previous month cost
            prev_response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': prev_month_start, 'End': prev_month_end},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )

            prev_cost = float(prev_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

            # Get current month cost (prorated)
            current_response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': current_month_start, 'End': current_month_end},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )

            current_cost_mtd = float(current_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

            # Prorate current month to full month
            days_in_month = 30
            days_elapsed = datetime.now().day
            current_cost_projected = (current_cost_mtd / days_elapsed) * days_in_month

            # Calculate growth
            growth_pct = ((current_cost_projected - prev_cost) / prev_cost) * 100 if prev_cost > 0 else 0

            print(f"   Previous Month: ${prev_cost:,.2f}")
            print(f"   Current (MTD): ${current_cost_mtd:,.2f}")
            print(f"   Current (Projected): ${current_cost_projected:,.2f}")
            print(f"   Growth: {growth_pct:+.1f}%")

            return growth_pct

        except Exception as e:
            print(f"   ⚠️  Could not calculate growth: {e}")

        return 0.0

    def calculate_waste_ratio(self) -> float:
        """
        Estimate waste from idle resources
        Target: < 10% waste

        Returns:
            Waste percentage (0-100)
        """
        print("   Calculating Waste Ratio...")

        # In production, this would:
        # 1. Query CloudWatch for idle instances (CPU < 10%)
        # 2. Find unattached volumes
        # 3. Identify unused elastic IPs
        # 4. Calculate wasted spend vs total spend

        # Simplified estimate for demo
        waste_estimate = 15.0  # Typical 10-20% waste in unoptimized accounts

        print(f"   Waste Ratio: ~{waste_estimate:.1f}%")
        return waste_estimate

    def calculate_all_kpis(self) -> Dict[str, float]:
        """
        Calculate all FinOps KPIs

        Returns:
            Dict with all KPI values
        """
        print("\n💡 Calculating FinOps KPIs")
        print("=" * 60)

        kpis = {
            'commitment_coverage': self.calculate_commitment_coverage(days=90),
            'commitment_utilization': self.calculate_commitment_utilization(days=90),
            'untagged_resources_pct': self.calculate_tagging_compliance(required_tag='CostCenter'),
            'mom_growth_pct': self.calculate_cost_growth(),
            'waste_ratio_pct': self.calculate_waste_ratio()
        }

        return kpis

    def display_kpi_dashboard(self, kpis: Dict[str, float]):
        """
        Display FinOps KPI dashboard with targets and scoring

        Args:
            kpis: Dict with KPI values
        """
        print("\n" + "=" * 70)
        print("             FINOPS KEY PERFORMANCE INDICATORS")
        print("=" * 70)

        # KPI 1: Commitment Coverage
        coverage = kpis['commitment_coverage']
        print(f"\n1️⃣  Commitment Coverage: {coverage:.1f}%")
        print("    (RI + Savings Plans coverage of eligible spend)")
        if coverage >= 70:
            print("    ✅ Target Met (>70%)")
        else:
            print(f"    ⚠️  Below Target (<70%) - Opportunity: {70 - coverage:.1f}%")
            print("       → Purchase RIs or Savings Plans for steady workloads")

        # KPI 2: Commitment Utilization
        utilization = kpis['commitment_utilization']
        print(f"\n2️⃣  Commitment Utilization: {utilization:.1f}%")
        print("    (Percentage of purchased commitments actually used)")
        if utilization >= 85:
            print("    ✅ Target Met (>85%)")
        else:
            print(f"    ⚠️  Below Target (<85%) - Waste: {85 - utilization:.1f}%")
            print("       → Reduce commitments or increase workload to match")

        # KPI 3: Tagging Compliance
        untagged = kpis['untagged_resources_pct']
        print(f"\n3️⃣  Tagging Compliance: {100 - untagged:.1f}% tagged")
        print("    (Resources with required cost allocation tags)")
        if untagged < 5:
            print("    ✅ Target Met (<5% untagged)")
        else:
            print(f"    ⚠️  Below Target (>{untagged:.1f}% untagged)")
            print("       → Implement tag policies and automated tagging")

        # KPI 4: Month-over-Month Growth
        growth = kpis['mom_growth_pct']
        print(f"\n4️⃣  Month-over-Month Growth: {growth:+.1f}%")
        print("    (Cost change vs previous month)")
        if growth < 0:
            print(f"    ✅ Cost Reduction Achieved! ({abs(growth):.1f}% decrease)")
        elif growth < 15:
            print("    ✅ Controlled Growth (<15%)")
        else:
            print(f"    ⚠️  High Growth (>{growth:.1f}%) - Investigate drivers")
            print("       → Review new resources, check for anomalies")

        # KPI 5: Waste Ratio
        waste = kpis['waste_ratio_pct']
        print(f"\n5️⃣  Waste Ratio: {waste:.1f}%")
        print("    (Idle resources, unused capacity)")
        if waste < 10:
            print("    ✅ Target Met (<10%)")
        else:
            print(f"    ⚠️  Above Target (>{waste:.1f}% waste)")
            print("       → Increase cleanup automation, right-size resources")

        # Overall FinOps Maturity Score
        score = 0
        if coverage >= 70: score += 20
        if utilization >= 85: score += 20
        if untagged < 5: score += 20
        if -5 < growth < 15: score += 20
        if waste < 10: score += 20

        print("\n" + "=" * 70)
        print(f"🎯 FinOps Maturity Score: {score}/100")
        print("=" * 70)

        if score >= 80:
            maturity = 'Run (Excellent)'
            color = '🟢'
            description = 'Continuous optimization with automation'
        elif score >= 60:
            maturity = 'Optimize (Good)'
            color = '🟡'
            description = 'Active cost management and improvements'
        elif score >= 40:
            maturity = 'Inform (Fair)'
            color = '🟠'
            description = 'Basic visibility, needs more optimization'
        else:
            maturity = 'Crawl (Needs Improvement)'
            color = '🔴'
            description = 'Limited cost management, establish foundations'

        print(f"\n   {color} Level: {maturity}")
        print(f"   {description}")

        return score

    def calculate_unit_economics(
        self,
        cost: float,
        metric_name: str,
        metric_value: float
    ) -> float:
        """
        Calculate cost per unit metric

        Args:
            cost: Total cost in period
            metric_name: Name of business metric (users, transactions, etc.)
            metric_value: Value of metric

        Returns:
            Unit cost
        """
        unit_cost = cost / metric_value if metric_value > 0 else 0

        print("\n📊 Unit Economics:")
        print(f"   Total Cost: ${cost:,.2f}")
        print(f"   {metric_name}: {metric_value:,.0f}")
        print(f"   Cost per {metric_name}: ${unit_cost:.4f}")

        return unit_cost

    def generate_finops_report(self, kpis: Dict[str, float]) -> pd.DataFrame:
        """
        Generate comprehensive FinOps report

        Args:
            kpis: Dict with KPI values

        Returns:
            DataFrame with report
        """
        report_data = []

        # KPI definitions with targets
        kpi_definitions = [
            {
                'metric': 'Commitment Coverage',
                'value': kpis['commitment_coverage'],
                'target': 70,
                'unit': '%',
                'better': 'higher',
                'category': 'Optimization'
            },
            {
                'metric': 'Commitment Utilization',
                'value': kpis['commitment_utilization'],
                'target': 85,
                'unit': '%',
                'better': 'higher',
                'category': 'Optimization'
            },
            {
                'metric': 'Untagged Resources',
                'value': kpis['untagged_resources_pct'],
                'target': 5,
                'unit': '%',
                'better': 'lower',
                'category': 'Governance'
            },
            {
                'metric': 'MoM Growth',
                'value': kpis['mom_growth_pct'],
                'target': 15,
                'unit': '%',
                'better': 'lower',
                'category': 'Efficiency'
            },
            {
                'metric': 'Waste Ratio',
                'value': kpis['waste_ratio_pct'],
                'target': 10,
                'unit': '%',
                'better': 'lower',
                'category': 'Efficiency'
            }
        ]

        for kpi in kpi_definitions:
            # Determine status
            if kpi['better'] == 'higher':
                status = 'Pass' if kpi['value'] >= kpi['target'] else 'Fail'
            else:
                status = 'Pass' if kpi['value'] <= kpi['target'] else 'Fail'

            report_data.append({
                'Metric': kpi['metric'],
                'Value': f"{kpi['value']:.1f}{kpi['unit']}",
                'Target': f"{kpi['target']}{kpi['unit']}",
                'Status': status,
                'Category': kpi['category']
            })

        df = pd.DataFrame(report_data)

        print("\n" + "=" * 70)
        print("FinOps KPI Report")
        print("=" * 70)
        print(df.to_string(index=False))

        # Save report
        df.to_csv('finops-kpi-report.csv', index=False)
        print("\n📁 Saved: finops-kpi-report.csv")

        return df

    def create_kpi_dashboard_visualization(self, kpis: Dict[str, float]):
        """
        Create visual dashboard of FinOps KPIs

        Args:
            kpis: Dict with KPI values
        """
        print("\n📊 Creating KPI Dashboard Visualization...")

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('FinOps KPI Dashboard', fontsize=20, fontweight='bold')

        # KPI configurations
        kpi_configs = [
            {
                'name': 'Commitment\nCoverage',
                'value': kpis['commitment_coverage'],
                'target': 70,
                'format': '%.1f%%',
                'higher_better': True
            },
            {
                'name': 'Commitment\nUtilization',
                'value': kpis['commitment_utilization'],
                'target': 85,
                'format': '%.1f%%',
                'higher_better': True
            },
            {
                'name': 'Untagged\nResources',
                'value': kpis['untagged_resources_pct'],
                'target': 5,
                'format': '%.1f%%',
                'higher_better': False
            },
            {
                'name': 'MoM Growth',
                'value': kpis['mom_growth_pct'],
                'target': 15,
                'format': '%+.1f%%',
                'higher_better': False
            },
            {
                'name': 'Waste Ratio',
                'value': kpis['waste_ratio_pct'],
                'target': 10,
                'format': '%.1f%%',
                'higher_better': False
            }
        ]

        # Plot each KPI
        for idx, kpi in enumerate(kpi_configs):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]

            # Determine status color
            if kpi['higher_better']:
                met_target = kpi['value'] >= kpi['target']
            else:
                met_target = kpi['value'] <= kpi['target']

            color = 'green' if met_target else 'red'

            # Gauge chart
            ax.barh([0], [kpi['value']], height=0.5, color=color, alpha=0.7)
            ax.axvline(kpi['target'], color='blue', linestyle='--', linewidth=2, label=f'Target: {kpi["target"]}%')
            ax.set_xlim(0, max(100, kpi['value'] * 1.2))
            ax.set_ylim(-0.5, 0.5)
            ax.set_yticks([])
            ax.set_xlabel('Percentage')
            ax.set_title(f"{kpi['name']}\n{kpi['format'] % kpi['value']}", fontsize=12, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(axis='x', alpha=0.3)

        # Overall maturity score in last panel
        score = sum([
            20 if kpis['commitment_coverage'] >= 70 else 0,
            20 if kpis['commitment_utilization'] >= 85 else 0,
            20 if kpis['untagged_resources_pct'] < 5 else 0,
            20 if -5 < kpis['mom_growth_pct'] < 15 else 0,
            20 if kpis['waste_ratio_pct'] < 10 else 0
        ])

        ax = axes[1, 2]
        ax.pie([score, 100-score], labels=['Score', 'Gap'], autopct='%1.0f%%',
               colors=['green' if score >= 80 else 'orange' if score >= 60 else 'red', 'lightgray'],
               startangle=90)
        ax.set_title(f'Maturity Score\n{score}/100', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig('finops-kpi-dashboard.png', dpi=300, bbox_inches='tight')
        print("   ✅ Dashboard saved: finops-kpi-dashboard.png")

def main():
    """Main FinOps KPI workflow"""
    print("=" * 70)
    print("FinOps Key Performance Indicators")
    print("=" * 70)

    calculator = FinOpsKPICalculator()

    # Calculate all KPIs
    kpis = calculator.calculate_all_kpis()

    # Display dashboard
    score = calculator.display_kpi_dashboard(kpis)

    # Generate report
    report = calculator.generate_finops_report(kpis)

    # Create visualization
    calculator.create_kpi_dashboard_visualization(kpis)

    # Summary and recommendations
    print("\n" + "=" * 70)
    print("📈 FinOps Maturity Roadmap")
    print("=" * 70)

    print("\n📍 Level 1: Inform (0-40 points, 1-3 months)")
    print("   • Enable Cost Explorer")
    print("   • Create basic budgets and alerts")
    print("   • Start tagging resources (>50% coverage)")
    print("   • Monthly cost reviews with leadership")

    print("\n📍 Level 2: Optimize (40-60 points, 3-6 months)")
    print("   • RI/SP coverage >60%")
    print("   • Implement lifecycle policies")
    print("   • Right-size based on utilization")
    print("   • Tagging compliance >80%")
    print("   • Weekly cost reviews with engineering")

    print("\n📍 Level 3: Operate (60-80 points, 6-12 months)")
    print("   • Automated cleanup (>80% coverage)")
    print("   • Commitment utilization >85%")
    print("   • Anomaly detection with auto-remediation")
    print("   • FinOps culture embedded in teams")
    print("   • Daily monitoring, monthly optimization sprints")

    print("\n📍 Level 4: Run (80-100 points, 12+ months)")
    print("   • Predictive cost forecasting")
    print("   • Unit economics tracked per feature")
    print("   • Showback/chargeback to teams")
    print("   • FinOps KPIs in OKRs")
    print("   • Continuous improvement culture")

    print("\n" + "=" * 70)
    print("💰 Real-World Example: 200-Person Engineering Org")
    print("=" * 70)

    print("\n   Baseline: $50,000/month AWS spend")
    print("\n   Governance Measures:")
    print("     • Team budgets: 10 teams × $5K each")
    print("     • Daily cleanup: Lambda automation")
    print("     • SCPs: Deny >4xlarge, require tags")
    print("     • Alerts: Slack notifications to 90% of engineers")
    print("     • Reviews: Weekly dashboard, monthly optimization")

    print("\n   Results After 6 Months:")
    print("     • Untagged: 40% → 3% 📉")
    print("     • Commitment coverage: 45% → 78% 📈")
    print("     • Waste ratio: 22% → 8% 📉")
    print("     • Monthly spend: $50K → $38K 💰")
    print("     • Engineering time: 8h/week → 2h/week ⏱️")

    print("\n   ROI:")
    print("     • Implementation: 120 hours ($12K)")
    print("     • Annual savings: $144K (24% reduction)")
    print("     • Payback period: 1 month")
    print("     • 3-year ROI: 3,500%")

if __name__ == '__main__':
    main()
