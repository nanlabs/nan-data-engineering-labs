#!/usr/bin/env python3
"""
Snowflake Cost Monitoring Tool

This script tracks and reports Snowflake credit usage and costs by querying
the ACCOUNT_USAGE schema. It provides insights into:
- Warehouse compute usage
- Storage costs
- Snowpipe usage
- Cost trends and forecasts
- Budget alerts

Usage:
    python monitor_costs.py --account xy12345.us-east-1
    python monitor_costs.py --days 30 --output costs.csv
    python monitor_costs.py --warehouse TRAINING_WH --alert-threshold 75
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import snowflake.connector
except ImportError:
    print("ERROR: snowflake-connector-python not installed")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Default cost rates (can be overridden)
DEFAULT_CREDIT_RATE = 3.0  # USD per credit
DEFAULT_STORAGE_RATE = 23.0  # USD per TB per month


class SnowflakeCostMonitor:
    """Monitor and report Snowflake costs."""

    def __init__(
        self,
        account: str,
        username: str,
        password: str,
        role: str = "ACCOUNTADMIN",
        warehouse: str = "COMPUTE_WH",
        credit_rate: float = DEFAULT_CREDIT_RATE,
        storage_rate: float = DEFAULT_STORAGE_RATE
    ):
        """
        Initialize the cost monitor.

        Args:
            account: Snowflake account identifier
            username: Snowflake username
            password: Snowflake password
            role: Role to use for queries (default: ACCOUNTADMIN)
            warehouse: Warehouse to use (default: COMPUTE_WH)
            credit_rate: Cost per compute credit in USD
            storage_rate: Cost per TB storage per month in USD
        """
        self.account = account
        self.username = username
        self.password = password
        self.role = role
        self.warehouse = warehouse
        self.credit_rate = credit_rate
        self.storage_rate = storage_rate
        self.connection = None

    def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            logger.info(f"Connecting to Snowflake account: {self.account}")
            self.connection = snowflake.connector.connect(
                account=self.account,
                user=self.username,
                password=self.password,
                role=self.role,
                warehouse=self.warehouse
            )
            logger.info("✓ Connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection to Snowflake."""
        if self.connection:
            self.connection.close()
            logger.info("✓ Disconnected from Snowflake")

    def execute_query(self, query: str) -> List[Tuple]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute

        Returns:
            List of result tuples
        """
        if not self.connection:
            raise RuntimeError("Not connected to Snowflake")

        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()

    def get_warehouse_usage(self, days: int = 30) -> List[Dict]:
        """
        Get warehouse compute usage for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            List of usage dictionaries
        """
        logger.info(f"Fetching warehouse usage for last {days} days...")

        query = f"""
        SELECT
            DATE(start_time) as usage_date,
            warehouse_name,
            SUM(credits_used) as total_credits,
            COUNT(*) as num_queries
        FROM snowflake.account_usage.warehouse_metering_history
        WHERE start_time >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        GROUP BY DATE(start_time), warehouse_name
        ORDER BY usage_date DESC, total_credits DESC
        """

        results = self.execute_query(query)

        usage_data = []
        for row in results:
            usage_data.append({
                'date': row[0],
                'warehouse': row[1],
                'credits': round(row[2], 4),
                'queries': row[3],
                'cost': round(row[2] * self.credit_rate, 2)
            })

        logger.info(f"✓ Retrieved {len(usage_data)} usage records")
        return usage_data

    def get_warehouse_summary(self, days: int = 30) -> List[Dict]:
        """
        Get summary of warehouse usage by warehouse.

        Args:
            days: Number of days to look back

        Returns:
            List of warehouse summary dictionaries
        """
        logger.info(f"Calculating warehouse summary for last {days} days...")

        query = f"""
        SELECT
            warehouse_name,
            SUM(credits_used) as total_credits,
            AVG(credits_used_compute) as avg_compute_credits,
            AVG(credits_used_cloud_services) as avg_cloud_credits,
            COUNT(*) as num_records
        FROM snowflake.account_usage.warehouse_metering_history
        WHERE start_time >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        GROUP BY warehouse_name
        ORDER BY total_credits DESC
        """

        results = self.execute_query(query)

        summary = []
        for row in results:
            summary.append({
                'warehouse': row[0],
                'total_credits': round(row[1], 4),
                'avg_compute_credits': round(row[2] or 0, 4),
                'avg_cloud_credits': round(row[3] or 0, 4),
                'num_records': row[4],
                'total_cost': round(row[1] * self.credit_rate, 2)
            })

        logger.info(f"✓ Summarized {len(summary)} warehouses")
        return summary

    def get_storage_usage(self) -> Dict:
        """
        Get current storage usage and costs.

        Returns:
            Dictionary with storage statistics
        """
        logger.info("Fetching storage usage...")

        query = """
        SELECT
            usage_date,
            storage_bytes + stage_bytes + failsafe_bytes as total_bytes,
            storage_bytes,
            stage_bytes,
            failsafe_bytes
        FROM snowflake.account_usage.storage_usage
        WHERE usage_date >= DATEADD(day, -2, CURRENT_DATE())
        ORDER BY usage_date DESC
        LIMIT 1
        """

        results = self.execute_query(query)

        if not results:
            logger.warning("⚠ No storage usage data available")
            return {}

        row = results[0]
        total_tb = row[1] / (1024 ** 4)  # Convert bytes to TB
        storage_tb = row[2] / (1024 ** 4)
        stage_tb = row[3] / (1024 ** 4)
        failsafe_tb = row[4] / (1024 ** 4)

        # Estimate monthly cost (assuming 30 days)
        monthly_cost = total_tb * self.storage_rate

        storage_data = {
            'date': row[0],
            'total_tb': round(total_tb, 4),
            'storage_tb': round(storage_tb, 4),
            'stage_tb': round(stage_tb, 4),
            'failsafe_tb': round(failsafe_tb, 4),
            'monthly_cost': round(monthly_cost, 2)
        }

        logger.info(f"✓ Storage usage: {storage_data['total_tb']:.4f} TB")
        return storage_data

    def get_snowpipe_usage(self, days: int = 30) -> List[Dict]:
        """
        Get Snowpipe usage for data loading.

        Args:
            days: Number of days to look back

        Returns:
            List of Snowpipe usage dictionaries
        """
        logger.info(f"Fetching Snowpipe usage for last {days} days...")

        query = f"""
        SELECT
            DATE(start_time) as usage_date,
            pipe_name,
            SUM(credits_used) as total_credits,
            SUM(bytes_inserted) as total_bytes,
            SUM(files_inserted) as total_files
        FROM snowflake.account_usage.pipe_usage_history
        WHERE start_time >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        GROUP BY DATE(start_time), pipe_name
        ORDER BY usage_date DESC, total_credits DESC
        """

        try:
            results = self.execute_query(query)

            pipe_data = []
            for row in results:
                pipe_data.append({
                    'date': row[0],
                    'pipe_name': row[1],
                    'credits': round(row[2], 4),
                    'bytes_inserted': row[3],
                    'files_inserted': row[4],
                    'cost': round(row[2] * self.credit_rate, 2)
                })

            logger.info(f"✓ Retrieved {len(pipe_data)} Snowpipe records")
            return pipe_data
        except Exception as e:
            logger.warning(f"⚠ Could not fetch Snowpipe usage: {e}")
            return []

    def get_resource_monitor_status(self, monitor_name: str = None) -> List[Dict]:
        """
        Get status of resource monitors.

        Args:
            monitor_name: Optional specific monitor name to check

        Returns:
            List of resource monitor status dictionaries
        """
        logger.info("Checking resource monitor status...")

        query = """
        SELECT
            name,
            credit_quota,
            used_credits,
            remaining_credits,
            level,
            start_time,
            end_time
        FROM snowflake.account_usage.resource_monitors
        WHERE deleted IS NULL
        """

        if monitor_name:
            query += f" AND name = '{monitor_name}'"

        try:
            results = self.execute_query(query)

            monitors = []
            for row in results:
                used = row[2] or 0
                quota = row[1] or 0
                usage_pct = (used / quota * 100) if quota > 0 else 0

                monitors.append({
                    'name': row[0],
                    'credit_quota': row[1],
                    'used_credits': used,
                    'remaining_credits': row[3] or 0,
                    'usage_percentage': round(usage_pct, 2),
                    'level': row[4],
                    'start_time': row[5],
                    'end_time': row[6]
                })

            logger.info(f"✓ Retrieved {len(monitors)} resource monitors")
            return monitors
        except Exception as e:
            logger.warning(f"⚠ Could not fetch resource monitors: {e}")
            return []

    def calculate_total_costs(self, days: int = 30) -> Dict:
        """
        Calculate total costs across all services.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with cost breakdown
        """
        logger.info(f"Calculating total costs for last {days} days...")

        # Get warehouse costs
        warehouse_usage = self.get_warehouse_usage(days)
        warehouse_cost = sum(item['cost'] for item in warehouse_usage)
        warehouse_credits = sum(item['credits'] for item in warehouse_usage)

        # Get storage costs (prorated for the period)
        storage_data = self.get_storage_usage()
        storage_cost = (storage_data.get('monthly_cost', 0) / 30) * days if storage_data else 0

        # Get Snowpipe costs
        pipe_usage = self.get_snowpipe_usage(days)
        pipe_cost = sum(item['cost'] for item in pipe_usage)
        pipe_credits = sum(item['credits'] for item in pipe_usage)

        total_credits = warehouse_credits + pipe_credits
        total_cost = warehouse_cost + storage_cost + pipe_cost

        costs = {
            'period_days': days,
            'warehouse_credits': round(warehouse_credits, 4),
            'warehouse_cost': round(warehouse_cost, 2),
            'storage_cost': round(storage_cost, 2),
            'pipe_credits': round(pipe_credits, 4),
            'pipe_cost': round(pipe_cost, 2),
            'total_credits': round(total_credits, 4),
            'total_cost': round(total_cost, 2),
            'daily_avg_cost': round(total_cost / days, 2),
            'monthly_forecast': round(total_cost / days * 30, 2)
        }

        logger.info(f"✓ Total cost: ${costs['total_cost']:.2f}")
        return costs

    def check_alerts(self, threshold_pct: float = 75) -> List[Dict]:
        """
        Check for cost/usage alerts.

        Args:
            threshold_pct: Alert threshold percentage

        Returns:
            List of alert dictionaries
        """
        logger.info(f"Checking alerts (threshold: {threshold_pct}%)...")

        alerts = []

        # Check resource monitors
        monitors = self.get_resource_monitor_status()
        for monitor in monitors:
            if monitor['usage_percentage'] >= threshold_pct:
                alerts.append({
                    'type': 'RESOURCE_MONITOR',
                    'severity': 'HIGH' if monitor['usage_percentage'] >= 90 else 'MEDIUM',
                    'message': f"Resource monitor '{monitor['name']}' at {monitor['usage_percentage']:.1f}% of quota",
                    'details': monitor
                })

        logger.info(f"✓ Found {len(alerts)} alerts")
        return alerts


def print_table(headers: List[str], rows: List[List], title: str = None):
    """Print a formatted table."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"{title:^80}")
        print('=' * 80)

    if not rows:
        print("  No data available")
        return

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Print header
    header_row = " | ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    )
    print(f"\n{header_row}")
    print("-" * len(header_row))

    # Print rows
    for row in rows:
        print(" | ".join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(row))
        ))


def save_to_csv(data: List[Dict], filepath: Path, fieldnames: List[str]):
    """Save data to CSV file."""
    logger.info(f"Saving report to {filepath}...")

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"✓ Report saved ({len(data)} records)")


def generate_report(monitor: SnowflakeCostMonitor, args: argparse.Namespace):
    """Generate and display cost report."""

    print("\n" + "=" * 80)
    print(" " * 25 + "SNOWFLAKE COST REPORT")
    print("=" * 80)
    print(f"Account: {args.account}")
    print(f"Period: Last {args.days} days")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Total costs
    total_costs = monitor.calculate_total_costs(args.days)

    print("\n" + "-" * 80)
    print("COST SUMMARY")
    print("-" * 80)
    print(f"Compute (Warehouse): ${total_costs['warehouse_cost']:>10.2f}  ({total_costs['warehouse_credits']:.4f} credits)")
    print(f"Storage:             ${total_costs['storage_cost']:>10.2f}")
    print(f"Data Loading (Pipe): ${total_costs['pipe_cost']:>10.2f}  ({total_costs['pipe_credits']:.4f} credits)")
    print("-" * 80)
    print(f"TOTAL COST:          ${total_costs['total_cost']:>10.2f}  ({total_costs['total_credits']:.4f} credits)")
    print(f"Daily Average:       ${total_costs['daily_avg_cost']:>10.2f}")
    print(f"Monthly Forecast:    ${total_costs['monthly_forecast']:>10.2f}")
    print("-" * 80)

    # Warehouse summary
    warehouse_summary = monitor.get_warehouse_summary(args.days)
    if warehouse_summary:
        rows = [
            [
                w['warehouse'],
                f"{w['total_credits']:.4f}",
                f"${w['total_cost']:.2f}",
                f"{w['num_records']:,}"
            ]
            for w in warehouse_summary[:10]
        ]
        print_table(
            ["Warehouse", "Credits Used", "Cost", "Records"],
            rows,
            "TOP WAREHOUSES BY COST"
        )

    # Storage details
    storage = monitor.get_storage_usage()
    if storage:
        print(f"\n{'=' * 80}")
        print(f"{'STORAGE USAGE':^80}")
        print('=' * 80)
        print(f"Total Storage:  {storage['total_tb']:>10.4f} TB")
        print(f"  Database:     {storage['storage_tb']:>10.4f} TB")
        print(f"  Stages:       {storage['stage_tb']:>10.4f} TB")
        print(f"  Fail-safe:    {storage['failsafe_tb']:>10.4f} TB")
        print(f"Monthly Cost:   ${storage['monthly_cost']:>10.2f}")

    # Alerts
    alerts = monitor.check_alerts(args.alert_threshold)
    if alerts:
        print(f"\n{'=' * 80}")
        print(f"{'⚠ ALERTS':^80}")
        print('=' * 80)
        for alert in alerts:
            severity_symbol = "🔴" if alert['severity'] == 'HIGH' else "🟡"
            print(f"{severity_symbol} [{alert['severity']}] {alert['message']}")

    # Save to CSV if requested
    if args.output:
        warehouse_usage = monitor.get_warehouse_usage(args.days)
        output_path = Path(args.output)
        save_to_csv(
            warehouse_usage,
            output_path,
            ['date', 'warehouse', 'credits', 'queries', 'cost']
        )

    print("\n" + "=" * 80)
    print("✓ Report generation complete")
    print("=" * 80 + "\n")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Monitor Snowflake costs and credit usage',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--account',
        type=str,
        required=True,
        help='Snowflake account identifier'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Snowflake username (or set SNOWFLAKE_USER env var)'
    )
    parser.add_argument(
        '--password',
        type=str,
        help='Snowflake password (or set SNOWFLAKE_PASSWORD env var)'
    )
    parser.add_argument(
        '--role',
        type=str,
        default='ACCOUNTADMIN',
        help='Role to use (default: ACCOUNTADMIN)'
    )
    parser.add_argument(
        '--warehouse',
        type=str,
        default='COMPUTE_WH',
        help='Warehouse to use (default: COMPUTE_WH)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save detailed report to CSV file'
    )
    parser.add_argument(
        '--credit-rate',
        type=float,
        default=DEFAULT_CREDIT_RATE,
        help=f'Cost per credit in USD (default: ${DEFAULT_CREDIT_RATE})'
    )
    parser.add_argument(
        '--storage-rate',
        type=float,
        default=DEFAULT_STORAGE_RATE,
        help=f'Cost per TB/month in USD (default: ${DEFAULT_STORAGE_RATE})'
    )
    parser.add_argument(
        '--alert-threshold',
        type=float,
        default=75.0,
        help='Alert threshold percentage (default: 75%%)'
    )

    args = parser.parse_args()

    # Get credentials from environment if not provided
    username = args.username or os.getenv('SNOWFLAKE_USER')
    password = args.password or os.getenv('SNOWFLAKE_PASSWORD')

    if not username or not password:
        print("ERROR: Username and password required")
        print("Provide via --username/--password or SNOWFLAKE_USER/SNOWFLAKE_PASSWORD env vars")
        sys.exit(1)

    # Initialize monitor
    monitor = SnowflakeCostMonitor(
        account=args.account,
        username=username,
        password=password,
        role=args.role,
        warehouse=args.warehouse,
        credit_rate=args.credit_rate,
        storage_rate=args.storage_rate
    )

    try:
        monitor.connect()
        generate_report(monitor, args)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        monitor.disconnect()


if __name__ == '__main__':
    main()
