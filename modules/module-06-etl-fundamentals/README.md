# Module 06: ETL (Extract, Transform, Load) Fundamentals

## 📋 Description

Welcome to Module 06 of the Data Engineering bootcamp. In this module you will learn the fundamentals of **ETL (Extract, Transform, Load)**, the core process of data engineering to move and transform data between systems.

⏱️ **Estimated duration**: 12-15 hours

## 🎯 Learning Objectives

By completing this module, you will be able to:

- ✅ Comprender los conceptos fundamentales de ETL
- ✅ Extract data from multiple sources (CSV, JSON, APIs, databases)
- ✅ Transformar datos usando pandas y Python
- ✅ Cargar datos a diferentes destinos
- ✅ Construir pipelines ETL completos y robustos
- ✅ Implementar manejo de errores y logging
- ✅ Validar calidad de datos y crear data quality checks

## 📦 Prerequisitos

Before beginning this module, you must have completed:

- ✅ **Module 02**: Storage Basics (reading/writing files)
- ✅ **Module 04**: Python for Data (pandas, testing)

**Conocimientos necesarios**:
- Python intermedio (funciones, clases, manejo de excepciones)
- basic pandas (DataFrame operations)
- Basic SQL (queries, inserts)
- Conceptos de APIs REST

**Software requerido**:
- Python 3.8+
- pip y virtualenv
- SQLite (incluido en Python)

## 🏗️ Arquitectura ETL

```
┌─────────────────────────────────────────────────────────────┐
│                      ETL PIPELINE                            │
│                                                               │
│  ┌──────────┐      ┌──────────────┐      ┌──────────┐      │
│  │ EXTRACT  │  →   │  TRANSFORM   │  →   │   LOAD   │      │
│  └──────────┘      └──────────────┘      └──────────┘      │
│       ↓                    ↓                     ↓           │
│   Sources           Processing            Destinations       │
│   • CSV             • Clean               • Database         │
│   • JSON            • Filter              • Data Lake        │
│   • APIs            • Aggregate           • Data Warehouse   │
│   • Databases       • Join                • Files            │
│   • Logs            • Enrich              • APIs             │
│                                                               │
│  Cross-cutting Concerns:                                     │
│  ✓ Logging & Monitoring   ✓ Error Handling                  │
│  ✓ Data Quality           ✓ Performance                     │
│  ✓ Idempotency            ✓ Testing                         │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Module Structure

```
module-06-etl-fundamentals/
├── README.md                          # Este archivo
├── STATUS.md                          # Estado de completitud
├── requirements.txt                   # Dependencias Python
│
├── theory/                            # Material teórico
│   ├── 01-concepts.md                 # Conceptos fundamentales ETL
│   ├── 02-patterns.md                 # Patrones y best practices
│   └── 03-resources.md                # Recursos adicionales
│
├── exercises/                         # 6 ejercicios prácticos
│   ├── 01-extract-basics/             # Extracción de datos
│   ├── 02-transform-basics/           # Transformaciones
│   ├── 03-load-basics/                # Carga de datos
│   ├── 04-full-pipeline/              # Pipeline ETL completo
│   ├── 05-error-handling/             # Errores y logging
│   └── 06-data-quality/               # Calidad de datos
│
├── data/                              # Datasets de ejemplo
│   ├── raw/                           # Datos crudos
│   ├── schemas/                       # Esquemas de datos
│   └── scripts/                       # Scripts generación datos
│
├── validation/                        # Tests automatizados
│   ├── conftest.py                    # Fixtures de pytest
│   └── test_*.py                      # Tests por ejercicio
│
├── scripts/                           # Scripts de automatización
│   ├── setup.sh                       # Setup del entorno
│   ├── validate.sh                    # Ejecutar tests
│   └── run_pipeline.sh                # Ejecutar pipeline ejemplo
│
└── assets/                            # Cheatsheets y referencia
    ├── etl-checklist.md
    └── pandas-transforms.md
```

## 🎓 Exercises

### Exercise 01: Extract Basics (⭐ Basic - 1.5h)
Data extraction from different sources: CSV, JSON, APIs, SQLite

### Exercise 02: Transform Basics (⭐⭐ Intermediate - 2h)
Common transformations: cleanup, type conversion, aggregations

### Exercise 03: Load Basics (⭐⭐ Intermediate - 1.5h)
Carga de datos: CSV, JSON, SQLite con upsert

### Exercise 04: Full pipeline (⭐⭐⭐ Advanced - 3h)
pipeline ETL end-to-end modular y configurable

### Exercise 05: Error Handling (⭐⭐⭐⭐ Advanced - 2h)
Manejo robusto de errores, logging, retry logic

### Exercise 06: Data Quality (⭐⭐⭐⭐⭐ Expert - 2.5h)
Data quality validation and anomaly detection

## 📊 Progress Checklist

- [ ] Read the entire theory
- [ ] Complete Exercise 01
- [ ] Complete Exercise 02
- [ ] Complete Exercise 03
- [ ] Complete Exercise 04
- [ ] Complete Exercise 05
- [ ] Complete Exercise 06
- [ ] Todos los tests pasan

## ➡️ Next Steps

- **Module 07**: Batch Processing (PySpark)
- **Module 08**: Streaming Basics (Kafka)
- **Module 10**: Workflow Orchestration (Airflow)

## Objective

This module focuses on one core concept and its practical implementation path.

## Learning Objectives

- Understand the core concept boundaries for this module.
- Apply the concept through guided exercises.
- Validate outcomes using module checks.

## Prerequisites

Review previous dependent modules according to LEARNING-PATH.md before starting.

## Validation

Run the corresponding module validation and confirm expected outputs.
