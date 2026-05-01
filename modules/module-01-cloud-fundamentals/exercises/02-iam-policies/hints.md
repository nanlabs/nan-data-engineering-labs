# Hints - Exercise 02: IAM Policies

## 🟢 NIVEL 1: Conceptual Hints

### Hint 1.1: IAM Policy Structure

Every IAM policy has this structure:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DescriptiveName",
      "Effect": "Allow" | "Deny",
      "Action": ["service:Operation"],
      "Resource": "arn:aws:service:::resource"
    }
  ]
}
```

**Common mistakes:**
- Olvidar el `Version` (debe ser "2012-10-17")
- `Action` y `Resource` deben ser arrays (con `[]`)
- ARNs deben tener formato correcto

### Hint 1.2: boto3 IAM Operations

```python
# Create group
iam.create_group(GroupName='my-group')

# Create policy
iam.create_policy(
    PolicyName='MyPolicy',
    PolicyDocument=json.dumps(policy_dict)
)

# Attach policy to group
iam.attach_group_policy(
    GroupName='my-group',
    PolicyArn='arn:aws:iam::...'
)

# Create user
iam.create_user(UserName='john.doe')

# Add user to group
iam.add_user_to_group(
    UserName='john.doe',
    GroupName='my-group'
)
```

### Hint 1.3: Reading JSON Files

```python
import json
from pathlib import Path

# Read policy file
with open('policies/data_engineer.json', 'r') as f:
    policy_doc = json.load(f)

# Now policy_doc is a Python dict
```

---

## 🟡 NIVEL 2: Implementation Hints

### Hint 2.1: Complete create_group Function

```python
def create_group(group_name: str) -> bool:
    try:
        response = iam.create_group(GroupName=group_name)
        print_success(f"Created group: {group_name}")
        return True
    except iam.exceptions.EntityAlreadyExistsException:
        print_success(f"Group already exists: {group_name}")
        return True
    except Exception as e:
        print_error(f"Failed to create group {group_name}: {str(e)}")
        return False
```

### Hint 2.2: Complete create_policy Function

```python
def create_policy(policy_name: str, policy_document: Dict) -> str:
    try:
        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        policy_arn = response['Policy']['Arn']
        print_success(f"Created policy: {policy_name}")
        return policy_arn
    except iam.exceptions.EntityAlreadyExistsException:
        # Construct ARN manually for existing policy
        policy_arn = f"arn:aws:iam::000000000000:policy/{policy_name}"
        print_success(f"Policy already exists: {policy_name}")
        return policy_arn
    except Exception as e:
        print_error(f"Failed to create policy: {str(e)}")
        return ""
```

### Hint 2.3: Main Function - Create Groups

```python
# In main():
print_step("Step 1: Creating IAM Groups")

groups = ['data-engineers', 'data-analysts', 'ml-scientists']

for group in groups:
    create_group(group)
```

### Hint 2.4: Main Function - Load and Create Policies

```python
print_step("Step 2: Creating IAM Policies")

policies_dir = Path(__file__).parent / 'policies'
policy_arns = {}

# Data Engineer policy
with open(policies_dir / 'data_engineer.json', 'r') as f:
    policy_doc = json.load(f)
    arn = create_policy('DataEngineerPolicy', policy_doc)
    policy_arns['engineer'] = arn

# Data Analyst policy
with open(policies_dir / 'data_analyst.json', 'r') as f:
    policy_doc = json.load(f)
    arn = create_policy('DataAnalystPolicy', policy_doc)
    policy_arns['analyst'] = arn

# ML Scientist policy
with open(policies_dir / 'ml_scientist.json', 'r') as f:
    policy_doc = json.load(f)
    arn = create_policy('MLScientistPolicy', policy_doc)
    policy_arns['scientist'] = arn
```

### Hint 2.5: Attach Policies to Groups

```python
print_step("Step 3: Attaching Policies to Groups")

attach_policy_to_group('data-engineers', policy_arns['engineer'])
attach_policy_to_group('data-analysts', policy_arns['analyst'])
attach_policy_to_group('ml-scientists', policy_arns['scientist'])
```

---

## 🔴 NIVEL 3: Complete Solution Parts

### Hint 3.1: Complete User Creation and Group Assignment

```python
print_step("Step 4: Creating IAM Users")

users = {
    'alice.engineer': 'data-engineers',
    'bob.engineer': 'data-engineers',
    'carol.analyst': 'data-analysts',
    'david.analyst': 'data-analysts',
    'eve.scientist': 'ml-scientists'
}

for username in users.keys():
    create_user(username)

print_step("Step 5: Adding Users to Groups")

for username, group_name in users.items():
    add_user_to_group(username, group_name)
```

### Hint 3.2: Lambda Role Creation

```python
print_step("Step 6: Creating Lambda Execution Role")

lambda_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role_arn = create_role('lambda-data-processor-role', lambda_trust_policy)

if role_arn:
    # Create inline policy for Lambda
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject"],
                "Resource": "arn:aws:s3:::my-data-lake-*/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }

    lambda_policy_arn = create_policy('LambdaDataProcessorPolicy', lambda_policy)
    if lambda_policy_arn:
        attach_policy_to_role('lambda-data-processor-role', lambda_policy_arn)
```

### Hint 3.3: Apply S3 Bucket Policy

```python
print_step("Step 7: Applying S3 Bucket Policy")

bucket_policy_file = Path(__file__).parent / 'bucket_policy.json'

if bucket_policy_file.exists():
    with open(bucket_policy_file, 'r') as f:
        bucket_policy = json.load(f)

    apply_bucket_policy('my-data-lake-raw', bucket_policy)
else:
    print_error("bucket_policy.json not found")
```

### Hint 3.4: Complete attach_policy_to_group Function

```python
def attach_policy_to_group(group_name: str, policy_arn: str) -> bool:
    try:
        iam.attach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )
        print_success(f"Attached policy to {group_name}")
        return True
    except Exception as e:
        print_error(f"Failed to attach policy: {str(e)}")
        return False
```

### Hint 3.5: Complete create_role Function

```python
def create_role(role_name: str, trust_policy: Dict) -> str:
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = response['Role']['Arn']
        print_success(f"Created role: {role_name}")
        return role_arn
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::000000000000:role/{role_name}"
        print_success(f"Role already exists: {role_name}")
        return role_arn
    except Exception as e:
        print_error(f"Failed to create role: {str(e)}")
        return ""
```

---

## 💡 Debugging Tips

### Testing Individual Functions

```python
# Test in Python REPL
python3

>>> import boto3
>>> iam = boto3.client('iam', endpoint_url='http://localhost:4566',
...     region_name='us-east-1', aws_access_key_id='test',
...     aws_secret_access_key='test')

>>> # Test create group
>>> iam.create_group(GroupName='test-group')

>>> # List groups to verify
>>> iam.list_groups()
```

### Verify IAM Resources

```bash
# List all groups
aws --endpoint-url=http://localhost:4566 iam list-groups

# List users in group
aws --endpoint-url=http://localhost:4566 iam get-group --group-name data-engineers

# List attached policies
aws --endpoint-url=http://localhost:4566 iam list-attached-group-policies \
  --group-name data-engineers

# Get policy document
aws --endpoint-url=http://localhost:4566 iam get-policy \
  --policy-arn arn:aws:iam::000000000000:policy/DataEngineerPolicy
```

### Common Errors

**Error: "EntityAlreadyExists"**
- Group/user/policy already created
- Handle with try/except
- Or delete first: `iam.delete_group(GroupName='...')`

**Error: "No such file or directory"**
- Check Path is correct
- Use `Path(__file__).parent` for relative paths
- Print paths for debugging

**Error: "Invalid JSON"**
- Validate JSON: `cat policies/file.json | jq .`
- Check for trailing commas
- Verify quotes are correct (`"`, not `'`)

---

## 🎯 Testing Your Implementation

After running the script, test permissions:

```python
# Test script
import boto3

# Simulate analyst user (read-only)
s3_analyst = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='analyst-key',  # Would need to create access keys
    aws_secret_access_key='analyst-secret'
)

# This should work
try:
    s3_analyst.list_objects_v2(Bucket='my-data-lake-raw')
    print("✅ Analyst can list objects")
except Exception as e:
    print(f"❌ Error: {e}")

# This should fail
try:
    s3_analyst.delete_object(Bucket='my-data-lake-raw', Key='file.txt')
    print("❌ Analyst can delete (SHOULD NOT HAPPEN)")
except Exception as e:
    print(f"✅ Analyst cannot delete (expected): {e}")
```

---

## 📚 Additional Resources

- IAM Policy Simulator (AWS real): https://policysim.aws.amazon.com/
- IAM Policy Examples: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_examples.html
- boto3 IAM Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html

**Remember:** Least privilege is not just best practice, it's a security requirement!
