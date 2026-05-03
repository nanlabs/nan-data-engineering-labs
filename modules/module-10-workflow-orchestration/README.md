# Module 10: Orquestación de Workflows con Apache Airflow

Domina la orquestación de workflows y automatización de pipelines de datos usando Apache Airflow, la plataforma estándar de la industria para crear, programar y monitorear pipelines de datos.

## 📋 Description General

Este module proporciona entrenamiento integral en Apache Airflow 2.8, cubriendo desde conceptos básicos hasta patrones de despliegue en producción. You will learn a diseñar, implementar, probar y desplegar pipelines de datos robustos que pueden orquestar workflows complejos a través de múltiples sistemas.

**¿Por qué orquestación de workflows?** Los pipelines de datos modernos involucran múltiples steps, dependencias e integraciones. Airflow proporciona:
- **Gestión de dependencias**: Define el orden y relaciones de las tareas
- **Programación**: Ejecución automatizada en intervalos especificados
- **Monitoreo**: Rastrea la salud y rendimiento del pipeline
- **Reintentos**: Recuperación automática de fallos
- **Escalabilidad**: Ejecución distribuida con workers
- **Extensibilidad**: Operadores y sensores personalizados

## 🎯 Objectives de Aprendizaje

Al completar este module, podrás:

1. **Entender la Arquitectura de Airflow**
   - Componentes centrales (webserver, scheduler, executor, workers, metadata DB)
   - Flujo de ejecución y ciclo de vida de tareas
   - Mecanismos de parsing de DAG y programación

2. **Crear DAGs Listos para Producción**
   - Patrones de diseño de DAG (clásico, context manager, TaskFlow API)
   - Dependencias de tareas y reglas de activación
   - Generación dinámica de tareas
   - Templating con Jinja

3. **Dominar Operadores y Sensores**
   - Operadores Python, Bash y Docker
   - Operadores de base de datos (Postgres, MySQL)
   - Operadores de nube (S3, GCS, BigQuery)
   - Desarrollo de operadores personalizados
   - Sensores de archivos, API y base de datos

4. **Construir Pipelines ETL Reales**
   - Ingesta de API a base de datos
   - Carga de CSV a data warehouse
   - Exportación de base de datos a data lake
   - Integración de datos multi-fuente
   - ETL incremental con change data capture

5. **Implementar Monitoreo y Alertas**
   - Seguimiento de SLA y violaciones
   - Callbacks personalizados (éxito, fallo, reintento)
   - Notificaciones de Slack y email
   - Monitoreo de rendimiento
   - Health checks

6. **Desplegar a Producción**
   - Configuration multi-servicio con Docker Compose
   - Patrones de alta disponibilidad
   - Escalado con CeleryExecutor
   - Gestión de secretos
   - CI/CD para DAGs
   - Estrategias de testing

## 📚 Prerequisites

### Requeridos
- **Module 06**: Fundamentos de ETL (completed)
- **Docker**: 20.10+ con Docker Compose
- **Python**: 3.8 o superior (3.11 recomendado)
- **Sistema**: 8GB RAM, 20GB espacio en disco

### Recomendados
- Cliente PostgreSQL (para exercises de base de datos)
- AWS CLI (para exercises de S3 con LocalStack)
- Comprensión básica de SQL
- Familiaridad con REST APIs

## 🛠️ Stack Tecnológico

| Componente | Versión | Propósito |
|-----------|---------|---------|
| Apache Airflow | 2.8.1 | Plataforma de orquestación de workflows |
| PostgreSQL | 13 | Base de datos de metadatos |
| Redis | latest | Message broker de Celery |
| CeleryExecutor | - | Ejecución distribuida de tareas |
| Python | 3.11 | Desarrollo de DAGs |
| Docker Compose | - | Orquestación multi-servicio |
| pytest | 7.4.3 | Framework de testing |
| Great Expectations | 0.18.8 | Validation de calidad de datos |
| boto3 | latest | AWS SDK (operaciones S3) |

## 🚀 Inicio Rápido

### 1. Configurar Ambiente

```bash
cd module-10-workflow-orchestration

# Ejecutar setup automatizado (instala e inicia todos los servicios)
./scripts/setup.sh
```

### 2. Acceder a la UI de Airflow

- **Airflow Webserver**: http://localhost:8080 (airflow/airflow)
- **Flower (Monitoreo de Celery)**: http://localhost:5555

### 3. Completar Exercises

Navega a través de los exercises en orden (01-06)

### 4. Validar tu Trabajo

```bash
./scripts/validate.sh
```

## 📖 Resumen de Exercises

1. **Primer DAG** (6 tareas) - Creación básica de DAG, programación
2. **Operadores y Sensores** (6 tareas) - Múltiples operadores, sensores
3. **Dependencias de Tareas** (6 tareas) - Ramificación, reglas de activación
4. **Pipelines de Datos** (6 tareas) - Workflows ETL reales
5. **Monitoreo y Alertas** (5 tareas) - Seguimiento de SLA, alertas
6. **Despliegue en Producción** (6 tareas) - Docker, testing, CI/CD

**Tiempo Total**: 20-25 hours

## 🧪 Pruebas

```bash
cd validation
pytest . -v

# Ejecutar categorías específicas
pytest -m dag_validation
pytest -m integration
```

## 📚 Recursos Adicionales

- [Documentación de Apache Airflow](https://airflow.apache.org/docs/)
- [Guía de Mejores Prácticas](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Referencia de API](https://airflow.apache.org/docs/apache-airflow/stable/python-api-ref.html)

## ✅ Checklist de Validation

- [ ] Explicar arquitectura de Airflow
- [ ] Crear DAGs usando TaskFlow API
- [ ] Implementar todas las reglas de activación
- [ ] Usar 5+ tipos de operadores
- [ ] Construir pipeline ETL (API → DB → S3)
- [ ] Configurar monitoreo y alertas
- [ ] Probar DAGs con pytest
- [ ] Desplegar con Docker Compose
- [ ] Todas las 40+ pruebas pasando

---

**Estado**: ✅ Module 100% Completo
**Tiempo Estimado**: 25-34 hours
**Próximo Module**: [Module 11: Infraestructura como Código](../module-11-infrastructure-as-code/README.md)

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
