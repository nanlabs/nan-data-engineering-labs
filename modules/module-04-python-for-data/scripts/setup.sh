#!/bin/bash

# ============================================================================
# Setup Script - Módulo 04: Python para Ingeniería de Datos
# ============================================================================
# 
# Este script configura el entorno completo del módulo:
# - Verifica dependencias del sistema
# - Crea y activa entorno virtual
# - Instala dependencias Python
# - Genera datos de ejemplo
# - Valida instalación
#
# Uso:
#   ./scripts/setup.sh
#   ./scripts/setup.sh --clean     # Limpia y recrea todo
#   ./scripts/setup.sh --no-data   # Sin generar datos
#
# ============================================================================

set -e  # Exit on error

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio del módulo
MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MODULE_DIR"

# ============================================================================
# Funciones de utilidad
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
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 está instalado ($(command -v $1))"
        return 0
    else
        print_error "$1 no está instalado"
        return 1
    fi
}

# ============================================================================
# Parsing de argumentos
# ============================================================================

CLEAN_INSTALL=false
SKIP_DATA=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --no-data)
            SKIP_DATA=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [OPTIONS]"
            echo ""
            echo "Opciones:"
            echo "  --clean       Limpia y recrea el entorno virtual"
            echo "  --no-data     No genera datos de ejemplo"
            echo "  --help, -h    Muestra esta ayuda"
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

print_header "Módulo 04: Python para Ingeniería de Datos - Setup"

# ============================================================================
# 1. Verificar dependencias del sistema
# ============================================================================

print_header "1. Verificando dependencias del sistema"

DEPS_OK=true

if ! check_command python3; then
    DEPS_OK=false
fi

if ! check_command pip3; then
    DEPS_OK=false
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8.0"

print_info "Versión de Python detectada: $PYTHON_VERSION"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    print_error "Se requiere Python >= $REQUIRED_VERSION"
    DEPS_OK=false
else
    print_success "Versión de Python compatible"
fi

# Verificar git
if ! check_command git; then
    print_warning "Git no está instalado (opcional)"
fi

# Verificar Docker (opcional)
if check_command docker; then
    print_success "Docker disponible para infraestructura"
else
    print_warning "Docker no disponible (opcional para este setup)"
fi

if [ "$DEPS_OK" = false ]; then
    print_error "Faltan dependencias críticas. Instala Python 3.8+ y pip3"
    exit 1
fi

# ============================================================================
# 2. Crear/Limpiar entorno virtual
# ============================================================================

print_header "2. Configurando entorno virtual"

VENV_DIR="venv"

if [ "$CLEAN_INSTALL" = true ]; then
    if [ -d "$VENV_DIR" ]; then
        print_info "Eliminando entorno virtual existente..."
        rm -rf "$VENV_DIR"
        print_success "Entorno virtual eliminado"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    print_info "Creando nuevo entorno virtual..."
    python3 -m venv "$VENV_DIR"
    print_success "Entorno virtual creado en: $VENV_DIR"
else
    print_info "Usando entorno virtual existente"
fi

# Activar entorno virtual
print_info "Activando entorno virtual..."
source "$VENV_DIR/bin/activate"
print_success "Entorno virtual activado"

# ============================================================================
# 3. Actualizar pip y setuptools
# ============================================================================

print_header "3. Actualizando herramientas base"

print_info "Actualizando pip, setuptools y wheel..."
pip install --upgrade pip setuptools wheel --quiet
print_success "Herramientas actualizadas"

# ============================================================================
# 4. Instalar dependencias
# ============================================================================

print_header "4. Instalando dependencias Python"

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt no encontrado"
    exit 1
fi

print_info "Instalando dependencias desde requirements.txt..."
print_info "Esto puede tomar unos minutos..."

pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    print_success "Todas las dependencias instaladas correctamente"
else
    print_error "Error instalando dependencias"
    exit 1
fi

# Verificar instalación de paquetes críticos
print_info "Verificando paquetes críticos..."

CRITICAL_PACKAGES=("pandas" "numpy" "pytest" "jupyter" "pyarrow")

for package in "${CRITICAL_PACKAGES[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        VERSION=$(python -c "import $package; print($package.__version__)")
        print_success "$package ($VERSION)"
    else
        print_error "$package no se pudo importar"
        exit 1
    fi
done

# ============================================================================
# 5. Crear estructura de directorios
# ============================================================================

print_header "5. Verificando estructura de directorios"

REQUIRED_DIRS=(
    "data/raw"
    "data/processed"
    "data/schemas"
    "exercises"
    "validation"
    "assets/cheatsheets"
    "assets/diagrams"
    "scripts"
    "docs"
    "theory"
    "infrastructure"
    ".pytest_cache"
    "logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_info "Creando directorio: $dir"
        mkdir -p "$dir"
    fi
done

print_success "Estructura de directorios verificada"

# ============================================================================
# 6. Generar datos de ejemplo
# ============================================================================

if [ "$SKIP_DATA" = false ]; then
    print_header "6. Generando datos de ejemplo"
    
    if [ -f "data/scripts/generate_all_datasets.py" ]; then
        print_info "Ejecutando script de generación de datos..."
        print_info "Generando 180,000 registros (esto puede tomar 1-2 minutos)..."
        
        python data/scripts/generate_all_datasets.py
        
        if [ $? -eq 0 ]; then
            print_success "Datos generados exitosamente"
            
            # Verificar archivos generados
            DATA_FILES=(
                "data/raw/customers.csv"
                "data/raw/transactions.csv"
                "data/raw/products.csv"
                "data/raw/orders.json"
                "data/raw/user_activity.json"
            )
            
            TOTAL_SIZE=0
            for file in "${DATA_FILES[@]}"; do
                if [ -f "$file" ]; then
                    SIZE=$(du -h "$file" | cut -f1)
                    print_success "  $file ($SIZE)"
                    TOTAL_SIZE=$((TOTAL_SIZE + $(du -k "$file" | cut -f1)))
                else
                    print_warning "  $file no encontrado"
                fi
            done
            
            TOTAL_MB=$((TOTAL_SIZE / 1024))
            print_info "Tamaño total de datos: ${TOTAL_MB}MB"
        else
            print_warning "Error generando datos (puedes generarlos manualmente después)"
        fi
    else
        print_warning "Script de generación de datos no encontrado"
        print_info "Puedes ejecutarlo manualmente: python data/scripts/generate_all_datasets.py"
    fi
else
    print_info "6. Saltando generación de datos (--no-data especificado)"
fi

# ============================================================================
# 7. Ejecutar tests de validación
# ============================================================================

print_header "7. Ejecutando tests de validación"

print_info "Ejecutando suite básica de tests..."

# Ejecutar solo tests rápidos
pytest validation/ -v --tb=short -m "not slow" --maxfail=3 -q

if [ $? -eq 0 ]; then
    print_success "Tests de validación pasaron correctamente"
else
    print_warning "Algunos tests fallaron (esto puede ser normal si faltan datos)"
    print_info "Puedes ejecutar todos los tests con: ./scripts/validate.sh"
fi

# ============================================================================
# 8. Resumen final
# ============================================================================

print_header "Setup Completado ✓"

echo -e "${GREEN}El módulo está listo para usar${NC}"
echo ""
echo "Próximos pasos:"
echo ""
echo "  1. Activar el entorno virtual:"
echo -e "     ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "  2. Explorar los ejercicios:"
echo -e "     ${BLUE}cd exercises/${NC}"
echo ""
echo "  3. Iniciar Jupyter Lab:"
echo -e "     ${BLUE}./scripts/run_jupyter.sh${NC}"
echo ""
echo "  4. Ejecutar todos los tests:"
echo -e "     ${BLUE}./scripts/validate.sh${NC}"
echo ""
echo "Recursos disponibles:"
echo -e "  📚 Theory:        ${BLUE}theory/${NC}"
echo -e "  💻 Exercises:     ${BLUE}exercises/${NC}"
echo -e "  📊 Data:          ${BLUE}data/raw/${NC}"
echo -e "  🎨 Assets:        ${BLUE}assets/${NC}"
echo -e "  📖 Docs:          ${BLUE}docs/${NC}"
echo ""
echo -e "${YELLOW}Si tienes problemas, consulta: docs/troubleshooting.md${NC}"
echo ""

# Crear archivo de activación rápida
cat > activate.sh << 'EOF'
#!/bin/bash
# Quick activation script
cd "$(dirname "$0")"
source venv/bin/activate
echo "✓ Entorno virtual activado"
echo "Ejecuta './scripts/run_jupyter.sh' para iniciar Jupyter Lab"
EOF

chmod +x activate.sh

print_success "Script de activación rápida creado: ./activate.sh"

exit 0
