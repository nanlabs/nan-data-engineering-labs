# Exercise 01: Kafka Basics

**Difficulty**: ⭐ Beginner
**Estimated Time**: 2-3 hours
**Prerequisites**: Docker, Python 3.8+

---

## 🎯 Objectives

Master Apache Kafka fundamentals:
- **Setup**: Run Kafka cluster locally with Docker
- **Producers**: Send events to Kafka topics
- **Consumers**: Read events from topics
- **Topics**: Create and manage topics
- **Consumer Groups**: Parallel processing

---

## 📚 Concepts

### Kafka Architecture

```
Producers → [Kafka Cluster] → Consumers
              ↓
           Topics
           ├─ Partition 0
           ├─ Partition 1
           └─ Partition 2
```

### Key Concepts

1. **Topic**: Logical channel for events
2. **Partition**: Physical division for parallelism
3. **Producer**: Publishes events to topics
4. **Consumer**: Reads events from topics
5. **Consumer Group**: Group of consumers processing in parallel

---

## 🏋️ Exercises

### Part 1: Setup Kafka Cluster (30 min)

**Task**: Start Kafka, Zookeeper, Schema Registry using Docker Compose

```bash
cd ../../infrastructure
docker-compose up -d

# Verify services
docker-compose ps

# Check logs
docker-compose logs kafka

# Access Kafka UI
open http://localhost:8080
```

**Expected**:
- ✅ All containers running
- ✅ Kafka UI accessible
- ✅ No errors in logs

### Part 2: Create Topics (20 min)

**Task**: Create topics with different partition counts

```bash
# Using kafka-topics command
docker exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --partitions 3 \
  --replication-factor 1

# List topics
docker exec kafka kafka-topics --list \
  --bootstrap-server localhost:9092

# Describe topic
docker exec kafka kafka-topics --describe \
  --bootstrap-server localhost:9092 \
  --topic user-events
```

**Create**:
- `user-events` (3 partitions)
- `sensor-readings` (6 partitions)
- `transactions` (4 partitions)

### Part 3: Simple Producer (45 min)

**File**: `starter/simple_producer.py`

**Task**: Implement Kafka producer

```python
from kafka import KafkaProducer
import json
import time

class SimpleProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_event(self, topic: str, event: dict) -> None:
        """TODO: Send event to Kafka topic"""
        pass

    def send_with_key(self, topic: str, key: str, event: dict) -> None:
        """TODO: Send event with key (for partitioning)"""
        pass

    def close(self):
        self.producer.flush()
        self.producer.close()
```

**Test**:
```python
producer = SimpleProducer()

# Send 100 events
for i in range(100):
    event = {
        'event_id': i,
        'event_type': 'PAGE_VIEW',
        'user_id': f'user_{i % 10}',
        'timestamp': int(time.time() * 1000)
    }
    producer.send_event('user-events', event)
    time.sleep(0.1)

producer.close()
```

### Part 4: Simple Consumer (45 min)

**File**: `starter/simple_consumer.py`

**Task**: Implement Kafka consumer

```python
from kafka import KafkaConsumer
import json

class SimpleConsumer:
    def __init__(self, topic: str, group_id: str,
                 bootstrap_servers=['localhost:9092']):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

    def consume(self, process_fn):
        """TODO: Consume messages and apply process_fn"""
        pass

    def close(self):
        self.consumer.close()
```

**Test**:
```python
def print_event(event):
    print(f"Received: {event['event_id']} - {event['event_type']}")

consumer = SimpleConsumer(
    topic='user-events',
    group_id='analytics-group'
)

consumer.consume(print_event)
```

### Part 5: Consumer Groups (30 min)

**Task**: Run multiple consumers in same group

```bash
# Terminal 1: Consumer A
python simple_consumer.py --group analytics --id consumer-A

# Terminal 2: Consumer B
python simple_consumer.py --group analytics --id consumer-B

# Terminal 3: Consumer C
python simple_consumer.py --group analytics --id consumer-C

# Terminal 4: Producer (send 300 events)
python simple_producer.py --count 300
```

**Expected**:
- Each consumer processes ~100 events (300 / 3)
- Partitions distributed among consumers
- No duplicate processing

### Part 6: Offset Management (30 min)

**File**: `starter/manual_commit.py`

**Task**: Manual offset commits for error handling

```python
consumer = KafkaConsumer(
    'user-events',
    enable_auto_commit=False  # Manual commit
)

for message in consumer:
    try:
        event = message.value
        process_event(event)

        # Commit only if successful
        consumer.commit()
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        # Don't commit, will retry
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_kafka_basics.py -v
```

**Expected Results**:
- ✅ Producer sends events to correct topic
- ✅ Consumer receives all events
- ✅ Consumer groups distribute load
- ✅ Manual commits work correctly
- ✅ Events with same key go to same partition

---

## 📚 Key Learnings

1. **Kafka Basics**:
   - Producers send, consumers read
   - Topics have partitions
   - Consumer groups enable parallelism

2. **Partitioning**:
   - Key-based: Same key → same partition
   - Round-robin: No key → distributed evenly

3. **Consumer Groups**:
   - One partition → one consumer in group
   - Adding consumers → rebalance

4. **Offset Management**:
   - Auto-commit: Fire and forget
   - Manual commit: At-least-once guarantee

---

## 🚀 Next Steps

- ✅ Exercise 02: Stream processing with transformations
- ✅ Read theory/02-architecture.md
- ✅ Explore Kafka UI for monitoring
