# 💰 COST ALERT: Databricks Lakehouse Platform

**Last Updated:** March 2026

## 🎁 Free Options Summary

| Option | Cost | Features | Limitations | Best For |
|--------|------|----------|-------------|----------|
| **Community Edition** | **FREE** | Basic Databricks, single-node Spark, notebooks | No Unity Catalog, no Workflows, 15GB storage | Learning basics |
| **14-Day Trial** | **FREE** (credit card required) | Full platform access | Expires after 14 days, auto-cancels | Production-like experience |
| **Academy Labs** | **FREE** | Pre-configured environments | Time-limited sessions (4 hours) | Structured courses |

## ✅ Recommended Approach for This Module

### For Learning (Budget: $0)
**Use Community Edition**
- ✅ Sufficient for Exercises 01, 02, 04, 05, 06
- ✅ No credit card required
- ✅ Unlimited time
- ❌ Cannot complete Exercise 03 (Unity Catalog)

### For Complete Experience (Budget: $0-25)
**Use 14-Day Trial**
- ✅ All exercises including Unity Catalog
- ✅ Workflows, SQL Analytics, full ML features
- ✅ Auto-cancels after trial (no charges)
- 💡 **Pro Tip:** Complete module within 14 days

## 💳 Databricks Pricing Breakdown

### DBU (Databricks Unit) Model

Databricks charges in **DBU** (Databricks Units) + **Cloud Provider costs** (EC2/Azure VMs).

**1 DBU ≈ $0.07 - 0.75** depending on:
- Workload type (All-Purpose, Jobs, SQL, ML)
- Instance size
- Cloud provider (AWS, Azure, GCP)

### Price Examples (AWS us-east-1)

| Cluster Type | DBU Rate | EC2 Cost | Total Cost | Use Case |
|--------------|----------|----------|------------|----------|
| **Jobs Compute** (m5.xlarge) | $0.15/DBU | $0.192/hour | ~$0.22/hour | Scheduled ETL |
| **All-Purpose** (m5.xlarge) | $0.40/DBU | $0.192/hour | ~$0.67/hour | Interactive development |
| **SQL Compute** (2X-Small) | $0.22/DBU | Included | $0.44/hour | SQL dashboards |
| **ML Compute** (m5.xlarge) | $0.40/DBU | $0.192/hour | ~$0.67/hour | Model training |

**DBU Consumption Rate:**
- 1 DBU consumed per hour per node
- Multi-node cluster: DBUs multiply by node count

### Real-World Cost Examples

#### Example 1: Learning This Module (Community Edition)
```
Cost: $0/month
Cluster: Single-node (built-in)
Hours: Unlimited
Features: Basic notebooks, Delta Lake, Spark SQL
Limitation: No Unity Catalog, no multi-node
```

#### Example 2: Complete This Module (14-Day Trial)
```
Trial Credits: ~$400 (typical)
Expected Usage: $20-50 for entire module
Hours: ~15 hours of interactive work
Cluster: 1 x m5.xlarge All-Purpose
Cost per hour: ~$0.67
Total: ~$10 (well within trial credits)

Breakdown:
- 15 hours × $0.67 = $10.05
- SQL queries: Minimal (included)
- Storage (S3): ~$0.50
- Total: ~$11
```

#### Example 3: Production Workload (Monthly)
```
Use Case: Medium-sized data platform
ETL Jobs: 50 hours/month × $0.22/hour = $11
Interactive Dev: 100 hours/month × $0.67/hour = $67
SQL Analytics: 100 hours/month × $0.44/hour = $44
Storage (S3): 1TB × $0.023/GB = $23
Data Transfer: Minimal = $5
Monthly Total: ~$150

With optimization:
- Use Jobs Compute (cheaper than All-Purpose)
- Auto-terminate clusters after 30 min idle
- Use Spot instances (70% discount on EC2)
Optimized: ~$75/month
```

## 🛡️ How to Avoid Unexpected Charges

### ⚠️ Common Cost Traps

1. **Forgetting to terminate clusters**
   - **Risk:** $0.67/hour × 24 hours × 30 days = $482/month
   - **Solution:** Auto-termination after 20-30 minutes

2. **Using All-Purpose for scheduled jobs**
   - **Risk:** 2.5x more expensive than Jobs Compute
   - **Solution:** Use Workflows with Jobs Compute

3. **Large multi-node clusters for small data**
   - **Risk:** 10 nodes × $0.67 = $6.70/hour
   - **Solution:** Start with 2-3 nodes, scale up only if needed

4. **Idle SQL endpoints**
   - **Risk:** $0.44/hour even when not queried
   - **Solution:** Auto-stop after 30 minutes

5. **Not canceling trial**
   - **Risk:** Auto-converts to paid (though rare now)
   - **Solution:** Cancel in account settings before day 14

### ✅ Cost Optimization Strategies

#### 1. Enable Auto-Termination
```python
# In cluster configuration
{
  "autotermination_minutes": 30,  # Terminate after 30 min idle
  "spark_conf": {
    "spark.databricks.delta.preview.enabled": "true"
  }
}
```

#### 2. Use Spot Instances (70% discount)
```python
# AWS Spot instances for Jobs Compute
{
  "aws_attributes": {
    "availability": "SPOT",
    "spot_bid_price_percent": 100
  }
}
```

#### 3. Right-Size Clusters
```
Small data (<10GB): Single-node or 2 workers
Medium data (10-100GB): 2-5 workers
Large data (>100GB): 5-20 workers

Don't over-provision!
```

#### 4. Use Jobs Compute for Pipelines
```
All-Purpose: Interactive development only
Jobs Compute: Scheduled ETL, batch processing (60% cheaper)
```

#### 5. Monitor Spend
```python
# Check cluster usage
%sql
SELECT
  cluster_name,
  SUM(total_time_sec) / 3600 as hours_used,
  hours_used * 0.67 as estimated_cost_usd
FROM system.compute.clusters
WHERE start_time >= current_date() - INTERVAL 7 DAYS
GROUP BY cluster_name
ORDER BY estimated_cost_usd DESC;
```

## 📊 Cost Comparison: Databricks vs AWS Native

### Scenario: 100GB daily ETL + 500GB data lake

| Solution | Monthly Cost | Setup Complexity | Performance |
|----------|--------------|------------------|-------------|
| **Databricks** | $150-300 | ⭐⭐⭐⭐⭐ Low | ⭐⭐⭐⭐⭐ Excellent |
| **AWS EMR** | $100-200 | ⭐⭐⭐ Medium | ⭐⭐⭐ Good |
| **AWS Glue** | $80-150 | ⭐⭐⭐⭐ Low | ⭐⭐⭐ Good |
| **Lambda + Athena** | $50-100 | ⭐⭐ High | ⭐⭐ Moderate |

**Databricks Value:**
- 10-50x faster (Photon engine)
- Unified platform (no service stitching)
- Better developer experience
- Built-in ML and governance

**Break-Even:**
- If team spends >20 hours/month on Spark management → Databricks cheaper (TCO)
- If <20 hours → AWS Glue/EMR cheaper (sticker price)

## 💡 Free Learning Resources

### No-Cost Ways to Learn Databricks

1. **Databricks Academy** (https://academy.databricks.com)
   - Free courses with lab environments
   - Hands-on exercises (4-hour sessions)
   - No credit card required

2. **Community Edition**
   - Sign up: https://community.cloud.databricks.com
   - Full Spark capabilities
   - Single-node (sufficient for learning)

3. **YouTube & Documentation**
   - Official Databricks YouTube channel
   - Comprehensive docs at docs.databricks.com
   - Weekly webinars (free)

4. **Coursera / Udemy**
   - Often have free trials
   - Use Databricks Community Edition for labs

## 📋 Cost Checklist for This Module

### Before Starting:
- [ ] Decide: Community Edition (free, basic) or Trial (free, full features)?
- [ ] Set calendar reminder to cancel trial (day 13)
- [ ] Enable auto-termination (30 minutes)
- [ ] Review cluster sizing guide

### During Module:
- [ ] Terminate clusters after each session (don't rely on auto-termination alone)
- [ ] Use single-node for exercises (sufficient for sample data)
- [ ] Monitor DBU usage in Account Console
- [ ] Keep cluster runtime < 2-3 hours per session

### After Completing:
- [ ] Delete all clusters
- [ ] Delete scratch data in DBFS
- [ ] Cancel trial if not continuing (to be safe)
- [ ] Export notebooks for backup

## 🚨 Emergency: How to Stop All Charges

If you see unexpected costs:

1. **Terminate All Clusters**
   ```
   Compute → Select All → Terminate
   ```

2. **Stop SQL Endpoints**
   ```
   SQL → SQL Warehouses → Stop All
   ```

3. **Delete Unused Data**
   ```
   Data → DBFS → Delete scratch files
   ```

4. **Contact Support**
   ```
   Help → Contact Support (within 24 hours of charge)
   Often refund accidental overruns
   ```

5. **Cancel Subscription** (if needed)
   ```
   Account Settings → Billing → Cancel Subscription
   ```

## ❓ FAQ

**Q: Will I be charged after the 14-day trial?**
A: Modern Databricks trials auto-cancel. However, always verify in Account Settings.

**Q: Can I use Community Edition for this entire module?**
A: Almost! You'll miss Exercise 03 (Unity Catalog) but complete 5 out of 6 exercises.

**Q: What if I run out of trial credits?**
A: Trial credits are generous (~$400). This module uses ~$20. Unlikely to run out.

**Q: Are cloud provider costs (EC2) included?**
A: On trial/Community Edition: Yes. On paid: You pay EC2 + DBU separately.

**Q: Can I get a student discount?**
A: Databricks Academy offers free lab environments for students. No personal account needed.

**Q: Is Databricks more expensive than AWS Glue?**
A: Sticker price: Yes (2-3x). Total Cost of Ownership (TCO): Often lower (faster development, less debugging, better performance).

## 📞 Getting Help

- **Billing Questions:** help@databricks.com
- **Technical Issues:** Community Forums (community.databricks.com)
- **Module Questions:** See instructor or course discussion board

---

**Key Takeaway:** This module can be completed for **$0** using Community Edition (5/6 exercises) or **$0-25** using the 14-day trial (all exercises). No hidden costs if you follow the cost checklist above.

**Safe to Start?** ✅ Yes! The free options are truly free with no surprise charges.
