"""
Weekly Reporting Lambda for RideShare Analytics Platform

This Lambda function supports the weekly reporting workflow by:
1. Checking data availability for the past 7 days
2. Processing Athena query results to calculate weekly KPIs
3. Generating personalized reports for stakeholders

Functions:
- check_data_availability: Verify data completeness
- process_athena_results: Calculate weekly KPIs and growth metrics
- generate_personalized_report: Create HTML/PDF reports

Author: RideShare Analytics Team
Version: 1.0.0
"""

import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
import boto3
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
athena = boto3.client('athena')

# Environment variables
METRICS_TABLE = os.environ.get('METRICS_TABLE', 'rideshare_aggregated_metrics')
REPORTS_BUCKET = os.environ.get('REPORTS_BUCKET', 'rideshare-analytics-reports')
ATHENA_RESULTS_BUCKET = os.environ.get('ATHENA_RESULTS_BUCKET', 'rideshare-athena-results')

# Constants
DAYS_TO_CHECK = 7
MIN_DATA_COMPLETENESS_PCT = 95.0


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON-serializable types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for weekly reporting operations

    Args:
        event: Input containing action and parameters
        context: Lambda execution context

    Returns:
        Dictionary with results based on action
    """
    try:
        logger.info(f"Weekly reporting lambda invoked with event: {json.dumps(event, cls=DecimalEncoder)}")

        action = event.get('action')

        if action == 'check_data_availability':
            return check_data_availability(event)
        elif action == 'process_athena_results':
            return process_athena_results(event)
        elif action == 'generate_personalized_report':
            return generate_personalized_report(event)
        else:
            raise ValueError(f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Error in weekly reporting lambda: {str(e)}", exc_info=True)
        raise


def check_data_availability(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if data is available for the past N days

    Verifies that each day has sufficient data by checking for daily metrics
    in the aggregated_metrics table. Ensures data quality before generating reports.

    Args:
        event: Contains days_back parameter

    Returns:
        Dictionary with availability status and missing days
    """
    days_back = event.get('days_back', DAYS_TO_CHECK)
    execution_id = event.get('execution_id', 'unknown')

    logger.info(f"Checking data availability for past {days_back} days")

    table = dynamodb.Table(METRICS_TABLE)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days_back)

    # Check each day
    missing_days = []
    days_with_data = []

    current_date = start_date
    while current_date <= end_date:
        # Query for daily metrics for this date
        date_str = current_date.strftime('%Y-%m-%d')

        # Check for rides_daily metric
        response = table.query(
            IndexName='metric_type_timestamp_index',  # Assumes GSI exists
            KeyConditionExpression=Key('metric_type').eq('rides_daily') &
                                  Key('timestamp').between(
                                      int(datetime.combine(current_date, datetime.min.time()).timestamp()),
                                      int(datetime.combine(current_date, datetime.max.time()).timestamp())
                                  )
        )

        if response.get('Count', 0) > 0:
            days_with_data.append(date_str)
            logger.info(f"Data found for {date_str}")
        else:
            missing_days.append(date_str)
            logger.warning(f"No data found for {date_str}")

        current_date += timedelta(days=1)

    # Calculate completeness
    total_days = days_back + 1  # Include today
    data_completeness_pct = (len(days_with_data) / total_days) * 100
    data_available = data_completeness_pct >= MIN_DATA_COMPLETENESS_PCT

    result = {
        'statusCode': 200,
        'data_available': data_available,
        'completeness_pct': round(data_completeness_pct, 2),
        'days_checked': total_days,
        'days_with_data': len(days_with_data),
        'missing_days': missing_days,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'execution_id': execution_id
    }

    logger.info(f"Data availability check completed: {json.dumps(result, cls=DecimalEncoder)}")
    return result


def process_athena_results(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Athena query results and calculate weekly KPIs

    Fetches results from S3, parses CSV data, and calculates:
    - Total rides and revenue for the week
    - Week-over-week growth percentages
    - Top performing cities
    - Revenue trends and patterns
    - Customer insights

    Args:
        event: Contains query_execution_id and output_location

    Returns:
        Dictionary with calculated KPIs and insights
    """
    query_execution_id = event.get('query_execution_id')
    output_location = event.get('output_location')
    date_range = event.get('date_range', {})

    logger.info(f"Processing Athena results for query: {query_execution_id}")

    # Parse S3 location
    if output_location.startswith('s3://'):
        output_location = output_location[5:]

    bucket_name = output_location.split('/')[0]
    key = '/'.join(output_location.split('/')[1:])

    # Fetch results from S3
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        results_data = response['Body'].read().decode('utf-8')
        logger.info(f"Fetched {len(results_data)} bytes from S3")
    except Exception as e:
        logger.error(f"Error fetching Athena results from S3: {str(e)}")
        raise

    # Parse CSV results
    lines = results_data.strip().split('\n')
    if len(lines) < 2:
        raise ValueError("No data rows in Athena results")

    headers = lines[0].split(',')
    rows = [line.split(',') for line in lines[1:]]

    logger.info(f"Parsed {len(rows)} data rows")

    # Calculate KPIs
    total_rides = 0
    total_revenue = 0
    completed_rides = 0
    city_metrics = {}
    daily_metrics = {}
    payment_method_revenue = {}

    for row in rows:
        # Parse row data (assumes specific column order from query)
        try:
            date = row[0]
            city = row[1]
            rides = int(row[2])
            completed = int(row[3])
            avg_duration = float(row[4])
            revenue = float(row[5])
            payment_method = row[6] if len(row) > 6 else 'unknown'
            transaction_count = int(row[7]) if len(row) > 7 else 0
            payment_amount = float(row[8]) if len(row) > 8 else 0

            # Aggregate totals
            total_rides += rides
            completed_rides += completed
            total_revenue += revenue

            # Aggregate by city
            if city not in city_metrics:
                city_metrics[city] = {
                    'rides': 0,
                    'completed': 0,
                    'revenue': 0
                }
            city_metrics[city]['rides'] += rides
            city_metrics[city]['completed'] += completed
            city_metrics[city]['revenue'] += revenue

            # Aggregate by date
            if date not in daily_metrics:
                daily_metrics[date] = {
                    'rides': 0,
                    'revenue': 0
                }
            daily_metrics[date]['rides'] += rides
            daily_metrics[date]['revenue'] += revenue

            # Aggregate by payment method
            if payment_method not in payment_method_revenue:
                payment_method_revenue[payment_method] = 0
            payment_method_revenue[payment_method] += payment_amount

        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing row: {row}, error: {str(e)}")
            continue

    # Calculate averages
    avg_rides_per_day = total_rides / len(daily_metrics) if daily_metrics else 0
    avg_revenue_per_day = total_revenue / len(daily_metrics) if daily_metrics else 0
    completion_rate = (completed_rides / total_rides * 100) if total_rides > 0 else 0

    # Calculate week-over-week growth (requires previous week's data)
    # For this example, we'll fetch previous week from DynamoDB
    previous_week_metrics = fetch_previous_week_metrics()
    wow_growth_rides = calculate_wow_growth(total_rides, previous_week_metrics.get('total_rides', 0))
    wow_growth_revenue = calculate_wow_growth(total_revenue, previous_week_metrics.get('total_revenue', 0))

    # Rank cities
    city_rankings = sorted(
        [
            {
                'city': city,
                'rides': metrics['rides'],
                'revenue': round(metrics['revenue'], 2),
                'avg_revenue_per_ride': round(metrics['revenue'] / metrics['rides'], 2) if metrics['rides'] > 0 else 0
            }
            for city, metrics in city_metrics.items()
        ],
        key=lambda x: x['revenue'],
        reverse=True
    )[:10]

    # Calculate revenue trends
    revenue_trend = [
        {
            'date': date,
            'revenue': round(metrics['revenue'], 2),
            'rides': metrics['rides']
        }
        for date, metrics in sorted(daily_metrics.items())
    ]

    result = {
        'statusCode': 200,
        'kpis': {
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'total_revenue': round(total_revenue, 2),
            'avg_rides_per_day': round(avg_rides_per_day, 2),
            'avg_revenue_per_day': round(avg_revenue_per_day, 2),
            'completion_rate_pct': round(completion_rate, 2),
            'unique_cities': len(city_metrics)
        },
        'weekly_summary': {
            'date_range': date_range,
            'total_days': len(daily_metrics),
            'by_payment_method': {
                method: round(amount, 2)
                for method, amount in payment_method_revenue.items()
            }
        },
        'city_rankings': city_rankings,
        'growth_metrics': {
            'wow_growth_pct': round(wow_growth_rides, 2),
            'wow_revenue_growth_pct': round(wow_growth_revenue, 2),
            'trend': 'up' if wow_growth_rides > 0 else 'down'
        },
        'revenue_trend': revenue_trend
    }

    logger.info(f"Athena results processed successfully: {json.dumps(result, cls=DecimalEncoder)}")
    return result


def fetch_previous_week_metrics() -> Dict[str, Any]:
    """
    Fetch metrics from the previous week for comparison

    Returns:
        Dictionary with previous week's metrics
    """
    try:
        table = dynamodb.Table(METRICS_TABLE)

        # Calculate previous week's date range
        end_date = datetime.utcnow().date() - timedelta(days=7)
        start_date = end_date - timedelta(days=7)

        # Query weekly summary metric if it exists
        response = table.query(
            IndexName='metric_type_timestamp_index',
            KeyConditionExpression=Key('metric_type').eq('weekly_summary') &
                                  Key('timestamp').between(
                                      int(datetime.combine(start_date, datetime.min.time()).timestamp()),
                                      int(datetime.combine(end_date, datetime.max.time()).timestamp())
                                  )
        )

        if response.get('Count', 0) > 0:
            item = response['Items'][0]
            return {
                'total_rides': int(item.get('total_rides', 0)),
                'total_revenue': float(item.get('total_revenue', 0))
            }
        else:
            logger.warning("No previous week metrics found")
            return {'total_rides': 0, 'total_revenue': 0}

    except Exception as e:
        logger.warning(f"Error fetching previous week metrics: {str(e)}")
        return {'total_rides': 0, 'total_revenue': 0}


def calculate_wow_growth(current: float, previous: float) -> float:
    """
    Calculate week-over-week growth percentage

    Args:
        current: Current week value
        previous: Previous week value

    Returns:
        Growth percentage
    """
    if previous == 0:
        return 0 if current == 0 else 100
    return ((current - previous) / previous) * 100


def generate_personalized_report(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a personalized report for a stakeholder

    Creates HTML and PDF reports customized based on stakeholder role:
    - Executive: High-level KPIs and trends
    - Operations: Detailed operational metrics
    - Finance: Revenue and payment analysis
    - Product: User engagement and features

    Args:
        event: Contains stakeholder info and KPIs

    Returns:
        Dictionary with report HTML, PDF URL, and summary
    """
    stakeholder = event.get('stakeholder', {})
    kpis = event.get('kpis', {})
    weekly_summary = event.get('weekly_summary', {})
    city_rankings = event.get('city_rankings', [])
    growth_metrics = event.get('growth_metrics', {})

    stakeholder_name = stakeholder.get('name', 'Stakeholder')
    stakeholder_role = stakeholder.get('role', 'general')
    stakeholder_email = stakeholder.get('email', 'unknown@example.com')

    logger.info(f"Generating personalized report for {stakeholder_name} ({stakeholder_role})")

    # Generate report based on role
    if stakeholder_role == 'executive':
        report_html = generate_executive_report(stakeholder_name, kpis, growth_metrics, city_rankings)
        report_title = "Executive Weekly Summary"
    elif stakeholder_role == 'operations':
        report_html = generate_operations_report(stakeholder_name, kpis, weekly_summary, city_rankings)
        report_title = "Operations Weekly Report"
    elif stakeholder_role == 'finance':
        report_html = generate_finance_report(stakeholder_name, kpis, weekly_summary, growth_metrics)
        report_title = "Finance Weekly Report"
    else:
        report_html = generate_general_report(stakeholder_name, kpis, city_rankings)
        report_title = "Weekly Analytics Report"

    # Save report to S3
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    report_key = f"weekly-reports/{stakeholder_role}/{timestamp}_{stakeholder_name.replace(' ', '_')}.html"

    try:
        s3.put_object(
            Bucket=REPORTS_BUCKET,
            Key=report_key,
            Body=report_html.encode('utf-8'),
            ContentType='text/html',
            Metadata={
                'stakeholder': stakeholder_name,
                'role': stakeholder_role,
                'report_date': timestamp
            }
        )

        report_pdf_url = f"https://{REPORTS_BUCKET}.s3.amazonaws.com/{report_key}"
        logger.info(f"Report saved to S3: {report_key}")

    except Exception as e:
        logger.error(f"Error saving report to S3: {str(e)}")
        report_pdf_url = "Report generation failed"

    # Generate summary for email
    report_summary = generate_report_summary(kpis, growth_metrics)

    result = {
        'statusCode': 200,
        'report_html': report_html[:1000] + '...',  # Truncate for Step Functions
        'report_pdf_url': report_pdf_url,
        'report_summary': report_summary,
        'report_title': report_title,
        'stakeholder': stakeholder_name
    }

    logger.info(f"Personalized report generated for {stakeholder_name}")
    return result


def generate_executive_report(name: str, kpis: Dict, growth: Dict, cities: List) -> str:
    """Generate HTML report for executives"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Executive Weekly Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            .kpi {{ background: #ecf0f1; padding: 20px; margin: 10px 0; border-radius: 5px; }}
            .positive {{ color: #27ae60; }}
            .negative {{ color: #e74c3c; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
        </style>
    </head>
    <body>
        <h1>Weekly Executive Summary</h1>
        <p>Dear {name},</p>
        <p>Here is your weekly RideShare analytics summary:</p>

        <div class="kpi">
            <h2>Key Performance Indicators</h2>
            <p><strong>Total Rides:</strong> {kpis.get('total_rides', 0):,}</p>
            <p><strong>Total Revenue:</strong> ${kpis.get('total_revenue', 0):,.2f}</p>
            <p><strong>Week-over-Week Growth:</strong>
                <span class="{'positive' if growth.get('wow_growth_pct', 0) > 0 else 'negative'}">
                    {growth.get('wow_growth_pct', 0):+.2f}%
                </span>
            </p>
        </div>

        <h2>Top Performing Cities</h2>
        <table>
            <tr><th>Rank</th><th>City</th><th>Revenue</th><th>Rides</th></tr>
"""

    for i, city in enumerate(cities[:5], 1):
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{city.get('city', 'Unknown')}</td>
                <td>${city.get('revenue', 0):,.2f}</td>
                <td>{city.get('rides', 0):,}</td>
            </tr>
"""

    html += """
        </table>
    </body>
    </html>
    """
    return html


def generate_operations_report(name: str, kpis: Dict, summary: Dict, cities: List) -> str:
    """Generate HTML report for operations team"""
    return f"""<html><body><h1>Operations Report</h1><p>Dear {name},</p>
    <p>Completion Rate: {kpis.get('completion_rate_pct', 0)}%</p>
    <p>Avg Rides per Day: {kpis.get('avg_rides_per_day', 0)}</p></body></html>"""


def generate_finance_report(name: str, kpis: Dict, summary: Dict, growth: Dict) -> str:
    """Generate HTML report for finance team"""
    return f"""<html><body><h1>Finance Report</h1><p>Dear {name},</p>
    <p>Total Revenue: ${kpis.get('total_revenue', 0):,.2f}</p>
    <p>Revenue Growth: {growth.get('wow_revenue_growth_pct', 0):+.2f}%</p></body></html>"""


def generate_general_report(name: str, kpis: Dict, cities: List) -> str:
    """Generate HTML report for general stakeholders"""
    return f"""<html><body><h1>Weekly Report</h1><p>Dear {name},</p>
    <p>Total Rides: {kpis.get('total_rides', 0):,}</p>
    <p>Total Revenue: ${kpis.get('total_revenue', 0):,.2f}</p></body></html>"""


def generate_report_summary(kpis: Dict, growth: Dict) -> str:
    """Generate text summary for email"""
    return f"""
Weekly Summary:
- Total Rides: {kpis.get('total_rides', 0):,}
- Total Revenue: ${kpis.get('total_revenue', 0):,.2f}
- Week-over-Week Growth: {growth.get('wow_growth_pct', 0):+.2f}%
- Completion Rate: {kpis.get('completion_rate_pct', 0):.1f}%
    """.strip()
