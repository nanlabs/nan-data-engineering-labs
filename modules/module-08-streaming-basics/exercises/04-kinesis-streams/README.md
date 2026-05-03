# Exercise 04: AWS Kinesis Streams

**Difficulty**: ⭐⭐ Intermediate
**Estimated Time**: 2-3 hours
**Prerequisites**: AWS account, Exercise 01-03 completed

---

## 🎯 Objectives

Learn AWS managed streaming:
- **Kinesis Data Streams**: Real-time data ingestion
- **Producers**: Send records to streams
- **Consumers**: Process records with KCL
- **Shards**: Scaling unit in Kinesis
- **Comparison**: Kinesis vs Kafka

---

## 📚 Concepts

### Kinesis Architecture

```
Producers → Kinesis Stream → Consumers
            ├─ Shard 1
            ├─ Shard 2
            └─ Shard 3
```

### Key Concepts

1. **Stream**: Named data stream
2. **Shard**: Unit of throughput (1 MB/s write, 2 MB/s read)
3. **Partition Key**: Determines shard routing
4. **Sequence Number**: Order within shard
5. **KCL**: Kinesis Client Library for consumers

### Kinesis vs Kafka

| Feature | Kinesis | Kafka |
|---------|---------|-------|
| Management | Fully managed | Self-managed or MSK |
| Scaling | Shard-based | Partition-based |
| Retention | 1-365 days | Unlimited |
| Pricing | Per shard-hour | Per cluster |
| throughput | 1 MB/s per shard | Higher per partition |

---

## 🏋️ Exercises

### Part 1: Create Kinesis Stream (30 min)

**AWS Console**:
1. Go to Kinesis → Data Streams
2. Create stream: `user-events-stream`
3. On-demand or provisioned (2 shards)

**AWS CLI**:
```bash
# Create stream
aws kinesis create-stream \
  --stream-name user-events-stream \
  --shard-count 2 \
  --region us-east-1

# Describe stream
aws kinesis describe-stream \
  --stream-name user-events-stream

# List streams
aws kinesis list-streams
```

**Python (boto3)**:
```python
import boto3

kinesis = boto3.client('kinesis', region_name='us-east-1')

# Create stream
response = kinesis.create_stream(
    StreamName='user-events-stream',
    ShardCount=2
)

# Wait for active
waiter = kinesis.get_waiter('stream_exists')
waiter.wait(StreamName='user-events-stream')
```

### Part 2: Kinesis Producer (45 min)

**File**: `starter/kinesis_producer.py`

```python
import boto3
import json
import time
from typing import Dict, Any

class KinesisProducer:
    def __init__(self, stream_name: str, region: str = 'us-east-1'):
        self.kinesis = boto3.client('kinesis', region_name=region)
        self.stream_name = stream_name

    def send_record(self, data: Dict[str, Any], partition_key: str):
        """TODO: Send single record"""
        try:
            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(data),
                PartitionKey=partition_key
            )
            return response['SequenceNumber']
        except Exception as e:
            print(f"Error: {e}")
            return None

    def send_batch(self, records: list):
        """TODO: Send batch of records (max 500)"""
        # Format records for put_records
        kinesis_records = [
            {
                'Data': json.dumps(record['data']),
                'PartitionKey': record['partition_key']
            }
            for record in records
        ]

        try:
            response = self.kinesis.put_records(
                StreamName=self.stream_name,
                Records=kinesis_records
            )

            # Check failed records
            failed = response['FailedRecordCount']
            if failed > 0:
                print(f"Failed records: {failed}")

            return response
        except Exception as e:
            print(f"Batch error: {e}")
            return None
```

**Test**:
```python
producer = KinesisProducer('user-events-stream')

# Single record
event = {
    'event_id': 'evt_001',
    'event_type': 'PURCHASE',
    'user_id': 'user_123',
    'amount': 99.99,
    'timestamp': int(time.time() * 1000)
}

seq = producer.send_record(event, partition_key='user_123')
print(f"Sequence: {seq}")

# Batch
records = [
    {'data': event, 'partition_key': f'user_{i}'}
    for i in range(100)
]
producer.send_batch(records)
```

### Part 3: Kinesis Consumer (60 min)

**File**: `starter/kinesis_consumer.py`

```python
class KinesisConsumer:
    def __init__(self, stream_name: str, region: str = 'us-east-1'):
        self.kinesis = boto3.client('kinesis', region_name=region)
        self.stream_name = stream_name

    def get_shard_iterator(self, shard_id: str,
                           iterator_type: str = 'TRIM_HORIZON'):
        """TODO: Get shard iterator"""
        response = self.kinesis.get_shard_iterator(
            StreamName=self.stream_name,
            ShardId=shard_id,
            ShardIteratorType=iterator_type  # TRIM_HORIZON, LATEST, AT_TIMESTAMP
        )
        return response['ShardIterator']

    def consume_shard(self, shard_id: str, process_fn):
        """TODO: Consume records from single shard"""
        shard_iterator = self.get_shard_iterator(shard_id)

        while True:
            try:
                response = self.kinesis.get_records(
                    ShardIterator=shard_iterator,
                    Limit=100
                )

                records = response['Records']
                for record in records:
                    data = json.loads(record['Data'])
                    process_fn(data)

                # Get next iterator
                shard_iterator = response['NextShardIterator']

                # Wait if no records
                if len(records) == 0:
                    time.sleep(1)

            except Exception as e:
                print(f"Error: {e}")
                break

    def consume_all_shards(self, process_fn):
        """TODO: Consume from all shards (multi-threaded)"""
        # List shards
        response = self.kinesis.describe_stream(
            StreamName=self.stream_name
        )
        shards = response['StreamDescription']['Shards']

        # Create thread per shard
        import threading
        threads = []

        for shard in shards:
            shard_id = shard['ShardId']
            thread = threading.Thread(
                target=self.consume_shard,
                args=(shard_id, process_fn)
            )
            thread.start()
            threads.append(thread)

        # Wait for threads
        for thread in threads:
            thread.join()
```

### Part 4: KCL Consumer (60 min)

**Task**: Use Kinesis Client Library for automatic shard management

**File**: `starter/kcl_consumer.py`

```python
from amazon_kclpy import kcl
from amazon_kclpy.v3 import processor

class RecordProcessor(processor.RecordProcessorBase):
    def __init__(self):
        self.checkpoint_counter = 0
        self.checkpoint_freq = 100

    def initialize(self, initialize_input):
        """Called when processor is initialized"""
        self.shard_id = initialize_input.shard_id
        print(f"Initialized processor for {self.shard_id}")

    def process_records(self, process_records_input):
        """TODO: Process batch of records"""
        records = process_records_input.records

        for record in records:
            data = json.loads(record.data)

            # Process record
            self.process_event(data)

            # Checkpoint periodically
            self.checkpoint_counter += 1
            if self.checkpoint_counter % self.checkpoint_freq == 0:
                try:
                    process_records_input.checkpointer.checkpoint()
                except Exception as e:
                    print(f"Checkpoint failed: {e}")

    def process_event(self, event: dict):
        """Process single event"""
        print(f"Processing: {event['event_id']}")

    def lease_lost(self, lease_lost_input):
        """Called when shard lease is lost"""
        print("Lease lost")

    def shard_ended(self, shard_ended_input):
        """Called when shard is closed"""
        shard_ended_input.checkpointer.checkpoint()
        print("Shard ended")

    def shutdown_requested(self, shutdown_requested_input):
        """Called when worker is shutting down"""
        shutdown_requested_input.checkpointer.checkpoint()
        print("Shutdown requested")

if __name__ == '__main__':
    # KCL will call this processor for each record batch
    kcl_process = kcl.KCLProcess(RecordProcessor())
    kcl_process.run()
```

**Properties file**: `kcl.properties`

```properties
applicationName = user-events-processor
streamName = user-events-stream
regionName = us-east-1
initialPositionInStream = TRIM_HORIZON
processingLanguage = python3
executorType = MultiLangDaemon
```

**Run KCL**:
```bash
# Install KCL
pip install amazon_kclpy

# Run processor
amazon_kclpy_helper.py --print_command \
  --properties kcl.properties \
  --python kcl_consumer.py
```

### Part 5: Monitoring (30 min)

**Task**: Monitor stream metrics

```python
import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

def get_stream_metrics(stream_name: str):
    """TODO: Get CloudWatch metrics"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    # Incoming records
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/Kinesis',
        MetricName='IncomingRecords',
        Dimensions=[{'Name': 'StreamName', 'Value': stream_name}],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,  # 5 minutes
        Statistics=['Sum']
    )

    print(f"Incoming records: {response['Datapoints']}")

    # Get other metrics: IncomingBytes, GetRecords.Latency, etc.
```

### Part 6: Scaling (30 min)

**Task**: Dynamically scale shards

```python
def scale_stream(stream_name: str, target_shard_count: int):
    """TODO: Update shard count"""
    kinesis = boto3.client('kinesis')

    # Update stream mode to PROVISIONED
    kinesis.update_stream_mode(
        StreamARN=f'arn:aws:kinesis:us-east-1:123456789:stream/{stream_name}',
        StreamModeDetails={'StreamMode': 'PROVISIONED'}
    )

    # Update shard count
    kinesis.update_shard_count(
        StreamName=stream_name,
        TargetShardCount=target_shard_count,
        ScalingType='UNIFORM_SCALING'
    )

    print(f"Scaling to {target_shard_count} shards")

# Auto-scaling based on metrics
def auto_scale(stream_name: str, threshold_mb_per_sec: float = 0.8):
    """Scale up if approaching throughput limit"""
    # Get current throughput
    # If > threshold, scale up
    pass
```

---

## ✅ Validation

**Run tests**:
```bash
pytest test_kinesis.py -v
```

**Tests cover**:
- ✅ Stream creation
- ✅ Producer sends records
- ✅ Consumer receives records
- ✅ Batch sending works
- ✅ KCL checkpointing

---

## 💰 Cost Optimization

1. **On-Demand vs Provisioned**:
   - On-demand: Pay per GB ingested/retrieved
   - Provisioned: Pay per shard-hour ($0.015/hour)

2. **Shard Optimization**:
   - 1 shard = 1 MB/s in, 2 MB/s out
   - Monitor utilization, scale as needed

3. **Retention**:
   - Default 24 hours (included)
   - Extended retention costs extra

---

## 🔑 Key Learnings

1. **Managed Service**: No infrastructure management
2. **Shard-based Scaling**: Add shards for more throughput
3. **KCL Benefits**: Automatic shard assignment, checkpointing
4. **Comparison**: Kafka offers higher throughput, Kinesis easier to manage

---

## 🚀 Next Steps

- ✅ Exercise 05: Apache Flink processing
- ✅ Integrate with Lambda for serverless processing
- ✅ Compare Kinesis vs Kafka performance
