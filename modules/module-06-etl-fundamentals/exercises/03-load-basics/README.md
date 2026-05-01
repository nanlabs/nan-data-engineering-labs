# Exercise 03: Load Basics

## 🎯 Objective
Learn to load transformed data to various destinations: CSV, JSON, Parquet, and databases.

## 📚 Concepts Covered
- Writing to different file formats
- Database loading (INSERT, UPSERT)
- Batch loading strategies
- Error handling during load

## 🏋️ Tasks

### Task 1: Load to CSV/JSON
Write data to file formats:
- CSV with proper encoding
- JSON with different orient options
- Parquet for efficient storage

### Task 2: Load to Database
Insert data into SQLite database:
- Create tables
- Batch inserts
- Handle constraints

### Task 3: UPSERT Logic
Implement update-or-insert:
- Check for existing records
- Update if exists, insert if not
- Handle conflicts

## 📝 Files
- `solution_file_writers.py` - File format solutions
- `solution_db_loader.py` - Database loading solution
- `test_load.py` - Unit tests

## ✅ Success Criteria
- Data written correctly to all formats
- Database constraints respected
- UPSERT works correctly
- All tests pass

## 🚀 How to Run

```bash
python solution_file_writers.py
python solution_db_loader.py
pytest test_load.py -v
```
