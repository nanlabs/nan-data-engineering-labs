# Kafka Quick Reference

Essential Kafka commands and Python snippets for quick reference.

---

## 🔧 CLI Commands

### Topics

```bash
# List all topics
kafka-topics --bootstrap-server localhost:9092 --list

# Create topic
kafka-topics --bootstrap-server localhost:9092 \
  --create \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 1

# Describe topic
kafka-topics --bootstrap-server localhost:9092 \
  --describe \
  --topic my-topic

# Delete topic
kafka-topics --bootstrap-server localhost:9092 \
  --delete \
  --topic my-topic

# Alter partitions (increase only)
kafka-topics --bootstrap-server localhost:9092 \
  --alter \
  --topic my-topic \
  --partitions 6
```

### Producer/Consumer

```bash
# Console producer
kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic my-topic

# Console consumer (from beginning)
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --from-beginning

# Console consumer (latest only)
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic my-topic

# With key display
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --property print.key=true \
  --property key.separator=":"
```

### Consumer Groups

```bash
# List consumer groups
kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe group
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --describe \
  --group my-group

# Reset offsets to earliest
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group \
  --topic my-topic \
  --reset-offsets \
  --to-earliest \
  --execute

# Reset offsets to specific offset
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group my-group \
  --topic my-topic:0 \
  --reset-offsets \
  --to-offset 100 \
  --execute
```

---

## 🐍 Python Snippets

### Simple Producer

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send message
producer.send('my-topic', {'key': 'value'})
producer.flush()
```

### Simple Consumer

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='my-group'
)

for message in consumer:
    print(message.value)
```

### Producer with Key

```python
producer.send(
    'my-topic',
    key='user_123'.encode('utf-8'),
    value={'event': 'purchase', 'amount': 99.99}
)
```

### Manual Commit

```python
consumer = KafkaConsumer(
    'my-topic',
    enable_auto_commit=False,
    ...
)

for message in consumer:
    process(message.value)
    consumer.commit()  # Manual commit
```

### Avro Producer (Confluent)

```python
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

sr_client = SchemaRegistryClient({'url': 'http://localhost:8081'})
avro_serializer = AvroSerializer(sr_client, schema_str)

producer = Producer({'bootstrap.servers': 'localhost:9092'})

producer.produce(
    topic='my-topic',
    value=avro_serializer(data, SerializationContext('my-topic', MessageField.VALUE)),
    key='user_123'.encode('utf-8')
)
producer.flush()
```

---

## 📊 Monitoring

### Get Lag

```python
from kafka import KafkaConsumer, TopicPartition, KafkaAdminClient

admin = KafkaAdminClient(bootstrap_servers='localhost:9092')
consumer = KafkaConsumer(bootstrap_servers='localhost:9092')

# Get group offsets
offsets = admin.list_consumer_group_offsets('my-group')

# Get end offsets
partitions = [TopicPartition('my-topic', p) for p in consumer.partitions_for_topic('my-topic')]
end_offsets = consumer.end_offsets(partitions)

# Calculate lag
for tp in partitions:
    committed = offsets.get(tp)
    end = end_offsets.get(tp)
    lag = end - committed.offset if committed else 0
    print(f"Partition {tp.partition}: lag = {lag}")
```

---

## ⚙️ Configuration

### Producer Config

```python
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    acks='all',             # Wait for all replicas
    retries=3,              # Retry failed sends
    batch_size=16384,       # Batch size bytes
    linger_ms=10,           # Wait time to batch
    compression_type='gzip' # Compress messages
)
```

### Consumer Config

```python
consumer = KafkaConsumer(
    'my-topic',
    bootstrap_servers='localhost:9092',
    group_id='my-group',
    auto_offset_reset='earliest',    # earliest | latest
    enable_auto_commit=True,
    auto_commit_interval_ms=5000,
    max_poll_records=500,
    session_timeout_ms=10000,
    heartbeat_interval_ms=3000
)
```

---

## 🎯 Common Patterns

### At-Least-Once

```python
consumer = KafkaConsumer(..., enable_auto_commit=False)

for message in consumer:
    try:
        process(message.value)
        consumer.commit()  # Commit after processing
    except Exception:
        # Don't commit, will retry
        pass
```

### Exactly-Once (Transactional)

```python
producer = KafkaProducer(
    ...,
    transactional_id='my-app-01',
    enable_idempotence=True
)

producer.init_transactions()

try:
    producer.begin_transaction()
    producer.send('output-topic', data)
    producer.commit_transaction()
except Exception:
    producer.abort_transaction()
```

### Batch Processing

```python
batch = []
for message in consumer:
    batch.append(message.value)

    if len(batch) >= 100:
        process_batch(batch)
        consumer.commit()
        batch = []
```

---

## 🔍 Debug

### Check if topic exists

```python
from kafka import KafkaAdminClient

admin = KafkaAdminClient(bootstrap_servers='localhost:9092')
topics = admin.list_topics()
print('my-topic' in topics)
```

### Get partition info

```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(bootstrap_servers='localhost:9092')
partitions = consumer.partitions_for_topic('my-topic')
print(f"Partitions: {sorted(partitions)}")
```

### Peek at messages

```python
consumer = KafkaConsumer(
    'my-topic',
    ...,
    consumer_timeout_ms=5000  # Stop after 5s no messages
)

messages = []
for msg in consumer:
    messages.append(msg.value)
    if len(messages) >= 10:
        break

print(f"First 10 messages: {messages}")
```
