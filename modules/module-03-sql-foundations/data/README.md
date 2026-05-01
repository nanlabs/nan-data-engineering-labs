# Data Directory

This directory contains database schemas, sample data, and migration scripts for the SQL Foundations module.

## 📁 Estructura

```
data/
├── schemas/              # Definiciones DDL de tablas
│   ├── 01_users.sql
│   ├── 02_products.sql
│   ├── 03_orders.sql
│   ├── 04_order_items.sql
│   └── 05_user_activity.sql
├── seeds/                # Datos de muestra en CSV
│   ├── users.csv
│   └── products.csv
├── migrations/           # Scripts de cambios de esquema
│   ├── 001_add_user_preferences.sql
│   ├── 002_add_product_ratings.sql
│   └── 003_add_order_tracking.sql
└── README.md            # Este archivo
```

## 🗄️ Schemas

Los archivos en `schemas/` contienen las definiciones DDL (Data Definition Language) de cada table:

### 01_users.sql
**table**: `users`
**Description**: User account information
**columns clave**: user_id (PK), email (unique), country, loyalty_points
**indexes**: email, country, registration_date, is_active

### 02_products.sql
**table**: `products`
**Description**: Product catalog with prices and inventory
**columns clave**: product_id (PK), product_name, category, price, stock_quantity
**indexes**: category, price, product_name (trigram for fuzzy search)

### 03_orders.sql
**table**: `orders`
**Description**: Customer orders with status and totals
**columns clave**: order_id (PK), user_id (FK), order_date, total_amount, status
**indexes**: user_id, order_date, status, composite (user_id, order_date)

### 04_order_items.sql
**table**: `order_items`
**Description**: Product lines in each order (union table)
**columns clave**: order_item_id (PK), order_id (FK), product_id (FK), quantity, subtotal
**indexes**: order_id, product_id
**Unique constraint**: (order_id, product_id) to prevent duplicates

### 05_user_activity.sql
**table**: `user_activity`
**Description**: User event log for analytics
**columns clave**: activity_id (PK), user_id (FK), activity_type, details (JSONB)
**indexes**: user_id, activity_timestamp, activity_type, details (GIN)

## 📊 Seeds (Datos de Muestra)

Los archivos CSV en `seeds/` contienen datos de muestra para testing y desarrollo:

### users.csv

- **Registros**: 10 usuarios de muestra
- **Use**: Testing of basic queries, joins
- **Formato**: CSV con headers

### products.csv
- **Registros**: 10 productos de muestra
- **Categories**: Electronics, Books, Furniture, Sports
- **Use**: Testing aggregations, filters by category

### Cargar Seeds

```bash
# Cargar usuarios
psql -h localhost -U dataengineer -d ecommerce -c "\COPY users FROM 'data/seeds/users.csv' CSV HEADER"

# Cargar productos
psql -h localhost -U dataengineer -d ecommerce -c "\COPY products FROM 'data/seeds/products.csv' CSV HEADER"
```

O usando Python:

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://dataengineer:training123@localhost:5432/ecommerce')

# Cargar usuarios
df_users = pd.read_csv('data/seeds/users.csv')
df_users.to_sql('users', engine, if_exists='append', index=False)

# Cargar productos
df_products = pd.read_csv('data/seeds/products.csv')
df_products.to_sql('products', engine, if_exists='append', index=False)
```

## 🔄 Migrations

Los scripts en `migrations/` documentan cambios incrementales al esquema:

### 001_add_user_preferences.sql

**Purpose**: Add JSONB column for user preferences
**Cambios**:

- Agrega column `preferences` (JSONB)
- Create GIN index for efficient searches
**Uso**: Almacenar configuraciones personalizadas (tema, notificaciones, etc.)

### 002_add_product_ratings.sql

**Purpose**: Add product ratings system
**Cambios**:

- Agrega column `average_rating` (DECIMAL 3,2)
- Agrega column `review_count` (INTEGER)
- Constraints de rango (0-5.00)
- index para filtrado por rating
**Use**: Show top rated products, search filters

### 003_add_order_tracking.sql

**Purpose**: Add shipment tracking
**Cambios**:

- Agrega `tracking_number` (VARCHAR 100)
- Agrega `estimated_delivery` (DATE)
- Agrega `shipped_date` (TIMESTAMP)
- indexes para lookups de tracking
**Use**: Order tracking, delivery notifications

### Aplicar Migrations

```bash
# Aplicar migración individual
psql -h localhost -U dataengineer -d ecommerce -f data/migrations/001_add_user_preferences.sql

# Aplicar todas las migraciones
for f in data/migrations/*.sql; do
    echo "Aplicando $f..."
    psql -h localhost -U dataengineer -d ecommerce -f "$f"
done
```

### Rollback Migrations

Cada archivo de migration incluye comentarios con comandos de rollback al final:

```bash
# Ver comandos de rollback
tail -n 10 data/migrations/001_add_user_preferences.sql

# Ejecutar rollback manualmente
psql -h localhost -U dataengineer -d ecommerce -c "ALTER TABLE users DROP COLUMN IF EXISTS preferences;"
```

## 🔧 Common Use

### Recrear Esquema desde Cero

```bash
# Opción 1: Usar init.sql en infrastructure/
cd infrastructure
docker-compose down -v
docker-compose up -d

# Opción 2: Aplicar schemas manualmente
psql -h localhost -U dataengineer -d ecommerce << EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
EOF

# Aplicar todos los schemas
for f in data/schemas/*.sql; do
    psql -h localhost -U dataengineer -d ecommerce -f "$f"
done
```

### Verificar Estructura

```sql
-- Listar todas las tablas
\dt

-- Describir tabla específica
\d users
\d+ products  -- Incluye comentarios

-- Ver índices de una tabla
\di+ users

-- Ver constraints
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'users'::regclass;
```

### Exportar Datos

```bash
# Exportar tabla a CSV
psql -h localhost -U dataengineer -d ecommerce -c "\COPY users TO 'users_export.csv' CSV HEADER"

# Exportar con query personalizado
psql -h localhost -U dataengineer -d ecommerce -c "\COPY (SELECT * FROM users WHERE country = 'US') TO 'us_users.csv' CSV HEADER"
```

## 📈 Data Metrics

### Table sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

### Conteo de Registros

```sql
SELECT
    'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'user_activity', COUNT(*) FROM user_activity;
```

### Index statistics

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## 🎯 Best Practices

### 1. Convenciones de Nomenclatura

- **tables**: plural, snake_case (users, order_items)
- **columns**: singular, snake_case (user_id, created_at)
- **indexes**: idx_{table}_{columns} (idx_users_email)
- **Constraints**: {table}_{column}_{type} (users_email_format)

### 2. Tipos de Datos

- **IDs**: SERIAL para auto-increment
- **Dinero**: DECIMAL(10,2) nunca FLOAT
- **Timestamps**: TIMESTAMP con timezone
- **Booleans**: BOOLEAN no VARCHAR
- **JSON**: JSONB no JSON (mejor performance)

### 3. indexes

- Indexar todas las foreign keys
- Indexar columns frecuentemente usadas en WHERE
- indexes compuestos para queries comunes
- GIN for JSONB and text searches
- Revisar pg_stat_user_indexes regularmente

### 4. Constraints

- Siempre definir PRIMARY KEY
- Usar FOREIGN KEY con ON DELETE apropiado
- CHECK constraints for data validation
- UNIQUE constraints for unique values
- NOT NULL cuando corresponda

### 5. Migrations

- Nunca modificar archivos de migration aplicados
- Crear nueva migration para cambios
- Incluir Up y Down en comentarios
- Test in development before production
- Document purpose and changes

## 🔍 Troubleshooting

### Error: table ya existe

```sql
-- Usar IF NOT EXISTS en schemas
CREATE TABLE IF NOT EXISTS users (...);
```

### Error: Foreign key violation

```sql
-- Verificar orden de carga (padres antes de hijos)
-- 1. users, products (sin FKs)
-- 2. orders (FK a users)
-- 3. order_items (FK a orders, products)
-- 4. user_activity (FK a users, products)
```

### Error: CSV import fallido

```bash
# Verificar formato del CSV
head -n 2 data/seeds/users.csv

# Verificar encoding
file -i data/seeds/users.csv  # debe ser utf-8

# Usar opciones adicionales de COPY
\COPY users FROM 'data/seeds/users.csv' CSV HEADER DELIMITER ',' NULL 'NULL'
```

## 📚 Additional Resources

- **PostgreSQL COPY**: https://www.postgresql.org/docs/current/sql-copy.html
- **Data Types**: https://www.postgresql.org/docs/current/datatype.html
- **Indexes**: https://www.postgresql.org/docs/current/indexes.html
- **Constraints**: https://www.postgresql.org/docs/current/ddl-constraints.html
- **Migrations Guide**: `../docs/migrations-guide.md`

---

**Last Update**: February 2026
**Mantenido por**: Equipo de Training Data Engineering
