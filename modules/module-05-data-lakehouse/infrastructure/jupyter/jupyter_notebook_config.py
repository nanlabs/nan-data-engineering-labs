# ============================================================================
# Jupyter Notebook Configuration - Data Lakehouse
# ============================================================================
# Configuration for Jupyter Lab with Spark integration
# ============================================================================

import os

# -----------------------------------------------------------------------------
# Application Configuration
# -----------------------------------------------------------------------------
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# Disable token/password for local development
c.ServerApp.token = ''
c.ServerApp.password = ''

# Allow all origins (for Docker networking)
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True

# -----------------------------------------------------------------------------
# Directory Configuration
# -----------------------------------------------------------------------------
c.ServerApp.root_dir = '/home/jovyan/work'
c.ServerApp.preferred_dir = '/home/jovyan/work'

# -----------------------------------------------------------------------------
# Kernel Configuration
# -----------------------------------------------------------------------------
# Default kernel
c.MultiKernelManager.default_kernel_name = 'python3'

# Kernel timeout (increase for long-running Spark jobs)
c.ServerApp.kernel_manager_class = 'notebook.services.kernels.kernelmanager.MappingKernelManager'

# -----------------------------------------------------------------------------
# Terminal Configuration
# -----------------------------------------------------------------------------
c.ServerApp.terminals_enabled = True
c.TerminalManager.shell_command = ['/bin/bash']

# -----------------------------------------------------------------------------
# File Management
# -----------------------------------------------------------------------------
c.ContentsManager.allow_hidden = True
c.FileContentsManager.delete_to_trash = False

# -----------------------------------------------------------------------------
# PySpark Configuration
# -----------------------------------------------------------------------------
# Set Spark environment variables
os.environ['PYSPARK_PYTHON'] = '/opt/conda/bin/python'
os.environ['PYSPARK_DRIVER_PYTHON'] = '/opt/conda/bin/python'
os.environ['PYSPARK_DRIVER_PYTHON_OPTS'] = ''

# Spark Master URL
os.environ['SPARK_MASTER'] = 'spark://spark-master:7077'

# S3/MinIO configuration
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['S3_ENDPOINT'] = 'http://minio:9000'

# Hive Metastore
os.environ['HIVE_METASTORE_URIS'] = 'thrift://hive-metastore:9083'

# -----------------------------------------------------------------------------
# Security (disabled for local development)
# -----------------------------------------------------------------------------
c.ServerApp.disable_check_xsrf = True

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
c.Application.log_level = 'INFO'

# -----------------------------------------------------------------------------
# Extensions
# -----------------------------------------------------------------------------
# Enable JupyterLab by default
c.ServerApp.default_url = '/lab'

# ============================================================================
# Notes:
# ============================================================================
# This configuration is for LOCAL DEVELOPMENT ONLY.
# For production environments:
# 1. Enable authentication (token/password)
# 2. Use HTTPS
# 3. Restrict allowed origins
# 4. Enable XSRF checks
# ============================================================================
