# 🔧 Troubleshooting - Troubleshooting Guide

## 📋 Table of Contents

1. [Installation Problems](#installation-problems)
2. [Virtual Environment Errors](#virtual-environment-errors)
3. [Dependency Problems](#dependency-problems)
4. [Test Errors](#test-errors)
5. [Data Issues](#data-issues)
6. [Jupyter Lab Issues](#jupyter-lab-issues)
7. [Performance Issues](#performance-issues)
8. [Docker and Containers](#docker-and-containers)

---

## 🔴 Installation Problems

### Error: "python3: command not found"

**Symptoms**:
```bash
$ python3 --version
bash: python3: command not found
```

**Solution**:

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Linux (Fedora/RHEL)**:
```bash
sudo dnf install python3 python3-pip
```

**macOS**:
```bash
brew install python3
```

**Verify installation**:
```bash
python3 --version  # Debe mostrar Python 3.8+
```

---

### Error: "Permission denied" al ejecutar scripts

**Yesntomas**:
```bash
$ ./scripts/setup.sh
bash: ./scripts/setup.sh: Permission denied
```

**Solution**:
```bash
# Dar permisos de ejecución a los scripts
chmod +x scripts/*.sh

# O individualmente
chmod +x scripts/setup.sh
chmod +x scripts/validate.sh
chmod +x scripts/reset_env.sh
chmod +x scripts/run_jupyter.sh
```

---

## 🟠 Errores de Entorno Virtual

### Error: "No module named 'venv'"

**Yesntomas**:
```bash
$ python3 -m venv venv
/usr/bin/python3: No module named venv
```

**Solution**:

**Linux (Ubuntu/Debian)**:
```bash
sudo apt install python3-venv
```

**Alternativa**: Usar `virtualenv`
```bash
pip3 install virtualenv
virtualenv venv
```

---

### Error: Entorno virtual no se activa

**Yesntomas**:
```bash
$ source venv/bin/activate
(no cambia el prompt)
```

**Solution**:

**Verify that the environment was created correctly**:
```bash
ls -la venv/bin/activate
```

**Si no existe, recrear**:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

**Verify activation**:
```bash
which python  # Debe mostrar ruta dentro de venv/
```

---

### Error: "cannot activate virtualenv from bash script"

**Yesntomas**:
El script ejecuta pero el entorno no permanece activo.

**Explanation**:
Bash scripts run in a subshell, so the activation does not persist.

**Solution**:
```bash
# En lugar de ejecutar el script:
./scripts/setup.sh

# Usa source:
source scripts/setup.sh

# O activa manualmente después:
./scripts/setup.sh
source venv/bin/activate
```

---

## 🟡 Problemas con Dependencias

### Error: "Could not find a version that satisfies the requirement"

**Yesntomas**:
```bash
ERROR: Could not find a version that satisfies the requirement pandas==2.0.0
```

**Solution**:

**1. Actualizar pip**:
```bash
pip install --upgrade pip
```

**2. Check Python version**:
```bash
python --version  # Debe ser 3.8+
```

**3. Install without specific version**:
```bash
pip install pandas  # Instala la última compatible
```

**4. Limpiar cache de pip**:
```bash
pip cache purge
pip install -r requirements.txt
```

---

### Error: "ImportError: No module named 'pandas'"

**Yesntomas**:
```python
>>> import pandas
ImportError: No module named 'pandas'
```

**Diagnosis**:
```bash
# Verificar que estás en el entorno virtual
echo $VIRTUAL_ENV  # Debe mostrar ruta a venv

# Verificar dónde está instalado pandas
pip list | grep pandas

# Verificar qué Python estás usando
which python
```

**Solution**:
```bash
# Activar entorno
source venv/bin/activate

# Reinstalar pandas
pip install pandas

# Verificar instalación
python -c "import pandas; print(pandas.__version__)"
```

---

### Error: Conflictos de dependencias

**Yesntomas**:
```bash
ERROR: package-a 1.0 has requirement package-b<2.0, but you have package-b 2.1
```

**Solution**:

**1. Crear requirements limpio**:
```bash
# Resetear entorno
./scripts/reset_env.sh --full

# Recrear
./scripts/setup.sh
```

**2. Usar pip-tools**:
```bash
pip install pip-tools
pip-compile requirements.in
pip-sync
```

---

## 🔵 Errores en Tests

### Error: "No tests ran" o "No tests collected"

**Yesntomas**:
```bash
$ pytest
collected 0 items
```

**Diagnosis**:
```bash
# Verificar ubicación de tests
find . -name "test_*.py"

# Verificar pytest.ini
cat pytest.ini
```

**Solution**:

**1. Ejecutar desde directorio correcto**:
```bash
cd /path/to/module-04-python-for-data
pytest exercises/
```

**2. Especificar ruta completa**:
```bash
pytest exercises/01-python-basics/tests/
```

**3. Verificar nombres de archivos**:
```bash
# Los tests deben empezar con test_
mv basics_test.py test_basics.py
```

---

### Error: "fixture not found"

**Yesntomas**:
```bash
fixture 'customers_df' not found
```

**Solution**:

**1. Verificar conftest.py existe**:
```bash
ls validation/conftest.py
```

**2. Verificar scope del fixture**:
```python
# En conftest.py
@pytest.fixture(scope="session")
def customers_df():
    return pd.read_csv("data/raw/customers.csv")
```

**3. Ejecutar desde directorio correcto**:
```bash
cd modules/module-04-python-for-data
pytest validation/
```

---

### Error: "FileNotFoundError" en tests

**Yesntomas**:
```python
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/customers.csv'
```

**Solution**:

**1. Generar datos**:
```bash
python data/scripts/generate_all_datasets.py
```

**2. Verificar rutas relativas**:
```python
# Usar Path absoluto en tests
from pathlib import Path

MODULE_DIR = Path(__file__).parent.parent.parent
DATA_PATH = MODULE_DIR / "data" / "raw" / "customers.csv"
```

**3. Run tests from the root of the module**:
```bash
cd modules/module-04-python-for-data
pytest
```

---

### Error: Tests lentos

**Yesntomas**:
Los tests tardan mucho en ejecutar.

**Solution**:

**1. Run only quick tests**:
```bash
./scripts/validate.sh --fast
```

**2. Ejecutar tests en paralelo**:
```bash
pip install pytest-xdist
pytest -n auto  # Usa todos los cores
```

**3. Usar markers para filtrar**:
```bash
pytest -m "not slow"
pytest -m "unit"
```

---

## 🟢 Problemas con Datos

### Error: "Data files not found"

**Yesntomas**:
```bash
FileNotFoundError: data/raw/customers.csv not found
```

**Solution**:

**1. Generar todos los datasets**:
```bash
python data/scripts/generate_all_datasets.py
```

**2. Verificar estructura**:
```bash
ls -lh data/raw/
# Debe mostrar:
# customers.csv
# transactions.csv
# products.csv
# orders.json
# user_activity.json
```

**3. Check sizes**:
```bash
du -h data/raw/*
# customers.csv: ~2MB
# transactions.csv: ~15MB
# products.csv: ~50KB
# orders.json: ~25MB
# user_activity.json: ~10MB
```

---

### Error: "ValueError: could not convert string to float"

**Yesntomas**:
```python
pd.read_csv("data.csv")
ValueError: could not convert string to float: 'N/A'
```

**Solution**:

**Especificar valores nulos**:
```python
df = pd.read_csv(
    "data.csv",
    na_values=['N/A', 'null', '', 'None']
)
```

**Forzar tipos**:
```python
df = pd.read_csv(
    "data.csv",
    dtype={'columna': str}  # Leer como string primero
)
df['columna'] = pd.to_numeric(df['columna'], errors='coerce')
```

---

### Error: "MemoryError" al cargar datos

**Yesntomas**:
```python
df = pd.read_csv("big_file.csv")
MemoryError
```

**Solution**:

**1. Leer por chunks**:
```python
chunks = []
for chunk in pd.read_csv("big_file.csv", chunksize=10000):
    # Procesar chunk
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
```

**2. Leer solo columns necesarias**:
```python
df = pd.read_csv(
    "big_file.csv",
    usecols=['col1', 'col2', 'col3']
)
```

**3. Optimizar tipos**:
```python
df = pd.read_csv(
    "big_file.csv",
    dtype={'id': 'int32', 'category': 'category'}
)
```

---

## 🟣 Jupyter Lab Issues

### Error: "Jupyter: command not found"

**Yesntomas**:
```bash
$ jupyter lab
bash: jupyter: command not found
```

**Solution**:

**1. Verificar entorno activo**:
```bash
echo $VIRTUAL_ENV
source venv/bin/activate
```

**2. Instalar Jupyter**:
```bash
pip install jupyter jupyterlab
```

**3. Verify installation**:
```bash
which jupyter
jupyter --version
```

---

### Error: "Port already in use"

**Yesntomas**:
```bash
OSError: [Errno 48] Address already in use
```

**Solution**:

**1. Usar otro puerto**:
```bash
./scripts/run_jupyter.sh --port 9000
```

**2. Encontrar y matar proceso**:
```bash
# Encontrar proceso usando el puerto
lsof -ti:8888

# Matar proceso
kill -9 $(lsof -ti:8888)
```

**3. Usar puerto aleatorio**:
```bash
jupyter lab --port=0
```

---

### Error: Kernel no conecta

**Yesntomas**:
El notebook muestra "Connecting to kernel..." indefinidamente.

**Solution**:

**1. Reiniciar kernel**:
- Kernel → Restart Kernel

**2. Limpiar cache**:
```bash
rm -rf ~/.jupyter/lab/
jupyter lab clean
```

**3. Reinstalar ipykernel**:
```bash
pip install --upgrade ipykernel
python -m ipykernel install --user
```

---

## ⚡ Performance Issues

### Operaciones pandas muy lentas

**Yesntomas**:
Operaciones simples tardan mucho.

**Solution**:

**1. Avoid loops, use vectorization**:
```python
# ❌ Lento
for i in range(len(df)):
    df.loc[i, 'new'] = df.loc[i, 'old'] * 2

# ✅ Rápido
df['new'] = df['old'] * 2
```

**2. Usar dtypes eficientes**:
```python
# Convertir a category
df['ciudad'] = df['ciudad'].astype('category')

# Usar int32 en lugar de int64
df['id'] = df['id'].astype('int32')
```

**3. Usar query() para filtros**:
```python
# ✅ Más rápido
df.query('edad > 25 and ciudad == "Madrid"')
```

---

### Alto uso de memoria

**Yesntomas**:
```python
df.memory_usage(deep=True).sum()  # Muy alto
```

**Solution**:

**1. Liberar memoria no usada**:
```python
import gc
del df_old
gc.collect()
```

**2. Usar chunks**:
```python
for chunk in pd.read_csv('file.csv', chunksize=10000):
    process(chunk)
```

**3. Optimizar columns**:
```python
# Antes
df.memory_usage(deep=True)

# Optimizar
df['ciudad'] = df['ciudad'].astype('category')
df['id'] = df['id'].astype('int32')

# Después
df.memory_usage(deep=True)  # Menor
```

---

## 🐳 Docker y Containers

### Error: "docker: command not found"

**Solution**:

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**macOS**:
```bash
brew install --cask docker
```

---

### Error: "permission denied" con Docker

**Yesntomas**:
```bash
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution**:
```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Logout y login nuevamente
# O reiniciar sesión
newgrp docker

# Verificar
docker ps
```

---

### Error: Container no inicia

**Yesntomas**:
```bash
$ docker-compose up
ERROR: container exited with code 1
```

**Diagnosis**:
```bash
# Ver logs
docker-compose logs

# Ver logs específicos
docker-compose logs jupyter

# Inspeccionar container
docker inspect container_name
```

**Solution**:

**1. Reconstruir containers**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

**2. Clear volumes**:
```bash
docker-compose down -v
docker-compose up
```

---

## 📞 Obtener Ayuda Adicional

### Pasos para reportar un problema

1. **Collect information**:
```bash
# Versión de Python
python --version

# Versiones de paquetes
pip list

# Entorno
echo $VIRTUAL_ENV
echo $PYTHONPATH
```

2. **Reproduce el error**:
```bash
# Ejecuta con modo verbose
pytest -vv test_file.py::test_function
```

3. **Revisa logs**:
```bash
# Logs de pytest
cat logs/pytest.log

# Logs de Jupyter
cat logs/jupyter.log
```

### useful resources

- **Pandas Documentation**: https://pandas.pydata.org/docs/
- **Pytest Documentation**: https://docs.pytest.org/
- **Stack Overflow**: Find your specific error
- **GitHub Issues**: Check module issues

### Diagnostic commands

```bash
# Información del sistema
uname -a
python --version
pip --version

# Información del módulo
ls -la
du -h data/
pytest --collect-only

# Verificar instalaciones
python -c "import pandas; print(pandas.__version__)"
python -c "import numpy; print(numpy.__version__)"
python -c "import pytest; print(pytest.__version__)"
```

---

**Last update**: Module 04 - Step 8
**Version**: 1.0
