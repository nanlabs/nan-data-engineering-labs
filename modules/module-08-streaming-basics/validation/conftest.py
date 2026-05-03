"""Shared pytest fixtures for Module 08: Streaming Basics"""

import pytest
import json
import time
from typing import Generator
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError


# ==================== Kafka Fixtures ====================

@pytest.fixture(scope='session')
def kafka_bootstrap_servers() -> str:
    """Kafka bootstrap servers"""
    return 'localhost:9092'


@pytest.fixture(scope='session')
def schema_registry_url() -> str:
    """Schema Registry URL"""
    return 'http://localhost:8081'


@pytest.fixture(scope='session')
def kafka_admin_client(kafka_bootstrap_servers) -> Generator[KafkaAdminClient, None, None]:
    """Kafka admin client for managing topics"""
    admin_client = KafkaAdminClient(
        bootstrap_servers=kafka_bootstrap_servers,
        request_timeout_ms=10000
    )
    yield admin_client
    admin_client.close()


@pytest.fixture
def test_topic(kafka_admin_client) -> Generator[str, None, None]:
    """Create a unique test topic"""
    topic_name = f'test-topic-{int(time.time() * 1000)}'

    topic = NewTopic(
        name=topic_name,
        num_partitions=3,
        replication_factor=1
    )

    try:
        kafka_admin_client.create_topics([topic])
        time.sleep(1)  # Wait for topic creation
    except TopicAlreadyExistsError:
        pass

    yield topic_name

    # Cleanup
    try:
        kafka_admin_client.delete_topics([topic_name])
    except Exception as e:
        print(f"Failed to delete topic {topic_name}: {e}")


@pytest.fixture
def kafka_producer(kafka_bootstrap_servers) -> Generator[KafkaProducer, None, None]:
    """Kafka producer with JSON serialization"""
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    yield producer
    producer.flush()
    producer.close()


@pytest.fixture
def kafka_consumer(kafka_bootstrap_servers, test_topic) -> Generator[KafkaConsumer, None, None]:
    """Kafka consumer with JSON deserialization"""
    consumer = KafkaConsumer(
        test_topic,
        bootstrap_servers=kafka_bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000,
        group_id=f'test-group-{int(time.time() * 1000)}'
    )
    yield consumer
    consumer.close()


# ==================== Sample Events ====================

@pytest.fixture
def sample_user_event() -> dict:
    """Sample user event"""
    return {
        'event_id': 'evt_test_001',
        'event_type': 'PURCHASE',
        'timestamp': int(time.time() * 1000),
        'user_id': 'user_test_123',
        'session_id': 'session_test_456',
        'amount': 99.99,
        'currency': 'USD',
        'country': 'US',
        'device_type': 'MOBILE'
    }


@pytest.fixture
def sample_sensor_reading() -> dict:
    """Sample sensor reading"""
    return {
        'sensor_id': 'sensor_test_001',
        'device_id': 'device_test_123',
        'timestamp': int(time.time() * 1000),
        'sensor_type': 'TEMPERATURE',
        'value': 23.5,
        'unit': 'celsius',
        'quality': 'GOOD',
        'battery_level': 85
    }


@pytest.fixture
def sample_transaction() -> dict:
    """Sample transaction"""
    return {
        'transaction_id': 'txn_test_001',
        'timestamp': int(time.time() * 1000),
        'user_id': 'user_test_123',
        'account_id': 'acc_test_456',
        'transaction_type': 'PURCHASE',
        'amount': 150.00,
        'currency': 'USD',
        'payment_method': 'CREDIT_CARD',
        'status': 'COMPLETED',
        'risk_score': 25,
        'flagged_for_review': False
    }


@pytest.fixture
def sample_events_batch(sample_user_event) -> list:
    """Batch of sample events"""
    return [
        {**sample_user_event, 'event_id': f'evt_{i}', 'amount': i * 10}
        for i in range(1, 11)
    ]


# ==================== Helper Functions ====================

@pytest.fixture
def produce_events(kafka_producer):
    """Helper to produce events to Kafka"""
    def _produce(topic: str, events: list, key_field: str = None):
        for event in events:
            key = event.get(key_field) if key_field else None
            kafka_producer.send(topic, value=event, key=key)
        kafka_producer.flush()
    return _produce


@pytest.fixture
def consume_events(kafka_consumer):
    """Helper to consume all available events"""
    def _consume(max_events: int = 100) -> list:
        events = []
        for message in kafka_consumer:
            events.append(message.value)
            if len(events) >= max_events:
                break
        return events
    return _consume


# ==================== Docker Compose Fixtures ====================

@pytest.fixture(scope='session', autouse=True)
def ensure_kafka_running():
    """Ensure Kafka is running before tests"""
    try:
        # Try to connect
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            request_timeout_ms=5000,
            max_block_ms=5000
        )
        producer.close()
        print("✓ Kafka is running")
    except Exception as e:
        pytest.fail(
            f"Kafka is not running. Please start with: "
            f"cd ../../infrastructure && docker-compose up -d\n"
            f"Error: {e}"
        )


# ==================== Cleanup ====================

@pytest.fixture(autouse=True)
def cleanup_between_tests():
    """Cleanup between tests"""
    yield
    # Add any cleanup logic here
    time.sleep(0.1)


# ==================== Markers ====================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "kafka: marks tests that require Kafka"
    )
    config.addinivalue_line(
        "markers", "flink: marks tests that require Flink"
    )
    config.addinivalue_line(
        "markers", "aws: marks tests that require AWS"
    )
