# Exercise 01: Medallion Data Lake Design

⏱️ **Estimated Time:** 90 minutes

## Learning Objectives

After completing this exercise, you will be able to:
- Design a production-grade medallion architecture (Bronze/Silver/Gold)
- Configure S3 buckets with proper naming conventions and structure
- Implement lifecycle policies for cost optimization
- Apply tagging strategy for governance and cost tracking
- Set up access control with IAM policies

## Scenario

**Company:** GlobalMart E-commerce
**Challenge:** Currently storing 50TB of data in a single S3 bucket with no organization. Data scientists can't find what they need, costs are high, and compliance is a nightmare.

**Your Task:** Design and implement a medallion data lake architecture that:
1. Separates raw, cleaned, and curated data
2. Reduces storage costs by 40% using lifecycle policies
3. Enables data discovery with proper structure
4. Meets compliance requirements (GDPR, SOC2)

**Data Sources:**
- Transactional data: 1M records/day, 5GB/day
- User events: 10M events/day, 20GB/day
- Product catalog: 50K products, updated hourly
- Customer data: 2M customers (PII - requires encryption)

## Requirements

### Bronze Layer (Raw Zone)
- Store all raw data as-is
- Partition by ingestion date (year/month/day)
- Retain for 2 years, then move to Glacier
- Support both batch and streaming ingestion

### Silver Layer (Cleaned Zone)
- Validated and deduplicated data
- Convert to Parquet format
- Partition by business date
- Retain for 1 year in Standard, then IA

### Gold Layer (Curated Zone)
- Pre-aggregated analytics tables
- Highly optimized for query performance
- Partition by entity type
- Retain for 3 years in Standard

### Additional Requirements
- Enable versioning on all buckets
- Encrypt all data at rest (SSE-S3)
- Block public access
- Enable access logging
- Tag all resources for cost allocation

## Project Structure

```
01-data-lake-design/
├── README.md                          # This file
├── starter/
│   ├── scenario.md                    # Detailed requirements
│   └── data-lake-stack.yaml          # CloudFormation template (incomplete)
├── hints.md                           # Progressive hints
└── solution/
    ├── data-lake-stack.yaml          # Complete CloudFormation
    ├── deploy.sh                      # Deployment script
    └── verify.py                      # Verification script
```

## Getting Started

1. **Read the scenario:**
   ```bash
   cat starter/scenario.md
   ```

2. **Review the starter template:**
   ```bash
   cat starter/data-lake-stack.yaml
   ```

3. **Complete the TODOs** in the CloudFormation template

4. **Deploy your solution:**
   ```bash
   aws cloudformation create-stack \
     --stack-name globalmart-data-lake \
     --template-body file://starter/data-lake-stack.yaml \
     --parameters ParameterKey=Environment,ParameterValue=dev \
     --capabilities CAPABILITY_IAM
   ```

5. **Verify your design:**
   ```bash
   python solution/verify.py
   ```

## Success Criteria

Your solution should:
- ✅ Create 3 S3 buckets (bronze, silver, gold)
- ✅ Implement Hive-style partitioning structure
- ✅ Configure lifecycle rules (Bronze: 30d→IA, 90d→Glacier; Silver: 90d→IA)
- ✅ Enable versioning and encryption
- ✅ Set up access logging
- ✅ Apply proper tags (Environment, Layer, CostCenter)
- ✅ Block all public access
- ✅ Create IAM roles for data engineers
- ✅ Pass all verification tests

## Hints Available

If you get stuck, check `hints.md` for progressive guidance:
- **Level 1:** Conceptual guidance on medallion architecture
- **Level 2:** S3 bucket configuration best practices
- **Level 3:** Complete CloudFormation resource examples

## Validation

Run the test suite:
```bash
cd ../../validation
pytest test_exercise_01.py -v
```

Expected: 10/10 tests passing

## Bonus Challenges

1. **Multi-region replication:** Set up cross-region replication for disaster recovery
2. **Access patterns:** Design bucket policies for different user personas
3. **Cost calculator:** Create script to estimate monthly costs
4. **Data catalog:** Register buckets in AWS Glue Catalog

## Resources

- [S3 Bucket Naming Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- [S3 Lifecycle Configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [CloudFormation S3 Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket.html)
- [Medallion Architecture on AWS](https://aws.amazon.com/blogs/big-data/build-a-lake-house-architecture-on-aws/)

## Common Pitfalls

❌ **Mistake:** Creating flat directory structure
✅ **Fix:** Use Hive-style partitioning (key=value/)

❌ **Mistake:** Storing all data in Standard tier
✅ **Fix:** Use lifecycle policies to transition to cheaper tiers

❌ **Mistake:** No encryption
✅ **Fix:** Enable SSE-S3 or SSE-KMS for PII

❌ **Mistake:** Inconsistent naming
✅ **Fix:** Follow naming convention: {company}-{layer}-{env}

## Time Breakdown

- Understanding requirements: 15 min
- Designing bucket structure: 20 min
- Writing CloudFormation: 30 min
- Deploying and testing: 15 min
- Verification: 10 min

---

**Next Exercise:** [02-file-formats](../02-file-formats/) - Convert between data formats
