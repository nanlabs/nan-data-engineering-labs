#!/usr/bin/env python3
"""
Exercise 03: Time Travel and Data Recovery - Validation Script
===============================================================

This script validates the completion of Time Travel and recovery exercise.

Validation Criteria (100 points total):
- Historical data tracking (15 points)
- Time Travel queries (20 points)
- UNDROP operations (20 points)
- Point-in-time recovery (25 points)
- Retention configuration (10 points)
- Disaster recovery documentation (10 points)
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


class TimeTravelValidator:
    """Validates Time Travel and recovery exercise completion."""

    def __init__(self, connection_params: Dict[str, str]):
        """Initialize validator with Snowflake connection parameters."""
        self.connection_params = connection_params
        self.conn = None
        self.score = 0
        self.max_score = 100

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

    def validate_historical_tracking(self) -> int:
        """Validate historical data tracking (15 points)."""
        print("\n" + "="*70)
        print("TEST 1: Historical Data Tracking (15 points)")
        print("="*70)

        points = 0

        # Check if time_travel_demo database exists
        query = "SHOW DATABASES LIKE 'TIME_TRAVEL_DEMO'"
        databases = self.execute_query(query)

        if not databases:
            print("❌ Database TIME_TRAVEL_DEMO not found")
            return points

        print("✅ Time Travel demo database exists")
        points += 5

        # Check if orders table has data
        query = "SELECT COUNT(*) as cnt FROM time_travel_demo.recovery.orders"
        result = self.execute_query(query)

        if result and result[0]['CNT'] > 0:
            row_count = result[0]['CNT']
            print(f"✅ Orders table exists with {row_count:,} rows")
            points += 5

            # Check for status variations (indicating updates were made)
            query = """
                SELECT
                    COUNT(DISTINCT status) as status_count,
                    COUNT(*) as total_rows
                FROM time_travel_demo.recovery.orders
            """
            result = self.execute_query(query)

            if result and result[0]['STATUS_COUNT'] >= 2:
                print(f"✅ Multiple status values found ({result[0]['STATUS_COUNT']} types)")
                points += 5
            else:
                print("⚠️  Limited status variation (updates may not have been performed)")
                points += 2
        else:
            print("❌ Orders table not found or empty")

        print(f"\nSubscore: {points}/15")
        return points

    def validate_time_travel_queries(self) -> int:
        """Validate Time Travel query capability (20 points)."""
        print("\n" + "="*70)
        print("TEST 2: Time Travel Queries (20 points)")
        print("="*70)

        points = 0

        # Test Time Travel with OFFSET
        query = """
            SELECT COUNT(*) as cnt
            FROM time_travel_demo.recovery.orders
            AT(OFFSET => -60)
        """

        try:
            result = self.execute_query(query)
            if result:
                print("✅ Time Travel query with OFFSET works")
                print(f"   Row count 60 seconds ago: {result[0]['CNT']:,}")
                points += 10
        except Exception:
            print("⚠️  Time Travel query with OFFSET failed")
            print("   (May be outside retention window)")
            points += 3

        # Test ability to query table information
        query = """
            SELECT
                table_name,
                retention_time
            FROM time_travel_demo.information_schema.tables
            WHERE table_schema = 'RECOVERY'
                AND table_name = 'ORDERS'
        """

        result = self.execute_query(query)
        if result and result[0]['RETENTION_TIME'] is not None:
            retention = result[0]['RETENTION_TIME']
            print(f"✅ Can query retention settings: {retention} days")
            points += 5
        else:
            print("⚠️  Unable to query retention settings")
            points += 2

        # Check for historical clones (evidence of Time Travel usage)
        query = """
            SHOW TABLES LIKE '%1HR_AGO%' IN SCHEMA time_travel_demo.recovery
        """
        result = self.execute_query(query)

        if result:
            print("✅ Historical clone table found")
            points += 5
        else:
            print("⚠️  No historical clone tables found")
            points += 2

        print(f"\nSubscore: {points}/20")
        return points

    def validate_undrop_capability(self) -> int:
        """Validate UNDROP operations (20 points)."""
        print("\n" + "="*70)
        print("TEST 3: UNDROP Operations (20 points)")
        print("="*70)

        points = 0

        # Check if customer_data table exists (should exist after UNDROP)
        query = "SHOW TABLES LIKE 'CUSTOMER_DATA' IN SCHEMA time_travel_demo.recovery"
        result = self.execute_query(query)

        if result:
            print("✅ customer_data table exists (UNDROP successful)")
            points += 10

            # Verify it has data
            query = "SELECT COUNT(*) as cnt FROM time_travel_demo.recovery.customer_data"
            result = self.execute_query(query)

            if result and result[0]['CNT'] > 0:
                print(f"   └─ Contains {result[0]['CNT']:,} rows")
                points += 5
        else:
            print("⚠️  customer_data table not found (UNDROP may not have been tested)")
            points += 3

        # Check if test_schema exists (UNDROP schema test)
        query = "SHOW SCHEMAS LIKE 'TEST_SCHEMA' IN DATABASE time_travel_demo"
        result = self.execute_query(query)

        if result:
            print("✅ test_schema exists (Schema UNDROP successful)")
            points += 5
        else:
            print("⚠️  test_schema not found (Schema UNDROP may not have been tested)")
            points += 2

        print(f"\nSubscore: {points}/20")
        return points

    def validate_point_in_time_recovery(self) -> int:
        """Validate point-in-time recovery (25 points)."""
        print("\n" + "="*70)
        print("TEST 4: Point-in-Time Recovery (25 points)")
        print("="*70)

        points = 0

        # Check if financial_transactions table exists
        query = "SHOW TABLES LIKE 'FINANCIAL_TRANSACTIONS' IN SCHEMA time_travel_demo.recovery"
        result = self.execute_query(query)

        if not result:
            print("❌ financial_transactions table not found")
            return points

        print("✅ financial_transactions table exists")
        points += 5

        # Check data integrity (no corruption)
        query = """
            SELECT
                COUNT(*) as total_rows,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                COUNT(CASE WHEN amount = 0 THEN 1 END) as zero_amount_count,
                COUNT(CASE WHEN transaction_type = 'corrupted' THEN 1 END) as corrupted_count
            FROM time_travel_demo.recovery.financial_transactions
        """
        result = self.execute_query(query)

        if result:
            row = result[0]
            total_rows = row['TOTAL_ROWS']
            total_amount = row['TOTAL_AMOUNT']
            zero_count = row['ZERO_AMOUNT_COUNT']
            corrupted_count = row['CORRUPTED_COUNT']

            print("\n📊 Transaction Data Analysis:")
            print(f"   Total transactions: {total_rows:,}")
            print(f"   Total amount: ${total_amount:,.2f}" if total_amount else "   Total amount: $0.00")
            print(f"   Zero amounts: {zero_count}")
            print(f"   Corrupted records: {corrupted_count}")

            # Recovery was successful if no corrupted data
            if corrupted_count == 0 and zero_count < total_rows * 0.1:
                print("✅ Data appears recovered (no corruption detected)")
                points += 15
            elif corrupted_count > 0 or zero_count > total_rows * 0.3:
                print("⚠️  Data may still be corrupted")
                points += 5
            else:
                print("⚠️  Some anomalies detected but mostly clean")
                points += 10

            # Check that recovery process was executed
            if total_rows >= 400:  # Should have ~500 rows if recovery succeeded
                print(f"✅ Row count looks healthy ({total_rows:,} rows)")
                points += 5
            else:
                print("⚠️  Row count lower than expected")
                points += 2

        print(f"\nSubscore: {points}/25")
        return points

    def validate_retention_config(self) -> int:
        """Validate retention configuration (10 points)."""
        print("\n" + "="*70)
        print("TEST 5: Retention Configuration (10 points)")
        print("="*70)

        points = 0

        # Check retention settings for financial_transactions
        query = """
            SELECT
                table_name,
                retention_time
            FROM time_travel_demo.information_schema.tables
            WHERE table_schema = 'RECOVERY'
                AND table_name = 'FINANCIAL_TRANSACTIONS'
        """

        result = self.execute_query(query)

        if result and result[0]['RETENTION_TIME'] is not None:
            retention = result[0]['RETENTION_TIME']
            print(f"✅ financial_transactions retention: {retention} days")

            if retention >= 90:
                print("   └─ Extended retention configured (Enterprise Edition)")
                points += 10
            elif retention >= 7:
                print("   └─ Standard retention configured")
                points += 7
            else:
                print("   └─ Minimal retention configured")
                points += 5
        else:
            print("⚠️  Unable to query retention settings")
            points += 3

        print(f"\nSubscore: {points}/10")
        return points

    def validate_disaster_recovery_plan(self, solution_file: str) -> int:
        """Validate disaster recovery documentation (10 points)."""
        print("\n" + "="*70)
        print("TEST 6: Disaster Recovery Documentation (10 points)")
        print("="*70)

        points = 0

        if not os.path.exists(solution_file):
            print(f"❌ Solution file not found: {solution_file}")
            return points

        with open(solution_file, 'r') as f:
            content = f.read()

        # Define the 5 required scenarios
        required_scenarios = [
            'Accidental Table Drop',
            'Bulk Data Corruption',
            'Malicious Data Deletion',
            'Application Bug',
            'Transaction Rollback'
        ]

        found_scenarios = 0
        for scenario in required_scenarios:
            if scenario.lower() in content.lower():
                found_scenarios += 1

        if found_scenarios >= 5:
            print("✅ All 5 disaster recovery scenarios documented")
            points += 5
        elif found_scenarios >= 3:
            print(f"⚠️  {found_scenarios} scenarios documented (expected 5)")
            points += 3
        else:
            print(f"❌ Insufficient scenarios documented ({found_scenarios} found)")
            points += 1

        # Check for SQL examples in scenarios
        sql_examples = re.findall(r'(UNDROP|CLONE|AT\(|BEFORE\()', content, re.IGNORECASE)

        if len(sql_examples) >= 5:
            print(f"✅ SQL recovery examples provided ({len(sql_examples)} found)")
            points += 5
        elif len(sql_examples) >= 3:
            print(f"⚠️  Limited SQL examples ({len(sql_examples)} found)")
            points += 3
        else:
            print("❌ Insufficient SQL examples")
            points += 1

        print(f"\nSubscore: {points}/10")
        return points

    def run_validation(self, solution_file: str) -> Tuple[int, int]:
        """Run all validation tests."""
        print("\n" + "="*70)
        print("TIME TRAVEL AND DATA RECOVERY EXERCISE VALIDATION")
        print("="*70)

        if not self.connect():
            return 0, self.max_score

        try:
            self.score += self.validate_historical_tracking()
            self.score += self.validate_time_travel_queries()
            self.score += self.validate_undrop_capability()
            self.score += self.validate_point_in_time_recovery()
            self.score += self.validate_retention_config()
            self.score += self.validate_disaster_recovery_plan(solution_file)

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
    # Connection parameters
    connection_params = {
        'user': os.getenv('SNOWFLAKE_USER', 'your_username'),
        'password': os.getenv('SNOWFLAKE_PASSWORD', 'your_password'),
        'account': os.getenv('SNOWFLAKE_ACCOUNT', 'your_account'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOWFLAKE_DATABASE', 'TIME_TRAVEL_DEMO'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', 'RECOVERY')
    }

    # Get solution file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solution_file = os.path.join(script_dir, 'solution.sql')

    # Run validation
    validator = TimeTravelValidator(connection_params)
    score, max_score = validator.run_validation(solution_file)
    validator.print_final_report()

    # Exit with appropriate code
    sys.exit(0 if score >= max_score * 0.7 else 1)


if __name__ == '__main__':
    main()
