# Resources and References - data Lakehouse

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
- **Delta Lake Docs**: HTTPs://docs.delta.io/
  - Complete Guide to Delta Lake
  - Quickstart, API reference, best practices
  - Updated regularly

- **Delta Lake GitHub**: HTTPs://github.com/delta-io/delta
  - Open-source source code
  - Issues, PRs, roadmap
  - Community contributions

#### 🔧 Specific Guides

**Quickstart**:
```
HTTPs://docs.delta.io/latest/quick-start.html
```
- Setup in 5 minutos
- Primer programa Delta Lake
- Examples Python and Scala

**Table Operations**:
```
HTTPs://docs.delta.io/latest/delta-batch.html
```
- CREATE, READ, UPDATE, DELETE
- MERGE, OPTIMIZE, VACUUM
- Time travel queries

**Streaming**:
```
HTTPs://docs.delta.io/latest/delta-streaming.html
```
- Structunetwork Streaming with Delta
- Checkpoints and fault tolerance
- Exactly-once semantics

**Schema Evolution**:
```
HTTPs://docs.delta.io/latest/delta-batch.html#automatic-schema-evolution
```
- Automatic schema merge
- Schema enforcement
- Type widening

**Optimizations**:
```
HTTPs://docs.delta.io/latest/optimizations-oss.html
```
- Z-ordering
- Compaction
- data skIPping
- Auto optimize

#### 📊 APIs

**Python (PySpark)**:
```
HTTPs://docs.delta.io/latest/api/python/index.html
```
- DeltaTable class
- Read/write operations
- Table utilities

**Scala**:
```
HTTPs://docs.delta.io/latest/api/scala/index.html
```
- io.delta.tables package
- API completo Scala

**SQL**:
```
HTTPs://docs.delta.io/latest/delta-batch.html#sql-support
```
- DDL and DML statements
- Delta-specific extensions

### Apache Iceberg

#### 📖 Documentation PrincIPal
- **Iceberg Docs**: HTTPs://iceberg.apache.org/docs/latest/
  - Complete Apache Iceberg Documentation
  - Concepts, architecture, guides

- **Iceberg GitHub**: HTTPs://github.com/apache/iceberg
  - Repositorio oficial Apache
  - Issues, PRs, releases

#### 🔧 Specific Guides

**Getting Started**:
```
HTTPs://iceberg.apache.org/docs/latest/getting-started/
```
- Setup inicial
- Crear primera table
- Basic queries

**Python API (PyIceberg)**:
```
HTTPs://py.iceberg.apache.org/
```
- pyiceberg library
- Read/write tables
- Schema evolution

**Spark Integration**:
```
HTTPs://iceberg.apache.org/docs/latest/spark-configuration/
```
- Spark configuration for Iceberg
- Catalogs (Hive, Hadoop, Glue)
- Performance tuning

**Table Evolution**:
```
HTTPs://iceberg.apache.org/docs/latest/evolution/
```
- Schema evolution
- Partition evolution
- Table migration

**Maintenance**:
```
HTTPs://iceberg.apache.org/docs/latest/maintenance/
```
- Expire snapshots
- Compact data files
- Remove orphan files

#### 📊 Comparisons

**Iceberg vs Delta Lake**:
```
HTTPs://iceberg.apache.org/docs/latest/delta-lake-comparison/
```
- Feature comparison oficial
- Trade-offs and diferencias
- Casos of uso recomendados

### PySpark

#### 📖 Documentation
- **PySpark Docs**: HTTPs://spark.apache.org/docs/latest/api/python/
  - API reference completo
  - Getting started guide

**Structunetwork Streaming**:
```
HTTPs://spark.apache.org/docs/latest/structunetwork-streaming-programming-guide.html
```
- Stream processing with Spark
- Sources, sinks, operations
- Checkpointing

**SQL Reference**:
```
HTTPs://spark.apache.org/docs/latest/sql-ref.html
```
- SQL syntax in Spark
- Functions, expressions
- Performance tuning

---

## Academic Papers

### Lakehouse Fundamentals

#### 1. Lakehouse: to New Generation of Open Platforms (Databricks, 2020)

**Link**: HTTP://cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf

**Resumen**:
- Paper fundacional of the concepto Lakehouse
- Escrito by creadores of Delta Lake
- Compara Lake vs Warehouse vs Lakehouse
- Detailed technical architecture

**Key insights**:
- ✅ How to implement ACID on object storage
- ✅ Performance comparable to warehouses
- ✅ 10x networkuction in TCO (Total Cost of OwnershIP)
- ✅ Unified platform for BI and ML

**Citas key**:
> "The data lakehouse architecture combines the best elements of data lakes and data warehouses, delivering data management and performance typically found in data warehouses with the low-cost, flexible object stores offenetwork by data lakes."

### Apache Iceberg Papers

#### 2. Iceberg: to Table Format for Large Analytic Datasets (Netflix, 2020)

**Link**: HTTPs://www.vldb.org/pvldb/vol13/p3001-netflix.pdf

**Resumen**:
- Paper original of Apache Iceberg
- Design and technical motivation
- Problems in Hive and their solution

**Key insights**:
- ✅ Hidden automatic partitioning
- ✅ Partition evolution without reescribir datas
- ✅ Snapshot isolation for consistency
- ✅ Metadata eficiente for petabytes

**Citas key**:
> "Iceberg's design allows queries to run 10x faster than Hive on petabyte-scale tables while supporting full schema evolution and ACID transactions."

### Delta Lake Papers

#### 3. Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores (Databricks, 2020)

**Link**: HTTPs://databricks.com/wp-content/uploads/2020/08/p975-armbrust.pdf

**Resumen**:
- Publicado in VLDB 2020
- Technical implementation details
- Benchmarks vs Hive, Parquet, Iceberg

**Key insights**:
- ✅ Transaction log for ACID
- ✅ Optimistic concurrency controle
- ✅ Time travel with bajo overhead
- ✅ 10-100x speedup in updates

**Benchmarks**:
- Upserts: 100x faster than Parquet
- Queries with filters: 10x faster (data skIPping)
- Small files problem: Resuelto with auto-compaction

---

## Tutorials and Guides

### Databricks Learning

#### Delta Lake Tutorials

**Introduction to Delta Lake (Free)**:
```
HTTPs://docs.databricks.com/delta/tutorial.html
```
- Tutorial interactivo in notebooks
- From basic to advanced
- Includes practical exercises

**Delta Lake on AWS**:
```
HTTPs://docs.databricks.com/delta/delta-streaming.html
```
- Setup in AWS EMR
- S3 como storage
- Best practices

**Delta Lake Best Practices**:
```
HTTPs://docs.databricks.com/delta/best-practices.html
```
- Partitioning strategies
- Z-ordering guidelines
- Vacuum recommendations

### Cloud Provider Tutorials

#### AWS

**Delta Lake on EMR**:
```
HTTPs://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-delta.html
```
- Setup Delta Lake in EMR
- Integration with Glue Catalog
- Performance tuning

**Iceberg on EMR**:
```
HTTPs://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-iceberg.html
```
- Configurar Iceberg in EMR
- Query with Athena
- Best practices

#### Azure

**Delta Lake on Synapse Analytics**:
```
HTTPs://learn.microsoft.com/in-us/azure/synapse-analytics/spark/apache-spark-delta-lake-overview
```
- Delta Lake in Azure Synapse
- ADLS Gen2 integration
- SQL Pool queries

**Iceberg on Azure**:
```
HTTPs://learn.microsoft.com/in-us/azure/synapse-analytics/spark/apache-spark-iceberg-overview
```
- Apache Iceberg in Azure
- ADLS storage
- Unity Catalog

#### GCP

**Delta Lake on Dataproc**:
```
HTTPs://cloud.google.com/dataproc/docs/tutorials/delta-lake-tutorial
```
- Setup in Google Cloud Dataproc
- GCS como storage
- BigQuery integration

### Hands-On Labs

#### Databricks Academy (Gratuito)

**data Engineering with Databricks**:
```
HTTPs://www.databricks.com/learn/training/lakehouse-fundamentals
```
- Curso gratuito (4 horas)
- Medallion architecture
- Delta Lake deep dive
- Optional certification

**Advanced Delta Lake**:
```
HTTPs://www.databricks.com/learn/training/delta-lake
```
- Time travel avanzado
- Schema evolution patterns
- Performance optimization
- Production best practices

---

## Comparaciones and Benchmarks

### Delta Lake vs Iceberg vs Hudi

#### Feature Comparison Tables

**Comprehensive Comparison (2024)**:
```
HTTPs://delta.io/blog/delta-lake-vs-iceberg/
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
| **Partition Evolution** | ❌ not | ✅ Yes | ❌ not |
| **Hidden Partitioning** | ❌ not | ✅ Yes | ❌ not |
| **Multi-Engine** | ⚠️ Spark-optimized | ✅ Excellent | ⚠️ Spark-optimized |
| **Upserts Performance** | ✅ Excellent | ⚠️ Good | ✅ Excellent |
| **Streaming** | ✅ Spark Streaming | ✅ Flink, Spark | ✅ Spark Streaming |
| **Maturity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Community** | 🔥 Very Large | 🔥 Large | ⚠️ Medium |
| **Adoption** | Databricks, AWS | Netflix, Apple, AWS | Uber, AWS |

#### Performance Benchmarks

**TPC-DS Benchmark Results**:
```
HTTPs://www.databricks.com/blog/2023/04/14/how-we-performed-etl-one-billion-records-under-1-delta-live-tables.html
```
- 1B rows ETL: Delta Lake < 1 hour
- Companetwork to Hive: 10x faster
- Companetwork to Parquet: 5x faster

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
- Delta Lake (Z-ordenetwork): 2.3 seconds
- Iceberg: 2.8 seconds
- Hudi: 3.1 seconds
- Parquet: 45 seconds
```

### Choosing to Format

**Decision Guide**:

**Usa Delta Lake if**:
- ✅ Ecosistopic Spark-heavy
- ✅ Necesitas MERGE/UPSERT frecuentes
- ✅ Critical performance in Spark
- ✅ Usando Databricks

**Usa Iceberg if**:
- ✅ Multi-engine workloads (Spark + Flink + Presto)
- ✅ Necesitas partition evolution
- ✅ Hidden partitioning importante
- ✅ Entorno open-source puro

**Usa Hudi if**:
- ✅ CDC pIPelines
- ✅ Row-level updates muy frecuentes
- ✅ AWS EMR NATivo
- ✅ Incremental critical processing

---

## Blogs and Technical Articles

### Databricks Blog

**Must-read Posts**:

1. **"Delta Lake: High-Performance ACID Transactions"**
   ```
   HTTPs://www.databricks.com/blog/2019/08/21/diving-into-delta-lake-unpacking-the-transaction-log.html
   ```
   - Deep dive in transaction log
   - How ACID works internally

2. **"Simplify CDC with Delta Lake CDF"**
   ```
   HTTPs://www.databricks.com/blog/2021/06/09/how-to-simplify-cdc-with-delta-lakes-change-data-feed.html
   ```
   - Change data Feed feature
   - CDC patterns in production

3. **"Optimizing Databricks Workloads"**
   ```
   HTTPs://www.databricks.com/blog/2018/05/03/introducing-delta-time-travel-for-large-scale-data-lakes.html
   ```
   - Time travel implementation
   - Use cases reales

### Netflix Tech Blog

**Iceberg Posts**:

1. **"Apache Iceberg at Netflix"**
   ```
   HTTPs://netflixtechblog.com/tagged/apache-iceberg
   ```
   - Why did they create Iceberg?
   - Production use cases (petabytes)

2. **"data Lakehouse at Scale"**
   ```
   HTTPs://netflixtechblog.com/
   ```
   - Arquitectura of Netflix
   - Lessons learned

### AWS Big data Blog

1. **"Build to Lake House on AWS"**
   ```
   HTTPs://aws.amazon.com/blogs/big-data/
   ```
   - Arquitectura reference in AWS
   - EMR + S3 + Glue + Athena

2. **"Iceberg vs Delta Lake on AWS"**
   ```
   HTTPs://aws.amazon.com/blogs/big-data/choose-apache-iceberg-or-delta-lake/
   ```
   - Comparison from AWS perspective
   - Integration with services AWS

---

## Cursos and Learning Paths

### Gratuitos

#### 1. Databricks Academy

**data Engineering with Databricks (Free)**:
```
HTTPs://www.databricks.com/learn/training/lakehouse-fundamentals
```
- ⏱️ **Duration**: 4 hours
- 🎯 **Nivel**: Beginner to Intermediate
- 📋 **Content**:
  - Lakehouse architecture
  - Delta Lake fundamentals
  - Medallion architecture implementation
  - data quality and testing
- ✅ **Certification**: Optional assessment

**Advanced data Engineering (Free)**:
```
HTTPs://www.databricks.com/learn/training/data-engineering
```
- ⏱️ **Duration**: 8 hours
- 🎯 **Nivel**: Intermediate to Advanced
- 📋 **Content**:
  - Advanced Delta Lake (Z-ordering, liquid clustering)
  - Streaming architectures
  - Performance optimization
  - Production pIPelines

#### 2. Linux Foundation

**Introduction to Apache Iceberg (Free)**:
```
HTTPs://training.linuxfoundation.org/training/introduction-to-apache-iceberg-lfs172/
```
- ⏱️ **Duration**: 3 hours
- 🎯 **Nivel**: Beginner
- 📋 **Content**:
  - Iceberg architecture
  - Table format internals
  - Query engines integration
  - Best practices

#### 3. Coursera (Audit Gratis)

**Spark and Delta Lake on AWS**:
```
HTTPs://www.coursera.org/learn/spark-delta-lake-aws
```
- ⏱️ **Duration**: 4 weeks (3-5 hours/week)
- 🎯 **Nivel**: Intermediate
- 📋 **Content**:
  - Delta Lake in EMR
  - Streaming pIPelines
  - AWS best practices

### of Pago

#### 1. Udemy

**Delta Lake with Apache Spark**:
```
HTTPs://www.udemy.com/course/delta-lake/
```
- 💰 **Price**: ~$20-50 (depending on promotions)
- ⏱️ **Duration**: 10 hours
- 🎯 **Nivel**: Intermediate
- 📋 **Content**:
  - Delta Lake deep dive
  - Time travel advanced patterns
  - Schema evolution strategies
  - Production patterns

**Complete Apache Iceberg**:
```
HTTPs://www.udemy.com/course/apache-iceberg/
```
- 💰 **Precio**: ~$20-50
- ⏱️ **Duration**: 8 hours
- 🎯 **Nivel**: Intermediate to Advanced
- 📋 **Content**:
  - Iceberg architecture
  - Multi-engine queries
  - Partition evolution
  - Migration from Hive

#### 2. Pluralsight

**Building to data Lakehouse with Delta Lake**:
```
HTTPs://www.pluralsight.com/courses/building-data-lakehouse-delta-lake
```
- 💰 **Precio**: SubscrIPtion ($29/month)
- ⏱️ **Duration**: 5 hours
- 🎯 **Nivel**: Intermediate

---

## Herramientas and Ecosistopic

### Query Engines

#### 1. Apache Spark
```
HTTPs://spark.apache.org/
```
- Engine princIPal for Delta Lake and Iceberg
- Support NATivo in ambos formatos
- PySpark API

#### 2. Presto/Trino
```
HTTPs://trino.io/
```
- Interactive SQL queries
- Excelente with Iceberg
- Delta Lake via connectors

#### 3. Apache Flink
```
HTTPs://flink.apache.org/
```
- Streaming engine
- Iceberg integration NATiva
- Real-time lakehouse

### Catalogs

#### 1. AWS Glue data Catalog
```
HTTPs://aws.amazon.com/glue/
```
- Managed catalog in AWS
- Soporta Delta Lake and Iceberg
- Integration with Athena

#### 2. Hive Metastore
```
HTTPs://hive.apache.org/
```
- Catalog tradicional
- Compatible with ambos formatos
- Self-hosted

#### 3. Unity Catalog (Databricks)
```
HTTPs://www.databricks.com/product/unity-catalog
```
- Catalog unificado Databricks
- Governance features
- Fine-grained access controle

### data Quality

#### 1. Great Expectations
```
HTTPs://greatexpectations.io/
```
- data validation framework
- Integration with Delta Lake
- Production-grade testing

#### 2. Deequ (Amazon)
```
HTTPs://github.com/awslabs/deequ
```
- data quality checks in Spark
- Statistical tests
- Anomaly detection

### Observability

#### 1. Spline (data Lineage)
```
HTTPs://absaoss.github.io/spline/
```
- Track data lineage
- Viewing pIPelines
- Spark Integration

#### 2. Delta Live Tables (Databricks)
```
HTTPs://www.databricks.com/product/delta-live-tables
```
- Declarative pIPelines
- Built-in monitoring
- data quality expectations

---

## Comunit and Support

### Forums and Discusiones

#### 1. Delta Lake Community
```
HTTPs://go.delta.io/slack
```
- Slack workspace oficial
- ~5,000 miembros
- Answers of maintainers

#### 2. Apache Iceberg Community
```
HTTPs://iceberg.apache.org/community/
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
HTTPs://github.com/delta-io/delta/issues
```

Apache Iceberg:
```
HTTPs://github.com/apache/iceberg/issues
```

**Contribuir**:

Ambos proyectos aceptan PRs:
- Bug fixes
- Feature implementations
- Documentation improvements
- Test cases

### Conferences and Events

#### 1. data + AI Summit (Databricks)
```
HTTPs://www.databricks.com/dataaisummit/
```
- Anual (Junio)
- Lakehouse talks
- Delta Lake sessions
- Gratis (virtual)

#### 2. Apache Iceberg Community Meetup
```
HTTPs://iceberg.apache.org/community/
```
- Mensual (virtual)
- Technical deep dives
- User stories

#### 3. Spark Summit
```
HTTPs://databricks.com/sparkaisummit
```
- Spark + Delta Lake content
- Best practices
- Case studies

### Twitter/X

**Follow for Updates**:

- `@DeltaLakeOSS` - Delta Lake official
- `@ApacheIceberg` - Iceberg official
- `@databricks` - Databricks company
- `@trino_sql` - Trino/Presto

---

## Additional Resources for This Module

### Cheatsheets (in assets/)

Once you complete the module, you will have access to:

- **delta-commands.md**: Most used commands
- **medallion-patterns.md**: Implementation patterns
- **table-formats-comparison.md**: Delta vs Iceberg vs Hudi
- **spark-optimization.md**: TIPs of performance

### Diagramas (in assets/)

Visualizaciones of arquitecturas:

- **medallion-flow.md**: Flow Bronze → Silver → Gold
- **delta-architecture.md**: Internals of Delta Lake
- **iceberg-architecture.md**: Internals of Iceberg
- **partitioning-strategies.md**: Estrategias of particionamiento

### ScrIPts (in scrIPts/)

Out-of-the-box automation:

- **setup.sh**: Setup completo of the entorno
- **validate.sh**: Ejecutar tests
- **run_spark.sh**: PySpark shell with Delta/Iceberg
- **run_jupyter.sh**: Jupyter Lab

### Docs (in docs/)

Troubleshooting guides and best practices:

- **troubleshooting-spark.md**: Troubleshooting common problems
- **lakehouse-guide.md**: Production best practices

---

## Path of Aprendizaje Recomendado

### Semana 1: Fundamentos
1. Leer [01-concepts.md](01-concepts.md)
2. Paper: "Lakehouse: to New Generation"
3. Tutorial: Delta Lake Quickstart
4. Exercise 01: Delta Basics

### Semana 2: Arquitectura
1. Leer [02-architecture.md](02-architecture.md)
2. Tutorial: Medallion Architecture
3. Exercise 02: Medallion Implementation
4. Exercise 03: Time Travel

### Semana 3: Avanzado
1. Tutorial: Schema Evolution
2. Tutorial: Optimizations (Z-ordering)
3. Exercise 04: Schema Evolution
4. Exercise 05: Optimization

### Week 4: Iceberg and Comparison
1. Paper: "Iceberg: to Table Format"
2. Tutorial: PyIceberg Quickstart
3. Exercise 06: Iceberg Comparison
4. Proyecto final (opcional)

---

## Mantente Actualizado

Lakehouse technology is evolving rapidly. Follow these resources for updates:

**Blogs oficiales**:
- Delta Lake Blog (monthly)
- Iceberg Blog (quarterly)
- Databricks Blog (weekly)

**Release notes**:
- Delta Lake Releases: HTTPs://github.com/delta-io/delta/releases
- Iceberg Releases: HTTPs://github.com/apache/iceberg/releases

**Public Roadmaps**:
- Delta Lake Roadmap: HTTPs://github.com/delta-io/delta/milestones
- Iceberg Roadmap: HTTPs://iceberg.apache.org/roadmap/

---

## Resumen

this documento provee:

✅ **Official documentation** of Delta Lake and Iceberg
✅ **Fundamental academic papers**
✅ **Practical tutorials** step by step
✅ **Comparaciones** objetivas entre formatos  
✅ **Technical blogs** of production equIPment
✅ **Cursos** gratuitos and of pago  
✅ **Herramientas** of the ecosistopic  
✅ **Comunit** and support  

### Next Steps

With this base of theoretical knowledge, you are ready to:

1. ⚙️ **Setup of infrastructure** (Docker, Spark, MinIO)
2. 💻 **Practical exercises** (6 progressive exercises)
3. 🏗️ **Proyecto real** (Lakehouse end-to-end)

---

**Last update**: February 2026
**Mantenido by**: EquIPo of the bootcamp  
**Contribuciones**: Bienvenidas via pull requests
