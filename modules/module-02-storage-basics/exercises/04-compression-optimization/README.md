# Exercise 04: Compression Optimization

⏱️ **Estimated Time:** 45 minutes

## Objective
Compare compression algorithms (Snappy, Gzip, LZ4, Zstd) for Parquet files, understanding trade-offs between compression ratio and speed.

## Scenario
100GB dataset - which compression to use?
- Bronze layer (write-once, read-rarely)
- Silver layer (frequent analytics)
- Gold layer (BI dashboards, SLA < 5sec)

## Requirements
Benchmark each algorithm:
- Compression ratio (%)
- Compression time
- Decompression time
- CPU usage
- Query performance

## Success Criteria
- ✅ Snappy: Best balance (recommended default)
- ✅ Gzip: Highest compression (archival)
- ✅ LZ4: Fastest (streaming)
- ✅ Zstd: Modern general-purpose
- ✅ Recommendations per layer

**Next:** [Exercise 05 - Schema Evolution](../05-schema-evolution/)
