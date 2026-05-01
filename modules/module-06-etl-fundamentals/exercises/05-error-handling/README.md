# Exercise 05: Error Handling

## 🎯 Objective
Implement robust error handling, retry logic, and failure recovery in ETL pipelines.

## 📚 Concepts Covered
- Try/except patterns
- Retry with exponential backoff
- Dead letter queues
- Graceful degradation
- Circuit breakers

## 🏋️ Tasks

### Task 1: Basic Error Handling
Handle common ETL errors:
- File not found
- Parse errors
- Type conversion errors
- Constraint violations

### Task 2: Retry Logic
Implement smart retries:
- Exponential backoff
- Max retries configuration
- Retry-specific exceptions

### Task 3: Failure Recovery
Handle partial failures:
- Dead letter queue for bad records
- Continue processing good records
- Save failure metadata

## 📝 Files
- `error_handler.py` - Error handling solution
- `retry_decorator.py` - Retry decorator implementation
- `test_errors.py` - Tests

## ✅ Success Criteria
- Graceful error handling
- Retry logic works correctly
- Bad records saved to DLQ
- All tests pass

## 🚀 How to Run

```bash
python error_handler.py
pytest test_errors.py -v
```
