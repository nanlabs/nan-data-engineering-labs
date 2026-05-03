# Module 16: Data Security & Compliance

## Overview

Master data security, encryption, access control, compliance frameworks, and governance in AWS. Learn to implement defense-in-depth strategies, data protection mechanisms, audit trails, and meet regulatory requirements (GDPR, HIPAA, SOC 2, PCI-DSS).

**Duration**: 16-18 hours
**Difficulty**: ⭐⭐⭐⭐ Expert
**Prerequisites**: Modules 02 (Storage), 05 (Data Lakehouse), 14 (Data Catalog)

## Learning Objectives

By completing this module, you will be able to:

1. **Implement IAM Best Practices**
   - Design least-privilege access policies
   - Configure IAM roles, policies, and permission boundaries
   - Implement identity federation (SAML, OIDC)
   - Use AWS Organizations for multi-account security

2. **Encrypt Data at Rest and in Transit**
   - Configure KMS keys with rotation policies
   - Implement envelope encryption patterns
   - Enable encryption for S3, RDS, DynamoDB, Redshift
   - Configure SSL/TLS for data in transit

3. **Implement Data Masking & Anonymization**
   - PII detection and redaction
   - Dynamic data masking in queries
   - Tokenization and pseudonymization
   - K-anonymity and differential privacy

4. **Establish Audit & Compliance**
   - Configure CloudTrail for audit logging
   - Use AWS Config for compliance rules
   - Implement automated compliance checks
   - Generate compliance reports

5. **Implement Data Governance**
   - Configure Lake Formation fine-grained access
   - Implement data lineage tracking
   - Establish data classification policies
   - Configure Glue Data Catalog security

6. **Monitor Security Threats**
   - Use GuardDuty for threat detection
   - Configure Security Hub for centralized monitoring
   - Implement SIEM with CloudWatch + Elasticsearch
   - Create incident response playbooks

## Exercises

### Exercise 01: IAM & Access Control (3 hours) - ⭐⭐⭐ Advanced
Implement least-privilege IAM policies for different personas, cross-account access, and permission boundaries.

### Exercise 02: Data Encryption (3 hours) - ⭐⭐⭐ Advanced
Configure KMS, encrypt data at rest/transit across S3, RDS, Redshift.

### Exercise 03: Data Masking & Anonymization (3 hours) - ⭐⭐⭐⭐ Expert
Detect PII with Macie/Comprehend, implement masking and tokenization.

### Exercise 04: Audit & Compliance (2.5 hours) - ⭐⭐⭐ Advanced
Configure CloudTrail, AWS Config rules, compliance reports.

### Exercise 05: Data Governance (3 hours) - ⭐⭐⭐⭐ Expert
Implement Lake Formation permissions, data lineage, tag-based access.

### Exercise 06: Security Monitoring (2.5 hours) - ⭐⭐⭐⭐ Expert
Deploy GuardDuty, Security Hub, build SIEM, incident response automation.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start infrastructure
make setup

# Validate
make validate
```

## Compliance Frameworks

- ✅ GDPR (General Data Protection Regulation)
- ✅ HIPAA (Health Insurance Portability and Accountability Act)
- ✅ PCI-DSS (Payment Card Industry Data Security Standard)
- ✅ SOC 2 (Service Organization Control 2)
- ✅ CIS AWS Foundations Benchmark

## Resources

See `theory/resources.md` for:
- Official AWS documentation
- Video tutorials and workshops
- Community resources
- Certification mapping

## Validation

Run all validations:
```bash
bash scripts/validate.sh
```

Or use the global validation:
```bash
make validate MODULE=module-{module_id}-{module["name"]}
```

## Progress Checklist

- [ ] Read all theory documentation
- [ ] Completed Exercise 01
- [ ] Completed Exercise 02
- [ ] Completed Exercise 03
- [ ] Completed Exercise 04
- [ ] Completed Exercise 05
- [ ] Completed Exercise 06
- [ ] All validations passing
- [ ] Ready for next module

## Next Steps

After completing this module, you'll be ready for:
[List of modules that depend on this one]
