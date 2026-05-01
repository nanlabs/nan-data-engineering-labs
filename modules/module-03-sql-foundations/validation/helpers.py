"""
Helper utilities for SQL query validation and testing.

Provides:
- Query result comparison
- Schema validation
- Performance benchmarking
- Data quality checks
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import time


def normalize_value(value: Any) -> Any:
    """
    Normalize a value for comparison (handle Decimal, None, etc.).

    Args:
        value: Value to normalize

    Returns:
        Normalized value
    """
    if isinstance(value, Decimal):
        return float(value)
    return value


def compare_results(actual: List[Dict], expected: List[Dict],
                   ignore_order: bool = False) -> tuple[bool, str]:
    """
    Compare two result sets for equality.

    Args:
        actual: Actual query results
        expected: Expected query results
        ignore_order: Whether to ignore row ordering

    Returns:
        (is_equal, message): Boolean and descriptive message
    """
    if len(actual) != len(expected):
        return False, f"Row count mismatch: {len(actual)} != {len(expected)}"

    if not actual and not expected:
        return True, "Both result sets empty"

    # Normalize values
    actual_normalized = [
        {k: normalize_value(v) for k, v in row.items()}
        for row in actual
    ]
    expected_normalized = [
        {k: normalize_value(v) for k, v in row.items()}
        for row in expected
    ]

    if ignore_order:
        # Convert to sorted tuples for comparison
        actual_set = {
            tuple(sorted(row.items()))
            for row in actual_normalized
        }
        expected_set = {
            tuple(sorted(row.items()))
            for row in expected_normalized
        }

        if actual_set == expected_set:
            return True, "Results match (order ignored)"
        else:
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            msg = []
            if missing:
                msg.append(f"Missing rows: {len(missing)}")
            if extra:
                msg.append(f"Extra rows: {len(extra)}")
            return False, "; ".join(msg)
    else:
        # Compare row by row
        for i, (actual_row, expected_row) in enumerate(zip(actual_normalized, expected_normalized)):
            if actual_row != expected_row:
                return False, f"Row {i} mismatch: {actual_row} != {expected_row}"

        return True, "Results match (order preserved)"


def validate_schema(results: List[Dict], expected_columns: List[str],
                    require_all: bool = True) -> tuple[bool, str]:
    """
    Validate that query results have expected columns.

    Args:
        results: Query results
        expected_columns: List of expected column names
        require_all: If True, requires exact match; if False, allows extra columns

    Returns:
        (is_valid, message): Boolean and descriptive message
    """
    if not results:
        return False, "No results to validate"

    actual_columns = set(results[0].keys())
    expected_set = set(expected_columns)

    missing = expected_set - actual_columns
    extra = actual_columns - expected_set

    if missing:
        return False, f"Missing columns: {missing}"

    if require_all and extra:
        return False, f"Unexpected columns: {extra}"

    return True, "Schema valid"


def benchmark_query(cursor, query: str, iterations: int = 5) -> Dict[str, float]:
    """
    Benchmark a query's execution time.

    Args:
        cursor: Database cursor
        query: SQL query to benchmark
        iterations: Number of iterations to run

    Returns:
        Dict with min, max, avg, median execution times
    """
    times = []

    for _ in range(iterations):
        start = time.time()
        cursor.execute(query)
        cursor.fetchall()
        end = time.time()
        times.append(end - start)

    times_sorted = sorted(times)
    median_idx = len(times) // 2

    return {
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'median': times_sorted[median_idx] if len(times) % 2 == 1
                  else (times_sorted[median_idx-1] + times_sorted[median_idx]) / 2,
        'iterations': iterations
    }


def check_data_quality(results: List[Dict], checks: Dict[str, callable]) -> tuple[bool, List[str]]:
    """
    Run data quality checks on results.

    Args:
        results: Query results
        checks: Dict of check_name -> check_function(row)

    Returns:
        (all_passed, failed_checks): Boolean and list of failed check names
    """
    failed = []

    for check_name, check_func in checks.items():
        try:
            for i, row in enumerate(results):
                if not check_func(row):
                    failed.append(f"{check_name} failed at row {i}")
                    break
        except Exception as e:
            failed.append(f"{check_name} raised exception: {e}")

    return len(failed) == 0, failed


def assert_no_nulls(results: List[Dict], columns: List[str]) -> None:
    """
    Assert that specified columns have no NULL values.

    Args:
        results: Query results
        columns: List of column names to check

    Raises:
        AssertionError: If NULL found
    """
    for i, row in enumerate(results):
        for col in columns:
            if col not in row:
                raise AssertionError(f"Column {col} not in results")
            if row[col] is None:
                raise AssertionError(f"NULL found in {col} at row {i}")


def assert_unique(results: List[Dict], column: str) -> None:
    """
    Assert that column values are unique across results.

    Args:
        results: Query results
        column: Column name to check

    Raises:
        AssertionError: If duplicates found
    """
    values = [row[column] for row in results]
    unique_values = set(values)

    if len(values) != len(unique_values):
        duplicates = [v for v in values if values.count(v) > 1]
        raise AssertionError(
            f"Duplicate values found in {column}: {set(duplicates)}"
        )


def assert_range(results: List[Dict], column: str,
                min_val: Optional[Any] = None,
                max_val: Optional[Any] = None) -> None:
    """
    Assert that column values are within specified range.

    Args:
        results: Query results
        column: Column name to check
        min_val: Minimum value (inclusive), None to skip
        max_val: Maximum value (inclusive), None to skip

    Raises:
        AssertionError: If values outside range
    """
    for i, row in enumerate(results):
        value = row[column]

        if min_val is not None and value < min_val:
            raise AssertionError(
                f"Value {value} in {column} at row {i} is below minimum {min_val}"
            )

        if max_val is not None and value > max_val:
            raise AssertionError(
                f"Value {value} in {column} at row {i} is above maximum {max_val}"
            )


def get_query_plan(cursor, query: str) -> List[str]:
    """
    Get EXPLAIN output for a query.

    Args:
        cursor: Database cursor
        query: SQL query

    Returns:
        List of plan lines
    """
    cursor.execute(f"EXPLAIN {query}")
    return [row[0] for row in cursor.fetchall()]


def estimate_query_cost(cursor, query: str) -> Dict[str, Any]:
    """
    Estimate query cost using EXPLAIN.

    Args:
        cursor: Database cursor
        query: SQL query

    Returns:
        Dict with cost estimates
    """
    cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
    plan = cursor.fetchone()[0][0]

    return {
        'total_cost': plan.get('Plan', {}).get('Total Cost'),
        'startup_cost': plan.get('Plan', {}).get('Startup Cost'),
        'plan_rows': plan.get('Plan', {}).get('Plan Rows'),
        'plan_width': plan.get('Plan', {}).get('Plan Width'),
    }


def format_results_table(results: List[Dict], max_rows: int = 10) -> str:
    """
    Format query results as a readable table string.

    Args:
        results: Query results
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not results:
        return "No results"

    # Get column names and widths
    columns = list(results[0].keys())
    col_widths = {
        col: max(len(str(col)), max(len(str(row[col])) for row in results[:max_rows]))
        for col in columns
    }

    # Header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)

    # Rows
    rows = []
    for i, row in enumerate(results[:max_rows]):
        rows.append(
            " | ".join(str(row[col]).ljust(col_widths[col]) for col in columns)
        )

    # Footer if truncated
    footer = f"\n... ({len(results) - max_rows} more rows)" if len(results) > max_rows else ""

    return f"{header}\n{separator}\n" + "\n".join(rows) + footer


# Common validation patterns
class QueryValidator:
    """Helper class for common query validation patterns."""

    @staticmethod
    def validate_pagination(cursor, base_query: str, page_size: int = 10) -> bool:
        """
        Validate that pagination works correctly.

        Args:
            cursor: Database cursor
            base_query: Base query without LIMIT/OFFSET
            page_size: Page size to test

        Returns:
            True if pagination works correctly
        """
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({base_query}) subq"
        cursor.execute(count_query)
        total = cursor.fetchone()[0]

        # Fetch pages
        all_ids = []
        offset = 0

        while offset < total:
            page_query = f"{base_query} LIMIT {page_size} OFFSET {offset}"
            cursor.execute(page_query)
            page_results = cursor.fetchall()

            if not page_results:
                break

            # Assuming first column is an ID
            page_ids = [row[0] for row in page_results]
            all_ids.extend(page_ids)

            offset += page_size

        # Check no duplicates
        return len(all_ids) == len(set(all_ids))

    @staticmethod
    def validate_join_integrity(cursor, left_table: str, right_table: str,
                                join_key: str) -> tuple[bool, str]:
        """
        Validate JOIN integrity between two tables.

        Args:
            cursor: Database cursor
            left_table: Left table name
            right_table: Right table name
            join_key: Column used for joining

        Returns:
            (is_valid, message): Boolean and descriptive message
        """
        # Check for orphaned records
        query = f"""
        SELECT COUNT(*) as count
        FROM {left_table} l
        LEFT JOIN {right_table} r ON l.{join_key} = r.{join_key}
        WHERE r.{join_key} IS NULL
        """
        cursor.execute(query)
        orphaned = cursor.fetchone()[0]

        if orphaned > 0:
            return False, f"Found {orphaned} orphaned records in {left_table}"

        return True, "JOIN integrity validated"
