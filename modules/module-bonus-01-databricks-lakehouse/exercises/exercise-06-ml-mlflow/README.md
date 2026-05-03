# Exercise 06: ML with MLflow

## Overview
Build an end-to-end machine learning pipeline with MLflow for experiment tracking, hyperparameter tuning, model registry, deployment, and monitoring for a customer churn prediction system.

**Estimated Time**: 2.5 hours
**Difficulty**: ⭐⭐⭐⭐ Advanced
**Prerequisites**: Exercise 02 (ETL Pipelines), Python/ML basics, Module 04 (Python for Data)

---

## Learning Objectives
By completing this exercise, you will be able to:
- Prepare ML datasets with feature engineering on Delta tables
- Track experiments with MLflow (params, metrics, artifacts)
- Perform hyperparameter tuning with grid search
- Register models in MLflow Model Registry
- Transition models through stages (Staging → Production)
- Deploy models for batch and real-time inference
- Monitor model performance and detect drift

---

## Scenario
You're building a customer churn prediction system for a subscription service. The business needs:
1. Predict which customers will churn in next 30 days
2. Track multiple ML experiments to find best model
3. Deploy the best model to production
4. Score new customers daily (batch inference)
5. Provide real-time predictions via API
6. Monitor model performance over time and detect drift

**Goal**: Build a complete MLOps pipeline from data to deployment with governance.

---

## Requirements

### Task 1: Data Preparation & Feature Engineering (20 min)
Create ML-ready dataset with engineered features.

**Requirements**:
- Generate `customers` table with 5,000 records
- Create `customer_features` with engineered features
- Split into train (70%), validation (15%), test (15%)

**Raw Customer Schema**:
```
customer_id: STRING
signup_date: DATE
age: INT (18-75)
country: STRING
subscription_type: STRING (Basic, Premium, Enterprise)
monthly_fee: DOUBLE
num_logins_30d: INT (0-100)
num_support_tickets: INT (0-20)
num_failed_payments: INT (0-5)
avg_session_minutes: DOUBLE (0-180)
days_since_last_login: INT (0-60)
total_purchases: INT (0-50)
churned: BOOLEAN (target variable, 15% churn rate)
```

**Feature Engineering**:
Create these derived features:

1. **Engagement Score** (0-100):
   ```
   (num_logins_30d * 2 + total_purchases * 5) /
   (days_since_last_login + 1)
   ```

2. **Payment Risk** (0-1):
   ```
   num_failed_payments / (total_purchases + 1)
   ```

3. **Activity Level** (categorical):
   ```
   CASE
     WHEN num_logins_30d > 20 THEN 'High'
     WHEN num_logins_30d > 10 THEN 'Medium'
     ELSE 'Low'
   END
   ```

4. **Tenure Months**:
   ```
   DATEDIFF(MONTH, signup_date, current_date())
   ```

5. **One-Hot Encoding**:
   - `subscription_type` → 3 binary columns
   - `country` → N binary columns (top 5 countries + "Other")
   - `activity_level` → 3 binary columns

**Train/Val/Test Split**:
```python
from sklearn.model_selection import train_test_split

train_df, temp_df = train_test_split(features_df, test_size=0.30, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42)

# Write to Delta tables
train_df.write.format("delta").mode("overwrite").saveAsTable("customer_features_train")
val_df.write.format("delta").mode("overwrite").saveAsTable("customer_features_val")
test_df.write.format("delta").mode("overwrite").saveAsTable("customer_features_test")
```

**Success Criteria**:
- ✅ Customer table has 5,000 records (750 churned, 15% rate)
- ✅ All engineered features populated
- ✅ No missing values in features
- ✅ Train: 3,500 rows, Val: 750 rows, Test: 750 rows
- ✅ Class distribution preserved across splits (~15% churn in each)

---

### Task 2: Experiment Tracking with MLflow (30 min)
Track multiple ML experiments to compare models.

**Requirements**:
- Train 3+ different models (Logistic Regression, Random Forest, XGBoost)
- Log parameters, metrics, and artifacts for each experiment
- Compare models using MLflow UI

**Experiment Setup**:
```python
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Set experiment
mlflow.set_experiment("/Users/yourname/churn-prediction")

# Prepare features and target
X_train = train_df.drop("customer_id", "churned").toPandas()
y_train = train_df.select("churned").toPandas().values.ravel()
X_val = val_df.drop("customer_id", "churned").toPandas()
y_val = val_df.select("churned").toPandas().values.ravel()
```

**Experiment 1: Logistic Regression**
```python
with mlflow.start_run(run_name="logistic_regression_baseline"):
    # Log parameters
    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("penalty", "l2")
    mlflow.log_param("C", 1.0)

    # Train model
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)[:, 1]

    # Log metrics
    mlflow.log_metric("accuracy", accuracy_score(y_val, y_pred))
    mlflow.log_metric("precision", precision_score(y_val, y_pred))
    mlflow.log_metric("recall", recall_score(y_val, y_pred))
    mlflow.log_metric("f1_score", f1_score(y_val, y_pred))
    mlflow.log_metric("roc_auc", roc_auc_score(y_val, y_pred_proba))

    # Log model
    mlflow.sklearn.log_model(model, "model")

    # Log confusion matrix as artifact
    from sklearn.metrics import confusion_matrix
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = confusion_matrix(y_val, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.savefig("confusion_matrix.png")
    mlflow.log_artifact("confusion_matrix.png")
```

**Experiment 2: Random Forest**
```python
with mlflow.start_run(run_name="random_forest"):
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("min_samples_split", 5)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Same prediction and logging logic...
```

**Experiment 3: XGBoost**
```python
with mlflow.start_run(run_name="xgboost"):
    params = {
        "model_type": "XGBoost",
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "objective": "binary:logistic"
    }
    mlflow.log_params(params)

    model = XGBClassifier(**params, random_state=42)
    model.fit(X_train, y_train)

    # Same prediction and logging logic...
```

**Model Comparison**:
```python
# Get all runs from experiment
experiment = mlflow.get_experiment_by_name("/Users/yourname/churn-prediction")
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# Compare key metrics
print(runs[["run_id", "params.model_type", "metrics.f1_score",
            "metrics.roc_auc", "metrics.recall"]].sort_values("metrics.f1_score", ascending=False))
```

**Success Criteria**:
- ✅ At least 3 experiments logged
- ✅ All experiments have params, metrics, and model artifacts
- ✅ Can view experiments in MLflow UI
- ✅ Confusion matrix visualizations saved
- ✅ Best model has F1 > 0.70 and ROC-AUC > 0.80

---

### Task 3: Hyperparameter Tuning (30 min)
Find optimal hyperparameters using grid search.

**Requirements**:
- Define parameter grid for best-performing model
- Train 27+ combinations (complete grid search)
- Track each combination as separate MLflow run
- Select best model based on validation F1 score

**Grid Search for Random Forest** (example):
```python
from sklearn.model_selection import ParameterGrid

# Define parameter grid
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}

# Generate all combinations (3 * 3 * 3 = 27)
grid = ParameterGrid(param_grid)

with mlflow.start_run(run_name="random_forest_grid_search") as parent_run:
    best_f1 = 0
    best_model = None
    best_params = None

    for i, params in enumerate(grid):
        with mlflow.start_run(nested=True, run_name=f"rf_config_{i}"):
            # Log parameters
            mlflow.log_params(params)

            # Train model
            model = RandomForestClassifier(**params, random_state=42)
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_val)
            y_pred_proba = model.predict_proba(X_val)[:, 1]

            f1 = f1_score(y_val, y_pred)
            roc_auc = roc_auc_score(y_val, y_pred_proba)

            mlflow.log_metric("f1_score", f1)
            mlflow.log_metric("roc_auc", roc_auc)

            # Track best model
            if f1 > best_f1:
                best_f1 = f1
                best_model = model
                best_params = params

    # Log best result in parent run
    mlflow.log_params(best_params)
    mlflow.log_metric("best_f1_score", best_f1)
    mlflow.sklearn.log_model(best_model, "best_model")

    print(f"Best F1: {best_f1:.4f}")
    print(f"Best params: {best_params}")
```

**Visualization**:
```python
# Create parameter importance plot
import pandas as pd

results = []
for params in grid:
    # ... get F1 for each param combination
    results.append({**params, "f1_score": f1})

results_df = pd.DataFrame(results)

# Plot parameter impact
for param in ['n_estimators', 'max_depth', 'min_samples_split']:
    plt.figure(figsize=(10, 6))
    results_df.groupby(param)['f1_score'].mean().plot(kind='bar')
    plt.title(f'F1 Score vs {param}')
    plt.ylabel('Average F1 Score')
    plt.savefig(f"{param}_impact.png")
    mlflow.log_artifact(f"{param}_impact.png")
```

**Success Criteria**:
- ✅ Grid search completes (27 runs logged)
- ✅ Each run tracked as nested MLflow run
- ✅ Best model identified (F1 improvement over baseline)
- ✅ Parameter importance plots generated
- ✅ Best parameters documented

---

### Task 4: Model Registry (25 min)
Register best model and manage lifecycle stages.

**Requirements**:
- Register best model in MLflow Model Registry
- Add model description and metadata
- Transition through stages: None → Staging → Production
- Test model loading from registry

**Register Model**:
```python
# Get best run from grid search
best_run = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1
).iloc[0]

best_run_id = best_run.run_id

# Register model
model_name = "churn_prediction_model"
model_uri = f"runs:/{best_run_id}/model"

model_version = mlflow.register_model(
    model_uri=model_uri,
    name=model_name
)

print(f"Model registered as {model_name} version {model_version.version}")
```

**Add Model Metadata**:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Update model description
client.update_registered_model(
    name=model_name,
    description="Customer churn prediction model trained on 5,000 customers. "
                "Predicts churn probability for next 30 days. "
                "Best model: Random Forest with F1=0.78, ROC-AUC=0.85"
)

# Add tags to version
client.set_model_version_tag(
    name=model_name,
    version=model_version.version,
    key="training_date",
    value="2026-03-09"
)
client.set_model_version_tag(
    name=model_name,
    version=model_version.version,
    key="training_size",
    value="3500"
)
```

**Transition to Staging**:
```python
client.transition_model_version_stage(
    name=model_name,
    version=model_version.version,
    stage="Staging"
)

print(f"Model version {model_version.version} transitioned to Staging")
```

**Test Model in Staging**:
```python
# Load model from staging
staging_model_uri = f"models:/{model_name}/Staging"
staging_model = mlflow.sklearn.load_model(staging_model_uri)

# Test prediction
test_sample = X_val.iloc[:5]
predictions = staging_model.predict(test_sample)
probabilities = staging_model.predict_proba(test_sample)[:, 1]

print("Test predictions:", predictions)
print("Churn probabilities:", probabilities)
```

**Transition to Production** (after validation):
```python
client.transition_model_version_stage(
    name=model_name,
    version=model_version.version,
    stage="Production"
)

print(f"Model version {model_version.version} promoted to Production")
```

**Success Criteria**:
- ✅ Model registered with name and version
- ✅ Model description and tags added
- ✅ Model in Production stage
- ✅ Can load model from registry URI
- ✅ Predictions work from loaded model

---

### Task 5: Model Deployment (30 min)
Deploy model for batch and real-time inference.

**5A: Batch Inference (Score Daily)**

Create scheduled job to score new customers:

```python
# Load production model
prod_model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

# Load new customers to score
new_customers = spark.table("customers_to_score")  # Today's signups

# Prepare features (same as training)
new_features = prepare_features(new_customers)  # Your feature engineering function
X_new = new_features.drop("customer_id").toPandas()

# Get predictions
predictions = prod_model.predict(X_new)
probabilities = prod_model.predict_proba(X_new)[:, 1]

# Save results to Delta
results_df = new_features.select("customer_id")
results_df = results_df.withColumn("churn_prediction", lit(predictions))
results_df = results_df.withColumn("churn_probability", lit(probabilities))
results_df = results_df.withColumn("scored_at", current_timestamp())

results_df.write.format("delta").mode("append").saveAsTable("churn_predictions")
```

**5B: Real-Time API Serving**

Deploy model as REST endpoint:

```python
# Option 1: MLflow Model Serving (Local testing)
import os
os.system(f"mlflow models serve -m models:/{model_name}/Production -p 5000")

# Test API with curl
# curl -X POST -H "Content-Type:application/json" \
#   --data '{"columns":["age","monthly_fee","num_logins_30d",...],
#            "data":[[35,50.0,15,...]]}' \
#   http://localhost:5000/invocations
```

```python
# Option 2: Python function for real-time scoring
def predict_churn(customer_data):
    """Real-time churn prediction endpoint"""
    # Load model
    model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

    # Prepare features
    features = prepare_features_from_api_request(customer_data)

    # Predict
    probability = model.predict_proba([features])[0][1]
    prediction = probability > 0.5

    return {
        "customer_id": customer_data["customer_id"],
        "churn_prediction": bool(prediction),
        "churn_probability": float(probability),
        "risk_level": "High" if probability > 0.7 else "Medium" if probability > 0.4 else "Low"
    }

# Test
test_customer = {
    "customer_id": "CUST_12345",
    "age": 45,
    "monthly_fee": 29.99,
    "num_logins_30d": 3,
    # ... other features
}

result = predict_churn(test_customer)
print(result)
# Output: {'customer_id': 'CUST_12345', 'churn_prediction': True,
#          'churn_probability': 0.78, 'risk_level': 'High'}
```

**5C: Integration with Delta Live Tables (Batch Pipeline)**

```python
import dlt

@dlt.table(
    name="churn_predictions_daily",
    comment="Daily batch predictions for all active customers"
)
def churn_predictions():
    # Load model
    model = mlflow.sklearn.load_model(f"models:/churn_prediction_model/Production")

    # Get active customers
    customers_df = dlt.read("active_customers")

    # Score in batches
    predictions = score_batch(customers_df, model)

    return predictions
```

**Success Criteria**:
- ✅ Batch inference pipeline scores 100+ customers
- ✅ Results saved to `churn_predictions` Delta table
- ✅ Real-time API endpoint works (test with curl or Python)
- ✅ Response time < 100ms for single prediction
- ✅ API returns probability and risk level

---

### Task 6: Model Monitoring & Drift Detection (25 min)
Monitor model performance and detect data/concept drift.

**Requirements**:
- Track predictions over time (last 30 days)
- Calculate performance metrics on labeled data
- Detect feature drift (input distribution changes)
- Detect prediction drift (output distribution changes)
- Alert when drift exceeds threshold (5%)

**Performance Monitoring**:
```python
# Simulate 30 days of predictions with ground truth
import numpy as np
from datetime import datetime, timedelta

monitoring_data = []
base_date = datetime.now() - timedelta(days=30)

for day in range(30):
    current_date = base_date + timedelta(days=day)

    # Score customers for that day
    daily_customers = get_customers_for_date(current_date)  # Simulate
    X_daily = prepare_features(daily_customers)
    y_pred = model.predict(X_daily)
    y_pred_proba = model.predict_proba(X_daily)[:, 1]

    # Get actual churn (after 30 days)
    y_actual = get_actual_churn(daily_customers, current_date)  # Simulate

    # Calculate metrics
    accuracy = accuracy_score(y_actual, y_pred)
    precision = precision_score(y_actual, y_pred)
    recall = recall_score(y_actual, y_pred)
    f1 = f1_score(y_actual, y_pred)
    roc_auc = roc_auc_score(y_actual, y_pred_proba)

    monitoring_data.append({
        "date": current_date,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "num_predictions": len(y_pred),
        "predicted_churn_rate": y_pred.mean(),
        "actual_churn_rate": y_actual.mean()
    })

monitoring_df = spark.createDataFrame(monitoring_data)
monitoring_df.write.format("delta").mode("overwrite").saveAsTable("model_performance_monitoring")
```

**Feature Drift Detection**:
```python
from scipy.stats import ks_2samp

def detect_feature_drift(training_data, production_data, features, threshold=0.05):
    """Detect drift using Kolmogorov-Smirnov test"""
    drift_results = []

    for feature in features:
        train_values = training_data[feature]
        prod_values = production_data[feature]

        # KS test
        statistic, p_value = ks_2samp(train_values, prod_values)

        drift_detected = p_value < threshold

        drift_results.append({
            "feature": feature,
            "ks_statistic": statistic,
            "p_value": p_value,
            "drift_detected": drift_detected,
            "train_mean": train_values.mean(),
            "prod_mean": prod_values.mean(),
            "mean_change_pct": ((prod_values.mean() - train_values.mean()) /
                                train_values.mean() * 100)
        })

    return pd.DataFrame(drift_results)

# Run drift detection
training_features = X_train
production_features = X_new  # Recent production data

drift_report = detect_feature_drift(
    training_features,
    production_features,
    features=X_train.columns.tolist()
)

print("Features with drift detected:")
print(drift_report[drift_report['drift_detected']])
```

**Prediction Drift Monitoring**:
```python
# Compare prediction distribution over time
def monitor_prediction_drift():
    monitoring_df = spark.table("model_performance_monitoring")

    # Get baseline (first week)
    baseline = monitoring_df.filter("date < current_date() - 23").select("predicted_churn_rate").avg()

    # Get current (last week)
    current = monitoring_df.filter("date >= current_date() - 7").select("predicted_churn_rate").avg()

    drift_pct = (current - baseline) / baseline * 100

    if abs(drift_pct) > 5:
        print(f"⚠️ ALERT: Prediction drift detected! {drift_pct:+.1f}% change")
        # Trigger retraining or investigation
    else:
        print(f"✅ No significant prediction drift ({drift_pct:+.1f}%)")

monitor_prediction_drift()
```

**Drift Dashboard**:
```python
# Visualize performance over time
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# F1 Score over time
monitoring_df.plot(x='date', y='f1_score', ax=axes[0, 0], title='F1 Score Trend')
axes[0, 0].axhline(y=0.70, color='r', linestyle='--', label='Threshold')

# Churn rate: predicted vs actual
monitoring_df.plot(x='date', y=['predicted_churn_rate', 'actual_churn_rate'],
                   ax=axes[0, 1], title='Predicted vs Actual Churn Rate')

# Feature drift heatmap
# axes[1, 0] - feature drift visualization

# Prediction volume
monitoring_df.plot(x='date', y='num_predictions', ax=axes[1, 1],
                   title='Daily Prediction Volume')

plt.tight_layout()
plt.savefig("drift_monitoring_dashboard.png")
mlflow.log_artifact("drift_monitoring_dashboard.png")
```

**Success Criteria**:
- ✅ Performance tracked over 30 days
- ✅ Feature drift detection implemented (KS test)
- ✅ Prediction drift monitoring active
- ✅ Alert triggered when drift > 5%
- ✅ Monitoring dashboard visualizes trends
- ✅ Recommendation for retraining based on drift

---

## Hints

<details>
<summary>Hint 1: Feature Engineering Pipeline</summary>

```python
from pyspark.sql.functions import col, when, datediff, current_date, lit
from pyspark.sql.types import DoubleType

def engineer_features(df):
    """Apply all feature engineering transformations"""

    # Engagement score
    engagement = ((col("num_logins_30d") * 2 + col("total_purchases") * 5) /
                  (col("days_since_last_login") + 1))

    # Payment risk
    payment_risk = col("num_failed_payments") / (col("total_purchases") + 1)

    # Activity level
    activity_level = when(col("num_logins_30d") > 20, "High") \
                     .when(col("num_logins_30d") > 10, "Medium") \
                     .otherwise("Low")

    # Tenure
    tenure_months = datediff(current_date(), col("signup_date")) / 30

    # Apply transformations
    features_df = df.withColumn("engagement_score", engagement) \
                    .withColumn("payment_risk", payment_risk) \
                    .withColumn("activity_level", activity_level) \
                    .withColumn("tenure_months", tenure_months)

    # One-hot encoding
    features_df = features_df.fillna(0)  # Handle nulls

    return features_df
```
</details>

<details>
<summary>Hint 2: MLflow Experiment Tracking Structure</summary>

```python
import mlflow

# Set experiment (creates if doesn't exist)
mlflow.set_experiment("/Users/analyst/churn-prediction-v1")

# Context manager for automatic logging
with mlflow.start_run(run_name="experiment_1"):
    # Log parameters (hyperparameters)
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)

    # Train model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)

    # Log metrics
    f1 = f1_score(y_val, y_pred)
    mlflow.log_metric("f1_score", f1)
    mlflow.log_metric("accuracy", accuracy_score(y_val, y_pred))

    # Log model
    mlflow.sklearn.log_model(model, "model")

    # Log artifacts (plots, files)
    plt.savefig("feature_importance.png")
    mlflow.log_artifact("feature_importance.png")
```
</details>

<details>
<summary>Hint 3: Model Registry Workflow</summary>

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Register model (creates new version)
model_uri = f"runs:/{run_id}/model"
result = mlflow.register_model(model_uri, "churn_model")

# Get latest version
latest_version = client.get_latest_versions("churn_model", stages=["None"])[0]

# Transition to Staging
client.transition_model_version_stage(
    name="churn_model",
    version=latest_version.version,
    stage="Staging"
)

# After testing, promote to Production
client.transition_model_version_stage(
    name="churn_model",
    version=latest_version.version,
    stage="Production"
)

# Load for inference
model = mlflow.sklearn.load_model("models:/churn_model/Production")
```
</details>

<details>
<summary>Hint 4: Drift Detection Implementation</summary>

```python
from scipy.stats import ks_2samp
import pandas as pd

def check_drift(baseline_data, current_data, features, threshold=0.05):
    """Check for data drift using KS test"""
    results = []

    for feature in features:
        # Extract feature values
        baseline_values = baseline_data[feature].dropna()
        current_values = current_data[feature].dropna()

        # Perform KS test
        statistic, p_value = ks_2samp(baseline_values, current_values)

        # Drift detected if p-value < threshold
        drift = p_value < threshold

        results.append({
            'feature': feature,
            'ks_statistic': statistic,
            'p_value': p_value,
            'drift_detected': drift
        })

    return pd.DataFrame(results)

# Run drift check
drift_report = check_drift(X_train, X_production, X_train.columns)
print(drift_report[drift_report['drift_detected']])
```
</details>

---

## Validation
Run the validation script to check your work:

```bash
cd exercises/exercise-06-ml-mlflow
python validate.py
```

**Expected Output**:
```
✅ Task 1: Data prepared (5,000 customers, 15.2% churn rate)
   - Train: 3,500 samples
   - Val: 750 samples
   - Test: 750 samples
   - 18 features engineered (12 numeric, 6 categorical)
✅ Task 2: Experiments tracked (3 models logged)
   - Logistic Regression: F1=0.68, ROC-AUC=0.79
   - Random Forest: F1=0.76, ROC-AUC=0.84
   - XGBoost: F1=0.78, ROC-AUC=0.85
✅ Task 3: Hyperparameter tuning (27 combinations tested)
   - Best params: {'n_estimators': 200, 'max_depth': 10, 'min_samples_split': 2}
   - Best F1: 0.79 (+0.03 improvement)
✅ Task 4: Model registered (version 1 in Production stage)
   - Model: churn_prediction_model
   - Description and tags populated
✅ Task 5: Deployment working
   - Batch inference: 100 customers scored in 1.2s
   - API serving: Response time 45ms average
✅ Task 6: Monitoring active (30 days tracked, drift detection working)
   - Feature drift detected: 2 features (num_logins_30d, days_since_last_login)
   - Prediction drift: +3.2% (within threshold)
   - Model performance stable: F1=0.77 ± 0.02

🎉 Exercise 06 Complete! Total Score: 100/100
💡 Recommendation: Retrain model due to feature drift in 2 features
```

---

## Deliverables
Submit the following:
1. `solution.py` - Complete ML pipeline with all tasks
2. MLflow experiment comparison (screenshot or exported CSV)
3. Model card (description, metrics, deployment info)
4. Drift monitoring report (30-day analysis with visualizations)

---

## Resources
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [Databricks MLflow Guide](https://docs.databricks.com/mlflow/index.html)
- [Drift Detection Techniques](https://docs.databricks.com/machine-learning/model-inference/model-monitoring.html)
- Notebook: `notebooks/06-ml-mlflow.py`
- Diagram: `assets/diagrams/mlops-lifecycle.mmd`

---

## Next Steps
After completing this exercise:
- ✅ Complete all 6 exercises! 🎉
- Review Module 04: Python for Data (advanced ML techniques)
- Explore Databricks AutoML for automated model training
- Consider Feature Store for centralized feature management
- Investigate Delta Live Tables for ML pipelines
- Study for Databricks Machine Learning Associate certification
