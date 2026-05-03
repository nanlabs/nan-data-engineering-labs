#!/usr/bin/env python3
"""
Exercise 02: Zero-Copy Cloning - Validation Script
===================================================

This script validates the completion of zero-copy cloning exercise.

Validation Criteria (100 points total):
- Production data setup (20 points)
- Database cloning (15 points)
- Table-level clones (15 points)
- Development modifications (20 points)
- Storage divergence tracking (15 points)
- Cost analysis documentation (15 points)
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


class ZeroCopyValidator:
    """Validates zero-copy cloning exercise completion."""

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

    def validate_production_data(self) -> int:
        """Validate production data setup (20 points)."""
        print("\n" + "="*70)
        print("TEST 1: Production Data Setup (20 points)")
        print("="*70)

        points = 0

        # Check if prod_db exists
        query = "SHOW DATABASES LIKE 'PROD_DB'"
        databases = self.execute_query(query)

        if not databases:
            print("❌ Production database (PROD_DB) not found")
            return points

        print("✅ Production database exists")
        points += 5

        # Check tables and row counts
        expected_tables = {
            'CUSTOMERS': (8000, 12000),
            'ORDERS': (40000, 60000),
            'ORDER_ITEMS': (120000, 180000)
        }

        for table_name, (min_rows, max_rows) in expected_tables.items():
            query = f"SELECT COUNT(*) as cnt FROM prod_db.sales.{table_name}"
            result = self.execute_query(query)

            if result:
                row_count = result[0]['CNT']
                if min_rows <= row_count <= max_rows:
                    print(f"✅ {table_name}: {row_count:,} rows")
                    points += 5
                else:
                    print(f"⚠️  {table_name}: {row_count:,} rows (expected {min_rows:,}-{max_rows:,})")
                    points += 2
            else:
                print(f"❌ {table_name} not found")

        print(f"\nSubscore: {points}/20")
        return points

    def validate_database_clone(self) -> int:
        """Validate database cloning (15 points)."""
        print("\n" + "="*70)
        print("TEST 2: Database Cloning (15 points)")
        print("="*70)

        points = 0

        # Check if dev_db exists
        query = "SHOW DATABASES LIKE 'DEV_DB'"
        databases = self.execute_query(query)

        if not databases:
            print("❌ Development database (DEV_DB) not found")
            return points

        print("✅ Development database exists")
        points += 5

        # Compare table counts
        query_prod = "SELECT COUNT(*) as cnt FROM prod_db.information_schema.tables WHERE table_schema = 'SALES'"
        query_dev = "SELECT COUNT(*) as cnt FROM dev_db.information_schema.tables WHERE table_schema = 'SALES'"

        prod_tables = self.execute_query(query_prod)
        dev_tables = self.execute_query(query_dev)

        if prod_tables and dev_tables:
            prod_count = prod_tables[0]['CNT']
            dev_count = dev_tables[0]['CNT']

            if prod_count == dev_count:
                print(f"✅ Table count matches: {prod_count} tables in both databases")
                points += 5
            else:
                print(f"⚠️  Table count mismatch: prod={prod_count}, dev={dev_count}")
                points += 2

        # Verify initial row counts match (before modifications)
        # Note: This may not match if modifications were already made
        print("\n📊 Comparing initial data volumes:")
        tables_to_check = ['CUSTOMERS', 'ORDERS', 'ORDER_ITEMS']

        for table in tables_to_check:
            query_prod = f"SELECT COUNT(*) as cnt FROM prod_db.sales.{table}"
            query_dev = f"SELECT COUNT(*) as cnt FROM dev_db.sales.{table}"

            prod_result = self.execute_query(query_prod)
            dev_result = self.execute_query(query_dev)

            if prod_result and dev_result:
                prod_cnt = prod_result[0]['CNT']
                dev_cnt = dev_result[0]['CNT']
                print(f"   {table}: prod={prod_cnt:,}, dev={dev_cnt:,}")

        points += 5
        print(f"\nSubscore: {points}/15")
        return points

    def validate_table_clones(self) -> int:
        """Validate table-level clones (15 points)."""
        print("\n" + "="*70)
        print("TEST 3: Table-Level Clones (15 points)")
        print("="*70)

        points = 0

        # Check for customers_test clone
        query = "SELECT COUNT(*) as cnt FROM prod_db.sales.customers_test"
        result = self.execute_query(query)

        if result and result[0]['CNT'] > 0:
            print(f"✅ customers_test clone exists with {result[0]['CNT']:,} rows")
            points += 5
        else:
            print("❌ customers_test clone not found")

        # Check for historical clones
        historical_tables = [
            'ORDERS_1HR_AGO',
            'ORDERS_HISTORICAL',
            'CUSTOMERS_30MIN_AGO',
            'CUSTOMERS_BEFORE_CHANGES'
        ]

        found_historical = 0
        for table in historical_tables:
            query = f"SHOW TABLES LIKE '{table}' IN SCHEMA prod_db.sales"
            result = self.execute_query(query)
            if result:
                found_historical += 1

        if found_historical >= 2:
            print(f"✅ Found {found_historical} time-travel clones")
            points += 5
        elif found_historical == 1:
            print(f"⚠️  Found only {found_historical} time-travel clone (expected 2+)")
            points += 3
        else:
            print("❌ No time-travel clones found")

        # Check for schema clone
        query = "SHOW SCHEMAS LIKE 'SALES_BACKUP' IN DATABASE prod_db"
        result = self.execute_query(query)

        if result:
            print("✅ sales_backup schema clone exists")
            points += 5
        else:
            print("❌ sales_backup schema clone not found")

        print(f"\nSubscore: {points}/15")
        return points

    def validate_dev_modifications(self) -> int:
        """Validate development modifications (20 points)."""
        print("\n" + "="*70)
        print("TEST 4: Development Modifications (20 points)")
        print("="*70)

        points = 0

        # Check if modifications were made in dev
        query_prod = "SELECT COUNT(*) as cnt FROM prod_db.sales.customers"
        query_dev = "SELECT COUNT(*) as cnt FROM dev_db.sales.customers"

        prod_result = self.execute_query(query_prod)
        dev_result = self.execute_query(query_dev)

        if prod_result and dev_result:
            prod_count = prod_result[0]['CNT']
            dev_count = dev_result[0]['CNT']

            if dev_count > prod_count:
                diff = dev_count - prod_count
                print(f"✅ Customers modified in dev: +{diff:,} rows")
                points += 7
            else:
                print("⚠️  No customer insertions detected in dev")
                points += 2

        # Check for updates in orders
        query = "SELECT COUNT(*) as cnt FROM dev_db.sales.orders WHERE status = 'test_status'"
        result = self.execute_query(query)

        if result and result[0]['CNT'] > 0:
            print(f"✅ Orders updated in dev: {result[0]['CNT']:,} test records")
            points += 7
        else:
            print("⚠️  No order updates detected in dev")
            points += 2

        # Verify prod is unchanged
        query = "SELECT COUNT(*) as cnt FROM prod_db.sales.orders WHERE status = 'test_status'"
        result = self.execute_query(query)

        if result and result[0]['CNT'] == 0:
            print("✅ Production data unchanged (no test_status in prod)")
            points += 6
        else:
            print("⚠️  Found test data in production (should be dev only)")

        print(f"\nSubscore: {points}/20")
        return points

    def validate_storage_tracking(self) -> int:
        """Validate storage divergence tracking (15 points)."""
        print("\n" + "="*70)
        print("TEST 5: Storage Divergence Tracking (15 points)")
        print("="*70)

        points = 0

        # Check if storage metrics are accessible
        query = """
            SELECT COUNT(*) as cnt
            FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
            WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
            LIMIT 1
        """

        try:
            result = self.execute_query(query)
            if result:
                print("✅ Can access TABLE_STORAGE_METRICS")
                points += 5

                # Try to get actual storage data
                query = """
                    SELECT
                        table_catalog,
                        table_name,
                        active_bytes / POWER(1024, 3) as active_gb
                    FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
                    WHERE table_catalog IN ('PROD_DB', 'DEV_DB')
                        AND table_schema = 'SALES'
                    ORDER BY active_gb DESC
                    LIMIT 5
                """
                storage_data = self.execute_query(query)

                if storage_data and len(storage_data) > 0:
                    print("\n📊 Storage Metrics Sample:")
                    for row in storage_data[:3]:
                        print(f"   {row['TABLE_CATALOG']}.{row['TABLE_NAME']}: {row['ACTIVE_GB']:.4f} GB")
                    points += 10
                else:
                    print("⚠️  Storage metrics data not yet populated (can take up to 3 hours)")
                    points += 5
        except Exception:
            print("⚠️  Limited access to storage metrics (normal for non-ACCOUNTADMIN)")
            points += 5

        print(f"\nSubscore: {points}/15")
        return points

    def validate_cost_analysis(self, solution_file: str) -> int:
        """Validate cost analysis documentation (15 points)."""
        print("\n" + "="*70)
        print("TEST 6: Cost Analysis Documentation (15 points)")
        print("="*70)

        points = 0

        if not os.path.exists(solution_file):
            print(f"❌ Solution file not found: {solution_file}")
            return points

        with open(solution_file, 'r') as f:
            content = f.read()

        # Check for cost analysis keywords
        cost_keywords = [
            'cost savings', 'storage cost', 'monthly cost',
            'traditional approach', 'zero-copy', 'savings percentage'
        ]

        found_keywords = sum(1 for keyword in cost_keywords if keyword.lower() in content.lower())

        if found_keywords >= 5:
            print(f"✅ Cost analysis documented ({found_keywords} key topics covered)")
            points += 8
        elif found_keywords >= 3:
            print(f"⚠️  Partial cost analysis ({found_keywords} key topics)")
            points += 5
        else:
            print("❌ Insufficient cost analysis documentation")

        # Check for benefit documentation
        benefit_pattern = r'(benefit|advantage|pro)'
        benefits = re.findall(benefit_pattern, content, re.IGNORECASE)

        if len(benefits) >= 3:
            print("✅ Benefits of zero-copy cloning documented")
            points += 7
        elif len(benefits) >= 1:
            print("⚠️  Limited benefit documentation")
            points += 3

        print(f"\nSubscore: {points}/15")
        return points

    def run_validation(self, solution_file: str) -> Tuple[int, int]:
        """Run all validation tests."""
        print("\n" + "="*70)
        print("ZERO-COPY CLONING EXERCISE VALIDATION")
        print("="*70)

        if not self.connect():
            return 0, self.max_score

        try:
            self.score += self.validate_production_data()
            self.score += self.validate_database_clone()
            self.score += self.validate_table_clones()
            self.score += self.validate_dev_modifications()
            self.score += self.validate_storage_tracking()
            self.score += self.validate_cost_analysis(solution_file)

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
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
    }

    # Get solution file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solution_file = os.path.join(script_dir, 'solution.sql')

    # Run validation
    validator = ZeroCopyValidator(connection_params)
    score, max_score = validator.run_validation(solution_file)
    validator.print_final_report()

    # Exit with appropriate code
    sys.exit(0 if score >= max_score * 0.7 else 1)


if __name__ == '__main__':
    main()
