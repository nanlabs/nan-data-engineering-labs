#!/bin/bash
# Setup script para el módulo de Infrastructure as Code

set -euo pipefail

echo "🚀 Módulo 11: Infrastructure as Code - Setup"
echo "============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "ℹ️  $1"
}

# 1. Verificar sistema operativo
echo "1️⃣  Verificando sistema operativo..."
OS="$(uname -s)"
case $OS in
    Linux*)     OS_TYPE=Linux;;
    Darwin*)    OS_TYPE=Mac;;
    MINGW*|MSYS*|CYGWIN*)    OS_TYPE=Windows;;
    *)          OS_TYPE="UNKNOWN:${OS}"
esac
info "Sistema operativo: $OS_TYPE"
echo ""

# 2. Verificar Terraform
echo "2️⃣  Verificando Terraform..."
if command -v terraform &> /dev/null; then
    TF_VERSION=$(terraform version -json | jq -r '.terraform_version' 2>/dev/null || terraform version | head -n1 | awk '{print $2}')
    success "Terraform instalado: $TF_VERSION"

    # Verificar versión mínima
    REQUIRED_VERSION="1.0.0"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$TF_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        success "Versión compatible (>= 1.0.0)"
    else
        warning "Versión $TF_VERSION es inferior a la recomendada (1.0.0+)"
    fi
else
    error "Terraform no está instalado"
    info "Instalación:"
    case $OS_TYPE in
        Mac)
            echo "  brew install terraform"
            ;;
        Linux)
            echo "  wget https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip"
            echo "  unzip terraform_1.7.5_linux_amd64.zip"
            echo "  sudo mv terraform /usr/local/bin/"
            ;;
        Windows)
            echo "  choco install terraform"
            ;;
    esac
    exit 1
fi
echo ""

# 3. Verificar AWS CLI
echo "3️⃣  Verificando AWS CLI..."
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version | awk '{print $1}' | cut -d'/' -f2)
    success "AWS CLI instalado: $AWS_VERSION"

    # Verificar credenciales
    if aws sts get-caller-identity &>/dev/null; then
        AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
        AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
        success "Credenciales AWS configuradas"
        info "Account: $AWS_ACCOUNT"
        info "User: $AWS_USER"
    else
        warning "AWS CLI instalado pero credenciales no configuradas"
        info "Ejecuta: aws configure"
    fi
else
    warning "AWS CLI no instalado (opcional para desarrollo local con LocalStack)"
fi
echo ""

# 4. Verificar Docker
echo "4️⃣  Verificando Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    success "Docker instalado: $DOCKER_VERSION"

    if docker ps &>/dev/null; then
        success "Docker daemon activo"
    else
        warning "Docker instalado pero daemon no está corriendo"
        info "Inicia Docker Desktop o ejecuta: sudo systemctl start docker"
    fi
else
    warning "Docker no instalado (necesario para LocalStack)"
    info "Instala desde: https://docs.docker.com/get-docker/"
fi
echo ""

# 5. Verificar herramientas opcionales
echo "5️⃣  Verificando herramientas opcionales..."

# tflint
if command -v tflint &> /dev/null; then
    success "tflint instalado: $(tflint --version | head -n1)"
else
    info "tflint no instalado (opcional, recomendado para linting)"
    case $OS_TYPE in
        Mac)
            echo "  brew install tflint"
            ;;
        Linux)
            echo "  curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash"
            ;;
    esac
fi

# tfsec
if command -v tfsec &> /dev/null; then
    success "tfsec instalado: $(tfsec --version)"
else
    info "tfsec no instalado (opcional, recomendado para security scanning)"
    case $OS_TYPE in
        Mac)
            echo "  brew install tfsec"
            ;;
        Linux)
            echo "  brew install tfsec  # o descargar desde GitHub releases"
            ;;
    esac
fi

# pre-commit
if command -v pre-commit &> /dev/null; then
    success "pre-commit instalado: $(pre-commit --version)"
else
    info "pre-commit no instalado (opcional)"
    echo "  pip install pre-commit"
fi

echo ""

# 6. Verificar Python y dependencias
echo "6️⃣  Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    success "Python instalado: $PYTHON_VERSION"

    # Instalar dependencias
    if [ -f "../requirements.txt" ]; then
        info "Instalando dependencias Python..."
        python3 -m pip install -q -r ../requirements.txt || warning "Error instalando dependencias"
        success "Dependencias instaladas"
    fi
else
    error "Python 3 no instalado"
    exit 1
fi
echo ""

# 7. Setup LocalStack
echo "7️⃣  LocalStack (Opcional - para testing local)..."
if command -v localstack &> /dev/null; then
    success "LocalStack CLI instalado"
    info "Para iniciar LocalStack: localstack start -d"
else
    info "LocalStack no instalado"
    echo "  pip install localstack awscli-local"
fi
echo ""

# 8. Crear estructura de directorios
echo "8️⃣  Verificando estructura de directorios..."
DIRS=("theory" "exercises" "infrastructure" "validation" "scripts" "data" "assets")
for dir in "${DIRS[@]}"; do
    if [ -d "../$dir" ]; then
        success "$dir/ existe"
    else
        warning "$dir/ no existe, creando..."
        mkdir -p "../$dir"
    fi
done
echo ""

# 9. Configurar .gitignore
echo "9️⃣  Configurando .gitignore..."
GITIGNORE="../.gitignore"
if [ ! -f "$GITIGNORE" ]; then
    cat > "$GITIGNORE" << 'EOF'
# Terraform
**/.terraform/*
*.tfstate
*.tfstate.*
.terraform.lock.hcl

# Secrets
*.tfvars
!*.tfvars.example

# IDE
.idea/
.vscode/
*.swp

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/

# OS
.DS_Store
EOF
    success ".gitignore creado"
else
    success ".gitignore ya existe"
fi
echo ""

# 10. Resumen final
echo "============================================="
echo "📊 Resumen de Setup"
echo "============================================="
echo ""

READY=true

if command -v terraform &> /dev/null; then
    echo -e "${GREEN}✅ Terraform${NC}"
else
    echo -e "${RED}❌ Terraform${NC}"
    READY=false
fi

if command -v aws &> /dev/null; then
    echo -e "${GREEN}✅ AWS CLI${NC}"
else
    echo -e "${YELLOW}⚠️  AWS CLI (opcional)${NC}"
fi

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker${NC}"
else
    echo -e "${YELLOW}⚠️  Docker (opcional)${NC}"
fi

if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python 3${NC}"
else
    echo -e "${RED}❌ Python 3${NC}"
    READY=false
fi

echo ""

if [ "$READY" = true ]; then
    echo -e "${GREEN}🎉 ¡Setup completo! Estás listo para comenzar.${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Lee la teoría en theory/"
    echo "  2. Completa los ejercicios en exercises/"
    echo "  3. Ejecuta: cd exercises/01-first-terraform && terraform init"
else
    echo -e "${RED}⚠️  Hay herramientas faltantes. Por favor instálalas antes de continuar.${NC}"
    exit 1
fi
