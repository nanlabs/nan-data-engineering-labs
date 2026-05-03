# Guía de Inicio Rápido - Module 10

## 🚀 Setup en 5 minutes

### 1. Iniciar Airflow (Opción recomendada: Docker)

```bash
cd modules/module-10-workflow-orchestration

# Ejecutar script de setup automático
./scripts/setup.sh

# Esperar ~2 minutes mientras se inicializan los servicios
```

### 2. Acceder a la UI

Abre tu navegador en:
- **Airflow Web UI**: http://localhost:8080
  - Usuario: `airflow`
  - Contraseña: `airflow`

- **Flower (Monitoreo Celery)**: http://localhost:5555

### 3. Verificar instalación

```bash
# Ejecutar validation automática
./scripts/validate.sh

# Deberías ver:
# ✅ Airflow corriendo
# ✅ Servicios saludables
# ✅ DAGs listados
# ✅ Tests pasando
```

## 📚 Orden de Aprendizaje

### Semana 1: Fundamentos (6-8 hours)

**Día 1-2: Theory**
1. Leer [theory/01-airflow-fundamentals.md](theory/01-airflow-fundamentals.md)
2. Leer [theory/02-dags-and-operators.md](theory/02-dags-and-operators.md)

**Día 3-4: Exercises Básicos**
1. [exercises/01-first-dag/](exercises/01-first-dag/) → 6 tasks (~2-3 hours)
2. [exercises/02-operators-sensors/](exercises/02-operators-sensors/) → 6 tasks (~3-4 hours)

**DAGs a revisar**: `ex01_hello_world.py`, `ex01_etl_pipeline.py`, `ex02_multi_operators.py`

### Semana 2: Intermedio (8-10 hours)

**Día 1-2: Dependencias Complejas**
1. [exercises/03-task-dependencies/](exercises/03-task-dependencies/) → 6 tasks (~3-4 hours)

**Día 3-5: Pipelines Reales**
1. [exercises/04-data-pipelines/](exercises/04-data-pipelines/) → 6 tasks (~4-5 hours)

**DAGs a revisar**: `ex03_branching.py`, `ex04_api_pipeline.py`

### Semana 3: Producción (6-8 hours)

**Día 1-2: Monitoreo**
1. [exercises/05-monitoring-alerts/](exercises/05-monitoring-alerts/) → 5 tasks (~2-3 hours)

**Día 3-5: Deployment**
1. Leer [theory/03-production-patterns.md](theory/03-production-patterns.md)
2. [exercises/06-production-deployment/](exercises/06-production-deployment/) → 6 tasks (~4-5 hours)

**DAGs a revisar**: `ex05_monitoring.py`

## ⚡ Comandos Rápidos

### Gestión de Servicios

```bash
# Iniciar
cd infrastructure && docker-compose up -d

# Ver logs
docker-compose logs -f webserver

# Reiniciar scheduler
docker-compose restart scheduler

# Detener todo
docker-compose down

# Detener y limpiar volúmenes
docker-compose down -v
```

### Comandos Airflow

```bash
# Listar DAGs
docker-compose exec webserver airflow dags list

# Probar un task
docker-compose exec webserver airflow tasks test ex01_hello_world hello_task 2024-01-01

# Ver estado de un DAG
docker-compose exec webserver airflow dags state ex01_hello_world

# Trigger manual
docker-compose exec webserver airflow dags trigger ex01_hello_world

# Ver logs
docker-compose exec webserver airflow tasks logs ex01_hello_world hello_task 2024-01-01 1
```

### Validation

```bash
# Validar todos los DAGs
cd validation && pytest . -v

# Solo tests de DAG
pytest -m dag_validation

# Tests rápidos
pytest -m unit

# Con cobertura
pytest --cov=../exercises --cov-report=html
```

## 🎓 Checklist de Progreso

### Fundamentos
- [ ] Entiendo qué es un DAG
- [ ] Puedo create un DAG básico con PythonOperator
- [ ] Entiendo las dependencias con `>>`
- [ ] Sé usar XComs para pasar datos
- [ ] Conozco schedule_interval y start_date

### Intermedio
- [ ] Uso múltiples operadores (Python, Bash, Email)
- [ ] Implemento branching con BranchPythonOperator
- [ ] Entiendo los 7 trigger rules
- [ ] Creo pipelines ETL reales (API→DB→S3)
- [ ] Manejo errores con retries y callbacks

### Avanzado
- [ ] Configuro SLAs y monitoreo
- [ ] Implemento callbacks personalizados
- [ ] Integro con Slack/email para alertas
- [ ] Escribo tests para mis DAGs
- [ ] Depliego con Docker Compose
- [ ] Configuro CI/CD para DAGs

## 🐛 Troubleshooting Rápido

### DAG no aparece
```bash
# Verificar errores de sintaxis
python dags/tu_dag.py

# Ver import errors en UI
# Admin → Import Errors

# Refrescar DAG list
docker-compose exec webserver airflow dags list-import-errors
```

### Task falla
```bash
# Ver logs detallados
docker-compose exec webserver airflow tasks logs DAG_ID TASK_ID DATE

# Re-execute task
docker-compose exec webserver airflow tasks run DAG_ID TASK_ID DATE

# Limpiar estado
docker-compose exec webserver airflow dags delete DAG_ID
```

### Servicios no inician
```bash
# Ver logs
docker-compose logs -f

# Verificar recursos
docker stats

# Reiniciar todo
docker-compose down
docker-compose up -d

# Reset completo
docker-compose down -v
./scripts/setup.sh
```

### Base de datos locked
```bash
# Reiniciar solo scheduler
docker-compose restart scheduler

# Si persiste, reset DB
docker-compose down -v
docker-compose up airflow-init
docker-compose up -d
```

## 📁 Estructura de Archivos Importante

```
module-10-workflow-orchestration/
├── dags/                     # 👈 TUS DAGs VAN AQUÍ
│   ├── ex01_hello_world.py  # Ejemplos listo para usar
│   └── tu_dag.py             # Create tus propios DAGs aquí
│
├── infrastructure/
│   ├── docker-compose.yml    # Configuration de servicios
│   └── .env                  # Variables de entorno
│
├── data/                     # Datos de ejemplo
│   ├── sample/*.csv          # Datasets para exercises
│   └── schemas/*.sql         # Crear tablas
│
├── scripts/
│   ├── setup.sh              # ⚡ Setup automático
│   └── validate.sh           # ✅ Validation completa
│
└── exercises/                # Guías step a step
    ├── 01-first-dag/
    ├── 02-operators-sensors/
    └── ...
```

## 💡 Tips Pro

1. **Desarrollo Local**:
   - Edita DAGs en `dags/` directamente
   - Airflow detecta cambios automáticamente
   - Validate sintaxis con `python tu_dag.py` antes

2. **Debugging**:
   - Usa `print()` liberalmente - aparece en logs
   - Test tasks individualmente con `airflow tasks test`
   - Revisa XCom viewer en la UI (Graph → XCom)

3. **Performance**:
   - Usa `catchup=False` para evitar backfill
   - Limita parallelism con pools
   - Implement idempotencia en tasks

4. **Producción**:
   - Siempre define SLAs para tasks críticos
   - Implement callbacks de error
   - Usa secrets para credenciales
   - Write tests para tus DAGs

## 📚 Recursos Útiles

- **Theory**: `theory/` → 15K palabras de documentación
- **Exercises**: `exercises/` → 6 exercises progresivos
- **Ejemplos**: `dags/` → 6 DAGs listos para usar
- **Tests**: `validation/` → 40+ tests como referencia

## 🆘 ¿Necesitas Ayuda?

1. Revisa [theory/01-airflow-fundamentals.md](theory/01-airflow-fundamentals.md) para conceptos
2. Busca en [theory/02-dags-and-operators.md](theory/02-dags-and-operators.md) para código
3. Consulta [theory/03-production-patterns.md](theory/03-production-patterns.md) para producción
4. Revisa DAGs de ejemplo en `dags/` para patrones
5. Execute `./scripts/validate.sh` para verify tu setup

## ✅ Verificación Final

Antes de continuar al siguiente module, asegúrate de:

```bash
# 1. Todos los servicios corriendo
docker-compose ps  # todos "healthy"

# 2. DAGs cargados sin errores
docker-compose exec webserver airflow dags list | grep ex0

# 3. Tests pasando
cd validation && pytest . -v  # all green

# 4. Puedes acceder a UI
curl http://localhost:8080/health  # {"status": "healthy"}
```

---

## 🎯 Próximos Steps

1. ✅ Completar los 6 exercises
2. ✅ Crear al menos 2 DAGs propios
3. ✅ Ejecutar `./scripts/validate.sh` exitosamente
4. ✅ Pasar todos los tests en `validation/`
5. ➡️  Continuar con **Module 11: Infrastructure as Code**

---

**¡Éxito con Airflow!** 🚀

Para preguntas o problemas, revisa la documentación o los exercises con ejemplos detallados.
