# Scenario: Cost Optimization & Resilience at QuickMart

## 📊 Business Context

QuickMart's data platform is growing fast:

- **10 TB** of application logs stored in S3 STANDARD
- **$230/month** in storage costs for historical logs
- **90% of logs** never accessed after 30 days
- **No backup strategy** for critical data
- **Manual processing** of uploaded files (no automation)

**CEO's Directive:** "Reduce storage costs by 60% while improving resilience"

## 🎯 Your Mission

You're tasked with implementing AWS S3 advanced features:

### 1. Cost Optimization (Lifecycle Policies)

**Problem:** Historical logs in expensive STANDARD storage

**Solution:**
- Keep recent data (0-30 days) in STANDARD for fast access
- Move warm data (30-90 days) to STANDARD_IA (50% cheaper)
- Archive cold data (90-365 days) to GLACIER (83% cheaper)
- Delete data older than 365 days (compliance requirement)

**Expected Savings:**
```
Current: 10 TB × $0.023/GB × 12 months = $2,820/year
After optimization:
  - 1 TB in STANDARD (0-30 days): $282/year
  - 2 TB in STANDARD_IA (30-90 days): $307/year
  - 7 TB in GLACIER (90-365 days): $344/year
Total: $933/year → 67% savings ✅
```

### 2. Disaster Recovery (Replication)

**Problem:** Single point of failure, no geographic redundancy

**Solution:**
- Enable versioning (protect against accidental deletion)
- Configure Cross-Region Replication to backup bucket
- Ensure business-critical data (financial, customer) is replicated

**RTO/RPO Targets:**
- Recovery Time Objective: < 1 hour
- Recovery Point Objective: < 5 minutes

### 3. Event-Driven Processing (Notifications)

**Problem:** Manual checking for new files, delayed processing

**Solution:**
- Configure S3 Event Notifications → SQS
- Lambda functions trigger automatically on upload
- Real-time processing pipeline

**Use Cases:**
```
uploads/transactions/*.csv → SQS → Lambda → Validate & Load to DB
uploads/images/*.jpg → SQS → Lambda → Resize & OCR
logs/*.json → SQS → Lambda → Parse & Send to CloudWatch
```

## 🗂️ Data Structure

```
s3://my-data-lake-raw/
├── transactions/
│   ├── 2024-01-15.csv (accessed daily)
│   ├── 2023-12-15.csv (accessed weekly)
│   └── 2023-09-15.csv (rarely accessed) ← Move to GLACIER
├── logs/
│   ├── app/2024-01-15.json (recent)
│   └── app/2023-10-01.json (old) ← Move to STANDARD_IA
└── uploads/
    └── incoming/*.* (real-time processing needed) ← Event notification
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        S3 my-data-lake-raw                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ STANDARD   │→│ STANDARD_IA │→│   GLACIER   │→ Expired  │
│  │  (30 days) │ │  (60 days)  │ │ (275 days)  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│         │              Versioning Enabled                   │
│         ├──────────────────────────────────────────┐        │
│         │                Replication                │        │
│         ▼                                           ▼        │
│  ┌─────────────┐                          ┌────────────────┐│
│  │ SQS Queue   │                          │ Backup Bucket  ││
│  │ s3-events   │                          │ (us-west-1)    ││
│  └──────┬──────┘                          └────────────────┘│
│         │ ObjectCreated:*                                    │
│         ▼                                                    │
│  ┌─────────────┐                                            │
│  │ Lambda Fn   │                                            │
│  │ Processor   │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Acceptance Criteria

### Versioning
- [x] Versioning enabled on main bucket
- [x] Upload same file 3 times → 3 versions exist
- [x] Delete object → can recover from version history

### Lifecycle
- [x] Lifecycle policy with 3 transitions (STANDARD → IA → GLACIER)
- [x] Expiration rule for 365+ day old objects
- [x] Policy applied to `/logs/` and `/transactions/` prefixes
- [x] Verify with `get-bucket-lifecycle-configuration`

### Replication
- [x] Backup bucket created in different region
- [x] Replication rule configured for critical paths
- [x] Upload file to source → appears in backup within seconds
- [x] IAM role with `s3:ReplicateObject` permission

### Event Notifications
- [x] SQS queue created with correct policy
- [x] Bucket notification configured for `ObjectCreated:*`
- [x] Upload file → SQS receives message with S3 metadata
- [x] Message includes: bucket, key, size, timestamp

## 🧪 Test Scenarios

### Test 1: Versioning Protection
```bash
# Simulate accidental deletion
echo "important data" > critical.txt
aws s3 cp critical.txt s3://my-data-lake/critical.txt
aws s3 rm s3://my-data-lake/critical.txt

# Recovery
aws s3api list-object-versions --bucket my-data-lake --prefix critical.txt
# Should show DeleteMarker + previous version
# Restore by copying previous version
```

### Test 2: Lifecycle Simulation
```python
# In production, this takes 30+ days
# LocalStack: verify policy exists
lifecycle = s3.get_bucket_lifecycle_configuration(Bucket='my-data-lake')
assert len(lifecycle['Rules']) >= 1
assert any(r['Status'] == 'Enabled' for r in lifecycle['Rules'])
```

### Test 3: Replication
```bash
# Upload to source
echo "test" > test.txt
aws s3 cp test.txt s3://my-data-lake-raw/test.txt

# Verify in backup (may take 5-10 seconds in LocalStack)
sleep 10
aws s3 ls s3://my-data-lake-backup/test.txt
```

### Test 4: Event Notification
```bash
# Upload triggers event
aws s3 cp file.txt s3://my-data-lake-raw/uploads/file.txt

# Check SQS
aws sqs receive-message --queue-url http://localhost:4566/000000000000/s3-events
# Should return message with eventName: "ObjectCreated:Put"
```

## 💰 Cost Analysis

### Before Optimization
```
Storage:
  10,000 GB × $0.023/GB = $230/month

Requests:
  1M PUT/POST: $5.50
  10M GET: $4.00

Total: ~$240/month
```

### After Optimization
```
Storage:
  1,000 GB STANDARD: $23/month
  2,000 GB STANDARD_IA: $25/month
  7,000 GB GLACIER: $28/month

Total: ~$76/month (68% savings!)
```

**Additional Benefits:**
- Disaster recovery: Priceless 😊
- Automated processing: 10x faster
- Versioning: Compliance requirement met

## 🎓 Learning Outcomes

After completing this scenario, you will:

✅ Understand storage class economics
✅ Implement cost-effective lifecycle policies
✅ Configure disaster recovery with replication
✅ Build event-driven architectures with S3+SQS
✅ Design for resilience and compliance
✅ Calculate ROI of cloud optimization

---

**Ready to start?** Head to [README.md](../README.md) for implementation steps!
