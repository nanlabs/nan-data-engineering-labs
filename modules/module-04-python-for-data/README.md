# Module 04: Python for Data Engineering

Master Python and its essential libraries to build robust data pipelines, process large volumes of information, and automate data engineering workflows.

## General Description

This module teaches you Python from a data engineering perspective, focusing on the practical skills needed to manipulate data, build ETL pipelines, and work with modern data formats. You will learn from Python fundamentals to advanced techniques with Pandas, working with real data in multiple formats.

**Duration**: 14-16 hours
**Difficulty**: Principiante a Intermedio  
**Prerequisites**:

- Module 03: SQL Foundations (recommended)
- Basic programming knowledge (any language)

## Learning Objectives

Upon completion of this module, you will be able to:

1. **Write idiomatic Python code** following best practices for data engineering
2. **Manipular estructuras de data complejas** usando listas, diccionarios, sets y comprehensions
3. **Work with files in multiple formats** (CSV, JSON, Parquet, Excel)
4. **Master pandas for data analysis** including DataFrames, Series and group operations
5. **Realizar transformaciones de data complejas** con merge, join, pivot y reshape
6. **Implementar data quality checks** usando validaciones y data profiling
7. **Manejar errores y logging** para pipelines de data robustos
8. **Optimize performance** with efficient processing techniques
9. **Trabajar con APIs y web scraping** para data ingestion
10. **Usar virtual environments** y gestionar dependencias correctamente
11. **Write testable code** with unit tests using pytest
12. **Apply data engineering patterns** such as Factory, Builder and pipeline

## Prerequisites

### Required Knowledge

- Basic programming understanding (variables, loops, conditionals)
- Command line familiarity
- Module 03 completed (recommended but not required)

### Required Software

- Python 3.11+
- Docker y Docker Compose
- pip y venv
- Code editor (VS Code recommended)
- 3GB de espacio libre en disco

### Recommended but Optional

- Jupyter Lab/Notebook
- Git para control de versiones
- Basic knowledge of SQL
- Familiaridad con conceptos de ETL

## Module Structure

```text
module-04-python-for-data/
├── README.md                    # Este file
├── STATUS.md                    # Seguimiento de progreso
├── requirements.txt             # Dependencias Python
├── .gitignore                   # Files a ignorar
│
├── theory/                      # 📚 Documentation conceptual
│   ├── concepts.md             # Fundamentos de Python para data
│   ├── architecture.md         # Patrones y arquitecturas
│   └── resources.md            # Recursos adicionales
│
├── infrastructure/              # 🐳 Configuration de environment
│   ├── docker-compose.yml      # Jupyter Lab + Python
│   ├── Dockerfile              # Imagen personalizada
│   ├── .env.example            # Variables de environment
│   └── README.md               # Guide de setup
│
├── data/                        # 📊 Practice datasets
│   ├── raw/                    # Data sin procesar
│   ├── processed/              # Data procesados
│   ├── schemas/                # Esquemas de data
│   └── README.md               # Diccionario de data
│
├── exercises/                   # 💻 Practical exercises
│   ├── 01-python-basics/       # Fundamentos de Python
│   ├── 02-data-structures/     # Listas, dicts, comprehensions
│   ├── 03-file-operations/     # CSV, JSON, Parquet
│   ├── 04-pandas-fundamentals/ # DataFrames y Series
│   ├── 05-data-transformation/ # Cleaning and transformation
│   └── 06-error-handling/      # Logging y excepciones
│
├── validation/                  # ✅ Tests automatizados
│   ├── conftest.py             # Configuration pytest
│   ├── test_exercise_*.py      # Tests per exercise
│   ├── helpers.py              # Utilidades de testing
│   └── README.md               # Guide de testing
│
├── assets/                      # 📋 Recursos de aprendizaje
│   ├── cheatsheets/            # Referencias quicks
│   ├── diagrams/               # Diagramas visuales
│   └── README.md               # Assets catalog
│
└── scripts/                     # 🔧 Automation scripts
    ├── setup.sh                # Configuration inicial
    ├── validate.sh             # Run tests
    ├── reset_env.sh            # Reset de environment
    └── run_jupyter.sh          # Iniciar Jupyter Lab
```text

## Ruta de Aprendizaje

### Fase 1: Fundamentos (4-5 horas)

1. **Theory**: Lee`theory/concepts.md` para entender fundamentos
2. **Setup**: Ejecuta `./scripts/setup.sh` para configurar environment
3. **Exercise 01**: Python Basics - Sintaxis, tipos, operadores
4. **Exercise 02**: Data Structures - Listas, dicts, sets, comprehensions

### Fase 2: Trabajo con Files (3-4 horas)

1. **Exercise 03**: File Operations - CSV, JSON, Parquet, Excel
2. **Practice**: Load and explore the datasets in`data/raw/`

### Fase 3: Pandas y Transformaciones (5-6 horas)

1. **Exercise 04**: Pandas Fundamentals - DataFrames, Series, indexing
2. **Exercise 05**: Data Transformation - Merge, group, pivot, reshape
3. **Mini Project**: Build a complete transformation pipeline

### Phase 4: Production (2-3 hours)

1. **Exercise 06**: Error Handling - Try/except, logging, debugging
2. **Validation**: Execute`./scripts/validate.sh` para verificar aprendizaje
3. **Review**: Study`assets/cheatsheets/` para repasar conceptos

## Exercises Detallados

### Exercise 01: Python Basics (60 min)

**Objectives**:

- Basic Python Syntax
- Tipos de data (int, float, str, bool)
- Operadores y expresiones
- Control de flujo (if/elif/else, loops)
- Basic functions

**Files**:

- `starter/basics.py` - Exercises con TODO
- `solution/basics.py` - Soluciones completas
- `README.md`- Theory and examples

---

### Exercise 02: Data Structures (90 min)

**Objectives**:

- Listas y operaciones (append, slice, sort)
- Dictionaries and methods (keys, values, items)
- Sets y operaciones de conjunto
- Tuples e inmutabilidad
- List/Dict/Set comprehensions
- Nested structures

**Files**:

- `starter/data_structures.py` - Exercises
- `solution/data_structures.py` - Soluciones
- `examples/comprehensions.py` - Ejemplos avanzados
- `README.md`- Detailed guide

---

### Exercise 03: File Operations (120 min)

**Objectives**:

- Lectura/escritura de CSV con `csv` module
- Trabajo con JSON (load, dump, nested data)
- Parquet files con `pyarrow`/`fastparquet`
- Excel files con `openpyxl`
- Context managers (`with` statement)
- Error handling en I/O

**Files**:

- `starter/file_io.py` - Exercises
- `solution/file_io.py` - Soluciones
- `data/` - Files de ejemplo
- `README.md`- Format guide

---

### Exercise 04: Pandas Fundamentals (150 min)

**Objectives**:

- Crear DataFrames y Series
- Indexing y selection (loc, iloc, at, iat)
- Filtering y querying
- Column operations
- Basic statistics (describe, mean, median)
- Sorting y ranking
- Missing data (isna, fillna, dropna)

**Files**:

- `starter/pandas_basics.py` - Exercises
- `solution/pandas_basics.py` - Soluciones
- `notebooks/pandas_tutorial.ipynb` - Jupyter notebook
- `README.md`- Complete guide

---

### Exercise 05: Data Transformation (180 min)

**Objectives**:

- Merge y join operations
- Concatenate DataFrames
- GroupBy y aggregations
- Pivot tables
- Reshape (melt, stack, unstack)
- Apply y map functions
- String operations
- Date/time handling

**Files**:

- `starter/transformation.py` - Exercises
- `solution/transformation.py` - Soluciones
- `examples/etl_pipeline.py` - pipeline completo
- `README.md`- Transformation patterns

---

### Exercise 06: Error Handling & Logging (90 min)

**Objectives**:

- Try/except/finally blocks
- Exception types
- Custom exceptions
- Logging module (info, warning, error)
- Log configuration
- Debugging techniques
- Best practices for production

**Files**:

- `starter/error_handling.py` - Exercises
- `solution/error_handling.py` - Soluciones
- `examples/production_pipeline.py` - pipeline robusto
- `README.md`- Common errors guide

---

## Practice Dataset

The module includes a realistic e-commerce dataset with multiple formats:

### Files Disponibles

- `customers.csv` (10,000 registros) - Data de clientes
- `orders.json`(50,000 records) - Orders with nested data
- `products.parquet`(5,000 records) - Product Catalog
- `transactions.csv` (100,000 registros) - transactions detalladas
- `user_activity.json` (200,000 registros) - Logs de actividad

### features

- Data realistas con casos edge (nulls, duplicados)
- Multiple formats for practice
- Relaciones entre tables para joins
- Timestamps for temporal analysis
- Data sucios para data cleaning

## Validation and Testing

### Run Todos los Tests

```bash
cd modules/module-04-python-for-data
./scripts/validate.sh
```text

### Tests por Exercise

```bash
./scripts/validate.sh --exercise 01  # Only exercise 01
./scripts/validate.sh --exercise 04  # Solo pandas
```

### Tests con Coverage

```bash
./scripts/validate.sh --coverage
```text

### Quick Tests (without slow ones)

```bash
./scripts/validate.sh --fast
```text

## Environment de Desarrollo

### Option 1: Docker (Recommended)

```bash
# Automatic setup
./scripts/setup.sh

# Iniciar Jupyter Lab
./scripts/run_jupyter.sh

# Acceder a: http://localhost:8888
```text

### Option 2: Virtual Environment Local

```bash
# Crear venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Verify installation
python -c "import pandas; print(pandas.__version__)"
```

### Option 3: Poetry (Advanced)

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Setup proyecto
poetry install

# Activar shell
poetry shell
```text

## resources Adicionales

### Cheatsheets Incluidos

- `assets/cheatsheets/python-basics.md` - Sintaxis fundamental
- `assets/cheatsheets/pandas-reference.md` - Operaciones pandas
- `assets/cheatsheets/data-cleaning.md`- Cleaning techniques
- `assets/cheatsheets/file-formats.md` - CSV/JSON/Parquet

### External Documentation

- [Python Docs](https://docs.python.org/3/) - Official documentation
- [Pandas Docs](https://pandas.pydata.org/docs/) - Pandas Guide
- [Real Python](https://realpython.com/) - Practical tutorials
- [Python for Data Analysis](https://wesmckinney.com/book/) - Libro de Wes McKinney

### Comunidad

- Stack Overflow - Technical Questions
- r/datascience - Reddit community
- PyData - Conferencias y meetups

## Checklist de Progreso

### Fundamentos

- [ ] Read`theory/concepts.md`
- [ ] Read`theory/architecture.md`
- [ ] Setup completed (`./scripts/setup.sh`)
- [ ] Jupyter Lab funcionando

### Exercises

- [ ] ✅ Exercise 01: Python Basics (tests pasando)
- [ ] ✅ Exercise 02: Data Structures (tests pasando)
- [ ] ✅ Exercise 03: File Operations (tests pasando)
- [ ] ✅ Exercise 04: Pandas Fundamentals (tests pasando)
- [ ] ✅ Exercise 05: Data Transformation (tests pasando)
- [ ] ✅ Exercise 06: Error Handling (tests pasando)

### Validation

- [ ] Todos los tests pasando (`./scripts/validate.sh`)
- [ ] Coverage > 80%
- [ ] Revisado cheatsheets en `assets/`

### Proyecto Final

- [ ] pipeline ETL completo implementado
- [ ] Data quality checks incluidos
- [ ] Error handling robusto
- [ ] Logging configurado
- [ ] Documented code

## Next Steps

After completing this module, you will be ready to:

- **Module 05**: Data Lakehouse Architecture - Apply Python in modern architectures
- **Module 06**: ETL Fundamentals - Build complete pipelines
- **Module 07**: Batch Processing - Process large volumes with PySpark
- **Module 08**: Streaming Basics - Real-time data processing

## Estimated Time per Section

| Section | Estimated Time | Priority |
|---------|----------------|-----------|
| Theory (concepts + architecture) | 2-3 horas | Alta |
| Setup (infrastructure) | 30 min | Alta |
| Exercise 01 (Python Basics) | 1 hora | Alta |
| Exercise 02 (Data Structures) | 1.5 horas | Alta |
| Exercise 03 (File Operations) | 2 horas | Alta |
| Exercise 04 (Pandas Fundamentals) | 2.5 hours | Review |
| Exercise 05 (Data Transformation) | 3 hours | Review |
| Exercise 06 (Error Handling) | 1.5 horas | Alta |
| Assets & Cheatsheets | 1 hora | Media |
| Proyecto Final | 2 horas | Media |
| **TOTAL** | **14-16 horas** | - |

## Quick Commands

```bash
# Setup inicial
./scripts/setup.sh

# Jupyter Lab
./scripts/run_jupyter.sh

# Validate todo
./scripts/validate.sh

# Validate specific exercise
./scripts/validate.sh --exercise 04

# Reset environment
./scripts/reset_env.sh

# Ver logs
docker-compose -f infrastructure/docker-compose.yml logs -f
```text

## Troubleshooting

### Error: "Module not found"

```bash
# Verify installation
pip list | grep pandas

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```text

### Jupyter Lab no inicia

```bash
# Verificar puerto 8888 libre
lsof -i :8888

# Reiniciar container
docker-compose -f infrastructure/docker-compose.yml restart
```

### Tests fallan

```bash
# Ver detalles
./scripts/validate.sh --verbose

# Limpiar cache pytest
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name .pytest_cache -exec rm -rf {} +
```text

See complete guide at`docs/troubleshooting.md`

## Contribuciones

This module is part of the **Training Cloud Data** course. To report bugs or suggest improvements:

1. Revisar `STATUS.md` para ver progreso actual
2. Verificar que el issue no exista
3. Incluir detalles del problema
4. Proporcionar ejemplos reproducibles

## Notas Importantes

- 🐍 **Python 3.11+** requerido (usa features modernas)
- 📊 **pandas 2.0+** para mejor performance
- 🐳 **Docker recomendado** para consistencia
- 📝 **Jupyter notebooks** included for exploration
- ✅ **Tests obligatorios** antes de avanzar
- 🔧 **Code style**: Seguimos PEP 8
- 📚 **Documentation**: All exercises have detailed README

## Licencia

Este material es parte del curso Training Cloud Data.

---

**Ready to get started?** 🚀

```bash
cd modules/module-04-python-for-data
./scripts/setup.sh
```text

Success in your learning Python for Data Engineering!
