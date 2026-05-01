# Exercises: Python for Data Engineering

This folder contains 6 progressive exercises designed to build Python skills applied to data engineering. Each exercise includes theory, starter code with TODOs, complete solutions and automated tests.

## Estructura de Ejercicios

```
exercises/
├── 01-python-basics/           # Fundamentos de Python
├── 02-data-structures/         # Listas, dicts, comprehensions
├── 03-file-operations/         # CSV, JSON, Parquet
├── 04-pandas-fundamentals/     # DataFrames y operaciones
├── 05-data-transformation/     # ETL, joins, aggregations
└── 06-error-handling/          # Logging, excepciones, producción
```

## How to Use the Exercises

### Option 1: Guided Mode (Recommended for Learning)

1. **Read theory**: Open the`README.md` de cada ejercicio
2. **Intentar starter**: Trabaja en `starter/ejercicio.py`
   - Busca los comentarios `# TODO:`
   - Implementa las funciones marcadas
3. **Run tests**: Verify your solution
   ```bash
   pytest exercises/01-python-basics/tests/ -v
   ```
4. **Comparar con solution**: Si te atoras, revisa `solution/`
5. **Repetir con ejemplos**: Explora `examples/` para casos avanzados

### Option 2: Self-taught Mode

1. Lee el README
2. Deploy your own version from scratch
3. Compare with solution after

### Option 3: Review Mode

1. Lee solution directamente
2. Ejecuta tests
3. Modifica y experimenta

---

## Lista de Ejercicios

### 📘 Ejercicio 01: Python Basics

**Duration**: 1-2 hours
**Dificultad**: ⭐☆☆☆☆

**Temas**:
- Variables y tipos de datos
- Features and documentation
- Control de flujo (if/else, loops)
- Basic operations with strings and numbers

**Objetivos**:
- Escribir funciones con type hints
- Document code with docstrings
- Handle edge cases (empty values, None)

**Archivos**:
- `README.md`- Theory
- `starter/basics.py`- Your code here
- `solution/basics.py`- Complete solution
- `tests/test_basics.py` - 15 tests

---

### 📗 Ejercicio 02: Data Structures

**Duration**: 2-3 hours
**Dificultad**: ⭐⭐☆☆☆

**Temas**:
- Listas y tuplas
- Diccionarios y sets
- List comprehensions
- Dictionary comprehensions
- Nested structures

**Objetivos**:
- Manipular estructuras de datos eficientemente
- Use comprehensions for concise code
- Trabajar con datos nested

**Archivos**:
- `README.md`- Theory
- `starter/data_structures.py`- Your code here
- `solution/data_structures.py`- Complete solution
- `examples/comprehensions.py` - Ejemplos avanzados
- `tests/test_data_structures.py` - 20 tests

---

### 📙 Ejercicio 03: File Operations

**Duration**: 2-3 hours
**Dificultad**: ⭐⭐⭐☆☆

**Temas**:
- Leer/escribir archivos de texto
- CSV con csv module
- JSON con json module
- Parquet con pandas/pyarrow
- Context managers

**Objetivos**:
- Handle multiple file formats
- Usar encoding correcto (UTF-8)
- Implementar error handling robusto
- Work with real module data

**Archivos**:
- `README.md`- Theory
- `starter/file_io.py`- Your code here
- `solution/file_io.py`- Complete solution
- `tests/test_file_io.py` - 18 tests

---

### 📕 Ejercicio 04: Pandas Fundamentals

**Duration**: 3-4 hours
**Dificultad**: ⭐⭐⭐☆☆

**Temas**:
- Crear DataFrames
- Selection and filtering
- Agregaciones y groupby
- Merge y join
- Basic data cleaning

**Objetivos**:
- Dominar operaciones core de pandas
- Limpiar datos sucios (nulls, duplicados)
- Perform exploratory analysis
- Use real data from the module

**Archivos**:
- `README.md`- Theory
- `starter/pandas_basics.py`- Your code here
- `solution/pandas_basics.py`- Complete solution
- `notebooks/pandas_tutorial.ipynb` - Tutorial interactivo
- `tests/test_pandas.py` - 25 tests

---

### 📔 Ejercicio 05: Data Transformation

**Duration**: 3-4 hours
**Dificultad**: ⭐⭐⭐⭐☆

**Temas**:
- ETL pipelines
- Flatten nested JSON
- Joins complejos (inner, left, right, outer)
- Pivot y reshape
- Data validation

**Objetivos**:
- Construir pipeline ETL completo
- Normalizar estructuras nested
- Integrate multiple datasets
- Calculate business metrics

**Archivos**:
- `README.md`- Theory
- `starter/transformation.py`- Your code here
- `solution/transformation.py`- Complete solution
- `examples/etl_pipeline.py` - pipeline completo
- `tests/test_transformation.py` - 22 tests

---

### 📓 Ejercicio 06: Error Handling & Production

**Duration**: 2-3 hours
**Dificultad**: ⭐⭐⭐⭐☆

**Temas**:
- Try/except/finally
- Excepciones personalizadas
- Logging estructurado
- Input validation
- Retry logic

**Objetivos**:
- Write production-ready code
- Manejar errores elegantemente
- Implement useful logging
- Validar datos con schemas

**Archivos**:
- `README.md`- Theory
- `starter/error_handling.py`- Your code here
- `solution/error_handling.py`- Complete solution
- `examples/production_pipeline.py` - pipeline robusto
- `tests/test_error_handling.py` - 20 tests

---

## Test Execution

### Ejecutar todos los tests

```bash
# Desde la raíz del módulo
pytest exercises/ -v

# Con coverage
pytest exercises/ --cov=exercises --cov-report=html
```

### Run tests for a specific exercise

```bash
pytest exercises/01-python-basics/tests/ -v
pytest exercises/04-pandas-fundamentals/tests/ -v
```

### Run a specific test

```bash
pytest exercises/01-python-basics/tests/test_basics.py::test_suma -v
```

### Ejecutar tests con output detallado

```bash
pytest exercises/ -v -s  # -s muestra prints
```

---

## Progreso Sugerido

### Semana 1: Fundamentos
- ✅ Day 1-2: Exercise 01 (Python Basics)
- ✅ Day 3-4: Exercise 02 (Data Structures)
- ✅ Day 5-6: Exercise 03 (File Operations)

### Semana 2: Pandas y ETL
- ✅ Day 1-3: Exercise 04 (Pandas Fundamentals)
- ✅ Day 4-6: Exercise 05 (Data Transformation)

### Semana 3: Production
- ✅ Day 1-2: Exercise 06 (Error Handling)
- ✅ Day 3-5: Final project (combine everything)

---

## Tips for Success

### 🎯 Antes de Empezar

1. **Lee el README completo** del ejercicio
2. **Watch the tests** to understand what to expect
3. **Experiment in notebook** before writing code
4. **Usa los datos reales** de `data/raw/`

### 💡 Durante el Ejercicio

1. **No copies-pegues** solution - aprende escribiendo
2. **Run tests frequently** (each function)
3. **Usa print()** liberalmente para debugging
4. **query documentation** (pandas, Python docs)
5. **Pregunta en comunidades** si te atoras

### ✅ After Completing

1. **Compare your code** with solution
2. **Identifica diferencias** en approach
3. **Aprende patrones** usados en solution
4. **Refactor** your code if necessary
5. **Experimenta con examples/** para profundizar

---

## resources Adicionales

### Official Documentation
- [Python Tutorial](https://docs.python.org/3/tutorial/)
- [Pandas User Guide](https://pandas.pydata.org/docs/user_guide/)
- [pytest Documentation](https://docs.pytest.org/)

### Module Theory
- `theory/concepts.md` - Fundamentos de Python
- `theory/architecture.md`- Design patterns
- `theory/resources.md` - 200+ resources externos

### Practice Data
- `data/README.md`- Complete dataset documentation
- `data/schemas/` - Schemas JSON con validaciones

---

## Troubleshooting

### Tests no pasan

```bash
# Ver error detallado
pytest exercises/01-python-basics/tests/ -v -s

# Ver qué línea falla exactamente
pytest exercises/01-python-basics/tests/ --tb=long
```

### Import errors

```bash
# Asegurarte de estar en la raíz del módulo
cd /path/to/module-04-python-for-data

# O ajustar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Datos no encontrados

```bash
# Verificar que los datos existen
ls -lh data/raw/

# Regenerar si es necesario
cd data && python3 generate_all_datasets.py
```

### Pandas no instalado

```bash
# Si usas Docker (recomendado)
docker-compose up -d jupyter
# Acceder a http://localhost:8888

# Si usas venv local
pip install -r requirements.txt
```

---

## Assessment

### Success Criteria by Exercise

| Exercise | Test Passing | Estimated Time | Comprehension |
|-----------|---------------|-----------------|-------------|
| 01 - Python Basics | 15/15 ✅ | 1-2h | Basic syntax |
| 02 - Data Structures | 20/20 ✅ | 2-3h | Estructuras core |
| 03 - File Operations | 18/18 ✅ | 2-3h | I/O multi-formato |
| 04 - Pandas Fundamentals | 25/25 ✅ | 3-4h | DataFrames |
| 05 - Data Transformation | 22/22 ✅ | 3-4h | ETL completo |
| 06 - Error Handling | 20/20 ✅ | 2-3h | Production code |

**Total**: 120 tests, ~14-16 horas

### Self-Assessment

After each exercise, ask yourself:

1. ✅ Do I understand **why** my code works?
2. ✅ Could you explain it to someone else?
3. ✅ Could you solve a similar problem without help?
4. ✅ Do I know alternatives to the approach I used?
5. ✅ Is my code readable and well documented?

---

## Proyecto Final (Opcional)

After completing the 6 exercises, build a **complete ETL pipeline**:

**Objetivo**: Procesar todos los datasets y generar un reporte de negocio

**Requerimientos**:
1. Leer los 5 datasets (CSV, JSON)
2. Limpiar datos (duplicados, nulls, inconsistencias)
3. Integrar con joins (customers ← orders ← transactions)
4. Calculate metrics:
   - Total revenue and by country
   - Top 10 best-selling products
   - Customer lifetime value
   - Conversion rate del funnel
5. Exportar resultados a CSV y JSON
6. Logging completo de cada paso
7. Tests unitarios (>80% coverage)

**Tiempo estimado**: 8-10 horas

---

## Siguiente Paso

After completing these exercises:

➡️ **Paso 6: Validation** - Tests automatizados integrados  
➡️ **Paso 7: Assets** - Cheatsheets y diagramas de referencia  
➡️ **Step 8: Scripts & Docs** - Automation and troubleshooting

---

**Happy coding! 🐍🐼**

Doubts? Review`theory/` o query los `examples/` en cada ejercicio.
