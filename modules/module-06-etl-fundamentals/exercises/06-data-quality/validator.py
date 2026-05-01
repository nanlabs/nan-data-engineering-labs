#!/usr/bin/env python3
"""
Exercise 06: Data Quality - Schema Validator - SOLUTION
"""
import pandas as pd
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSchema(BaseModel):
    """Pydantic schema for user validation."""

    id: int = Field(..., gt=0, description="User ID must be positive")
    email: EmailStr = Field(..., description="Valid email required")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=120, description="Age between 18-120")
    country: str = Field(..., min_length=2, max_length=100)
    status: str = Field(..., description="User status")
    created_at: str = Field(..., description="ISO format datetime")

    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed = ['active', 'inactive', 'suspended', 'pending']
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v.lower()

    @validator('created_at')
    def validate_datetime(cls, v):
        """Validate datetime format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("created_at must be ISO format datetime")
        return v

class DataValidator:
    """Validate DataFrame against schema."""

    def __init__(self, schema_class: type[BaseModel]):
        self.schema_class = schema_class
        self.validation_results = []

    def validate_dataframe(self, df: pd.DataFrame) -> tuple[List[dict], List[dict]]:
        """
        Validate all records in DataFrame.

        Returns:
            (valid_records, invalid_records)
        """
        valid = []
        invalid = []

        for idx, row in df.iterrows():
            try:
                # Validate with Pydantic
                validated = self.schema_class(**row.to_dict())
                valid.append(validated.dict())
            except Exception as e:
                invalid.append({
                    'row_index': idx,
                    'record': row.to_dict(),
                    'errors': str(e)
                })

        logger.info(f"Validation complete: {len(valid)} valid, {len(invalid)} invalid")
        return valid, invalid

    def get_validation_report(self, df: pd.DataFrame) -> dict:
        """Generate validation report."""
        valid, invalid = self.validate_dataframe(df)

        report = {
            'total_records': len(df),
            'valid_records': len(valid),
            'invalid_records': len(invalid),
            'valid_percentage': (len(valid) / len(df) * 100) if len(df) > 0 else 0,
            'validation_errors': []
        }

        # Count error types
        from collections import Counter
        if invalid:
            error_types = []
            for item in invalid:
                # Extract error type from error message
                error_msg = item['errors']
                error_types.append(error_msg.split('\n')[0])

            report['error_distribution'] = dict(Counter(error_types))

        return report

def main():
    """Test validator."""
    # Create test data
    data = {
        'id': [1, 2, 3, 4, 5],
        'email': ['user1@test.com', 'invalid_email', 'user3@test.com', 'user4@test.com', 'user5@test.com'],
        'first_name': ['John', 'Jane', '', 'Bob', 'Alice'],
        'last_name': ['Doe', 'Smith', 'Johnson', 'Brown', 'Wilson'],
        'age': [25, 30, 200, 28, 17],  # 200 and 17 are invalid
        'country': ['USA', 'UK', 'USA', 'Canada', 'USA'],
        'status': ['active', 'active', 'invalid_status', 'pending', 'active'],
        'created_at': [
            '2024-01-01T00:00:00',
            '2024-01-02T00:00:00',
            '2024-01-03T00:00:00',
            'invalid_date',
            '2024-01-05T00:00:00'
        ]
    }
    df = pd.DataFrame(data)

    print(f"Validating {len(df)} records...")

    validator = DataValidator(UserSchema)
    valid, invalid = validator.validate_dataframe(df)

    print(f"\n✓ Valid records: {len(valid)}")
    if valid:
        print(pd.DataFrame(valid).head())

    print(f"\n❌ Invalid records: {len(invalid)}")
    if invalid:
        for item in invalid:
            print(f"  Row {item['row_index']}: {item['errors'][:100]}...")

    # Get report
    report = validator.get_validation_report(df)
    print("\n📊 Validation Report:")
    print(f"  Total: {report['total_records']}")
    print(f"  Valid: {report['valid_records']} ({report['valid_percentage']:.1f}%)")
    print(f"  Invalid: {report['invalid_records']}")

if __name__ == '__main__':
    main()
