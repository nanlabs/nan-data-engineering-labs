# Architectures and Patterns: Python for Data Engineering

## Table of Contents

1. [Introduction](#introduction)
2. [Data Pipeline Architecture](#data-pipeline-architecture)
3. [Design Patterns for Data Engineering](#design-patterns-for-data-engineering)
4. [Python Project Architecture](#python-project-architecture)
5. [Virtual Environments and Dependency Management](#virtual-environments-and-dependency-management)
6. [Testing Strategy](#testing-strategy)
7. [CI/CD for Data Pipelines](#cicd-for-data-pipelines)
8. [Observability and Monitoring](#observability-and-monitoring)
9. [Scalability and Performance](#scalability-and-performance)
10. [Security and Secrets Management](#security-and-secrets-management)

---

## Introduction

Good architecture is essential to building maintainable, scalable and robust data pipelines. This document explores architectural patterns, best practices, and project structures for data engineering with Python.

### Architectural Principles

**SOLID in Data Engineering**:
- **S**ingle Responsibility: Each module/function has a responsibility
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Interchangeable implementations
- **I**nterface Segregation: Specific, non-monolithic interfaces
- **D**ependency Inversion: Depend on abstractions, not implementations

**Data Specific Principles**:
- **Idempotencia**: Mismos inputs → mismos outputs siempre
- **Atomicidad**: Operaciones completas o rollback completo
- **Incrementalidad**: Procesar solo datos nuevos/modificados
- **Trazabilidad**: Saber origen y transformaciones de cada dato
- **Recuperabilidad**: Poder reintentar desde punto de fallo

---

## Arquitectura de Pipelines de Datos

### ETL vs ELT

#### ETL (Extract, Transform, Load)

```python
class ETLPipeline:
    """
    ETL tradicional: Transformaciones antes de cargar
    Usado cuando: destino es OLTP o recursos limitados
    """
    
    def __init__(self, extractor, transformer, loader):
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def ejecutar(self, config: Dict) -> Dict[str, int]:
        """Ejecuta pipeline ETL completo"""
        try:
            # 1. Extract
            self.logger.info("Iniciando extracción...")
            datos_raw = self.extractor.extraer(config['source'])
            self.logger.info(f"Extraídos {len(datos_raw)} registros")
            
            # 2. Transform
            self.logger.info("Iniciando transformación...")
            datos_transformados = self.transformer.transformar(datos_raw)
            self.logger.info(f"Transformados {len(datos_transformados)} registros")
            
            # 3. Load
            self.logger.info("Iniciando carga...")
            resultado = self.loader.cargar(datos_transformados, config['destination'])
            self.logger.info(f"Cargados {resultado['registros']} registros")
            
            return {
                'extraidos': len(datos_raw),
                'transformados': len(datos_transformados),
                'cargados': resultado['registros']
            }
            
        except Exception as e:
            self.logger.error(f"Error en pipeline ETL: {e}")
            raise
```

#### ELT (Extract, Load, Transform)

```python
class ELTPipeline:
    """
    ELT moderno: Carga primero, transforma en destino
    Usado cuando: destino es data warehouse/lakehouse con poder de cómputo
    """
    
    def __init__(self, extractor, loader, transformer_sql):
        self.extractor = extractor
        self.loader = loader
        self.transformer_sql = transformer_sql
        self.logger = logging.getLogger(__name__)
    
    def ejecutar(self, config: Dict) -> Dict[str, int]:
        """Ejecuta pipeline ELT completo"""
        try:
            # 1. Extract
            self.logger.info("Iniciando extracción...")
            datos_raw = self.extractor.extraer(config['source'])
            
            # 2. Load (staging area)
            self.logger.info("Cargando a staging...")
            self.loader.cargar_staging(datos_raw)
            
            # 3. Transform (SQL en warehouse)
            self.logger.info("Ejecutando transformaciones SQL...")
            resultado = self.transformer_sql.ejecutar_transformaciones(
                staging_table=config['staging_table'],
                target_table=config['target_table']
            )
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error en pipeline ELT: {e}")
            raise
```

### pipeline Pattern: Composition of Transformations

```python
from typing import Callable, List, Any
from functools import reduce

class DataPipeline:
    """
    Pipeline composable de transformaciones
    Permite encadenar múltiples pasos de manera declarativa
    """
    
    def __init__(self):
        self.steps: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    def agregar_paso(self, 
                     paso: Callable, 
                     nombre: str = None,
                     skip_on_error: bool = False) -> 'DataPipeline':
        """Agrega paso al pipeline"""
        def wrapped_step(datos):
            step_name = nombre or paso.__name__
            try:
                self.logger.info(f"Ejecutando: {step_name}")
                resultado = paso(datos)
                self.logger.info(f"Completado: {step_name}")
                return resultado
            except Exception as e:
                if skip_on_error:
                    self.logger.warning(
                        f"Error en {step_name} (skip_on_error=True): {e}"
                    )
                    return datos
                else:
                    self.logger.error(f"Error en {step_name}: {e}")
                    raise
        
        self.steps.append(wrapped_step)
        return self  # Para encadenamiento
    
    def ejecutar(self, datos_iniciales: Any) -> Any:
        """Ejecuta todos los pasos del pipeline"""
        return reduce(lambda datos, paso: paso(datos), self.steps, datos_iniciales)

# Uso
pipeline = DataPipeline()
pipeline \
    .agregar_paso(extraer_datos, "Extracción") \
    .agregar_paso(validar_esquema, "Validación") \
    .agregar_paso(limpiar_nulls, "Limpieza") \
    .agregar_paso(transformar_fechas, "Transformación fechas") \
    .agregar_paso(enriquecer_datos, "Enriquecimiento", skip_on_error=True) \
    .agregar_paso(cargar_destino, "Carga")

resultado = pipeline.ejecutar(datos_iniciales)
```

### Batch vs Streaming

#### Batch Processing

```python
class BatchProcessor:
    """
    Procesamiento por lotes: procesa datos históricos en ventanas
    Ventajas: Simple, más fácil de debuggear, puede reprocesar
    Desventajas: Latencia (minutos/horas)
    """
    
    def __init__(self, window_size: timedelta):
        self.window_size = window_size
    
    def procesar_ventana(self, fecha_inicio: datetime, fecha_fin: datetime):
        """Procesa ventana de tiempo específica"""
        # 1. Extraer datos de la ventana
        query = f"""
            SELECT * FROM transacciones 
            WHERE timestamp >= '{fecha_inicio}' 
            AND timestamp < '{fecha_fin}'
        """
        datos = ejecutar_query(query)
        
        # 2. Procesar
        procesados = self.transformar(datos)
        
        # 3. Guardar con partición de tiempo
        fecha_particion = fecha_inicio.strftime('%Y-%m-%d')
        ruta = f"s3://bucket/datos/fecha={fecha_particion}/datos.parquet"
        procesados.to_parquet(ruta)
        
        return len(procesados)
    
    def procesar_backfill(self, fecha_inicio: datetime, fecha_fin: datetime):
        """Reprocesa rango histórico completo"""
        fecha_actual = fecha_inicio
        while fecha_actual < fecha_fin:
            fecha_siguiente = fecha_actual + self.window_size
            self.procesar_ventana(fecha_actual, fecha_siguiente)
            fecha_actual = fecha_siguiente
```

#### Micro-batch / Mini-batch

```python
class MicroBatchProcessor:
    """
    Procesamiento en micro-lotes: balance entre batch y streaming
    Procesa pequeños lotes frecuentemente (segundos/minutos)
    """
    
    def __init__(self, batch_size: int = 1000, flush_interval: int = 60):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.last_flush = time.time()
    
    def procesar_evento(self, evento: Dict):
        """Agrega evento al buffer y procesa si es necesario"""
        self.buffer.append(evento)
        
        # Flush por tamaño o tiempo
        if (len(self.buffer) >= self.batch_size or 
            time.time() - self.last_flush >= self.flush_interval):
            self.flush()
    
    def flush(self):
        """Procesa y limpia buffer"""
        if not self.buffer:
            return
        
        df = pd.DataFrame(self.buffer)
        df_procesado = self.transformar(df)
        self.guardar(df_procesado)
        
        self.buffer = []
        self.last_flush = time.time()
```

---

## Design Patterns for Data Engineering

### Factory Pattern

```python
from abc import ABC, abstractmethod

class DataExtractor(ABC):
    """Interfaz para extractores de datos"""
    
    @abstractmethod
    def extraer(self, config: Dict) -> pd.DataFrame:
        pass

class CSVExtractor(DataExtractor):
    def extraer(self, config: Dict) -> pd.DataFrame:
        return pd.read_csv(config['path'])

class APIExtractor(DataExtractor):
    def extraer(self, config: Dict) -> pd.DataFrame:
        response = requests.get(config['url'])
        return pd.DataFrame(response.json())

class DatabaseExtractor(DataExtractor):
    def extraer(self, config: Dict) -> pd.DataFrame:
        engine = create_engine(config['connection_string'])
        return pd.read_sql(config['query'], engine)

class ExtractorFactory:
    """Factory para crear extractores según tipo"""
    
    _extractors = {
        'csv': CSVExtractor,
        'api': APIExtractor,
        'database': DatabaseExtractor
    }
    
    @classmethod
    def crear_extractor(cls, tipo: str) -> DataExtractor:
        extractor_class = cls._extractors.get(tipo)
        if not extractor_class:
            raise ValueError(f"Tipo de extractor desconocido: {tipo}")
        return extractor_class()

# Uso
config = {
    'type': 'csv',
    'path': '/data/ventas.csv'
}

extractor = ExtractorFactory.crear_extractor(config['type'])
datos = extractor.extraer(config)
```

### Strategy Pattern

```python
class TransformationStrategy(ABC):
    """Interfaz para estrategias de transformación"""
    
    @abstractmethod
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

class CleaningStrategy(TransformationStrategy):
    """Estrategia de limpieza"""
    
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()
        df = df.drop_duplicates()
        return df

class NormalizationStrategy(TransformationStrategy):
    """Estrategia de normalización"""
    
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            df[col] = (df[col] - df[col].mean()) / df[col].std()
        return df

class AggregationStrategy(TransformationStrategy):
    """Estrategia de agregación"""
    
    def __init__(self, group_by: List[str], agg_config: Dict):
        self.group_by = group_by
        self.agg_config = agg_config
    
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby(self.group_by).agg(self.agg_config).reset_index()

class DataTransformer:
    """Contexto que usa estrategias de transformación"""
    
    def __init__(self, strategy: TransformationStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: TransformationStrategy):
        self.strategy = strategy
    
    def ejecutar(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.strategy.transformar(df)

# Uso
transformer = DataTransformer(CleaningStrategy())
df_limpio = transformer.ejecutar(df)

transformer.set_strategy(NormalizationStrategy())
df_normalizado = transformer.ejecutar(df_limpio)
```

### Builder Pattern

```python
class DataPipelineBuilder:
    """Builder para construir pipelines complejos paso a paso"""
    
    def __init__(self):
        self._pipeline = {
            'nombre': None,
            'extractor': None,
            'transformaciones': [],
            'validaciones': [],
            'loader': None,
            'error_handler': None,
            'config': {}
        }
    
    def con_nombre(self, nombre: str) -> 'DataPipelineBuilder':
        self._pipeline['nombre'] = nombre
        return self
    
    def con_extractor(self, extractor: DataExtractor) -> 'DataPipelineBuilder':
        self._pipeline['extractor'] = extractor
        return self
    
    def agregar_transformacion(self, transformacion: Callable) -> 'DataPipelineBuilder':
        self._pipeline['transformaciones'].append(transformacion)
        return self
    
    def agregar_validacion(self, validacion: Callable) -> 'DataPipelineBuilder':
        self._pipeline['validaciones'].append(validacion)
        return self
    
    def con_loader(self, loader: DataLoader) -> 'DataPipelineBuilder':
        self._pipeline['loader'] = loader
        return self
    
    def con_error_handler(self, handler: Callable) -> 'DataPipelineBuilder':
        self._pipeline['error_handler'] = handler
        return self
    
    def con_config(self, config: Dict) -> 'DataPipelineBuilder':
        self._pipeline['config'].update(config)
        return self
    
    def construir(self) -> 'Pipeline':
        # Validar que componentes requeridos están presentes
        if not self._pipeline['extractor']:
            raise ValueError("Pipeline requiere un extractor")
        if not self._pipeline['loader']:
            raise ValueError("Pipeline requiere un loader")
        
        return Pipeline(**self._pipeline)

# Uso
pipeline = (
    DataPipelineBuilder()
    .con_nombre("Pipeline Ventas")
    .con_extractor(CSVExtractor())
    .agregar_validacion(validar_esquema)
    .agregar_transformacion(limpiar_nulls)
    .agregar_transformacion(calcular_metricas)
    .agregar_validacion(validar_rangos)
    .con_loader(ParquetLoader())
    .con_error_handler(notificar_error)
    .con_config({'max_retries': 3, 'timeout': 300})
    .construir()
)

resultado = pipeline.ejecutar()
```

### Repository Pattern

```python
class DataRepository(ABC):
    """Abstracción para acceso a datos - separa lógica de negocio de persistencia"""
    
    @abstractmethod
    def obtener_por_id(self, id: int) -> Dict:
        pass
    
    @abstractmethod
    def obtener_todos(self, filtros: Dict = None) -> List[Dict]:
        pass
    
    @abstractmethod
    def guardar(self, datos: Dict) -> int:
        pass
    
    @abstractmethod
    def actualizar(self, id: int, datos: Dict) -> bool:
        pass
    
    @abstractmethod
    def eliminar(self, id: int) -> bool:
        pass

class PostgresRepository(DataRepository):
    """Implementación con PostgreSQL"""
    
    def __init__(self, connection_string: str, tabla: str):
        self.engine = create_engine(connection_string)
        self.tabla = tabla
    
    def obtener_por_id(self, id: int) -> Dict:
        query = f"SELECT * FROM {self.tabla} WHERE id = {id}"
        df = pd.read_sql(query, self.engine)
        return df.to_dict('records')[0] if not df.empty else None
    
    def obtener_todos(self, filtros: Dict = None) -> List[Dict]:
        query = f"SELECT * FROM {self.tabla}"
        if filtros:
            conditions = [f"{k} = '{v}'" for k, v in filtros.items()]
            query += " WHERE " + " AND ".join(conditions)
        df = pd.read_sql(query, self.engine)
        return df.to_dict('records')
    
    def guardar(self, datos: Dict) -> int:
        df = pd.DataFrame([datos])
        df.to_sql(self.tabla, self.engine, if_exists='append', index=False)
        # Retornar ID del nuevo registro
        return self._obtener_ultimo_id()
    
    # ... otros métodos

class S3Repository(DataRepository):
    """Implementación con S3 (diferentes operaciones)"""
    
    def __init__(self, bucket: str, prefix: str):
        self.s3 = boto3.client('s3')
        self.bucket = bucket
        self.prefix = prefix
    
    def obtener_por_id(self, id: int) -> Dict:
        key = f"{self.prefix}/{id}.json"
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return json.loads(obj['Body'].read())
    
    # ... otros métodos adaptados a S3

# Uso - Lógica de negocio desacoplada de implementación
class VentasService:
    def __init__(self, repository: DataRepository):
        self.repo = repository
    
    def procesar_venta(self, venta: Dict):
        # Validar
        if not self._validar_venta(venta):
            raise ValueError("Venta inválida")
        
        # Guardar
        venta_id = self.repo.guardar(venta)
        
        # Lógica adicional
        self._actualizar_inventario(venta)
        
        return venta_id

# Fácil cambiar implementación sin tocar lógica de negocio
ventas_service = VentasService(PostgresRepository(conn_str, 'ventas'))
# O cambiar a S3
ventas_service = VentasService(S3Repository('bucket', 'ventas'))
```

---

## Arquitectura de Proyectos Python

### Estructura Recomendada

```
mi_data_pipeline/
├── README.md                   # Documentación del proyecto
├── requirements.txt            # Dependencias (pip)
├── pyproject.toml             # Configuración del proyecto (Poetry)
├── setup.py                   # Instalación del paquete
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Archivos a ignorar en git
│
├── config/                    # Configuraciones
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
│
├── src/                       # Código fuente
│   └── mi_pipeline/
│       ├── __init__.py
│       ├── main.py            # Entry point
│       │
│       ├── extractors/        # Extractores
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── csv_extractor.py
│       │   └── api_extractor.py
│       │
│       ├── transformers/      # Transformadores
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── cleaning.py
│       │
│       ├── loaders/           # Loaders
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── parquet_loader.py
│       │
│       ├── validators/        # Validadores
│       │   ├── __init__.py
│       │   └── schema_validator.py
│       │
│       ├── models/            # Modelos de datos
│       │   ├── __init__.py
│       │   └── schemas.py
│       │
│       └── utils/             # Utilidades
│           ├── __init__.py
│           ├── logging.py
│           ├── config.py
│           └── helpers.py
│
├── tests/                     # Tests
│   ├── __init__.py
│   ├── conftest.py            # Fixtures de pytest
│   ├── unit/                  # Tests unitarios
│   │   ├── test_extractors.py
│   │   └── test_transformers.py
│   ├── integration/           # Tests de integración
│   │   └── test_pipeline.py
│   └── fixtures/              # Datos de prueba
│       └── sample_data.csv
│
├── scripts/                   # Scripts de utilidad
│   ├── setup.sh
│   ├── run_pipeline.sh
│   └── deploy.sh
│
├── notebooks/                 # Jupyter notebooks (exploración)
│   └── exploracion_datos.ipynb
│
├── docs/                      # Documentación adicional
│   ├── architecture.md
│   └── api.md
│
└── logs/                      # Logs (git-ignored)
    └── .gitkeep
```

### Configuration with YAML files

```python
# src/mi_pipeline/utils/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Gestor de configuración con soporte para múltiples ambientes"""
    
    def __init__(self, env: str = 'dev'):
        self.env = env
        self._config = self._cargar_config()
    
    def _cargar_config(self) -> Dict[str, Any]:
        """Carga configuración del ambiente especificado"""
        config_path = Path(__file__).parent.parent.parent / 'config' / f'{self.env}.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config no encontrada: {config_path}")
        
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración con soporte para nested keys"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    @property
    def database(self) -> Dict:
        return self._config.get('database', {})
    
    @property
    def s3(self) -> Dict:
        return self._config.get('s3', {})

# config/dev.yaml
"""
database:
  host: localhost
  port: 5432
  name: datos_dev
  user: dev_user
  
s3:
  bucket: datos-dev
  region: us-east-1
  
pipeline:
  batch_size: 1000
  max_retries: 3
  timeout: 300
"""

# Uso
config = Config(env='dev')
db_host = config.get('database.host')
batch_size = config.get('pipeline.batch_size', 500)
```

---

## Virtual Environments and Dependency Management

### venv (Built-in)

```bash
# Crear
python -m venv venv

# Activar
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Generar requirements.txt
pip freeze > requirements.txt

# Desactivar
deactivate
```

### Poetry (Recomendado)

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Inicializar proyecto
poetry init

# Agregar dependencias
poetry add pandas numpy
poetry add --group dev pytest black

# Instalar
poetry install

# Ejecutar en ambiente
poetry run python script.py
poetry run pytest

# Actualizar dependencias
poetry update

# Generar requirements.txt (si es necesario)
poetry export -f requirements.txt --output requirements.txt
```

**pyproject.toml**:
```toml
[tool.poetry]
name = "mi-data-pipeline"
version = "0.1.0"
description = "Pipeline de datos con Python"
authors = ["Tu Nombre <tu@email.com>"]

[tool.poetry.dependencies]
python = "^3.11"
pandas = "^2.2.0"
numpy = "^1.26.0"
sqlalchemy = "^2.0.0"
pydantic = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
black = "^24.1.0"
flake8 = "^7.0.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Docker para ambientes reproducibles

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY config/ ./config/

# Entry point
CMD ["python", "src/mi_pipeline/main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  pipeline:
    build: .
    environment:
      - ENV=dev
      - DATABASE_URL=postgresql://user:pass@db:5432/datos
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: datos
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## Testing Strategy

### Testing Pyramid

```
        /\
       /  \  E2E Tests (5%)
      /────\
     /      \ Integration Tests (15%)
    /────────\
   /          \ Unit Tests (80%)
  /────────────\
```

### Unit Tests

```python
# tests/unit/test_transformers.py
import pytest
import pandas as pd
from src.mi_pipeline.transformers.cleaning import CleaningTransformer

class TestCleaningTransformer:
    """Tests para limpieza de datos"""
    
    @pytest.fixture
    def transformer(self):
        return CleaningTransformer()
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'id': [1, 2, 2, 3, None],
            'valor': [10, 20, 20, 30, 40],
            'categoria': ['A', 'B', 'B', 'C', 'D']
        })
    
    def test_eliminar_nulls(self, transformer, sample_df):
        """Debe eliminar filas con nulls"""
        resultado = transformer.eliminar_nulls(sample_df)
        assert len(resultado) == 4
        assert resultado['id'].isna().sum() == 0
    
    def test_eliminar_duplicados(self, transformer, sample_df):
        """Debe eliminar filas duplicadas"""
        resultado = transformer.eliminar_duplicados(sample_df)
        assert len(resultado) == 4  # Una fila duplicada removida
    
    def test_pipeline_completo(self, transformer, sample_df):
        """Pipeline completo debe remover nulls y duplicados"""
        resultado = transformer.limpiar(sample_df)
        assert len(resultado) == 3
        assert resultado['id'].isna().sum() == 0
    
    @pytest.mark.parametrize("entrada,esperado", [
        (pd.DataFrame({'a': [1, 2, 3]}), 3),
        (pd.DataFrame({'a': []}), 0),
        (pd.DataFrame({'a': [1, None, 3]}), 2),
    ])
    def test_multiples_casos(self, transformer, entrada, esperado):
        """Test parametrizado con múltiples casos"""
        resultado = transformer.eliminar_nulls(entrada)
        assert len(resultado) == esperado
```

### Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
from src.mi_pipeline.main import Pipeline
from src.mi_pipeline.extractors.csv_extractor import CSVExtractor
from src.mi_pipeline.loaders.parquet_loader import ParquetLoader

class TestPipelineIntegration:
    """Tests de integración del pipeline completo"""
    
    @pytest.fixture
    def pipeline(self, tmp_path):
        """Pipeline configurado con archivos temporales"""
        return Pipeline(
            extractor=CSVExtractor(),
            loader=ParquetLoader(tmp_path)
        )
    
    def test_pipeline_end_to_end(self, pipeline, tmp_path):
        """Test de extremo a extremo del pipeline"""
        # Crear CSV de entrada
        input_file = tmp_path / "input.csv"
        input_file.write_text("id,valor\n1,100\n2,200")
        
        # Ejecutar pipeline
        resultado = pipeline.ejecutar({
            'input': str(input_file),
            'output': str(tmp_path / "output.parquet")
        })
        
        # Verificar
        assert resultado['registros_procesados'] == 2
        assert (tmp_path / "output.parquet").exists()
```

### Mocking

```python
from unittest.mock import Mock, patch, MagicMock

def test_extractor_con_api_mock():
    """Test de extractor con API mockeada"""
    # Mock de requests
    with patch('requests.get') as mock_get:
        # Configurar respuesta mock
        mock_response = Mock()
        mock_response.json.return_value = {'datos': [1, 2, 3]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Ejecutar
        extractor = APIExtractor()
        resultado = extractor.extraer({'url': 'http://api.example.com'})
        
        # Verificar
        assert len(resultado) == 3
        mock_get.assert_called_once_with('http://api.example.com')
```

---

## CI/CD para Data Pipelines

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run linting
      run: |
        pip install flake8
        flake8 src/ --max-line-length=100
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t mi-pipeline:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
        docker tag mi-pipeline:${{ github.sha }} usuario/mi-pipeline:latest
        docker push usuario/mi-pipeline:latest
```

---

## Observabilidad y Monitoring

### Logging Estructurado

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar contexto adicional si existe
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        # Agregar exception si existe
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Configuración
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Uso con contexto
logger.info(
    "Pipeline ejecutado",
    extra={
        'pipeline_id': 'ventas_daily',
        'registros_procesados': 15000,
        'duracion_segundos': 120,
        'ambiente': 'production'
    }
)
```

### Metrics with decorators

```python
import time
from functools import wraps

def medir_tiempo(func):
    """Decorator para medir tiempo de ejecución"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        try:
            resultado = func(*args, **kwargs)
            duracion = time.time() - inicio
            logger.info(
                f"{func.__name__} completado",
                extra={
                    'funcion': func.__name__,
                    'duracion': duracion,
                    'exito': True
                }
            )
            return resultado
        except Exception as e:
            duracion = time.time() - inicio
            logger.error(
                f"{func.__name__} falló",
                extra={
                    'funcion': func.__name__,
                    'duracion': duracion,
                    'exito': False,
                    'error': str(e)
                }
            )
            raise
    return wrapper

@medir_tiempo
def procesar_datos(df):
    # procesamiento
    return df
```

---

## scalability y Performance

### Procesamiento Paralelo

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Thread Pool (I/O bound)
def descargar_archivos_paralelo(urls: List[str]) -> List[bytes]:
    """Descarga múltiples archivos en paralelo"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        resultados = list(executor.map(descargar_archivo, urls))
    return resultados

# Process Pool (CPU bound)
def procesar_archivos_paralelo(archivos: List[str]) -> List[pd.DataFrame]:
    """Procesa archivos en paralelo usando múltiples procesos"""
    num_workers = mp.cpu_count() - 1
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        resultados = list(executor.map(procesar_archivo, archivos))
    return resultados
```

### Chunking para grandes datasets

```python
def procesar_csv_grande(archivo: str, chunk_size: int = 10000):
    """Procesa CSV grande en chunks para evitar OOM"""
    resultados = []
    
    for chunk in pd.read_csv(archivo, chunksize=chunk_size):
        # Procesar chunk
        chunk_procesado = transformar(chunk)
        resultados.append(chunk_procesado)
    
    # Combinar resultados
    return pd.concat(resultados, ignore_index=True)
```

---

## Security y Secrets Management

### Variables de Entorno

```python
import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Acceder a secrets
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
API_KEY = os.getenv('API_KEY')

# Con valores por defecto
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

### AWS Secrets Manager

```python
import boto3
import json

def obtener_secret(secret_name: str, region: str = 'us-east-1') -> Dict:
    """Obtiene secret de AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Error obteniendo secret {secret_name}: {e}")
        raise

# Uso
db_credentials = obtener_secret('prod/database/credentials')
connection_string = f"postgresql://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}"
```

---

## Resumen

This document covered:

1. **Arquitecturas**: ETL vs ELT, batch vs streaming, pipeline patterns
2. **Patrones**: Factory, Strategy, Builder, Repository
3. **Project Structure**: Modular and maintainable organization
4. **Ambientes**: venv, Poetry, Docker
5. **Testing**: Unit, integration, mocking
6. **CI/CD**: GitHub Actions, automation
7. **Observability**: Structured logging, metrics
8. **Performance**: Parallelization, chunking
9. **Security**: Secrets management

Estos patrones y arquitecturas son fundamentales para construir pipelines de datos robustos y scalables.

---

**Next Step**: Read [resources.md](./resources.md) for additional learning resources.
