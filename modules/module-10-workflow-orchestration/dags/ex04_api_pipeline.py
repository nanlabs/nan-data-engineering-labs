"""
Ejercicio 04: Pipeline ETL Real con API
Pipeline completo: API → Transform → Database
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_from_api(**context):
    """
    Extrae datos de una API pública (JSONPlaceholder)
    """
    import requests

    print("📥 Extrayendo datos de API...")

    # Extraer usuarios
    users_response = requests.get('https://jsonplaceholder.typicode.com/users')
    users = users_response.json()

    # Extraer posts
    posts_response = requests.get('https://jsonplaceholder.typicode.com/posts')
    posts = posts_response.json()

    print(f"✓ Extraídos {len(users)} usuarios")
    print(f"✓ Extraídos {len(posts)} posts")

    return {
        'users': users,
        'posts': posts,
        'extracted_at': datetime.now().isoformat()
    }

def transform_data(**context):
    """
    Transforma los datos extraídos
    """
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')

    print("🔄 Transformando datos...")

    # Calcular estadísticas por usuario
    users_stats = []
    for user in data['users']:
        user_posts = [p for p in data['posts'] if p['userId'] == user['id']]

        stats = {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'company': user['company']['name'],
            'total_posts': len(user_posts),
            'avg_title_length': sum(len(p['title']) for p in user_posts) / len(user_posts) if user_posts else 0,
            'processed_at': datetime.now().isoformat()
        }
        users_stats.append(stats)

    print(f"✓ Transformados datos de {len(users_stats)} usuarios")

    return users_stats

def load_to_database(**context):
    """
    Simula carga a base de datos
    En producción, usar PostgresHook o similar
    """
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform')

    print("💾 Cargando datos a base de datos...")

    # Simular INSERT statements
    for record in data:
        print(f"  INSERT INTO user_stats VALUES ({record['user_id']}, '{record['username']}', {record['total_posts']} posts)")

    print(f"✓ Cargados {len(data)} registros exitosamente")

    return {
        'records_loaded': len(data),
        'loaded_at': datetime.now().isoformat()
    }

def generate_report(**context):
    """
    Genera reporte del pipeline
    """
    ti = context['ti']
    extract_info = ti.xcom_pull(task_ids='extract')
    load_info = ti.xcom_pull(task_ids='load')

    report = f"""
    📊 REPORTE DEL PIPELINE ETL
    ════════════════════════════
    📥 Extracción:
       - Usuarios extraídos: {len(extract_info['users'])}
       - Posts extraídos: {len(extract_info['posts'])}
       - Hora extracción: {extract_info['extracted_at']}

    💾 Carga:
       - Registros cargados: {load_info['records_loaded']}
       - Hora carga: {load_info['loaded_at']}

    ✅ Pipeline completado exitosamente
    """

    print(report)
    return report

with DAG(
    'ex04_api_to_db_pipeline',
    default_args=default_args,
    description='Pipeline ETL completo: API → Transform → Database',
    schedule_interval='0 */12 * * *',  # Cada 12 horas
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ejercicio', 'etl', 'api', 'pipeline'],
) as dag:

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_from_api,
        provide_context=True,
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        provide_context=True,
    )

    load = PythonOperator(
        task_id='load',
        python_callable=load_to_database,
        provide_context=True,
    )

    report = PythonOperator(
        task_id='report',
        python_callable=generate_report,
        provide_context=True,
    )

    # Pipeline ETL
    extract >> transform >> load >> report
