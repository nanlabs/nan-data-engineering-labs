"""
Test suite for Exercise 01: Basic Queries

Tests cover:
- SELECT projection
- WHERE filtering
- Pattern matching (LIKE, IN, BETWEEN)
- Sorting (ORDER BY)
- Pagination (LIMIT, OFFSET)
- Combined queries
"""

import pytest
from conftest import (
    assert_query_returns_columns,
    assert_query_returns_n_rows,
    assert_results_ordered_by
)


@pytest.mark.exercise01
class TestProjection:
    """Test basic SELECT and projection queries."""

    def test_select_specific_columns(self, execute_query):
        """Test selecting specific columns from users."""
        query = """
        SELECT first_name, last_name, email
        FROM users
        LIMIT 5
        """
        results = execute_query(query)

        assert_query_returns_n_rows(results, 5)
        assert_query_returns_columns(results, ['first_name', 'last_name', 'email'])

    def test_column_aliases(self, execute_query):
        """Test using column aliases."""
        query = """
        SELECT
            product_name AS nombre_producto,
            price AS precio
        FROM products
        LIMIT 5
        """
        results = execute_query(query)

        assert_query_returns_columns(results, ['nombre_producto', 'precio'])

    def test_exclude_columns(self, execute_query):
        """Test selecting all columns except timestamps."""
        query = """
        SELECT
            product_id,
            product_name,
            category,
            price,
            stock_quantity,
            description,
            is_available
        FROM products
        LIMIT 1
        """
        results = execute_query(query)

        # Ensure created_at and updated_at are NOT in results
        assert 'created_at' not in results[0]
        assert 'updated_at' not in results[0]


@pytest.mark.exercise01
class TestFiltering:
    """Test WHERE clause filtering."""

    def test_simple_equality(self, execute_query):
        """Test simple WHERE with equality."""
        query = """
        SELECT * FROM users
        WHERE country = 'US'
        """
        results = execute_query(query)

        # All results should have country = 'US'
        assert all(row['country'] == 'US' for row in results)

    def test_multiple_conditions_and(self, execute_query):
        """Test WHERE with AND conditions."""
        query = """
        SELECT * FROM users
        WHERE country = 'US' AND is_active = TRUE
        """
        results = execute_query(query)

        assert all(
            row['country'] == 'US' and row['is_active'] is True
            for row in results
        )

    def test_comparison_operators(self, execute_query):
        """Test numeric comparison operators."""
        query = """
        SELECT * FROM products
        WHERE price < 50
        """
        results = execute_query(query)

        assert all(row['price'] < 50 for row in results)

    def test_in_operator(self, execute_query):
        """Test IN operator."""
        query = """
        SELECT * FROM orders
        WHERE status IN ('delivered', 'shipped')
        """
        results = execute_query(query)

        assert all(row['status'] in ('delivered', 'shipped') for row in results)

    def test_not_in_operator(self, execute_query):
        """Test NOT IN operator."""
        query = """
        SELECT * FROM users
        WHERE country NOT IN ('US', 'GB', 'CA')
        """
        results = execute_query(query)

        assert all(row['country'] not in ('US', 'GB', 'CA') for row in results)


@pytest.mark.exercise01
class TestPatternMatching:
    """Test pattern matching with LIKE, BETWEEN, etc."""

    def test_like_ends_with(self, execute_query):
        """Test LIKE for emails ending with @gmail.com."""
        query = """
        SELECT * FROM users
        WHERE email LIKE '%@gmail.com'
        """
        results = execute_query(query)

        assert all(row['email'].endswith('@gmail.com') for row in results)

    def test_like_contains(self, execute_query):
        """Test LIKE for products containing 'Laptop'."""
        query = """
        SELECT * FROM products
        WHERE product_name LIKE '%Laptop%'
        """
        results = execute_query(query)

        assert all('Laptop' in row['product_name'] for row in results)

    def test_like_starts_with(self, execute_query):
        """Test LIKE for names starting with 'J'."""
        query = """
        SELECT * FROM users
        WHERE first_name LIKE 'J%'
        """
        results = execute_query(query)

        assert all(row['first_name'].startswith('J') for row in results)

    def test_between_operator(self, execute_query):
        """Test BETWEEN operator for price range."""
        query = """
        SELECT * FROM products
        WHERE price BETWEEN 20 AND 100
        """
        results = execute_query(query)

        assert all(20 <= row['price'] <= 100 for row in results)

    def test_is_null(self, execute_query):
        """Test IS NULL for tracking numbers."""
        query = """
        SELECT * FROM orders
        WHERE tracking_number IS NULL
        """
        results = execute_query(query)

        assert all(row['tracking_number'] is None for row in results)


@pytest.mark.exercise01
class TestSorting:
    """Test ORDER BY sorting."""

    def test_order_by_desc(self, execute_query):
        """Test descending order."""
        query = """
        SELECT * FROM users
        ORDER BY loyalty_points DESC
        LIMIT 10
        """
        results = execute_query(query)

        assert_results_ordered_by(results, 'loyalty_points', descending=True)

    def test_order_by_asc(self, execute_query):
        """Test ascending order."""
        query = """
        SELECT * FROM products
        ORDER BY price ASC
        LIMIT 10
        """
        results = execute_query(query)

        assert_results_ordered_by(results, 'price', descending=False)

    def test_order_by_multiple_columns(self, execute_query):
        """Test ordering by multiple columns."""
        query = """
        SELECT * FROM users
        ORDER BY country ASC, registration_date ASC
        LIMIT 20
        """
        results = execute_query(query)

        # Check that primary sort is by country
        countries = [row['country'] for row in results]
        assert countries == sorted(countries)


@pytest.mark.exercise01
class TestPagination:
    """Test LIMIT and OFFSET for pagination."""

    def test_limit_basic(self, execute_query):
        """Test basic LIMIT."""
        query = """
        SELECT * FROM users
        ORDER BY user_id
        LIMIT 10
        """
        results = execute_query(query)

        assert_query_returns_n_rows(results, 10)

    def test_limit_with_offset(self, execute_query):
        """Test LIMIT with OFFSET for pagination."""
        # Page 1
        query_page1 = """
        SELECT user_id FROM users
        ORDER BY user_id
        LIMIT 5 OFFSET 0
        """
        page1 = execute_query(query_page1)

        # Page 2
        query_page2 = """
        SELECT user_id FROM users
        ORDER BY user_id
        LIMIT 5 OFFSET 5
        """
        page2 = execute_query(query_page2)

        # Verify no overlap
        page1_ids = {row['user_id'] for row in page1}
        page2_ids = {row['user_id'] for row in page2}
        assert len(page1_ids & page2_ids) == 0, "Pages should not overlap"

    def test_pagination_formula(self, execute_query):
        """Test pagination formula: OFFSET = (page - 1) * size."""
        page_size = 10
        page_number = 3
        offset = (page_number - 1) * page_size

        query = f"""
        SELECT * FROM users
        ORDER BY user_id
        LIMIT {page_size} OFFSET {offset}
        """
        results = execute_query(query)

        assert len(results) <= page_size


@pytest.mark.exercise01
class TestCombinedQueries:
    """Test complex queries combining multiple concepts."""

    def test_filter_and_sort(self, execute_query):
        """Test filtering with sorting."""
        query = """
        SELECT * FROM users
        WHERE is_active = TRUE
          AND country IN ('US', 'GB')
          AND loyalty_points > 100
        ORDER BY loyalty_points DESC
        """
        results = execute_query(query)

        # Verify all conditions
        assert all(
            row['is_active'] is True and
            row['country'] in ('US', 'GB') and
            row['loyalty_points'] > 100
            for row in results
        )

        # Verify ordering
        if len(results) > 1:
            assert_results_ordered_by(results, 'loyalty_points', descending=True)

    def test_pattern_with_sort_and_limit(self, execute_query):
        """Test LIKE with ORDER BY and LIMIT."""
        query = """
        SELECT * FROM products
        WHERE is_available = TRUE
          AND price BETWEEN 20 AND 100
        ORDER BY price ASC
        LIMIT 10
        """
        results = execute_query(query)

        assert len(results) <= 10
        assert all(
            row['is_available'] is True and
            20 <= row['price'] <= 100
            for row in results
        )

    def test_complex_where_clause(self, execute_query):
        """Test complex WHERE with multiple AND/OR."""
        query = """
        SELECT * FROM users
        WHERE is_active = TRUE
          AND country NOT IN ('US')
          AND email LIKE '%@gmail.com'
          AND loyalty_points >= 50
        ORDER BY loyalty_points DESC
        LIMIT 10
        """
        results = execute_query(query)

        assert all(
            row['is_active'] is True and
            row['country'] != 'US' and
            '@gmail.com' in row['email'] and
            row['loyalty_points'] >= 50
            for row in results
        )
