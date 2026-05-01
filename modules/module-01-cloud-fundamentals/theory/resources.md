# Learning Resources: Cloud Fundamentals

This list contains official and quality-verified Resources to delve deeper into the Module's Concepts.

---

## 📚 Official AWS Documentation

### Essential Reading

1. **AWS Well-Architected Framework**
   - URL: https://aws.amazon.com/architecture/well-architected/
   - Tiempo: 2-3 horas
   - Why: Best practices framework used by AWS architects
   - Focus on: The 5 pillars and how to apply them to data engineering

2. **AWS Global Infrastructure**
   - URL: https://aws.amazon.com/about-aws/global-infrastructure/
   - Tiempo: 30 minutos
   - Interactive map of regions, AZs and edge locations
   - Understand: How to choose region according to latency, compliance, costs

3. **IAM Best Practices**
   - URL: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
   - Tiempo: 1 hora
   - Critical for security in all your projects
   - Memoriza: Principle of least privilege, MFA, roles vs users

4. **Amazon S3 User Guide**
   - URL: https://docs.aws.amazon.com/s3/
   - Tiempo: 3-4 horas (lectura selectiva)
   - Secciones clave:
     - Storage classes and lifecycle management
     - Versioning
     - Event notifications
     - Performance optimization

5. **AWS Lambda Developer Guide**
   - URL: https://docs.aws.amazon.com/lambda/
   - Tiempo: 2 horas
   - Secciones clave:
     - Execution model
     - Permissions (execution role)
     - Best practices
     - Monitoring and troubleshooting

---

## 🎥 Videos Oficiales AWS

### AWS re:Invent Talks

**1. AWS re:Invent 2023: Building Data Lakes on AWS**
- YouTube: Buscar "AWS re:Invent 2023 data lakes"
- Duration: 50 minutes
- Speaker: AWS Solutions Architect
- Key Timestamps:
  - 00:00-10:00: Data lake architecture overview
  - 10:00-25:00: S3 as foundation (zones, partitioning)
  - 25:00-35:00: AWS Glue for cataloging and ETL
  - 35:00-50:00: Real customer case study
- Why: Learn data lake architecture directly from AWS

**2. AWS re:Invent 2022: Security Best Practices for Data Engineers**
- Duration: 45 minutes
- Key Timestamps:
  - 00:00-15:00: IAM policies and roles
  - 15:00-30:00: Encryption (KMS, at rest, in transit)
  - 30:00-45:00: VPC, security groups, endpoints
- Why: Security from the start, not as an afterthought

**3. AWS re:Invent 2023: Serverless Data Processing at Scale**
- Duration: 60 minutes
- Key Timestamps:
  - 00:00-20:00: Lambda patterns for data processing
  - 20:00-40:00: Step Functions for orchestration
  - 40:00-60:00: Cost optimization techniques
- Why: Learn when to use serverless vs. containers/VMs

### AWS Digital Courses

**4. AWS Skill Builder: AWS Cloud Practitioner Essentials**
- URL: https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/
- Duration: 6 hours (self-paced)
- Free with AWS account
- Cubre:
  - AWS global infrastructure
  - Compute, storage, databases
  - Security and compliance
  - Pricing and support
- Why: Solid fundamentals before specializing in data

**5. AWS Skill Builder: Getting Started with AWS Storage**
- Duration: 4 hours
- Gratis
- Deep dive on S3, EBS, EFS
- Why: S3 is the heart of data engineering in AWS

---

## 🎓 Courses from Recognized Instructors

### Stephane Maarek (Highly Recommended)

**6. Ultimate AWS Certified Cloud Practitioner**
- Plataforma: Udemy
- Duration: 14 hours
- Price: ~$15-20 (wait for it from Udemy)
- Rating: 4.7/5 (500K+ students)
- Why: Best introductory course to AWS, very educational
- Covers: Everything you need to understand AWS from scratch

**7. Ultimate AWS Certified Solutions Architect Associate**
- Plataforma: Udemy
- Duration: 27 hours
- Precio: ~$15-20
- Rating: 4.7/5 (800K+ students)
- Why: Goes deeper into architectures, includes many data services
- Note: More advanced, consider after Module 04

### FreeCodeCamp (YouTube - GRATIS)

**8. AWS Certified Cloud Practitioner Training 2023**
- URL: https://www.youtube.com/watch?v=SOTamWNgDKc
- Duration: 13 hours
- Gratis
- Instructor: Andrew Brown (ExamPro)
- Why: Great free alternative to paid courses
- Tip: 1.25x speed for already known Content

**9. AWS Certified Solutions Architect - Associate 2023**
- URL: Search YouTube FreeCodeCamp AWS Solutions Architect
- Duration: 10+ hours
- Gratis
- Why: Covers more complex architectures, useful for data engineering

---

## 📖 Blogs and Technical Articles

**10. AWS Architecture Blog**
- URL: https://aws.amazon.com/blogs/architecture/
- Frecuencia: Semanal
- Why: Reference architectures with diagrams and code
- Recommended articles:
  - "Building a Data Lake on AWS"
  - "Serverless Analytics Architecture"
  - "Cost Optimization for Data Workloads"

**11. AWS Big Data Blog**
- URL: https://aws.amazon.com/blogs/big-data/
- Frecuencia: 2-3 veces/semana
- Why: Specific for data engineering
- Search articles about: Glue, EMR, Athena, Lake Formation

**12. AWS Startups Blog - Data & Analytics**
- URL: https://aws.amazon.com/blogs/startups/tag/data-analytics/
- Why: Real Usage Cases from startups with limited budgets
- Learn: How to do more with less ($)

---

## 🛠️ Hands-On Labs (Gratis)

**13. AWS Workshops**
- URL: https://workshops.aws/
- Category: Analytics & Data Lakes
- Workshops recomendados:
  - "Building a Data Lake on AWS"
  - "Serverless Data Processing"
  - "AWS Glue ETL Workshop"
- Time: 2-3 hours per workshop
- Why: Guided practice with a real AWS account
- Cost: Free tier enough, careful to clean Resources after

**14. AWS Free Tier Hands-On Tutorials**
- URL: https://aws.amazon.com/getting-started/hands-on/
- Filter by: Storage, Analytics, Serverless
- Tutoriales paso a paso:
  - "Store and Retrieve a File with S3"
  - "Run a Serverless Hello World"
  - "Query Data in S3 with Athena"
- Time: 15-30 min per tutorial
- Why: Get familiar with the AWS Console and basic services

---

## 📊 Whitepapers AWS (Lectura Avanzada)

**15. AWS Well-Architected Framework - Data Analytics Lens**
- URL: https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/
- Pages: ~80
- Tiempo: 3-4 horas
- Why: Specific best practices for data workloads
- Read after: Completing Module Exercises

**16. Cost Optimization for Data Lakes**
- URL: Search AWS whitepapers
- Why: Learn to design cost-effective architectures from the beginning

---

## 🎙️ Podcasts (Optional - For commutes)

**17. AWS Podcast**
- URL: https://aws.amazon.com/podcasts/aws-podcast/
- Relevant episodes: Search "data" in the catalog
- Duration: 20-30 min per episode
- Why: Stay up to date with AWS news

**18. The Data Engineering Podcast**
- URL: https://www.dataengineeringpodcast.com/
- Episodes with "AWS" in the title
- Why: Perspective of practitioners, not just Theory AWS

---

## 📱 Reference Tools

**19. AWS CLI Command Reference**
- URL: https://docs.aws.amazon.com/cli/
- Usa como referencia durante Exercises
- Tip: Bookmark sections of S3, IAM, Lambda

**20. AWS SDK for Python (Boto3) Documentation**
- URL: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- Essential to automate with Python
- Secciones clave: S3, Lambda, Glue, Athena

**21. AWS Pricing Calculator**
- URL: https://calculator.aws/
- Practice: Estimate architecture costs before implementing
- Use in Exercise 06 (Cost Optimization)

---

## 🌐 Communities and Forums

**22. AWS re:Post (Official Q&A)**
- URL: https://repost.aws/
- Official replacement for AWS Forums
- Why: Answers from AWS Solutions Architects and community experts

**23. r/aws (Reddit)**
- URL: https://reddit.com/r/aws
- Why: Active community, troubleshooting, shared architectures
- Tip: Look for posts with "data engineering" or "data lake"

**24. AWS Slack Community**
- URL: Search "AWS Community Slack" on Google
- Channels relevantes: #analytics, #serverless, #lambda
- Why: Chat in real time with other learners and professionals

---

## 📝 Cheat Sheets and Quick References

**25. AWS Services Overview**
- URL: https://aws.amazon.com/products/
- Usage: Overview of all AWS services
- Tip: Explore categories Analytics, Storage, Compute

**26. AWS Service Limits**
- URL: https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html
- Why: Know limits (ex: 1000 concurrent Lambdas) before designing

**27. Markdown Cheat Sheet for Mermaid Diagrams**
- URL: https://mermaid.js.org/syntax/examples.html
- Use in: architecture.md and your own diagrams
- Why: Diagrams as code, versionable in Git

---

## 🎯 Suggested Consumption Roadmap

### Before Exercises (8-10 hours)

1. **Day 1-2:** Read complete concepts.md (this Module)
2. **Day 3:** AWS Cloud Practitioner Essentials (digital course) - First 3 hours
3. **Day 4:** FreeCodeCamp AWS Cloud Practitioner Video (1.5x speed) - IAM, S3, Lambda Sections
4. **Day 5:** Read architecture.md + AWS Well-Architected Framework overview

### Durante Exercises (5-8 horas)

- Usa AWS CLI Reference como consulta
- Consulta Boto3 docs cuando escribas Python
- Si te atascas: re:Post o Stack Overflow

### After Exercises (Optional, go deeper)

- Stephane Maarek course (si quieres certificarte)
- AWS Workshops hands-on
- Whitepapers for advanced design

---

## 🔖 Bookmarks Sugeridos

Create a folder in your browser: **"AWS Data Engineering"**

Subcarpetas:
```
📁 AWS Data Engineering
├── 📁 Docs Oficiales
│   ├── IAM Best Practices
│   ├── S3 User Guide
│   ├── Lambda Developer Guide
│   └── Well-Architected Framework
├── 📁 Videos
│   ├── FreeCodeCamp AWS (YouTube)
│   └── AWS re:Invent Playlists
├── 📁 Blogs
│   ├── AWS Architecture Blog
│   └── AWS Big Data Blog
├── 📁 Tools
│   ├── AWS Pricing Calculator
│   ├── AWS CLI Reference
│   └── Boto3 Docs
└── 📁 Community
    ├── AWS re:Post
    └── r/aws
```

---

## ⚠️ Advertencias

**Don't fall for "Tutorial Hell":**
- Don't watch all the videos before practicing
- Alterna Theory (1 hora) → Practice (2 horas)
- Exercises are more important than additional videos

**Evita distracciones:**
- No persigas cada servicio AWS (hay 200+)
- Focus on: S3, IAM, Lambda, Glue, Athena for data engineering
- You will learn other services when you need them

**Free Tier limits:**
- Monitor Usage with AWS Budgets (set $5 alarm)
- Delete Resources after each Exercise
- LocalStack (in this course) avoids real costs

---

## 📈 Next Steps

You have reviewed the available Resources. Now:

1. ✅ Complete the reading of`concepts.md`and`architecture.md`
2. ⏭️ Watch at least 2 hours of recommended videos
3. 🏗️ Comienza Exercise 01: AWS CLI & S3 Basics
4. 📖 Consult these Resources when you have specific questions

**Remember:** The best way to learn cloud is by **building**. These Resources are complementary to the practical Exercises.

Onward with the Exercises! 🚀
