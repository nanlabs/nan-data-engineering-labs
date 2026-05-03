"""
Ejercicio 05: Monitoreo y Alertas
Demuestra SLA monitoring, callbacks y manejo de errores
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

def on_success_callback(context):
    """
    Callback ejecutado cuando un task tiene éxito
    """
    print(f"✅ SUCCESS: Task '{context['task_instance'].task_id}' completado exitosamente")
    print(f"   Duración: {context['task_instance'].duration}s")

def on_failure_callback(context):
    """
    Callback ejecutado cuando un task falla
    """
    print(f"❌ FAILURE: Task '{context['task_instance'].task_id}' falló")
    print(f"   Error: {context['exception']}")
    print(f"   Intento: {context['task_instance'].try_number}")
    # En producción: enviar a Slack, email, PagerDuty, etc.

def on_retry_callback(context):
    """
    Callback ejecutado cuando un task se reintenta
    """
    print(f"🔄 RETRY: Reintentando task '{context['task_instance'].task_id}'")
    print(f"   Intento: {context['task_instance'].try_number}")

def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """
    Callback ejecutado cuando se viola un SLA
    """
    print("⚠️  SLA VIOLATION!")
    for sla in slas:
        print(f"   Task: {sla.task_id}")
        print(f"   Expected: {sla.timestamp}")
    # En producción: alertas críticas

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=30),
    'on_success_callback': on_success_callback,
    'on_failure_callback': on_failure_callback,
    'on_retry_callback': on_retry_callback,
    'sla': timedelta(minutes=5),  # SLA de 5 minutos
}

def critical_task():
    """
    Task crítico con monitoreo
    """
    import time
    import random

    print("🔧 Ejecutando tarea crítica...")

    # Simular procesamiento
    processing_time = random.uniform(1, 3)
    time.sleep(processing_time)

    # Simular posible fallo (10% de probabilidad)
    if random.random() < 0.1:
        raise Exception("Error simulado en procesamiento")

    print(f"✓ Procesamiento completado en {processing_time:.2f}s")
    return "success"

def data_quality_check(**context):
    """
    Verifica calidad de datos
    """
    import random

    quality_score = random.uniform(0.7, 1.0)
    print(f"📊 Score de calidad: {quality_score:.2%}")

    if quality_score < 0.85:
        print("⚠️  Advertencia: Calidad de datos por debajo del umbral (85%)")

    return quality_score

def performance_monitoring(**context):
    """
    Monitorea performance del pipeline
    """
    ti = context['ti']
    task_instances = context['dag_run'].get_task_instances()

    print("📈 MÉTRICAS DE PERFORMANCE")
    print("═" * 40)

    for task_instance in task_instances:
        if task_instance.duration:
            print(f"  {task_instance.task_id}: {task_instance.duration:.2f}s")

    # En producción: enviar a Prometheus, DataDog, etc.
    return "monitoring_complete"

with DAG(
    'ex05_monitoring_alerts',
    default_args=default_args,
    description='DAG con monitoreo, SLAs y alertas',
    schedule_interval='*/15 * * * *',  # Cada 15 minutos
    start_date=datetime(2024, 1, 1),
    catchup=False,
    sla_miss_callback=sla_miss_callback,
    tags=['ejercicio', 'monitoreo', 'alertas', 'produccion'],
) as dag:

    start = BashOperator(
        task_id='start',
        bash_command='echo "Iniciando pipeline monitoreado..."',
    )

    critical = PythonOperator(
        task_id='critical_task',
        python_callable=critical_task,
        sla=timedelta(minutes=3),  # SLA más estricto para esta task
    )

    quality = PythonOperator(
        task_id='quality_check',
        python_callable=data_quality_check,
        provide_context=True,
    )

    monitoring = PythonOperator(
        task_id='performance_monitoring',
        python_callable=performance_monitoring,
        provide_context=True,
        trigger_rule='all_done',  # Se ejecuta siempre
    )

    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline completado - revisar métricas"',
    )

    # Pipeline con monitoreo
    start >> critical >> quality >> monitoring >> end
