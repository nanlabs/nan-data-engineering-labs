# Module 02: Storage Basics - Learning Resources

Curated resources para dominar storage de datos y formatos de archivo.

## 📚 Official Documentation

### AWS Services

**Amazon S3**
- [S3 User Guide](https://docs.aws.amazon.com/s3/index.html) - Complete S3 documentation
- [S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/) - Compare storage tiers
- [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) - Performance optimization
- [S3 Lifecycle Management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) - Automate tiering

**AWS Glue**
- [Glue Data Catalog](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html) - Metadata management
- [Glue Crawlers](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html) - Auto-discover schemas
- [Glue ETL](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-glue-data-types.html) - ETL transformations

**Amazon Athena**
- [Athena User Guide](https://docs.aws.amazon.com/athena/latest/ug/what-is.html) - SQL on S3
- [Query Performance Tuning](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html) - Optimization tips
- [Partitioning Data](https://docs.aws.amazon.com/athena/latest/ug/partitions.html) - Partition strategies

### File Formats

**Apache Parquet**
- [Parquet Documentation](https://parquet.apache.org/docs/) - Official docs
- [Parquet Format Spec](https://github.com/apache/parquet-format) - Technical specification
- [PyArrow Parquet](https://arrow.apache.org/docs/python/parquet.html) - Python implementation
- [Parquet Blog](https://blog.cloudera.com/apache-parquet/) - Deep dives and updates

**Apache Avro**
- [Avro Documentation](https://avro.apache.org/docs/current/) - Official guide
- [Schema Evolution](https://docs.confluent.io/platform/current/schema-registry/avro.html) - Confluent guide
- [Avro Python](https://avro.apache.org/docs/current/gettingstartedpython.html) - Python quickstart

**Apache ORC**
- [ORC Documentation](https://orc.apache.org/docs/) - Official docs
- [ORC Specification](https://orc.apache.org/specification/) - Format details

**CSV & JSON**
- [CSV RFC 4180](https://tools.ietf.org/html/rfc4180) - CSV standard
- [JSON Specification](https://www.json.org/json-en.html) - JSON spec
- [JSON Lines](https://jsonlines.org/) - JSONL format

## 🎥 Video Courses & Tutorials

### AWS Training

**AWS Skill Builder (Free)**
- [Getting Started with Amazon S3](https://explore.skillbuilder.aws/learn/course/external/view/elearning/53/getting-started-with-amazon-s3) - 1 hour
- [Deep Dive on Amazon S3](https://www.youtube.com/watch?v=rHeTn9pHNKo) - 45 min re:Invent session
- [AWS Glue Data Catalog](https://www.youtube.com/watch?v=WwhZ7Y4XW_U) - 30 min tutorial

**AWS re:Invent Sessions**
- [Advanced S3 Performance Patterns](https://www.youtube.com/watch?v=w1S1KvHzilk) - re:Invent 2023 (60 min)
- [Building Data Lakes on S3](https://www.youtube.com/watch?v=WHEsDa92HFQ) - re:Invent 2023 (50 min)
- [Optimizing S3 Costs](https://www.youtube.com/watch?v=XUJJL3PK0Xo) - Best practices (45 min)

### Data Engineering Courses

**Coursera**
- [Data Engineering on GCP Specialization](https://www.coursera.org/specializations/gcp-data-machine-learning) - Includes storage concepts
- [IBM Data Engineering Professional Certificate](https://www.coursera.org/professional-certificates/ibm-data-engineer) - Comprehensive

**Udemy**
- [Apache Spark and Scala](https://www.udemy.com/course/apache-spark-with-scala-hands-on-with-big-data/) - Includes Parquet, Avro
- [AWS Certified Data Analytics](https://www.udemy.com/course/aws-data-analytics/) - S3, Glue, Athena

**YouTube Channels**
- [AWS Online Tech Talks](https://www.youtube.com/c/AWSOnlineTechTalks) - Regular webinars
- [Databricks](https://www.youtube.com/c/Databricks) - Delta Lake, optimization
- [Confluent](https://www.youtube.com/c/Confluent) - Kafka, Avro, streaming

## 📖 Books

### Essential Reads

**"Designing Data-Intensive Applications" by Martin Kleppmann**
- **Rating:** ⭐⭐⭐⭐⭐ (5/5)
- **Focus:** Storage engines, data formats, distributed systems
- **Best Chapters:**
  - Chapter 3: Storage and Retrieval
  - Chapter 4: Encoding and Evolution
- **Price:** $45 (Hardcover), $30 (Kindle)
- **Link:** [O'Reilly](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/)

**"The Data Warehouse Toolkit" by Ralph Kimball**
- **Rating:** ⭐⭐⭐⭐ (4/5)
- **Focus:** Dimensional modeling, data warehousing
- **Relevant For:** Understanding when to use data lakes vs warehouses
- **Price:** $50 (Hardcover)

**"Fundamentals of Data Engineering" by Joe Reis, Matt Housley**
- **Rating:** ⭐⭐⭐⭐⭐ (5/5)
- **Focus:** Modern data engineering practices
- **Best Chapters:**
  - Storage (S3, formats)
  - Data lake architecture
- **Price:** $60 (O'Reilly subscription)
- **Link:** [O'Reilly](https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298/)

**"Programming AWS Lambda" by Mike Roberts**
- **Rating:** ⭐⭐⭐⭐ (4/5)
- **Focus:** Serverless data processing
- **Relevant:** Processing S3 events, file transformations

### Technical References

**"Hadoop: The Definitive Guide" by Tom White**
- Deep dive on file formats (Parquet, ORC, Avro)
- Chapter 12: Avro
- Chapter 13: Parquet

**"Streaming Systems" by Tyler Akidau**
- Best for understanding streaming vs batch
- Avro usage in streaming

## 🔬 Research Papers

### Foundational Papers

**"Dremel: Interactive Analysis of Web-Scale Datasets" (Google, 2010)**
- [PDF Link](https://research.google/pubs/pub36632/)
- **Why Read:** Foundation of columnr formats (Parquet)
- **Key Concepts:** Nested data encoding, column pruning

**"The Data Lakehouse: Data Warehousing and More" (Databricks, 2021)**
- [PDF Link](https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf)
- **Why Read:** Modern data architecture patterns
- **Key Concepts:** ACID on data lakes, Delta Lake

**"Amazon S3: A Simple Storage Service" (Amazon, 2006)**
- **Why Read:** Understanding S3 design decisions
- **Key Concepts:** Eventual consistency, durability

### Performance Studies

**"Parquet vs ORC vs Avro: Performance Comparison"**
- [Link](https://www.bigdatamastery.com/parquet-vs-orc-vs-avro/)
- Benchmark results for different workloads

**"Compression in Columnar Databases"**
- [PDF](https://www.vldb.org/pvldb/vol9/p1012-kurz.pdf)
- Deep dive on compression algorithms

## 🛠️ Tools & Libraries

### Python Libraries

**PyArrow**
```bash
pip install pyarrow
```
- [Documentation](https://arrow.apache.org/docs/python/)
- [GitHub](https://github.com/apache/arrow)
- **Use For:** Parquet I/O, high-performance processing

**Pandas**
```bash
pip install pandas
```
- [Documentation](https://pandas.pydata.org/docs/)
- **Use For:** DataFrame operations, CSV/JSON/Parquet

**Boto3 (AWS SDK)**
```bash
pip install boto3
```
- [Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- **Use For:** S3 operations, Glue API

**FastAvro**
```bash
pip install fastavro
```
- [Documentation](https://fastavro.readthedocs.io/)
- **Use For:** Avro serialization, faster than native

**PyORC**
```bash
pip install pyorc
```
- [GitHub](https://github.com/noirello/pyorc)
- **Use For:** ORC file operations

### Command-Line Tools

**AWS CLI**
```bash
# Install
pip install awscli

# Essential commands
aws s3 ls s3://bucket/
aws s3 sync local/ s3://bucket/
aws glue get-tables --database-name mydb
aws athena start-query-execution
```
- [Documentation](https://docs.aws.amazon.com/cli/latest/reference/)

**Parquet Tools**
```bash
# Install
pip install parquet-tools

# Usage
parquet-tools show data.parquet
parquet-tools schema data.parquet
parquet-tools meta data.parquet
parquet-tools csv data.parquet
```
- [GitHub](https://github.com/ktrueda/parquet-tools)

**DuckDB (SQL on Parquet)**
```bash
# Install
pip install duckdb

# Query Parquet directly
duckdb -c "SELECT * FROM 'data.parquet' WHERE amount > 100"
```
- [Documentation](https://duckdb.org/docs/)

**JQ (JSON processor)**
```bash
# Install
sudo apt install jq

# Usage
cat data.json | jq '.[] | select(.amount > 100)'
```
- [Documentation](https://stedolan.github.io/jq/)

### GUI Tools

**Apache Zeppelin**
- Web-based notebook for data analytics
- [Website](https://zeppelin.apache.org/)

**DBeaver**
- Universal database tool, supports Athena
- [Download](https://dbeaver.io/)

**AWS Console**
- S3 Browser, Glue Catalog, Athena Query Editor
- [Link](https://console.aws.amazon.com/)

## 📝 Blogs & Articles

### Must-Read Articles

**AWS Big Data Blog**
- [Best Practices for Data Partitioning](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-tips-for-amazon-athena/)
- [Optimizing S3 for Analytics](https://aws.amazon.com/blogs/big-data/best-practices-for-successfully-managing-memory-for-apache-spark-applications-on-amazon-emr/)
- [Blog Home](https://aws.amazon.com/blogs/big-data/)

**Databricks Blog**
- [Delta Lake vs Data Lake](https://www.databricks.com/blog/2020/01/30/what-is-a-data-lakehouse.html)
- [Optimizing Parquet Files](https://www.databricks.com/blog/2019/03/25/spark-data-serialization-using-json-with-parquet.html)
- [Blog Home](https://www.databricks.com/blog)

**Netflix Tech Blog**
- [Data Warehouse to Data Lake](https://netflixtechblog.com/evolution-of-the-netflix-data-pipeline-da246ca36905)
- [S3 at Scale](https://netflixtechblog.com/s3mper-consistency-in-the-cloud-2d1c0bb4f15f)

**Uber Engineering**
- [Building a Reliable Data Lake](https://eng.uber.com/uber-big-data-platform/)
- [Hudi: Hadoop Upserts Deletes](https://eng.uber.com/hoodie/)

**Spotify Engineering**
- [Event Delivery at Spotify](https://engineering.atspotify.com/2016/02/spotify-event-delivery-the-road-to-the-cloud-part-i/)

### Industry Benchmarks

**TPC-H Benchmark Results**
- [Parquet Performance](http://www.tpc.org/tpch/)
- Industry-standard analytics benchmark

**Apache Arrow Benchmarks**
- [Format Comparison](https://arrow.apache.org/blog/2019/02/05/python-parquet-benchmark/)
- Read/write performance tests

## 🎓 Certification Preparation

### AWS Certified Data Analytics - Specialty

**Exam Guide**
- [Official Exam Guide](https://aws.amazon.com/certification/certified-data-analytics-specialty/)
- **Domains:**
  - Storage (S3, Glacier): 18%
  - Processing (Glue, EMR): 24%
  - Analysis (Athena, Redshift): 26%

**Study Materials**
- [AWS Training](https://www.aws.training/) - Free digital training
- [Exam Readiness](https://www.aws.training/Details/eLearning?id=46612) - Free course
- [Practice Exams](https://aws.amazon.com/certification/certification-prep/) - $20-40

**Key Topics for Module 02:**
- S3 storage classes and lifecycle policies
- Partitioning strategies for Athena
- File format selection (Parquet, ORC, Avro)
- Glue Data Catalog and crawlers
- Schema evolution patterns

### Google Cloud Professional Data Engineer

**Relevant Topics:**
- Google Cloud Storage (similar to S3)
- BigQuery (uses columnr storage)
- Parquet format optimization

**Study Guide:**
- [Official Guide](https://cloud.google.com/certification/data-engineer)

## 💻 Hands-On Labs

### AWS Workshops

**Data Lake Workshop**
- [Link](https://catalog.us-east-1.prod.workshops.aws/workshops/44c91c21-a6a4-4b56-bd95-56bd443aa449/en-US)
- **Duration:** 4 hours
- **Topics:** S3, Glue, Athena, Lake Formation

**Big Data Analytics Workshop**
- [Link](https://catalog.workshops.aws/aws-analytics-course/en-US)
- **Duration:** 6 hours
- **Topics:** Kinesis, Glue, Athena, QuickSight

### Self-Paced Labs

**Qwiklabs**
- [Data Engineering Quest](https://www.qwiklabs.com/quests/132)
- Hands-on AWS/GCP labs with temporary credentials

**Coursera Labs**
- Included with course enrollment
- Real AWS environments

## 🌐 Community Resources

### Forums & Discussion

**AWS Forums**
- [S3 Forum](https://forums.aws.amazon.com/forum.jspa?forumID=24)
- [Athena Forum](https://forums.aws.amazon.com/forum.jspa?forumID=242)
- [Glue Forum](https://forums.aws.amazon.com/forum.jspa?forumID=250)

**Stack Overflow**
- [parquet tag](https://stackoverflow.com/questions/tagged/parquet) - 5,000+ questions
- [amazon-s3 tag](https://stackoverflow.com/questions/tagged/amazon-s3) - 50,000+ questions
- [aws-glue tag](https://stackoverflow.com/questions/tagged/aws-glue) - 3,000+ questions

**Reddit**
- [r/dataengineering](https://www.reddit.com/r/dataengineering/) - 150K members
- [r/aws](https://www.reddit.com/r/aws/) - 250K members
- [r/bigdata](https://www.reddit.com/r/bigdata/) - 50K members

### Slack Communities

**Data Engineering Slack**
- [Join Link](https://dataengineering.slack.com/)
- Channels: #storage, #parquet, #aws

**Locally Optimistic**
- [Join Link](https://www.locallyoptimistic.com/community/)
- Data professionals community

### Newsletters

**Data Engineering Weekly**
- [Subscribe](https://www.dataengineeringweekly.com/)
- Curated articles every week

**AWS Newsletter**
- [Subscribe](https://aws.amazon.com/newsletters/)
- Product updates, best practices

## 📊 Datasets for Practice

### Public Datasets

**AWS Open Data**
- [Registry](https://registry.opendata.aws/)
- **Examples:**
  - NYC Taxi (Parquet, 200GB)
  - NOAA Weather (JSON, 1TB)
  - NASA Earth Data (Various formats)

**Kaggle Datasets**
- [Browse](https://www.kaggle.com/datasets)
- Download CSV, convert to Parquet/Avro

**GitHub Awesome Public Datasets**
- [Repository](https://github.com/awesomedata/awesome-public-datasets)
- Curated list by domain

### Sample Data Generators

**Faker (Python)**
```python
from faker import Faker
import pandas as pd

fake = Faker()
data = [fake.simple_profile() for _ in range(10000)]
df = pd.DataFrame(data)
df.to_parquet('fake_data.parquet')
```

**Mockaroo**
- [Website](https://www.mockaroo.com/)
- Generate realistic test data
- Export to CSV, JSON

## 🔗 Quick Reference Links

### Cheat Sheets

**AWS S3 CLI Cheat Sheet**
```bash
# List
aws s3 ls s3://bucket/prefix/

# Copy
aws s3 cp file.txt s3://bucket/

# Sync
aws s3 sync local/ s3://bucket/

# Storage class
aws s3 cp file.txt s3://bucket/ --storage-class GLACIER
```

**Parquet with PyArrow**
```python
import pyarrow.parquet as pq

# Read
table = pq.read_table('data.parquet')
df = table.to_pandas()

# Write
table = pa.Table.from_pandas(df)
pq.write_table(table, 'output.parquet', compression='snappy')

# Partitioned write
pq.write_to_dataset(table, 'output/', partition_cols=['year', 'month'])
```

**Athena Query Optimization**
```sql
-- Use partitions
SELECT * FROM table WHERE year=2024 AND month=2;

-- Column pruning
SELECT id, amount FROM table;  -- Good
SELECT * FROM table;  -- Bad

-- Use CTAS for complex queries
CREATE TABLE optimized AS
SELECT ... FROM table WHERE ...
```

## 🎯 Learning Path

### Beginner (Weeks 1-2)
1. ✅ Read Module 02 theory (concepts.md)
2. ✅ Watch "Getting Started with S3" video
3. ✅ Complete Exercise 01: Data lake design
4. ✅ Complete Exercise 02: File format conversion

### Intermediate (Weeks 3-4)
1. ✅ Read "Designing Data-Intensive Applications" Ch 3-4
2. ✅ Complete Exercise 03: Partitioning
3. ✅ Complete Exercise 04: Compression
4. ✅ Watch re:Invent session on data lakes

### Advanced (Weeks 5-6)
1. ✅ Complete Exercise 05: Schema evolution
2. ✅ Complete Exercise 06: Glue Catalog
3. ✅ Read Dremel paper
4. ✅ Build personal project with production data

### Mastery (Weeks 7-8)
1. ✅ Complete AWS Data Lake workshop
2. ✅ Contribute to open-source (PyArrow, etc.)
3. ✅ Write blog post on learning
4. ✅ Consider AWS Data Analytics certification

## 📞 Getting Help

### When Stuck

1. **Check Documentation:** Official AWS docs first
2. **Search Stack Overflow:** Likely someone had same issue
3. **AWS Forums:** Post detailed question
4. **Office Hours:** Use module Slack channel
5. **Instructor:** Tag instructor for review

### Best Practices for Asking Questions

**Good Question:**
```
I'm trying to convert 10GB CSV to Parquet using PyArrow but getting
MemoryError. I've tried:
- Reading in chunks: Still fails
- Increasing memory: Not available
- Using pandas: Same issue

Environment: Python 3.9, PyArrow 10.0, 8GB RAM
Code: [gist link]
Error: [full traceback]

Any suggestions for streaming conversion?
```

**Bad Question:**
```
Parquet doesn't work. Help?
```

## 🏆 Success Metrics

Track your progress:
- [ ] Completed all 6 exercises
- [ ] Read 2+ recommended articles
- [ ] Watched 1+ video tutorial
- [ ] Built sample data lake project
- [ ] Can explain Parquet vs Avro to peer
- [ ] Understand when to use each storage class
- [ ] Optimized query from 5min to <10s
- [ ] Reduced storage costs by 50%+

---

**Last Updated:** February 2, 2026

*This resource list is continuously updated. Submit PR for additions via course repository.*
