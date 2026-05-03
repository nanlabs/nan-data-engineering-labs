# Module 09: Data Quality

⏱️ **Estimated duration:** 15-20 hours
🎯 **Level:** Intermediate-Advanced
📊 **Status:** ✅ Completed

## 📋 Description

Complete module on data quality that covers the 6 dimensions of quality, business frameworks (Great Expectations, Pandera, PyDeequ), anomaly detection, continuous monitoring and quality gates in production.

## 🎯 Learning Objectives

By completing this module, you will be able to:

- ✅ Understand and apply the **6 dimensions of data quality**
- ✅ Implement manual and automatic **data profiling**
- ✅ Create custom **validation rules**
- ✅ Dominar **Great Expectations** para validaciones empresariales
- ✅ Detect **anomalies** using statistical methods and ML
- ✅ Implement **continuous quality monitoring**
- ✅ Configure **quality gates** in production pipelines
- ✅ Manage **quarantine zones** and automatic rollback

## 📚 Content

### Theory (45,000 palabras)

- **01-concepts.md** - 6 Quality dimensions, profiling, metrics
- **02-architecture.md** - Great Expectations, Pandera, PyDeequ, architecture patterns
- **03-resources.md** - Herramientas, cloud services, resources de aprendizaje

### Exercises (6 progressive exercises)

1. **Data Profiling** - Manual and automatic profiling, outlier detection
2. **Validation Rules** - Custom rules, validation framework
3. **Great Expectations** - Setup, expectation suites, checkpoints, Data Docs
4. **Anomaly Detection** - Statistical and ML methods, time series
5. **Quality Monitoring** - Continuous metrics, quality drift, alerts
6. **Production Quality Gates** - Integration with Airflow, circuit breakers, versioning

### Data

- **generate_data.py** - Script to generate datasets with configurable quality
- **Schemas** - JSON schemas con qualityRules para 3 tables
- **3 quality levels** - clean, medium, poor

### Validation

- **50+ tests** - Pytest suite completa
- **Markers** - smoke, profiling, validation, great_expectations, anomaly_detection, monitoring
- **Coverage** - HTML coverage reports

## 🚀 Quick Start

```bash
# 1. Setup
./scripts/setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Generate sample data
python data/scripts/generate_data.py --quality clean --output data/generated/

# 4. Start with exercises
# See exercises/01-data-profiling/README.md

# 5. Validate completion
./scripts/validate.sh
```

## 🛠️ Technologies

### Core Frameworks
- **Great Expectations** 0.18+ - Validaciones empresariales
- **Pandera** 0.17+ - Schema-based validation
- **PyDeequ** 1.1+ - Big data quality (Spark)

### Profiling & Analysis
- **ydata-profiling** 4.5+ - Automatic profiling
- **scipy** 1.11+ - Statistical methods

### Anomaly Detection
- **PyOD** 1.1+ - Outlier detection algorithms
- **scikit-learn** 1.3+ - Isolation Forest, LOF

### Testing
- **pytest** 7.4+ - Testing framework
- **pytest-cov** 4.1+ - Coverage reports

## 📖 Prerequisites

- ✅ Module 04: Python for Data (100%)
- ✅ Module 06: ETL Fundamentals (100%)
- Python 3.9+
- Conocimiento de Pandas, NumPy

## ✅ Validation

```bash
# Run all tests
pytest validation/ -v

# Run specific categories
pytest validation/ -m smoke
pytest validation/ -m profiling
pytest validation/ -m validation
pytest validation/ -m anomaly_detection

# Generate coverage
pytest validation/ --cov=. --cov-report=html

# Full validation

./scripts/validate.sh
```

## 📊 Module Metrics

- **Files**: 30+ archivos
- **Documentation**: ~45,000 palabras
- **Code**: ~2,000 Python lines
- **Tests**: 50+ tests
- **Exercises**: 6 progressive exercises

## 🔗 Resources

- [Great Expectations Docs](https://docs.greatexpectations.io/)
- [Pandera Documentation](https://pandera.readthedocs.io/)
- [PyOD Documentation](https://pyod.readthedocs.io/)

## ➡️ Next Modules

- **Module 10: Workflow Orchestration**
- **Module 11: Infrastructure as Code**

---

**Status**: ✅ 100% Completed
**Last Updated**: 2024

## Objective

This module focuses on one core concept and its practical implementation path.

## Learning Objectives

- Understand the core concept boundaries for this module.
- Apply the concept through guided exercises.
- Validate outcomes using module checks.
