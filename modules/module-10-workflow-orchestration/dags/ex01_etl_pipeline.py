"""
Ejercicio 01: Pipeline ETL con XComs
Demuestra paso de datos entre tasks usando XComs
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract(**context):
    """
    Extrae datos simulados
    """
    data = {
        'users': [
            {'id': 1, 'name': 'Alice', 'age': 30},
            {'id': 2, 'name': 'Bob', 'age': 25},
            {'id': 3, 'name': 'Charlie', 'age': 35},
        ]
    }
    print(f"Extrayendo {len(data['users'])} usuarios")
    # Push data to XCom
    return data

def transform(**context):
    """
    Transforma los datos extraídos
    """
    # Pull data from XCom
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')

    # Transformar: agregar campo processed y filtrar por edad
    transformed = []
    for user in data['users']:
        if user['age'] >= 30:
            user['processed'] = True
            user['category'] = 'senior'
            transformed.append(user)

    print(f"Transformados {len(transformed)} usuarios (edad >= 30)")
    return {'users': transformed}

def load(**context):
    """
    Carga los datos transformados
    """
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform')

    print(f"Cargando {len(data['users'])} usuarios a destino")
    for user in data['users']:
        print(f"  → Usuario {user['id']}: {user['name']} ({user['category']})")

    return f"Cargados {len(data['users'])} usuarios exitosamente"

with DAG(
    'ex01_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL simple con XComs',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ejercicio', 'etl', 'xcoms'],
) as dag:

    extract_task = PythonOperator(
        task_id='extract',
        python_callable=extract,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id='transform',
        python_callable=transform,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id='load',
        python_callable=load,
        provide_context=True,
    )

    # ETL flow
    extract_task >> transform_task >> load_task
