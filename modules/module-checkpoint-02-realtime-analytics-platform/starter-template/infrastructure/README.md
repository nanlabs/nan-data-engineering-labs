# Infrastructure Setup Guide

## Overview

This directory contains Terraform infrastructure code for deploying the Real-Time Analytics Platform. The `main.tf` file includes TODO comments marking areas you need to complete.

## Total TODOs in Infrastructure: 17

### Configuration Tasks

1. **KMS Keys (TODOs 1-2)**: Complete encryption key configuration
2. **Kinesis Streams (TODOs 3-4)**: Configure data streams with proper retention and encryption
3. **S3 Bucket (TODOs 5-8)**: Set up data lake with versioning, encryption, and lifecycle policies
4. **DynamoDB Tables (TODOs 9-12)**: Create tables with GSIs, streams, and PITR
5. **IAM Roles (TODOs 13-14)**: Configure Lambda execution roles with proper permissions
6. **Lambda Functions (TODOs 15-16)**: Deploy Lambda functions (code separate)
7. **CloudWatch Logs (TODO 17)**: Set up log groups for monitoring

## Prerequisites

- Terraform >= 1.5.0
- AWS CLI configured with credentials
- AWS account with appropriate permissions

## Setup Steps

### 1. Review Variables

Check `variables.tf` and create `terraform.tfvars`:

```hcl
project_name = "rideshare-analytics"
environment  = "dev"
aws_region   = "us-east-1"

kinesis_shard_count = 2
log_retention_days  = 7

tags = {
  Team = "DataEngineering"
  Cost = "Training"
}
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Complete TODOs

Work through each TODO in `main.tf`:

#### TODO 1-2: KMS Keys
- Encryption keys are mostly complete
- Verify deletion windows and key rotation settings

#### TODO 3-4: Kinesis Streams
- Set correct shard counts (high-volume streams need more shards)
- Configure 24-hour retention
- Enable KMS encryption

**Example:**
```hcl
resource "aws_kinesis_stream" "rides" {
  shard_count      = var.kinesis_shard_count  # 2 for high volume
  retention_period = 24
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.kinesis.key_id
}
```

#### TODO 5-8: S3 Bucket
- Enable versioning
- Configure KMS encryption
- Set lifecycle policies (IA at 30 days, Glacier at 90 days, expire at 365 days)

**Example:**
```hcl
transition {
  days          = 30
  storage_class = "STANDARD_IA"
}
```

#### TODO 9-12: DynamoDB Tables
- Use PAY_PER_REQUEST billing mode
- Add Global Secondary Indexes for querying patterns
- Enable streams with NEW_AND_OLD_IMAGES
- Enable Point-in-Time Recovery
- Configure KMS encryption

**Key GSIs:**
- Rides table: rider-index (by rider_id), driver-index (by driver_id)
- Drivers table: city-index (by city)
- Payments table: ride-index (by ride_id)

#### TODO 13-14: IAM Roles
- Lambda trust policy allowing lambda.amazonaws.com
- Permissions for Kinesis read, DynamoDB write, S3 write
- CloudWatch Logs write permissions

**Example Policy:**
```json
{
  "Effect": "Allow",
  "Action": ["kinesis:GetRecords", "kinesis:GetShardIterator"],
  "Resource": "arn:aws:kinesis:*:*:stream/*"
}
```

#### TODO 15-16: Lambda Functions
- Create 4 Lambda functions (rides, locations, payments, ratings processors)
- Python 3.11 runtime
- Memory: 512MB (256MB for locations/ratings)
- Timeout: 60s (30s for locations/ratings)
- Environment variables: DYNAMODB_TABLE_PREFIX, S3_BUCKET, AWS_REGION

**Note:** Lambda code deployment is separate (see ../pipelines/lambda/)

#### TODO 17: CloudWatch Log Groups
- Create log groups for each Lambda function
- Set retention period from variable
- Pattern: `/aws/lambda/${project_name}-${environment}-{function_name}`

### 4. Validate Configuration

```bash
# Check for syntax errors
terraform validate

# Preview changes
terraform plan
```

### 5. Deploy Infrastructure

```bash
# Deploy all resources
terraform apply

# Or deploy specific resources
terraform apply -target=aws_kinesis_stream.rides
```

### 6. Verify Deployment

```bash
# Check Kinesis streams
aws kinesis list-streams

# Check DynamoDB tables
aws dynamodb list-tables

# Check S3 bucket
aws s3 ls
```

## Resource Naming Convention

All resources follow this pattern:
```
${project_name}-${environment}-{resource_type}
```

Examples:
- `rideshare-analytics-dev-rides-stream`
- `rideshare-analytics-dev-rides` (DynamoDB table)
- `rideshare-analytics-dev-data-us-east-1` (S3 bucket)

## Cost Considerations

Estimated monthly costs (dev environment):

- Kinesis (4 streams, 4 shards total): ~$30
- Lambda (pay-per-use): ~$5-10
- DynamoDB (pay-per-request): ~$5-10
- S3 (with lifecycle): ~$5
- **Total: ~$45-55/month**

### Cost Optimization Tips

1. Use fewer shards for low-volume streams
2. Set appropriate Lambda memory (don't over-provision)
3. Enable S3 lifecycle policies
4. Use DynamoDB PAY_PER_REQUEST for variable workloads
5. Set log retention to 7 days (not indefinite)

## Troubleshooting

### Issue: Terraform State Lock

```bash
# If state is locked
terraform force-unlock <LOCK_ID>
```

### Issue: Insufficient Permissions

Check IAM user/role has these permissions:
- kinesis:*
- dynamodb:*
- s3:*
- lambda:*
- iam:CreateRole, iam:AttachRolePolicy
- kms:CreateKey, kms:CreateAlias
- logs:CreateLogGroup

### Issue: Resource Already Exists

If resources exist with same names:
```bash
# Import existing resource
terraform import aws_kinesis_stream.rides rideshare-analytics-dev-rides-stream

# Or destroy and recreate
terraform destroy -target=aws_kinesis_stream.rides
terraform apply -target=aws_kinesis_stream.rides
```

### Issue: KMS Key Deletion

KMS keys have deletion windows. If you destroy and recreate:
1. Wait for deletion window (30 days default)
2. Or use different alias names
3. Or cancel deletion: `aws kms cancel-key-deletion --key-id <ID>`

## Testing Infrastructure

After deployment, run acceptance tests:

```bash
cd ../../validation/acceptance-tests
./run_tests.sh infrastructure
```

## Cleanup

To destroy all resources:

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy

# Or destroy specific resources
terraform destroy -target=aws_kinesis_stream.rides
```

**Warning:** This will delete all data! Export important data first.

## Next Steps

After completing infrastructure:

1. ✅ Deploy Lambda functions (see ../pipelines/lambda/)
2. ✅ Configure Event Source Mappings
3. ✅ Set up producers (see ../pipelines/producers/)
4. ✅ Deploy Step Functions workflows
5. ✅ Configure QuickSight dashboards

## Additional Resources

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Kinesis Best Practices](https://docs.aws.amazon.com/streams/latest/dev/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## Support

If you get stuck:
1. Review the TODO comments for hints
2. Check the reference solution (for comparison only)
3. Run `terraform plan` to see what's missing
4. Consult AWS documentation
5. Ask in the course forum
