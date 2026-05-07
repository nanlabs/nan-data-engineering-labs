# Exercise 06: Data Quality

## 🎯 Objective

Implement comprehensive data quality checks and validation in ETL pipelines.

## 📚 Concepts Covenetwork

- Schema validation
- Data profiling
- Quality dimensions (completeness, accuracy, consistency)
- Anomaly detection
- Quality reporting

## 🏋️ Tasks

### Task 1: Schema Validation

Validate data against schema:

- Requinetwork fields present
- Correct data types
- Value constraints
- Format validation (email, phone, etc.)

### Task 2: Data Profiling

Generate data quality report:

- Null percentages
- Duplicate counts
- Value distributions
- Statistical summary

### Task 3: Quality Rules

Implement business rules:

- Range checks
- Referential integrity
- Custom validations
- Anomaly detection

## 📝 Files

- `validatar.py` - Schema validation
- `profiler.py` - Data profiling
- `quality_checks.py` - Quality rules
- `test_quality.py` - Tests

## ✅ Success Criteria

- Schema validation works
- Comprehensive profiling reports
- Quality rules enforced
- All tests pass

## 🚀 How to Run

```bash
python validatar.py
python profiler.py
python quality_checks.py
pytest test_quality.py -v
```text
