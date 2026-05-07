# Streaming Basics - Conceptos Fundamentales

## index

1. [What is Stream Processing?](#what-is-stream-processing)
2. [Streaming vs Batch Processing](#streaming-vs-batch-processing)
3. [Event-Driven Architecture](#event-driven-architecture)
4. [Apache Kafka Fundamentals](#apache-kafka-fundamentals)
5. [Stream Processing Concepts](#stream-processing-concepts)
6. [Delivery Semantics](#delivery-semantics)
7. [Windowing](#windowing)
8. [State Management](#state-management)
9. [Schema Management](#schema-management)
10. [Best Practices](#best-practices)

---

## What is Stream Processing?

### Definition

**Stream Processing** is the continuous processing of data in motion in real time or near-real-time, as events arrive at the system.

Unlike batch processing that processes static data at rest, streaming processes:

- 📊 **Continuous events**: Data that constantly flows
- ⏱️ **Baja latency**: Procesamiento en segundos o milisegundos
- 🔄 **Endless data**: Infinite streams with no time limit

### Casos de Uso

```python
# Ejemplos de streaming en producción:

# 1. Real-time Analytics
event = {
    "user_id": "user_123",
    "action": "purchase",
    "amount": 99.99,
    "timestamp": "2024-03-07T10:30:00Z"
}
# → Actualizar dashboard en tiempo real

# 2. Fraud Detection
transaction = {
    "card_id": "card_456",
    "amount": 5000,
    "location": "Nigeria"
}
# → Alertar si patrón sospechoso

# 3. IoT Monitoring
sensor_reading = {
    "device_id": "sensor_789",
    "temperature": 95.5,
    "timestamp": "2024-03-07T10:30:01Z"
}
# → Alertar si excede umbral

# 4. Log Analysis
log_entry = {
    "level": "ERROR",
    "service": "api",
    "message": "Database connection failed"
}
# → Alertar al on-call engineer
```text

### Aplicaciones Reales

| Industria | Caso de Uso | latency Requerida |
|-----------|-------------|-------------------|
| **Finance** | Fraud detection | < 100ms |
| **E-commerce** | Real-time recommendations | < 1 second |
| **IoT** | Sensor monitoring | < 5 seconds |
| **Gaming** | Leaderboards | < 1 second |
| **Logistics** | Package tracking | < 10 seconds |
| **Social Media** | Activity feeds | < 2 seconds |

---

## Streaming vs Batch Processing

### Comparison

| Aspecto | Batch Processing | Stream Processing |
|---------|-----------------|-------------------|
| **Data** | Data at rest (almacenada) | Data in motion (fluyendo) |
| **latency** | Minutes to hours | Milliseconds to seconds |
| **Volumen** | Grandes conjuntos completos | Eventos individuales |
| **Processing** | Newspaper (hourly, daily) | Continuous (24/7) |
| **Complejidad** | Menor (mapreduce simple) | Mayor (state, windowing) |
| **Costo** | Menor (solo cuando corre) | Mayor (siempre corriendo) |
| **Use Cases** | Reporting, ETL, ML training | Alertas, monitoring, dashboards |

### Ejemplo Comparativo: E-commerce Analytics

**Batch Processing (cada hora)**:

```python
# Corre cada hora en un cron job
def hourly_analytics():
    # Leer todas las transacciones de la última hora
    transactions = read_from_db(last_hour)

    # Calcular métricas agregadas
    revenue = transactions['amount'].sum()
    orders = len(transactions)
    avg_order_value = revenue / orders

    # Escribir a data warehouse
    write_to_warehouse({
        'hour': current_hour,
        'revenue': revenue,
        'orders': orders,
        'aov': avg_order_value
    })
```text

**Stream Processing (continuo)**:

```python
# Corre 24/7, procesa cada evento
def process_transaction(transaction):
    # Evento individual llega
    event = {
        'timestamp': transaction['ts'],
        'amount': transaction['amount'],
        'user_id': transaction['user_id']
    }

    # Actualizar métricas en tiempo real
    update_live_dashboard(event)

    # Detectar anomalías inmediatamente
    if is_fraudulent(event):
        trigger_alert(event)

    # Actualizar recomendaciones personalizadas
    update_recommendations(event['user_id'])
```text

### When to Use Each

**Use Batch When**:

- ✅ latency of hours is acceptable
- ✅ Procesas datasets completos (full scans)
- ✅ Operaciones complejas (joins, aggregations pesadas)
- ✅ Costo es prioridad
- ✅ Historical data (backfills)

**Use Streaming When**:

- ✅ Necesitas baja latency (< 1 minuto)
- ✅ Eventos deben procesarse inmediatamente
- ✅ Real-time anomaly detection
- ✅ Dashboards live
- ✅ Critical alerts

**Lambda Architecture** (combinando ambos):

```
┌─────────────────┐
│  Data Source    │
└────────┬────────┘
         ├──────────────────┐
         │                  │
    ┌────▼─────┐      ┌────▼────────┐
    │  Batch   │      │  Streaming  │
    │  Layer   │      │   Layer     │
    └────┬─────┘      └────┬────────┘
         │                  │
         └──────┬───────────┘
                │
         ┌──────▼──────┐
         │   Serving   │
         │    Layer    │
         └─────────────┘
```text

---

## Event-Driven Architecture

### Conceptos Core

**Event**: Something that happened at a point in time

```python
event = {
    "event_id": "evt_123",
    "event_type": "order_placed",
    "timestamp": "2024-03-07T10:30:00Z",
    "payload": {
        "order_id": "ord_456",
        "user_id": "user_789",
        "amount": 99.99
    }
}
```text

### Event Types

1. **Domain Events**: Cambios en el model de negocio

   ```python
   # OrderPlaced, UserRegistered, PaymentProcessed
   ```

2. **System Events**: Technical events

   ```python
   # ServerStarted, CacheInvalidated, JobCompleted
   ```text

3. **Integration Events**: Comunican entre bounded contexts

   ```python
   # CustomerUpdated, InventoryChanged
   ```

### Event Sourcing Pattern

En lugar de almacenar el estado actual, almacenas todos los eventos:

```python
# Traditional CRUD (estado actual)
user = {
    "user_id": "user_123",
    "email": "john@example.com",
    "status": "active",
    "balance": 100
}

# Event Sourcing (historial de eventos)
events = [
    {"type": "UserCreated", "email": "john@example.com", "ts": "2024-01-01T00:00:00Z"},
    {"type": "EmailChanged", "old": "john@example.com", "new": "john@newdomain.com", "ts": "2024-02-01T00:00:00Z"},
    {"type": "DepositMade", "amount": 50, "ts": "2024-02-15T10:00:00Z"},
    {"type": "PurchaseMade", "amount": 30, "ts": "2024-03-01T15:00:00Z"},
    {"type": "UserDeactivated", "ts": "2024-03-05T09:00:00Z"}
]

# Reconstruir estado actual desde eventos
def replay_events(events):
    user = {}
    for event in events:
        if event['type'] == 'UserCreated':
            user['email'] = event['email']
            user['balance'] = 0
            user['status'] = 'active'
        elif event['type'] == 'EmailChanged':
            user['email'] = event['new']
        elif event['type'] == 'DepositMade':
            user['balance'] += event['amount']
        elif event['type'] == 'PurchaseMade':
            user['balance'] -= event['amount']
        elif event['type'] == 'UserDeactivated':
            user['status'] = 'inactive'
    return user
```text

**Ventajas**:

- 📜 Full audit (immutable history)
- 🔄 Replay para debugging
- 📊 Temporal analysis (state at any point)
- 🔙 Easy rollback

---

## Apache Kafka Fundamentals

### What is Kafka?

Apache Kafka es una plataforma de streaming distribuida que funciona como un **event bus** o **message broker** altamente scalable.

```text
┌──────────┐                  ┌─────────┐                  ┌──────────┐
│ Producer │──── publish ────▶│  Kafka  │──── consume ────▶│ Consumer │
│ (App 1)  │                  │ Cluster │                  │ (App 2)  │
└──────────┘                  └─────────┘                  └──────────┘
```text

### Conceptos Clave

**1. Topic**: Logical channel where events are published

```python
# Topics son como tablas en una base de datos
topics = [
    "user-events",      # Eventos de usuarios
    "transactions",     # Transacciones financieras
    "logs",            # Logs de aplicación
    "metrics"          # Métricas de sistema
]
```

**2. Partition**: Physical division of a topic for parallelism

```text
Topic: "transactions"
├── Partition 0: [event1, event4, event7, ...]
├── Partition 1: [event2, event5, event8, ...]
└── Partition 2: [event3, event6, event9, ...]
```text

**3. Producer**: Application that publishes events

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Enviar evento
event = {"user_id": "user_123", "action": "purchase", "amount": 99.99}
producer.send('transactions', event)
producer.flush()
```text

**4. Consumer**: Application that reads events

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='analytics-service'
)

# Leer eventos
for message in consumer:
    event = message.value
    process(event)
```

**5. Consumer Group**: Grupo de consumers que procesan en paralelo

```text
Topic "transactions" (3 partitions)
├── Partition 0  →  Consumer A  ┐
├── Partition 1  →  Consumer B  ├─ Consumer Group "analytics"
└── Partition 2  →  Consumer C  ┘

Topic "transactions" (3 partitions)
├── Partition 0  →  Consumer X  ┐
├── Partition 1  →  Consumer Y  ├─ Consumer Group "fraud-detection"
└── Partition 2  →  Consumer Z  ┘
```text

### features de Kafka

| features | Description | Example |
|---------------|-------------|---------|
| **Durability** | Events persist to disk | Retention 7 days |
| **scalability** | Horizontal distribution | 1000+ partitions |
| **Alto throughput** | Millones mensajes/segundo | LinkedIn: 7M msgs/sec |
| **Low latency** | < 10ms end-to-end | Critical for real-time |
| **Fault tolerance** | automatic replication | 3 replicas by default |
| **Ordering** | Guarantee within partition | FIFO per partition |

### Message Anatomy

```python
message = {
    # Metadata (automático)
    "offset": 12345,           # Posición única en partition
    "partition": 2,            # A qué partition pertence
    "timestamp": 1678195800,   # Unix timestamp
    "key": "user_123",         # Para partitioning

    # Payload (tu data)
    "value": {
        "event_type": "purchase",
        "amount": 99.99,
        "product_id": "prod_456"
    },

    # Headers opcionales
    "headers": {
        "schema_version": "v2",
        "source": "mobile_app"
    }
}
```text

---

## Stream Processing Concepts

### Stateless Processing

Cada evento se procesa independientemente sin memoria de eventos previos:

```python
# Stateless: Filtrar eventos
def filter_high_value(event):
    if event['amount'] > 1000:
        return event
    return None

# Stateless: Transformar eventos
def enrich_event(event):
    event['processed_at'] = current_timestamp()
    event['category'] = categorize(event['amount'])
    return event
```

### Stateful Processing

Mantiene estado entre eventos (requiere state store):

```python
# Stateful: Conteo acumulado
state = {}  # User ID → Count

def count_per_user(event):
    user_id = event['user_id']
    state[user_id] = state.get(user_id, 0) + 1
    return {
        'user_id': user_id,
        'total_events': state[user_id]
    }

# Stateful: Running average
state = {}  # User ID → (sum, count)

def running_average(event):
    user_id = event['user_id']
    amount = event['amount']

    if user_id not in state:
        state[user_id] = (0, 0)

    total, count = state[user_id]
    state[user_id] = (total + amount, count + 1)

    return {
        'user_id': user_id,
        'avg_amount': state[user_id][0] / state[user_id][1]
    }
```text

### Stream Transformations

```python
from kafka import KafkaConsumer, KafkaProducer

# 1. Filter
def apply_filter(stream):
    for event in stream:
        if event['amount'] > 100:
            yield event

# 2. Map
def apply_map(stream):
    for event in stream:
        yield {
            'user_id': event['user_id'],
            'amount_usd': event['amount'] * 1.0,
            'amount_eur': event['amount'] * 0.92
        }

# 3. FlatMap
def apply_flatmap(stream):
    for event in stream:
        # Un evento puede generar múltiples eventos
        for product in event['products']:
            yield {
                'order_id': event['order_id'],
                'product_id': product['id'],
                'quantity': product['qty']
            }

# 4. Aggregate (stateful)
def apply_aggregate(stream, window_size=60):
    from collections import defaultdict
    window = defaultdict(list)

    for event in stream:
        minute = event['timestamp'] // 60
        window[minute].append(event['amount'])

        if len(window[minute]) >= window_size:
            yield {
                'minute': minute,
                'total': sum(window[minute]),
                'count': len(window[minute]),
                'avg': sum(window[minute]) / len(window[minute])
            }
            del window[minute]
```text

---

## Delivery Semantics

### Three Guarantees

**1. At-Most-Once** (puede perderse):

```python
# Read mensaje → Procesa → Commit offset
# Si falla antes de commit, se pierde el mensaje
consumer.poll()
process_message(msg)
consumer.commit()  # ← Si falla aquí, mensaje perdido
```text

**2. At-Least-Once** (puede duplicarse):

```python
# Read mensaje → Commit offset → Procesa
# Si falla después de commit pero antes de procesar, se duplic
consumer.commit()  # ← Commit primero
process_message(msg)  # ← Si falla aquí, mensaje ya committed
```

**3. Exactly-Once** (una sola vez):

```python
# Usa transacciones de Kafka
producer.init_transactions()
producer.begin_transaction()
try:
    producer.send(topic, msg)
    consumer.commit_offsets()
    producer.commit_transaction()
except Exception:
    producer.abort_transaction()
```text

### Comparison

| Semantic | Guarantee | Performance | Usage |
|----------|----------|-------------|-----|
| **At-Most-Once** | You can lose | Faster | Logs, metrics |
| **At-Least-Once** | Puede duplicar | Medio | Analytics (idempotente) |
| **Exactly-Once** | Exactly once | Slower | Payments, transactions |

### Idempotencia

Para manejar duplicados con at-least-once:

```python
# Usar ID único para deduplicación
processed_ids = set()

def process_with_dedup(event):
    event_id = event['event_id']

    if event_id in processed_ids:
        # Ya procesado, skip
        return

    # Procesar
    do_something(event)

    # Marcar como procesado
    processed_ids.add(event_id)
```text

---

## Windowing

### Why Windowing?

Streams son infinitos, necesitamos dividirlos en ventanas finitas para agregar:

```python
# Stream infinito
events = [evt1, evt2, evt3, evt4, evt5, ...]  # ∞

# Con windowing: dividir en ventanas de 1 minuto
window_1 = [evt1, evt2, evt3]  # 10:00 - 10:01
window_2 = [evt4, evt5]        # 10:01 - 10:02
window_3 = [...]               # 10:02 - 10:03
```text

### Tipos de Windows

**1. Tumbling Window** (no se sobreponen):

```
Time: ────────────────────────────▶
      [Window 1][Window 2][Window 3]
Size: 1 minute  1 minute  1 minute
```text

```python
# Ejemplo: Contar eventos cada minuto
def tumbling_count(stream, window_size=60):
    from collections import defaultdict
    windows = defaultdict(int)

    for event in stream:
        window_key = event['timestamp'] // window_size
        windows[window_key] += 1

        # Emitir cuando window completa
        if should_emit(window_key):
            yield {
                'window_start': window_key * window_size,
                'window_end': (window_key + 1) * window_size,
                'count': windows[window_key]
            }
```text

**2. Sliding Window** (se sobreponen):

```text
Time: ────────────────────────────▶
      [──── Window 1 ────]
          [──── Window 2 ────]
              [──── Window 3 ────]
Size: 5 minutes, slide every 1 minute
```

```python
# Ejemplo: Moving average de últimos 5 minutes
def sliding_average(stream, window_size=300, slide=60):
    from collections import deque
    window = deque(maxlen=window_size//slide)

    for event in stream:
        window.append(event['amount'])

        if len(window) == window.maxlen:
            yield {
                'timestamp': event['timestamp'],
                'avg_last_5min': sum(window) / len(window)
            }
```text

**3. Session Window** (basado en inactividad):

```text
Time: ─────────────────────────────────────▶
      [Session 1]     [Session 2] [Session 3]
Events: ███─────────────███████────█────────
Gap:       ^ 10 min      ^ 10 min   ^ 10 min
```text

```python
# Ejemplo: Sesiones de usuario (gap de 10 minutes)
def session_window(stream, gap_seconds=600):
    sessions = {}

    for event in stream:
        user_id = event['user_id']
        timestamp = event['timestamp']

        if user_id in sessions:
            last_event = sessions[user_id]['last_timestamp']

            if timestamp - last_event > gap_seconds:
                # Nueva sesión (gap exceeded)
                yield sessions[user_id]
                sessions[user_id] = new_session(event)
            else:
                # Misma sesión
                sessions[user_id]['events'].append(event)
                sessions[user_id]['last_timestamp'] = timestamp
        else:
            # Primera sesión del usuario
            sessions[user_id] = new_session(event)
```

---

## State Management

### Local State

Estado en memoria del proceso:

```python
# Ventaja: Rápido (RAM)
# Desventaja: Se pierde si falla el proceso
state = {}

def stateful_process(event):
    key = event['key']
    state[key] = state.get(key, 0) + 1
    return state[key]
```text

### Distributed State Store

Estado persistido y replicado (ej: RocksDB en Kafka Streams):

```python
from kafka.streams import StreamsBuilder, KTable

# KTable = tabla changelog compactada
builder = StreamsBuilder()
table = builder.table('user-counts')  # State store

# State automáticamente:
# - Persistido a disco
# - Replicado a otros nodos
# - Recuperado en failover
```text

### Checkpointing

Save state periodically for recovery:

```python
import pickle

state = {}
checkpoint_interval = 1000  # cada 1000 eventos
events_processed = 0

for event in stream:
    # Procesar
    key = event['key']
    state[key] = state.get(key, 0) + 1
    events_processed += 1

    # Checkpoint periódico
    if events_processed % checkpoint_interval == 0:
        with open('checkpoint.pkl', 'wb') as f:
            pickle.dump(state, f)
        consumer.commit()  # Commit offset

# Al reiniciar, cargar desde checkpoint
try:
    with open('checkpoint.pkl', 'rb') as f:
        state = pickle.load(f)
except FileNotFoundError:
    state = {}
```text

---

## Schema Management

### Avro Schema

Efficient binary format with explicit schema:

```json
{
  "type": "record",
  "name": "PurchaseEvent",
  "namespace": "com.example.events",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "product_id", "type": "string"},
    {"name": "amount", "type": "double"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "currency", "type": "string", "default": "USD"}
  ]
}
```

```python
from avro.io import DatumWriter, BinaryEncoder
import avro.schema
import io

# Cargar schema
schema = avro.schema.parse(open("purchase_event.avsc").read())

# Serializar evento
writer = DatumWriter(schema)
bytes_writer = io.BytesIO()
encoder = BinaryEncoder(bytes_writer)

event = {
    "event_id": "evt_123",
    "user_id": "user_456",
    "product_id": "prod_789",
    "amount": 99.99,
    "timestamp": 1678195800000,
    "currency": "USD"
}

writer.write(event, encoder)
raw_bytes = bytes_writer.getvalue()
```text

### Schema Registry

Repositorio centralizado de schemas (Confluent Schema Registry):

```python
from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer

# Producer con schema registry
producer = AvroProducer({
    'bootstrap.servers': 'localhost:9092',
    'schema.registry.url': 'http://localhost:8081'
}, default_value_schema=schema)

# Schema automáticamente registrado y versionado
producer.produce(topic='purchases', value=event)
```text

### Schema Evolution

Cambiar schema sin romper compatibilidad:

```python
# v1: Schema original
{
  "name": "User",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "email", "type": "string"}
  ]
}

# v2: Agregar campo con default (backward compatible)
{
  "name": "User",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "phone", "type": ["null", "string"], "default": null}  # Nuevo
  ]
}

# Consumers v1 pueden leer messages v2 (ignoran phone)
# Consumers v2 pueden leer messages v1 (usan default null)
```text

**Compatibility Modes**:

- **BACKWARD**: Consumers nuevos leen data antigua
- **FORWARD**: Consumers antiguos leen data nueva
- **FULL**: Ambos (backward + forward)

---

## Best Practices

### 1. Monitoring & Alerting

```python
import structlog

logger = structlog.get_logger()

# Log métricas clave
def process_event(event):
    start = time.time()

    try:
        result = do_processing(event)

        # Metrics
        processing_time = time.time() - start
        logger.info("event_processed",
            event_type=event['type'],
            processing_time_ms=processing_time * 1000,
            status="success"
        )

        # Alert si lento
        if processing_time > 1.0:
            alert("Slow processing", event)

        return result

    except Exception as e:
        logger.error("event_processing_failed",
            event_type=event['type'],
            error=str(e)
        )
        # Alert on failure
        alert("Processing failed", event, e)
        raise
```

**Critical Metrics**:

- 📊 **throughput**: Eventos/segundo
- ⏱️ **Latency**: Tiempo end-to-end
- 🔄 **Lag**: Diferencia entre producido y consumido
- ❌ **Error Rate**: Porcentaje de failures

### 2. Error Handling

```python
# Dead Letter Queue (DLQ) para mensajes fallidos
def process_with_dlq(event):
    max_retries = 3
    retry_count = event.get('_retry_count', 0)

    try:
        result = do_processing(event)
        return result

    except Exception as e:
        if retry_count < max_retries:
            # Retry con backoff
            event['_retry_count'] = retry_count + 1
            time.sleep(2 ** retry_count)  # Exponential backoff
            return process_with_dlq(event)
        else:
            # Send to DLQ después de max retries
            send_to_dlq(event, error=str(e))
            logger.error("event_sent_to_dlq", event_id=event['id'])
```text

### 3. Backpressure

Manejar cuando processing no puede mantener el ritmo:

```python
from collections import deque

# Buffer limitado
buffer = deque(maxlen=1000)

def consume_with_backpressure():
    consumer = KafkaConsumer(...)

    for message in consumer:
        try:
            # Agregar a buffer
            buffer.append(message.value)
        except IndexError:
            # Buffer lleno, pausar consumer
            logger.warning("buffer_full_pausing_consumer")
            consumer.pause()

            # Procesar buffer
            process_buffer(buffer)
            buffer.clear()

            # Resumir consumer
            consumer.resume()
```text

### 4. Testing Streaming Applications

```python
import pytest

def test_event_filtering():
    # Arrange
    events = [
        {'amount': 50},
        {'amount': 150},
        {'amount': 200}
    ]

    # Act
    results = list(filter_high_value(events, threshold=100))

    # Assert
    assert len(results) == 2
    assert all(e['amount'] > 100 for e in results)

# Testing con time
from freezegun import freeze_time

@freeze_time("2024-03-07 10:00:00")
def test_windowing():
    events = generate_test_events(count=100)
    windows = list(tumbling_window(events, size=60))

    assert len(windows) == 10
    assert windows[0]['start'] == "2024-03-07T10:00:00Z"
```text

### 5. Performance Optimization

```python
# 1. Batch processing
def consume_in_batches(batch_size=100):
    consumer = KafkaConsumer(...)
    batch = []

    for message in consumer:
        batch.append(message)

        if len(batch) >= batch_size:
            # Procesar batch (más eficiente)
            process_batch(batch)
            consumer.commit()
            batch.clear()

# 2. Async processing
import asyncio

async def async_process(event):
    # I/O no bloqueante
    result = await fetch_from_api(event['user_id'])
    return enrich(event, result)

async def consume_async():
    consumer = KafkaConsumer(...)
    tasks = []

    for message in consumer:
        # Process concurrentemente
        task = asyncio.create_task(async_process(message.value))
        tasks.append(task)

        if len(tasks) >= 100:
            # Wait for batch
            await asyncio.gather(*tasks)
            tasks.clear()
            consumer.commit()

# 3. Parallelism con múltiples partitions
# Kafka automáticamente distribuye partitions entre consumers del mismo group
```

---

## Resumen

### Key Takeaways

✅ **Streaming procesa eventos continuos** en tiempo real
✅ **Kafka is the standard** for event streaming
✅ **Windowing permite agregar** streams infinitos
✅ **State management** is critical for stateful operations
✅ **Exactly-once is expensive** but necessary for critical cases
✅ **Schema registry** handles schema evolution
✅ **Monitoring and alerting** are essential in production

### Next Steps

1. 📖 Leer `02-architecture.md` para arquitecturas de streaming
2. 🏋️ Completar Exercise 01: Kafka Basics
3. 🔬 Experimentar con diferentes window types
4. 📊 Practicar stateful transformations
5. 🚀 Construir tu primer pipeline streaming

---

**Next**: [02-architecture.md](./02-architecture.md) - Streaming Architectures & AWS Kinesis
