#!/usr/bin/env python3
"""
Exercise 04: Complete ETL Pipeline - SOLUTION
"""
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    """Complete ETL pipeline with extract, transform, load."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': None,
            'records_extracted': 0,
            'records_transformed': 0,
            'records_loaded': 0,
            'errors': []
        }

    def extract(self) -> pd.DataFrame:
        """Extract data from configured sources."""
        logger.info("Starting extraction phase")

        source_config = self.config['source']
        source_type = source_config['type']

        if source_type == 'csv':
            df = pd.read_csv(
                source_config['path'],
                encoding=source_config.get('encoding', 'utf-8')
            )
        elif source_type == 'json':
            df = pd.read_json(
                source_config['path'],
                lines=source_config.get('lines', False)
            )
        elif source_type == 'parquet':
            df = pd.read_parquet(source_config['path'])
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        self.metrics['records_extracted'] = len(df)
        logger.info(f"Extracted {len(df)} records from {source_type}")
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply configured transformations."""
        logger.info("Starting transformation phase")

        transform_config = self.config.get('transform', {})

        # Drop duplicates
        if transform_config.get('drop_duplicates', False):
            initial_count = len(df)
            df = df.drop_duplicates()
            logger.info(f"Dropped {initial_count - len(df)} duplicates")

        # Handle nulls
        if 'drop_nulls' in transform_config:
            df = df.dropna(subset=transform_config['drop_nulls'])

        # Filter rows
        if 'filters' in transform_config:
            for filter_config in transform_config['filters']:
                column = filter_config['column']
                operator = filter_config['operator']
                value = filter_config['value']

                if operator == '==':
                    df = df[df[column] == value]
                elif operator == '!=':
                    df = df[df[column] != value]
                elif operator == 'in':
                    df = df[df[column].isin(value)]

                logger.info(f"Applied filter: {column} {operator} {value}")

        # Select columns
        if 'columns' in transform_config:
            df = df[transform_config['columns']]

        # Add metadata
        if transform_config.get('add_metadata', False):
            df['etl_processed_at'] = datetime.now()
            df['etl_pipeline'] = self.config.get('name', 'unknown')

        self.metrics['records_transformed'] = len(df)
        logger.info(f"Transformed {len(df)} records")
        return df

    def load(self, df: pd.DataFrame) -> None:
        """Load data to configured destination."""
        logger.info("Starting load phase")

        dest_config = self.config['destination']
        dest_type = dest_config['type']

        # Ensure output directory exists
        Path(dest_config['path']).parent.mkdir(parents=True, exist_ok=True)

        if dest_type == 'csv':
            df.to_csv(
                dest_config['path'],
                index=False,
                encoding=dest_config.get('encoding', 'utf-8')
            )
        elif dest_type == 'json':
            df.to_json(
                dest_config['path'],
                orient=dest_config.get('orient', 'records'),
                lines=dest_config.get('lines', False),
                indent=dest_config.get('indent')
            )
        elif dest_type == 'parquet':
            df.to_parquet(
                dest_config['path'],
                index=False,
                compression=dest_config.get('compression', 'snappy')
            )
        else:
            raise ValueError(f"Unsupported destination type: {dest_type}")

        self.metrics['records_loaded'] = len(df)
        logger.info(f"Loaded {len(df)} records to {dest_type}")

    def run(self) -> Dict[str, Any]:
        """Run complete ETL pipeline."""
        logger.info(f"Starting pipeline: {self.config.get('name', 'unnamed')}")
        self.metrics['start_time'] = datetime.now()

        try:
            # Extract
            df = self.extract()

            # Transform
            df = self.transform(df)

            # Load
            self.load(df)

            # Calculate metrics
            self.metrics['end_time'] = datetime.now()
            self.metrics['duration_seconds'] = (
                self.metrics['end_time'] - self.metrics['start_time']
            ).total_seconds()

            logger.info(f"Pipeline completed successfully in {self.metrics['duration_seconds']:.2f}s")
            logger.info(f"Metrics: {self.metrics}")

            return self.metrics

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.metrics['errors'].append(str(e))
            raise

def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    """Run ETL pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description='Run ETL pipeline')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    args = parser.parse_args()

    # Load configuration
    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    config = load_config(str(config_path))

    # Run pipeline
    pipeline = ETLPipeline(config)
    metrics = pipeline.run()

    print(f"\n{'='*60}")
    print("ETL Pipeline Metrics")
    print(f"{'='*60}")
    print(f"Duration: {metrics['duration_seconds']:.2f} seconds")
    print(f"Extracted: {metrics['records_extracted']} records")
    print(f"Transformed: {metrics['records_transformed']} records")
    print(f"Loaded: {metrics['records_loaded']} records")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
