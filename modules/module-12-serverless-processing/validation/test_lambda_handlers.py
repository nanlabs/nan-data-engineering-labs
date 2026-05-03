"""
Unit tests for Lambda handlers
"""
import pytest
import json

def test_csv_processor_handler(s3_client, test_bucket):
    """Test CSV processing Lambda"""
    # Arrange
    s3_client.put_object(
        Bucket=test_bucket,
        Key='input/data.csv',
        Body='name,age\nJohn,30\nJane,25'
    )

    event = {
        'Records': [{
            's3': {
                'bucket': {'name': test_bucket},
                'object': {'key': 'input/data.csv'}
            }
        }]
    }

    # Act
    # Import here to ensure moto mocks are active
    from exercises.ex01.src.csv_processor import lambda_handler
    result = lambda_handler(event, None)

    # Assert
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert body['rows_processed'] == 2
    assert body['columns'] == ['name', 'age']


def test_api_handler_create(dynamodb_client, test_table, monkeypatch):
    """Test API Gateway POST handler"""
    monkeypatch.setenv('TABLE_NAME', test_table)

    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'name': 'John Doe',
            'email': 'john@example.com'
        })
    }

    from exercises.ex04.src.api_handler import lambda_handler
    result = lambda_handler(event, None)

    assert result['statusCode'] == 201
    body = json.loads(result['body'])
    assert 'id' in body
    assert body['name'] == 'John Doe'


def test_sqs_processor_batch(sqs_client, test_queue, monkeypatch):
    """Test SQS batch processing"""
    # Send messages
    for i in range(5):
        sqs_client.send_message(
            QueueUrl=test_queue,
            MessageBody=json.dumps({'order_id': f'order-{i}'})
        )

    # Receive and process
    messages = sqs_client.receive_message(
        QueueUrl=test_queue,
        MaxNumberOfMessages=10
    )

    assert 'Messages' in messages
    assert len(messages['Messages']) == 5


def test_validation_error_handling():
    """Test input validation"""
    from exercises.ex06.src.ingestion_api import validate_log_event

    # Missing required field
    with pytest.raises(ValueError, match="Missing required field"):
        validate_log_event({'app_id': 'test'})

    # Invalid level
    with pytest.raises(ValueError, match="Invalid level"):
        validate_log_event({
            'app_id': 'test',
            'level': 'INVALID',
            'message': 'test',
            'timestamp': '2024-01-01T00:00:00Z'
        })

    # Valid event
    try:
        validate_log_event({
            'app_id': 'test',
            'level': 'INFO',
            'message': 'test',
            'timestamp': '2024-01-01T00:00:00Z'
        })
    except ValueError:
        pytest.fail("Valid event raised ValueError")
