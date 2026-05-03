# Exercise 04: CEP Fraud Detection

## Overview
Implement Complex Event Processing (CEP) using Apache Flink to detect fraud patterns in real-time transaction streams using pattern matching and sequence detection.

**Difficulty**: ⭐⭐⭐ Advanced
**Duration**: ~2.5 hours
**Prerequisites**: Exercise 01-02, Understanding of state management

## Learning Objectives

- Implement Flink CEP patterns in Python
- Use MATCH_RECOGNIZE for SQL-based pattern detection
- Detect multi-event fraud sequences
- Configure pattern time constraints
- Route fraud alerts to SNS/SQS
- Handle false positives

## Key Concepts

- **CEP**: Complex Event Processing for pattern detection
- **MATCH_RECOGNIZE**: SQL syntax for pattern matching
- **Pattern Sequences**: Multi-event patterns with ordering
- **Time Windows**: Patterns must complete within time bounds
- **Quantifiers**: ONE, ONE_OR_MORE, ZERO_OR_MORE
- **Contiguity**: STRICT, RELAXED, NON_DETERMINISTIC

## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────┐
│  Kinesis Stream  │────>│   Flink CEP        │────>│     SNS      │
│  (transactions)  │     │  Pattern Matcher   │     │ (fraud-alert)│
└──────────────────┘     └────────────────────┘     └──────────────┘
                                   │                          │
                                   │                          v
                                   v                  ┌──────────────┐
                         ┌────────────────┐          │     SQS      │
                         │   DynamoDB     │          │ (for review) │
                         │ fraud-detections│         └──────────────┘
                         └────────────────┘
```

## Pattern Definitions

### Pattern 1: Failed Payment + Success
Detect: 3-5 failed payments followed by 1 success within 10 minutes (potential card testing)

### Pattern 2: Rapid Geographic Movement
Detect: Purchases from 3+ different countries within 1 hour (impossible travel)

### Pattern 3: Unusual Amount Spike
Detect: Average transaction increases 10x suddenly (account takeover)

## Task 1: Setup CEP Environment (15 minutes)

**File**: `flink_cep_config.py`

```python
#!/usr/bin/env python3
"""Flink CEP configuration for fraud detection"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types
import os


def create_cep_environment():
    """Create Flink environment optimized for CEP"""

    # StreamExecutionEnvironment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    # Enable checkpointing for state management
    env.enable_checkpointing(30000)  # 30 seconds

    # Configure checkpoint storage
    checkpoint_dir = os.getenv('CHECKPOINT_DIR',
                              'file:///tmp/flink-checkpoints')
    env.get_checkpoint_config().set_checkpoint_storage(checkpoint_dir)

    # Set state backend to RocksDB for large state
    env.set_state_backend('rocksdb')

    # Table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    table_env = StreamTableEnvironment.create(env, settings)

    # CEP-specific configs
    table_env.get_config().get_configuration().set_string(
        "table.exec.state.ttl", "1 h"  # Clean old patterns after 1 hour
    )

    return env, table_env


def register_transaction_source(table_env):
    """Register Kinesis source for transactions"""

    ddl = """
    CREATE TABLE transactions (
        transaction_id STRING,
        user_id STRING,
        amount DECIMAL(10, 2),
        currency STRING,
        payment_method STRING,
        status STRING,  -- 'success', 'failed'
        merchant_id STRING,
        merchant_category STRING,
        country STRING,
        city STRING,
        ip_address STRING,
        device_id STRING,
        transaction_timestamp BIGINT,
        event_timestamp AS TO_TIMESTAMP(FROM_UNIXTIME(transaction_timestamp)),
        WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '10' SECOND
    ) WITH (
        'connector' = 'kinesis',
        'stream' = 'transaction-stream',
        'aws.region' = 'us-east-1',
        'aws.endpoint' = 'http://localstack:4566',
        'scan.stream.initpos' = 'LATEST',
        'format' = 'json',
        'json.timestamp-format.standard' = 'ISO-8601'
    )
    """

    table_env.execute_sql(ddl)
    print("✓ Transaction source registered")


def register_fraud_sink(table_env):
    """Register sink for detected fraud events"""

    # SNS sink for immediate alerts
    sns_ddl = """
    CREATE TABLE fraud_alerts (
        fraud_id STRING,
        user_id STRING,
        pattern_name STRING,
        confidence_score DECIMAL(5, 2),
        details STRING,
        transaction_ids ARRAY<STRING>,
        detection_timestamp TIMESTAMP(3)
    ) WITH (
        'connector' = 'kinesis',
        'stream' = 'fraud-alerts',
        'aws.region' = 'us-east-1',
        'aws.endpoint' = 'http://localstack:4566',
        'format' = 'json',
        'json.timestamp-format.standard' = 'ISO-8601'
    )
    """

    table_env.execute_sql(sns_ddl)

    # DynamoDB sink for investigation
    dynamodb_ddl = """
    CREATE TABLE fraud_detections (
        fraud_id STRING PRIMARY KEY,
        user_id STRING,
        pattern_name STRING,
        confidence_score DECIMAL(5, 2),
        details STRING,
        transaction_ids ARRAY<STRING>,
        detection_timestamp TIMESTAMP(3),
        reviewed BOOLEAN,
        reviewer_notes STRING
    ) WITH (
        'connector' = 'dynamodb',
        'table-name' = 'fraud-detections',
        'aws.region' = 'us-east-1',
        'aws.endpoint' = 'http://localstack:4566'
    )
    """

    table_env.execute_sql(dynamodb_ddl)

    print("✓ Fraud sinks registered")


if __name__ == '__main__':
    env, table_env = create_cep_environment()
    register_transaction_source(table_env)
    register_fraud_sink(table_env)
    print("✓ CEP environment ready")
```

## Task 2: Pattern 1 - Card Testing Detection (25 minutes)

Detect multiple failed payments followed by success (card validation fraud).

**File**: `pattern_card_testing.py`

```python
#!/usr/bin/env python3
"""Detect card testing fraud pattern"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types
from pyflink.common.time import Time
import json
from datetime import datetime


class CardTestingDetector(KeyedProcessFunction):
    """
    Detect pattern: 3-5 failed payments → 1 success within 10 minutes
    """

    def __init__(self):
        self.failed_payments_state = None
        self.timer_state = None

    def open(self, runtime_context: RuntimeContext):
        """Initialize state"""

        # Store failed payment attempts
        failed_descriptor = ValueStateDescriptor(
            "failed-payments",
            Types.LIST(Types.TUPLE([Types.STRING(), Types.LONG()]))
        )
        self.failed_payments_state = runtime_context.get_state(failed_descriptor)

        # Store cleanup timer
        timer_descriptor = ValueStateDescriptor(
            "cleanup-timer",
            Types.LONG()
        )
        self.timer_state = runtime_context.get_state(timer_descriptor)

    def process_element(self, value, ctx):
        """Process each transaction"""

        transaction = json.loads(value)
        status = transaction['status']
        transaction_id = transaction['transaction_id']
        timestamp = transaction['transaction_timestamp']

        # Get current failed attempts
        failed_attempts = self.failed_payments_state.value() or []

        # Remove old attempts (>10 minutes)
        ten_minutes_ago = timestamp - (10 * 60)
        failed_attempts = [
            (txn_id, ts) for txn_id, ts in failed_attempts
            if ts > ten_minutes_ago
        ]

        if status == 'failed':
            # Add to failed attempts
            failed_attempts.append((transaction_id, timestamp))
            self.failed_payments_state.update(failed_attempts)

            # Set cleanup timer (10 minutes from now)
            cleanup_time = timestamp + (10 * 60 * 1000)
            ctx.timer_service().register_event_time_timer(cleanup_time)
            self.timer_state.update(cleanup_time)

        elif status == 'success':
            # Check if this follows multiple failures
            if len(failed_attempts) >= 3:
                # FRAUD DETECTED!
                fraud_event = {
                    'fraud_id': f"card_test_{transaction['user_id']}_{timestamp}",
                    'user_id': transaction['user_id'],
                    'pattern_name': 'card_testing',
                    'confidence_score': min(95.0 + len(failed_attempts) * 2, 99.0),
                    'details': json.dumps({
                        'failed_attempts': len(failed_attempts),
                        'success_transaction': transaction_id,
                        'time_window_minutes': 10,
                        'payment_method': transaction['payment_method']
                    }),
                    'transaction_ids': [txn_id for txn_id, _ in failed_attempts] + [transaction_id],
                    'detection_timestamp': datetime.fromtimestamp(timestamp).isoformat()
                }

                yield json.dumps(fraud_event)

            # Clear state after success
            self.failed_payments_state.clear()
            self.timer_state.clear()

    def on_timer(self, timestamp, ctx):
        """Cleanup old state"""
        self.failed_payments_state.clear()
        self.timer_state.clear()


def run_card_testing_detection():
    """Execute card testing detection job"""

    from flink_cep_config import create_cep_environment, register_transaction_source, register_fraud_sink

    env, table_env = create_cep_environment()
    register_transaction_source(table_env)
    register_fraud_sink(table_env)

    # Convert table to DataStream
    transaction_stream = table_env.to_append_stream(
        table_env.from_path('transactions'),
        Types.STRING()
    )

    # Apply pattern detector (keyed by user_id)
    fraud_stream = (transaction_stream
                    .key_by(lambda x: json.loads(x)['user_id'])
                    .process(CardTestingDetector()))

    # Write to fraud sinks
    fraud_table = table_env.from_data_stream(fraud_stream)
    fraud_table.execute_insert('fraud_alerts').wait()
    fraud_table.execute_insert('fraud_detections').wait()

    print("✓ Card testing detection running")


if __name__ == '__main__':
    run_card_testing_detection()
```

## Task 3: Pattern 2 - Geographic Anomaly (SQL) (25 minutes)

Detect impossible travel using MATCH_RECOGNIZE.

**File**: `pattern_geographic_anomaly.sql`

```sql
-- Detect purchases from 3+ different countries within 1 hour

CREATE VIEW geographic_fraud AS
SELECT *
FROM transactions
MATCH_RECOGNIZE (
    PARTITION BY user_id
    ORDER BY event_timestamp
    MEASURES
        FIRST(A.transaction_id) AS first_transaction,
        LAST(C.transaction_id) AS last_transaction,
        A.country AS country_1,
        B.country AS country_2,
        C.country AS country_3,
        A.event_timestamp AS start_time,
        C.event_timestamp AS end_time,
        CAST((C.event_timestamp - A.event_timestamp) AS INTERVAL MINUTE) AS time_span,
        'geographic_anomaly' AS pattern_name,
        85.0 AS confidence_score

    ONE ROW PER MATCH
    AFTER MATCH SKIP PAST LAST ROW

    PATTERN (A B C)
    WITHIN INTERVAL '1' HOUR

    DEFINE
        B AS B.country <> A.country,
        C AS C.country <> A.country AND C.country <> B.country
);

-- Write results to fraud alerts
INSERT INTO fraud_alerts
SELECT
    CONCAT('geo_', user_id, '_', CAST(UNIX_TIMESTAMP(start_time) AS STRING)) AS fraud_id,
    user_id,
    pattern_name,
    confidence_score,
    CAST(MAP[
        'countries', ARRAY[country_1, country_2, country_3],
        'time_span_minutes', CAST(time_span AS STRING),
        'risk_level', 'HIGH'
    ] AS STRING) AS details,
    ARRAY[first_transaction, last_transaction] AS transaction_ids,
    CURRENT_TIMESTAMP AS detection_timestamp
FROM geographic_fraud;
```

**Python wrapper**:

**File**: `pattern_geographic_anomaly.py`

```python
#!/usr/bin/env python3
"""Execute geographic anomaly detection"""

from flink_cep_config import create_cep_environment, register_transaction_source, register_fraud_sink


def run_geographic_anomaly_detection():
    """Run SQL-based geographic fraud detection"""

    env, table_env = create_cep_environment()
    register_transaction_source(table_env)
    register_fraud_sink(table_env)

    # Read SQL file
    with open('pattern_geographic_anomaly.sql', 'r') as f:
        sql_statements = f.read()

    # Execute each statement
    for statement in sql_statements.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            table_env.execute_sql(statement)
            print(f"✓ Executed: {statement[:50]}...")

    print("✓ Geographic anomaly detection running")


if __name__ == '__main__':
    run_geographic_anomaly_detection()
```

## Task 4: Pattern 3 - Amount Spike Detection (25 minutes)

Detect sudden increases in transaction amounts (account takeover).

**File**: `pattern_amount_spike.py`

```python
#!/usr/bin/env python3
"""Detect unusual amount spike pattern"""

from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types
import json
from datetime import datetime
from decimal import Decimal


class AmountSpikeDetector(KeyedProcessFunction):
    """
    Detect: Average amount increases 10x within 30 minutes
    """

    def __init__(self):
        self.baseline_state = None
        self.recent_transactions_state = None

    def open(self, runtime_context: RuntimeContext):
        """Initialize state"""

        # Baseline average (from historical data)
        baseline_descriptor = ValueStateDescriptor(
            "baseline-average",
            Types.TUPLE([Types.DOUBLE(), Types.INT()])  # (sum, count)
        )
        self.baseline_state = runtime_context.get_state(baseline_descriptor)

        # Recent transactions in window
        recent_descriptor = ValueStateDescriptor(
            "recent-transactions",
            Types.LIST(Types.TUPLE([Types.DOUBLE(), Types.LONG()]))
        )
        self.recent_transactions_state = runtime_context.get_state(recent_descriptor)

    def process_element(self, value, ctx):
        """Process each transaction"""

        transaction = json.loads(value)
        amount = float(transaction['amount'])
        timestamp = transaction['transaction_timestamp']

        # Get or initialize baseline
        baseline = self.baseline_state.value()
        if baseline is None:
            baseline = (0.0, 0)

        baseline_sum, baseline_count = baseline

        # Update baseline (running average)
        baseline_sum += amount
        baseline_count += 1
        baseline_avg = baseline_sum / baseline_count if baseline_count > 0 else 0

        self.baseline_state.update((baseline_sum, baseline_count))

        # Get recent transactions
        recent = self.recent_transactions_state.value() or []

        # Remove old transactions (>30 minutes)
        thirty_minutes_ago = timestamp - (30 * 60)
        recent = [(amt, ts) for amt, ts in recent if ts > thirty_minutes_ago]

        # Add current transaction
        recent.append((amount, timestamp))
        self.recent_transactions_state.update(recent)

        # Calculate recent average
        if len(recent) >= 3:  # Need at least 3 transactions
            recent_avg = sum(amt for amt, _ in recent) / len(recent)

            # Check for spike (10x increase)
            if baseline_avg > 0 and recent_avg > baseline_avg * 10:
                # FRAUD DETECTED!
                fraud_event = {
                    'fraud_id': f"spike_{transaction['user_id']}_{timestamp}",
                    'user_id': transaction['user_id'],
                    'pattern_name': 'amount_spike',
                    'confidence_score': min(80.0 + (recent_avg / baseline_avg), 99.0),
                    'details': json.dumps({
                        'baseline_average': round(baseline_avg, 2),
                        'recent_average': round(recent_avg, 2),
                        'spike_multiplier': round(recent_avg / baseline_avg, 2),
                        'recent_transaction_count': len(recent),
                        'time_window_minutes': 30
                    }),
                    'transaction_ids': [transaction['transaction_id']],
                    'detection_timestamp': datetime.fromtimestamp(timestamp).isoformat()
                }

                yield json.dumps(fraud_event)


def run_amount_spike_detection():
    """Execute amount spike detection job"""

    from flink_cep_config import create_cep_environment, register_transaction_source, register_fraud_sink

    env, table_env = create_cep_environment()
    register_transaction_source(table_env)
    register_fraud_sink(table_env)

    # Convert to DataStream
    transaction_stream = table_env.to_append_stream(
        table_env.from_path('transactions'),
        Types.STRING()
    )

    # Apply detector
    fraud_stream = (transaction_stream
                    .key_by(lambda x: json.loads(x)['user_id'])
                    .process(AmountSpikeDetector()))

    # Write results
    fraud_table = table_env.from_data_stream(fraud_stream)
    fraud_table.execute_insert('fraud_alerts').wait()
    fraud_table.execute_insert('fraud_detections').wait()

    print("✓ Amount spike detection running")


if __name__ == '__main__':
    run_amount_spike_detection()
```

## Task 5: Main Orchestrator (15 minutes)

Combine all pattern detectors.

**File**: `main_cep.py`

```python
#!/usr/bin/env python3
"""Main CEP fraud detection orchestrator"""

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def run_pattern(pattern_name):
    """Run a single fraud pattern detector"""
    try:
        if pattern_name == 'card_testing':
            from pattern_card_testing import run_card_testing_detection
            logger.info("Starting card testing detection...")
            run_card_testing_detection()

        elif pattern_name == 'geographic':
            from pattern_geographic_anomaly import run_geographic_anomaly_detection
            logger.info("Starting geographic anomaly detection...")
            run_geographic_anomaly_detection()

        elif pattern_name == 'amount_spike':
            from pattern_amount_spike import run_amount_spike_detection
            logger.info("Starting amount spike detection...")
            run_amount_spike_detection()

        else:
            logger.error(f"Unknown pattern: {pattern_name}")
            return False

        logger.info(f"✓ {pattern_name} detection completed")
        return True

    except Exception as e:
        logger.error(f"✗ Error in {pattern_name}: {e}")
        return False


def run_all_patterns():
    """Run all fraud detection patterns concurrently"""

    patterns = ['card_testing', 'geographic', 'amount_spike']

    logger.info(f"Starting {len(patterns)} fraud detection patterns...")

    # Run patterns in separate threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_pattern, p): p for p in patterns}

        for future in futures:
            pattern_name = futures[future]
            try:
                success = future.result()
                if not success:
                    logger.error(f"✗ {pattern_name} failed")
            except Exception as e:
                logger.error(f"✗ {pattern_name} exception: {e}")

    logger.info("✓ All patterns started")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Flink CEP Fraud Detection'
    )
    parser.add_argument(
        '--pattern',
        choices=['card_testing', 'geographic', 'amount_spike', 'all'],
        default='all',
        help='Which pattern to run'
    )

    args = parser.parse_args()

    try:
        if args.pattern == 'all':
            run_all_patterns()
        else:
            success = run_pattern(args.pattern)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
```

## Task 6: Generate Test Data (20 minutes)

Create realistic transaction data with fraud patterns.

**File**: `generate_fraud_data.py`

```python
#!/usr/bin/env python3
"""Generate transactions with embedded fraud patterns"""

import boto3
import json
import random
import time
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

kinesis = boto3.client('kinesis',
                      endpoint_url='http://localhost:4566',
                      region_name='us-east-1')


def generate_normal_transaction(user_id, base_amount=50.0):
    """Generate normal transaction"""
    return {
        'transaction_id': fake.uuid4(),
        'user_id': user_id,
        'amount': round(random.uniform(base_amount * 0.5, base_amount * 2), 2),
        'currency': 'USD',
        'payment_method': random.choice(['credit_card', 'debit_card', 'paypal']),
        'status': 'success',
        'merchant_id': fake.uuid4(),
        'merchant_category': random.choice(['retail', 'food', 'travel', 'entertainment']),
        'country': 'US',
        'city': fake.city(),
        'ip_address': fake.ipv4(),
        'device_id': fake.uuid4(),
        'transaction_timestamp': int(time.time())
    }


def generate_card_testing_sequence(user_id):
    """Generate card testing fraud pattern"""
    transactions = []
    base_time = int(time.time())

    # 4 failed attempts
    for i in range(4):
        txn = generate_normal_transaction(user_id)
        txn['status'] = 'failed'
        txn['transaction_timestamp'] = base_time + (i * 60)  # 1 min apart
        transactions.append(txn)

    # 1 success (the fraud)
    success_txn = generate_normal_transaction(user_id)
    success_txn['transaction_timestamp'] = base_time + (5 * 60)
    success_txn['amount'] = 199.99  # High value
    transactions.append(success_txn)

    return transactions


def generate_geographic_anomaly_sequence(user_id):
    """Generate impossible travel pattern"""
    transactions = []
    base_time = int(time.time())
    countries = ['US', 'UK', 'JP']

    for i, country in enumerate(countries):
        txn = generate_normal_transaction(user_id)
        txn['country'] = country
        txn['transaction_timestamp'] = base_time + (i * 10 * 60)  # 10 min apart
        transactions.append(txn)

    return transactions


def generate_amount_spike_sequence(user_id):
    """Generate amount spike pattern"""
    transactions = []
    base_time = int(time.time())

    # 5 normal transactions (~$50)
    for i in range(5):
        txn = generate_normal_transaction(user_id, base_amount=50)
        txn['transaction_timestamp'] = base_time + (i * 60)
        transactions.append(txn)

    # 3 high-value transactions (~$500) - 10x spike
    for i in range(3):
        txn = generate_normal_transaction(user_id, base_amount=500)
        txn['transaction_timestamp'] = base_time + ((5 + i) * 60)
        transactions.append(txn)

    return transactions


def send_to_kinesis(transactions):
    """Send transactions to Kinesis"""
    for txn in transactions:
        kinesis.put_record(
            StreamName='transaction-stream',
            Data=json.dumps(txn),
            PartitionKey=txn['user_id']
        )
        time.sleep(0.1)  # Small delay


def main():
    print("Generating fraud test data...")

    # Generate 80 normal transactions
    print("  Generating 80 normal transactions...")
    for i in range(80):
        user_id = f"user_{random.randint(1000, 9999)}"
        txn = generate_normal_transaction(user_id)
        send_to_kinesis([txn])

    # Generate 5 card testing frauds
    print("  Generating 5 card testing patterns...")
    for i in range(5):
        user_id = f"fraud_card_{i}"
        txns = generate_card_testing_sequence(user_id)
        send_to_kinesis(txns)
        time.sleep(2)

    # Generate 3 geographic anomalies
    print("  Generating 3 geographic anomalies...")
    for i in range(3):
        user_id = f"fraud_geo_{i}"
        txns = generate_geographic_anomaly_sequence(user_id)
        send_to_kinesis(txns)
        time.sleep(2)

    # Generate 2 amount spikes
    print("  Generating 2 amount spikes...")
    for i in range(2):
        user_id = f"fraud_spike_{i}"
        txns = generate_amount_spike_sequence(user_id)
        send_to_kinesis(txns)
        time.sleep(2)

    print("✓ Test data generated")
    print("  Total: 80 normal + 25 fraud = 105 transactions")


if __name__ == '__main__':
    main()
```

## Task 7: Deploy and Validate (15 minutes)

**Deployment**:

```bash
# Create transaction stream
awslocal kinesis create-stream \
    --stream-name transaction-stream \
    --shard-count 2 \
    --region us-east-1

# Run all fraud detectors
python main_cep.py --pattern all

# In separate terminal: Generate test data
python generate_fraud_data.py
```

**Validation**:

```bash
# Check fraud alerts in Kinesis
awslocal kinesis get-records \
    --shard-iterator $(awslocal kinesis get-shard-iterator \
        --stream-name fraud-alerts \
        --shard-id shardId-000000000000 \
        --shard-iterator-type LATEST \
        --query 'ShardIterator' \
        --output text) \
    --limit 10

# Check DynamoDB detections
awslocal dynamodb scan \
    --table-name fraud-detections \
    --limit 10

# Verify pattern distribution
awslocal dynamodb scan \
    --table-name fraud-detections | \
    jq '.Items[] | .pattern_name.S' | sort | uniq -c
```

## Validation Checklist

- [ ] All 3 patterns deployed successfully
- [ ] Test data generated (105 transactions)
- [ ] Card testing pattern detected (5 alerts)
- [ ] Geographic anomaly detected (3 alerts)
- [ ] Amount spike detected (2 alerts)
- [ ] No false positives on normal transactions
- [ ] Fraud alerts in Kinesis stream
- [ ] Fraud records in DynamoDB
- [ ] Confidence scores > 80%
- [ ] Detection latency < 5 seconds

## Expected Results

**Fraud Distribution**:
- card_testing: 5 detections
- geographic_anomaly: 3 detections
- amount_spike: 2 detections
- Total: 10 fraud events detected

**Sample Fraud Alert**:
```json
{
  "fraud_id": "card_test_fraud_card_0_1704067200",
  "user_id": "fraud_card_0",
  "pattern_name": "card_testing",
  "confidence_score": 97.0,
  "details": {
    "failed_attempts": 4,
    "time_window_minutes": 10,
    "payment_method": "credit_card"
  },
  "transaction_ids": ["uuid1", "uuid2", "uuid3", "uuid4", "uuid5"]
}
```

## Troubleshooting

### Problem: Patterns not detecting

```bash
# Check Flink job status
curl http://localhost:8081/jobs

# Verify watermarks are progressing
curl http://localhost:8081/jobs/<job-id>/metrics?get=watermark

# Check state size
curl http://localhost:8081/jobs/<job-id>/metrics?get=State.Size
```

### Problem: False positives

Adjust thresholds in detector code:
- Card testing: Change required failures from 3 to 4
- Geographic: Reduce time window from 1 hour to 30 minutes
- Amount spike: Increase multiplier from 10x to 15x

### Problem: Missing events

```bash
# Verify transactions in source stream
awslocal kinesis describe-stream --stream-name transaction-stream

# Check consumer lag
awslocal kinesis get-records --shard-iterator ... --limit 5
```

## Key Learnings

1. **CEP Power**: Pattern matching is more expressive than simple filters
2. **State Management**: Keyed state essential for per-user tracking
3. **Time Windows**: Balance detection speed vs pattern completeness
4. **False Positives**: Tune confidence scores based on pattern strength
5. **MATCH_RECOGNIZE**: SQL syntax simpler for sequence patterns

## Next Steps

- **Exercise 05**: Integrate ML models for fraud scoring
- **Production**: Add pattern versioning and A/B testing
- **Optimization**: Use Rete algorithm for complex patterns

## Additional Resources

- [Flink CEP Documentation](https://nightlies.apache.org/flink/flink-docs-master/docs/libs/cep/)
- [MATCH_RECOGNIZE Guide](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/queries/match_recognize/)
- [Fraud Detection Patterns](https://www.ververica.com/blog/complex-event-processing-flink-cep-update)
