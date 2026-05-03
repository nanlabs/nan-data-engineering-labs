# Module 08: Streaming Basics - Getting Started

Welcome to **Streaming Basics**! This module teaches real-time data processing with Apache Kafka, Flink, and AWS Kinesis.

---

## 🚀 Quick Start (5 Minutes)

### 1. Setup Environment

```bash
# Navigate to module
cd modules/module-08-streaming-basics

# Run setup script
./scripts/setup.sh
```

This will:
- ✅ Start Kafka, Zookeeper, Schema Registry (Docker)
- ✅ Create topics
- ✅ Generate sample data
- ✅ Verify all services

### 2. Verify Installation

```bash
# Run validation
./scripts/validate.sh
```

### 3. Explore Kafka UI

Open in browser: **http://localhost:8080**

- View topics
- Browse messages
- Monitor consumer groups

---

## 📚 Learning Path

### Week 1: Kafka Fundamentals

**Theory** (2-3 hours):
1. Read [01-concepts.md](theory/01-concepts.md) - Stream processing basics
2. Review [02-architecture.md](theory/02-architecture.md) - Kafka architecture

**Practice** (4-5 hours):
1. [Exercise 01: Kafka Basics](exercises/01-kafka-basics/)
   - Producers & consumers
   - Topics & partitions
   - Consumer groups

2. [Exercise 02: Stream Processing](exercises/02-stream-processing/)
   - Filtering & mapping
   - Windowing
   - Stateful aggregation

### Week 2: Schema Management

**Theory** (1-2 hours):
- [Schema Registry](theory/02-architecture.md#schema-registry)
- Avro serialization

**Practice** (3-4 hours):
- [Exercise 03: Avro Schemas](exercises/03-avro-schemas/)
  - Schema registration
  - Avro producer/consumer
  - Schema evolution

### Week 3: Cloud Streaming

**Theory** (1-2 hours):
- AWS Kinesis vs Kafka comparison
- Managed streaming services

**Practice** (3-4 hours):
- [Exercise 04: Kinesis Streams](exercises/04-kinesis-streams/)
  - Kinesis Data Streams
  - KCL consumers
  - CloudWatch monitoring

### Week 4: Advanced Processing

**Theory** (2-3 hours):
- Apache Flink architecture
- Event time vs processing time
- Exactly-once semantics

**Practice** (6-8 hours):
- [Exercise 05: Flink Processing](exercises/05-flink-processing/)
  - DataStream API
  - Windows & watermarks
  - Stateful processing
  - Checkpointing

- [Exercise 06: Production Streams](exercises/06-production-streams/)
  - Monitoring & metrics
  - Error handling (DLQ)
  - Auto-scaling
  - Testing strategies

---

## 🎯 Learning Objectives

By the end of this module, you will:

### Core Concepts
- ✅ Understand stream vs batch processing
- ✅ Explain event-driven architecture
- ✅ Master Kafka fundamentals (topics, partitions, consumer groups)
- ✅ Implement stream transformations

### Technical Skills
- ✅ Produce/consume Kafka events with Python
- ✅ Use Avro for schema management
- ✅ Build stateful stream processors
- ✅ Implement windowing (tumbling, sliding, session)
- ✅ Deploy Flink jobs for stream processing
- ✅ Monitor streaming applications

### Production Readiness
- ✅ Implement error handling (DLQ)
- ✅  Set up monitoring & alerting
- ✅ Handle late events with watermarks
- ✅ Achieve exactly-once semantics
- ✅ Scale streaming applications

---

## 🛠️ Tools & Technologies

### Core Stack
- **Apache Kafka** (2.13): Distributed streaming platform
- **Apache Flink** (1.18): Stream processing framework
- **Schema Registry** (7.5): Centralized schema management
- **Avro**: Binary serialization format

### Python Libraries
- `kafka-python`: Kafka client
- `confluent-kafka`: High-performance Kafka client with Avro
- `pyflink`: Flink Python API
- `boto3`: AWS SDK (for Kinesis)

### Infrastructure
- **Docker**: Local development environment
- **Kafka UI**: Web interface for Kafka
- **Prometheus + Grafana**: Monitoring (optional)

---

## 📁 Module Structure

```
module-08-streaming-basics/
├── theory/                    # Conceptual documentation
│   ├── 01-concepts.md        # 8K words: fundamentals
│   ├── 02-architecture.md    # 7K words: Kafka, Kinesis, Flink
│   └── 03-resources.md       # 3.5K words: tools & learning
│
├── exercises/                 # Hands-on practice
│   ├── 01-kafka-basics/      # Producers, consumers, topics
│   ├── 02-stream-processing/ # Transformations, windows
│   ├── 03-avro-schemas/      # Schema management
│   ├── 04-kinesis-streams/   # AWS Kinesis
│   ├── 05-flink-processing/  # Apache Flink
│   └── 06-production-streams/# Production patterns
│
├── infrastructure/            # Docker Compose
│   └── docker-compose.yml    # Kafka stack
│
├── data/
│   ├── schemas/              # Avro schemas
│   │   ├── user_event.avsc
│   │   ├── sensor_reading.avsc
│   │   └── transaction.avsc
│   └── scripts/
│       └── stream_generator.py  # Event generator
│
├── validation/               # Tests
│   ├── conftest.py          # Pytest fixtures
│   └── test_module.py       # Validation tests
│
└── scripts/
    ├── setup.sh             # Environment setup
    └── validate.sh          # Validation script
```

---

## 🔧 Common Commands

### Docker Management

```bash
# Start services
cd infrastructure
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs kafka
docker-compose logs -f    # Follow logs

# Restart service
docker-compose restart kafka
```

### Kafka CLI

```bash
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic user-events

# Create topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic my-topic --partitions 3 --replication-factor 1

# Delete topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --delete --topic my-topic

# List consumer groups
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe consumer group
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --describe --group my-group
```

### Event Generation

```bash
# Stream mode (continuous)
python data/scripts/stream_generator.py \
  --type user \
  --mode stream \
  --rate 10 \
  --duration 60

# Batch mode (fixed count)
python data/scripts/stream_generator.py \
  --type transaction \
  --mode batch \
  --count 1000 \
  --output data/samples/transactions.json
```

### Testing

```bash
# All tests
pytest validation/ -v

# Specific markers
pytest validation/ -v -m kafka           # Kafka tests only
pytest validation/ -v -m "not slow"      # Skip slow tests
pytest validation/ -v -m integration     # Integration tests

# Specific test
pytest validation/test_module.py::TestKafkaBasics::test_producer_sends_events -v
```

---

## 🆘 Troubleshooting

### Issue: Kafka not starting

**Symptoms**: `docker-compose up` fails, Kafka container exits

**Solutions**:
```bash
# Check logs
docker-compose logs kafka

# Remove old data
docker-compose down -v
docker-compose up -d

# Check ports
netstat -an | grep 9092  # Should not be in use
```

### Issue: Cannot connect to Kafka

**Symptoms**: Connection refused errors

**Solutions**:
```bash
# Verify Kafka is running
docker ps | grep kafka

# Test connection
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check broker logs
docker exec kafka cat /var/log/kafka/server.log
```

### Issue: Consumer not receiving messages

**Symptoms**: Producer sends, consumer receives nothing

**Solutions**:
```bash
# Check topic exists
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Verify messages in topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --from-beginning \
  --max-messages 10

# Check consumer group lag
docker exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group my-group
```

### Issue: Schema Registry connection failed

**Symptoms**: Cannot register schemas

**Solutions**:
```bash
# Check Schema Registry
curl http://localhost:8081/subjects

# Restart Schema Registry
docker-compose restart schema-registry

# Check logs
docker-compose logs schema-registry
```

---

## 📖 Additional Resources

### Official Documentation
- [Apache Kafka Docs](https://kafka.apache.org/documentation/)
- [Apache Flink Docs](https://flink.apache.org/docs/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/)

### Internal Resources
- [Kafka Quick Reference](assets/kafka-quick-reference.md)
- [Streaming Patterns Guide](assets/streaming-patterns.md)
- [Theory: Concepts](theory/01-concepts.md)
- [Theory: Architecture](theory/02-architecture.md)

### Community
- [Confluent Community](https://forum.confluent.io/)
- [Apache Kafka Users](https://kafka.apache.org/contact)
- Stack Overflow: [apache-kafka](https://stackoverflow.com/questions/tagged/apache-kafka)

---

## ✅ Success Criteria

You've completed this module when you can:

1. **Kafka Basics** ✓
   - Produce and consume messages
   - Explain partitions and consumer groups
   - Manage topics via CLI

2. **Stream Processing** ✓
   - Implement filtering and mapping
   - Use tumbling/sliding windows
   - Maintain stateful aggregations

3. **Schema Management** ✓
   - Register Avro schemas
   - Produce/consume with Avro
   - Evolve schemas with compatibility

4. **Advanced** ✓
   - Deploy Flink stream processing jobs
   - Handle late events with watermarks
   - Implement exactly-once semantics

5. **Production** ✓
   - Set up monitoring & metrics
   - Implement dead letter queues
   - Auto-scale based on lag

---

## 🎓 Next Modules

- **Module 09**: Data Quality & Validation
- **Module 10**: Workflow Orchestration (Airflow)
- **Module 15**: Real-Time Analytics

---

**Ready to start?** Run `./scripts/setup.sh` and begin with [Exercise 01](exercises/01-kafka-basics/)!
