# Exercise 03: Data Mesh Architecture

## Overview

Data Mesh is a **decentralized approach** to data architecture that treats **data as a product** and distributes ownership to **domain teams**. Instead of a centralized data lake/warehouse, each business domain (Product, Sales, Customer) owns its data products.

**Time**: 4-5 hours
**Difficulty**: ⭐⭐⭐⭐⭐ Advanced

## Learning Objectives

After completing this exercise, you will be able to:

1. **Implement domain-oriented data products** with clear ownership and SLAs
2. **Design self-serve data platform** with reusable infrastructure
3. **Implement federated computational governance** (decentralized but consistent)
4. **Build data product APIs** with quality metrics and discovery
5. **Compare Data Mesh vs Centralized Data Lake** trade-offs

## Data Mesh Four Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA MESH PRINCIPLES                       │
└─────────────────────────────────────────────────────────────────┘

1. Domain Ownership
   ├─ Product Domain Team: Owns product catalog, inventory
   ├─ Sales Domain Team: Owns transactions, orders
   └─ Customer Domain Team: Owns profiles, preferences

2. Data as a Product
   ├─ API for data access (not raw files)
   ├─ Quality SLAs (freshness, accuracy)
   ├─ Documentation & discovery
   └─ Consumer feedback loops

3. Self-Serve Data Platform
   ├─ Reusable infrastructure (S3, Glue, Athena)
   ├─ Automated deployment (Terraform)
   ├─ Monitoring dashboards (CloudWatch)
   └─ Common tooling (Python SDKs)

4. Federated Computational Governance
   ├─ Global policies (PII masking, retention)
   ├─ Domain-specific rules (Product: 7yr, Sales: 10yr)
   └─ Automated compliance checks (Lake Formation)
```

## Architecture: Multi-Domain Data Mesh

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              FEDERATED GOVERNANCE                              │
│  (Lake Formation + Glue Catalog + EventBridge Rules)                          │
└────────────────────────────────────────────────────────────────────────────────┘
                          ↓                    ↓                    ↓
      ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
      │   PRODUCT DOMAIN          │  │   SALES DOMAIN            │  │   CUSTOMER DOMAIN         │
      │   Team: Product Eng (5)   │  │   Team: Sales Eng (4)     │  │   Team: CRM Eng (3)       │
      ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤
      │ Data Products:            │  │ Data Products:            │  │ Data Products:            │
      │  • Product Catalog        │  │  • Order Events           │  │  • Customer Profiles      │
      │  • Inventory Snapshot     │  │  • Revenue Daily          │  │  • Preferences            │
      │  • Category Hierarchy     │  │  • Shopping Carts         │  │  • Segments               │
      ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤
      │ Storage:                  │  │ Storage:                  │  │ Storage:                  │
      │  S3:                      │  │  S3:                      │  │  S3:                      │
      │   product-domain-prod/    │  │   sales-domain-prod/      │  │   customer-domain-prod/   │
      ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤
      │ API (FastAPI):            │  │ API (FastAPI):            │  │ API (FastAPI):            │
      │  GET /products            │  │  GET /orders              │  │  GET /customers           │
      │  GET /inventory           │  │  GET /revenue             │  │  GET /segments            │
      ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤
      │ Schema (Glue Registry):   │  │ Schema (Glue Registry):   │  │ Schema (Glue Registry):   │
      │  product.avsc v3          │  │  order.avsc v5            │  │  customer.avsc v2         │
      ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤
      │ SLAs:                     │  │ SLAs:                     │  │ SLAs:                     │
      │  • Freshness: < 1 hour    │  │  • Freshness: < 5 min     │  │  • Freshness: < 15 min    │
      │  • Availability: 99.9%    │  │  • Availability: 99.95%   │  │  • Availability: 99.9%    │
      │  • Accuracy: > 99%        │  │  • Accuracy: 100%         │  │  • Accuracy: > 95%        │
      └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘
                          ↓                    ↓                    ↓
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │                    SELF-SERVE DATA PLATFORM (Central)                       │
      │  • S3 buckets infrastructure                                                │
      │  • Glue Data Catalog (federated across domains)                             │
      │  • Lake Formation access control                                            │
      │  • Athena query engine (shared)                                             │
      │  • CloudWatch dashboards (SLA monitoring)                                   │
      └─────────────────────────────────────────────────────────────────────────────┘
                                          ↓
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │                          DATA CONSUMERS                                     │
      │  • Analytics Team: Cross-domain queries (JOIN products + orders + customers)│
      │  • ML Team: Feature engineering pipelines                                   │
      │  • BI Team: Dashboards (QuickSight)                                         │
      └─────────────────────────────────────────────────────────────────────────────┘
```

## Key Differences: Data Mesh vs Centralized Data Lake

| Aspect | Centralized Data Lake | Data Mesh |
|--------|----------------------|-----------|
| **Ownership** | Central data team (5-10 people) | Domain teams (3-5 per domain) |
| **Data Quality** | Data team responsible | Domain team responsible |
| **Scaling** | Bottleneck at data team | Scales with business domains |
| **Expertise** | Data team learns all domains | Domain team has business context |
| **Time to Market** | 2-4 weeks (queued) | 1-3 days (self-serve) |
| **Cost** | $50K/month (central team) | $20K/month + $10K per domain |
| **Complexity** | Low (single system) | High (distributed governance) |

## Use Case: Multi-Domain E-Commerce Analytics

**Question**: "What is revenue by product category for high-value customers?"

**Data Mesh Answer**:
1. **Customer Domain**: Provides `high-value customers` segment (RFM score > 400)
2. **Sales Domain**: Provides `order events` with revenue
3. **Product Domain**: Provides `product catalog` with categories
4. **Analytics Team**: JOINs all 3 data products (federated query via Athena)

**Benefits**:
- **Product Domain**: Enriches catalog independently (add hierarchy, attributes)
- **Sales Domain**: Can change order schema (v4 → v5) without breaking consumers
- **Customer Domain**: Manages PII compliance (GDPR, CCPA) autonomously
- **Analytics Team**: Discovers data products via catalog, no dependency on central team

## Implementation

### Part 1: Domain Data Product API

Each domain exposes its data as a **data product** with:
- **API endpoint**: FastAPI REST API (GET /products, /orders, /customers)
- **Schema registry**: Glue Schema Registry with versioning (Avro)
- **Quality metrics**: Freshness, completeness, accuracy SLAs
- **Documentation**: Auto-generated OpenAPI spec
- **Discovery**: Glue Data Catalog metadata

**File**: `domain_api.py`

```python
# Product Domain API
from domain_api import DomainDataProduct

product_domain = DomainDataProduct(
    domain_name="product",
    data_products=["catalog", "inventory"],
    s3_bucket="product-domain-prod",
    glue_database="product_domain_db"
)

# Start API server
product_domain.serve(port=8001)

# Query: GET http://localhost:8001/products?category=Electronics
```

**Features**:
- Auto-register data products in Glue Catalog
- SLA monitoring (track freshness, availability)
- Access control with API keys
- Usage analytics (consumer tracking)

### Part 2: Schema Registry with Versioning

Centralized schema management with **backward/forward compatibility**.

**File**: `schema_registry.py`

```python
from schema_registry import SchemaRegistry

registry = SchemaRegistry()

# Register schema
registry.register_schema(
    domain="product",
    data_product="catalog",
    schema_type="AVRO",
    schema_content={
        "type": "record",
        "name": "Product",
        "fields": [
            {"name": "product_id", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "category", "type": "string"},
            {"name": "price", "type": "double"}
        ]
    },
    compatibility="BACKWARD"  # Can add optional fields
)

# Validate schema evolution
is_compatible = registry.check_compatibility(
    domain="product",
    data_product="catalog",
    new_schema=updated_schema
)
```

### Part 3: Catalog Federation (Cross-Domain Queries)

Enable analytics teams to discover and query data products across domains.

**File**: `catalog_federation.py`

```python
from catalog_federation import CatalogFederation

federation = CatalogFederation()

# Discover data products
products = federation.discover_data_products(
    domain="sales",  # or None for all domains
    tags={"freshness": "realtime"}
)

# Cross-domain query
sql = """
    SELECT
        p.category,
        SUM(o.amount) as revenue,
        COUNT(DISTINCT o.customer_id) as buyers
    FROM sales_domain_db.orders o
    JOIN product_domain_db.catalog p
        ON o.product_id = p.product_id
    JOIN customer_domain_db.profiles c
        ON o.customer_id = c.customer_id
    WHERE c.segment = 'high_value'
      AND o.order_date >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY p.category
"""

result = federation.execute_federated_query(sql)
```

**Features**:
- Glue Data Catalog search across domains
- Lake Formation permissions (column-level access)
- Athena federated query execution
- Query cost attribution per domain

## Validation Tasks

### Task 1: Verify Domain Independence

**Test**: Product Domain should be able to add a new field without breaking Sales Domain

```bash
# Add field to Product schema (v3 → v4)
python schema_registry.py --domain product --add-field "brand:string"

# Sales Domain queries should still work (backward compatible)
python domain_api.py --domain sales --query "SELECT * FROM orders LIMIT 10"
```

**Expected**: Sales Domain continues to work (doesn't use `brand` field)

### Task 2: Measure SLA Compliance

**Test**: Check if all domains meet their freshness SLAs

```bash
# Check SLAs
python domain_api.py --mode check-slas

# Expected output:
# Product Domain: ✅ Freshness 45 minutes (SLA: < 60 min)
# Sales Domain: ✅ Freshness 2 minutes (SLA: < 5 min)
# Customer Domain: ✅ Freshness 8 minutes (SLA: < 15 min)
```

### Task 3: Execute Cross-Domain Query

**Test**: Query data from all 3 domains

```bash
# Revenue by category for high-value customers
python catalog_federation.py \
    --mode federated-query \
    --sql "SELECT p.category, SUM(o.amount) as revenue
           FROM sales_domain_db.orders o
           JOIN product_domain_db.catalog p ON o.product_id = p.product_id
           JOIN customer_domain_db.profiles c ON o.customer_id = c.customer_id
           WHERE c.segment = 'high_value'
           GROUP BY p.category"
```

**Expected**: Query joins across 3 domains, returns aggregated revenue

## Challenges

### Challenge 1: Schema Evolution Without Breaking Consumers

**Scenario**: Product Domain wants to add a new field `sustainability_score` (1-100).

**Requirements**:
1. Add field with default value (backward compatible)
2. Validate compatibility before deployment
3. Consumers (Sales Domain) should not break
4. Update schema in Glue Schema Registry (v4)

**Validation**: Sales Domain continues to query products without errors

### Challenge 2: Implement Domain SLA Dashboard

**Requirements**:
1. Track freshness for each data product (last update time)
2. Track availability (API uptime %)
3. Track accuracy (data quality checks)
4. Alert if SLA violated (CloudWatch alarm → SNS)

**Metrics to Track**:
- Product Domain: `last_update_timestamp`, `catalog_completeness` (% products with images)
- Sales Domain: `order_processing_delay`, `revenue_accuracy` (% orders reconciled)
- Customer Domain: `profile_completeness`, `segment_freshness`

**Validation**: Dashboard shows all domains meeting SLAs

### Challenge 3: Handle PII Compliance Across Domains

**Scenario**: GDPR requires deleting customer data within 30 days of request.

**Requirements**:
1. Customer Domain: Delete from `customer_domain_db.profiles`
2. Sales Domain: Keep orders but pseudonymize `customer_id` (hash with salt)
3. Product Domain: No customer data (no action needed)
4. Implement **data lineage tracking** (which domains have customer data?)

**Validation**: After deletion, customer data removed but orders preserved (anonymized)

## Real-World Examples

### Example 1: Uber Data Mesh

**Scale**:
- **Domains**: 30+ (Matching, Payments, Dispatch, Pricing, Safety, Restaurants...)
- **Engineers**: 1,000+ (was 100 before Data Mesh)
- **Data Products**: 10,000+ pipelines
- **Data Volume**: Multiple petabytes

**Structure**:
```
Matching Domain (3 teams, 15 engineers)
├─ Data Products: driver_availability, ride_requests, eta_predictions
├─ Storage: S3 (Parquet), Kafka (events), Cassandra (realtime)
├─ API: gRPC + REST
└─ SLAs: 99.9% availability, < 1 min freshness

Payments Domain (2 teams, 10 engineers)
├─ Data Products: transactions, refunds, balances
├─ Storage: S3 (encrypted), Aurora (transactional)
├─ API: GraphQL
└─ SLAs: 99.99% availability, < 30 sec freshness
```

**Benefits**:
- **70% faster feature development**: Domain teams don't wait for central data team
- **10x scaling**: From 100 to 1,000+ engineers without bottleneck
- **Clearer ownership**: Each team owns data quality (no ambiguity)

**Challenges**:
- **Discoverability**: 10,000+ pipelines hard to find → built internal catalog (DataBook)
- **Duplication**: Some metrics computed in multiple domains → shared platform components
- **Coordination**: Cross-domain changes require sync → domain contracts

**Cost**: Estimated $5-10M/month for full platform (30 domains × $150K-300K per domain)

### Example 2: Intuit Data Mesh

**Context**: Tax preparation software (TurboTax, QuickBooks) with seasonal spike.

**Domains**:
1. **Tax Domain**: Tax returns, deductions, refunds
2. **Financial Domain**: Bank connections, transactions
3. **Identity Domain**: Users, authentication, KYC

**Data Products**:
- `TaxDomain.annual_returns` (100M records, 50 GB)
- `FinancialDomain.bank_transactions` (1B records, 500 GB)
- `IdentityDomain.verified_users` (50M records, 10 GB)

**Governance**:
- **Global**: PII encryption (AES-256), retention (7 years), access logs
- **Domain-specific**: Tax Domain keeps raw returns 10 years (IRS compliance)

**Cost Savings**: $2M/year by eliminating central data team (20 people × $100K salary)

## Architecture Trade-offs

### Advantages of Data Mesh

✅ **Scalability**: Each domain scales independently (add engineers without coordination)
✅ **Faster Innovation**: Teams deploy data products without waiting for central team
✅ **Domain Expertise**: Teams understand their data better (higher quality)
✅ **Fault Isolation**: Issues in Sales Domain don't affect Product Domain
✅ **Clear Ownership**: Accountability clear (no "not my problem")

### Disadvantages of Data Mesh

❌ **Complexity**: Distributed system harder to debug (30 APIs vs 1 data lake)
❌ **Duplication**: Common logic duplicated across domains (customer segmentation)
❌ **Learning Curve**: Teams need to learn platform (Glue, Lake Formation, Athena)
❌ **Discovery Challenge**: 10,000+ data products hard to find (need catalog tooling)
❌ **Cross-Domain Coordination**: Breaking changes require synchronization
❌ **Cost**: Higher infrastructure cost per domain ($10K-20K/domain/month)

## Cost Analysis

### Centralized Data Lake (Baseline)

```
Central Data Lake (Single team, 10 engineers):
├─ S3 Storage: 50 TB × $0.023/GB = $1,150/month
├─ Glue ETL: 500 DPU-hours/day × $0.44 = $6,600/month
├─ Athena Queries: 10 TB scanned × $5/TB = $50/month
├─ Team Salaries: 10 engineers × $150K/year = $125,000/month
└─ Total: $132,800/month

Limitations:
- Bottleneck at central team (2-4 week backlog)
- Domain teams dependent on data engineering
```

### Data Mesh (3 Domains)

```
Data Mesh (3 domains, 4 engineers per domain = 12 total):

Product Domain:
├─ S3: 10 TB × $0.023/GB = $230/month
├─ Glue: 100 DPU-hours/day × $0.44 = $1,320/month
├─ API: Fargate 2 vCPU × $29.89 = $60/month
└─ Subtotal: $1,610/month

Sales Domain:
├─ S3: 25 TB × $0.023/GB = $575/month
├─ Glue: 300 DPU-hours/day × $0.44 = $3,960/month
├─ Kinesis: 3 shards × $33.12 = $99/month
├─ API: Fargate 4 vCPU × $59.78 = $120/month
└─ Subtotal: $4,754/month

Customer Domain:
├─ S3: 15 TB × $0.023/GB = $345/month
├─ Glue: 150 DPU-hours/day × $0.44 = $1,980/month
├─ DynamoDB: 10M requests/day × $1.25/million = $12/month
├─ API: Fargate 2 vCPU × $29.89 = $60/month
└─ Subtotal: $2,397/month

Shared Platform:
├─ Athena: 15 TB scanned × $5/TB = $75/month
├─ Lake Formation: $0.50/100K resources = $10/month
├─ CloudWatch: 50 dashboards × $3 = $150/month
└─ Subtotal: $235/month

Infrastructure Total: $8,996/month
Team Salaries: 12 engineers × $150K/year = $150,000/month

Total: $158,996/month
```

**Cost Comparison**:
- **Centralized**: $132,800/month (10 engineers)
- **Data Mesh**: $158,996/month (12 engineers)
- **Difference**: +$26,196/month (+20% more expensive)

**When Data Mesh Worth It**:
- **Break-even**: If domain autonomy reduces time-to-market by 50% → generates $26K+/month extra revenue
- **Example**: Launch 2 features/month instead of 1 → each feature generates $20K/month → $40K extra revenue → +$13K net profit
- **Uber**: Went from 100 → 1,000+ engineers → 70% faster features → justified $5M+/month extra cost

## Getting Started

### Prerequisites

1. AWS Account with services available:
   - S3 (storage)
   - Glue (ETL + catalog + schema registry)
   - Lake Formation (access control)
   - Athena (queries)
   - Fargate (APIs)

2. Python environment:
```bash
pip install -r requirements.txt
```

3. IAM Permissions:
   - `s3:*` on domain buckets
   - `glue:*` on domain databases
   - `lakeformation:*` for permissions
   - `athena:*` for queries

### Step 1: Create Domain Infrastructure

```bash
# Product Domain
python domain_api.py --mode setup --domain product

# Creates:
# - S3 bucket: product-domain-prod
# - Glue database: product_domain_db
# - Glue schema registry: product-schemas
# - DynamoDB table: product-api-usage
```

### Step 2: Register Data Product Schema

```bash
# Register product catalog schema
python schema_registry.py \
    --mode register \
    --domain product \
    --data-product catalog \
    --schema-file schemas/product.avsc \
    --compatibility BACKWARD
```

### Step 3: Load Sample Data

```bash
# Generate sample product catalog
python domain_api.py \
    --mode generate-data \
    --domain product \
    --data-product catalog \
    --num-records 10000
```

### Step 4: Start Domain API

```bash
# Start Product Domain API
python domain_api.py --mode serve --domain product --port 8001

# Start Sales Domain API
python domain_api.py --mode serve --domain sales --port 8002

# Start Customer Domain API
python domain_api.py --mode serve --domain customer --port 8003
```

### Step 5: Query Data Products

```bash
# Query Product Domain
curl "http://localhost:8001/products?category=Electronics&limit=10"

# Query Sales Domain
curl "http://localhost:8002/orders?start_date=2025-01-01&end_date=2025-01-31"

# Query Customer Domain
curl "http://localhost:8003/customers?segment=high_value"
```

### Step 6: Execute Federated Query

```bash
# Cross-domain query (3 domains)
python catalog_federation.py \
    --mode query \
    --sql "SELECT p.category, SUM(o.amount) as revenue
           FROM sales_domain_db.orders o
           JOIN product_domain_db.catalog p ON o.product_id = p.product_id
           WHERE o.order_date >= CURRENT_DATE - 30
           GROUP BY p.category
           ORDER BY revenue DESC"
```

### Step 7: Monitor SLAs

```bash
# Check all domains
python domain_api.py --mode check-slas

# Expected output:
# ✅ Product Domain: Freshness 42 min (SLA: < 60 min), Availability 99.94%
# ✅ Sales Domain: Freshness 3 min (SLA: < 5 min), Availability 99.98%
# ✅ Customer Domain: Freshness 11 min (SLA: < 15 min), Availability 99.91%
```

## Expected Results

### Domain Data Product Output

**Product Domain API Response**:
```json
{
  "data_product": "catalog",
  "version": "v3",
  "timestamp": "2025-01-15T10:30:00Z",
  "records": [
    {
      "product_id": "PROD_00001",
      "name": "Wireless Mouse",
      "category": "Electronics",
      "price": 29.99,
      "brand": "Microsoft",
      "in_stock": true
    }
  ],
  "metadata": {
    "freshness_minutes": 42,
    "completeness_pct": 98.5,
    "sla_compliant": true
  }
}
```

### Federated Query Output

**Cross-Domain Revenue by Category**:
```
category        revenue      buyers  avg_order
─────────────────────────────────────────────────
Electronics     $2,450,890   12,345  $198.62
Clothing        $1,890,234    9,876  $191.37
Home            $1,234,567    6,789  $181.84
Sports          $  890,123    5,432  $163.89
```

### SLA Compliance Report

```
╔═══════════════════════════════════════════════════════════════════╗
║                       DOMAIN SLA REPORT                           ║
╚═══════════════════════════════════════════════════════════════════╝

Product Domain (Owner: Engineering Team A)
   Data Product: catalog
   ✅ Freshness: 42 min (SLA: < 60 min)
   ✅ Availability: 99.94% (SLA: > 99.9%)
   ✅ Completeness: 98.5% (SLA: > 95%)
   ✅ API Response Time: 89ms (SLA: < 200ms)

Sales Domain (Owner: Engineering Team B)
   Data Product: orders
   ✅ Freshness: 3 min (SLA: < 5 min)
   ✅ Availability: 99.98% (SLA: > 99.95%)
   ✅ Accuracy: 100% (SLA: 100%)
   ✅ API Response Time: 45ms (SLA: < 100ms)

Customer Domain (Owner: Engineering Team C)
   Data Product: profiles
   ✅ Freshness: 11 min (SLA: < 15 min)
   ✅ Availability: 99.91% (SLA: > 99.9%)
   ⚠️  Completeness: 92.3% (SLA: > 95%) ← VIOLATION
   ✅ API Response Time: 67ms (SLA: < 150ms)

Overall: 11/12 SLAs met (91.7%)
```

## Performance Benchmarks

### Data Product API Latency

| Domain | Endpoint | P50 | P95 | P99 | SLA |
|--------|----------|-----|-----|-----|-----|
| Product | GET /products | 65ms | 120ms | 180ms | < 200ms ✅ |
| Sales | GET /orders | 35ms | 78ms | 95ms | < 100ms ✅ |
| Customer | GET /customers | 42ms | 89ms | 145ms | < 150ms ✅ |

### Cross-Domain Query Performance

| Query Type | Domains | Data Scanned | Duration | Cost |
|------------|---------|--------------|----------|------|
| Revenue by Category | 2 (Sales + Product) | 500 MB | 3.2 sec | $0.0025 |
| Customer Lifetime Value | 2 (Sales + Customer) | 1.2 GB | 5.8 sec | $0.0060 |
| Full Join (3 domains) | 3 (All) | 2.5 GB | 12.4 sec | $0.0125 |

## Key Learnings

### When to Use Data Mesh

✅ **Use Data Mesh When**:
- Large organization (100+ engineers working on data)
- Many business domains (5+ with clear boundaries)
- Domain teams have data expertise (each team has 1-2 data engineers)
- Rapid innovation needed (weekly feature releases)
- Central data team is bottleneck (2+ week backlogs)

❌ **Don't Use Data Mesh When**:
- Small team (<50 engineers total)
- Few domains (<3 with unclear boundaries)
- Limited data engineering expertise (only 1-2 data engineers total)
- Central team not bottleneck (responds in 1-3 days)
- Simple use cases (basic reporting, dashboards)

### Common Pitfalls

1. **Too Many Domains**: If you have 20+ domains, consider grouping (Product + Inventory → Product Domain)
2. **Weak Platform Team**: Self-serve platform requires 3-5 engineers to build/maintain
3. **No Governance**: Without federated governance, chaos (inconsistent schemas, no access control)
4. **Premature Adoption**: Data Mesh adds complexity - start centralized, migrate when bottleneck appears

### Migration Strategy: Strangler Fig Pattern

**Phase 1: Centralized (Current State)**
```
All data → Central Data Lake → Analytics Team queries
```

**Phase 2: Hybrid (One Domain)**
```
Product data → Product Domain API ─┐
Sales data → Central Data Lake     ├─→ Analytics Team
Customer data → Central Data Lake  ┘
```

**Phase 3: Hybrid (Two Domains)**
```
Product data → Product Domain API ─┐
Sales data → Sales Domain API ─────┤
Customer data → Central Data Lake ─┘─→ Analytics Team
```

**Phase 4: Full Data Mesh**
```
Product data → Product Domain API ─┐
Sales data → Sales Domain API ─────┼─→ Analytics Team (federated queries)
Customer data → Customer Domain API┘
```

**Timeline**: 6-12 months for full migration (one domain every 2-3 months)

## Cost-Benefit Analysis

### Scenario: Medium E-Commerce Company

**Assumptions**:
- Engineers: 150 total (30% work with data)
- Data Volume: 50 TB
- Queries: 10,000/day
- Domains: 5 (Product, Sales, Customer, Marketing, Operations)

**Centralized Approach**:
- Cost: $150K/month (10-person central data team + infrastructure)
- Time to Market: 3 weeks average (queued backlog)
- Issues: Bottleneck (teams wait), context loss (data team doesn't understand domains)

**Data Mesh Approach**:
- Cost: $220K/month (5 domains × $15K infrastructure + 3-person platform team × $150K salary / 12 = $37.5K)
- Time to Market: 3 days average (self-serve)
- Benefits: 7x faster (3 weeks → 3 days), better quality (domain expertise)

**ROI Calculation**:
- Extra cost: +$70K/month
- Revenue impact: 7x faster features → 7 features/month instead of 1 → assume $20K/feature → +$120K/month revenue
- **Net benefit**: $120K - $70K = **+$50K/month profit**

**Decision**: Data Mesh justified if faster time-to-market generates $70K+/month extra revenue

## Next Steps

After completing this exercise:

1. **Exercise 04**: Event-Driven CQRS (event sourcing + immutable log)
2. **Exercise 05**: Multi-Region Active-Active (global data mesh)
3. **Exercise 06**: Polyglot Persistence (right database per domain)

**Real-World Application**:
- If your company has 5+ domains: Propose Data Mesh pilot (start with 1 domain)
- If your company is small: Stick with centralized (Data Mesh overkill)
- Read **"Data Mesh"** book by Zhamak Dehghani (O'Reilly, 2022)

## Additional Resources

- **Book**: "Data Mesh" by Zhamak Dehghani (O'Reilly, 2022)
- **AWS Blog**: [How to Build a Data Mesh on AWS](https://aws.amazon.com/blogs/big-data/design-a-data-mesh-architecture-using-aws-lake-formation-and-aws-glue/)
- **Martinfowler.com**: [Data Mesh Principles](https://martinfowler.com/articles/data-mesh-principles.html)
- **Case Study**: [Uber's Data Mesh Journey](https://eng.uber.com/building-data-products/)

---

**Estimated Completion Time**: 4-5 hours
**Key Takeaway**: Data Mesh scales data teams by distributing ownership, but adds complexity - only adopt when centralized approach is bottleneck.
