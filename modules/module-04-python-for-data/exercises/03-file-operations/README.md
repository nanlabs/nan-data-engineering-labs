# Exercise 03: File Operations

## Learning Objectives

After completing this exercise, you will be able to:

1. ✅ Leer y escribir files **CSV** con pandas
2. ✅ Manipular files **JSON** (simple y anidado)
3. ✅ Trabajar con formato **Parquet** (columnr)
4. ✅ Usar **context managers** (`with` statement)
5. ✅ Manejar errores de I/O correctamente

---

## Conceptos Clave

### Context Managers (with statement)

```python
# ❌ Sin context manager (mal)
file = open("data.txt", "r")
contenido = file.read()
file.close()  # Facil de olvidar

# ✅ Con context manager (bien)
with open("data.txt", "r") as file:
    contenido = file.read()
# Se cierra automaticamente
```text

**Beneficios**:

- Automatically close the file
- Libera resources incluso si hay error
- Cleaner and safer code

### CSV con pandas

```python
import pandas as pd

# Leer CSV
df = pd.read_csv("data.csv")

# Leer con opciones
df = pd.read_csv(
    "data.csv",
    sep=",",           # Separador
    encoding="utf-8",  # Codificacion
    na_values=["N/A", "null"],  # Valores nulos
    parse_dates=["fecha"]  # Parsear fechas
)

# Escribir CSV
df.to_csv("salida.csv", index=False)
```text

### JSON

```python
import json

# Leer JSON
with open("data.json", "r") as f:
    data = json.load(f)

# Escribir JSON
with open("salida.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# JSON con pandas
df = pd.read_json("data.json")
df = pd.read_json("data.json", orient="records")  # Lista de objetos
```text

### Parquet

```python
import pandas as pd

# Leer Parquet
df = pd.read_parquet("data.parquet")

# Escribir Parquet
df.to_parquet("salida.parquet", compression="snappy")
```

**Advantages de Parquet**:

- columnr format (more efficient)
- Integrated compression
- Preserva tipos de data
- Faster than CSV for reading

### Manejo de Errores

```python
try:
    with open("file.txt", "r") as f:
        contenido = f.read()
except FileNotFoundError:
    print("File no encontrado")
except PermissionError:
    print("Sin permisos para leer")
except Exception as e:
    print(f"Error inesperado: {e}")
```text

---

## Exercises

Usa los datasets generados en `data/raw/`:

- `customers.csv` (10,000 registros)
- `orders.json` (50,000 registros, anidado)
- `products.csv` (500 registros)
- `transactions.csv` (100,000 registros)
- `user_activity.json` (20,000 registros, anidado)

### 1. leer_csv(ruta) ⭐

Lee un file CSV y retorna un DataFrame.

```python
df = leer_csv("data/raw/customers.csv")
assert len(df) == 10000
assert "customer_id" in df.columns
```text

### 2. escribir_csv(df, ruta) ⭐

Escribe un DataFrame a CSV.

```python
df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
escribir_csv(df, "output.csv")
assert os.path.exists("output.csv")
```text

### 3. leer_json(ruta) ⭐⭐

Lee un file JSON y retorna dict/list.

```python
data = leer_json("data/raw/orders.json")
assert isinstance(data, list)
assert len(data) == 50000
```

### 4. escribir_json(data, ruta) ⭐⭐

Escribe data a JSON con formato legible.

```python
data = {"nombre": "Ana", "edad": 25}
escribir_json(data, "output.json")
```text

### 5. csv_a_parquet(csv_path, parquet_path) ⭐⭐

Convierte CSV a Parquet.

```python
csv_a_parquet("data/raw/products.csv", "data/processed/products.parquet")
```text

### 6. contar_registros(ruta) ⭐⭐

Cuenta registros en file CSV/JSON.

```python
assert contar_registros("data/raw/customers.csv") == 10000
assert contar_registros("data/raw/orders.json") == 50000
```text

### 7. obtener_columns_csv(ruta) ⭐

Obtiene nombres de columns de un CSV.

```python
columnas = obtener_columnas_csv("data/raw/customers.csv")
assert "customer_id" in columnas
```

### 8. filtrar_csv(ruta_entrada, ruta_salida, condicion) ⭐⭐⭐

Filter CSV according to condition and save result.

```python
# Ejemplo: filtrar clientes de USA
filtrar_csv(
    "data/raw/customers.csv",
    "customers_usa.csv",
    lambda df: df[df["country"] == "USA"]
)
```text

### 9. combinar_csvs(rutas, ruta_salida) ⭐⭐

Combine multiple CSVs into one.

```python
combinar_csvs(
    ["parte1.csv", "parte2.csv"],
    "completo.csv"
)
```text

### 10. json_a_csv_plano(json_path, csv_path) ⭐⭐⭐

Convierte JSON anidado a CSV plano (flatten).

```python
# orders.json tiene estructura:
# {
#   "order_id": 1,
#   "items": [{"product": "A", "qty": 2}],
#   "customer": {"name": "Ana"}
# }
json_a_csv_plano("data/raw/orders.json", "orders_flat.csv")
```text

---

## Execution

```bash
# Run tests
pytest exercises/03-file-operations/tests/ -v

# Con coverage
pytest exercises/03-file-operations/tests/ --cov

# Test especifico
pytest exercises/03-file-operations/tests/test_file_io.py::test_leer_csv -v
```

---

## Tips

1. **Context managers**: Siempre usa `with` para files
2. **Encoding**: Especifica UTF-8 para evitar problemas
3. **Chunks**: Para files grandes, procesa por chunks
4. **Validation**: Verify that the file exists before reading
5. **Cleanup**: Borra files temporales en tests

---

## resources

- [Pandas I/O](https://pandas.pydata.org/docs/user_guide/io.html)
- [JSON Module](https://docs.python.org/3/library/json.html)
- [Parquet Format](https://parquet.apache.org/docs/overview/)

---

## Next Step

Una vez completed: ➡️ **Exercise 04: Pandas Fundamentals**
