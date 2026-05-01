# ============================================================================
# Module 04: Python for Data Engineering - Custom Jupyter Lab Image
# ============================================================================
# Imagen basada en jupyter/scipy-notebook con herramientas adicionales
# para data engineering con Python
# ============================================================================

FROM jupyter/scipy-notebook:python-3.11

# Metadata
LABEL maintainer="Training Cloud Data"
LABEL description="Jupyter Lab environment for Python Data Engineering"
LABEL version="1.0"

# Switch to root para instalar paquetes del sistema
USER root

# ============================================================================
# System Dependencies
# ============================================================================

# Actualizar paquetes y agregar herramientas útiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    # PostgreSQL client
    postgresql-client \
    # Network tools
    curl \
    wget \
    netcat-openbsd \
    # Text processing
    vim \
    nano \
    jq \
    # Compression
    zip \
    unzip \
    # Version control
    git \
    # Timezone data
    tzdata \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Python Dependencies - Core Data Engineering
# ============================================================================

USER $NB_UID

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel

# Core data processing libraries
RUN pip install --no-cache-dir \
    # DataFrames y arrays
    pandas==2.2.0 \
    numpy==1.26.0 \
    polars==0.20.0 \
    # File formats
    pyarrow==15.0.0 \
    fastparquet==2024.2.0 \
    openpyxl==3.1.2 \
    xlrd==2.0.1 \
    # Database connectivity
    sqlalchemy==2.0.25 \
    psycopg2-binary==2.9.9 \
    pymongo==4.6.0 \
    # Data validation
    pandera==0.18.0 \
    pydantic==2.5.0 \
    jsonschema==4.21.0

# ============================================================================
# Python Dependencies - Development Tools
# ============================================================================

RUN pip install --no-cache-dir \
    # Code quality
    black==24.1.0 \
    flake8==7.0.0 \
    pylint==3.0.0 \
    mypy==1.8.0 \
    isort==5.13.0 \
    # Testing
    pytest==8.0.0 \
    pytest-cov==4.1.0 \
    pytest-mock==3.12.0 \
    hypothesis==6.98.0 \
    faker==23.0.0 \
    # Logging
    loguru==0.7.2 \
    python-json-logger==2.0.7 \
    colorlog==6.8.0

# ============================================================================
# Python Dependencies - HTTP & APIs
# ============================================================================

RUN pip install --no-cache-dir \
    requests==2.31.0 \
    httpx==0.26.0 \
    beautifulsoup4==4.12.0 \
    lxml==5.1.0

# ============================================================================
# Python Dependencies - Utilities
# ============================================================================

RUN pip install --no-cache-dir \
    python-dotenv==1.0.0 \
    click==8.1.7 \
    tabulate==0.9.0 \
    rich==13.7.0 \
    tqdm==4.66.0

# ============================================================================
# Python Dependencies - Data Visualization
# ============================================================================

RUN pip install --no-cache-dir \
    matplotlib==3.8.0 \
    seaborn==0.13.0 \
    plotly==5.18.0

# ============================================================================
# Python Dependencies - Performance
# ============================================================================

RUN pip install --no-cache-dir \
    joblib==1.3.0 \
    dask==2024.1.0 \
    numba==0.59.0

# ============================================================================
# Python Dependencies - Cloud & Storage (Optional)
# ============================================================================

# Descomentar si necesitas trabajar con cloud providers
# RUN pip install --no-cache-dir \
#     boto3==1.34.0 \
#     s3fs==2024.2.0 \
#     fsspec==2024.2.0 \
#     azure-storage-blob==12.19.0 \
#     google-cloud-storage==2.14.0

# ============================================================================
# JupyterLab Extensions
# ============================================================================

RUN pip install --no-cache-dir \
    # Variable inspector
    jupyterlab-lsp \
    python-lsp-server[all] \
    # Git integration
    jupyterlab-git \
    # Code formatter
    jupyterlab-code-formatter \
    # System monitor
    jupyterlab-system-monitor \
    # Spreadsheet viewer
    jupyterlab-spreadsheet-editor

# ============================================================================
# Jupyter Configuration
# ============================================================================

# Crear directorios de trabajo
RUN mkdir -p /home/jovyan/work/notebooks \
    && mkdir -p /home/jovyan/work/data \
    && mkdir -p /home/jovyan/work/exercises \
    && mkdir -p /home/jovyan/work/scripts

# Configuración de Jupyter
RUN jupyter labextension enable jupyterlab-git && \
    jupyter lab build --dev-build=False --minimize=True

# ============================================================================
# Environment Variables
# ============================================================================

ENV JUPYTER_ENABLE_LAB=yes
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ============================================================================
# Working Directory
# ============================================================================

WORKDIR /home/jovyan/work

# ============================================================================
# Health Check
# ============================================================================

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8888/api || exit 1

# ============================================================================
# Expose Port
# ============================================================================

EXPOSE 8888

# ============================================================================
# Default Command
# ============================================================================

# El comando será sobrescrito por docker-compose
CMD ["start-notebook.sh", "--NotebookApp.token='python-data-2026'"]

# ============================================================================
# Build Instructions
# ============================================================================
#
# Build:
#   docker build -t python-data-jupyter:latest .
#
# Run standalone:
#   docker run -p 8888:8888 \
#     -v $(pwd)/notebooks:/home/jovyan/work/notebooks \
#     -v $(pwd)/data:/home/jovyan/work/data \
#     python-data-jupyter:latest
#
# Check size:
#   docker images python-data-jupyter
#
# ============================================================================
