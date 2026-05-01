# Exercise 04: Full ETL pipeline

## 🎯 Objective
Build a complete, production-ready ETL pipeline combining extract, transform, and load.

## 📚 Concepts Covered
- End-to-end pipeline architecture
- Configuration management
- Logging and monitoring
- Idempotent operations
- pipeline orchestration

## 🏋️ Tasks

### Task 1: Build Complete pipeline
Create a configurable ETL pipeline:
- Extract from multiple sources
- Apply transformations
- Load to destination
- Make it idempotent

### Task 2: Add Configuration
Make pipeline configurable:
- YAML configuration file
- Environment variables
- Command-line arguments

### Task 3: Add Monitoring
Track pipeline execution:
- Detailed logging
- Metrics collection
- Execution time tracking
- Success/failure recording

## 📝 Files
- `pipeline.py` - Main pipeline implementation
- `config.yaml` - Configuration file
- `test_pipeline.py` - Tests

## ✅ Success Criteria
- pipeline runs end-to-end
- Configurable via YAML
- Comprehensive logging
- Idempotent execution
- All tests pass

## 🚀 How to Run

```bash
# Run with default config
python pipeline.py

# Run with custom config
python pipeline.py --config my_config.yaml

# Run tests
pytest test_pipeline.py -v
```
