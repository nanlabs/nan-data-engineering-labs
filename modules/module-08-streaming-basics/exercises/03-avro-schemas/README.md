# Exercise 03: Avro Schema Management

**Difficulty**: ⭐⭐ Intermediate
**Estimated Time**: 2-3 hours
**Prerequisites**: Exercise 01-02 completed

---

## 🎯 Objectives

Master schema management:
- **Avro**: Binary serialization format
- **Schema Registry**: Centralized schema storage
- **Evolution**: Backward/forward compatibility
- **Validation**: Type-safe event production

---

## 📚 Concepts

### Why Avro?

**Benefits**:
- ✅ Compact binary format (smaller than JSON)
- ✅ Schema evolution with compatibility checks
- ✅ Type safety at serialize/deserialize
- ✅ Language agnostic (Python, Java, etc.)

**Comparison**:
```
JSON:    {"user_id": "user_123", "amount": 99.99}  // 46 bytes
Avro:    Binary representation                     // ~20 bytes
```

### Schema Evolution Rules

**Backward Compatible** (new consumers, old producers):
- ✅ Add field with default
- ✅ Remove field

**Forward Compatible** (old consumers, new producers):
- ✅ Add field
- ✅ Remove field with default

**Full Compatible**:
- ✅ Add field with default
- ✅ Remove field with default

---

## 🏋️ Exercises

### Part 1: Register Schemas (30 min)

**Task**: Register Avro schemas in Schema Registry

```bash
# Check Schema Registry is running
curl http://localhost:8081/subjects

# Register user event schema
curl -X POST http://localhost:8081/subjects/user-events-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d @register_schema.json

# List all schemas
curl http://localhost:8081/subjects

# Get schema by ID
curl http://localhost:8081/schemas/ids/1
```

**File**: `scripts/register_schemas.py`

```python
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema

def register_schemas():
    sr_client = SchemaRegistryClient({'url': 'http://localhost:8081'})

    # Load schema from file
    with open('../../data/schemas/user_event.avsc') as f:
        schema_str = f.read()

    # Register schema
    schema = Schema(schema_str, schema_type='AVRO')
    schema_id = sr_client.register_schema(
        subject_name='user-events-value',
        schema=schema
    )

    print(f"Schema registered with ID: {schema_id}")
```

### Part 2: Avro Producer (45 min)

**Task**: Produce events with Avro serialization

**File**: `starter/avro_producer.py`

```python
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

class AvroProducer:
    def __init__(self, bootstrap_servers, schema_registry_url):
        # TODO: Initialize Schema Registry client
        self.sr_client = SchemaRegistryClient({
            'url': schema_registry_url
        })

        # TODO: Load schema
        with open('../../data/schemas/user_event.avsc') as f:
            schema_str = f.read()

        # TODO: Create Avro serializer
        self.avro_serializer = AvroSerializer(
            self.sr_client,
            schema_str
        )

        # TODO: Create producer
        self.producer = Producer({
            'bootstrap.servers': bootstrap_servers
        })

    def send_event(self, topic: str, event: dict):
        """TODO: Serialize and send event"""
        try:
            # Serialize value
            serialized_value = self.avro_serializer(
                event,
                SerializationContext(topic, MessageField.VALUE)
            )

            # Send to Kafka
            self.producer.produce(
                topic=topic,
                value=serialized_value,
                key=event.get('user_id', '').encode('utf-8')
            )

            self.producer.flush()
        except Exception as e:
            print(f"Error: {e}")
```

**Test**:
```python
producer = AvroProducer(
    bootstrap_servers='localhost:9092',
    schema_registry_url='http://localhost:8081'
)

event = {
    'event_id': 'evt_001',
    'event_type': 'PURCHASE',
    'timestamp': int(time.time() * 1000),
    'user_id': 'user_123',
    'session_id': 'session_456',
    'amount': 99.99,
    'currency': 'USD'
}

producer.send_event('user-events', event)
```

### Part 3: Avro Consumer (45 min)

**Task**: Consume and deserialize Avro events

**File**: `starter/avro_consumer.py`

```python
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

class AvroConsumer:
    def __init__(self, bootstrap_servers, schema_registry_url, group_id):
        # TODO: Initialize Schema Registry client
        self.sr_client = SchemaRegistryClient({
            'url': schema_registry_url
        })

        # TODO: Create Avro deserializer
        self.avro_deserializer = AvroDeserializer(self.sr_client)

        # TODO: Create consumer
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })

    def consume(self, topic: str, process_fn):
        """TODO: Consume and deserialize events"""
        self.consumer.subscribe([topic])

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    print(f"Error: {msg.error()}")
                    continue

                # Deserialize value
                event = self.avro_deserializer(
                    msg.value(),
                    SerializationContext(topic, MessageField.VALUE)
                )

                # Process event
                process_fn(event)
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()
```

### Part 4: Schema Evolution (60 min)

**Task**: Evolve schema while maintaining compatibility

**Scenario**: Add `user_tier` field to user events

**Step 1: Create new schema version**

`data/schemas/user_event_v2.avsc`:
```json
{
  "type": "record",
  "name": "UserEvent",
  "namespace": "com.training.events",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "user_tier", "type": "string", "default": "free"}  // NEW FIELD
  ]
}
```

**Step 2: Check compatibility**

```python
def check_compatibility(new_schema_str: str, subject: str):
    """TODO: Check if new schema is compatible"""
    sr_client = SchemaRegistryClient({'url': 'http://localhost:8081'})

    # Get latest schema
    latest = sr_client.get_latest_version(subject)

    # Test compatibility
    is_compatible = sr_client.test_compatibility(
        subject_name=subject,
        schema=Schema(new_schema_str, 'AVRO')
    )

    return is_compatible
```

**Step 3: Register new version**

```python
if check_compatibility(new_schema_str, 'user-events-value'):
    schema_id = sr_client.register_schema(
        subject_name='user-events-value',
        schema=Schema(new_schema_str, 'AVRO')
    )
    print(f"New schema version registered: {schema_id}")
else:
    print("Schema not compatible!")
```

### Part 5: Schema Validation (45 min)

**Task**: Validate events before producing

**File**: `starter/schema_validator.py`

```python
from fastavro import validate
from fastavro.schema import load_schema

class SchemaValidator:
    def __init__(self, schema_file: str):
        self.schema = load_schema(schema_file)

    def validate_event(self, event: dict) -> bool:
        """TODO: Validate event against schema"""
        try:
            validate(event, self.schema)
            return True
        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def get_required_fields(self) -> list:
        """TODO: Return required fields from schema"""
        required = []
        for field in self.schema['fields']:
            if 'default' not in field and field['type'] != ['null', ...]:
                required.append(field['name'])
        return required
```

**Test**:
```python
validator = SchemaValidator('../../data/schemas/user_event.avsc')

# Valid event
event1 = {
    'event_id': 'evt_001',
    'event_type': 'PURCHASE',
    'timestamp': 1234567890,
    'user_id': 'user_123',
    'session_id': 'session_456'
}
assert validator.validate_event(event1) == True

# Invalid event (missing required field)
event2 = {
    'event_id': 'evt_002'
    # Missing required fields
}
assert validator.validate_event(event2) == False
```

### Part 6: Schema Registry CLI (30 min)

**Task**: Create CLI tool for schema management

**File**: `scripts/schema_cli.py`

```python
import click
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema

@click.group()
def cli():
    """Schema Registry CLI"""
    pass

@cli.command()
def list_schemas():
    """List all registered schemas"""
    # TODO: Implement
    pass

@cli.command()
@click.argument('subject')
def get_versions(subject):
    """Get all versions of a schema"""
    # TODO: Implement
    pass

@cli.command()
@click.argument('schema_file')
@click.argument('subject')
def register(schema_file, subject):
    """Register a new schema"""
    # TODO: Implement
    pass

@cli.command()
@click.argument('subject')
@click.argument('schema_file')
def check_compatibility(subject, schema_file):
    """Check if schema is compatible"""
    # TODO: Implement
    pass

if __name__ == '__main__':
    cli()
```

**Usage**:
```bash
# List schemas
python schema_cli.py list-schemas

# Get versions
python schema_cli.py get-versions user-events-value

# Register schema
python schema_cli.py register ../../data/schemas/user_event.avsc user-events-value

# Check compatibility
python schema_cli.py check-compatibility user-events-value user_event_v2.avsc
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_avro_schemas.py -v
```

**Tests cover**:
- ✅ Schema registration successful
- ✅ Avro serialization/deserialization
- ✅ Schema evolution compatibility
- ✅ Validation catches invalid events
- ✅ Backward compatibility maintained

---

## 📊 Benefits Comparison

| Feature | JSON | Avro |
|---------|------|------|
| Size | Larger | Smaller (50-70% reduction) |
| Schema | Optional | Required |
| Evolution | Manual | Automatic compatibility checks |
| Type Safety | Runtime only | Compile + Runtime |
| Performance | Slower | Faster (binary) |

---

## 🔑 Key Learnings

1. **Avro Benefits**: Smaller size, type safety, schema evolution
2. **Schema Registry**: Centralized schema management
3. **Compatibility**: Backward/forward/full compatibility rules
4. **Evolution**: Add fields with defaults for compatibility

---

## 🚀 Next Steps

- ✅ Exercise 04: AWS Kinesis streams
- ✅ Implement schema versioning strategy
- ✅ Test schema evolution scenarios
