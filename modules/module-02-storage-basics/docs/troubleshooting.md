# Troubleshooting Guide - Module 02

## Table of Contents
1. [LocalStack Issues](#localstack-issues)
2. [Python Dependencies](#python-dependencies)
3. [File Format Issues](#file-format-issues)
4. [CloudFormation Issues](#cloudformation-issues)
5. [Performance Issues](#performance-issues)

## LocalStack Issues

### Issue: LocalStack won't start

**Symptoms**:
```bash
ERROR: Cannot connect to the Docker daemon
```

**Solution**:
```bash
# 1. Check if Docker is running
sudo systemctl status docker

# 2. Start Docker
sudo systemctl start docker

# 3. Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# 4. Try again
cd infrastructure && ./init.sh
```

### Issue: Port 4566 already in use

**Symptoms**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:4566: bind: address already in use
```

**Solution**:
```bash
# 1. Find process using port 4566
lsof -i :4566

# 2. Kill the process
kill -9 <PID>

# 3. Or change LocalStack port in docker-compose.yml
ports:
  - "4567:4566"  # Use different port
```

### Issue: S3 bucket creation fails

**Symptoms**:
```
An error occurred (BucketAlreadyExists) when calling the CreateBucket operation
```

**Solution**:
```bash
# 1. List existing buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# 2. Delete existing bucket
aws --endpoint-url=http://localhost:4566 s3 rb s3://my-bucket --force

# 3. Recreate bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket
```

### Issue: LocalStack data not persisting

**Symptoms**:
- Buckets disappear after restart

**Solution**:
```bash
# 1. Check if volume is mounted
docker inspect localstack-module-02 | grep -A 5 Mounts

# 2. Ensure PERSISTENCE=1 in docker-compose.yml
environment:
  - PERSISTENCE=1
  - DATA_DIR=/tmp/localstack

# 3. Check permissions on localstack-data/
sudo chown -R $USER:$USER localstack-data/
```

## Python Dependencies

### Issue: pip install fails for PyArrow

**Symptoms**:
```
ERROR: Could not build wheels for pyarrow
```

**Solution**:
```bash
# Option 1: Install system dependencies (Linux)
sudo apt-get update
sudo apt-get install -y build-essential python3-dev

# Option 2: Use pre-built wheel
pip install --upgrade pip
pip install pyarrow --prefer-binary

# Option 3: Install specific version
pip install pyarrow==12.0.0
```

### Issue: fastavro import error

**Symptoms**:
```python
ModuleNotFoundError: No module named 'fastavro'
```

**Solution**:
```bash
# 1. Reinstall from requirements.txt
pip install -r requirements.txt

# 2. Or install individually
pip install fastavro>=1.7.0

# 3. Verify installation
python -c "import fastavro; print(fastavro.__version__)"
```

### Issue: pandas read_parquet fails

**Symptoms**:
```
ValueError: Unable to find a usable engine
```

**Solution**:
```bash
# Install PyArrow (required engine for Parquet)
pip install pyarrow>=12.0.0

# Or use fastparquet
pip install fastparquet
df = pd.read_parquet('file.parquet', engine='fastparquet')
```

## File Format Issues

### Issue: Parquet file is corrupted

**Symptoms**:
```
ArrowInvalid: Parquet file size is 0 bytes
OSError: Couldn't deserialize thrift
```

**Solution**:
```bash
# 1. Verify file is not empty
ls -lh file.parquet

# 2. Check file integrity
parquet-tools inspect file.parquet

# 3. Try reading with PyArrow directly
python -c "import pyarrow.parquet as pq; pq.read_table('file.parquet')"

# 4. If corrupted, regenerate from source
python convert_formats.py source.csv output/
```

### Issue: Schema mismatch when reading Parquet

**Symptoms**:
```
ArrowInvalid: Unable to merge: Field amount has incompatible types: double vs int32
```

**Solution**:
```python
# Option 1: Read without schema validation
df = pd.read_parquet('file.parquet', use_nullable_dtypes=True)

# Option 2: Cast columns explicitly
df = pd.read_parquet('file.parquet')
df['amount'] = df['amount'].astype('float64')

# Option 3: Read with PyArrow and convert schema
import pyarrow.parquet as pq
table = pq.read_table('file.parquet')
table = table.cast(new_schema)
df = table.to_pandas()
```

### Issue: JSON parsing fails

**Symptoms**:
```
JSONDecodeError: Extra data: line 2 column 1
```

**Solution**:
```python
# If JSONL (JSON Lines) format, use lines=True
df = pd.read_json('file.json', lines=True)

# For standard JSON array
df = pd.read_json('file.json', orient='records')

# For nested JSON, normalize it
df = pd.json_normalize(data)
```

### Issue: Avro schema validation error

**Symptoms**:
```
fastavro._write_common.SchemaResolutionError
```

**Solution**:
```python
# 1. Validate schema matches data
schema = {
    'type': 'record',
    'name': 'Transaction',
    'fields': [
        {'name': 'id', 'type': 'int'},
        {'name': 'amount', 'type': 'double'}  # Not 'float'
    ]
}

# 2. Handle null values
{'name': 'email', 'type': ['null', 'string'], 'default': null}

# 3. Convert DataFrame types before writing
df['id'] = df['id'].astype('int32')
df['amount'] = df['amount'].astype('float64')
```

## CloudFormation Issues

### Issue: Stack creation fails - BucketName already exists

**Symptoms**:
```
The requested bucket name is not available
```

**Solution**:
```bash
# Option 1: Use unique bucket names (add timestamp/random suffix)
aws cloudformation deploy --parameter-overrides \
  CompanyName=globalmart-${RANDOM}

# Option 2: Delete existing bucket
aws s3 rb s3://globalmart-bronze-dev --force

# Option 3: Let CloudFormation auto-generate names
# Remove BucketName property from template
```

### Issue: IAM role permissions denied

**Symptoms**:
```
User: arn:aws:iam::123456789:user/alice is not authorized to perform: iam:CreateRole
```

**Solution**:
```bash
# 1. For LocalStack: Use test credentials (no restrictions)
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

# 2. For real AWS: Add CAPABILITY_NAMED_IAM
aws cloudformation deploy \
  --capabilities CAPABILITY_NAMED_IAM

# 3. Check your IAM permissions
aws iam get-user
```

### Issue: CloudFormation template validation error

**Symptoms**:
```
Template format error: YAML not well-formed
```

**Solution**:
```bash
# 1. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('template.yaml'))"

# 2. Validate CloudFormation template
aws cloudformation validate-template --template-body file://template.yaml

# 3. Common issues:
#    - Indentation (use 2 spaces, not tabs)
#    - Missing quotes around !Ref or !Sub
#    - Invalid resource types
```

### Issue: Lifecycle policy not working

**Symptoms**:
- Objects not transitioning to different storage classes

**Solution**:
```yaml
# 1. Ensure Status: Enabled
LifecycleConfiguration:
  Rules:
    - Id: MoveToIA
      Status: Enabled  # NOT 'Active'

# 2. Check filter matches objects
      Filter:
        Prefix: data/  # Must match object keys

# 3. Wait - transitions happen daily (not immediately)

# 4. Test with short timeframes
      Transitions:
        - TransitionInDays: 1  # For testing
          StorageClass: STANDARD_IA
```

## Performance Issues

### Issue: Parquet writes are very slow

**Symptoms**:
- Taking minutes to write 100K rows

**Solution**:
```python
# 1. Use row_group_size parameter
df.to_parquet('file.parquet', row_group_size=100000)

# 2. Use faster compression
df.to_parquet('file.parquet', compression='lz4')  # Faster than Snappy

# 3. Write in batches for large DataFrames
for chunk in pd.read_csv('large.csv', chunksize=100000):
    chunk.to_parquet(f'file_part_{i}.parquet')

# 4. Use PyArrow directly (faster than pandas)
import pyarrow as pa
import pyarrow.parquet as pq
table = pa.Table.from_pandas(df)
pq.write_table(table, 'file.parquet', compression='snappy')
```

### Issue: Reading Parquet is slow

**Symptoms**:
- Queries taking seconds on small files

**Solution**:
```python
# 1. Read only needed columns
df = pd.read_parquet('file.parquet', columns=['amount', 'country'])

# 2. Use filters (predicate pushdown)
df = pd.read_parquet('file.parquet',
                      filters=[('country', '=', 'USA')])

# 3. Use PyArrow dataset API for partitioned data
import pyarrow.dataset as ds
dataset = ds.dataset('partitioned_data/', format='parquet')
table = dataset.to_table(filter=ds.field('year') == 2024)

# 4. Check row group size (should be ~128 MB)
pq.read_metadata('file.parquet').num_row_groups
```

### Issue: Out of memory when processing large files

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```python
# Option 1: Process in chunks
for chunk in pd.read_csv('large.csv', chunksize=10000):
    process(chunk)

# Option 2: Use Dask for larger-than-memory data
import dask.dataframe as dd
df = dd.read_csv('large.csv')
result = df.groupby('country')['amount'].sum().compute()

# Option 3: Use PyArrow's memory-mapped reading
import pyarrow.parquet as pq
table = pq.read_table('large.parquet', memory_map=True)

# Option 4: Filter data before loading
df = pd.read_parquet('large.parquet',
                      columns=['amount', 'country'],
                      filters=[('year', '=', 2024)])
```

### Issue: Partitioned data has many small files

**Symptoms**:
- Thousands of files per partition
- Slow query performance

**Solution**:
```python
# Problem: Over-partitioning
df.to_parquet('data/', partition_cols=['year', 'month', 'day', 'hour', 'country'])
# Result: Too many partitions!

# Solution 1: Reduce partition granularity
df.to_parquet('data/', partition_cols=['year', 'month', 'country'])
# Fewer, larger partitions

# Solution 2: Compact small files
import pyarrow.parquet as pq
import pyarrow.dataset as ds

dataset = ds.dataset('data/', format='parquet')
table = dataset.to_table()
pq.write_to_dataset(table, 'compacted_data/',
                     partition_cols=['year', 'month'],
                     max_rows_per_file=1000000)

# Rule of thumb: Keep partitions >100 MB
```

## Quick Reference Commands

### Docker & LocalStack
```bash
# Start LocalStack
docker-compose up -d

# Check logs
docker logs -f localstack-module-02

# Stop LocalStack
docker-compose down

# Reset everything
docker-compose down -v && rm -rf localstack-data/

# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls
```

### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import pandas, pyarrow, fastavro; print('OK')"
```

### File Format Tools
```bash
# View Parquet schema
parquet-tools schema file.parquet

# View Parquet data
parquet-tools head file.parquet

# Get file metadata
parquet-tools meta file.parquet

# View JSON structure
jq '.' file.json | head -20

# Count lines in JSONL
wc -l file.jsonl
```

### AWS CLI (LocalStack)
```bash
# Always use endpoint URL
export AWS_ENDPOINT=http://localhost:4566
alias awslocal='aws --endpoint-url=$AWS_ENDPOINT'

# S3 operations
awslocal s3 ls
awslocal s3 cp file.txt s3://my-bucket/
awslocal s3 sync data/ s3://my-bucket/data/

# Glue operations
awslocal glue get-databases
awslocal glue get-tables --database-name mydb
```

## Getting Help

If you're still stuck:

1. **Check logs**:
   ```bash
   docker logs localstack-module-02
   python script.py 2>&1 | tee error.log
   ```

2. **Search for error message**:
   - [Stack Overflow](https://stackoverflow.com/)
   - [GitHub Issues](https://github.com/apache/parquet-format/issues)
   - [AWS Forums](https://repost.aws/)

3. **Minimal reproducible example**:
   ```python
   import pandas as pd
   df = pd.DataFrame({'a': [1, 2, 3]})
   df.to_parquet('test.parquet')  # Where exactly does it fail?
   ```

4. **Contact instructor** with:
   - Error message (full stack trace)
   - Python version: `python --version`
   - Package versions: `pip list | grep -E "(pandas|pyarrow|fastavro)"`
   - Steps to reproduce

---

**Last Updated**: February 2, 2026
**Module**: 02 - Storage Basics
