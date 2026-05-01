# Exercise 05: Schema Evolution

⏱️ **Estimated Time:** 60 minutes

## Objective
Implement schema evolution in Parquet: add columns, change types, handle backward/forward compatibility.

## Scenario
V1: `{id, amount, timestamp}`
V2: Add `customer_email` (optional)
V3: Add `loyalty_points` (with default)
V4: Change `amount` from float to decimal

## Requirements
1. Write data with V1 schema
2. Add columns (V2, V3) - test backward compatibility
3. Attempt type change (V4) - handle safely
4. Read mixed-version files

## Success Criteria
- ✅ Old readers can read new data (backward compatible)
- ✅ New readers can read old data (forward compatible)
- ✅ Added columns have defaults/nulls
- ✅ Type changes handled with new column approach

**Next:** [Exercise 06 - Glue Catalog Integration](../06-glue-catalog/)
