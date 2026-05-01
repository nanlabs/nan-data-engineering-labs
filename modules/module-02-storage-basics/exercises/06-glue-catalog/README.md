# Exercise 06: AWS Glue Catalog Integration

⏱️ **Estimated Time:** 75 minutes

## Objective
Register datasets in AWS Glue Data Catalog, create crawlers for auto-discovery, and query with Athena.

## Scenario
GlobalMart's Silver layer has 5 datasets (transactions, users, products, events, logs). Register in Glue Catalog for:
- Schema discovery
- Partition management
- Athena queries
- Data lineage

## Requirements
1. Create Glue database `globalmart`
2. Define tables manually (transactions, users)
3. Create crawler for auto-discovery (products, events)
4. Query with Athena
5. Update partitions with `MSCK REPAIR TABLE`

## Success Criteria
- ✅ Glue database created
- ✅ 5 tables registered
- ✅ Crawler runs successfully
- ✅ Partitions auto-discovered
- ✅ Athena queries work
- ✅ Schema changes detected by crawler

**Congratulations!** You've completed Module 02! 🎉
