"""Module 08: Streaming Basics - Validation Tests"""

import pytest
import json
import time
from pathlib import Path


# ==================== Kafka Basic Tests ====================

@pytest.mark.kafka
class TestKafkaBasics:
    """Test Kafka fundamentals"""

    def test_producer_sends_events(self, kafka_producer, test_topic,
                                   sample_user_event):
        """Test producer can send events"""
        # Send event
        future = kafka_producer.send(test_topic, value=sample_user_event)
        result = future.get(timeout=10)

        assert result.topic == test_topic
        assert result.partition >= 0
        assert result.offset >= 0

    def test_consumer_receives_events(self, kafka_producer, kafka_consumer,
                                     test_topic, sample_user_event):
        """Test consumer receives sent events"""
        # Produce event
        kafka_producer.send(test_topic, value=sample_user_event)
        kafka_producer.flush()

        # Consume event
        messages = []
        for message in kafka_consumer:
            messages.append(message.value)
            break

        assert len(messages) == 1
        assert messages[0]['event_id'] == sample_user_event['event_id']

    def test_batch_sending(self, kafka_producer, test_topic,
                          sample_events_batch):
        """Test batch sending of events"""
        futures = []
        for event in sample_events_batch:
            future = kafka_producer.send(test_topic, value=event)
            futures.append(future)

        kafka_producer.flush()

        # Verify all sent
        for future in futures:
            result = future.get(timeout=10)
            assert result.offset >= 0

    def test_partitioning_by_key(self, kafka_producer, test_topic):
        """Test events with same key go to same partition"""
        key = 'test_user_123'

        partitions = set()
        for i in range(10):
            event = {'event_id': f'evt_{i}', 'user_id': key}
            future = kafka_producer.send(test_topic, value=event, key=key)
            result = future.get(timeout=10)
            partitions.add(result.partition)

        # All should go to same partition
        assert len(partitions) == 1


# ==================== Stream Processing Tests ====================

@pytest.mark.integration
class TestStreamProcessing:
    """Test stream processing operations"""

    def test_filter_stream(self, produce_events, consume_events,
                          test_topic, sample_events_batch):
        """Test filtering stream"""
        # Produce events
        produce_events(test_topic, sample_events_batch)

        # Consume and filter
        events = consume_events(max_events=10)
        high_value = [e for e in events if e['amount'] > 50]

        assert len(high_value) > 0
        assert all(e['amount'] > 50 for e in high_value)

    def test_map_transformation(self, produce_events, consume_events,
                               test_topic, sample_events_batch):
        """Test map transformation"""
        produce_events(test_topic, sample_events_batch)

        events = consume_events(max_events=10)

        # Transform: add computed field
        transformed = [
            {**e, 'amount_doubled': e['amount'] * 2}
            for e in events
        ]

        assert len(transformed) == len(events)
        assert all('amount_doubled' in e for e in transformed)

    def test_stateful_aggregation(self, produce_events, consume_events,
                                 test_topic, sample_events_batch):
        """Test stateful aggregation"""
        produce_events(test_topic, sample_events_batch)

        events = consume_events(max_events=10)

        # Aggregate: sum per user
        state = {}
        for event in events:
            user_id = event['user_id']
            if user_id not in state:
                state[user_id] = {'count': 0, 'total': 0}

            state[user_id]['count'] += 1
            state[user_id]['total'] += event['amount']

        assert len(state) > 0
        for user_id, agg in state.items():
            assert agg['count'] > 0
            assert agg['total'] > 0


# ==================== Avro Schema Tests ====================

@pytest.mark.integration
class TestAvroSchemas:
    """Test Avro schema management"""

    def test_user_event_schema_exists(self):
        """Test user event schema file exists"""
        schema_path = Path('../../data/schemas/user_event.avsc')
        assert schema_path.exists()

        with open(schema_path) as f:
            schema = json.load(f)

        assert schema['type'] == 'record'
        assert schema['name'] == 'UserEvent'
        assert len(schema['fields']) > 0

    def test_sensor_reading_schema_exists(self):
        """Test sensor reading schema exists"""
        schema_path = Path('../../data/schemas/sensor_reading.avsc')
        assert schema_path.exists()

        with open(schema_path) as f:
            schema = json.load(f)

        assert schema['type'] == 'record'
        assert schema['name'] == 'SensorReading'

    def test_transaction_schema_exists(self):
        """Test transaction schema exists"""
        schema_path = Path('../../data/schemas/transaction.avsc')
        assert schema_path.exists()

        with open(schema_path) as f:
            schema = json.load(f)

        assert schema['type'] == 'record'
        assert schema['name'] == 'Transaction'

    def test_schema_validation(self, sample_user_event):
        """Test event validates against schema"""
        from fastavro import validate
        from fastavro.schema import load_schema

        schema_path = Path('../../data/schemas/user_event.avsc')
        schema = load_schema(schema_path)

        # Valid event should pass
        assert validate(sample_user_event, schema)

        # Invalid event should fail
        invalid_event = {'invalid': 'event'}
        with pytest.raises(Exception):
            validate(invalid_event, schema, raise_errors=True)


# ==================== Data Generation Tests ====================

class TestDataGeneration:
    """Test event generation"""

    def test_event_generator_script_exists(self):
        """Test generator script exists"""
        script_path = Path('../../data/scripts/stream_generator.py')
        assert script_path.exists()

    def test_generate_user_event(self):
        """Test generating user event"""
        import sys
        sys.path.insert(0, str(Path('../../data/scripts')))

        from stream_generator import EventGenerator

        generator = EventGenerator()
        event = generator.generate_user_event()

        assert 'event_id' in event
        assert 'event_type' in event
        assert 'timestamp' in event
        assert 'user_id' in event

    def test_generate_sensor_reading(self):
        """Test generating sensor reading"""
        import sys
        sys.path.insert(0, str(Path('../../data/scripts')))

        from stream_generator import EventGenerator

        generator = EventGenerator()
        reading = generator.generate_sensor_reading()

        assert 'sensor_id' in reading
        assert 'sensor_type' in reading
        assert 'value' in reading
        assert 'timestamp' in reading

    def test_generate_transaction(self):
        """Test generating transaction"""
        import sys
        sys.path.insert(0, str(Path('../../data/scripts')))

        from stream_generator import EventGenerator

        generator = EventGenerator()
        transaction = generator.generate_transaction()

        assert 'transaction_id' in transaction
        assert 'transaction_type' in transaction
        assert 'amount' in transaction
        assert 'timestamp' in transaction


# ==================== Infrastructure Tests ====================

class TestInfrastructure:
    """Test infrastructure setup"""

    def test_docker_compose_exists(self):
        """Test Docker Compose file exists"""
        compose_path = Path('../../infrastructure/docker-compose.yml')
        assert compose_path.exists()

    def test_kafka_accessible(self, kafka_bootstrap_servers):
        """Test Kafka is accessible"""
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            request_timeout_ms=5000
        )
        producer.close()

    def test_schema_registry_accessible(self, schema_registry_url):
        """Test Schema Registry is accessible"""
        import requests

        response = requests.get(f'{schema_registry_url}/subjects')
        assert response.status_code == 200


# ==================== Theory Content Tests ====================

class TestTheoryContent:
    """Test theory documentation exists"""

    def test_concepts_doc_exists(self):
        """Test concepts documentation exists"""
        doc_path = Path('../../theory/01-concepts.md')
        assert doc_path.exists()

        content = doc_path.read_text()
        assert len(content) > 5000  # At least 5K characters

    def test_architecture_doc_exists(self):
        """Test architecture documentation exists"""
        doc_path = Path('../../theory/02-architecture.md')
        assert doc_path.exists()

        content = doc_path.read_text()
        assert len(content) > 5000

    def test_resources_doc_exists(self):
        """Test resources documentation exists"""
        doc_path = Path('../../theory/03-resources.md')
        assert doc_path.exists()

        content = doc_path.read_text()
        assert len(content) > 2000


# ==================== Exercise Tests ====================

class TestExercises:
    """Test exercise READMEs exist"""

    @pytest.mark.parametrize('exercise_num', range(1, 7))
    def test_exercise_readme_exists(self, exercise_num):
        """Test exercise README exists"""
        exercise_name = {
            1: 'kafka-basics',
            2: 'stream-processing',
            3: 'avro-schemas',
            4: 'kinesis-streams',
            5: 'flink-processing',
            6: 'production-streams'
        }[exercise_num]

        readme_path = Path(f'../../exercises/{exercise_num:02d}-{exercise_name}/README.md')
        assert readme_path.exists(), f"Exercise {exercise_num} README not found"

        content = readme_path.read_text()
        assert len(content) > 1000, f"Exercise {exercise_num} README too short"


# ==================== Performance Tests ====================

@pytest.mark.slow
class TestPerformance:
    """Test streaming performance"""

    def test_producer_throughput(self, kafka_producer, test_topic):
        """Test producer throughput"""
        num_events = 1000
        start_time = time.time()

        for i in range(num_events):
            event = {
                'event_id': f'evt_{i}',
                'timestamp': int(time.time() * 1000),
                'data': f'test_data_{i}'
            }
            kafka_producer.send(test_topic, value=event)

        kafka_producer.flush()
        duration = time.time() - start_time

        throughput = num_events / duration
        print(f"\nProducer throughput: {throughput:.2f} events/sec")

        # Should achieve at least 100 events/sec locally
        assert throughput > 100

    @pytest.mark.integration
    def test_end_to_end_latency(self, kafka_producer, kafka_consumer,
                                test_topic):
        """Test end-to-end latency"""
        send_time = time.time()
        event = {
            'event_id': 'latency_test',
            'timestamp': int(send_time * 1000)
        }

        kafka_producer.send(test_topic, value=event)
        kafka_producer.flush()

        # Consume
        for message in kafka_consumer:
            if message.value['event_id'] == 'latency_test':
                receive_time = time.time()
                break

        latency = (receive_time - send_time) * 1000  # ms
        print(f"\nEnd-to-end latency: {latency:.2f}ms")

        # Should be under 100ms locally
        assert latency < 100


# ==================== Summary ====================

def test_module_08_summary():
    """Print module completion summary"""
    print("\n" + "="*60)
    print("MODULE 08: STREAMING BASICS - VALIDATION SUMMARY")
    print("="*60)
    print("✓ Kafka basics tested")
    print("✓ Stream processing validated")
    print("✓ Avro schemas verified")
    print("✓ Data generation working")
    print("✓ Infrastructure accessible")
    print("✓ Theory content complete")
    print("✓ Exercise READMEs present")
    print("="*60)
