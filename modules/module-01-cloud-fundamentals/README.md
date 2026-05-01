# Module 01: Cloud Fundamentals

**Estimated Time:** 8-12 hours (3-4 hours theory + 5-8 hours exercises)

## Prerequisites

- None - This is a foundation module
- Basic command-line familiarity helpful but not required
- AWS account NOT required (we use LocalStack)


## Module Overview

This module gives you the AWS and cloud computing foundations required for data engineering. You will learn core concepts and practical implementations using LocalStack (without AWS costs).

**What will you build?**
- S3 storage system with data lake structure
- Restrictive IAM policies for security
- Lambda functions for serverless processing
- End-to-end infrastructure using CloudFormation
- Cost optimization pipeline

**Why this module matters**
All subsequent modules assume strong AWS knowledge. Without these foundations, advanced data pipeline architectures will be harder to understand.

## Learning Objectives

By the end of this module, you will be able to:

- [x] Explain the 5 essential cloud computing characteristics defined by NIST
- [x] Differentiate IaaS, PaaS, and SaaS and choose the best option based on requirements
- [x] Design multi-AZ architectures for high availability
- [x] Implement restrictive IAM policies following the principle of least privilege
- [x] Create and manage S3 buckets with partitioned data lake structure
- [x] Develop Lambda functions for event-driven processing
- [x] Optimize costs using storage classes, lifecycle policies, and right-sizing
- [x] Apply the AWS Well-Architected Framework to data pipelines
- [x] Use AWS CLI to automate infrastructure operations
- [x] Troubleshoot common AWS and cloud infrastructure issues

## Structure

- **theory/**: Core concepts and architecture documentation
- **exercises/**: Hands-on practice exercises (6 exercises)
- **infrastructure/**: LocalStack/Docker setup for this module
- **data/**: Sample datasets and schemas
- **validation/**: Automated tests to validate your learning
- **scripts/**: Helper scripts

## Getting Started

### Recommended Path (8-12 hours total)

**Phase 1: Theory (3-4 hours)**

1. Read `theory/concepts.md` fully (~2 hours)
   - Take notes on key concepts
   - Answer the self-assessment questions at the end

2. Study `theory/architecture.md` (~1 hour)
   - Review the architecture diagrams
   - Identify patterns you will apply in exercises

3. Review `theory/resources.md` (~30 min)
   - Bookmark official AWS resources
   - Watch at least 1 recommended video (optional)

**Phase 2: Setup (15-20 min)**

4. Verify that LocalStack is running:
   ```bash
   cd ../../..  # Return to project root
   make up
   docker ps | grep localstack
   ```

5. Install AWS CLI if needed:
   ```bash
   # macOS
   brew install awscli

   # Ubuntu/Debian
   sudo apt install awscli

   # Or via pip
   pip install awscli
   ```

6. Configure dummy credentials for LocalStack:
   ```bash
   aws configure
   # Access Key: test
   # Secret Key: test
   # Region: us-east-1
   ```

**Phase 3: Exercises (5-8 hours)**

7. Complete exercises in order:
   - Each exercise includes: README -> starter/ -> my_solution/ -> hints.md -> solution/
   - Work ONLY in `my_solution/` (copy from `starter/` first)
   - Do not open `solution/` until you attempt with hints

8. Validate after each exercise:
   ```bash
   ../../scripts/validate-module.sh 01
   ```

**Phase 4: Final Validation (15 min)**

9. Run all validations:
   ```bash
   cd scripts/
   bash validate.sh
   ```

10. Check your progress:
    ```bash
    cd ../../..  # Project root
    make progress
    ```

## Exercises

### 1. **AWS CLI & S3 Basics** - 45-60 min
   - Configure AWS CLI for LocalStack
   - Create buckets with partitioned structure (year/month/day)
   - Upload, download, and copy objects
   - List with prefixes and retrieve metadata
   - **Deliverable:** Automated script `s3_operations.sh`

### 2. **IAM Policies & Security** - 60-75 min
   - Create users, groups, and roles
   - Write restrictive IAM policies (least privilege)
   - Implement S3 bucket policies
   - Cross-account access scenarios
   - **Deliverable:** JSON policies and permissions documentation

### 3. **S3 Advanced Features** - 60-75 min
   - Configure versioning and MFA delete
   - Implement lifecycle policies (Standard -> IA -> Glacier)
   - Set up cross-region replication
   - Configure S3 event notifications to Lambda
   - **Deliverable:** Production-ready bucket configuration

### 4. **Lambda Functions** - 75-90 min
   - Create Lambda function for S3 file processing
   - Configure execution roles and permissions
   - Implement error handling and retry logic
   - Add logging with CloudWatch
   - **Deliverable:** Lambda function that processes CSV -> JSON

### 5. **Infrastructure as Code (CloudFormation)** - 75-90 min
   - Write YAML templates for S3 + Lambda + IAM
   - Use parameters and outputs
   - Practice stack updates and changesets
   - Simulate rollback scenarios
   - **Deliverable:** Reusable basic data pipeline template

### 6. **Cost Optimization** - 60-75 min
   - Analyze simulated AWS bill
   - Implement lifecycle policies to reduce storage cost
   - Configure budgets and alerts
   - Compare costs: On-Demand vs Reserved vs Spot
   - **Deliverable:** Optimization plan with projected savings

## Resources

See `theory/resources.md` for:
- Official AWS documentation
- Video tutorials and workshops
- Community resources
- Certification mapping

## Validation

Run all validations:
```bash
bash scripts/validate.sh
```

Or use the global validation:
```bash
make validate MODULE=module-{module_id}-{module["name"]}
```

## Progress Checklist

- [ ] Read all theory documentation
- [ ] Completed Exercise 01
- [ ] Completed Exercise 02
- [ ] Completed Exercise 03
- [ ] Completed Exercise 04
- [ ] Completed Exercise 05
- [ ] Completed Exercise 06
- [ ] All validations passing
- [ ] Ready for next module

## Next Steps

After completing this module, you'll be ready for:
[List of modules that depend on this one]
