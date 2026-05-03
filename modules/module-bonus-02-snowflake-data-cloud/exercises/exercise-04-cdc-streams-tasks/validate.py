#!/usr/bin/env python3
"""
Exercise 04: CDC Streams and Tasks - Validation Script
Validates the implementation of Snowflake CDC pipeline with streams and tasks.
"""

import os
import sys
import snowflake.connector
from snowflake.connector import DictCursor


class CDCValidator:
    """Validator for CDC Streams and Tasks exercise."""

    def __init__(self):
        """Initialize validator with Snowflake connection."""
        self.conn = None
        self.cursor = None
        self.score = 0
        self.max_score = 100
        self.results = []

    def connect(self) -> bool:
        """Establish Snowflake connection."""
        try:
            self.conn = snowflake.connector.connect(
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                user=os.getenv('SNOWFLAKE_USER'),
                password=os.getenv('SNOWFLAKE_PASSWORD'),
                warehouse='TRAINING_WH',
                database='CDC_LAB',
                schema='PIPELINE'
            )
            self.cursor = self.conn.cursor(DictCursor)
            print("✓ Connected to Snowflake successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Snowflake: {e}")
            return False

    def close(self):
        """Close Snowflake connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def add_result(self, test_name: str, passed: bool, points: int, message: str):
        """Add test result."""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'points': points if passed else 0,
            'message': message
        })
        if passed:
            self.score += points

    def validate_bronze_setup(self) -> None:
        """Validate bronze layer setup (15 points)."""
        print("\n=== Validating Bronze Layer Setup ===")

        # Check bronze_orders table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'PIPELINE'
                AND TABLE_NAME = 'BRONZE_ORDERS'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('bronze_table_exists', True, 5,
                              'bronze_orders table exists')
            else:
                self.add_result('bronze_table_exists', False, 5,
                              'bronze_orders table not found')
                return
        except Exception as e:
            self.add_result('bronze_table_exists', False, 5, f'Error: {e}')
            return

        # Check data volume (5 points)
        try:
            self.cursor.execute("SELECT COUNT(*) as cnt FROM bronze_orders")
            result = self.cursor.fetchone()
            count = result['CNT']
            if count >= 1000:
                self.add_result('bronze_data_volume', True, 5,
                              f'bronze_orders has {count} records')
            else:
                self.add_result('bronze_data_volume', False, 5,
                              f'Expected >= 1000 records, found {count}')
        except Exception as e:
            self.add_result('bronze_data_volume', False, 5, f'Error: {e}')

        # Check required columns (5 points)
        try:
            self.cursor.execute("DESC TABLE bronze_orders")
            columns = {row['name'].upper() for row in self.cursor.fetchall()}
            required = {'ORDER_ID', 'CUSTOMER_ID', 'PRODUCT', 'AMOUNT',
                       'STATUS', 'CREATED_AT'}
            if required.issubset(columns):
                self.add_result('bronze_columns', True, 5,
                              'All required columns present')
            else:
                missing = required - columns
                self.add_result('bronze_columns', False, 5,
                              f'Missing columns: {missing}')
        except Exception as e:
            self.add_result('bronze_columns', False, 5, f'Error: {e}')

    def validate_stream_setup(self) -> None:
        """Validate stream configuration (20 points)."""
        print("\n=== Validating Stream Setup ===")

        # Check stream exists (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'PIPELINE'
                AND TABLE_NAME = 'ORDERS_STREAM'
                AND TABLE_TYPE = 'STREAM'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('stream_exists', True, 10,
                              'orders_stream exists')
            else:
                self.add_result('stream_exists', False, 10,
                              'orders_stream not found')
                return
        except Exception as e:
            self.add_result('stream_exists', False, 10, f'Error: {e}')
            return

        # Check stream captures changes (10 points)
        try:
            # Verify stream is on bronze_orders
            self.cursor.execute("SHOW STREAMS LIKE 'ORDERS_STREAM'")
            stream_info = self.cursor.fetchone()
            if stream_info and 'BRONZE_ORDERS' in stream_info['table_name'].upper():
                self.add_result('stream_config', True, 10,
                              'Stream correctly configured on bronze_orders')
            else:
                self.add_result('stream_config', False, 10,
                              'Stream not properly configured')
        except Exception as e:
            self.add_result('stream_config', False, 10, f'Error: {e}')

    def validate_silver_layer(self) -> None:
        """Validate silver layer transformation (20 points)."""
        print("\n=== Validating Silver Layer ===")

        # Check silver_orders table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'PIPELINE'
                AND TABLE_NAME = 'SILVER_ORDERS'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('silver_table_exists', True, 5,
                              'silver_orders table exists')
            else:
                self.add_result('silver_table_exists', False, 5,
                              'silver_orders table not found')
                return
        except Exception as e:
            self.add_result('silver_table_exists', False, 5, f'Error: {e}')
            return

        # Check silver has CDC tracking columns (5 points)
        try:
            self.cursor.execute("DESC TABLE silver_orders")
            columns = {row['name'].upper() for row in self.cursor.fetchall()}
            cdc_columns = {'UPDATED_AT', 'IS_DELETED'}
            if cdc_columns.issubset(columns):
                self.add_result('silver_cdc_columns', True, 5,
                              'CDC tracking columns present')
            else:
                self.add_result('silver_cdc_columns', False, 5,
                              'Missing CDC tracking columns')
        except Exception as e:
            self.add_result('silver_cdc_columns', False, 5, f'Error: {e}')

        # Check data consistency (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as silver_cnt FROM silver_orders WHERE NOT IS_DELETED
            """)
            silver_count = self.cursor.fetchone()['SILVER_CNT']

            self.cursor.execute("SELECT COUNT(*) as bronze_cnt FROM bronze_orders")
            bronze_count = self.cursor.fetchone()['BRONZE_CNT']

            # Allow some variance for in-flight changes
            variance = abs(silver_count - bronze_count) / bronze_count
            if variance < 0.05:  # Within 5%
                self.add_result('data_consistency', True, 10,
                              f'Data consistent: Bronze={bronze_count}, Silver={silver_count}')
            else:
                self.add_result('data_consistency', False, 10,
                              f'Data inconsistency: Bronze={bronze_count}, Silver={silver_count}')
        except Exception as e:
            self.add_result('data_consistency', False, 10, f'Error: {e}')

    def validate_tasks(self) -> None:
        """Validate task configuration (25 points)."""
        print("\n=== Validating Tasks ===")

        # Check tasks exist (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TASKS
                WHERE SCHEMA_NAME = 'PIPELINE'
                AND NAME IN ('EXTRACT_FROM_BRONZE', 'TRANSFORM_TO_SILVER', 'AGGREGATE_TO_GOLD')
            """)
            result = self.cursor.fetchone()
            task_count = result['CNT']
            if task_count >= 3:
                self.add_result('tasks_exist', True, 10,
                              f'Found {task_count} tasks in DAG')
            else:
                self.add_result('tasks_exist', False, 10,
                              f'Expected 3 tasks, found {task_count}')
        except Exception as e:
            self.add_result('tasks_exist', False, 10, f'Error: {e}')

        # Check task dependencies (10 points)
        try:
            self.cursor.execute("""
                SELECT NAME, PREDECESSORS
                FROM INFORMATION_SCHEMA.TASKS
                WHERE SCHEMA_NAME = 'PIPELINE'
                AND NAME IN ('TRANSFORM_TO_SILVER', 'AGGREGATE_TO_GOLD')
            """)
            tasks = self.cursor.fetchall()
            has_dependencies = all(row['PREDECESSORS'] for row in tasks)
            if has_dependencies:
                self.add_result('task_dependencies', True, 10,
                              'Task dependencies properly configured')
            else:
                self.add_result('task_dependencies', False, 10,
                              'Task dependencies not configured')
        except Exception as e:
            self.add_result('task_dependencies', False, 10, f'Error: {e}')

        # Check task execution history (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
                    SCHEDULED_TIME_RANGE_START => DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
                ))
                WHERE SCHEMA_NAME = 'PIPELINE' AND STATE = 'SUCCEEDED'
            """)
            result = self.cursor.fetchone()
            exec_count = result['CNT']
            if exec_count > 0:
                self.add_result('task_execution', True, 5,
                              f'{exec_count} successful task executions')
            else:
                self.add_result('task_execution', False, 5,
                              'No successful task executions found')
        except Exception as e:
            self.add_result('task_execution', False, 5, f'Error: {e}')

    def validate_gold_layer(self) -> None:
        """Validate gold layer aggregations (15 points)."""
        print("\n=== Validating Gold Layer ===")

        # Check gold table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'PIPELINE'
                AND TABLE_NAME = 'GOLD_DAILY_SALES'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('gold_table_exists', True, 5,
                              'gold_daily_sales table exists')
            else:
                self.add_result('gold_table_exists', False, 5,
                              'gold_daily_sales table not found')
                return
        except Exception as e:
            self.add_result('gold_table_exists', False, 5, f'Error: {e}')
            return

        # Check aggregation accuracy (10 points)
        try:
            # Get aggregated data from gold
            self.cursor.execute("""
                SELECT SUM(TOTAL_REVENUE) as gold_revenue
                FROM gold_daily_sales
            """)
            gold_revenue = self.cursor.fetchone()['GOLD_REVENUE']

            # Calculate from silver
            self.cursor.execute("""
                SELECT SUM(AMOUNT) as silver_revenue
                FROM silver_orders
                WHERE NOT IS_DELETED
            """)
            silver_revenue = self.cursor.fetchone()['SILVER_REVENUE']

            if gold_revenue and silver_revenue:
                variance = abs(gold_revenue - silver_revenue) / silver_revenue
                if variance < 0.01:  # Within 1%
                    self.add_result('aggregation_accuracy', True, 10,
                                  f'Gold aggregations accurate: {gold_revenue:.2f}')
                else:
                    self.add_result('aggregation_accuracy', False, 10,
                                  f'Aggregation mismatch: Gold={gold_revenue:.2f}, Expected≈{silver_revenue:.2f}')
            else:
                self.add_result('aggregation_accuracy', False, 10,
                              'Missing aggregation data')
        except Exception as e:
            self.add_result('aggregation_accuracy', False, 10, f'Error: {e}')

    def validate_error_handling(self) -> None:
        """Validate error handling implementation (5 points)."""
        print("\n=== Validating Error Handling ===")

        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'PIPELINE'
                AND TABLE_NAME = 'ERROR_LOG'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('error_handling', True, 5,
                              'Error logging table exists')
            else:
                self.add_result('error_handling', False, 5,
                              'Error logging not implemented')
        except Exception as e:
            self.add_result('error_handling', False, 5, f'Error: {e}')

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)

        for result in self.results:
            status = "✓" if result['passed'] else "✗"
            print(f"{status} {result['test']}: {result['message']} "
                  f"({result['points']} points)")

        print("="*70)
        print(f"TOTAL SCORE: {self.score}/{self.max_score}")
        print("="*70)

        if self.score >= 90:
            print("🎉 Excellent! CDC pipeline implemented correctly!")
        elif self.score >= 70:
            print("👍 Good work! Minor improvements needed.")
        elif self.score >= 50:
            print("📚 Keep going! Review the solution for guidance.")
        else:
            print("🔧 Needs work. Check the solution and try again.")

    def run_all_validations(self):
        """Run all validation tests."""
        if not self.connect():
            return False

        try:
            self.validate_bronze_setup()
            self.validate_stream_setup()
            self.validate_silver_layer()
            self.validate_tasks()
            self.validate_gold_layer()
            self.validate_error_handling()
            self.print_summary()
            return True
        except Exception as e:
            print(f"\n✗ Validation failed with error: {e}")
            return False
        finally:
            self.close()


def main():
    """Main validation entry point."""
    print("="*70)
    print("Exercise 04: CDC Streams and Tasks - Validation")
    print("="*70)

    validator = CDCValidator()
    success = validator.run_all_validations()

    sys.exit(0 if success and validator.score >= 70 else 1)


if __name__ == "__main__":
    main()
