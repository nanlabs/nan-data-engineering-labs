# Docker Fundamentals para Data Engineering

## 📋 Índice

1. [Conceptos de Containerización](#conceptos-containerización)
2. [Docker Architecture](#docker-architecture)
3. [Images y Containers](#images-containers)
4. [Dockerfile Best Practices](#dockerfile-best-practices)
5. [Docker Compose](#docker-compose)
6. [Networking y Storage](#networking-storage)
7. [Security](#security)

---

## 1. Conceptos de Containerización

### ¿Qué es un Container?

Un **container** es una unidad estándar de software que empaqueta código y todas sus dependencias para que una aplicación se ejecute de forma rápida y confiable de un entorno a otro.

**Diferencias clave:**

| Aspecto | Containers | Virtual Machines |
|---------|-----------|------------------|
| **Tamaño** | MB | GB |
| **Startup** | Segundos | Minutos |
| **Performance** | Nativo | Overhead |
| **Isolation** | Process-level | Hardware-level |
| **Portability** | Alta | Media |

### Beneficios para Data Engineering

```
✅ Reproducibilidad
   - Mismo entorno en dev, test, prod
   - Versiones específicas de librerías (pandas, spark)

✅ Isolation
   - Múltiples versiones de Python en mismo host
   - Dependencias conflictivas aisladas

✅ Portability
   - Docker image funciona en cualquier lugar
   - On-prem → Cloud migration simplificada

✅ Scalability
   - Horizontal scaling fácil
   - Orquestación con ECS/Kubernetes

✅ CI/CD
   - Build once, deploy anywhere
   - Deployment automation
```

### Casos de Uso en Data Engineering

1. **ETL Pipelines**: Airflow, dbt, custom scripts
2. **Data Processing**: Spark jobs, batch processing
3. **Databases**: PostgreSQL, MongoDB, Redis
4. **Streaming**: Kafka, Flink, Kinesis consumers
5. **ML Models**: Model serving (FastAPI + ML model)
6. **Development**: Jupyter notebooks con dependencias

---

## 2. Docker Architecture

### Componentes Principales

```
┌──────────────────────────────────────────┐
│         Docker Architecture               │
├──────────────────────────────────────────┤
│                                           │
│  ┌────────────────────────────────────┐  │
│  │       Docker Client (CLI)          │  │
│  │  $ docker run, build, push, etc    │  │
│  └────────────┬───────────────────────┘  │
│               │ REST API                  │
│               ▼                           │
│  ┌────────────────────────────────────┐  │
│  │       Docker Daemon (dockerd)      │  │
│  │  - Manages images, containers      │  │
│  │  - Networking, volumes             │  │
│  └────────────┬───────────────────────┘  │
│               │                           │
│     ┌─────────┴──────────┐               │
│     │                    │               │
│     ▼                    ▼               │
│  ┌────────┐         ┌────────┐           │
│  │ Images │         │Registry│           │
│  │        │         │ (ECR)  │           │
│  └───┬────┘         └────────┘           │
│      │                                    │
│      ▼                                    │
│  ┌────────────┐                          │
│  │ Containers │                          │
│  │ (Running)  │                          │
│  └────────────┘                          │
└──────────────────────────────────────────┘
```

### Docker Image Layers

Las images son **read-only layers** apiladas:

```dockerfile
# Layer 1: Base OS
FROM python:3.11-slim

# Layer 2: System dependencies
RUN apt-get update && apt-get install -y postgresql-client

# Layer 3: Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Layer 4: Application code
COPY . /app

# Layer 5: Metadata
WORKDIR /app
CMD ["python", "app.py"]
```

Cada instrucción (`FROM`, `RUN`, `COPY`) crea una nueva layer:

```
Image ID: sha256:abc123...
├── Layer 5: CMD ["python", "app.py"]       (metadata)
├── Layer 4: COPY . /app                    (10 MB)
├── Layer 3: RUN pip install...             (300 MB)
├── Layer 2: RUN apt-get install...         (50 MB)
└── Layer 1: FROM python:3.11-slim          (150 MB)
                                    Total: ~510 MB
```

**Ventajas**:
- **Cache**: Layers no cambiadas se reutilizan
- **Sharing**: Múltiples images comparten base layers
- **Efficiency**: Sólo capas modificadas se transfieren

---

## 3. Images y Containers

### Creando tu Primera Image

**Ejemplo: ETL Script con Pandas**

`etl_script.py`:

```python
import pandas as pd
import psycopg2
from datetime import datetime

def extract_data():
    """Extract data from PostgreSQL"""
    conn = psycopg2.connect(
        host="db",
        database="sales",
        user="etl_user",
        password="secret"
    )

    query = """
    SELECT * FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print(f"Extracted {len(df)} rows")
    return df

def transform_data(df):
    """Transform data"""
    # Agregar columnas
    df['total_amount'] = df['quantity'] * df['price']
    df['processed_at'] = datetime.utcnow()

    # Limpiar datos
    df = df.dropna()
    df = df[df['total_amount'] > 0]

    print(f"Transformed to {len(df)} rows")
    return df

def load_data(df):
    """Load to CSV (simulated)"""
    output_file = f"/output/sales_{datetime.utcnow().date()}.csv"
    df.to_csv(output_file, index=False)
    print(f"Loaded to {output_file}")

if __name__ == "__main__":
    print("Starting ETL pipeline...")
    df = extract_data()
    df = transform_data(df)
    load_data(df)
    print("ETL completed successfully!")
```

`Dockerfile`:

```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY etl_script.py .

# Create output directory
RUN mkdir -p /output

# Run ETL script
CMD ["python", "etl_script.py"]
```

`requirements.txt`:

```
pandas==2.1.0
psycopg2-binary==2.9.7
sqlalchemy==2.0.20
```

### Build y Run

```bash
# Build image
docker build -t my-etl:v1.0 .

# Ver images
docker images

# Run container
docker run --name etl-job \
  -v $(pwd)/output:/output \
  --network my-network \
  my-etl:v1.0

# Ver logs
docker logs etl-job

# Ver containers corriendo
docker ps

# Ver todos los containers (incluye stopped)
docker ps -a

# Remover container
docker rm etl-job
```

### Multi-Stage Builds

Reduce image size con multi-stage builds:

```dockerfile
# ============================================
# Stage 1: Build
# ============================================
FROM python:3.11 AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make

# Install Python packages
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY etl_script.py .

# Update PATH
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "etl_script.py"]
```

**Ventajas**:
- Image builder: 1.2 GB
- Image final: 350 MB (70% reducción)

---

## 4. Dockerfile Best Practices

### 1. Order Matters (Cache Optimization)

❌ **Mal**: Code changes invalidan cache de dependencies

```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

✅ **Bien**: Dependencies cached, solo code rebuilds

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Dependencies first (rarely change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code last (changes frequently)
COPY . .

CMD ["python", "app.py"]
```

### 2. Minimize Layers

❌ **Mal**: Muchos RUN statements

```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN apt-get install -y vim
```

✅ **Bien**: Combinar en un RUN

```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    && rm -rf /var/lib/apt/lists/*
```

### 3. Use .dockerignore

`.dockerignore`:

```
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
venv/
.env

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/
*.swp

# Data files (don't include in image)
data/
*.csv
*.parquet

# Logs
logs/
*.log

# Documentation
README.md
docs/
```

### 4. Non-Root User (Security)

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

CMD ["python", "app.py"]
```

### 5. Health Checks

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install flask

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "api.py"]
```

### 6. ARG vs ENV

```dockerfile
# ARG: Build-time variables
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

# ENV: Runtime variables
ENV APP_ENV=production \
    LOG_LEVEL=info \
    DATABASE_URL=postgresql://db:5432/mydb

WORKDIR /app

# ARG for build config
ARG INSTALL_DEV_DEPS=false

COPY requirements.txt .
RUN pip install -r requirements.txt

# Conditional install
RUN if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      pip install pytest black flake8; \
    fi

COPY . .

CMD ["python", "app.py"]
```

Build with arguments:

```bash
# Production build
docker build -t my-app:prod .

# Development build
docker build \
  --build-arg INSTALL_DEV_DEPS=true \
  -t my-app:dev .
```

---

## 5. Docker Compose

Para aplicaciones multi-container, Docker Compose simplifica la orquestación.

### Ejemplo: Data Pipeline Stack

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: analytics_db
    environment:
      POSTGRES_DB: analytics
      POSTGRES_USER: dataeng
      POSTGRES_PASSWORD: secret123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dataeng"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: redis_cache
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # ETL Service
  etl:
    build:
      context: ./etl
      dockerfile: Dockerfile
    container_name: etl_service
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://dataeng:secret123@postgres:5432/analytics
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: info
    volumes:
      - ./data:/data
      - ./output:/output
    networks:
      - data_network

  # Jupyter Notebook
  jupyter:
    image: jupyter/pyspark-notebook:latest
    container_name: jupyter_lab
    ports:
      - "8888:8888"
    environment:
      JUPYTER_ENABLE_LAB: "yes"
    volumes:
      - ./notebooks:/home/jovyan/work
      - ./data:/home/jovyan/data
    networks:
      - data_network

  # Airflow (simplified)
  airflow:
    image: apache/airflow:2.7.0
    container_name: airflow_scheduler
    depends_on:
      - postgres
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://dataeng:secret123@postgres/airflow
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
    ports:
      - "8080:8080"
    command: standalone
    networks:
      - data_network

volumes:
  postgres_data:
  redis_data:

networks:
  data_network:
    driver: bridge
```

### Comandos Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f etl

# Scale service
docker-compose up -d --scale etl=3

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild services
docker-compose build --no-cache

# Execute command in running service
docker-compose exec postgres psql -U dataeng analytics
```

---

## 6. Networking y Storage

### Docker Networks

**Tipos de networks**:

1. **Bridge** (default): Containers en mismo host
2. **Host**: Container usa network stack del host
3. **None**: Sin networking
4. **Overlay**: Multi-host networking (Swarm/K8s)

```bash
# Create custom network
docker network create data-network

# Run containers in network
docker run -d --name db \
  --network data-network \
  postgres:15

docker run -d --name app \
  --network data-network \
  my-app:latest

# Containers can communicate by name:
# postgresql://db:5432/mydb
```

### Docker Volumes

**Tipos de storage**:

1. **Volumes**: Managed by Docker (recommended)
2. **Bind Mounts**: Mount host directory
3. **tmpfs**: In-memory (no persistence)

```bash
# Named volume
docker volume create pgdata

docker run -d \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15

# Bind mount (development)
docker run -d \
  -v $(pwd)/code:/app \
  -v $(pwd)/data:/data \
  my-etl:latest

# Inspect volume
docker volume inspect pgdata

# List volumes
docker volume ls

# Remove unused volumes
docker volume prune
```

### Ejemplo: Data Pipeline con Volumes

```bash
# Create volume for processed data
docker volume create processed_data

# Run ETL job
docker run \
  --name etl-job \
  -v $(pwd)/raw_data:/input:ro \
  -v processed_data:/output \
  -e DATABASE_URL=postgresql://db:5432/analytics \
  --network data-network \
  my-etl:v1.0

# Run another container to access processed data
docker run -it \
  -v processed_data:/data:ro \
  python:3.11 \
  python -c "import pandas as pd; print(pd.read_csv('/data/result.csv'))"
```

---

## 7. Security Best Practices

### 1. Image Scanning

```bash
# Scan with Docker Scout
docker scout cves my-app:latest

# Scan with Trivy
docker run aquasec/trivy image my-app:latest
```

### 2. Non-Root User

```dockerfile
FROM python:3.11-slim

# Create user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install as root
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy files with ownership
COPY --chown=appuser:appuser . .

# Run as non-root
USER appuser

CMD ["python", "app.py"]
```

### 3. Secrets Management

❌ **Never hardcode secrets**:

```dockerfile
# BAD!
ENV DATABASE_PASSWORD=supersecret123
```

✅ **Use Docker secrets or external vault**:

```bash
# Pass secrets at runtime
docker run \
  -e DATABASE_PASSWORD_FILE=/run/secrets/db_password \
  --secret db_password \
  my-app:latest
```

### 4. Read-Only Filesystem

```bash
docker run \
  --read-only \
  --tmpfs /tmp \
  my-app:latest
```

### 5. Resource Limits

```bash
docker run \
  --memory="2g" \
  --memory-swap="2g" \
  --cpus="1.5" \
  --pids-limit=100 \
  my-etl:latest
```

### 6. Network Security

```bash
# Disable inter-container communication
docker network create --internal secure-network

# Run with no network
docker run --network none my-app:latest
```

---

## 🎯 Checklist de Docker para Data Engineering

### Development
- [ ] Dockerfile optimizado con multi-stage builds
- [ ] .dockerignore configurado
- [ ] docker-compose.yml para local development
- [ ] Volumes para código (hot reload)
- [ ] Networks para service communication

### Testing
- [ ] Unit tests en container
- [ ] Integration tests con docker-compose
- [ ] Performance tests con resource limits

### Production
- [ ] Base images oficiales y actualizadas
- [ ] Non-root user
- [ ] Health checks
- [ ] Resource limits
- [ ] Read-only filesystem (cuando posible)
- [ ] Image scanning (vulnerabilities)
- [ ] Secrets management
- [ ] Logging a stdout/stderr
- [ ] Monitoring (Prometheus, CloudWatch)

### CI/CD
- [ ] Automated builds
- [ ] Image tagging (semver)
- [ ] Registry (ECR, Docker Hub)
- [ ] Automated testing
- [ ] Security scanning

---

## 📚 Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker for Data Science](https://www.datacamp.com/tutorial/docker-for-data-science-introduction)

---

**Próximo**: [02 - AWS ECS & Fargate](02-aws-ecs-fargate.md) para desplegar containers en AWS.
