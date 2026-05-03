# Exercise 02: Stream Processing

**Difficulty**: ⭐⭐ Intermediate
**Estimated Time**: 2-3 hours
**Prerequisites**: Exercise 01 completed

---

## 🎯 Objectives

Learn stream processing patterns:
- **Filtering**: Remove unwanted events
- **Mapping**: Transform events
- **Aggregation**: Compute running totals
- **Windowing**: Time-based aggregation
- **Joining**: Combine multiple streams

---

## 📚 Concepts

### Stream Transformations

```python
# Stateless: Each event processed independently
filtered = stream.filter(lambda x: x['amount'] > 100)
mapped = stream.map(lambda x: transform(x))

# Stateful: Maintains state between events
aggregated = stream.reduce(lambda acc, x: acc + x['amount'])
windowed = stream.window(size=60).aggregate(sum)
```

### Windowing

**Tumbling Windows** (non-overlapping):
```
[──Window 1──][──Window 2──][──Window 3──]
0-60s         60-120s       120-180s
```

**Sliding Windows** (overlapping):
```
[────Window 1────]
    [────Window 2────]
        [────Window 3────]
```

**Session Windows** (gap-based):
```
[Session 1]  [Session 2]    [Session 3]
███──────────███████────────█
      ^10min gap    ^10min gap
```

---

## 🏋️ Exercises

### Part 1: Filter Stream (30 min)

**Task**: Filter high-value transactions

**File**: `starter/stream_filter.py`

```python
from kafka import KafkaConsumer, KafkaProducer
import json

class StreamFilter:
    def __init__(self, input_topic: str, output_topic: str):
        self.consumer = KafkaConsumer(input_topic, ...)
        self.producer = KafkaProducer(...)
        self.output_topic = output_topic

    def filter_high_value(self, threshold: float = 100.0):
        """TODO: Filter and forward events where amount > threshold"""
        for message in self.consumer:
            event = message.value

            # Filter logic
            if event.get('amount', 0) > threshold:
                # Forward to output topic
                pass
```

**Test**:
```python
filter_app = StreamFilter(
    input_topic='transactions',
    output_topic='high-value-transactions'
)
filter_app.filter_high_value(threshold=500.0)
```

### Part 2: Map/Transform Stream (45 min)

**Task**: Enrich events with computed fields

**File**: `starter/stream_mapper.py`

```python
class StreamMapper:
    def enrich_user_event(self, event: dict) -> dict:
        """TODO: Add computed fields:
        - hour_of_day: Extract from timestamp
        - is_weekend: Boolean
        - device_category: mobile vs desktop
        """
        enriched = event.copy()

        # Add hour_of_day
        # Add is_weekend
        # Add device_category

        return enriched

    def process_stream(self):
        for message in self.consumer:
            event = message.value
            enriched = self.enrich_user_event(event)
            self.producer.send(self.output_topic, enriched)
```

### Part 3: Stateful Aggregation (60 min)

**Task**: Running count and sum per user

**File**: `starter/stream_aggregator.py`

```python
class StreamAggregator:
    def __init__(self):
        self.state = {}  # user_id -> {'count': int, 'total': float}

    def aggregate_per_user(self, event: dict) -> dict:
        """TODO: Maintain running totals per user"""
        user_id = event['user_id']
        amount = event.get('amount', 0)

        # Update state
        if user_id not in self.state:
            self.state[user_id] = {'count': 0, 'total': 0}

        # Increment count and total
        # ...

        return {
            'user_id': user_id,
            'count': self.state[user_id]['count'],
            'total': self.state[user_id]['total'],
            'average': self.state[user_id]['total'] / self.state[user_id]['count']
        }
```

### Part 4: Tumbling Window (60 min)

**Task**: Aggregate events in 1-minute windows

**File**: `starter/windowed_aggregator.py`

```python
from collections import defaultdict
import time

class TumblingWindowAggregator:
    def __init__(self, window_size_seconds: int = 60):
        self.window_size = window_size_seconds
        self.windows = defaultdict(lambda: {'count': 0, 'total': 0})

    def get_window_key(self, timestamp_ms: int) -> int:
        """TODO: Calculate window bucket"""
        # Example: timestamp_ms // (window_size * 1000)
        pass

    def aggregate(self, event: dict):
        """TODO: Aggregate into windows"""
        window_key = self.get_window_key(event['timestamp'])

        # Update window
        self.windows[window_key]['count'] += 1
        self.windows[window_key]['total'] += event.get('amount', 0)

        # Emit completed windows
        self.emit_completed_windows()

    def emit_completed_windows(self):
        """Emit and clean up old windows"""
        current_window = self.get_window_key(int(time.time() * 1000))

        for window_key in list(self.windows.keys()):
            if window_key < current_window - 1:
                # Window is complete, emit
                result = {
                    'window_start': window_key * self.window_size,
                    'window_end': (window_key + 1) * self.window_size,
                    **self.windows[window_key]
                }
                yield result
                del self.windows[window_key]
```

### Part 5: Stream Join (45 min)

**Task**: Join user events with user profiles

**File**: `starter/stream_joiner.py`

```python
class StreamJoiner:
    def __init__(self):
        # Load user profiles (dimension table)
        self.user_profiles = self.load_user_profiles()

    def load_user_profiles(self) -> dict:
        """Load user profiles from file or database"""
        # TODO: Load from users.json
        return {}

    def join_with_profile(self, event: dict) -> dict:
        """TODO: Enrich event with user profile data"""
        user_id = event['user_id']
        profile = self.user_profiles.get(user_id, {})

        return {
            **event,
            'user_tier': profile.get('tier'),
            'user_country': profile.get('country'),
            'user_registration_date': profile.get('registration_date')
        }
```

### Part 6: Complex pipeline (30 min)

**Task**: Chain multiple transformations

```python
class StreamPipeline:
    def __init__(self):
        self.filter = StreamFilter(...)
        self.mapper = StreamMapper(...)
        self.aggregator = StreamAggregator(...)

    def process(self):
        """Pipeline: filter → map → aggregate → output"""
        for message in self.consumer:
            event = message.value

            # Step 1: Filter
            if not self.should_process(event):
                continue

            # Step 2: Transform
            enriched = self.mapper.enrich(event)

            # Step 3: Aggregate
            aggregate = self.aggregator.update(enriched)

            # Step 4: Output
            self.producer.send('processed-events', aggregate)
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_stream_processing.py -v
```

**Tests cover**:
- ✅ Filter correctly removes events
- ✅ Map adds all computed fields
- ✅ Aggregation maintains correct state
- ✅ Windows aggregate correctly
- ✅ Join enriches with profile data
- ✅ pipeline chains transformations

---

## 📊 Performance Tips

1. **Batch Processing**: Process multiple events before committing
2. **State Management**: Periodically persist state to disk
3. **Window Cleanup**: Remove old windows to avoid memory leak
4. **Async Processing**: Use async I/O for enrichment

---

## 🚀 Next Steps

- ✅ Exercise 03: Avro schema management
- ✅ Experiment with different window sizes
- ✅ Implement sliding windows
