#!/usr/bin/env python3
"""
Exercise 02 - Data Cleaning - SOLUTION
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean user data.

    Cleaning steps:
    1. Remove duplicates
    2. Drop rows with missing critical fields
    3. Fix invalid emails
    4. Normalize country codes
    5. Filter invalid ages
    """
    logger.info(f"Cleaning {len(df)} users")

    initial_count = len(df)

    # Remove exact duplicates
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_count - len(df)} duplicates")

    # Drop rows with missing email or id
    df = df.dropna(subset=['id', 'email'])

    # Fix invalid emails (must contain @)
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'
    df = df[df['email'].str.match(email_pattern, na=False)]

    # Normalize emails to lowercase
    df['email'] = df['email'].str.lower().str.strip()

    # Filter invalid ages
    df = df[df['age'].between(18, 120)]

    # Standardize country codes
    country_mapping = {
        'United States': 'USA',
        'US': 'USA',
        'United Kingdom': 'UK',
        'Great Britain': 'UK'
    }
    df['country'] = df['country'].replace(country_mapping)

    # Fill missing names with 'Unknown'
    df['first_name'] = df['first_name'].fillna('Unknown')
    df['last_name'] = df['last_name'].fillna('Unknown')

    # Standardize status values
    df['status'] = df['status'].str.lower()

    logger.info(f"Cleaned: {len(df)} users remaining")
    return df

def main():
    """Test the cleaning function."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    dirty_file = data_dir / 'users_dirty.csv'

    if not dirty_file.exists():
        print("⚠️  Dirty data file not found. Run data generation first.")
        return

    print("Loading dirty data...")
    df_dirty = pd.read_csv(dirty_file)
    print(f"Loaded {len(df_dirty)} dirty records")
    print("\nNull counts before cleaning:")
    print(df_dirty.isnull().sum())

    print("\nCleaning data...")
    df_clean = clean_users(df_dirty)

    print(f"\n✓ Cleaned {len(df_clean)} records")
    print("\nNull counts after cleaning:")
    print(df_clean.isnull().sum())

    # Save cleaned data
    output_dir = Path(__file__).parents[2] / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'users_cleaned.csv'
    df_clean.to_csv(output_file, index=False)
    print(f"\n✓ Saved to {output_file}")

if __name__ == '__main__':
    main()
