#!/usr/bin/env python3
"""
Generate synthetic user data for ETL exercises.
"""
import pandas as pd
from faker import Faker
import random
from pathlib import Path

fake = Faker()
random.seed(42)
Faker.seed(42)

def generate_users(n_users=10000):
    """Generate synthetic user data."""
    users = []

    countries = ['USA', 'UK', 'Canada', 'Australia', 'Germany',
                 'France', 'Spain', 'Mexico', 'Brazil', 'Argentina']
    statuses = ['active', 'inactive', 'suspended', 'pending']

    for i in range(1, n_users + 1):
        created_at = fake.date_time_between(start_date='-2y', end_date='now')

        # 80% have logged in at least once
        last_login = None
        if random.random() < 0.8:
            last_login = fake.date_time_between(
                start_date=created_at,
                end_date='now'
            ).isoformat()

        user = {
            'id': i,
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'age': random.randint(18, 80),
            'country': random.choice(countries),
            'status': random.choice(statuses),
            'created_at': created_at.isoformat(),
            'last_login': last_login
        }
        users.append(user)

    return pd.DataFrame(users)

def introduce_data_quality_issues(df):
    """Introduce data quality issues for testing."""
    df_dirty = df.copy()

    # 5% missing emails
    mask = df_dirty.sample(frac=0.05).index
    df_dirty.loc[mask, 'email'] = None

    # 3% invalid email formats
    mask = df_dirty.sample(frac=0.03).index
    df_dirty.loc[mask, 'email'] = df_dirty.loc[mask, 'email'].str.replace('@', '')

    # 2% missing names
    mask = df_dirty.sample(frac=0.02).index
    df_dirty.loc[mask, 'first_name'] = None

    # 1% invalid ages
    mask = df_dirty.sample(frac=0.01).index
    df_dirty.loc[mask, 'age'] = random.choice([-1, 150, 999])

    # 5% duplicates
    n_duplicates = int(len(df_dirty) * 0.05)
    duplicates = df_dirty.sample(n=n_duplicates).copy()
    df_dirty = pd.concat([df_dirty, duplicates], ignore_index=True)

    return df_dirty

def main():
    """Generate and save user data."""
    output_dir = Path(__file__).parent.parent / 'raw'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating users...")
    df_users = generate_users(10000)

    # Clean version
    clean_path = output_dir / 'users_clean.csv'
    df_users.to_csv(clean_path, index=False)
    print(f"✓ Generated {len(df_users)} clean users → {clean_path}")

    # Dirty version (with data quality issues)
    df_dirty = introduce_data_quality_issues(df_users)
    dirty_path = output_dir / 'users_dirty.csv'
    df_dirty.to_csv(dirty_path, index=False)
    print(f"✓ Generated {len(df_dirty)} dirty users → {dirty_path}")

    # JSON version
    json_path = output_dir / 'users.json'
    df_users.to_json(json_path, orient='records', lines=True)
    print(f"✓ Generated JSON version → {json_path}")

    # Sample for testing
    sample = df_users.head(100)
    sample_path = output_dir / 'users_sample.csv'
    sample.to_csv(sample_path, index=False)
    print(f"✓ Generated sample (100 records) → {sample_path}")

    # Statistics
    print("\n📊 Statistics:")
    print(f"  Total users: {len(df_users)}")
    print(f"  Countries: {df_users['country'].nunique()}")
    print("  Status distribution:")
    print(df_users['status'].value_counts().to_string())

if __name__ == '__main__':
    main()
