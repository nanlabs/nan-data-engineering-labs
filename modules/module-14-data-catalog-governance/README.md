# Module 14: Data Catalog & Governance

⏱️ **Estimated Time:** 8-10 hours

## Prerequisites

- ✅ Module 05 must be completed (100%) - S3 and Data Lakes
- ✅ Module 09 must be completed (100%) - Data Processing (Glue ETL)

## Module Overview

Master AWS Glue Data Catalog and Lake Formation to implement enterprise-grade data governance. Learn to organize metadata, automate schema discovery, implement fine-grained access control, validate data quality, and build automated governance workflows.

This module covers the complete governance lifecycle: from cataloging data with AWS Glue, to securing it with Lake Formation permissions (database/table/column/row-level), validating quality with automated rules, sharing across accounts, and orchestrating end-to-end governance automation.

## Learning Objectives

By the end of this module, you will be able to:

- [ ] Create and manage AWS Glue Data Catalog databases, tables, and partitions
- [ ] Configure and optimize Glue Crawlers for automatic schema discovery
- [ ] Implement fine-grained access control with Lake Formation (DBMS/table/column/row permissions)
- [ ] Apply Tag-Based Access Control (TBAC) for scalable permission management
- [ ] Define and enforce data quality rules using AWS Glue Data Quality
- [ ] Securely share data across AWS accounts using resource links
- [ ] Build automated governance workflows with Step Functions and EventBridge
- [ ] Monitor catalog health, quality scores, and access patterns with CloudWatch

## Structure

- **theory/**: Core concepts and architecture documentation (4 files)
  - `concepts.md`: Data governance fundamentals, Glue Catalog, Lake Formation
  - `architecture.md`: AWS service architectures with ASCII diagrams
  - `best-practices.md`: Implementation guidelines and optimization patterns
  - `resources.md`: AWS documentation, workshops, certifications

- **assets/diagrams/**: Visual architecture and workflow diagrams (3 files)
  - `architecture-diagrams.md`: 10 core architectural diagrams
  - `workflow-diagrams.md`: 10 operational workflow diagrams
  - `pattern-diagrams.md`: 10 advanced pattern diagrams

- **exercises/**: Hands-on practice exercises (6 exercises)

- **infrastructure/**: LocalStack/Docker setup for this module

- **data/**: Sample datasets and JSON schemas
  - `sample/`: Sales transaction CSV, catalog metadata, quality rules
  - `schemas/`: Glue table schema, Lake Formation permission schema

- **validation/**: Automated tests to validate your learning

- **scripts/**: Helper scripts for setup, validation, cleanup

## Getting Started

1. Ensure prerequisites are completed (Module 05 and 09)
2. Read `theory/concepts.md` for foundational understanding (2-3 hours)
3. Review `theory/architecture.md` for AWS architecture patterns (1-2 hours)
4. Study diagrams in `assets/diagrams/` for visual understanding (30-45 min)
5. Set up infrastructure: `bash scripts/setup.sh` (10-15 min)
6. Complete exercises in order (01 through 06) (4-5 hours)
7. Validate your learning: `bash scripts/validate.sh` (10-15 min)

## Exercises

1. **Exercise 01**: Data Catalog Setup - Create databases, tables, and partitions
   - Define metadata schemas with proper data types
   - Organize catalog following medallion architecture (Bronze/Silver/Gold)
   - Add business metadata and tags
   - Query catalog programmatically with Boto3

2. **Exercise 02**: Crawler Automation - Automated schema discovery
   - Configure Glue Crawlers with optimal settings
   - Implement scheduling patterns (time-based, event-driven)
   - Handle schema evolution and change detection
   - Monitor crawler performance and costs

3. **Exercise 03**: Lake Formation Permissions - Fine-grained access control
   - Register S3 locations with Lake Formation
   - Implement database, table, and column-level permissions
   - Configure row-level security with data filters
   - Set up Tag-Based Access Control (TBAC) for scalability

4. **Exercise 04**: Data Quality Validation - Automated quality checks
   - Define quality rules (completeness, validity, consistency)
   - Integrate quality checks into ETL pipelines
   - Implement quarantine process for bad data
   - Build quality monitoring dashboards

5. **Exercise 05**: Cross-Account Sharing - Secure multi-account access
   - Configure producer account for data sharing
   - Create resource links in consumer accounts
   - Implement least-privilege access patterns
   - Monitor and audit cross-account access

6. **Exercise 06**: Governance Automation - End-to-end workflow
   - Build Step Functions governance workflow
   - Integrate catalog discovery, quality validation, permissions
   - Create event-driven automation with EventBridge
   - Build comprehensive governance dashboards

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
