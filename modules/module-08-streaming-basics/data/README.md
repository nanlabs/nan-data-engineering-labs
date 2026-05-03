# Stream Event Generator

Generate realistic streaming events for testing and learning.

## Usage

### Stream Mode (Continuous)

Generate events continuously at specified rate:

```bash
# User events at 10 events/second
python stream_generator.py --type user --mode stream --rate 10

# Sensor readings at 100 events/second for 60 seconds
python stream_generator.py --type sensor --mode stream --rate 100 --duration 60

# Transactions at 5 events/second to file
python stream_generator.py --type transaction --mode stream --rate 5 --output transactions.jsonl
```

### Batch Mode

Generate fixed number of events:

```bash
# Generate 10,000 user events
python stream_generator.py --type user --mode batch --count 10000 --output user_events.jsonl

# Generate 50,000 sensor readings
python stream_generator.py --type sensor --mode batch --count 50000 --output sensor_data.jsonl

# Generate 5,000 transactions
python stream_generator.py --type transaction --mode batch --count 5000 --output transactions.jsonl
```

## Event Types

### User Events
- `PAGE_VIEW`: User views a page
- `CLICK`: User clicks on element
- `PURCHASE`: User completes purchase
- `ADD_TO_CART`: User adds item to cart
- `SEARCH`: User searches for product
- `LOGIN`: User logs in

Fields:
- event_id, event_type, timestamp
- user_id, session_id
- page_url, product_id, amount, search_query
- country, device_type

### Sensor Readings
- `TEMPERATURE`: Temperature sensor (celsius)
- `HUMIDITY`: Humidity sensor (percent)
- `PRESSURE`: Pressure sensor (hPa)
- `MOTION`: Motion detector (boolean)

Fields:
- sensor_id, device_id, timestamp
- sensor_type, value, unit
- quality, battery_level
- location (optional)

### Transactions
- `PURCHASE`: Purchase transaction
- `REFUND`: Refund transaction
- `DEPOSIT`: Deposit to account
- `WITHDRAWAL`: Withdrawal from account

Fields:
- transaction_id, timestamp
- user_id, account_id
- amount, currency, payment_method
- status, risk_score, flagged_for_review
- merchant info, location

## Integration with Kafka

### Produce to Kafka Topic

```python
from kafka import KafkaProducer
import subprocess
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Stream events to Kafka
proc = subprocess.Popen(
    ['python', 'stream_generator.py', '--type', 'user', '--rate', '10'],
    stdout=subprocess.PIPE
)

for line in proc.stdout:
    event = json.loads(line)
    producer.send('user-events', event)
```

### Direct Kafka Producer Script

See `kafka_producer.py` for ready-to-use Kafka producer with event generation.

## Realistic Distributions

- **User Events**: 40% page views, 25% clicks, 10% purchases
- **Sensor Quality**: 85% good, 10% fair, 5% poor
- **Transaction Status**: 90% completed, 8% pending, 2% failed
- **Risk Scores**: Higher for international + large amounts

## Examples

### E-commerce Analytics

```bash
# Generate shopping behavior for past hour
python stream_generator.py --type user --mode stream --rate 50 --duration 3600 --output shopping_1h.jsonl
```

### IoT Monitoring

```bash
# Generate sensor readings (1000 sensors, 1 reading/sec each)
python stream_generator.py --type sensor --mode stream --rate 1000 --duration 600
```

### Fraud Detection

```bash
# Generate transactions with varying risk scores
python stream_generator.py --type transaction --mode stream --rate 20 --output fraud_detection.jsonl
```
