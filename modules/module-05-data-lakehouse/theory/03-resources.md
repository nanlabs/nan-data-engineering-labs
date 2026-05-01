# Resources and References - Data Lakehouse

## 📚 Table of Contents

1. [Official Documentation](#official-documentation)
2. [Academic Papers](#academic-papers)
3. [Tutorials and Guides](#tutorials-and-guides)
4. [Comparisons and Benchmarks](#comparisons-and-benchmarks)
5. [Blogs and Technical Articles](#blogs-and-technical-articles)
6. [Courses and Learning Paths](#courses-and-learning-paths)
7. [Tools and Ecosystem](#tools-and-ecosystem)
8. [Community and Support](#community-and-support)

---

## Official Documentation

### Delta Lake

#### 📖 Main Documentation
- **Delta Lake Docs**: https://docs.delta.io/
  - Complete Guide to Delta Lake
  - Quickstart, API reference, best practices
  - Updated regularly

- **Delta Lake GitHub**: https://github.com/delta-io/delta
  - Open-source source code
  - Issues, PRs, roadmap
  - Community contributions

#### 🔧 Specific Guides

**Quickstart**:
```
https://docs.delta.io/latest/quick-start.html
```
- Setup en 5 minutos
- Primer programa Delta Lake
- Ejemplos Python y Scala

**Table Operations**:
```
https://docs.delta.io/latest/delta-batch.html
```
- CREATE, READ, UPDATE, DELETE
- MERGE, OPTIMIZE, VACUUM
- Time travel queries

**Streaming**:
```
https://docs.delta.io/latest/delta-streaming.html
```
- Structured Streaming con Delta
- Checkpoints y fault tolerance
- Exactly-once semantics

**Schema Evolution**:
```
https://docs.delta.io/latest/delta-batch.html#automatic-schema-evolution
```
- Automatic schema merge
- Schema enforcement
- Type widening

**Optimizations**:
```
https://docs.delta.io/latest/optimizations-oss.html
```
- Z-ordering
- Compaction
- Data skipping
- Auto optimize

#### 📊 APIs

**Python (PySpark)**:
```
https://docs.delta.io/latest/api/python/index.html
```
- DeltaTable class
- Read/write operations
- Table utilities

**Scala**:
```
https://docs.delta.io/latest/api/scala/index.html
```
- io.delta.tables package
- API completo Scala

**SQL**:
```
https://docs.delta.io/latest/delta-batch.html#sql-support
```
- DDL y DML statements
- Delta-specific extensions

### Apache Iceberg

#### 📖 Documentation Principal
- **Iceberg Docs**: https://iceberg.apache.org/docs/latest/
  - Complete Apache Iceberg Documentation
  - Concepts, architecture, guides

- **Iceberg GitHub**: https://github.com/apache/iceberg
  - Repositorio oficial Apache
  - Issues, PRs, releases

#### 🔧 Specific Guides

**Getting Started**:
```
https://iceberg.apache.org/docs/latest/getting-started/
```
- Setup inicial
- Crear primera table
- Basic queries

**Python API (PyIceberg)**:
```
https://py.iceberg.apache.org/
```
- pyiceberg library
- Read/write tables
- Schema evolution

**Spark Integration**:
```
https://iceberg.apache.org/docs/latest/spark-configuration/
```
- Spark configuration for Iceberg
- Catalogs (Hive, Hadoop, Glue)
- Performance tuning

**Table Evolution**:
```
https://iceberg.apache.org/docs/latest/evolution/
```
- Schema evolution
- Partition evolution
- Table migration

**Maintenance**:
```
https://iceberg.apache.org/docs/latest/maintenance/
```
- Expire snapshots
- Compact data files
- Remove orphan files

#### 📊 Comparisons

**Iceberg vs Delta Lake**:
```
https://iceberg.apache.org/docs/latest/delta-lake-comparison/
```
- Feature comparison oficial
- Trade-offs y diferencias
- Casos de uso recomendados

### PySpark

#### 📖 Documentation
- **PySpark Docs**: https://spark.apache.org/docs/latest/api/python/
  - API reference completo
  - Getting started guide

**Structured Streaming**:
```
https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
```
- Stream processing con Spark
- Sources, sinks, operations
- Checkpointing

**SQL Reference**:
```
https://spark.apache.org/docs/latest/sql-ref.html
```
- SQL syntax en Spark
- Functions, expressions
- Performance tuning

---

## Academic Papers

### Lakehouse Fundamentals

#### 1. Lakehouse: A New Generation of Open Platforms (Databricks, 2020)

**Link**: http://cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf

**Resumen**:
- Paper fundacional del concepto Lakehouse
- Escrito por creadores de Delta Lake
- Compara Lake vs Warehouse vs Lakehouse
- Detailed technical architecture

**Key insights**:
- ✅ How to implement ACID on object storage
- ✅ Performance comparable a warehouses
- ✅ 10x reduction in TCO (Total Cost of Ownership)
- ✅ Unified platform para BI y ML

**Citas clave**:
> "The data lakehouse architecture combines the best elements of data lakes and data warehouses, delivering data management and performance typically found in data warehouses with the low-cost, flexible object stores offered by data lakes."

### Apache Iceberg Papers

#### 2. Iceberg: A Table Format for Large Analytic Datasets (Netflix, 2020)

**Link**: https://www.vldb.org/pvldb/vol13/p3001-netflix.pdf

**Resumen**:
- Paper original de Apache Iceberg
- Design and technical motivation
- Problems in Hive and their solution

**Key insights**:
- ✅ Hidden automatic partitioning
- ✅ Partition evolution sin reescribir datos
- ✅ Snapshot isolation para consistencia
- ✅ Metadata eficiente para petabytes

**Citas clave**:
> "Iceberg's design allows queries to run 10x faster than Hive on petabyte-scale tables while supporting full schema evolution and ACID transactions."

### Delta Lake Papers

#### 3. Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores (Databricks, 2020)

**Link**: https://databricks.com/wp-content/uploads/2020/08/p975-armbrust.pdf

**Resumen**:
- Publicado en VLDB 2020
- Technical implementation details
- Benchmarks vs Hive, Parquet, Iceberg

**Key insights**:
- ✅ Transaction log para ACID
- ✅ Optimistic concurrency control
- ✅ Time travel con bajo overhead
- ✅ 10-100x speedup en updates

**Benchmarks**:
- Upserts: 100x faster than Parquet
- Queries with filters: 10x faster (data skipping)
- Small files problem: Resuelto con auto-compaction

---

## Tutorials and Guides

### Databricks Learning

#### Delta Lake Tutorials

**Introduction to Delta Lake (Free)**:
```
https://docs.databricks.com/delta/tutorial.html
```
- Tutorial interactivo en notebooks
- From basic to advanced
- Includes practical exercises

**Delta Lake on AWS**:
```
https://docs.databricks.com/delta/delta-streaming.html
```
- Setup en AWS EMR
- S3 como storage
- Best practices

**Delta Lake Best Practices**:
```
https://docs.databricks.com/delta/best-practices.html
```
- Partitioning strategies
- Z-ordering guidelines
- Vacuum recommendations

### Cloud Provider Tutorials

#### AWS

**Delta Lake on EMR**:
```
https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-delta.html
```
- Setup Delta Lake en EMR
- Integration with Glue Catalog
- Performance tuning

**Iceberg on EMR**:
```
https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-iceberg.html
```
- Configurar Iceberg en EMR
- Query con Athena
- Best practices

#### Azure

**Delta Lake on Synapse Analytics**:
```
https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-delta-lake-overview
```
- Delta Lake en Azure Synapse
- ADLS Gen2 integration
- SQL Pool queries

**Iceberg on Azure**:
```
https://learn.microsoft.com/en-us/azure/synapse-analytics/spark/apache-spark-iceberg-overview
```
- Apache Iceberg en Azure
- ADLS storage
- Unity Catalog

#### GCP

**Delta Lake on Dataproc**:
```
https://cloud.google.com/dataproc/docs/tutorials/delta-lake-tutorial
```
- Setup en Google Cloud Dataproc
- GCS como storage
- BigQuery integration

### Hands-On Labs

#### Databricks Academy (Gratuito)

**Data Engineering with Databricks**:
```
https://www.databricks.com/learn/training/lakehouse-fundamentals
```
- Curso gratuito (4 horas)
- Medallion architecture
- Delta Lake deep dive
- Optional certification

**Advanced Delta Lake**:
```
https://www.databricks.com/learn/training/delta-lake
```
- Time travel avanzado
- Schema evolution patterns
- Performance optimization
- Production best practices

---

## Comparaciones y Benchmarks

### Delta Lake vs Iceberg vs Hudi

#### Feature Comparison Tables

**Comprehensive Comparison (2024)**:
```
https://delta.io/blog/delta-lake-vs-iceberg/
```
- Feature-by-feature comparison
- Performance benchmarks
- Use case recommendations

**table resumen**:

| Feature | Delta Lake | Iceberg | Hudi |
|---------|-----------|---------|------|
| **ACID** | ✅ Full | ✅ Full | ✅ Full |
| **Time Travel** | ✅ Excellent | ✅ Excellent | ✅ Good |
| **Schema Evolution** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Partition Evolution** | ❌ No | ✅ Yes | ❌ No |
| **Hidden Partitioning** | ❌ No | ✅ Yes | ❌ No |
| **Multi-Engine** | ⚠️ Spark-optimized | ✅ Excellent | ⚠️ Spark-optimized |
| **Upserts Performance** | ✅ Excellent | ⚠️ Good | ✅ Excellent |
| **Streaming** | ✅ Spark Streaming | ✅ Flink, Spark | ✅ Spark Streaming |
| **Maturity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Community** | 🔥 Very Large | 🔥 Large | ⚠️ Medium |
| **Adoption** | Databricks, AWS | Netflix, Apple, AWS | Uber, AWS |

#### Performance Benchmarks

**TPC-DS Benchmark Results**:
```
https://www.databricks.com/blog/2023/04/14/how-we-performed-etl-one-billion-records-under-1-delta-live-tables.html
```
- 1B rows ETL: Delta Lake < 1 hour
- Compared to Hive: 10x faster
- Compared to Parquet: 5x faster

**Update Performance**:
```
Benchmark: 100M rows table, 10% updates
- Delta Lake: 45 seconds
- Iceberg: 62 seconds
- Hudi (MoR): 38 seconds
- Hudi (CoW): 90 seconds
- Parquet (overwrite): 15 minutes
```

**Query Performance** (with pruning):
```
Benchmark: 1B rows table, filter on high-cardinality column
- Delta Lake (Z-ordered): 2.3 seconds
- Iceberg: 2.8 seconds
- Hudi: 3.1 seconds
- Parquet: 45 seconds
```

### Choosing a Format

**Decision Guide**:

**Usa Delta Lake si**:
- ✅ Ecosistema Spark-heavy
- ✅ Necesitas MERGE/UPSERT frecuentes
- ✅ Critical performance in Spark
- ✅ Usando Databricks

**Usa Iceberg si**:
- ✅ Multi-engine workloads (Spark + Flink + Presto)
- ✅ Necesitas partition evolution
- ✅ Hidden partitioning importante
- ✅ Entorno open-source puro

**Usa Hudi si**:
- ✅ CDC pipelines
- ✅ Row-level updates muy frecuentes
- ✅ AWS EMR nativo
- ✅ Incremental critical processing

---

## Blogs and Technical Articles

### Databricks Blog

**Must-read Posts**:

1. **"Delta Lake: High-Performance ACID Transactions"**
   ```
   https://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html
   ```
   - Deep dive en transaction log
   - How ACID works internally

2. **"Simplify CDC with Delta Lake CDF"**
   ```
   https://www.databricks.com/blog/2021/06/09/how-to-simplify-cdc-with-delta-lakes-change-data-feed.html
   ```
   - Change Data Feed feature
   - CDC patterns in production

3. **"Optimizing Databricks Workloads"**
   ```
   https://www.databricks.com/blog/2018/05/03/introducing-delta-time-travel-for-large-scale-data-lakes.html
   ```
   - Time travel implementation
   - Use cases reales

### Netflix Tech Blog

**Iceberg Posts**:

1. **"Apache Iceberg at Netflix"**
   ```
   https://netflixtechblog.com/tagged/apache-iceberg
   ```
   - Why did they create Iceberg?
   - Production use cases (petabytes)

2. **"Data Lakehouse at Scale"**
   ```
   https://netflixtechblog.com/
   ```
   - Arquitectura de Netflix
   - Lessons learned

### AWS Big Data Blog

1. **"Build a Lake House on AWS"**
   ```
   https://aws.amazon.com/blogs/big-data/
   ```
   - Arquitectura reference en AWS
   - EMR + S3 + Glue + Athena

2. **"Iceberg vs Delta Lake on AWS"**
   ```
   https://aws.amazon.com/blogs/big-data/choose-apache-iceberg-or-delta-lake/
   ```
   - Comparison from AWS perspective
   - Integration con services AWS

---

## Cursos y Learning Paths

### Gratuitos

#### 1. Databricks Academy

**Data Engineering with Databricks (Free)**:
```
https://www.databricks.com/learn/training/lakehouse-fundamentals
```
- ⏱️ **Duration**: 4 hours
- 🎯 **Nivel**: Beginner to Intermediate
- 📋 **Contenido**:
  - Lakehouse architecture
  - Delta Lake fundamentals
  - Medallion architecture implementation
  - Data quality and testing
- ✅ **Certification**: Optional assessment

**Advanced Data Engineering (Free)**:
```
https://www.databricks.com/learn/training/data-engineering
```
- ⏱️ **Duration**: 8 hours
- 🎯 **Nivel**: Intermediate to Advanced
- 📋 **Contenido**:
  - Advanced Delta Lake (Z-ordering, liquid clustering)
  - Streaming architectures
  - Performance optimization
  - Production pipelines

#### 2. Linux Foundation

**Introduction to Apache Iceberg (Free)**:
```
https://training.linuxfoundation.org/training/introduction-to-apache-iceberg-lfs172/
```
- ⏱️ **Duration**: 3 hours
- 🎯 **Nivel**: Beginner
- 📋 **Contenido**:
  - Iceberg architecture
  - Table format internals
  - Query engines integration
  - Best practices

#### 3. Coursera (Audit Gratis)

**Spark and Delta Lake on AWS**:
```
https://www.coursera.org/learn/spark-delta-lake-aws
```
- ⏱️ **Duration**: 4 weeks (3-5 hours/week)
- 🎯 **Nivel**: Intermediate
- 📋 **Contenido**:
  - Delta Lake en EMR
  - Streaming pipelines
  - AWS best practices

### De Pago

#### 1. Udemy

**Delta Lake with Apache Spark**:
```
https://www.udemy.com/course/delta-lake/
```
- 💰 **Price**: ~$20-50 (depending on promotions)
- ⏱️ **Duration**: 10 hours
- 🎯 **Nivel**: Intermediate
- 📋 **Contenido**:
  - Delta Lake deep dive
  - Time travel advanced patterns
  - Schema evolution strategies
  - Production patterns

**Complete Apache Iceberg**:
```
https://www.udemy.com/course/apache-iceberg/
```
- 💰 **Precio**: ~$20-50
- ⏱️ **Duration**: 8 hours
- 🎯 **Nivel**: Intermediate to Advanced
- 📋 **Contenido**:
  - Iceberg architecture
  - Multi-engine queries
  - Partition evolution
  - Migration from Hive

#### 2. Pluralsight

**Building a Data Lakehouse with Delta Lake**:
```
https://www.pluralsight.com/courses/building-data-lakehouse-delta-lake
```
- 💰 **Precio**: Subscription ($29/month)
- ⏱️ **Duration**: 5 hours
- 🎯 **Nivel**: Intermediate

---

## Herramientas y Ecosistema

### Query Engines

#### 1. Apache Spark
```
https://spark.apache.org/
```
- Engine principal para Delta Lake y Iceberg
- Soporte nativo en ambos formatos
- PySpark API

#### 2. Presto/Trino
```
https://trino.io/
```
- Interactive SQL queries
- Excelente con Iceberg
- Delta Lake via connectors

#### 3. Apache Flink
```
https://flink.apache.org/
```
- Streaming engine
- Iceberg integration nativa
- Real-time lakehouse

### Catalogs

#### 1. AWS Glue Data Catalog
```
https://aws.amazon.com/glue/
```
- Managed catalog en AWS
- Soporta Delta Lake y Iceberg
- Integration with Athena

#### 2. Hive Metastore
```
https://hive.apache.org/
```
- Catalog tradicional
- Compatible con ambos formatos
- Self-hosted

#### 3. Unity Catalog (Databricks)
```
https://www.databricks.com/product/unity-catalog
```
- Catalog unificado Databricks
- Governance features
- Fine-grained access control

### Data Quality

#### 1. Great Expectations
```
https://greatexpectations.io/
```
- Data validation framework
- Integration with Delta Lake
- Production-grade testing

#### 2. Deequ (Amazon)
```
https://github.com/awslabs/deequ
```
- Data quality checks en Spark
- Statistical tests
- Anomaly detection

### Observability

#### 1. Spline (Data Lineage)
```
https://absaoss.github.io/spline/
```
- Track data lineage
- Viewing pipelines
- Spark Integration

#### 2. Delta Live Tables (Databricks)
```
https://www.databricks.com/product/delta-live-tables
```
- Declarative pipelines
- Built-in monitoring
- Data quality expectations

---

## Comunidad y Soporte

### Forums y Discusiones

#### 1. Delta Lake Community
```
https://go.delta.io/slack
```
- Slack workspace oficial
- ~5,000 miembros
- Respuestas de maintainers

#### 2. Apache Iceberg Community
```
https://iceberg.apache.org/community/
```
- Mailing lists
- Slack channel
- Monthly community calls

#### 3. Stack Overflow
```
Tags: [delta-lake], [apache-iceberg], [lakehouse]
```
- Technical questions
- Community-driven answers
- Searchable knowledge base

### GitHub

**Reportar Issues**:

Delta Lake:
```
https://github.com/delta-io/delta/issues
```

Apache Iceberg:
```
https://github.com/apache/iceberg/issues
```

**Contribuir**:

Ambos proyectos aceptan PRs:
- Bug fixes
- Feature implementations
- Documentation improvements
- Test cases

### Conferences y Events

#### 1. Data + AI Summit (Databricks)
```
https://www.databricks.com/dataaisummit/
```
- Anual (Junio)
- Lakehouse talks
- Delta Lake sessions
- Gratis (virtual)

#### 2. Apache Iceberg Community Meetup
```
https://iceberg.apache.org/community/
```
- Mensual (virtual)
- Technical deep dives
- User stories

#### 3. Spark Summit
```
https://databricks.com/sparkaisummit
```
- Spark + Delta Lake content
- Best practices
- Case studies

### Twitter/X

**Follow para Updates**:

- `@DeltaLakeOSS` - Delta Lake official
- `@ApacheIceberg` - Iceberg official
- `@databricks` - Databricks company
- `@trino_sql` - Trino/Presto

---

## Additional Resources for This Module

### Cheatsheets (en assets/)

Once you complete the module, you will have access to:

- **delta-commands.md**: Most used commands
- **medallion-patterns.md**: Implementation patterns
- **table-formats-comparison.md**: Delta vs Iceberg vs Hudi
- **spark-optimization.md**: Tips de performance

### Diagramas (en assets/)

Visualizaciones de arquitecturas:

- **medallion-flow.md**: Flujo Bronze → Silver → Gold
- **delta-architecture.md**: Internals de Delta Lake
- **iceberg-architecture.md**: Internals de Iceberg
- **partitioning-strategies.md**: Estrategias de particionamiento

### Scripts (en scripts/)

Out-of-the-box automation:

- **setup.sh**: Setup completo del entorno
- **validate.sh**: Ejecutar tests
- **run_spark.sh**: PySpark shell con Delta/Iceberg
- **run_jupyter.sh**: Jupyter Lab

### Docs (en docs/)

Troubleshooting guides and best practices:

- **troubleshooting-spark.md**: Troubleshooting common problems
- **lakehouse-guide.md**: Production best practices

---

## Path de Aprendizaje Recomendado

### Semana 1: Fundamentos
1. Leer [01-concepts.md](01-concepts.md)
2. Paper: "Lakehouse: A New Generation"
3. Tutorial: Delta Lake Quickstart
4. Ejercicio 01: Delta Basics

### Semana 2: Arquitectura
1. Leer [02-architecture.md](02-architecture.md)
2. Tutorial: Medallion Architecture
3. Ejercicio 02: Medallion Implementation
4. Ejercicio 03: Time Travel

### Semana 3: Avanzado
1. Tutorial: Schema Evolution
2. Tutorial: Optimizations (Z-ordering)
3. Ejercicio 04: Schema Evolution
4. Ejercicio 05: Optimization

### Week 4: Iceberg and Comparison
1. Paper: "Iceberg: A Table Format"
2. Tutorial: PyIceberg Quickstart
3. Ejercicio 06: Iceberg Comparison
4. Proyecto final (opcional)

---

## Mantente Actualizado

Lakehouse technology is evolving rapidly. Follow these resources for updates:

**Blogs oficiales**:
- Delta Lake Blog (monthly)
- Iceberg Blog (quarterly)
- Databricks Blog (weekly)

**Release notes**:
- Delta Lake Releases: https://github.com/delta-io/delta/releases
- Iceberg Releases: https://github.com/apache/iceberg/releases

**Public Roadmaps**:
- Delta Lake Roadmap: https://github.com/delta-io/delta/milestones
- Iceberg Roadmap: https://iceberg.apache.org/roadmap/

---

## Resumen

Este documento provee:

✅ **Official documentation** of Delta Lake and Iceberg
✅ **Fundamental academic papers**
✅ **Practical tutorials** step by step
✅ **Comparaciones** objetivas entre formatos  
✅ **Technical blogs** of production equipment
✅ **Cursos** gratuitos y de pago  
✅ **Herramientas** del ecosistema  
✅ **Comunidad** y soporte  

### Next Steps

With this base of theoretical knowledge, you are ready to:

1. ⚙️ **Setup de infraestructura** (Docker, Spark, MinIO)
2. 💻 **Practical exercises** (6 progressive exercises)
3. 🏗️ **Proyecto real** (Lakehouse end-to-end)

---

**Last update**: February 2026
**Mantenido por**: Equipo del bootcamp  
**Contribuciones**: Bienvenidas via pull requests
