# Exercise 04: Event-Driven CQRS Architecture

## Overview

**CQRS** (Command Query Responsibility Segregation) separates write operations (commands) from read operations (queries). Combined with **Event Sourcing**, all state changes are stored as immutable events, enabling:
- Temporal queries ("What was inventory on Jan 1, 2025?")
- Audit trails (complete history of changes)
- Replay capability (rebuild state from events)
- Multiple read models (optimized for different queries)

**Time**: 4-5 hours
**Difficulty**: ⭐⭐⭐⭐⭐ Advanced

## Learning Objectives

After completing this exercise, you will be able to:

1. **Implement Event Sourcing** with immutable event log (DynamoDB)
2. **Separate write and read models** (CQRS pattern)
3. **Build event-driven system** with EventBridge routing
4. **Handle eventual consistency** between command and query sides
5. **Implement compensating transactions** (Saga pattern)

## CQRS + Event Sourcing Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                          COMMAND SIDE (Writes)                                 │
└────────────────────────────────────────────────────────────────────────────────┘

      API Request (POST /orders)
             ↓
      ┌─────────────────────┐
      │  Command Handler    │  Validation: business rules, inventory check
      │  (Lambda)           │  Result: Success → emit event | Failure → reject
      └─────────────────────┘
             ↓
      ┌─────────────────────┐
      │  Event Store        │  Append-only log (DynamoDB)
      │  (DynamoDB)         │  - OrderPlaced
      │                     │  - OrderCancelled
      │  PK: order_id       │  - PaymentProcessed
      │  SK: timestamp      │  - OrderShipped
      └─────────────────────┘
             ↓
      ┌─────────────────────┐
      │  EventBridge        │  Event router: publish events to subscribers
      └─────────────────────┘
             ↓
      ┌──────────────────────────────────────────────────────────────┐
      │                    QUERY SIDE (Reads)                        │
      └──────────────────────────────────────────────────────────────┘

      Event Subscription → Update Projections:

      ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
      │  Current State        │  │  Historical Analysis  │  │  Search Index         │
      │  (ElastiCache)        │  │  (Redshift)           │  │  (OpenSearch)         │
      │                       │  │                       │  │                       │
      │  Key: order_id        │  │  Table: order_history │  │  Index: orders        │
      │  Value: {             │  │  Columns:             │  │  Fields:              │
      │    status,            │  │   - order_id          │  │   - order_id          │
      │    total,             │  │   - event_type        │  │   - customer_name     │
      │    customer           │  │   - timestamp         │  │   - status            │
      │  }                    │  │   - amount            │  │   - items             │
      └───────────────────────┘  └───────────────────────┘  └───────────────────────┘

      API Queries: GET /orders/{id} → ElastiCache (fast, current)
                   GET /orders/history → Redshift (analytics, temporal)
                   GET /orders?search=laptop → OpenSearch (full-text)
```

## Key Concepts

### Event Sourcing

**Definition**: Store all state changes as sequence of events (not current state).

**Traditional Approach** (CRUD):
```sql
-- Update order status
UPDATE orders SET status = 'shipped' WHERE order_id = 'ORD_001';

-- Problem: History lost (can't see order was 'pending' then 'processing')
```

**Event Sourcing Approach**:
```json
Event 1: { "type": "OrderPlaced", "order_id": "ORD_001", "timestamp": "2025-01-15T10:00:00Z", "amount": 150.00 }
Event 2: { "type": "PaymentProcessed", "order_id": "ORD_001", "timestamp": "2025-01-15T10:01:23Z" }
Event 3: { "type": "OrderShipped", "order_id": "ORD_001", "timestamp": "2025-01-15T14:30:00Z", "tracking": "1Z999..." }

-- Current state: Replay events 1-3 → status = 'shipped'
-- Historical query "What was status at 10:15?": Replay events 1-2 → status = 'pending'
```

**Advantages**:
- ✅ **Complete Audit Trail**: Every change recorded (compliance, debugging)
- ✅ **Temporal Queries**: Query state at any point in time
- ✅ **Replay**: Rebuild state from events (fix bugs, add analytics)
- ✅ **Event Notifications**: Subscribers get notified of changes

**Disadvantages**:
- ❌ **Complexity**: Need to replay events to get current state
- ❌ **Storage**: Keep all events forever (100x more data than current state)
- ❌ **Eventual Consistency**: Read models lag behind writes

### CQRS (Command Query Responsibility Segregation)

**Definition**: Use different models for writes (commands) and reads (queries).

**Why CQRS?**
- **Write Model**: Optimized for validation and consistency (DynamoDB with strong consistency)
- **Read Model**: Optimized for query performance (ElastiCache for speed, Redshift for analytics)

**Example**:
```python
# Command Side (Write)
command_handler.place_order(
    order_id="ORD_001",
    customer_id="CUST_123",
    items=[{"product_id": "PROD_456", "quantity": 2}],
    amount=150.00
)
# → Writes to Event Store (DynamoDB)
# → Emits event to EventBridge

# Query Side (Read)
order = query_projection.get_current_order("ORD_001")
# → Reads from ElastiCache (fast, eventually consistent)
```

## Use Case: E-Commerce Order Management

**Question**: "What is the complete history of order ORD_12345?"

**CQRS Answer**:
1. **Event Store**: Query all events for `ORD_12345` (OrderPlaced, PaymentProcessed, OrderShipped)
2. **Timeline Reconstruction**: Show timeline with timestamps
3. **Temporal Query**: "What was status at 2025-01-15T12:00:00Z?" → Replay events up to timestamp

**Benefits**:
- **Compliance**: Complete audit trail for disputes
- **Debugging**: Replay events to reproduce issues
- **Analytics**: Analyze order lifecycle (place → ship duration)

## Implementation

### Part 1: Event Store (Immutable Log)

**File**: `event_store.py`

```python
from event_store import EventStore

store = EventStore()

# Append event (immutable)
store.append_event({
    'aggregate_id': 'ORD_001',
    'event_type': 'OrderPlaced',
    'timestamp': '2025-01-15T10:00:00Z',
    'data': {
        'customer_id': 'CUST_123',
        'amount': 150.00,
        'items': [{'product_id': 'PROD_456', 'qty': 2}]
    }
})

# Replay events for aggregate
events = store.get_events('ORD_001')  # All events for order

# Temporal query
events_at = store.get_events_at_time('ORD_001', '2025-01-15T12:00:00Z')
```

**Key Features**:
- DynamoDB with composite key (PK: aggregate_id, SK: timestamp)
- Immutable (no updates, only appends)
- Optimistic locking (version numbers)
- Snapshots (cache state every 100 events)

### Part 2: Command Handler (Write Operations)

**File**: `command_handler.py`

```python
from command_handler import CommandHandler

handler = CommandHandler()

# Execute command
result = handler.execute_command({
    'command_type': 'PlaceOrder',
    'order_id': 'ORD_001',
    'customer_id': 'CUST_123',
    'items': [{'product_id': 'PROD_456', 'qty': 2}],
    'amount': 150.00
})

# If successful: Event appended to store + published to EventBridge
# If failed: Validation error returned (no event stored)
```

**Validation Rules**:
- `PlaceOrder`: Inventory available, customer active, payment method valid
- `CancelOrder`: Order not shipped yet, refund processed
- `ProcessPayment`: Amount matches order total

### Part 3: Query Projections (Read Models)

**File**: `query_projections.py`

```python
from query_projections import QueryProjections

projections = QueryProjections()

# Current state (ElastiCache - fast)
order = projections.get_current_state('ORD_001')
# → { "status": "shipped", "amount": 150.00 }

# Historical analysis (Redshift - analytics)
lifecycle = projections.get_order_lifecycle('ORD_001')
# → [ "placed at 10:00", "paid at 10:01", "shipped at 14:30" ]

# Temporal query (replay events)
state_at = projections.get_state_at_time('ORD_001', '2025-01-15T12:00:00Z')
# → { "status": "pending", "amount": 150.00 }
```

**Read Models**:
1. **Current State** (ElastiCache): Fast access (<10ms), eventually consistent
2. **Historical Data** (Redshift): Complex analytics, full history
3. **Search Index** (OpenSearch): Full-text search (find orders by customer name)

## Validation Tasks

### Task 1: Verify Event Immutability

**Test**: Attempt to update event (should fail)

```bash
# Append event
python event_store.py --mode append \
    --aggregate ORD_001 \
    --event-type OrderPlaced \
    --data '{"amount": 150.00}'

# Attempt update (should fail)
python event_store.py --mode update \
    --aggregate ORD_001 \
    --timestamp 2025-01-15T10:00:00Z \
    --data '{"amount": 200.00}'
```

**Expected**: Update command rejected (event store is append-only)

### Task 2: Temporal Query

**Test**: Query order state at specific time

```bash
# Events:
# 10:00 - OrderPlaced (amount: $150)
# 10:05 - PaymentProcessed
# 14:30 - OrderShipped

# Query at 10:10 (after payment, before shipping)
python query_projections.py --mode temporal \
    --aggregate ORD_001 \
    --timestamp "2025-01-15T10:10:00Z"

# Expected: { "status": "pending", "paid": true, "shipped": false }

# Query at 15:00 (after shipping)
python query_projections.py --mode temporal \
    --aggregate ORD_001 \
    --timestamp "2025-01-15T15:00:00Z"

# Expected: { "status": "shipped", "paid": true, "shipped": true }
```

**Expected**: Correct state for each timestamp

### Task 3: Eventual Consistency Lag

**Test**: Measure lag between write and read availability

```bash
# Measure lag
python command_handler.py --mode latency-test

# Steps:
# 1. Execute PlaceOrder command (write to event store)
# 2. Poll ElastiCache until order appears (read model updated)
# 3. Calculate lag time

# Expected: Lag < 100ms (ElastiCache update via EventBridge + Lambda)
```

## Challenges

### Challenge 1: Handle Out-of-Order Events

**Scenario**: Network delays cause events to arrive out of order.

```
Expected: Event 1 (10:00) → Event 2 (10:05) → Event 3 (10:10)
Actual:   Event 1 (10:00) → Event 3 (10:10) → Event 2 (10:05) ← Late arrival
```

**Requirements**:
1. Detect out-of-order events (compare timestamp with previous)
2. Reorder events before applying to projection
3. Alert if event arrives >5 minutes late

**Validation**: Projections remain correct even with out-of-order events

### Challenge 2: Implement Saga Pattern (Distributed Transaction)

**Scenario**: Place order requires 3 services (Inventory, Payment, Shipping).

**Saga Choreography**:
```
1. OrderService: PlaceOrder → OrderPlaced event
2. InventoryService: Reserve inventory → InventoryReserved event
3. PaymentService: Charge customer → PaymentProcessed event
4. ShippingService: Create shipment → OrderShipped event

Failure at step 3 (payment declined):
3. PaymentService: → PaymentFailed event
   ↓ Compensating Transactions:
2. InventoryService: → InventoryReleased event (rollback reservation)
1. OrderService: → OrderCancelled event
```

**Requirements**:
1. Implement compensating transactions
2. Handle partial failures (some services succeed, others fail)
3. Ensure eventual consistency (all services reach correct state)

**Validation**: After payment failure, inventory released and order cancelled

### Challenge 3: Optimize Replay Performance

**Scenario**: Replaying 1 million events takes 10 minutes (too slow for production).

**Optimizations**:
1. **Snapshots**: Save state every 100 events → replay only last 100
2. **Parallel Replay**: Process multiple aggregates in parallel
3. **Incremental Projections**: Only replay new events (track watermark)

**Requirements**:
- Implement snapshot strategy
- Reduce replay time to <1 minute

**Validation**: Replay 1M events in <1 minute with snapshots

## Real-World Examples

### Example 1: Airbnb Booking System

**Scale**:
- **Events**: 100M events/day (BookingCreated, BookingCancelled, PaymentProcessed)
- **Event Store**: DynamoDB (300 TB total size)
- **Projections**: 15 different read models (current bookings, revenue analytics, fraud detection)

**Event Types**:
```json
BookingCreated: { "booking_id", "property_id", "guest_id", "check_in", "check_out", "amount" }
BookingCancelled: { "booking_id", "cancelled_by", "refund_amount", "reason" }
PaymentProcessed: { "booking_id", "payment_method", "amount", "currency" }
```

**Query Models**:
1. **Current Bookings** (ElastiCache): Fast lookup for API (GET /bookings/{id})
2. **Revenue Analytics** (Redshift): Aggregate bookings by property, date range
3. **Fraud Detection** (OpenSearch): Search for suspicious patterns (multiple cancellations)

**Benefits**:
- **Audit Trail**: Resolve disputes (complete history of booking changes)
- **Temporal Queries**: "What was occupancy on Dec 31, 2024?" → Replay events
- **Multiple Read Models**: Same events feed different projections (no duplicate writes)

**Challenges**:
- **Event Versioning**: Schema evolution (BookingCreated v1 → v2 with new fields)
- **Consistency**: Read model lag ~100ms (eventual consistency)

**Cost**: Estimated $80K/month (DynamoDB $50K, EventBridge $10K, projections $20K)

### Example 2: Banking Account Transactions

**Events**:
```
AccountOpened → DepositMade → WithdrawalMade → InterestCredited
```

**Use Case**: "Show all transactions from Jan 1 to Jan 31"

**Implementation**:
- **Event Store**: DynamoDB with GSI on account_id
- **Current Balance**: ElastiCache (sum of all DepositMade - WithdrawalMade)
- **Transaction History**: Replay events for date range

**Regulatory Compliance**:
- SOX requires **immutable audit trail** (Event Sourcing provides this)
- Events never deleted (7-year retention)

## Architecture Trade-offs

### Advantages of CQRS + Event Sourcing

✅ **Complete Audit Trail**: Every change recorded (compliance, debugging)
✅ **Temporal Queries**: Query state at any time ("What was inventory on Jan 1?")
✅ **Multiple Read Models**: Same events → different projections (no duplicate writes)
✅ **Flexibility**: Add new projections without changing write side
✅ **Replay Capability**: Fix bugs by replaying events with corrected logic

### Disadvantages

❌ **Complexity**: More complex than CRUD (events, projections, eventual consistency)
❌ **Eventual Consistency**: Read models lag behind writes (50-200ms)
❌ **Storage**: 10-100x more storage (keep all events forever)
❌ **Learning Curve**: Team needs to understand event sourcing patterns
❌ **No Ad-Hoc Deletes**: Can't delete events (only compensating events)

## Cost Analysis

### CRUD Baseline

```
Traditional CRUD (Single database):
├─ RDS PostgreSQL: db.r5.xlarge (4 vCPU, 32 GB) = $500/month
├─ Storage: 500 GB × $0.115/GB = $58/month
└─ Total: $558/month

Queries: Direct SQL on current state
Audit: Separate audit_log table (limited history)
```

### CQRS + Event Sourcing

```
Event Sourcing Architecture:

Event Store (Write Path):
├─ DynamoDB: 1M events/day × 1 KB × 30 days = 30 GB
│  ├─ Write: 1M × $1.25/million = $1.25/day = $37.50/month
│  ├─ Read: 10M × $0.25/million = $2.50/day = $75/month
│  └─ Storage: 30 GB × $0.25/GB = $7.50/month
├─ EventBridge: 1M events × $1.00/million = $1.00/day = $30/month
└─ Subtotal: $150/month

Query Projections (Read Path):
├─ ElastiCache: cache.r5.large (2 vCPU, 13.5 GB) = $116/month
├─ Redshift: dc2.large (2 vCPU, 15 GB, 160 GB SSD) = $180/month
├─ Lambda (projection updaters): 1M invocations × $0.20/million = $0.20/day = $6/month
└─ Subtotal: $302/month

Total: $452/month
```

**Cost Comparison**:
- **CRUD**: $558/month (simple, single database)
- **CQRS**: $452/month (complex, multiple databases)
- **Difference**: -$106/month (19% cheaper for reads, but higher complexity)

**When Worth It**:
- High read:write ratio (100:1) → read optimization pays off
- Compliance requirements → audit trail required (event store provides this)
- Multiple query patterns → separate read models make sense

## Getting Started

### Prerequisites

1. AWS Services:
   - DynamoDB (event store)
   - EventBridge (event routing)
   - ElastiCache Redis (current state projection)
   - Redshift (historical analytics)
   - Lambda (projection updaters)

2. Python environment:
```bash
pip install boto3 redis psycopg2-binary pandas
```

### Step 1: Setup Event Store

```bash
# Create DynamoDB event store
python event_store.py --mode setup
```

### Step 2: Execute Commands

```bash
# Place order
python command_handler.py \
    --mode execute \
    --command PlaceOrder \
    --aggregate ORD_001 \
    --data '{"customer_id": "CUST_123", "amount": 150.00}'

# Process payment
python command_handler.py \
    --mode execute \
    --command ProcessPayment \
    --aggregate ORD_001 \
    --data '{"payment_method": "credit_card"}'

# Ship order
python command_handler.py \
    --mode execute \
    --command ShipOrder \
    --aggregate ORD_001 \
    --data '{"tracking_number": "1Z999AA10123456784"}'
```

### Step 3: Query Current State

```bash
# Get order (from ElastiCache)
python query_projections.py \
    --mode current \
    --aggregate ORD_001

# Expected output:
# {
#   "order_id": "ORD_001",
#   "status": "shipped",
#   "amount": 150.00,
#   "customer_id": "CUST_123",
#   "tracking_number": "1Z999AA10123456784"
# }
```

### Step 4: Query Historical State (Temporal Query)

```bash
# Get state at specific time
python query_projections.py \
    --mode temporal \
    --aggregate ORD_001 \
    --timestamp "2025-01-15T10:30:00Z"

# Expected: { "status": "pending" } (payment not processed yet)
```

### Step 5: Replay Events

```bash
# Rebuild projection from events
python query_projections.py \
    --mode rebuild \
    --aggregate ORD_001

# Replays all events for ORD_001 → updates ElastiCache
```

## Expected Results

### Event Store Output

**All Events for Order**:
```json
[
  {
    "aggregate_id": "ORD_001",
    "event_type": "OrderPlaced",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": 1,
    "data": {
      "customer_id": "CUST_123",
      "items": [{"product_id": "PROD_456", "qty": 2, "price": 75.00}],
      "amount": 150.00
    }
  },
  {
    "aggregate_id": "ORD_001",
    "event_type": "PaymentProcessed",
    "timestamp": "2025-01-15T10:01:23Z",
    "version": 2,
    "data": {
      "payment_method": "credit_card",
      "transaction_id": "TXN_789"
    }
  },
  {
    "aggregate_id": "ORD_001",
    "event_type": "OrderShipped",
    "timestamp": "2025-01-15T14:30:15Z",
    "version": 3,
    "data": {
      "tracking_number": "1Z999AA10123456784",
      "carrier": "UPS"
    }
  }
]
```

### Query Projection Output

**Current State (ElastiCache)**:
```json
{
  "order_id": "ORD_001",
  "status": "shipped",
  "amount": 150.00,
  "customer_id": "CUST_123",
  "payment_status": "processed",
  "tracking_number": "1Z999AA10123456784",
  "last_updated": "2025-01-15T14:30:15Z"
}
```

**Temporal Query (State at 10:30)**:
```json
{
  "order_id": "ORD_001",
  "status": "pending",
  "amount": 150.00,
  "customer_id": "CUST_123",
  "payment_status": "processed",
  "tracking_number": null,
  "state_as_of": "2025-01-15T10:30:00Z"
}
```

## Performance Benchmarks

### Command Execution (Write)

| Command | DynamoDB Write | EventBridge Publish | Total Latency | Cost per Command |
|---------|----------------|---------------------|---------------|------------------|
| PlaceOrder | 8ms | 5ms | 13ms | $0.00000125 |
| ProcessPayment | 6ms | 5ms | 11ms | $0.00000125 |
| CancelOrder | 7ms | 5ms | 12ms | $0.00000125 |

**Write Throughput**: 1,000 commands/second per Lambda instance

### Query Execution (Read)

| Query Type | Data Source | P50 Latency | P99 Latency | Cost per Query |
|------------|-------------|-------------|-------------|----------------|
| Current State | ElastiCache | 5ms | 15ms | $0 |
| Event History | DynamoDB | 12ms | 45ms | $0.0000025 |
| Analytics | Redshift | 2.5 sec | 8 sec | $0.005 |
| Temporal Query | DynamoDB + Replay | 50ms | 200ms | $0.000005 |

**Read Throughput**: 10,000 queries/second (ElastiCache), 500 queries/second (DynamoDB)

### Projection Update Lag

| Projection | Update Method | P50 Lag | P95 Lag | P99 Lag |
|------------|---------------|---------|---------|---------|
| ElastiCache | EventBridge → Lambda | 45ms | 120ms | 250ms |
| Redshift | EventBridge → Lambda → Batch | 5 min | 10 min | 15 min |
| OpenSearch | EventBridge → Lambda | 80ms | 200ms | 400ms |

## Key Learnings

### When to Use CQRS + Event Sourcing

✅ **Use When**:
- Need complete audit trail (compliance: SOX, GDPR)
- Temporal queries required ("What was balance on Dec 31?")
- Multiple read patterns (current state, analytics, search)
- High read:write ratio (100:1) → optimize reads separately
- Complex business logic (order lifecycle with many states)

❌ **Don't Use When**:
- Simple CRUD (create, read, update, delete)
- Low data volume (<10K records)
- Team lacks event sourcing expertise
- No compliance requirements
- Ad-hoc deletes needed (event sourcing doesn't allow true deletes)

### Event Store Design Patterns

**Pattern 1: Aggregate Root**
```
Order (aggregate root)
├─ OrderPlaced
├─ ItemAdded
├─ ItemRemoved
├─ PaymentProcessed
└─ OrderShipped

All events belong to single order (order_id)
```

**Pattern 2: Snapshot Strategy**
```
Events 1-100: Full replay
Event 100: Create snapshot (cache state)
Events 101-200: Replay from snapshot

Query: Load snapshot + replay events 101+
```

**Pattern 3: Versioned Events**
```
OrderPlaced_v1: { "order_id", "amount" }
OrderPlaced_v2: { "order_id", "amount", "currency" }  ← Added field

Replay: Handle both versions (upcaster converts v1 → v2)
```

## Migration Strategy

### Phase 1: CRUD (Current State)
```
API → PostgreSQL (orders table) → API response
```

### Phase 2: Dual Write (Add Event Store)
```
API → PostgreSQL (orders table)
    → Event Store (OrderPlaced event)
    → EventBridge
```

### Phase 3: CQRS (Separate Read Model)
```
API Write → Event Store → EventBridge → ElastiCache (projection)
API Read → ElastiCache (read model)
```

### Phase 4: Full Event Sourcing (No CRUD DB)
```
API Write → Event Store → EventBridge → Projections (ElastiCache, Redshift)
API Read → Projections (current state from ElastiCache)
```

**Timeline**: 3-6 months (Phase 1 → Phase 4), migrate one aggregate type at a time

## Cost-Benefit Analysis

### Scenario: E-Commerce Order System

**Assumptions**:
- Orders: 100K/day (3M/month)
- Queries: 5M/day (read:write = 50:1)
- Events per order: 5 average (Placed, Paid, Packed, Shipped, Delivered)
- Retention: 2 years

**CRUD Approach**:
```
RDS PostgreSQL (db.r5.xlarge):
├─ Instance: $500/month
├─ Storage: 200 GB × $0.115/GB = $23/month
├─ IOPS: 10K provisioned × $0.10 = $1,000/month
└─ Total: $1,523/month

Limitations:
- No temporal queries (history lost on UPDATE)
- Audit logs separate (extra table)
- Single read pattern (can't optimize for different queries)
```

**CQRS + Event Sourcing**:
```
Event Store (DynamoDB):
├─ Events: 100K orders × 5 events × 30 days = 15M events
├─ Write: 100K/day × 30 days × $1.25/million = $3.75/month
├─ Read: 500K/day × 30 days × $0.25/million = $3.75/month
├─ Storage: 15M × 1 KB = 15 GB × $0.25/GB = $3.75/month
└─ Subtotal: $11.25/month

EventBridge:
├─ Events: 15M × $1.00/million = $15/month

Projections:
├─ ElastiCache Redis (cache.r5.large): $116/month
├─ Redshift Serverless: 300 RPU-hours × $0.36 = $108/month
└─ Subtotal: $224/month

Total: $250.25/month
```

**Cost Comparison**:
- **CRUD**: $1,523/month
- **CQRS**: $250/month (84% cheaper!)
- **Reason**: DynamoDB + ElastiCache cheaper than RDS with high IOPS

**However**:
- CQRS adds operational complexity (3 systems vs 1)
- Development time: 2x longer (need to build event handlers, projections)

**Decision**: CQRS justified if:
- Cost savings > $1,200/month covers extra dev time
- OR compliance requires audit trail (event sourcing provides this for free)

## Next Steps

After completing this exercise:

1. **Exercise 05**: Multi-Region Active-Active (replicate events globally)
2. **Exercise 06**: Polyglot Persistence (choose right database per projection)
3. **Module Bonus**: Implement CQRS with Kafka (higher throughput than EventBridge)

**Real-World Application**:
- If audit trail required: Event Sourcing (banking, healthcare, legal)
- If temporal queries needed: Event Sourcing (historical analysis)
- If simple CRUD: Stick with PostgreSQL (CQRS overkill)

## Additional Resources

- **Book**: "Implementing Domain-Driven Design" by Vaughn Vernon (Chapter on Event Sourcing)
- **Article**: [Martin Fowler - Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- **AWS Workshop**: [Event-Driven Architectures](https://catalog.workshops.aws/event-driven-architectures)
- **Video**: Greg Young - "CQRS and Event Sourcing" (90 minutes)

---

**Estimated Completion Time**: 4-5 hours
**Key Takeaway**: CQRS + Event Sourcing provides complete audit trail and temporal queries, but adds complexity - only adopt when requirements justify the extra overhead.
