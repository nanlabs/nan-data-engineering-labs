#!/bin/bash
# Script de validación para Terraform

set -euo pipefail

echo "🔍 Validando configuraciones de Terraform"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# 1. Format check
echo "1️⃣  Terraform Format Check..."
cd ..
if terraform fmt -check -recursive > /dev/null 2>&1; then
    success "Código formateado correctamente"
else
    warning "Código necesita formateo"
    terraform fmt -recursive
    success "Auto-formateado aplicado"
fi
echo ""

# 2. Validate exercises
echo "2️⃣  Validando ejercicios..."
for exercise in exercises/*/; do
    if [ -f "$exercise/main.tf" ] || [ -f "$exercise/README.md" ]; then
        exercise_name=$(basename "$exercise")
        echo "  Validando $exercise_name..."

        cd "$exercise"

        # Solo validar si hay archivos .tf
        if ls *.tf > /dev/null 2>&1; then
            terraform init -backend=false > /dev/null 2>&1 || true

            if terraform validate > /dev/null 2>&1; then
                success "  $exercise_name válido"
            else
                error "  $exercise_name tiene errores"
            fi
        fi

        cd - > /dev/null
    fi
done
echo ""

# 3. Validate modules
echo "3️⃣  Validando módulos..."
if [ -d "infrastructure/modules" ]; then
    for module in infrastructure/modules/*/; do
        if [ -f "$module/main.tf" ]; then
            module_name=$(basename "$module")
            echo "  Validando módulo: $module_name..."

            cd "$module"
            terraform init -backend=false > /dev/null 2>&1 || true

            if terraform validate > /dev/null 2>&1; then
                success "  $module_name válido"
            else
                error "  $module_name tiene errores"
            fi

            cd - > /dev/null
        fi
    done
fi
echo ""

# 4. Check for security issues (if tfsec is installed)
echo "4️⃣  Security Scan..."
if command -v tfsec &> /dev/null; then
    if tfsec . --minimum-severity MEDIUM > /dev/null 2>&1; then
        success "Sin problemas de seguridad críticos"
    else
        warning "Problemas de seguridad detectados (ejecuta: tfsec .)"
    fi
else
    warning "tfsec no instalado, saltando security scan"
fi
echo ""

# 5. Lint (if tflint is installed)
echo "5️⃣  Linting..."
if command -v tflint &> /dev/null; then
    tflint --init > /dev/null 2>&1 || true
    if tflint --recursive > /dev/null 2>&1; then
        success "Sin problemas de linting"
    else
        warning "Problemas de linting detectados"
    fi
else
    warning "tflint no instalado, saltando lint check"
fi
echo ""

# 6. Check documentation
echo "6️⃣  Verificando documentación..."
for dir in theory exercises infrastructure; do
    if [ -d "$dir" ]; then
        if [ -f "$dir/README.md" ] || ls $dir/*/README.md > /dev/null 2>&1; then
            success "$dir/ tiene documentación"
        else
            warning "$dir/ falta documentación README.md"
        fi
    fi
done
echo ""

# 7. Test runner
echo "7️⃣  Tests..."
if [ -f "validation/conftest.py" ]; then
    cd validation
    if python3 -m pytest -v > /dev/null 2>&1; then
        success "Todos los tests pasan"
    else
        error "Algunos tests fallan (ejecuta: pytest -v)"
    fi
    cd ..
else
    warning "No hay tests configurados"
fi
echo ""

# Resumen
echo "=========================================="
echo "📊 Resumen de Validación"
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Validación exitosa${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS advertencias (opcional)${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ $ERRORS errores encontrados${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS advertencias${NC}"
    fi
    exit 1
fi
