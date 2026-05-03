# Streaming Patterns Guide

Common patterns for stream processing applications.

---

## 1. Filtering

**Use Case**: Remove unwanted events

**Pattern**:
```python
for message in consumer:
    event = message.value

    # Filter condition
    if event['amount'] > 100:
        process_high_value_event(event)
```

**Example**: Filter high-value transactions

---

## 2. Mapping / Enrichment

**Use Case**: Transform or enrich events

**Pattern**:
```python
user_profiles = load_profiles()  # Lookup table

for message in consumer:
    event = message.value

    # Enrich with profile data
    enriched = {
        **event,
        'user_tier': user_profiles[event['user_id']]['tier'],
        'user_country': user_profiles[event['user_id']]['country']
    }

    producer.send('enriched-events', enriched)
```

**Example**: Enrich user events with profile data

---

## 3. Stateful Aggregation

**Use Case**: Running totals per key

**Pattern**:
```python
state = {}  # user_id -> {'count': int, 'total': float}

for message in consumer:
    event = message.value
    user_id = event['user_id']

    # Update state
    if user_id not in state:
        state[user_id] = {'count': 0, 'total': 0}

    state[user_id]['count'] += 1
    state[user_id]['total'] += event['amount']

    # Emit aggregate
    aggregate = {
        'user_id': user_id,
        **state[user_id],
        'average': state[user_id]['total'] / state[user_id]['count']
    }

    producer.send('user-aggregates', aggregate)
```

**Example**: User purchase totals

---

## 4. Windowed Aggregation

**Use Case**: Aggregates over time windows

**Pattern** (Tumbling Window):
```python
from collections import defaultdict

window_size = 60  # seconds
windows = defaultdict(lambda: {'count': 0, 'total': 0})

def get_window_key(timestamp_ms):
    return timestamp_ms // (window_size * 1000)

for message in consumer:
    event = message.value
    window_key = get_window_key(event['timestamp'])

    # Update window
    windows[window_key]['count'] += 1
    windows[window_key]['total'] += event['amount']

    # Emit completed windows
    current_window = get_window_key(int(time.time() * 1000))
    for w_key in list(windows.keys()):
        if w_key < current_window - 1:
            emit_window(w_key, windows[w_key])
            del windows[w_key]
```

**Example**: Events per minute

---

## 5. Stream Join

**Use Case**: Combine two streams

**Pattern** (Stream-Table Join):
```python
# Load dimension table
products = load_products()  # product_id -> product data

for message in consumer:
    event = message.value

    # Join with product
    product = products.get(event['product_id'], {})
    joined = {
        **event,
        'product_name': product.get('name'),
        'product_category': product.get('category'),
        'product_price': product.get('price')
    }

    producer.send('joined-events', joined)
```

**Pattern** (Stream-Stream Join with Window):
```python
from collections import deque
import time

# Buffers for both streams
stream_a_buffer = deque(maxlen=1000)
stream_b_buffer = deque(maxlen=1000)

def find_matching_event(event, buffer, match_key, time_window_sec=60):
    event_time = event['timestamp']
    for buffered in buffer:
        if buffered[match_key] == event[match_key]:
            time_diff = abs(event_time - buffered['timestamp']) / 1000
            if time_diff <= time_window_sec:
                return buffered
    return None

# Join streams
for message in consumer_a:
    event_a = message.value

    # Find matching event in stream B
    event_b = find_matching_event(event_a, stream_b_buffer, 'user_id')

    if event_b:
        joined = {**event_a, **event_b}
        producer.send('joined-stream', joined)
    else:
        stream_a_buffer.append(event_a)
```

**Example**: Join clicks with impressions

---

## 6. Sessionization

**Use Case**: Group events by session

**Pattern**:
```python
from collections import defaultdict

sessions = defaultdict(list)
session_timeout = 30 * 60  # 30 minutes

def is_session_active(session_events, new_event_time):
    if not session_events:
        return False
    last_event_time = session_events[-1]['timestamp']
    return (new_event_time - last_event_time) / 1000 < session_timeout

for message in consumer:
    event = message.value
    session_id = event['session_id']

    if is_session_active(sessions[session_id], event['timestamp']):
        # Add to existing session
        sessions[session_id].append(event)
    else:
        # Close old session
        if sessions[session_id]:
            emit_session(session_id, sessions[session_id])

        # Start new session
        sessions[session_id] = [event]
```

**Example**: User browsing sessions

---

## 7. Deduplication

**Use Case**: Remove duplicate events

**Pattern** (Time-based):
```python
from collections import deque

seen_ids = set()
seen_queue = deque(maxlen=10000)  # Keep last 10K IDs

for message in consumer:
    event = message.value
    event_id = event['event_id']

    if event_id not in seen_ids:
        # New event, process it
        process(event)

        # Track ID
        seen_ids.add(event_id)
        seen_queue.append(event_id)

        # Remove oldest if needed
        if len(seen_ids) > 10000:
            oldest_id = seen_queue.popleft()
            seen_ids.discard(oldest_id)
```

**Example**: Deduplicate retry events

---

## 8. Dead Letter Queue

**Use Case**: Handle failed events

**Pattern**:
```python
dlq_producer = KafkaProducer(...)

for message in consumer:
    event = message.value

    try:
        process(event)
        consumer.commit()
    except RetryableError as e:
        # Retry
        time.sleep(1)
        retry_process(event)
    except Exception as e:
        # Send to DLQ
        dlq_event = {
            'original_event': event,
            'error': str(e),
            'failed_at': int(time.time() * 1000)
        }
        dlq_producer.send('failed-events-dlq', dlq_event)
        consumer.commit()  # Don't reprocess
```

**Example**: Failed payment processing

---

## 9. Fan-Out

**Use Case**: Send event to multiple destinations

**Pattern**:
```python
for message in consumer:
    event = message.value

    # Send to multiple topics
    if event['event_type'] == 'PURCHASE':
        producer.send('analytics-events', event)
        producer.send('revenue-events', event)
        producer.send('inventory-events', event)
```

**Example**: Purchase event distribution

---

## 10. Throttling / Rate Limiting

**Use Case**: Limit processing rate

**Pattern**:
```python
import time

rate_limit = 100  # events per second
sleep_time = 1.0 / rate_limit

for message in consumer:
    event = message.value

    process(event)
    time.sleep(sleep_time)
```

**Example**: API rate limiting

---

## 11. Change Data Capture (CDC)

**Use Case**: Stream database changes

**Pattern**:
```python
# Kafka Connect with Debezium captures DB changes
# Consumer processes change events

for message in consumer:
    change = message.value

    operation = change['op']  # c=create, u=update, d=delete
    before = change.get('before', {})
    after = change.get('after', {})

    if operation == 'c':
        handle_insert(after)
    elif operation == 'u':
        handle_update(before, after)
    elif operation == 'd':
        handle_delete(before)
```

**Example**: MySQL to Elasticsearch sync

---

## 12. CQRS (Command Query Responsibility Segregation)

**Use Case**: Separate read and write models

**Pattern**:
```python
# Write side: Commands to Kafka
producer.send('commands', {
    'type': 'UpdateUser',
    'user_id': '123',
    'name': 'John'
})

# Read side: Materialize view
materialized_view = {}

for message in consumer:
    command = message.value

    if command['type'] == 'UpdateUser':
        user_id = command['user_id']
        materialized_view[user_id] = command
```

**Example**: High-read user profiles

---

## 13. Saga Pattern

**Use Case**: Distributed transactions

**Pattern**:
```python
# Choreography-based saga
for message in consumer:
    event = message.value

    if event['type'] == 'OrderCreated':
        # Reserve inventory
        producer.send('inventory-commands', {
            'type': 'ReserveInventory',
            'order_id': event['order_id'],
            'items': event['items']
        })

    elif event['type'] == 'InventoryReserved':
        # Process payment
        producer.send('payment-commands', {
            'type': 'ProcessPayment',
            'order_id': event['order_id'],
            'amount': event['amount']
        })

    elif event['type'] == 'PaymentFailed':
        # Compensate: release inventory
        producer.send('inventory-commands', {
            'type': 'ReleaseInventory',
            'order_id': event['order_id']
        })
```

**Example**: Order processing workflow

---

## Best Practices

1. **Idempotency**: Make processing idempotent to handle retries
2. **State Management**: Periodically persist state to disk
3. **Error Handling**: Use DLQ for non-retryable errors
4. **Monitoring**: Track lag, throughput, error rate
5. **Testing**: Use test containers for integration tests
6. **Backpressure**: Handle slow downstream systems
7. **Schema Evolution**: Use schema registry for compatibility
8. **Exactly-Once**: Use transactions when needed
