# Infraestructura: Jupyter Lab con Docker

This folder contains the Docker configuration for running Jupyter Lab and supporting services for the Python for Data Engineering module.

## Contenido

```
infrastructure/
├── Dockerfile              # Imagen personalizada de Jupyter Lab
├── docker-compose.yml      # Orquestación de servicios
├── .env.example           # Template de variables de entorno
├── jupyter_config.py      # Configuración de Jupyter Lab
└── README.md              # Este archivo
```

## services Disponibles

### 1. Jupyter Lab (Principal)

**Imagen**: Basada en `jupyter/scipy-notebook:python-3.11`

**features**:
- Python 3.11 con bibliotecas de data engineering
- pandas, NumPy, Polars, PyArrow
- SQLAlchemy, psycopg2 para databases
- Herramientas de testing (pytest)
- Extensiones de JupyterLab (git, formatters, etc.)
- Mounted volumes for persistence

**Acceso**:
- URL: http://localhost:8888
- Token: Ver en `.env` (default: `python-data-2026`)

### 2. PostgreSQL (Opcional)

**Imagen**: `postgres:15-alpine`

**Uso**: Para ejercicios que requieren conectar Python con databases

**Acceso**:
- Host: `localhost`(from machine) or`postgres` (desde Jupyter)
- Port: 5433 (so as not to conflict with local installation)
- Credenciales: Ver `.env`

### 3. MinIO (Opcional)

**Imagen**: `minio/minio:latest`

**Use**: S3 simulation for exercises with storage cloud

**Acceso**:
- API: http://localhost:9000
- Console: http://localhost:9001
- Credenciales: Ver `.env`

---

## Quick Setup

### 1. Copiar variables de entorno

```bash
# Desde la carpeta infrastructure/
cp .env.example .env

# Editar valores si es necesario
nano .env
```

### 2. Iniciar services

```bash
# Iniciar solo Jupyter Lab
docker-compose up -d jupyter

# O iniciar todos los servicios (si descomentaste postgres/minio)
docker-compose up -d
```

### 3. Acceder a Jupyter Lab

```bash
# Ver logs y obtener URL con token
docker-compose logs jupyter

# O abrir directamente
open http://localhost:8888
```

**Token por defecto**: `python-data-2026`

---

## Useful Commands

### Service management

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f jupyter

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ elimina datos)
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart jupyter

# Ver estado de servicios
docker-compose ps
```

### Build y Debugging

```bash
# Reconstruir imagen (después de modificar Dockerfile)
docker-compose build --no-cache jupyter

# Ejecutar comando en container
docker-compose exec jupyter bash

# Ver uso de recursos
docker stats python-data-jupyter

# Inspeccionar container
docker inspect python-data-jupyter
```

### Mantenimiento

```bash
# Limpiar imágenes no usadas
docker system prune -a

# Ver espacio usado
docker system df

# Actualizar imagen base
docker-compose pull
docker-compose up -d --build
```

---

## Volume Structure

The following module directories are mounted in the container:

### Persistent Volumes (Read-Write)

| Local | Container | Description |
|-------|-----------|-------------|
| `./notebooks` | `/home/jovyan/work/notebooks`| Your exploration notebooks |
| `../data` | `/home/jovyan/work/data` | Datasets y archivos de datos |

### Read-Only Volumes

| Local | Container | Description |
|-------|-----------|-------------|
| `../exercises` | `/home/jovyan/work/exercises` | Ejercicios (evita sobrescribir) |
| `../scripts` | `/home/jovyan/work/scripts` | Scripts de utilidad |
| `../assets` | `/home/jovyan/work/assets` | Cheatsheets y resources |

**Note**: Read-only volumes prevent accidental modifications of exercises and solutions.

---

## Jupyter Lab Setup

### jupyter_config.py

File with custom configuration:

- **Autoreload**: Automatic reload of modified modules
- **Autosave**: Automatic save every minute
- **Plots**: Inline matplotlib configuration
- **Logging**: Formato y nivel de logs
- **Security**: CORS y acceso remoto

**Modify settings**:

1. Editar `jupyter_config.py`
2. Reiniciar: `docker-compose restart jupyter`

### Extensiones Instaladas

- **jupyterlab-git**: Integration with Git
- **jupyterlab-code-formatter**: Automatic formatting (Black)
- **jupyterlab-lsp**: Language Server Protocol (autocompletado mejorado)
- **jupyterlab-system-monitor**: Monitor de resources

---

## Trabajar con Notebooks

### Crear Notebook

```python
# 1. Acceder a http://localhost:8888
# 2. Click en "Python 3" bajo Notebook
# 3. Guardar en: work/notebooks/mi_notebook.ipynb
```

### Automatic Imports

The environment is configured with common imports:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

### Connect to PostgreSQL (if enabled)

```python
from sqlalchemy import create_engine

# Connection string
DATABASE_URL = "postgresql://python_user:python_pass@postgres:5432/python_data"

# Crear engine
engine = create_engine(DATABASE_URL)

# Leer query
df = pd.read_sql("SELECT * FROM mi_tabla", engine)
```

### Leer/Escribir Archivos

```python
# Leer CSV
df = pd.read_csv('/home/jovyan/work/data/raw/datos.csv')

# Escribir Parquet
df.to_parquet('/home/jovyan/work/data/processed/datos.parquet')

# Los archivos persisten en tu máquina local
```

---

## Trabajar con Terminal

### Abrir Terminal en Jupyter Lab

1. Click en "+" (New Launcher)
2. Click en "Terminal" bajo "Other"

### Useful Commands in Terminal

```bash
# Ver estructura de archivos
tree /home/jovyan/work

# Ejecutar script Python
python /home/jovyan/work/scripts/mi_script.py

# Instalar paquete adicional (temporal)
pip install nueva-libreria

# Ver procesos
htop

# Probar conectividad PostgreSQL
pg_isready -h postgres -p 5432
```

---

## Habilitar services Opcionales

### Habilitar PostgreSQL

1. Editar `docker-compose.yml`
2. Uncomment section`postgres`
3. Descomentar volumen `postgres_data`
4. Guardar y ejecutar:

```bash
docker-compose up -d postgres
```

### Habilitar MinIO (S3 local)

1. Editar `docker-compose.yml`
2. Uncomment section`minio`
3. Descomentar volumen `minio_data`
4. Guardar y ejecutar:

```bash
docker-compose up -d minio
```

**Acceder a MinIO Console**:
- URL: http://localhost:9001
- Usuario: `minio_admin` (ver `.env`)
- Password: `minio_pass123` (ver `.env`)

---

## Add Python Libraries

### Temporal (se pierde al recrear container)

```bash
# Desde terminal de Jupyter Lab
pip install nombre-libreria

# O desde notebook
!pip install nombre-libreria
```

### Permanent (persists in reconstruction)

**Method 1: Modify requirements.txt**

```bash
# 1. Editar modules/module-04-python-for-data/requirements.txt
echo "nueva-libreria>=1.0.0" >> requirements.txt

# 2. Reconstruir
docker-compose up -d --build
```

**Method 2: Modify Dockerfile**

```dockerfile
# Editar infrastructure/Dockerfile
# Agregar en la sección apropiada:
RUN pip install --no-cache-dir nueva-libreria==1.0.0

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

---

## Troubleshooting

### Problema: Jupyter no inicia

**Yesntomas**: Container se detiene inmediatamente

**Solution**:

```bash
# Ver logs detallados
docker-compose logs jupyter

# Verificar sintaxis de archivos
docker-compose config

# Reconstruir desde cero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Problema: Puerto 8888 ocupado

**Yesntomas**: Error "port is already allocated"

**Solution**:

```bash
# Opción 1: Cambiar puerto en .env
JUPYTER_PORT=8889

# Opción 2: Detener proceso que usa el puerto
lsof -i :8888
kill -9 <PID>
```

### Problema: No puedo guardar notebooks

**Yesntomas**: Error de permisos al guardar

**Solution**:

```bash
# Verificar permisos de carpeta notebooks
ls -la infrastructure/notebooks/

# Dar permisos (Linux/Mac)
chmod -R 777 infrastructure/notebooks/

# Reiniciar container
docker-compose restart jupyter
```

### Problema: Out of Memory

**Yesntomas**: Kernel muere procesando datos grandes

**Solution**:

```bash
# Editar docker-compose.yml
# Aumentar límite de memoria:
deploy:
  resources:
    limits:
      memory: 8G  # Aumentar de 4G a 8G

# Reiniciar
docker-compose down
docker-compose up -d
```

### Problem: Code changes are not reflected

**Yesntomas**: Modificaciones en .py no se cargan en notebook

**Solution**:

```python
# En notebook, habilitar autoreload
%load_ext autoreload
%autoreload 2

# O reiniciar kernel: Kernel -> Restart Kernel
```

### Problema: No puedo conectar a PostgreSQL

**Yesntomas**: Connection refused o timeout

**Solution**:

```bash
# 1. Verificar que postgres está corriendo
docker-compose ps postgres

# 2. Verificar health
docker-compose exec postgres pg_isready

# 3. Verificar connection string
# Desde Jupyter, debe ser: postgres:5432
# Desde host, debe ser: localhost:5433

# 4. Ver logs
docker-compose logs postgres
```

---

## Performance Tips

### 1. Allocate more resources

Edit limits on`docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'    # Aumentar CPUs
      memory: 8G     # Aumentar RAM
```

### 2. Use delegated volumes (Mac)

Para mejor performance en macOS:

```yaml
volumes:
  - ./notebooks:/home/jovyan/work/notebooks:delegated
```

### 3. Desactivar extensiones no usadas

En `jupyter_config.py`, comentar extensiones:

```python
# c.ServerApp.jpserver_extensions = {
#     'jupyterlab_git': True,  # Comentar si no usas Git
# }
```

### 4. Limpiar outputs de notebooks

```bash
# Desde terminal
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

---

## Security Best Practices

### 1. Cambiar token por defecto

```bash
# En .env, generar token seguro
JUPYTER_TOKEN=$(openssl rand -hex 32)
```

### 2. No exponer puertos innecesarios

Si no necesitas acceso externo, omite el mapeo de puertos:

```yaml
# En docker-compose.yml, comentar:
# ports:
#   - "8888:8888"
```

### 3. Usar secrets para passwords

For production, use Docker secrets:

```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### 4. Ejecutar container como usuario no-root

Ya configurado con usuario `jovyan` (non-root) en la imagen base.

---

## Backup y Restore

### Backup de Notebooks

```bash
# Backup manual
tar -czf notebooks-backup-$(date +%Y%m%d).tar.gz notebooks/

# Script de backup automático (agregar a cron)
#!/bin/bash
docker-compose exec jupyter bash -c "tar -czf /home/jovyan/work/notebooks-backup-$(date +%Y%m%d).tar.gz /home/jovyan/work/notebooks"
```

### Backup de PostgreSQL

```bash
# Exportar database
docker-compose exec postgres pg_dump -U python_user python_data > backup.sql

# Restaurar
docker-compose exec -T postgres psql -U python_user python_data < backup.sql
```

---

## resources Adicionales

### Official Documentation

- **Jupyter Docker Stacks**: https://jupyter-docker-stacks.readthedocs.io/
- **Jupyter Lab**: https://jupyterlab.readthedocs.io/
- **Docker Compose**: https://docs.docker.com/compose/

### Base Images Available

- `jupyter/base-notebook`: Minimum
- `jupyter/minimal-notebook`: + basic tools
- `jupyter/scipy-notebook`: + NumPy, pandas, matplotlib (usamos esta)
- `jupyter/datascience-notebook`: + Julia, R
- `jupyter/pyspark-notebook`: + PySpark

### Alternativas

Si prefieres no usar Docker:

1. **Local venv**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install jupyterlab
   pip install -r requirements.txt
   jupyter lab
   ```

2. **Conda**:
   ```bash
   conda create -n python-data python=3.11
   conda activate python-data
   pip install -r requirements.txt
   jupyter lab
   ```

3. **Google Colab**: Gratuito, en la cloud (pero sin persistencia local)

---

## Next Steps

After configuring the infrastructure:

1. ✅ Verificar que Jupyter Lab funciona
2. ✅ Crear un notebook de prueba
3. ✅ Importar pandas y crear un DataFrame
4. ➡️ Continue with **Step 4: Data** (practice datasets)
5. ➡️ Continue with **Step 5: Exercises** (practical exercises)

---

**Unresolved problems?**

See complete troubleshooting guide at`docs/troubleshooting.md` (creado en Paso 8)

**Suggestions for improvement?**

This module is constantly evolving. Feedback welcome!
