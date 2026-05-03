#!/usr/bin/env python3
"""
Exercise 01: Warehouse Optimization - Validation Script
========================================================

This script validates the completion of warehouse optimization exercise.

Validation Criteria (100 points total):
- Warehouse creation and configuration (20 points)
- Test data setup (15 points)
- Performance testing completion (25 points)
- Auto-suspend configuration (15 points)
- Credit monitoring queries (15 points)
- Optimization strategies documented (10 points)
"""

import sys
import os
from typing import Dict, List, Tuple
import re

# Add shared utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'utilities'))

try:
    import snowflake.connector
    from snowflake.connector import DictCursor
except ImportError:
    print("❌ Error: snowflake-connector-python not installed")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)


class WarehouseOptimizationValidator:
    """Validates warehouse optimization exercise completion."""

    def __init__(self, connection_params: Dict[str, str]):
        """Initialize validator with Snowflake connection parameters."""
        self.connection_params = connection_params
        self.conn = None
        self.score = 0
        self.max_score = 100
        self.results = []

    def connect(self) -> bool:
        """Establish connection to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(**self.connection_params)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def execute_query(self, query: str) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        try:
            cursor = self.conn.cursor(DictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"Query error: {str(e)}")
            return []

    def validate_warehouses(self) -> int:
        """Validate warehouse creation and configuration (20 points)."""
        print("\n" + "="*70)
        print("TEST 1: Warehouse Creation and Configuration (20 points)")
        print("="*70)

        points = 0
        required_warehouses = {
            'COMPUTE_WH_XSMALL': 'X-SMALL',
            'COMPUTE_WH_MEDIUM': 'MEDIUM',
            'COMPUTE_WH_LARGE': 'LARGE'
        }

        query = "SHOW WAREHOUSES LIKE 'COMPUTE_WH_%'"
        warehouses = self.execute_query(query)

        for wh_name, expected_size in required_warehouses.items():
            found = False
            for wh in warehouses:
                if wh['name'] == wh_name:
                    found = True
                    if wh['size'] == expected_size:
                        print(f"✅ {wh_name} created with correct size: {expected_size}")
                        points += 5
                    else:
                        print(f"⚠️  {wh_name} has incorrect size: {wh['size']} (expected {expected_size})")
                        points += 2

                    # Check auto-suspend configuration
                    auto_suspend = wh.get('auto_suspend', 0)
                    if auto_suspend > 0:
                        print(f"   └─ Auto-suspend: {auto_suspend} seconds")
                        points += 1
                    break

            if not found:
                print(f"❌ {wh_name} not found")

        # Check for multi-cluster warehouse
        multi_cluster = [wh for wh in warehouses if wh['name'] == 'COMPUTE_WH_MULTI']
        if multi_cluster:
            wh = multi_cluster[0]
            if wh.get('max_cluster_count', 1) > 1:
                print(f"✅ Multi-cluster warehouse configured (min={wh.get('min_cluster_count')}, max={wh.get('max_cluster_count')})")
                points += 2
            else:
                print("⚠️  COMPUTE_WH_MULTI exists but not configured as multi-cluster")

        print(f"\nSubscore: {points}/20")
        return points

    def validate_test_data(self) -> int:
        """Validate test data creation (15 points)."""
        print("\n" + "="*70)
        print("TEST 2: Test Data Setup (15 points)")
        print("="*70)

        points = 0

        # Check database exists
        query = "SHOW DATABASES LIKE 'WAREHOUSE_OPTIMIZATION_DB'"
        databases = self.execute_query(query)

        if databases:
            print("✅ Database WAREHOUSE_OPTIMIZATION_DB exists")
            points += 3

            # Use the database
            self.execute_query("USE DATABASE WAREHOUSE_OPTIMIZATION_DB")
            self.execute_query("USE SCHEMA PERFORMANCE_TESTING")

            # Check tables
            tables_to_check = {
                'SALES_FACT': (800000, 1200000),
                'CUSTOMER_DIMENSION': (80000, 120000),
                'PRODUCT_DIMENSION': (8000, 12000)
            }

            for table_name, (min_rows, max_rows) in tables_to_check.items():
                query = f"SELECT COUNT(*) as cnt FROM {table_name}"
                result = self.execute_query(query)

                if result:
                    row_count = result[0]['CNT']
                    if min_rows <= row_count <= max_rows:
                        print(f"✅ {table_name}: {row_count:,} rows")
                        points += 4
                    else:
                        print(f"⚠️  {table_name}: {row_count:,} rows (expected {min_rows:,}-{max_rows:,})")
                        points += 2
                else:
                    print(f"❌ {table_name} not found or empty")
        else:
            print("❌ Database WAREHOUSE_OPTIMIZATION_DB not found")

        print(f"\nSubscore: {points}/15")
        return points

    def validate_performance_testing(self) -> int:
        """Validate performance testing (25 points)."""
        print("\n" + "="*70)
        print("TEST 3: Performance Testing (25 points)")
        print("="*70)

        points = 0

        # Check if performance results table exists
        query = "SELECT COUNT(*) as cnt FROM PERFORMANCE_RESULTS"
        result = self.execute_query(query)

        if result and result[0]['CNT'] >= 3:
            test_count = result[0]['CNT']
            print(f"✅ Performance results table exists with {test_count} test runs")
            points += 10

            # Analyze performance results
            query = """
                SELECT
                    warehouse_size,
                    execution_time_ms,
                    query_description
                FROM PERFORMANCE_RESULTS
                ORDER BY test_id DESC
                LIMIT 3
            """
            results = self.execute_query(query)

            if results:
                print("\n📊 Performance Test Results:")
                for result in results:
                    print(f"   {result['WAREHOUSE_SIZE']:10} - {result['EXECUTION_TIME_MS']:8,}ms")
                    points += 5

                print("✅ Performance comparison completed across warehouse sizes")
        else:
            print("❌ Performance results table not found or insufficient test runs")
            print("   Expected at least 3 test runs (one per warehouse size)")

        print(f"\nSubscore: {points}/25")
        return points

    def validate_auto_suspend(self) -> int:
        """Validate auto-suspend configuration (15 points)."""
        print("\n" + "="*70)
        print("TEST 4: Auto-Suspend Configuration (15 points)")
        print("="*70)

        points = 0

        query = "SHOW WAREHOUSES LIKE 'COMPUTE_WH_%'"
        warehouses = self.execute_query(query)

        config_checks = {
            'COMPUTE_WH_XSMALL': (30, 120),    # 30s - 2min acceptable
            'COMPUTE_WH_MEDIUM': (120, 600),    # 2min - 10min acceptable
            'COMPUTE_WH_LARGE': (180, 900)      # 3min - 15min acceptable
        }

        for wh_name, (min_suspend, max_suspend) in config_checks.items():
            wh = [w for w in warehouses if w['name'] == wh_name]
            if wh:
                auto_suspend = wh[0].get('auto_suspend', 0)
                auto_resume = wh[0].get('auto_resume', False)

                if min_suspend <= auto_suspend <= max_suspend:
                    print(f"✅ {wh_name}: {auto_suspend}s auto-suspend (within best practice range)")
                    points += 4
                elif auto_suspend > 0:
                    print(f"⚠️  {wh_name}: {auto_suspend}s auto-suspend (outside optimal range)")
                    points += 2
                else:
                    print(f"❌ {wh_name}: Auto-suspend not configured")

                if auto_resume:
                    points += 1

        print(f"\nSubscore: {points}/15")
        return points

    def validate_credit_monitoring(self) -> int:
        """Validate credit monitoring implementation (15 points)."""
        print("\n" + "="*70)
        print("TEST 5: Credit Monitoring (15 points)")
        print("="*70)

        points = 0

        # Check if user can query account usage
        query = """
            SELECT COUNT(*) as cnt
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            WHERE start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
            LIMIT 1
        """

        try:
            result = self.execute_query(query)
            if result:
                print("✅ Can query WAREHOUSE_METERING_HISTORY")
                points += 10
                print("✅ Credit monitoring queries are accessible")
                points += 5
        except Exception:
            print("⚠️  Limited access to ACCOUNT_USAGE views")
            print("   (This is normal for non-ACCOUNTADMIN roles)")
            points += 5

        print(f"\nSubscore: {points}/15")
        return points

    def validate_optimization_strategies(self, solution_file: str) -> int:
        """Validate optimization strategies documentation (10 points)."""
        print("\n" + "="*70)
        print("TEST 6: Optimization Strategies Documentation (10 points)")
        print("="*70)

        points = 0

        if not os.path.exists(solution_file):
            print(f"❌ Solution file not found: {solution_file}")
            return points

        with open(solution_file, 'r') as f:
            content = f.read()

        # Check for documented strategies
        strategy_pattern = r'(OPTIMIZATION STRATEGY|Strategy \d+:|-- Strategy)'
        strategies = re.findall(strategy_pattern, content, re.IGNORECASE)

        if len(strategies) >= 5:
            print(f"✅ Found {len(strategies)} optimization strategies documented")
            points += 5
        elif len(strategies) >= 3:
            print(f"⚠️  Found {len(strategies)} optimization strategies (expected 5+)")
            points += 3
        else:
            print(f"❌ Insufficient optimization strategies documented (found {len(strategies)})")

        # Check for savings estimates
        savings_pattern = r'(savings|cost reduction|Expected Savings)'
        savings = re.findall(savings_pattern, content, re.IGNORECASE)

        if len(savings) >= 5:
            print("✅ Savings estimates documented")
            points += 5
        elif len(savings) >= 3:
            print("⚠️  Partial savings estimates documented")
            points += 2

        print(f"\nSubscore: {points}/10")
        return points

    def run_validation(self, solution_file: str) -> Tuple[int, int]:
        """Run all validation tests."""
        print("\n" + "="*70)
        print("WAREHOUSE OPTIMIZATION EXERCISE VALIDATION")
        print("="*70)

        if not self.connect():
            return 0, self.max_score

        try:
            self.score += self.validate_warehouses()
            self.score += self.validate_test_data()
            self.score += self.validate_performance_testing()
            self.score += self.validate_auto_suspend()
            self.score += self.validate_credit_monitoring()
            self.score += self.validate_optimization_strategies(solution_file)

        finally:
            if self.conn:
                self.conn.close()

        return self.score, self.max_score

    def print_final_report(self):
        """Print final validation report with grade."""
        print("\n" + "="*70)
        print("FINAL VALIDATION REPORT")
        print("="*70)

        percentage = (self.score / self.max_score) * 100

        print(f"\nTotal Score: {self.score}/{self.max_score} ({percentage:.1f}%)")

        if percentage >= 90:
            grade = "A"
            emoji = "🏆"
            message = "Excellent work!"
        elif percentage >= 80:
            grade = "B"
            emoji = "🎯"
            message = "Good job!"
        elif percentage >= 70:
            grade = "C"
            emoji = "👍"
            message = "Satisfactory"
        elif percentage >= 60:
            grade = "D"
            emoji = "📚"
            message = "Needs improvement"
        else:
            grade = "F"
            emoji = "❌"
            message = "Please review and retry"

        print(f"Grade: {grade} {emoji}")
        print(f"Status: {message}")
        print("="*70)


def main():
    """Main validation function."""
    # Connection parameters (adjust as needed)
    connection_params = {
        'user': os.getenv('SNOWFLAKE_USER', 'your_username'),
        'password': os.getenv('SNOWFLAKE_PASSWORD', 'your_password'),
        'account': os.getenv('SNOWFLAKE_ACCOUNT', 'your_account'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOWFLAKE_DATABASE', 'WAREHOUSE_OPTIMIZATION_DB'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', 'PERFORMANCE_TESTING')
    }

    # Get solution file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solution_file = os.path.join(script_dir, 'solution.sql')

    # Run validation
    validator = WarehouseOptimizationValidator(connection_params)
    score, max_score = validator.run_validation(solution_file)
    validator.print_final_report()

    # Exit with appropriate code
    sys.exit(0 if score >= max_score * 0.7 else 1)


if __name__ == '__main__':
    main()
