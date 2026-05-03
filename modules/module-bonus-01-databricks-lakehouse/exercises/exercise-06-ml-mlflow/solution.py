"""
Exercise 06: ML with MLflow - Complete Solution
End-to-end ML pipeline for customer churn prediction with MLflow tracking.
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, expr
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, DateType

# ML Libraries
from sklearn.model_selection import train_test_split, ParameterGrid
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

# Statistical tests
from scipy.stats import ks_2samp

# MLflow
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Initialize Spark
spark = SparkSession.builder \
    .appName("ChurnPredictionMLflow") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Set random seeds
random.seed(42)
np.random.seed(42)

# Global variables
EXPERIMENT_NAME = "/Users/analyst/churn-prediction"
MODEL_NAME = "churn_prediction_model"


# ============================================================
# TASK 1: DATA PREPARATION & FEATURE ENGINEERING
# ============================================================

def generate_churn_data(num_customers=5000):
    """Generate synthetic customer data for churn prediction."""
    print(f"  Generating {num_customers} customer records...")

    # Define parameters
    countries = ["USA", "UK", "Canada", "Germany", "France"]
    subscription_types = ["Basic", "Premium", "Enterprise"]
    subscription_fees = {"Basic": 19.99, "Premium": 49.99, "Enterprise": 99.99}

    data = []
    base_date = datetime.now() - timedelta(days=730)  # 2 years ago

    for i in range(num_customers):
        # Basic info
        customer_id = f"CUST_{i+1:05d}"
        signup_date = base_date + timedelta(days=random.randint(0, 730))
        age = random.randint(18, 75)
        country = random.choice(countries)
        subscription_type = random.choice(subscription_types)
        monthly_fee = subscription_fees[subscription_type]

        # Behavioral features
        num_logins_30d = random.randint(0, 100)
        num_support_tickets = random.randint(0, 20)
        num_failed_payments = random.randint(0, 5)
        avg_session_minutes = round(random.uniform(5, 180), 2)
        days_since_last_login = random.randint(0, 60)
        total_purchases = random.randint(0, 50)

        # Churn logic (15% churn rate with realistic patterns)
        churn_score = 0
        if num_logins_30d < 5:
            churn_score += 30
        if num_support_tickets > 10:
            churn_score += 20
        if num_failed_payments > 2:
            churn_score += 25
        if days_since_last_login > 30:
            churn_score += 25
        if subscription_type == "Basic":
            churn_score += 10

        churned = churn_score + random.randint(0, 20) > 50

        data.append({
            "customer_id": customer_id,
            "signup_date": signup_date.date(),
            "age": age,
            "country": country,
            "subscription_type": subscription_type,
            "monthly_fee": monthly_fee,
            "num_logins_30d": num_logins_30d,
            "num_support_tickets": num_support_tickets,
            "num_failed_payments": num_failed_payments,
            "avg_session_minutes": avg_session_minutes,
            "days_since_last_login": days_since_last_login,
            "total_purchases": total_purchases,
            "churned": churned
        })

    # Create Spark DataFrame
    schema = StructType([
        StructField("customer_id", StringType(), False),
        StructField("signup_date", DateType(), False),
        StructField("age", IntegerType(), False),
        StructField("country", StringType(), False),
        StructField("subscription_type", StringType(), False),
        StructField("monthly_fee", DoubleType(), False),
        StructField("num_logins_30d", IntegerType(), False),
        StructField("num_support_tickets", IntegerType(), False),
        StructField("num_failed_payments", IntegerType(), False),
        StructField("avg_session_minutes", DoubleType(), False),
        StructField("days_since_last_login", IntegerType(), False),
        StructField("total_purchases", IntegerType(), False),
        StructField("churned", BooleanType(), False)
    ])

    df = spark.createDataFrame(data, schema)

    # Save to Delta table
    df.write.format("delta").mode("overwrite").saveAsTable("churn_data")

    churn_count = df.filter(col("churned") == True).count()
    churn_rate = (churn_count / num_customers) * 100
    print(f"  ✅ Generated {num_customers} customers ({churn_count} churned, {churn_rate:.1f}%)")

    return df


def engineer_features(df):
    """Apply feature engineering transformations."""
    print("  Engineering features...")

    # Engagement score
    engagement = ((col("num_logins_30d") * 2 + col("total_purchases") * 5) /
                  (col("days_since_last_login") + 1))

    # Payment risk
    payment_risk = col("num_failed_payments") / (col("total_purchases") + 1)

    # Activity level (categorical)
    activity_level = when(col("num_logins_30d") > 20, "High") \
                     .when(col("num_logins_30d") > 10, "Medium") \
                     .otherwise("Low")

    # Tenure months
    tenure_months = expr("months_between(current_date(), signup_date)")

    # Apply transformations
    features_df = df.withColumn("engagement_score", engagement) \
                    .withColumn("payment_risk", payment_risk) \
                    .withColumn("activity_level", activity_level) \
                    .withColumn("tenure_months", tenure_months)

    print("  ✅ Feature engineering complete")

    return features_df


def prepare_ml_datasets():
    """Prepare train/validation/test splits."""
    print("  Preparing ML datasets...")

    # Generate data
    df = generate_churn_data(5000)

    # Engineer features
    features_df = engineer_features(df)

    # Convert to Pandas for sklearn
    pdf = features_df.toPandas()

    # Separate features and target
    feature_cols = ['age', 'monthly_fee', 'num_logins_30d', 'num_support_tickets',
                    'num_failed_payments', 'avg_session_minutes', 'days_since_last_login',
                    'total_purchases', 'engagement_score', 'payment_risk', 'tenure_months']

    # Encode categorical variables
    le_subscription = LabelEncoder()
    le_country = LabelEncoder()
    le_activity = LabelEncoder()

    pdf['subscription_encoded'] = le_subscription.fit_transform(pdf['subscription_type'])
    pdf['country_encoded'] = le_country.fit_transform(pdf['country'])
    pdf['activity_encoded'] = le_activity.fit_transform(pdf['activity_level'])

    feature_cols.extend(['subscription_encoded', 'country_encoded', 'activity_encoded'])

    X = pdf[feature_cols]
    y = pdf['churned'].astype(int)

    # Train/val/test split (70/15/15) with stratification
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    print(f"  ✅ Train: {len(X_train)} samples, Val: {len(X_val)} samples, Test: {len(X_test)} samples")
    print(f"  ✅ Train churn rate: {y_train.mean()*100:.1f}%")

    return X_train, X_val, X_test, y_train, y_val, y_test, feature_cols


# ============================================================
# TASK 2: EXPERIMENT TRACKING WITH MLFLOW
# ============================================================

def setup_mlflow_experiment(experiment_name=EXPERIMENT_NAME):
    """Set up MLflow experiment."""
    mlflow.set_experiment(experiment_name)
    print(f"  ✅ MLflow experiment set: {experiment_name}")


def train_logistic_regression(X_train, y_train, X_val, y_val):
    """Train logistic regression baseline."""
    print("  Training Logistic Regression...")

    with mlflow.start_run(run_name="logistic_regression_baseline"):
        # Parameters
        params = {
            "model_type": "LogisticRegression",
            "penalty": "l2",
            "C": 1.0,
            "solver": "lbfgs"
        }
        mlflow.log_params(params)

        # Train
        model = LogisticRegression(random_state=42, max_iter=1000)
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_val)
        y_pred_proba = model.predict_proba(X_val)[:, 1]

        # Metrics
        metrics = {
            "accuracy": accuracy_score(y_val, y_pred),
            "precision": precision_score(y_val, y_pred),
            "recall": recall_score(y_val, y_pred),
            "f1_score": f1_score(y_val, y_pred),
            "roc_auc": roc_auc_score(y_val, y_pred_proba)
        }
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        # Confusion matrix
        cm = confusion_matrix(y_val, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix - Logistic Regression')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.savefig("/tmp/confusion_matrix_lr.png")
        mlflow.log_artifact("/tmp/confusion_matrix_lr.png")
        plt.close()

        print(f"    ✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")

        return model, metrics


def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest model."""
    print("  Training Random Forest...")

    with mlflow.start_run(run_name="random_forest"):
        # Parameters
        params = {
            "model_type": "RandomForest",
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5
        }
        mlflow.log_params(params)

        # Train
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_val)
        y_pred_proba = model.predict_proba(X_val)[:, 1]

        # Metrics
        metrics = {
            "accuracy": accuracy_score(y_val, y_pred),
            "precision": precision_score(y_val, y_pred),
            "recall": recall_score(y_val, y_pred),
            "f1_score": f1_score(y_val, y_pred),
            "roc_auc": roc_auc_score(y_val, y_pred_proba)
        }
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        mlflow.log_dict(feature_importance.to_dict(), "feature_importance.json")

        print(f"    ✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")

        return model, metrics


def train_gradient_boosting(X_train, y_train, X_val, y_val):
    """Train Gradient Boosting model."""
    print("  Training Gradient Boosting...")

    with mlflow.start_run(run_name="gradient_boosting"):
        # Parameters
        params = {
            "model_type": "GradientBoosting",
            "learning_rate": 0.1,
            "n_estimators": 100,
            "max_depth": 5
        }
        mlflow.log_params(params)

        # Train
        model = GradientBoostingClassifier(
            learning_rate=0.1,
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_val)
        y_pred_proba = model.predict_proba(X_val)[:, 1]

        # Metrics
        metrics = {
            "accuracy": accuracy_score(y_val, y_pred),
            "precision": precision_score(y_val, y_pred),
            "recall": recall_score(y_val, y_pred),
            "f1_score": f1_score(y_val, y_pred),
            "roc_auc": roc_auc_score(y_val, y_pred_proba)
        }
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        print(f"    ✅ F1: {metrics['f1_score']:.4f}, ROC-AUC: {metrics['roc_auc']:.4f}")

        return model, metrics


def compare_experiments():
    """Compare all experiments."""
    print("  Comparing experiments...")

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        print("    ⚠️ Experiment not found")
        return

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.f1_score DESC"]
    )

    if len(runs) > 0:
        print("\n  Model Comparison:")
        comparison = runs[['tags.mlflow.runName', 'metrics.f1_score',
                          'metrics.roc_auc', 'metrics.recall']].head(3)
        print(comparison.to_string(index=False))

    return runs


# ============================================================
# TASK 3: HYPERPARAMETER TUNING
# ============================================================

def hyperparameter_tuning(X_train, y_train, X_val, y_val):
    """Perform grid search for Random Forest hyperparameters."""
    print("  Performing hyperparameter tuning (27 combinations)...")

    # Define parameter grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 10, 15],
        'min_samples_split': [2, 5, 10]
    }

    grid = list(ParameterGrid(param_grid))

    with mlflow.start_run(run_name="random_forest_grid_search") as parent_run:
        best_f1 = 0
        best_model = None
        best_params = None
        best_auc = 0

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
                if roc_auc > best_auc:
                    best_f1 = f1
                    best_auc = roc_auc
                    best_model = model
                    best_params = params

        # Log best result in parent run
        mlflow.log_params(best_params)
        mlflow.log_metric("best_f1_score", best_f1)
        mlflow.log_metric("best_roc_auc", best_auc)
        mlflow.sklearn.log_model(best_model, "best_model")

        print(f"    ✅ Best F1: {best_f1:.4f}, Best AUC: {best_auc:.4f}")
        print(f"    ✅ Best params: {best_params}")

        return best_model, best_params, best_f1


# ============================================================
# TASK 4: MODEL REGISTRY
# ============================================================

def register_best_model(experiment_name=EXPERIMENT_NAME, model_name=MODEL_NAME):
    """Register best model in MLflow Model Registry."""
    print("  Registering best model...")

    # Get experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        print("    ⚠️ Experiment not found")
        return None

    # Find best run by ROC-AUC
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["metrics.roc_auc DESC"],
        max_results=1
    )

    if len(runs) == 0:
        print("    ⚠️ No completed runs found")
        return None

    best_run = runs.iloc[0]
    best_run_id = best_run.run_id

    # Register model
    model_uri = f"runs:/{best_run_id}/model"

    try:
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name
        )

        print(f"    ✅ Model registered: {model_name} version {model_version.version}")

        # Add metadata
        client = MlflowClient()

        # Update model description
        client.update_registered_model(
            name=model_name,
            description="Customer churn prediction model. Predicts 30-day churn probability."
        )

        # Add version tags
        client.set_model_version_tag(
            name=model_name,
            version=model_version.version,
            key="training_date",
            value=datetime.now().strftime("%Y-%m-%d")
        )
        client.set_model_version_tag(
            name=model_name,
            version=model_version.version,
            key="data_version",
            value="v1.0"
        )

        # Transition to Staging
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Staging"
        )
        print("    ✅ Model transitioned to Staging")

        # Transition to Production
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Production"
        )
        print("    ✅ Model transitioned to Production")

        return model_version

    except Exception as e:
        print(f"    ⚠️ Registration error: {e}")
        return None


def test_model_from_registry(model_name, X_test):
    """Load model from registry and test predictions."""
    print("  Testing model from registry...")

    try:
        # Load production model
        model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

        # Test predictions
        test_sample = X_test.iloc[:5]
        predictions = model.predict(test_sample)
        probabilities = model.predict_proba(test_sample)[:, 1]

        print(f"    ✅ Sample predictions: {predictions}")
        print(f"    ✅ Churn probabilities: {probabilities}")

        return model

    except Exception as e:
        print(f"    ⚠️ Error loading model: {e}")
        return None


# ============================================================
# TASK 5: MODEL DEPLOYMENT
# ============================================================

def batch_inference(model_name=MODEL_NAME, num_customers=100):
    """Perform batch inference for new customers."""
    print(f"  Running batch inference on {num_customers} customers...")

    try:
        # Load production model
        model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

        # Generate new customer data (simplified for demo)
        new_data = generate_churn_data(num_customers)
        features_df = engineer_features(new_data)
        pdf = features_df.toPandas()

        # Prepare features (same encoding as training)
        le_subscription = LabelEncoder()
        le_country = LabelEncoder()
        le_activity = LabelEncoder()

        pdf['subscription_encoded'] = le_subscription.fit_transform(pdf['subscription_type'])
        pdf['country_encoded'] = le_country.fit_transform(pdf['country'])
        pdf['activity_encoded'] = le_activity.fit_transform(pdf['activity_level'])

        feature_cols = ['age', 'monthly_fee', 'num_logins_30d', 'num_support_tickets',
                        'num_failed_payments', 'avg_session_minutes', 'days_since_last_login',
                        'total_purchases', 'engagement_score', 'payment_risk', 'tenure_months',
                        'subscription_encoded', 'country_encoded', 'activity_encoded']

        X_new = pdf[feature_cols]

        # Predictions
        predictions = model.predict(X_new)
        probabilities = model.predict_proba(X_new)[:, 1]

        # Add risk categories
        risk_levels = []
        for prob in probabilities:
            if prob > 0.7:
                risk_levels.append("High")
            elif prob > 0.4:
                risk_levels.append("Medium")
            else:
                risk_levels.append("Low")

        # Create results DataFrame
        results_pdf = pd.DataFrame({
            'customer_id': pdf['customer_id'],
            'churn_prediction': predictions,
            'churn_probability': probabilities,
            'risk_category': risk_levels,
            'scored_at': datetime.now()
        })

        # Save to Delta
        results_df = spark.createDataFrame(results_pdf)
        results_df.write.format("delta").mode("overwrite").saveAsTable("churn_predictions")

        high_risk = (results_pdf['risk_category'] == 'High').sum()
        print(f"    ✅ Scored {num_customers} customers ({high_risk} high risk)")

        return results_pdf

    except Exception as e:
        print(f"    ⚠️ Batch inference error: {e}")
        return None


def predict_churn_realtime(customer_data, model_name=MODEL_NAME):
    """Real-time prediction function (REST API simulation)."""
    try:
        # Load model
        model = mlflow.sklearn.load_model(f"models:/{model_name}/Production")

        # Prepare features (simplified)
        features = [
            customer_data.get('age', 30),
            customer_data.get('monthly_fee', 49.99),
            customer_data.get('num_logins_30d', 15),
            customer_data.get('num_support_tickets', 2),
            customer_data.get('num_failed_payments', 0),
            customer_data.get('avg_session_minutes', 45.0),
            customer_data.get('days_since_last_login', 3),
            customer_data.get('total_purchases', 10),
            customer_data.get('engagement_score', 50.0),
            customer_data.get('payment_risk', 0.1),
            customer_data.get('tenure_months', 12.0),
            customer_data.get('subscription_encoded', 1),
            customer_data.get('country_encoded', 0),
            customer_data.get('activity_encoded', 1)
        ]

        # Predict
        probability = model.predict_proba([features])[0][1]
        prediction = probability > 0.5

        risk_level = "High" if probability > 0.7 else "Medium" if probability > 0.4 else "Low"

        return {
            "customer_id": customer_data.get("customer_id", "UNKNOWN"),
            "churn_prediction": bool(prediction),
            "churn_probability": float(probability),
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# TASK 6: MONITORING & DRIFT DETECTION
# ============================================================

def simulate_monitoring_data(model, X_val, y_val, days=30):
    """Simulate 30 days of model performance monitoring."""
    print(f"  Simulating {days} days of monitoring data...")

    monitoring_data = []
    base_date = datetime.now() - timedelta(days=days)

    for day in range(days):
        current_date = base_date + timedelta(days=day)

        # Simulate gradual performance degradation
        degradation_factor = 1.0 - (day / days) * 0.1  # 10% degradation over time

        # Add noise to validation data
        X_daily = X_val.copy()
        noise = np.random.normal(0, 0.05, X_daily.shape)
        X_daily_noisy = X_daily + noise * degradation_factor

        # Predictions
        y_pred = model.predict(X_daily_noisy)
        y_pred_proba = model.predict_proba(X_daily_noisy)[:, 1]

        # Calculate metrics
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred)
        recall = recall_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred)
        roc_auc = roc_auc_score(y_val, y_pred_proba)

        monitoring_data.append({
            "date": current_date.date(),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "num_predictions": len(y_pred),
            "predicted_churn_rate": y_pred.mean(),
            "actual_churn_rate": y_val.mean()
        })

    monitoring_pdf = pd.DataFrame(monitoring_data)
    monitoring_df = spark.createDataFrame(monitoring_pdf)
    monitoring_df.write.format("delta").mode("overwrite").saveAsTable("model_performance_monitoring")

    print(f"    ✅ Monitoring data saved (avg F1: {monitoring_pdf['f1_score'].mean():.4f})")

    return monitoring_pdf


def detect_feature_drift(X_train, X_production, threshold=0.05):
    """Detect feature drift using Kolmogorov-Smirnov test."""
    print("  Detecting feature drift...")

    drift_results = []

    for feature in X_train.columns:
        train_values = X_train[feature].dropna()
        prod_values = X_production[feature].dropna()

        # KS test
        statistic, p_value = ks_2samp(train_values, prod_values)

        drift_detected = p_value < threshold

        mean_change = ((prod_values.mean() - train_values.mean()) /
                      (train_values.mean() + 1e-10) * 100)

        drift_results.append({
            "feature": feature,
            "ks_statistic": statistic,
            "p_value": p_value,
            "drift_detected": drift_detected,
            "train_mean": train_values.mean(),
            "prod_mean": prod_values.mean(),
            "mean_change_pct": mean_change
        })

    drift_df = pd.DataFrame(drift_results)
    drifted_features = drift_df[drift_df['drift_detected']]

    print(f"    ✅ Drift detected in {len(drifted_features)} features")
    if len(drifted_features) > 0:
        print(f"    Features with drift: {drifted_features['feature'].tolist()}")

    return drift_df


def monitor_prediction_drift():
    """Monitor prediction distribution changes."""
    print("  Monitoring prediction drift...")

    try:
        monitoring_df = spark.table("model_performance_monitoring").toPandas()

        # Baseline (first 7 days)
        baseline = monitoring_df.head(7)['predicted_churn_rate'].mean()

        # Current (last 7 days)
        current = monitoring_df.tail(7)['predicted_churn_rate'].mean()

        drift_pct = ((current - baseline) / baseline) * 100

        if abs(drift_pct) > 5:
            print(f"    ⚠️ ALERT: Prediction drift detected! {drift_pct:+.1f}% change")
            print("    ⚠️ Recommended action: Retrain model with recent data")
        else:
            print(f"    ✅ No significant prediction drift ({drift_pct:+.1f}%)")

        return drift_pct

    except Exception as e:
        print(f"    ⚠️ Error monitoring drift: {e}")
        return None


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
    X_train, X_val, X_test, y_train, y_val, y_test, feature_cols = prepare_ml_datasets()

    # Task 2: Experiment Tracking
    print("\n[Task 2] Training models with MLflow experiment tracking...")
    setup_mlflow_experiment()
    train_logistic_regression(X_train, y_train, X_val, y_val)
    train_random_forest(X_train, y_train, X_val, y_val)
    train_gradient_boosting(X_train, y_train, X_val, y_val)
    compare_experiments()

    # Task 3: Hyperparameter Tuning
    print("\n[Task 3] Performing hyperparameter tuning...")
    best_model, best_params, best_f1 = hyperparameter_tuning(X_train, y_train, X_val, y_val)

    # Task 4: Model Registry
    print("\n[Task 4] Registering best model...")
    model_version = register_best_model()
    if model_version:
        test_model_from_registry(MODEL_NAME, X_test)

    # Task 5: Deployment
    print("\n[Task 5] Deploying model for inference...")
    batch_results = batch_inference(MODEL_NAME, 100)

    # Test real-time API
    test_customer = {
        "customer_id": "TEST_001",
        "age": 35,
        "monthly_fee": 49.99,
        "num_logins_30d": 5,
        "num_support_tickets": 8,
        "num_failed_payments": 2,
        "avg_session_minutes": 20.0,
        "days_since_last_login": 15,
        "total_purchases": 3,
        "engagement_score": 15.0,
        "payment_risk": 0.4,
        "tenure_months": 6.0,
        "subscription_encoded": 0,
        "country_encoded": 0,
        "activity_encoded": 0
    }

    prediction = predict_churn_realtime(test_customer, MODEL_NAME)
    print(f"  Real-time API test: {prediction}")

    # Task 6: Monitoring
    print("\n[Task 6] Setting up monitoring and drift detection...")
    monitoring_data = simulate_monitoring_data(best_model, X_val, y_val, 30)
    drift_report = detect_feature_drift(X_train, X_val)
    prediction_drift = monitor_prediction_drift()

    print("\n" + "=" * 60)
    print("✅ All tasks complete! Run validate.py to verify your work.")
    print("=" * 60)


if __name__ == "__main__":
    main()
