"""
Pytest configuration and fixtures for SQL Foundations module validation.

This module provides:
- Database connection fixtures
- Test data setup/teardown
- Query execution helpers
- Assertion utilities
"""

import os
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'ecommerce'),
    'user': os.getenv('POSTGRES_USER', 'dataengineer'),
    'password': os.getenv('POSTGRES_PASSWORD', 'training123')
}


@pytest.fixture(scope='session')
def db_connection():
    """
    Create a database connection that persists for the entire test session.

    Yields:
        psycopg2.connection: Database connection object
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def db_cursor(db_connection):
    """
    Create a cursor for each test function with automatic rollback.

    This fixture ensures test isolation - changes made during a test
    are rolled back after the test completes.

    Args:
        db_connection: Session-scoped database connection

    Yields:
        psycopg2.cursor: Cursor with RealDictCursor factory (returns dicts)
    """
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    db_connection.rollback()
    cursor.close()


@pytest.fixture(scope='function')
def execute_query(db_cursor):
    """
    Helper fixture to execute SQL queries and return results.

    Args:
        db_cursor: Function-scoped cursor

    Returns:
        function: Query execution function
    """
    def _execute(query, params=None):
        """
        Execute a query and return all results.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Query parameters for parameterized queries

        Returns:
            list[dict]: Query results as list of dictionaries
        """
        db_cursor.execute(query, params)
        try:
            return db_cursor.fetchall()
        except psycopg2.ProgrammingError:
            # Query doesn't return results (INSERT, UPDATE, etc.)
            return []

    return _execute


@pytest.fixture(scope='function')
def execute_file(db_cursor):
    """
    Helper fixture to execute SQL from a file.

    Args:
        db_cursor: Function-scoped cursor

    Returns:
        function: File execution function
    """
    def _execute(filepath):
        """
        Execute SQL statements from a file.

        Args:
            filepath (str): Path to SQL file

        Returns:
            list[dict]: Results from the last query in the file
        """
        with open(filepath, 'r') as f:
            sql = f.read()

        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        results = []

        for statement in statements:
            if statement:
                db_cursor.execute(statement)
                try:
                    results = db_cursor.fetchall()
                except psycopg2.ProgrammingError:
                    pass

        return results

    return _execute


@pytest.fixture(scope='session')
def verify_db_setup(db_connection):
    """
    Verify that the database is properly set up with required tables.

    This fixture runs once per session and checks that all expected
    tables exist with data.

    Args:
        db_connection: Session-scoped connection

    Raises:
        RuntimeError: If database setup is incomplete
    """
    cursor = db_connection.cursor()

    # Check required tables
    required_tables = ['users', 'products', 'orders', 'order_items', 'user_activity']
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    existing_tables = {row[0] for row in cursor.fetchall()}

    missing_tables = set(required_tables) - existing_tables
    if missing_tables:
        raise RuntimeError(
            f"Missing required tables: {missing_tables}. "
            f"Please run infrastructure/init.sql first."
        )

    # Check that tables have data
    for table in required_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count == 0:
            raise RuntimeError(
                f"Table {table} is empty. "
                f"Please ensure init.sql has been executed properly."
            )

    cursor.close()
    return True


@contextmanager
def temporary_table(cursor, table_name, schema):
    """
    Context manager for creating a temporary table that's automatically dropped.

    Args:
        cursor: Database cursor
        table_name (str): Name for temporary table
        schema (str): CREATE TABLE statement

    Yields:
        str: Table name
    """
    cursor.execute(schema)
    try:
        yield table_name
    finally:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")


def assert_query_returns_columns(results, expected_columns):
    """
    Assert that query results contain expected columns.

    Args:
        results (list[dict]): Query results
        expected_columns (list[str]): Expected column names

    Raises:
        AssertionError: If columns don't match
    """
    if not results:
        raise AssertionError("Query returned no results")

    actual_columns = set(results[0].keys())
    expected_set = set(expected_columns)

    missing = expected_set - actual_columns
    extra = actual_columns - expected_set

    errors = []
    if missing:
        errors.append(f"Missing columns: {missing}")
    if extra:
        errors.append(f"Unexpected columns: {extra}")

    if errors:
        raise AssertionError("; ".join(errors))


def assert_query_returns_n_rows(results, expected_count, operator='=='):
    """
    Assert that query returns expected number of rows.

    Args:
        results (list): Query results
        expected_count (int): Expected row count
        operator (str): Comparison operator ('==', '>', '<', '>=', '<=')

    Raises:
        AssertionError: If count doesn't match expectation
    """
    actual_count = len(results)

    operators = {
        '==': lambda a, b: a == b,
        '>': lambda a, b: a > b,
        '<': lambda a, b: a < b,
        '>=': lambda a, b: a >= b,
        '<=': lambda a, b: a <= b,
    }

    if operator not in operators:
        raise ValueError(f"Invalid operator: {operator}")

    if not operators[operator](actual_count, expected_count):
        raise AssertionError(
            f"Expected {operator} {expected_count} rows, got {actual_count}"
        )


def assert_results_ordered_by(results, column, descending=False):
    """
    Assert that results are properly ordered by a column.

    Args:
        results (list[dict]): Query results
        column (str): Column name to check ordering
        descending (bool): Whether order should be descending

    Raises:
        AssertionError: If results are not properly ordered
    """
    if len(results) < 2:
        return  # Can't check ordering with < 2 rows

    values = [row[column] for row in results]

    if descending:
        expected = sorted(values, reverse=True)
    else:
        expected = sorted(values)

    if values != expected:
        raise AssertionError(
            f"Results not properly ordered by {column} "
            f"({'DESC' if descending else 'ASC'})"
        )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "exercise01: tests for exercise 01 (basic queries)"
    )
    config.addinivalue_line(
        "markers", "exercise02: tests for exercise 02 (joins)"
    )
    config.addinivalue_line(
        "markers", "exercise03: tests for exercise 03 (aggregations)"
    )
    config.addinivalue_line(
        "markers", "exercise04: tests for exercise 04 (window functions)"
    )
    config.addinivalue_line(
        "markers", "exercise05: tests for exercise 05 (CTEs & subqueries)"
    )
    config.addinivalue_line(
        "markers", "exercise06: tests for exercise 06 (optimization)"
    )
