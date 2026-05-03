# Exercise 05: Apache Flink Processing

**Difficulty**: ⭐⭐⭐ Advanced
**Estimated Time**: 3-4 hours
**Prerequisites**: Exercise 01-04 completed

---

## 🎯 Objectives

Master Apache Flink:
- **DataStream API**: Transform streams
- **Windows**: Time-based aggregation
- **State**: Stateful operations
- **Watermarks**: Handle late events
- **Checkpointing**: Fault tolerance

---

## 📚 Concepts

### Flink Architecture

```
Source → Transformations → Sink
         ├─ Map
         ├─ Filter
         ├─ KeyBy
         ├─ Window
         └─ Aggregate
```

### Event Time vs Processing Time

**Processing Time**: Time when event arrives at operator
**Event Time**: Time when event actually occurred (in event payload)

```
Event occurs → Network delay → Flink processes
   t=0              ?              t=5s

Use Event Time for accurate windows!
```

---

## 🏋️ Exercises

### Part 1: Simple Flink Job (45 min)

**Task**: Read from Kafka, transform, write back

**File**: `starter/simple_flink_job.py`

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer, KafkaSink
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common import Types

def create_kafka_source(bootstrap_servers: str, topic: str, group_id: str):
    """TODO: Create Kafka source"""
    return KafkaSource.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_topics(topic) \
        .set_group_id(group_id) \
        .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()

def create_kafka_sink(bootstrap_servers: str, topic: str):
    """TODO: Create Kafka sink"""
    return KafkaSink.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_record_serializer(...) \
        .build()

def main():
    # Create execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    # TODO: Create source
    source = create_kafka_source(
        bootstrap_servers='localhost:9092',
        topic='user-events',
        group_id='flink-consumer'
    )

    # TODO: Read stream
    stream = env.from_source(
        source,
        watermark_strategy=...,
        source_name='Kafka Source'
    )

    # TODO: Transform
    transformed = stream \
        .map(lambda x: json.loads(x)) \
        .filter(lambda x: x['event_type'] == 'PURCHASE') \
        .map(lambda x: json.dumps(x))

    # TODO: Write to sink
    sink = create_kafka_sink('localhost:9092', 'purchases')
    transformed.sink_to(sink)

    # Execute job
    env.execute('Simple Flink Job')

if __name__ == '__main__':
    main()
```

### Part 2: Keyed Streams (45 min)

**Task**: Aggregate by key

**File**: `starter/keyed_aggregation.py`

```python
from pyflink.datastream.functions import MapFunction, ReduceFunction

class ParseEvent(MapFunction):
    """TODO: Parse JSON event"""
    def map(self, value):
        import json
        return json.loads(value)

class SumAmounts(ReduceFunction):
    """TODO: Sum amounts per key"""
    def reduce(self, value1, value2):
        return {
            'user_id': value1['user_id'],
            'total_amount': value1.get('total_amount', 0) + value2.get('amount', 0),
            'count': value1.get('count', 0) + 1
        }

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    stream = env.from_source(...)

    # TODO: Key by user_id
    keyed_stream = stream \
        .map(ParseEvent()) \
        .key_by(lambda x: x['user_id'])

    # TODO: Reduce (running sum)
    aggregated = keyed_stream.reduce(SumAmounts())

    # Print results
    aggregated.print()

    env.execute('Keyed Aggregation')

if __name__ == '__main__':
    main()
```

### Part 3: Windowed Aggregation (60 min)

**Task**: Tumbling window aggregation

**File**: `starter/windowed_aggregation.py`

```python
from pyflink.datastream.window import TumblingEventTimeWindows, Time
from pyflink.datastream.functions import ProcessWindowFunction
from pyflink.common.watermark_strategy import WatermarkStrategy

class WindowAggregator(ProcessWindowFunction):
    """TODO: Aggregate events in window"""
    def process(self, key, context, elements):
        total = 0
        count = 0

        for element in elements:
            total += element.get('amount', 0)
            count += 1

        yield {
            'user_id': key,
            'window_start': context.window().start,
            'window_end': context.window().end,
            'total_amount': total,
            'count': count,
            'average': total / count if count > 0 else 0
        }

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    # TODO: Set watermark strategy
    watermark_strategy = WatermarkStrategy \
        .for_monotonous_timestamps() \
        .with_timestamp_assigner(lambda event, ts: event['timestamp'])

    stream = env.from_source(
        source=...,
        watermark_strategy=watermark_strategy,
        source_name='...'
    )

    # TODO: Windowed aggregation
    windowed = stream \
        .map(ParseEvent()) \
        .key_by(lambda x: x['user_id']) \
        .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
        .process(WindowAggregator())

    windowed.print()

    env.execute('Windowed Aggregation')

if __name__ == '__main__':
    main()
```

### Part 4: Stateful Processing (60 min)

**Task**: Maintain state per key

**File**: `starter/stateful_processing.py`

```python
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.typeinfo import Types

class StatefulProcessor(KeyedProcessFunction):
    """TODO: Process with state"""

    def open(self, runtime_context: RuntimeContext):
        """Initialize state"""
        # Value state: stores single value per key
        state_descriptor = ValueStateDescriptor(
            'user_total',
            Types.TUPLE([Types.FLOAT(), Types.INT()])  # (total, count)
        )
        self.state = runtime_context.get_state(state_descriptor)

    def process_element(self, value, ctx):
        """TODO: Update state and emit result"""
        # Get current state
        current = self.state.value()
        if current is None:
            total, count = 0.0, 0
        else:
            total, count = current

        # Update state
        amount = value.get('amount', 0)
        total += amount
        count += 1

        self.state.update((total, count))

        # Emit result
        yield {
            'user_id': value['user_id'],
            'total': total,
            'count': count,
            'average': total / count
        }

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    stream = env.from_source(...) \
        .map(ParseEvent()) \
        .key_by(lambda x: x['user_id']) \
        .process(StatefulProcessor())

    stream.print()

    env.execute('Stateful Processing')

if __name__ == '__main__':
    main()
```

### Part 5: Late Events with Watermarks (60 min)

**Task**: Handle late-arriving events

**File**: `starter/late_events.py`

```python
from pyflink.datastream.window import TumblingEventTimeWindows, Time
from pyflink.common.watermark_strategy import WatermarkStrategy, TimestampAssigner
from datetime import timedelta

class EventTimestampAssigner(TimestampAssigner):
    """Extract timestamp from event"""
    def extract_timestamp(self, value, record_timestamp):
        return value['timestamp']

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    # TODO: Watermark strategy with allowed lateness
    watermark_strategy = WatermarkStrategy \
        .for_bounded_out_of_orderness(timedelta(seconds=10)) \
        .with_timestamp_assigner(EventTimestampAssigner())

    stream = env.from_source(
        source=...,
        watermark_strategy=watermark_strategy,
        source_name='...'
    )

    # TODO: Window with allowed lateness
    windowed = stream \
        .map(ParseEvent()) \
        .key_by(lambda x: x['user_id']) \
        .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
        .allowed_lateness(Time.seconds(30)) \
        .process(WindowAggregator())

    # TODO: Side output for very late events
    late_output_tag = OutputTag('late-events', Types.STRING())

    windowed.get_side_output(late_output_tag).print_to_err()

    windowed.print()

    env.execute('Late Events Handling')

if __name__ == '__main__':
    main()
```

### Part 6: Checkpointing (30 min)

**Task**: Enable fault tolerance

**File**: `starter/checkpointing.py`

```python
from pyflink.datastream.checkpointing_mode import CheckpointingMode

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    # TODO: Enable checkpointing
    env.enable_checkpointing(60000)  # 60 seconds

    # TODO: Set checkpointing mode
    env.get_checkpoint_config().set_checkpointing_mode(
        CheckpointingMode.EXACTLY_ONCE
    )

    # TODO: Set checkpoint storage
    env.get_checkpoint_config().set_checkpoint_storage(
        'file:///tmp/flink-checkpoints'
    )

    # TODO: Set min pause between checkpoints
    env.get_checkpoint_config().set_min_pause_between_checkpoints(30000)

    # TODO: Set max concurrent checkpoints
    env.get_checkpoint_config().set_max_concurrent_checkpoints(1)

    # TODO: Enable unaligned checkpoints for low latency
    env.get_checkpoint_config().enable_unaligned_checkpoints()

    # ... rest of job ...

    env.execute('Checkpointed Job')

if __name__ == '__main__':
    main()
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_flink.py -v
```

**Tests cover**:
- ✅ Simple transformations work
- ✅ Keyed aggregation correct
- ✅ Windows aggregate properly
- ✅ State maintained correctly
- ✅ Late events handled
- ✅ Checkpointing enabled

---

## 🎯 Flink Benefits

1. **True Streaming**: Low latency, event-at-a-time
2. **Event Time**: Correct results even with late data
3. **Exactly-Once**: Strong fault tolerance guarantees
4. **Stateful**: Built-in state management
5. **Scalable**: Distributed processing

---

## 🔑 Key Learnings

1. **DataStream API**: Functional transformations on streams
2. **Windows**: Time-based or count-based grouping
3. **State**: Per-key state with fault tolerance
4. **Watermarks**: Track event time progress
5. **Checkpointing**: Exactly-once semantics

---

## 🚀 Next Steps

- ✅ Exercise 06: Production deployment patterns
- ✅ Experiment with different window types
- ✅ Compare Flink vs Kafka Streams
