# Exercise 05: ML Model Scoring in Streams

## Overview
Integrate machine learning models with Apache Flink for real-time fraud scoring using SageMaker endpoints, featuring async I/O, feature engineering, and online learning.

**Difficulty**: ⭐⭐⭐⭐ Expert
**Duration**: ~3 hours
**Prerequisites**: Exercise 04, Basic ML knowledge, SageMaker familiarity

## Learning Objectives

- Train and deploy fraud detection models to SageMaker
- Implement feature engineering in Flink streams
- Use AsyncDataStream for non-blocking model invocation
- Handle model timeouts and fallback strategies
- Measure and optimize inference latency
- Implement online learning feedback loops

## Key Concepts

- **Feature Engineering**: Transform raw events into ML features
- **Async I/O**: Non-blocking external service calls
- **Online Learning**: Update models with streaming data
- **A/B Testing**: Compare model versions in production
- **Circuit Breaker**: Prevent cascade failures

## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│  Kinesis Stream  │────>│   Flink Pipeline   │────>│  SageMaker       │
│  (transactions)  │     │  Feature Engineer  │<────│  Endpoint        │
└──────────────────┘     └────────────────────┘     │  (Fraud Model)   │
                                   │                 └──────────────────┘
                                   │
                                   v
                         ┌────────────────┐
                         │   Scored        │
                         │   Transactions  │
                         │   (DynamoDB)    │
                         └────────────────┘
                                   │
                                   v
                         ┌────────────────┐
                         │  Feedback Loop  │
                         │  (Online Learn) │
                         └────────────────┘
```

## Task 1: Train Fraud Model (30 minutes)

Train a simple fraud detection model using scikit-learn.

**File**: `train_model.py`

```python
#!/usr/bin/env python3
"""Train fraud detection model"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import json
from datetime import datetime


def generate_training_data(n_samples=10000):
    """Generate synthetic training data"""

    np.random.seed(42)

    # Normal transactions (90%)
    n_normal = int(n_samples * 0.9)
    normal_data = {
        'amount': np.random.lognormal(3.5, 1.2, n_normal),  # ~$50 avg
        'hour_of_day': np.random.randint(6, 23, n_normal),  # Daytime
        'day_of_week': np.random.randint(0, 7, n_normal),
        'failed_attempts_24h': np.random.poisson(0.1, n_normal),
        'avg_amount_7d': np.random.lognormal(3.5, 0.8, n_normal),
        'country_risk_score': np.random.uniform(0.1, 0.3, n_normal),
        'device_new': np.random.binomial(1, 0.05, n_normal),
        'merchant_reputation': np.random.uniform(0.7, 1.0, n_normal),
        'is_fraud': np.zeros(n_normal)
    }

    # Fraud transactions (10%)
    n_fraud = n_samples - n_normal
    fraud_data = {
        'amount': np.random.lognormal(5.0, 1.5, n_fraud),  # Higher amounts
        'hour_of_day': np.random.choice([0, 1, 2, 3, 22, 23], n_fraud),  # Night
        'day_of_week': np.random.randint(0, 7, n_fraud),
        'failed_attempts_24h': np.random.poisson(3.0, n_fraud),  # More failures
        'avg_amount_7d': np.random.lognormal(3.0, 0.5, n_fraud),  # Lower baseline
        'country_risk_score': np.random.uniform(0.5, 0.9, n_fraud),  # High risk
        'device_new': np.random.binomial(1, 0.4, n_fraud),  # Often new devices
        'merchant_reputation': np.random.uniform(0.3, 0.7, n_fraud),  # Sketchy
        'is_fraud': np.ones(n_fraud)
    }

    # Combine
    df_normal = pd.DataFrame(normal_data)
    df_fraud = pd.DataFrame(fraud_data)
    df = pd.concat([df_normal, df_fraud], ignore_index=True)

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Feature engineering
    df['amount_vs_avg_ratio'] = df['amount'] / (df['avg_amount_7d'] + 1)
    df['is_night'] = ((df['hour_of_day'] <= 4) | (df['hour_of_day'] >= 22)).astype(int)
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['risk_score_composite'] = (
        df['country_risk_score'] * 0.4 +
        df['device_new'] * 0.3 +
        (1 - df['merchant_reputation']) * 0.3
    )

    return df


def train_model(df):
    """Train Random Forest classifier"""

    # Features
    feature_cols = [
        'amount', 'hour_of_day', 'day_of_week', 'failed_attempts_24h',
        'avg_amount_7d', 'country_risk_score', 'device_new',
        'merchant_reputation', 'amount_vs_avg_ratio', 'is_night',
        'is_weekend', 'risk_score_composite'
    ]

    X = df[feature_cols]
    y = df['is_fraud']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Fraud rate: {y.mean():.2%}")

    # Train model
    print("\nTraining Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Evaluate
    print("\n" + "="*50)
    print("MODEL EVALUATION")
    print("="*50)

    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
    print(f"\nCross-validation ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Test set predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print("\nTest Set Performance:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Fraud']))

    print(f"\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  TN: {cm[0,0]:4d}  |  FP: {cm[0,1]:4d}")
    print(f"  FN: {cm[1,0]:4d}  |  TP: {cm[1,1]:4d}")

    # Feature importance
    print("\nTop 10 Feature Importances:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:25s}: {row['importance']:.4f}")

    return model, feature_cols


def save_model(model, feature_cols, output_dir='models'):
    """Save model and metadata"""

    import os
    os.makedirs(output_dir, exist_ok=True)

    # Save sklearn model
    model_path = f"{output_dir}/fraud_model.pkl"
    joblib.dump(model, model_path)
    print(f"\n✓ Model saved: {model_path}")

    # Save feature names
    features_path = f"{output_dir}/feature_names.json"
    with open(features_path, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    print(f"✓ Features saved: {features_path}")

    # Save metadata
    metadata = {
        'model_type': 'RandomForestClassifier',
        'n_features': len(feature_cols),
        'feature_names': feature_cols,
        'trained_at': datetime.utcnow().isoformat(),
        'version': '1.0'
    }

    metadata_path = f"{output_dir}/metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved: {metadata_path}")


if __name__ == '__main__':
    print("="*50)
    print("FRAUD DETECTION MODEL TRAINING")
    print("="*50)

    # Generate data
    print("\nGenerating training data...")
    df = generate_training_data(n_samples=10000)

    # Train
    model, feature_cols = train_model(df)

    # Save
    save_model(model, feature_cols)

    print("\n" + "="*50)
    print("✓ TRAINING COMPLETE")
    print("="*50)
```

## Task 2: Deploy Model to SageMaker (25 minutes)

Create SageMaker endpoint for real-time inference.

**File**: `deploy_model.py`

```python
#!/usr/bin/env python3
"""Deploy model to SageMaker endpoint"""

import boto3
import joblib
import json
import tarfile
import os
from datetime import datetime

sagemaker = boto3.client('sagemaker',
                         endpoint_url='http://localhost:4566',
                         region_name='us-east-1')

s3 = boto3.client('s3',
                 endpoint_url='http://localhost:4566',
                 region_name='us-east-1')


def create_model_artifact():
    """Package model for SageMaker"""

    # Create tar.gz with model
    model_tar = 'model.tar.gz'

    with tarfile.open(model_tar, 'w:gz') as tar:
        tar.add('models/fraud_model.pkl', arcname='fraud_model.pkl')
        tar.add('models/feature_names.json', arcname='feature_names.json')
        tar.add('models/metadata.json', arcname='metadata.json')

    print(f"✓ Model artifact created: {model_tar}")
    return model_tar


def upload_to_s3(model_tar, bucket='ml-models'):
    """Upload model to S3"""

    # Create bucket
    try:
        s3.create_bucket(Bucket=bucket)
        print(f"✓ S3 bucket created: {bucket}")
    except:
        print(f"  S3 bucket exists: {bucket}")

    # Upload model
    key = f"fraud-detection/v1/{model_tar}"
    s3.upload_file(model_tar, bucket, key)

    model_uri = f"s3://{bucket}/{key}"
    print(f"✓ Model uploaded: {model_uri}")

    return model_uri


def create_sagemaker_model(model_uri):
    """Create SageMaker model"""

    model_name = f"fraud-detection-{int(datetime.utcnow().timestamp())}"

    try:
        response = sagemaker.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': '763104351884.dkr.ecr.us-east-1.amazonaws.com/sklearn-inference:0.23-1-cpu-py3',
                'ModelDataUrl': model_uri,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': model_uri
                }
            },
            ExecutionRoleArn='arn:aws:iam::000000000000:role/SageMakerRole'
        )

        print(f"✓ SageMaker model created: {model_name}")
        return model_name

    except Exception as e:
        print(f"✗ Error creating model: {e}")
        return None


def create_endpoint_config(model_name):
    """Create endpoint configuration"""

    config_name = f"{model_name}-config"

    try:
        sagemaker.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[{
                'VariantName': 'AllTraffic',
                'ModelName': model_name,
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.m5.large',
                'InitialVariantWeight': 1.0
            }]
        )

        print(f"✓ Endpoint config created: {config_name}")
        return config_name

    except Exception as e:
        print(f"✗ Error creating config: {e}")
        return None


def create_endpoint(config_name):
    """Create SageMaker endpoint"""

    endpoint_name = 'fraud-detection-endpoint'

    try:
        sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=config_name
        )

        print(f"✓ Endpoint created: {endpoint_name}")
        print(f"  Status: Creating (wait ~5 minutes for 'InService')")

        return endpoint_name

    except Exception as e:
        print(f"✗ Error creating endpoint: {e}")
        return None


def wait_for_endpoint(endpoint_name, timeout=300):
    """Wait for endpoint to be ready"""

    import time

    print(f"\nWaiting for endpoint '{endpoint_name}' to be ready...")

    start_time = time.time()

    while (time.time() - start_time) < timeout:
        try:
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']

            if status == 'InService':
                print(f"✓ Endpoint is ready!")
                return True
            elif status == 'Failed':
                print(f"✗ Endpoint creation failed")
                return False
            else:
                print(f"  Status: {status}...")
                time.sleep(30)

        except Exception as e:
            print(f"  Error checking status: {e}")
            time.sleep(30)

    print(f"✗ Timeout waiting for endpoint")
    return False


def test_endpoint(endpoint_name):
    """Test endpoint with sample data"""

    runtime = boto3.client('sagemaker-runtime',
                          endpoint_url='http://localhost:4566',
                          region_name='us-east-1')

    # Sample features
    test_data = {
        'features': [
            [250.0, 14, 2, 0, 45.0, 0.2, 0, 0.85, 5.56, 0, 0, 0.24],  # Normal
            [1200.0, 2, 5, 4, 50.0, 0.75, 1, 0.45, 24.0, 1, 1, 0.68]  # Fraud
        ]
    }

    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_data)
        )

        result = json.loads(response['Body'].read().decode())

        print("\n" + "="*50)
        print("ENDPOINT TEST")
        print("="*50)
        print("\nPredictions:")
        for i, pred in enumerate(result['predictions']):
            label = "FRAUD" if pred > 0.5 else "NORMAL"
            print(f"  Sample {i+1}: {label} (score: {pred:.4f})")

        print("\n✓ Endpoint test successful")
        return True

    except Exception as e:
        print(f"✗ Endpoint test failed: {e}")
        return False


if __name__ == '__main__':
    print("="*50)
    print("DEPLOYING MODEL TO SAGEMAKER")
    print("="*50)

    # Package model
    print("\n1. Creating model artifact...")
    model_tar = create_model_artifact()

    # Upload to S3
    print("\n2. Uploading to S3...")
    model_uri = upload_to_s3(model_tar)

    # Create SageMaker model
    print("\n3. Creating SageMaker model...")
    model_name = create_sagemaker_model(model_uri)

    if not model_name:
        exit(1)

    # Create endpoint config
    print("\n4. Creating endpoint config...")
    config_name = create_endpoint_config(model_name)

    if not config_name:
        exit(1)

    # Create endpoint
    print("\n5. Creating endpoint...")
    endpoint_name = create_endpoint(config_name)

    if not endpoint_name:
        exit(1)

    # Wait for endpoint (uncomment for real AWS)
    # wait_for_endpoint(endpoint_name)

    # Test endpoint (uncomment after ready)
    # test_endpoint(endpoint_name)

    print("\n" + "="*50)
    print("✓ DEPLOYMENT COMPLETE")
    print("="*50)
    print(f"\nEndpoint Name: {endpoint_name}")
    print(f"Use this endpoint in Flink for real-time scoring")
```

## Task 3: Feature Engineering in Flink (30 minutes)

Calculate ML features from streaming data.

**File**: `feature_engineering.py`

```python
#!/usr/bin/env python3
"""Feature engineering for ML scoring"""

from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor, ListStateDescriptor
from pyflink.common.typeinfo import Types
import json
from datetime import datetime, timedelta
from collections import deque


class FeatureEngineer(KeyedProcessFunction):
    """
    Compute ML features from transaction stream
    """

    def __init__(self):
        self.transaction_history_state = None
        self.failed_attempts_state = None
        self.avg_amount_state = None

    def open(self, runtime_context: RuntimeContext):
        """Initialize state"""

        # Transaction history (last 7 days)
        history_descriptor = ListStateDescriptor(
            "transaction-history",
            Types.TUPLE([Types.DOUBLE(), Types.LONG()])  # (amount, timestamp)
        )
        self.transaction_history_state = runtime_context.get_list_state(history_descriptor)

        # Failed attempts (last 24 hours)
        failed_descriptor = ValueStateDescriptor(
            "failed-attempts",
            Types.LIST(Types.LONG())  # timestamps
        )
        self.failed_attempts_state = runtime_context.get_state(failed_descriptor)

        # Running average
        avg_descriptor = ValueStateDescriptor(
            "avg-amount",
            Types.TUPLE([Types.DOUBLE(), Types.INT()])  # (sum, count)
        )
        self.avg_amount_state = runtime_context.get_state(avg_descriptor)

    def process_element(self, value, ctx):
        """Compute features for each transaction"""

        transaction = json.loads(value)

        amount = float(transaction['amount'])
        timestamp = transaction['transaction_timestamp']
        status = transaction['status']
        country = transaction.get('country', 'US')

        # Get transaction history
        history = list(self.transaction_history_state.get()) or []

        # Clean old transactions (>7 days)
        seven_days_ago = timestamp - (7 * 24 * 3600)
        history = [(amt, ts) for amt, ts in history if ts > seven_days_ago]

        # Get failed attempts
        failed_attempts = self.failed_attempts_state.value() or []

        # Clean old failures (>24 hours)
        one_day_ago = timestamp - (24 * 3600)
        failed_attempts = [ts for ts in failed_attempts if ts > one_day_ago]

        # Update failed attempts
        if status == 'failed':
            failed_attempts.append(timestamp)
            self.failed_attempts_state.update(failed_attempts)

        # Get average amount
        avg_state = self.avg_amount_state.value() or (0.0, 0)
        avg_sum, avg_count = avg_state

        avg_amount_7d = avg_sum / avg_count if avg_count > 0 else amount

        # Compute features
        features = {
            # Transaction features
            'amount': amount,
            'hour_of_day': datetime.fromtimestamp(timestamp).hour,
            'day_of_week': datetime.fromtimestamp(timestamp).weekday(),

            # Historical features
            'failed_attempts_24h': len(failed_attempts),
            'avg_amount_7d': avg_amount_7d,

            # Risk features
            'country_risk_score': self._get_country_risk(country),
            'device_new': int(transaction.get('device_new', False)),
            'merchant_reputation': self._get_merchant_reputation(
                transaction.get('merchant_id', '')
            ),

            # Derived features
            'amount_vs_avg_ratio': amount / (avg_amount_7d + 1),
            'is_night': int(datetime.fromtimestamp(timestamp).hour < 5 or
                          datetime.fromtimestamp(timestamp).hour >= 22),
            'is_weekend': int(datetime.fromtimestamp(timestamp).weekday() >= 5),
            'risk_score_composite': 0.0  # Computed below
        }

        # Compute composite risk
        features['risk_score_composite'] = (
            features['country_risk_score'] * 0.4 +
            features['device_new'] * 0.3 +
            (1 - features['merchant_reputation']) * 0.3
        )

        # Update state
        history.append((amount, timestamp))
        for amt, ts in history:
            self.transaction_history_state.add((amt, ts))

        avg_sum += amount
        avg_count += 1
        self.avg_amount_state.update((avg_sum, avg_count))

        # Output: transaction + features
        output = {
            **transaction,
            'ml_features': features
        }

        yield json.dumps(output)

    def _get_country_risk(self, country):
        """Get country risk score"""
        risk_map = {
            'US': 0.1, 'UK': 0.15, 'CA': 0.12, 'DE': 0.13,
            'FR': 0.14, 'JP': 0.11, 'CN': 0.45, 'RU': 0.75,
            'NG': 0.85, 'PK': 0.70
        }
        return risk_map.get(country, 0.5)

    def _get_merchant_reputation(self, merchant_id):
        """Get merchant reputation (0-1)"""
        # In production: lookup from database
        # For demo: hash-based pseudo-random
        import hashlib
        h = int(hashlib.md5(merchant_id.encode()).hexdigest()[:8], 16)
        return 0.5 + (h % 100) / 200.0  # Range: 0.5-1.0


def run_feature_engineering():
    """Run feature engineering pipeline"""

    from flink_cep_config import create_cep_environment, register_transaction_source

    env, table_env = create_cep_environment()
    register_transaction_source(table_env)

    # Convert to DataStream
    transaction_stream = table_env.to_append_stream(
        table_env.from_path('transactions'),
        Types.STRING()
    )

    # Apply feature engineering
    featured_stream = (transaction_stream
                       .key_by(lambda x: json.loads(x)['user_id'])
                       .process(FeatureEngineer()))

    # Print for debugging
    featured_stream.print()

    env.execute("Feature Engineering")


if __name__ == '__main__':
    run_feature_engineering()
```

## Task 4: Async Model Invocation (30 minutes)

Invoke SageMaker asynchronously for low latency.

**File**: `async_ml_scoring.py`

```python
#!/usr/bin/env python3
"""Async ML model scoring with SageMaker"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import AsyncFunction
from pyflink.common.typeinfo import Types
import asyncio
import aiohttp
import json
import time


class AsyncSageMakerScorer(AsyncFunction):
    """
    Async invocation of SageMaker endpoint
    """

    def __init__(self, endpoint_name, timeout_ms=1000):
        self.endpoint_name = endpoint_name
        self.timeout_ms = timeout_ms
        self.session = None

        # Metrics
        self.invocations = 0
        self.timeouts = 0
        self.errors = 0

    async def open(self):
        """Initialize async client"""
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Cleanup"""
        if self.session:
            await self.session.close()

    async def async_invoke(self, input_value, result_future):
        """Async model invocation"""

        try:
            transaction = json.loads(input_value)
            features = transaction.get('ml_features', {})

            # Prepare feature vector
            feature_vector = [
                features.get('amount', 0),
                features.get('hour_of_day', 0),
                features.get('day_of_week', 0),
                features.get('failed_attempts_24h', 0),
                features.get('avg_amount_7d', 0),
                features.get('country_risk_score', 0.5),
                features.get('device_new', 0),
                features.get('merchant_reputation', 0.5),
                features.get('amount_vs_avg_ratio', 1.0),
                features.get('is_night', 0),
                features.get('is_weekend', 0),
                features.get('risk_score_composite', 0.5)
            ]

            # Invoke SageMaker (or mock for LocalStack)
            start_time = time.time()

            score = await self._invoke_sagemaker(feature_vector)

            latency_ms = (time.time() - start_time) * 1000

            self.invocations += 1

            # Add score to transaction
            output = {
                **transaction,
                'ml_score': score,
                'ml_latency_ms': latency_ms,
                'ml_model_version': '1.0'
            }

            result_future.complete(json.dumps(output))

        except asyncio.TimeoutError:
            self.timeouts += 1
            # Fallback: use rule-based score
            fallback_output = {
                **transaction,
                'ml_score': self._fallback_score(transaction),
                'ml_latency_ms': self.timeout_ms,
                'ml_model_version': 'fallback'
            }
            result_future.complete(json.dumps(fallback_output))

        except Exception as e:
            self.errors += 1
            result_future.complete_exceptionally(e)

    async def _invoke_sagemaker(self, feature_vector):
        """Invoke SageMaker endpoint"""

        # For LocalStack/demo: simulate with simple logic
        # In production: actual SageMaker API call

        # Mock scoring (higher risk = higher score)
        amount = feature_vector[0]
        failed_attempts = feature_vector[3]
        risk_score = feature_vector[11]

        base_score = risk_score * 0.6
        amount_factor = min(amount / 1000.0, 0.3)
        failure_factor = min(failed_attempts * 0.1, 0.3)

        fraud_score = base_score + amount_factor + failure_factor
        fraud_score = max(0.0, min(1.0, fraud_score))

        # Simulate network latency
        await asyncio.sleep(0.05)  # 50ms

        return fraud_score

    def _fallback_score(self, transaction):
        """Rule-based fallback when ML unavailable"""

        features = transaction.get('ml_features', {})

        score = 0.0

        # High amount
        if features.get('amount', 0) > 500:
            score += 0.3

        # Multiple failures
        if features.get('failed_attempts_24h', 0) >= 3:
            score += 0.4

        # High risk factors
        score += features.get('risk_score_composite', 0) * 0.3

        return min(score, 1.0)

    def timeout(self, input_value, result_future):
        """Handle timeout"""
        self.timeouts += 1

        transaction = json.loads(input_value)

        fallback_output = {
            **transaction,
            'ml_score': self._fallback_score(transaction),
            'ml_latency_ms': self.timeout_ms,
            'ml_model_version': 'fallback_timeout'
        }

        result_future.complete(json.dumps(fallback_output))


def run_async_scoring():
    """Run async ML scoring pipeline"""

    from pyflink.datastream.functions import AsyncDataStream
    from feature_engineering import FeatureEngineer
    from flink_cep_config import create_cep_environment, register_transaction_source

    env, table_env = create_cep_environment()
    register_transaction_source(table_env)

    # Transaction stream
    transaction_stream = table_env.to_append_stream(
        table_env.from_path('transactions'),
        Types.STRING()
    )

    # Feature engineering
    featured_stream = (transaction_stream
                       .key_by(lambda x: json.loads(x)['user_id'])
                       .process(FeatureEngineer()))

    # Async ML scoring
    scorer = AsyncSageMakerScorer(
        endpoint_name='fraud-detection-endpoint',
        timeout_ms=1000
    )

    scored_stream = AsyncDataStream.unordered_wait(
        featured_stream,
        scorer,
        timeout=1000,  # 1 second
        capacity=100   # Max concurrent requests
    )

    # Filter high-risk transactions
    fraud_stream = scored_stream.filter(
        lambda x: json.loads(x)['ml_score'] > 0.7
    )

    # Print results
    fraud_stream.print()

    env.execute("Async ML Scoring")


if __name__ == '__main__':
    run_async_scoring()
```

## Task 5: Measure and Optimize Latency (20 minutes)

Track inference performance.

**File**: `latency_monitoring.py`

```python
#!/usr/bin/env python3
"""Monitor ML scoring latency"""

from pyflink.datastream.functions import MapFunction
import json
import time


class LatencyTracker(MapFunction):
    """Track and report latency metrics"""

    def __init__(self):
        self.latencies = []
        self.last_report = time.time()

    def map(self, value):
        """Track latency"""

        transaction = json.loads(value)
        latency = transaction.get('ml_latency_ms', 0)

        self.latencies.append(latency)

        # Report every 10 seconds
        if time.time() - self.last_report > 10:
            self._report_metrics()
            self.latencies = []
            self.last_report = time.time()

        return value

    def _report_metrics(self):
        """Calculate and log metrics"""

        if not self.latencies:
            return

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        avg = sum(sorted_latencies) / n
        p50 = sorted_latencies[int(n * 0.50)]
        p95 = sorted_latencies[int(n * 0.95)]
        p99 = sorted_latencies[int(n * 0.99)]
        max_lat = sorted_latencies[-1]

        print("="*50)
        print("ML SCORING LATENCY METRICS (last 10s)")
        print("="*50)
        print(f"  Count: {n}")
        print(f"  Avg:   {avg:.2f} ms")
        print(f"  p50:   {p50:.2f} ms")
        print(f"  p95:   {p95:.2f} ms")
        print(f"  p99:   {p99:.2f} ms")
        print(f"  Max:   {max_lat:.2f} ms")
        print("="*50)


# Integration with scoring pipeline
def run_with_monitoring():
    """Run scoring with latency monitoring"""

    from async_ml_scoring import run_async_scoring, AsyncSageMakerScorer
    from flink_cep_config import create_cep_environment

    # Add latency tracker to pipeline
    # (insert after scored_stream in async_ml_scoring.py)
    pass  # See async_ml_scoring.py for integration
```

## Validation Checklist

- [ ] Model trained with >90% ROC-AUC
- [ ] Model deployed to SageMaker endpoint
- [ ] Features computed correctly in Flink
- [ ] Async invocation working (no blocking)
- [ ] Latency p99 < 100ms
- [ ] Timeout fallback triggers correctly
- [ ] High-risk transactions (score >0.7) detected
- [ ] Monitoring metrics published

## Expected Results

**Model Performance**:
- Training ROC-AUC: 0.95+
- Precision: 90%+
- Recall: 85%+

**Latency**:
- p50: 50ms
- p95: 80ms
- p99: 100ms

## Troubleshooting

### Problem: High latency (>200ms)

1. Increase `capacity` in AsyncDataStream (more concurrent requests)
2. Reduce model complexity (fewer trees, smaller depth)
3. Use SageMaker Multi-Model Endpoints for batching

### Problem: Model timeouts

Check SageMaker endpoint:
```bash
awslocal sagemaker describe-endpoint \
    --endpoint-name fraud-detection-endpoint
```

Increase timeout or reduce traffic:
```python
AsyncDataStream.unordered_wait(..., timeout=2000)
```

## Key Learnings

1. **Async I/O**: Essential for external service calls in streams
2. **Feature Engineering**: Most time spent here, not model training
3. **Fallback**: Always have rule-based backup when ML fails
4. **Latency**: p99 matters more than average
5. **State Management**: Use Flink state for historical features

## Next Steps

- **Exercise 06**: Production deployment with monitoring
- **A/B Testing**: Compare model versions
- **Online Learning**: Update model with streaming feedback

## Additional Resources

- [SageMaker Real-Time Inference](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints.html)
- [Flink Async I/O](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/datastream/operators/asyncio/)
- [Feature Engineering for Fraud Detection](https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/)
