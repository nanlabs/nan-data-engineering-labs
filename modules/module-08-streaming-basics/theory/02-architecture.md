# Streaming Architectures & Technologies

## index
1. [Apache Kafka Architecture](#apache-kafka-architecture)
2. [AWS Kinesis](#aws-kinesis)
3. [Apache Flink](#apache-flink)
4. [Stream Processing Patterns](#stream-processing-patterns)
5. [Lambda vs Kappa Architecture](#lambda-vs-kappa-architecture)
6. [Microservices & Event Streaming](#microservices-event-streaming)
7. [Scalability & Performance](#scalability-performance)
8. [Monitoring & Operations](#monitoring-operations)

---

## Apache Kafka Architecture

### Cluster Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Kafka Cluster                        │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Broker 1  │  │   Broker 2  │  │   Broker 3  │    │
│  │             │  │             │  │             │    │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │    │
│  │ │Topic A  │ │  │ │Topic A  │ │  │ │Topic B  │ │    │
│  │ │Part 0   │ │  │ │Part 1   │ │  │ │Part 0   │ │    │
│  │ │(Leader) │ │  │ │(Leader) │ │  │ │(Leader) │ │    │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │    │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │              │    │
│  │ │Topic B  │ │  │ │Topic A  │ │  │              │    │
│  │ │Part 0   │ │  │ │Part 0   │ │  │              │    │
│  │ │(Replica)│ │  │ │(Replica)│ │  │              │    │
│  │ └─────────┘ │  │ └─────────┘ │  │              │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         ZooKeeper/KRaft (Coordination)           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ▲                                      │
         │                                      │
    ┌────┴────┐                           ┌────▼────┐
    │Producer │                           │Consumer │
    └─────────┘                           └─────────┘
```

### Components Deep Dive

**1. Broker**: server que almacena y sirve mensajes

```python
# Broker configuration
broker_config = {
    'broker.id': 1,
    'listeners': 'PLAINTEXT://localhost:9092',
    'log.dirs': '/var/kafka-logs',
    'num.partitions': 3,
    'default.replication.factor': 3,
    'min.insync.replicas': 2,  # Mínimo replicas para ack
    'log.retention.hours': 168,  # 7 días
    'log.segment.bytes': 1073741824  # 1GB
}
```

**2. Topic & Partitions**: Logical organization

```python
from kafka.admin import KafkaAdminClient, NewTopic

admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'])

# Crear topic con 6 partitions, replication factor 3
topic = NewTopic(
    name='user-events',
    num_partitions=6,
    replication_factor=3,
    topic_configs={
        'retention.ms': '604800000',  # 7 días
        'compression.type': 'snappy',
        'cleanup.policy': 'delete'  # o 'compact' para log compaction
    }
)

admin.create_topics([topic])
```

**Partition Strategy**:
```python
# Partitioning por key (garantiza orden por key)
producer.send('user-events', key=b'user_123', value=event)

# Resultado: Todos eventos de user_123 van a misma partition
# → Orden garantizado para este usuario

# Round-robin (sin key, para load balancing)
producer.send('user-events', value=event)
```

**3. Replication**: Alta availability

```
Topic: user-events, Partition 0
┌────────────────────────────────────────┐
│  Broker 1 (Leader)                     │
│  ┌──────────────────────────────────┐  │
│  │ Offset 0: Event A                │  │
│  │ Offset 1: Event B                │  │
│  │ Offset 2: Event C                │  │
│  └──────────────────────────────────┘  │
└────────────│───────────────────────────┘
             │ Replication
         ┌───┴─────┬─────────────┐
         ▼         ▼             ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Broker 2 │ │Broker 3 │ │Broker 4 │
   │(Replica)│ │(Replica)│ │(Replica)│
   └─────────┘ └─────────┘ └─────────┘
```

```python
# ISR: In-Sync Replicas
# Replicas que están sincronizadas con el leader

# Producer acknowledge levels:
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    acks='all',  # Espera todas ISR
    # acks=0  # Fire-and-forget (no ack)
    # acks=1  # Solo leader ack
)
```

**4. Consumer Groups**: Procesamiento paralelo

```python
# Consumer Group permite:
# - Escalabilidad: Agregar consumers para mayor throughput
# - Fault tolerance: Si un consumer falla, rebalance automático

consumer = KafkaConsumer(
    'user-events',
    group_id='analytics-service',
    bootstrap_servers=['localhost:9092'],
    enable_auto_commit=False,  # Manual commit
    auto_offset_reset='earliest'  # Desde el inicio o 'latest'
)

# Procesar y commits explícitos
for message in consumer:
    try:
        process(message.value)
        consumer.commit()  # Commit solo si success
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        # No commit, retry en próximo poll
```

**Consumer Rebalancing**:
```python
# Cuando agregamos/removemos consumers, Kafka rebalancea partitions

# Initial: 3 consumers, 6 partitions
# Consumer A: [P0, P1]
# Consumer B: [P2, P3]
# Consumer C: [P4, P5]

# Agregamos Consumer D
# → Rebalance triggered

# After rebalance: 4 consumers, 6 partitions
# Consumer A: [P0]
# Consumer B: [P2]
# Consumer C: [P4]
# Consumer D: [P1, P3, P5]

# Hook para manejar rebalance
def on_revoke(revoked_partitions):
    logger.info(f"Partitions revoked: {revoked_partitions}")
    # Cleanup antes de perder partitions

def on_assign(assigned_partitions):
    logger.info(f"Partitions assigned: {assigned_partitions}")
    # Setup para nuevas partitions

consumer.subscribe(['user-events'],
                   on_revoke=on_revoke,
                   on_assign=on_assign)
```

### Log Compaction

To keep only the last value per key (useful for entity state):

```python
# Topic config
{
    'cleanup.policy': 'compact',
    'min.cleanable.dirty.ratio': 0.5,
    'delete.retention.ms': 86400000  # 1 día
}

# Ejemplo: User profiles
# Antes de compaction:
[
    (key='user_123', value={'name': 'John', 'email': 'john@old.com'}),  # Offset 0
    (key='user_456', value={'name': 'Jane', 'email': 'jane@email.com'}),  # Offset 1
    (key='user_123', value={'name': 'John', 'email': 'john@new.com'}),  # Offset 2
    (key='user_789', value={'name': 'Bob', 'email': 'bob@email.com'}),   # Offset 3
    (key='user_123', value=None),  # Offset 4 (tombstone → delete)
]

# Después de compaction (solo últimos valores):
[
    (key='user_456', value={'name': 'Jane', 'email': 'jane@email.com'}),
    (key='user_789', value={'name': 'Bob', 'email': 'bob@email.com'})
    # user_123 eliminado (tombstone)
]
```

---

## AWS Kinesis

### Kinesis Family

```
AWS Kinesis
├── Kinesis Data Streams    (similar a Kafka)
├── Kinesis Firehose        (ETL managed, auto-scaling)
├── Kinesis Analytics       (SQL sobre streams)
└── Kinesis Video Streams   (video/audio streaming)
```

### Kinesis Data Streams

**Architecture**:
```
┌──────────────────────────────────────────────────┐
│           Kinesis Data Stream                     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Shard │  │Shard │  │Shard │  │Shard │        │
│  │  1   │  │  2   │  │  3   │  │  4   │        │
│  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘        │
│      │         │         │         │            │
│   1 MB/s    1 MB/s    1 MB/s    1 MB/s         │
│   1000/s    1000/s    1000/s    1000/s         │
└──────┼─────────┼─────────┼─────────┼────────────┘
       │         │         │         │
       └─────────┴─────────┴─────────┘
                  │
            Consumers (KCL)
```

**Shards**: Unidad de throughput (similar a partitions)
- **Write**: 1 MB/s or 1000 records/s per shard
- **Read**: 2 MB/s per shard

```python
import boto3

kinesis = boto3.client('kinesis')

# Crear stream con 4 shards
kinesis.create_stream(
    StreamName='user-events',
    ShardCount=4  # Throughput: 4 MB/s write, 8 MB/s read
)

# Producer
response = kinesis.put_record(
    StreamName='user-events',
    Data=json.dumps(event),
    PartitionKey='user_123'  # Determina shard
)

# Batch put (más eficiente)
records = [
    {
        'Data': json.dumps(event),
        'PartitionKey': event['user_id']
    }
    for event in events
]

kinesis.put_records(
    StreamName='user-events',
    Records=records[:500]  # Max 500 records por batch
)
```

**Consumer (Kinesis Client Library)**:
```python
from amazon_kinesis_client import KinesisClientLibConfiguration, Worker
from amazon_kinesis_client.processor import RecordProcessorBase

class MyRecordProcessor(RecordProcessorBase):
    def process_records(self, records, checkpointer):
        for record in records:
            data = json.loads(record.get_data())
            process_event(data)

        # Checkpoint (similar a Kafka commit)
        checkpointer.checkpoint()

config = KinesisClientLibConfiguration(
    app_name='analytics-app',
    stream_name='user-events',
    kinesis_endpoint='https://kinesis.us-east-1.amazonaws.com',
    dynamodb_endpoint='https://dynamodb.us-east-1.amazonaws.com',
    initial_position='TRIM_HORIZON'  # O 'LATEST'
)

worker = Worker(MyRecordProcessor, config)
worker.run()
```

### Kinesis Firehose

ETL managed que entrega a S3, Redshift, Elasticsearch:

```python
firehose = boto3.client('firehose')

# Crear delivery stream
firehose.create_delivery_stream(
    DeliveryStreamName='user-events-to-s3',
    S3DestinationConfiguration={
        'BucketARN': 'arn:aws:s3:::my-bucket',
        'Prefix': 'events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/',
        'BufferingHints': {
            'SizeInMBs': 5,      # Buffer hasta 5 MB
            'IntervalInSeconds': 60  # O 60 segundos
        },
        'CompressionFormat': 'GZIP',
        'EncryptionConfiguration': {
            'NoEncryptionConfig': 'NoEncryption'
        }
    }
)

# Producer (muy simple)
firehose.put_record(
    DeliveryStreamName='user-events-to-s3',
    Record={'Data': json.dumps(event)}
)

# Firehose automáticamente:
# - Batchea records
# - Comprime con GZIP
# - Particiona por fecha
# - Entrega a S3
# → Sin gestión de shards ni consumers
```

### Kafka vs Kinesis

| Feature | Kafka | Kinesis |
|---------|-------|---------|
| **Deployment** | Self-managed (EMR, EC2) | Fully managed |
| **Retention** | Configurable (ex: 7 days) | Max 365 days |
| **throughput** | Ilimitado (agregar brokers) | 1 MB/s per shard |
| **Scaling** | Manual (agregar partitions) | Manual shard splitting |
| **Cost** | EC2 instances | Pay per shard-hour |
| **Integrations** | Kafka Connect ecosystem | AWS services nativos |
| **Latency** | < 10ms | ~100ms |
| **Ordering** | Per partition | Per shard |
| **Community** | Muy grande | AWS-specific |

**When to use each**:

**Kafka**:
- ✅ On-premise o multi-cloud
- ✅ Necesitas < 10ms latency
- ✅ Muy alto throughput (GB/s)
- ✅ Rich ecosystem (Kafka Connect)
- ✅ Full control

**Kinesis**:
- ✅ AWS-native (integration with Lambda, S3, etc.)
- ✅ No quieres gestionar infraestructura
- ✅ throughput moderado (< 100 MB/s)
- ✅ Quieres simplicity

---

## Apache Flink

### What is Flink?

Framework de procesamiento distribuido para streams y batch con:
- ✅ Exactly-once semantics
- ✅ Stateful processing
- ✅ Event time processing
- ✅ Low latency (ms)

### Architecture

```
┌───────────────────────────────────────────────────┐
│                Flink Cluster                       │
│                                                    │
│  ┌─────────────┐                                  │
│  │ JobManager  │  ← Coordina ejecución            │
│  │ (Master)    │                                  │
│  └──────┬──────┘                                  │
│         │                                          │
│    ┌────┴────┬────────┬────────┐                 │
│    │         │        │        │                  │
│  ┌─▼──────┐ ┌▼──────┐ ┌▼──────┐ ┌▼──────┐       │
│  │TaskMgr │ │TaskMgr│ │TaskMgr│ │TaskMgr│       │
│  │   1    │ │   2   │ │   3   │ │   4   │       │
│  │ (Slot) │ │(Slot) │ │(Slot) │ │(Slot) │       │
│  └────────┘ └───────┘ └───────┘ └───────┘       │
└───────────────────────────────────────────────────┘
```

### DataStream API

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer

# Setup Flink environment
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(4)

# Source: Kafka
kafka_consumer = FlinkKafkaConsumer(
    topics='user-events',
    deserialization_schema=SimpleStringSchema(),
    properties={
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'flink-processor'
    }
)

# Create DataStream
stream = env.add_source(kafka_consumer)

# Transformations
filtered = stream \
    .filter(lambda x: json.loads(x)['amount'] > 100) \
    .map(lambda x: process_event(json.loads(x)))

# Keyed stream (por user_id)
keyed_stream = filtered.key_by(lambda x: x['user_id'])

# Windowing (tumbling de 1 minuto)
windowed = keyed_stream \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .reduce(lambda a, b: {
        'user_id': a['user_id'],
        'total_amount': a.get('total_amount', 0) + b['amount'],
        'count': a.get('count', 0) + 1
    })

# Sink: Kafka
kafka_producer = FlinkKafkaProducer(
    topic='user-aggregates',
    serialization_schema=SimpleStringSchema(),
    producer_config={
        'bootstrap.servers': 'localhost:9092'
    }
)

windowed.map(lambda x: json.dumps(x)).add_sink(kafka_producer)

# Execute
env.execute('User Event Aggregation')
```

### Stateful Processing

```python
from pyflink.datastream.state import ValueStateDescriptor

class CountMapper(MapFunction):
    def __init__(self):
        self.state = None

    def open(self, runtime_context):
        # Definir state (persisted)
        descriptor = ValueStateDescriptor('count', Types.INT())
        self.state = runtime_context.get_state(descriptor)

    def map(self, value):
        # Leer state actual
        current_count = self.state.value()
        if current_count is None:
            current_count = 0

        # Actualizar state
        new_count = current_count + 1
        self.state.update(new_count)

        return (value, new_count)

# Usar stateful mapper
stateful_stream = keyed_stream.map(CountMapper())

# State automáticamente:
# - Checkpointed (fault tolerance)
# - Distribuido por key
# - Puede ser RocksDB (grandes estados)
```

### Event Time vs Processing Time

```python
# Event Time: Timestamp en el evento (cuando sucedió)
# Processing Time: Timestamp cuando Flink lo procesa

# Configurar event time
env.set_stream_time_characteristic(TimeCharacteristic.EventTime)

# Watermarks: "Hasta qué punto event time ha progresado"
def extract_timestamp(event, current_watermark):
    return event['timestamp']  # Unix millis

stream = stream.assign_timestamps_and_watermarks(
    WatermarkStrategy
        .for_bounded_out_of_orderness(Duration.of_seconds(10))
        .with_timestamp_assigner(extract_timestamp)
)

# Eventos pueden llegar desordenados:
# Event 1: timestamp=10:00:00 → Llega a las 10:00:05
# Event 2: timestamp=10:00:02 → Llega a las 10:00:10 (más tarde!)

# Watermark permite esperar eventos atrasados hasta 10 segundos
```

### Checkpointing & Fault Tolerance

```python
# Habilitar checkpointing (exactly-once)
env.enable_checkpointing(60000)  # Cada 60 segundos

# Configurar checkpointing
config = env.get_checkpoint_config()
config.set_checkpoint_storage_dir('s3://my-bucket/checkpoints')
config.set_min_pause_between_checkpoints(30000)  # 30s entre checkpoints
config.set_checkpoint_timeout(600000)  # 10 min timeout
config.set_max_concurrent_checkpoints(1)

# Si hay failure:
# 1. Flink detecta failure (TaskManager murió)
# 2. Restaura desde último checkpoint
# 3. Replay desde Kafka offset
# → Exactly-once garantizado
```

---

## Stream Processing Patterns

### 1. Filtering (Stateless)

```python
# Filter out eventos no relevantes
def filter_pattern(stream):
    return stream.filter(lambda event:
        event['type'] == 'purchase' and
        event['amount'] > 100 and
        event['country'] == 'US'
    )
```

### 2. Enrichment (Stateless con side input)

```python
# Enrichr eventos con data externa (ej: user profiles)

# Broadcast state para enriquecimiento
user_profiles = env.from_collection([
    ('user_123', {'tier': 'premium', 'country': 'US'}),
    ('user_456', {'tier': 'basic', 'country': 'UK'})
])

# Broadcast a todos los tasks
broadcast_state = user_profiles.broadcast()

# Enrich stream
def enrich_with_profile(event, broadcast_state):
    user_id = event['user_id']
    profile = broadcast_state.get(user_id)

    return {
        **event,
        'user_tier': profile['tier'],
        'user_country': profile['country']
    }

enriched = stream.connect(broadcast_state).process(enrich_with_profile)
```

### 3. Aggregation (Stateful)

```python
# Agregar eventos por ventanas temporales

windowed_aggregates = stream \
    .key_by(lambda x: x['user_id']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(5))) \
    .aggregate(
        AggregateFunction(
            create_accumulator=lambda: {'count': 0, 'sum': 0},
            add=lambda acc, value: {
                'count': acc['count'] + 1,
                'sum': acc['sum'] + value['amount']
            },
            get_result=lambda acc: {
                'count': acc['count'],
                'total': acc['sum'],
                'average': acc['sum'] / acc['count'] if acc['count'] > 0 else 0
            },
            merge=lambda acc1, acc2: {
                'count': acc1['count'] + acc2['count'],
                'sum': acc1['sum'] + acc2['sum']
            }
        )
    )
```

### 4. Joining Streams

```python
# Join dos streams (ej: clicks + purchases)

clicks = env.add_source(clicks_source) \
    .key_by(lambda x: x['session_id'])

purchases = env.add_source(purchases_source) \
    .key_by(lambda x: x['session_id'])

# Window join (eventos cercanos en tiempo)
joined = clicks \
    .join(purchases) \
    .where(lambda x: x['session_id']) \
    .equal_to(lambda x: x['session_id']) \
    .window(TumblingEventTimeWindows.of(Time.minutes(10))) \
    .apply(lambda click, purchase: {
        'session_id': click['session_id'],
        'clicked_product': click['product_id'],
        'purchased_product': purchase['product_id'],
        'conversion': click['product_id'] == purchase['product_id']
    })
```

### 5. Sessionization

```python
# Agrupar eventos en sesiones (gap-based)

sessionized = stream \
    .key_by(lambda x: x['user_id']) \
    .window(ProcessingTimeSessionWindows.with_gap(Time.minutes(10))) \
    .reduce(lambda session, event: {
        'user_id': session['user_id'],
        'events': session.get('events', []) + [event],
        'start_time': min(session.get('start_time', event['ts']), event['ts']),
        'end_time': max(session.get('end_time', event['ts']), event['ts'])
    })
```

### 6. Anomaly Detection

```python
# Detectar comportamiento anómalo

class AnomalyDetector(KeyedProcessFunction):
    def __init__(self, threshold_multiplier=3.0):
        self.threshold_multiplier = threshold_multiplier
        self.stats_state = None

    def open(self, runtime_context):
        descriptor = ValueStateDescriptor('stats', Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()]))
        self.stats_state = runtime_context.get_state(descriptor)

    def process_element(self, value, ctx):
        # Mantener running mean y stddev
        stats = self.stats_state.value()
        if stats is None:
            mean, stddev = value['amount'], 0
        else:
            mean, stddev = stats

        # Detectar anomalía (> 3 σ)
        if abs(value['amount'] - mean) > self.threshold_multiplier * stddev:
            yield ('anomaly', value)

        # Actualizar estadísticas (!IMPORTANTE: Use algoritmo incremental real en producción!)
        new_mean = 0.9 * mean + 0.1 * value['amount']  # Exponential moving average
        self.stats_state.update((new_mean, stddev))

anomalies = stream \
    .key_by(lambda x: x['user_id']) \
    .process(AnomalyDetector(threshold_multiplier=3.0))
```

---

## Lambda vs Kappa Architecture

### Lambda Architecture

Combina batch y streaming para balance entre latency y accuracy:

```
                  ┌─────────────┐
                  │ Data Source │
                  └──────┬──────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
      ┌────▼────┐                 ┌────▼────┐
      │  Batch  │                 │  Speed  │
      │  Layer  │                 │  Layer  │
      │         │                 │         │
      │ (Spark) │                 │ (Flink) │
      └────┬────┘                 └────┬────┘
           │                           │
           │   ┌─────────────┐         │
           └──▶│   Serving   │◀────────┘
               │    Layer    │
               │             │
               │(merge views)│
               └─────────────┘
                      │
                   Queries
```

**features**:
- **Batch Layer**: Procesa TODO el history (slow, accurate)
- **Speed ​​Layer**: Processes latest events (fast, approximate)
- **Serving Layer**: Merge de ambas vistas

```python
# Batch layer (cada hora)
def batch_processing():
    # Leer últimos 7 días completos
    df = spark.read.parquet('s3://data/history/')

    # Cálculo exacto
    aggregates = df.groupBy('user_id').agg(
        count('*').alias('total_events'),
        sum('amount').alias('total_amount'),
        avg('amount').alias('avg_amount')
    )

    # Sobrescribir vista batch
    aggregates.write.mode('overwrite').parquet('s3://data/batch-view/')

# Speed layer (real-time)
def speed_processing(event):
    # Actualizar agregado incremental (aproximado)
    key = event['user_id']
    increment_counter(key, 'total_events', 1)
    increment_counter(key, 'total_amount', event['amount'])

    # Guardar en speed view (Redis, DynamoDB)
    save_to_speed_view(key, incremental_stats)

# Serving layer (query time)
def get_user_stats(user_id):
    # Leer batch view (vista histórica completa)
    batch_stats = read_from_batch_view(user_id)

    # Leer speed view (delta desde último batch)
    speed_stats = read_from_speed_view(user_id)

    # Merge
    return {
        'total_events': batch_stats['total_events'] + speed_stats['total_events'],
        'total_amount': batch_stats['total_amount'] + speed_stats['total_amount']
    }
```

**Ventajas**:
- ✅ Best of both worlds (accuracy + latency)
- ✅ Batch puede corregir errores en speed layer

**Desventajas**:
- ❌ Complejidad (dos codebases)
- ❌ Duplicate logic
- ❌ Merge layer complex

### Kappa Architecture

Solo streaming (simplificado):

```
           ┌─────────────┐
           │ Data Source │
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   Kafka     │ ← Inmutable log
           │  (Storage)  │
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │  Streaming  │
           │  Processing │
           │   (Flink)   │
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   Serving   │
           │    Layer    │
           └─────────────┘
```

**features**:
- Todo es streaming
- Re-procesar history = replay desde Kafka
- Una sola codebase

```python
# Una sola stream processing job
def kappa_processing(stream):
    return stream \
        .key_by(lambda x: x['user_id']) \
        .window(TumblingEventTimeWindows.of(Time.days(7))) \
        .aggregate(AggregateFunction(...))

# Para re-procesar (ej: bug fix):
# 1. Deploy nueva versión con consumer group diferente
# 2. Start desde earliest offset (replay todo)
# 3. Una vez alcanza "live", switch al nuevo group
# 4. Eliminar viejo group
```

**Ventajas**:
- ✅ Simplicidad (una codebase)
- ✅ Menos infraestructura
- ✅ Easier to maintain

**Desventaj as**:
- ❌ Re-processing puede tomar tiempo
- ❌ Todo debe ser stream-friendly

### When to Use Each

**Lambda**:
- You need maximum accuracy (e.g. billing)
- Batch puede hacer joins/agregaciones pesadas
- Tienes equipo grande para mantener dos sistemas

**Kappa**:
- Prioridad es simplicidad
- Data can be re-processed reasonably quickly
- Streaming framework suficientemente powerful (Flink)

**Tendencia actual**: Kappa gana (Flink/Spark Structured Streaming suficientemente capaces)

---

## Microservices & Event Streaming

### Event-Driven Microservices

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   Orders     │        │  Inventory   │        │  Shipping    │
│   Service    │        │   Service    │        │   Service    │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │ publish               │ subscribe             │ subscribe
       │                       │                       │
       │         ┌─────────────▼───────────────┐       │
       └────────▶│       Kafka Topics          │◀──────┘
                 │                             │
                 │ • order-created             │
                 │ • order-shipped             │
                 │ • inventory-updated         │
                 └─────────────────────────────┘
```

**Benefits**:
- 🔄 **Decoupling**: Services no se llaman directamente
- 📈 **Scalability**: Cada consumer escala independientemente
- 🎯 **Event Sourcing**: History completo de cambios
- ⚡ **Async**: No bloqueante

### Example: Order Processing

```python
# Order Service (Producer)
class OrderService:
    def create_order(self, order_data):
        # Guardar orden en DB
        order = self.db.save_order(order_data)

        # Publicar evento
        event = {
            'event_type': 'OrderCreated',
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'order_id': order.id,
            'user_id': order.user_id,
            'items': order.items,
            'total_amount': order.total
        }

        self.kafka_producer.send('order-events', event)

        return order

# Inventory Service (Consumer)
class InventoryService:
    def consume_order_events(self):
        consumer = KafkaConsumer('order-events', group_id='inventory-service')

        for message in consumer:
            event = message.value

            if event['event_type'] == 'OrderCreated':
                # Reducir inventory
                for item in event['items']:
                    self.reduce_stock(item['product_id'], item['quantity'])

                # Publicar evento de inventory
                self.kafka_producer.send('inventory-events', {
                    'event_type': 'InventoryReduced',
                    'order_id': event['order_id'],
                    'items': event['items']
                })

# Shipping Service (Consumer)
class ShippingService:
    def consume_order_events(self):
        consumer = KafkaConsumer('order-events', group_id='shipping-service')

        for message in consumer:
            event = message.value

            if event['event_type'] == 'OrderCreated':
                # Crear envío
                shipment = self.create_shipment(event['order_id'])

                # Publicar evento
                self.kafka_producer.send('shipping-events', {
                    'event_type': 'ShipmentCreated',
                    'order_id': event['order_id'],
                    'shipment_id': shipment.id
                })
```

### Saga Pattern (Distributed Transactions)

Cuando necesitas transactions distribuidas con streaming:

```python
# Choreography Saga (event-driven)
# Cada servicio escucha eventos y reacciona

# Order Service
def create_order_saga(order):
    try:
        # Step 1: Reserve inventory
        kafka.send('saga-commands', {
            'command': 'ReserveInventory',
            'saga_id': order.saga_id,
            'order_id': order.id,
            'items': order.items
        })
    except Exception as e:
        # Compensating action
        kafka.send('saga-commands', {
            'command': 'CancelOrder',
            'saga_id': order.saga_id,
            'order_id': order.id
        })

# Inventory Service
def handle_saga_command(command):
    if command['command'] == 'ReserveInventory':
        try:
            reserve_stock(command['items'])
            # Success: Next step
            kafka.send('saga-events', {
                'event': 'InventoryReserved',
                'saga_id': command['saga_id']
            })
        except OutOfStockError:
            # Failure: Compensation
            kafka.send('saga-events', {
                'event': 'InventoryReservationFailed',
                'saga_id': command['saga_id']
            })

# Payment Service listens to InventoryReserved
# If payment fails → Trigger compensation (release inventory)
```

---

## Scalability & Performance

### Kafka Performance Tuning

**1. Producer Performance**:
```python
producer = KafkaProducer(
    # Batching (más latencia, mejor throughput)
    linger_ms=10,  # Esperar 10ms para batchear
    batch_size=16384,  # 16KB batch size

    # Compression (reduce network)
    compression_type='snappy',  # O 'gzip', 'lz4'

    # Acks
    acks='all',  # Esperar todas replicas (durable, más lento)
    # acks=1  # Solo leader (más rápido)

    # Retries
    retries=3,
    max_in_flight_requests_per_connection=5,

    # Buffer
    buffer_memory=33554432  # 32MB buffer
)
```

**2. Partitioning Strategy**:
```python
# Buena distribución = mejor paralelism
def custom_partitioner(key, all_partitions, available_partitions):
    # Hash distribution
    if key:
        return hash(key) % len(all_partitions)
    else:
        # Round-robin si no hay key
        return random.choice(available_partitions)

producer = KafkaProducer(partitioner=custom_partitioner)
```

**3. Consumer Performance**:
```python
consumer = KafkaConsumer(
    # Fetch más data en cada poll
    fetch_min_bytes=1024,  # Min 1KB
    fetch_max_wait_ms=500,  # Esperar max 500ms

    # Más records por poll
    max_poll_records=500,

    # Auto-commit
    enable_auto_commit=True,
    auto_commit_interval_ms=5000  # Cada 5s
)

# Batch processing
def consume_in_batches():
    batch = []
    for message in consumer:
        batch.append(message.value)

        if len(batch) >= 100:
            # Process batch (más eficiente que uno por uno)
            process_batch(batch)
            batch.clear()
```

### Flink Performance

**1. Parallelism**:
```python
env = StreamExecutionEnvironment.get_execution_environment()

# Global parallelism
env.set_parallelism(8)

# Per-operator parallelism
stream.map(func).set_parallelism(4)  # Override global
```

**2. State Backend**:
```python
from pyflink.datastream import FsStateBackend, RocksDBStateBackend

# MemoryStateBackend: Fast, limitado por heap
env.set_state_backend(MemoryStateBackend())

# FsStateBackend: Heap + disk backup
env.set_state_backend(FsStateBackend("s3://my-bucket/checkpoints"))

# RocksDBStateBackend: Para estados grandes (GB+)
env.set_state_backend(RocksDBStateBackend("s3://my-bucket/checkpoints"))
```

**3. Network Buffers**:
```python
# taskmanager.network.memory.fraction
# taskmanager.network.memory.min/max

# Más buffers = más throughput (pero más latency)
```

---

## Monitoring & Operations

### Metrics to Track

**Kafka**:
```python
# Producer metrics
- messages-sent-rate: Mensajes/segundo
- compression-rate: Ratio de compresión
- request-latency-avg: Latencia promedio
- buffer-available-bytes: Buffer disponible

# Consumer metrics
- records-consumed-rate: Records/segundo
- records-lag: Diferencia entre produced y consumed
- fetch-latency-avg: Latencia de fetch

# Broker metrics
- under-replicated-partitions: Partitions sin todas sus replicas
- leader-election-rate: Frecuencia de elections (↑ = problema)
- request-queue-size: Queue de requests pendientes
```

**Monitoring con Prometheus**:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
messages_processed = Counter('messages_processed_total', 'Total messages processed')
processing_time = Histogram('processing_duration_seconds', 'Processing duration')
current_lag = Gauge('consumer_lag_messages', 'Current lag', ['topic', 'partition'])

# Instrumentar código
def process_message(msg):
    with processing_time.time():
        # Process
        result = do_work(msg)
        messages_processed.inc()
        return result

# Exponer métricas
start_http_server(8000)
```

### Alerting

```yaml
# Prometheus alerts
groups:
  - name: streaming
    rules:
      # Consumer lag alto
      - alert: HighConsumerLag
        expr: kafka_consumer_group_lag > 10000
        for: 5m
        annotations:
          summary: "Consumer {{ $labels.group }} lagging behind"

      # Under-replicated partitions
      - alert: UnderReplicatedPartitions
        expr: kafka_server_replicamanager_underreplicatedpartitions > 0
        for: 1m
        annotations:
          summary: "Broker {{ $labels.broker }} has under-replicated partitions"

      # Processing errors
      - alert: HighErrorRate
        expr: rate(processing_errors_total[5m]) > 0.01
        for: 2m
        annotations:
          summary: "Error rate exceeds 1%"
```

---

## Resumen

### Key Takeaways

✅ **Kafka** is the standard for event streaming
✅ **Kinesis** simplifica en AWS pero con trade-offs
✅ **Flink** offers advanced stream processing with exactly-once
✅ **Kappa architecture** tiende a ganar sobre Lambda por simplicidad
✅ **Event-driven microservices** con Kafka para desacoplamiento
✅ **Performance tuning** critical for high-throughput
✅ **Monitoring** esencial para operaciones productivas

### Next Steps

1. 📖 Leer `03-resources.md` para tools y learning resources
2. 🏋️ Completar Exercise 01: Setup Kafka cluster
3. 🔬 Experimentar con Flink DataStream API
4. 📊 Implementar monitoring con Prometheus
5. 🚀 Construir tu primer pipeline end-to-end

---

**Previous**: [01-concepts.md](./01-concepts.md) - Streaming Fundamentals
**Next**: [03-resources.md](./03-resources.md) - Tools & Learning Resources
