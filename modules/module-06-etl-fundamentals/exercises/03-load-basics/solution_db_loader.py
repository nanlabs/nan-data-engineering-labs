#!/usr/bin/env python3
"""
Exercise 03 - Database Loader - SOLUTION
"""
import pandas as pd
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseLoader:
    """Load data into SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_users_table(self):
        """Create users table."""
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            age INTEGER,
            country TEXT,
            status TEXT,
            created_at TEXT,
            last_login TEXT
        )
        """
        self.conn.execute(sql)
        self.conn.commit()
        logger.info("Users table created")

    def load_dataframe(self, df: pd.DataFrame, table: str, if_exists='append'):
        """Load DataFrame to database."""
        df.to_sql(table, self.conn, if_exists=if_exists, index=False)
        logger.info(f"Loaded {len(df)} records to {table}")

    def upsert_users(self, df: pd.DataFrame):
        """
        UPSERT users: Update if exists, insert if not.

        Uses SQLite's INSERT OR REPLACE syntax.
        """
        sql = """
        INSERT OR REPLACE INTO users
        (id, email, first_name, last_name, age, country, status, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        records = df.to_records(index=False)
        data = list(records)

        cursor = self.conn.cursor()
        cursor.executemany(sql, data)
        self.conn.commit()

        logger.info(f"Upserted {len(df)} users")
        return cursor.rowcount

    def get_record_count(self, table: str) -> int:
        """Get record count from table."""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        return count

def main():
    """Test database loading."""
    data_dir = Path(__file__).parents[2] / 'data' / 'raw'
    users_file = data_dir / 'users_clean.csv'

    if not users_file.exists():
        print("⚠️  Data file not found. Run data generation first.")
        return

    # Load sample data
    df = pd.read_csv(users_file, nrows=1000)
    print(f"Loaded {len(df)} sample records")

    # Setup database
    db_dir = Path(__file__).parents[2] / 'data' / 'databases'
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / 'etl_exercise.db'

    # Load to database
    loader = DatabaseLoader(str(db_path))
    loader.connect()

    try:
        print("\nCreating table...")
        loader.create_users_table()

        print("Loading data...")
        loader.load_dataframe(df, 'users', if_exists='replace')

        count = loader.get_record_count('users')
        print(f"✓ Loaded {count} records to database")

        # Test upsert
        print("\nTesting UPSERT...")
        df_update = df.head(10).copy()
        df_update['status'] = 'updated'
        loader.upsert_users(df_update)

        count_after = loader.get_record_count('users')
        print(f"✓ Count after upsert: {count_after} (should be same as before)")

    finally:
        loader.close()

    print(f"\n✓ Database created at: {db_path}")

if __name__ == '__main__':
    main()
