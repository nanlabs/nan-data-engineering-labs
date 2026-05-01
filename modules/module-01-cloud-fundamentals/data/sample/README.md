# Sample Datasets

Synthetic datasets generated for Module 01 exercises.

## Files

### transactions-sample.csv
- **Format:** CSV
- **Size:** ~1.2 MB
- **Rows:** 10,000

### logs-sample.jsonl
- **Format:** JSON Lines
- **Size:** ~8.5 MB

### users-sample.csv
- **Format:** CSV
- **Size:** ~0.08 MB
- **Rows:** 1,000

### products-sample.json
- **Format:** JSON
- **Size:** ~0.05 MB

## Usage

These datasets are used in:

- S3 upload/download operations
- Data format conversion (CSV → Parquet)
- Partitioning strategies
- Compression analysis
- Schema evolution testing

## Regenerate

```bash
python3 generate_sample_data.py
```
