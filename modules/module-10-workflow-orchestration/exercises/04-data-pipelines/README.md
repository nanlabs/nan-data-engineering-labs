# Exercise 04: Real ETL Data Pipelines

## 🎯 Objective

Build production-ready ETL pipelines that extract data from APIs/databases, transform it with pandas/SQL, and load to data warehouses.

## 📚 Prerequisites

- Completed Exercises 01-03
- PostgreSQL database access
- API access or mock API
- Understanding of pandas and SQL
- AWS S3 or LocalStack (optional)

## 📋 Tasks

### Task 1: API to Database ETL

Create a complete ETL pipeline:

1. **Extract**: Fetch data from JSONPlaceholder API (`/users`, `/posts`)
2. **Transform**: Clean, normalize, and join data with pandas
3. **Load**: Insert into PostgreSQL tables

**Requirements:**
- Extract from 2 API endpoints
- Transform: Join users with posts, calculate post count per user
- Load: Create tables if not exist, insert/update data
- Handle API errors with retries
- Log record counts at each stage

**Expected Tables:**
```sql
-- users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    company VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- posts table
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title TEXT,
    body TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- user_stats table
CREATE TABLE user_stats (
    user_id INTEGER PRIMARY KEY,
    post_count INTEGER,
    avg_post_length FLOAT,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

---

### Task 2: CSV to Data Warehouse

Create an ETL pipeline for CSV files:

1. **Sensor**: Wait for CSV file in `/tmp/data/`
2. **Extract**: Read CSV with pandas
3. **Validate**: Data quality checks (schema, nulls, duplicates)
4. **Transform**:
   - Clean data (remove nulls, fix types)
   - Calculate aggregates
   - Add derived columns
5. **Load**: Insert into staging and final tables

**Requirements:**
- Use FileSensor (5 min timeout)
- Pandas validation checks
- Staging → Final table pattern
- Incremental loading (detect new records)
- Error handling for bad data

**Sample CSV** (`/tmp/data/sales.csv`):
```csv
order_id,customer_id,product,amount,order_date
1001,C001,Laptop,1200.50,2024-01-15
1002,C002,Mouse,25.00,2024-01-15
1003,C001,Keyboard,75.00,2024-01-16
```

---

### Task 3: Database to S3 Data Lake

Create a pipeline exporting database to S3:

1. **Extract**: Query PostgreSQL with date filter
2. **Transform**: Convert to Parquet format
3. **Partition**: By year/month/day
4. **Load**: Upload to S3 with partitioning

**Requirements:**
- Use PostgresHook for extraction
- Pandas to Parquet conversion
- S3Hook for upload
- Partitioning: `s3://bucket/data/year=2024/month=01/day=15/data.parquet`
- Compression: Snappy

---

### Task 4: Multi-Source Data Integration

Create a pipeline integrating multiple sources:

1. **Extract**:
   - API: Weather data
   - Database: Store locations
   - CSV: Sales data
2. **Transform**:
   - Join all sources on date and location
   - Calculate metrics (sales per location, weather impact)
3. **Load**: Create analytics table

**Requirements:**
- Parallel extraction (all sources at once)
- Complex join logic
- Error handling per source
- Aggregate metrics
- Data quality report

---

### Task 5: Incremental ETL with CDC

Create an incremental ETL pipeline:

1. **Extract**: Query records modified since last run
2. **Transform**: Process only changed records
3. **Load**: Upsert (update existing, insert new)
4. **Checkpoint**: Store last processed timestamp

**Requirements:**
- Use Airflow Variables for checkpoint
- Incremental extraction (`WHERE modified_at > last_checkpoint`)
- Upsert logic (PostgreSQL `ON CONFLICT`)
- Handle first run (no checkpoint)
- Log processed record count

---

### Task 6: Full Data Pipeline with Data Quality

Complete production pipeline:

1. **Pre-checks**: Validate source availability
2. **Extract**: API + Database
3. **Validate**: Great Expectations checks
4. **Transform**: Complex business logic
5. **Load**: Warehouse tables
6. **Post-checks**: Data quality assertions
7. **Cleanup**: Archive processed files
8. **Notify**: Send success/failure notifications

**Requirements:**
- Use Great Expectations for validation
- Multiple transformation stages
- Rollback on failure
- Comprehensive logging
- Email/Slack notifications
- SLA monitoring

---

## 🚀 Implementation Guides

### Task 1: API to Database ETL

```python
# dags/ex04_task1_api_to_db.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import requests
import pandas as pd
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'student',
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='ex04_api_to_database',
    default_args=default_args,
    description='ETL from API to PostgreSQL',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'etl', 'ex04'],
) as dag:

    def extract_users():
        """Extract users from API"""
        logger.info("Extracting users from API")

        response = requests.get('https://jsonplaceholder.typicode.com/users')
        response.raise_for_status()

        users = response.json()
        logger.info(f"Extracted {len(users)} users")

        # Convert to DataFrame
        df = pd.DataFrame(users)
        df = df[['id', 'name', 'email', 'company']]
        df['company'] = df['company'].apply(lambda x: x['name'] if isinstance(x, dict) else x)

        # Save temporarily
        df.to_csv('/tmp/users.csv', index=False)

        return len(df)

    def extract_posts():
        """Extract posts from API"""
        logger.info("Extracting posts from API")

        response = requests.get('https://jsonplaceholder.typicode.com/posts')
        response.raise_for_status()

        posts = response.json()
        logger.info(f"Extracted {len(posts)} posts")

        # Convert to DataFrame
        df = pd.DataFrame(posts)
        df = df[['id', 'userId', 'title', 'body']]
        df.rename(columns={'userId': 'user_id'}, inplace=True)

        # Save temporarily
        df.to_csv('/tmp/posts.csv', index=False)

        return len(df)

    def transform_data():
        """Transform and join data"""
        logger.info("Transforming data")

        # Load data
        users_df = pd.read_csv('/tmp/users.csv')
        posts_df = pd.read_csv('/tmp/posts.csv')

        logger.info(f"Loaded {len(users_df)} users, {len(posts_df)} posts")

        # Calculate user stats
        user_stats = posts_df.groupby('user_id').agg({
            'id': 'count',
            'body': lambda x: x.str.len().mean()
        }).reset_index()

        user_stats.columns = ['user_id', 'post_count', 'avg_post_length']

        logger.info(f"Calculated stats for {len(user_stats)} users")

        # Save transformed data
        users_df.to_csv('/tmp/users_transformed.csv', index=False)
        posts_df.to_csv('/tmp/posts_transformed.csv', index=False)
        user_stats.to_csv('/tmp/user_stats.csv', index=False)

        return {
            'users': len(users_df),
            'posts': len(posts_df),
            'stats': len(user_stats)
        }

    def load_to_database():
        """Load data to PostgreSQL"""
        logger.info("Loading data to PostgreSQL")

        pg_hook = PostgresHook(postgres_conn_id='postgres_default')

        # Create tables
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            company VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title TEXT,
            body TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            post_count INTEGER,
            avg_post_length FLOAT,
            last_updated TIMESTAMP DEFAULT NOW()
        );
        """

        pg_hook.run(create_tables_sql)
        logger.info("Tables created successfully")

        # Load users
        users_df = pd.read_csv('/tmp/users_transformed.csv')
        for _, row in users_df.iterrows():
            insert_sql = """
            INSERT INTO users (id, name, email, company)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                company = EXCLUDED.company;
            """
            pg_hook.run(insert_sql, parameters=(
                int(row['id']), row['name'], row['email'], row['company']
            ))

        logger.info(f"Loaded {len(users_df)} users")

        # Load posts
        posts_df = pd.read_csv('/tmp/posts_transformed.csv')
        for _, row in posts_df.iterrows():
            insert_sql = """
            INSERT INTO posts (id, user_id, title, body)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                title = EXCLUDED.title,
                body = EXCLUDED.body;
            """
            pg_hook.run(insert_sql, parameters=(
                int(row['id']), int(row['user_id']), row['title'], row['body']
            ))

        logger.info(f"Loaded {len(posts_df)} posts")

        # Load stats
        stats_df = pd.read_csv('/tmp/user_stats.csv')
        for _, row in stats_df.iterrows():
            insert_sql = """
            INSERT INTO user_stats (user_id, post_count, avg_post_length)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                post_count = EXCLUDED.post_count,
                avg_post_length = EXCLUDED.avg_post_length,
                last_updated = NOW();
            """
            pg_hook.run(insert_sql, parameters=(
                int(row['user_id']), int(row['post_count']), float(row['avg_post_length'])
            ))

        logger.info(f"Loaded {len(stats_df)} user stats")

        return {
            'users_loaded': len(users_df),
            'posts_loaded': len(posts_df),
            'stats_loaded': len(stats_df)
        }

    def cleanup():
        """Clean up temporary files"""
        import os

        files = [
            '/tmp/users.csv',
            '/tmp/posts.csv',
            '/tmp/users_transformed.csv',
            '/tmp/posts_transformed.csv',
            '/tmp/user_stats.csv'
        ]

        for file in files:
            if os.path.exists(file):
                os.remove(file)
                logger.info(f"Removed {file}")

    # Create tasks
    extract_users_task = PythonOperator(
        task_id='extract_users',
        python_callable=extract_users,
    )

    extract_posts_task = PythonOperator(
        task_id='extract_posts',
        python_callable=extract_posts,
    )

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
    )

    load_task = PythonOperator(
        task_id='load',
        python_callable=load_to_database,
    )

    cleanup_task = PythonOperator(
        task_id='cleanup',
        python_callable=cleanup,
        trigger_rule='all_done',
    )

    # Dependencies
    [extract_users_task, extract_posts_task] >> transform_task >> load_task >> cleanup_task
```

---

### Task 2: CSV to Data Warehouse

```python
# dags/ex04_task2_csv_to_warehouse.py
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

with DAG(
    dag_id='ex04_csv_to_warehouse',
    description='CSV to Data Warehouse ETL',
    schedule='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['exercise', 'etl', 'csv', 'ex04'],
) as dag:

    # Wait for file
    wait_for_file = FileSensor(
        task_id='wait_for_file',
        filepath='/tmp/data/sales.csv',
        poke_interval=30,
        timeout=300,
    )

    def extract_csv():
        """Extract data from CSV"""
        logger.info("Extracting CSV")
        df = pd.read_csv('/tmp/data/sales.csv')
        logger.info(f"Extracted {len(df)} records")
        return len(df)

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_csv,
    )

    def validate_data():
        """Validate data quality"""
        logger.info("Validating data")

        df = pd.read_csv('/tmp/data/sales.csv')

        # Check schema
        required_columns = ['order_id', 'customer_id', 'product', 'amount', 'order_date']
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # Check nulls
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")

        # Check duplicates
        duplicates = df.duplicated(subset=['order_id']).sum()
        if duplicates > 0:
            logger.warning(f"Found {duplicates} duplicate orders")
            df = df.drop_duplicates(subset=['order_id'])

        # Type validation
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')

        # Save cleaned
        df.to_csv('/tmp/data/sales_cleaned.csv', index=False)

        logger.info(f"Validation complete: {len(df)} valid records")
        return len(df)

    validate = PythonOperator(
        task_id='validate',
        python_callable=validate_data,
    )

    def transform_data():
        """Transform data"""
        logger.info("Transforming data")

        df = pd.read_csv('/tmp/data/sales_cleaned.csv')

        # Add derived columns
        df['year'] = pd.to_datetime(df['order_date']).dt.year
        df['month'] = pd.to_datetime(df['order_date']).dt.month
        df['day'] = pd.to_datetime(df['order_date']).dt.day

        # Aggregates
        daily_stats = df.groupby('order_date').agg({
            'order_id': 'count',
            'amount': ['sum', 'mean', 'max']
        }).reset_index()

        daily_stats.columns = ['order_date', 'order_count', 'total_amount', 'avg_amount', 'max_amount']

        # Save transformed
        df.to_csv('/tmp/data/sales_transformed.csv', index=False)
        daily_stats.to_csv('/tmp/data/daily_stats.csv', index=False)

        logger.info(f"Transformation complete")
        return {'records': len(df), 'days': len(daily_stats)}

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
    )

    def load_to_warehouse():
        """Load to warehouse"""
        logger.info("Loading to warehouse")

        pg_hook = PostgresHook(postgres_conn_id='postgres_default')

        # Create tables
        pg_hook.run("""
            CREATE TABLE IF NOT EXISTS sales_staging (
                order_id VARCHAR(50),
                customer_id VARCHAR(50),
                product VARCHAR(100),
                amount DECIMAL(10,2),
                order_date DATE,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                loaded_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS sales_final (
                order_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50),
                product VARCHAR(100),
                amount DECIMAL(10,2),
                order_date DATE,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                loaded_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS daily_sales_stats (
                order_date DATE PRIMARY KEY,
                order_count INTEGER,
                total_amount DECIMAL(10,2),
                avg_amount DECIMAL(10,2),
                max_amount DECIMAL(10,2),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # Load staging
        df = pd.read_csv('/tmp/data/sales_transformed.csv')
        # ... load logic ...

        logger.info(f"Loaded {len(df)} records to warehouse")

    load = PythonOperator(
        task_id='load',
        python_callable=load_to_warehouse,
    )

    def cleanup():
        import os
        files = ['/tmp/data/sales_cleaned.csv', '/tmp/data/sales_transformed.csv', '/tmp/data/daily_stats.csv']
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    cleanup_task = PythonOperator(
        task_id='cleanup',
        python_callable=cleanup,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # Pipeline
    wait_for_file >> extract >> validate >> transform >> load >> cleanup_task
```

---

## ✅ Validation

### Test API ETL

```bash
# Trigger DAG
airflow dags trigger ex04_api_to_database

# Check database
psql -U airflow -d airflow <<EOF
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM posts;
SELECT * FROM user_stats LIMIT 5;
EOF
```

### Test CSV Pipeline

```bash
# Create test CSV
echo "order_id,customer_id,product,amount,order_date
1001,C001,Laptop,1200.50,2024-01-15
1002,C002,Mouse,25.00,2024-01-15
1003,C001,Keyboard,75.00,2024-01-16" > /tmp/data/sales.csv

# Trigger DAG
airflow dags trigger ex04_csv_to_warehouse

# Monitor in UI
```

---

## 🎓 Learning Objectives

✅ Real ETL pattern (Extract → Transform → Load)
✅ API integration with error handling
✅ Data validation and quality checks
✅ Pandas transformations
✅ Database operations (upsert, transactions)
✅ File sensors for data arrival
✅ Incremental loading patterns
✅ Data partitioning
✅ Production best practices

---

**Next Exercise**: [05-monitoring-alerts](../05-monitoring-alerts/README.md)
