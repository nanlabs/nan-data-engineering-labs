"""
Tests de Calidad de Datos

Valida que los datasets tienen las características esperadas,
incluyendo los problemas de calidad intencionales.
"""

import pytest
import pandas as pd
import json
from pathlib import Path


class TestDatasetExistence:
    """Verifica que todos los datasets existen."""
    
    def test_all_csv_files_exist(self, data_dir):
        """Verifica que todos los CSVs existen."""
        expected_csvs = ["customers.csv", "products.csv", "transactions.csv"]
        
        for filename in expected_csvs:
            file_path = data_dir / filename
            assert file_path.exists(), f"{filename} debe existir"
            assert file_path.stat().st_size > 0, f"{filename} no debe estar vacío"
    
    def test_all_json_files_exist(self, data_dir):
        """Verifica que todos los JSONs existen."""
        expected_jsons = ["orders.json", "user_activity.json"]
        
        for filename in expected_jsons:
            file_path = data_dir / filename
            assert file_path.exists(), f"{filename} debe existir"
            assert file_path.stat().st_size > 0, f"{filename} no debe estar vacío"
    
    def test_schemas_exist(self):
        """Verifica que todos los schemas JSON existen."""
        schema_dir = Path(__file__).parent.parent / "data" / "schemas"
        
        expected_schemas = [
            "customers_schema.json",
            "orders_schema.json",
            "products_schema.json",
            "transactions_schema.json",
            "user_activity_schema.json"
        ]
        
        for filename in expected_schemas:
            schema_path = schema_dir / filename
            assert schema_path.exists(), f"Schema {filename} debe existir"
            
            # Validar que es JSON válido
            with open(schema_path) as f:
                schema = json.load(f)
                assert isinstance(schema, dict), "Schema debe ser un diccionario"


class TestDatasetSize:
    """Verifica el tamaño correcto de los datasets."""
    
    @pytest.mark.data
    def test_customers_size(self, customers_df):
        """Customers debe tener 10,000 registros."""
        assert len(customers_df) == 10000, "Customers debe tener exactamente 10K registros"
    
    @pytest.mark.data
    def test_transactions_size(self, transactions_df):
        """Transactions debe tener 100,000 registros."""
        assert len(transactions_df) == 100000, "Transactions debe tener 100K registros"
    
    @pytest.mark.data
    def test_products_size(self, products_df):
        """Products debe tener 500 registros."""
        assert len(products_df) == 500, "Products debe tener 500 registros"
    
    @pytest.mark.data
    def test_orders_size(self, orders_json):
        """Orders debe tener 50,000 registros."""
        assert len(orders_json) == 50000, "Orders debe tener 50K registros"
    
    @pytest.mark.data
    def test_user_activity_size(self, user_activity_json):
        """User activity debe tener 20,000 registros."""
        assert len(user_activity_json) == 20000, "User activity debe tener 20K registros"
    
    @pytest.mark.data
    def test_total_records(self, customers_df, transactions_df, products_df, 
                          orders_json, user_activity_json):
        """Total debe ser 180,000 registros."""
        total = (len(customers_df) + len(transactions_df) + len(products_df) + 
                len(orders_json) + len(user_activity_json))
        
        assert total == 180000, f"Total debe ser 180K registros, obtenido: {total}"


class TestDataQualityIssues:
    """Verifica que los problemas de calidad intencionales están presentes."""
    
    @pytest.mark.data
    def test_customers_has_nulls(self, customers_df):
        """Customers debe tener valores nulos (5-10%)."""
        null_count = customers_df.isnull().sum().sum()
        total_cells = customers_df.shape[0] * customers_df.shape[1]
        null_percentage = (null_count / total_cells) * 100
        
        assert null_percentage > 0, "Debe haber valores nulos"
        assert 2 <= null_percentage <= 15, f"Nulls deben estar entre 2-15%, obtenido: {null_percentage:.2f}%"
    
    @pytest.mark.data
    def test_customers_has_duplicates(self, customers_df):
        """Customers debe tener duplicados (~2%)."""
        dup_count = customers_df.duplicated().sum()
        dup_percentage = (dup_count / len(customers_df)) * 100
        
        assert dup_count > 0, "Debe haber duplicados"
        assert 0.5 <= dup_percentage <= 5, f"Duplicados deben estar entre 0.5-5%, obtenido: {dup_percentage:.2f}%"
    
    @pytest.mark.data
    def test_transactions_has_nulls(self, transactions_df):
        """Transactions debe tener valores nulos."""
        null_count = transactions_df.isnull().sum().sum()
        assert null_count > 0, "Debe haber valores nulos en transactions"
    
    @pytest.mark.data
    def test_transactions_has_duplicates(self, transactions_df):
        """Transactions debe tener duplicados."""
        dup_count = transactions_df.duplicated().sum()
        assert dup_count > 0, "Debe haber duplicados en transactions"
    
    @pytest.mark.data
    def test_orphan_foreign_keys(self, transactions_df, customers_df):
        """Debe haber transactions con customer_ids que no existen (~5%)."""
        valid_customers = set(customers_df['customer_id'].unique())
        transaction_customers = set(transactions_df['customer_id'].dropna().unique())
        
        orphans = transaction_customers - valid_customers
        orphan_percentage = (len(orphans) / len(transaction_customers)) * 100
        
        # Puede haber algunos orphans debido a la generación aleatoria
        # No es un error, es intencional para práctica de data quality
        if orphan_percentage > 0:
            assert orphan_percentage < 20, f"Orphans no deben exceder 20%, obtenido: {orphan_percentage:.2f}%"


class TestDataSchema:
    """Valida el schema de los datasets."""
    
    @pytest.mark.data
    def test_customers_columns(self, customers_df):
        """Verifica columnas de customers."""
        expected_columns = [
            'customer_id', 'first_name', 'last_name', 'email', 
            'country', 'city', 'signup_date'
        ]
        
        for col in expected_columns:
            assert col in customers_df.columns, f"Columna {col} debe existir en customers"
    
    @pytest.mark.data
    def test_transactions_columns(self, transactions_df):
        """Verifica columnas de transactions."""
        expected_columns = [
            'transaction_id', 'customer_id', 'amount', 
            'transaction_date', 'status'
        ]
        
        for col in expected_columns:
            assert col in transactions_df.columns, f"Columna {col} debe existir en transactions"
    
    @pytest.mark.data
    def test_products_columns(self, products_df):
        """Verifica columnas de products."""
        expected_columns = [
            'product_id', 'product_name', 'category', 'price'
        ]
        
        for col in expected_columns:
            assert col in products_df.columns, f"Columna {col} debe existir en products"
    
    @pytest.mark.data
    def test_orders_structure(self, orders_json):
        """Verifica estructura de orders (puede ser anidada)."""
        assert len(orders_json.columns) > 0, "Orders debe tener columnas"
        assert 'order_id' in orders_json.columns, "Orders debe tener order_id"


class TestDataTypes:
    """Valida tipos de datos."""
    
    @pytest.mark.data
    def test_customers_id_type(self, customers_df):
        """customer_id debe ser numérico."""
        assert pd.api.types.is_numeric_dtype(customers_df['customer_id']), \
            "customer_id debe ser numérico"
    
    @pytest.mark.data
    def test_transactions_amount_type(self, transactions_df):
        """amount debe ser numérico."""
        assert pd.api.types.is_numeric_dtype(transactions_df['amount']), \
            "amount debe ser numérico"
    
    @pytest.mark.data
    def test_products_price_type(self, products_df):
        """price debe ser numérico."""
        assert pd.api.types.is_numeric_dtype(products_df['price']), \
            "price debe ser numérico"


class TestDataRelationships:
    """Valida relaciones entre datasets."""
    
    @pytest.mark.data
    def test_customer_transactions_relationship(self, customers_df, transactions_df):
        """Verifica que la mayoría de transactions tienen un customer válido."""
        valid_customers = set(customers_df['customer_id'].unique())
        transaction_customers = transactions_df['customer_id'].dropna()
        
        valid_relationships = transaction_customers.isin(valid_customers).sum()
        total_transactions = len(transaction_customers)
        
        valid_percentage = (valid_relationships / total_transactions) * 100
        
        # Al menos 80% de las transacciones deben tener un customer válido
        assert valid_percentage >= 80, \
            f"Al menos 80% de transactions deben tener customer válido, obtenido: {valid_percentage:.2f}%"
    
    @pytest.mark.data
    def test_products_have_valid_prices(self, products_df):
        """Productos deben tener precios válidos (positivos)."""
        if 'price' in products_df.columns:
            valid_prices = products_df['price'].dropna()
            positive_prices = (valid_prices > 0).sum()
            
            percentage = (positive_prices / len(valid_prices)) * 100
            
            assert percentage >= 95, \
                f"Al menos 95% de precios deben ser positivos, obtenido: {percentage:.2f}%"


class TestDataStatistics:
    """Valida estadísticas básicas de los datos."""
    
    @pytest.mark.data
    def test_transactions_amount_range(self, transactions_df):
        """Amounts deben estar en un rango razonable."""
        amounts = transactions_df['amount'].dropna()
        
        assert amounts.min() >= 0, "Amount mínimo debe ser >= 0"
        assert amounts.max() <= 100000, "Amount máximo debe ser razonable"
        assert amounts.mean() > 0, "Amount promedio debe ser positivo"
    
    @pytest.mark.data
    def test_products_price_range(self, products_df):
        """Precios deben estar en un rango razonable."""
        if 'price' in products_df.columns:
            prices = products_df['price'].dropna()
            
            assert prices.min() >= 0, "Precio mínimo debe ser >= 0"
            assert prices.max() <= 100000, "Precio máximo debe ser razonable"
    
    @pytest.mark.data
    def test_customers_distribution(self, customers_df):
        """Customers deben estar distribuidos en múltiples países."""
        if 'country' in customers_df.columns:
            countries = customers_df['country'].dropna().nunique()
            assert countries >= 3, f"Debe haber al menos 3 países, obtenido: {countries}"


# =============================================================================
# Test Final de Calidad
# =============================================================================

@pytest.mark.data
def test_overall_data_quality_report(customers_df, transactions_df, products_df):
    """
    Genera un reporte completo de calidad de datos.
    """
    report = {
        'customers': {
            'total_rows': len(customers_df),
            'null_percentage': (customers_df.isnull().sum().sum() / 
                              (customers_df.shape[0] * customers_df.shape[1]) * 100),
            'duplicate_percentage': (customers_df.duplicated().sum() / len(customers_df) * 100),
            'columns': len(customers_df.columns)
        },
        'transactions': {
            'total_rows': len(transactions_df),
            'null_percentage': (transactions_df.isnull().sum().sum() / 
                              (transactions_df.shape[0] * transactions_df.shape[1]) * 100),
            'duplicate_percentage': (transactions_df.duplicated().sum() / len(transactions_df) * 100),
            'columns': len(transactions_df.columns)
        },
        'products': {
            'total_rows': len(products_df),
            'null_percentage': (products_df.isnull().sum().sum() / 
                              (products_df.shape[0] * products_df.shape[1]) * 100),
            'duplicate_percentage': (products_df.duplicated().sum() / len(products_df) * 100),
            'columns': len(products_df.columns)
        }
    }
    
    # Validar que el reporte tiene datos
    assert all(ds['total_rows'] > 0 for ds in report.values()), \
        "Todos los datasets deben tener registros"
    
    # Imprimir reporte para referencia
    print("\n" + "="*70)
    print("REPORTE DE CALIDAD DE DATOS")
    print("="*70)
    for dataset, stats in report.items():
        print(f"\n{dataset.upper()}:")
        print(f"  Registros: {stats['total_rows']:,}")
        print(f"  Columnas: {stats['columns']}")
        print(f"  Nulls: {stats['null_percentage']:.2f}%")
        print(f"  Duplicados: {stats['duplicate_percentage']:.2f}%")
    print("="*70 + "\n")
    
    return report
