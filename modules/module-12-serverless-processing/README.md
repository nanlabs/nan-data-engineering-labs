# Module 12: Serverless Processing

## 📖 Description

Este module cubre el procesamiento serverless de datos utilizando AWS Lambda, Step Functions y servicios relacionados. You will learn a construir pipelines de datos escalables, event-driven y completamente serverless.

## 🎯 Objectives de Aprendizaje

Al completar este module, serás capaz de:

- ✅ Diseñar arquitecturas serverless para procesamiento de datos
- ✅ Implementar funciones Lambda production-ready con Python
- ✅ Orquestar workflows complejos con AWS Step Functions
- ✅ Construir APIs REST escalables con API Gateway + Lambda
- ✅ Procesar streams en tiempo real con Kinesis
- ✅ Implementar patrones de messaging con SQS/SNS
- ✅ Aplicar observability con CloudWatch y X-Ray
- ✅ Desplegar con CI/CD automation
- ✅ Optimizar costos y performance

## 📋 Prerequisites

- Conocimiento de Python (level intermedio)
- Experiencia con AWS básico (S3, IAM)
- Comprensión de event-driven architecture
- Familiaridad con Terraform
- Git y GitHub básico

## 📚 Estructura del Module

### 📖 Theory (3 archivos)

1. **[01-serverless-fundamentals.md](theory/01-serverless-fundamentals.md)** (~3,500 líneas)
   - Conceptos de serverless computing
   - AWS Lambda fundamentals (handlers, context, lifecycle)
   - Event sources y triggers
   - Cold starts vs warm execution
   - Pricing model y limits
   - Best practices

2. **[02-serverless-data-processing.md](theory/02-serverless-data-processing.md)** (~4,200 líneas)
   - Lambda + S3 file processing patterns
   - AWS Step Functions orchestration
   - Amazon States Language (ASL)
   - EventBridge para event routing
   - Serverless ETL patterns
   - Glue integration
   - Monitoring y observability

3. **[03-serverless-patterns.md](theory/03-serverless-patterns.md)** (~4,800 líneas)
   - Advanced architecture patterns
   - API Gateway integration
   - Security best practices
   - Observability (CloudWatch, X-Ray)
   - CI/CD for serverless
   - Cost optimization strategies
   - Production readiness checklist

### 💻 Practical Exercises (6 exercises)

1. **[01-first-lambda](exercises/01-first-lambda/)** - Básico (2-3 hours)
   - Primera función Lambda
   - S3 event triggers
   - CSV processing con pandas
   - CloudWatch logging
   - Unit testing

2. **[02-s3-event-processing](exercises/02-s3-event-processing/)** - Intermedio (3-4 hours)
   - CSV to Parquet transformation
   - SQS como buffer
   - Dead Letter Queue (DLQ)
   - Data partitioning
   - Glue Data Catalog integration

3. **[03-step-functions](exercises/03-step-functions/)** - Intermedio (3-4 hours)
   - Complete ETL pipeline
   - State machine orchestration
   - Parallel execution
   - Error handling y retry logic
   - EventBridge triggers

4. **[04-rest-api-lambda](exercises/04-rest-api-lambda/)** - Intermedio (3-4 hours)
   - Full CRUD REST API
   - API Gateway + Lambda
   - DynamoDB integration
   - Authentication (API Key)
   - Rate limiting

5. **[05-sqs-messaging](exercises/05-sqs-messaging/)** - Avanzado (2-3 hours)
   - Order processing system
   - SQS FIFO queues
   - Message deduplication
   - Batch processing
   - CloudWatch alarms

6. **[06-production-pipeline](exercises/06-production-pipeline/)** - Avanzado (4-5 hours)
   - Production-ready pipeline
   - Real-time analytics
   - Multi-environment deployment
   - Complete observability
   - CI/CD automation

### 🏗️ Infrastructure

- **[templates/](infrastructure/templates/)** - Modules Terraform reutilizables
  - Lambda function module
  - SQS queue module
  - API Gateway module
  - Step Functions module

### ✅ Validation

- **[validation/](validation/)** - Test suite completo
  - Unit tests con pytest
  - Integration tests con moto
  - Infrastructure tests

### 🛠️ Scripts

- **[setup.sh](scripts/setup.sh)** - Configuration inicial del entorno
- **[deploy.sh](scripts/deploy.sh)** - Deployment automation

## 🚀 Getting Started

See `theory/resources.md` for:
- Official AWS documentation

### 1. Setup del Entorno

```bash
# Clonar repositorio
cd modules/module-12-serverless-processing

# Ejecutar setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activar virtual environment
source venv/bin/activate
```

### 2. Configurar AWS

```bash
# Configurar credenciales
aws configure

# Verificar acceso
aws sts get-caller-identity
```

### 3. Comenzar con la Theory

Lee los archivos de theory en orden:
1. `theory/01-serverless-fundamentals.md`
2. `theory/02-serverless-data-processing.md`
3. `theory/03-serverless-patterns.md`

### 4. Realizar los Exercises

Completa los exercises en orden progresivo:

```bash
# Exercise 1
cd exercises/01-first-lambda
# Seguir instrucciones en README.md

# Exercise 2
cd ../02-s3-event-processing
# ...y así sucesivamente
```

## 📊 Stack Tecnológico

### Core Services
- **AWS Lambda** - Compute serverless
- **API Gateway** - REST APIs
- **Step Functions** - Workflow orchestration
- **EventBridge** - Event routing

### Data Services
- **S3** - Data Lake storage
- **DynamoDB** - NoSQL database
- **Kinesis** - Stream processing
- **Glue Data Catalog** - Metadata management

### Messaging
- **SQS** - Message queuing (Standard & FIFO)
- **SNS** - Pub/Sub messaging

### Observability
- **CloudWatch** - Logs, metrics, dashboards
- **X-Ray** - Distributed tracing

### Infrastructure
- **Terraform** - Infrastructure as Code
- **GitHub Actions** - CI/CD

### Development
- **Python 3.11** - Runtime
- **pytest** - Testing framework
- **moto** - AWS mocking
- **boto3** - AWS SDK

## 🎓 Path de Aprendizaje

```
1. Theory Review (3-4 hours)
   ↓
2. Exercise 01: First Lambda (2-3 hours)
   ↓
3. Exercise 02: S3 Event Processing (3-4 hours)
   ↓
4. Exercise 03: Step Functions (3-4 hours)
   ↓
5. Exercise 04: REST API (3-4 hours)
   ↓
6. Exercise 05: SQS Messaging (2-3 hours)
   ↓
7. Exercise 06: Production Pipeline (4-5 hours)
   ↓
8. Final Project (opcional, 8-10 hours)

Total estimado: 25-30 hours
```

## 📈 Criterios de Evaluación

### Conocimiento Teórico (30%)
- [ ] Comprensión de serverless fundamentals
- [ ] Event-driven architecture patterns
- [ ] AWS Lambda lifecycle y optimizations
- [ ] Step Functions state machines

### Implementación Práctica (40%)
- [ ] 6 exercises completeds
- [ ] Código funcional y bien documentado
- [ ] Infrastructure as Code implementado
- [ ] Tests pasando (>80% coverage)

### Production Readiness (30%)
- [ ] Observability implementada
- [ ] Security best practices aplicadas
- [ ] CI/CD pipeline funcional
- [ ] Cost optimization considerada

## 🔍 Troubleshooting

### Lambda Timeout
```python
# Aumentar timeout en Terraform
timeout = 300  # 5 minutes
```

### Cold Start Issues
```python
# Usar reserved concurrency
reserved_concurrent_executions = 10
```

### Permission Errors
```bash
# Verificar IAM role
aws iam get-role --role-name lambda-role
```

## 📚 Recursos Adicionales

### Documentación Oficial
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [Step Functions Guide](https://docs.aws.amazon.com/step-functions/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)

### Herramientas
- [AWS SAM](https://aws.amazon.com/serverless/sam/) - Serverless Application Model
- [LocalStack](https://localstack.cloud/) - Local AWS testing
- [Serverless Framework](https://www.serverless.com/)

### Libros
- "Serverless Architectures on AWS" - Peter Sbarski
- "Production-Ready Serverless" - Yan Cui

## 🤝 Contribuciones

¿Encontraste un error? ¿Tienes sugerencias?
- Abre un issue en GitHub
- Envía un pull request
- Contacta al instructor

## 📄 Licencia

Este material es parte del Training Cloud Data y está disponible para uso educativo.

---

## Validation

Ejecutar todas las validaciones:

```bash
bash scripts/validate.sh
```

O usar la validation global:

```bash
make validate MODULE=module-12-serverless-processing
```

## Progress Checklist

- [x] Leer toda la documentación teórica
- [x] Completar Exercise 01
- [x] Completar Exercise 02
- [x] Completar Exercise 03
- [x] Completar Exercise 04
- [x] Completar Exercise 05
- [x] Completar Exercise 06
- [x] Todas las validaciones pasando
- [x] Listo para el próximo module

## 🎯 Próximos Steps

Una vez completed este module, continúa con:
- **[Module 13: Container Orchestration](../module-13-container-orchestration/)** - Kubernetes y ECS
- **[Module 15: Real-Time Analytics](../module-15-real-time-analytics/)** - Kinesis Analytics

¡Buena suerte con tu aprendizaje serverless! 🚀


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
