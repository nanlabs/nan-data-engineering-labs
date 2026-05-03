# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook 06: Machine Learning with MLflow
# MAGIC
# MAGIC ## Learning Objectives
# MAGIC - Train ML models on Databricks
# MAGIC - Use MLflow for experiment tracking
# MAGIC - Register models in MLflow Model Registry
# MAGIC - Deploy models for batch and real-time inference
# MAGIC - Implement AutoML for rapid prototyping
# MAGIC
# MAGIC ## Prerequisites
# MAGIC - Databricks Runtime ML (14.3 LTS ML)
# MAGIC - Basic machine learning knowledge
# MAGIC
# MAGIC ## Estimated Time: 60-75 minutes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder

from pyspark.sql.functions import *
from pyspark.sql.types import *
import pandas as pd
import numpy as np

# Set MLflow experiment
experiment_name = "/Users/" + spark.sql("SELECT current_user()").collect()[0][0] + "/ml_training"
mlflow.set_experiment(experiment_name)

print(f"✅ MLflow experiment: {experiment_name}")
print(f"✅ MLflow tracking URI: {mlflow.get_tracking_uri()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Prepare Training Data

# COMMAND ----------

# Generate customer churn dataset
print("Generating customer churn dataset...")

np.random.seed(42)

def generate_churn_data(n_samples=5000):
    """Generate synthetic customer churn data."""
    data = {
        "customer_id": range(1, n_samples + 1),
        "tenure_months": np.random.randint(1, 72, n_samples),
        "monthly_charges": np.random.uniform(20, 150, n_samples),
        "total_charges": np.random.uniform(100, 8000, n_samples),
        "contract_type": np.random.choice(["Month-to-month", "One year", "Two year"], n_samples, p=[0.5, 0.3, 0.2]),
        "payment_method": np.random.choice(["Credit card", "Bank transfer", "Electronic check", "Mailed check"], n_samples),
        "internet_service": np.random.choice(["DSL", "Fiber optic", "No"], n_samples, p=[0.4, 0.4, 0.2]),
        "online_security": np.random.choice(["Yes", "No", "No internet"], n_samples, p=[0.3, 0.5, 0.2]),
        "tech_support": np.random.choice(["Yes", "No", "No internet"], n_samples, p=[0.3, 0.5, 0.2]),
        "num_support_tickets": np.random.poisson(2, n_samples),
        "satisfaction_score": np.random.randint(1, 6, n_samples)
    }

    # Generate churn based on features (with some logic)
    churn_prob = (
        (data["tenure_months"] < 12) * 0.3 +
        (data["contract_type"] == "Month-to-month") * 0.2 +
        (data["satisfaction_score"] <= 2) * 0.3 +
        (data["num_support_tickets"] > 3) * 0.15 +
        np.random.uniform(0, 0.2, n_samples)
    )

    data["churned"] = (churn_prob > 0.5).astype(int)

    return pd.DataFrame(data)

# Generate data
churn_df = generate_churn_data(5000)

print(f"✅ Generated {len(churn_df)} customer records")
print(f"   Churn rate: {churn_df['churned'].mean():.1%}")

# Display sample
display(spark.createDataFrame(churn_df.head(10)))

# COMMAND ----------

# Prepare features
print("Preparing features...")

# Encode categorical variables
le = LabelEncoder()
categorical_cols = ["contract_type", "payment_method", "internet_service", "online_security", "tech_support"]

for col in categorical_cols:
    churn_df[f"{col}_encoded"] = le.fit_transform(churn_df[col])

# Feature columns
feature_cols = [
    "tenure_months", "monthly_charges", "total_charges",
    "contract_type_encoded", "payment_method_encoded", "internet_service_encoded",
    "online_security_encoded", "tech_support_encoded",
    "num_support_tickets", "satisfaction_score"
]

X = churn_df[feature_cols]
y = churn_df["churned"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"✅ Training set: {len(X_train)} samples")
print(f"✅ Test set: {len(X_test)} samples")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: MLflow Experiment Tracking

# COMMAND ----------

# Train model with MLflow tracking
print("Training model with MLflow tracking...")

with mlflow.start_run(run_name="random_forest_baseline") as run:
    # Log parameters
    params = {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "random_state": 42
    }
    mlflow.log_params(params)

    # Train model
    rf_model = RandomForestClassifier(**params)
    rf_model.fit(X_train, y_train)

    # Predictions
    y_pred = rf_model.predict(X_test)
    y_pred_proba = rf_model.predict_proba(X_test)[:, 1]

    # Calculate metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_pred_proba)
    }

    # Log metrics
    mlflow.log_metrics(metrics)

    # Log model
    mlflow.sklearn.log_model(rf_model, "model", registered_model_name="churn_prediction_model")

    # Log feature importance
    feature_importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": rf_model.feature_importances_
    }).sort_values("importance", ascending=False)

    mlflow.log_dict(feature_importance.to_dict(), "feature_importance.json")

    run_id = run.info.run_id
    print(f"✅ Run completed: {run_id}")
    print("\nMetrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

# COMMAND ----------

# Display feature importance
print("📊 Feature Importance:")
display(spark.createDataFrame(feature_importance))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 3: Hyperparameter Tuning with MLflow

# COMMAND ----------

# Train multiple models with different hyperparameters
print("Hyperparameter tuning...")

param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, 15],
    "min_samples_split": [2, 5, 10]
}

best_auc = 0
best_params = None

for n_est in param_grid["n_estimators"]:
    for depth in param_grid["max_depth"]:
        for min_split in param_grid["min_samples_split"]:

            with mlflow.start_run(run_name=f"rf_n{n_est}_d{depth}_s{min_split}"):
                # Parameters
                params = {
                    "n_estimators": n_est,
                    "max_depth": depth,
                    "min_samples_split": min_split,
                    "random_state": 42
                }
                mlflow.log_params(params)

                # Train
                model = RandomForestClassifier(**params)
                model.fit(X_train, y_train)

                # Evaluate
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                auc = roc_auc_score(y_test, y_pred_proba)

                mlflow.log_metric("roc_auc", auc)

                # Track best
                if auc > best_auc:
                    best_auc = auc
                    best_params = params

print("\n✅ Tuning complete")
print(f"   Best ROC-AUC: {best_auc:.4f}")
print(f"   Best params: {best_params}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 4: Compare Multiple Algorithms

# COMMAND ----------

# Train and compare different algorithms
print("Comparing algorithms...")

algorithms = {
    "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42)
}

results = []

for algo_name, model in algorithms.items():
    with mlflow.start_run(run_name=f"comparison_{algo_name.replace(' ', '_')}"):
        # Log algorithm name
        mlflow.log_param("algorithm", algo_name)

        # Train
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        # Metrics
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_pred_proba)
        }

        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model")

        results.append({
            "algorithm": algo_name,
            **metrics
        })

# Display comparison
comparison_df = pd.DataFrame(results)
print("\n📊 Algorithm Comparison:")
display(spark.createDataFrame(comparison_df))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 5: MLflow Model Registry

# COMMAND ----------

# Register best model
print("Registering best model in MLflow Model Registry...")

client = MlflowClient()

# Get best run
experiment = mlflow.get_experiment_by_name(experiment_name)
best_run = mlflow.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.roc_auc DESC"],
    max_results=1
).iloc[0]

best_run_id = best_run["run_id"]
best_auc = best_run["metrics.roc_auc"]

print(f"   Best run ID: {best_run_id}")
print(f"   Best ROC-AUC: {best_auc:.4f}")

# Register model
model_name = "churn_prediction_production"
model_uri = f"runs:/{best_run_id}/model"

mv = mlflow.register_model(model_uri, model_name)

print(f"✅ Model registered: {model_name} version {mv.version}")

# COMMAND ----------

# Transition model to staging
client.transition_model_version_stage(
    name=model_name,
    version=mv.version,
    stage="Staging",
    archive_existing_versions=True
)

print(f"✅ Model version {mv.version} transitioned to Staging")

# COMMAND ----------

# Add model description and tags
client.update_registered_model(
    name=model_name,
    description="Customer churn prediction model. Predicts probability of customer churning based on usage patterns and satisfaction."
)

client.set_model_version_tag(
    name=model_name,
    version=mv.version,
    key="training_date",
    value=pd.Timestamp.now().strftime("%Y-%m-%d")
)

client.set_model_version_tag(
    name=model_name,
    version=mv.version,
    key="data_version",
    value="v1.0"
)

print("✅ Model metadata updated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 6: Model Inference (Batch)

# COMMAND ----------

# Load model from registry
print("Loading model from registry...")

model_uri = f"models:/{model_name}/Staging"
loaded_model = mlflow.sklearn.load_model(model_uri)

print(f"✅ Model loaded from: {model_uri}")

# COMMAND ----------

# Batch inference on new data
print("Running batch inference...")

# Simulate new customer data
new_customers = generate_churn_data(100)

# Prepare features (same encoding as training)
for col in categorical_cols:
    new_customers[f"{col}_encoded"] = le.fit_transform(new_customers[col])

X_new = new_customers[feature_cols]

# Predictions
predictions = loaded_model.predict(X_new)
prediction_proba = loaded_model.predict_proba(X_new)[:, 1]

# Add to DataFrame
new_customers["churn_prediction"] = predictions
new_customers["churn_probability"] = prediction_proba
new_customers["risk_category"] = pd.cut(
    prediction_proba,
    bins=[0, 0.3, 0.7, 1.0],
    labels=["Low Risk", "Medium Risk", "High Risk"]
)

print(f"✅ Predictions generated for {len(new_customers)} customers")

# Display results
display_cols = ["customer_id", "tenure_months", "satisfaction_score", "churn_probability", "risk_category"]
display(spark.createDataFrame(new_customers[display_cols].head(20)))

# COMMAND ----------

# Save predictions to Delta table
predictions_df = spark.createDataFrame(new_customers)

predictions_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("churn_predictions")

print("✅ Predictions saved to table: churn_predictions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 7: MLflow Model Serving (REST API)

# COMMAND ----------

# MAGIC %md
# MAGIC **To enable model serving:**
# MAGIC
# MAGIC 1. **Go to Models** page in Databricks
# MAGIC 2. **Select model**: `churn_prediction_production`
# MAGIC 3. **Click version** in Staging
# MAGIC 4. **Click "Use model for inference"**
# MAGIC 5. **Enable Serving**:
# MAGIC    - Choose cluster size (Small, Medium, Large)
# MAGIC    - Set auto-scaling (min/max instances)
# MAGIC    - Click "Enable"
# MAGIC 6. **Get API endpoint** and token
# MAGIC 7. **Test with curl** or Python requests

# COMMAND ----------

# Example: Call model serving API
print("Example model serving API call:\n")

example_curl = """
curl -X POST https://<databricks-instance>/model/churn_prediction_production/Staging/invocations \\
  -H 'Authorization: Bearer <token>' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "dataframe_records": [
      {
        "tenure_months": 12,
        "monthly_charges": 75.5,
        "total_charges": 900.0,
        "contract_type_encoded": 0,
        "payment_method_encoded": 1,
        "internet_service_encoded": 1,
        "online_security_encoded": 0,
        "tech_support_encoded": 0,
        "num_support_tickets": 2,
        "satisfaction_score": 3
      }
    ]
  }'
"""

print(example_curl)

# COMMAND ----------

# Python example for calling served model
import requests

def predict_churn(customer_features, endpoint_url, token):
    """
    Call model serving endpoint for real-time prediction.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "dataframe_records": [customer_features]
    }

    response = requests.post(endpoint_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Prediction failed: {response.text}")

# Example usage (with actual endpoint and token):
# result = predict_churn(
#     customer_features={...},
#     endpoint_url="https://<instance>/model/churn_prediction_production/Staging/invocations",
#     token="<your-token>"
# )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 8: Databricks AutoML (Quick Start)

# COMMAND ----------

# MAGIC %md
# MAGIC **Using Databricks AutoML:**
# MAGIC
# MAGIC 1. **Go to Machine Learning** → **AutoML**
# MAGIC 2. **Select table**: Choose training data table
# MAGIC 3. **Configure**:
# MAGIC    - Problem type: Classification
# MAGIC    - Target column: `churned`
# MAGIC    - Timeout: 15-60 minutes
# MAGIC 4. **Start AutoML**
# MAGIC 5. **Review results**:
# MAGIC    - Best model accuracy
# MAGIC    - Feature importance
# MAGIC    - Generated notebook with code
# MAGIC 6. **Register best model** to MLflow
# MAGIC
# MAGIC AutoML automatically:
# MAGIC - Tries multiple algorithms
# MAGIC - Tunes hyperparameters
# MAGIC - Generates explanations
# MAGIC - Creates deployment-ready notebook

# COMMAND ----------

# Programmatic AutoML (Python API)
print("Example: Run AutoML programmatically\n")

example_code = """
from databricks import automl

# Run AutoML
summary = automl.classify(
    dataset=churn_df,
    target_col="churned",
    primary_metric="f1",
    timeout_minutes=30,
    max_trials=20
)

# Get best model
best_trial = summary.best_trial
print(f"Best trial: {best_trial.model_description}")
print(f"Best F1 score: {best_trial.metrics['test_f1_score']}")

# Register best model
model_uri = f"runs:/{best_trial.mlflow_run_id}/model"
mlflow.register_model(model_uri, "automl_churn_model")
"""

print(example_code)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 9: Model Monitoring

# COMMAND ----------

# Monitor model performance over time
print("Setting up model monitoring...")

# Simulated monitoring metrics
monitoring_data = []

for day in range(30):
    date = pd.Timestamp.now() - pd.Timedelta(days=30-day)

    # Simulate metrics with slight degradation
    accuracy = 0.85 - (day * 0.001)  # Slight decline
    roc_auc = 0.90 - (day * 0.0008)

    monitoring_data.append({
        "date": date,
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "predictions_count": np.random.randint(800, 1200),
        "avg_churn_probability": np.random.uniform(0.25, 0.35)
    })

monitoring_df = pd.DataFrame(monitoring_data)

print("📊 Model Performance Over Time:")
display(spark.createDataFrame(monitoring_df))

# COMMAND ----------

# Check for model drift
print("Checking for model drift...")

recent_auc = monitoring_df.tail(7)["roc_auc"].mean()
baseline_auc = 0.90

drift_threshold = 0.05

if (baseline_auc - recent_auc) > drift_threshold:
    print("⚠️ WARNING: Model drift detected!")
    print(f"   Baseline ROC-AUC: {baseline_auc:.4f}")
    print(f"   Recent ROC-AUC (7 days): {recent_auc:.4f}")
    print(f"   Degradation: {(baseline_auc - recent_auc):.4f}")
    print("\n   Recommended action: Retrain model with recent data")
else:
    print("✅ Model performance stable")
    print(f"   Baseline: {baseline_auc:.4f}")
    print(f"   Recent: {recent_auc:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Key Takeaways
# MAGIC
# MAGIC ✅ **MLflow Tracking**
# MAGIC - Log parameters, metrics, and artifacts
# MAGIC - Track experiments automatically
# MAGIC - Compare runs easily
# MAGIC
# MAGIC ✅ **Model Registry**
# MAGIC - Version control for models
# MAGIC - Stage transitions (None → Staging → Production)
# MAGIC - Model lineage and metadata
# MAGIC
# MAGIC ✅ **Model Deployment**
# MAGIC - Batch inference with saved models
# MAGIC - Real-time serving via REST API
# MAGIC - Integration with Databricks workflows
# MAGIC
# MAGIC ✅ **AutoML**
# MAGIC - Rapid prototyping
# MAGIC - Automated hyperparameter tuning
# MAGIC - Generated notebooks for customization
# MAGIC
# MAGIC ✅ **Production Best Practices**
# MAGIC - Model monitoring and drift detection
# MAGIC - A/B testing between versions
# MAGIC - Automated retraining pipelines
# MAGIC
# MAGIC ## Next Steps
# MAGIC
# MAGIC - Complete Exercise 06: **ML with MLflow**
# MAGIC - Build end-to-end ML pipeline
# MAGIC - Deploy model to production
# MAGIC - Set up monitoring and alerts

# COMMAND ----------

# Cleanup (optional)
# mlflow.delete_experiment(experiment.experiment_id)
# spark.sql("DROP TABLE IF EXISTS churn_predictions")
# print("✅ Cleanup complete")
