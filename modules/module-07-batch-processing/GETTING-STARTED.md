# Module 07: Batch Processing - Getting Started Guide

Welcome to Module 07! This guide will help you get started with batch processing.

## 🎯 Module Goals

After completing this module, you will:
- ✅ Understand batch processing fundamentals
- ✅ Implement efficient data partitioning strategies
- ✅ Use PySpark for distributed processing
- ✅ Build production-ready batch pipelines
- ✅ Optimize performance for large datasets (10M+ records)
- ✅ Deploy and monitor production batch jobs

## 📚 Learning Path

### Step 1: Setup (30 minutes)
```bash
cd modules/module-07-batch-processing
bash scripts/setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies (pandas, PySpark, pytest, etc.)
- Generate sample data (10M transactions, 1M users, 100K products)
- Run validation tests

### Step 2: Theory (3-4 hours)
Read in this order:

1. **theory/01-concepts.md** (7,500 words, ~2 hours)
   - What is batch processing?
   - Batch vs stream processing
   - Partitioning strategies (date, range, hash)
   - Chunking and memory management
   - File formats (CSV, JSON, Parquet)

2. **theory/02-architecture.md** (6,000 words, ~1.5 hours)
   - Apache Spark architecture
   - Lambda vs Kappa patterns
   - Batch pipeline best practices
   - Performance optimization techniques
   - Monitoring and alerting

3. **theory/03-resources.md** (3,500 words, ~30 minutes)
   - Tools comparison (Spark, pandas, Dask, dbt)
   - Cloud services (AWS, GCP, Azure)
   - Learning resources
   - Community best practices

### Step 3: Exercises (8-10 hours)

#### Exercise 01: Batch Basics (1.5-2 hours)
**Focus**: Chunking, memory optimization, progress tracking

```bash
cd exercises/01-batch-basics
# Read README.md
# Implement starter/batch_reader.py
# Implement starter/memory_optimizer.py
# Compare with solutions
pytest test_batch_basics.py -v
```

**Key Learnings**:
- Read large files in chunks to avoid memory issues
- Optimize DataFrame memory (int64→int32, object→category)
- Track progress with tqdm

#### Exercise 02: Data Partitioning (1.5-2 hours)
**Focus**: Date, range, hash partitioning strategies

```bash
cd exercises/02-partitioning
# Read README.md
# Implement date_partitioner.py
# Implement range_partitioner.py
# Implement hash_partitioner.py
# Benchmark performance
```

**Key Learnings**:
- Partition by date for time-series data
- Partition by range for numeric data
- Partition by hash for even distribution
- Benchmark partitioned vs non-partitioned reads

#### Exercise 03: PySpark Basics (2-3 hours)
**Focus**: Distributed processing with Apache Spark

```bash
cd exercises/03-pyspark-basics
# Read README.md
# Implement spark_setup.py
# Implement spark_operations.py
# Implement spark_optimization.py
```

**Key Learnings**:
- Create and configure SparkSession
- Read/write Parquet with Spark
- Filter, aggregate, join with Spark DataFrames
- Use window functions
- Cache DataFrames for reuse

#### Exercise 04: Batch ETL pipeline (2-3 hours)
**Focus**: Complete batch pipeline with error handling

```bash
cd exercises/04-batch-pipeline
# Read README.md
# Implement etl_pipeline.py
# Implement transformations.py
# Implement error_handler.py
# Implement pipeline_metrics.py
```

**Key Learnings**:
- Extract from multiple sources
- Transform with business logic
- Load to partitioned output
- Handle errors gracefully
- Track pipeline metrics

#### Exercise 05: Performance Optimization (1.5-2 hours)
**Focus**: Caching, broadcast joins, partition tuning

```bash
cd exercises/05-optimization
# Read README.md
# Implement partition_optimizer.py
# Implement cache_manager.py
# Implement broadcast_optimizer.py
# Benchmark optimizations
```

**Key Learnings**:
- Cache frequently reused DataFrames
- Broadcast small tables for joins
- Tune partition sizes (128MB-1GB)
- Handle data skew

#### Exercise 06: Production Jobs (1.5-2 hours)
**Focus**: Production deployment, monitoring, SLA management

```bash
cd exercises/06-production-jobs
# Read README.md
# Implement production_job.py
# Implement retry_handler.py
# Implement job_monitor.py
# Implement quality_checks.py
```

**Key Learnings**:
- Implement retry logic with exponential backoff
- Monitor job metrics (duration, throughput)
- Check data quality
- Alert on failures or SLA violations

### Step 4: Validation (30 minutes)

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest validation/ -v

# Run specific test categories
pytest validation/ -v -m "not slow"  # Skip slow tests
pytest validation/ -v -m spark        # Only Spark tests
pytest validation/ -v -m performance  # Only performance tests

# Run validation script
bash scripts/validate.sh
```

## 🔧 Troubleshooting

### Issue: PySpark not starting
**Solution**: Check Java installation
```bash
java -version  # Should be Java 8 or 11
```

### Issue: Memory errors with 10M records
**Solution**: Process in chunks or increase memory
```python
# Process in chunks
for chunk in pd.read_csv("large_file.csv", chunksize=100000):
    process(chunk)

# Or increase Spark memory
spark = SparkSession.builder \
    .config("spark.driver.memory", "8g") \
    .getOrCreate()
```

### Issue: Tests failing
**Solution**: Ensure data is generated
```bash
# Re-run data generation
python data/scripts/generate_users.py --num-users 10000
python data/scripts/generate_products.py --num-products 1000
python data/scripts/generate_transactions.py --num-transactions 100000
```

### Issue: Slow data generation
**Solution**: Generate smaller datasets for testing
```bash
# Generate smaller datasets (faster)
python data/scripts/generate_users.py --num-users 10000
python data/scripts/generate_products.py --num-products 1000
python data/scripts/generate_transactions.py --num-transactions 100000
```

## 📖 Reference Materials

### Quick References
- **assets/pyspark-quick-reference.md**: Complete PySpark cheat sheet
- **assets/batch-processing-checklist.md**: Production checklist (100+ items)

### Code Examples
- **exercises/01-batch-basics/solution/**: Complete implementations
- **validation/test_module.py**: Working test examples

### Documentation
- [Apache Spark Docs](https://spark.apache.org/docs/latest/)
- [pandas Docs](https://pandas.pydata.org/docs/)
- [Parquet Docs](https://parquet.apache.org/docs/)

## 💡 Tips for Success

### 1. Start Small, Scale Up
- Test with 1,000 records first
- Then 10,000 records
- Finally full 10M records

### 2. Use the Right Tool
- **pandas**: < 1GB, single machine
- **PySpark**: > 1GB, needs distribution
- **Dask**: Middle ground (pandas API, distributed)

### 3. Parquet is Your Friend
- 5-10x smaller than CSV
- Columnar = faster queries
- Built-in compression (snappy)
- Schema included

### 4. Partition Wisely
- Date partitioning: `year=2024/month=03/day=15/`
- Avoid over-partitioning (< 1MB per partition)
- Query only needed partitions

### 5. Monitor Everything
- Track duration, throughput, errors
- Set up alerts for failures
- Log critical information
- Use Spark UI for debugging

### 6. Test Thoroughly
- Unit tests for transformations
- Integration tests for pipelines
- Performance tests with realistic data
- Test error scenarios

### 7. Optimize Iteratively
1. Make it work (correctness)
2. Make it right (code quality)
3. Make it fast (performance)

## 🎯 Success Criteria

You've completed this module when:
- ✅ All theory files read and understood
- ✅ All 6 exercises completed
- ✅ All validation tests passing (35+ tests)
- ✅ Can explain batch vs stream processing
- ✅ Can choose appropriate partitioning strategy
- ✅ Can write and optimize PySpark code
- ✅ Can build production-ready batch pipelines

## 🚀 Next Module

After completing Module 07, proceed to:
- **Module 08: Streaming Basics** - Learn real-time data processing
- **Module 10: Workflow Orchestration** - Schedule batch jobs with Airflow

---

**Estimated Total Time**: 12-15 hours

**Questions?** Check theory files or review solution code in exercises/01-batch-basics/solution/

**Ready to start?** Run `bash scripts/setup.sh` and begin with theory/01-concepts.md!
