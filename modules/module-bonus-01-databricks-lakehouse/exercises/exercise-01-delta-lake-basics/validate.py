"""
Exercise 01: Delta Lake Fundamentals - Validation Script

This script validates all 6 tasks from the Delta Lake Fundamentals exercise.

Usage:
    python validate.py

Author: Cloud Data Training
Module: Bonus 01 - Databricks Lakehouse
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import *


class DeltaLakeValidator:
    """Validator for Delta Lake Fundamentals exercise."""

    def __init__(self):
        """Initialize Spark session and validation state."""
        print("Initializing validator...")
        print("=" * 70)

        # Create Spark session with Delta Lake support
        self.spark = SparkSession.builder \
            .appName("DeltaLakeFundamentalsValidator") \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .getOrCreate()

        self.spark.sparkContext.setLogLevel("ERROR")

        # Set database
        try:
            self.spark.sql("USE exercise_01_db")
            print("✅ Connected to database: exercise_01_db\n")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}\n")
            sys.exit(1)

        # Track validation results
        self.results = []
        self.total_score = 0
        self.max_score = 100

    def validate_task_1(self):
        """
        Validate Task 1: Create Delta Table

        Checks:
        - Table exists
        - Format is Delta
        - Row count is 1,000
        - Schema matches specification
        """
        print("\n" + "=" * 70)
        print("Task 1: Create Delta Table (20 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 20

        try:
            # Check if table exists
            tables = [row.tableName for row in self.spark.sql("SHOW TABLES").collect()]
            if "customers" not in tables:
                print("❌ Table 'customers' does not exist")
                self.results.append(("Task 1", 0, max_task_score))
                return

            print("✅ Table 'customers' exists")
            task_score += 5

            # Check table format
            details = self.spark.sql("DESCRIBE DETAIL customers").collect()[0]
            if details["format"].lower() == "delta":
                print("✅ Table format is Delta")
                task_score += 5
            else:
                print(f"❌ Table format is {details['format']}, expected 'delta'")

            # Check row count
            count = self.spark.table("customers").count()
            if count >= 1000:
                print(f"✅ Table has {count:,} rows (expected ≥1,000)")
                task_score += 5
            else:
                print(f"❌ Table has {count} rows, expected ≥1,000")

            # Check schema
            expected_columns = {
                "customer_id": "int",
                "name": "string",
                "email": "string",
                "country": "string",
                "signup_date": "date",
                "total_purchases": "double"
            }

            actual_schema = {field.name: field.dataType.simpleString()
                           for field in self.spark.table("customers").schema.fields}

            schema_valid = True
            for col_name, col_type in expected_columns.items():
                if col_name not in actual_schema:
                    print(f"❌ Missing column: {col_name}")
                    schema_valid = False
                elif actual_schema[col_name] != col_type:
                    print(f"❌ Column {col_name} has type {actual_schema[col_name]}, expected {col_type}")
                    schema_valid = False

            if schema_valid:
                print("✅ Schema matches specification (6 required columns present)")
                task_score += 5
            else:
                print("❌ Schema does not match specification")

        except Exception as e:
            print(f"❌ Error validating Task 1: {e}")

        self.results.append(("Task 1: Create Delta Table", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 1 Score: {task_score}/{max_task_score}")

    def validate_task_2(self):
        """
        Validate Task 2: ACID Transactions

        Checks:
        - Atomicity demonstrated (500 customers added)
        - Row count increased appropriately
        """
        print("\n" + "=" * 70)
        print("Task 2: ACID Transactions (15 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 15

        try:
            # Check if atomicity was demonstrated (should have 1,500+ rows from initial + atomic batch)
            count = self.spark.table("customers").count()
            if count >= 1500:
                print(f"✅ Atomicity demonstrated: {count:,} rows (≥1,500 expected)")
                print("   Initial 1,000 + atomic batch of 500 = 1,500")
                task_score += 10
            else:
                print(f"⚠️  Row count is {count:,}, expected ≥1,500")
                print("   (May indicate atomicity test not run)")
                task_score += 5

            # Check for consistency (no negative total_purchases)
            negative_count = self.spark.table("customers").filter(
                col("total_purchases") < 0
            ).count()

            if negative_count == 0:
                print("✅ Consistency maintained: No negative total_purchases found")
                task_score += 5
            else:
                print(f"❌ Found {negative_count} customers with negative total_purchases")

        except Exception as e:
            print(f"❌ Error validating Task 2: {e}")

        self.results.append(("Task 2: ACID Transactions", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 2 Score: {task_score}/{max_task_score}")

    def validate_task_3(self):
        """
        Validate Task 3: Time Travel

        Checks:
        - DESCRIBE HISTORY shows operations
        - Multiple versions exist (≥4)
        - Can query historical versions
        """
        print("\n" + "=" * 70)
        print("Task 3: Time Travel (20 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 20

        try:
            # Check DESCRIBE HISTORY
            history = self.spark.sql("DESCRIBE HISTORY customers")
            version_count = history.count()

            if version_count >= 4:
                print(f"✅ Table history exists: {version_count} versions found")
                task_score += 10
            else:
                print(f"⚠️  Only {version_count} versions found, expected ≥4")
                print("   (Should have: create, update, delete, insert)")
                task_score += 5

            # Check operations in history
            operations = [row.operation for row in history.collect()]
            expected_ops = ["WRITE", "UPDATE", "DELETE", "MERGE"]

            found_ops = [op for op in expected_ops if any(op in str(h_op).upper() for h_op in operations)]
            if len(found_ops) >= 2:
                print(f"✅ Found expected operations: {', '.join(found_ops)}")
                task_score += 5
            else:
                print(f"⚠️  Limited operations found: {', '.join(operations[:5])}")

            # Test time travel query
            latest_version = history.select(max("version")).first()[0]
            if latest_version >= 1:
                prev_version_count = self.spark.read.format("delta") \
                    .option("versionAsOf", max(0, latest_version - 1)) \
                    .table("customers").count()

                current_count = self.spark.table("customers").count()

                print("✅ Time travel query successful")
                print(f"   Version {max(0, latest_version - 1)}: {prev_version_count:,} rows")
                print(f"   Current version: {current_count:,} rows")
                task_score += 5

        except Exception as e:
            print(f"❌ Error validating Task 3: {e}")

        self.results.append(("Task 3: Time Travel", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 3 Score: {task_score}/{max_task_score}")

    def validate_task_4(self):
        """
        Validate Task 4: Schema Evolution

        Checks:
        - New columns exist (loyalty_tier, last_purchase_date)
        - Original columns still present
        - Some rows have values in new columns
        """
        print("\n" + "=" * 70)
        print("Task 4: Schema Evolution (15 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 15

        try:
            # Get current schema
            schema = {field.name: field.dataType.simpleString()
                     for field in self.spark.table("customers").schema.fields}

            # Check for new columns
            new_columns = ["loyalty_tier", "last_purchase_date"]
            found_new_cols = []

            for col_name in new_columns:
                if col_name in schema:
                    print(f"✅ New column added: {col_name} ({schema[col_name]})")
                    found_new_cols.append(col_name)
                    task_score += 5
                else:
                    print(f"❌ Missing new column: {col_name}")

            # Check if new columns have some non-null values
            if found_new_cols:
                with_values = self.spark.table("customers").filter(
                    col("loyalty_tier").isNotNull()
                ).count()

                if with_values > 0:
                    print(f"✅ Schema evolution successful: {with_values} rows with new column values")
                    task_score += 5
                else:
                    print("⚠️  New columns exist but have no values")

        except Exception as e:
            print(f"❌ Error validating Task 4: {e}")

        self.results.append(("Task 4: Schema Evolution", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 4 Score: {task_score}/{max_task_score}")

    def validate_task_5(self):
        """
        Validate Task 5: MERGE Operations

        Checks:
        - Final row count is correct (1,050)
        - No duplicate customer_ids
        - MERGE operation in history
        """
        print("\n" + "=" * 70)
        print("Task 5: MERGE Operations (15 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 15

        try:
            # Check final row count (1,000 original + 50 new from MERGE)
            count = self.spark.table("customers").count()

            # Expected: ~1,050 (may vary based on deletes/restores)
            if count >= 1050:
                print(f"✅ Final row count: {count:,} (expected ~1,050)")
                task_score += 5
            else:
                print(f"⚠️  Row count is {count:,}, expected ~1,050")
                print("   (100 updates + 50 inserts)")

            # Check for duplicates
            duplicates = self.spark.table("customers").groupBy("customer_id") \
                .count().filter(col("count") > 1).count()

            if duplicates == 0:
                print("✅ No duplicate customer_ids (idempotency verified)")
                task_score += 5
            else:
                print(f"❌ Found {duplicates} duplicate customer_ids")

            # Check for MERGE operation in history
            history = self.spark.sql("DESCRIBE HISTORY customers")
            operations = [row.operation for row in history.collect()]

            if any("MERGE" in str(op).upper() for op in operations):
                print("✅ MERGE operation found in table history")
                task_score += 5
            else:
                print("⚠️  MERGE operation not found in history")
                print(f"   Found operations: {', '.join([str(op) for op in operations[:5]])}")

        except Exception as e:
            print(f"❌ Error validating Task 5: {e}")

        self.results.append(("Task 5: MERGE Operations", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 5 Score: {task_score}/{max_task_score}")

    def validate_task_6(self):
        """
        Validate Task 6: Optimize Performance

        Checks:
        - OPTIMIZE operation in history
        - File count is reasonable (compacted)
        - Table is optimized
        """
        print("\n" + "=" * 70)
        print("Task 6: Optimize Performance (15 points)")
        print("=" * 70)

        task_score = 0
        max_task_score = 15

        try:
            # Check for OPTIMIZE operation in history
            history = self.spark.sql("DESCRIBE HISTORY customers")
            operations = [row.operation for row in history.collect()]

            optimize_count = sum(1 for op in operations if "OPTIMIZE" in str(op).upper())

            if optimize_count >= 1:
                print(f"✅ OPTIMIZE operation found ({optimize_count} times)")
                task_score += 5
            else:
                print("❌ OPTIMIZE operation not found in history")

            # Check file count (should be reasonably small after OPTIMIZE)
            details = self.spark.sql("DESCRIBE DETAIL customers").collect()[0]
            num_files = details["numFiles"]

            if num_files <= 10:
                print(f"✅ File count optimized: {num_files} files (efficient)")
                task_score += 5
            elif num_files <= 50:
                print(f"⚠️  File count: {num_files} files (acceptable)")
                task_score += 3
            else:
                print(f"⚠️  File count: {num_files} files (may need more optimization)")

            # Check for ZORDER in operation parameters
            zorder_found = False
            for row in history.collect():
                if hasattr(row, 'operationParameters') and row.operationParameters:
                    if 'zOrderBy' in str(row.operationParameters):
                        zorder_found = True
                        break

            if zorder_found:
                print("✅ ZORDER optimization applied")
                task_score += 5
            else:
                print("⚠️  ZORDER optimization not detected")
                print("   (May be in operation parameters)")

        except Exception as e:
            print(f"❌ Error validating Task 6: {e}")

        self.results.append(("Task 6: Optimize Performance", task_score, max_task_score))
        self.total_score += task_score
        print(f"\nTask 6 Score: {task_score}/{max_task_score}")

    def print_summary(self):
        """Print final validation summary."""
        print("\n" + "=" * 70)
        print(" VALIDATION SUMMARY")
        print("=" * 70)

        for task_name, score, max_score in self.results:
            percentage = (score / max_score * 100) if max_score > 0 else 0
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"{status} {task_name:<35} {score:>3}/{max_score:<3} ({percentage:>5.1f}%)")

        print("-" * 70)
        final_percentage = (self.total_score / self.max_score * 100)
        print(f"   {'TOTAL SCORE':<35} {self.total_score:>3}/{self.max_score:<3} ({final_percentage:>5.1f}%)")
        print("=" * 70)

        # Final verdict
        if final_percentage >= 90:
            print("\n🎉 EXCELLENT! All tasks completed successfully!")
            print("   You have mastered Delta Lake fundamentals.")
        elif final_percentage >= 75:
            print("\n✅ GOOD! Most tasks completed successfully.")
            print("   Review any warnings above to improve further.")
        elif final_percentage >= 60:
            print("\n⚠️  PARTIAL SUCCESS. Some tasks need attention.")
            print("   Review the failed checks and retry.")
        else:
            print("\n❌ INCOMPLETE. Please review the exercise requirements.")
            print("   Focus on failed tasks and run validation again.")

        print("\n" + "=" * 70)

        return self.total_score >= (self.max_score * 0.75)

    def run_all_validations(self):
        """Run all validation tasks."""
        print("\n")
        print("=" * 70)
        print(" DELTA LAKE FUNDAMENTALS - VALIDATION")
        print("=" * 70)
        print("\nValidating Exercise 01: Delta Lake Fundamentals")
        print("This will check all 6 tasks from the exercise.\n")

        try:
            self.validate_task_1()
            self.validate_task_2()
            self.validate_task_3()
            self.validate_task_4()
            self.validate_task_5()
            self.validate_task_6()

            success = self.print_summary()

            return success

        except Exception as e:
            print(f"\n❌ Validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            self.spark.stop()


def main():
    """Main entry point for validation script."""
    try:
        validator = DeltaLakeValidator()
        success = validator.run_all_validations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
