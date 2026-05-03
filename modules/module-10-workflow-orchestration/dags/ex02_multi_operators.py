"""
Ejercicio 02: Múltiples Operadores
Demuestra el uso de diferentes tipos de operadores en Airflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def process_data():
    """
    Procesa datos con Python
    """
    import random
    records = random.randint(100, 1000)
    print(f"Procesados {records} registros")
    return records

def validate_data(**context):
    """
    Valida la calidad de los datos procesados
    """
    ti = context['ti']
    records = ti.xcom_pull(task_ids='process')

    if records < 500:
        print(f"⚠️  Advertencia: Solo {records} registros procesados (< 500)")
    else:
        print(f"✅ Validación exitosa: {records} registros")

    return records >= 100  # Retorna True si pasó validación

with DAG(
    'ex02_multi_operators',
    default_args=default_args,
    description='DAG con múltiples tipos de operadores',
    schedule_interval='0 */6 * * *',  # Cada 6 horas
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ejercicio', 'operadores'],
) as dag:

    # BashOperator: Preparar directorio de trabajo
    prepare = BashOperator(
        task_id='prepare',
        bash_command='echo "Preparando entorno..." && mkdir -p /tmp/airflow_ex02',
    )

    # PythonOperator: Procesar datos
    process = PythonOperator(
        task_id='process',
        python_callable=process_data,
    )

    # PythonOperator: Validar datos
    validate = PythonOperator(
        task_id='validate',
        python_callable=validate_data,
        provide_context=True,
    )

    # BashOperator: Generar reporte
    report = BashOperator(
        task_id='report',
        bash_command='echo "Reporte generado: $(date)" > /tmp/airflow_ex02/report.txt',
    )

    # BashOperator: Cleanup
    cleanup = BashOperator(
        task_id='cleanup',
        bash_command='echo "Limpieza completada" && rm -rf /tmp/airflow_ex02',
        trigger_rule='all_done',  # Se ejecuta siempre, incluso si hay fallos
    )

    # Pipeline: prepare → process → validate → report → cleanup
    prepare >> process >> validate >> report >> cleanup
