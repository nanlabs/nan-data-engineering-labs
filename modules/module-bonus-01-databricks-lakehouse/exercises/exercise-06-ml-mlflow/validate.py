"""
Exercise 06: ML with MLflow - Validation Script
Validates all 6 tasks for the ML pipeline.
"""

import sys
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# MLflow
import mlflow
from mlflow.tracking import MlflowClient

# Initialize Spark
spark = SparkSession.builder \
    .appName("ChurnValidation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Constants
EXPERIMENT_NAME = "/Users/analyst/churn-prediction"
MODEL_NAME = "churn_prediction_model"
TOTAL_SCORE = 0
MAX_SCORE = 100


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_task(task_name, points):
    """Decorator for task checking."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            global TOTAL_SCORE
            print(f"\n[{task_name}] (Max: {points} points)")
            try:
                earned_points = func(*args, **kwargs)
                TOTAL_SCORE += earned_points
                return earned_points
            except Exception as e:
                print(f"  ❌ Error checking task: {e}")
                return 0
        return wrapper
    return decorator


@check_task("Task 1: Data Preparation", 15)
def validate_task_1():
    """Validate data preparation and feature engineering."""
    points = 0

    # Check churn_data table exists
    try:
        churn_df = spark.table("churn_data")
        count = churn_df.count()

        if count >= 4500 and count <= 5500:
            print(f"  ✅ churn_data table exists ({count} rows)")
            points += 3
        else:
            print(f"  ❌ churn_data table has {count} rows (expected ~5000)")

    except Exception as e:
        print(f"  ❌ churn_data table not found: {e}")
        return points

    # Check churn rate
    churn_count = churn_df.filter(col("churned") == True).count()
    churn_rate = (churn_count / count) * 100

    if churn_rate >= 10 and churn_rate <= 20:
        print(f"  ✅ Churn rate: {churn_rate:.1f}% (expected ~15%)")
        points += 3
    else:
        print(f"  ❌ Churn rate: {churn_rate:.1f}% (expected 10-20%)")

    # Check required columns
    required_cols = ['customer_id', 'age', 'subscription_type', 'monthly_fee',
                     'num_logins_30d', 'churned']
    missing_cols = [col for col in required_cols if col not in churn_df.columns]

    if len(missing_cols) == 0:
        print("  ✅ All required columns present")
        points += 3
    else:
        print(f"  ❌ Missing columns: {missing_cols}")

    # Check feature engineering
    sample = churn_df.limit(1).toPandas()
    if 'engagement_score' in sample.columns or 'payment_risk' in sample.columns:
        print("  ✅ Feature engineering indicators found")
        points += 3
    else:
        print("  ⚠️ Feature engineering not verified in table")
        points += 1

    # Check no missing values in critical fields
    null_counts = churn_df.select([col(c).isNull().cast("int").alias(c)
                                    for c in churn_df.columns]).agg(*[
        spark.sql.functions.sum(c).alias(c) for c in churn_df.columns
    ]).collect()[0].asDict()

    critical_nulls = sum([null_counts.get(c, 0) for c in required_cols])

    if critical_nulls == 0:
        print("  ✅ No missing values in critical fields")
        points += 3
    else:
        print(f"  ❌ Found {critical_nulls} missing values in critical fields")

    return points


@check_task("Task 2: Experiment Tracking", 20)
def validate_task_2():
    """Validate MLflow experiment tracking."""
    points = 0

    # Check experiment exists
    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment:
            print(f"  ✅ MLflow experiment exists: {EXPERIMENT_NAME}")
            points += 4
        else:
            print(f"  ❌ MLflow experiment not found: {EXPERIMENT_NAME}")
            return points
    except Exception as e:
        print(f"  ❌ Error accessing MLflow: {e}")
        return points

    # Check runs exist
    try:
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

        if len(runs) >= 3:
            print(f"  ✅ Found {len(runs)} experiment runs (expected ≥3)")
            points += 4
        else:
            print(f"  ❌ Found {len(runs)} runs (expected ≥3 models)")
            return points
    except Exception as e:
        print(f"  ❌ Error retrieving runs: {e}")
        return points

    # Check metrics logged
    metrics_present = True
    required_metrics = ['f1_score', 'roc_auc', 'accuracy']

    for metric in required_metrics:
        if f'metrics.{metric}' not in runs.columns or runs[f'metrics.{metric}'].isna().all():
            metrics_present = False
            break

    if metrics_present:
        print("  ✅ All required metrics logged")
        points += 4
    else:
        print("  ❌ Some metrics missing")

    # Check model artifacts
    first_run = runs.iloc[0]
    if 'tags.mlflow.log-model.history' in runs.columns:
        print("  ✅ Model artifacts logged")
        points += 4
    else:
        print("  ⚠️ Model artifacts not verified")
        points += 2

    # Check performance
    best_f1 = runs['metrics.f1_score'].max()
    best_auc = runs['metrics.roc_auc'].max()

    if best_f1 >= 0.65:
        print(f"  ✅ Best F1 score: {best_f1:.4f} (≥0.65)")
        points += 2
    else:
        print(f"  ⚠️ Best F1 score: {best_f1:.4f} (expected ≥0.65)")

    if best_auc >= 0.75:
        print(f"  ✅ Best ROC-AUC: {best_auc:.4f} (≥0.75)")
        points += 2
    else:
        print(f"  ⚠️ Best ROC-AUC: {best_auc:.4f} (expected ≥0.75)")

    return points


@check_task("Task 3: Hyperparameter Tuning", 20)
def validate_task_3():
    """Validate hyperparameter tuning."""
    points = 0

    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

        # Check for grid search runs (should have nested runs or multiple similar runs)
        if len(runs) >= 27:
            print(f"  ✅ Found {len(runs)} runs (≥27 for grid search)")
            points += 8
        elif len(runs) >= 10:
            print(f"  ⚠️ Found {len(runs)} runs (expected ≥27 for full grid)")
            points += 4
        else:
            print(f"  ❌ Found {len(runs)} runs (expected ≥27)")
            return points

        # Check for parameter variations
        param_cols = [col for col in runs.columns if col.startswith('params.')]

        if len(param_cols) >= 3:
            print(f"  ✅ Multiple parameters tracked ({len(param_cols)} params)")
            points += 4
        else:
            print("  ⚠️ Limited parameter tracking")
            points += 2

        # Check for parent/nested run structure
        if 'tags.mlflow.parentRunId' in runs.columns:
            nested_runs = runs[runs['tags.mlflow.parentRunId'].notna()]
            if len(nested_runs) >= 20:
                print(f"  ✅ Nested runs detected ({len(nested_runs)} nested)")
                points += 4
            else:
                print("  ⚠️ Some nested runs found")
                points += 2
        else:
            print("  ⚠️ Nested run structure not detected")
            points += 1

        # Check for best parameters identified
        best_run = runs.loc[runs['metrics.f1_score'].idxmax()]
        best_params = {k.replace('params.', ''): v
                      for k, v in best_run.items()
                      if k.startswith('params.') and pd.notna(v)}

        if len(best_params) >= 2:
            print(f"  ✅ Best parameters identified: {list(best_params.keys())}")
            points += 4
        else:
            print("  ⚠️ Best parameters not fully tracked")
            points += 2

    except Exception as e:
        print(f"  ❌ Error validating tuning: {e}")

    return points


@check_task("Task 4: Model Registry", 15)
def validate_task_4():
    """Validate model registry."""
    points = 0

    client = MlflowClient()

    # Check model registered
    try:
        registered_models = client.search_registered_models()
        model_found = False

        for rm in registered_models:
            if rm.name == MODEL_NAME:
                model_found = True
                print(f"  ✅ Model registered: {MODEL_NAME}")
                points += 5
                break

        if not model_found:
            print(f"  ❌ Model not found in registry: {MODEL_NAME}")
            return points

    except Exception as e:
        print(f"  ❌ Error accessing model registry: {e}")
        return points

    # Check model versions
    try:
        versions = client.search_model_versions(f"name='{MODEL_NAME}'")

        if len(versions) >= 1:
            print(f"  ✅ Model has {len(versions)} version(s)")
            points += 3
        else:
            print("  ❌ No model versions found")
            return points

    except Exception as e:
        print(f"  ❌ Error retrieving versions: {e}")
        return points

    # Check model stage
    production_versions = [v for v in versions if v.current_stage == "Production"]

    if len(production_versions) > 0:
        print("  ✅ Model in Production stage")
        points += 4
    else:
        staging_versions = [v for v in versions if v.current_stage == "Staging"]
        if len(staging_versions) > 0:
            print("  ⚠️ Model in Staging (expected Production)")
            points += 2
        else:
            print("  ❌ Model not in Production or Staging")

    # Check model metadata
    latest_version = versions[0]
    if latest_version.description or len(latest_version.tags) > 0:
        print("  ✅ Model metadata (description/tags) present")
        points += 3
    else:
        print("  ⚠️ Model metadata not found")
        points += 1

    return points


@check_task("Task 5: Model Deployment", 15)
def validate_task_5():
    """Validate model deployment."""
    points = 0

    # Check batch inference results
    try:
        predictions_df = spark.table("churn_predictions")
        count = predictions_df.count()

        if count >= 50:
            print(f"  ✅ Batch predictions table exists ({count} rows)")
            points += 5
        else:
            print(f"  ⚠️ Batch predictions table has {count} rows (expected ≥100)")
            points += 2
    except Exception as e:
        print(f"  ❌ churn_predictions table not found: {e}")
        return points

    # Check required columns
    required_cols = ['customer_id', 'churn_prediction', 'churn_probability']
    missing_cols = [col for col in required_cols if col not in predictions_df.columns]

    if len(missing_cols) == 0:
        print("  ✅ All prediction columns present")
        points += 3
    else:
        print(f"  ❌ Missing columns: {missing_cols}")

    # Check risk categories
    if 'risk_category' in predictions_df.columns:
        risk_counts = predictions_df.groupBy('risk_category').count().collect()
        categories = [row['risk_category'] for row in risk_counts]

        if any(cat in ['High', 'Medium', 'Low'] for cat in categories):
            print(f"  ✅ Risk categories present: {categories}")
            points += 3
        else:
            print("  ⚠️ Risk categories found but unexpected values")
            points += 1
    else:
        print("  ⚠️ risk_category column not found")
        points += 1

    # Check predictions are valid
    sample = predictions_df.limit(10).toPandas()
    probs = sample['churn_probability']

    if (probs >= 0).all() and (probs <= 1).all():
        print("  ✅ Probabilities in valid range [0, 1]")
        points += 2
    else:
        print("  ❌ Invalid probability values detected")

    # Check timestamp
    if 'scored_at' in predictions_df.columns:
        print("  ✅ Timestamp column present")
        points += 2
    else:
        print("  ⚠️ scored_at timestamp not found")
        points += 1

    return points


@check_task("Task 6: Monitoring & Drift Detection", 15)
def validate_task_6():
    """Validate monitoring and drift detection."""
    points = 0

    # Check monitoring table
    try:
        monitoring_df = spark.table("model_performance_monitoring")
        count = monitoring_df.count()

        if count >= 20:
            print(f"  ✅ Monitoring table exists ({count} days)")
            points += 5
        else:
            print(f"  ⚠️ Monitoring table has {count} rows (expected ≥30)")
            points += 2
    except Exception as e:
        print(f"  ❌ model_performance_monitoring table not found: {e}")
        return points

    # Check required metrics
    required_metrics = ['date', 'accuracy', 'f1_score', 'roc_auc']
    missing_metrics = [col for col in required_metrics if col not in monitoring_df.columns]

    if len(missing_metrics) == 0:
        print("  ✅ All monitoring metrics present")
        points += 3
    else:
        print(f"  ❌ Missing metrics: {missing_metrics}")

    # Check metrics values
    sample = monitoring_df.limit(20).toPandas()

    if 'f1_score' in sample.columns:
        avg_f1 = sample['f1_score'].mean()
        if avg_f1 >= 0.60:
            print(f"  ✅ Average F1 score: {avg_f1:.4f}")
            points += 3
        else:
            print(f"  ⚠️ Low average F1 score: {avg_f1:.4f}")
            points += 1

    # Check drift detection metrics
    if 'predicted_churn_rate' in sample.columns and 'actual_churn_rate' in sample.columns:
        print("  ✅ Drift detection metrics present")
        points += 2
    else:
        print("  ⚠️ Drift detection metrics not found")
        points += 1

    # Check monitoring completeness
    if len(sample) >= 20:
        print("  ✅ Sufficient monitoring history")
        points += 2
    else:
        print("  ⚠️ Limited monitoring history")
        points += 1

    return points


def print_summary():
    """Print validation summary."""
    print_section("VALIDATION SUMMARY")

    percentage = (TOTAL_SCORE / MAX_SCORE) * 100

    print(f"\n  Total Score: {TOTAL_SCORE}/{MAX_SCORE} ({percentage:.1f}%)")
    print()

    if percentage >= 90:
        print("  🎉 Excellent! All tasks completed successfully!")
        print("  💡 You've built a complete MLOps pipeline with MLflow.")
    elif percentage >= 75:
        print("  ✅ Great work! Most tasks completed.")
        print("  💡 Review failed tasks and ensure all features are implemented.")
    elif percentage >= 60:
        print("  ⚠️ Good progress, but some tasks need attention.")
        print("  💡 Check the failed validations above.")
    else:
        print("  ❌ More work needed to complete the exercise.")
        print("  💡 Review the README and solution.py for guidance.")

    print()
    print("  Deliverables:")
    print("  - MLflow experiment with 3+ models tracked")
    print("  - Hyperparameter tuning (27 combinations)")
    print("  - Model registered in Production stage")
    print("  - Batch predictions (100 customers)")
    print("  - Monitoring data (30 days)")
    print()


def main():
    """Main validation execution."""
    print_section("Exercise 06: ML with MLflow - Validation")
    print("\nValidating your ML pipeline implementation...\n")

    # Run all validations
    validate_task_1()
    validate_task_2()
    validate_task_3()
    validate_task_4()
    validate_task_5()
    validate_task_6()

    # Print summary
    print_summary()

    # Exit with appropriate code
    if TOTAL_SCORE >= 75:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
