# Streaming - Tools & Learning Resources

## index

1. [Tools Ecosystem](#tools-ecosystem)
2. [Cloud Services](#cloud-services)
3. [Libraries & Frameworks](#libraries-frameworks)
4. [Development Tools](#development-tools)
5. [Learning Resources](#learning-resources)
6. [Books](#books)
7. [Courses & Certifications](#courses-certifications)
8. [Community & Events](#community-events)

---

## Tools Ecosystem

### Message Brokers

**1. Apache Kafka** ⭐⭐⭐⭐⭐

- **Best for**: High-throughput, distributed streaming
- **Pros**: Mature, scalable, rich ecosystem
- **Cons**: Complexity, operational overhead
- **Used by**: LinkedIn, Uber, Netflix, Airbnb

```bash
# Start Kafka locally
docker run -d \
  --name kafka \
  -p 9092:9092 \
  confluentinc/cp-kafka:latest
```text

**2. AWS Kinesis** ⭐⭐⭐⭐

- **Best for**: AWS-native streaming
- **Pros**: Fully managed, simple
- **Cons**: AWS lock-in, throughput limitations
- **Used by**: Amazon, Lyft, Sonos

**3. Apache Pulsar** ⭐⭐⭐⭐

- **Best for**: Multi-tenancy, geo-replication
- **Pros**: Unified messaging + streaming, storage separation
- **Cons**: Less mature than Kafka
- **Used by**: Yahoo, Splunk, Verizon

**4. RabbitMQ** ⭐⭐⭐

- **Best for**: Traditional messaging (not streaming)
- **Pros**: Simple, mature
- **Cons**: Lower throughput para streaming
- **Used by**: Reddit, Instagram

**5. Google Cloud Pub/Sub** ⭐⭐⭐⭐

- **Best for**: GCP-native streaming
- **Pros**: Serverless, auto-scaling
- **Cons**: GCP lock-in
- **Used by**: Spotify, Twitter (on GCP)

### Stream Processing Frameworks

**1. Apache Flink** ⭐⭐⭐⭐⭐

- **Best for**: Complex event processing, exactly-once
- **Pros**: True streaming, low latency, stateful
- **Cons**: Steeper learning curve
- **Language**: Java, Scala, Python (PyFlink)

```python
# Flink example
from pyflink.datastream import StreamExecutionEnvironment

env = StreamExecutionEnvironment.get_execution_environment()
stream = env.add_source(kafka_source)
result = stream.map(lambda x: x.upper())
result.add_sink(kafka_sink)
env.execute()
```text

**2. Apache Spark Structured Streaming** ⭐⭐⭐⭐

- **Best for**: Unified batch + streaming
- **Pros**: Familiar API (para Spark users), integrations
- **Cons**: Micro-batch (no true streaming)
- **Language**: Python, Scala, Java, R

```python
# Spark Structured Streaming
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("streaming").getOrCreate()

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "topic") \
    .load()

query = df.writeStream \
    .format("console") \
    .start()
```text

**3. Kafka Streams** ⭐⭐⭐⭐

- **Best for**: Kafka-to-Kafka processing
- **Pros**: Library (no cluster), simple
- **Cons**: Java only, tied to Kafka
- **Language**: Java

**4. Apache Storm** ⭐⭐⭐

- **Best for**: Legacy systems
- **Pros**: Low latency
- **Cons**: Older, less features que Flink
- **Status**: Maintenance mode

**5. Apache Samza** ⭐⭐⭐

- **Best for**: LinkedIn workloads
- **Pros**: Tight Kafka integration
- **Cons**: Less popular
- **Used by**: LinkedIn, Optimizely

### Comparison: Flink vs Spark Streaming vs Kafka Streams

| Feature | Flink | Spark Streaming | Kafka Streams |
|---------|-------|-----------------|---------------|
| **Model** | True streaming | Micro-batch | Stream |
| **Latency** | ~10ms | ~100ms | ~10ms |
| **State** | Advanced (RocksDB) | Structured | Local store |
| **Exactly-once** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Event time** | ✅ Native | ✅ Supported | ✅ Supported |
| **Windowing** | ✅ Rich | ✅ Good | ✅ Basic |
| **Deployment** | Cluster | Cluster | Library |
| **Language** | Java, Scala, Python | Scala, Python, Java | Java |
| **Learning curve** | Steep | Medium | Easy |
| **Use case** | Complex CEP | Batch + Stream | Simple Kafka processing |

---

## Cloud Services

### AWS

**1. Amazon Kinesis Data Streams**

```python
import boto3

kinesis = boto3.client('kinesis')

# Producer
response = kinesis.put_record(
    StreamName='my-stream',
    Data=json.dumps(data),
    PartitionKey='key-1'
)

# Consumer (KCL)
from amazon_kinesis_client import KinesisClientLibConfiguration

config = KinesisClientLibConfiguration(...)
worker = Worker(RecordProcessor, config)
worker.run()
```

**2. Amazon Kinesis Data Firehose**

- Managed ETL to S3/Redshift/Elasticsearch
- No code required
- Auto-scaling

**3. Amazon Kinesis Data Analytics**

- SQL queries on streams
- Real-time dashboards

**4. Amazon MSK (Managed Streaming for Kafka)**

- Fully managed Kafka
- Compatible with Apache Kafka
- Integrates with AWS services

**Pricing**:

- Kinesis: ~$0.015 per shard-hour + $0.014 per 1M PUT records
- MSK: ~$0.21 per broker-hour + storage

### GCP

**1. Google Cloud Pub/Sub**

```python
from google.cloud import pubsub_v1

# Publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

future = publisher.publish(
    topic_path,
    data=json.dumps(message).encode('utf-8')
)
```text

**2. Google Cloud Dataflow**

- Apache Beam runner
- Unified batch + streaming
- Auto-scaling

**Pricing**:

- Pub/Sub: $0.06 per GB ingested
- Dataflow: ~$0.069 per vCPU-hour

### Azure

**1. Azure Event Hubs**

- Kafka-compatible
- Integration with Azure ecosystem

**2. Azure Stream Analytics**

- SQL-based stream processing
- Integration with Power BI

**Pricing**:

- Event Hubs: ~$0.028 per million events
- Stream Analytics: ~$0.11 per streaming unit-hour

### Comparison

| Feature | AWS Kinesis | GCP Pub/Sub | Azure Event Hubs |
|---------|-------------|-------------|------------------|
| **throughput** | 1 MB/s per shard | Auto-scaling | Auto-scaling |
| **Retention** | Up to 365 days | 7 days | 7 days (90 premium) |
| **Ordering** | Per shard | Per ordering key | Per partition |
| **Pricing model** | Per shard-hour | Per GB | Per throughput unit |
| **Kafka compatible** | MSK only | No | ✅ Yes |
| **Best for** | AWS ecosystem | GCP ecosystem | Azure ecosystem |

---

## Libraries & Frameworks

### Python Libraries

**1. kafka-python**

```bash
pip install kafka-python
```text

- Pure Python Kafka client
- Simple, lightweight
- Good for producers/consumers

**2. confluent-kafka-python**

```bash
pip install confluent-kafka
```text

- C bindings (librdkafka)
- Higher performance
- More features (Avro, Schema Registry)

**3. faust**

```bash
pip install faust-streaming
```

- Stream processing library
- Python-native (like Kafka Streams but Python)
- Async/await support

```python
import faust

app = faust.App('myapp', broker='kafka://localhost:9092')

class Order(faust.Record):
    order_id: str
    amount: float

orders_topic = app.topic('orders', value_type=Order)

@app.agent(orders_topic)
async def process_order(orders):
    async for order in orders:
        if order.amount > 100:
            print(f'High value order: {order}')
```text

**4. aiokafka**

```bash
pip install aiokafka
```text

- Asyncio Kafka client
- Non-blocking I/O
- High concurrency

### Schema Management

**1. Apache Avro**

```bash
pip install avro-python3
```text

- Binary serialization
- Schema evolution
- Compact

**2. Protocol Buffers**

```bash
pip install protobuf
```

- Google's serialization
- Strongly typed
- Fast

**3. JSON Schema**

```bash
pip install jsonschema
```text

- Human-readable
- Easy to debug
- Larger size

### Testing

**1. pytest-kafka**

```bash
pip install pytest-kafka
```text

- Embedded Kafka for testing
- Fixtures for producers/consumers

**2. testcontainers**

```bash
pip install testcontainers
```text

- Docker containers en tests
- Kafka, Zookeeper, Schema Registry

```python
from testcontainers.kafka import KafkaContainer

def test_kafka_integration():
    with KafkaContainer() as kafka:
        bootstrap_servers = kafka.get_bootstrap_server()
        # Test con Kafka real
        producer = KafkaProducer(bootstrap_servers=[bootstrap_servers])
        producer.send('test-topic', b'message')
```

---

## Development Tools

### Kafka Tools

**1. Kafka UI (Confluent Control Center/Kafdrop)**

- Web UI para Kafka
- Browse topics, messages
- Monitoring

```bash
# Kafdrop (open source UI)
docker run -d \
  --name kafdrop \
  -p 9000:9000 \
  -e KAFKA_BROKERCONNECT=localhost:9092 \
  obsidiandynamics/kafdrop
```text

**2. kcat (kafkacat)**

- CLI tool para Kafka
- Produce/consume desde terminal
- Debugging

```bash
# Install
brew install kcat

# Produce
echo '{"event": "test"}' | kcat -P -b localhost:9092 -t my-topic

# Consume
kcat -C -b localhost:9092 -t my-topic -o beginning

# Get topic metadata
kcat -L -b localhost:9092
```text

**3. Kafka Manager**

- Manage clusters
- Create/delete topics
- Partition reassignment

### Monitoring

**1. Prometheus + Grafana**

```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```text

**2. Kafka Exporter**

- Export Kafka metrics to Prometheus
- Consumer lag, throughput, etc.

```bash
docker run -d \
  --name kafkaexporter \
  -p 9308:9308 \
  danielqsj/kafka-exporter \
  --kafka.server=localhost:9092
```

**3. Confluent Telemetry Reporter**

- Cloud monitoring
- Metrics, logs, traces
- SaaS offering

### IDE Extensions

**1. VS Code Extensions**

- **Kafka**: vscode-kafka
- **Avro**: avro-tools
- **Docker**: docker-compose management

**2. IntelliJ IDEA Plugins**

- Big Data Tools
- Kafka Tool
- Avro and Parquet Viewer

---

## Learning Resources

### Official Documentation

**Kafka**:

- 📖 [Apache Kafka Docs](https://kafka.apache.org/documentation/)
- 📖 [Confluent Docs](https://docs.confluent.io/)
- 📖 [Kafka Quickstart](https://kafka.apache.org/quickstart)

**Flink**:

- 📖 [Apache Flink Docs](https://nightlies.apache.org/flink/flink-docs-stable/)
- 📖 [PyFlink Docs](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/python/overview/)
- 📖 [Flink Training](https://nightlies.apache.org/flink/flink-docs-stable/docs/learn-flink/overview/)

**AWS**:

- 📖 [Kinesis Developer Guide](https://docs.aws.amazon.com/streams/latest/dev/introduction.html)
- 📖 [MSK Developer Guide](https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html)

### Video Tutorials

**Free Courses**:

- 🎥 [Kafka Tutorial for Beginners](https://www.youtube.com/watch?v=qu96DFXtbG4) - Stephane Maarek (2h)
- 🎥 [Apache Flink Training](https://www.youtube.com/playlist?list=PLhfHPmPYPPRl9s0WcLj1gZLWBECCZEhOw) - Flink Forward
- 🎥 [Event-Driven Architecture](https://www.youtube.com/watch?v=STKCRSUsyP0) - Scaling up (45min)

**Conference Talks**:

- 🎥 **Kafka Summit**: kafka-summit.org/past-events
- 🎥 **Flink Forward**: flink-forward.org/
- 🎥 **AWS re:Invent** Kinesis talks

### Interactive Tutorials

**1. Confluent Schema Registry Tutorial**

- <https://developer.confluent.io/tutorials/>
- Hands-on Kafka tutorials
- Code included

**2. AWS Kinesis Workshops**

- <https://streaming-data-workshop.workshop.aws/>
- Free, interactive
- Real AWS environment

**3. Katacoda Kafka Tutorials**

- <https://www.katacoda.com/courses/kafka>
- Browser-based
- No setup required

### Blog Posts & Articles

**Must-Read Posts**:

- 📝 [The Log: What every software engineer should know about real-time data](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying) - LinkedIn Engineering
- 📝 [Building a Real-time Data Platform](https://www.confluent.io/blog/building-real-time-data-platform/) - Confluent Blog
- 📝 [Stream Processing 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) - Tyler Akidau

**Engineering Blogs**:

- 🏢 **LinkedIn**: engineering.linkedin.com/blog
- 🏢 **Uber**: eng.uber.com (Real-time Data Infrastructure)
- 🏢 **Netflix**: netflixtechblog.com (Stream Processing at Netflix)
- 🏢 **Airbnb**: medium.com/airbnb-engineering

---

## Books

### Beginner

**1. "Kafka: The Definitive Guide"** ⭐⭐⭐⭐⭐

- **Authors**: Neha Narkhede, Gwen Shapira, Todd Palino
- **Publisher**: O'Reilly (2021, 2nd Edition)
- **Topics**: Kafka fundamentals, architecture, operations
- **Best for**: Complete beginners to Kafka

**2. "Learning Apache Kafka"**

- **Author**: Nishant Garg
- **Publisher**: Packt (2022, 2nd Edition)
- **Topics**: Quick start, practical examples
- **Best for**: Hands-on learners

### Intermediate

**3. "Streaming Systems"** ⭐⭐⭐⭐⭐

- **Authors**: Tyler Akidau, Slava Chernyak, Reuven Lax
- **Publisher**: O'Reilly (2018)
- **Topics**: Stream processing concepts, windowing, watermarks
- **Best for**: Understanding streaming fundamentals
- **Note**: Language-agnostic theory

**4. "Stream Processing with Apache Flink"**

- **Authors**: Fabian Hueske, Vasiliki Kalavri
- **Publisher**: O'Reilly (2019)
- **Topics**: Flink architecture, DataStream API, stateful processing
- **Best for**: Flink developers

**5. "Designing Event-Driven Systems"**

- **Author**: Ben Stopford (Confluent)
- **Publisher**: O'Reilly (2018)
- **Free**: <https://www.confluent.io/designing-event-driven-systems/>
- **Topics**: Event-driven architectures, patterns
- **Best for**: Architectural design

### Advanced

**6. "Streaming Architecture"**

- **Authors**: Ted Dunning, Ellen Friedman
- **Publisher**: O'Reilly (2016)
- **Topics**: Architectural patterns, Lambda vs Kappa
- **Best for**: Architects

**7. "Building Data-Intensive Applications"** ⭐⭐⭐⭐⭐

- **Author**: Martin Kleppmann
- **Publisher**: O'Reilly (2017)
- **Topics**: Distributed systems, replication, consistency
- **Best for**: Deep technical understanding
- **Note**: Chapter 11 on Stream Processing es gold

---

## Courses & Certifications

### Online Courses

**Udemy**:

- 🎓 **Apache Kafka Series - Learn Apache Kafka for Beginners** ($85)
  - Instructor: Stephane Maarek
  - 12 hours, 4.6★
  - Hands-on projects

- 🎓 **Apache Kafka Series - Kafka Streams for Data Processing** ($85)
  - Instructor: Stephane Maarek
  - 7 hours, 4.6★
  - Kafka Streams deep dive

**Coursera**:

- 🎓 **Modern Big Data Analysis with SQL Specialization**
  - Includes Kafka and streaming analytics
  - 6 months, beginner level

**Pluralsight**:

- 🎓 **Getting Started with Apache Kafka**
  - 2h 30m, intermediate
  - Practical examples

**LinkedIn Learning**:

- 🎓 **Learning Apache Kafka**
  - 1h 20m, beginner
  - Quick introduction

### Confluent Training

**Official Confluent Courses**:

- 🎓 **Confluent Fundamentals for Apache Kafka** (Free)
  - Self-paced, 5 hours
  - Certificate included

- 🎓 **Building Kafka Solutions with Schema Registry** ($500)
  - Instructor-led, 1 day
  - Hands-on labs

- 🎓 **Apache Kafka Administration by Confluent** ($500)
  - Operations, monitoring, troubleshooting
  - 2 days

### Certifications

**1. Confluent Certified Administrator for Apache Kafka (CCAAK)**

- **Cost**: $150
- **Duration**: 90 minutes
- **Questions**: ~60
- **Topics**: Kafka architecture, operations, troubleshooting
- **Validity**: 2 years
- **Preparation**: Study guide + practice exams

**2. Confluent Certified Developer for Apache Kafka (CCDAK)**

- **Cost**: $150
- **Duration**: 90 minutes
- **Questions**: ~60
- **Topics**: Producers, consumers, Kafka Streams, Connect
- **Validity**: 2 years

**3. AWS Certified Data Analytics - Specialty**

- **Cost**: $300
- **Duration**: 180 minutes
- **Topics**: Kinesis, EMR, Glue, Athena
- **Includes**: Streaming data processing

**4. Google Cloud Professional Data Engineer**

- **Cost**: $200
- **Duration**: 120 minutes
- **Topics**: Pub/Sub, Dataflow, BigQuery streaming
- **Validity**: 2 years

### Free Resources

**Confluent Developer**:

- <https://developer.confluent.io/>
- Free courses, tutorials, examples
- Kafka 101, Kafka Streams 101

**AWS Training**:

- <https://www.aws.training/>
- Free Kinesis courses
- Digital badges

---

## Community & Events

### Conferences

**1. Kafka Summit** (2x/year)

- North America + Europe/APAC
- Confluent-organized
- 100+ talks
- <https://kafka-summit.org/>

**2. Flink Forward** (Annual)

- Berlin, San Francisco, Asia
- Apache Flink community
- <https://flink-forward.org/>

**3. Current (by Confluent)**

- Annual, Austin TX
- Real-time data streaming
- <https://current.confluent.io/>

**4. AWS re:Invent** (Annual)

- Las Vegas, November
- Kinesis/MSK sessions
- <https://reinvent.awsevents.com/>

### Meetups

**Find Local Meetups**:

- meetup.com/topics/apache-kafka/
- meetup.com/topics/stream-processing/
- 300+ Kafka meetups worldwide

**Virtual Meetups**:

- Kafka Summit Community Slack
- Confluent Community Slack
- Flink Slack

### Online Communities

**Slack**:

- 💬 **Confluent Community**: cnfl.io/slack
- 💬 **Apache Flink**: s.apache.org/flink-slack
- 💬 **Apache Kafka Users**: <kafka-users@googlegroups.com>

**Reddit**:

- 📱 r/apachekafka (13K members)
- 📱 r/dataengineering (100K members)
- 📱 r/bigdata (50K members)

**Stack Overflow**:

- 🔍 [apache-kafka] tag (20K+ questions)
- 🔍 [apache-flink] tag (5K+ questions)
- 🔍 [aws-kinesis] tag (3K+ questions)

**GitHub**:

- ⭐ apache/kafka (27K stars)
- ⭐ apache/flink (22K stars)
- ⭐ confluentinc/kafka-streams-examples (2K stars)

### Newsletters

**Weekly**:

- 📧 **Confluent Newsletter**: confluent.io/resources/newsletter/
- 📧 **Data Engineering Weekly**: dataengineeringweekly.com
- 📧 **Streaming Media Guild**: streaminmediaguild.com

---

## Comparison Matrix

### When to Use Each Tool

| Scenario | Tool | Reason |
|----------|------|--------|
| High-throughput logs | **Kafka** | Durability, replay |
| AWS-native, simple | **Kinesis** | Managed, easy |
| Complex event processing | **Flink** | Stateful, event-time |
| Batch + streaming unified | **Spark Streaming** | Familiar API |
| Simple Kafka transformations | **Kafka Streams** | No cluster |
| GCP-native | **Pub/Sub + Dataflow** | Serverless |
| Traditional messaging | **RabbitMQ** | Queuing patterns |
| Multi-cloud streaming | **Pulsar** | Geo-replication |

---

## Roadmap de Aprendizaje

### Mes 1: Fundamentos

- ✅ Leer "Kafka: The Definitive Guide" Parte I
- ✅ Completar Confluent Kafka 101
- ✅ Setup local Kafka cluster (Docker)
- ✅ Escribir primer producer/consumer
- ✅ Module 08 Exercises 01-03

### Mes 2: Stream Processing

- ✅ Read "Streaming Systems" Chapters 1-4
- ✅ Learn Flink DataStream API
- ✅ Implementar windowing/stateful processing
- ✅ Module 08 Exercises 04-06
- ✅ Build personal streaming project

### Month 3: Production

- ✅ Kafka operations + monitoring
- ✅ Deploy en AWS (MSK o self-hosted)
- ✅ Implementar CI/CD para streaming apps
- ✅ Performance tuning
- ✅ CCDAK Certification (optional)

### Month 4+: Advanced

- ✅ Schema evolution strategies
- ✅ Multi-DC replication
- ✅ Event-driven microservices architecture
- ✅ Contribute to open source (Kafka/Flink)
- ✅ Advanced certifications

---

## Resumen

### Herramientas Esenciales

**Must-Know**:

- ✅ Apache Kafka (broker)
- ✅ Apache Flink o Spark Streaming (processing)
- ✅ Avro (serialization)
- ✅ Docker + Docker Compose (local dev)
- ✅ Prometheus + Grafana (monitoring)

**Nice-to-Know**:

- ✅ AWS Kinesis | GCP Pub/Sub | Azure Event Hubs
- ✅ Kafka Streams
- ✅ Schema Registry
- ✅ kcat (kafkacat)

### Mejores resources para Empezar

1. 📖 Confluent Kafka 101 (Free course)
2. 🎥 Stephane Maarek's Udemy course
3. 📚 "Kafka: The Definitive Guide" book
4. 🏋️ Module 08 hands-on exercises
5. 💬 Join Confluent Community Slack

### Next Steps

1. 🚀 Completar Exercise 01: Kafka Setup
2. 📊 Build un streaming dashboard con Flink
3. 🔍 Explorar AWS Kinesis
4. 🎯 CCDAK Certification
5. 🏆 Contribuir a proyecto open source

---

**Previous**: [02-architecture.md](./02-architecture.md) - Streaming Architectures
**Next**: Start with [exercises/01-kafka-basics/](../exercises/01-kafka-basics/)
