"""
Module 15: Real-Time Analytics - Infrastructure Validation Tests
Tests that infrastructure is properly set up and running
"""

import pytest
import boto3
import requests
import docker
import time


@pytest.fixture(scope="module")
def aws_config():
    """AWS configuration for LocalStack"""
    return {
        'endpoint_url': 'http://localhost:4566',
        'region_name': 'us-east-1',
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test'
    }


@pytest.fixture(scope="module")
def kinesis_client(aws_config):
    """Kinesis client for LocalStack"""
    return boto3.client('kinesis', **aws_config)


@pytest.fixture(scope="module")
def dynamodb_client(aws_config):
    """DynamoDB client for LocalStack"""
    return boto3.client('dynamodb', **aws_config)


@pytest.fixture(scope="module")
def s3_client(aws_config):
    """S3 client for LocalStack"""
    return boto3.client('s3', **aws_config)


@pytest.fixture(scope="module")
def docker_client():
    """Docker client for container checks"""
    return docker.from_env()


class TestDockerInfrastructure:
    """Test Docker containers are running"""

    def test_localstack_running(self, docker_client):
        """Test LocalStack container is running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-localstack'}
        )
        assert len(containers) == 1, "LocalStack container not running"
        assert containers[0].status == 'running'

    def test_flink_jobmanager_running(self, docker_client):
        """Test Flink Job Manager is running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-flink-jobmanager'}
        )
        assert len(containers) == 1, "Flink Job Manager not running"
        assert containers[0].status == 'running'

    def test_flink_taskmanagers_running(self, docker_client):
        """Test Flink Task Managers are running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-flink-taskmanager'}
        )
        assert len(containers) >= 2, "Expected at least 2 Flink Task Managers"
        for container in containers:
            assert container.status == 'running'

    def test_postgres_running(self, docker_client):
        """Test PostgreSQL is running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-postgres'}
        )
        assert len(containers) == 1, "PostgreSQL container not running"
        assert containers[0].status == 'running'

    def test_kafka_running(self, docker_client):
        """Test Kafka is running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-kafka'}
        )
        assert len(containers) == 1, "Kafka container not running"
        assert containers[0].status == 'running'

    def test_grafana_running(self, docker_client):
        """Test Grafana is running"""
        containers = docker_client.containers.list(
            filters={'name': 'module15-grafana'}
        )
        assert len(containers) == 1, "Grafana container not running"
        assert containers[0].status == 'running'


class TestLocalStackServices:
    """Test LocalStack AWS services are accessible"""

    def test_localstack_health(self):
        """Test LocalStack health endpoint"""
        response = requests.get('http://localhost:4566/_localstack/health')
        assert response.status_code == 200

        health = response.json()
        assert 'services' in health
        assert health['services']['kinesis'] == 'available'
        assert health['services']['dynamodb'] == 'available'
        assert health['services']['s3'] == 'available'

    def test_kinesis_service_available(self, kinesis_client):
        """Test Kinesis service is responding"""
        try:
            response = kinesis_client.list_streams()
            assert 'StreamNames' in response
        except Exception as e:
            pytest.fail(f"Kinesis service not available: {e}")

    def test_dynamodb_service_available(self, dynamodb_client):
        """Test DynamoDB service is responding"""
        try:
            response = dynamodb_client.list_tables()
            assert 'TableNames' in response
        except Exception as e:
            pytest.fail(f"DynamoDB service not available: {e}")

    def test_s3_service_available(self, s3_client):
        """Test S3 service is responding"""
        try:
            response = s3_client.list_buckets()
            assert 'Buckets' in response
        except Exception as e:
            pytest.fail(f"S3 service not available: {e}")


class TestKinesisStreams:
    """Test Kinesis streams are created correctly"""

    def test_events_stream_exists(self, kinesis_client):
        """Test events-stream exists"""
        response = kinesis_client.describe_stream(StreamName='events-stream')
        assert response['StreamDescription']['StreamStatus'] in ['ACTIVE', 'UPDATING']

    def test_events_stream_shard_count(self, kinesis_client):
        """Test events-stream has correct number of shards"""
        response = kinesis_client.describe_stream(StreamName='events-stream')
        shards = response['StreamDescription']['Shards']
        assert len(shards) == 4, f"Expected 4 shards, got {len(shards)}"

    def test_aggregated_stream_exists(self, kinesis_client):
        """Test aggregated-stream exists"""
        response = kinesis_client.describe_stream(StreamName='aggregated-stream')
        assert response['StreamDescription']['StreamStatus'] in ['ACTIVE', 'UPDATING']

    def test_fraud_alerts_stream_exists(self, kinesis_client):
        """Test fraud-alerts-stream exists"""
        response = kinesis_client.describe_stream(StreamName='fraud-alerts-stream')
        assert response['StreamDescription']['StreamStatus'] in ['ACTIVE', 'UPDATING']

    def test_dlq_stream_exists(self, kinesis_client):
        """Test DLQ stream exists"""
        response = kinesis_client.describe_stream(StreamName='dlq-stream')
        assert response['StreamDescription']['StreamStatus'] in ['ACTIVE', 'UPDATING']

    def test_can_write_to_stream(self, kinesis_client):
        """Test writing data to Kinesis stream"""
        import json

        test_data = {
            'event_type': 'test',
            'timestamp': '2024-03-08T10:00:00Z',
            'test_id': 'pytest_infrastructure_test'
        }

        response = kinesis_client.put_record(
            StreamName='events-stream',
            Data=json.dumps(test_data).encode('utf-8'),
            PartitionKey='test'
        )

        assert 'SequenceNumber' in response
        assert 'ShardId' in response


class TestDynamoDBTables:
    """Test DynamoDB tables are created correctly"""

    def test_realtime_aggregates_table_exists(self, dynamodb_client):
        """Test realtime-aggregates table exists"""
        response = dynamodb_client.describe_table(TableName='realtime-aggregates')
        assert response['Table']['TableStatus'] == 'ACTIVE'

    def test_user_sessions_table_exists(self, dynamodb_client):
        """Test user-sessions table exists"""
        response = dynamodb_client.describe_table(TableName='user-sessions')
        assert response['Table']['TableStatus'] == 'ACTIVE'

    def test_fraud_detections_table_exists(self, dynamodb_client):
        """Test fraud-detections table exists"""
        response = dynamodb_client.describe_table(TableName='fraud-detections')
        assert response['Table']['TableStatus'] == 'ACTIVE'

    def test_can_write_to_dynamodb(self, dynamodb_client):
        """Test writing data to DynamoDB"""
        from datetime import datetime

        response = dynamodb_client.put_item(
            TableName='realtime-aggregates',
            Item={
                'metric_name': {'S': 'pytest_test'},
                'timestamp': {'N': str(int(datetime.now().timestamp()))},
                'value': {'N': '42.0'},
                'metadata': {'S': 'test_data'}
            }
        )

        assert response['ResponseMetadata']['HTTPStatusCode'] == 200


class TestS3Buckets:
    """Test S3 buckets are created correctly"""

    def test_checkpoints_bucket_exists(self, s3_client):
        """Test analytics-checkpoints bucket exists"""
        response = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in response['Buckets']]
        assert 'analytics-checkpoints' in bucket_names

    def test_savepoints_bucket_exists(self, s3_client):
        """Test analytics-savepoints bucket exists"""
        response = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in response['Buckets']]
        assert 'analytics-savepoints' in bucket_names

    def test_data_lake_bucket_exists(self, s3_client):
        """Test analytics-data-lake bucket exists"""
        response = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in response['Buckets']]
        assert 'analytics-data-lake' in bucket_names

    def test_can_write_to_s3(self, s3_client):
        """Test writing data to S3"""
        test_content = b"pytest infrastructure test"

        s3_client.put_object(
            Bucket='analytics-checkpoints',
            Key='test/pytest_test.txt',
            Body=test_content
        )

        # Verify it was written
        response = s3_client.get_object(
            Bucket='analytics-checkpoints',
            Key='test/pytest_test.txt'
        )

        assert response['Body'].read() == test_content


class TestFlinkCluster:
    """Test Flink cluster is properly configured"""

    def test_flink_rest_api_accessible(self):
        """Test Flink REST API is accessible"""
        response = requests.get('http://localhost:8081/overview')
        assert response.status_code == 200

        overview = response.json()
        assert 'taskmanagers' in overview
        assert 'slots-total' in overview

    def test_flink_taskmanagers_registered(self):
        """Test task managers are registered with job manager"""
        response = requests.get('http://localhost:8081/taskmanagers')
        assert response.status_code == 200

        data = response.json()
        assert 'taskmanagers' in data
        assert len(data['taskmanagers']) >= 2, "Expected at least 2 task managers"

    def test_flink_has_available_slots(self):
        """Test Flink has available task slots"""
        response = requests.get('http://localhost:8081/overview')
        overview = response.json()

        assert overview['slots-total'] >= 8, "Expected at least 8 total slots"
        assert overview['slots-available'] > 0, "No available slots"

    def test_flink_configuration(self):
        """Test Flink configuration"""
        response = requests.get('http://localhost:8081/config')
        assert response.status_code == 200

        config = response.json()
        # Check checkpointing is enabled
        assert any('checkpoint' in item.get('key', '').lower()
                  for item in config)


class TestGrafana:
    """Test Grafana is accessible"""

    def test_grafana_accessible(self):
        """Test Grafana web UI is accessible"""
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get('http://localhost:3000/api/health')
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                if attempt < max_attempts - 1:
                    time.sleep(2)
                else:
                    raise

        assert response.status_code == 200
        health = response.json()
        assert health['database'] == 'ok'


class TestEndToEndConnectivity:
    """Test end-to-end data flow"""

    def test_kinesis_to_flink_connectivity(self, kinesis_client):
        """Test data can flow from Kinesis to Flink"""
        import json
        from datetime import datetime

        # Send a test event
        test_event = {
            'event_type': 'connectivity_test',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'test_id': f'pytest_{int(time.time())}'
        }

        response = kinesis_client.put_record(
            StreamName='events-stream',
            Data=json.dumps(test_event).encode('utf-8'),
            PartitionKey='test'
        )

        assert 'SequenceNumber' in response

        # Note: Full Flink job testing would require deploying a job
        # This just verifies Kinesis is writable

    def test_data_persistence(self, dynamodb_client, s3_client):
        """Test data can be persisted to DynamoDB and S3"""
        from datetime import datetime
        import json

        timestamp = int(datetime.now().timestamp())

        # Write to DynamoDB
        dynamodb_client.put_item(
            TableName='realtime-aggregates',
            Item={
                'metric_name': {'S': 'e2e_test'},
                'timestamp': {'N': str(timestamp)},
                'value': {'N': '99.9'}
            }
        )

        # Write to S3
        s3_client.put_object(
            Bucket='analytics-data-lake',
            Key=f'tests/e2e_{timestamp}.json',
            Body=json.dumps({'test': 'e2e', 'timestamp': timestamp}).encode('utf-8')
        )

        # Verify reads
        dynamo_item = dynamodb_client.get_item(
            TableName='realtime-aggregates',
            Key={
                'metric_name': {'S': 'e2e_test'},
                'timestamp': {'N': str(timestamp)}
            }
        )
        assert 'Item' in dynamo_item

        s3_object = s3_client.get_object(
            Bucket='analytics-data-lake',
            Key=f'tests/e2e_{timestamp}.json'
        )
        assert s3_object['Body'].read()


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    """Setup before all tests and cleanup after"""
    print("\n=== Module 15 Infrastructure Validation ===\n")
    yield
    print("\n=== Validation Complete ===\n")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
