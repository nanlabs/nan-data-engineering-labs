"""
Tests de Integración del Módulo 04

Valida que todos los ejercicios funcionan juntos en un flujo end-to-end.
"""

import pytest
import pandas as pd
from pathlib import Path


class TestPipelineIntegration:
    """Tests de integración simulando un pipeline real."""
    
    @pytest.mark.integration
    @pytest.mark.data
    def test_etl_pipeline_completo(self, customers_df, transactions_df, tmp_path):
        """
        Pipeline completo: Extract → Transform → Load
        
        Simula un flujo real de trabajo:
        1. Leer datos de customers y transactions
        2. Limpiar datos (remover nulls, duplicados)
        3. Hacer join entre datasets
        4. Calcular métricas agregadas
        5. Guardar resultado
        """
        # 1. EXTRACT
        assert len(customers_df) == 10000, "Customers debe tener 10K registros"
        assert len(transactions_df) == 100000, "Transactions debe tener 100K registros"
        
        # 2. TRANSFORM - Limpieza de customers
        customers_clean = customers_df.dropna(subset=['customer_id'])
        customers_clean = customers_clean.drop_duplicates(subset=['customer_id'])
        
        # 3. TRANSFORM - Limpieza de transactions
        transactions_clean = transactions_df.dropna(subset=['transaction_id', 'customer_id'])
        transactions_clean = transactions_clean.drop_duplicates(subset=['transaction_id'])
        
        # 4. JOIN - Combinar datasets
        merged = pd.merge(
            transactions_clean,
            customers_clean[['customer_id', 'first_name', 'last_name', 'country']],
            on='customer_id',
            how='inner'
        )
        
        assert len(merged) > 0, "El join debe producir resultados"
        assert 'first_name' in merged.columns, "Debe incluir columnas de customers"
        
        # 5. AGGREGATE - Calcular métricas por cliente
        metrics = merged.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_id': 'count'
        }).reset_index()
        
        assert len(metrics) > 0, "Debe haber métricas calculadas"
        
        # 6. LOAD - Guardar resultado
        output_path = tmp_path / "customer_metrics.csv"
        metrics.to_csv(output_path, index=False)
        
        assert output_path.exists(), "Archivo de salida debe existir"
        
        # 7. VALIDATE - Verificar archivo guardado
        loaded = pd.read_csv(output_path)
        assert len(loaded) == len(metrics), "Datos guardados deben coincidir"
    
    
    @pytest.mark.integration
    def test_flujo_file_operations_a_pandas(self, data_dir, tmp_path):
        """
        Integración entre ejercicios 03 (File Operations) y 04 (Pandas).
        
        Flujo:
        1. Leer CSV (ejercicio 03)
        2. Procesar con Pandas (ejercicio 04)
        3. Guardar resultado (ejercicio 03)
        """
        # Leer CSV
        df = pd.read_csv(data_dir / "products.csv")
        
        # Procesar con Pandas
        df_clean = df.dropna()
        df_clean = df_clean.drop_duplicates()
        
        # Agregar columna calculada
        if 'price' in df_clean.columns:
            df_clean['price_with_tax'] = df_clean['price'] * 1.21
        
        # Guardar resultado
        output_path = tmp_path / "products_processed.csv"
        df_clean.to_csv(output_path, index=False)
        
        # Validar
        assert output_path.exists()
        df_loaded = pd.read_csv(output_path)
        assert len(df_loaded) > 0


class TestDataStructuresIntegration:
    """Tests de integración entre estructuras de datos y pandas."""
    
    @pytest.mark.integration
    def test_dict_to_dataframe_to_analysis(self, transactions_df):
        """
        Flujo: Dict → DataFrame → Análisis
        
        Simula procesamiento de datos estructurados.
        """
        # 1. Convertir DataFrame a dict (estructura de datos)
        data_dict = transactions_df.head(100).to_dict('records')
        
        assert isinstance(data_dict, list), "Debe ser lista de dicts"
        assert len(data_dict) == 100, "Debe tener 100 registros"
        
        # 2. Manipular con estructuras de datos básicas
        # Filtrar por país usando comprehension
        if 'country' in data_dict[0]:
            usa_transactions = [t for t in data_dict if t.get('country') == 'USA']
            assert isinstance(usa_transactions, list)
        
        # 3. Convertir de vuelta a DataFrame
        df_from_dict = pd.DataFrame(data_dict)
        
        assert len(df_from_dict) == 100
        
        # 4. Hacer análisis con Pandas
        if 'amount' in df_from_dict.columns:
            stats = {
                'mean': df_from_dict['amount'].mean(),
                'median': df_from_dict['amount'].median(),
                'total': df_from_dict['amount'].sum()
            }
            
            assert all(isinstance(v, (int, float)) for v in stats.values())
    
    
    @pytest.mark.integration
    def test_aggregation_pipeline(self, customers_df):
        """
        Pipeline de agregación complejo.
        
        Usa: comprehensions → pandas → dict operations
        """
        # 1. Filtrar datos con comprehension-style
        df = customers_df[customers_df['country'].isin(['USA', 'UK', 'Canada'])]
        
        # 2. Agrupar con Pandas
        by_country = df.groupby('country').size().to_dict()
        
        assert isinstance(by_country, dict)
        assert all(isinstance(v, (int, float)) for v in by_country.values())
        
        # 3. Transformar resultados con dict comprehension
        percentages = {
            country: (count / sum(by_country.values()) * 100)
            for country, count in by_country.items()
        }
        
        assert abs(sum(percentages.values()) - 100.0) < 0.01, "Porcentajes deben sumar 100%"


class TestTransformationIntegration:
    """Tests de transformaciones complejas entre ejercicios."""
    
    @pytest.mark.integration
    @pytest.mark.data
    @pytest.mark.slow
    def test_nested_json_to_flat_csv(self, orders_json, tmp_path):
        """
        Transformación completa: JSON anidado → CSV plano
        
        Integra ejercicios 03, 04 y 05.
        """
        # 1. Verificar estructura anidada
        if len(orders_json) > 0:
            sample = orders_json.iloc[0]
            
            # Algunos orders tienen items anidados
            if 'items' in orders_json.columns:
                # 2. Flatten usando json_normalize
                df_flat = pd.json_normalize(
                    orders_json.head(1000).to_dict('records'),
                    sep='_'
                )
                
                assert len(df_flat) > 0, "Debe generar registros"
                
                # 3. Limpiar datos
                df_clean = df_flat.dropna(thresh=len(df_flat.columns) // 2)
                
                # 4. Guardar como CSV
                output_path = tmp_path / "orders_flat.csv"
                df_clean.to_csv(output_path, index=False)
                
                assert output_path.exists()
                
                # 5. Validar lectura
                df_loaded = pd.read_csv(output_path)
                assert len(df_loaded) > 0
    
    
    @pytest.mark.integration
    def test_multi_dataset_join(self, customers_df, transactions_df, products_df):
        """
        Join de múltiples datasets simulando un data warehouse.
        """
        # 1. Join transactions con customers
        df1 = pd.merge(
            transactions_df.head(1000),
            customers_df[['customer_id', 'country']],
            on='customer_id',
            how='left'
        )
        
        # 2. Si hay product_id, join con products
        if 'product_id' in df1.columns and 'product_id' in products_df.columns:
            df2 = pd.merge(
                df1,
                products_df[['product_id', 'product_name', 'category']],
                on='product_id',
                how='left'
            )
            
            assert len(df2) > 0
            
            # 3. Calcular métricas por categoría y país
            if 'category' in df2.columns and 'amount' in df2.columns:
                summary = df2.groupby(['country', 'category'])['amount'].agg([
                    'sum', 'mean', 'count'
                ]).reset_index()
                
                assert len(summary) > 0


class TestErrorHandlingIntegration:
    """Tests de manejo de errores en contexto integrado."""
    
    @pytest.mark.integration
    def test_robust_pipeline_with_errors(self, tmp_path):
        """
        Pipeline robusto que maneja errores correctamente.
        
        Integra ejercicio 06 con todos los anteriores.
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        results = {
            'success': [],
            'errors': []
        }
        
        # Procesar múltiples archivos, algunos pueden fallar
        test_files = [
            "customers.csv",
            "no_existe.csv",  # Este fallará
            "transactions.csv"
        ]
        
        for filename in test_files:
            try:
                # Intentar leer archivo
                file_path = Path("data/raw") / filename
                
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    results['success'].append({
                        'file': filename,
                        'rows': len(df)
                    })
                else:
                    raise FileNotFoundError(f"Archivo no encontrado: {filename}")
                    
            except Exception as e:
                logger.error(f"Error procesando {filename}: {e}")
                results['errors'].append({
                    'file': filename,
                    'error': str(e)
                })
        
        # Validar que capturamos ambos: éxitos y errores
        assert len(results['success']) > 0, "Debe haber archivos procesados exitosamente"
        assert len(results['errors']) > 0, "Debe haber archivos con error"
        assert results['errors'][0]['file'] == "no_existe.csv"


# =============================================================================
# TEST FINAL: Pipeline End-to-End Completo
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.data
def test_full_data_engineering_pipeline(data_dir, tmp_path):
    """
    Test final: Pipeline completo de ingeniería de datos.
    
    Este test integra TODOS los ejercicios del módulo en un flujo realista:
    
    1. Python Basics: Validaciones y funciones auxiliares
    2. Data Structures: Manipulación de estructuras
    3. File Operations: I/O en múltiples formatos
    4. Pandas: Análisis y transformación
    5. Transformation: ETL completo
    6. Error Handling: Robustez y logging
    """
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 1. EXTRACT - Leer múltiples fuentes
        logger.info("Fase 1: Extract")
        customers = pd.read_csv(data_dir / "customers.csv")
        transactions = pd.read_csv(data_dir / "transactions.csv")
        
        assert len(customers) > 0
        assert len(transactions) > 0
        
        # 2. VALIDATE - Usar funciones básicas de Python
        logger.info("Fase 2: Validate")
        
        # Validar que no hay customer_ids inválidos
        assert customers['customer_id'].notna().all()
        
        # 3. TRANSFORM - Limpieza con Pandas
        logger.info("Fase 3: Transform")
        
        customers_clean = customers.dropna(subset=['customer_id'])
        customers_clean = customers_clean.drop_duplicates(subset=['customer_id'])
        
        transactions_clean = transactions.dropna(subset=['transaction_id', 'customer_id'])
        transactions_clean = transactions_clean.drop_duplicates(subset=['transaction_id'])
        
        # 4. JOIN - Integración de datos
        logger.info("Fase 4: Join")
        
        fact_table = pd.merge(
            transactions_clean,
            customers_clean,
            on='customer_id',
            how='inner'
        )
        
        assert len(fact_table) > 0
        
        # 5. AGGREGATE - Métricas de negocio
        logger.info("Fase 5: Aggregate")
        
        customer_metrics = fact_table.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_id': 'count'
        }).reset_index()
        
        # 6. LOAD - Guardar resultados en múltiples formatos
        logger.info("Fase 6: Load")
        
        # CSV
        csv_path = tmp_path / "customer_metrics.csv"
        customer_metrics.to_csv(csv_path, index=False)
        
        # Parquet (más eficiente)
        parquet_path = tmp_path / "customer_metrics.parquet"
        customer_metrics.to_parquet(parquet_path, compression='snappy')
        
        # JSON
        json_path = tmp_path / "customer_metrics.json"
        customer_metrics.to_json(json_path, orient='records', indent=2)
        
        # 7. VALIDATE OUTPUT
        logger.info("Fase 7: Validate Output")
        
        assert csv_path.exists()
        assert parquet_path.exists()
        assert json_path.exists()
        
        # Verificar que los datos se guardaron correctamente
        df_csv = pd.read_csv(csv_path)
        df_parquet = pd.read_parquet(parquet_path)
        df_json = pd.read_json(json_path)
        
        assert len(df_csv) == len(customer_metrics)
        assert len(df_parquet) == len(customer_metrics)
        assert len(df_json) == len(customer_metrics)
        
        logger.info("✅ Pipeline completado exitosamente")
        
        # Retornar métricas del pipeline
        pipeline_stats = {
            'customers_procesados': len(customers_clean),
            'transactions_procesadas': len(transactions_clean),
            'registros_finales': len(customer_metrics),
            'archivos_generados': 3
        }
        
        return pipeline_stats
        
    except Exception as e:
        logger.error(f"❌ Pipeline falló: {e}", exc_info=True)
        raise
