"""
Ejercicio 01: Primer DAG - Hello World
DAG simple para introducir conceptos básicos de Airflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def hello_world():
    """
    Función simple que imprime un saludo
    """
    print("¡Hola Mundo desde Airflow!")
    print(f"Ejecutado en: {datetime.now()}")
    return "¡Éxito!"

with DAG(
    'ex01_hello_world',
    default_args=default_args,
    description='Mi primer DAG en Airflow',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ejercicio', 'basico', 'ejemplo'],
) as dag:

    # Task 1: Hello World con PythonOperator
    hello_task = PythonOperator(
        task_id='hello_task',
        python_callable=hello_world,
    )

    # Task 2: Comando bash simple
    bash_task = BashOperator(
        task_id='bash_task',
        bash_command='echo "Ejecutando comando bash en Airflow"',
    )

    # Task 3: Verificar fecha de ejecución
    date_task = BashOperator(
        task_id='date_task',
        bash_command='date',
    )

    # Definir dependencias: ejecución secuencial
    hello_task >> bash_task >> date_task
