# Project Brief: Real-Time Analytics Platform for RideShare

## Document Control

| Attribute | Value |
|-----------|-------|
| **Project Name** | Real-Time Analytics Platform |
| **Client** | RideShare Inc. |
| **Document Version** | 1.0 |
| **Date** | March 2026 |
| **Status** | Final |
| **Author** | Data Engineering Team |
| **Stakeholders** | CTO, VP Engineering, VP Operations, Head of Data |

## Table of Contents

- [Executive Summary](#executive-summary)
- [Business Context](#business-context)
- [Current State Analysis](#current-state-analysis)
- [Problem Statement](#problem-statement)
- [Project Objectives](#project-objectives)
- [Technical Requirements](#technical-requirements)
- [Data Sources](#data-sources)
- [Architecture Requirements](#architecture-requirements)
- [Deliverables](#deliverables)
- [Acceptance Criteria](#acceptance-criteria)
- [Security and Compliance](#security-and-compliance)
- [Timeline and Milestones](#timeline-and-milestones)
- [Grading Rubric](#grading-rubric)
- [Assumptions and Constraints](#assumptions-and-constraints)
- [Success Metrics](#success-metrics)
- [Appendices](#appendices)

## Executive Summary

### Business Challenge

RideShare, a rapidly growing ride-sharing platform with 5 million active users and 500,000 drivers across 50 cities, is experiencing critical limitations due to its batch-only data processing architecture. The company processes 10 million rides per month (growing 20% MoM) but relies exclusively on nightly ETL jobs, resulting in 24-hour data latency.

This architectural constraint is causing:

- **$7.5M annual revenue loss** from suboptimal surge pricing decisions based on stale data
- **20% customer churn** due to long wait times from inefficient driver matching
- **$1.2M annual fraud losses** from delayed fraud detection
- **Competitive disadvantage** against Uber and Lyft, which have real-time capabilities

### Proposed Solution

Build a **Real-Time Analytics Platform** that provides sub-5-second data latency across all critical business metrics. The platform will leverage AWS serverless services (Kinesis, Lambda, DynamoDB) to process 100,000+ events per minute, enable dynamic surge pricing, real-time driver dispatch, instant fraud detection, and live operational dashboards.

### Business Value

| Benefit Category | Annual Impact | Notes |
|-----------------|---------------|-------|
| **Revenue Optimization** | +$2.0M | Optimized surge pricing capturing peak demand |
| **Fraud Prevention** | +$0.5M | Real-time fraud detection preventing losses |
| **Customer Retention** | +$1.5M | Reduced churn from improved wait times |
| **Operational Efficiency** | +$0.5M | Automated pricing, faster incident response |
| **Platform Cost** | -$0.05M | AWS infrastructure and operations |
| **Net Annual Benefit** | **+$4.45M** | ROI: 8,900% |

### Project Scope

**In Scope:**
- Real-time event streaming infrastructure (Kinesis Data Streams)
- Stream processing pipelines (Lambda, Kinesis Data Analytics)
- Real-time state management (DynamoDB)
- Live dashboards (QuickSight)
- Data quality monitoring framework
- Workflow orchestration (Step Functions)
- Cost optimization and monitoring

**Out of Scope:**
- Mobile application development (event generation simulated)
- Machine learning models for fraud/demand prediction (future phase)
- Multi-region deployment (future phase)
- Historical data migration beyond 1 year (future phase)
- Integration with external payment gateways (simulated)

### Timeline and Investment

- **Duration**: 4 weeks (25-30 hours of development time)
- **Development Cost**: $50-80/month (AWS Free Tier eligible)
- **Production Cost**: $2-5K/month at current scale
- **Team**: 1 data engineer (you!)

## Business Context

### About RideShare

RideShare is a ride-sharing platform founded in 2018, connecting passengers with nearby drivers through mobile apps. The company has experienced rapid growth and now operates in 50 cities across North America.

**Company Metrics (Current):**

| Metric | Value | Growth Rate |
|--------|-------|-------------|
| Active Users | 5,000,000 | +20% MoM |
| Active Drivers | 500,000 | +15% MoM |
| Monthly Rides | 10,000,000 | +20% MoM |
| Annual Revenue | $50,000,000 | +25% YoY |
| Average Fare | $5.00 | Stable |
| Cities | 50 | +2 per quarter |
| Customer Satisfaction | 4.2/5.0 | Declining (-0.1/quarter) |

### Market Position

RideShare competes in a highly competitive ride-sharing market dominated by Uber and Lyft.

**Competitive Landscape:**

| Company | Market Share | Key Differentiator |
|---------|--------------|-------------------|
| Uber | 68% | Global presence, diverse services |
| Lyft | 25% | Customer service focus, U.S. focus |
| RideShare | 7% | Competitive pricing, local markets |

**RideShare's Competitive Advantages:**
- Lower commission rates (15% vs 25-30% for competitors)
- Strong presence in mid-sized cities (less competition)
- Better driver compensation leading to higher retention
- Focus on customer service and safety

**Current Weaknesses:**
- **No real-time capabilities** (Uber/Lyft have sophisticated real-time systems)
- Manual surge pricing (competitors have automated dynamic pricing)
- Slower driver matching (competitors match in <30 seconds)
- Limited data-driven decision making

### Current Pain Points

#### 1. Revenue Loss from Suboptimal Pricing

**Problem**: Surge pricing decisions are made manually by operations team based on yesterday's data patterns.

**Impact**:
- Miss peak demand windows (e.g., sudden rainstorm, concert letting out)
- Over-price during slow periods, driving customers to competitors
- Under-price during high demand, leaving revenue on table
- **Estimated annual loss: $7.5M** (15% of potential surge revenue)

**Example Scenario**:
```
Friday 6pm - Large concert ends, 20,000 people need rides
Current System:
- Operations team not aware of surge until next day's report
- Standard pricing applied ($5 average fare)
- Many customers can't find rides, use competitor

With Real-Time System:
- Detect 1000+ simultaneous ride requests in concert area
- Auto-adjust surge multiplier to 2.5x within 1 minute
- Attract more drivers to area with higher fares
- Capture $25K additional revenue in 1 hour
```

#### 2. Poor Customer Experience from Slow Matching

**Problem**: Cannot see real-time driver locations and availability, leading to inefficient rider-driver matching.

**Impact**:
- Average wait time: 8.5 minutes (competitors: 4 minutes)
- 40% of customers wait >10 minutes
- 15% of requests result in no driver found
- **20% customer churn rate** (industry avg: 10%)
- Lost annual revenue from churn: **$10M**

**Customer Journey (Current State)**:
```
1. Customer requests ride (9:00:00 AM)
2. Request sent to server, server queries database for nearby drivers
3. Database reflects driver locations from 5 minutes ago (batch update)
4. System assigns driver who may no longer be nearby
5. Driver takes 10 minutes to arrive
6. Customer frustrated, may use competitor next time
```

#### 3. Fraud Detection Delays

**Problem**: Fraudulent activity (fake rides, payment fraud, driver fraud) detected 24 hours later through batch analysis.

**Impact**:
- Cannot stop fraud in progress
- Fraudulent drivers complete multiple fake rides before detection
- Payment fraud not caught until after payout to driver
- **$100K monthly fraud losses** ($1.2M annually)

**Common Fraud Patterns**:
- **Route fraud**: Driver takes circular routes to inflate fare
- **Ghost rides**: Fake rides between colluding driver and "rider"
- **Payment fraud**: Stolen credit cards
- **Bonus abuse**: Gaming referral and bonus systems

**Current Detection (Batch)**:
```
Monday: Fraud occurs (10 fake rides)
Tuesday 3am: Nightly ETL job processes Monday's data
Tuesday 9am: Fraud detection models run on batch data
Tuesday 10am: Fraud team reviews alerts (18-24 hours after fraud)
Tuesday 11am: Driver account suspended
Net Loss: ~$500 (10 rides × $50 average fraud amount)
```

**Desired State (Real-Time)**:
```
Monday: Fraud attempt (unusual route pattern detected in <5 seconds)
Monday: Automatic alert to fraud team + temporary account flag
Monday: Fraud team reviews within minutes, can stop ride in progress
Net Loss: ~$50 (1 ride × $50, vs 10 rides)
90% reduction in fraud losses
```

#### 4. Operational Blind Spots

**Problem**: Zero visibility into platform health and business metrics until next day's reports.

**Impact**:
- Cannot detect outages, degraded performance, or issues in real-time
- Slow incident response (average 8 hours to detect and respond)
- Customer support lacks real-time data to assist customers
- **Estimated cost: 10 hours cumulative downtime per month**

**Recent Incidents**:
- Payment gateway failure went undetected for 4 hours (6pm-10pm Friday) → $200K lost transactions
- Driver app bug caused GPS issues, detected next morning → 12 hours of poor service quality
- Database performance degradation caused slow ride matching → Customers blamed platform, switched to Uber

#### 5. Manual Operations

**Problem**: Operations team manually performs tasks that should be automated.

**Daily Manual Tasks**:
- Set surge pricing multipliers for each city zone (50 cities × 10 zones = 500 manual updates)
- Review yesterday's performance and adjust strategies
- Generate reports for executives
- Investigate customer complaints with stale data

**Impact**:
- Operations team of 20 people spending 50% time on manual tasks
- Human error i n surge pricing decisions
- Delayed response to market changes
- **$500K annual operational cost** that could be automated

## Current State Analysis

### Existing Technology Architecture

#### Data Sources

1. **PostgreSQL OLTP Database** (Primary transactional database)
   - Stores: Users, Drivers, Rides, Payments, Ratings
   - Read replicas for reporting queries
   - ~2 TB database size
   - ~1,000 writes/second during peak hours

2. **Mobile Apps** (iOS and Android for riders and drivers)
   - Generate: Ride requests, GPS locations, ratings
   - Store data locally, sync to server
   - ~5M active users, ~500K active drivers

3. **Third-Party Systems**
   - Payment processors (Stripe, PayPal)
   - SMS/Email notification services
   - Mapping and routing APIs (Google Maps)

#### Current Data Pipeline

```
┌────────────────────────────────────────────────────┐
│         Operational Systems (OLTP)                 │
│                                                    │
│  ┌──────────────┐         ┌──────────────┐        │
│  │ PostgreSQL   │         │ MongoDB      │        │
│  │ (Rides, Users)│         │ (Logs)       │        │
│  └──────┬───────┘         └──────┬───────┘        │
└─────────┼────────────────────────┼────────────────┘
          │                        │
          │ Daily ETL (2am)        │ Daily ETL (3am)
          ▼                        ▼
┌────────────────────────────────────────────────────┐
│            AWS S3 (Data Lake)                      │
│         CSV/JSON files exported daily              │
└────────────┬───────────────────────────────────────┘
             │
             │ Daily ETL (4am-6am)
             ▼
┌────────────────────────────────────────────────────┐
│         Amazon Redshift (Data Warehouse)           │
│      Dimensional model (star schema)               │
│      Aggregations precomputed                      │
└────────────┬───────────────────────────────────────┘
             │
             │ Query
             ▼
┌────────────────────────────────────────────────────┐
│           Tableau (Business Intelligence)          │
│      Dashboards refreshed daily at 7am             │
└────────────────────────────────────────────────────┘
```

**Pipeline Characteristics**:
- **Latency**: 24+ hours (data from Monday available Tuesday morning)
- **Refresh Schedule**: Nightly (2am-7am batch window)
- **Data Volume**: ~50 GB per day
- **ETL Tool**: Python scripts + Airflow orchestration
- **Cost**: ~$2K/month (Redshift + S3 + compute)

#### Current Data Model

**PostgreSQL Schema (Simplified)**:

```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);

-- Drivers table
CREATE TABLE drivers (
    driver_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    vehicle_make VARCHAR(50),
    vehicle_model VARCHAR(50),
    license_plate VARCHAR(20),
    rating DECIMAL(3, 2),
    status VARCHAR(20), -- active, inactive, suspended
    created_at TIMESTAMP
);

-- Rides table
CREATE TABLE rides (
    ride_id UUID PRIMARY KEY,
    customer_id UUID REFERENCES users(user_id),
    driver_id UUID REFERENCES drivers(driver_id),
    status VARCHAR(20), -- requested, matched, in_progress, completed, cancelled
    request_time TIMESTAMP,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    pickup_lat DECIMAL(10, 8),
    pickup_lon DECIMAL(11, 8),
    dropoff_lat DECIMAL(10, 8),
    dropoff_lon DECIMAL(11, 8),
    fare_amount DECIMAL(10, 2),
    surge_multiplier DECIMAL(3, 2),
    distance_km DECIMAL(10, 2),
    duration_minutes INTEGER
);

-- Payments table
CREATE TABLE payments (
    payment_id UUID PRIMARY KEY,
    ride_id UUID REFERENCES rides(ride_id),
    amount DECIMAL(10, 2),
    payment_method VARCHAR(20),
    status VARCHAR(20), -- pending, completed, failed, refunded
    processed_at TIMESTAMP
);

-- Ratings table
CREATE TABLE ratings (
    rating_id UUID PRIMARY KEY,
    ride_id UUID REFERENCES rides(ride_id),
    customer_id UUID REFERENCES users(user_id),
    driver_id UUID REFERENCES drivers(driver_id),
    rating INTEGER, -- 1-5
    comment TEXT,
    created_at TIMESTAMP
);
```

### Limitations of Current Architecture

#### 1. High Latency

- **Data Delay**: Minimum 24 hours, often 36+ hours
- **Root Causes**:
  - Batch ETL runs once per day
  - PostgreSQL replication lag (15-30 minutes)
  - Redshift load times (2-3 hours for large batches)
  - Tableau extract refresh (1 hour)

#### 2. No Real-Time Alerts

- Cannot detect anomalies as they occur
- No automated alerts for SLA breaches
- Operations team reviews static reports, not live dashboards

#### 3. Limited Scalability

- PostgreSQL struggling with write volume (currently 1,000 writes/sec, need 10,000+)
- Redshift nightly loads taking 3+ hours (batch window at risk)
- ETL scripts not designed for micro-batch or streaming

#### 4. High Operational Cost

- Manual interventions required for failures
- Operations team babysitting pipelines
- Frequent issues with data quality (ETL bugs not caught until after loading)

#### 5. Poor Developer Experience

- Long feedback loops (make change, wait 24 hours to see result)
- Difficult to troubleshoot issues (logs scattered, no tracing)
- Hard to add new metrics (requires schema changes, ETL updates, dashboard updates)

## Problem Statement

**How might we** enable real-time visibility into rider and driver activity, platform health, and business metrics **so that** RideShare can make data-driven decisions with sub-5-second latency, optimize revenue through dynamic pricing, improve customer experience through faster matching, and prevent fraud in real-time?

### Success Definition

The real-time analytics platform is successful if it:

1. **Reduces data latency** from 24+ hours to <5 seconds (P95)
2. **Increases revenue** by $2M+ annually through optimized surge pricing
3. **Reduces fraud losses** by 90% through real-time detection
4. **Improves customer satisfaction** (CSAT score from 4.2 to 4.5+)
5. **Maintains cost efficiency** (<$5K/month for production environment)

## Project Objectives

### Primary Objective

**Build a real-time analytics platform** that ingests, processes, and visualizes streaming data from RideShare's operational systems with <5 second end-to-end latency and 99.9% uptime.

### Specific Objectives

#### 1. Real-Time Event Ingestion

**Goal**: Ingest 100,000 events per minute with ability to scale to 1,000,000 events per minute.

**Key Requirements**:
- Four event streams: Rides, Driver Locations, Payments, Ratings
- Event batching for cost optimization (500 records per batch)
- Exactly-once delivery semantics (no duplicates or lost events)
- Automatic partitioning for parallel processing
- Configurable retention (24-168 hours)

**Success Metrics**:
- Throughput: 100K+ events/min sustained, 1M+ events/min peak
- Latency: <1 second from event generation to stream
- Availability: 99.9% uptime
- Error rate: <0.1% failed writes

#### 2. Stream Processing

**Goal**: Process streaming events with <3 second latency and enrich with contextual data.

**Key Requirements**:
- Lambda functions for simple transformations and enrichment
- Kinesis Data Analytics for complex windowing and aggregations
- Stateful processing with DynamoDB lookups
- Error handling with retries and dead-letter queues

**Success Metrics**:
- Processing latency: <3 seconds (P95)
- Throughput: Match ingestion rate (100K+ events/min)
- Error rate: <0.5% failed processing
- Data loss: <0.01%

#### 3. Real-Time Aggregations

**Goal**: Compute streaming aggregations with 1-minute granularity.

**Key Requirements**:
- **1-minute windows**: Ride counts, active drivers, revenue by city
- **5-minute windows**: Surge pricing multipliers, demand/supply ratios
- **1-hour windows**: Daily trends, hour-over-hour comparisons
- **Top-N queries**: Busiest zones, highest-rated drivers

**Success Metrics**:
- Aggregation latency: <5 seconds from event to aggregated metric
- Accuracy: 99.9% (compared to batch calculations)
- Completeness: Handle 99%+ of events (account for late arrivals)

#### 4. Real-Time Dashboards

**Goal**: Provide live operational dashboards with <10 second refresh for operations team and executives.

**Key Requirements**:
- **Operational Dashboard**: Active rides, available drivers, revenue (current), recent alters
- **Executive Dashboard**: Daily trends, city comparisons, top performers
- Auto-refresh without manual intervention
- Mobile-responsive design
- Role-based access control

**Success Metrics**:
- Dashboard refresh: <10 seconds
- Query latency: <2 seconds
- Concurrent users: 100+ without degradation

#### 5. Data Quality Monitoring

**Goal**: Achieve >95% data quality across completeness, accuracy, and timeliness dimensions.

**Key Requirements**:
- Schema validation on all incoming events
- Completeness checks (required fields present, no nulls)
- Consistency checks (cross-stream validation)
- Timeliness checks (event timestamp vs processing timestamp)
- Quality metrics tracked and visualized

**Success Metrics**:
- Data quality score: >95%
- Invalid events: <1%
- Detection latency: <30 seconds for quality issues
- Automated alerts: 100% of quality breaches trigger alert

#### 6. Workflow Orchestration

**Goal**: Orchestrate batch and streaming workflows with automatic error handling and retry logic.

**Key Requirements**:
- Daily aggregation jobs (summarize previous day's data)
- Weekly reporting (executive summaries, trends)
- Error handling with exponential backoff (retry 3x)
- Parallel processing for independent tasks
- Notifications on success/failure

**Success Metrics**:
- Workflow success rate: >99%
- Failed task recovery: <5 minutes
- Notification latency: <1 minute

## Technical Requirements

### Functional Requirements

#### FR-1: Event Streaming

**Description**: Ingest four types of events in real-time.

**Event Types**:

1. **Ride Events** (`ride_requested`, `ride_started`, `ride_completed`, `ride_cancelled`)
2. **Driver Location Events** (GPS coordinates every 30 seconds)
3. **Payment Events** (`payment_initiated`, `payment_completed`, `payment_failed`)
4. **Rating Events** (customer ratings after ride completion)

**Requirements**:
- Support for 100,000 events per minute (current load)
- Auto-scaling to 1,000,000 events per minute (future growth)
- Event ordering within partition key
- Configurable retention period (24-168 hours)
- Compression support (gzip, snappy)

#### FR-2: Stream Processing

**Description**: Process streaming events with transformations, enrichment, and aggregations.

**Processing Requirements**:

1. **Parse and Validate**
   - Parse JSON payloads
   - Validate against JSON Schema
   - Handle malformed events gracefully

2. **Enrich**
   - Lookup user/driver profile data from DynamoDB
   - Add derived fields (e.g., wait time = start_time - request_time)
   - Geocode lat/lon to city/neighborhood

3. **Transform**
   - Standardize formats (timestamps, currencies)
   - Filter sensitive PII fields
   - Aggregate related events (e.g., ride lifecycle)

4. **Write**
   - Write to DynamoDB (real-time state)
   - Write to S3 (archival)
   - Emit custom CloudWatch metrics

**Requirements**:
- Processing latency: <3 seconds (P95)
- Exactly-once processing semantics
- Idempotent operations (safe to retry)
- Error handling with DLQ

#### FR-3: Real-Time Analytics

**Description**: Compute real-time aggregations using Kinesis Data Analytics (Flink SQL).

**Analytics Applications**:

1. **Surge Pricing Calculator**
   - 5-minute sliding windows
   - Calculate demand (ride requests) and supply (available drivers) by zone
   - Compute surge multiplier: `surge = min(3.0, max(1.0, demand / supply))`
   - Output to DynamoDB table for API consumption

2. **Real-Time KPI Aggregator**
   - 1-minute tumbling windows
   - Aggregate: ride counts, revenue, active drivers, average wait time
   - Group by: city, status, hour
   - Output to DynamoDB for dashboard consumption

3. **Hot Spot Detector**
   - 5-minute tumbling windows
   - Geospatial clustering to find busy areas
   - Top-10 busiest zones by ride request volume
   - Output to DynamoDB

**Requirements**:
- Window latency: <5 seconds (from event to windowed result)
- Late arrival handling: 1-minute watermark tolerance
- Exactly-once processing with checkpointing

#### FR-4: State Management

**Description**: Store real-time state in DynamoDB for fast reads and writes.

**DynamoDB Tables**:

1. **rides_state**
   - Partition Key: ride_id
   - Attributes: customer_id, driver_id, status, pickup/dropoff coords, timestamps
   - Purpose: Current state of all active and recent rides

2. **driver_availability**
   - Partition Key: driver_id
   - GSI: city + available (for quick lookups)
   - Attributes: location (lat, lon), available (boolean), current_ride_id, last_update
   - Purpose: Real-time driver location and availability

3. **aggregated_metrics**
   - Partition Key: metric_name (e.g., "active_rides_nyc")
   - Sort Key: timestamp (minute-level granularity)
   - Attributes: value, dimensions (city, status, etc.)
   - Purpose: Pre-computed metrics for dashboards

**Requirements**:
- Read latency: <10ms (P99)
- Write latency: <20ms (P99)
- Capacity: Auto-scaling based on load
- TTL: 30 days for aggregated metrics, 7 days for driver locations

#### FR-5: Data Archival

**Description**: Archive all events to S3 for historical analysis and compliance.

**S3 Structure**:
```
s3://rideshare-events-archive/
├── raw/
│   ├── rides/
│   │   ├── year=2024/
│   │   │   ├── month=01/
│   │   │   │   ├── day=15/
│   │   │   │   │   ├── hour=14/
│   │   │   │   │   │   ├── rides-14-00.parquet
│   │   │   │   │   │   ├── rides-14-30.parquet
│   ├── driver_locations/
│   ├── payments/
│   └── ratings/
├── processed/
│   └── daily_aggregates/
└── quality_reports/
```

**Requirements**:
- Format: Parquet (columnar, compressed)
- Partitioning: year/month/day/hour
- Lifecycle policies: Transition to IA after 30 days, Glacier after 90 days
- Cataloging: AWS Glue Data Catalog for Athena queries

#### FR-6: Dashboards and Visualization

**Description**: QuickSight dashboards for real-time monitoring and historical analysis.

**Dashboard 1: Operational Dashboard** (for operations team)
- **KPI Cards**: Active rides, Available drivers, Current revenue (today), Avg wait time
- **Line Charts**: Rides over time (last 4 hours, 1-min granularity)
- **Bar Charts**: Rides by city (top 10), Rides by status
- **Heatmap**: Geographic density of ride requests
- **Table**: Recent alerts and errors
- **Refresh**: Every 10 seconds

**Dashboard 2: Executive Dashboard** (for leadership)
- **KPI Cards**: Today's metrics vs yesterday, MTD vs last month
- **Line Charts**: Daily rides (last 30 days), Revenue trend, CSAT score
- **Pie Chart**: Revenue by city
- **Bar Chart**: Top 10 drivers (by rating and ride count)
- **Refresh**: Every 1 hour

**Requirements**:
- Data freshness: <10 seconds for operational, <1 hour for executive
- Query latency: <2 seconds
- Concurrent users: 100+
- Mobile responsive

#### FR-7: Alerting and Monitoring

**Description**: Automated alerting for system health, SLA breaches, and data quality issues.

**CloudWatch Alarms**:

| Alarm Name | Condition | Action |
|-----------|-----------|--------|
| High Error Rate | Lambda errors >1% over 5 min | SNS → PagerDuty (P1) |
| High Latency | Processing latency >10s (P95) | SNS → Email (P2) |
| Kinesis Throttling | WriteProvisionedThroughputExceeded >0 | SNS → Email (P3) |
| DynamoDB Throttling | ThrottledRequests >10 over 5 min | SNS → Email (P3) |
| Data Quality Degradation | Quality score <95% | SNS → Email (P2) |
| Cost Anomaly | Daily spend >$200 | SNS → Email (P2) |

**Requirements**:
- Alert latency: <1 minute from condition to notification
- Alert fatigue: <10 alerts per day (avoid false positives)
- On-call rotation: PagerDuty integration for P1 alerts

#### FR-8: Workflow Orchestration

**Description**: Step Functions workflows for batch jobs and complex orchestration.

**Workflow 1: Daily Aggregation**
```
Start
├── Parallel Branch 1: Aggregate rides data
│   ├── Query S3 (yesterday's rides)
│   ├── Glue ETL job
│   └── Write to DynamoDB/S3
├── Parallel Branch 2: Aggregate driver data
│   ├── Query S3 (yesterday's driver locations)
│   ├── Glue ETL job
│   └── Write to DynamoDB/S3
├── Parallel Branch 3: Aggregate payments data
│   ├── Query S3 (yesterday's payments)
│   ├── Glue ETL job
│   └── Write to DynamoDB/S3
├── Join: All branches complete
├── Generate summary report
└── SNS notification (success/failure)

Error Handling: Retry 3x with exponential backoff
Schedule: Daily at 2:00 AM UTC
```

**Workflow 2: Weekly Reporting**
```
Start
├── Fan-out: For each city (50 cities)
│   ├── Generate city report
│   └── Upload to S3
├── Fan-in: Aggregate city reports
├── Generate executive summary
├── Email to stakeholders
└── SNS notification (success/failure)

Error Handling: Continue on failure (individual city)
Schedule: Weekly on Sunday at 3:00 AM UTC
```

**Requirements**:
- Workflow success rate: >99%
- Error recovery: Automatic retry 3x with exponential backoff
- Visibility: CloudWatch Logs for debugging
- Cost: Optimize for minimal Step Functions transitions

### Non-Functional Requirements

#### NFR-1: Performance

| Metric | Requirement |
|--------|-------------|
| Event Ingestion Latency | <1 second (P95) |
| Processing Latency | <3 seconds (P95) |
| End-to-End Latency | <5 seconds (P95) from event generation to dashboard |
| Query Latency | <2 seconds for dashboard queries |
| Throughput | 100,000 events/min sustained, 1,000,000 events/min peak |

#### NFR-2: Availability and Reliability

| Metric | Requirement |
|--------|-------------|
| Uptime | 99.9%  (43 minutes downtime per month) |
| Data Loss | <0.01% (99.99% durability) |
| Processing Success Rate | >99.5% (including retries) |
| RTO (Recovery Time Objective) | <15 minutes |
| RPO (Recovery Point Objective) | <5 minutes |

#### NFR-3: Scalability

- **Horizontal Scaling**: Auto-scale from 1,000 to 1,000,000 events/min without manual intervention
- **Shard Growth**: Kinesis streams auto-scale or use on-demand mode
- **Lambda Concurrency**: Auto-scale to handle load (reserve quotas if needed)
- **DynamoDB Capacity**: Use on-demand mode or auto-scaling provisioned throughput

#### NFR-4: Security

- **Encryption at Rest**: All data encrypted with AWS KMS
- **Encryption in Transit**: TLS 1.2+ for all data transfers
- **IAM Roles**: Least privilege principle, no hardcoded credentials
- **Secrets Management**: AWS Secrets Manager for API keys and passwords
- **Network Security**: Resources in private subnets where appropriate, use VPC endpoints
- **Audit Logging**: AWS CloudTrail enabled for all API calls

#### NFR-5: Cost Efficiency

| Environment | Monthly Budget | Notes |
|------------|----------------|-------|
| Development | $50-80 | Leverage Free Tier, minimal shards/capacity |
| Production | $2,000-5,000 | At current scale (10M rides/month) |
| Production (Future) | $5,000-10,000 | At 100M rides/month (10x growth) |

**Cost Optimization Strategies**:
- Use AWS Free Tier where eligible
- Right-size Lambda memory and timeout
- Optimize Kinesis shard count
- Use DynamoDB on-demand for spiky workloads
- S3 lifecycle policies for archival
- Reserved capacity for predictable workloads

#### NFR-6: Maintainability

- **Infrastructure as Code**: 100% of infrastructure in Terraform
- **Version Control**: Git for all code and configuration
- **Documentation**: Architecture diagrams, runbooks, API docs
- **Code Quality**: >80% test coverage, linting, formatting
- **Observability**: Comprehensive logging, metrics, distributed tracing (X-Ray)

## Data Sources

### 1. Ride Events Stream

**Event Producer**: Mobile apps (riders and drivers)

**Event Types**:

#### Event: `ride_requested`

```json
{
  "event_type": "ride_requested",
  "event_id": "evt_a1b2c3d4",
  "event_timestamp": "2024-01-15T14:23:45.123Z",
  "ride_id": "ride_x9y8z7w6",
  "customer_id": "usr_12345678",
  "pickup_location": {
    "lat": 40.7589,
    "lon": -73.9851,
    "address": "1633 Broadway, New York, NY 10019"
  },
  "dropoff_location": {
    "lat": 40.7128,
    "lon": -74.0060,
    "address": "1 World Trade Center, New York, NY 10007"
  },
  "ride_type": "standard",  // standard, premium, shared
  "estimated_fare": 15.50,
  "estimated_duration_minutes": 18
}
```

#### Event: `ride_started`

```json
{
  "event_type": "ride_started",
  "event_id": "evt_b2c3d4e5",
  "event_timestamp": "2024-01-15T14:28:12.456Z",
  "ride_id": "ride_x9y8z7w6",
  "driver_id": "drv_87654321",
  "actual_pickup_location": {
    "lat": 40.7591,
    "lon": -73.9849
  },
  "wait_time_seconds": 267  // time from request to start
}
```

#### Event: `ride_completed`

```json
{
  "event_type": "ride_completed",
  "event_id": "evt_c3d4e5f6",
  "event_timestamp": "2024-01-15T14:46:33.789Z",
  "ride_id": "ride_x9y8z7w6",
  "actual_dropoff_location": {
    "lat": 40.7130,
    "lon": -74.0062
  },
  "distance_km": 8.3,
  "duration_minutes": 18,
  "base_fare": 15.50,
  "surge_multiplier": 1.5,
  "final_fare": 23.25,
  "route": [
    {"lat": 40.7589, "lon": -73.9851, "timestamp": "2024-01-15T14:28:12.456Z"},
    {"lat": 40.7545, "lon": -73.9860, "timestamp": "2024-01-15T14:30:00.000Z"},
    // ... more waypoints
    {"lat": 40.7130, "lon": -74.0062, "timestamp": "2024-01-15T14:46:33.789Z"}
  ]
}
```

**Event Volume**: 10M rides/month = ~333K rides/day = ~231 rides/minute (avg), ~1,000 rides/minute (peak)

**Event Size**: ~500 bytes per event (excluding route waypoints)

**Kinesis Configuration**:
- Stream name: `rideshare-ride-events`
- Shard count: 4 shards (250 rides/min per shard)
- Retention: 24 hours

### 2. Driver Location Events Stream

**Event Producer**: Driver mobile app (sends GPS location every 30 seconds when app is open)

**Event Schema**:

```json
{
  "event_type": "driver_location",
  "event_id": "evt_d4e5f6g7",
  "event_timestamp": "2024-01-15T14:23:30.000Z",
  "driver_id": "drv_87654321",
  "location": {
    "lat": 40.7589,
    "lon": -73.9851,
    "accuracy_meters": 10,
    "speed_kmh": 25,
    "heading_degrees": 90
  },
  "available": true,  // false if currently on a ride
  "current_ride_id": null,  // populated if on a ride
  "battery_level": 85,
  "app_version": "4.2.1"
}
```

**Event Volume**: 500K drivers × 2 updates/minute (30-second interval) = 1M events/minute

**Event Size**: ~250 bytes per event

**Kinesis Configuration**:
- Stream name: `rideshare-driver-locations`
- Shard count: 10 shards (100K events/min per shard)
- Retention: 24 hours

**Note**: This is the highest-volume stream. Consider data reduction strategies:
- Only send location if driver moved >50 meters
- Dynamic interval (30s when moving, 2min when stationary)
- Sample locations (e.g., send every other location for analytics)

### 3. Payment Events Stream

**Event Producer**: Payment processing service

**Event Types**:

#### Event: `payment_initiated`

```json
{
  "event_type": "payment_initiated",
  "event_id": "evt_e5f6g7h8",
  "event_timestamp": "2024-01-15T14:46:34.123Z",
  "payment_id": "pmt_abcdef12",
  "ride_id": "ride_x9y8z7w6",
  "customer_id": "usr_12345678",
  "amount": 23.25,
  "currency": "USD",
  "payment_method": "credit_card",  // credit_card, debit_card, paypal, apple_pay
  "card_last_four": "4242"
}
```

#### Event: `payment_completed`

```json
{
  "event_type": "payment_completed",
  "event_id": "evt_f6g7h8i9",
  "event_timestamp": "2024-01-15T14:46:36.789Z",
  "payment_id": "pmt_abcdef12",
  "ride_id": "ride_x9y8z7w6",
  "status": "success",  // success, failed
  "processor_transaction_id": "txn_stripe_xyz789",
  "processing_time_ms": 2456
}
```

**Event Volume**: ~10M payments/month = ~333K payments/day = ~231 payments/minute (avg)

**Event Size**: ~300 bytes per event

**Kinesis Configuration**:
- Stream name: `rideshare-payment-events`
- Shard count: 2 shards
- Retention: 168 hours (7 days for compliance)

### 4. Rating Events Stream

**Event Producer**: Mobile app (rider submits rating after ride completion)

**Event Schema**:

```json
{
  "event_type": "rating_submitted",
  "event_id": "evt_g7h8i9j0",
  "event_timestamp": "2024-01-15T14:50:22.456Z",
  "rating_id": "rat_12345678",
  "ride_id": "ride_x9y8z7w6",
  "customer_id": "usr_12345678",
  "driver_id": "drv_87654321",
  "rating": 5,  // 1-5 stars
  "comment": "Great driver, very friendly!",
  "categories": ["cleanliness", "safety", "communication"],  // positive categories
  "tip_amount": 5.00
}
```

**Event Volume**: ~8M ratings/month (80% of rides) = ~267K ratings/day = ~185 ratings/minute

**Event Size**: ~400 bytes per event

**Kinesis Configuration**:
- Stream name: `rideshare-rating-events`
- Shard count: 1 shard
- Retention: 24 hours

## Architecture Requirements

### Logical Architecture

The platform will follow a **Lambda Architecture** approach, combining real-time stream processing (speed layer) and batch processing (batch layer) for comprehensive analytics.

```
                      ┌──────────────────────┐
                      │   Event Sources      │
                      │  (Mobile Apps, etc.) │
                      └──────────┬───────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
        ┌──────────────┐  ┌──────────────┐  ┌─────────┐
        │ Speed Layer  │  │  Batch Layer │  │ Serving │
        │ (Real-Time)  │  │ (Historical) │  │  Layer  │
        └──────────────┘  └──────────────┘  └─────────┘
```

### Physical Architecture (AWS Services)

See README.md for detailed architecture diagram.

**Key Components**:
- **Ingestion**: Kinesis Data Streams (4 streams)
- **Processing**: Lambda (6 functions) + Kinesis Data Analytics (3 applications)
- **Storage**: DynamoDB (3 tables) + S3 (3 buckets)
- **Orchestration**: Step Functions (2 workflows) + EventBridge
- **Visualization**: QuickSight (2 dashboards)
- **Monitoring**: CloudWatch + SNS + X-Ray

### Network Architecture

- **VPC**: Create dedicated VPC for RideShare resources
- **Subnets**: Public subnets for internet-facing resources, private subnets for data stores
- **Security Groups**: Least privilege access rules
- **VPC Endpoints**: For S3, DynamoDB to avoid internet routing
- **NAT Gateway**: For Lambda functions in private subnets (if needed)

### Disaster Recovery

**Backup Strategy**:
- Kinesis: Data retained 24-168 hours (configurable)
- DynamoDB: Point-in-time recovery (PITR) enabled, 35-day retention
- S3: Versioning enabled, cross-region replication (optional for compliance)

**Recovery Procedures**:
- **Scenario 1: Lambda Function Failure** → Automatic retries (3x), DLQ for failed events, replay from Kinesis
- **Scenario 2: Kinesis Stream Unavailable** → Events buffer in producer, circuit breaker after 5 minutes, replay when available
- **Scenario 3: DynamoDB Throttling** → Auto-scaling triggers, write buffering, alert to ops team
- **Scenario 4: Complete Region Failure** → Manual failover to secondary region (future: active-active multi-region)

## Deliverables

### 1. Infrastructure as Code (Terraform)

**Files**:
- `main.tf`: Main configuration
- `variables.tf`: Input variables
- `outputs.tf`: Output values (ARNs, endpoints)
- `iam.tf`: IAM roles and policies
- `kinesis.tf`: Kinesis streams
- `lambda.tf`: Lambda functions
- `dynamodb.tf`: DynamoDB tables
- `s3.tf`: S3 buckets
- `step-functions.tf`: Step Functions workflows
- `eventbridge.tf`: EventBridge rules
- `cloudwatch.tf`: CloudWatch dashboards and alarms
- `sns.tf`: SNS topics

**Acceptance Criteria**:
- `terraform plan` shows 0 changes after initial apply
- All resources tagged with: `Project=RideShare`, `Environment=dev/prod`, `ManagedBy=Terraform`
- State stored remotely in S3 with locking (DynamoDB)
- Modules used for reusable components

### 2. Event Producer Scripts

**Files**:
- `ride_event_producer.py`
- `driver_location_producer.py`
- `payment_producer.py`
- `rating_producer.py`
- `base_producer.py` (shared base class)

**Acceptance Criteria**:
- Generate realistic events based on probability distributions
- Batch 500 records per PutRecords call
- Retry on throttling with exponential backoff (3 retries, 1s, 2s, 4s)
- Logging with structured JSON format
- Configurable via environment variables or config file

### 3. Lambda Functions

**Functions**:
1. `ride_processor` - Process ride events
2. `driver_location_processor` - Update driver availability
3. `payment_processor` - Fraud detection and revenue aggregation
4. `rating_processor` - Update driver ratings
5. `aggregation_processor` - Daily batch aggregations
6. `data_quality_checker` - Quality validation

**Acceptance Criteria**:
- Each function <10 MB deployment package
- Appropriate timeout (30-60 seconds)
- Memory sized appropriately (512-1024 MB)
- Environment variables for configuration
- Logging with Lambda Powertools
- X-Ray tracing enabled
- Unit tests with >80% coverage

### 4. Kinesis Data Analytics SQL Applications

**Applications**:
1. `surge_pricing_calculator.sql` - 5-minute windows, demand/supply ratio
2. `real_time_metrics.sql` - 1-minute windows, KPIs
3. `hot_spots_detector.sql` - Geospatial clustering

**Acceptance Criteria**:
- Correct window definitions (TUMBLE, HOP, SESSION)
- Watermark handling for late arrivals (1-minute tolerance)
- Output to Kinesis streams or DynamoDB
- Checkpointing enabled for exactly-once semantics

### 5. Step Functions Workflows

**Workflows**:
1. `daily_aggregation_workflow.json` - Parallel processing of daily aggregates
2. `weekly_reporting_workflow.json` - Fan-out/fan-in pattern for reports

**Acceptance Criteria**:
- Visual workflow in Step Functions console
- Error handling: Catch, Retry with exponential backoff
- Parallel branches where appropriate
- SNS notifications on success/failure
- CloudWatch Logs integration

### 6. QuickSight Dashboards

**Dashboards**:
1. Operational Dashboard (real-time)
2. Executive Dashboard (daily trends)

**Acceptance Criteria**:
- Data sources connected (DynamoDB, Athena)
- Auto-refresh configured
- Responsive design (works on mobile)
- Role-based access control
- Export to PDF capability

### 7. Monitoring and Alerting

**CloudWatch Dashboards**:
1. System Health Dashboard
2. Business KPI Dashboard

**CloudWatch Alarms**:
- Lambda errors, duration, throttles
- Kinesis throughput, throttles
- DynamoDB throttles, latency
- Cost anomaly detection

**Acceptance Criteria**:
- All critical metrics represented
- Alarms have appropriate thresholds
- SNS topics configured
- Alarm test: Inject failure, verify alert received within 1 minute

### 8. Documentation

**Documents**:
1. README.md (overview, getting started)
2. PROJECT-BRIEF.md (this document)
3. IMPLEMENTATION-GUIDE.md (step-by-step instructions)
4. ARCHITECTURE-DECISIONS.md (ADRs for key decisions)
5. COST-ESTIMATION.md (cost breakdown and optimization)
6. docs/runbook.md (operational procedures)
7. docs/api-specifications.md (event schemas, APIs)

**Acceptance Criteria**:
- All documentation complete and accurate
- Architecture diagrams (text-based or images)
- Code comments for complex logic
- README includes setup instructions
- Runbook covers common scenarios

### 9. Test Suite

**Tests**:
- Unit tests for Lambda functions (pytest)
- Integration tests (end-to-end flows)
- Load tests (simulate 10x traffic)
- Chaos tests (inject failures)

**Acceptance Criteria**:
- >80% code coverage
- All tests pass in CI/CD pipeline
- Load tests validate scalability
- Chaos tests validate resilience

## Acceptance Criteria

### Functional Acceptance Criteria

| Criterion | Success Measure |
|-----------|----------------|
| **AC-1: Infrastructure Deployment** | `terraform apply` completes successfully in <30 minutes, all resources created |
| **AC-2: Event Ingestion** | Successfully ingest 1,000 events/second for 5 minutes with 0 throttling errors |
| **AC-3: Processing Latency** | P95 latency <5 seconds from event generation to DynamoDB write |
| **AC-4: Data Quality** | >95% completeness, >99% schema compliance, <1% invalid events |
| **AC-5: Dashboard Refresh** | Operational dashboard shows data <10 seconds old |
| **AC-6: Workflow Execution** | Daily aggregation workflow completes successfully on schedule |
| **AC-7: Alerting** | Inject error, alarm fires within 1 minute, SNS notification received |
| **AC-8: Cost** | Development environment cost <$80/month |

### Non-Functional Acceptance Criteria

| Criterion | Success Measure |
|-----------|----------------|
| **AC-9: Availability** | System uptime >99.9% over 30-day period |
| **AC-10: Scalability** | Handle 10x traffic spike (10,000 events/sec) without failures |
| **AC-11: Security** | All IAM roles follow least privilege, data encrypted at rest and in transit |
| **AC-12: Reliability** | <0.01% data loss rate, exactly-once processing |
| **AC-13: Maintainability** | All infrastructure in Terraform, code documented, test coverage >80% |
| **AC-14: Observability** | Comprehensive logs, metrics, and traces available in CloudWatch/X-Ray |

### Demonstration Scenarios

To prove your implementation meets requirements, demonstrate these scenarios:

#### Scenario 1: Real-Time Surge Pricing

**Setup**:
1. Simulate 1,000 ride requests in NYC within 1 minute (surge event)
2. Only 100 available drivers in that zone

**Expected Outcome**:
- Surge pricing calculator detects high demand within 5 minutes
- Surge multiplier increases from 1.0x to 2.5x
- New ride requests show updated pricing on operational dashboard within 10 seconds

#### Scenario 2: Fraud Detection

**Setup**:
1. Simulate suspicious ride: circular route, fare 3x higher than normal for distance

**Expected Outcome**:
- Payment processor flags ride as suspicious within 5 seconds
- Fraud alert appears on operational dashboard
- SNS notification sent to fraud team
- Ride marked for manual review in DynamoDB

#### Scenario 3: Driver Availability

**Setup**:
1. Simulate 1,000 driver location updates within 1 minute

**Expected Outcome**:
- Driver availability table updated in real-time
- Operational dashboard shows updated "Available Drivers" count within 10 seconds
- Geohashing enables fast location-based queries (<10ms)

#### Scenario 4: Workflow Orchestration

**Setup**:
1. Manually trigger daily aggregation workflow
2. Inject failure in one parallel branch

**Expected Outcome**:
- Workflow executes parallel branches
- Failed branch retries 3x with exponential backoff
- SNS notification sent on final failure
- Other branches complete successfully

#### Scenario 5: Load Testing

**Setup**:
1. Run load test: 10,000 events/second for 5 minutes (3M events)

**Expected Outcome**:
- Kinesis auto-scales (or on-demand mode handles load)
- Lambda auto-scales to match throughput
- DynamoDB auto-scales or on-demand mode handles writes
- No throttling errors, <0.01% data loss

## Security and Compliance

### Data Classification

| Data Type | Classification | Handling Requirements |
|-----------|---------------|----------------------|
| Ride coordinates | Sensitive | Encrypt at rest/transit, access logs |
| Customer/Driver PII | Highly Sensitive | Encrypt, mask in logs, strict access control |
| Payment information | PCI-DSS | Tokenize, never store full card numbers |
| GPS locations | Sensitive | Retention policy (30 days), encrypted |
| Ratings/Comments | Confidential | Encrypted, access logs |

### Security Requirements

#### Authentication and Authorization

- **IAM Roles**: All services use IAM roles (no API keys hardcoded)
- **Principle of Least Privilege**: Each Lambda function has minimal permissions
- **MFA**: Require MFA for administrative access
- **Service Control Policies**: Restrict regions, services (if using AWS Organizations)

#### Encryption

- **At Rest**: All data encrypted with AWS KMS
  - DynamoDB: AWS managed keys or customer-managed keys
  - S3: SSE-S3 or SSE-KMS
  - Kinesis: KMS encryption for streams
- **In Transit**: TLS 1.2+ for all data transfers
  - HTTPS for API calls
  - TLS for Kinesis PutRecords

#### Network Security

- **VPC**: Resources deployed in VPC where appropriate
- **Security Groups**: Least privilege ingress/egress rules
- **NACLs**: Network-level access control
- **VPC Endpoints**: S3, DynamoDB to avoid internet routing
- **Private Subnets**: Data stores in private subnets with no internet access

#### Secrets Management

- **AWS Secrets Manager**: Store API keys, database credentials
- **Automatic Rotation**: Rotate secrets every 90 days
- **No Hardcoded Secrets**: Enforce via pre-commit hooks and scanning

### Compliance

#### GDPR (General Data Protection Regulation)

- **Right to Access**: API to retrieve user data
- **Right to Erasure**: Mechanism to delete user data from all systems
- **Data Retention**: 7 days for GPS, 90 days for aggregates, 7 years for financial
- **Data Residency**: Store EU user data in EU regions (future requirement)

#### SOC 2 (Service Organization Control 2)

- **Audit Logging**: CloudTrail enabled for all API calls
- **Access Reviews**: Quarterly review of IAM permissions
- **Incident Response**: Documented runbooks for security incidents
- **Change Management**: All infrastructure changes via Terraform, PR reviews

#### HIPAA (Future Consideration)

If RideShare expands to medical transport:
- BAA (Business Associate Agreement) with AWS
- Encrypt PHI (Protected Health Information)
- Access logs and audits

### Data Retention and Lifecycle

| Data Type | Hot | Warm | Cold | Delete |
|-----------|-----|------|------|--------|
| Kinesis Streams | 24 hours | N/A | N/A | Auto-delete |
| DynamoDB (rides) | 7 days | N/A | N/A | TTL |
| DynamoDB (locations) | 24 hours | N/A | N/A | TTL |
| DynamoDB (metrics) | 30 days | N/A | N/A | TTL |
| S3 (raw events) | 30 days | 90 days (IA) | 7 years (Glacier) | After 7 years |
| CloudWatch Logs | 30 days | N/A | N/A | Auto-delete |

### Privacy

- **PII Masking**: Mask PII in CloudWatch Logs (e.g., email → e***@***.com)
- **Anonymization**: Consider hashing user_id for analytics (reversible with salt)
- **Data Access Logs**: Log all access to sensitive data (DynamoDB, S3)

## Timeline and Milestones

### Overall Timeline: 4 Weeks (25-30 hours)

#### Week 1: Infrastructure and Ingestion (7-8 hours)

**Phase 1: Infrastructure Setup** (2-3 hours)
- Day 1: Terraform setup, Kinesis streams, DynamoDB tables
- Day 2: Lambda functions scaffolding, IAM roles, S3 buckets

**Phase 2: Event Ingestion** (3-4 hours)
- Day 3: Event producer scripts (rides, locations)
- Day 4: Event producer scripts (payments, ratings), testing

**Milestone 1**: Successfully ingest 1,000 events/second to Kinesis

#### Week 2: Processing and Storage (8-9 hours)

**Phase 3: Stream Processing** (5-6 hours)
- Day 5: Lambda function - ride_processor
- Day 6: Lambda function - driver_location_processor
- Day 7: Lambda functions - payment_processor, rating_processor
- Day 8: Kinesis Data Analytics - surge pricing, real-time metrics

**Phase 4: State Management** (2-3 hours)
- Day 9: DynamoDB table designs, CRUD operations
- Day 10: DynamoDB Streams, indexing optimization

**Milestone 2**: Events processed and written to DynamoDB with <5s latency

#### Week 3: Orchestration and Quality (6-7 hours)

**Phase 5: Workflow Orchestration** (3-4 hours)
- Day 11: Step Functions - daily aggregation workflow
- Day 12: Step Functions - weekly reporting workflow, EventBridge schedules

**Phase 6: Data Quality** (2-3 hours)
- Day 13: JSON Schema validation, quality framework
- Day 14: Quality metrics, alerts

**Milestone 3**: Workflows execute successfully, data quality >95%

#### Week 4: Visualization and Production Readiness (4-6 hours)

**Phase 7: Visualization** (2-3 hours)
- Day 15: QuickSight operational dashboard
- Day 16: QuickSight executive dashboard

**Phase 8: Monitoring and Alerts** (1-2 hours)
- Day 17: CloudWatch dashboards, alarms, SNS notifications

**Phase 9: Optimization** (1-2 hours)
- Day 18: Performance tuning, cost optimization, load testing

**Milestone 4**: Production-ready system with dashboards and monitoring

### Milestones and Gates

| Milestone | Deliverables | Gate Criteria |
|-----------|--------------|---------------|
| **M1: Infrastructure Ready** | Terraform applies, resources created | All resources provisioned, no errors |
| **M2: Data Flowing** | Events ingested, processed, stored | 1,000 events/sec throughput, <5s latency |
| **M3: Workflows Operational** | Step Functions working, quality checks | Workflows execute successfully, quality >95% |
| **M4: Production Ready** | Dashboards live, monitoring active | All acceptance criteria met |

## Grading Rubric

### Total: 100 Points + 10 Bonus Points

#### 1. Infrastructure (25 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Terraform Configuration** | 10 | All resources defined, variables/outputs, state management |
| **Kinesis Streams** | 5 | 4 streams created, appropriate shard sizing, retention configured |
| **DynamoDB Tables** | 5 | 3 tables with correct schema, GSIs, capacity mode justified |
| **S3 Buckets** | 5 | Buckets for raw/processed/aggregates, lifecycle policies, encryption |

#### 2. Event Ingestion (15 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Event Producers** | 10 | 4 producers, realistic events, batching, retry logic |
| **Throughput** | 5 | 1,000 events/sec sustained, 0 throttling errors |

#### 3. Stream Processing (20 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Lambda Functions** | 12 | 4-6 functions, correct processing logic, error handling, idempotent |
| **Kinesis Data Analytics** | 8 | 3 SQL applications, correct windowing, joins, aggregations |

#### 4. Data Quality (10 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Schema Validation** | 4 | JSON Schemas defined, validation in Lambda |
| **Quality Checks** | 4 | Completeness, consistency, timeliness checks |
| **Monitoring** | 2 | Quality metrics dashboard, alerts |

#### 5. Workflow Orchestration (10 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Step Functions** | 6 | 2 workflows, parallel processing, error handling |
| **EventBridge** | 2 | Cron schedules, event patterns |
| **Notifications** | 2 | SNS topics, alerts working |

#### 6. Visualization (10 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **QuickSight Dashboards** | 8 | 2 dashboards, appropriate visualizations, auto-refresh |
| **Data Freshness** | 2 | Operational dashboard <10s latency |

#### 7. Documentation (10 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Code Documentation** | 3 | Comments, docstrings, README |
| **Architecture Docs** | 4 | Diagrams, data flow, ADRs |
| **Operational Docs** | 3 | Runbook, troubleshooting, setup instructions |

#### 8. Bonus Points (10 points)

| Enhancement | Points | Criteria |
|-------------|--------|----------|
| **Advanced Features** | 5 | ML-based fraud detection, multi-region, blue-green deployment |
| **Performance Optimization** | 3 | <2s P95 latency, caching, advanced tuning |
| **Cost Optimization** | 2 | 30%+ cost reduction, detailed attribution, forecasting |

### Grading Scale

- **90-100**: Excellent - Production-ready, professional quality
- **80-89**: Good - Solid implementation, minor gaps
- **70-79**: Satisfactory - Core functionality works, some issues
- **60-69**: Needs Improvement - Major functionality missing or broken
- **<60**: Incomplete - Does not meet minimum requirements

## Assumptions and Constraints

### Assumptions

1. **AWS Account**: You have an AWS account with sufficient permissions
2. **Budget**: $100/month budget for development and testing
3. **Data Volume**: Current scale (10M rides/month), not production scale
4. **Event Generation**: Simulated events (not real mobile apps)
5. **Time Commitment**: 25-30 hours over 4 weeks
6. **Prior Knowledge**: Completed modules 07-12
7. **Development Environment**: Local machine with Python 3.9+, Terraform, AWS CLI
8. **Single Region**: Deploy to single AWS region (us-east-1 recommended)
9. **Data Quality**: Simulated data has realistic distributions and relationships
10. **Third-Party Services**: Payment processors and mapping APIs simulated (not actual integrations)

### Constraints

1. **Cost**: Must stay within $80/month for development environment
2. **Timeline**: 4 weeks maximum
3. **Technology Stack**: Must use AWS services (as specified)
4. **Infrastructure as Code**: All resources must be in Terraform (no manual console clicks)
5. **Data Retention**: Limited to 7 days for hot data (production would be longer)
6. **Simplified Flows**: Some business logic simplified vs. real-world (e.g., surge pricing algorithm)
7. **No Mobile Apps**: Event generation simulated via Python scripts
8. **No Machine Learning**: Placeholder logic for fraud detection (future enhancement)
9. **Single Region**: No multi-region deployment (future enhancement)
10. **Limited Historical Data**: Only migrate 30 days of historical data for testing

### Out of Scope

The following are explicitly out of scope for this checkpoint:

1. **Mobile Application Development**: Event generation is simulated
2. **Machine Learning Models**: Fraud detection, demand forecasting use heuristics
3. **Multi-Region Deployment**: Active-active or disaster recovery across regions
4. **Advanced Security**: Beyond basic IAM, encryption (e.g., no WAF, Shield, GuardDuty)
5. **CI/CD Pipeline**: Manual deployment (production would use CI/CD)
6. **A/B Testing Framework**: For testing pricing strategies, UI changes
7. **Customer Portal**: For riders/drivers to view their data
8. **Admin Console**: For operations team (only dashboards)
9. **Historical Data Migration**: Beyond 30 days
10. **Production Support**: 24/7 on-call, SLA commitments

## Success Metrics

### Technical Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Event Ingestion Throughput | 1,000 events/sec | Load test script |
| Processing Latency (P95) | <5 seconds | End-to-end latency test |
| Data Quality Score | >95% | Quality validation script |
| Infrastructure Deployment Time | <30 minutes | `time terraform apply` |
| System Uptime | >99.9% | CloudWatch uptime dashboard |
| Lambda Error Rate | <0.5% | CloudWatch metrics |
| Cost (Dev Environment) | <$80/month | AWS Cost Explorer |

### Business Success Metrics (Simulated)

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Surge Pricing Accuracy | 60% optimal | 95% optimal | +58% |
| Fraud Detection Time | 24 hours | <5 seconds | 99.99% faster |
| Driver wait Time | 8.5 minutes | 5 minutes | 41% reduction |
| Customer Satisfaction | 4.2/5.0 | 4.5/5.0 | +7% |
| Revenue Capture | 85% potential | 98% potential | +15% |

### Learning Objectives Achievement

By completing this checkpoint, you should be able to:

- [ ] Design and implement real-time streaming architectures
- [ ] Use Kinesis Data Streams for event ingestion
- [ ] Build Lambda functions for stream processing
- [ ] Write Flink SQL for complex analytics
- [ ] Manage real-time state with DynamoDB
- [ ] Orchestrate workflows with Step Functions
- [ ] Build live dashboards with QuickSight
- [ ] Monitor and alert with CloudWatch
- [ ] Optimize for cost and performance
- [ ] Apply production best practices (IaC, testing, documentation)

## Appendices

### Appendix A: Event Schema Definitions

See `schemas/` directory for complete JSON Schema definitions:
- `ride_event.schema.json`
- `driver_location.schema.json`
- `payment_event.schema.json`
- `rating_event.schema.json`

### Appendix B: AWS Service Quotas

Ensure your AWS account has sufficient quotas:

| Service | Quota | Current Limit | Required |
|---------|-------|---------------|----------|
| Kinesis Shards per Region | 500 | 500 | 20 |
| Lambda Concurrent Executions | 1,000 | 1,000 | 500 |
| DynamoDB Tables per Region | 256 | 256 | 10 |
| S3 Buckets per Account | 100 | 100 | 10 |
| CloudWatch Alarms | 5,000 | 5,000 | 50 |

### Appendix C: Glossary

- **Event**: An immutable fact representing a state change (e.g., ride_requested)
- **Stream**: Ordered sequence of events (topic, queue)
- **Shard**: Partition of a Kinesis stream for parallel processing
- **Windowing**: Grouping events by time (tumbling, sliding, session)
- **Watermark**: Timestamp tracking event time progress for late arrival handling
- **Exactly-Once**: Processing semantics ensuring each event processed once (no duplicates or loss)
- **Idempotent**: Operation that produces same result if applied multiple times
- **Surge Pricing**: Dynamic pricing based on demand/supply ratio
- **DLQ**: Dead Letter Queue for failed events

### Appendix D: References

- [AWS Kinesis Best Practices](https://docs.aws.amazon.com/streams/latest/dev/best-practices.html)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Apache Flink SQL](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/overview/)

---

**Document End**

For implementation instructions, proceed to [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md).
