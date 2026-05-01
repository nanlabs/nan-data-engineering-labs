# ============================================================================
# Jupyter Lab Configuration
# ============================================================================
# Configuración personalizada para Jupyter Lab
# Este archivo se monta en /home/jovyan/.jupyter/jupyter_lab_config.py
# ============================================================================

import os

# ----------------------------------------------------------------------------
# Server Configuration
# ----------------------------------------------------------------------------

# Permitir acceso desde cualquier IP (necesario para Docker)
c.ServerApp.ip = '0.0.0.0'

# Puerto de escucha
c.ServerApp.port = 8888

# Permitir origen remoto
c.ServerApp.allow_origin = '*'

# Deshabilitar redirección a /tree
c.ServerApp.open_browser = False

# Token de autenticación (obtener de variable de entorno)
c.ServerApp.token = os.environ.get('JUPYTER_TOKEN', 'python-data-2026')

# No requerir password adicional
c.ServerApp.password = ''

# Permitir root (necesario en algunos casos con Docker)
c.ServerApp.allow_root = True

# ----------------------------------------------------------------------------
# Content Manager
# ----------------------------------------------------------------------------

# Directorio raíz de notebooks
c.ServerApp.root_dir = '/home/jovyan/work'

# Crear directorios si no existen
c.FileContentsManager.checkpoints_dir = '/home/jovyan/work/.ipynb_checkpoints'

# ----------------------------------------------------------------------------
# Extensions
# ----------------------------------------------------------------------------

# Habilitar extensiones
c.ServerApp.jpserver_extensions = {
    'jupyterlab': True,
    'jupyterlab_git': True,
}

# ----------------------------------------------------------------------------
# Kernel Manager
# ----------------------------------------------------------------------------

# Timeout para inicio de kernel (segundos)
c.KernelManager.shutdown_wait_time = 10.0

# Reinicio automático de kernels
c.KernelRestarter.restart_limit = 5

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------

# Nivel de logging
c.Application.log_level = os.environ.get('LOG_LEVEL_JUPYTER', 'INFO')

# Formato de logs
c.Application.log_format = '[%(levelname)s] %(asctime)s - %(name)s - %(message)s'

# ----------------------------------------------------------------------------
# Auto-save
# ----------------------------------------------------------------------------

# Intervalo de auto-guardado (segundos)
c.FileContentsManager.checkpoints_kwargs = {'root_dir': '.ipynb_checkpoints'}

# ----------------------------------------------------------------------------
# Terminal
# ----------------------------------------------------------------------------

# Shell por defecto en terminal
c.ServerApp.terminado_settings = {
    'shell_command': ['/bin/bash']
}

# ----------------------------------------------------------------------------
# Performance
# ----------------------------------------------------------------------------

# Límite de tamaño de celda output (bytes)
c.ServerApp.iopub_data_rate_limit = 10000000

# Timeout para mensajes (segundos)
c.ServerApp.iopub_msg_rate_limit = 3000

# ----------------------------------------------------------------------------
# IPython Configuration
# ----------------------------------------------------------------------------

# Autoload extensions
c.InteractiveShellApp.extensions = []

# Autoreload (útil para desarrollo)
if os.environ.get('AUTORELOAD', 'true').lower() == 'true':
    c.InteractiveShellApp.exec_lines = [
        '%load_ext autoreload',
        '%autoreload 2',
        'print("Autoreload habilitado")'
    ]

# Configuración de plots inline
c.InlineBackend.figure_formats = {'retina', 'png'}
c.InlineBackend.rc = {
    'figure.figsize': (12, 8),
    'font.size': 12,
    'figure.dpi': 100
}

# ----------------------------------------------------------------------------
# Notebook Settings
# ----------------------------------------------------------------------------

# Mostrar números de línea por defecto
c.LineNumbersExtension.default_state = 'on'

# ----------------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------------

# Permitir inline frames (útil para embeber notebooks)
c.ServerApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': "frame-ancestors 'self' *"
    }
}

# Habilitar CORS
c.ServerApp.allow_remote_access = True

# ----------------------------------------------------------------------------
# Workspace Settings
# ----------------------------------------------------------------------------

# Layout por defecto
c.LabApp.default_url = '/lab/tree/notebooks'

# ----------------------------------------------------------------------------
# Custom Startup
# ----------------------------------------------------------------------------

# Ejecutar código al iniciar (opcional)
startup_code = """
# Imports comunes
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

# Configuración de visualización
%matplotlib inline
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Warnings
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

print("✅ Entorno configurado correctamente")
print(f"📊 pandas: {pd.__version__}")
print(f"🔢 numpy: {np.__version__}")
"""

# Si quieres ejecutar código al inicio, descomenta:
# c.InteractiveShellApp.exec_lines.append(startup_code)

# ----------------------------------------------------------------------------
# Notas
# ----------------------------------------------------------------------------
#
# Para aplicar cambios:
# 1. Modificar este archivo
# 2. Reiniciar container: docker-compose restart jupyter
#
# Para debugging:
# - Ver logs: docker-compose logs -f jupyter
# - Verificar config: docker-compose exec jupyter jupyter lab --show-config
#
# Documentación completa:
# https://jupyter-server.readthedocs.io/en/latest/users/configuration.html
#
# ============================================================================
