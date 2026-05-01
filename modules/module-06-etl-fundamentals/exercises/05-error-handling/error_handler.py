#!/usr/bin/env python3
"""
Exercise 05: Error Handling - SOLUTION
"""
import pandas as pd
from pathlib import Path
from typing import Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handle errors in ETL pipeline."""

    def __init__(self, dlq_path: str = None):
        self.dlq_path = Path(dlq_path) if dlq_path else Path('dlq')
        self.dlq_path.mkdir(parents=True, exist_ok=True)
        self.error_count = 0

    def process_with_error_handling(
        self,
        df: pd.DataFrame,
        transform_func: callable
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process records with error handling.

        Returns:
            (successful_records, failed_records)
        """
        successful = []
        failed = []

        for idx, row in df.iterrows():
            try:
                transformed = transform_func(row)
                successful.append(transformed)
            except Exception as e:
                logger.warning(f"Record {idx} failed: {e}")
                failed.append({
                    'original_record': row.to_dict(),
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                })
                self.error_count += 1

        df_successful = pd.DataFrame(successful) if successful else pd.DataFrame()
        df_failed = pd.DataFrame(failed) if failed else pd.DataFrame()

        logger.info(f"Processed: {len(successful)} successful, {len(failed)} failed")
        return df_successful, df_failed

    def save_to_dlq(self, failed_records: pd.DataFrame, batch_id: str = None):
        """Save failed records to dead letter queue."""
        if failed_records.empty:
            logger.info("No failed records to save")
            return

        batch_id = batch_id or datetime.now().strftime('%Y%m%d_%H%M%S')
        dlq_file = self.dlq_path / f"failed_{batch_id}.json"

        failed_records.to_json(dlq_file, orient='records', indent=2)
        logger.info(f"Saved {len(failed_records)} failed records to {dlq_file}")

    def get_error_summary(self) -> dict:
        """Get summary of errors."""
        return {
            'total_errors': self.error_count,
            'dlq_path': str(self.dlq_path),
            'dlq_files': len(list(self.dlq_path.glob('*.json')))
        }

def validate_and_transform(row: pd.Series) -> dict:
    """
    Validate and transform a record.

    Raises ValueError for invalid data.
    """
    # Validate email
    if '@' not in str(row.get('email', '')):
        raise ValueError(f"Invalid email: {row.get('email')}")

    # Validate age
    age = row.get('age')
    if pd.isna(age) or not (18 <= age <= 120):
        raise ValueError(f"Invalid age: {age}")

    # Transform
    return {
        'id': int(row['id']),
        'email': str(row['email']).lower().strip(),
        'age': int(age),
        'country': str(row.get('country', 'Unknown')),
        'status': str(row.get('status', 'unknown')).lower()
    }

def main():
    """Test error handling."""
    # Create sample data with errors
    data = {
        'id': [1, 2, 3, 4, 5],
        'email': ['user1@test.com', 'invalid', 'user3@test.com', None, 'user5@test.com'],
        'age': [25, 30, 200, 28, 35],  # 200 is invalid
        'country': ['USA', 'UK', 'USA', 'Canada', None],
        'status': ['active', 'active', 'active', 'pending', 'active']
    }
    df = pd.DataFrame(data)

    print(f"Processing {len(df)} records...")
    print("\nOriginal data:")
    print(df)

    # Process with error handling
    handler = ErrorHandler(dlq_path='../../data/dlq')
    df_success, df_failed = handler.process_with_error_handling(
        df,
        validate_and_transform
    )

    print(f"\n✓ Successful records: {len(df_success)}")
    print(df_success)

    print(f"\n❌ Failed records: {len(df_failed)}")
    if not df_failed.empty:
        print(df_failed[['error_type', 'error']])

    # Save failed records to DLQ
    handler.save_to_dlq(df_failed)

    # Summary
    summary = handler.get_error_summary()
    print("\n📊 Error Summary:")
    print(f"  Total errors: {summary['total_errors']}")
    print(f"  DLQ files: {summary['dlq_files']}")

if __name__ == '__main__':
    main()
