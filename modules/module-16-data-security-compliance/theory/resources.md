# Learning Resources - Data Security & Compliance

## Table of Contents
- [AWS Official Documentation](#aws-official-documentation)
- [AWS Certifications](#aws-certifications)
- [Training Courses](#training-courses)
- [Books](#books)
- [Blogs and Websites](#blogs-and-websites)
- [Tools](#tools)
- [Communities](#communities)
- [Compliance Frameworks](#compliance-frameworks)

---

## AWS Official Documentation

### **Essential AWS Security Guides**
- 📘 [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- 📘 [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- 📘 [AWS Security Reference Architecture (SRA)](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/)
- 📘 [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- 📘 [AWS KMS Developer Guide](https://docs.aws.amazon.com/kms/latest/developerguide/)

### **Service-Specific Security**
- 📘 [Amazon S3 Security](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security.html)
- 📘 [Amazon RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.html)
- 📘 [AWS Lake Formation Security](https://docs.aws.amazon.com/lake-formation/latest/dg/security.html)
- 📘 [AWS Glue Security](https://docs.aws.amazon.com/glue/latest/dg/security.html)
- 📘 [Amazon Redshift Security](https://docs.aws.amazon.com/redshift/latest/mgmt/security.html)

### **Compliance Documentation**
- 📘 [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/)
- 📘 [HIPAA on AWS](https://aws.amazon.com/compliance/hipaa-compliance/)
- 📘 [GDPR on AWS](https://aws.amazon.com/compliance/gdpr-center/)
- 📘 [PCI-DSS on AWS](https://aws.amazon.com/compliance/pci-dss-level-1-faqs/)

---

## AWS Certifications

### **Security Specialty**
🎓 **AWS Certified Security - Specialty**
- **Duration**: 170 minutes
- **Cost**: $300 USD
- **Prerequisite**: 2+ years AWS security experience
- **Domains**:
  1. Incident Response (12%)
  2. Logging and Monitoring (20%)
  3. Infrastructure Security (26%)
  4. Identity and Access Management (20%)
  5. Data Protection (22%)
- **Study Guide**: [Official Exam Guide](https://aws.amazon.com/certification/certified-security-specialty/)
- **Practice Exams**: [AWS Skill Builder](https://explore.skillbuilder.aws/)

### **Related Certifications**
🎓 **AWS Certified Solutions Architect - Professional**
- Includes advanced security architecture patterns

🎓 **AWS Certified Data Analytics - Specialty**
- Data security and compliance for analytics workloads

---

## Training Courses

### **AWS Official Training**
1. **Security Engineering on AWS** (3 days)
   - URL: [AWS Training](https://aws.amazon.com/training/classroom/security-engineering-on-aws/)
   - Level: Advanced
   - Topics: Network security, encryption, monitoring, incident response

2. **AWS Security Fundamentals** (Digital, 4 hours)
   - URL: [AWS Skill Builder](https://explore.skillbuilder.aws/learn/course/external/view/elearning/48/aws-security-fundamentals-second-edition)
   - Level: Beginner
   - Free

3. **Exam Readiness: AWS Certified Security - Specialty** (Digital, 2 hours)
   - URL: [AWS Skill Builder](https://explore.skillbuilder.aws/)
   - Level: Advanced
   - Free with AWS Skill Builder subscription

### **Third-Party Platforms**

**A Cloud Guru / Pluralsight**
- [AWS Certified Security - Specialty](https://acloudguru.com/course/aws-certified-security-specialty)
- Duration: 15-20 hours
- Hands-on labs included

**Udemy**
- [AWS Certified Security Specialty 2024](https://www.udemy.com/course/aws-certified-security-specialty/)
- Instructor: Stephane Maarek
- Rating: 4.6/5

**Linux Academy / A Cloud Guru**
- [AWS Security Fundamentals](https://linuxacademy.com/)
- Hands-on labs with real AWS environments

---

## Books

### **AWS Security**
📖 **"AWS Security" by Dylan Shield** (2023)
- Comprehensive guide to AWS security services
- Practical examples and architectures
- ISBN: 978-1617297632

📖 **"Mastering AWS Security" by Albert Anthony** (2022)
- Advanced IAM, encryption, compliance
- Real-world case studies
- ISBN: 978-1803239729

📖 **"AWS Certified Security Study Guide" by Ben Piper** (2023)
- Exam preparation for Security Specialty
- Practice questions and explanations
- ISBN: 978-1119942344

### **Data Security & Privacy**
📖 **"Data Privacy: A Runbook for Engineers" by Nishant Bhajaria** (2022)
- GDPR, CCPA compliance
- Privacy-by-design principles
- ISBN: 978-1617298998

📖 **"Practical Cloud Security" by Chris Dotson** (2021)
- Multi-cloud security patterns
- DevSecOps practices
- ISBN: 978-1492037514

### **Compliance**
📖 **"The GDPR Challenge" by David Dumont** (2023)
- GDPR implementation guide
- Cloud compliance strategies
- ISBN: 978-1484268741

---

## Blogs and Websites

### **AWS Official Blogs**
- 📝 [AWS Security Blog](https://aws.amazon.com/blogs/security/)
  - Latest security announcements, best practices
- 📝 [AWS Big Data Blog - Security](https://aws.amazon.com/blogs/big-data/tag/security/)
  - Data security patterns
- 📝 [AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/)
  - Security reference architectures

### **Community Blogs**
- 📝 [Christophe Tafani-Dereeper (Blog)](https://blog.christophetd.fr/)
  - AWS security research, offensive security
- 📝 [Scott Piper (Summit Route)](https://summitroute.com/blog/)
  - AWS security news, vulnerability research
- 📝 [Rhino Security Labs](https://rhinosecuritylabs.com/blog/)
  - AWS penetration testing, security research

### **Podcasts**
🎙️ **"AWS Security Podcast"** by Dmitriy Samovskiy
- Weekly security news and interviews

🎙️ **"Cloud Security Podcast"** by Google
- Multi-cloud security discussions

---

## Tools

### **Security Scanning**
🔧 **Prowler** (Open Source)
- CIS AWS Foundations Benchmark checks
- GDPR, HIPAA, PCI-DSS assessments
- GitHub: [prowler-cloud/prowler](https://github.com/prowler-cloud/prowler)
```bash
pip install prowler
prowler aws --compliance cis_1.5_aws
```

🔧 **ScoutSuite** (Open Source)
- Multi-cloud security auditing
- GitHub: [nccgroup/ScoutSuite](https://github.com/nccgroup/ScoutSuite)
```bash
pip install scoutsuite
scout aws --profile prod
```

🔧 **CloudSploit** (Open Source)
- 100+ security checks
- GitHub: [aquasecurity/cloudsploit](https://github.com/aquasecurity/cloudsploit)

### **IAM Policy Analysis**
🔧 **Parliament** (AWS Open Source)
- IAM policy linting
- GitHub: [duo-labs/parliament](https://github.com/duo-labs/parliament)
```bash
pip install parliament
parliament --file policy.json
```

🔧 **Policy Sentry** (Open Source)
- Least privilege IAM policy generator
- GitHub: [salesforce/policy_sentry](https://github.com/salesforce/policy_sentry)
```bash
pip install policy-sentry
policy_sentry create-template --output-file template.yml --template-type crud
```

### **Secrets Management**
🔧 **git-secrets** (AWS Open Source)
- Prevent committing secrets to git
- GitHub: [awslabs/git-secrets](https://github.com/awslabs/git-secrets)
```bash
git secrets --install
git secrets --register-aws
```

🔧 **Gitleaks** (Open Source)
- SAST tool for detecting secrets
- GitHub: [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks)
```bash
gitleaks detect --source . --verbose
```

### **Infrastructure as Code Security**
🔧 **tfsec** (Open Source)
- Terraform security scanner
- GitHub: [aquasecurity/tfsec](https://github.com/aquasecurity/tfsec)
```bash
brew install tfsec
tfsec .
```

🔧 **Checkov** (Open Source)
- IaC security scanner (Terraform, CloudFormation, Kubernetes)
- GitHub: [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov)
```bash
pip install checkov
checkov -d infrastructure/
```

### **Container Security**
🔧 **Trivy** (Open Source)
- Vulnerability scanner for containers, IaC, SBOM
- GitHub: [aquasecurity/trivy](https://github.com/aquasecurity/trivy)
```bash
trivy image python:3.11
```

### **PII Detection**
🔧 **Microsoft Presidio** (Open Source)
- PII detection and anonymization
- GitHub: [microsoft/presidio](https://github.com/microsoft/presidio)
```python
from presidio_analyzer import AnalyzerEngine
analyzer = AnalyzerEngine()
results = analyzer.analyze(text="My SSN is 123-45-6789", language='en')
```

---

## Communities

### **AWS Communities**
🌍 **AWS re:Inforce** (Annual Conference)
- URL: [reinforce.awsevents.com](https://reinforce.awsevents.com/)
- Focus: Cloud security
- Sessions, workshops, networking

🌍 **AWS Security Forums**
- URL: [repost.aws/tags/TAjybM38hSQiO01aZVEQxIVA/security](https://repost.aws/tags/TAjybM38hSQiO01aZVEQxIVA/security)
- Community Q&A

### **Security Communities**
🌍 **OWASP Cloud Security**
- URL: [owasp.org/www-project-cloud-security/](https://owasp.org/www-project-cloud-security/)
- Cloud security testing guide

🌍 **Reddit r/AWSCloud**
- URL: [reddit.com/r/AWSCloud](https://reddit.com/r/AWSCloud)
- Active community discussions

🌍 **Slack - AWS Developers Community**
- URL: [awsdevelopers.slack.com](https://awsdevelopers.slack.com/)
- Real-time help and discussions

---

## Compliance Frameworks

### **GDPR**
📋 [GDPR Official Text](https://gdpr-info.eu/)
📋 [AWS GDPR Data Processing Addendum (DPA)](https://aws.amazon.com/compliance/gdpr-center/)

### **HIPAA**
📋 [HIPAA Regulations](https://www.hhs.gov/hipaa/index.html)
📋 [AWS HIPAA Compliance Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/architecting-hipaa-security-and-compliance-on-aws/welcome.html)

### **PCI-DSS**
📋 [PCI Security Standards](https://www.pcisecuritystandards.org/)
📋 [AWS PCI-DSS Compliance Package](https://aws.amazon.com/compliance/pci-dss-level-1-faqs/)

### **SOC 2**
📋 [AICPA SOC 2 Overview](https://www.aicpa.org/soc2)
📋 [AWS SOC Reports](https://aws.amazon.com/compliance/soc-faqs/)

### **ISO 27001**
📋 [ISO 27001 Standard](https://www.iso.org/isoiec-27001-information-security.html)
📋 [AWS ISO 27001 Certification](https://aws.amazon.com/compliance/iso-27001-faqs/)

### **CIS Benchmarks**
📋 [CIS AWS Foundations Benchmark v1.5](https://www.cisecurity.org/benchmark/amazon_web_services)
- Automated compliance checks

---

## Learning Path Recommendations

### **Beginner** (0-6 months)
1. Read: AWS Security Fundamentals (course)
2. Practice: Create IAM policies, enable MFA
3. Tool: Run Prowler on personal AWS account
4. Certification: AWS Certified Cloud Practitioner

### **Intermediate** (6-12 months)
1. Read: "AWS Security" by Dylan Shield
2. Practice: Exercise 01-06 from this module
3. Tool: Set up CloudTrail, GuardDuty, Security Hub
4. Certification: AWS Certified Solutions Architect - Associate

### **Advanced** (12-24 months)
1. Read: "Mastering AWS Security"
2. Practice: Build multi-account security architecture
3. Tool: Implement automated incident response
4. Certification: AWS Certified Security - Specialty

### **Expert** (24+ months)
1. Read: AWS Security Blog (weekly)
2. Practice: Contribute to open-source security tools
3. Tool: Build custom compliance automation
4. Certification: AWS Certified Solutions Architect - Professional

---

## Next Steps

✅ **Complete this module's exercises** (hands-on practice)
✅ **Read AWS Security Best Practices** (foundational knowledge)
✅ **Join AWS Security community** (networking, learning)
✅ **Set up security tooling** (Prowler, git-secrets, etc.)
✅ **Plan certification path** (Security Specialty recommended)

---

## Additional Resources

- 🔗 [AWS Security Workshops](https://workshops.aws/)
- 🔗 [AWS Security Maturity Model](https://maturitymodel.security.aws.dev/)
- 🔗 [AWS Security Incident Response Guide](https://docs.aws.amazon.com/whitepapers/latest/aws-security-incident-response-guide/)
- 🔗 [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
