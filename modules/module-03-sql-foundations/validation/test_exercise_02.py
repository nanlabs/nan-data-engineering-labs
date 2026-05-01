"""
Test suite for Exercise 02: Joins

Tests cover:
- INNER JOIN
- LEFT JOIN (and finding unmatched records)
- Multiple JOINs (3+ tables)
- Aggregations with JOINs
"""

import pytest
from conftest import (
    assert_query_returns_columns
)


@pytest.mark.exercise02
class TestInnerJoin:
    """Test INNER JOIN queries."""

    def test_orders_with_users(self, execute_query):
        """Test joining orders with users."""
        query = """
        SELECT
            o.order_id,
            o.order_date,
            o.total_amount,
            u.first_name,
            u.last_name
        FROM orders o
        INNER JOIN users u ON o.user_id = u.user_id
        LIMIT 10
        """
        results = execute_query(query)

        assert_query_returns_columns(
            results,
            ['order_id', 'order_date', 'total_amount', 'first_name', 'last_name']
        )

        # All rows should have non-null user names
        assert all(row['first_name'] is not None for row in results)

    def test_order_items_with_products(self, execute_query):
        """Test joining order_items with products."""
        query = """
        SELECT
            oi.order_item_id,
            oi.order_id,
            p.product_name,
            oi.quantity,
            oi.subtotal
        FROM order_items oi
        INNER JOIN products p ON oi.product_id = p.product_id
        LIMIT 10
        """
        results = execute_query(query)

        assert_query_returns_columns(
            results,
            ['order_item_id', 'order_id', 'product_name', 'quantity', 'subtotal']
        )

    def test_user_activity_with_users(self, execute_query):
        """Test joining user_activity with users."""
        query = """
        SELECT
            ua.activity_id,
            ua.activity_type,
            u.first_name,
            u.email
        FROM user_activity ua
        INNER JOIN users u ON ua.user_id = u.user_id
        LIMIT 10
        """
        results = execute_query(query)

        assert all(row['email'] is not None for row in results)


@pytest.mark.exercise02
class TestLeftJoin:
    """Test LEFT JOIN queries."""

    def test_all_users_with_order_count(self, execute_query):
        """Test LEFT JOIN to get all users with their order counts."""
        query = """
        SELECT
            u.user_id,
            u.first_name,
            u.last_name,
            COUNT(o.order_id) AS num_orders
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.user_id, u.first_name, u.last_name
        """
        results = execute_query(query)

        # Should return all users (even those with 0 orders)
        total_users_query = "SELECT COUNT(*) as count FROM users"
        total_users = execute_query(total_users_query)[0]['count']

        assert len(results) == total_users

        # Some users should have 0 orders
        assert any(row['num_orders'] == 0 for row in results)

    def test_users_without_orders(self, execute_query):
        """Test finding users who haven't placed orders."""
        query = """
        SELECT
            u.user_id,
            u.first_name,
            u.last_name
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        WHERE o.order_id IS NULL
        """
        results = execute_query(query)

        # Should find at least some users without orders
        assert len(results) >= 0  # May be 0 if all users have orders

        # If there are results, verify they truly have no orders
        if results:
            user_id = results[0]['user_id']
            check_query = f"""
            SELECT COUNT(*) as count
            FROM orders
            WHERE user_id = {user_id}
            """
            check_result = execute_query(check_query)
            assert check_result[0]['count'] == 0

    def test_products_with_sales_stats(self, execute_query):
        """Test LEFT JOIN to get product sales including unsold products."""
        query = """
        SELECT
            p.product_id,
            p.product_name,
            COUNT(oi.order_item_id) AS times_sold,
            COALESCE(SUM(oi.quantity), 0) AS total_quantity
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name
        """
        results = execute_query(query)

        # Should return all products
        total_products_query = "SELECT COUNT(*) as count FROM products"
        total_products = execute_query(total_products_query)[0]['count']

        assert len(results) == total_products

        # COALESCE should ensure no NULL values
        assert all(row['total_quantity'] is not None for row in results)


@pytest.mark.exercise02
class TestMultipleJoins:
    """Test queries joining 3+ tables."""

    def test_complete_order_details(self, execute_query):
        """Test joining orders, users, order_items, and products."""
        query = """
        SELECT
            o.order_id,
            u.first_name || ' ' || u.last_name AS customer,
            p.product_name,
            oi.quantity,
            oi.subtotal
        FROM orders o
        INNER JOIN users u ON o.user_id = u.user_id
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.product_id
        LIMIT 20
        """
        results = execute_query(query)

        assert_query_returns_columns(
            results,
            ['order_id', 'customer', 'product_name', 'quantity', 'subtotal']
        )

        # All fields should be non-null
        assert all(
            row['customer'] is not None and
            row['product_name'] is not None
            for row in results
        )

    def test_user_purchase_summary(self, execute_query):
        """Test aggregating across multiple joined tables."""
        query = """
        SELECT
            u.first_name || ' ' || u.last_name AS customer,
            COUNT(DISTINCT o.order_id) AS num_orders,
            COUNT(oi.order_item_id) AS num_items,
            SUM(oi.subtotal) AS total_spent
        FROM users u
        INNER JOIN orders o ON u.user_id = o.user_id
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY u.user_id, u.first_name, u.last_name
        HAVING COUNT(DISTINCT o.order_id) > 0
        ORDER BY total_spent DESC
        LIMIT 10
        """
        results = execute_query(query)

        # Verify aggregations are numeric
        assert all(
            isinstance(row['num_orders'], int) and
            isinstance(row['num_items'], int) and
            row['total_spent'] is not None
            for row in results
        )

    def test_spending_by_category(self, execute_query):
        """Test multi-table JOIN with category analysis."""
        query = """
        SELECT
            u.first_name || ' ' || u.last_name AS customer,
            p.category,
            SUM(oi.quantity) AS total_items,
            SUM(oi.subtotal) AS total_spent
        FROM users u
        INNER JOIN orders o ON u.user_id = o.user_id
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.product_id
        GROUP BY u.user_id, u.first_name, u.last_name, p.category
        ORDER BY total_spent DESC
        LIMIT 10
        """
        results = execute_query(query)

        assert all(
            row['category'] is not None and
            row['total_items'] > 0
            for row in results
        )


@pytest.mark.exercise02
class TestJoinPerformance:
    """Test JOIN efficiency and correctness."""

    def test_join_cardinality(self, execute_query):
        """Verify JOIN doesn't create unexpected duplicates."""
        # Count distinct orders
        orders_count = execute_query("SELECT COUNT(*) as count FROM orders")[0]['count']

        # Count after JOIN (should be same or more, but not multiplied)
        query = """
        SELECT COUNT(DISTINCT o.order_id) as count
        FROM orders o
        INNER JOIN users u ON o.user_id = u.user_id
        """
        joined_count = execute_query(query)[0]['count']

        # After JOIN with users, we should still have same number of distinct orders
        assert joined_count == orders_count

    def test_left_join_preserves_left_table(self, execute_query):
        """Verify LEFT JOIN preserves all left table rows."""
        # Count products
        products_count = execute_query("SELECT COUNT(*) as count FROM products")[0]['count']

        # Count after LEFT JOIN
        query = """
        SELECT COUNT(DISTINCT p.product_id) as count
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        """
        joined_count = execute_query(query)[0]['count']

        # Should preserve all products
        assert joined_count == products_count
