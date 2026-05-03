# Learning Resources for Advanced Data Architectures

## Table of Contents

1. [Essential Books](#essential-books)
2. [AWS Documentation](#aws-documentation)
3. [Online Courses](#online-courses)
4. [Research Papers](#research-papers)
5. [Blogs & Articles](#blogs--articles)
6. [Video Content](#video-content)
7. [Community Resources](#community-resources)
8. [AWS Certification Paths](#aws-certification-paths)
9. [Hands-on Labs](#hands-on-labs)
10. [Case Studies](#case-studies)

---

## Essential Books

### 1. **Designing Data-Intensive Applications** (Martin Kleppmann, 2017)

**Why Read**: The Bible of distributed data systems.

**Key Chapters**:
- Chapter 5: Replication (single-leader, multi-leader, leaderless)
- Chapter 6: Partitioning (sharding strategies, rebalancing)
- Chapter 7: Transactions (ACID, isolation levels, distributed transactions)
- Chapter 9: Consistency & Consensus (linearizability, CAP theorem)
- Chapter 11: Stream Processing (event sourcing, Lambda vs Kappa)

**Relevance to Module**:
- Lambda/Kappa architectures: Chapter 11
- Multi-region patterns: Chapters 5-6
- Event sourcing: Chapter 11
- CAP theorem: Chapter 9

**Level**: Advanced (requires CS fundamentals)
**Time**: 40-60 hours
**Price**: $40 (Kindle), $60 (paperback)
**Link**: https://dataintensive.net/

### 2. **Data Mesh** (Zhamak Dehghani, 2022)

**Why Read**: Written by the Data Mesh creator (Thoughtworks principal).

**Key Concepts**:
- Domain-oriented decentralization
- Data as a product thinking
- Self-serve data platform
- Federated computational governance

**Case Studies**:
- Thoughtworks client transformations
- Comparison: Centralized vs Mesh

**Relevance to Module**:
- Data Mesh patterns: Exercise 03
- Governance models: All exercises
- Organizational challenges

**Level**: Intermediate (less technical, more organizational)
**Time**: 20-30 hours
**Price**: $35 (Kindle), $50 (paperback)
**Link**: https://martinfowler.com/books/data-mesh.html

### 3. **Building Microservices** (Sam Newman, 2021 - 2nd Edition)

**Why Read**: Microservices foundation (applies to data services).

**Key Chapters**:
- Chapter 4: Communication Styles (sync vs async, events)
- Chapter 7: Build (CI/CD for microservices)
- Chapter 8: Deployment (blue-green, canary)
- Chapter 10: Resilience (circuit breakers, retries)
- Chapter 11: Monitoring & Observability

**Relevance to Module**:
- Event-driven patterns: Exercise 04
- Polyglot persistence: Exercise 06
- Resilience: All exercises

**Level**: Intermediate
**Time**: 30-40 hours
**Price**: $40 (Kindle)
**Link**: https://samnewman.io/books/building_microservices_2nd_edition/

### 4. **Streaming Systems** (Tyler Akidau et al., 2018)

**Why Read**: Written by Google engineers (creators of Dataflow).

**Key Concepts**:
- Event time vs processing time
- Watermarks (handle late data)
- Windowing (tumbling, sliding, session)
- Exactly-once semantics

**Relevance to Module**:
- Lambda architecture: Chapter 8
- Kappa architecture: Chapter 9
- Stream processing: Exercises 01-02

**Level**: Advanced
**Time**: 40 hours
**Price**: $50
**Link**: https://www.oreilly.com/library/view/streaming-systems/9781491983867/

### 5. **Big Data** (Nathan Marz, 2015)

**Why Read**: Lambda Architecture explained by the creator.

**Key Concepts**:
- Human fault tolerance principle
- Batch layer design
- Speed layer design
- Serving layer queries

**Relevance to Module**:
- Lambda architecture: Exercise 01
- Batch processing patterns

**Level**: Intermediate
**Time**: 20 hours
**Price**: $35
**Link**: https://www.manning.com/books/big-data

---

## AWS Documentation

### Architecture Guides

#### **AWS Well-Architected Framework**
https://aws.amazon.com/architecture/well-architected/

**Pillars**:
1. **Operational Excellence**: Monitoring, automation
2. **Security**: Encryption, least privilege
3. **Reliability**: Multi-region, disaster recovery
4. **Performance Efficiency**: Right-sizing, caching
5. **Cost Optimization**: Lifecycle policies, reserved capacity
6. **Sustainability**: Carbon footprint optimization (new in 2022)

**Relevance**: Apply to all architecture decisions.

#### **AWS Architecture Center**
https://aws.amazon.com/architecture/

**Sections**:
- **Reference Architectures**: 100+ diagrams with CloudFormation
- **This Is My Architecture**: Video series by AWS customers
- **AWS Solutions Library**: Pre-built architectures (deploy in 1 click)

**Recommended**:
- "Real-time Analytics Architecture"
- "Serverless Data Lake Architecture"
- "Multi-Region Active-Active Architecture"

### Service-Specific Guides

#### **DynamoDB Best Practices**
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html

**Topics**:
- Partition key design (avoid hot partitions)
- Sort key strategies (enable range queries)
- Global tables (multi-region)
- Streams (CDC pattern)
- DynamoDB Accelerator (DAX) for caching

**Time**: 4 hours
**Relevance**: Exercises 03-05

#### **Kinesis Best Practices**
https://docs.aws.amazon.com/streams/latest/dev/key-concepts.html

**Topics**:
- Shard calculation (`shards = MB_per_sec / 1_MB`)
- Resharding (split/merge shards)
- Record aggregation (reduce costs)
- Enhanced fan-out (2 MB/sec per consumer)

**Time**: 3 hours
**Relevance**: Exercises 01-02, 04-05

#### **Redshift Best Practices**
https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html

**Topics**:
- Distribution styles (KEY, ALL, EVEN)
- Sort keys (optimize range queries)
- Compression encodings (reduce storage 70%)
- Vacuum & Analyze (maintain performance)
- Workload Management (WLM) queues

**Time**: 5 hours
**Relevance**: Exercise 06, Lambda serving layer

---

## Online Courses

### 1. **AWS Skill Builder**: Advanced Architecting on AWS

**Link**: https://explore.skillbuilder.aws/learn/course/external/view/elearning/1296/advanced-architecting-on-aws

**Content** (3 days, 24 hours):
- Module 1: Account strategies (multi-account, Organizations)
- Module 2: Advanced networking (Transit Gateway, PrivateLink)
- Module 3: Deployment management (CodePipeline, blue-green)
- Module 4: Data stores (choosing right database, migration)
- Module 5: Scalability (auto-scaling, caching)
- Module 6: High availability (multi-region, disaster recovery)

**Cost**: $600 (instructor-led), Free (self-paced)
**Certification Prep**: Solutions Architect Professional

### 2. **Coursera**: Data Engineering on Google Cloud (specialization)

**Link**: https://www.coursera.org/specializations/gcp-data-engineering

**Why Google Cloud?**: Many patterns (Dataflow = Beam, Pub/Sub = Kafka, BigQuery = Redshift) applicable to AWS.

**Courses** (5 courses, 4 months):
1. Google Cloud Big Data and Machine Learning Fundamentals
2. Modernizing Data Lakes and Data Warehouses with GCP
3. Building Batch Data Pipelines on GCP
4. Building Resilient Streaming Analytics Systems on GCP
5. Smart Analytics, Machine Learning, and AI on GCP

**Cost**: $49/month (Coursera Plus), Free (audit mode)
**Certification**: Google Professional Data Engineer

### 3. **A Cloud Guru**: AWS Certified Solutions Architect Professional

**Link**: https://acloudguru.com/course/aws-certified-solutions-architect-professional

**Content** (30 hours):
- Multi-account strategies
- Hybrid architectures (Direct Connect, VPN)
- Migration strategies (6 R's: Rehost, Replatform, Refactor, etc.)
- High availability (Route 53, multi-region)
- Cost optimization

**Cost**: $49/month
**Certification Prep**: SA Pro (most difficult AWS cert)

---

## Research Papers

### 1. **Lambda Architecture (Nathan Marz, 2011)**

**Link**: http://nathanmarz.com/blog/how-to-beat-the-cap-theorem.html

**Summary**: Batch + Speed layers provide strong eventual consistency.

**Key Quote**:
> "The batch layer is the elephant in the room... but the elephant is actually the solution."

**Reading Time**: 30 minutes

### 2. **Kappa Architecture (Jay Kreps, 2014)**

**Link**: https://www.oreilly.com/radar/questioning-the-lambda-architecture/

**Summary**: Stream-only architecture eliminates batch layer complexity.

**Key Quote**:
> "Why maintain two systems when one will do?"

**Reading Time**: 20 minutes

### 3. **Data Mesh Principles (Zhamak Dehghani, 2019)**

**Link**: https://martinfowler.com/articles/data-mesh-principles.html

**Summary**: Decentralized sociotechnical approach to data architecture.

**Key Sections**:
- Domain ownership
- Data as a product
- Self-serve platform
- Federated governance

**Reading Time**: 45 minutes

### 4. **Eventual Consistency (Werner Vogels, 2008)**

**Link**: https://www.allthingsdistributed.com/2008/12/eventually_consistent.html

**Summary**: CTO of Amazon explains consistency trade-offs.

**Key Quote**:
> "There is a range of applications that can handle eventual consistency, and for those the benefits are real."

**Reading Time**: 30 minutes

### 5. **Dynamo: Amazon's Highly Available Key-value Store (2007)**

**Link**: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf

**Summary**: Academic paper describing DynamoDB's predecessor.

**Key Concepts**:
- Consistent hashing
- Vector clocks (conflict resolution)
- Quorum reads/writes (N, R, W)
- Gossip protocol

**Reading Time**: 2 hours (16 pages, dense)
**Level**: PhD-level distributed systems

---

## Blogs & Articles

### AWS Blogs

1. **AWS Big Data Blog**
   https://aws.amazon.com/blogs/big-data/
   **Topics**: Glue, EMR, Kinesis, Redshift
   **Frequency**: 3-4 articles/week
   **Subscription**: RSS feed available

2. **AWS Database Blog**
   https://aws.amazon.com/blogs/database/
   **Topics**: Aurora, DynamoDB, migration patterns
   **Relevance**: Exercise 05-06

3. **AWS Architecture Blog**
   https://aws.amazon.com/blogs/architecture/
   **Topics**: Reference architectures, case studies
   **Recommended**: "Multi-Region Application Architecture" series

### Personal Blogs

1. **Martin Kleppmann** (Author of DDIA)
   https://martin.kleppmann.com/
   **Deep Dives**: CRDTs, event sourcing, distributed transactions

2. **High Scalability**
   http://highscalability.com/
   **Topics**: Case studies (Netflix, Uber, Airbnb scale)
   **Format**: "X is Y" (e.g., "How Instagram scaled to 14M users with only 3 engineers")

3. **Netflix Tech Blog**
   https://netflixtechblog.com/
   **Topics**: Cassandra, microservices, chaos engineering
   **Recommended**: "Streaming data platform" series

---

## Video Content

### AWS re:Invent Sessions

**Link**: https://www.youtube.com/c/AWSEventsChannel

**Recommended Sessions**:

1. **DAT401: Amazon DynamoDB Deep Dive** (2023)
   - Global tables architecture
   - Conflict resolution strategies
   - Performance optimization
   **Time**: 60 minutes

2. **ANT346: Advanced Architectures for Multi-Region Applications** (2022)
   - Route 53 routing policies
   - Aurora global database
   - Cross-region disaster recovery
   **Time**: 60 minutes

3. **DAT323: Building Streaming Data Platforms with Kappa Architecture** (2021)
   - Kinesis vs MSK comparison
   - Flink on Kinesis Analytics
   - Reprocessing patterns
   **Time**: 45 minutes

### Tech Company Engineering Blogs

1. **Uber Engineering**
   https://www.youtube.com/@UberEngineering
   **Topics**: Data platform evolution, Kafka at scale

2. **Netflix Engineering**
   https://www.youtube.com/c/NetflixOpenSource
   **Topics**: Microservices, chaos engineering, data platform

---

## Community Resources

### Forums

1. **AWS re:Post**
   https://repost.aws/
   **Description**: Official AWS Q&A (replaced forums)
   **Activity**: 1,000+ questions/day
   **Response Time**: <24 hours for most questions

2. **Stack Overflow**
   https://stackoverflow.com/questions/tagged/amazon-web-services
   **Tags**: `amazon-dynamodb`, `amazon-kinesis`, `aws-lambda`, `apache-spark`
   **Questions**: 400K+ AWS-related

3. **Reddit**
   - r/aws (300K members)
   - r/dataengineering (180K members)
   - r/bigdata (50K members)

### Slack/Discord Communities

1. **Data Engineering Discord**
   https://discord.gg/dataengineering
   **Members**: 10K+
   **Channels**: #architecture, #aws, #streaming, #lakehouse

2. **Locally Optimistic (Data Slack)**
   http://locallyoptimistic.com/community/
   **Members**: 8K+ data professionals
   **Channels**: Technical discussions, career advice

---

## AWS Certification Paths

### For This Module

#### **AWS Certified Solutions Architect – Professional**

**Exam Code**: SAP-C02
**Cost**: $300
**Duration**: 180 minutes
**Questions**: 75 (scenario-based, complex)
**Passing Score**: 750/1000

**Domains**:
1. Design for Organizational Complexity (26%)
   - Multi-account strategies
   - Hybrid architectures

2. Design for New Solutions (29%)
   - Architecture patterns ← **This Module**
   - Database selection

3. Continuous Improvement (25%)
   - Migration strategies
   - Performance optimization

4. Accelerate Workload Migration (20%)
   - Data migration (DMS, Snowball)

**Study Plan**:
- **Prerequisites**: Solutions Architect Associate (SAA-C03)
- **Study Time**: 100-150 hours
- **Practice Exams**: AWS Skill Builder (official), Tutorials Dojo
- **Hands-on**: 6-12 months AWS experience recommended

**Overlap with Module 18**: ~60%
- Lambda/Kappa architectures
- Multi-region patterns
- Database selection (polyglot)
- Event-driven architectures

#### **AWS Certified Data Engineer – Associate**

**Exam Code**: DEA-C01 (NEW - released November 2023)
**Cost**: $150
**Duration**: 170 minutes
**Questions**: 85
**Passing Score**: 720/1000

**Domains**:
1. Data Ingestion and Transformation (34%)
   - Kinesis, Glue, EMR
   - Batch vs streaming

2. Data Store Management (26%)
   - S3, DynamoDB, Redshift, Athena
   - Partitioning, optimization

3. Data Operations and Support (22%)
   - Monitoring, troubleshooting
   - Security, compliance

4. Data Security and Governance (18%)
   - Encryption, Lake Formation
   - Data quality, lineage

**Study Plan**:
- **Prerequisites**: Cloud Practitioner (helpful, not required)
- **Study Time**: 60-80 hours
- **Practice Exams**: AWS Skill Builder, Udemy
- **Hands-on**: Complete Modules 05-18

**Overlap with Module 18**: ~40%
- Architecture patterns (high-level)
- Service selection
- Security best practices

---

## Hands-on Labs

### AWS Workshops

1. **Serverless Data Lake Workshop**
   https://catalog.workshops.aws/serverless-data-lake/en-US
   **Time**: 4 hours
   **Topics**: S3, Glue, Athena, QuickSight
   **Cost**: Free (AWS Free Tier)
   **Relevance**: Lambda batch layer

2. **Streaming Data Workshop**
   https://catalog.workshops.aws/real-time-streaming/en-US
   **Time**: 3 hours
   **Topics**: Kinesis, Flink, Lambda
   **Cost**: ~$10 (past Free Tier)
   **Relevance**: Kappa architecture, speed layer

3. **Multi-Region Workshop**
   https://disaster-recovery.workshop.aws/
   **Time**: 5 hours
   **Topics**: Aurora global, Route 53, active-active
   **Cost**: ~$20
   **Relevance**: Exercise 05

### Qwiklabs (Hands-on Labs)

**Link**: https://www.qwiklabs.com/

**Recommended Quests**:
1. **Data Engineering on AWS** (10 labs, 12 hours)
2. **Serverless Architecture on AWS** (8 labs, 10 hours)
3. **Advanced Solutions Architect** (12 labs, 16 hours)

**Cost**: $55/month (unlimited labs)
**Benefit**: Real AWS environment (no credit card needed)

---

## Case Studies

### Netflix: Petabyte-Scale Streaming

**Link**: https://netflixtechblog.com/keystone-real-time-stream-processing-platform-a3ee651812a

**Architecture**:
- Kafka: Backbone (1 trillion events/day)
- Flink: Stream processing
- Druid: Real-time OLAP
- S3: Data lake (100 PB)

**Scale Numbers**:
- 200M subscribers
- 1 trillion events/day
- <100ms personalization latency
- 99.99% uptime

**Key Learnings**:
- Lambda architecture at scale
- Chaos engineering (Chaos Monkey)
- Auto-remediation (self-healing)

**Reading Time**: 30 minutes

### Uber: Data Mesh Journey

**Link**: https://www.uber.com/blog/ubers-journey-toward-better-data-culture-from-first-principles/

**Evolution**:
1. **2013**: Centralized data team (Hadoop)
2. **2016**: Data platform team (Hive, Presto)
3. **2019**: Data mesh (domain ownership)

**Results**:
- 10x data teams (100 → 1,000 engineers)
- 70% faster feature development
- 50% cost optimization (right-sized resources)

**Key Learnings**:
- Migration took 3 years
- Cultural change harder than technical
- Governance critical for success

**Reading Time**: 45 minutes

### Airbnb: Minerva Data Platform

**Link**: https://medium.com/airbnb-engineering/how-airbnb-democratized-data-science-with-data-university-3eccc71e073a

**Architecture**:
- S3: Data lake (100 PB)
- Presto: SQL engine (10K queries/day)
- Airflow: Orchestration (10K+ DAGs)
- Apache Hudi: Lakehouse (ACID)

**Scale**:
- 150M users
- 6M listings
- 100 PB data
- 1,000+ data engineers

**Key Learnings**:
- Lakehouse > separate lake + warehouse
- Self-service >> gated access
- Data quality critical for trust

**Reading Time**: 30 minutes

### LinkedIn: Espresso Multi-Datacenter

**Link**: https://engineering.linkedin.com/espresso/introducing-espresso-linkedins-hot-new-distributed-document-store

**Architecture**:
- 6 datacenters (active-active)
- Timeline consistency (eventual with ordering)
- 100K queries/sec
- <100ms global latency

**Key Learnings**:
- Active-active > active-passive (better latency)
- Timeline consistency practical middle ground
- Custom conflict resolution needed

**Reading Time**: 40 minutes

---

## AWS Certification Paths

### Recommended Path for Data Engineers

```
Level 1: Foundational
├─ AWS Certified Cloud Practitioner (CLF-C02)
│  Time: 40 hours, Cost: $100
│  ↓
Level 2: Associate
├─ AWS Certified Solutions Architect Associate (SAA-C03)
│  Time: 80 hours, Cost: $150
│  ↓
├─ AWS Certified Data Engineer Associate (DEA-C01) ← NEW!
│  Time: 60 hours, Cost: $150
│  ↓
Level 3: Professional
├─ AWS Certified Solutions Architect Professional (SAP-C02)
│  Time: 150 hours, Cost: $300 ← **Best for Module 18**
│  ↓
Level 4: Specialty (Optional)
├─ AWS Certified Database Specialty (DBS-C01)
│  Time: 80 hours, Cost: $300
```

### Study Resources per Certification

#### **Solutions Architect Professional**

**Books**:
- "AWS Certified Solutions Architect Official Study Guide" (Sybex)

**Courses**:
- A Cloud Guru: 30 hours
- Udemy (Stephane Maarek): 25 hours

**Practice Exams**:
- Tutorials Dojo: $15 (6 practice exams, 390 questions)
- AWS Skill Builder: Free (1 official practice exam)

**Tips**:
- Focus on hybrid architectures (on-premise + cloud)
- Master multi-region patterns (Route 53, global databases)
- Practice designing for 100K+ users, PB-scale data

#### **Data Engineer Associate**

**Courses**:
- AWS Skill Builder: "Exam Prep Standard Course" (16 hours, free)
- Udemy: Multiple courses ($15-30)

**Practice Exams**:
- Tutorials Dojo: $15

**Tips**:
- Heavy on Glue, EMR, Kinesis, Redshift
- Security: Lake Formation, encryption, IAM
- Focus on cost optimization (S3 storage classes, Spot instances)

---

## Comparison: AWS vs Azure vs GCP

| Service Category | AWS | Azure | GCP | Notes |
|------------------|-----|-------|-----|-------|
| **Object Storage** | S3 | Blob Storage | Cloud Storage | All similar |
| **Data Warehouse** | Redshift | Synapse | BigQuery | BigQuery serverless |
| **NoSQL** | DynamoDB | Cosmos DB | Firestore/Bigtable | Cosmos multi-model |
| **Streaming** | Kinesis | Event Hubs | Pub/Sub | Kafka alternative |
| **Stream Processing** | Kinesis Analytics | Stream Analytics | Dataflow | Flink vs Beam |
| **Batch Processing** | EMR/Glue | HDInsight/Databricks | Dataproc | Spark on all |
| **Data Catalog** | Glue Catalog | Purview | Data Catalog | Purview most advanced |

**Multi-Cloud Strategy**:
- Use Terraform (infrastructure as code) for portability
- Adopt open formats (Parquet, Avro) over proprietary
- Abstract cloud SDKs with wrapper libraries

---

## Advanced Topics (Beyond This Module)

### 1. **CRDT (Conflict-Free Replicated Data Types)**

**Problem**: Multi-region writes without conflicts.

**Solution**: Data structures that mathematically converge.

**Example**: G-Counter (increment-only counter)

```python
# US increments by 3
us_counter = {"us": 3, "eu": 0}

# EU increments by 2
eu_counter = {"us": 0, "eu": 2}

# Merge (max per region)
merged = {"us": 3, "eu": 2}
final_count = sum(merged.values())  # = 5 (correct!)
```

**Learn More**:
- "CRDTs: Consistency without concurrency control" (Shapiro et al., 2011)
- https://crdt.tech/

### 2. **Data Vault 2.0**

**Problem**: Traditional star schema too rigid for Agile.

**Solution**: Three table types: Hubs (business keys), Links (relationships), Satellites (attributes).

**Use Case**: Enterprise data warehouses with frequent changes.

**Learn More**:
- "Building a Scalable Data Warehouse with Data Vault 2.0" (Linstedt & Olschimke)

### 3. **Reverse ETL**

**Problem**: Analytics data stuck in warehouse, not actionable.

**Solution**: Sync warehouse → operational tools (Salesforce, Marketo).

**Example**:
```
Redshift (customer segments) → Census/Hightouch → Salesforce (targeted campaigns)
```

**Tools**: Census, Hightouch, Fivetran (reverse mode)

---

## Learning Path Recommendations

### For Beginners (0-1 year experience)

1. ✅ Complete Modules 01-10 (fundamentals)
2. ✅ Read "Designing Data-Intensive Applications" (Chapters 1-4)
3. ✅ AWS Certified Cloud Practitioner cert
4. ✅ Build 1 project (e.g., "Real-time dashboard with Kinesis + Lambda")

### For Intermediate (1-3 years)

1. ✅ Complete Modules 11-17
2. ✅ Read DDIA (Chapters 5-12)
3. ✅ AWS Solutions Architect Associate cert
4. ✅ AWS Data Engineer Associate cert
5. ✅ Build 2-3 projects (Lambda architecture, Data Mesh POC)

### For Advanced (3+ years) ← **This Module**

1. ✅ Complete Module 18
2. ✅ Read "Data Mesh" (Dehghani)
3. ✅ AWS Solutions Architect Professional cert
4. ✅ Contribute to open source (Apache Spark, Flink, etc.)
5. ✅ Design architecture for 1M+ users, PB-scale data

---

## Practice Projects (Beyond Exercises)

### Project 1: Build Netflix Recommendations Clone

**Architecture**: Lambda (batch collaborative filtering + real-time session)

**Technologies**:
- Batch: EMR with Spark MLlib (collaborative filtering)
- Speed: Kinesis + Lambda (session tracking)
- Serving: DynamoDB (user recommendations) + ElastiCache (movie metadata)

**Scale**: 10K users, 100K movies, 1M ratings

**Time**: 40 hours

### Project 2: Build Uber-like Data Mesh

**Architecture**: 3 domains (Rides, Drivers, Payments)

**Technologies**:
- Platform: S3 + Glue + Athena
- API: FastAPI (data product endpoints)
- Governance: Glue Schema Registry + Lake Formation

**Scale**: 1K drivers, 10K rides/day

**Time**: 50 hours

### Project 3: Build Trading Platform (Event Sourcing)

**Architecture**: Event-sourced with CQRS

**Technologies**:
- Event Store: DynamoDB (immutable trades)
- Command: Lambda (place trade, cancel trade)
- Query: ElastiCache (portfolio summary), Redshift (historical analysis)

**Scale**: 1K users, 10K trades/day

**Time**: 60 hours

---

## Industry Trends (2026)

### 1. **Streaming-First**

Companies moving from batch → streaming:
- **Why**: Real-time insights competitive advantage
- **Challenge**: Team skills (batch easier than streaming)
- **Solution**: Managed services (Kinesis, MSK) reduce complexity

### 2. **Lakehouse > Data Warehouse**

Unified platform for batch + streaming + ML:
- **Winners**: Databricks, Snowflake, Delta Lake
- **Losers**: Traditional data warehouses (Teradata, Netezza)
- **AWS Strategy**: S3 + Glue + Athena (open lakehouse)

### 3. **Data Mesh Adoption**

Enterprise-scale data organizations:
- **Adopters**: Uber, Netflix, Airbnb, Intuit
- **Challenge**: Cultural change (decentralization)
- **Timeline**: 2-3 years for full migration

### 4. **Serverless Everything**

Shift from managed systems → serverless:
- **From**: EMR (manage clusters) → **To**: Glue (serverless Spark)
- **From**: RDS (patch OS) → **To**: Aurora Serverless v2 (auto-scale)
- **From**: OpenSearch (size cluster) → **To**: OpenSearch Serverless

**Benefits**: Pay-per-use, zero management, auto-scaling
**Trade-off**: Less control (can't tune deep settings)

### 5. **AI/ML Integration**

Data platforms becoming ML platforms:
- **Feature Stores**: SageMaker Feature Store (online + offline)
- **Model Endpoints**: SageMaker (deploy models as APIs)
- **MLOps**: CI/CD for ML models (train → test → deploy)

**Example**: Build recommendations (Spark batch features) + serve via SageMaker.

---

## Recommended Reading Order

### Week 1: Foundations
- [ ] Read concepts.md (this module)
- [ ] Read architecture.md (this module)
- [ ] Watch "DynamoDB Deep Dive" (re:Invent session)
- [ ] Complete Exercise 01 (hands-on)

### Week 2: Streaming
- [ ] Read "Streaming Systems" (Chapters 1-3)
- [ ] Watch "Kappa Architecture" (re:Invent session)
- [ ] Complete Exercises 02-03
- [ ] Build practice project 1 (recommendations)

### Week 3: Distributed Systems
- [ ] Read DDIA (Chapters 5-7: Replication, Partitioning, Transactions)
- [ ] Read "Eventual Consistency" (Vogels paper)
- [ ] Complete Exercises 04-05
- [ ] Experiment with conflict resolution

### Week 4: Advanced
- [ ] Read "Data Mesh" (full book)
- [ ] Complete Exercise 06
- [ ] Build practice project 2 (Data Mesh POC)
- [ ] Take practice exams (SA Pro or Data Engineer)

### Week 5: Certification (Optional)
- [ ] Review AWS re:Invent sessions (10-15 videos)
- [ ] Take 3-4 practice exams
- [ ] Schedule certification exam
- [ ] Pass exam! 🎉

---

## Getting Help

### When Stuck on Exercises

1. **Check Solution Guide**: `exercises/XX/solution.md` (hints, not full code)
2. **AWS Documentation**: Search for specific service docs
3. **AWS re:Post**: Ask question with code sample
4. **Stack Overflow**: Search AWS tag + error message
5. **Module Slack**: Ask in #module-18 channel

### When Debugging Production Issues

1. **CloudWatch Logs**: Search for error messages
2. **X-Ray**: Trace request to find bottleneck
3. **AWS Support**: Open ticket (if Business/Enterprise support)
4. **AWS re:Post**: Describe issue with architecture diagram
5. **Disaster Recovery Plan**: Have rollback strategy ready

---

## Summary: Must-Read Resources

**Books** (Priority Order):
1. ⭐⭐⭐ Designing Data-Intensive Applications (Kleppmann)
2. ⭐⭐ Streaming Systems (Akidau)
3. ⭐⭐ Data Mesh (Dehghani)

**Papers** (Priority Order):
1. ⭐⭐⭐ Lambda Architecture (Marz)
2. ⭐⭐ Kappa Architecture (Kreps)
3. ⭐⭐ Data Mesh Principles (Dehghani)

**Videos** (Priority Order):
1. ⭐⭐⭐ AWS re:Invent: DynamoDB Deep Dive
2. ⭐⭐ AWS re:Invent: Multi-Region Architectures
3. ⭐⭐ Netflix Tech Talk: Streaming Platform

**Hands-on** (Priority Order):
1. ⭐⭐⭐ Complete all 6 exercises in this module
2. ⭐⭐ AWS Workshops (Serverless Data Lake, Streaming)
3. ⭐ Build 1 practice project (recommendations or trading platform)

**Total Time Investment**: 200-300 hours (including exercises, reading, certification)

---

**Next**: Begin Exercise 01 - Lambda Architecture Implementation.
