#!/bin/bash

###############################################################################
# AWS Cost Optimization Infrastructure Initialization
#
# This script sets up all AWS services required for cost optimization:
# - Enable Cost Explorer
# - Create Cost and Usage Report (CUR)
# - Set up AWS Budgets with alerts
# - Activate cost allocation tags
# - Configure Cost Anomaly Detection
# - Create sample S3 bucket with lifecycle policies
# - Set up SNS topics for alerts
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - IAM permissions for billing, Cost Explorer, Budgets, S3, SNS
#
# Usage: ./init-aws.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
COST_ALLOCATION_TAGS=("CostCenter" "Team" "Environment" "Project" "Owner")
MONTHLY_BUDGET="${MONTHLY_BUDGET:-1000}"  # Default $1000/month
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install: https://aws.amazon.com/cli/"
        exit 1
    fi

    # Check AWS credentials
    if [ -z "$ACCOUNT_ID" ]; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi

    log_success "Prerequisites OK (Account: $ACCOUNT_ID)"
}

# Enable Cost Explorer
enable_cost_explorer() {
    log_info "Enabling Cost Explorer..."

    # Note: Cost Explorer must be enabled via AWS Console first time
    # After that, this API call will work
    aws ce get-cost-and-usage \
        --time-period Start=2024-01-01,End=2024-01-02 \
        --granularity MONTHLY \
        --metrics UnblendedCost \
        --region us-east-1 \
        &>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Cost Explorer already enabled"
    else
        log_warning "Cost Explorer not enabled. Enable at: https://console.aws.amazon.com/cost-management/home#/cost-explorer"
        log_info "After enabling, wait 24 hours for data to populate"
    fi
}

# Create Cost and Usage Report (CUR)
create_cur_report() {
    log_info "Creating Cost and Usage Report..."

    # Create S3 bucket for CUR
    CUR_BUCKET="cost-usage-report-${ACCOUNT_ID}"

    # Check if bucket exists
    if aws s3api head-bucket --bucket "$CUR_BUCKET" 2>/dev/null; then
        log_success "CUR bucket already exists: $CUR_BUCKET"
    else
        # Create bucket
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$CUR_BUCKET" --region "$AWS_REGION"
        else
            aws s3api create-bucket \
                --bucket "$CUR_BUCKET" \
                --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi

        # Apply bucket policy for CUR delivery
        cat > /tmp/cur-bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "billingreports.amazonaws.com"
      },
      "Action": [
        "s3:GetBucketAcl",
        "s3:GetBucketPolicy"
      ],
      "Resource": "arn:aws:s3:::${CUR_BUCKET}"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "billingreports.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::${CUR_BUCKET}/*"
    }
  ]
}
EOF

        aws s3api put-bucket-policy \
            --bucket "$CUR_BUCKET" \
            --policy file:///tmp/cur-bucket-policy.json

        log_success "Created CUR bucket: $CUR_BUCKET"
    fi

    # Create CUR report definition
    cat > /tmp/cur-definition.json <<EOF
{
  "ReportName": "detailed-cost-usage-report",
  "TimeUnit": "HOURLY",
  "Format": "Parquet",
  "Compression": "Parquet",
  "AdditionalSchemaElements": [
    "RESOURCES"
  ],
  "S3Bucket": "${CUR_BUCKET}",
  "S3Prefix": "reports",
  "S3Region": "${AWS_REGION}",
  "AdditionalArtifacts": [
    "ATHENA"
  ],
  "RefreshClosedReports": true,
  "ReportVersioning": "OVERWRITE_REPORT"
}
EOF

    # Put report definition (note: CUR API is only in us-east-1)
    aws cur put-report-definition \
        --report-definition file:///tmp/cur-definition.json \
        --region us-east-1 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Cost and Usage Report created"
        log_info "First report will be available within 24 hours"
    else
        log_warning "CUR may already exist or you don't have permissions"
    fi
}

# Activate cost allocation tags
activate_cost_tags() {
    log_info "Activating cost allocation tags..."

    for tag in "${COST_ALLOCATION_TAGS[@]}"; do
        aws ce update-cost-allocation-tags-status \
            --cost-allocation-tags-status TagKey="$tag",Status=Active \
            --region us-east-1 \
            2>/dev/null

        if [ $? -eq 0 ]; then
            log_success "Activated tag: $tag"
        else
            log_warning "Could not activate tag: $tag (may already be active)"
        fi
    done

    log_info "Cost allocation tags will be visible in Cost Explorer after 24 hours"
}

# Create AWS Budget with alerts
create_budget() {
    log_info "Creating monthly budget ($${MONTHLY_BUDGET})..."

    # Create SNS topic for budget alerts
    SNS_TOPIC_ARN=$(aws sns create-topic \
        --name cost-optimization-budget-alerts \
        --region "$AWS_REGION" \
        --query 'TopicArn' \
        --output text 2>/dev/null)

    if [ $? -eq 0 ]; then
        log_success "Created SNS topic: $SNS_TOPIC_ARN"

        # Subscribe your email (optional - comment out if not needed)
        # aws sns subscribe \
        #     --topic-arn "$SNS_TOPIC_ARN" \
        #     --protocol email \
        #     --notification-endpoint your-email@example.com \
        #     --region "$AWS_REGION"
    else
        log_warning "SNS topic may already exist"
        SNS_TOPIC_ARN="arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:cost-optimization-budget-alerts"
    fi

    # Create budget
    cat > /tmp/budget.json <<EOF
{
  "BudgetName": "monthly-cost-budget",
  "BudgetType": "COST",
  "TimeUnit": "MONTHLY",
  "BudgetLimit": {
    "Amount": "${MONTHLY_BUDGET}",
    "Unit": "USD"
  },
  "CostFilters": {},
  "CostTypes": {
    "IncludeTax": true,
    "IncludeSubscription": true,
    "UseBlended": false,
    "IncludeRefund": false,
    "IncludeCredit": false,
    "IncludeUpfront": true,
    "IncludeRecurring": true,
    "IncludeOtherSubscription": true,
    "IncludeSupport": true,
    "IncludeDiscount": true,
    "UseAmortized": false
  },
  "TimeStart": "2024-01-01T00:00:00Z"
}
EOF

    # Create notifications (4 thresholds)
    cat > /tmp/notifications.json <<EOF
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE",
      "NotificationState": "ALARM"
    },
    "Subscribers": [
      {
        "SubscriptionType": "SNS",
        "Address": "${SNS_TOPIC_ARN}"
      }
    ]
  },
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE",
      "NotificationState": "ALARM"
    },
    "Subscribers": [
      {
        "SubscriptionType": "SNS",
        "Address": "${SNS_TOPIC_ARN}"
      }
    ]
  },
  {
    "Notification": {
      "NotificationType": "FORECASTED",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE",
      "NotificationState": "ALARM"
    },
    "Subscribers": [
      {
        "SubscriptionType": "SNS",
        "Address": "${SNS_TOPIC_ARN}"
      }
    ]
  }
]
EOF

    # Create budget (Note: First 2 budgets are free)
    aws budgets create-budget \
        --account-id "$ACCOUNT_ID" \
        --budget file:///tmp/budget.json \
        --notifications-with-subscribers file:///tmp/notifications.json \
        --region us-east-1 \
        2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Budget created: monthly-cost-budget"
    else
        log_warning "Budget may already exist"
    fi
}

# Configure Cost Anomaly Detection
setup_anomaly_detection() {
    log_info "Setting up Cost Anomaly Detection..."

    # Create SNS topic for anomalies
    ANOMALY_TOPIC_ARN=$(aws sns create-topic \
        --name cost-anomaly-alerts \
        --region "$AWS_REGION" \
        --query 'TopicArn' \
        --output text 2>/dev/null)

    if [ $? -eq 0 ]; then
        log_success "Created anomaly SNS topic"
    else
        ANOMALY_TOPIC_ARN="arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:cost-anomaly-alerts"
    fi

    # Create anomaly monitor (AWS service-level)
    MONITOR_ARN=$(aws ce create-anomaly-monitor \
        --anomaly-monitor file:///dev/stdin <<EOF | jq -r '.AnomalyMonitorArn' 2>/dev/null
{
  "MonitorName": "ServiceLevelMonitor",
  "MonitorType": "DIMENSIONAL",
  "MonitorDimension": "SERVICE"
}
EOF
)

    if [ -n "$MONITOR_ARN" ]; then
        log_success "Created anomaly monitor: $MONITOR_ARN"

        # Create subscription
        aws ce create-anomaly-subscription \
            --anomaly-subscription file:///dev/stdin <<EOF >/dev/null 2>&1
{
  "SubscriptionName": "DailyAnomalyAlerts",
  "Threshold": 100,
  "Frequency": "DAILY",
  "MonitorArnList": ["${MONITOR_ARN}"],
  "Subscribers": [
    {
      "Type": "SNS",
      "Address": "${ANOMALY_TOPIC_ARN}"
    }
  ]
}
EOF

        if [ $? -eq 0 ]; then
            log_success "Created anomaly subscription with daily alerts"
        fi
    else
        log_warning "Could not create anomaly monitor (may already exist or insufficient permissions)"
    fi
}

# Create sample S3 bucket with lifecycle
create_sample_bucket() {
    log_info "Creating sample S3 bucket with lifecycle policies..."

    SAMPLE_BUCKET="cost-optimization-demo-${ACCOUNT_ID}"

    # Create bucket
    if aws s3api head-bucket --bucket "$SAMPLE_BUCKET" 2>/dev/null; then
        log_success "Sample bucket already exists: $SAMPLE_BUCKET"
    else
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$SAMPLE_BUCKET" --region "$AWS_REGION"
        else
            aws s3api create-bucket \
                --bucket "$SAMPLE_BUCKET" \
                --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi

        log_success "Created bucket: $SAMPLE_BUCKET"
    fi

    # Apply lifecycle policy
    cat > /tmp/lifecycle-policy.json <<EOF
{
  "Rules": [
    {
      "Id": "hot-to-warm-30d",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        }
      ],
      "Filter": {
        "Prefix": ""
      }
    },
    {
      "Id": "warm-to-cold-90d",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        }
      ],
      "Filter": {
        "Prefix": ""
      }
    },
    {
      "Id": "cold-to-archive-180d",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 180,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Filter": {
        "Prefix": ""
      }
    },
    {
      "Id": "delete-incomplete-multipart",
      "Status": "Enabled",
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      },
      "Filter": {
        "Prefix": ""
      }
    }
  ]
}
EOF

    aws s3api put-bucket-lifecycle-configuration \
        --bucket "$SAMPLE_BUCKET" \
        --lifecycle-configuration file:///tmp/lifecycle-policy.json

    if [ $? -eq 0 ]; then
        log_success "Applied 4-tier lifecycle policy to bucket"
    fi

    # Apply cost allocation tags
    aws s3api put-bucket-tagging \
        --bucket "$SAMPLE_BUCKET" \
        --tagging "TagSet=[
            {Key=CostCenter,Value=CC-12345},
            {Key=Team,Value=Data},
            {Key=Environment,Value=dev},
            {Key=Project,Value=cost-optimization-training},
            {Key=Owner,Value=engineering@example.com}
        ]"

    if [ $? -eq 0 ]; then
        log_success "Applied cost allocation tags to bucket"
    fi

    echo ""
    echo "Sample bucket created: s3://$SAMPLE_BUCKET"
}

# Create CloudWatch billing alarm
create_billing_alarm() {
    log_info "Creating CloudWatch billing alarm..."

    # Create SNS topic for CloudWatch alarms (different from budget alerts)
    ALARM_TOPIC_ARN=$(aws sns create-topic \
        --name cloudwatch-billing-alarms \
        --region us-east-1 \
        --query 'TopicArn' \
        --output text 2>/dev/null)

    if [ $? -eq 0 ]; then
        log_success "Created CloudWatch alarm topic"
    else
        ALARM_TOPIC_ARN="arn:aws:sns:us-east-1:${ACCOUNT_ID}:cloudwatch-billing-alarms"
    fi

    # Create alarm for 90% of budget
    ALARM_THRESHOLD=$(echo "scale=2; $MONTHLY_BUDGET * 0.9" | bc)

    aws cloudwatch put-metric-alarm \
        --alarm-name "monthly-cost-90pct" \
        --alarm-description "Alert when monthly cost reaches 90% of budget" \
        --metric-name EstimatedCharges \
        --namespace AWS/Billing \
        --statistic Maximum \
        --period 21600 \
        --evaluation-periods 1 \
        --threshold "$ALARM_THRESHOLD" \
        --comparison-operator GreaterThanThreshold \
        --alarm-actions "$ALARM_TOPIC_ARN" \
        --dimensions Name=Currency,Value=USD \
        --region us-east-1 \
        2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Created CloudWatch billing alarm (threshold: \$$ALARM_THRESHOLD)"
    else
        log_warning "Could not create billing alarm (may already exist)"
    fi
}

# Enable Compute Optimizer
enable_compute_optimizer() {
    log_info "Enrolling in AWS Compute Optimizer..."

    aws compute-optimizer update-enrollment-status \
        --status Active \
        --region us-east-1 \
        2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "Enrolled in Compute Optimizer"
        log_info "Recommendations will be available after 30 hours of resource usage"
    else
        log_warning "Could not enroll in Compute Optimizer (may already be enrolled)"
    fi
}

# Create IAM role for Lambda cost optimization functions
create_lambda_role() {
    log_info "Creating IAM role for cost optimization Lambda functions..."

    ROLE_NAME="CostOptimizationLambdaRole"

    # Check if role exists
    if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
        log_success "IAM role already exists: $ROLE_NAME"
        return
    fi

    # Create trust policy
    cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --description "Role for cost optimization Lambda functions"

    # Attach policies
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

    # Create custom policy for cost optimization
    cat > /tmp/cost-optimization-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:StopInstances",
        "ec2:DeleteVolume",
        "ec2:DeleteSnapshot",
        "rds:DescribeDBInstances",
        "rds:StopDBInstance",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
EOF

    POLICY_ARN=$(aws iam create-policy \
        --policy-name CostOptimizationPolicy \
        --policy-document file:///tmp/cost-optimization-policy.json \
        --query 'Policy.Arn' \
        --output text 2>/dev/null)

    if [ -n "$POLICY_ARN" ]; then
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "$POLICY_ARN"

        log_success "Created IAM role with cost optimization permissions"
    else
        log_warning "Policy may already exist"
    fi
}

# Create Athena database for CUR analysis
setup_athena_cur() {
    log_info "Setting up Athena for CUR analysis..."

    # Create Athena results bucket
    ATHENA_BUCKET="aws-athena-query-results-${ACCOUNT_ID}-${AWS_REGION}"

    if ! aws s3api head-bucket --bucket "$ATHENA_BUCKET" 2>/dev/null; then
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$ATHENA_BUCKET" --region "$AWS_REGION"
        else
            aws s3api create-bucket \
                --bucket "$ATHENA_BUCKET" \
                --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi

        log_success "Created Athena results bucket: $ATHENA_BUCKET"
    else
        log_success "Athena results bucket already exists"
    fi

    # Create Athena database
    aws athena start-query-execution \
        --query-string "CREATE DATABASE IF NOT EXISTS cur_analysis" \
        --result-configuration "OutputLocation=s3://${ATHENA_BUCKET}/cur-database/" \
        --region "$AWS_REGION" \
        >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        log_success "Created Athena database: cur_analysis"
        log_info "After CUR is generated, run the Athena table creation query from CUR bucket"
    else
        log_warning "Could not create Athena database (may already exist)"
    fi
}

# Create sample cost data (for local testing)
create_sample_data() {
    log_info "Creating sample cost data..."

    mkdir -p data/sample

    # This will be created by a separate script
    log_info "Sample data files will be created separately"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║       AWS Cost Optimization Setup Complete           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "📊 Services Configured:"
    echo "   ✓ Cost Explorer (enable manually if not already)"
    echo "   ✓ Cost and Usage Report (CUR)"
    echo "   ✓ Cost Allocation Tags (${#COST_ALLOCATION_TAGS[@]} tags)"
    echo "   ✓ AWS Budget (\$$MONTHLY_BUDGET/month)"
    echo "   ✓ Cost Anomaly Detection"
    echo "   ✓ Compute Optimizer"
    echo "   ✓ Sample S3 bucket with lifecycle"
    echo "   ✓ Athena database for CUR"
    echo "   ✓ IAM role for Lambda functions"
    echo ""
    echo "⏰ Wait Times:"
    echo "   • Cost Explorer data: 24 hours"
    echo "   • Cost allocation tags: 24 hours"
    echo "   • CUR first report: 24 hours"
    echo "   • Compute Optimizer: 30 hours of resource usage"
    echo ""
    echo "📁 Resources Created:"
    echo "   • S3 bucket: cost-usage-report-${ACCOUNT_ID}"
    echo "   • S3 bucket: cost-optimization-demo-${ACCOUNT_ID}"
    echo "   • SNS topic: cost-optimization-budget-alerts"
    echo "   • SNS topic: cost-anomaly-alerts"
    echo "   • Budget: monthly-cost-budget"
    echo "   • Athena DB: cur_analysis"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Wait 24 hours for data to populate"
    echo "   2. Run 'make validate' to check setup"
    echo "   3. Start with Exercise 01: Cost Analysis"
    echo "   4. View costs: https://console.aws.amazon.com/cost-management/home"
    echo ""
    echo "💰 Expected First Month Costs:"
    echo "   • CUR storage: ~\$1"
    echo "   • Budget (first 2 free): \$0"
    echo "   • Cost Explorer API: ~\$0 (minimal calls)"
    echo "   • Anomaly Detection: \$0 (free)"
    echo "   • Total setup cost: <\$5"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   AWS Cost Optimization Infrastructure Setup          ║"
    echo "║   Module 17: Cloud Cost Optimization                  ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    check_prerequisites
    echo ""

    enable_cost_explorer
    echo ""

    create_cur_report
    echo ""

    activate_cost_tags
    echo ""

    create_budget
    echo ""

    setup_anomaly_detection
    echo ""

    enable_compute_optimizer
    echo ""

    create_sample_bucket
    echo ""

    create_lambda_role
    echo ""

    setup_athena_cur
    echo ""

    create_sample_data
    echo ""

    print_summary
}

# Run main function
main "$@"
