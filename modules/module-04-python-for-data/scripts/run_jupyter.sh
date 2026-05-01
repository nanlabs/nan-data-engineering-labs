#!/bin/bash

# ============================================================================
# Jupyter Lab Launcher - Módulo 04: Python para Ingeniería de Datos
# ============================================================================
# 
# Este script inicia Jupyter Lab con configuración optimizada para el módulo:
# - Verifica entorno virtual
# - Configura variables de entorno
# - Inicia Jupyter Lab en el puerto adecuado
# - Abre el navegador automáticamente
#
# Uso:
#   ./scripts/run_jupyter.sh              # Puerto 8888 (default)
#   ./scripts/run_jupyter.sh --port 9000  # Puerto personalizado
#   ./scripts/run_jupyter.sh --no-browser # Sin abrir navegador
#
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Directorio del módulo
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MODULE_DIR"

# ============================================================================
# Funciones
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# ============================================================================
# Parsing de argumentos
# ============================================================================

PORT=8888
NO_BROWSER=false
WORKING_DIR="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --no-browser)
            NO_BROWSER=true
            shift
            ;;
        --dir|-d)
            WORKING_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Uso: $0 [OPTIONS]"
            echo ""
            echo "Opciones:"
            echo "  --port, -p NUM      Puerto para Jupyter Lab (default: 8888)"
            echo "  --no-browser        No abrir navegador automáticamente"
            echo "  --dir, -d PATH      Directorio de trabajo (default: .)"
            echo "  --help, -h          Muestra esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0                           # Puerto 8888, abre navegador"
            echo "  $0 --port 9000               # Puerto 9000"
            echo "  $0 --no-browser              # Sin navegador"
            echo "  $0 --dir exercises           # Inicia en exercises/"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# Banner
# ============================================================================

print_header "Jupyter Lab - Módulo 04: Python para Ingeniería de Datos"

# ============================================================================
# Verificaciones
# ============================================================================

# Verificar entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "No estás en un entorno virtual"
    
    if [ -d "venv" ]; then
        print_info "Activando entorno virtual..."
        source venv/bin/activate
        print_success "Entorno virtual activado"
    else
        print_error "Entorno virtual no encontrado"
        print_info "Ejecuta primero: ./scripts/setup.sh"
        exit 1
    fi
else
    print_success "Entorno virtual activo: $VIRTUAL_ENV"
fi

# Verificar Jupyter
if ! command -v jupyter &> /dev/null; then
    print_error "Jupyter no está instalado"
    print_info "Ejecuta: pip install jupyter jupyterlab"
    exit 1
fi

print_success "Jupyter Lab disponible ($(jupyter --version | head -n1))"

# Verificar puerto disponible
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "El puerto $PORT ya está en uso"
    print_info "Puedes usar otro puerto con: --port NUMERO"
    echo ""
    read -p "¿Usar puerto aleatorio? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        PORT=0  # Jupyter elegirá puerto automáticamente
        print_info "Usando puerto aleatorio disponible"
    else
        exit 1
    fi
else
    print_success "Puerto $PORT disponible"
fi

# ============================================================================
# Configurar entorno
# ============================================================================

print_header "Configurando Entorno"

# Variables de entorno útiles
export PYTHONPATH="${MODULE_DIR}:${PYTHONPATH}"
export JUPYTER_CONFIG_DIR="${MODULE_DIR}/.jupyter"

print_success "PYTHONPATH configurado"

# Crear directorio de configuración si no existe
mkdir -p .jupyter

# ============================================================================
# Información de directorios disponibles
# ============================================================================

echo ""
echo -e "${MAGENTA}Directorios Disponibles:${NC}"
echo ""
echo -e "  📚 ${CYAN}theory/${NC}          - Material teórico"
echo -e "  💻 ${CYAN}exercises/${NC}       - Ejercicios prácticos"
echo -e "  📊 ${CYAN}data/raw/${NC}        - Datos de entrada"
echo -e "  🧹 ${CYAN}data/processed/${NC}  - Datos procesados"
echo -e "  🎨 ${CYAN}assets/${NC}          - Cheatsheets y diagramas"
echo -e "  ✅ ${CYAN}validation/${NC}      - Tests de validación"
echo ""

# ============================================================================
# Tips de uso
# ============================================================================

echo -e "${YELLOW}💡 Tips de Uso:${NC}"
echo ""
echo "  1. Usa Tab para autocompletado"
echo "  2. Shift+Enter para ejecutar celda"
echo "  3. Ctrl+S para guardar"
echo "  4. Los datos están en: data/raw/"
echo "  5. Consulta cheatsheets en: assets/cheatsheets/"
echo ""

# ============================================================================
# Iniciar Jupyter Lab
# ============================================================================

print_header "Iniciando Jupyter Lab"

# Configurar opciones de Jupyter
JUPYTER_OPTS="--port=$PORT"

if [ "$NO_BROWSER" = true ]; then
    JUPYTER_OPTS="$JUPYTER_OPTS --no-browser"
fi

# Cambiar al directorio de trabajo si se especificó
if [ "$WORKING_DIR" != "." ]; then
    cd "$WORKING_DIR"
    print_info "Directorio de trabajo: $(pwd)"
fi

echo ""
print_info "Jupyter Lab se está iniciando..."
print_info "Para detenerlo: Ctrl+C"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Trap para limpiar al salir
cleanup() {
    echo ""
    echo ""
    print_info "Cerrando Jupyter Lab..."
    print_success "Sesión terminada"
}

trap cleanup EXIT

# Iniciar Jupyter Lab
jupyter lab $JUPYTER_OPTS \
    --ServerApp.terminado_settings='{"shell_command": ["/bin/bash"]}' \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --ServerApp.allow_origin='*' \
    2>&1 | while IFS= read -r line; do
        # Colorear output de Jupyter
        if [[ $line == *"http"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"error"* ]] || [[ $line == *"Error"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"warning"* ]] || [[ $line == *"Warning"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo "$line"
        fi
    done
