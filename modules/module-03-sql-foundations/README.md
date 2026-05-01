# Module 03: SQL Fundamentals for Data Engineering

Master SQL fundamentals and advanced querying techniques essential for modern data engineering workflows.

## General Description

This module teaches SQL from a data engineering perspective, focusing on real-world scenarios you will encounter when working with data lakes, warehouses, and analytical workloads. You will learn to write efficient queries, optimize performance and take advantage of SQL through different engines (PostgreSQL, Athena, Spark SQL).

**Duration**: 12-15 hours
**Dificultad**: Principiante a Intermedio
**Prerequisites**: Basic understanding of databases and data structures

## Objetivos de Aprendizaje

Upon completion of this module, you will be able to:

1. **Write complex SQL queries** using SELECT, WHERE, JOIN, GROUP BY and aggregation functions
2. **Realizar operaciones multi-table** con joins INNER, LEFT, RIGHT, FULL y CROSS
3. **Use window functions** for analytical queries (ROW_NUMBER, RANK, LAG, LEAD, NTILE)
4. **Dominar Common Table Expressions (CTEs)** para querys legibles y mantenibles
5. **Optimize query performance** using EXPLAIN, indexes and query planning
6. **Handle data transformations** with CASE, COALESCE, type conversion and string functions
7. **Work with dates and timestamps** for time series analysis and partitioning
8. **Understand query execution plans** and how databases process SQL
9. **Apply SQL best practices** for data engineering workflows
10. **Use SQL across different engines** (PostgreSQL, Presto/Athena, Spark SQL)
11. **Debuggear y resolver problemas** de querys lentas y errores comunes de SQL
12. **Write efficient analytical queries** for data pipeline transformations


## Prerequisitos

### Conocimientos Requeridos
- Basic understanding of relational databases
- Familiaridad con tipos de datos (integers, strings, dates)
- Basic command line commands

### Software Requerido
- Python 3.9+
- Docker y Docker Compose
- Cliente PostgreSQL (psql)
- 2GB de espacio libre en disco

### Recomendado pero Opcional
- Basic understanding of data warehousing concepts
- Familiarity with any programming language
- Experience with data analysis tools

## Module Structure

```
module-03-sql-foundations/
├── theory/                      # Documentación conceptual
│   ├── concepts.md             # Fundamentos de SQL (20,000+ palabras)
│   ├── architecture.md         # Ejecución y optimización de consultas
│   └── resources.md            # Materiales de aprendizaje adicionales
├── exercises/                   # Práctica hands-on
│   ├── 01-basic-queries/       # SELECT, WHERE, ORDER BY
│   ├── 02-joins/               # Operaciones multi-tabla
│   ├── 03-aggregations/        # GROUP BY, funciones de agregación
│   ├── 04-window-functions/    # Consultas analíticas
│   ├── 05-ctes-subqueries/     # Composición de consultas complejas
│   └── 06-optimization/        # Ajuste de rendimiento
├── data/                        # Datasets de muestra
│   ├── schemas/                # Esquemas de base de datos
│   ├── seeds/                  # Datos de muestra
│   └── migrations/             # Scripts de evolución de esquema
├── infrastructure/              # Setup de desarrollo local
│   ├── docker-compose.yml      # Contenedor PostgreSQL
│   └── init.sql                # Inicialización de base de datos
├── validation/                  # Tests automatizados
│   └── test_*.py               # Validación de ejercicios
├── assets/                      # Recursos visuales
│   ├── diagrams/               # Diagramas de ejecución SQL
│   └── cheatsheets/            # Guías de referencia rápida
├── scripts/                     # Scripts de automatización
│   ├── setup.sh                # Configuración del entorno
│   └── validate.sh             # Ejecutar todas las validaciones
└── docs/                        # Documentación adicional
    ├── sql-guide.md            # Guía completa de SQL
    └── troubleshooting.md      # Problemas comunes y soluciones
```

## Comenzando

### 1. Clonar y Navegar
```bash
cd modules/module-03-sql-foundations
```

### 2. Instalar Dependencias de Python
```bash
pip install -r requirements.txt
```

### 3. Iniciar database PostgreSQL
```bash
cd infrastructure
docker-compose up -d
cd ..
```

### 4. Inicializar database de Muestra
```bash
bash scripts/setup.sh
```

### 5. Verify Database Connection
```bash
psql -h localhost -p 5432 -U dataeng -d training
# Password: dataeng123
```

### 6. Read the Theory First
```bash
# Comenzar con fundamentos
cat theory/concepts.md | less

# Luego revisar arquitectura
cat theory/architecture.md | less
```

### 7. Completar Ejercicios en Orden
```bash
cd exercises/01-basic-queries
cat README.md
# Seguir instrucciones en cada ejercicio
```

### 8. Validar tu Aprendizaje
```bash
bash scripts/validate.sh
# o
pytest validation/ -v
```

## Ejercicios

### Exercise 01: Basic queries
**Objetivo**: Dominar operaciones fundamentales de SQL

**Temas**:
- SELECT de columns y expresiones
- Filtering with WHERE clause
- Ordenamiento con ORDER BY
- Pagination with LIMIT and OFFSET
- DISTINCT for unique values
- Basic string operations and mathematics

**Datasets**: transactions de e-commerce (100k rows)

**Tiempo**: 2 horas

---

### Ejercicio 02: Joins y Relaciones
**Goal**: Combine data from multiple tables

**Temas**:
- INNER JOIN para registros coincidentes
- LEFT/RIGHT JOIN para preservar rows
- FULL OUTER JOIN para todos los registros
- CROSS JOIN para productos cartesianos
- Self joins for hierarchical data
- Consideraciones de performance de JOIN

**Datasets**: Users, Orders, Products (multi-table)

**Tiempo**: 2-3 horas

---

### Ejercicio 03: Agregaciones y Agrupamiento
**Objetivo**: Resumir y analizar datos

**Temas**:
- COUNT, SUM, AVG, MIN, MAX
- GROUP BY with one or multiple columns
- HAVING para agregados filtrados
- Agregaciones con DISTINCT
- GROUP BY con JOINs
- Common Aggregation Patterns

**Datasets**: Sales data with categories

**Tiempo**: 2 horas

---

### Ejercicio 04: Funciones de Ventana
**Objective**: Perform advanced analytical queries

**Temas**:
- ROW_NUMBER para ranking
- RANK y DENSE_RANK
- LAG y LEAD para comparaciones
- Totales acumulados con SUM OVER
- PARTITION BY para grupos
- Window frames (ROWS, RANGE)

**Datasets**: Actividad de usuarios en series temporales

**Tiempo**: 3 horas

---

### Ejercicio 05: CTEs y Subquerys
**Objetivo**: Escribir querys complejas y mantenibles

**Temas**:
- Common Table Expressions (WITH)
- CTEs recursivos
- Subquerys en SELECT, WHERE, FROM
- Subquerys correlacionadas vs no correlacionadas
- Query readability best practices
- Performance comparison

**Datasets**: Escenarios complejos multi-table

**Tiempo**: 2-3 horas

---

### Exercise 06: Query optimization
**Objetivo**: Analizar y mejorar el performance de querys

**Temas**:
- EXPLAIN y EXPLAIN ANALYZE
- Tipos y uso de indexs
- Query planning and execution
- Optimizing the order of JOINs
- Evitar anti-patrones comunes
- monitor performance de querys

**Datasets**: Dataset grande (1M+ rows)

**Tiempo**: 2-3 horas

---

## Esquema de database de Muestra

The module uses a realistic e-commerce database:

```sql
-- Tabla de usuarios
users (user_id, email, first_name, last_name, created_at, country)

-- Tabla de productos
products (product_id, name, category, price, stock)

-- Tabla de órdenes
orders (order_id, user_id, order_date, total_amount, status)

-- Tabla de items de orden
order_items (item_id, order_id, product_id, quantity, price)

-- Tabla de actividad de usuarios
user_activity (activity_id, user_id, event_type, event_time, session_id)
```

## resources

### Official Documentation
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)

### Aprendizaje Interactivo
- [SQLBolt](https://sqlbolt.com/) - Lecciones interactivas de SQL
- [Mode SQL Tutorial](https://mode.com/sql-tutorial/) - Focused on analytics
- [PostgreSQL Exercises](https://pgexercises.com/) - Practice Problems

### Books and Guides
- "SQL for Data Analysis" by Cathy Tanimura
- "Practical SQL" by Anthony DeBarros
- Ver `theory/resources.md` para lista completa

### Contenido en Video
- [SQL Tutorial - Full Database Course](https://www.youtube.com/watch?v=HXV3zeQKqGY)
- [Advanced SQL for Data Engineers](https://www.youtube.com/playlist?list=PLBgogxgQVM9v0xG0QTFQ5PTbNrj8uGSS-)

## Validation

### Ejecutar Todos los Tests
```bash
bash scripts/validate.sh
```

### Run Specific Exercise Tests
```bash
pytest validation/test_exercise_01.py -v
pytest validation/test_exercise_02.py -v
```

### Verificar performance de queries
```bash
# Ejecutar benchmarks de optimización
python validation/benchmark_queries.py
```

## Progress Checklist

### Theory
- [ ] Leer `theory/concepts.md` (fundamentos de SQL)
- [ ] Leer `theory/architecture.md`(query execution)
- [ ] Revisar `theory/resources.md` (materiales adicionales)

### Ejercicios
- [ ] Exercise 01: Basic queries ✓
- [ ] Ejercicio 02: Joins y Relaciones ✓
- [ ] Ejercicio 03: Agregaciones y Agrupamiento ✓
- [ ] Ejercicio 04: Funciones de Ventana ✓
- [ ] Ejercicio 05: CTEs y Subquerys ✓
- [ ] Exercise 06: Query optimization ✓

### Validation
- [ ] Todos los tests pasando (`pytest validation/`)
- [ ] Benchmarks de performance revisados
- [ ] I can explain query execution plans

### Optional Challenges
- [ ] Resolver todos los problemas bonus en ejercicios
- [ ] Escribir 5 querys complejas desde cero
- [ ] Optimizar una query lenta 10x
- [ ] Completar PostgreSQL Exercises (pgexercises.com)

## Problemas Comunes

### Database connection failure
```bash
# Verificar que Docker está corriendo
docker ps

# Reiniciar PostgreSQL
cd infrastructure
docker-compose restart
```

### queries Lentas
```sql
-- Usar EXPLAIN para analizar
EXPLAIN ANALYZE
SELECT * FROM large_table WHERE condition;

-- Verificar índices faltantes
SELECT * FROM pg_indexes WHERE tablename = 'your_table';
```

### Datos de Muestra Faltantes
```bash
# Re-inicializar base de datos
bash scripts/setup.sh --reset
```

Ver `docs/troubleshooting.md`for complete troubleshooting guide.

## Siguientes Pasos

After completing this module:

1. **Module 04: data transformation** - Apply SQL in ETL pipelines
2. **Module 05: Data Warehousing** - Dimensional modeling with SQL
3. **Module 06: Advanced Analytics** - SQL for ML feature engineering

## resources Adicionales

- **Cheat Sheets**: Ver `assets/cheatsheets/`for quick references
- **SQL Style Guide**: Follow consistent format (see`docs/sql-guide.md`)
- **Ejemplos del Mundo Real**: Revisar `exercises/*/examples/`for production patterns

## Soporte

- Consultar `docs/troubleshooting.md` para problemas comunes
- Revisar pistas de ejercicios en `exercises/*/hints.md`
- See PostgreSQL documentation for function references

---

**Module 03 Status**: Ready for Learning
**Last Update**: February 2026
**Version**: 1.0.0

- [ ] Todas las validaciones pasando
- [ ] Ready for next module

## Siguientes Pasos

After completing this module, you will be ready to:
[List of modules that depend on it]

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
