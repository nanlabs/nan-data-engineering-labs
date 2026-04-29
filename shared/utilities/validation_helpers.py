"""
Validation helper utilities for Cloud Data Engineering modules.

Provides common validation functions for data quality, schema validation,
infrastructure checks, and test result comparisons.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import hashlib


class DataQualityValidator:
    """Validates data quality metrics and assertions."""

    @staticmethod
    def validate_schema(df: pd.DataFrame, expected_schema: Dict[str, str]) -> tuple[bool, List[str]]:
        """
        Validate DataFrame schema against expected schema.

        Args:
            df: DataFrame to validate
            expected_schema: Dict mapping column names to expected dtypes

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Check columns exist
        missing_cols = set(expected_schema.keys()) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")

        # Check extra columns
        extra_cols = set(df.columns) - set(expected_schema.keys())
        if extra_cols:
            errors.append(f"Unexpected columns: {extra_cols}")

        # Check dtypes
        for col, expected_dtype in expected_schema.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if not actual_dtype.startswith(expected_dtype):
                    errors.append(f"Column '{col}': expected {expected_dtype}, got {actual_dtype}")

        return len(errors) == 0, errors

    @staticmethod
    def check_null_percentage(df: pd.DataFrame, column: str, max_null_pct: float = 0.05) -> tuple[bool, str]:
        """Check if null percentage is within acceptable threshold."""
        null_pct = df[column].isnull().sum() / len(df)
        is_valid = null_pct <= max_null_pct
        message = f"Column '{column}': {null_pct:.2%} nulls ({'PASS' if is_valid else 'FAIL'} - threshold: {max_null_pct:.2%})"
        return is_valid, message

    @staticmethod
    def check_uniqueness(df: pd.DataFrame, column: str) -> tuple[bool, str]:
        """Check if column values are unique."""
        duplicates = df[column].duplicated().sum()
        is_valid = duplicates == 0
        message = f"Column '{column}': {duplicates} duplicates ({'PASS' if is_valid else 'FAIL'})"
        return is_valid, message

    @staticmethod
    def check_value_range(df: pd.DataFrame, column: str, min_val: Any, max_val: Any) -> tuple[bool, str]:
        """Check if values are within expected range."""
        out_of_range = ((df[column] < min_val) | (df[column] > max_val)).sum()
        is_valid = out_of_range == 0
        message = f"Column '{column}': {out_of_range} values out of range [{min_val}, {max_val}] ({'PASS' if is_valid else 'FAIL'})"
        return is_valid, message


class QueryResultValidator:
    """Validates SQL query results against expected outputs."""

    @staticmethod
    def compare_dataframes(actual: pd.DataFrame, expected: pd.DataFrame,
                          tolerance: float = 0.0) -> tuple[bool, List[str]]:
        """
        Compare two DataFrames with optional tolerance for numeric columns.

        Args:
            actual: Actual result DataFrame
            expected: Expected result DataFrame
            tolerance: Tolerance for numeric comparisons (default: 0.0 - exact match)

        Returns:
            (is_match, differences)
        """
        differences = []

        # Check shape
        if actual.shape != expected.shape:
            differences.append(f"Shape mismatch: actual {actual.shape} vs expected {expected.shape}")
            return False, differences

        # Check columns
        if list(actual.columns) != list(expected.columns):
            differences.append(f"Column mismatch: {list(actual.columns)} vs {list(expected.columns)}")
            return False, differences

        # Compare values
        for col in actual.columns:
            if pd.api.types.is_numeric_dtype(actual[col]):
                # Numeric comparison with tolerance
                if not actual[col].equals(expected[col]):
                    if tolerance > 0:
                        diff_mask = abs(actual[col] - expected[col]) > tolerance
                        if diff_mask.any():
                            differences.append(f"Column '{col}': {diff_mask.sum()} rows exceed tolerance {tolerance}")
                    else:
                        differences.append(f"Column '{col}': values don't match exactly")
            else:
                # Exact comparison for non-numeric
                if not actual[col].equals(expected[col]):
                    mismatches = (actual[col] != expected[col]).sum()
                    differences.append(f"Column '{col}': {mismatches} mismatches")

        return len(differences) == 0, differences

    @staticmethod
    def load_expected_result(expected_file: Path) -> pd.DataFrame:
        """Load expected result from CSV or Parquet."""
        if expected_file.suffix == '.csv':
            return pd.read_csv(expected_file)
        elif expected_file.suffix == '.parquet':
            return pd.read_parquet(expected_file)
        else:
            raise ValueError(f"Unsupported file format: {expected_file.suffix}")

    @staticmethod
    def compute_checksum(df: pd.DataFrame) -> str:
        """Compute SHA256 checksum of DataFrame for quick comparison."""
        return hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest()


class InfrastructureValidator:
    """Validates infrastructure configurations and deployments."""

    @staticmethod
    def validate_terraform_syntax(terraform_dir: Path) -> tuple[bool, str]:
        """
        Validate Terraform syntax (requires terraform CLI).

        Args:
            terraform_dir: Directory containing Terraform files

        Returns:
            (is_valid, output_message)
        """
        import subprocess

        try:
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=terraform_dir,
                capture_output=True,
                text=True
            )
            is_valid = result.returncode == 0
            return is_valid, result.stdout + result.stderr
        except FileNotFoundError:
            return False, "Terraform CLI not found. Install from https://www.terraform.io/downloads"

    @staticmethod
    def validate_json_schema(json_file: Path, schema: Dict) -> tuple[bool, List[str]]:
        """Validate JSON file against JSON Schema."""
        from jsonschema import validate, ValidationError

        with open(json_file) as f:
            data = json.load(f)

        try:
            validate(instance=data, schema=schema)
            return True, []
        except ValidationError as e:
            return False, [str(e)]

    @staticmethod
    def validate_yaml_syntax(yaml_file: Path) -> tuple[bool, str]:
        """Validate YAML syntax."""
        import yaml

        try:
            with open(yaml_file) as f:
                yaml.safe_load(f)
            return True, "YAML syntax valid"
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {e}"


class TestReporter:
    """Generate test reports with clear pass/fail indicators."""

    @staticmethod
    def print_test_result(test_name: str, passed: bool, message: str = "",
                         learning_objective: str = ""):
        """
        Print formatted test result.

        Args:
            test_name: Name of the test
            passed: Whether test passed
            message: Additional message
            learning_objective: What this test validates (for learning purposes)
        """
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} | {test_name}")

        if learning_objective:
            print(f"  📖 This test validates: {learning_objective}")

        if message:
            print(f"  💬 {message}")

    @staticmethod
    def generate_summary(results: List[tuple[str, bool]]) -> str:
        """Generate test summary."""
        total = len(results)
        passed = sum(1 for _, p in results if p)
        failed = total - passed

        summary = f"\n{'='*60}\n"
        summary += f"TEST SUMMARY: {passed}/{total} passed\n"
        summary += f"{'='*60}\n"

        if failed == 0:
            summary += "🎉 All tests passed! You're ready to move forward.\n"
        else:
            summary += f"⚠️  {failed} test(s) failed. Review the errors above and try again.\n"

        return summary


def load_config(config_file: Path) -> Dict:
    """Load configuration from JSON or YAML file."""
    import yaml

    with open(config_file) as f:
        if config_file.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)


def validate_exercise(exercise_dir: Path, validation_config: Dict) -> bool:
    """
    Main validation function for exercises.

    Args:
        exercise_dir: Directory containing exercise solution
        validation_config: Configuration dict with validation rules

    Returns:
        True if all validations pass
    """
    results = []
    reporter = TestReporter()

    # Run validations based on config
    # This is a template - specific implementations in each module

    print(f"\n🔍 Validating exercise: {exercise_dir.name}\n")

    # Example validation flow
    if 'data_quality' in validation_config:
        # Run data quality checks
        pass

    if 'query_results' in validation_config:
        # Compare query results
        pass

    if 'infrastructure' in validation_config:
        # Validate infrastructure
        pass

    # Print summary
    print(reporter.generate_summary(results))

    return all(passed for _, passed in results)
