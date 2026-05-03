# Architecture Diagrams - Module 16: Data Security & Compliance

This directory contains Mermaid diagrams illustrating data security, encryption, compliance, and governance patterns on AWS.

## Diagrams

### 1. IAM Security Architecture
**File**: [iam-security-architecture.mmd](iam-security-architecture.mmd)

Shows identity and access management:
- **IAM Users, Groups, Roles**: Least-privilege policies
- **Permission Boundaries**: Maximum permissions
- **Service Control Policies (SCPs)**: Organization-wide guardrails
- **Cross-Account Access**: AssumeRole patterns

**Use Cases**:
- Multi-account data access
- Federated identity (SAML/OIDC)
- Data scientist personas with limited access

**Example**: Data engineer role with S3 read-only, Glue job execution

---

### 2. Data Encryption Flow
**File**: [data-encryption-flow.mmd](data-encryption-flow.mmd)

Shows encryption architecture:
- **KMS Customer Master Keys (CMKs)**: Key management
- **Envelope Encryption**: Data key encryption
- **At-Rest Encryption**: S3, RDS, DynamoDB, Redshift
- **In-Transit Encryption**: TLS/SSL

**Use Cases**:
- Protect sensitive customer data
- Meet compliance requirements (HIPAA, PCI-DSS)
- Client-side encryption for high security

**Example**: S3 bucket with SSE-KMS encryption and key rotation

---

### 3. PII Detection & Masking
**File**: [pii-detection-masking.mmd](pii-detection-masking.mmd)

Shows data protection workflow:
- **PII Detection**: Macie, Comprehend Medical
- **Data Masking**: Dynamic masking in queries
- **Tokenization**: Replace PII with tokens
- **Anonymization**: K-anonymity, differential privacy

**Use Cases**:
- GDPR compliance (right to erasure)
- HIPAA protected health information
- Credit card number masking

**Example**: Mask SSN in analytics queries (XXX-XX-1234)

---

### 4. Compliance & Audit Trail
**File**: [compliance-audit-trail.mmd](compliance-audit-trail.mmd)

Shows audit and compliance architecture:
- **CloudTrail**: API call logging (5-year retention)
- **AWS Config**: Resource configuration compliance
- **Compliance Frameworks**: GDPR, HIPAA, SOC 2, PCI-DSS
- **Automated Remediation**: Lambda functions for violations

**Use Cases**:
- Audit who accessed what data and when
- Prove compliance for certifications
- Detect unauthorized data access

**Example**: Track all S3 GetObject calls for sensitive data

---

### 5. Lake Formation Access Control
**File**: [lake-formation-access-control.mmd](lake-formation-access-control.mmd)

Shows fine-grained access:
- **Table-Level Permissions**: Grant SELECT on specific tables
- **Column-Level Security**: Restrict PII columns
- **Row-Level Security**: Filter based on user attributes
- **Tag-Based Access**: LF-Tags for scalable permissions

**Use Cases**:
- Data lake with multiple teams
- Restrict PII access to authorized users
- Regional data residency enforcement

**Example**: Analysts can query sales data but not customer emails

---

### 6. Threat Detection & Response
**File**: [threat-detection-response.mmd](threat-detection-response.mmd)

Shows security monitoring:
- **GuardDuty**: ML-based threat detection
- **Security Hub**: Centralized security findings
- **CloudWatch Alarms**: Anomaly detection
- **Incident Response**: Automated playbooks

**Use Cases**:
- Detect compromised IAM credentials
- Alert on unusual data access patterns
- Automated incident response

**Example**: GuardDuty detects exfiltration attempt → SNS alert → Lambda isolates instance

---

## How to Use Diagrams

### Rendering Mermaid

**VS Code** (with Mermaid extension):
```bash
code --install-extension bierner.markdown-mermaid
code iam-security-architecture.mmd
```

**Online**:
- [Mermaid Live Editor](https://mermaid.live/)

### Exporting to Image

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i data-encryption-flow.mmd -o data-encryption-flow.png
```

---

## Exercise Mapping

| Exercise | Diagrams |
|----------|----------|
| Exercise 01 (IAM & Access Control) | iam-security-architecture |
| Exercise 02 (Data Encryption) | data-encryption-flow |
| Exercise 03 (PII Detection & Masking) | pii-detection-masking |
| Exercise 04 (Compliance & Audit) | compliance-audit-trail |
| Exercise 05 (Lake Formation) | lake-formation-access-control |
| Exercise 06 (Threat Detection) | threat-detection-response |

---

## Security Pattern Flow

```
Identity (IAM Roles, Federated Users)
    ↓
Authentication (Cognito, SAML, OIDC)
    ↓
Authorization (Lake Formation, IAM Policies)
    ↓
Encryption (KMS, TLS)
    ↓
Data Access (S3, Redshift, Athena)
    ↓
Audit Logging (CloudTrail, Config)
    ↓
Threat Detection (GuardDuty, Security Hub)
    ↓
Incident Response (Lambda, SNS, EventBridge)
```

---

## Customization

All diagrams use consistent styling:
- **Blue**: IAM/Identity
- **Green**: Encryption/Security
- **Orange**: Data stores
- **Red**: Threats/Violations
- **Purple**: Monitoring/Alerts

---

## Resources

### AWS Documentation
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [KMS Developer Guide](https://docs.aws.amazon.com/kms/)
- [Lake Formation Security](https://docs.aws.amazon.com/lake-formation/latest/dg/security.html)
- [GuardDuty User Guide](https://docs.aws.amazon.com/guardduty/)

### Compliance Frameworks
- **GDPR**: Data protection regulation (EU)
- **HIPAA**: Healthcare data (US)
- **SOC 2**: Security controls certification
- **PCI-DSS**: Payment card industry standards

### Real-World Examples
- **Netflix**: 100% encrypted data at rest and transit
- **Capital One**: Column-level encryption in Redshift
- **Goldman Sachs**: FIPS 140-2 validated KMS keys

---

## Notes

- All diagrams show production-ready architectures
- Security is defense-in-depth (multiple layers)
- Least-privilege principle applied throughout
- Compliance automation reduces manual audits
- Encryption adds <5% performance overhead
