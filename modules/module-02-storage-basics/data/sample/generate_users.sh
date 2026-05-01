#!/bin/bash
# Quick script to generate users_sample.parquet

cd "$(dirname "$0")"

python3 << 'PYTHON_EOF'
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta
import random

random.seed(42)

first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Lisa', 'Tom', 'Anna',
               'Robert', 'Maria', 'James', 'Patricia', 'Michael', 'Jennifer', 'William', 'Linda',
               'Richard', 'Barbara', 'Joseph', 'Susan', 'Thomas', 'Jessica', 'Charles', 'Karen']

last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
              'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
              'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson']

countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'Spain', 'Italy', 'Australia']

users_data = []
base_date = datetime(2024, 1, 1)

for i in range(1, 51):
    user_id = 1000 + i
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
    age = random.randint(18, 70)
    country = random.choice(countries)
    registration_date = (base_date + timedelta(days=random.randint(0, 365))).date()
    is_active = random.choice([True, True, True, False])

    users_data.append({
        'user_id': user_id,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'age': age,
        'country': country,
        'registration_date': registration_date,
        'is_active': is_active
    })

df = pd.DataFrame(users_data)

schema = pa.schema([
    ('user_id', pa.int64()),
    ('first_name', pa.string()),
    ('last_name', pa.string()),
    ('email', pa.string()),
    ('age', pa.int64()),
    ('country', pa.string()),
    ('registration_date', pa.date32()),
    ('is_active', pa.bool_())
])

table = pa.Table.from_pandas(df, schema=schema)

pq.write_table(
    table,
    'users_sample.parquet',
    compression='snappy',
    use_dictionary=True,
    write_statistics=True
)

print(f"✓ Created users_sample.parquet with {len(df)} users")
print(f"  Columns: {list(df.columns)}")
print(f"  Countries: {df['country'].nunique()}")
print(f"  Active users: {df['is_active'].sum()}/{len(df)}")
PYTHON_EOF

echo ""
echo "Users sample generated successfully!"
ls -lh users_sample.parquet
