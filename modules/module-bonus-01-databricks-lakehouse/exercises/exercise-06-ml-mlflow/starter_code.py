"""
Exercise 06: ML with MLflow - Starter Code
Build an end-to-end ML pipeline for customer churn prediction.

Tasks:
1. Data Preparation & Feature Engineering
2. Experiment Tracking with MLflow
3. Hyperparameter Tuning
4. Model Registry
5. Model Deployment
6. Monitoring & Drift Detection

Estimated Time: 2.5 hours
"""

import random
import numpy as np
from pyspark.sql import SparkSession

# ML Libraries

# MLflow

# Visualization

# Initialize Spark
spark = SparkSession.builder \
    .appName("ChurnPredictionMLflow") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)


# ============================================================
# TASK 1: DATA PREPARATION & FEATURE ENGINEERING (20 min)
# ============================================================

def generate_churn_data(num_customers=5000):
    """
    Generate synthetic customer data for churn prediction.

    TODO: Implement data generation with the following schema:
    - customer_id: STRING
    - signup_date: DATE (last 24 months)
    - age: INT (18-75)
    - country: STRING (USA, UK, Canada, Germany, France)
    - subscription_type: STRING (Basic, Premium, Enterprise)
    - monthly_fee: DOUBLE (19.99, 49.99, 99.99 based on subscription)
    - num_logins_30d: INT (0-100)
    - num_support_tickets: INT (0-20)
    - num_failed_payments: INT (0-5)
    - avg_session_minutes: DOUBLE (0-180)
    - days_since_last_login: INT (0-60)
    - total_purchases: INT (0-50)
    - churned: BOOLEAN (target variable, 15% churn rate)

    Returns:
        Spark DataFrame with customer data
    """
    # TODO: Generate synthetic data
    pass


def engineer_features(df):
    """
    Apply feature engineering transformations.

    TODO: Create derived features:
    1. engagement_score: (num_logins_30d * 2 + total_purchases * 5) / (days_since_last_login + 1)
    2. payment_risk: num_failed_payments / (total_purchases + 1)
    3. activity_level: High (>20 logins), Medium (>10), Low (<=10)
    4. tenure_months: Months since signup_date
    5. One-hot encoding: subscription_type, country, activity_level

    Returns:
        DataFrame with engineered features
    """
    # TODO: Implement feature engineering
    pass


def prepare_ml_datasets():
    """
    Prepare train/validation/test splits.

    TODO:
    - Generate customer data (5,000 records)
    - Apply feature engineering
    - Split into train (70%), val (15%), test (15%) with stratification
    - Return pandas DataFrames ready for sklearn

    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test
    """
    # TODO: Implement data preparation pipeline
    pass


# ============================================================
# TASK 2: EXPERIMENT TRACKING WITH MLFLOW (30 min)
# ============================================================

def setup_mlflow_experiment(experiment_name="/Users/analyst/churn-prediction"):
    """
    TODO: Set up MLflow experiment and tracking URI.
    """
    # TODO: Configure MLflow
    pass


def train_logistic_regression(X_train, y_train, X_val, y_val):
    """
    TODO: Train logistic regression baseline model.
    - Log parameters: model_type, penalty, C
    - Log metrics: accuracy, precision, recall, f1_score, roc_auc
    - Log model artifact
    - Save confusion matrix visualization
    """
    # TODO: Implement training with MLflow tracking
    pass


def train_random_forest(X_train, y_train, X_val, y_val):
    """
    TODO: Train Random Forest model.
    - Log parameters: model_type, n_estimators, max_depth, min_samples_split
    - Log all classification metrics
    - Log feature importance plot
    """
    # TODO: Implement training with MLflow tracking
    pass


def train_gradient_boosting(X_train, y_train, X_val, y_val):
    """
    TODO: Train Gradient Boosting model.
    - Log parameters: model_type, learning_rate, n_estimators, max_depth
    - Log all classification metrics
    - Compare with previous models
    """
    # TODO: Implement training with MLflow tracking
    pass


def compare_experiments():
    """
    TODO: Compare all experiments and select best model.
    - Retrieve all runs from experiment
    - Sort by F1 score or ROC-AUC
    - Print comparison table
    """
    # TODO: Implement experiment comparison
    pass


# ============================================================
# TASK 3: HYPERPARAMETER TUNING (30 min)
# ============================================================

def hyperparameter_tuning(X_train, y_train, X_val, y_val):
    """
    TODO: Perform grid search for Random Forest hyperparameters.

    Grid:
    - n_estimators: [50, 100, 200]
    - max_depth: [5, 10, 15]
    - min_samples_split: [2, 5, 10]

    Total combinations: 3 × 3 × 3 = 27

    - Create parent MLflow run for grid search
    - Log each combination as nested run
    - Track best model and parameters
    - Log parameter importance plots

    Returns:
        best_model, best_params, best_f1_score
    """
    # TODO: Implement grid search with MLflow nested runs
    pass


# ============================================================
# TASK 4: MODEL REGISTRY (25 min)
# ============================================================

def register_best_model(experiment_name, model_name="churn_prediction_model"):
    """
    TODO: Register best model in MLflow Model Registry.
    - Find best run by F1 score
    - Register model with name
    - Add model description and metadata tags
    - Transition to Staging, then Production

    Returns:
        model_version
    """
    # TODO: Implement model registration
    pass


def test_model_from_registry(model_name, X_test):
    """
    TODO: Load model from registry and test predictions.
    - Load model from Production stage
    - Make predictions on test set
    - Print sample predictions
    """
    # TODO: Implement model loading and testing
    pass


# ============================================================
# TASK 5: MODEL DEPLOYMENT (30 min)
# ============================================================

def batch_inference(model_name, num_customers=100):
    """
    TODO: Perform batch inference for new customers.
    - Generate new customer data
    - Load production model
    - Make predictions
    - Save results to Delta table 'churn_predictions'
    - Include: customer_id, churn_prediction, churn_probability, risk_level, scored_at

    Risk levels:
    - High: probability > 0.7
    - Medium: probability > 0.4
    - Low: probability <= 0.4
    """
    # TODO: Implement batch scoring pipeline
    pass


def predict_churn_realtime(customer_data, model_name="churn_prediction_model"):
    """
    TODO: Real-time prediction function (REST API simulation).

    Args:
        customer_data: Dictionary with customer features

    Returns:
        Dictionary with prediction results
    """
    # TODO: Implement real-time prediction
    pass


# ============================================================
# TASK 6: MONITORING & DRIFT DETECTION (25 min)
# ============================================================

def simulate_monitoring_data(model, X_val, y_val, days=30):
    """
    TODO: Simulate 30 days of model performance monitoring.
    - For each day, calculate metrics
    - Simulate gradual performance degradation
    - Save to 'model_performance_monitoring' Delta table

    Returns:
        monitoring_df with daily metrics
    """
    # TODO: Implement performance monitoring simulation
    pass


def detect_feature_drift(X_train, X_production, threshold=0.05):
    """
    TODO: Detect feature drift using Kolmogorov-Smirnov test.

    Args:
        X_train: Training data features
        X_production: Recent production data features
        threshold: p-value threshold for drift detection

    Returns:
        DataFrame with drift results per feature
    """
    # TODO: Implement drift detection
    pass


def monitor_prediction_drift():
    """
    TODO: Monitor prediction distribution changes.
    - Compare baseline (first week) vs current (last week)
    - Alert if drift > 5%
    - Recommend retraining if needed
    """
    # TODO: Implement prediction drift monitoring
    pass


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution pipeline."""
    print("=" * 60)
    print("Exercise 06: ML with MLflow - Customer Churn Prediction")
    print("=" * 60)

    # Task 1: Data Preparation
    print("\n[Task 1] Preparing data and engineering features...")
    # TODO: Call prepare_ml_datasets()

    # Task 2: Experiment Tracking
    print("\n[Task 2] Training models with MLflow experiment tracking...")
    # TODO: Set up experiment and train 3 models

    # Task 3: Hyperparameter Tuning
    print("\n[Task 3] Performing hyperparameter tuning...")
    # TODO: Run grid search

    # Task 4: Model Registry
    print("\n[Task 4] Registering best model...")
    # TODO: Register and transition model stages

    # Task 5: Deployment
    print("\n[Task 5] Deploying model for inference...")
    # TODO: Run batch inference and test real-time API

    # Task 6: Monitoring
    print("\n[Task 6] Setting up monitoring and drift detection...")
    # TODO: Simulate monitoring and detect drift

    print("\n" + "=" * 60)
    print("✅ All tasks complete! Run validate.py to check your work.")
    print("=" * 60)


if __name__ == "__main__":
    main()
