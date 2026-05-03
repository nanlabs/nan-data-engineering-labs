#!/usr/bin/env python3
"""
Cost Explorer Analysis
Query and analyze AWS costs using the Cost Explorer API
"""

import boto3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import sys
from typing import Dict

# Set plotting style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)

class CostExplorerAnalyzer:
    """Analyze AWS costs using Cost Explorer API"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize Cost Explorer client"""
        self.ce = boto3.client('ce', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity()['Account']

    def get_monthly_costs_by_service(self, months: int = 6) -> pd.DataFrame:
        """
        Get monthly costs grouped by service

        Args:
            months: Number of months to retrieve

        Returns:
            DataFrame with Period, Service, Cost, Usage columns
        """
        print(f"\n📊 Querying Cost Explorer for last {months} months...")

        end = datetime.now().date()
        start = (end - timedelta(days=months*30)).replace(day=1)

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
        except Exception as e:
            print(f"❌ Error querying Cost Explorer: {e}")
            print("   Ensure you have ce:GetCostAndUsage permission")
            sys.exit(1)

        # Parse results
        costs = []
        for result in response['ResultsByTime']:
            period = result['TimePeriod']['Start']

            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                usage = float(group['Metrics']['UsageQuantity']['Amount'])

                costs.append({
                    'Period': period,
                    'Service': service,
                    'Cost': cost,
                    'Usage': usage
                })

        df = pd.DataFrame(costs)
        print(f"✅ Retrieved {len(df)} cost records")

        return df

    def get_daily_costs(self, days: int = 30) -> pd.DataFrame:
        """
        Get daily costs for trend analysis

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with Date, Cost columns
        """
        print(f"\n📅 Querying daily costs for last {days} days...")

        end = datetime.now().date()
        start = end - timedelta(days=days)

        response = self.ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )

        # Parse results
        daily_costs = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            cost = float(result['Total']['UnblendedCost']['Amount'])
            daily_costs.append({'Date': date, 'Cost': cost})

        df = pd.DataFrame(daily_costs)
        df['Date'] = pd.to_datetime(df['Date'])

        # Calculate moving averages
        df['MA7'] = df['Cost'].rolling(window=7).mean()
        df['MA30'] = df['Cost'].rolling(window=30).mean() if days >= 30 else None

        print(f"✅ Retrieved {len(df)} daily records")

        return df

    def get_costs_by_tag(self, tag_key: str, tag_value: str = None) -> pd.DataFrame:
        """
        Get costs grouped by cost allocation tag

        Args:
            tag_key: Tag key to group by (e.g., 'Team', 'Project', 'Environment')
            tag_value: Optional specific tag value to filter

        Returns:
            DataFrame with tag values and costs
        """
        print(f"\n🏷️  Querying costs by tag: {tag_key}")

        # Get current month
        start = datetime.now().date().replace(day=1)
        end = datetime.now().date()

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'TAG', 'Key': tag_key}
                ]
            )
        except Exception as e:
            print("⚠️  Warning: Cost allocation tags may not be activated yet")
            print(f"   Error: {e}")
            return pd.DataFrame()

        # Parse results
        costs = []
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                tag = group['Keys'][0].split('$')[1] if '$' in group['Keys'][0] else 'No Tag'
                cost = float(group['Metrics']['UnblendedCost']['Amount'])

                if tag_value is None or tag == tag_value:
                    costs.append({
                        'TagKey': tag_key,
                        'TagValue': tag,
                        'Cost': cost
                    })

        df = pd.DataFrame(costs)
        print(f"✅ Retrieved costs for {len(df)} tag values")

        return df

    def analyze_top_cost_drivers(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        Identify top cost drivers from cost data

        Args:
            df: DataFrame with Service and Cost columns
            top_n: Number of top services to return

        Returns:
            DataFrame with top services sorted by cost
        """
        print(f"\n🔝 Analyzing top {top_n} cost drivers...")

        # Group by service and sum costs
        service_costs = df.groupby('Service')['Cost'].sum().sort_values(ascending=False).head(top_n)

        total_cost = df['Cost'].sum()

        # Create summary DataFrame
        top_services = pd.DataFrame({
            'Service': service_costs.index,
            'TotalCost': service_costs.values,
            'Percentage': (service_costs.values / total_cost * 100).round(2)
        })

        print(f"\n💰 Top {top_n} Services by Cost:")
        for idx, row in top_services.iterrows():
            print(f"  {row['Service']}: ${row['TotalCost']:,.2f} ({row['Percentage']}%)")

        print(f"\n📈 Top {top_n} services account for {top_services['Percentage'].sum():.1f}% of total costs")

        return top_services

    def get_cost_forecast(self, months_ahead: int = 3) -> pd.DataFrame:
        """
        Get AWS cost forecast for future months

        Args:
            months_ahead: Number of months to forecast

        Returns:
            DataFrame with forecast data
        """
        print(f"\n🔮 Querying cost forecast for next {months_ahead} months...")

        start = datetime.now().date()
        end = start + timedelta(days=months_ahead * 30)

        try:
            response = self.ce.get_cost_forecast(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
        except Exception as e:
            print(f"⚠️  Forecast unavailable: {e}")
            return pd.DataFrame()

        # Parse results
        forecasts = []
        for result in response['ForecastResultsByTime']:
            period = result['TimePeriod']['Start']
            mean_value = float(result['MeanValue'])

            forecasts.append({
                'Period': period,
                'ForecastedCost': mean_value
            })

        df = pd.DataFrame(forecasts)

        print("\n📊 Forecasted Costs:")
        for idx, row in df.iterrows():
            print(f"  {row['Period']}: ${row['ForecastedCost']:,.2f}")

        return df

    def calculate_cost_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for cost data

        Args:
            df: DataFrame with Cost column

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total': df['Cost'].sum(),
            'mean': df['Cost'].mean(),
            'median': df['Cost'].median(),
            'std': df['Cost'].std(),
            'min': df['Cost'].min(),
            'max': df['Cost'].max(),
            'records': len(df)
        }

        print("\n📊 Cost Statistics:")
        print(f"  Total: ${stats['total']:,.2f}")
        print(f"  Average: ${stats['mean']:,.2f}")
        print(f"  Median: ${stats['median']:,.2f}")
        print(f"  Std Dev: ${stats['std']:,.2f}")
        print(f"  Range: ${stats['min']:,.2f} - ${stats['max']:,.2f}")
        print(f"  Records: {stats['records']}")

        return stats

def main():
    """Main analysis workflow"""
    print("=" * 70)
    print("AWS Cost Explorer Analysis")
    print("=" * 70)

    analyzer = CostExplorerAnalyzer()

    # 1. Get monthly costs by service
    monthly_df = analyzer.get_monthly_costs_by_service(months=6)

    # 2. Analyze top cost drivers
    top_services = analyzer.analyze_top_cost_drivers(monthly_df, top_n=10)

    # 3. Get daily costs for trend analysis
    daily_df = analyzer.get_daily_costs(days=30)

    # 4. Calculate statistics
    stats = analyzer.calculate_cost_statistics(daily_df)

    # 5. Check for trend
    recent_avg = daily_df['Cost'].iloc[-7:].mean()
    older_avg = daily_df['Cost'].iloc[:7].mean()
    trend = "📈 Increasing" if recent_avg > older_avg else "📉 Decreasing"
    change = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

    print("\n📈 Cost Trend Analysis:")
    print(f"  Recent 7-day avg: ${recent_avg:.2f}/day")
    print(f"  Older 7-day avg: ${older_avg:.2f}/day")
    print(f"  Trend: {trend} ({change:+.1f}%)")

    # 6. Get cost forecast
    forecast_df = analyzer.get_cost_forecast(months_ahead=3)

    # 7. Try to get costs by tag (may fail if tags not activated)
    for tag_key in ['Team', 'Environment', 'Project']:
        tag_df = analyzer.get_costs_by_tag(tag_key)
        if not tag_df.empty:
            print(f"\n💰 Cost by {tag_key}:")
            for idx, row in tag_df.iterrows():
                print(f"  {row['TagValue']}: ${row['Cost']:,.2f}")

    # 8. Save results
    monthly_df.to_csv('cost-explorer-monthly.csv', index=False)
    daily_df.to_csv('cost-explorer-daily.csv', index=False)
    top_services.to_csv('top-cost-drivers.csv', index=False)

    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print("\n📁 Output Files:")
    print("  - cost-explorer-monthly.csv")
    print("  - cost-explorer-daily.csv")
    print("  - top-cost-drivers.csv")

    # Summary
    print("\n📊 Summary:")
    print(f"  Total spend (last 6 months): ${monthly_df['Cost'].sum():,.2f}")
    print(f"  Average daily cost: ${stats['mean']:,.2f}")
    print(f"  Top service: {top_services.iloc[0]['Service']} (${top_services.iloc[0]['TotalCost']:,.2f}, {top_services.iloc[0]['Percentage']}%)")
    print(f"  Cost trend: {trend}")

if __name__ == '__main__':
    main()
