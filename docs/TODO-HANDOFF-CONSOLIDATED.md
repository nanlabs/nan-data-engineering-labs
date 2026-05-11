# TODO Handoff Consolidated

This file consolidates all TODO markers currently detected in the
repository so the next session can continue from a single source of truth.

## Scope

- Repository: nan-data-engineering-labs
- Generated: 2026-05-11
- Detection rules:
  - Markdown files containing `TODO` keyword (case-insensitive).
  - Markdown files containing unchecked checklist items (`- [ ]`).

## Operational TODOs (Immediate Work Queue)

- docs/TODO-STRUCTURE-UNIFICATION.md
  - 20:- [ ] Consolidate follow-up quality tasks now that structure
  - 22:- [ ] Review and prioritize module-content quality improvements
  - 33:- [ ] Replace placeholder starter/solution notes with exercise-specific
  - 35:- [ ] Define the next wave (content quality, test depth, and consistency
  - 54:- [ ] Decide regular-module baseline for `docs/`:
  - 57:- [ ] Decide policy for `dags/` in module 10:
  - 60:- [ ] Remove `venv/` from `module-05-data-lakehouse`.
  - 61:- [ ] Decide policy for checkpoint `extensions/`:
  - 67:- [ ] Update `docs/MODULE-CONTRACT-MATRIX.md` with approved optional
  - 69:- [ ] Update `scripts/validate_learning_labs.py` to fail on
    unapproved extras.
  - 70:- [ ] Add exception list support (if needed) for module-specific
    justified folders.

<!-- markdownlint-disable MD013 -->

- 74:- [ ] Run `python scripts/validate_learning_labs.py --strict-core --strict-headings` and verify expected output is clean

<!-- markdownlint-enable MD013 -->

- 81:- [ ] Use `nanlabs-assistant` for workflow guardrails.
- 82:- [ ] Use `planner` for wave planning and dependency sequencing.
- 83:- [ ] Use `code-reviewer` after each migration wave.
- 84:- [ ] Use `security-reviewer` for scripts and CI changes.
- 85:- [ ] Use `build-error-resolver` if validator or CI checks fail.
- 86:- [ ] Confirm `nan-skills check` passes once `clickup` and `glab` are installed.

## Markdown Files With TODO Keyword

- docs/TODO-HANDOFF-CONSOLIDATED.md
- docs/TODO-STRUCTURE-UNIFICATION.md
- modules/module-01-cloud-fundamentals/assets/diagrams/README.md
- modules/module-01-cloud-fundamentals/exercises/01-s3-basics/hints.md
- modules/module-01-cloud-fundamentals/exercises/01-s3-basics/README.md
- modules/module-01-cloud-fundamentals/exercises/02-iam-policies/README.md
- modules/module-01-cloud-fundamentals/exercises/02-iam-policies/starter/scenario.md
- modules/module-01-cloud-fundamentals/exercises/03-s3-advanced/README.md
- modules/module-01-cloud-fundamentals/exercises/04-lambda-functions/README.md
- modules/module-01-cloud-fundamentals/exercises/04-lambda-functions/starter/scenario.md
- modules/module-01-cloud-fundamentals/exercises/05-infrastructure-as-code/README.md
- modules/module-01-cloud-fundamentals/exercises/06-cost-optimization/README.md
- modules/module-01-cloud-fundamentals/PROGRESS.md
- modules/module-01-cloud-fundamentals/STATUS-FINAL.md
- modules/module-01-cloud-fundamentals/STATUS.md
- modules/module-01-cloud-fundamentals/theory/architecture.md
- modules/module-01-cloud-fundamentals/theory/concepts.md
- modules/module-01-cloud-fundamentals/validation/README.md
- modules/module-02-storage-basics/exercises/01-data-lake-design/README.md
- modules/module-02-storage-basics/exercises/02-file-formats/README.md
- modules/module-02-storage-basics/STATUS-FINAL.md
- modules/module-03-sql-foundations/data/README.md
- modules/module-03-sql-foundations/exercises/01-basic-queries/hints.md
- modules/module-03-sql-foundations/exercises/01-basic-queries/README.md
- modules/module-03-sql-foundations/exercises/02-joins/hints.md
- modules/module-03-sql-foundations/exercises/02-joins/README.md
- modules/module-03-sql-foundations/README.md
- modules/module-03-sql-foundations/STATUS.md
- modules/module-03-sql-foundations/theory/concepts.md
- modules/module-04-python-for-data/assets/cheatsheets/data-cleaning.md
- modules/module-04-python-for-data/assets/cheatsheets/file-formats.md
- modules/module-04-python-for-data/assets/cheatsheets/python-basics.md
- modules/module-04-python-for-data/assets/diagrams/pandas-operations.md
- modules/module-04-python-for-data/data/README.md
- modules/module-04-python-for-data/docs/python-guide.md
- modules/module-04-python-for-data/docs/troubleshooting.md
- modules/module-04-python-for-data/exercises/05-data-transformation/README.md
- modules/module-04-python-for-data/exercises/README.md
- modules/module-04-python-for-data/infrastructure/README.md
- modules/module-04-python-for-data/README.md
- modules/module-04-python-for-data/STATUS.md
- modules/module-04-python-for-data/theory/architecture.md
- modules/module-04-python-for-data/theory/concepts.md
- modules/module-04-python-for-data/validation/README.md
- modules/module-05-data-lakehouse/data/README.md
- modules/module-05-data-lakehouse/docs/TROUBLESHOOTING.md
- modules/module-05-data-lakehouse/exercises/01-delta-basics/solution/README.md
- modules/module-05-data-lakehouse/exercises/02-medallion-architecture/README.md
- modules/module-05-data-lakehouse/exercises/03-time-travel/hints.md
- modules/module-05-data-lakehouse/exercises/04-schema-evolution/hints.md
- modules/module-05-data-lakehouse/exercises/05-optimization/hints.md
- modules/module-05-data-lakehouse/infrastructure/README.md
- modules/module-05-data-lakehouse/README.md
- modules/module-05-data-lakehouse/STATUS.md
- modules/module-05-data-lakehouse/theory/01-concepts.md
- modules/module-05-data-lakehouse/theory/02-architecture.md
- modules/module-05-data-lakehouse/validation/README.md
- modules/module-06-etl-fundamentals/README.md
- modules/module-06-etl-fundamentals/theory/01-concepts.md
- modules/module-06-etl-fundamentals/theory/02-patterns.md
- modules/module-07-batch-processing/data/README.md
- modules/module-07-batch-processing/exercises/01-batch-basics/README.md
- modules/module-07-batch-processing/theory/01-concepts.md
- modules/module-07-batch-processing/theory/03-resources.md
- modules/module-08-streaming-basics/exercises/01-kafka-basics/README.md
- modules/module-08-streaming-basics/exercises/02-stream-processing/README.md
- modules/module-08-streaming-basics/exercises/03-avro-schemas/README.md
- modules/module-08-streaming-basics/exercises/04-kinesis-streams/README.md
- modules/module-08-streaming-basics/exercises/05-flink-processing/README.md
- modules/module-08-streaming-basics/exercises/06-production-streams/README.md
- modules/module-08-streaming-basics/theory/01-concepts.md
- modules/module-08-streaming-basics/theory/02-architecture.md
- modules/module-09-data-quality/exercises/01-data-profiling/README.md
- modules/module-09-data-quality/exercises/02-validation-rules/README.md
- modules/module-09-data-quality/exercises/03-great-expectations/README.md
- modules/module-09-data-quality/exercises/04-anomaly-detection/README.md
- modules/module-09-data-quality/exercises/05-quality-monitoring/README.md
- modules/module-09-data-quality/exercises/06-production-gates/README.md
- modules/module-09-data-quality/theory/01-concepts.md
- modules/module-10-workflow-orchestration/dags/README.md
- modules/module-10-workflow-orchestration/data/README.md
- modules/module-10-workflow-orchestration/QUICK-START.md
- modules/module-10-workflow-orchestration/README.md
- modules/module-10-workflow-orchestration/STATUS.md
- modules/module-11-infrastructure-as-code/exercises/01-first-terraform/README.md
- modules/module-11-infrastructure-as-code/exercises/02-multi-resource/README.md
- modules/module-11-infrastructure-as-code/exercises/03-modules/README.md
- modules/module-11-infrastructure-as-code/exercises/04-data-infrastructure/README.md
- modules/module-11-infrastructure-as-code/exercises/05-state-management/README.md
- modules/module-11-infrastructure-as-code/exercises/06-production-ready/README.md
- modules/module-11-infrastructure-as-code/README.md
- modules/module-11-infrastructure-as-code/STATUS.md
- modules/module-11-infrastructure-as-code/theory/01-terraform-fundamentals.md
- modules/module-11-infrastructure-as-code/theory/02-terraform-advanced.md
- modules/module-11-infrastructure-as-code/theory/03-iac-patterns.md
- modules/module-12-serverless-processing/exercises/01-first-lambda/README.md
- modules/module-12-serverless-processing/exercises/04-rest-api-lambda/README.md
- modules/module-12-serverless-processing/exercises/06-production-pipeline/README.md
- modules/module-12-serverless-processing/theory/01-serverless-fundamentals.md
- modules/module-12-serverless-processing/theory/02-serverless-data-processing.md
- modules/module-12-serverless-processing/theory/03-serverless-patterns.md
- modules/module-13-container-orchestration/assets/diagrams/container-architecture.md
- modules/module-13-container-orchestration/exercises/01-docker-basics/README.md
- modules/module-13-container-orchestration/exercises/04-kubernetes-basics/README.md
- modules/module-13-container-orchestration/theory/01-docker-fundamentals.md
- modules/module-14-data-catalog-governance/STATUS.md
- modules/module-15-real-time-analytics/STATUS.md
- modules/module-18-advanced-architectures/STATUS.md
- modules/module-checkpoint-01-serverless-data-lake/README.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/CHECKLIST.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/infrastructure/README.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/README.md
- modules/module-checkpoint-02-realtime-analytics-platform/starter-template/infrastructure/README.md
- modules/module-checkpoint-02-realtime-analytics-platform/starter-template/README.md
- modules/module-checkpoint-03-enterprise-data-lakehouse/starter-template/
  README.md

## Markdown Files With Unchecked Checkboxes

- docs/TODO-HANDOFF-CONSOLIDATED.md
- docs/TODO-STRUCTURE-UNIFICATION.md
- modules/module-01-cloud-fundamentals/docs/troubleshooting.md
- modules/module-01-cloud-fundamentals/exercises/01-s3-basics/hints.md
- modules/module-01-cloud-fundamentals/exercises/01-s3-basics/README.md
- modules/module-01-cloud-fundamentals/exercises/02-iam-policies/README.md
- modules/module-01-cloud-fundamentals/README.md
- modules/module-01-cloud-fundamentals/validation/README.md
- modules/module-02-storage-basics/exercises/01-data-lake-design/hints.md
- modules/module-02-storage-basics/exercises/01-data-lake-design/starter/scenario.md
- modules/module-02-storage-basics/README.md
- modules/module-02-storage-basics/STATUS.md
- modules/module-02-storage-basics/theory/resources.md
- modules/module-03-sql-foundations/README.md
- modules/module-03-sql-foundations/STATUS.md
- modules/module-03-sql-foundations/theory/resources.md
- modules/module-04-python-for-data/docs/python-guide.md
- modules/module-04-python-for-data/README.md
- modules/module-04-python-for-data/STATUS.md
- modules/module-05-data-lakehouse/assets/optimization-checklist.md
- modules/module-05-data-lakehouse/exercises/02-medallion-architecture/README.md
- modules/module-05-data-lakehouse/exercises/03-time-travel/hints.md
- modules/module-05-data-lakehouse/exercises/03-time-travel/README.md
- modules/module-05-data-lakehouse/exercises/04-schema-evolution/hints.md
- modules/module-05-data-lakehouse/exercises/05-optimization/hints.md
- modules/module-05-data-lakehouse/exercises/06-iceberg-comparison/hints.md
- modules/module-06-etl-fundamentals/assets/etl-checklist.md
- modules/module-06-etl-fundamentals/README.md
- modules/module-07-batch-processing/assets/batch-processing-checklist.md
- modules/module-07-batch-processing/README.md
- modules/module-07-batch-processing/theory/03-resources.md
- modules/module-09-data-quality/exercises/01-data-profiling/README.md
- modules/module-09-data-quality/exercises/02-validation-rules/README.md
- modules/module-09-data-quality/exercises/03-great-expectations/README.md
- modules/module-09-data-quality/exercises/04-anomaly-detection/README.md
- modules/module-09-data-quality/exercises/05-quality-monitoring/README.md
- modules/module-09-data-quality/exercises/06-production-gates/README.md
- modules/module-09-data-quality/theory/03-resources.md
- modules/module-10-workflow-orchestration/exercises/06-production-deployment/README.md
- modules/module-10-workflow-orchestration/QUICK-START.md
- modules/module-10-workflow-orchestration/README.md
- modules/module-10-workflow-orchestration/STATUS.md
- modules/module-10-workflow-orchestration/theory/03-production-patterns.md
- modules/module-11-infrastructure-as-code/exercises/05-state-management/README.md
- modules/module-11-infrastructure-as-code/exercises/06-production-ready/README.md
- modules/module-11-infrastructure-as-code/README.md
- modules/module-11-infrastructure-as-code/STATUS.md
- modules/module-11-infrastructure-as-code/theory/03-iac-patterns.md
- modules/module-12-serverless-processing/exercises/01-first-lambda/README.md
- modules/module-12-serverless-processing/exercises/02-s3-event-processing/README.md
- modules/module-12-serverless-processing/exercises/03-step-functions/README.md
- modules/module-12-serverless-processing/exercises/04-rest-api-lambda/README.md
- modules/module-12-serverless-processing/exercises/05-sqs-messaging/README.md
- modules/module-12-serverless-processing/exercises/06-production-pipeline/README.md
- modules/module-12-serverless-processing/README.md
- modules/module-13-container-orchestration/README.md
- modules/module-13-container-orchestration/theory/01-docker-fundamentals.md
- modules/module-13-container-orchestration/theory/02-aws-ecs-fargate.md
- modules/module-14-data-catalog-governance/README.md
- modules/module-15-real-time-analytics/exercises/01-kinesis-analytics-sql/README.md
- modules/module-15-real-time-analytics/exercises/02-flink-table-api/README.md
- modules/module-15-real-time-analytics/exercises/03-real-time-dashboards/README.md
- modules/module-15-real-time-analytics/exercises/04-cep-fraud-detection/README.md
- modules/module-15-real-time-analytics/exercises/05-ml-scoring/README.md
- modules/module-15-real-time-analytics/exercises/06-production-deployment/README.md
- modules/module-15-real-time-analytics/README.md
- modules/module-16-data-security-compliance/exercises/01-iam-access-control/README.md
- modules/module-16-data-security-compliance/exercises/02-data-encryption/README.md
- modules/module-16-data-security-compliance/exercises/03-data-masking-anonymization/README.md
- modules/module-16-data-security-compliance/exercises/05-data-governance/README.md
- modules/module-16-data-security-compliance/exercises/06-security-monitoring/README.md
- modules/module-16-data-security-compliance/README.md
- modules/module-17-cost-optimization/exercises/01-cost-analysis/README.md
- modules/module-17-cost-optimization/exercises/02-storage-optimization/README.md
- modules/module-17-cost-optimization/exercises/03-compute-purchasing/README.md
- modules/module-17-cost-optimization/exercises/04-right-sizing/README.md
- modules/module-17-cost-optimization/exercises/05-serverless-costs/README.md
- modules/module-17-cost-optimization/exercises/06-cost-governance/README.md
- modules/module-17-cost-optimization/theory/architecture.md
- modules/module-17-cost-optimization/theory/best-practices.md
- modules/module-17-cost-optimization/theory/concepts.md
- modules/module-17-cost-optimization/theory/resources.md
- modules/module-18-advanced-architectures/README.md
- modules/module-18-advanced-architectures/STATUS.md
- modules/module-18-advanced-architectures/theory/resources.md
- modules/module-bonus-01-databricks-lakehouse/assets/diagrams/README.md
- modules/module-bonus-01-databricks-lakehouse/COST-ALERT.md
- modules/module-bonus-01-databricks-lakehouse/README.md
- modules/module-bonus-01-databricks-lakehouse/theory/best-practices.md
- modules/module-bonus-01-databricks-lakehouse/theory/setup-guide.md
- modules/module-bonus-02-snowflake-data-cloud/assets/diagrams/README.md
- modules/module-bonus-02-snowflake-data-cloud/exercises/exercise-03-time-travel-recovery/README.md
- modules/module-checkpoint-01-serverless-data-lake/docs/ARCHITECTURE-DECISIONS.md
- modules/module-checkpoint-01-serverless-data-lake/docs/COST-ESTIMATION.md
- modules/module-checkpoint-01-serverless-data-lake/docs/PROJECT-BRIEF.md
- modules/module-checkpoint-01-serverless-data-lake/docs/README.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/CHECKLIST.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/infrastructure/README.md
- modules/module-checkpoint-01-serverless-data-lake/starter-template/README.md
- modules/module-checkpoint-02-realtime-analytics-platform/docs/PROJECT-BRIEF.md
- modules/module-checkpoint-02-realtime-analytics-platform/docs/README.md
- modules/module-checkpoint-02-realtime-analytics-platform/starter-template/CHECKLIST.md
- modules/module-checkpoint-03-enterprise-data-lakehouse/docs/IMPLEMENTATION-GUIDE.md
- modules/module-checkpoint-03-enterprise-data-lakehouse/README.md
- modules/module-checkpoint-03-enterprise-data-lakehouse/starter-template/CHECKLIST.md
- modules/module-checkpoint-03-enterprise-data-lakehouse/starter-template/README.md

## Handoff Notes For Next Session

- Prioritize operational checklist in docs/TODO-STRUCTURE-UNIFICATION.md first.
- Treat module exercise TODOs/checklists as curriculum content unless
  explicitly requested as repo debt.
- If updating this report, regenerate with the same commands to keep consistency.
