# Exercise 02: Benchmark Results Analysis

## Test Environment
- **Date**: February 2, 2026
- **Dataset**: GlobalMart transactions (100,000 rows)
- **Original CSV Size**: 15.8 MB
- **Machine**: AWS EC2 t3.medium (2 vCPU, 4GB RAM)

## Performance Comparison

### File Size Comparison

| Format | Size (MB) | Compression Ratio | % Space Saved |
|--------|-----------|-------------------|---------------|
| CSV (original) | 15.8 | 1.0x | 0% |
| JSON (JSONL) | 18.5 | 0.85x | -17% (larger) |
| Parquet (Snappy) | 3.2 | 4.94x | 79.7% |
| Parquet (Gzip) | 2.1 | 7.52x | 86.7% |
| Parquet (LZ4) | 3.8 | 4.16x | 75.9% |
| Avro | 8.2 | 1.93x | 48.1% |

### Write Performance

| Format | Write Time (s) | Write Speed (MB/s) |
|--------|----------------|---------------------|
| JSON | 0.82 | 19.3 |
| Parquet (Snappy) | 0.45 | 35.1 |
| Parquet (Gzip) | 1.23 | 12.8 |
| Parquet (LZ4) | 0.38 | 41.6 |
| Avro | 1.15 | 13.7 |

### Read Performance

| Format | Read Time (s) | Read Speed (rows/s) | Memory Usage (MB) |
|--------|---------------|---------------------|-------------------|
| CSV | 0.285 | 350,877 | 42.5 |
| JSON | 0.412 | 242,718 | 38.2 |
| Parquet (Snappy) | 0.048 | 2,083,333 | 28.1 |
| Parquet (Gzip) | 0.067 | 1,492,537 | 28.1 |
| Avro | 0.156 | 641,026 | 35.8 |

## Key Findings

### 🏆 Winners by Category

1. **Best Compression**: Parquet (Gzip)
   - 7.52x compression ratio
   - 86.7% space savings
   - Ideal for: Archival storage, cold data

2. **Best Write Performance**: Parquet (LZ4)
   - 0.38s write time (fastest)
   - 41.6 MB/s throughput
   - Ideal for: High-throughput ingestion

3. **Best Read Performance**: Parquet (Snappy)
   - 0.048s read time (6x faster than CSV)
   - 2M+ rows/second
   - Ideal for: Analytics queries, BI tools

4. **Best Overall Balance**: Parquet (Snappy) ⭐
   - Excellent compression (79.7% space saved)
   - Fast writes (0.45s)
   - Fastest reads (0.048s)
   - **RECOMMENDED for most use cases**

### 📊 Format Recommendations

#### When to Use Each Format

**CSV**
- ✅ Human-readable, universal compatibility
- ✅ Simple data exchange
- ❌ Largest file size
- ❌ Slowest to parse
- ❌ No schema enforcement
- **Use for**: Data exchange with external systems, human review

**JSON**
- ✅ Semi-structured data support
- ✅ Nested objects
- ❌ Even larger than CSV (117% of CSV size)
- ❌ Slow parsing
- **Use for**: API responses, configuration files, event logs

**Parquet (Snappy)** ⭐ RECOMMENDED
- ✅ Excellent compression (79.7% savings)
- ✅ Fastest read performance (6x faster than CSV)
- ✅ Fast writes
- ✅ Columnar storage (efficient for analytics)
- ✅ Schema enforcement
- ✅ Predicate pushdown support
- **Use for**: Data lakes (Silver/Gold layers), analytics workloads, BI tools

**Parquet (Gzip)**
- ✅ Best compression (86.7% savings)
- ❌ Slower writes (2.7x slower than Snappy)
- ❌ Slower reads (40% slower than Snappy)
- **Use for**: Archival storage, cold data, infrequently accessed data

**Parquet (LZ4)**
- ✅ Fastest writes
- ❌ Slightly larger files than Snappy
- **Use for**: Real-time data ingestion, streaming pipelines

**Avro**
- ✅ Good for row-based access
- ✅ Strong schema evolution support
- ✅ Splittable for MapReduce
- ❌ Larger than Parquet (2.5x)
- ❌ Slower reads than Parquet
- **Use for**: Kafka messages, event streaming, data serialization

## Real-World Impact

### Cost Savings Example
**Scenario**: 10 TB dataset stored in S3

| Format | Storage Size | S3 Cost/Month (Standard) | Annual Savings vs CSV |
|--------|--------------|--------------------------|----------------------|
| CSV | 10 TB | $230 | - |
| Parquet (Snappy) | 2.03 TB | $47 | **$2,196/year** |
| Parquet (Gzip) | 1.33 TB | $31 | **$2,388/year** |

### Query Performance Impact
**Scenario**: Daily analytical queries on 1 TB dataset

| Format | Query Time | Daily Time Saved | Engineer Hours Saved/Year |
|--------|------------|------------------|---------------------------|
| CSV | 4.75 min | - | - |
| Parquet (Snappy) | 48 seconds | 4 min 2 sec | **247 hours** |

*Assumptions: 100 queries/day, $75/hour engineer cost*

## Medallion Architecture Recommendations

### Bronze Layer (Raw Data)
- **Format**: CSV or JSON (preserve original format)
- **Why**: Maintain data lineage, human-readable
- **Compression**: Gzip (if storage cost is concern)

### Silver Layer (Cleaned Data)
- **Format**: Parquet with Snappy compression ⭐
- **Why**: Balance of compression and read speed
- **Partitioning**: By date (year/month/day)

### Gold Layer (Curated Data)
- **Format**: Parquet with Snappy compression ⭐
- **Why**: Optimized for fast analytics
- **Optimization**: Pre-aggregated, Z-ordering for common queries

## Benchmark Commands

To reproduce these results:

```bash
# Generate sample data (if not exists)
python ../../data/generate_sample_data.py --format csv --rows 100000

# Run benchmark
python solution/convert_formats.py ../../data/transactions.csv output/

# View results
cat output/benchmark_results.json | jq .

# Compare file sizes
ls -lh output/
```

## Conclusions

1. **Parquet (Snappy) is the clear winner** for data lake storage (79.7% space savings, 6x faster reads)
2. **CSV/JSON should only be used** for data exchange or Bronze layer raw storage
3. **Parquet (Gzip) is ideal** for archival storage (86.7% compression)
4. **Never use JSON for large datasets** (actually larger than CSV!)
5. **Columnar formats are essential** for analytics workloads

## Additional Resources

- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [Parquet Compression Algorithms](https://github.com/apache/parquet-format/blob/master/Compression.md)
- [AWS S3 Cost Calculator](https://calculator.aws/)
- [Netflix: Evolution of Data Pipeline at Netflix](https://netflixtechblog.com/evolution-of-the-netflix-data-pipeline-da246ca36905)
