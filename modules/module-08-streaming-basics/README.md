# Module 08: Streaming Fundamentals

Production-ready real-time stream processing with Apache Kafka, Flink, and AWS Kinesis.

---

## 🎯 General Description

Master real-time data streaming and build production-grade streaming applications. Learn Apache Kafka for distributed messaging, implement stream transformations with Python, and deploy advanced processing with Apache Flink.

**Duration**: 4-5 weeks (40-50 hours)
**Level**: Intermediate to Advanced
**Prerequisites**: Python, Docker, fundamentos de SQL

---

## 📚 What You Will Learn

### Conceptos Centrales de Streaming

- Paradigmas de procesamiento stream vs batch
- Fundamentals of event-driven architecture
- Apache Kafka architecture (topics, partitions, consumer groups)
- Message delivery semantics (at-most-once, at-least-once, exactly-once)
- Estrategias de ventanas (tumbling, sliding, session)
- State management in stream processing

### Technical Skills

- **Kafka**: Productores, consumidores, topics, particionamiento, replication
- **Schema Management**: Avro Serialization, Schema Registry, schema evolution
- **Stream Processing**: Filtering, mapping, aggregation, joins
- **Apache Flink**: DataStream API, event time, watermarks, checkpointing
- **AWS Kinesis**: Data Streams, Firehose, consumidores KCL
- **Production Patterns**: Monitoring, error handling (DLQ), scaling

### Architecture Patterns

- Arquitecturas Lambda vs Kappa
- Microservices orientados a eventos
- CQRS (Command Query Responsibility Segregation)
- Saga pattern for distributed transactions
- Change Data Capture (CDC)

---

## 🚀 Quick Start

### 1. Configurar Ambiente (5 minutes)

\`\`\`bash
cd modules/module-08-streaming-basics
./scripts/setup.sh
\`\`\`

This will do:

- ✅ Iniciar Kafka, Zookeeper, Schema Registry (Docker)
- ✅ Crear topics (user-events, sensor-readings, transactions)
- ✅ Generar 300 eventos de ejemplo
- ✅ Verify that all services are running

### 2. Verify Installation

\`\`\`bash
./scripts/validate.sh
\`\`\`

### 3. Explorar Kafka UI

Abre <http://localhost:8080> en tu navegador para:

- Explorar topics y mensajes
- monitor grupos de consumidores
- Ver salud del cluster

### 4. Comenzar a Learn

Start with [Exercise 01: Kafka Basics](exercises/01-kafka-basics/)

Complete guide: [GETTING-STARTED.md](GETTING-STARTED.md)

---

## ✅ Complete Module

This module includes:

- ✅ **18,500 words** of comprehensive theory
- ✅ **6 progressive exercises** (Kafka → Flink → Production)
- ✅ **Infraestructura basada en Docker** (sin costos de cloud)
- ✅ **3 esquemas Avro** para casos de uso realistas
- ✅ **Event generator** with 350 lines of code
- ✅ **40+ validation tests**
- ✅ **Automation scripts** (setup, validate)
- ✅ **Quick References** (Kafka CLI, streaming patterns)

Ver [GETTING-STARTED.md](GETTING-STARTED.md) para la ruta de aprendizaje completa.

---

## 🛠️ Technologies

- Apache Kafka 2.13
- Apache Flink 1.18
- Schema Registry 7.5
- AWS Kinesis
- Python (kafka-python, confluent-kafka, pyflink, boto3)
- Docker & Docker Compose

---

## 📖 Documentation

- [GETTING-STARTED.md](GETTING-STARTED.md) - Complete Guide
- [theory/01-concepts.md](theory/01-concepts.md) - 8K palabras sobre fundamentos
- [theory/02-architecture.md](theory/02-architecture.md) - 7K palabras sobre Kafka/Flink/Kinesis
- [theory/03-resources.md](theory/03-resources.md) - 3.5K palabras sobre herramientas y aprendizaje
- [assets/kafka-quick-reference.md](assets/kafka-quick-reference.md) - Snippets de CLI y Python
- [assets/streaming-patterns.md](assets/streaming-patterns.md) - 13 patrones comunes

---

**Ready to get started?** Run`./scripts/setup.sh` y comienza tu viaje en streaming!

## Objective

This module focuses on one core concept and its practical implementation path.

## Learning Objectives

- Understand the core concept boundaries for this module.
- Apply the concept through guided exercises.
- Validate outcomes using module checks.

## Prerequisites

Review previous dependent modules according to LEARNING-PATH.md before starting.

## Validation

Run the corresponding module validation and confirm expected outputs.
