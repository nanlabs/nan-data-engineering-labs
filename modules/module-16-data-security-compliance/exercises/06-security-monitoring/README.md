# Exercise 06: Security Monitoring & Incident Response

## Overview
Implement comprehensive security monitoring using Amazon GuardDuty, AWS Security Hub, EventBridge automation, SIEM with Elasticsearch/Kibana, incident response playbooks, and automated remediation.

**Difficulty**: ⭐⭐⭐⭐ Expert
**Duration**: ~2.5 hours
**Prerequisites**: Security operations, SIEM concepts, incident response

## Learning Objectives

- Enable Amazon GuardDuty for threat detection
- Configure AWS Security Hub multi-account aggregation
- Create EventBridge rules for security automation
- Build SIEM with Elasticsearch and Kibana
- Develop incident response playbooks
- Implement auto-remediation with Lambda + Systems Manager
- Conduct tabletop incident response exercises

## Key Concepts

- **GuardDuty**: ML-powered threat detection
- **Security Hub**: Centralized security findings aggregator
- **EventBridge**: Event-driven automation
- **SIEM**: Security Information and Event Management
- **IR Playbook**: Step-by-step incident response procedure
- **SOAR**: Security Orchestration, Automation, and Response
- **MTTR**: Mean Time To Respond/Remediate
- **IOC**: Indicators of Compromise

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         SECURITY MONITORING & RESPONSE ARCHITECTURE          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            THREAT DETECTION LAYER                     │   │
│  │                                                       │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────┐│   │
│  │  │  GuardDuty     │  │  Security Hub  │  │ Macie   ││   │
│  │  │  - VPC Flow    │  │  - CIS AWS     │  │ S3 PII  ││   │
│  │  │  - DNS Logs    │  │  - PCI-DSS     │  │ Discover││   │
│  │  │  - CloudTrail  │  │  - AWS Best    │  │         ││   │
│  │  │  - Threat Intel│  │    Practices   │  │         ││   │
│  │  └───────┬────────┘  └───────┬────────┘  └────┬────┘│   │
│  │          │                   │                │     │   │
│  │          └───────────────────┴────────────────┘     │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │                               │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         AGGREGATION & NORMALIZATION                   │   │
│  │                                                       │   │
│  │              AWS Security Hub                         │   │
│  │         (Security Finding Format - ASFF)             │   │
│  │                                                       │   │
│  │  Finding Severity: CRITICAL | HIGH | MEDIUM | LOW    │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │                               │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            AUTOMATED RESPONSE                         │   │
│  │                                                       │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │       Amazon EventBridge Rules                │   │   │
│  │  │                                              │   │   │
│  │  │  Rule 1: GuardDuty HIGH → Lambda Response   │   │   │
│  │  │  Rule 2: Unencrypted S3 → Auto-Encrypt      │   │   │
│  │  │  Rule 3: IAM Policy Change → Notify         │   │   │
│  │  │  Rule 4: Root Login → Alert + Disable       │   │   │
│  │  └──────────────────┬───────────────────────────┘   │   │
│  │                     │                                │   │
│  │         ┌───────────┼───────────┐                   │   │
│  │         ▼           ▼           ▼                   │   │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────┐             │   │
│  │  │ Lambda   │ │  SNS    │ │ Systems  │             │   │
│  │  │ Auto-    │ │ Alerts  │ │ Manager  │             │   │
│  │  │ Remediate│ │ PagerDuty│ │ Run Doc  │             │   │
│  │  └──────────┘ └─────────┘ └──────────┘             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SIEM & ANALYTICS                         │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  CloudWatch Logs → Kinesis Firehose         │    │   │
│  │  │          ↓                                   │    │   │
│  │  │  ElasticSearch (OpenSearch)                 │    │   │
│  │  │          ↓                                   │    │   │
│  │  │  Kibana Dashboards:                          │    │   │
│  │  │    - Threat Feed                            │    │   │
│  │  │    - Failed Logins                          │    │   │
│  │  │    - Privilege Escalation                   │    │   │
│  │  │    - Data Exfiltration Patterns             │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         INCIDENT RESPONSE PLAYBOOKS                   │   │
│  │                                                       │   │
│  │  1. Compromised IAM Credentials                      │   │
│  │     - Disable access keys                            │   │
│  │     - Revoke sessions                                │   │
│  │     - Analyze CloudTrail                             │   │
│  │     - Rotate all secrets                             │   │
│  │                                                       │   │
│  │  2. Data Exfiltration Attempt                        │   │
│  │     - Block S3 public access                         │   │
│  │     - Isolate compromised instance                   │   │
│  │     - Capture forensics snapshot                     │   │
│  │     - Analyze VPC flow logs                          │   │
│  │                                                       │   │
│  │  3. Malware Detected                                 │   │
│  │     - Quarantine instance                            │   │
│  │     - Run AV scan                                    │   │
│  │     - Collect memory dump                            │   │
│  │     - Rebuild from golden AMI                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Task 1: Enable GuardDuty (20 minutes)

**File**: `setup_guardduty.py`

```python
#!/usr/bin/env python3
\"\"\"Setup Amazon GuardDuty threat detection\"\"\"

import boto3
import json

guardduty = boto3.client('guardduty')
s3 = boto3.client('s3')
sts = boto3.client('sts')


def enable_guardduty():
    \"\"\"Enable GuardDuty\"\"\"

    print(\"\\n1. Enabling GuardDuty\")
    print(\"=\"*60)

    try:
        response = guardduty.create_detector(
            Enable=True,
            FindingPublishingFrequency='FIFTEEN_MINUTES',
            DataSources={
                'S3Logs': {'Enable': True},
                'Kubernetes': {'AuditLogs': {'Enable': True}}
            },
            Tags={'Environment': 'production', 'Purpose': 'threat-detection'}
        )

        detector_id = response['DetectorId']
        print(f\"✓ GuardDuty enabled\")
        print(f\"  Detector ID: {detector_id}\")
        print(f\"  S3 Protection: Enabled\")
        print(f\"  Kubernetes Protection: Enabled\")

        return detector_id

    except guardduty.exceptions.BadRequestException as e:
        # Already enabled
        detectors = guardduty.list_detectors()['DetectorIds']
        if detectors:
            detector_id = detectors[0]
            print(f\"  GuardDuty already enabled\")
            print(f\"  Detector ID: {detector_id}\")
            return detector_id
        raise e


def create_threat_intel_set(detector_id):
    \"\"\"Upload custom threat intelligence list\"\"\"

    print(\"\\n2. Creating Threat Intelligence Set\")
    print(\"=\"*60)

    account_id = sts.get_caller_identity()['Account']
    bucket_name = f'guardduty-threat-intel-{account_id}'

    # Create bucket
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f\"✓ Created bucket: {bucket_name}\")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f\"  Bucket exists: {bucket_name}\")

    # Upload threat IP list
    threat_ips = [
        '192.0.2.0',  # Example malicious IP
        '198.51.100.0',
        '203.0.113.0'
    ]

    threat_list = '\\n'.join(threat_ips)

    s3.put_object(
        Bucket=bucket_name,
        Key='threat-ip-list.txt',
        Body=threat_list.encode('utf-8')
    )
    print(f\"✓ Uploaded {len(threat_ips)} threat IPs\")

    # Create threat intel set
    try:
        response = guardduty.create_threat_intel_set(
            DetectorId=detector_id,
            Name='CustomThreatIPList',
            Format='TXT',
            Location=f'https://s3.amazonaws.com/{bucket_name}/threat-ip-list.txt',
            Activate=True
        )
        print(f\"✓ Created threat intel set\")
        print(f\"  Set ID: {response['ThreatIntelSetId']}\")
    except guardduty.exceptions.BadRequestException:
        print(f\"  Threat intel set already exists\")


def get_sample_findings(detector_id):
    \"\"\"Generate sample findings for testing\"\"\"

    print(\"\\n3. Generating Sample Findings\")
    print(\"=\"*60)

    finding_types = [
        'Recon:EC2/PortProbeUnprotectedPort',
        'UnauthorizedAccess:IAMUser/TorIPCaller',
        'CryptoCurrency:EC2/BitcoinTool.B!DNS',
        'Backdoor:EC2/C&CActivity.B!DNS',
        'Exfiltration:S3/ObjectRead.Unusual'
    ]

    try:
        response = guardduty.create_sample_findings(
            DetectorId=detector_id,
            FindingTypes=finding_types
        )
        print(f\"✓ Generated {len(finding_types)} sample findings\")
        for finding_type in finding_types:
            print(f\"  - {finding_type}\")
    except Exception as e:
        print(f\"✗ Error generating findings: {e}\")


def list_findings(detector_id):
    \"\"\"List current GuardDuty findings\"\"\"

    print(\"\\n4. Listing Current Findings\")
    print(\"=\"*60)

    try:
        # Get finding IDs
        response = guardduty.list_findings(
            DetectorId=detector_id,
            FindingCriteria={
                'Criterion': {
                    'severity': {'Gte': 4}  # Medium and above
                }
            },
            MaxResults=10
        )

        finding_ids = response.get('FindingIds', [])

        if not finding_ids:
            print(\"  No findings (this is good!)\")\n            return

        # Get finding details
        findings_response = guardduty.get_findings(
            DetectorId=detector_id,
            FindingIds=finding_ids
        )

        findings = findings_response.get('Findings', [])

        print(f\"\\nFound {len(findings)} finding(s):\\n\")

        for finding in findings:
            severity = finding.get('Severity', 0)
            title = finding.get('Title', 'Unknown')
            description = finding.get('Description', 'No description')

            severity_label = 'CRITICAL' if severity >= 8 else 'HIGH' if severity >= 7 else 'MEDIUM' if severity >= 4 else 'LOW'

            print(f\"  [{severity_label}] {title}\")
            print(f\"  Description: {description}\")
            print(f\"  Severity: {severity}/10\\n\")

    except Exception as e:
        print(f\"✗ Error listing findings: {e}\")


if __name__ == '__main__':
    print(\"=\"*60)
    print(\"SETTING UP AMAZON GUARDDUTY\")
    print(\"=\"*60)

    # Enable GuardDuty
    detector_id = enable_guardduty()

    # Add threat intelligence
    create_threat_intel_set(detector_id)

    # Generate sample findings for testing
    get_sample_findings(detector_id)

    # List findings
    list_findings(detector_id)

    print(\"\\n\" + \"=\"*60)
    print(\"✓ GUARDDUTY CONFIGURED\")
    print(\"=\"*60)
```

## Task 2: Configure Security Hub (30 minutes)

**File**: `setup_security_hub.py`

```python
#!/usr/bin/env python3
\"\"\"Setup AWS Security Hub\"\"\"

import boto3

securityhub = boto3.client('securityhub')


def enable_security_hub():
    \"\"\"Enable Security Hub\"\"\"

    print(\"\\n1. Enabling AWS Security Hub\")
    print(\"=\"*60)

    try:
        response = securityhub.enable_security_hub(
            Tags={'Environment': 'production', 'Purpose': 'security-monitoring'},
            EnableDefaultStandards=True
        )
        print(f\"✓ Security Hub enabled\")
        print(f\"  Hub ARN: {response['HubArn']}\")
    except securityhub.exceptions.ResourceConflictException:
        print(f\"  Security Hub already enabled\")


def enable_security_standards():
    \"\"\"Enable security standards (compliance frameworks)\"\"\"

    print(\"\\n2. Enabling Security Standards\")
    print(\"=\"*60)

    # Get available standards
    standards_response = securityhub.describe_standards()
    available_standards = standards_response.get('Standards', [])

    for standard in available_standards:
        standard_arn = standard['StandardsArn']
        standard_name = standard['Name']

        try:
            securityhub.batch_enable_standards(
                StandardsSubscriptionRequests=[
                    {'StandardsArn': standard_arn}
                ]
            )
            print(f\"✓ Enabled: {standard_name}\")
        except securityhub.exceptions.ResourceConflictException:
            print(f\"  Already enabled: {standard_name}\")


def enable_product_integrations():
    \"\"\"Enable product integrations\"\"\"

    print(\"\\n3. Enabling Product Integrations\")
    print(\"=\"*60)

    # Get available integrations
    products_response = securityhub.describe_products()
    available_products = products_response.get('Products', [])

    # Enable GuardDuty, IAM Access Analyzer, Macie
    target_products = ['GuardDuty', 'IAM Access Analyzer', 'Macie']

    for product in available_products:
        product_name = product['ProductName']
        product_arn = product['ProductArn']

        if any(target in product_name for target in target_products):
            try:
                securityhub.enable_import_findings_for_product(
                    ProductArn=product_arn
                )
                print(f\"✓ Enabled: {product_name}\")
            except securityhub.exceptions.ResourceConflictException:
                print(f\"  Already enabled: {product_name}\")


def get_security_score():
    \"\"\"Get security score summary\"\"\"

    print(\"\\n4. Security Score Summary\")
    print(\"=\"*60)

    try:
        # Get findings by severity
        response = securityhub.get_findings(
            Filters={
                'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}]
            },
            MaxResults=100
        )

        findings = response.get('Findings', [])

        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFORMATIONAL': 0}

        for finding in findings:
            severity = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        total = sum(severity_counts.values())

        print(f\"\\nTotal Findings: {total}\\n\")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL']:
            count = severity_counts[severity]
            if count > 0:
                print(f\"  {severity}: {count}\")\n
        # Calculate score (100 - weighted penalties)
        score = 100
        score -= severity_counts['CRITICAL'] * 10
        score -= severity_counts['HIGH'] * 5
        score -= severity_counts['MEDIUM'] * 2
        score -= severity_counts['LOW'] * 1
        score = max(0, score)

        print(f\"\\nSecurity Score: {score}/100\")

        if score >= 80:
            print(\"  Status: ✓ Good\")
        elif score >= 60:
            print(\"  Status: ⚠ Needs Improvement\")
        else:
            print(\"  Status: ✗ Critical Issues\")

    except Exception as e:
        print(f\"✗ Error calculating score: {e}\")


if __name__ == '__main__':
    print(\"=\"*60)
    print(\"SETTING UP AWS SECURITY HUB\")
    print(\"=\"*60)

    enable_security_hub()
    enable_security_standards()
    enable_product_integrations()
    get_security_score()

    print(\"\\n\" + \"=\"*60)
    print(\"✓ SECURITY HUB CONFIGURED\")
    print(\"=\"*60)
```

## Task 3: Automated Incident Response (45 minutes)

**File**: `incident_response_automation.py`

```python
#!/usr/bin/env python3
\"\"\"Automated incident response playbooks\"\"\"

import boto3
import json

events = boto3.client('events')
lambda_client = boto3.client('lambda')
sns = boto3.client('sns')
iam = boto3.client('iam')
sts = boto3.client('sts')


def create_sns_alert_topic():
    \"\"\"Create SNS topic for security alerts\"\"\"

    print(\"\\n1. Creating SNS Alert Topic\")
    print(\"=\"*60)

    try:
        response = sns.create_topic(
            Name='SecurityAlerts',
            Tags=[
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Purpose', 'Value': 'security-alerts'}
            ]
        )
        topic_arn = response['TopicArn']
        print(f\"✓ Created topic: SecurityAlerts\")
        print(f\"  ARN: {topic_arn}\")

        return topic_arn

    except sns.exceptions.TopicLimitExceededException:
        topics = sns.list_topics()['Topics']
        for topic in topics:
            if 'SecurityAlerts' in topic['TopicArn']:
                print(f\"  Topic already exists\")
                return topic['TopicArn']


def create_response_lambda_function():
    \"\"\"Create Lambda function for automated response\"\"\"

    print(\"\\n2. Creating Response Lambda Function\")
    print(\"=\"*60)

    # Lambda code for incident response
    lambda_code = '''
import boto3
import json

ec2 = boto3.client('ec2')
iam = boto3.client('iam')
s3 = boto3.client('s3')


def lambda_handler(event, context):
    \"\"\"Automated incident response\"\"\"

    detail = event.get('detail', {})
    finding_type = detail.get('type', '')
    severity = detail.get('severity', 0)

    print(f\"Processing finding: {finding_type} (severity: {severity})\")

    # Route to appropriate playbook
    if 'UnauthorizedAccess:IAMUser' in finding_type:
        return handle_compromised_credentials(detail)
    elif 'Exfiltration:S3' in finding_type:
        return handle_data_exfiltration(detail)
    elif 'CryptoCurrency' in finding_type or 'Backdoor' in finding_type:
        return handle_malware_detection(detail)
    else:
        return {'status': 'no_action', 'message': 'No playbook for this finding type'}


def handle_compromised_credentials(detail):
    \"\"\"Playbook: Compromised IAM credentials\"\"\"

    print(\"Executing: Compromised Credentials Playbook\")

    # Extract IAM user from finding
    resource = detail.get('resource', {})
    access_key_details = resource.get('accessKeyDetails', {})
    user_name = access_key_details.get('userName')
    access_key_id = access_key_details.get('accessKeyId')

    actions_taken = []

    if user_name and access_key_id:
        try:
            # Disable access key
            iam.update_access_key(
                UserName=user_name,
                AccessKeyId=access_key_id,
                Status='Inactive'
            )
            actions_taken.append(f\"Disabled access key: {access_key_id}\")

            # Attach deny policy
            deny_policy = {
                \"Version\": \"2012-10-17\",
                \"Statement\": [{
                    \"Effect\": \"Deny\",
                    \"Action\": \"*\",
                    \"Resource\": \"*\"
                }]
            }

            iam.put_user_policy(
                UserName=user_name,
                PolicyName='EmergencyDenyAll',
                PolicyDocument=json.dumps(deny_policy)
            )
            actions_taken.append(f\"Applied deny-all policy to user: {user_name}\")

        except Exception as e:
            actions_taken.append(f\"Error: {str(e)}\")

    return {'status': 'success', 'actions': actions_taken}


def handle_data_exfiltration(detail):
    \"\"\"Playbook: Data exfiltration attempt\"\"\"

    print(\"Executing: Data Exfiltration Playbook\")

    resource = detail.get('resource', {})
    s3_bucket_details = resource.get('s3BucketDetails', [])

    actions_taken = []

    for bucket_detail in s3_bucket_details:
        bucket_name = bucket_detail.get('name')

        if bucket_name:
            try:
                # Block public access
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                actions_taken.append(f\"Blocked public access on bucket: {bucket_name}\")

            except Exception as e:
                actions_taken.append(f\"Error on {bucket_name}: {str(e)}\")

    return {'status': 'success', 'actions': actions_taken}


def handle_malware_detection(detail):
    \"\"\"Playbook: Malware detected on EC2\"\"\"

    print(\"Executing: Malware Detection Playbook\")

    resource = detail.get('resource', {})
    instance_details = resource.get('instanceDetails', {})
    instance_id = instance_details.get('instanceId')

    actions_taken = []

    if instance_id:
        try:
            # Isolate instance (remove from all security groups except quarantine)
            response = ec2.describe_instances(InstanceIds=[instance_id])

            if response['Reservations']:
                instance = response['Reservations'][0]['Instances'][0]
                vpc_id = instance.get('VpcId')

                # Create quarantine security group
                sg_response = ec2.create_security_group(
                    GroupName=f'quarantine-{instance_id}',
                    Description='Quarantine security group - no inbound/outbound',
                    VpcId=vpc_id
                )
                quarantine_sg = sg_response['GroupId']

                # Assign quarantine SG
                ec2.modify_instance_attribute(
                    InstanceId=instance_id,
                    Groups=[quarantine_sg]
                )

                actions_taken.append(f\"Quarantined instance: {instance_id}\")

                # Create snapshot for forensics
                for device in instance.get('BlockDeviceMappings', []):
                    volume_id = device.get('Ebs', {}).get('VolumeId')
                    if volume_id:
                        snapshot = ec2.create_snapshot(
                            VolumeId=volume_id,
                            Description=f'Forensics snapshot for {instance_id}'
                        )
                        actions_taken.append(f\"Created forensics snapshot: {snapshot['SnapshotId']}\")

        except Exception as e:
            actions_taken.append(f\"Error: {str(e)}\")

    return {'status': 'success', 'actions': actions_taken}
'''

    # Create Lambda execution role
    trust_policy = {
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
            \"Effect\": \"Allow\",
            \"Principal\": {\"Service\": \"lambda.amazonaws.com\"},
            \"Action\": \"sts:AssumeRole\"
        }]
    }

    role_name = 'IncidentResponseLambdaRole'

    try:
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role_response['Role']['Arn']
        print(f\"✓ Created Lambda role: {role_name}\")
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f\"  Role already exists: {role_name}\")

    # Attach managed policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/SecurityAudit'
    ]

    for policy_arn in policies:
        try:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        except iam.exceptions.LimitExceededException:
            pass

    # Create Lambda function
    function_name = 'SecurityIncidentResponse'

    try:
        import zipfile
        import io

        # Create deployment package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', lambda_code)

        zip_buffer.seek(0)

        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Timeout=300,
            MemorySize=256
        )
        print(f\"✓ Created Lambda function: {function_name}\")

        # Get function ARN
        function_response = lambda_client.get_function(FunctionName=function_name)
        function_arn = function_response['Configuration']['FunctionArn']

        return function_arn

    except lambda_client.exceptions.ResourceConflictException:
        function_response = lambda_client.get_function(FunctionName=function_name)
        function_arn = function_response['Configuration']['FunctionArn']
        print(f\"  Function already exists: {function_name}\")
        return function_arn


def create_eventbridge_rules(lambda_arn, sns_arn):
    \"\"\"Create EventBridge rules for automated response\"\"\"

    print(\"\\n3. Creating EventBridge Automation Rules\")
    print(\"=\"*60)

    rules = [
        {
            'name': 'GuardDutyHighSeverityFindings',
            'description': 'Trigger on GuardDuty HIGH/CRITICAL findings',
            'pattern': {
                \"source\": [\"aws.guardduty\"],
                \"detail-type\": [\"GuardDuty Finding\"],
                \"detail\": {
                    \"severity\": [7, 8, 9, 10]
                }
            }
        },
        {
            'name': 'CompromisedIAMCredentials',
            'description': 'Respond to compromised IAM credentials',
            'pattern': {
                \"source\": [\"aws.guardduty\"],
                \"detail-type\": [\"GuardDuty Finding\"],
                \"detail\": {
                    \"type\": [{\"prefix\": \"UnauthorizedAccess:IAMUser\"}]
                }
            }
        },
        {
            'name': 'RootAccountUsage',
            'description': 'Alert on root account usage',
            'pattern': {
                \"source\": [\"aws.signin\"],
                \"detail-type\": [\"AWS Console Sign In via CloudTrail\"],
                \"detail\": {
                    \"userIdentity\": {
                        \"type\": [\"Root\"]
                    }
                }
            }
        }
    ]

    for rule in rules:
        try:
            # Create rule
            events.put_rule(
                Name=rule['name'],
                Description=rule['description'],
                EventPattern=json.dumps(rule['pattern']),
                State='ENABLED'
            )
            print(f\"✓ Created rule: {rule['name']}\")

            # Add Lambda target
            events.put_targets(
                Rule=rule['name'],
                Targets=[
                    {
                        'Id': '1',
                        'Arn': lambda_arn
                    },
                    {
                        'Id': '2',
                        'Arn': sns_arn
                    }
                ]
            )

            # Grant permission to EventBridge to invoke Lambda
            try:
                lambda_client.add_permission(
                    FunctionName='SecurityIncidentResponse',
                    StatementId=f'EventBridge-{rule[\"name\"]}',
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=f\"arn:aws:events:{boto3.session.Session().region_name}:{sts.get_caller_identity()['Account']}:rule/{rule['name']}\"
                )
            except lambda_client.exceptions.ResourceConflictException:
                pass

        except events.exceptions.ResourceAlreadyExistsException:
            print(f\"  Rule already exists: {rule['name']}\")


if __name__ == '__main__':
    print(\"=\"*60)
    print(\"AUTOMATED INCIDENT RESPONSE SETUP\")
    print(\"=\"*60)

    # Create SNS topic
    sns_arn = create_sns_alert_topic()

    # Create Lambda function
    lambda_arn = create_response_lambda_function()

    # Create EventBridge rules
    create_eventbridge_rules(lambda_arn, sns_arn)

    print(\"\\n\" + \"=\"*60)
    print(\"✓ INCIDENT RESPONSE AUTOMATION CONFIGURED\")
    print(\"=\"*60)
    print(\"\\nPlaybooks implemented:\")
    print(\"  1. Compromised IAM Credentials\")
    print(\"     → Disable access key → Apply deny policy\")
    print(\"  2. Data Exfiltration Attempt\")
    print(\"     → Block S3 public access → Isolate bucket\")
    print(\"  3. Malware Detection\")
    print(\"     → Quarantine instance → Create forensics snapshot\")
```

## Validation Checklist

- [ ] GuardDuty enabled with threat intelligence
- [ ] Security Hub aggregating findings
- [ ] Security standards enabled (CIS, PCI-DSS)
- [ ] EventBridge rules created
- [ ] Lambda response function deployed
- [ ] SNS alerts configured
- [ ] Sample findings generate alerts
- [ ] Automated remediation tested

## Expected Results

**GuardDuty**: Continuous threat detection (VPC Flow, DNS, CloudTrail)
**Security Hub**: 95%+ compliance score
**Response Time**: <5 minutes for critical findings
**Automation**: 80%+ incidents auto-remediated

## Key Learnings

1. **Defense in Depth**: Multiple detection layers catch more threats
2. **Automation**: Reduces MTTR from hours to minutes
3. **Playbooks**: Consistent response procedures
4. **SIEM**: Correlate events across services
5. **Practice**: Regular IR drills improve response

## Next Steps

- **Advanced**: Build full SIEM with Elasticsearch + Kibana dashboards
- **Production**: Integrate with PagerDuty/Splunk
- **Certification**: Prepare for AWS Security Specialty

## Resources

- [GuardDuty User Guide](https://docs.aws.amazon.com/guardduty/)
- [Security Hub](https://docs.aws.amazon.com/securityhub/)
- [IR Best Practices](https://aws.amazon.com/blogs/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
