# 🚀 Snowflake Setup Guide

> **Overview**: This guide walks through setting up your Snowflake environment, from trial signup to creating your first database, configuring CLI tools, and connecting from Python. Perfect for beginners starting with Snowflake.

## 📋 Table of Contents

- [Trial Signup](#trial-signup)
- [Web UI Tour](#web-ui-tour)
- [Creating Training Database](#creating-training-database)
- [SnowSQL CLI Setup](#snowsql-cli-setup)
- [Python Connector Setup](#python-connector-setup)
- [Resource Monitor Setup](#resource-monitor-setup)
- [Verification & Testing](#verification--testing)
- [Troubleshooting](#troubleshooting)

---

## 🎁 Trial Signup

### Step 1: Create Free Trial Account

1. **Navigate to Signup Page**:
   - Visit: https://signup.snowflake.com/
   - Or: https://trial.snowflake.com/

2. **Choose Cloud Provider**:
   ```
   Options:
   ├─ Amazon Web Services (AWS)     ← Most common, recommended
   ├─ Microsoft Azure
   └─ Google Cloud Platform (GCP)

   Recommendation: Choose AWS (us-east-1 or nearest region)
   ```

3. **Select Region**:
   ```
   AWS Regions (examples):
   ├─ US East (N. Virginia)        us-east-1      ← Low-cost, popular
   ├─ US West (Oregon)             us-west-2
   ├─ Europe (Ireland)             eu-west-1
   ├─ Europe (Frankfurt)           eu-central-1
   └─ Asia Pacific (Singapore)     ap-southeast-1

   💡 Choose nearest region for best performance
   ```

4. **Fill Account Details**:
   ```
   Required Information:
   ├─ First Name
   ├─ Last Name
   ├─ Email Address              ← Use personal or work email
   ├─ Company Name               ← Can use "Personal Learning"
   ├─ Job Title                  ← Optional
   └─ Country
   ```

5. **Choose Edition**:
   ```
   Available for Trial:
   ├─ Standard Edition           $2/credit   (basic features)
   ├─ Enterprise Edition         $3/credit   ← Recommended (90-day Time Travel)
   └─ Business Critical          $4/credit   (enhanced security)

   Recommendation: Enterprise Edition (best learning experience)
   ```

6. **Accept Terms**:
   - Review Snowflake Terms of Service
   - Check "I agree" box
   - Click **Get Started**

7. **Verify Email**:
   - Check email inbox (from noreply@snowflake.com)
   - Click verification link
   - Set password (strong, 8+ characters, mixed case, numbers, symbols)

8. **Account Created**:
   ```
   You'll receive:
   ├─ Account Identifier:  abc12345
   ├─ Account URL:         https://abc12345.snowflakecomputing.com
   ├─ Username:            <your-email>
   ├─ Organization:        MYORG
   └─ Trial Credits:       $400 USD
   ```

### Step 2: First Login

1. **Navigate to Account URL**:
   ```bash
   # Example URL format
   https://<account_identifier>.snowflakecomputing.com

   # Specific example
   https://abc12345.snowflakecomputing.com
   ```

2. **Login Credentials**:
   ```
   Username: <your-email>
   Password: <password-you-set>
   ```

3. **Initial Setup Wizard** (optional):
   - Snowflake may present quick-start wizard
   - You can skip this (we'll do manual setup)

4. **Welcome Screen**:
   - First time: Shows welcome tour
   - Can skip or follow (we cover everything here)

---

## 🖥️ Web UI Tour

### Main Navigation

```
┌────────────────────────────────────────────────────────────┐
│  Snowflake Web UI Layout                                   │
├────────────────────────────────────────────────────────────┤
│  Top Bar:                                                  │
│    [Snowflake Logo] [Home/Projects] [Worksheets] [...]    │
├────────────────────────────────────────────────────────────┤
│  Left Sidebar:                                             │
│    📊 Worksheets      ← SQL Editor (primary workspace)     │
│    💾 Data            ← Databases, Schemas, Tables         │
│    📈 Data Products   ← Shares, Marketplace               │
│    ⚡ Compute          ← Warehouses                        │
│    📜 Activity        ← Query History                      │
│    👤 Admin           ← Users, Roles, Account settings     │
│    📚 Learn           ← Documentation, Tutorials           │
└────────────────────────────────────────────────────────────┘
```

### Worksheets (SQL Editor)

**Purpose**: Write and execute SQL queries

**Key Features**:
```sql
-- 1. Create new worksheet
-- Click: Worksheets → + Worksheet

-- 2. Context selection (top-right)
/*
Role:       [ACCOUNTADMIN ▼]      ← Select role
Warehouse:  [COMPUTE_WH ▼]        ← Select warehouse to run queries
Database:   [MY_DB ▼]             ← Default database
Schema:     [PUBLIC ▼]            ← Default schema
*/

-- 3. SQL Editor (main area)
SELECT CURRENT_VERSION(), CURRENT_USER(), CURRENT_ROLE();

-- 4. Execute query
-- Method 1: Click "Run" button (▶)
-- Method 2: Ctrl+Enter (Cmd+Enter on Mac)
-- Method 3: Highlight SQL block, then Run (for partial execution)

-- 5. View results (bottom pane)
-- Results tab: Query output
-- Chart tab: Visualize data
-- Query Details: Execution stats, bytes scanned, duration
```

**Worksheet Tips**:
```sql
-- Multiple statements (separated by semicolon)
SELECT 1;
SELECT 2;
SELECT 3;

-- Run all: Click "Run All" dropdown
-- Run selected: Highlight specific SQL, then Run

-- Save worksheet: File → Save As → "My Analysis"
-- Share worksheet: Top-right → Share
-- Format SQL: Click "Format" button (beautify)
```

### Data (Database Explorer)

**Navigation**:
```
Data → Databases → [Database Name] → [Schema] → Tables/Views
```

**Actions**:
- **View Table Data**: Click table → Preview Data (top 100 rows, no warehouse needed)
- **Table Schema**: Click Columns tab
- **Table Details**: Storage size, row count, owner
- **Open in Worksheet**: Click "..." → Open in Worksheet (generates SELECT *)

**Example**:
```sql
-- Navigate to SNOWFLAKE_SAMPLE_DATA (free sample database)
-- Data → Databases → SNOWFLAKE_SAMPLE_DATA → TPCDS_SF10TCL → STORE_SALES
-- Click table → Preview Data → See 100 rows instantly
```

### Compute (Warehouses)

**View Warehouses**:
```
Compute → Warehouses → View list
```

**Warehouse Actions**:
- **Resume**: Start suspended warehouse
- **Suspend**: Stop running warehouse (save costs)
- **Edit**: Change size, auto-suspend settings
- **Monitor**: View credit usage, query count

**Creating Warehouse via UI**:
```
1. Compute → Warehouses
2. Click "+ Warehouse"
3. Fill details:
   - Name: training_wh
   - Size: X-Small
   - Auto Suspend: 60 seconds
   - Auto Resume: ✓
4. Click "Create Warehouse"
```

### Activity (Query History)

**Purpose**: Monitor all queries executed in account

**Filters**:
```
├─ Time Range:      Last 24 hours, 7 days, 30 days, Custom
├─ User:            Filter by user
├─ Warehouse:       Filter by warehouse
├─ Query Status:    Success, Failed, Running
└─ Query Text:      Search query content
```

**Query Details**:
- Click any query → View full SQL, execution plan, bytes scanned, credits used
- Useful for debugging slow queries or errors

### Admin (Account Management)

**Key Sections**:
```
Admin → Users             ← Manage users
Admin → Roles             ← RBAC configuration
Admin → Warehouses        ← Same as Compute tab
Admin → Resource Monitors ← Set credit limits
Admin → Usage             ← Credit consumption reports
Admin → Billing           ← Payment methods (post-trial)
Admin → Account           ← Account details, edition, region
```

---

## 💾 Creating Training Database

### Step 1: Create Database & Schemas

**Open Worksheet** (Worksheets → + Worksheet)

```sql
-- Set context to ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Create training database
CREATE DATABASE IF NOT EXISTS training_snowflake
    COMMENT = 'Training database for Snowflake exercises';

-- Use the database
USE DATABASE training_snowflake;

-- Create schemas for different stages
CREATE SCHEMA IF NOT EXISTS raw
    COMMENT = 'Raw ingested data';

CREATE SCHEMA IF NOT EXISTS staging
    COMMENT = 'Staging and transformation layer';

CREATE SCHEMA IF NOT EXISTS analytics
    COMMENT = 'Production analytics tables and views';

CREATE SCHEMA IF NOT EXISTS sandbox
    COMMENT = 'Experimental and development area';

-- Verify creation
SHOW SCHEMAS IN DATABASE training_snowflake;
```

**Expected Output**:
```
name        | database_name        | owner       | comment
------------|----------------------|-------------|------------------------
RAW         | TRAINING_SNOWFLAKE   | ACCOUNTADMIN| Raw ingested data
STAGING     | TRAINING_SNOWFLAKE   | ACCOUNTADMIN| Staging and transformation layer
ANALYTICS   | TRAINING_SNOWFLAKE   | ACCOUNTADMIN| Production analytics tables and views
SANDBOX     | TRAINING_SNOWFLAKE   | ACCOUNTADMIN| Experimental and development area
PUBLIC      | TRAINING_SNOWFLAKE   | ACCOUNTADMIN| Default schema
```

### Step 2: Create Virtual Warehouse

```sql
-- Create development warehouse (cost-optimized)
CREATE WAREHOUSE IF NOT EXISTS training_wh WITH
    WAREHOUSE_SIZE = 'X-SMALL'           -- 1 credit/hour ($2-4/hour)
    AUTO_SUSPEND = 60                    -- Suspend after 60 seconds idle
    AUTO_RESUME = TRUE                   -- Auto-start on query
    INITIALLY_SUSPENDED = TRUE           -- Start in suspended state
    MIN_CLUSTER_COUNT = 1                -- Single cluster
    MAX_CLUSTER_COUNT = 1                -- No scaling
    SCALING_POLICY = 'STANDARD'
    COMMENT = 'Training warehouse for exercises';

-- Grant usage to current role
GRANT USAGE ON WAREHOUSE training_wh TO ROLE ACCOUNTADMIN;

-- Verify creation
SHOW WAREHOUSES LIKE 'training_wh';

-- Check status (should be "Suspended")
DESC WAREHOUSE training_wh;
```

### Step 3: Create Sample Tables

```sql
-- Set context
USE WAREHOUSE training_wh;  -- Warehouse auto-resumes
USE DATABASE training_snowflake;
USE SCHEMA analytics;

-- Create customers table
CREATE OR REPLACE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'USA',
    created_date DATE DEFAULT CURRENT_DATE(),
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Insert sample data
INSERT INTO customers (customer_id, first_name, last_name, email, city, state)
VALUES
    (1, 'John', 'Doe', 'john.doe@example.com', 'New York', 'NY'),
    (2, 'Jane', 'Smith', 'jane.smith@example.com', 'Los Angeles', 'CA'),
    (3, 'Bob', 'Johnson', 'bob.j@example.com', 'Chicago', 'IL'),
    (4, 'Alice', 'Williams', 'alice.w@example.com', 'Houston', 'TX'),
    (5, 'Charlie', 'Brown', 'charlie.b@example.com', 'Phoenix', 'AZ');

-- Create orders table
CREATE OR REPLACE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    order_amount DECIMAL(10,2),
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Insert sample orders
INSERT INTO orders (order_id, customer_id, order_date, order_amount, status)
VALUES
    (101, 1, CURRENT_DATE(), 99.99, 'completed'),
    (102, 2, CURRENT_DATE() - 1, 149.50, 'completed'),
    (103, 1, CURRENT_DATE() - 2, 75.00, 'pending'),
    (104, 3, CURRENT_DATE() - 3, 200.00, 'completed'),
    (105, 4, CURRENT_DATE() - 5, 50.25, 'cancelled');

-- Verify tables
SHOW TABLES IN SCHEMA analytics;

-- Query sample data
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(o.order_id) AS order_count,
    SUM(o.order_amount) AS total_spent
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, customer_name
ORDER BY total_spent DESC;
```

**Expected Output**:
```
customer_id | customer_name    | order_count | total_spent
------------|------------------|-------------|------------
1           | John Doe         | 2           | 174.99
3           | Bob Johnson      | 1           | 200.00
2           | Jane Smith       | 1           | 149.50
4           | Alice Williams   | 1           | 50.25
5           | Charlie Brown    | 0           | NULL
```

### Step 4: Set Default Context

```sql
-- Set defaults for your user (avoid setting context every time)
ALTER USER <your-email-username> SET
    DEFAULT_ROLE = ACCOUNTADMIN
    DEFAULT_WAREHOUSE = training_wh
    DEFAULT_NAMESPACE = training_snowflake.analytics;

-- Verify settings
SHOW PARAMETERS LIKE 'DEFAULT%' FOR USER <your-email-username>;
```

**Future logins**: New worksheets will automatically use these defaults.

---

## 🖥️ SnowSQL CLI Setup

### Installation

**macOS** (Homebrew):
```bash
# Install SnowSQL via Homebrew
brew install snowflake-snowsql

# Verify installation
snowsql --version
# Expected: SnowSQL v1.3.x
```

**macOS/Linux** (Manual):
```bash
# Download installer from Snowflake
curl -O https://sfc-repo.snowflakecomputing.com/snowsql/bootstrap/1.3/linux_x86_64/snowsql-1.3.1-linux_x86_64.bash

# Make executable
chmod +x snowsql-1.3.1-linux_x86_64.bash

# Run installer
./snowsql-1.3.1-linux_x86_64.bash

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.snowsql:$PATH"

# Verify
snowsql --version
```

**Windows**:
```powershell
# Download installer from Snowflake
# https://sfc-repo.snowflakecomputing.com/snowsql/bootstrap/1.3/windows_x86_64/snowsql-1.3.1-windows_x86_64.msi

# Run MSI installer
# Follow installation wizard

# Verify (in Command Prompt or PowerShell)
snowsql --version
```

### Configuration

**Create Config File** (~/.snowsql/config):
```bash
mkdir -p ~/.snowsql
nano ~/.snowsql/config
```

**Config File Content**:
```ini
[connections]

# Default connection
[connections.training]
accountname = abc12345                     # Your account identifier
username = your-email@example.com          # Your Snowflake username
password = your-password                   # Or leave blank for prompt
dbname = training_snowflake                # Default database
schemaname = analytics                     # Default schema
warehousename = training_wh                # Default warehouse
rolename = ACCOUNTADMIN                    # Default role

# Optional settings
[options]
log_level = INFO
timing = True                              # Show query execution time
output_format = psql                       # Table format (psql, json, csv)
auto_completion = True                     # Enable tab completion
syntax_style = monokai                     # Syntax highlighting
```

**Secure Config File**:
```bash
# Restrict permissions (important for security)
chmod 600 ~/.snowsql/config
```

### Using SnowSQL

**Connect to Snowflake**:
```bash
# Connect using named connection
snowsql -c training

# Connect with inline parameters
snowsql -a abc12345 -u your-email@example.com

# You'll be prompted for password if not in config
```

**Sample SnowSQL Session**:
```bash
$ snowsql -c training
Password:
* SnowSQL * v1.3.1
Type SQL queries and press Enter to execute.
Type !help to see available commands.

yourname@training_snowflake.analytics> SELECT CURRENT_USER(), CURRENT_ROLE();
+------------------+----------------+
| CURRENT_USER()   | CURRENT_ROLE() |
|------------------+----------------|
| YOUR_EMAIL       | ACCOUNTADMIN   |
+------------------+----------------+
1 Row(s) produced. Time Elapsed: 0.234s

yourname@training_snowflake.analytics> SELECT COUNT(*) FROM customers;
+----------+
| COUNT(*) |
|----------|
|        5 |
+----------+
1 Row(s) produced. Time Elapsed: 0.156s

yourname@training_snowflake.analytics> !quit
Goodbye!
```

**Useful SnowSQL Commands**:
```bash
# Execute SQL file
snowsql -c training -f create_tables.sql

# Execute inline query
snowsql -c training -q "SELECT COUNT(*) FROM customers;"

# Output to file (CSV)
snowsql -c training -o output_format=csv -o header=true -q "SELECT * FROM customers;" > customers.csv

# Output to file (JSON)
snowsql -c training -o output_format=json -q "SELECT * FROM customers;" > customers.json

# Variables in query
snowsql -c training -D target_state=CA -q "SELECT * FROM customers WHERE state = '&target_state';"
```

**Interactive Commands** (inside SnowSQL):
```sql
-- List available commands
!help

-- Exit SnowSQL
!exit  -- or !quit

-- Execute local SQL file
!source /path/to/script.sql

-- Set output format
!set output_format=json

-- Show current settings
!options

-- Change database
USE DATABASE training_snowflake;

-- Change warehouse
USE WAREHOUSE training_wh;
```

---

## 🐍 Python Connector Setup

### Installation

```bash
# Install Snowflake connector for Python
pip install snowflake-connector-python

# Or with conda
conda install -c conda-forge snowflake-connector-python

# Verify installation
python -c "import snowflake.connector; print(snowflake.connector.__version__)"
```

**Optional**: Install pandas and sqlalchemy for advanced features
```bash
pip install snowflake-connector-python[pandas]
pip install snowflake-sqlalchemy
```

### Basic Connection

**Create Python Script** (snowflake_test.py):
```python
import snowflake.connector

# Connect to Snowflake
conn = snowflake.connector.connect(
    account='abc12345',                      # Your account identifier
    user='your-email@example.com',
    password='your-password',
    warehouse='training_wh',
    database='training_snowflake',
    schema='analytics',
    role='ACCOUNTADMIN'
)

# Create cursor
cursor = conn.cursor()

# Execute query
cursor.execute("SELECT CURRENT_VERSION(), CURRENT_USER(), CURRENT_ROLE()")

# Fetch results
row = cursor.fetchone()
print(f"Snowflake Version: {row[0]}")
print(f"Current User: {row[1]}")
print(f"Current Role: {row[2]}")

# Close cursor and connection
cursor.close()
conn.close()
```

**Run Script**:
```bash
python snowflake_test.py

# Expected output:
# Snowflake Version: 8.5.0
# Current User: YOUR_EMAIL@EXAMPLE.COM
# Current Role: ACCOUNTADMIN
```

### Query Examples

**Fetch All Rows**:
```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='abc12345',
    user='your-email@example.com',
    password='your-password',
    warehouse='training_wh',
    database='training_snowflake',
    schema='analytics'
)

cursor = conn.cursor()

# Execute query
cursor.execute("SELECT * FROM customers")

# Fetch all rows
rows = cursor.fetchall()

# Print results
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]} {row[2]}, Email: {row[3]}")

cursor.close()
conn.close()
```

**Using Pandas**:
```python
import snowflake.connector
import pandas as pd

conn = snowflake.connector.connect(
    account='abc12345',
    user='your-email@example.com',
    password='your-password',
    warehouse='training_wh',
    database='training_snowflake',
    schema='analytics'
)

# Query to DataFrame
query = """
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS name,
        COUNT(o.order_id) AS order_count,
        COALESCE(SUM(o.order_amount), 0) AS total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, name
    ORDER BY total_spent DESC
"""

df = pd.read_sql(query, conn)

print(df)
print(f"\nDataFrame shape: {df.shape}")
print(f"Top spender: {df.iloc[0]['name']} - ${df.iloc[0]['total_spent']}")

conn.close()
```

**Insert Data from Python**:
```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='abc12345',
    user='your-email@example.com',
    password='your-password',
    warehouse='training_wh',
    database='training_snowflake',
    schema='analytics'
)

cursor = conn.cursor()

# Insert single row
cursor.execute("""
    INSERT INTO customers (customer_id, first_name, last_name, email, city, state)
    VALUES (%(id)s, %(fname)s, %(lname)s, %(email)s, %(city)s, %(state)s)
""", {
    'id': 6,
    'fname': 'David',
    'lname': 'Miller',
    'email': 'david.m@example.com',
    'city': 'Austin',
    'state': 'TX'
})

print(f"Inserted {cursor.rowcount} row(s)")

# Commit transaction
conn.commit()

cursor.close()
conn.close()
```

**Batch Insert**:
```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='abc12345',
    user='your-email@example.com',
    password='your-password',
    warehouse='training_wh',
    database='training_snowflake',
    schema='analytics'
)

cursor = conn.cursor()

# Batch data
customers = [
    (7, 'Eva', 'Davis', 'eva.d@example.com', 'Seattle', 'WA'),
    (8, 'Frank', 'Garcia', 'frank.g@example.com', 'Denver', 'CO'),
    (9, 'Grace', 'Martinez', 'grace.m@example.com', 'Boston', 'MA')
]

# Execute batch
cursor.executemany("""
    INSERT INTO customers (customer_id, first_name, last_name, email, city, state)
    VALUES (%s, %s, %s, %s, %s, %s)
""", customers)

print(f"Inserted {cursor.rowcount} row(s)")
conn.commit()

cursor.close()
conn.close()
```

### Connection Best Practices

**Use Environment Variables**:
```python
import os
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'training_wh'),
    database=os.getenv('SNOWFLAKE_DATABASE', 'training_snowflake'),
    schema=os.getenv('SNOWFLAKE_SCHEMA', 'analytics')
)
```

**Set Environment Variables** (.env file):
```bash
export SNOWFLAKE_ACCOUNT="abc12345"
export SNOWFLAKE_USER="your-email@example.com"
export SNOWFLAKE_PASSWORD="your-password"
export SNOWFLAKE_WAREHOUSE="training_wh"
export SNOWFLAKE_DATABASE="training_snowflake"
export SNOWFLAKE_SCHEMA="analytics"
```

**Context Manager** (auto-close connection):
```python
import snowflake.connector

def get_connection():
    return snowflake.connector.connect(
        account='abc12345',
        user='your-email@example.com',
        password='your-password',
        warehouse='training_wh',
        database='training_snowflake',
        schema='analytics'
    )

# Use context manager
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        print(f"Customer count: {count}")

# Connection and cursor automatically closed
```

---

## 🛡️ Resource Monitor Setup

**Why Resource Monitors?**
- Prevent unexpected costs
- Get alerts on credit usage
- Automatically suspend warehouses at thresholds

**Create Resource Monitor** (via SQL):
```sql
-- Use ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Create monitor for trial credits
CREATE RESOURCE MONITOR trial_credit_monitor WITH
    CREDIT_QUOTA = 400                   -- $400 trial credits
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 50 PERCENT DO NOTIFY          -- Alert at $200 (50%)
        ON 75 PERCENT DO NOTIFY          -- Alert at $300 (75%)
        ON 90 PERCENT DO NOTIFY          -- Alert at $360 (90%)
        ON 100 PERCENT DO SUSPEND        -- Suspend all warehouses at $400
        ON 110 PERCENT DO SUSPEND_IMMEDIATE;  -- Emergency stop

-- Apply to account (affects all warehouses)
ALTER ACCOUNT SET RESOURCE_MONITOR = trial_credit_monitor;

-- Verify
SHOW RESOURCE MONITORS;
```

**Create Warehouse-Specific Monitor**:
```sql
-- Monitor for training warehouse only
CREATE RESOURCE MONITOR training_wh_monitor WITH
    CREDIT_QUOTA = 50                    -- $50-150 limit per month
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS
        ON 80 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

-- Apply to specific warehouse
ALTER WAREHOUSE training_wh SET RESOURCE_MONITOR = training_wh_monitor;
```

**Check Monitor Status**:
```sql
-- View monitor usage
SELECT *
FROM TABLE(INFORMATION_SCHEMA.RESOURCE_MONITOR_USAGE(
    DATE_RANGE_START => DATEADD('day', -30, CURRENT_DATE())
));

-- Check remaining credits
SELECT
    credit_quota,
    used_credits,
    credit_quota - used_credits AS remaining_credits,
    ROUND((used_credits / credit_quota) * 100, 2) AS percent_used
FROM SNOWFLAKE.ACCOUNT_USAGE.RESOURCE_MONITORS
WHERE name = 'TRIAL_CREDIT_MONITOR';
```

---

## ✅ Verification & Testing

### Test Database Access

```sql
-- Set context
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE training_wh;
USE DATABASE training_snowflake;
USE SCHEMA analytics;

-- Test queries
SELECT 'Database accessible!' AS test_result;
SELECT COUNT(*) AS customer_count FROM customers;
SELECT COUNT(*) AS order_count FROM orders;

-- Test joins
SELECT
    c.first_name,
    c.last_name,
    COUNT(o.order_id) AS orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.first_name, c.last_name;
```

### Test Warehouse Auto-Suspend

```sql
-- Check warehouse status
SHOW WAREHOUSES LIKE 'training_wh';
-- Look for "state" column: Should be "STARTED" if recently used

-- Wait 60 seconds (auto-suspend time)
-- Check again
SHOW WAREHOUSES LIKE 'training_wh';
-- State should be "SUSPENDED"

-- Run query (warehouse auto-resumes)
SELECT COUNT(*) FROM customers;

-- Check status again (should be "STARTED")
SHOW WAREHOUSES LIKE 'training_wh';
```

### Test SnowSQL Connection

```bash
# Test connection
snowsql -c training -q "SELECT 'SnowSQL working!' AS test;"

# Expected output:
# +-------------------+
# | TEST              |
# |-------------------|
# | SnowSQL working!  |
# +-------------------+
```

### Test Python Connection

```python
# test_connection.py
import snowflake.connector

try:
    conn = snowflake.connector.connect(
        account='abc12345',
        user='your-email@example.com',
        password='your-password'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 'Python connector working!' AS test")
    result = cursor.fetchone()
    print(f"✅ Success: {result[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Cannot Login to Web UI**:
```
Problem: "Incorrect username or password"
Solution:
  1. Verify username (usually your email)
  2. Try password reset: https://<account>.snowflakecomputing.com → Forgot Password
  3. Check caps lock
  4. Clear browser cache/cookies
  5. Try incognito/private window
```

**2. Warehouse Not Starting**:
```
Problem: Query fails with "Warehouse not started"
Solution:
  1. Check if warehouse exists: SHOW WAREHOUSES;
  2. Resume manually: ALTER WAREHOUSE training_wh RESUME;
  3. Check permissions: GRANT USAGE ON WAREHOUSE training_wh TO ROLE <your-role>;
  4. Verify AUTO_RESUME is TRUE: DESC WAREHOUSE training_wh;
```

**3. Table Not Found**:
```
Problem: "Object does not exist"
Solution:
  1. Check current context:
     SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();
  2. Use fully qualified name:
     SELECT * FROM training_snowflake.analytics.customers;
  3. Verify table exists:
     SHOW TABLES IN training_snowflake.analytics;
```

**4. Insufficient Privileges**:
```
Problem: "SQL access control error"
Solution:
  1. Check current role: SELECT CURRENT_ROLE();
  2. Switch to ACCOUNTADMIN: USE ROLE ACCOUNTADMIN;
  3. Grant privileges:
     GRANT USAGE ON DATABASE training_snowflake TO ROLE <your-role>;
     GRANT USAGE ON SCHEMA training_snowflake.analytics TO ROLE <your-role>;
     GRANT SELECT ON ALL TABLES IN SCHEMA training_snowflake.analytics TO ROLE <your-role>;
```

**5. SnowSQL Connection Fails**:
```
Problem: "Unable to connect"
Solution:
  1. Verify account identifier: snowsql -a abc12345 -u your-email
  2. Check network/firewall (Snowflake ports: 443, 80)
  3. Test account URL in browser: https://abc12345.snowflakecomputing.com
  4. Update SnowSQL: brew upgrade snowflake-snowsql (macOS)
  5. Check config file: cat ~/.snowsql/config
```

**6. Python Connector Issues**:
```
Problem: Import error or connection fails
Solution:
  1. Reinstall: pip uninstall snowflake-connector-python && pip install snowflake-connector-python
  2. Check Python version (3.8+ required): python --version
  3. Verify installation: python -c "import snowflake.connector; print(snowflake.connector.__version__)"
  4. Test simple connection (no warehouse/database)
```

**7. Resource Monitor Suspends Warehouse**:
```
Problem: Queries fail after heavy usage
Solution:
  1. Check monitor status:
     SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.RESOURCE_MONITORS;
  2. Increase quota or remove monitor temporarily:
     ALTER RESOURCE MONITOR trial_credit_monitor SET CREDIT_QUOTA = 500;
  3. Resume warehouse manually:
     ALTER WAREHOUSE training_wh RESUME;
```

---

## 📚 Next Steps

Now that your environment is set up:

1. ✅ **Verify all components work** (Web UI, SnowSQL, Python)
2. ✅ **Review [COST-ALERT.md](../COST-ALERT.md)** to understand pricing
3. ✅ **Start exercises** in the `exercises/` directory
4. ✅ **Explore sample data**: `SNOWFLAKE_SAMPLE_DATA` database
5. ✅ **Join Snowflake Community**: https://community.snowflake.com/

**Congratulations!** 🎉 Your Snowflake environment is ready for learning.

---

**Last Updated**: March 2026
**Module**: Bonus 02 - Snowflake Data Cloud
