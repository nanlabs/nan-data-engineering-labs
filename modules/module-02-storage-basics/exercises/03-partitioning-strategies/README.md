# Exercise 03: Partitioning Strategies

⏱️ **Estimated Time:** 60 minutes

## Objective
Implement and compare Hive-style partitioning strategies (date-based, geography-based, hybrid) to optimize query performance.

## Scenario
1M transactions across 365 days and 50 countries. Compare:
- No partitioning
- Date partitioning (year/month/day)
- Geography partitioning (country/state)
- Hybrid partitioning (date + country)

## Requirements
Implement partitioning and measure:
- Data scanned per query
- Query execution time
- Number of files read
- Cost (Athena charges per GB scanned)

## Success Criteria
- ✅ Date partitioning reduces scan by 99%+ for single-day queries
- ✅ Hybrid partitioning further optimizes multi-dimensional queries
- ✅ File count per partition: 1-10 (avoid small files)
- ✅ Athena queries use partition pruning

**Next:** [Exercise 04 - Compression Optimization](../04-compression-optimization/)
