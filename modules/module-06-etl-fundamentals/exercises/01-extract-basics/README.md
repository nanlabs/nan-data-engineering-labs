# Exercise 01: Extract Basics

## 🎯 Objective
Learn to extract data from multiple sources: CSV, JSON, APIs, and databases.

## 📚 Concepts Covered
- Reading CSV files with pandas
- Parsing JSON data
- Making API requests
- Connecting to databases
- Error handling during extraction

## 🏋️ Tasks

### Task 1: Extract from CSV
Extract user data from CSV file and handle encoding issues.

**Expected output**: DataFrame with 10,000 users

### Task 2: Extract from JSON
Parse JSON Lines format and handle nested structures.

**Expected output**: DataFrame with transactions

### Task 3: Extract from API
Make HTTP requests to external API and handle rate limiting.

**Expected output**: DataFrame with API data

### Task 4: Extract from Database
Connect to SQLite database and extract data with SQL queries.

**Expected output**: DataFrame from database query

## 📝 Files
- `starter_csv.py` - CSV extraction starter
- `starter_json.py` - JSON extraction starter
- `starter_api.py` - API extraction starter
- `starter_db.py` - Database extraction starter
- `solution_csv.py` - CSV extraction solution
- `solution_json.py` - JSON extraction solution
- `solution_api.py` - API extraction solution
- `solution_db.py` - Database extraction solution
- `test_extract.py` - Unit tests
- `hints.md` - Helpful hints

## ✅ Success Criteria
- All extractors return valid DataFrames
- Handle missing files gracefully
- Validate extracted data
- Pass all unit tests

## 🚀 How to Run

```bash
# Run each extractor
python starter_csv.py
python starter_json.py
python starter_api.py
python starter_db.py

# Run tests
pytest test_extract.py -v
```

## 💡 Tips
- Use `try/except` for error handling
- Validate data after extraction
- Check for nulls and data types
- Use `pd.read_csv()` parameters for CSV issues
