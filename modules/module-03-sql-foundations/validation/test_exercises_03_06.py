"""
Consolidated test suite for Exercises 03-06.

Covers:
- Exercise 03: Aggregations (GROUP BY, HAVING)
- Exercise 04: Window Functions (ROW_NUMBER, RANK, LAG, LEAD)
- Exercise 05: CTEs & Subqueries
- Exercise 06: Query Optimization (EXPLAIN analysis)
"""

import pytest
from conftest import assert_query_returns_columns


# =============================================================================
# EXERCISE 03: AGGREGATIONS
# =============================================================================

@pytest.mark.exercise03
class TestAggregations:
    """Test aggregate functions and GROUP BY."""

    def test_count_and_sum(self, execute_query):
        """Test COUNT and SUM aggregates."""
        query = """
        SELECT
            COUNT(*) AS total_orders,
            SUM(total_amount) AS total_revenue
        FROM orders
        """
        results = execute_query(query)

        assert len(results) == 1
        assert results[0]['total_orders'] > 0
        assert results[0]['total_revenue'] > 0

    def test_group_by_basic(self, execute_query):
        """Test basic GROUP BY."""
        query = """
        SELECT
            user_id,
            COUNT(*) AS num_orders,
            SUM(total_amount) AS total_spent
        FROM orders
        GROUP BY user_id
        """
        results = execute_query(query)

        # Should have one row per user who has orders
        assert all(row['num_orders'] > 0 for row in results)

    def test_having_clause(self, execute_query):
        """Test HAVING to filter aggregated results."""
        query = """
        SELECT
            user_id,
            COUNT(*) AS num_orders
        FROM orders
        GROUP BY user_id
        HAVING COUNT(*) > 2
        """
        results = execute_query(query)

        # All results should have more than 2 orders
        assert all(row['num_orders'] > 2 for row in results)

    def test_aggregation_with_join(self, execute_query):
        """Test aggregations across joined tables."""
        query = """
        SELECT
            p.category,
            COUNT(DISTINCT p.product_id) AS num_products,
            SUM(oi.quantity) AS total_sold
        FROM products p
        INNER JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.category
        """
        results = execute_query(query)

        assert all(
            row['num_products'] > 0 and
            row['total_sold'] > 0
            for row in results
        )


# =============================================================================
# EXERCISE 04: WINDOW FUNCTIONS
# =============================================================================

@pytest.mark.exercise04
class TestWindowFunctions:
    """Test window functions."""

    def test_row_number(self, execute_query):
        """Test ROW_NUMBER() window function."""
        query = """
        SELECT
            product_name,
            price,
            ROW_NUMBER() OVER (ORDER BY price DESC) AS rank
        FROM products
        LIMIT 10
        """
        results = execute_query(query)

        # Verify ranks are sequential
        ranks = [row['rank'] for row in results]
        assert ranks == list(range(1, len(results) + 1))

    def test_partition_by(self, execute_query):
        """Test PARTITION BY in window function."""
        query = """
        SELECT
            product_name,
            category,
            price,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) AS rank_in_category
        FROM products
        """
        results = execute_query(query)

        # Each category should have rank starting at 1
        categories_seen = {}
        for row in results:
            cat = row['category']
            rank = row['rank_in_category']

            if cat not in categories_seen:
                assert rank == 1, f"First rank in {cat} should be 1"
                categories_seen[cat] = rank

    def test_lag_lead(self, execute_query):
        """Test LAG and LEAD functions."""
        query = """
        SELECT
            order_id,
            order_date,
            total_amount,
            LAG(total_amount) OVER (ORDER BY order_date) AS previous_order
        FROM orders
        ORDER BY order_date
        LIMIT 10
        """
        results = execute_query(query)

        # First row should have NULL for LAG
        assert results[0]['previous_order'] is None

        # Second row's previous_order should equal first row's total_amount
        if len(results) > 1:
            assert results[1]['previous_order'] == results[0]['total_amount']

    def test_running_total(self, execute_query):
        """Test running total with window function."""
        query = """
        SELECT
            order_date,
            total_amount,
            SUM(total_amount) OVER (ORDER BY order_date) AS running_total
        FROM orders
        ORDER BY order_date
        LIMIT 10
        """
        results = execute_query(query)

        # Running total should be monotonically increasing
        running_totals = [row['running_total'] for row in results]
        assert all(
            running_totals[i] <= running_totals[i+1]
            for i in range(len(running_totals)-1)
        )


# =============================================================================
# EXERCISE 05: CTEs & SUBQUERIES
# =============================================================================

@pytest.mark.exercise05
class TestCTEsAndSubqueries:
    """Test Common Table Expressions and subqueries."""

    def test_basic_cte(self, execute_query):
        """Test basic CTE."""
        query = """
        WITH high_value_orders AS (
            SELECT * FROM orders WHERE total_amount > 500
        )
        SELECT
            u.first_name,
            hvo.order_id,
            hvo.total_amount
        FROM high_value_orders hvo
        INNER JOIN users u ON hvo.user_id = u.user_id
        """
        results = execute_query(query)

        # All results should have total_amount > 500
        assert all(row['total_amount'] > 500 for row in results)

    def test_multiple_ctes(self, execute_query):
        """Test chaining multiple CTEs."""
        query = """
        WITH
        user_stats AS (
            SELECT
                user_id,
                COUNT(*) AS num_orders
            FROM orders
            GROUP BY user_id
        ),
        active_users AS (
            SELECT * FROM user_stats WHERE num_orders > 1
        )
        SELECT
            u.first_name,
            au.num_orders
        FROM users u
        INNER JOIN active_users au ON u.user_id = au.user_id
        """
        results = execute_query(query)

        assert all(row['num_orders'] > 1 for row in results)

    def test_subquery_in_where(self, execute_query):
        """Test subquery in WHERE clause."""
        query = """
        SELECT *
        FROM products
        WHERE price > (SELECT AVG(price) FROM products)
        """
        results = execute_query(query)

        # Get average price
        avg_query = "SELECT AVG(price) as avg_price FROM products"
        avg_price = execute_query(avg_query)[0]['avg_price']

        # All results should be above average
        assert all(row['price'] > avg_price for row in results)

    def test_subquery_in_select(self, execute_query):
        """Test subquery in SELECT clause."""
        query = """
        SELECT
            product_name,
            price,
            (SELECT AVG(price) FROM products) AS avg_price,
            price - (SELECT AVG(price) FROM products) AS diff_from_avg
        FROM products
        LIMIT 10
        """
        results = execute_query(query)

        assert_query_returns_columns(
            results,
            ['product_name', 'price', 'avg_price', 'diff_from_avg']
        )


# =============================================================================
# EXERCISE 06: QUERY OPTIMIZATION
# =============================================================================

@pytest.mark.exercise06
@pytest.mark.slow
class TestQueryOptimization:
    """Test query optimization concepts."""

    def test_explain_basic(self, execute_query):
        """Test that EXPLAIN returns a query plan."""
        query = "EXPLAIN SELECT * FROM users WHERE user_id = 1"
        results = execute_query(query)

        # EXPLAIN should return at least one row
        assert len(results) > 0

    def test_index_usage(self, execute_query):
        """Test that queries can use indexes."""
        # This query should use an index on user_id (from FK)
        query = """
        EXPLAIN SELECT * FROM orders WHERE user_id = 5
        """
        results = execute_query(query)

        # Should have some execution plan
        assert len(results) > 0

    def test_join_optimization(self, execute_query):
        """Test JOIN query performance."""
        # Selective query (using specific filters)
        query = """
        SELECT COUNT(*) as count
        FROM orders o
        INNER JOIN users u ON o.user_id = u.user_id
        WHERE o.status = 'delivered'
        """
        results = execute_query(query)

        assert results[0]['count'] >= 0

    def test_limit_performance(self, execute_query):
        """Test that LIMIT reduces result set."""
        query_without_limit = "SELECT * FROM orders"
        query_with_limit = "SELECT * FROM orders LIMIT 10"

        results_all = execute_query(query_without_limit)
        results_limited = execute_query(query_with_limit)

        assert len(results_limited) <= 10
        assert len(results_limited) < len(results_all)

    def test_exists_vs_in(self, execute_query):
        """Test EXISTS and IN produce same results."""
        # Using IN
        query_in = """
        SELECT user_id
        FROM users u
        WHERE user_id IN (SELECT user_id FROM orders)
        ORDER BY user_id
        """
        results_in = execute_query(query_in)

        # Using EXISTS
        query_exists = """
        SELECT user_id
        FROM users u
        WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id)
        ORDER BY user_id
        """
        results_exists = execute_query(query_exists)

        # Should return same users
        assert len(results_in) == len(results_exists)

        ids_in = {row['user_id'] for row in results_in}
        ids_exists = {row['user_id'] for row in results_exists}
        assert ids_in == ids_exists


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.slow
class TestIntegration:
    """Integration tests combining multiple concepts."""

    def test_complex_analytics_query(self, execute_query):
        """Test complex query combining JOINs, aggregations, and window functions."""
        query = """
        WITH user_spending AS (
            SELECT
                u.user_id,
                u.first_name || ' ' || u.last_name AS customer,
                COUNT(DISTINCT o.order_id) AS num_orders,
                SUM(o.total_amount) AS total_spent
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.first_name, u.last_name
        )
        SELECT
            customer,
            num_orders,
            total_spent,
            ROW_NUMBER() OVER (ORDER BY total_spent DESC) AS spending_rank
        FROM user_spending
        WHERE num_orders > 0
        ORDER BY total_spent DESC
        LIMIT 10
        """
        results = execute_query(query)

        assert len(results) <= 10
        assert all(row['num_orders'] > 0 for row in results)

        # Verify ranks are sequential
        ranks = [row['spending_rank'] for row in results]
        assert ranks == list(range(1, len(results) + 1))
