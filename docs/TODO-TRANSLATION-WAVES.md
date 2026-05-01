# TODO: Translation Migration Waves

This checklist controls incremental migration of translated submodule content from source repository into `nan-data-engineering-labs`.

## Global Rules (Apply to Every Wave)

- [ ] Keep folder names and module taxonomy from destination repository.
- [ ] Keep all new/edited governance and instructional content in English.
- [ ] Preserve exercise unit contract in each exercise folder:
  - `README.md`
  - `hints.md`
  - `starter/`
  - `solution/`
  - `my_solution/`
- [ ] Run contract validation after each wave:
  - `python scripts/validate_learning_labs.py --strict-core --strict-headings`
- [ ] Run full language validation after each wave:
  - `python scripts/validate_english_content.py --full-scan`
- [ ] Save evidence in `docs/validation-evidence/`.

## Wave 1 (Modules 01-06)

- [ ] `module-01-cloud-fundamentals`
- [ ] `module-02-storage-basics`
- [ ] `module-03-sql-foundations`
- [ ] `module-04-python-for-data`
- [ ] `module-05-data-lakehouse`
- [ ] `module-06-etl-fundamentals`
- [ ] Validate and record evidence.

## Wave 2 (Modules 07-12)

- [ ] `module-07-batch-processing`
- [ ] `module-08-streaming-basics`
- [ ] `module-09-data-quality`
- [ ] `module-10-workflow-orchestration`
- [ ] `module-11-infrastructure-as-code`
- [ ] `module-12-serverless-processing`
- [ ] Validate and record evidence.

## Wave 3 (Modules 13-18)

- [ ] `module-13-container-orchestration`
- [ ] `module-14-data-catalog-governance`
- [ ] `module-15-real-time-analytics`
- [ ] `module-16-data-security-compliance`
- [ ] `module-17-cost-optimization`
- [ ] `module-18-advanced-architectures`
- [ ] Validate and record evidence.

## Wave 4 (Checkpoints)

- [ ] `module-checkpoint-01-serverless-data-lake`
- [ ] `module-checkpoint-02-realtime-analytics-platform`
- [ ] `module-checkpoint-03-enterprise-data-lakehouse`
- [ ] Ensure each checkpoint includes `README.md` and acceptance validation assets.
- [ ] Validate and record evidence.

## Wave 5 (Bonus Modules)

- [ ] `module-bonus-01-databricks-lakehouse`
- [ ] `module-bonus-02-snowflake-data-cloud`
- [ ] Ensure optional tracks do not break default prerequisite path.
- [ ] Validate and record evidence.
