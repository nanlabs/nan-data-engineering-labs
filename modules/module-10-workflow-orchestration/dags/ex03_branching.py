"""
Ejercicio 03: Branching y Dependencias Complejas
Demuestra branching condicional y diferentes trigger rules
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

def check_data_size(**context):
    """
    Determina la ruta de procesamiento basándose en el tamaño de datos
    """
    import random
    data_size = random.randint(1, 1000)

    print(f"Tamaño de datos: {data_size} MB")

    # Branch basado en tamaño
    if data_size < 100:
        print("→ Ruta: Procesamiento PEQUEÑO")
        return 'small_processing'
    elif data_size < 500:
        print("→ Ruta: Procesamiento MEDIANO")
        return 'medium_processing'
    else:
        print("→ Ruta: Procesamiento GRANDE")
        return 'large_processing'

def small_process():
    print("✓ Procesamiento rápido para dataset pequeño")
    return "small_complete"

def medium_process():
    print("✓ Procesamiento estándar para dataset mediano")
    return "medium_complete"

def large_process():
    print("✓ Procesamiento distribuido para dataset grande")
    return "large_complete"

def consolidate_results(**context):
    """
    Consolida resultados de cualquier rama
    """
    ti = context['ti']

    # Intentar obtener resultado de cada rama
    for task_id in ['small_processing', 'medium_processing', 'large_processing']:
        result = ti.xcom_pull(task_ids=task_id)
        if result:
            print(f"✓ Resultado consolidado: {result}")
            return result

    return "consolidation_complete"

with DAG(
    'ex03_branching',
    default_args=default_args,
    description='DAG con branching condicional',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ejercicio', 'branching', 'avanzado'],
) as dag:

    # Inicio: Verificar datos
    start = BashOperator(
        task_id='start',
        bash_command='echo "Iniciando pipeline con branching..."',
    )

    # Branch: Decidir ruta de procesamiento
    branch = BranchPythonOperator(
        task_id='branch',
        python_callable=check_data_size,
        provide_context=True,
    )

    # Rutas alternativas
    small = PythonOperator(
        task_id='small_processing',
        python_callable=small_process,
    )

    medium = PythonOperator(
        task_id='medium_processing',
        python_callable=medium_process,
    )

    large = PythonOperator(
        task_id='large_processing',
        python_callable=large_process,
    )

    # Consolidar resultados (se ejecuta sin importar qué rama se tomó)
    consolidate = PythonOperator(
        task_id='consolidate',
        python_callable=consolidate_results,
        provide_context=True,
        trigger_rule='none_failed_min_one_success',
    )

    # Finalizar
    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline completado exitosamente"',
    )

    # Flujo de dependencias
    start >> branch
    branch >> [small, medium, large]
    [small, medium, large] >> consolidate >> end
