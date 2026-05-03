# Databricks Setup Guide

This guide walks you through creating a Databricks account, setting up your workspace, and preparing for the exercises.

## Table of Contents

1. [Choose Your Databricks Edition](#choose-your-databricks-edition)
2. [Option A: Community Edition Setup](#option-a-community-edition-setup)
3. [Option B: Trial Account Setup](#option-b-trial-account-setup)
4. [Workspace Configuration](#workspace-configuration)
5. [Create Your First Cluster](#create-your-first-cluster)
6. [Import Notebooks](#import-notebooks)
7. [Configure Databricks CLI](#configure-databricks-cli)
8. [Troubleshooting](#troubleshooting)

---

## Choose Your Databricks Edition

### Comparison

| Feature | Community Edition | 14-Day Trial | Enterprise |
|---------|-------------------|--------------|------------|
| **Cost** | FREE | FREE (14 days) | Paid |
| **Credit Card** | Not required | Required | Required |
| **Cluster Type** | Single-node only | All types | All types |
| **Unity Catalog** | ❌ No | ✅ Yes | ✅ Yes |
| **Workflows** | ❌ No | ✅ Yes | ✅ Yes |
| **SQL Analytics** | Limited | ✅ Yes | ✅ Yes |
| **Repos (Git)** | ❌ No | ✅ Yes | ✅ Yes |
| **Collaboration** | Limited | ✅ Full | ✅ Full |
| **Best For** | Learning basics | Full experience | Production |

### Recommendation for This Module

- **Community Edition**: Complete 4 out of 6 exercises (skip Unity Catalog, Workflows)
- **Trial Account**: Complete all 6 exercises

---

## Option A: Community Edition Setup

### Step 1: Sign Up (5 minutes)

1. **Visit:** https://community.cloud.databricks.com/login.html
2. **Click:** "Sign up for Community Edition"
3. **Fill out form:**
   - First name, Last name
   - Email address
   - Password (min 8 characters)
   - Check "I accept the terms of service"
4. **Click:** "Get started for free"
5. **Verify email:** Check your inbox and click verification link

### Step 2: Explore Workspace (2 minutes)

After login, you'll see:
- **Workspace**: Folder for notebooks
- **Compute**: Create clusters
- **Data**: Browse tables (DBFS)
- **Repos**: Git integration (not available in CE)

### Step 3: Limitations to Note

Community Edition has:
- ✅ Full Spark and Delta Lake capabilities
- ✅ Unlimited usage time
- ✅ 15GB storage
- ❌ Single-node clusters only (no distributed computing)
- ❌ No Unity Catalog
- ❌ No Workflows (scheduled jobs)
- ❌ No Repos (Git integration)

**For this module:** You'll complete exercises 01, 02, 04, 05, 06 (skip 03: Unity Catalog)

---

## Option B: Trial Account Setup

### Step 1: Choose Cloud Provider (2 minutes)

Databricks runs on AWS, Azure, or GCP. For this module:

**Recommended:** AWS (most common, well-documented)

1. **Visit:** https://www.databricks.com/try-databricks
2. **Select:** "Start Free Trial"
3. **Choose:** AWS (or Azure/GCP if preferred)

### Step 2: Account Creation (5 minutes)

1. **Fill out form:**
   - First name, Last name
   - Work email
   - Company name
   - Phone number
   - Password

2. **Choose deployment:**
   - **Quick Start** (recommended): Databricks manages everything
   - **Bring Your Own Cloud**: Use your existing AWS account

3. **For Quick Start:**
   - Databricks creates AWS resources automatically
   - No AWS account needed
   - Everything in Databricks control plane

4. **Click:** "Start Trial"

### Step 3: Payment Information (3 minutes)

**⚠️ Credit card required but:**
- You **won't be charged** during 14-day trial
- Trial auto-expires (no auto-conversion to paid)
- Set up billing alerts as precaution

1. **Enter credit card details**
2. **Set billing alerts:**
   - Go to: Account Settings → Billing
   - Set alert: "Notify me if charges exceed $10"

### Step 4: Workspace Setup (2 minutes)

After account creation:
1. **Workspace URL assigned:** `https://dbc-xxxxxxxx-xxxx.cloud.databricks.com`
2. **Bookmark this URL** (your permanent workspace link)
3. **Explore:** Left sidebar shows all features

### Step 5: Enable Unity Catalog (Optional but Recommended)

Unity Catalog might not be enabled by default:

1. **Go to:** Account Console (top-right dropdown)
2. **Click:** Catalog → Enable Unity Catalog
3. **Follow wizard:**
   - Create metastore
   - Assign to workspace
   - Create default catalogs (main, sandbox)

**Note:** Unity Catalog required for Exercise 03

---

## Workspace Configuration

### 1. Set Your Profile

1. **Click:** Your email (top-right) → User Settings
2. **Set:**
   - Display name
   - Time zone
   - Language

### 2. Create Workspace Folders

Organize your work:

1. **Go to:** Workspace → Users → [your-email]
2. **Create folders:**
   ```
   /Users/your-email@example.com/
   ├── training/
   │   ├── module-bonus-01/
   │   │   ├── notebooks/
   │   │   └── exercises/
   ```

3. **Right-click folder** → Create → Folder

### 3. Configure Workspace Settings

1. **Go to:** Admin Console → Workspace Settings
2. **Recommended settings:**
   - Auto-terminate: ON (prevent cost overruns)
   - Default cluster timeout: 30 minutes
   - Notebook revision history: ON

---

## Create Your First Cluster

### Cluster Types

For this module:
- **Exercises:** Use All-Purpose cluster (interactive)
- **Production (if applicable):** Use Job clusters

### Step 1: Navigate to Compute

1. **Click:** Compute (left sidebar)
2. **Click:** "Create Cluster" button

### Step 2: Configure Cluster

**Cluster Name:** `training-cluster`

**Cluster Mode:**
- Community Edition: Single Node (only option)
- Trial/Enterprise: Standard (single-user recommended)

**Databricks Runtime Version:**
- **Recommended:** 14.3 LTS (Long Term Support)
- Includes: Spark 3.5.x, Delta Lake, ML libraries

**Node Type:**
- Community Edition: Predefined (cannot change)
- Trial AWS: `m5.xlarge` (4 vCPU, 16GB RAM) - sufficient for module
- Trial Azure: `Standard_DS3_v2`

**Auto-scaling:**
- Trial: Enable (min 2, max 4 workers)
- Cost-conscious: Disable (fixed 2 workers)

**Auto-termination:**
- ✅ **Enable:** 30 minutes (IMPORTANT for cost control)

**Advanced Options:**

Click "Advanced options" and set:

```python
# Spark Config
spark.databricks.delta.preview.enabled true
spark.sql.adaptive.enabled true
spark.sql.adaptive.coalescePartitions.enabled true

# For Unity Catalog (Trial only)
spark.databricks.unityCatalog.enabled true
```

**Init Scripts:** (Leave empty for now)

### Step 3: Create and Start

1. **Click:** "Create Cluster"
2. **Wait:** 5-10 minutes for cluster to start
3. **Status:** Should show "Running" (green)

### Cluster States

- 🟢 **Running**: Ready for use
- 🟡 **Pending**: Starting up (5-10 min)
- 🟠 **Restarting**: Applying configuration changes
- 🔴 **Terminated**: Stopped (not consuming resources)
- ⚫ **Error**: Failed to start (check logs)

---

## Import Notebooks

### Method 1: Manual Upload (Recommended for Learning)

1. **Download notebooks** from course repository:
   ```bash
   git clone https://github.com/your-org/training-cloud-data
   cd training-cloud-data/modules/module-bonus-01-databricks-lakehouse/notebooks
   ```

2. **In Databricks:**
   - Go to: Workspace → Users → [your-email] → training
   - Right-click → Import
   - Select files: `01-delta-lake-basics.py`, `02-etl-pipeline.py`, etc.
   - Click "Import"

3. **Notebooks appear in folder**

### Method 2: Git Integration (Trial/Enterprise Only)

More advanced, better for version control:

1. **Go to:** Repos (left sidebar)
2. **Click:** "Add Repo"
3. **Enter:**
   - Git URL: `https://github.com/your-org/training-cloud-data`
   - Branch: `main`
   - Path: `/Repos/your-email/training-cloud-data`
4. **Click:** "Create Repo"

**Benefits:**
- Auto-sync with Git
- Pull latest updates
- Commit changes from Databricks

### Method 3: Databricks CLI (Advanced)

If you prefer command-line:

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token

# Import notebooks
databricks workspace import_dir \
  ./notebooks \
  /Users/your-email@example.com/training/notebooks \
  --overwrite
```

---

## Configure Databricks CLI

The Databricks CLI is useful for automation and bulk operations.

### Step 1: Install CLI

```bash
# Using pip
pip install databricks-cli

# Using conda
conda install -c conda-forge databricks-cli

# Verify installation
databricks --version
```

### Step 2: Generate Access Token

1. **In Databricks:**
   - Click: User Settings (top-right)
   - Go to: Access tokens tab
   - Click: "Generate new token"
   - Comment: "Training module access"
   - Lifetime: 90 days
   - Click: "Generate"

2. **Copy token** (you'll only see it once!)

### Step 3: Configure CLI

```bash
# Run configuration
databricks configure --token

# Enter when prompted:
# Databricks Host: https://dbc-xxxxxxxx-xxxx.cloud.databricks.com
# Token: dapi1234567890abcdef... (paste your token)
```

**Test connection:**
```bash
# List workspaces
databricks workspace ls /Users/your-email@example.com

# Should show your folders
```

### Step 4: Common CLI Commands

```bash
# List clusters
databricks clusters list

# Start a cluster
databricks clusters start --cluster-id <cluster-id>

# Upload notebook
databricks workspace import \
  ./my-notebook.py \
  /Users/your-email@example.com/training/my-notebook

# Download notebook
databricks workspace export \
  /Users/your-email@example.com/training/my-notebook \
  ./my-notebook.py

# Run job
databricks jobs run-now --job-id <job-id>
```

---

## Verify Setup Checklist

Before starting exercises:

### Community Edition
- [ ] Account created at community.cloud.databricks.com
- [ ] Logged in successfully
- [ ] Single-node cluster created and running
- [ ] Notebooks imported to workspace
- [ ] Can run simple cell: `print("Hello Databricks!")`

### Trial Account
- [ ] Trial account created (AWS/Azure/GCP)
- [ ] Workspace URL bookmarked
- [ ] Billing alert set ($10 threshold)
- [ ] Cluster created with auto-termination (30 min)
- [ ] Unity Catalog enabled (for Exercise 03)
- [ ] Notebooks imported to workspace
- [ ] Databricks CLI configured (optional)

---

## Troubleshooting

### Issue: Cluster won't start

**Error:** "Could not launch cluster"

**Solutions:**
1. Check cloud provider status (AWS/Azure/GCP outage?)
2. Try different instance type (m5.large instead of m5.xlarge)
3. Check quota limits (trial accounts have limits)
4. Contact Databricks support: help@databricks.com

### Issue: "Notebook not found" when importing

**Solution:**
- Ensure path is correct: `/Users/your-email@example.com/training/`
- Create parent folders first
- Check file format: Must be `.py`, `.sql`, `.scala`, or `.r`

### Issue: Permission denied when accessing Unity Catalog

**Error:** "User does not have permission on catalog 'main'"

**Solution:**
```sql
-- Grant yourself access (run as admin)
GRANT USE CATALOG, USE SCHEMA, CREATE TABLE ON CATALOG main TO `your-email@example.com`;
```

### Issue: Cluster auto-terminated while I was working

**Explanation:** 30-minute idle timeout triggered

**Solution:**
- Restart cluster: Compute → Select cluster → Start
- Adjust timeout: Cluster → Edit → Auto-termination (increase to 60 min)
- **Note:** Longer timeout = higher costs

### Issue: Out of memory errors

**Error:** "OutOfMemoryError: Java heap space"

**Solutions:**
1. Increase driver memory:
   ```python
   spark.conf.set("spark.driver.memory", "8g")
   ```
2. Use larger instance type (m5.xlarge → m5.2xlarge)
3. Process data in smaller batches
4. Enable auto-scaling (add more workers)

### Issue: Notebooks run slowly

**Possible causes:**
1. Single-node cluster (Community Edition limitation)
2. Large dataset (>1GB on single node)
3. Cold start (first run after cluster start)

**Solutions:**
1. Upgrade to multi-node cluster (Trial/Enterprise)
2. Cache frequently-used DataFrames: `df.cache()`
3. Use Delta Lake optimization: `OPTIMIZE table_name`
4. Consider sampling data: `df.sample(0.1)`  # 10% sample

### Issue: Trial expired

**After 14 days:**
1. Workspace becomes read-only
2. Cannot create new clusters
3. Can export notebooks (download backups)

**Options:**
1. Sign up for paid account
2. Use Community Edition (lose Unity Catalog access)
3. Request trial extension (education/non-profit)

### Issue: Unexpected charges

**If you see charges during trial:**
1. Check billing dashboard: Account → Billing
2. Identify source (likely cluster running 24/7)
3. Terminate all clusters: Compute → Terminate All
4. Contact support for refund: help@databricks.com
   - Screenshot billing dashboard
   - Explain: "Accidental cluster left running"
   - Usually refunded within 48 hours

---

## Next Steps

Once setup is complete:

1. **Verify cluster is running**
   - Compute → Check green "Running" status

2. **Open first notebook**
   - Workspace → training → notebooks → 01-delta-lake-basics.py

3. **Attach notebook to cluster**
   - Click "Connect" dropdown (top-right)
   - Select your cluster

4. **Run first cell**
   ```python
   print("✅ Setup complete! Ready to learn Databricks.")
   ```

5. **Proceed to exercises**
   - Start with Exercise 01: Delta Lake Fundamentals

---

## Useful Resources

- **Databricks Academy:** https://academy.databricks.com (free courses)
- **Documentation:** https://docs.databricks.com
- **Community Forums:** https://community.databricks.com
- **YouTube Tutorials:** https://www.youtube.com/c/Databricks
- **Status Page:** https://status.databricks.com

---

## Support

**Questions about setup?**
- Community Forums: https://community.databricks.com
- Databricks Help Center: help@databricks.com
- Course instructor or TA

**Billing questions:**
- Email: billing@databricks.com
- Include: Workspace ID, issue description

---

**Setup Guide Version:** 1.0
**Last Updated:** March 2026
**Tested On:** Databricks Runtime 14.3 LTS
