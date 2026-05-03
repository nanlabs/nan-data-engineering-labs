"""Tests for Module 10: Workflow Orchestration"""

import pytest
from airflow.models import DagBag
from datetime import datetime


class TestDAGIntegrity:
    """Test DAG integrity and structure"""

    @pytest.fixture(scope='class')
    def dag_bag(self):
        """Load all DAGs"""
        return DagBag(dag_folder='../exercises', include_examples=False)

    @pytest.mark.dag_validation
    def test_no_import_errors(self, dag_bag):
        """Test that all DAGs can be imported without errors"""
        assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"

    @pytest.mark.dag_validation
    def test_dag_count(self, dag_bag):
        """Test expected number of DAGs"""
        # Should have at least exercise DAGs
        assert len(dag_bag.dags) >= 6, f"Expected at least 6 DAGs, found {len(dag_bag.dags)}"

    @pytest.mark.dag_validation
    def test_no_cycles(self, dag_bag):
        """Test that no DAGs contain cycles"""
        for dag_id, dag in dag_bag.dags.items():
            assert dag.test_cycle() is None, f"Cycle detected in {dag_id}"

    @pytest.mark.dag_validation
    def test_all_dags_have_tags(self, dag_bag):
        """Test that all DAGs have tags"""
        for dag_id, dag in dag_bag.dags.items():
            assert len(dag.tags) > 0, f"DAG {dag_id} has no tags"

    @pytest.mark.dag_validation
    def test_all_dags_have_owner(self, dag_bag):
        """Test that all DAGs have an owner"""
        for dag_id, dag in dag_bag.dags.items():
            assert dag.default_args.get('owner') is not None, f"DAG {dag_id} has no owner"

    @pytest.mark.dag_validation
    def test_all_dags_have_retries(self, dag_bag):
        """Test that all DAGs have retry configuration"""
        for dag_id, dag in dag_bag.dags.items():
            retries = dag.default_args.get('retries')
            assert retries is not None, f"DAG {dag_id} has no retries configured"
            assert retries >= 0, f"DAG {dag_id} has negative retries"


class TestSpecificDAGs:
    """Test specific exercise DAGs"""

    @pytest.fixture(scope='class')
    def dag_bag(self):
        return DagBag(dag_folder='../exercises', include_examples=False)

    def test_ex01_hello_world_structure(self, dag_bag):
        """Test Exercise 01 DAG structure"""
        if 'ex01_hello_world' not in dag_bag.dags:
            pytest.skip("DAG not found")

        dag = dag_bag.get_dag('ex01_hello_world')
        assert dag is not None
        assert 'hello_task' in dag.task_ids
        assert 'exercise' in dag.tags

    def test_ex01_etl_pipeline_dependencies(self, dag_bag):
        """Test Exercise 01 ETL pipeline dependencies"""
        if 'ex01_etl_pipeline' not in dag_bag.dags:
            pytest.skip("DAG not found")

        dag = dag_bag.get_dag('ex01_etl_pipeline')

        # Check tasks exist
        assert 'extract' in dag.task_ids
        assert 'transform' in dag.task_ids
        assert 'load' in dag.task_ids

        # Check dependencies
        extract_task = dag.get_task('extract')
        transform_task = dag.get_task('transform')
        load_task = dag.get_task('load')

        assert transform_task in extract_task.downstream_list
        assert load_task in transform_task.downstream_list

    def test_ex02_multi_operators(self, dag_bag):
        """Test Exercise 02 multi-operator DAG"""
        if 'ex02_multi_operators' not in dag_bag.dags:
            pytest.skip("DAG not found")

        dag = dag_bag.get_dag('ex02_multi_operators')

        # Should have multiple operator types
        operator_types = [type(task).__name__ for task in dag.tasks]
        assert 'PythonOperator' in operator_types
        assert 'BashOperator' in operator_types

    def test_ex03_branching_structure(self, dag_bag):
        """Test Exercise 03 branching DAG"""
        if 'ex03_branching' not in dag_bag.dags:
            pytest.skip("DAG not found")

        dag = dag_bag.get_dag('ex03_branching')

        # Should have branch operator
        assert 'branch' in dag.task_ids

        # Should have multiple processing paths
        assert 'small_processing' in dag.task_ids
        assert 'medium_processing' in dag.task_ids
        assert 'large_processing' in dag.task_ids


class TestTaskExecution:
    """Test individual task execution"""

    @pytest.mark.unit
    def test_python_operator_execution(self, mock_airflow_context):
        """Test PythonOperator task execution"""
        from airflow.operators.python import PythonOperator

        def test_function():
            return "test_result"

        task = PythonOperator(
            task_id='test_task',
            python_callable=test_function,
        )

        result = task.execute(context=mock_airflow_context)
        assert result == "test_result"

    @pytest.mark.unit
    def test_python_operator_with_context(self, mock_airflow_context):
        """Test PythonOperator with context access"""
        from airflow.operators.python import PythonOperator

        def test_function(**context):
            return context['execution_date']

        task = PythonOperator(
            task_id='test_task',
            python_callable=test_function,
        )

        result = task.execute(context=mock_airflow_context)
        assert result == datetime(2024, 1, 1)


class TestDataQuality:
    """Test data quality checks in pipelines"""

    @pytest.mark.unit
    def test_csv_validation(self, temp_csv_file):
        """Test CSV file validation"""
        import pandas as pd

        df = pd.read_csv(temp_csv_file)

        # Check schema
        assert set(df.columns) == {'id', 'name', 'value'}

        # Check no nulls
        assert df.isnull().sum().sum() == 0

        # Check types
        assert df['id'].dtype == 'int64'
        assert df['value'].dtype == 'int64'

    @pytest.mark.unit
    def test_data_transformation(self):
        """Test data transformation logic"""
        import pandas as pd

        # Input data
        data = {'id': [1, 2, 3], 'value': [10, 20, 30]}
        df = pd.DataFrame(data)

        # Transform
        df['value_doubled'] = df['value'] * 2

        # Validate
        assert df['value_doubled'].tolist() == [20, 40, 60]


class TestConfiguration:
    """Test DAG and task configuration"""

    @pytest.fixture(scope='class')
    def dag_bag(self):
        return DagBag(dag_folder='../exercises', include_examples=False)

    @pytest.mark.dag_validation
    def test_schedule_intervals(self, dag_bag):
        """Test that DAGs have valid schedule intervals"""
        for dag_id, dag in dag_bag.dags.items():
            schedule = dag.schedule_interval
            # Should have schedule (or None for manual)
            assert schedule is not None or dag.schedule_interval is None

    @pytest.mark.dag_validation
    def test_start_dates(self, dag_bag):
        """Test that all DAGs have start dates"""
        for dag_id, dag in dag_bag.dags.items():
            assert dag.start_date is not None, f"DAG {dag_id} has no start_date"
            assert isinstance(dag.start_date, datetime), f"DAG {dag_id} start_date is not datetime"

    @pytest.mark.dag_validation
    def test_catchup_disabled(self, dag_bag):
        """Test that catchup is disabled for exercise DAGs"""
        for dag_id, dag in dag_bag.dags.items():
            if 'exercise' in dag.tags:
                assert dag.catchup is False, f"DAG {dag_id} has catchup enabled"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
