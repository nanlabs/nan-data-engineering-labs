# DAGs de Ejemplo - Module 10

Este directorio contiene DAGs de ejemplo para cada exercise del module. Estos archivos están listos para usar y demuestran las mejores prácticas de Airflow.

## 📁 Estructura

```
dags/
├── ex01_hello_world.py          # Exercise 01: Primer DAG básico
├── ex01_etl_pipeline.py          # Exercise 01: Pipeline ETL con XComs
├── ex02_multi_operators.py       # Exercise 02: Múltiples operadores
├── ex03_branching.py             # Exercise 03: Branching condicional
├── ex04_api_pipeline.py          # Exercise 04: Pipeline API→DB
└── ex05_monitoring.py            # Exercise 05: Monitoreo y alertas
```

## 🎯 Description de DAGs

### 1. ex01_hello_world.py
**Conceptos**: DAG básico, PythonOperator, BashOperator, dependencias simples

Primer DAG de introducción que muestra:
- Configuration básica de un DAG
- PythonOperator para execute funciones Python
- BashOperator para comandos shell
- Dependencias secuenciales (`>>`)
- Tags y metadata

**Schedule**: `@daily`
**Tags**: `exercise`, `basico`, `ejemplo`

### 2. ex01_etl_pipeline.py
**Conceptos**: Pipeline ETL, XComs, step de datos entre tasks

Pipeline ETL completo que demuestra:
- Extracción de datos (simulado)
- Transformación con lógica de negocio
- Carga de datos transformados
- Uso de XComs para pasar datos entre tasks
- `provide_context=True` para acceder a context

**Schedule**: `@daily`
**Tags**: `exercise`, `etl`, `xcoms`

### 3. ex02_multi_operators.py
**Conceptos**: Múltiples tipos de operadores, callbacks, trigger rules

Demuestra el uso de varios operadores:
- PythonOperator para procesamiento
- BashOperator para comandos del sistema
- Diferentes configuraciones de retry
- Trigger rule `all_done` para cleanup
- Callbacks de éxito y fallo

**Schedule**: `0 */6 * * *` (cada 6 hours)
**Tags**: `exercise`, `operadores`

### 4. ex03_branching.py
**Conceptos**: Branching condicional, BranchPythonOperator, trigger rules avanzados

Pipeline con lógica condicional:
- BranchPythonOperator para decisiones
- Múltiples rutas de ejecución
- Trigger rule `none_failed_min_one_success` para consolidación
- Lógica de negocio basada en datos

**Schedule**: `@daily`
**Tags**: `exercise`, `branching`, `avanzado`

### 5. ex04_api_pipeline.py
**Conceptos**: ETL real, integración con APIs, manejo de errores

Pipeline ETL completo con API real:
- Extracción desde JSONPlaceholder API
- Transformación de datos (joins, agregaciones)
- Simulación de carga a base de datos
- Generación de reportes
- Manejo de errores con retries

**Schedule**: `0 */12 * * *` (cada 12 hours)
**Tags**: `exercise`, `etl`, `api`, `pipeline`

### 6. ex05_monitoring.py
**Conceptos**: Monitoreo, SLAs, callbacks, observabilidad

DAG con monitoreo completo:
- SLA tracking (5 minutes global, 3 minutes para task crítico)
- Callbacks personalizados (success, failure, retry)
- Callback de violación de SLA
- Métricas de performance
- Quality checks

**Schedule**: `*/15 * * * *` (cada 15 minutes)
**Tags**: `exercise`, `monitoreo`, `alertas`, `produccion`

## 🚀 Cómo Usar

### Opción 1: Copiar a Airflow Local

Si tienes Airflow corriendo localmente:

```bash
# Copiar todos los DAGs
cp dags/*.py $AIRFLOW_HOME/dags/

# O copiar individualmente
cp dags/ex01_hello_world.py $AIRFLOW_HOME/dags/
```

### Opción 2: Usar con Docker Compose

Si usas el Docker Compose del module:

```bash
# Los DAGs ya están montados en el volumen
cd infrastructure
docker-compose up -d

# Acceder a Airflow UI
open http://localhost:8080
```

Los DAGs aparecerán automáticamente en la UI.

### Opción 3: Desarrollo y Testing

Validar sintaxis de un DAG:

```bash
# Verificar que no hay errores de importación
python dags/ex01_hello_world.py

# Listar tasks del DAG
airflow tasks list ex01_hello_world

# Probar un task específico
airflow tasks test ex01_hello_world hello_task 2024-01-01
```

## 📊 Dependencias

Todos los DAGs requieren:
- **Apache Airflow**: 2.8.1+
- **Python**: 3.8+

DAGs específicos requieren:
- `ex04_api_pipeline.py`: `requests` library
- Pipeline con DB: `psycopg2-binary`, `apache-airflow-providers-postgres`
- Pipeline con S3: `boto3`, `apache-airflow-providers-amazon`

Instalar todas las dependencias:

```bash
pip install -r ../requirements.txt
```

## 🧪 Testing

Ejecutar tests de validation de DAGs:

```bash
cd ../validation
pytest test_module.py -v
```

Tests incluyen:
- ✅ No import errors
- ✅ No cycles en DAGs
- ✅ Todos los DAGs tienen tags
- ✅ Estructura correcta de dependencias
- ✅ Configuration válida

## 🎓 Orden de Aprendizaje Recomendado

1. **ex01_hello_world.py** → Conceptos básicos
2. **ex01_etl_pipeline.py** → XComs y step de datos
3. **ex02_multi_operators.py** → Diferentes operadores
4. **ex03_branching.py** → Lógica condicional
5. **ex04_api_pipeline.py** → Pipeline real completo
6. **ex05_monitoring.py** → Producción y observabilidad

## 💡 Tips

### Debugging
```bash
# Ver logs de un task
airflow tasks logs ex01_hello_world hello_task 2024-01-01

# Limpiar estado de un DAG
airflow dags delete ex01_hello_world
```

### Performance
- Usa `catchup=False` para evitar backfilling
- Define SLAs apropiados
- Implement idempotencia en tasks
- Usa pools para limitar concurrencia

### Producción
- Siempre define `owner`
- Configure `retries` y `retry_delay`
- Implement callbacks de error
- Usa tags para organización
- Document tus DAGs con docstrings

## 📚 Recursos Adicionales

- [Documentación oficial de Airflow](https://airflow.apache.org/docs/)
- [Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [TaskFlow API](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)

## ❓ Troubleshooting

**DAG no aparece en la UI**
- Verify que no hay errores de sintaxis: `python dags/tu_dag.py`
- Revisa import errors en Admin → Import Errors
- Asegúrate que el archivo está en `$AIRFLOW_HOME/dags/`

**Task falla**
- Revisa logs en la UI o con `airflow tasks logs`
- Verify dependencias instaladas
- Comprueba configuration de connections/variables

**SLA violation**
- Ajusta los tiempos de SLA según tu entorno
- Revisa que tasks no están bloqueados
- Verify recursos del sistema (CPU, memoria)

---

**¿Preguntas?** Revisa la documentación en [theory/](../theory/) o los exercises en [exercises/](../exercises/)
