# Exercise 02: Transform Basics

## 🎯 Objective
Learn data transformation techniques: cleaning, type conversion, aggregations, and joins.

## 📚 Concepts Covered
- Data cleaning (nulls, duplicates, outliers)
- Type conversions
- String manipulations
- Aggregations and grouping
- Joining datasets

## 🏋️ Tasks

### Task 1: Data Cleaning
Clean dirty user data:
- Remove duplicates
- Handle missing values
- Fix invalid emails
- Standardize country codes

### Task 2: Type Conversions
Convert data types properly:
- Parse dates
- Convert numeric columns
- Handle categorical data
- Deal with mixed types

### Task 3: Aggregations
Calculate business metrics:
- User statistics by country
- Transaction totals by user
- Time-based aggregations

### Task 4: Joins
Combine multiple datasets:
- Join users and transactions
- Handle missing matches
- Aggregate after joining

## 📝 Files
- `starter_cleaning.py` - Data cleaning starter
- `starter_aggregations.py` - Aggregations starter
- `starter_joins.py` - Joins starter
- `solution_cleaning.py` - Cleaning solution
- `solution_aggregations.py` - Aggregations solution
- `solution_joins.py` - Joins solution
- `test_transform.py` - Unit tests
- `hints.md` - Helpful hints

## ✅ Success Criteria
- Clean data passes validation
- Aggregations match expected results
- Joins produce correct row counts
- All tests pass

## 🚀 How to Run

```bash
python starter_cleaning.py
python starter_aggregations.py
python starter_joins.py

pytest test_transform.py -v
```
