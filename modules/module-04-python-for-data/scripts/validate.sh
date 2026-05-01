#!/bin/bash

# ============================================================================
# Validation Script - Módulo 04: Python para Ingeniería de Datos
# ============================================================================
# 
# Este script ejecuta la suite completa de tests de validación:
# - Tests de ejercicios (120+ tests)
# - Tests de integración
# - Tests de calidad de datos
# - Tests de completitud del módulo
# - Genera reporte de coverage
#
# Uso:
#   ./scripts/validate.sh                    # Todos los tests
#   ./scripts/validate.sh --fast             # Solo tests rápidos
#   ./scripts/validate.sh --exercise 01      # Solo un ejercicio
#   ./scripts/validate.sh --coverage         # Con reporte de coverage
#   ./scripts/validate.sh --html             # Genera reporte HTML
#
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
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

MODE="all"
EXERCISE=""
WITH_COVERAGE=false
HTML_REPORT=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            MODE="fast"
            shift
            ;;
        --exercise)
            MODE="exercise"
            EXERCISE="$2"
            shift 2
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [OPTIONS]"
            echo ""
            echo "Modos:"
            echo "  (default)           Ejecutar todos los tests"
            echo "  --fast              Solo tests rápidos (sin 'slow' marker)"
            echo "  --exercise NUM      Solo ejercicio específico (01-06)"
            echo ""
            echo "Opciones:"
            echo "  --coverage          Generar reporte de coverage"
            echo "  --html              Generar reporte HTML de tests"
            echo "  --verbose, -v       Modo verbose"
            echo "  --help, -h          Muestra esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0                          # Todos los tests"
            echo "  $0 --fast                   # Tests rápidos"
            echo "  $0 --exercise 03            # Solo ejercicio 03"
            echo "  $0 --coverage --html        # Con reportes"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# Verificación del entorno
# ============================================================================

print_header "Validación de Tests - Módulo 04"

# Verificar que estamos en entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "No estás en un entorno virtual"
    print_info "Ejecuta: source venv/bin/activate"
    echo ""
    read -p "¿Continuar de todos modos? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# Verificar pytest
if ! command -v pytest &> /dev/null; then
    print_error "pytest no está instalado"
    print_info "Ejecuta: pip install pytest"
    exit 1
fi

print_success "Entorno verificado"

# ============================================================================
# Configurar pytest options
# ============================================================================

PYTEST_OPTS="-v --tb=short --color=yes"

if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -vv -s"
fi

if [ "$WITH_COVERAGE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=. --cov-report=term-missing"
fi

if [ "$HTML_REPORT" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --html=logs/test-report.html --self-contained-html"
    mkdir -p logs
fi

# ============================================================================
# Ejecutar tests según modo
# ============================================================================

case $MODE in
    fast)
        print_header "Ejecutando Tests Rápidos"
        print_info "Saltando tests marcados como 'slow'"
        echo ""
        
        pytest $PYTEST_OPTS -m "not slow"
        TEST_RESULT=$?
        ;;
        
    exercise)
        print_header "Ejecutando Tests del Ejercicio $EXERCISE"
        
        # Validar número de ejercicio
        if [[ ! "$EXERCISE" =~ ^0[1-6]$ ]]; then
            print_error "Ejercicio inválido: $EXERCISE (debe ser 01-06)"
            exit 1
        fi
        
        EXERCISE_DIR="exercises/$EXERCISE-*"
        
        if [ ! -d exercises/${EXERCISE}-* ]; then
            print_error "Ejercicio $EXERCISE no encontrado"
            exit 1
        fi
        
        echo ""
        pytest $PYTEST_OPTS -m "exercise${EXERCISE}" exercises/${EXERCISE}-*/tests/
        TEST_RESULT=$?
        ;;
        
    all)
        print_header "Ejecutando Suite Completa de Tests"
        print_info "Esto incluye:"
        print_info "  • 120+ tests de ejercicios"
        print_info "  • Tests de integración"
        print_info "  • Tests de calidad de datos"
        print_info "  • Tests de completitud"
        echo ""
        print_warning "Esto puede tomar 2-3 minutos..."
        echo ""
        
        # Ejecutar por categorías
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${MAGENTA}1/4: Tests de Ejercicios (Unit Tests)${NC}"
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        pytest $PYTEST_OPTS -m "unit" exercises/ || true
        
        echo ""
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${MAGENTA}2/4: Tests de Integración${NC}"
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        pytest $PYTEST_OPTS -m "integration" validation/test_integration.py || true
        
        echo ""
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${MAGENTA}3/4: Tests de Calidad de Datos${NC}"
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        pytest $PYTEST_OPTS -m "data" validation/test_data_quality.py || true
        
        echo ""
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${MAGENTA}4/4: Tests de Completitud del Módulo${NC}"
        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        
        pytest $PYTEST_OPTS validation/test_module_completeness.py
        TEST_RESULT=$?
        ;;
esac

# ============================================================================
# Resumen de resultados
# ============================================================================

echo ""
print_header "Resumen de Validación"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}║                    ✓ TODOS LOS TESTS PASARON                      ║${NC}"
    echo -e "${GREEN}║                                                                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_success "El módulo está completamente validado"
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}║                    ✗ ALGUNOS TESTS FALLARON                       ║${NC}"
    echo -e "${RED}║                                                                    ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_error "Revisa los errores arriba"
fi

# Información adicional si se generaron reportes
if [ "$WITH_COVERAGE" = true ]; then
    echo ""
    print_info "Reporte de coverage generado"
    
    if [ -f "htmlcov/index.html" ]; then
        print_info "Abre: htmlcov/index.html para ver reporte detallado"
    fi
fi

if [ "$HTML_REPORT" = true ]; then
    echo ""
    if [ -f "logs/test-report.html" ]; then
        print_info "Reporte HTML generado: logs/test-report.html"
    fi
fi

# Sugerencias según resultado
echo ""
if [ $TEST_RESULT -ne 0 ]; then
    echo -e "${YELLOW}Sugerencias:${NC}"
    echo "  1. Revisa los errores específicos arriba"
    echo "  2. Ejecuta un test individual para debug:"
    echo -e "     ${BLUE}pytest -vv exercises/01-python-basics/tests/test_basics.py::test_specific${NC}"
    echo "  3. Consulta la guía de troubleshooting:"
    echo -e "     ${BLUE}cat docs/troubleshooting.md${NC}"
    echo ""
fi

echo -e "${CYAN}Otros comandos útiles:${NC}"
echo -e "  Tests rápidos:        ${BLUE}./scripts/validate.sh --fast${NC}"
echo -e "  Un ejercicio:         ${BLUE}./scripts/validate.sh --exercise 03${NC}"
echo -e "  Con coverage:         ${BLUE}./scripts/validate.sh --coverage${NC}"
echo -e "  Modo verbose:         ${BLUE}./scripts/validate.sh -v${NC}"
echo ""

exit $TEST_RESULT
