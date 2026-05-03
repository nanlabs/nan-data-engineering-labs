# Security & Compliance Concepts

## Overview

This document covers fundamental concepts of data security, encryption, compliance frameworks, and governance principles essential for building secure data platforms on AWS.

---

## Table of Contents

1. [Security Fundamentals](#security-fundamentals)
2. [Identity & Access Management](#identity--access-management)
3. [Encryption & Key Management](#encryption--key-management)
4. [Data Privacy & Protection](#data-privacy--protection)
5. [Compliance Frameworks](#compliance-frameworks)
6. [Audit & Monitoring](#audit--monitoring)
7. [Incident Response](#incident-response)

---

## Security Fundamentals

### CIA Triad

The foundation of information security:

```
┌────────────────────────────────┐
│         CIA TRIAD              │
│                                │
│  ┌──────────────────────────┐  │
│  │   CONFIDENTIALITY        │  │
│  │   - Encryption           │  │
│  │   - Access control       │  │
│  │   - Data classification  │  │
│  └──────────────────────────┘  │
│                                │
│  ┌──────────────────────────┐  │
│  │   INTEGRITY              │  │
│  │   - Hashing              │  │
│  │   - Digital signatures   │  │
│  │   - Checksums            │  │
│  └──────────────────────────┘  │
│                                │
│  ┌──────────────────────────┐  │
│  │   AVAILABILITY           │  │
│  │   - Redundancy           │  │
│  │   - Disaster recovery    │  │
│  │   - DDoS protection      │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
```

**Confidentiality**: Only authorized users can access data
**Integrity**: Data accuracy and consistency maintained
**Availability**: Data accessible when needed

### Defense in Depth

Layered security approach:

1. **Physical Layer**: Data center security
2. **Network Layer**: VPCs, security groups, NACLs
3. **Host Layer**: OS hardening, patching
4. **Application Layer**: WAF, input validation
5. **Data Layer**: Encryption, masking
6. **User Layer**: MFA, strong passwords

### Principle of Least Privilege

**Definition**: Grant minimum permissions necessary to perform a task

**Benefits**:
- Reduces attack surface
- Limits blast radius of compromised credentials
- Simplifies audit and compliance

**Implementation**:
```python
# Bad: Overly permissive
{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
}

# Good: Specific permissions
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:ListBucket"
    ],
    "Resource": [
        "arn:aws:s3:::data-lake-curated/*",
        "arn:aws:s3:::data-lake-curated"
    ],
    "Condition": {
        "StringEquals": {
            "s3:x-amz-server-side-encryption": "aws:kms"
        }
    }
}
```

### Zero Trust Security

**Principle**: Never trust, always verify

**Key Components**:
- Verify explicitly (MFA, device health)
- Least privilege access
- Assume breach (microsegmentation, encryption everywhere)
- Continuous monitoring

---

## Identity & Access Management

### Authentication vs Authorization

**Authentication**: Verify identity ("Who are you?")
- Username/password
- Multi-factor authentication (MFA)
- Biometrics
- SSO (SAML, OAuth, OIDC)

**Authorization**: Control access ("What can you do?")
- IAM policies
- Resource-based policies
- Permission boundaries
- Service control policies (SCPs)

### IAM Components

**IAM User**: Individual AWS account
**IAM Group**: Collection of users
**IAM Role**: Assumable identity for services/applications
**IAM Policy**: JSON document defining permissions

**Policy Types**:
1. **Identity-Based**: Attached to users, groups, roles
2. **Resource-Based**: Attached to resources (S3 bucket policy)
3. **Permission Boundaries**: Maximum permissions limit
4. **Service Control Policies (SCPs)**: Organization-wide restrictions

### IAM Best Practices

1. **Enable MFA** for all users, especially root
2. **Use roles** instead of access keys
3. **Rotate credentials** regularly (90 days)
4. **Apply permission boundaries** to delegate safely
5. **Monitor with IAM Access Analyzer**
6. **Use conditions** in policies (time, IP, MFA)
7. **Delete unused** credentials and roles

### Federated Access

**SAML 2.0**: Enterprise SSO (Active Directory → AWS)
**OIDC**: Web identity federation (Google, Facebook)
**AWS SSO**: Centralized access management

**Benefits**:
- Single source of truth for identities
- No long-term AWS credentials
- Audit trail in corporate IdP

---

## Encryption & Key Management

### Types of Encryption

**Symmetric Encryption**: Same key for encryption/decryption
- Algorithms: AES-256, AES-128
- Fast, suitable for large data
- Key distribution challenge

**Asymmetric Encryption**: Public/private key pair
- Algorithms: RSA, ECC
- Public key encrypts, private key decrypts
- Slower, used for key exchange

### Encryption at Rest

**S3 Encryption Options**:
1. **SSE-S3**: S3-managed keys (AES-256)
2. **SSE-KMS**: KMS-managed keys (CMK)
3. **SSE-C**: Customer-provided keys
4. **Client-Side**: Encrypt before upload

**Database Encryption**:
- RDS: KMS encryption, transparent data encryption (TDE)
- DynamoDB: KMS encryption (default)
- Redshift: KMS or CloudHSM

### Encryption in Transit

**TLS/SSL**:
- TLS 1.2+ required (TLS 1.0/1.1 deprecated)
- Certificate management with ACM
- HTTPS endpoints for all APIs

**VPN/Direct Connect**:
- IPsec tunnels
- MACsec for Direct Connect

### AWS KMS Concepts

**Customer Master Key (CMK)**: Top-level key resource
**Data Key**: Key used to encrypt data
**Envelope Encryption**: CMK encrypts data keys, data keys encrypt data

**Key Types**:
- **AWS Managed**: Created by AWS services
- **Customer Managed**: You create and manage
- **AWS Owned**: Used by AWS, not visible to you

**Key Policies**: Resource-based policy for CMK

**Grants**: Temporary delegation of key permissions

### Key Rotation

**Automatic Rotation**:
- AWS KMS: Yearly (365 days)
- Old key versions retained for decryption
- Transparent to applications

**Manual Rotation**:
- Create new CMK
- Update references in code
- Decrypt with old key, re-encrypt with new key

---

## Data Privacy & Protection

### PII (Personally Identifiable Information)

**Definition**: Information that identifies an individual

**Examples**:
- Direct identifiers: SSN, passport, driver's license
- Indirect identifiers: Name, email, phone, IP address
- Sensitive: Medical records, biometrics, financial data

### Data Classification

**Public**: No harm if disclosed
**Internal**: Internal use only
**Confidential**: Limited access, harm if disclosed
**Restricted**: Strict controls, severe harm if disclosed

### Data Masking Techniques

**Static Masking**: Permanent replacement
```python
# Original: john.smith@company.com
# Masked:   j***.s****@company.com
```

**Dynamic Masking**: Runtime masking based on user
```sql
-- Data engineer sees:
SELECT ssn FROM customers; -- '123-45-6789'

-- Analyst sees:
SELECT ssn FROM customers; -- 'XXX-XX-6789'
```

**Tokenization**: Reversible replacement
```python
# Original: 4532-1234-5678-9010
# Token:    TKN-CREDIT_CARD-abc123xyz
# Stored in encrypted vault for reversal
```

### Anonymization Techniques

**K-Anonymity**:
- Each record indistinguishable from k-1 others
- Generalization: Age 27 → 20-30
- Suppression: Remove identifying columns

**L-Diversity**:
- Each equivalence class has at least L distinct sensitive values
- Prevents homogeneity attack

**Differential Privacy**:
- Add statistical noise to results
- Mathematically proven privacy guarantee
- Used by Apple, Google, US Census

---

## Compliance Frameworks

### GDPR (General Data Protection Regulation)

**Scope**: EU residents' data
**Effective**: May 25, 2018

**Key Requirements**:
- **Lawful basis** for processing data
- **Data subject rights**: Access, rectification, erasure ("right to be forgotten"), portability
- **Privacy by design**: Build privacy into systems from start
- **Data breach notification**: Within 72 hours
- **Data Protection Officer (DPO)**: Required for large-scale processing
- **International transfers**: Adequacy decisions, SCCs, BCRs

**Penalties**: Up to €20M or 4% of global revenue (whichever is higher)

**AWS Tools**:
- Data residency: Choose EU regions
- Encryption: KMS, CloudHSM
- Access logs: CloudTrail
- Data deletion: S3 lifecycle policies, S3 Object Lock

### HIPAA (Health Insurance Portability and Accountability Act)

**Scope**: US healthcare data (PHI - Protected Health Information)

**Rules**:
- **Privacy Rule**: Standards for PHI use/disclosure
- **Security Rule**: Administrative, physical, technical safeguards
- **Breach Notification Rule**: Notify within 60 days

**Required Safeguards**:
- Access controls (unique user IDs, emergency access)
- Audit controls (log access to PHI)
- Integrity controls (detect unauthorized changes)
- Transmission security (encrypt PHI in transit)

**AWS HIPAA Eligibility**:
- Sign BAA (Business Associate Agreement)
- Use HIPAA-eligible services (EC2, S3, RDS, etc.)
- Enable encryption, logging, access controls

### PCI-DSS (Payment Card Industry Data Security Standard)

**Scope**: Credit card data (CHD - Cardholder Data)

**12 Requirements**:
1. Install and maintain firewall
2. No default passwords
3. Protect stored cardholder data (encrypt)
4. Encrypt transmission (TLS)
5. Antivirus software
6. Secure systems and applications
7. Restrict access (need-to-know)
8. Unique IDs for users
9. Restrict physical access
10. Track and monitor access
11. Test security regularly
12. Information security policy

**Compliance Levels**:
- **Level 1**: >6M transactions/year (annual on-site audit)
- **Level 2-4**: Fewer transactions (self-assessment)

### SOC 2 (Service Organization Control 2)

**Trust Service Criteria**:
- **Security**: Protection against unauthorized access
- **Availability**: System operational and usable
- **Processing Integrity**: Complete, accurate, timely processing
- **Confidentiality**: Protected as committed
- **Privacy**: Personal information collected, used, retained, disclosed per commitments

**Report Types**:
- **SOC 2 Type I**: Design of controls at a point in time
- **SOC 2 Type II**: Operating effectiveness over period (6-12 months)

### ISO 27001

**Standard**: Information Security Management System (ISMS)

**Domains**: 14 security control categories (114 controls total)

**Certification**: External audit against standard

---

## Audit & Monitoring

### CloudTrail

**Purpose**: API activity logging (who did what, when)

**Logged Events**:
- Management events: Control plane (CreateBucket, RunInstances)
- Data events: Data plane (GetObject, PutObject)
- Insights events: Unusual activity detection

**Best Practices**:
- Enable organization trail
- Send to CloudWatch Logs
- Enable log file validation
- Encrypt with KMS
- Enable S3 bucket versioning and MFA delete

### AWS Config

**Purpose**: Resource configuration tracking and compliance

**Config Rules**:
- Managed rules: AWS-provided (s3-bucket-encryption-enabled)
- Custom rules: Lambda-based

**Remediation**:
- Manual: Review and fix
- Automatic: SSM automation documents, Lambda

**Compliance Dashboard**: Visualize compliance status

### VPC Flow Logs

**Purpose**: Network traffic logging (accept/reject)

**Fields**: src IP, dst IP, src port, dst port, protocol, packets, bytes, action

**Use Cases**:
- Troubleshoot connectivity
- Detect suspicious traffic
- Analyze traffic patterns

### GuardDuty

**Purpose**: ML-powered threat detection

**Data Sources**:
- VPC Flow Logs
- DNS logs
- CloudTrail event logs
- S3 data events

**Finding Types**:
- Reconnaissance (port scanning)
- Instance compromise (malware, C&C)
- Account compromise (credential misuse)
- Bucket compromise (unusual data access)

---

## Incident Response

### IR Lifecycle

```
┌─────────────────────────────────────────────┐
│    INCIDENT RESPONSE LIFECYCLE              │
│                                             │
│  1. PREPARATION                             │
│     - IR plan, playbooks                    │
│     - Tools (forensics, backups)            │
│     - Training, drills                      │
│                                             │
│  2. DETECTION                               │
│     - GuardDuty, Security Hub               │
│     - CloudWatch alarms                     │
│     - User reports                          │
│                                             │
│  3. CONTAINMENT                             │
│     - Isolate compromised resources         │
│     - Disable credentials                   │
│     - Block malicious IPs                   │
│                                             │
│  4. ERADICATION                             │
│     - Remove malware                        │
│     - Patch vulnerabilities                 │
│     - Rebuild from clean images             │
│                                             │
│  5. RECOVERY                                │
│     - Restore from backups                  │
│     - Validate integrity                    │
│     - Monitor closely                       │
│                                             │
│  6. LESSONS LEARNED                         │
│     - Post-mortem analysis                  │
│     - Update playbooks                      │
│     - Improve defenses                      │
└─────────────────────────────────────────────┘
```

### Common Incident Types

**1. Compromised Credentials**
- Symptoms: Unusual API calls, resource creation
- Response: Disable access keys, revoke sessions, rotate secrets

**2. Data Exfiltration**
- Symptoms: Large data transfers, unusual S3 access
- Response: Block public access, isolate bucket, analyze logs

**3. Malware/Ransomware**
- Symptoms: CPU spikes, network activity, file encryption
- Response: Quarantine instance, snapshot for forensics, rebuild

**4. DDoS Attack**
- Symptoms: Service unavailability, high traffic
- Response: AWS Shield, CloudFront, WAF rules

### Forensics on AWS

**Evidence Collection**:
- EBS snapshots (disk images)
- Memory dumps (EC2 instance metadata)
- CloudTrail logs (API activity)
- VPC Flow Logs (network activity)
- S3 access logs

**Chain of Custody**: Document who accessed evidence and when

**Analysis Tools**:
- Amazon Detective (graph-based investigation)
- CloudWatch Logs Insights
- Athena queries on CloudTrail

---

## Key Takeaways

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Minimize permissions
3. **Encryption Everywhere**: At rest and in transit
4. **Continuous Monitoring**: GuardDuty, Config, CloudTrail
5. **Compliance**: Understand GDPR, HIPAA, PCI-DSS requirements
6. **Incident Response**: Prepare, practice, improve
7. **Automation**: Reduce MTTR with auto-remediation
8. **Privacy by Design**: Build security and privacy from start

---

## Additional Resources

- [AWS Security Documentation](https://docs.aws.amazon.com/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://d1.awsstatic.com/whitepapers/Security/AWS_Security_Best_Practices.pdf)
