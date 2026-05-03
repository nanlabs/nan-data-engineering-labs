#!/usr/bin/env python3
"""
Operations Data Generator for Enterprise Data Lakehouse
Generates synthetic operations domain data including IoT sensor data, equipment logs,
maintenance records, and inventory movements. Writes data to S3 as JSON streams.
"""

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from faker import Faker
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OperationsDataGenerator:
    """Generator for synthetic operations and IoT data."""

    SENSOR_TYPES = [
        'TEMPERATURE', 'PRESSURE', 'VIBRATION', 'HUMIDITY',
        'FLOW_RATE', 'VOLTAGE', 'CURRENT', 'SPEED', 'LEVEL'
    ]

    EQUIPMENT_TYPES = [
        'Pump', 'Motor', 'Compressor', 'Generator', 'Conveyor',
        'Valve', 'Heat Exchanger', 'Boiler', 'Turbine', 'Robot Arm'
    ]

    EQUIPMENT_STATUS = ['RUNNING', 'IDLE', 'MAINTENANCE', 'FAULT', 'OFFLINE']

    MAINTENANCE_TYPES = ['PREVENTIVE', 'CORRECTIVE', 'PREDICTIVE', 'EMERGENCY']

    FACILITY_LOCATIONS = [
        'Plant A - Texas', 'Plant B - Ohio', 'Plant C - California',
        'Warehouse 1 - Illinois', 'Warehouse 2 - New York',
        'Distribution Center - Georgia', 'Manufacturing Hub - Michigan'
    ]

    INVENTORY_TRANSACTION_TYPES = [
        'RECEIPT', 'SHIPMENT', 'TRANSFER', 'ADJUSTMENT',
        'RETURN', 'SCRAP', 'CYCLE_COUNT'
    ]

    def __init__(self, seed: Optional[int] = 42):
        """Initialize the generator with optional seed for reproducibility."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

        self.sensors = []
        self.sensor_events = []
        self.equipment = []
        self.equipment_logs = []
        self.maintenance_records = []
        self.inventory_movements = []

    def generate_sensors(self, num_sensors: int = 500) -> List[Dict]:
        """Generate sensor metadata."""
        logger.info(f"Generating {num_sensors} sensors...")

        sensors = []

        for i in range(num_sensors):
            sensor_type = random.choice(self.SENSOR_TYPES)
            location = random.choice(self.FACILITY_LOCATIONS)

            sensor = {
                'sensor_id': f'SNS{i+1:06d}',
                'sensor_type': sensor_type,
                'sensor_model': f"{sensor_type}-{random.randint(1000, 9999)}",
                'manufacturer': random.choice(['Honeywell', 'Siemens', 'Emerson', 'ABB', 'Schneider']),
                'location': location,
                'zone': f"Zone-{random.randint(1, 20):02d}",
                'equipment_id': f'EQP{random.randint(1, 200):05d}',
                'installation_date': self.fake.date_between(start_date='-5y', end_date='-1m').isoformat(),
                'calibration_date': self.fake.date_between(start_date='-6m', end_date='today').isoformat(),
                'next_calibration': (datetime.now() + timedelta(days=random.randint(30, 180))).date().isoformat(),
                'status': random.choices(
                    ['ACTIVE', 'MAINTENANCE', 'OFFLINE'],
                    weights=[0.90, 0.05, 0.05]
                )[0],
                'sample_rate_hz': random.choice([1, 5, 10, 60]),
                'accuracy': f"±{random.uniform(0.1, 2.0):.2f}%",
                'created_at': datetime.now().isoformat()
            }
            sensors.append(sensor)

        self.sensors = sensors
        logger.info(f"Generated {len(sensors)} sensors")
        return sensors

    def generate_sensor_events(
        self,
        num_events: int = 1000000,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Generate IoT sensor event data."""
        logger.info(f"Generating {num_events} sensor events...")

        if not self.sensors:
            logger.warning("No sensors generated. Generating sensors first.")
            self.generate_sensors()

        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        events = []

        for i in range(num_events):
            sensor = random.choice(self.sensors)

            # Generate timestamp
            time_delta = end_date - start_date
            random_seconds = random.randint(0, int(time_delta.total_seconds()))
            event_time = start_date + timedelta(seconds=random_seconds)

            # Generate sensor readings based on type
            if sensor['sensor_type'] == 'TEMPERATURE':
                value = round(random.gauss(75, 15), 2)  # °F
                unit = 'F'
                threshold_min, threshold_max = 40, 110
            elif sensor['sensor_type'] == 'PRESSURE':
                value = round(random.gauss(100, 20), 2)  # PSI
                unit = 'PSI'
                threshold_min, threshold_max = 50, 150
            elif sensor['sensor_type'] == 'VIBRATION':
                value = round(random.gauss(0.5, 0.2), 3)  # mm/s
                unit = 'mm/s'
                threshold_min, threshold_max = 0, 2.0
            elif sensor['sensor_type'] == 'HUMIDITY':
                value = round(random.gauss(50, 15), 2)  # %
                unit = '%'
                threshold_min, threshold_max = 20, 80
            elif sensor['sensor_type'] == 'FLOW_RATE':
                value = round(random.gauss(50, 10), 2)  # GPM
                unit = 'GPM'
                threshold_min, threshold_max = 20, 80
            elif sensor['sensor_type'] == 'VOLTAGE':
                value = round(random.gauss(220, 10), 2)  # V
                unit = 'V'
                threshold_min, threshold_max = 200, 240
            elif sensor['sensor_type'] == 'CURRENT':
                value = round(random.gauss(15, 5), 2)  # A
                unit = 'A'
                threshold_min, threshold_max = 5, 25
            elif sensor['sensor_type'] == 'SPEED':
                value = round(random.gauss(1500, 200), 2)  # RPM
                unit = 'RPM'
                threshold_min, threshold_max = 1000, 2000
            else:  # LEVEL
                value = round(random.gauss(70, 15), 2)  # %
                unit = '%'
                threshold_min, threshold_max = 20, 95

            # Determine if value is within normal range
            is_anomaly = value < threshold_min or value > threshold_max

            # Add noise occasionally
            if random.random() < 0.02:
                value = value * random.uniform(1.5, 3.0)
                is_anomaly = True

            event = {
                'event_id': f'EVT{i+1:012d}',
                'sensor_id': sensor['sensor_id'],
                'sensor_type': sensor['sensor_type'],
                'equipment_id': sensor['equipment_id'],
                'location': sensor['location'],
                'timestamp': event_time.isoformat(),
                'value': round(value, 3),
                'unit': unit,
                'threshold_min': threshold_min,
                'threshold_max': threshold_max,
                'is_anomaly': is_anomaly,
                'anomaly_score': round(random.uniform(0.7, 1.0), 3) if is_anomaly else round(random.uniform(0, 0.3), 3),
                'quality': random.choices(
                    ['GOOD', 'UNCERTAIN', 'BAD'],
                    weights=[0.95, 0.04, 0.01]
                )[0],
                'metadata': {
                    'firmware_version': f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                    'battery_level': random.randint(20, 100),
                    'signal_strength': random.randint(-90, -30)
                }
            }
            events.append(event)

        self.sensor_events = events
        logger.info(f"Generated {len(events)} sensor events")
        return events

    def generate_equipment(self, num_equipment: int = 200) -> List[Dict]:
        """Generate equipment master data."""
        logger.info(f"Generating {num_equipment} equipment records...")

        equipment_list = []

        for i in range(num_equipment):
            equipment_type = random.choice(self.EQUIPMENT_TYPES)
            install_date = self.fake.date_between(start_date='-15y', end_date='-1y')

            # Calculate age and condition
            age_years = (datetime.now().date() - install_date).days / 365
            condition_score = max(0, 100 - age_years * random.uniform(3, 8))

            equipment = {
                'equipment_id': f'EQP{i+1:05d}',
                'equipment_name': f"{equipment_type} {i+1}",
                'equipment_type': equipment_type,
                'manufacturer': random.choice(['Caterpillar', 'GE', 'Siemens', 'Mitsubishi', 'Rockwell']),
                'model': f"{equipment_type[:3].upper()}-{random.randint(1000, 9999)}",
                'serial_number': self.fake.bothify(text='SN-########??'),
                'location': random.choice(self.FACILITY_LOCATIONS),
                'install_date': install_date.isoformat(),
                'commissioning_date': (install_date + timedelta(days=random.randint(1, 30))).isoformat(),
                'warranty_expiry': (install_date + timedelta(days=random.randint(365, 1825))).isoformat(),
                'status': random.choices(
                    self.EQUIPMENT_STATUS,
                    weights=[0.70, 0.15, 0.08, 0.05, 0.02]
                )[0],
                'condition_score': round(condition_score, 2),
                'criticality': random.choice(['HIGH', 'MEDIUM', 'LOW']),
                'mtbf_hours': round(random.uniform(1000, 10000), 2),  # Mean Time Between Failures
                'mttr_hours': round(random.uniform(2, 24), 2),  # Mean Time To Repair
                'operating_hours': round(random.uniform(1000, 50000), 2),
                'maintenance_cost_ytd': round(random.uniform(5000, 100000), 2),
                'purchase_cost': round(random.uniform(50000, 1000000), 2),
                'replacement_cost': round(random.uniform(60000, 1200000), 2),
                'department': random.choice(['Production', 'Maintenance', 'Quality', 'Warehouse']),
                'responsible_person': self.fake.name(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            equipment_list.append(equipment)

        self.equipment = equipment_list
        logger.info(f"Generated {len(equipment_list)} equipment records")
        return equipment_list

    def generate_equipment_logs(self, days_back: int = 90) -> List[Dict]:
        """Generate equipment operational logs."""
        logger.info(f"Generating equipment logs for {days_back} days...")

        if not self.equipment:
            logger.warning("No equipment generated. Generating equipment first.")
            self.generate_equipment()

        logs = []
        end_date = datetime.now()

        for day_offset in range(days_back):
            log_date = end_date - timedelta(days=day_offset)

            for equip in self.equipment:
                # Generate 1-4 log entries per equipment per day
                num_logs = random.randint(1, 4)

                for _ in range(num_logs):
                    log_time = log_date.replace(
                        hour=random.randint(0, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )

                    # Generate operational metrics
                    runtime_hours = round(random.uniform(0, 24), 2)
                    downtime_hours = round(24 - runtime_hours, 2)

                    log = {
                        'log_id': f"LOG{len(logs)+1:012d}",
                        'equipment_id': equip['equipment_id'],
                        'timestamp': log_time.isoformat(),
                        'status': random.choices(
                            self.EQUIPMENT_STATUS,
                            weights=[0.75, 0.12, 0.06, 0.05, 0.02]
                        )[0],
                        'runtime_hours': runtime_hours,
                        'downtime_hours': downtime_hours,
                        'utilization_pct': round((runtime_hours / 24) * 100, 2),
                        'production_units': random.randint(0, 1000) if runtime_hours > 0 else 0,
                        'efficiency_pct': round(random.uniform(75, 98), 2) if runtime_hours > 0 else 0.0,
                        'power_consumption_kwh': round(runtime_hours * random.uniform(10, 50), 2),
                        'operator_id': f'OPR{random.randint(1, 50):04d}',
                        'shift': random.choice(['DAY', 'NIGHT', 'SWING']),
                        'alerts_count': random.choices([0, 1, 2, 3], weights=[0.80, 0.12, 0.05, 0.03])[0],
                        'errors_count': random.choices([0, 1, 2], weights=[0.90, 0.08, 0.02])[0],
                        'notes': self.fake.sentence(nb_words=8) if random.random() < 0.15 else '',
                        'created_at': datetime.now().isoformat()
                    }
                    logs.append(log)

        self.equipment_logs = logs
        logger.info(f"Generated {len(logs)} equipment logs")
        return logs

    def generate_maintenance_records(self, num_records: int = 5000) -> List[Dict]:
        """Generate maintenance records."""
        logger.info(f"Generating {num_records} maintenance records...")

        if not self.equipment:
            logger.warning("No equipment generated. Generating equipment first.")
            self.generate_equipment()

        records = []

        for i in range(num_records):
            equip = random.choice(self.equipment)
            maintenance_type = random.choice(self.MAINTENANCE_TYPES)

            scheduled_date = self.fake.date_between(start_date='-1y', end_date='+30d')

            # Determine if maintenance is completed
            is_completed = scheduled_date < datetime.now().date()

            if is_completed:
                actual_start = datetime.combine(
                    scheduled_date,
                    datetime.min.time()
                ) + timedelta(hours=random.randint(0, 8))
                duration_hours = round(random.uniform(0.5, 24), 2)
                actual_end = actual_start + timedelta(hours=duration_hours)

                cost = round(random.uniform(500, 25000), 2)
                status = random.choices(
                    ['COMPLETED', 'PARTIALLY_COMPLETED', 'CANCELLED'],
                    weights=[0.85, 0.10, 0.05]
                )[0]
            else:
                actual_start = None
                actual_end = None
                duration_hours = 0.0
                cost = 0.0
                status = 'SCHEDULED'

            record = {
                'maintenance_id': f'MNT{i+1:08d}',
                'equipment_id': equip['equipment_id'],
                'equipment_name': equip['equipment_name'],
                'maintenance_type': maintenance_type,
                'priority': random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
                'scheduled_date': scheduled_date.isoformat(),
                'actual_start': actual_start.isoformat() if actual_start else None,
                'actual_end': actual_end.isoformat() if actual_end else None,
                'duration_hours': duration_hours,
                'status': status,
                'description': self.fake.sentence(nb_words=12),
                'work_performed': self.fake.text(max_nb_chars=200) if is_completed else '',
                'parts_replaced': [
                    f"Part-{random.randint(1000, 9999)}"
                    for _ in range(random.randint(0, 5))
                ] if is_completed else [],
                'technician_id': f'TECH{random.randint(1, 30):03d}' if is_completed else None,
                'technician_name': self.fake.name() if is_completed else None,
                'labor_cost': round(cost * 0.6, 2) if is_completed else 0.0,
                'parts_cost': round(cost * 0.4, 2) if is_completed else 0.0,
                'total_cost': cost,
                'downtime_hours': round(duration_hours * random.uniform(0.5, 1.0), 2) if is_completed else 0.0,
                'follow_up_required': random.choices([True, False], weights=[0.20, 0.80])[0],
                'next_maintenance_date': (
                    scheduled_date + timedelta(days=random.randint(30, 180))
                ).isoformat() if maintenance_type == 'PREVENTIVE' else None,
                'notes': self.fake.sentence(nb_words=10),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            records.append(record)

        self.maintenance_records = records
        logger.info(f"Generated {len(records)} maintenance records")
        return records

    def generate_inventory_movements(self, num_movements: int = 50000) -> List[Dict]:
        """Generate inventory movement transactions."""
        logger.info(f"Generating {num_movements} inventory movements...")

        # Generate some product SKUs
        products = [f'SKU-{random.randint(10000, 99999)}' for _ in range(500)]

        movements = []

        for i in range(num_movements):
            transaction_type = random.choice(self.INVENTORY_TRANSACTION_TYPES)
            transaction_date = self.fake.date_time_between(start_date='-6m', end_date='now')

            # Generate quantity based on transaction type
            if transaction_type in ['RECEIPT', 'RETURN']:
                quantity = random.randint(10, 1000)
            elif transaction_type == 'SHIPMENT':
                quantity = -random.randint(10, 500)
            elif transaction_type == 'SCRAP':
                quantity = -random.randint(1, 50)
            elif transaction_type == 'ADJUSTMENT':
                quantity = random.randint(-100, 100)
            else:  # TRANSFER, CYCLE_COUNT
                quantity = random.randint(-200, 200)

            movement = {
                'movement_id': f'INV{i+1:010d}',
                'transaction_type': transaction_type,
                'transaction_date': transaction_date.isoformat(),
                'product_sku': random.choice(products),
                'product_description': self.fake.catch_phrase(),
                'quantity': quantity,
                'unit_of_measure': random.choice(['EA', 'BOX', 'PALLET', 'LB', 'KG']),
                'location_from': random.choice(self.FACILITY_LOCATIONS) if transaction_type != 'RECEIPT' else None,
                'location_to': random.choice(self.FACILITY_LOCATIONS) if transaction_type != 'SHIPMENT' else None,
                'bin_location': f"BIN-{random.randint(1, 20):02d}-{random.randint(1, 50):02d}",
                'batch_number': self.fake.bothify(text='BATCH-####??'),
                'lot_number': self.fake.bothify(text='LOT-######'),
                'unit_cost': round(random.uniform(10, 500), 2),
                'total_value': round(abs(quantity) * random.uniform(10, 500), 2),
                'reference_number': self.fake.bothify(text='REF-########'),
                'notes': self.fake.sentence(nb_words=8) if random.random() < 0.2 else '',
                'processed_by': self.fake.name(),
                'created_at': transaction_date.isoformat()
            }
            movements.append(movement)

        self.inventory_movements = movements
        logger.info(f"Generated {len(movements)} inventory movements")
        return movements

    def write_to_local(self, output_dir: str):
        """Write generated data to local JSON files."""
        logger.info(f"Writing operations data to local directory: {output_dir}")

        output_path = Path(output_dir)

        # Write sensor events with date partitioning
        if self.sensor_events:
            events_by_date = {}
            for event in self.sensor_events:
                event_date = datetime.fromisoformat(event['timestamp']).date()
                date_key = event_date.strftime('%Y-%m-%d')
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)

            for date_key, events in events_by_date.items():
                date_path = output_path / 'sensor_events' / f'date={date_key}'
                date_path.mkdir(parents=True, exist_ok=True)
                with open(date_path / f'events_{date_key}.json', 'w') as f:
                    json.dump(events, f, indent=2)
            logger.info(f"Wrote {len(self.sensor_events)} sensor events")

        # Write other datasets
        for dataset_name, data in [
            ('sensors', self.sensors),
            ('equipment', self.equipment),
            ('equipment_logs', self.equipment_logs),
            ('maintenance_records', self.maintenance_records),
            ('inventory_movements', self.inventory_movements)
        ]:
            if data:
                dataset_path = output_path / dataset_name
                dataset_path.mkdir(parents=True, exist_ok=True)
                with open(dataset_path / f'{dataset_name}.json', 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Wrote {len(data)} {dataset_name}")

    def write_to_s3(self, s3_bucket: str, s3_prefix: str = 'raw/operations'):
        """Write generated data to S3 as JSON."""
        logger.info(f"Writing operations data to S3: s3://{s3_bucket}/{s3_prefix}")

        try:
            s3_client = boto3.client('s3')

            # Write sensor events with date partitioning
            if self.sensor_events:
                events_by_date = {}
                for event in self.sensor_events:
                    event_date = datetime.fromisoformat(event['timestamp']).date()
                    date_key = event_date.strftime('%Y-%m-%d')
                    if date_key not in events_by_date:
                        events_by_date[date_key] = []
                    events_by_date[date_key].append(event)

                for date_key, events in events_by_date.items():
                    key = f"{s3_prefix}/sensor_events/date={date_key}/events_{date_key}.json"
                    s3_client.put_object(
                        Bucket=s3_bucket,
                        Key=key,
                        Body=json.dumps(events).encode('utf-8'),
                        ContentType='application/json'
                    )
                logger.info(f"Wrote {len(self.sensor_events)} sensor events to S3")

            # Write other datasets
            for dataset_name, data in [
                ('sensors', self.sensors),
                ('equipment', self.equipment),
                ('equipment_logs', self.equipment_logs),
                ('maintenance_records', self.maintenance_records),
                ('inventory_movements', self.inventory_movements)
            ]:
                if data:
                    key = f"{s3_prefix}/{dataset_name}/{dataset_name}.json"
                    s3_client.put_object(
                        Bucket=s3_bucket,
                        Key=key,
                        Body=json.dumps(data).encode('utf-8'),
                        ContentType='application/json'
                    )
                    logger.info(f"Wrote {len(data)} {dataset_name} to S3")

        except ClientError as e:
            logger.error(f"Error writing to S3: {e}")
            raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic operations data for Enterprise Data Lakehouse'
    )

    parser.add_argument(
        '--sensor-events',
        type=int,
        default=1000000,
        help='Number of sensor event records to generate (default: 1000000)'
    )

    parser.add_argument(
        '--sensors',
        type=int,
        default=500,
        help='Number of sensor devices (default: 500)'
    )

    parser.add_argument(
        '--equipment',
        type=int,
        default=200,
        help='Number of equipment items (default: 200)'
    )

    parser.add_argument(
        '--maintenance-records',
        type=int,
        default=5000,
        help='Number of maintenance records (default: 5000)'
    )

    parser.add_argument(
        '--inventory-movements',
        type=int,
        default=50000,
        help='Number of inventory movements (default: 50000)'
    )

    parser.add_argument(
        '--equipment-log-days',
        type=int,
        default=90,
        help='Number of days of equipment logs (default: 90)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for sensor events (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for sensor events (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--output-path',
        type=str,
        default='./data/operations',
        help='Local output path for generated data'
    )

    parser.add_argument(
        '--s3-bucket',
        type=str,
        help='S3 bucket name for output (if not specified, writes to local only)'
    )

    parser.add_argument(
        '--s3-prefix',
        type=str,
        default='raw/operations',
        help='S3 key prefix (default: raw/operations)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()

    # Parse dates if provided
    start_date = None
    end_date = None

    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD")
            sys.exit(1)

    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Initialize generator
    logger.info("Initializing Operations Data Generator...")
    generator = OperationsDataGenerator(seed=args.seed)

    # Generate data
    generator.generate_sensors(num_sensors=args.sensors)
    generator.generate_sensor_events(
        num_events=args.sensor_events,
        start_date=start_date,
        end_date=end_date
    )
    generator.generate_equipment(num_equipment=args.equipment)
    generator.generate_equipment_logs(days_back=args.equipment_log_days)
    generator.generate_maintenance_records(num_records=args.maintenance_records)
    generator.generate_inventory_movements(num_movements=args.inventory_movements)

    # Write to local
    generator.write_to_local(args.output_path)

    # Write to S3 if bucket specified
    if args.s3_bucket:
        generator.write_to_s3(args.s3_bucket, args.s3_prefix)

    logger.info("Operations data generation completed successfully!")
    logger.info(f"Generated: {len(generator.sensors)} sensors, "
                f"{len(generator.sensor_events)} sensor events, "
                f"{len(generator.equipment)} equipment, "
                f"{len(generator.equipment_logs)} equipment logs, "
                f"{len(generator.maintenance_records)} maintenance records, "
                f"{len(generator.inventory_movements)} inventory movements")


if __name__ == '__main__':
    main()
