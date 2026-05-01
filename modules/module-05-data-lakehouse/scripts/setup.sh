#!/bin/bash
# Setup completo para Module 05: Data Lakehouse Architecture

set -e

echo "🚀 Iniciando setup de Data Lakehouse Architecture..."

# 1. Verificar Docker
echo "📦 Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no instalado. Instala Docker Desktop primero."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon no está corriendo. Inicia Docker Desktop."
    exit 1
fi

echo "✅ Docker OK"

# 2. Crear directorios
echo "📁 Creando estructura de directorios..."
mkdir -p data/raw data/bronze data/silver data/gold
mkdir -p notebooks logs
chmod -R 777 data notebooks logs

# 3. Variables de entorno
echo "🔧 Configurando variables de entorno..."
cat > .env << 'EOF'
# MinIO (S3 Compatible)
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=password123
MINIO_ENDPOINT=minio:9000

# Spark
SPARK_MASTER=spark://spark-master:7077
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g

# Hive Metastore
HIVE_METASTORE_URI=thrift://hive-metastore:9083

# PostgreSQL (Metastore DB)
POSTGRES_USER=hive
POSTGRES_PASSWORD=hive123
POSTGRES_DB=metastore
EOF

echo "✅ Variables configuradas"

# 4. Levantar infraestructura
echo "🐳 Levantando servicios Docker..."
cd infrastructure
docker-compose up -d

echo "⏳ Esperando servicios (30s)..."
sleep 30

# 5. Verificar servicios
echo "🔍 Verificando servicios..."

# MinIO
if curl -s http://localhost:9001 > /dev/null; then
    echo "✅ MinIO UI: http://localhost:9001"
else
    echo "⚠️  MinIO no responde"
fi

# Spark
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Spark UI: http://localhost:8080"
else
    echo "⚠️  Spark no responde"
fi

# Jupyter
if curl -s http://localhost:8888 > /dev/null; then
    echo "✅ Jupyter: http://localhost:8888"
else
    echo "⚠️  Jupyter no responde"
fi

# 6. Inicializar buckets en MinIO
echo "🪣 Creando buckets S3..."
docker exec minio mc alias set local http://localhost:9000 admin password123
docker exec minio mc mb local/bronze --ignore-existing
docker exec minio mc mb local/silver --ignore-existing
docker exec minio mc local/gold --ignore-existing
docker exec minio mc mb local/warehouse --ignore-existing

echo "✅ Buckets creados: bronze, silver, gold, warehouse"

# 7. Generar datasets
echo "📊 Generando datasets de prueba..."
cd ../scripts
python generate_transactions.py

echo "✅ Datasets generados en data/raw/"

# 8. Verificar instalación Python
echo "🐍 Verificando dependencias Python..."
pip install -q -r ../validation/requirements.txt

# 9. Ejecutar test de validación
echo "🧪 Ejecutando tests básicos..."
pytest ../validation/test_01_delta_basics.py -v --tb=short || echo "⚠️  Algunos tests fallaron (normal si no has completado ejercicios)"

# 10. Resumen final
echo ""
echo "=" * 60
echo "✅ SETUP COMPLETO"
echo "=" * 60
echo ""
echo "🎯 URLs Disponibles:"
echo "   • MinIO UI:    http://localhost:9001 (admin/password123)"
echo "   • Spark UI:    http://localhost:8080"
echo "   • Jupyter:     http://localhost:8888"
echo "   • Hive Thrift: localhost:9083"
echo ""
echo "📂 Directorios:"
echo "   • data/raw/       → JSON files (614,500 registros)"
echo "   • data/bronze/    → Ingesta cruda"
echo "   • data/silver/    → Datos limpios"
echo "   • data/gold/      → Agregaciones"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. cd exercises/01-delta-basics"
echo "   2. python starter/01_create_table.py"
echo "   3. Revisar assets/ para cheatsheets"
echo ""
echo "📚 Documentación: README.md"
echo "🧪 Validación: pytest validation/ -v"
echo ""
