# Exercise 01: Docker Basics - Tu Primer Container

## 📋 Información General

- **Level**: Básico
- **Duration estimada**: 2-3 hours
- **Prerequisites**:
  - Docker instalado
  - Conocimientos básicos de Python
  - Cuenta AWS (opcional)

## 🎯 Objectives de Aprendizaje

1. Crear tu primera Docker image
2. Escribir Dockerfiles optimizados
3. Multi-stage builds
4. Docker Compose para local development
5. Push image a Amazon ECR

---

## 📚 Context

Crearás una aplicación ETL simple containerizada que:

- Read archivos CSV de S3 (o local)
- Procesa con pandas
- Write resultados a PostgreSQL
- Todo dockerizado con Docker Compose

**Arquitectura**:

```text
┌──────────────────────────────────────────┐
│      Docker Compose Stack                │
├──────────────────────────────────────────┤
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  ETL Container                     │  │
│  │  (Python + pandas)                 │  │
│  │  Reads: /data/input/*.csv          │  │
│  │  Writes: PostgreSQL                │  │
│  └────────────┬───────────────────────┘  │
│               │                           │
│               ▼                           │
│  ┌────────────────────────────────────┐  │
│  │  PostgreSQL Container              │  │
│  │  Port: 5432                        │  │
│  │  Volume: postgres_data             │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```text

---

## 🔧 Parte 1: Aplicación ETL

### Step 1.1: Crear ETL Script

Create `etl/app.py`:

```python
"""
Simple ETL Pipeline:
- Extract: Read CSV from /data/input
- Transform: Clean and aggregate
- Load: Write to PostgreSQL
"""
import os
import sys
import pandas as pd
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'postgres'),
            port=os.environ.get('DB_PORT', '5432'),
            database=os.environ.get('DB_NAME', 'analytics'),
            user=os.environ.get('DB_USER', 'dataeng'),
            password=os.environ.get('DB_PASSWORD', 'secret123')
        )
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def create_tables(conn):
    """Create necessary tables"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_summary (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            total_sales DECIMAL(12, 2),
            total_orders INTEGER,
            avg_order_value DECIMAL(10, 2),
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date)
        )
    """)

    conn.commit()
    cursor.close()
    logger.info("Tables created successfully")


def extract_data(input_path='/data/input'):
    """Extract CSV files"""
    logger.info(f"Extracting data from {input_path}")

    csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]

    if not csv_files:
        logger.warning(f"No CSV files found in {input_path}")
        return None

    dfs = []
    for csv_file in csv_files:
        file_path = os.path.join(input_path, csv_file)
        logger.info(f"Reading {csv_file}")
        df = pd.read_csv(file_path)
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    logger.info(f"Extracted {len(result)} rows from {len(csv_files)} files")

    return result


def transform_data(df):
    """Transform and aggregate data"""
    logger.info("Transforming data")

    # Convert date column
    df['order_date'] = pd.to_datetime(df['order_date'])

    # Calculate order value
    df['order_value'] = df['quantity'] * df['price']

    # Remove invalid data
    df = df[df['order_value'] > 0]
    df = df.dropna()

    # Aggregate by date
    summary = df.groupby(df['order_date'].dt.date).agg({
        'order_value': 'sum',
        'order_id': 'count',
    }).reset_index()

    summary.columns = ['date', 'total_sales', 'total_orders']
    summary['avg_order_value'] = summary['total_sales'] / summary['total_orders']

    logger.info(f"Transformed to {len(summary)} daily summaries")

    return summary


def load_data(df, conn):
    """Load data to PostgreSQL"""
    logger.info("Loading data to database")

    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO sales_summary (date, total_sales, total_orders, avg_order_value)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                total_sales = EXCLUDED.total_sales,
                total_orders = EXCLUDED.total_orders,
                avg_order_value = EXCLUDED.avg_order_value,
                processed_at = CURRENT_TIMESTAMP
        """, (
            row['date'],
            row['total_sales'],
            row['total_orders'],
            row['avg_order_value']
        ))

    conn.commit()
    cursor.close()

    logger.info(f"Loaded {len(df)} rows to database")


def main():
    """Main ETL pipeline"""
    logger.info("="*50)
    logger.info("Starting ETL Pipeline")
    logger.info("="*50)

    try:
        # Extract
        df = extract_data()

        if df is None or len(df) == 0:
            logger.warning("No data to process")
            return

        # Transform
        summary = transform_data(df)

        # Connect to database
        conn = get_db_connection()
        create_tables(conn)

        # Load
        load_data(summary, conn)

        conn.close()

        logger.info("="*50)
        logger.info("ETL Pipeline completed successfully!")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```text

### Step 1.2: Requirements

Create `etl/requirements.txt`:

```txt
pandas==2.1.0
psycopg2-binary==2.9.7
sqlalchemy==2.0.20
```

---

## 🐳 Parte 2: Dockerfile

### Step 2.1: Dockerfile Simple

Create `etl/Dockerfile`:

```dockerfile
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Run ETL
CMD ["python", "app.py"]
```text

### Step 2.2: Build y Run

```bash
# Build image
docker build -t data-etl:v1.0 etl/

# Run container (will fail without database)
docker run --rm data-etl:v1.0
```text

---

## 🚀 Parte 3: Multi-Stage Build (Optimización)

### Step 3.1: Optimized Dockerfile

Create `etl/Dockerfile.optimized`:

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages to user directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY --chown=appuser:appuser app.py .

# Update PATH
ENV PATH=/root/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check (for future use with orchestrator)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

CMD ["python", "app.py"]
```text

### Step 3.2: Build Optimizado

```bash
# Build with optimized Dockerfile
docker build -f etl/Dockerfile.optimized -t data-etl:v2.0 etl/

# Compare image sizes
docker images | grep data-etl

# Output:
# data-etl   v1.0   500MB
# data-etl   v2.0   280MB  (44% reduction!)
```

---

## 🐘 Parte 4: Docker Compose Stack

### Step 4.1: docker-compose.yml

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: analytics_db
    environment:
      POSTGRES_DB: analytics
      POSTGRES_USER: dataeng
      POSTGRES_PASSWORD: secret123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dataeng -d analytics"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - data_network

  # ETL Application
  etl:
    build:
      context: ./etl
      dockerfile: Dockerfile.optimized
    container_name: etl_job
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: analytics
      DB_USER: dataeng
      DB_PASSWORD: secret123
    volumes:
      - ./data/input:/data/input:ro
      - ./data/output:/data/output
    networks:
      - data_network
    restart: "no"  # Run once

  # pgAdmin (optional - for database management)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin123
    ports:
      - "8080:80"
    depends_on:
      - postgres
    networks:
      - data_network

volumes:
  postgres_data:

networks:
  data_network:
    driver: bridge
```text

### Step 4.2: Sample Data

Create `data/input/sales_2024_01.csv`:

```csv
order_id,order_date,product,quantity,price
1001,2024-01-01,Laptop,1,1200.00
1002,2024-01-01,Mouse,2,25.00
1003,2024-01-02,Keyboard,1,75.00
1004,2024-01-02,Monitor,1,300.00
1005,2024-01-03,Laptop,2,1200.00
1006,2024-01-03,USB Cable,5,10.00
```text

### Step 4.3: Run Stack

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f etl

# Expected output:
# etl_job | 2024-01-15 10:00:00 - Starting ETL Pipeline
# etl_job | 2024-01-15 10:00:01 - Extracted 6 rows from 1 files
# etl_job | 2024-01-15 10:00:02 - Transformed to 3 daily summaries
# etl_job | 2024-01-15 10:00:03 - Loaded 3 rows to database
# etl_job | 2024-01-15 10:00:04 - ETL Pipeline completed successfully!

# Check database
docker-compose exec postgres psql -U dataeng -d analytics -c "SELECT * FROM sales_summary;"

# Stop stack
docker-compose down

# Stop and remove volumes
docker-compose down -v
```text

---

## 📤 Parte 5: Push to Amazon ECR

### Step 5.1: Create ECR Repository

```bash
# Create repository
aws ecr create-repository \
  --repository-name data-etl \
  --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com
```

### Step 5.2: Tag and Push

```bash
# Tag image
docker tag data-etl:v2.0 \
  123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:v2.0

docker tag data-etl:v2.0 \
  123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:latest

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:v2.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:latest

# Verify
aws ecr describe-images \
  --repository-name data-etl \
  --region us-east-1
```text

---

## ✅ Validation

### 1. Image Build Success

```bash
docker images data-etl:v2.0
# Should show image with size ~280MB
```text

### 2. Docker Compose Stack Runs

```bash
docker-compose ps
# All services should be running/exited (etl)
docker-compose logs etl | grep "completed successfully"
# Should show success message
```text

### 3. Data in Database

```bash
docker-compose exec postgres psql -U dataeng -d analytics -c \
  "SELECT COUNT(*) FROM sales_summary;"
# Should return 3 rows
```

### 4. ECR Push Success

```bash
aws ecr list-images --repository-name data-etl
# Should show v2.0 and latest tags
```text

---

## 🎓 Conceptos Aprendidos

✅ **Docker Basics**:

- Dockerfile syntax
- Build process y layers
- Image tagging

✅ **Multi-Stage Builds**:

- Separar build y runtime
- Image size optimization
- Security (non-root user)

✅ **Docker Compose**:

- Multi-container applications
- Service dependencies
- Volume management
- Network isolation

✅ **AWS ECR**:

- Container registry management
- Authentication
- Image push/pull

---

## 🔍 Troubleshooting

### Error: ETL cannot connect to database

```bash
# Check if postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres

# Verify network
docker network inspect docker-basics_data_network
```text

### Error: Permission denied in container

```dockerfile
# Ensure proper ownership in Dockerfile
COPY --chown=appuser:appuser app.py .
USER appuser
```text

### Error: No space left on device

```bash
# Clean up Docker
docker system prune -a --volumes
```

---

## 📚 Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/ecr/)

---

**Próximo exercise**: [02 - ECS Fargate Deployment](../02-ecs-fargate-deployment/) donde desplegarás este container en AWS ECS.
