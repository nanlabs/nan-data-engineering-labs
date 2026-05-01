# Sample Data Files

This directory contains small sample data files for quick testing and demonstration.

## Files

### transactions_sample.csv
Small sample of transaction data (100 rows) for quick testing.

**Columns**:
- `transaction_id` (int): Unique transaction identifier
- `user_id` (int): User who made the transaction
- `product_id` (int): Product purchased
- `amount` (float): Transaction amount in USD
- `timestamp` (datetime): Transaction timestamp
- `country` (string): Country code
- `status` (string): Transaction status

**Usage**:
```bash
# Use for quick testing of Exercise 02
python exercises/02-file-formats/solution/convert_formats.py \
    data/sample/transactions_sample.csv \
    output/
```

### users_sample.parquet
Small sample of user data (50 rows) in Parquet format.

**⚠️ Note**: This file needs to be generated first:
```bash
cd data/sample
bash generate_users.sh
```

**Columns**:
- `user_id` (int64): Unique user identifier
- `first_name` (string): First name
- `last_name` (string): Last name
- `email` (string): User email
- `age` (int64): User age
- `country` (string): Country code
- `registration_date` (date32): Registration date
- `is_active` (bool): Account status

**Usage**:
```python
import pandas as pd
df = pd.read_parquet('data/sample/users_sample.parquet')
print(df.head())
```

### products_sample.json
Small sample of product catalog (25 products) in JSON format.

**Structure**:
```json
{
  "product_id": 1,
  "name": "Product Name",
  "category": "Electronics",
  "price": 99.99,
  "stock": 100,
  "rating": 4.5
}
```

**Usage**:
```python
import pandas as pd
df = pd.read_json('data/sample/products_sample.json', lines=True)
```

## Generating Sample Data

To regenerate or create sample data files:

```bash
# Generate users_sample.parquet (required first time)
cd data/sample
bash generate_users.sh

# Or generate all full datasets using the main generator
cd ../../  # back to module root
python data/generate_sample_data.py

# Create smaller custom samples
python data/generate_sample_data.py --transactions 100 --users 50 --products 25
```

**Note**: The `users_sample.parquet` file is not included in git and must be generated locally by running `generate_users.sh`.

## Use Cases

1. **Quick Testing**: Test exercises without generating full datasets
2. **CI/CD**: Use in automated tests (fast execution)
3. **Demonstrations**: Show data transformations quickly
4. **Learning**: Understand data structure before working with full datasets

## File Sizes

- `transactions_sample.csv`: ~5 KB
- `users_sample.parquet`: ~2 KB
- `products_sample.json`: ~1 KB

**Total**: ~8 KB (vs. ~20 MB for full datasets)
