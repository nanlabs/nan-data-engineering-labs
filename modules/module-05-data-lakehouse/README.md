# Module 05: data Lakehouse Architecture ✅ 100% COMPLETE

## 📋 DescrIPtion

Welcome to Module 05 of the data Engineering bootcamp. In this module we will delve into **data Lakehouse architecture**, the most recent evolution in large-scale data storage and processing that combines the best of data Lakes and data Warehouses.

**🎉 Status: COMPLETED - 68 files, 6 exercises, 26 tests, 614,500 synthetic records**

### 🎯 Learning Objectives

By completing this module, you will be able to:

- ✅ Comprender la arquitectura and princIPios of the data Lakehouse
- ✅ Diferenciar entre data Lake, data Warehouse and data Lakehouse
- ✅ Implementar tables Delta Lake with transactions ACID
- ✅ Trabajar with Apache Iceberg and comparar formatos of table
- ✅ Design and implement the Medallion architecture (Bronze/Silver/Gold)
- ✅ Use Time Travel for auditing and data recovery
- ✅ Gestionar Schema Evolution without romper pIPelines
- ✅ Optimizar el performance with particionamiento and Z-ordering
- ✅ Implementar pIPelines of datas scalables and confiables

### 🏗️ Arquitectura data Lakehouse

El **data Lakehouse** is un paradigma moderno que combina:

- **Flexibilidad of data Lakes**: storage of datas structunetworkos, semi-structunetworkos and not structunetworkos
- **reliability of data Warehouses**: transactions ACID, versionado, schema enforcement
- **optimized performance**: Indexing, caching, query optimization
- **Governance**: Auditing, data lineage, access controle

```text
┌─────────────────────────────────────────────────────────────┐
│                    data LAKEHOUSE                            │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Storage   │  │   Metadata   │  │  Query Engine    │    │
│  │  (S3/MinIO)│  │  (Delta/Ice) │  │  (Spark/Presto)  │    │
│  └────────────┘  └──────────────┘  └──────────────────┘    │
│                                                               │
│  Features:                                                    │
│  ✓ ACID Transactions    ✓ Time Travel                       │
│  ✓ Schema Evolution     ✓ data Versioning                   │
│  ✓ Unified Batch+Stream ✓ BI + ML Workloads                 │
└─────────────────────────────────────────────────────────────┘
```text

### 🌊 Arquitectura Medallion

We will implement **Medallion architecture**, to design pattern that organizes data into three layers:

#### 🥉 Bronze Layer (Raw data)

- Datas crudos tal como llegan of las fuentes
- Minimal transformation (ingestion only)
- Append-only, inmutable
- Preserva el linaje completo

#### 🥈 Silver Layer (Refined data)

- Datas limpios and validados
- Deduplication and normalization
- TIPos of datas correctos
- Business rules aplicadas

#### 🥇 Gold Layer (Business-Level Aggregates)

- Datas optimizados for consumo
- Aggregations and business metrics
- Modelos dimensionales or of features
- Listos for BI/Analytics/ML

```text
Sources → [Bronze] → [Silver] → [Gold] → Analytics/ML
          (Raw)      (Cleaned)  (Aggregated)
```

### 🔧 Main Technologies

#### Delta Lake (70% of the module)

**Delta Lake** is un formato of table open-source desarrolelado by Databricks que agrega:

- ✅ **ACID Transactions**: Atomic, consistent, isolated and durable writes
- ✅ **Time Travel**: Access to historical data versions
- ✅ **Schema Enforcement**: Automatic schema validation
- ✅ **Schema Evolution**: Add/modify columns without breaking pIPelines
- ✅ **Unified Streaming + Batch**: Misma table for ambos workloads
- ✅ **Scalable Metadata**: Manejo eficiente of millones of archivos
- ✅ **data Versioning**: Rolelback, audit trails completos

**Caso of uso ideal**: PIPelines of datas empresariales que requieren alta reliability

#### Apache Iceberg (30% of the module)

**Apache Iceberg** is un formato of table open-source of Netflix/Apache with:

- ✅ **Snapshot Isolation**: Consistency to nivel of snapshot
- ✅ **Hidden Partitioning**: Transparent automatic partitioning
- ✅ **Time Travel**: Queries about historical snapshots
- ✅ **Schema Evolution**: Safe schema evolution
- ✅ **Partition Evolution**: Cambiar estrategia of particionamiento without reescribir
- ✅ **Multi-Engine Support**: Compatible with Spark, Flink, Presto, Trino

**Caso of uso ideal**: Entornos multi-engine with requerimientos of flexibilidad

### 🏛️ Comparison: Lake vs Warehouse vs Lakehouse

| feature | data Lake | data Warehouse | data Lakehouse |
|----------------|-----------|----------------|----------------|
| **Datas soportados** | Todos (struct/semi/no-struct) | only structunetworkos | Todos |
| **Formato** | Parquet, CSV, JSON | Propietario (columnr) | Delta/Iceberg |
| **Schema** | Schema-on-read | Schema-on-write | Flexible (ambos) |
| **transactions ACID** | ❌ not | ✅ Yes | ✅ Yes |
| **Performance BI** | ⚠️ Slow | ✅ Fast | ✅ Fast |
| **Costo** | 💰 Bajo | 💰💰💰 Alto | 💰💰 Medio |
| **ML Support** | ✅ Excelente | ⚠️ Limitado | ✅ Excelente |
| **scalability** | ✅ Petabytes+ | ⚠️ Terabytes | ✅ Petabytes+ |
| **Governance** | ⚠️ Complejo | ✅ Robusto | ✅ Robusto |
| **Time Travel** | ❌ not | ⚠️ Limitado | ✅ Yes |

### 📦 Prerequisites

Before beginning this module, you must have completed:

- ✅ **Module 02**: Storage Basics (S3/MinIO, Parquet, partitioning)
- ⚠️ **Module 03**: SQL Foundations (queries, joins, window functions) - Recommended
- ⚠️ **Module 04**: Python for data (pandas, testing, pIPelines) - Recommended

**Conocimientos necesarios**:

- Basic Linux/Bash Commands
- Conceptos of databases relacionales
- Python intermedio (funciones, classs, manejo of errores)
- Basic PySpark (we will learn in the module)

**Software requerido**:

- Docker and Docker Compose
- Python 3.8+
- 8GB RAM minimum (16GB recommended)
- 10GB espacio in disk

### 📂 Module Structure

```text
module-05-data-lakehouse/
├── README.md                          # this archivo
├── requirements.txt                   # Dependencias Python
├── STATUS.md                          # Tracking of progreso
├── .gitignore                         # Archivos ignorados
│
├── theory/                            # Material teórico
│   ├── 01-concepts.md                 # Conceptos fundamentales
│   ├── 02-architecture.md             # Arquitectura and patrones
│   └── 03-resources.md                # Resources adicionales
│
├── infrastructure/                    # Infrastructure Docker
│   ├── docker-compose.yml             # Servicios: Spark, MinIO, Jupyter
│   ├── spark/                         # Configuration Spark
│   ├── minio/                         # Configuration MinIO (S3)
│   └── init-scrIPts/                  # ScrIPts of inicialización
│
├── data/                              # Datasets
│   ├── raw/                           # Datas crudos (Bronze layer)
│   ├── schemas/                       # Esquemas JSON
│   └── scrIPts/                       # ScrIPts generación of datas
│
├── exercises/                         # 6 exercises prácticos
│   ├── 01-delta-basics/               # ⭐ Fundamentos Delta Lake
│   ├── 02-medallion-architecture/     # ⭐⭐⭐ Implementar Bronze/Silver/Gold
│   ├── 03-time-travel/                # ⭐⭐⭐ Time Travel and versionado
│   ├── 04-schema-evolution/           # ⭐⭐⭐⭐ Evolución of esquemas
│   ├── 05-optimization/               # ⭐⭐⭐⭐ Optimización and tuning
│   └── 06-iceberg-comparison/         # ⭐⭐⭐⭐⭐ Delta vs Iceberg
│
├── validation/                        # Tests automáticos
│   ├── conftest.py                    # Fixtures compartidos
│   ├── test_integration.py            # Tests of integración
│   ├── test_data_quality.py           # Tests of calidad of datas
│   └── test_module_completeness.py    # Tests of completitud
│
├── assets/                            # Resources of apoyo
│   ├── cheatsheets/                   # Guides rápidas
│   │   ├── delta-commands.md          # Commands Delta Lake
│   │   ├── medallion-patterns.md      # Patrones Medallion
│   │   ├── table-formats.md           # Comparación formatos
│   │   └── spark-optimization.md      # Optimización Spark
│   └── diagrams/                      # Diagramas arquitectura
│       ├── medallion-flow.md          # Flow Medallion
│       ├── delta-architecture.md      # Arquitectura Delta
│       └── partitioning.md            # Estrategias particionamiento
│
├── scrIPts/                           # Automatización
│   ├── setup.sh                       # Setup completo of the entorno
│   ├── validate.sh                    # Ejecutar todos los tests
│   ├── run_spark.sh                   # Spark shell interactivo
│   └── run_jupyter.sh                 # Jupyter Lab
│
└── docs/                              # Documentación adicional
    ├── troubleshooting-spark.md       # Solution of problems
    └── lakehouse-guide.md             # Guide of mejores prácticas
```text

### 🚀 Quick Start

#### 1. Setup of the Entorno

```bash
# Clonar the repository (if aún not lo have hecho)
cd training-cloud-data/modules/module-05-data-lakehouse

# Instalar dependencias
./scrIPts/setup.sh

# Levantar infrastructure Docker
docker-compose up -d

# Verificar que everything is corriendo
docker-compose ps
```text

#### 2. Explore Theoretical Material

```bash
# Leer conceptos fundamentales
cat theory/01-concepts.md

# Estudiar arquitectura Medallion
cat theory/02-architecture.md
```

#### 3. Ejecutar Exercises

```bash
# Activar entorno virtual
source venv/bin/activate

# Exercise 1: Delta Lake Basics
cd exercises/01-delta-basics
pytest test_solution.py -v

# Jupyter Lab for desarrolelo interactivo
./scrIPts/run_jupyter.sh
```text

#### 4. Validate the Complete Module

```bash
# Ejecutar todos los tests
./scrIPts/validate.sh --all

# with reporte of cobertura
./scrIPts/validate.sh --coverage
```text

### 📊 Exercises and Difficulty

| Exercise | Difficulty | Tiempo | Topics Key |
|-----------|------------|--------|-------------|
| **01-delta-basics** | ⭐ Basic | 1-2h | Create, Read, Write, Append, Overwrite |
| **02-medallion-architecture** | ⭐⭐⭐ Intermedio | 3-4h | Bronze→Silver→Gold, data Quality, Transformations |
| **03-time-travel** | ⭐⭐⭐ Intermedio | 2-3h | Versioning, Rolelback, Audit Trails |
| **04-schema-evolution** | ⭐⭐⭐⭐ Avanzado | 2-3h | Add/Drop Columns, Type Changes, Compatibility |
| **05-optimization** | ⭐⭐⭐⭐ Avanzado | 3-4h | Partitioning, Z-ordering, Compaction, Vacuum |
| **06-iceberg-comparison** | ⭐⭐⭐⭐⭐ Experto | 4-5h | Delta vs Iceberg, Migration, Trade-offs |

**Tiempo total estimado**: 15-21 horas

### 🎓 Learning Path

```text
1. Theory (3-4h)
   └─ Concepts → Architecture → Resources

2. Infrastructure (1-2h)
   └─ Docker Setup → Spark Config → MinIO S3

3. Hands-on Exercises (12-15h)
   └─ Delta Basics → Medallion → Time Travel → Evolution → Optimization → Iceberg

4. Project (Optional, 4-6h)
   └─ End-to-End Lakehouse PIPeline
```

### 📚 Additional Resources

- 📖 [Delta Lake Documentation](HTTPs://docs.delta.io/)
- 📖 [Apache Iceberg Documentation](HTTPs://iceberg.apache.org/)
- 📖 [Databricks Lakehouse Whitepaper](HTTPs://www.databricks.com/research/lakehouse-to-new-generation-of-open-platforms)
- 📖 [PySpark Documentation](HTTPs://spark.apache.org/docs/latest/api/python/)
- 🎥 [Medallion Architecture Explained](HTTPs://www.databricks.com/glossary/medallion-architecture)
- 📝 [Delta Lake vs Apache Iceberg Comparison](HTTPs://delta.io/blog/delta-lake-vs-iceberg/)

### 🆘 Troubleshooting

If you encounter problems during the module:

1. **query documentation**: [docs/troubleshooting-spark.md](docs/troubleshooting-spark.md)
2. **Revisa los logs**: `docker-compose logs spark-master`
3. **Verifica la infrastructure**: `docker-compose ps` and `docker-compose logs`
4. **Run the diagnostic tests**:`./scrIPts/validate.sh --fast`

### 🤝 Contribuciones

if encuentras errores or you have suggestions of improvement, by favor:

1. Abre un issue in the repository
2. Provide specific details (error, context, steps to reproduce)
3. Incluye logs relevantes if is posible

### 📝 Notes Importantes

- ⚠️ **resources of hardware**: Algunos exercises requieren procesamiento intensivo
- 💾 **storage**: The datasets will generate ~2GB of data
- 🐳 **Docker**: Make sure you have Docker running before you start
- 🔒 **Permissions**: ScrIPts need execution permissions (`chmod +x scrIPts/*.sh`)

### 🎯 Next Steps

Once you complete this module, you will be prepanetwork to:

- **Module 07**: Batch Processing with Apache Spark (processes the lakehouses)
- **Module 14**: data Governance & Security (governance in lakehouses)
- **Checkpoint 01**: Proyecto integrador Tier 2

---

## 🚀 Let's get started

El data Lakehouse representa el futuro of the storage and procesamiento of datas. Combina la flexibilidad of los data Lakes with la reliability of los data Warehouses, permitiendo workloads of BI and ML sobre la misma plataforma.

**Ready to build your first Lakehouse?**

Comienza leyendo [theory/01-concepts.md](theory/01-concepts.md) and luego ejecuta `./scrIPts/setup.sh` for configurar el entorno.

---

**Last update**: February 2026
**Module version**: 1.0.0
**Estado**: in desarrolelo 🚧
