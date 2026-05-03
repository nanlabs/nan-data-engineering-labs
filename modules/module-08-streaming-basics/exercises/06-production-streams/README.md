# Exercise 06: Production Streaming

**Difficulty**: ⭐⭐⭐ Advanced
**Estimated Time**: 3-4 hours
**Prerequisites**: Exercise 01-05 completed

---

## 🎯 Objectives

Production-ready streaming:
- **Monitoring**: Metrics and alerting
- **Error Handling**: Dead letter queues
- **Scaling**: Horizontal scaling strategies
- **Fault Tolerance**: Recovery mechanisms
- **Testing**: Stream testing patterns

---

## 📚 Concepts

### Production Checklist

- ✅ **Monitoring**: Metrics collection and visualization
- ✅ **Alerting**: Automated incident detection
- ✅ **Error Handling**: DLQ for failed events
- ✅ **Scaling**: Auto-scaling based on lag
- ✅ **Testing**: Unit, integration, end-to-end tests
- ✅ **Deployment**: CI/CD pipeline
- ✅ **Documentation**: Runbooks and architecture docs

---

## 🏋️ Exercises

### Part 1: Structured Logging (30 min)

**Task**: Implement JSON structured logging

**File**: `starter/streaming_logger.py`

```python
import structlog
import logging

def configure_logging():
    \"\"\"TODO: Configure structured logging\"\"\"
    logging.basicConfig(
        format='%(message)s',
        level=logging.INFO
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )

logger = structlog.get_logger()

# Usage in stream processor
def process_event(event: dict):
    logger.info(
        'processing_event',
        event_id=event['event_id'],
        event_type=event['event_type'],
        user_id=event['user_id']
    )

    try:
        # Process...
        logger.info('event_processed', event_id=event['event_id'])
    except Exception as e:
        logger.error(
            'processing_failed',
            event_id=event['event_id'],
            error=str(e),
            exc_info=True
        )
```

### Part 2: Metrics Collection (45 min)

**Task**: Collect and expose Prometheus metrics

**File**: `starter/stream_metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

class StreamMetrics:
    def __init__(self):
        # Counters
        self.events_processed = Counter(
            'stream_events_processed_total',
            'Total events processed',
            ['event_type', 'status']
        )

        self.events_failed = Counter(
            'stream_events_failed_total',
            'Total events failed',
            ['event_type', 'error_type']
        )

        # Histograms
        self.processing_duration = Histogram(
            'stream_processing_duration_seconds',
            'Event processing duration',
            ['event_type']
        )

        # Gauges
        self.consumer_lag = Gauge(
            'stream_consumer_lag',
            'Consumer lag per partition',
            ['topic', 'partition']
        )

        self.events_in_flight = Gauge(
            'stream_events_in_flight',
            'Currently processing events'
        )

    def record_event_processed(self, event_type: str, status: str):
        \"\"\"TODO: Record processed event\"\"\"
        self.events_processed.labels(
            event_type=event_type,
            status=status
        ).inc()

    def record_event_failed(self, event_type: str, error_type: str):
        \"\"\"TODO: Record failed event\"\"\"
        self.events_failed.labels(
            event_type=event_type,
            error_type=error_type
        ).inc()

    def record_processing_time(self, event_type: str, duration: float):
        \"\"\"TODO: Record processing duration\"\"\"
        self.processing_duration.labels(
            event_type=event_type
        ).observe(duration)

    def update_consumer_lag(self, topic: str, partition: int, lag: int):
        \"\"\"TODO: Update consumer lag\"\"\"
        self.consumer_lag.labels(
            topic=topic,
            partition=str(partition)
        ).set(lag)

# Usage in consumer
metrics = StreamMetrics()
start_http_server(8000)  # Expose metrics on :8000/metrics

def process_with_metrics(event: dict):
    start_time = time.time()
    metrics.events_in_flight.inc()

    try:
        # Process event
        result = process_event(event)

        metrics.record_event_processed(
            event['event_type'],
            'success'
        )
    except Exception as e:
        metrics.record_event_failed(
            event['event_type'],
            type(e).__name__
        )
        raise
    finally:
        duration = time.time() - start_time
        metrics.record_processing_time(event['event_type'], duration)
        metrics.events_in_flight.dec()
```

### Part 3: Dead Letter Queue (60 min)

**Task**: Handle failed events with DLQ

**File**: `starter/dlq_handler.py`

```python
class DeadLetterQueue:
    def __init__(self, dlq_topic: str):
        self.dlq_producer = KafkaProducer(...)
        self.dlq_topic = dlq_topic

    def send_to_dlq(self, event: dict, error: Exception,
                    retry_count: int = 0):
        \"\"\"TODO: Send failed event to DLQ with metadata\"\"\"
        dlq_event = {
            'original_event': event,
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            },
            'metadata': {
                'retry_count': retry_count,
                'failed_at': int(time.time() * 1000),
                'processor': 'stream-processor-v1'
            }
        }

        self.dlq_producer.send(
            self.dlq_topic,
            value=json.dumps(dlq_event),
            key=event.get('event_id', '').encode('utf-8')
        )

class RobustStreamProcessor:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.dlq = DeadLetterQueue('failed-events-dlq')

    def process_with_retry(self, event: dict):
        \"\"\"TODO: Process with retry logic\"\"\"
        for attempt in range(self.max_retries):
            try:
                return self.process_event(event)
            except RetryableError as e:
                logger.warning(
                    'retrying_event',
                    event_id=event['event_id'],
                    attempt=attempt + 1,
                    error=str(e)
                )
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                # Non-retryable error
                logger.error('event_failed', event_id=event['event_id'])
                self.dlq.send_to_dlq(event, e, retry_count=attempt)
                return None

        # Max retries exceeded
        logger.error('max_retries_exceeded', event_id=event['event_id'])
        self.dlq.send_to_dlq(event, Exception('Max retries'),
                            retry_count=self.max_retries)
        return None
```

### Part 4: Consumer Lag Monitoring (45 min)

**Task**: Monitor and alert on consumer lag

**File**: `starter/lag_monitor.py`

```python
class ConsumerLagMonitor:
    def __init__(self, bootstrap_servers: str):
        self.admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers
        )
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            enable_auto_commit=False
        )

    def get_consumer_lag(self, group_id: str, topic: str) -> dict:
        \"\"\"TODO: Calculate consumer lag per partition\"\"\"
        # Get group offsets
        group_offsets = self.admin_client.list_consumer_group_offsets(
            group_id
        )

        # Get end offsets (latest)
        partitions = self.consumer.partitions_for_topic(topic)
        topic_partitions = [
            TopicPartition(topic, p) for p in partitions
        ]
        end_offsets = self.consumer.end_offsets(topic_partitions)

        # Calculate lag
        lag = {}
        for tp in topic_partitions:
            committed = group_offsets.get(tp)
            end = end_offsets.get(tp)

            if committed and end:
                lag[tp.partition] = end - committed.offset

        return lag

    def check_lag_threshold(self, group_id: str, topic: str,
                           threshold: int = 1000):
        \"\"\"TODO: Alert if lag exceeds threshold\"\"\"
        lag = self.get_consumer_lag(group_id, topic)

        for partition, lag_count in lag.items():
            if lag_count > threshold:
                logger.error(
                    'high_consumer_lag',
                    group_id=group_id,
                    topic=topic,
                    partition=partition,
                    lag=lag_count,
                    threshold=threshold
                )

                # Send alert
                self.send_alert(
                    f\"High lag on {topic}:{partition} = {lag_count}\"
                )

        return lag

# Run as background thread
def monitor_lag_continuously(interval_seconds: int = 60):
    monitor = ConsumerLagMonitor('localhost:9092')

    while True:
        try:
            lag = monitor.check_lag_threshold(
                group_id='analytics-group',
                topic='user-events',
                threshold=1000
            )

            # Update metrics
            for partition, lag_count in lag.items():
                metrics.update_consumer_lag('user-events', partition, lag_count)
        except Exception as e:
            logger.error('lag_monitoring_failed', error=str(e))

        time.sleep(interval_seconds)
```

### Part 5: Auto-Scaling (60 min)

**Task**: Scale consumers based on lag

**File**: `starter/auto_scaler.py`

```python
class ConsumerAutoScaler:
    def __init__(self, min_consumers: int = 1, max_consumers: int = 10):
        self.min_consumers = min_consumers
        self.max_consumers = max_consumers
        self.current_consumers = min_consumers
        self.lag_monitor = ConsumerLagMonitor('localhost:9092')

    def calculate_desired_consumers(self, total_lag: int,
                                    lag_threshold: int = 1000) -> int:
        \"\"\"TODO: Calculate desired consumer count\"\"\"
        if total_lag == 0:
            return self.min_consumers

        # Scale up if lag > threshold
        if total_lag > lag_threshold * self.current_consumers:
            desired = min(
                self.current_consumers + 1,
                self.max_consumers
            )
        # Scale down if lag << threshold
        elif total_lag < lag_threshold * (self.current_consumers - 1) / 2:
            desired = max(
                self.current_consumers - 1,
                self.min_consumers
            )
        else:
            desired = self.current_consumers

        return desired

    def scale_consumers(self, desired_count: int):
        \"\"\"TODO: Start/stop consumer processes\"\"\"
        if desired_count > self.current_consumers:
            # Scale up
            for _ in range(desired_count - self.current_consumers):
                self.start_consumer()
        elif desired_count < self.current_consumers:
            # Scale down
            for _ in range(self.current_consumers - desired_count):
                self.stop_consumer()

        self.current_consumers = desired_count

        logger.info(
            'scaled_consumers',
            previous=self.current_consumers,
            current=desired_count
        )

    def auto_scale_loop(self, interval_seconds: int = 60):
        \"\"\"Run auto-scaling loop\"\"\"
        while True:
            try:
                lag = self.lag_monitor.get_consumer_lag(
                    'analytics-group',
                    'user-events'
                )
                total_lag = sum(lag.values())

                desired = self.calculate_desired_consumers(total_lag)

                if desired != self.current_consumers:
                    self.scale_consumers(desired)
            except Exception as e:
                logger.error('auto_scaling_failed', error=str(e))

            time.sleep(interval_seconds)
```

### Part 6: Integration Testing (45 min)

**Task**: Test stream processing end-to-end

**File**: `tests/test_stream_integration.py`

```python
import pytest
from testcontainers.kafka import KafkaContainer

@pytest.fixture(scope='session')
def kafka_container():
    \"\"\"Start Kafka container for testing\"\"\"
    with KafkaContainer() as kafka:
        yield kafka

def test_stream_processing_pipeline(kafka_container):
    \"\"\"TODO: Test full pipeline\"\"\"
    bootstrap_servers = kafka_container.get_bootstrap_server()

    # 1. Produce test events
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
    test_events = [
        {'event_id': 'test_1', 'amount': 100},
        {'event_id': 'test_2', 'amount': 200}
    ]

    for event in test_events:
        producer.send('test-input', json.dumps(event).encode())
    producer.flush()

    # 2. Process stream
    processor = StreamProcessor(
        input_topic='test-input',
        output_topic='test-output',
        bootstrap_servers=bootstrap_servers
    )

    # Run for 5 seconds
    import threading
    thread = threading.Thread(target=processor.run)
    thread.start()
    time.sleep(5)
    processor.stop()

    # 3. Consume and verify output
    consumer = KafkaConsumer(
        'test-output',
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000
    )

    results = [json.loads(msg.value) for msg in consumer]

    assert len(results) == 2
    assert results[0]['amount'] == 100
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_production.py -v
```

**Verify**:
- ✅ Metrics exposed on :8000/metrics
- ✅ DLQ receives failed events
- ✅ Lag monitoring works
- ✅ Auto-scaling triggers correctly
- ✅ Integration tests pass

---

## 📊 Monitoring Dashboard

**Grafana Dashboard** (import JSON):

```json
{
  \"panels\": [
    {
      \"title\": \"Events Per Second\",
      \"targets\": [{
        \"expr\": \"rate(stream_events_processed_total[1m])\"
      }]
    },
    {
      \"title\": \"Consumer Lag\",
      \"targets\": [{
        \"expr\": \"stream_consumer_lag\"
      }]
    },
    {
      \"title\": \"Error Rate\",
      \"targets\": [{
        \"expr\": \"rate(stream_events_failed_total[5m])\"
      }]
    }
  ]
}
```

---

## 🔑 Key Learnings

1. **Observability**: Logging, metrics, tracing are essential
2. **Error Handling**: DLQ prevents data loss
3. **Scaling**: Monitor lag and scale proactively
4. **Testing**: Test with real Kafka containers
5. **Automation**: Auto-scaling reduces operational burden

---

## 🚀 Next Steps

- ✅ Deploy to production environment
- ✅ Set up alerting rules
- ✅ Create runbooks for incidents
- ✅ Implement chaos testing
