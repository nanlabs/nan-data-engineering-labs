# Security Architecture Patterns

## Table of Contents
- [Multi-Account Architecture](#multi-account-architecture)
- [Network Security Architecture](#network-security-architecture)
- [Data Platform Security](#data-platform-security)
- [Zero Trust Architecture](#zero-trust-architecture)
- [Reference Architectures](#reference-architectures)

---

## Multi-Account Architecture

### AWS Organizations Structure

```
Root Organization
├── Security OU
│   ├── Security Tooling Account (GuardDuty, Security Hub)
│   ├── Log Archive Account (CloudTrail, VPC Flow Logs)
│   └── Audit Account (Read-only access for auditors)
│
├── Infrastructure OU
│   ├── Network Account (Transit Gateway, VPN)
│   └── Shared Services Account (AD, DNS)
│
├── Workloads OU
│   ├── Production Account
│   ├── Staging Account
│   └── Development Account
│
└── Sandbox OU
    └── Experiment Accounts (isolated)
```

### **Benefits of Multi-Account Strategy**:
- **Isolation**: Blast radius containment, workload separation
- **Billing**: Cost allocation by business unit
- **Compliance**: Regulatory boundaries (PCI-DSS workloads isolated)
- **Governance**: Centralized policy enforcement with SCPs

### **Service Control Policies (SCPs)**:

**Deny leaving organization**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Action": "organizations:LeaveOrganization",
    "Resource": "*"
  }]
}
```

**Deny disabling security services**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Action": [
      "guardduty:DeleteDetector",
      "guardduty:DisassociateFromMasterAccount",
      "securityhub:DisableSecurityHub",
      "config:DeleteConfigurationRecorder",
      "cloudtrail:StopLogging",
      "cloudtrail:DeleteTrail"
    ],
    "Resource": "*"
  }]
}
```

### **AWS Control Tower**:
- **Guardrails**: Preventive (SCPs) and detective (Config rules)
- **Account Factory**: Automated account provisioning
- **Landing Zone**: Pre-configured multi-account baseline
- **Dashboards**: Compliance visibility across organization

---

## Network Security Architecture

### **VPC Design for Data Platform**

```
┌─────────────────────────────────────────────────────────────┐
│                     VPC (10.0.0.0/16)                       │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │   Public Subnets        │  │   Private Subnets       │  │
│  │   (10.0.1.0/24)        │  │   (10.0.10.0/24)       │  │
│  │                         │  │                         │  │
│  │  ┌─────────────┐       │  │  ┌─────────────┐       │  │
│  │  │   NAT GW    │ ─────────▶  │   EMR       │       │  │
│  │  └─────────────┘       │  │  │   Redshift  │       │  │
│  │  ┌─────────────┐       │  │  │   RDS       │       │  │
│  │  │   ALB       │       │  │  └─────────────┘       │  │
│  │  └─────────────┘       │  │                         │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │               Isolated Subnets                        │ │
│  │               (10.0.20.0/24)                          │ │
│  │                                                       │ │
│  │      ┌─────────────┐     ┌─────────────┐            │ │
│  │      │  S3 Gateway │     │ DynamoDB GW │            │ │
│  │      │  Endpoint   │     │  Endpoint   │            │ │
│  │      └─────────────┘     └─────────────┘            │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Security Groups (Stateful)**:

**Data engineers: SSH + web access**:
```python
{
    "IpProtocol": "tcp",
    "FromPort": 22,
    "ToPort": 22,
    "IpRanges": [{"CidrIp": "10.0.0.0/8", "Description": "Internal only"}]
}
```

**EMR cluster: Internal communication**:
```python
{
    "IpProtocol": "-1",  # All protocols
    "SourceSecurityGroupId": "sg-emr-cluster"  # Self-referencing
}
```

### **Network ACLs (Stateless)**:

**Deny known bad IPs**:
```python
{
    "RuleNumber": 50,
    "Protocol": "-1",
    "RuleAction": "deny",
    "CidrBlock": "192.0.2.0/24",  # Known threat actor
    "Egress": False
}
```

### **VPC Endpoints (PrivateLink)**:

**Benefits**:
- Traffic doesn't leave AWS network
- No NAT Gateway costs for AWS services
- Improved security (no internet exposure)

**Types**:
- **Gateway Endpoints**: S3, DynamoDB (free)
- **Interface Endpoints**: KMS, Secrets Manager, STS (charged)

**Example: S3 Gateway Endpoint**:
```python
import boto3

ec2 = boto3.client('ec2')

response = ec2.create_vpc_endpoint(
    VpcId='vpc-12345',
    ServiceName='com.amazonaws.us-east-1.s3',
    RouteTableIds=['rtb-12345'],
    PolicyDocument=json.dumps({
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::secure-data-lake/*"
        }]
    })
)
```

### **AWS PrivateLink for Data Sharing**:

```
┌──────────────────┐                       ┌──────────────────┐
│  Consumer VPC    │                       │  Provider VPC    │
│                  │                       │                  │
│  ┌────────────┐  │    PrivateLink        │  ┌────────────┐  │
│  │    EC2     │──┼───────────────────────┼──│    NLB     │  │
│  │ Consumer   │  │   (Private IP)        │  │            │  │
│  └────────────┘  │                       │  └────────────┘  │
│                  │                       │        │         │
└──────────────────┘                       │  ┌────▼──────┐  │
                                           │  │  Target   │  │
                                           │  │  Service  │  │
                                           │  └───────────┘  │
                                           └──────────────────┘
```

---

## Data Platform Security Architecture

### **Secure Data Lake**

```
┌────────────────────────────────────────────────────────────────┐
│                         Ingestion Layer                        │
│                                                                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐   │
│  │   Kinesis   │ ───▶ │   Lambda    │ ───▶ │   Kinesis   │   │
│  │  Firehose   │      │  (Validate) │      │  Data       │   │
│  └─────────────┘      └─────────────┘      │  Streams    │   │
│                                              └──────┬──────┘   │
└────────────────────────────────────────────────────┼──────────┘
                                                      │
┌────────────────────────────────────────────────────┼──────────┐
│                         Storage Layer              │          │
│                                                     ▼          │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                   S3 Data Lake                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │ Raw Zone     │  │ Curated Zone │  │ Trusted Zone │ │   │
│  │  │ (SSE-KMS)    │  │ (SSE-KMS)    │  │ (SSE-KMS)    │ │   │
│  │  │ Encryption   │  │ Encryption   │  │ Encryption   │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  │       │                   │                   │         │   │
│  └───────┼───────────────────┼───────────────────┼─────────┘   │
│          │                   │                   │             │
│  ┌───────▼───────────────────▼───────────────────▼─────────┐   │
│  │              AWS Lake Formation                         │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │  Fine-grained Access Control                     │   │   │
│  │  │  - Table-level permissions                       │   │   │
│  │  │  - Column-level permissions                      │   │   │
│  │  │  - Row-level filters                             │   │   │
│  │  │  - LF-Tags (TBAC)                                │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────┐
│                    Processing Layer│                            │
│                                    ▼                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │     EMR     │  │   Glue ETL  │  │   Athena    │            │
│  │  (Spark)    │  │   (PySpark) │  │  (Presto)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                   │
└────────────────────────────┼───────────────────────────────────┘
                             │
┌────────────────────────────┼───────────────────────────────────┐
│                    Consumption Layer                           │
│                            ▼                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Redshift   │  │  QuickSight │  │     API     │            │
│  │ (Spectrum)  │  │ (Dashboards)│  │  (Lambda)   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    Security & Governance                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   KMS Keys   │  │  CloudTrail  │  │   Macie      │         │
│  │  (Envelope   │  │  (Audit Log) │  │  (PII Scan)  │         │
│  │  Encryption) │  └──────────────┘  └──────────────┘         │
│  └──────────────┘                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  GuardDuty   │  │ Security Hub │  │   Config     │         │
│  │  (Threat     │  │  (Findings   │  │  (Compliance)│         │
│  │  Detection)  │  │  Aggregation)│  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────────────┘
```

### **Security Controls by Layer**:

| Layer | Security Controls |
|-------|-------------------|
| **Ingestion** | - Input validation (Lambda)<br>- Kinesis Data Analytics (anomaly detection)<br>- VPC endpoints for data sources |
| **Storage** | - S3 bucket encryption (SSE-KMS)<br>- Versioning enabled<br>- MFA delete<br>- Object Lock (WORM)<br>- Block public access |
| **Processing** | - EMR security configurations (encryption at rest/transit)<br>- Glue job bookmarks (idempotent)<br>- IAM roles for service access |
| **Consumption** | - Redshift encryption<br>- QuickSight row-level security<br>- API Gateway auth (IAM, Cognito, Lambda authorizers) |
| **Governance** | - Lake Formation permissions<br>- CloudTrail data events<br>- Macie sensitive data discovery |

---

## Zero Trust Architecture

### **Core Principles**:
1. **Never trust, always verify**: Authenticate every request
2. **Least privilege access**: Grant minimal permissions
3. **Assume breach**: Design for compromise scenarios
4. **Verify explicitly**: Use all available signals (identity, location, device)
5. **Microsegmentation**: Isolate workloads

### **Implementation on AWS**:

```
┌────────────────────────────────────────────────────────────────┐
│                       User/Application                         │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                  Identity Verification                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - AWS IAM / AWS SSO                                     │  │
│  │  - Multi-Factor Authentication (MFA)                     │  │
│  │  - Conditional Access (IP, time, device)                │  │
│  │  - Session policies (dynamic permissions)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                     Policy Enforcement                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - Service Control Policies (SCPs)                       │  │
│  │  - Permission Boundaries                                 │  │
│  │  - IAM Policies (identity-based, resource-based)         │  │
│  │  - Security Groups (network-level)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                   Continuous Monitoring                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - CloudTrail (API calls)                                │  │
│  │  - VPC Flow Logs (network traffic)                       │  │
│  │  - GuardDuty (threat detection)                          │  │
│  │  - IAM Access Analyzer (unintended access)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                  Automated Response                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - EventBridge (detection)                               │  │
│  │  - Lambda (response functions)                           │  │
│  │  - Systems Manager (remediation)                         │  │
│  │  - Security Hub (findings aggregation)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### **Zero Trust for Data Access**:

**Dynamic permissions with session policies**:
```python
import boto3
import json

sts = boto3.client('sts')

# Assume role with session policy (restricts base role permissions)
response = sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/DataScientist',
    RoleSessionName='scientist-session-123',
    DurationSeconds=3600,
    Policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::data-lake/curated/non-pii/*",
            "Condition": {
                "IpAddress": {"aws:SourceIp": "10.0.0.0/8"},
                "DateGreaterThan": {"aws:CurrentTime": "2024-01-01T00:00:00Z"},
                "DateLessThan": {"aws:CurrentTime": "2024-12-31T23:59:59Z"}
            }
        }]
    })
)

# Use temporary credentials
credentials = response['Credentials']
```

---

## Reference Architectures

### **1. HIPAA-Compliant Data Analytics Platform**

```
┌────────────────────────────────────────────────────────────────┐
│                    Requirements                                │
│  - BAA with AWS                                                │
│  - PHI encryption at rest/transit                              │
│  - Audit logging (6 years retention)                           │
│  - Access controls (minimum necessary)                         │
└────────────────────────────────────────────────────────────────┘

Architecture:
- VPC with private subnets (no internet gateway)
- S3 buckets with SSE-KMS (customer-managed keys)
- RDS PostgreSQL with encryption, automated backups
- EMR with encryption at rest/transit, Kerberos auth
- CloudTrail organization trail with log validation
- AWS Config rules (encrypted volumes, MFA, etc.)
- VPC Flow Logs (detect anomalous access)
```

### **2. PCI-DSS Compliant Payment Data Platform**

```
┌────────────────────────────────────────────────────────────────┐
│                PCI-DSS Requirements                            │
│  Requirement 1: Install firewall (Security Groups, NACLs)     │
│  Requirement 3: Protect stored cardholder data (tokenization) │
│  Requirement 4: Encrypt transmission (TLS 1.2+)               │
│  Requirement 8: Identify and authenticate access (MFA)        │
│  Requirement 10: Track and monitor (CloudTrail, GuardDuty)    │
└────────────────────────────────────────────────────────────────┘

Architecture:
- Isolated VPC (Cardholder Data Environment - CDE)
- Tokenization service (DynamoDB with encryption)
- API Gateway with mutual TLS
- Lambda functions (no cardholder data in logs)
- Redshift (non-sensitive analytics only)
- Security Hub (CIS AWS + PCI-DSS standards)
```

### **3. GDPR-Compliant European Data Platform**

```
┌────────────────────────────────────────────────────────────────┐
│                    GDPR Requirements                           │
│  - Data residency (EU regions only)                           │
│  - Right to erasure (data deletion)                           │
│  - Data minimization (collect only necessary)                 │
│  - Breach notification (72 hours)                             │
└────────────────────────────────────────────────────────────────┘

Architecture:
- S3 buckets in eu-west-1 (Ireland) or eu-central-1 (Frankfurt)
- S3 Object Lock (prevent deletion for 30 days - investigation)
- Lifecycle policies (automatic deletion after retention period)
- Macie for PII discovery
- EventBridge + SNS for breach notification
- Data deletion workflows (Step Functions)
```

---

## Key Takeaways

✅ **Multi-account strategy**: Isolate workloads, enforce governance with SCPs
✅ **Network security**: VPC design, security groups, PrivateLink, endpoints
✅ **Data lake security**: Encryption, Lake Formation, fine-grained access
✅ **Zero Trust**: Never trust, always verify, least privilege
✅ **Reference architectures**: HIPAA, PCI-DSS, GDPR patterns

---

## Additional Resources

- [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [AWS Multi-Account Strategy](https://aws.amazon.com/organizations/getting-started/best-practices/)
