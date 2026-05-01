# Infrastructure Configuration

Este directorio contiene la configuración de infraestructura necesaria para ejecutar los ejercicios del Module 01.

## 📦 Contenido

### docker-compose.yml

Configuración de LocalStack para simular servicios AWS localmente.

**Servicios incluidos:**
- S3 (buckets, objects, versioning, lifecycle)
- IAM (users, groups, roles, policies)
- Lambda (functions, triggers)
- SQS (queues, messages)
- CloudWatch (logs, metrics)
- CloudFormation (stacks, templates)
- SNS (topics, subscriptions)
- EventBridge (events, rules)

**Uso:**

```bash
# Iniciar LocalStack
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado
curl http://localhost:4566/_localstack/health

# Detener
docker-compose down

# Limpiar datos
docker-compose down -v
rm -rf ./localstack-data/*
```

## 🔧 Configuración

### Variables de Entorno

```bash
# AWS CLI
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Verificar
aws s3 ls --endpoint-url=$AWS_ENDPOINT_URL
```

### Python/boto3

```python
import boto3

# Opción 1: Cliente con endpoint
s3 = boto3.client('s3', endpoint_url='http://localhost:4566')

# Opción 2: Variable de entorno
import os
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
s3 = boto3.client('s3')
```

## 📊 Persistencia de Datos

Los datos de LocalStack se guardan en `./localstack-data/` para persistencia entre reinicios.

**Estructura:**
```
localstack-data/
├── s3/           # Buckets y objetos
├── logs/         # CloudWatch logs
├── lambda/       # Funciones Lambda
└── ...
```

## 🚀 Inicio Rápido

```bash
# 1. Iniciar infraestructura
docker-compose up -d

# 2. Esperar a que esté listo (30 segundos)
sleep 30

# 3. Verificar salud
docker-compose ps
curl http://localhost:4566/_localstack/health | jq

# 4. Ejecutar setup
cd ..
./scripts/setup.sh

# 5. Correr ejercicios
cd exercises/01-s3-basics/starter
./s3_operations.sh
```

## 🔍 Troubleshooting

### LocalStack no inicia

```bash
# Verificar Docker
docker ps

# Ver logs
docker-compose logs localstack

# Reiniciar
docker-compose restart
```

### Puerto 4566 en uso

```bash
# Encontrar proceso
sudo lsof -i :4566

# Matar proceso
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
ports:
  - "4567:4566"  # Usar puerto 4567 externamente
```

### Datos corruptos

```bash
# Limpiar y reiniciar
docker-compose down -v
rm -rf ./localstack-data/*
docker-compose up -d
```

## 📚 Referencias

- [LocalStack Docs](https://docs.localstack.cloud/)
- [Docker Compose](https://docs.docker.com/compose/)
- [AWS CLI con LocalStack](https://docs.localstack.cloud/user-guide/integrations/aws-cli/)
