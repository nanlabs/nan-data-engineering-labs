#!/bin/bash

# ============================================================================
# Reset Environment Script - Módulo 04: Python para Ingeniería de Datos
# ============================================================================
# 
# Este script limpia y resetea el entorno del módulo:
# - Elimina entorno virtual
# - Limpia archivos temporales y cache
# - Elimina datos generados (opcional)
# - Limpia logs y reportes
# - Resetea a estado inicial
#
# ADVERTENCIA: Este script elimina archivos. Úsalo con precaución.
#
# Uso:
#   ./scripts/reset_env.sh                # Limpieza básica
#   ./scripts/reset_env.sh --full         # Limpieza completa (incluye datos)
#   ./scripts/reset_env.sh --data-only    # Solo elimina datos
#   ./scripts/reset_env.sh --dry-run      # Muestra qué se eliminaría
#
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}ℹ $1${NC}"
}

remove_if_exists() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        if [ "$DRY_RUN" = true ]; then
            print_warning "[DRY RUN] Se eliminaría: $description ($path)"
        else
            rm -rf "$path"
            print_success "Eliminado: $description"
        fi
    else
        print_info "No existe: $description"
    fi
}

# ============================================================================
# Parsing de argumentos
# ============================================================================

MODE="basic"
DRY_RUN=false
CONFIRMED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            MODE="full"
            shift
            ;;
        --data-only)
            MODE="data"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --yes|-y)
            CONFIRMED=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [OPTIONS]"
            echo ""
            echo "Modos:"
            echo "  (default)       Limpieza básica (venv, cache, logs)"
            echo "  --full          Limpieza completa (incluye datos generados)"
            echo "  --data-only     Solo elimina datos generados"
            echo ""
            echo "Opciones:"
            echo "  --dry-run       Muestra qué se eliminaría sin hacerlo"
            echo "  --yes, -y       No pedir confirmación"
            echo "  --help, -h      Muestra esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0                    # Limpieza básica"
            echo "  $0 --full             # Limpieza completa"
            echo "  $0 --dry-run          # Ver qué se eliminaría"
            echo "  $0 --data-only -y     # Solo datos, sin confirmar"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# Banner y confirmación
# ============================================================================

print_header "Reset de Entorno - Módulo 04"

if [ "$DRY_RUN" = true ]; then
    print_warning "MODO DRY RUN - No se eliminará nada"
    echo ""
fi

# Mostrar qué se va a eliminar
echo -e "${YELLOW}Se eliminarán los siguientes elementos:${NC}"
echo ""

case $MODE in
    basic)
        echo "  • Entorno virtual (venv/)"
        echo "  • Archivos cache de Python (__pycache__, *.pyc)"
        echo "  • Cache de pytest (.pytest_cache/)"
        echo "  • Logs (logs/)"
        echo "  • Reportes de coverage (htmlcov/, .coverage)"
        echo "  • Archivos temporales"
        ;;
    data)
        echo "  • Datos generados (data/raw/*.csv, data/raw/*.json)"
        echo "  • Datos procesados (data/processed/)"
        ;;
    full)
        echo "  • Entorno virtual (venv/)"
        echo "  • Archivos cache de Python"
        echo "  • Cache de pytest"
        echo "  • Logs y reportes"
        echo "  • Datos generados (data/raw/)"
        echo "  • Datos procesados (data/processed/)"
        echo "  • Todo cache y temporales"
        ;;
esac

echo ""

if [ "$CONFIRMED" = false ] && [ "$DRY_RUN" = false ]; then
    print_warning "Esta operación no se puede deshacer"
    echo ""
    read -p "¿Continuar? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Operación cancelada"
        exit 0
    fi
fi

# ============================================================================
# Limpieza según modo
# ============================================================================

if [ "$MODE" = "basic" ] || [ "$MODE" = "full" ]; then
    print_header "Limpiando Entorno Python"
    
    # Entorno virtual
    remove_if_exists "venv" "Entorno virtual"
    remove_if_exists "activate.sh" "Script de activación"
    
    # Cache de Python
    print_info "Limpiando cache de Python..."
    if [ "$DRY_RUN" = false ]; then
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        find . -type f -name "*.pyo" -delete 2>/dev/null || true
        print_success "Cache de Python eliminado"
    else
        print_warning "[DRY RUN] Se eliminaría cache de Python"
    fi
    
    # Cache de pytest
    remove_if_exists ".pytest_cache" "Cache de pytest"
    remove_if_exists "exercises/.pytest_cache" "Cache de pytest (exercises)"
    remove_if_exists "validation/.pytest_cache" "Cache de pytest (validation)"
    
    # Logs y reportes
    print_header "Limpiando Logs y Reportes"
    
    remove_if_exists "logs" "Directorio de logs"
    remove_if_exists "htmlcov" "Reporte de coverage HTML"
    remove_if_exists ".coverage" "Archivo de coverage"
    remove_if_exists ".coverage.*" "Archivos de coverage"
    
    # Archivos temporales
    print_header "Limpiando Archivos Temporales"
    
    if [ "$DRY_RUN" = false ]; then
        find . -type f -name "*.tmp" -delete 2>/dev/null || true
        find . -type f -name "*.temp" -delete 2>/dev/null || true
        find . -type f -name ".DS_Store" -delete 2>/dev/null || true
        print_success "Archivos temporales eliminados"
    else
        print_warning "[DRY RUN] Se eliminarían archivos temporales"
    fi
fi

if [ "$MODE" = "data" ] || [ "$MODE" = "full" ]; then
    print_header "Limpiando Datos Generados"
    
    # Datos raw
    DATA_FILES=(
        "data/raw/customers.csv"
        "data/raw/transactions.csv"
        "data/raw/products.csv"
        "data/raw/orders.json"
        "data/raw/user_activity.json"
    )
    
    for file in "${DATA_FILES[@]}"; do
        remove_if_exists "$file" "$(basename $file)"
    done
    
    # Datos procesados
    remove_if_exists "data/processed" "Datos procesados"
    
    # Checkpoints
    remove_if_exists "checkpoints" "Checkpoints de pipeline"
fi

# ============================================================================
# Limpieza adicional para modo full
# ============================================================================

if [ "$MODE" = "full" ]; then
    print_header "Limpieza Adicional (Full Mode)"
    
    # Jupyter checkpoints
    if [ "$DRY_RUN" = false ]; then
        find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
        print_success "Jupyter checkpoints eliminados"
    else
        print_warning "[DRY RUN] Se eliminarían Jupyter checkpoints"
    fi
    
    # Archivos de editor
    remove_if_exists ".vscode/.ropeproject" "Configuración de rope"
    
    if [ "$DRY_RUN" = false ]; then
        find . -type f -name "*.swp" -delete 2>/dev/null || true
        find . -type f -name "*.swo" -delete 2>/dev/null || true
        find . -type f -name "*~" -delete 2>/dev/null || true
        print_success "Archivos de editor eliminados"
    fi
fi

# ============================================================================
# Resumen
# ============================================================================

print_header "Resumen de Reset"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Modo DRY RUN - Ningún archivo fue eliminado${NC}"
    echo ""
    print_info "Para ejecutar la limpieza real, ejecuta sin --dry-run"
else
    echo -e "${GREEN}Limpieza completada exitosamente${NC}"
    echo ""
    
    # Mostrar qué hacer ahora
    if [ "$MODE" = "basic" ] || [ "$MODE" = "full" ]; then
        echo "Para restablecer el entorno:"
        echo ""
        echo "  1. Ejecuta el setup nuevamente:"
        echo -e "     ${BLUE}./scripts/setup.sh${NC}"
        echo ""
        
        if [ "$MODE" = "full" ]; then
            echo "  2. Esto recreará:"
            echo "     • Entorno virtual"
            echo "     • Instalará dependencias"
            echo "     • Generará datos nuevamente"
        else
            echo "  2. Los datos existentes se conservaron"
            echo "     Si necesitas datos frescos, ejecuta:"
            echo -e "     ${BLUE}python data/scripts/generate_all_datasets.py${NC}"
        fi
    elif [ "$MODE" = "data" ]; then
        echo "Datos eliminados. Para regenerarlos:"
        echo ""
        echo -e "  ${BLUE}python data/scripts/generate_all_datasets.py${NC}"
        echo ""
        echo "O ejecuta el setup completo:"
        echo -e "  ${BLUE}./scripts/setup.sh${NC}"
    fi
fi

echo ""
print_info "Para ver otras opciones de reset: ./scripts/reset_env.sh --help"

exit 0
