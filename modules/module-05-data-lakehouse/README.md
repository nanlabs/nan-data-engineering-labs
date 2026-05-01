# Module 05: Data Lakehouse Architecture ✅ 100% COMPLETE

## 📋 Description

Welcome to Module 05 of the Data Engineering bootcamp. In this module we will delve into **Data Lakehouse architecture**, the most recent evolution in large-scale data storage and processing that combines the best of Data Lakes and Data Warehouses.

**🎉 Status: COMPLETED - 68 files, 6 exercises, 26 tests, 614,500 synthetic records**

### 🎯 Objetivos de Aprendizaje

By completing this module, you will be able to:

- ✅ Comprender la arquitectura y principios del Data Lakehouse
- ✅ Diferenciar entre Data Lake, Data Warehouse y Data Lakehouse
- ✅ Implementar tables Delta Lake con transactions ACID
- ✅ Trabajar con Apache Iceberg y comparar formatos de table
- ✅ Design and implement the Medallion architecture (Bronze/Silver/Gold)
- ✅ Use Time Travel for auditing and data recovery
- ✅ Gestionar Schema Evolution sin romper pipelines
- ✅ Optimizar el performance con particionamiento y Z-ordering
- ✅ Implementar pipelines de datos scalables y confiables

### 🏗️ Arquitectura Data Lakehouse

El **Data Lakehouse** es un paradigma moderno que combina:

- **Flexibilidad de Data Lakes**: storage de datos estructurados, semi-estructurados y no estructurados
- **reliability de Data Warehouses**: transactions ACID, versionado, schema enforcement
- **optimized performance**: Indexing, caching, query optimization
- **Governance**: Auditing, data lineage, access control

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAKEHOUSE                            │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Storage   │  │   Metadata   │  │  Query Engine    │    │
│  │  (S3/MinIO)│  │  (Delta/Ice) │  │  (Spark/Presto)  │    │
│  └────────────┘  └──────────────┘  └──────────────────┘    │
│                                                               │
│  Features:                                                    │
│  ✓ ACID Transactions    ✓ Time Travel                       │
│  ✓ Schema Evolution     ✓ Data Versioning                   │
│  ✓ Unified Batch+Stream ✓ BI + ML Workloads                 │
└─────────────────────────────────────────────────────────────┘
```

### 🌊 Arquitectura Medallion

We will implement **Medallion architecture**, a design pattern that organizes data into three layers:

#### 🥉 Bronze Layer (Raw Data)
- Datos crudos tal como llegan de las fuentes
- Minimal transformation (ingestion only)
- Append-only, inmutable
- Preserva el linaje completo

#### 🥈 Silver Layer (Refined Data)
- Datos limpios y validados
- Deduplication and normalization
- Tipos de datos correctos
- Business rules aplicadas

#### 🥇 Gold Layer (Business-Level Aggregates)
- Datos optimizados para consumo
- Aggregations and business metrics
- Modelos dimensionales o de features
- Listos para BI/Analytics/ML

```
Sources → [Bronze] → [Silver] → [Gold] → Analytics/ML
          (Raw)      (Cleaned)  (Aggregated)
```

### 🔧 Main Technologies

#### Delta Lake (70% of the module)

**Delta Lake** es un formato de table open-source desarrollado por Databricks que agrega:

- ✅ **ACID Transactions**: Atomic, consistent, isolated and durable writes
- ✅ **Time Travel**: Access to historical data versions
- ✅ **Schema Enforcement**: Automatic schema validation
- ✅ **Schema Evolution**: Add/modify columns without breaking pipelines
- ✅ **Unified Streaming + Batch**: Misma table para ambos workloads
- ✅ **Scalable Metadata**: Manejo eficiente de millones de archivos
- ✅ **Data Versioning**: Rollback, audit trails completos

**Caso de uso ideal**: Pipelines de datos empresariales que requieren alta reliability

#### Apache Iceberg (30% of the module)

**Apache Iceberg** es un formato de table open-source de Netflix/Apache con:

- ✅ **Snapshot Isolation**: Consistencia a nivel de snapshot
- ✅ **Hidden Partitioning**: Transparent automatic partitioning
- ✅ **Time Travel**: Queries about historical snapshots
- ✅ **Schema Evolution**: Safe schema evolution
- ✅ **Partition Evolution**: Cambiar estrategia de particionamiento sin reescribir
- ✅ **Multi-Engine Support**: Compatible con Spark, Flink, Presto, Trino

**Caso de uso ideal**: Entornos multi-engine con requerimientos de flexibilidad

### 🏛️ Comparison: Lake vs Warehouse vs Lakehouse

| feature | Data Lake | Data Warehouse | Data Lakehouse |
|----------------|-----------|----------------|----------------|
| **Datos soportados** | Todos (struct/semi/no-struct) | Solo estructurados | Todos |
| **Formato** | Parquet, CSV, JSON | Propietario (columnr) | Delta/Iceberg |
| **Schema** | Schema-on-read | Schema-on-write | Flexible (ambos) |
| **transactions ACID** | ❌ No | ✅ Yes | ✅ Yes |
| **Performance BI** | ⚠️ Slow | ✅ Fast | ✅ Fast |
| **Costo** | 💰 Bajo | 💰💰💰 Alto | 💰💰 Medio |
| **ML Support** | ✅ Excelente | ⚠️ Limitado | ✅ Excelente |
| **scalability** | ✅ Petabytes+ | ⚠️ Terabytes | ✅ Petabytes+ |
| **Governance** | ⚠️ Complejo | ✅ Robusto | ✅ Robusto |
| **Time Travel** | ❌ No | ⚠️ Limitado | ✅ Yes |

### 📦 Prerequisitos

Before beginning this module, you must have completed:

- ✅ **Module 02**: Storage Basics (S3/MinIO, Parquet, partitioning)
- ⚠️ **Module 03**: SQL Foundations (queries, joins, window functions) - Recommended
- ⚠️ **Module 04**: Python for Data (pandas, testing, pipelines) - Recommended

**Conocimientos necesarios**:
- Basic Linux/Bash Commands
- Conceptos de databases relacionales
- Python intermedio (funciones, clases, manejo de errores)
- Basic PySpark (we will learn in the module)

**Software requerido**:
- Docker y Docker Compose
- Python 3.8+
- 8GB RAM minimum (16GB recommended)
- 10GB espacio en disco

### 📂 Module Structure

```
module-05-data-lakehouse/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias Python
├── STATUS.md                          # Tracking de progreso
├── .gitignore                         # Archivos ignorados
│
├── theory/                            # Material teórico
│   ├── 01-concepts.md                 # Conceptos fundamentales
│   ├── 02-architecture.md             # Arquitectura y patrones
│   └── 03-resources.md                # Recursos adicionales
│
├── infrastructure/                    # Infraestructura Docker
│   ├── docker-compose.yml             # Servicios: Spark, MinIO, Jupyter
│   ├── spark/                         # Configuración Spark
│   ├── minio/                         # Configuración MinIO (S3)
│   └── init-scripts/                  # Scripts de inicialización
│
├── data/                              # Datasets
│   ├── raw/                           # Datos crudos (Bronze layer)
│   ├── schemas/                       # Esquemas JSON
│   └── scripts/                       # Scripts generación de datos
│
├── exercises/                         # 6 ejercicios prácticos
│   ├── 01-delta-basics/               # ⭐ Fundamentos Delta Lake
│   ├── 02-medallion-architecture/     # ⭐⭐⭐ Implementar Bronze/Silver/Gold
│   ├── 03-time-travel/                # ⭐⭐⭐ Time Travel y versionado
│   ├── 04-schema-evolution/           # ⭐⭐⭐⭐ Evolución de esquemas
│   ├── 05-optimization/               # ⭐⭐⭐⭐ Optimización y tuning
│   └── 06-iceberg-comparison/         # ⭐⭐⭐⭐⭐ Delta vs Iceberg
│
├── validation/                        # Tests automáticos
│   ├── conftest.py                    # Fixtures compartidos
│   ├── test_integration.py            # Tests de integración
│   ├── test_data_quality.py           # Tests de calidad de datos
│   └── test_module_completeness.py    # Tests de completitud
│
├── assets/                            # Recursos de apoyo
│   ├── cheatsheets/                   # Guías rápidas
│   │   ├── delta-commands.md          # Comandos Delta Lake
│   │   ├── medallion-patterns.md      # Patrones Medallion
│   │   ├── table-formats.md           # Comparación formatos
│   │   └── spark-optimization.md      # Optimización Spark
│   └── diagrams/                      # Diagramas arquitectura
│       ├── medallion-flow.md          # Flujo Medallion
│       ├── delta-architecture.md      # Arquitectura Delta
│       └── partitioning.md            # Estrategias particionamiento
│
├── scripts/                           # Automatización
│   ├── setup.sh                       # Setup completo del entorno
│   ├── validate.sh                    # Ejecutar todos los tests
│   ├── run_spark.sh                   # Spark shell interactivo
│   └── run_jupyter.sh                 # Jupyter Lab
│
└── docs/                              # Documentación adicional
    ├── troubleshooting-spark.md       # Solución de problemas
    └── lakehouse-guide.md             # Guía de mejores prácticas
```

### 🚀 Quick Start

#### 1. Setup del Entorno

```bash
# Clonar el repositorio (si aún no lo has hecho)
cd training-cloud-data/modules/module-05-data-lakehouse

# Instalar dependencias
./scripts/setup.sh

# Levantar infraestructura Docker
docker-compose up -d

# Verificar que todo está corriendo
docker-compose ps
```

#### 2. Explore Theoretical Material

```bash
# Leer conceptos fundamentales
cat theory/01-concepts.md

# Estudiar arquitectura Medallion
cat theory/02-architecture.md
```

#### 3. Ejecutar Ejercicios

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejercicio 1: Delta Lake Basics
cd exercises/01-delta-basics
pytest test_solution.py -v

# Jupyter Lab para desarrollo interactivo
./scripts/run_jupyter.sh
```

#### 4. Validate the Complete Module

```bash
# Ejecutar todos los tests
./scripts/validate.sh --all

# Con reporte de cobertura
./scripts/validate.sh --coverage
```

### 📊 Ejercicios y Dificultad

| Ejercicio | Dificultad | Tiempo | Temas Clave |
|-----------|------------|--------|-------------|
| **01-delta-basics** | ⭐ Basic | 1-2h | Create, Read, Write, Append, Overwrite |
| **02-medallion-architecture** | ⭐⭐⭐ Intermedio | 3-4h | Bronze→Silver→Gold, Data Quality, Transformations |
| **03-time-travel** | ⭐⭐⭐ Intermedio | 2-3h | Versioning, Rollback, Audit Trails |
| **04-schema-evolution** | ⭐⭐⭐⭐ Avanzado | 2-3h | Add/Drop Columns, Type Changes, Compatibility |
| **05-optimization** | ⭐⭐⭐⭐ Avanzado | 3-4h | Partitioning, Z-ordering, Compaction, Vacuum |
| **06-iceberg-comparison** | ⭐⭐⭐⭐⭐ Experto | 4-5h | Delta vs Iceberg, Migration, Trade-offs |

**Tiempo total estimado**: 15-21 horas

### 🎓 Learning Path

```
1. Theory (3-4h)
   └─ Concepts → Architecture → Resources

2. Infrastructure (1-2h)
   └─ Docker Setup → Spark Config → MinIO S3

3. Hands-on Exercises (12-15h)
   └─ Delta Basics → Medallion → Time Travel → Evolution → Optimization → Iceberg

4. Project (Optional, 4-6h)
   └─ End-to-End Lakehouse Pipeline
```

### 📚 Additional Resources

- 📖 [Delta Lake Documentation](https://docs.delta.io/)
- 📖 [Apache Iceberg Documentation](https://iceberg.apache.org/)
- 📖 [Databricks Lakehouse Whitepaper](https://www.databricks.com/research/lakehouse-a-new-generation-of-open-platforms)
- 📖 [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- 🎥 [Medallion Architecture Explained](https://www.databricks.com/glossary/medallion-architecture)
- 📝 [Delta Lake vs Apache Iceberg Comparison](https://delta.io/blog/delta-lake-vs-iceberg/)

### 🆘 Troubleshooting

If you encounter problems during the module:

1. **query documentation**: [docs/troubleshooting-spark.md](docs/troubleshooting-spark.md)
2. **Revisa los logs**: `docker-compose logs spark-master`
3. **Verifica la infraestructura**: `docker-compose ps` y `docker-compose logs`
4. **Run the diagnostic tests**:`./scripts/validate.sh --fast`

### 🤝 Contribuciones

Si encuentras errores o tienes sugerencias de mejora, por favor:

1. Abre un issue en el repositorio
2. Provide specific details (error, context, steps to reproduce)
3. Incluye logs relevantes si es posible

### 📝 Notas Importantes

- ⚠️ **resources de hardware**: Algunos ejercicios requieren procesamiento intensivo
- 💾 **storage**: The datasets will generate ~2GB of data
- 🐳 **Docker**: Make sure you have Docker running before you start
- 🔒 **Permissions**: Scripts need execution permissions (`chmod +x scripts/*.sh`)

### 🎯 Next Steps

Once you complete this module, you will be prepared to:

- **Module 07**: Batch Processing with Apache Spark (processes the lakehouses)
- **Module 14**: Data Governance & Security (governance in lakehouses)
- **Checkpoint 01**: Proyecto integrador Tier 2

---

## 🚀 Let's get started!

El Data Lakehouse representa el futuro del storage y procesamiento de datos. Combina la flexibilidad de los Data Lakes con la reliability de los Data Warehouses, permitiendo workloads de BI y ML sobre la misma plataforma.

**Ready to build your first Lakehouse?**

Comienza leyendo [theory/01-concepts.md](theory/01-concepts.md) y luego ejecuta `./scripts/setup.sh` para configurar el entorno.

---

**Last update**: February 2026
**Module version**: 1.0.0
**Estado**: En desarrollo 🚧
