# Exercise 04: REST API con Lambda y API Gateway

## 📋 Información General

- **Level**: Intermedio
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercises 01-03 completeds
  - Conocimiento básico de REST APIs
  - DynamoDB fundamentals

## 🎯 Objectives de Aprendizaje

1. Crear REST API completa con API Gateway
2. Implementar CRUD operations con Lambda + DynamoDB
3. Configurar authentication (API Key, Cognito)
4. Implementar rate limiting y request validation
5. Manejo de CORS
6. API documentation con OpenAPI/Swagger

---

## 📚 Context

Construirás una **User Management API** serverless con:
- CRUD completo de usuarios
- Autenticación con múltiples métodos
- Validation de requests
- Rate limiting por cliente
- Documentación automática

**Arquitectura**:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ▼
┌────────────────────────────────────┐
│  Amazon API Gateway                │
│  - API Key validation              │
│  - Request validation              │
│  - Rate limiting (1000 req/day)    │
│  - CORS                            │
└────────┬───────────────────────────┘
         │
    ┌────┴─────┬──────┬───────┬─────────┐
    ▼          ▼      ▼       ▼         ▼
┌────────┐ ┌────┐ ┌────┐ ┌─────┐ ┌──────┐
│Lambda  │ │GET │ │POST│ │PUT  │ │DELETE│
│Router  │ │    │ │    │ │     │ │      │
└────┬───┘ └────┘ └────┘ └─────┘ └──────┘
     │
     ▼
┌──────────────────┐
│  DynamoDB Table   │
│  users            │
└──────────────────┘
```

---

## 🔧 Parte 1: API Handler

### 1.1 Lambda Handler Principal

**`src/api_handler.py`**:

```python
"""
REST API Handler para User Management
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import boto3
from boto3.dynamodb.conditions import Key
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Router principal para todos los endpoints
    """

    logger.info(json.dumps({
        'event': 'api_request',
        'method': event['httpMethod'],
        'path': event['path'],
        'request_id': context.aws_request_id
    }))

    # Router
    method = event['httpMethod']
    path = event['path']

    try:
        if method == 'GET' and path == '/users':
            return list_users(event)
        elif method == 'GET' and path.startswith('/users/'):
            return get_user(event)
        elif method == 'POST' and path == '/users':
            return create_user(event)
        elif method == 'PUT' and path.startswith('/users/'):
            return update_user(event)
        elif method == 'DELETE' and path.startswith('/users/'):
            return delete_user(event)
        else:
            return response(404, {'error': 'Endpoint not found'})

    except ValueError as e:
        return response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Internal error: {e}")
        return response(500, {'error': 'Internal server error'})


def list_users(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /users - List all users with pagination
    Query params: limit, next_token
    """

    # Parámetros de query
    query_params = event.get('queryStringParameters') or {}
    limit = int(query_params.get('limit', 20))

    # Scan con limit
    scan_kwargs = {'Limit': limit}

    # Pagination
    if 'next_token' in query_params:
        scan_kwargs['ExclusiveStartKey'] = json.loads(query_params['next_token'])

    result = table.scan(**scan_kwargs)

    response_body = {
        'users': result['Items'],
        'count': len(result['Items'])
    }

    # Next page token
    if 'LastEvaluatedKey' in result:
        response_body['next_token'] = json.dumps(result['LastEvaluatedKey'])

    return response(200, response_body)


def get_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    GET /users/{id} - Get user by ID
    """

    user_id = event['pathParameters']['id']

    result = table.get_item(Key={'user_id': user_id})

    if 'Item' not in result:
        return response(404, {'error': 'User not found'})

    return response(200, result['Item'])


def create_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST /users - Create new user
    Body: {email, name, age (optional)}
    """

    body = json.loads(event['body'])

    # Validation
    validate_user_input(body, required=['email', 'name'])

    # Check if email exists
    existing = table.scan(
        FilterExpression='email = :email',
        ExpressionAttributeValues={':email': body['email']}
    )

    if existing['Items']:
        return response(409, {'error': 'User with this email already exists'})

    # Create user
    user = {
        'user_id': str(uuid.uuid4()),
        'email': body['email'],
        'name': body['name'],
        'age': body.get('age'),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    table.put_item(Item=user)

    logger.info(f"User created: {user['user_id']}")

    return response(201, user)


def update_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    PUT /users/{id} - Update user
    Body: {name, age}
    """

    user_id = event['pathParameters']['id']
    body = json.loads(event['body'])

    # Validation
    validate_user_input(body, required=[])

    # Check if user exists
    existing = table.get_item(Key={'user_id': user_id})
    if 'Item' not in existing:
        return response(404, {'error': 'User not found'})

    # Build update expression
    update_expr = "SET updated_at = :updated_at"
    expr_values = {':updated_at': datetime.utcnow().isoformat()}

    if 'name' in body:
        update_expr += ", #name = :name"
        expr_values[':name'] = body['name']

    if 'age' in body:
        update_expr += ", age = :age"
        expr_values[':age'] = body['age']

    # Update
    result = table.update_item(
        Key={'user_id': user_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames={'#name': 'name'},
        ExpressionAttributeValues=expr_values,
        ReturnValues='ALL_NEW'
    )

    logger.info(f"User updated: {user_id}")

    return response(200, result['Attributes'])


def delete_user(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    DELETE /users/{id} - Delete user
    """

    user_id = event['pathParameters']['id']

    # Check if exists
    existing = table.get_item(Key={'user_id': user_id})
    if 'Item' not in existing:
        return response(404, {'error': 'User not found'})

    # Delete
    table.delete_item(Key={'user_id': user_id})

    logger.info(f"User deleted: {user_id}")

    return response(204, {})


def validate_user_input(data: Dict[str, Any], required: list = []):
    """Validate user input"""

    # Required fields
    for field in required:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")

    # Email format
    if 'email' in data:
        if '@' not in data['email']:
            raise ValueError("Invalid email format")

    # Age range
    if 'age' in data:
        if not isinstance(data['age'], int) or data['age'] < 0 or data['age'] > 150:
            raise ValueError("Age must be between 0 and 150")


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create HTTP response
    """

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-API-Key'
        },
        'body': json.dumps(body, default=str)
    }
```

---

## 🔧 Parte 2: Infrastructure

### 2.1 Terraform Configuration

**`infrastructure/main.tf`**:

```hcl
# DynamoDB Table
resource "aws_dynamodb_table" "users" {
  name           = "users-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  # Global Secondary Index para buscar por email
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  attribute {
    name = "email"
    type = "S"
  }

  tags = {
    Environment = var.environment
  }
}

# Lambda Function
resource "aws_lambda_function" "api" {
  filename      = "lambda.zip"
  function_name = "user-api-${var.environment}"
  role          = aws_iam_role.lambda.arn
  handler       = "api_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.users.name
    }
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "user_api" {
  name        = "user-api-${var.environment}"
  description = "User Management API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway Resource: /users
resource "aws_api_gateway_resource" "users" {
  rest_api_id = aws_api_gateway_rest_api.user_api.id
  parent_id   = aws_api_gateway_rest_api.user_api.root_resource_id
  path_part   = "users"
}

# API Gateway Resource: /users/{id}
resource "aws_api_gateway_resource" "user_id" {
  rest_api_id = aws_api_gateway_rest_api.user_api.id
  parent_id   = aws_api_gateway_resource.users.id
  path_part   = "{id}"
}

# Method: GET /users
resource "aws_api_gateway_method" "list_users" {
  rest_api_id   = aws_api_gateway_rest_api.user_api.id
  resource_id   = aws_api_gateway_resource.users.id
  http_method   = "GET"
  authorization = "API_KEY"
  api_key_required = true
}

# Integration: GET /users → Lambda
resource "aws_api_gateway_integration" "list_users" {
  rest_api_id = aws_api_gateway_rest_api.user_api.id
  resource_id = aws_api_gateway_resource.users.id
  http_method = aws_api_gateway_method.list_users.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# Method: POST /users (similar setup)
# ... (repeat for other methods)

# API Gateway Deployment
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.user_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.list_users.id,
      aws_api_gateway_integration.list_users.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "api" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.user_api.id
  stage_name    = var.environment
}

# Usage Plan (Rate Limiting)
resource "aws_api_gateway_usage_plan" "basic" {
  name = "basic-plan-${var.environment}"

  api_stages {
    api_id = aws_api_gateway_rest_api.user_api.id
    stage  = aws_api_gateway_stage.api.stage_name
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }
}

# API Key
resource "aws_api_gateway_api_key" "client_key" {
  name = "client-api-key-${var.environment}"
}

resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.client_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.basic.id
}

# Lambda Permission
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.user_api.execution_arn}/*/*"
}

# Outputs
output "api_url" {
  value = "${aws_api_gateway_stage.api.invoke_url}/users"
}

output "api_key" {
  value     = aws_api_gateway_api_key.client_key.value
  sensitive = true
}
```

---

## 🧪 Parte 3: Testing

### 3.1 Test con curl

```bash
# Get API URL and Key
API_URL=$(cd infrastructure && terraform output -raw api_url)
API_KEY=$(cd infrastructure && terraform output -raw api_key)

# CREATE user
curl -X POST "$API_URL" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "name": "Alice Johnson",
    "age": 28
  }'

# LIST users
curl -X GET "$API_URL" \
  -H "X-API-Key: $API_KEY"

# GET user by ID
USER_ID="<user-id-from-create>"
curl -X GET "$API_URL/$USER_ID" \
  -H "X-API-Key: $API_KEY"

# UPDATE user
curl -X PUT "$API_URL/$USER_ID" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Smith",
    "age": 29
  }'

# DELETE user
curl -X DELETE "$API_URL/$USER_ID" \
  -H "X-API-Key: $API_KEY"
```

### 3.2 Integration Tests

**`tests/test_api.py`**:

```python
import pytest
import requests
import os

API_URL = os.environ['API_URL']
API_KEY = os.environ['API_KEY']

HEADERS = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def test_create_user():
    response = requests.post(
        API_URL,
        json={
            'email': 'test@example.com',
            'name': 'Test User',
            'age': 25
        },
        headers=HEADERS
    )

    assert response.status_code == 201
    data = response.json()
    assert 'user_id' in data
    assert data['email'] == 'test@example.com'

    return data['user_id']

def test_get_user():
    user_id = test_create_user()

    response = requests.get(f"{API_URL}/{user_id}", headers=HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data['user_id'] == user_id

def test_rate_limiting():
    # Hacer 150 requests (debería fallar después de 100)
    for i in range(150):
        response = requests.get(API_URL, headers=HEADERS)
        if response.status_code == 429:
            print(f"Rate limited after {i} requests")
            break

    assert response.status_code == 429
```

---

## ✅ Checklist

- [ ] REST API deployed
- [ ] All CRUD operations working
- [ ] API Key authentication
- [ ] Rate limiting active
- [ ] Request validation
- [ ] CORS configured
- [ ] Error handling
- [ ] Integration tests passing

**Siguiente**: [Exercise 05 - SQS Messaging](../05-sqs-messaging/)
