# Sample Data Files - Module 18: Advanced Architectures

This directory contains sample data files for testing exercises.

## Files

### event-store-sample.json
Sample events for CQRS/Event Sourcing (Exercise 04).

**Events**:
- `OrderPlaced`, `PaymentProcessed`, `OrderShipped`, `OrderDelivered`, `OrderCancelled`
- Immutable event log with timestamps
- Aggregate IDs for order tracking

**Usage**:
```bash
cd exercises/04-event-driven-cqrs
python event_store.py --mode setup --env localstack
python command_handler.py --command PlaceOrder --aggregate ORD_001 --data '{"customer_id":"CUST_123","items":[{"product_id":"PROD_456","quantity":2}],"amount":150.00}'
```

---

### kinesis-stream-events.json
Sample streaming events for Kappa Architecture (Exercise 02).

**Events**:
- Real-time user activity (page views, clicks, purchases)
- Includes user_id, event_type, timestamp, metadata
- ~100 events for quick testing

**Usage**:
```bash
cd exercises/02-kappa-architecture
python stream_processor.py --mode produce --events ../data/sample/kinesis-stream-events.json
```

---

### batch-data-sample.parquet
Historical data for Lambda Architecture batch layer (Exercise 01).

**Schema**:
- transaction_id, user_id, product_id, amount, timestamp, country

**Size**: 10,000 transactions (90 days of data)

**Usage**:
```bash
cd exercises/01-lambda-architecture
python batch_layer.py --mode batch-process --input ../data/sample/batch-data-sample.parquet
```

---

### domain-products-sample.json
Product catalog for Data Mesh (Exercise 03 - Product Domain).

**Schema**:
- product_id, name, category, price, stock, supplier_id
- 500 products

**Usage**:
```bash
cd exercises/03-data-mesh
python domain_api.py --mode serve --domain product --data ../data/sample/domain-products-sample.json
```

---

### domain-sales-sample.json
Sales orders for Data Mesh (Exercise 03 - Sales Domain).

**Schema**:
- order_id, customer_id, product_id, quantity, amount, order_date
- 1,000 orders

---

### domain-customer-sample.json
Customer profiles for Data Mesh (Exercise 03 - Customer Domain).

**Schema**:
- customer_id, name, email, country, lifetime_value, segment
- 200 customers

---

### generate_sample_data.py
Python script to generate all sample data files.

**Usage**:
```bash
python data/sample/generate_sample_data.py

# Generate specific datasets
python data/sample/generate_sample_data.py --events 100 --transactions 10000 --products 500

# Generate for specific exercise
python data/sample/generate_sample_data.py --exercise lambda  # batch-data-sample.parquet only
python data/sample/generate_sample_data.py --exercise kappa   # kinesis-stream-events.json only
python data/sample/generate_sample_data.py --exercise mesh    # domain-*-sample.json only
python data/sample/generate_sample_data.py --exercise cqrs    # event-store-sample.json only
```

---

## File Sizes

| File | Size | Rows | Format |
|------|------|------|--------|
| event-store-sample.json | ~50 KB | 50 events | JSONL |
| kinesis-stream-events.json | ~100 KB | 100 events | JSONL |
| batch-data-sample.parquet | ~500 KB | 10,000 | Parquet |
| domain-products-sample.json | ~80 KB | 500 | JSONL |
| domain-sales-sample.json | ~150 KB | 1,000 | JSONL |
| domain-customer-sample.json | ~30 KB | 200 | JSONL |

**Total**: ~910 KB (small for quick testing)

---

## Generating Data

### First Time Setup

```bash
cd modules/module-18-advanced-architectures
python data/sample/generate_sample_data.py
```

This creates all sample files needed for exercises.

### Regenerate Specific Dataset

```bash
# Regenerate events (CQRS)
python data/sample/generate_sample_data.py --exercise cqrs

# Regenerate batch data (Lambda)
python data/sample/generate_sample_data.py --exercise lambda --transactions 50000

# Regenerate all with custom sizes
python data/sample/generate_sample_data.py \
    --events 200 \
    --transactions 20000 \
    --products 1000 \
    --customers 500 \
    --orders 2000
```

---

## Use Cases

1. **Quick Testing**: Test exercises without AWS infrastructure
2. **CI/CD**: Use in automated tests (fast execution)
3. **LocalStack**: Test locally before deploying to AWS
4. **Demonstrations**: Show architecture patterns with real data
5. **Learning**: Understand event structures and data flows

---

## Data Schemas

### Event Store (CQRS)

```json
{
  "aggregate_id": "ORD_12345",
  "event_type": "OrderPlaced",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": 1,
  "data": {
    "customer_id": "CUST_123",
    "items": [
      {"product_id": "PROD_456", "quantity": 2, "price": 75.00}
    ],
    "amount": 150.00,
    "currency": "USD"
  }
}
```

### Streaming Events (Kappa)

```json
{
  "event_id": "EVT_67890",
  "user_id": "USER_123",
  "event_type": "purchase",
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "product_id": "PROD_456",
    "amount": 75.00,
    "payment_method": "credit_card"
  }
}
```

### Batch Transactions (Lambda)

```json
{
  "transaction_id": 12345,
  "user_id": 123,
  "product_id": 456,
  "amount": 75.00,
  "timestamp": "2024-01-15T10:30:00Z",
  "country": "US",
  "status": "completed"
}
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- JSONL format (one JSON object per line) for streaming compatibility
- Parquet for batch data (columnar storage)
- Realistic data with proper referential integrity
- IDs follow naming conventions (ORD_, CUST_, PROD_, etc.)

---

## Regenerating for Production

For production testing with larger datasets:

```bash
python data/sample/generate_sample_data.py \
    --events 10000 \
    --transactions 1000000 \
    --products 10000 \
    --customers 100000 \
    --orders 500000 \
    --output data/production/
```

**Warning**: Large datasets take longer to generate and require more storage.
