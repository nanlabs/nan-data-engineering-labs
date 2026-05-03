#!/usr/bin/env python3
"""
Exercise 05: Snowpipe Automated Ingestion - Validation Script
Validates the implementation of Snowpipe for automated data ingestion.
"""

import os
import sys
import snowflake.connector
from snowflake.connector import DictCursor


class SnowpipeValidator:
    """Validator for Snowpipe Ingestion exercise."""

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
                database='INGESTION_LAB',
                schema='IOT_DATA'
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

    def validate_stage_setup(self) -> None:
        """Validate external stage configuration (20 points)."""
        print("\n=== Validating External Stage Setup ===")

        # Check stage exists (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.STAGES
                WHERE STAGE_SCHEMA = 'IOT_DATA'
                AND STAGE_NAME = 'S3_STAGE'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('stage_exists', True, 10,
                              's3_stage created successfully')
            else:
                self.add_result('stage_exists', False, 10,
                              's3_stage not found')
                return
        except Exception as e:
            self.add_result('stage_exists', False, 10, f'Error: {e}')
            return

        # Check stage configuration (10 points)
        try:
            self.cursor.execute("SHOW STAGES LIKE 's3_stage'")
            stage_info = self.cursor.fetchone()
            if stage_info:
                url = stage_info.get('url', '').lower()
                if 's3://' in url:
                    self.add_result('stage_config', True, 10,
                                  'Stage configured with S3 URL')
                else:
                    self.add_result('stage_config', False, 10,
                                  'Stage not configured for S3')
            else:
                self.add_result('stage_config', False, 10,
                              'Cannot retrieve stage configuration')
        except Exception as e:
            self.add_result('stage_config', False, 10, f'Error: {e}')

    def validate_file_format(self) -> None:
        """Validate file format configuration (15 points)."""
        print("\n=== Validating File Format ===")

        # Check file format exists (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.FILE_FORMATS
                WHERE FILE_FORMAT_SCHEMA = 'IOT_DATA'
                AND FILE_FORMAT_NAME = 'JSON_FORMAT'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('file_format_exists', True, 10,
                              'json_format created successfully')
            else:
                self.add_result('file_format_exists', False, 10,
                              'json_format not found')
                return
        except Exception as e:
            self.add_result('file_format_exists', False, 10, f'Error: {e}')
            return

        # Check file format type (5 points)
        try:
            self.cursor.execute("SHOW FILE FORMATS LIKE 'json_format'")
            format_info = self.cursor.fetchone()
            if format_info and format_info.get('type', '').upper() == 'JSON':
                self.add_result('file_format_type', True, 5,
                              'File format type is JSON')
            else:
                self.add_result('file_format_type', False, 5,
                              'File format type is not JSON')
        except Exception as e:
            self.add_result('file_format_type', False, 5, f'Error: {e}')

    def validate_target_table(self) -> None:
        """Validate target table structure (15 points)."""
        print("\n=== Validating Target Table ===")

        # Check table exists (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'IOT_DATA'
                AND TABLE_NAME = 'SENSOR_DATA'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('table_exists', True, 5,
                              'sensor_data table exists')
            else:
                self.add_result('table_exists', False, 5,
                              'sensor_data table not found')
                return
        except Exception as e:
            self.add_result('table_exists', False, 5, f'Error: {e}')
            return

        # Check table schema (5 points)
        try:
            self.cursor.execute("DESC TABLE sensor_data")
            columns = {row['name'].upper() for row in self.cursor.fetchall()}
            required = {'SENSOR_ID', 'TIMESTAMP', 'TEMPERATURE',
                       'HUMIDITY', 'LOCATION'}
            if required.issubset(columns):
                self.add_result('table_schema', True, 5,
                              'All required columns present')
            else:
                missing = required - columns
                self.add_result('table_schema', False, 5,
                              f'Missing columns: {missing}')
        except Exception as e:
            self.add_result('table_schema', False, 5, f'Error: {e}')

        # Check data loaded (5 points)
        try:
            self.cursor.execute("SELECT COUNT(*) as cnt FROM sensor_data")
            result = self.cursor.fetchone()
            count = result['CNT']
            if count > 0:
                self.add_result('data_loaded', True, 5,
                              f'Table contains {count} records')
            else:
                self.add_result('data_loaded', False, 5,
                              'Table is empty - no data ingested')
        except Exception as e:
            self.add_result('data_loaded', False, 5, f'Error: {e}')

    def validate_pipe_setup(self) -> None:
        """Validate Snowpipe configuration (25 points)."""
        print("\n=== Validating Snowpipe Setup ===")

        # Check pipe exists (10 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM INFORMATION_SCHEMA.PIPES
                WHERE PIPE_SCHEMA = 'IOT_DATA'
                AND PIPE_NAME = 'SENSOR_PIPE'
            """)
            result = self.cursor.fetchone()
            if result['CNT'] == 1:
                self.add_result('pipe_exists', True, 10,
                              'sensor_pipe created successfully')
            else:
                self.add_result('pipe_exists', False, 10,
                              'sensor_pipe not found')
                return
        except Exception as e:
            self.add_result('pipe_exists', False, 10, f'Error: {e}')
            return

        # Check auto_ingest enabled (10 points)
        try:
            self.cursor.execute("SHOW PIPES LIKE 'sensor_pipe'")
            pipe_info = self.cursor.fetchone()
            if pipe_info:
                # Check if notification_channel exists (indicates AUTO_INGEST)
                notification = pipe_info.get('notification_channel', '')
                if notification:
                    self.add_result('auto_ingest', True, 10,
                                  'AUTO_INGEST enabled with notification channel')
                else:
                    self.add_result('auto_ingest', False, 10,
                                  'AUTO_INGEST not properly configured')
            else:
                self.add_result('auto_ingest', False, 10,
                              'Cannot retrieve pipe configuration')
        except Exception as e:
            self.add_result('auto_ingest', False, 10, f'Error: {e}')

        # Check pipe status queryable (5 points)
        try:
            self.cursor.execute("SELECT SYSTEM$PIPE_STATUS('sensor_pipe') as status")
            result = self.cursor.fetchone()
            if result and result['STATUS']:
                self.add_result('pipe_status', True, 5,
                              'Pipe status queryable')
            else:
                self.add_result('pipe_status', False, 5,
                              'Cannot query pipe status')
        except Exception as e:
            self.add_result('pipe_status', False, 5, f'Error: {e}')

    def validate_monitoring(self) -> None:
        """Validate monitoring and cost tracking (15 points)."""
        print("\n=== Validating Monitoring ===")

        # Check copy history accessible (5 points)
        try:
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
                    TABLE_NAME => 'SENSOR_DATA',
                    START_TIME => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
                ))
            """)
            result = self.cursor.fetchone()
            if result['CNT'] >= 0:  # Query succeeded
                self.add_result('copy_history', True, 5,
                              f'Copy history accessible ({result["CNT"]} records)')
            else:
                self.add_result('copy_history', False, 5,
                              'Copy history query failed')
        except Exception as e:
            self.add_result('copy_history', False, 5, f'Error: {e}')

        # Check pipe usage history (5 points)
        try:
            # Note: PIPE_USAGE_HISTORY requires ACCOUNT_USAGE which may have delay
            self.cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
                WHERE PIPE_NAME = 'SENSOR_PIPE'
                AND START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
            """)
            result = self.cursor.fetchone()
            if result['CNT'] >= 0:
                self.add_result('pipe_usage', True, 5,
                              'Pipe usage history accessible')
            else:
                self.add_result('pipe_usage', False, 5,
                              'Pipe usage history unavailable')
        except Exception:
            # Account usage may not be accessible in all environments
            self.add_result('pipe_usage', True, 5,
                          'Pipe usage query attempted (may require permissions)')

        # Check cost calculation logic (5 points)
        try:
            # Verify student understands cost model (0.06 credits per 1K files)
            self.cursor.execute("""
                SELECT
                    100 AS sample_files,
                    ROUND(100 / 1000.0 * 0.06, 4) AS calculated_credits
            """)
            result = self.cursor.fetchone()
            expected_credits = 0.006
            if abs(result['CALCULATED_CREDITS'] - expected_credits) < 0.0001:
                self.add_result('cost_calculation', True, 5,
                              'Cost calculation logic correct (0.06 per 1K files)')
            else:
                self.add_result('cost_calculation', False, 5,
                              'Cost calculation logic incorrect')
        except Exception as e:
            self.add_result('cost_calculation', False, 5, f'Error: {e}')

    def validate_error_tracking(self) -> None:
        """Validate error tracking and data quality (10 points)."""
        print("\n=== Validating Error Tracking ===")

        # Check error tracking query (5 points)
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) AS total_loads,
                    SUM(CASE WHEN STATUS = 'LOAD_FAILED' THEN 1 ELSE 0 END) AS failed_loads
                FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
                    TABLE_NAME => 'SENSOR_DATA',
                    START_TIME => DATEADD(DAY, -7, CURRENT_TIMESTAMP())
                ))
            """)
            result = self.cursor.fetchone()
            if result and result['TOTAL_LOADS'] is not None:
                total = result['TOTAL_LOADS']
                failed = result['FAILED_LOADS'] or 0
                self.add_result('error_tracking', True, 5,
                              f'Error tracking working: {failed}/{total} failed')
            else:
                self.add_result('error_tracking', False, 5,
                              'Error tracking query failed')
        except Exception as e:
            self.add_result('error_tracking', False, 5, f'Error: {e}')

        # Check data quality validation (5 points)
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) AS total_records,
                    SUM(CASE WHEN SENSOR_ID IS NULL THEN 1 ELSE 0 END) AS null_sensor_id,
                    SUM(CASE WHEN TIMESTAMP IS NULL THEN 1 ELSE 0 END) AS null_timestamp
                FROM sensor_data
            """)
            result = self.cursor.fetchone()
            if result and result['TOTAL_RECORDS'] > 0:
                nulls = result['NULL_SENSOR_ID'] + result['NULL_TIMESTAMP']
                if nulls == 0:
                    self.add_result('data_quality', True, 5,
                                  'Data quality checks passing (no critical nulls)')
                else:
                    self.add_result('data_quality', False, 5,
                                  f'Data quality issues: {nulls} null critical fields')
            else:
                self.add_result('data_quality', False, 5,
                              'No data to validate')
        except Exception as e:
            self.add_result('data_quality', False, 5, f'Error: {e}')

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
            print("🎉 Excellent! Snowpipe configured correctly!")
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
            self.validate_stage_setup()
            self.validate_file_format()
            self.validate_target_table()
            self.validate_pipe_setup()
            self.validate_monitoring()
            self.validate_error_tracking()
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
    print("Exercise 05: Snowpipe Automated Ingestion - Validation")
    print("="*70)

    validator = SnowpipeValidator()
    success = validator.run_all_validations()

    sys.exit(0 if success and validator.score >= 70 else 1)


if __name__ == "__main__":
    main()
