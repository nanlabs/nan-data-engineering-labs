# Exercise 03: Real-Time Dashboards

## Overview
Build interactive real-time dashboards using Amazon QuickSight, CloudWatch, and Grafana to visualize streaming analytics with sub-second updates.

**Difficulty**: ⭐⭐ Intermediate
**Duration**: ~2 hours
**Prerequisites**: Exercise 01 or 02, DynamoDB tables created

## Learning Objectives

- Connect QuickSight to DynamoDB for real-time dashboards
- Create CloudWatch custom metrics and dashboards
- Build Grafana dashboards with multiple data sources
- Configure auto-refresh and alerting
- Optimize dashboard query performance

## Key Concepts

- **SPICE**: QuickSight's in-memory calculation engine
- **CloudWatch Metrics**: Time-series monitoring data
- **Grafana Data Sources**: CloudWatch, Prometheus, JSON API
- **Auto-Refresh**: Automatic dashboard updates
- **Metric Dimensions**: Tags for filtering and grouping

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Flink      │      │    DynamoDB      │      │   QuickSight    │
│ Analytics    │─────>│  realtime-       │<────>│   Dashboard     │
│              │      │  aggregates      │      │  (1s refresh)   │
└──────────────┘      └──────────────────┘      └─────────────────┘
       │
       │ put_metric_data
       v
┌──────────────┐      ┌──────────────────┐
│  CloudWatch  │<────>│   CloudWatch     │
│   Metrics    │      │    Dashboard     │
└──────────────┘      └──────────────────┘
                                │
                                v
                      ┌──────────────────┐
                      │     Grafana      │
                      │  (Multi-source)  │
                      └──────────────────┘
```

## Setup

### Prerequisites Check

```bash
# Verify infrastructure
make status

# Check DynamoDB table exists
awslocal dynamodb describe-table \
    --table-name realtime-aggregates \
    --region us-east-1

# Verify Grafana is running
curl http://localhost:3000/api/health
```

## Task 1: Prepare Dashboard Data (15 minutes)

Write analytics results to DynamoDB continuously.

**File**: `populate_dashboard_data.py`

```python
#!/usr/bin/env python3
"""Populate DynamoDB with dashboard metrics"""

import boto3
import json
import time
import random
from datetime import datetime, timezone
from decimal import Decimal

# Initialize clients
dynamodb = boto3.resource('dynamodb',
                          endpoint_url='http://localhost:4566',
                          region_name='us-east-1')

table = dynamodb.Table('realtime-aggregates')

def generate_metrics():
    """Generate realistic dashboard metrics"""

    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())

    metrics = [
        {
            'metric_name': 'events_per_second',
            'metric_timestamp': timestamp,
            'metric_value': Decimal(str(random.uniform(50, 200))),
            'metadata': json.dumps({
                'source': 'kinesis',
                'shard_count': 4
            })
        },
        {
            'metric_name': 'revenue_per_minute',
            'metric_timestamp': timestamp,
            'metric_value': Decimal(str(random.uniform(1000, 5000))),
            'metadata': json.dumps({
                'currency': 'USD',
                'country': 'US'
            })
        },
        {
            'metric_name': 'unique_users_per_minute',
            'metric_timestamp': timestamp,
            'metric_value': Decimal(str(random.randint(100, 500))),
            'metadata': json.dumps({
                'active_sessions': random.randint(200, 800)
            })
        },
        {
            'metric_name': 'conversion_rate',
            'metric_timestamp': timestamp,
            'metric_value': Decimal(str(random.uniform(2.0, 8.0))),
            'metadata': json.dumps({
                'total_visitors': random.randint(1000, 3000),
                'purchases': random.randint(50, 200)
            })
        },
        {
            'metric_name': 'avg_page_load_time_ms',
            'metric_timestamp': timestamp,
            'metric_value': Decimal(str(random.uniform(100, 500))),
            'metadata': json.dumps({
                'p50': random.randint(150, 250),
                'p95': random.randint(400, 600),
                'p99': random.randint(600, 900)
            })
        }
    ]

    return metrics


def write_metrics_batch(metrics):
    """Write metrics to DynamoDB"""
    try:
        with table.batch_writer() as batch:
            for metric in metrics:
                batch.put_item(Item=metric)
        return True
    except Exception as e:
        print(f"Error writing metrics: {e}")
        return False


def continuous_metrics_generator(duration_seconds=3600):
    """Generate metrics continuously"""

    print(f"Generating dashboard metrics for {duration_seconds} seconds...")
    print("Press Ctrl+C to stop")

    start_time = time.time()
    iteration = 0

    try:
        while (time.time() - start_time) < duration_seconds:
            metrics = generate_metrics()

            if write_metrics_batch(metrics):
                iteration += 1
                if iteration % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = iteration / elapsed
                    print(f"  Wrote {iteration} batches ({rate:.1f} batches/sec)")

            time.sleep(1)  # Update every second

    except KeyboardInterrupt:
        print("\nStopped by user")

    total_time = time.time() - start_time
    print(f"\n✓ Generated {iteration} metric batches in {total_time:.1f}s")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=3600,
                       help='Duration in seconds (default: 1 hour)')
    args = parser.parse_args()

    continuous_metrics_generator(args.duration)
```

**Run the generator**:

```bash
# Generate metrics continuously
python populate_dashboard_data.py --duration 3600 &

# Or run in background with Makefile
make generate-dashboard-data
```

## Task 2: Create CloudWatch Dashboard (20 minutes)

Build a CloudWatch dashboard with custom metrics.

**File**: `create_cloudwatch_dashboard.py`

```python
#!/usr/bin/env python3
"""Create CloudWatch dashboard for real-time analytics"""

import boto3
import json

cloudwatch = boto3.client('cloudwatch',
                         endpoint_url='http://localhost:4566',
                         region_name='us-east-1')


def create_analytics_dashboard():
    """Create comprehensive analytics dashboard"""

    dashboard_body = {
        "widgets": [
            # Events per second - Line chart
            {
                "type": "metric",
                "x": 0, "y": 0,
                "width": 12, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "EventsPerSecond", {"stat": "Average"}],
                        [".", ".", {"stat": "Maximum", "color": "#ff7f0e"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Events Per Second",
                    "yAxis": {
                        "left": {"min": 0}
                    }
                }
            },

            # Revenue - Number widget
            {
                "type": "metric",
                "x": 12, "y": 0,
                "width": 6, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "RevenueUSD", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Revenue (5 min)",
                    "setPeriodToTimeRange": True,
                    "sparkline": True,
                    "view": "singleValue",
                    "yAxis": {
                        "left": {"min": 0}
                    }
                }
            },

            # Active users - Number widget
            {
                "type": "metric",
                "x": 18, "y": 0,
                "width": 6, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "UniqueUsers", {"stat": "Sum"}]
                    ],
                    "period": 60,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Active Users (1 min)",
                    "setPeriodToTimeRange": False,
                    "sparkline": True,
                    "view": "singleValue"
                }
            },

            # Stacked area chart - Events by type
            {
                "type": "metric",
                "x": 0, "y": 6,
                "width": 12, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "Events", {"stat": "Sum", "EventType": "page_view"}],
                        ["...", {"EventType": "click"}],
                        ["...", {"EventType": "add_to_cart"}],
                        ["...", {"EventType": "purchase"}]
                    ],
                    "period": 60,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Events by Type",
                    "yAxis": {
                        "left": {"min": 0}
                    },
                    "view": "timeSeries",
                    "stacked": True
                }
            },

            # Conversion rate - Line chart
            {
                "type": "metric",
                "x": 12, "y": 6,
                "width": 12, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "ConversionRate", {"stat": "Average"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Conversion Rate (%)",
                    "yAxis": {
                        "left": {"min": 0, "max": 100}
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Target",
                                "value": 5.0,
                                "fill": "above",
                                "color": "#2ca02c"
                            }
                        ]
                    }
                }
            },

            # Performance metrics - Bar chart
            {
                "type": "metric",
                "x": 0, "y": 12,
                "width": 8, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "LatencyMs", {"stat": "Average", "label": "Avg"}],
                        [".", ".", {"stat": "p50", "label": "p50"}],
                        [".", ".", {"stat": "p95", "label": "p95"}],
                        [".", ".", {"stat": "p99", "label": "p99"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Latency Distribution",
                    "yAxis": {
                        "left": {"label": "ms", "min": 0}
                    }
                }
            },

            # Error rate - Line chart with alarm annotation
            {
                "type": "metric",
                "x": 8, "y": 12,
                "width": 8, "height": 6,
                "properties": {
                    "metrics": [
                        ["Analytics", "ErrorRate", {"stat": "Average"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Error Rate (%)",
                    "yAxis": {
                        "left": {"min": 0, "max": 10}
                    },
                    "annotations": {
                        "horizontal": [
                            {
                                "label": "Critical",
                                "value": 5.0,
                                "fill": "above",
                                "color": "#d62728"
                            },
                            {
                                "label": "Warning",
                                "value": 1.0,
                                "fill": "above",
                                "color": "#ff7f0e"
                            }
                        ]
                    }
                }
            },

            # Top products table
            {
                "type": "log",
                "x": 16, "y": 12,
                "width": 8, "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/kinesis-analytics/flink-apps' | fields @timestamp, product_name, revenue | sort revenue desc | limit 10",
                    "region": "us-east-1",
                    "title": "Top 10 Products by Revenue",
                    "view": "table"
                }
            }
        ]
    }

    # Create dashboard
    try:
        response = cloudwatch.put_dashboard(
            DashboardName='RealTimeAnalytics',
            DashboardBody=json.dumps(dashboard_body)
        )

        print("✓ CloudWatch dashboard created successfully")
        print(f"  Dashboard ARN: {response.get('DashboardValidationMessages', [])}")
        print("  View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=RealTimeAnalytics")

        return True

    except Exception as e:
        print(f"✗ Error creating dashboard: {e}")
        return False


def publish_custom_metrics():
    """Publish custom metrics to CloudWatch"""

    import time
    import random
    from datetime import datetime

    print("Publishing custom metrics to CloudWatch...")

    for i in range(60):  # Publish for 1 minute
        try:
            cloudwatch.put_metric_data(
                Namespace='Analytics',
                MetricData=[
                    {
                        'MetricName': 'EventsPerSecond',
                        'Value': random.uniform(50, 200),
                        'Unit': 'Count/Second',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'RevenueUSD',
                        'Value': random.uniform(100, 500),
                        'Unit': 'None',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'UniqueUsers',
                        'Value': random.randint(10, 50),
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'ConversionRate',
                        'Value': random.uniform(3.0, 7.0),
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )

            if (i + 1) % 10 == 0:
                print(f"  Published {i + 1}/60 metric batches")

            time.sleep(1)

        except Exception as e:
            print(f"Error publishing metrics: {e}")

    print("✓ Metrics published successfully")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true',
                       help='Publish test metrics')
    args = parser.parse_args()

    # Create dashboard
    create_analytics_dashboard()

    # Optionally publish test data
    if args.publish:
        publish_custom_metrics()
```

**Deploy dashboard**:

```bash
# Create dashboard
python create_cloudwatch_dashboard.py

# Create dashboard and publish test metrics
python create_cloudwatch_dashboard.py --publish
```

## Task 3: Configure Grafana Dashboards (25 minutes)

Create Grafana dashboards with multiple data sources.

**File**: `grafana/dashboards/realtime-analytics.json`

```json
{
  "dashboard": {
    "title": "Real-Time Analytics",
    "tags": ["analytics", "realtime", "kinesis"],
    "timezone": "browser",
    "refresh": "5s",
    "time": {
      "from": "now-15m",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Events Per Second",
        "type": "graph",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "namespace": "Analytics",
            "metricName": "EventsPerSecond",
            "dimensions": {},
            "statistics": ["Average", "Maximum"],
            "period": "60"
          }
        ],
        "yaxes": [
          {"label": "Events/sec", "min": 0},
          {"show": false}
        ]
      },
      {
        "id": 2,
        "title": "Total Revenue",
        "type": "stat",
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 8},
        "targets": [
          {
            "namespace": "Analytics",
            "metricName": "RevenueUSD",
            "statistics": ["Sum"],
            "period": "300"
          }
        ],
        "options": {
          "graphMode": "area",
          "colorMode": "background",
          "justifyMode": "center",
          "textMode": "value_and_name"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD",
            "decimals": 2
          }
        }
      },
      {
        "id": 3,
        "title": "Active Users",
        "type": "stat",
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 8},
        "targets": [
          {
            "namespace": "Analytics",
            "metricName": "UniqueUsers",
            "statistics": ["Sum"],
            "period": "60"
          }
        ],
        "options": {
          "graphMode": "area",
          "colorMode": "value"
        }
      },
      {
        "id": 4,
        "title": "Conversion Funnel",
        "type": "bargauge",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "Analytics_page_view",
            "legendFormat": "Page Views"
          },
          {
            "expr": "Analytics_click",
            "legendFormat": "Clicks"
          },
          {
            "expr": "Analytics_add_to_cart",
            "legendFormat": "Add to Cart"
          },
          {
            "expr": "Analytics_purchase",
            "legendFormat": "Purchases"
          }
        ],
        "options": {
          "orientation": "horizontal",
          "displayMode": "gradient"
        }
      },
      {
        "id": 5,
        "title": "Top Products (DynamoDB)",
        "type": "table",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "datasource": "DynamoDB",
            "tableName": "realtime-aggregates",
            "filter": "metric_name = :name",
            "filterValues": {":name": "top_product"},
            "limit": 10
          }
        ]
      }
    ]
  }
}
```

**Install Grafana datasources**:

**File**: `grafana/datasources/datasources.yml`

```yaml
apiVersion: 1

datasources:
  - name: CloudWatch
    type: cloudwatch
    access: proxy
    jsonData:
      authType: default
      defaultRegion: us-east-1
      endpoint: http://localstack:4566
    isDefault: true

  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: false

  - name: DynamoDB
    type: grafana-simple-json-datasource
    access: proxy
    url: http://dynamodb-proxy:3000
    jsonData:
      endpoint: http://localstack:4566
```

**Setup script**:

```bash
#!/bin/bash
# setup_grafana.sh

echo "Setting up Grafana datasources and dashboards..."

# Copy datasource config
cp grafana/datasources/datasources.yml \
   ../../infrastructure/grafana/datasources/

# Copy dashboard
cp grafana/dashboards/realtime-analytics.json \
   ../../infrastructure/grafana/dashboards/

# Restart Grafana
docker restart module15-grafana

echo "✓ Grafana configured"
echo "  Access: http://localhost:3000 (admin/admin123)"
```

## Task 4: Create Alerts (15 minutes)

Configure alerting for anomalies.

**File**: `create_cloudwatch_alarms.py`

```python
#!/usr/bin/env python3
"""Create CloudWatch alarms for real-time analytics"""

import boto3

cloudwatch = boto3.client('cloudwatch',
                         endpoint_url='http://localhost:4566',
                         region_name='us-east-1')

sns = boto3.client('sns',
                  endpoint_url='http://localhost:4566',
                  region_name='us-east-1')


def create_sns_topic():
    """Create SNS topic for alarms"""
    response = sns.create_topic(Name='analytics-alarms')
    topic_arn = response['TopicArn']

    # Subscribe email (for real AWS, not LocalStack)
    # sns.subscribe(
    #     TopicArn=topic_arn,
    #     Protocol='email',
    #     Endpoint='alerts@example.com'
    # )

    print(f"✓ SNS topic created: {topic_arn}")
    return topic_arn


def create_high_error_rate_alarm(topic_arn):
    """Alarm when error rate exceeds 5%"""

    cloudwatch.put_metric_alarm(
        AlarmName='HighErrorRate',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='ErrorRate',
        Namespace='Analytics',
        Period=60,
        Statistic='Average',
        Threshold=5.0,
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='Error rate exceeded 5%',
        Dimensions=[],
        Unit='Percent'
    )

    print("✓ High error rate alarm created")


def create_low_revenue_alarm(topic_arn):
    """Alarm when revenue drops below threshold"""

    cloudwatch.put_metric_alarm(
        AlarmName='LowRevenue',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=3,
        MetricName='RevenueUSD',
        Namespace='Analytics',
        Period=300,
        Statistic='Sum',
        Threshold=500.0,
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='Revenue below $500 in 5 minutes',
        TreatMissingData='notBreaching'
    )

    print("✓ Low revenue alarm created")


def create_high_latency_alarm(topic_arn):
    """Alarm when latency p99 exceeds 1 second"""

    cloudwatch.put_metric_alarm(
        AlarmName='HighLatency',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='LatencyMs',
        Namespace='Analytics',
        Period=60,
        ExtendedStatistic='p99',
        Threshold=1000.0,
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmDescription='p99 latency exceeded 1 second'
    )

    print("✓ High latency alarm created")


def create_composite_alarm(topic_arn):
    """Composite alarm - trigger if multiple conditions met"""

    cloudwatch.put_composite_alarm(
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        AlarmName='SystemDegraded',
        AlarmDescription='Multiple performance indicators degraded',
        AlarmRule='(ALARM(HighErrorRate) OR ALARM(HighLatency)) AND ALARM(LowRevenue)'
    )

    print("✓ Composite alarm created")


if __name__ == '__main__':
    print("Creating CloudWatch alarms...")

    # Create SNS topic
    topic_arn = create_sns_topic()

    # Create alarms
    create_high_error_rate_alarm(topic_arn)
    create_low_revenue_alarm(topic_arn)
    create_high_latency_alarm(topic_arn)
    create_composite_alarm(topic_arn)

    print("\n✓ All alarms configured")
    print(f"  Topic ARN: {topic_arn}")
```

## Task 5: Test Dashboard Updates (10 minutes)

Verify dashboards update in real-time.

**File**: `test_dashboard_updates.sh`

```bash
#!/bin/bash

echo "Testing real-time dashboard updates..."

# Start metrics generator in background
python populate_dashboard_data.py --duration 300 &
GENERATOR_PID=$!

echo "Metrics generator started (PID: $GENERATOR_PID)"
echo ""
echo "Verify updates in:"
echo "  1. Grafana:    http://localhost:3000"
echo "  2. CloudWatch: AWS Console (if configured)"
echo ""
echo "Press Enter to stop generator..."
read

# Stop generator
kill $GENERATOR_PID
echo "✓ Generator stopped"

# Query recent metrics
echo ""
echo "Recent metrics in DynamoDB:"
awslocal dynamodb scan \
    --table-name realtime-aggregates \
    --limit 10 \
    --region us-east-1 | jq '.Items[] | {
        metric: .metric_name.S,
        value: .metric_value.N,
        time: .metric_timestamp.N
    }'
```

## Validation Checklist

- [ ] DynamoDB table has streaming data
- [ ] CloudWatch dashboard displays metrics
- [ ] Grafana dashboard shows real-time updates
- [ ] Dashboards auto-refresh (5-10 seconds)
- [ ] Alarms are configured and testable
- [ ] Metrics show realistic trends
- [ ] Dashboard queries complete in <1 second
- [ ] Multiple data sources integrated (CloudWatch + DynamoDB)

## Expected Results

**Dashboard Metrics**:
- Events per second: 50-200
- Revenue per minute: $1K-$5K
- Unique users: 100-500
- Conversion rate: 2-8%

**Auto-refresh**: Dashboards update every 5 seconds without manual refresh

## Troubleshooting

### Problem: Grafana can't connect to CloudWatch

```bash
# Verify LocalStack endpoint
curl http://localhost:4566/_localstack/health

# Check Grafana logs
docker logs module15-grafana | tail -50

# Test datasource manually in Grafana UI
```

### Problem: No data in dashboards

```bash
# Verify metrics exist in DynamoDB
awslocal dynamodb scan --table-name realtime-aggregates --limit 5

# Check CloudWatch metrics
awslocal cloudwatch list-metrics --namespace Analytics

# Verify time range is correct (use "Last 15 minutes")
```

## Key Learnings

1. **Real-Time**: DynamoDB + QuickSight provides sub-second dashboard updates
2. **CloudWatch**: Best for AWS-native metrics and alarms
3. **Grafana**: Flexible, supports multiple data sources
4. **Auto-Refresh**: Essential for monitoring live systems
5. **Alerting**: Proactive monitoring prevents incidents

## Next Steps

- **Exercise 04**: Implement CEP for fraud detection
- **Production**: Set up proper IAM roles and VPC endpoints
- **Optimization**: Use CloudWatch Insights for complex queries

## Additional Resources

- [QuickSight SPICE](https://docs.aws.amazon.com/quicksight/latest/user/spice.html)
- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)
- [Grafana CloudWatch Plugin](https://grafana.com/grafana/plugins/cloudwatch/)
