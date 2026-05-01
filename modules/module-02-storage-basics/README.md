# Module 02: Storage Fundamentals and Data Formats

⏱️ **Estimated Time:** 10-12 hours

## Prerequisitos

- Module 01: Cloud Fundamentals (completed)

## Module Overview

Master the fundamentals of data storage and file formats essential for data engineering. Dive deeper into S3 as a data lake, learn how to choose optimal formats (JSON, CSV, Parquet, Avro), and understand partitioning and compression for performance.

## Objetivos de Aprendizaje

Upon completion of this module, you will be able to:

- [x] Design data lakes with medallion architecture (Bronze/Silver/Gold)
- [x] Select optimal formats according to use case (analytical vs transactional)
- [x] Implement Hive-style partitioning to optimize queries
- [x] Apply compression (Snappy, Gzip, LZ4) according to trade-offs
- [x] Convert between formats with PyArrow and pandas
- [x] Calculate storage costs and optimize TCO
- [x] Implement schema evolution in Parquet
- [x] Optimize metadata with Glue Catalog

## Estructura

- **theory/**: Core concepts and architectural documentation
- **exercises/**: Practical exercises (6 exercises)
- **infrastructure/**: LocalStack/Docker configuration for this module
- **data/**: Sample datasets and schemas
- **validation/**: Automated tests to validate your learning
- **scripts/**: Help scripts

## Comenzando

1. Make sure prerequisites are completed
2. Install dependencies: `pip install -r requirements.txt`
3. Generate sample data: `cd data/sample && bash generate_users.sh && cd ../..`
4. Read `theory/concepts.md` for fundamental understanding
5. Review `theory/architecture.md` for AWS architecture patterns
6. Configure infrastructure: `bash scripts/setup.sh`
7. Complete exercises in order (01 to 06)
8. Validate your learning: `bash scripts/validate.sh`

## Ejercicios

1. **Exercise 01**: Data Lake Medallion Design - Design Bronze/Silver/Gold architecture with S3, lifecycle policies, and IAM
2. **Exercise 02**: File Format Conversion - Convert between CSV, JSON, Parquet, Avro with performance benchmarking
3. **Exercise 03**: Partitioning Strategies - Implement Hive style partitioning (date, geography, hybrid) to optimize queries
4. **Exercise 04**: Compression Optimization - Compare Snappy, Gzip, LZ4, Zstd compression algorithms for Parquet
5. **Exercise 05**: Schema Evolution - Add columns, handle backward/forward compatibility in Parquet files
6. **Exercise 06**: Integration with Glue Catalog - Register datasets, create crawlers, query with Athena

## resources

See `theory/resources.md` for:
- Official AWS Documentation
- Video tutorials and workshops
- community resources
- Certification mapping

## Validation

Ejecutar todas las validaciones:
```bash
bash scripts/validate.sh
```

Or use global validation:
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

## Siguientes Pasos

After completing this module, you will be ready to:
[List of modules that depend on it]

## Learning Objectives

- Understand the core concept boundaries for this module.
- Apply the concept through guided exercises.
- Validate outcomes using module checks.

## Prerequisites

Review previous dependent modules according to LEARNING-PATH.md before starting.

## Validation

Run the corresponding module validation and confirm expected outputs.
