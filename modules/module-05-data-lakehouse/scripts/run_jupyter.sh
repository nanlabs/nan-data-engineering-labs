#!/bin/bash
# run_jupyter.sh - Lanzar Jupyter Lab con PySpark kernel

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Jupyter Lab con PySpark${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Debe ejecutar este script desde el directorio module-05-data-lakehouse${NC}"
    exit 1
fi

# Verificar que Docker esté corriendo
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker no está corriendo${NC}"
    echo -e "${YELLOW}   Inicie los servicios con: cd infrastructure && docker-compose up -d${NC}"
    exit 1
fi

# Verificar servicios
echo -e "${YELLOW}🔍 Verificando servicios...${NC}"
if docker-compose -f infrastructure/docker-compose.yml ps | grep -q "jupyter.*Up"; then
    echo -e "${GREEN}✅ Jupyter Lab corriendo${NC}"
else
    echo -e "${YELLOW}⚠️  Jupyter Lab no está corriendo, iniciando servicios...${NC}"
    cd infrastructure
    docker-compose up -d jupyter
    cd ..
    echo -e "${GREEN}✅ Servicios iniciados${NC}"
    sleep 5
fi

# Obtener URL de Jupyter
echo -e "\n${BLUE}📋 Información de acceso:${NC}"
JUPYTER_TOKEN=$(docker exec jupyter jupyter server list 2>/dev/null | grep -o 'token=[^[:space:]]*' | head -1 | cut -d'=' -f2 || echo "")

if [ -n "$JUPYTER_TOKEN" ]; then
    echo -e "${GREEN}✅ Jupyter Lab está corriendo${NC}"
    echo -e "\n${YELLOW}🌐 URL de acceso:${NC}"
    echo -e "   http://localhost:8888/lab?token=${JUPYTER_TOKEN}"
    echo -e "\n${YELLOW}📝 Token:${NC} ${JUPYTER_TOKEN}"
else
    echo -e "${GREEN}✅ Jupyter Lab está corriendo${NC}"
    echo -e "\n${YELLOW}🌐 URL de acceso:${NC}"
    echo -e "   http://localhost:8888/lab"
    echo -e "\n${YELLOW}ℹ️  Si requiere token, revise los logs:${NC}"
    echo -e "   docker logs jupyter"
fi

echo -e "\n${BLUE}📊 Servicios disponibles:${NC}"
echo -e "  • MinIO (S3): http://localhost:9001 (minioadmin/minioadmin)"
echo -e "  • Spark Master UI: http://localhost:8080"
echo -e "  • Spark Worker UI: http://localhost:8081"

echo -e "\n${YELLOW}💡 Consejos:${NC}"
echo -e "  • Los notebooks se guardan en: $(pwd)/notebooks/"
echo -e "  • Para ver logs: docker logs -f jupyter"
echo -e "  • Para detener: cd infrastructure && docker-compose stop jupyter"

echo -e "\n${GREEN}✅ Jupyter Lab configurado${NC}"
echo -e "${YELLOW}🔗 Abriendo navegador...${NC}\n"

# Intentar abrir el navegador (opcional)
if command -v xdg-open > /dev/null; then
    # Linux
    xdg-open "http://localhost:8888/lab?token=${JUPYTER_TOKEN}" 2>/dev/null || true
elif command -v open > /dev/null; then
    # macOS
    open "http://localhost:8888/lab?token=${JUPYTER_TOKEN}" 2>/dev/null || true
else
    echo -e "${YELLOW}ℹ️  Abra manualmente la URL en su navegador${NC}"
fi

# Mantener el script abierto para mostrar información
echo -e "\n${BLUE}Presione Ctrl+C para salir (Jupyter seguirá corriendo)${NC}"
echo -e "${YELLOW}Para detener Jupyter: cd infrastructure && docker-compose stop jupyter${NC}\n"

# Tail logs (opcional) 
# docker logs -f jupyter
