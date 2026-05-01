# Exercise 02: File Format Conversion & Benchmarking

⏱️ **Estimated Time:** 60 minutes

## Objective
Convert data between CSV, JSON, Parquet, and Avro formats while benchmarking performance, compression ratios, and query speed.

## Scenario
GlobalMart has 100,000 transaction records in CSV (500MB). Convert to JSON, Parquet, and Avro, comparing:
- File size (compression ratio)
- Write time
- Read time (full scan)
- Read time (filtered query)
- Memory usage

## Requirements
Create a Python script that:
1. Reads CSV transactions
2. Converts to JSON, Parquet (Snappy), Parquet (Gzip), Avro
3. Benchmarks each format
4. Generates comparison report

## Structure
```
02-file-formats/
├── README.md
├── starter/
│   └── format_converter.py  # Template with TODOs
├── hints.md
└── solution/
    ├── format_converter.py  # Complete with benchmarking
    └── benchmark_results.md # Sample output
```

## Success Criteria
- ✅ CSV → JSON, Parquet, Avro conversion working
- ✅ Benchmark metrics collected
- ✅ Parquet shows 60-80% compression vs CSV
- ✅ Parquet read 5-10x faster than CSV
- ✅ Report generated with recommendations

## Key Learnings
- Parquet excels for analytics (columnr, compression, predicate pushdown)
- Avro better for streaming (row-based, schema evolution)
- CSV/JSON for interchange only
- Compression trades CPU for storage

**Next:** [Exercise 03 - Partitioning Strategies](../03-partitioning-strategies/)
