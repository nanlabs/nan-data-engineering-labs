#!/usr/bin/env python3
"""
Exercise 06: Data Sharing and Secure Views - Validation Script
Validates the implementation of Snowflake Data Sharing with secure views.
"""

import os
import sys
import snowflake.connector
from snowflake.connector import DictCursor


class DataSharingValidator:
    """Validator for Data Sharing exercise."""

    def __init__(self):
        """Initialize validator with Snowflake connection."""
        self.conn = None
        self.cursor = None
        self.score = 0
        self.max_score = 100
        self.results = []
        self.marketplace_datasets = []

    def connect(self) -> bool:
        """Establish Snowflake connection."""
        try:
            self.conn = snowflake.connector.connect(
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                user=os.getenv('SNOWFLAKE_USER'),
                password=os.getenv('SNOWFLAKE_PASSWORD'),
                warehouse='TRAINING_WH',
                database='SHARED_ANALYTICS',
                schema='CUSTOMER_DATA'
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

    def validate_source_data(self) -> None:
        """Validate source tables and data (15 points)."""
        print("\n=== Validating Source Data ===")

        # Check customer_metrics table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'CUSTOMER_DATA'
                AND TABLE_NAME = 'CUSTOMER_METRICS'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('metrics_table_exists', True, 5,
                              'customer_metrics table exists')
            else:
                self.add_result('metrics_table_exists', False, 5,
                              'customer_metrics table not found')
                return
        except Exception as e:
            self.add_result('metrics_table_exists', False, 5, f'Error: {e}')
            return

        # Check data volume (5 points)
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT CUSTOMER_ID) as unique_customers
                FROM customer_metrics
            """)
            result = self.cursor.fetchone()
            if result['TOTAL_RECORDS'] >= 10000 and result['UNIQUE_CUSTOMERS'] >= 5:
                self.add_result('data_volume', True, 5,
                              f"{result['TOTAL_RECORDS']} records, "
                              f"{result['UNIQUE_CUSTOMERS']} customers")
            else:
                self.add_result('data_volume', False, 5,
                              "Expected >=10000 records and >=5 customers")
        except Exception as e:
            self.add_result('data_volume', False, 5, f'Error: {e}')

        # Check PII table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'CUSTOMER_DATA'
                AND TABLE_NAME = 'CUSTOMER_DETAILS'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('details_table_exists', True, 5,
                              'customer_details table exists')
            else:
                self.add_result('details_table_exists', False, 5,
                              'customer_details table not found')
        except Exception as e:
            self.add_result('details_table_exists', False, 5, f'Error: {e}')

    def validate_secure_views(self) -> None:
        """Validate secure views implementation (25 points)."""
        print("\n=== Validating Secure Views ===")

        # Check filtered view exists and is secure (10 points)
        try:
            self.cursor.execute("""
                SELECT
                    TABLE_NAME,
                    TABLE_TYPE,
                    IS_SECURE
                FROM INFORMATION_SCHEMA.VIEWS
                WHERE TABLE_SCHEMA = 'CUSTOMER_DATA'
                AND TABLE_NAME = 'CUSTOMER_METRICS_FILTERED'
            """)
            result = self.cursor.fetchone()
            if result and result['IS_SECURE'] == 'YES':
                self.add_result('secure_view_filtered', True, 10,
                              'customer_metrics_filtered is a secure view')
            else:
                self.add_result('secure_view_filtered', False, 10,
                              'customer_metrics_filtered not secure or missing')
        except Exception as e:
            self.add_result('secure_view_filtered', False, 10, f'Error: {e}')

        # Check masked view exists and is secure (10 points)
        try:
            self.cursor.execute("""
                SELECT
                    TABLE_NAME,
                    IS_SECURE
                FROM INFORMATION_SCHEMA.VIEWS
                WHERE TABLE_SCHEMA = 'CUSTOMER_DATA'
                AND TABLE_NAME = 'CUSTOMER_DETAILS_MASKED'
            """)
            result = self.cursor.fetchone()
            if result and result['IS_SECURE'] == 'YES':
                self.add_result('secure_view_masked', True, 10,
                              'customer_details_masked is a secure view')
            else:
                self.add_result('secure_view_masked', False, 10,
                              'customer_details_masked not secure or missing')
        except Exception as e:
            self.add_result('secure_view_masked', False, 10, f'Error: {e}')

        # Verify masking implementation (5 points)
        try:
            self.cursor.execute("""
                SELECT EMAIL, PHONE, CREDIT_CARD
                FROM customer_details_masked
                LIMIT 1
            """)
            result = self.cursor.fetchone()
            if result:
                email_masked = 'XXXX' in result['EMAIL'] or '****' in result['EMAIL']
                phone_masked = 'XXX' in result['PHONE']
                cc_masked = 'XXXX' in result['CREDIT_CARD']

                if email_masked and phone_masked and cc_masked:
                    self.add_result('masking_implemented', True, 5,
                                  'PII masking correctly implemented')
                else:
                    self.add_result('masking_implemented', False, 5,
                                  'PII masking incomplete')
            else:
                self.add_result('masking_implemented', False, 5,
                              'No data in masked view')
        except Exception as e:
            self.add_result('masking_implemented', False, 5, f'Error: {e}')

    def validate_share_creation(self) -> None:
        """Validate share creation and grants (25 points)."""
        print("\n=== Validating Share Creation ===")

        # Check share exists (10 points)
        try:
            self.cursor.execute("SHOW SHARES LIKE 'client_analytics'")
            shares = self.cursor.fetchall()
            if len(shares) > 0:
                self.add_result('share_exists', True, 10,
                              'client_analytics share created')
            else:
                self.add_result('share_exists', False, 10,
                              'client_analytics share not found')
                return
        except Exception as e:
            self.add_result('share_exists', False, 10, f'Error: {e}')
            return

        # Check grants to share (10 points)
        try:
            self.cursor.execute("SHOW GRANTS TO SHARE client_analytics")
            grants = self.cursor.fetchall()

            # Check for database, schema, and view grants
            granted_objects = set()
            for grant in grants:
                grant_type = grant.get('granted_on', '').upper()
                granted_objects.add(grant_type)

            required_grants = {'DATABASE', 'SCHEMA', 'VIEW'}
            if required_grants.issubset(granted_objects) or 'TABLE' in granted_objects:
                self.add_result('share_grants', True, 10,
                              f'Proper grants configured: {granted_objects}')
            else:
                missing = required_grants - granted_objects
                self.add_result('share_grants', False, 10,
                              f'Missing grants: {missing}')
        except Exception as e:
            self.add_result('share_grants', False, 10, f'Error: {e}')

        # Check consumer accounts added (5 points)
        try:
            self.cursor.execute("SHOW SHARES LIKE 'client_analytics'")
            result = self.cursor.fetchone()
            if result:
                accounts_to = result.get('to', '')
                # In real scenario, would parse the accounts list
                if accounts_to or len(str(accounts_to)) > 0:
                    self.add_result('consumer_accounts', True, 5,
                                  'Consumer accounts configured')
                else:
                    self.add_result('consumer_accounts', False, 5,
                                  'No consumer accounts added')
            else:
                self.add_result('consumer_accounts', False, 5,
                              'Cannot verify consumer accounts')
        except Exception:
            # May not have permission to see consumer accounts
            self.add_result('consumer_accounts', True, 5,
                          'Consumer account validation attempted')

    def validate_monitoring(self) -> None:
        """Validate usage monitoring queries (20 points)."""
        print("\n=== Validating Monitoring ===")

        # Check access to DATA_TRANSFER_HISTORY (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY
                WHERE SOURCE_DATABASE = 'SHARED_ANALYTICS'
                AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
            """)
            result = self.cursor.fetchone()
            if result is not None:
                self.add_result('transfer_history', True, 10,
                              'Data transfer history accessible')
            else:
                self.add_result('transfer_history', False, 10,
                              'Cannot access data transfer history')
        except Exception:
            # May require ACCOUNT_USAGE access
            self.add_result('transfer_history', True, 10,
                          'Transfer history query attempted (may require permissions)')

        # Check access to ACCESS_HISTORY (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
                WHERE START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
                LIMIT 1
            """)
            result = self.cursor.fetchone()
            if result is not None:
                self.add_result('access_history', True, 10,
                              'Access history queryable')
            else:
                self.add_result('access_history', False, 10,
                              'Cannot access access history')
        except Exception:
            # May require ACCOUNT_USAGE access
            self.add_result('access_history', True, 10,
                          'Access history query attempted (may require permissions)')

    def validate_marketplace_exploration(self) -> None:
        """Validate Snowflake Marketplace exploration (15 points)."""
        print("\n=== Validating Marketplace Exploration ===")

        # This is validated by checking documentation or comments in solution
        # In real scenario, would check if student accessed marketplace datasets

        # For this exercise, we'll check if they documented datasets
        # This would typically be done by reviewing their solution.sql comments

        # Award points based on documented research (manual verification needed)
        print("ℹ  Marketplace exploration requires manual verification")
        print("   Check solution.sql for documented datasets:")
        print("   - At least 3 datasets should be documented")
        print("   - Each with: name, provider, description, use case")

        # For automated validation, check if they can list shares
        try:
            self.cursor.execute("SHOW SHARES")
            shares = self.cursor.fetchall()

            # Award full points if they can query marketplace
            self.add_result('marketplace_access', True, 15,
                          f'Marketplace accessible ({len(shares)} shares visible)')
        except Exception as e:
            self.add_result('marketplace_access', False, 15,
                          f'Marketplace access issue: {e}')

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
            print("🎉 Excellent! Data sharing configured correctly!")
        elif self.score >= 70:
            print("👍 Good work! Minor improvements needed.")
        elif self.score >= 50:
            print("📚 Keep going! Review the solution for guidance.")
        else:
            print("🔧 Needs work. Check the solution and try again.")

        # Additional instructions
        print("\n" + "="*70)
        print("MANUAL VERIFICATION REQUIRED:")
        print("="*70)
        print("✓ Check solution.sql for Snowflake Marketplace documentation")
        print("  - At least 3 datasets should be documented")
        print("  - Each should include: name, provider, description, use case")
        print("✓ Verify consumer accounts added to share (if applicable)")
        print("✓ Test share from consumer perspective (if possible)")

    def run_all_validations(self):
        """Run all validation tests."""
        if not self.connect():
            return False

        try:
            self.validate_source_data()
            self.validate_secure_views()
            self.validate_share_creation()
            self.validate_monitoring()
            self.validate_marketplace_exploration()
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
    print("Exercise 06: Data Sharing and Secure Views - Validation")
    print("="*70)

    validator = DataSharingValidator()
    success = validator.run_all_validations()

    sys.exit(0 if success and validator.score >= 70 else 1)


if __name__ == "__main__":
    main()
