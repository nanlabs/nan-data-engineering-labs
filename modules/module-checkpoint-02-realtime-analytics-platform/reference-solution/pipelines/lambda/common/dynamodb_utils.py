"""
Common DynamoDB utilities for Lambda processors.

Provides shared functions for interacting with DynamoDB tables.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_dynamodb_client(region_name: str = 'us-east-1'):
    """
    Create and return a DynamoDB client.

    Args:
        region_name: AWS region name

    Returns:
        boto3 DynamoDB client
    """
    return boto3.client('dynamodb', region_name=region_name)


def get_dynamodb_resource(region_name: str = 'us-east-1'):
    """
    Create and return a DynamoDB resource.

    Args:
        region_name: AWS region name

    Returns:
        boto3 DynamoDB resource
    """
    return boto3.resource('dynamodb', region_name=region_name)


def python_obj_to_dynamo_obj(python_obj: Any) -> Any:
    """
    Convert Python objects to DynamoDB compatible objects.

    Handles conversion of floats to Decimal for DynamoDB compatibility.
    """
    if isinstance(python_obj, float):
        return Decimal(str(python_obj))
    elif isinstance(python_obj, dict):
        return {k: python_obj_to_dynamo_obj(v) for k, v in python_obj.items()}
    elif isinstance(python_obj, list):
        return [python_obj_to_dynamo_obj(v) for v in python_obj]
    return python_obj


def dynamo_obj_to_python_obj(dynamo_obj: Any) -> Any:
    """
    Convert DynamoDB objects to Python objects.

    Handles conversion of Decimal to float.
    """
    if isinstance(dynamo_obj, Decimal):
        return float(dynamo_obj)
    elif isinstance(dynamo_obj, dict):
        return {k: dynamo_obj_to_python_obj(v) for k, v in dynamo_obj.items()}
    elif isinstance(dynamo_obj, list):
        return [dynamo_obj_to_python_obj(v) for v in dynamo_obj]
    return dynamo_obj


def put_item(
    table_name: str,
    item: Dict[str, Any],
    region_name: str = 'us-east-1',
    condition_expression: Optional[str] = None
) -> bool:
    """
    Put an item into DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        item: Item to put
        region_name: AWS region
        condition_expression: Optional condition expression

    Returns:
        True if successful, False otherwise
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        item = python_obj_to_dynamo_obj(item)

        kwargs = {'Item': item}
        if condition_expression:
            kwargs['ConditionExpression'] = condition_expression

        table.put_item(**kwargs)
        logger.debug(f"Put item to {table_name}: {item.get('id', 'unknown')}")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Conditional check failed for item: {item}")
            return False
        else:
            logger.error(f"Error putting item to {table_name}: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error putting item to {table_name}: {e}")
        raise


def update_item(
    table_name: str,
    key: Dict[str, Any],
    update_expression: str,
    expression_attribute_values: Dict[str, Any],
    expression_attribute_names: Optional[Dict[str, str]] = None,
    region_name: str = 'us-east-1',
    condition_expression: Optional[str] = None
) -> bool:
    """
    Update an item in DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of item to update
        update_expression: Update expression
        expression_attribute_values: Expression attribute values
        expression_attribute_names: Expression attribute names (optional)
        region_name: AWS region
        condition_expression: Optional condition expression

    Returns:
        True if successful, False otherwise
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        key = python_obj_to_dynamo_obj(key)
        expression_attribute_values = python_obj_to_dynamo_obj(expression_attribute_values)

        kwargs = {
            'Key': key,
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_attribute_values,
        }

        if expression_attribute_names:
            kwargs['ExpressionAttributeNames'] = expression_attribute_names

        if condition_expression:
            kwargs['ConditionExpression'] = condition_expression

        table.update_item(**kwargs)
        logger.debug(f"Updated item in {table_name}: {key}")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Conditional check failed for key: {key}")
            return False
        else:
            logger.error(f"Error updating item in {table_name}: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error updating item in {table_name}: {e}")
        raise


def get_item(
    table_name: str,
    key: Dict[str, Any],
    region_name: str = 'us-east-1'
) -> Optional[Dict[str, Any]]:
    """
    Get an item from DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of item to get
        region_name: AWS region

    Returns:
        Item if found, None otherwise
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        key = python_obj_to_dynamo_obj(key)

        response = table.get_item(Key=key)

        if 'Item' in response:
            item = dynamo_obj_to_python_obj(response['Item'])
            logger.debug(f"Got item from {table_name}: {key}")
            return item
        else:
            logger.debug(f"Item not found in {table_name}: {key}")
            return None

    except Exception as e:
        logger.error(f"Error getting item from {table_name}: {e}")
        raise


def query_table(
    table_name: str,
    key_condition_expression,
    filter_expression=None,
    index_name: Optional[str] = None,
    region_name: str = 'us-east-1',
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query a DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        key_condition_expression: Key condition expression
        filter_expression: Optional filter expression
        index_name: Optional index name for GSI/LSI
        region_name: AWS region
        limit: Maximum number of items to return

    Returns:
        List of items matching the query
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        kwargs = {
            'KeyConditionExpression': key_condition_expression,
        }

        if filter_expression:
            kwargs['FilterExpression'] = filter_expression

        if index_name:
            kwargs['IndexName'] = index_name

        if limit:
            kwargs['Limit'] = limit

        response = table.query(**kwargs)

        items = [dynamo_obj_to_python_obj(item) for item in response.get('Items', [])]
        logger.debug(f"Queried {table_name}, found {len(items)} items")

        return items

    except Exception as e:
        logger.error(f"Error querying {table_name}: {e}")
        raise


def batch_write(
    table_name: str,
    items: List[Dict[str, Any]],
    region_name: str = 'us-east-1'
) -> Dict[str, int]:
    """
    Batch write items to DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        items: List of items to write
        region_name: AWS region

    Returns:
        Dictionary with success/failure counts
    """
    if not items:
        return {'success': 0, 'failed': 0}

    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        items = [python_obj_to_dynamo_obj(item) for item in items]

        success_count = 0
        failed_count = 0

        # DynamoDB batch write limit is 25 items
        batch_size = 25

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            with table.batch_writer() as writer:
                for item in batch:
                    try:
                        writer.put_item(Item=item)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error writing item: {e}")
                        failed_count += 1

        logger.info(f"Batch write to {table_name}: {success_count} succeeded, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}

    except Exception as e:
        logger.error(f"Error in batch write to {table_name}: {e}")
        raise


def delete_item(
    table_name: str,
    key: Dict[str, Any],
    region_name: str = 'us-east-1',
    condition_expression: Optional[str] = None
) -> bool:
    """
    Delete an item from DynamoDB table.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of item to delete
        region_name: AWS region
        condition_expression: Optional condition expression

    Returns:
        True if successful, False otherwise
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        key = python_obj_to_dynamo_obj(key)

        kwargs = {'Key': key}
        if condition_expression:
            kwargs['ConditionExpression'] = condition_expression

        table.delete_item(**kwargs)
        logger.debug(f"Deleted item from {table_name}: {key}")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Conditional check failed for delete: {key}")
            return False
        else:
            logger.error(f"Error deleting item from {table_name}: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error deleting item from {table_name}: {e}")
        raise


def atomic_counter_increment(
    table_name: str,
    key: Dict[str, Any],
    counter_attribute: str,
    increment_value: int = 1,
    region_name: str = 'us-east-1'
) -> int:
    """
    Atomically increment a counter in DynamoDB.

    Args:
        table_name: Name of the DynamoDB table
        key: Primary key of item
        counter_attribute: Name of counter attribute
        increment_value: Value to increment by
        region_name: AWS region

    Returns:
        New counter value
    """
    try:
        dynamodb = get_dynamodb_resource(region_name)
        table = dynamodb.Table(table_name)

        # Convert floats to Decimal
        key = python_obj_to_dynamo_obj(key)
        increment_value = Decimal(str(increment_value))

        response = table.update_item(
            Key=key,
            UpdateExpression=f'ADD {counter_attribute} :val',
            ExpressionAttributeValues={':val': increment_value},
            ReturnValues='UPDATED_NEW'
        )

        new_value = response['Attributes'][counter_attribute]
        logger.debug(f"Incremented {counter_attribute} in {table_name}: {new_value}")
        return int(new_value)

    except Exception as e:
        logger.error(f"Error incrementing counter in {table_name}: {e}")
        raise
