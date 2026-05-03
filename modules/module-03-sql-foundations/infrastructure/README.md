# Infrastructure Configuration

This directory contains the infrastructure configuration for the SQL Fundamentals module, including a PostgreSQL database running in Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Required Software

1. **Docker Desktop** (or Docker Engine + Docker Compose)
   - Download: https://www.docker.com/products/docker-desktop
   - Version: 20.10+ recommended

2. **Optional: PostgreSQL Client**
   - **psql**: Command-line client (comes with PostgreSQL)
   - **pgAdmin**: GUI client (can use dockerized version)
   - **DBeaver**: Universal database client
   - **DataGrip**: JetBrains SQL IDE

### System Requirements

- **RAM**: 2GB minimum (4GB recommended)
- **Disk Space**: 2GB for Docker images and data
- **Ports**: 5432 (PostgreSQL), 5050 (pgAdmin, optional)

---

## Quick Start

### 1. Configurar Entorno

Copiar el archivo de entorno de ejemplo y personalizar si es necesario:

```bash
# Desde el directorio infrastructure/
cp .env.example .env

# Editar .env si necesitas cambiar valores por defecto
nano .env  # o tu editor preferido
```

**Valores por defecto**:
- database: `ecommerce`
- Usuario: `dataengineer`
- Password:`training123`
- Puerto: `5432`

### 2. Iniciar PostgreSQL

```bash
# Iniciar contenedor PostgreSQL
docker-compose up -d

# Verify logs to confirm initialization
docker-compose logs -f postgres

# Esperar por "database system is ready to accept connections"
```

**What happens**:
1. Descarga imagen PostgreSQL 15 Alpine (~80MB)
2. Crea contenedor llamado `sql-foundations-postgres`
3. Crea volumen persistente para datos
4. Ejecuta `init.sql` para crear esquema y datos de muestra
5. Configura ajustes de performance

### 3. Verify Connection

```bash
# Test connection with psql
docker exec -it sql-foundations-postgres psql -U dataengineer -d ecommerce

# Or from host (if psql is installed)
psql -h localhost -p 5432 -U dataengineer -d ecommerce
# Password: training123

# Quick test query
\dt  # List tables
SELECT COUNT(*) FROM users;  # Should return 50
\q   # Salir
```

### 4. Opcional: Iniciar pgAdmin GUI

```bash
# Iniciar con pgAdmin incluido
docker-compose --profile gui up -d

# Acceder a pgAdmin en: http://localhost:5050
# Email: admin@training.local
# Password: admin123
```

**Agregar server en pgAdmin**:
1. Click derecho "Servers" → "Register" → "Server"
2. Nombre: `SQL Foundations`
3. Connection tab:
   - Host: `postgres` (si conectas desde contenedor pgAdmin)
   - Host: `localhost` (si pgAdmin corre fuera de Docker)
   - Port: `5432`
   - Database: `ecommerce`
   - User: `dataengineer`
   - Password: `training123`

---

## Esquema de database

### Tables

#### 1. **users**
User account information.

| Column | Type | Description |
|--------|------|-------------|
| user_id | SERIAL PK | Unique identifier |
| email | VARCHAR(255) | User email (unique) |
| first_name | VARCHAR(100) | First name |
| last_name | VARCHAR(100) | Last name |
| country | VARCHAR(2) | ISO country code |
| city | VARCHAR(100) | City name |
| registration_date | DATE | Sign-up date |
| last_login | TIMESTAMP | Last login time |
| is_active | BOOLEAN | Account status |
| loyalty_points | INTEGER | Reward points |

**Sample size**: 50 users

#### 2. **products**
Product catalog.

| columns | Type | Description |
|--------|------|-------------|
| product_id | SERIAL PK | Unique identifier |
| product_name | VARCHAR(255) | Nombre del producto |
| category | VARCHAR(50) | Product Category |
| price | DECIMAL(10,2) | Precio del producto |
| stock_quantity | INTEGER | Stock disponible |
| description | TEXT | Product Description |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| is_available | BOOLEAN | Estado de availability |

**Sample size**: 50 products
**Categories**: Electronics, Books, Furniture, Sports, Home, Accessories

#### 3. **orders**
Customer orders.

| columns | Type | Description |
|--------|------|-------------|
| order_id | SERIAL PK | Unique identifier |
| user_id | INTEGER FK | Referencia a users |
| order_date | TIMESTAMP | Order placement time |
| total_amount | DECIMAL(10,2) | Valor total de orden |
| status | VARCHAR(20) | Estado de orden |
| shipping_address | TEXT | Delivery address |
| payment_method | VARCHAR(50) | Tipo de pago |

**Sample size**: 200 orders
**Estados**: pending, processing, shipped, delivered, cancelled

#### 4. **order_items**
Products in each order (union table).

| columns | Type | Description |
|--------|------|-------------|
| order_item_id | SERIAL PK | Unique identifier |
| order_id | INTEGER FK | Referencia a orders |
| product_id | INTEGER FK | Referencia a products |
| quantity | INTEGER | Cantidad ordenada |
| unit_price | DECIMAL(10,2) | Precio por unidad |
| subtotal | DECIMAL(10,2) | Line Total |

**Sample size**: ~600 order items (2-5 per order)

#### 5. **user_activity**
Registro de actividad de usuarios.

| columns | Type | Description |
|--------|------|-------------|
| activity_id | SERIAL PK | Unique identifier |
| user_id | INTEGER FK | Referencia a users |
| activity_type | VARCHAR(50) | Tipo de actividad |
| activity_timestamp | TIMESTAMP | When the activity occurred |
| product_id | INTEGER FK | Producto relacionado (opcional) |
| details | JSONB | Additional metadata |

**Sample size**: 1,000 activities
**Tipos**: login, logout, view_product, add_to_cart, purchase, review

### Vistas

#### v_order_summary
Order details with user information.
```sql
SELECT * FROM v_order_summary LIMIT 10;
```

#### v_product_sales
Agregados de ventas de productos.
```sql
SELECT * FROM v_product_sales ORDER BY total_revenue DESC;
```

#### v_user_summary
Resumen de historial de compras de usuario.
```sql
SELECT * FROM v_user_summary WHERE total_orders > 5;
```

### indexes

- **users**: email, country, registration_date, is_active
- **products**: category, price, name (trigram for fuzzy search)
- **orders**: user_id, order_date, status, (user_id, order_date) compuesto
- **order_items**: order_id, product_id
- **user_activity**: user_id, activity_timestamp, activity_type, details (GIN)

### Funciones

#### calculate_loyalty_points(amount)
Calcular puntos de lealtad para monto de orden.
```sql
SELECT calculate_loyalty_points(150.00);  -- Retorna 15
```

#### get_top_products_by_category(category, limit)
Get best-selling products by category.
```sql
SELECT * FROM get_top_products_by_category('Electronics', 5);
```

---

## Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Database
POSTGRES_DB=ecommerce           # Database name
POSTGRES_USER=dataengineer      # Username
POSTGRES_PASSWORD=training123   # Password (change for production!)
POSTGRES_PORT=5432              # Host port

# pgAdmin (optional)
PGADMIN_EMAIL=admin@training.local
PGADMIN_PASSWORD=admin123
PGADMIN_PORT=5050
```

### Performance Tuning

Current settings in `docker-compose.yml`:

```yaml
shared_buffers: 256MB        # Cache for data pages
effective_cache_size: 1GB    # OS cache estimate
work_mem: 8MB                # Memory per operation
maintenance_work_mem: 128MB  # Memory for maintenance
max_connections: 100         # Connection limit
```

**Adjust for your system**:
- **8GB RAM**: Double the values
- **16GB+ RAM**: Quadruple the values
- **SSD**: Set `random_page_cost=1.1` (already set)
- **HDD**: Set `random_page_cost=4.0`

### Custom PostgreSQL Configuration

Para usar `postgresql.conf` personalizado:

1. Crear `postgresql.conf` en infrastructure/
2. Descomentar volumen en `docker-compose.yml`:
   ```yaml
   - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
   ```
3. Agregar al comando:
   ```yaml
   - "-c"
   - "config_file=/etc/postgresql/postgresql.conf"
   ```

---

## Usage

### Common Docker Commands

```bash
# Start services
docker-compose up -d

# Start with pgAdmin
docker-compose --profile gui up -d

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down

# Stop and remove volumes (deletes all data!)
docker-compose down -v

# Restart services
docker-compose restart

# Check status
docker-compose ps

# Execute command in container
docker exec -it sql-foundations-postgres psql -U dataengineer -d ecommerce
```

### Conectar desde Python

#### Usando psycopg2

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="ecommerce",
    user="dataengineer",
    password="training123"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM users")
print(cursor.fetchone())

cursor.close()
conn.close()
```

#### Usando SQLAlchemy

```python
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('postgresql://dataengineer:training123@localhost:5432/ecommerce')

# Consulta a DataFrame
df = pd.read_sql("SELECT * FROM users LIMIT 10", engine)
print(df)
```

### Connect from Command Line

```bash
# psql
psql -h localhost -p 5432 -U dataengineer -d ecommerce

# With password in command (not recommended)
PGPASSWORD=training123 psql -h localhost -p 5432 -U dataengineer -d ecommerce

# Connection string
psql "postgresql://dataengineer:training123@localhost:5432/ecommerce"
```

### Useful psql commands

```sql
-- List databases
\l

-- Listar tablas
\dt

-- Describir tabla
\d users

-- List indexes
\di

-- Listar vistas
\dv

-- Listar funciones
\df

-- Show current database
\conninfo

-- Execute SQL file
\i /path/to/file.sql

-- Establecer formato de salida
\x  -- Display expandido (vertical)
\a  -- Unaligned output (no padding)
\t  -- Solo tuplas (sin encabezados)

-- Timing
\timing on

-- Salir
\q
```

---

## Troubleshooting

### Port Already in Use

**Error**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Solution**:
1. Change port in `.env`:
   ```bash
   POSTGRES_PORT=5433
   ```
2. Restart:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
3. Connect using new port:
   ```bash
   psql -h localhost -p 5433 -U dataengineer -d ecommerce
   ```

### Container Won't Start

**Check logs**:
```bash
docker-compose logs postgres
```

**Common issues**:
- Insufficient memory (increase Docker RAM)
- Corrupted data volume (remove with `docker-compose down -v`)
- Permission problems (run `docker-compose down -v` and try again)

### Cannot Connect

**Verify which container is running**:
```bash
docker-compose ps
```

**Verify health**:
```bash
docker inspect sql-foundations-postgres | grep Health
```

**Test from inside the container**:
```bash
docker exec -it sql-foundations-postgres psql -U dataengineer -d ecommerce -c "SELECT 1"
```

**Firewall issues**:
- Ensure Docker has firewall exceptions
- On Linux, check `ufw` or `iptables`

### Database Not Initialized

If tables are missing:

1. Verify whether `init.sql` was executed:
   ```bash
   docker-compose logs postgres | grep "initialization"
   ```

2. Reinitialize:
   ```bash
   docker-compose down -v  # Deletes volumes!
   docker-compose up -d
   ```

### queries Lentas

**Run ANALYZE**:
```sql
ANALYZE;
```

**Verificar plan de query**:
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE country = 'US';
```

**Increase cache**:
Editar `docker-compose.yml` y aumentar `shared_buffers` y `effective_cache_size`.

---

## Advanced Settings

### Location of Persistent Data

Data is stored in Docker volume: `sql-foundations-postgres-data`

**Find volume location**:
```bash
docker volume inspect sql-foundations-postgres-data
```

**Back up data**:
```bash
# Dump database
docker exec -t sql-foundations-postgres pg_dump -U dataengineer ecommerce > backup.sql

# Restore database
docker exec -i sql-foundations-postgres psql -U dataengineer -d ecommerce < backup.sql
```

### Multiple Environments

Crear archivos `.env` separados:

```bash
# Desarrollo
docker-compose --env-file .env.dev up -d

# Production (do not commit!)
docker-compose --env-file .env.prod up -d
```

### Connection Pooling

For production, use **pgBouncer**:

Agregar a `docker-compose.yml`:
```yaml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    DATABASES_USER: dataengineer
    DATABASES_PASSWORD: training123
    DATABASES_DBNAME: ecommerce
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
    PGBOUNCER_DEFAULT_POOL_SIZE: 20
  ports:
    - "6432:5432"
  depends_on:
    - postgres
```

Conectar a pgBouncer en puerto 6432 en lugar de 5432.

### Conexiones SSL/TLS

For production, enable SSL:

1. Generar certificados
2. Montar en contenedor
3. Agregar a `postgresql.conf`:
   ```
   ssl = on
   ssl_cert_file = '/path/to/server.crt'
   ssl_key_file = '/path/to/server.key'
   ```

### Monitoreo

**Check statistics**:
```sql
-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public';

-- Cache hit rate
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))::float as cache_hit_ratio
FROM pg_statio_user_tables;

-- Conexiones activas
SELECT count(*) FROM pg_stat_activity;
```

---

## resources Adicionales

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/15/
- **Referencia Docker Compose**: https://docs.docker.com/compose/
- **Referencia de Comandos psql**: https://www.postgresql.org/docs/15/app-psql.html
- **Ajuste de performance**: https://wiki.postgresql.org/wiki/Performance_Optimization

---

## Do you need help?

1. Check logs: `docker-compose logs postgres`
2. Verify connection: Try with `psql` from inside the container
3. Review section [Troubleshooting](#troubleshooting)
4. See `theory/architecture.md` for query optimization tips
5. Consult PostgreSQL documentation for specific errors

---

**Last Update**: February 2, 2026
**PostgreSQL version**: 15
**Docker Compose version**: 3.8
