# Exercise 02: IAM Policies & Security

**Difficulty:** ⭐⭐ Beginner-Intermedio
**Estimated Time:** 60-75 minutos
**Prerequisites:** Exercise 01 completed

---

## 🎯 Objective

Dominar IAM (Identity and Access Management) creando users, groups, roles y policies restrictivas. Implementarás el principio de **least privilege** y configurarás acceso seguro para diferentes roles en un data team.

## 📋 What You Will Learn

1. ✅ Crear IAM users, groups y roles con AWS CLI
2. ✅ Escribir IAM policies en JSON (inline y managed)
3. ✅ Implementar least privilege principle
4. ✅ Configurar S3 bucket policies (resource-based)
5. ✅ Setup cross-account access con roles
6. ✅ Troubleshooting de permisos (Access Denied)

## 🛤️ Clear Path to Follow

### Step 1: Entender el Escenario (5 min)

Lee `starter/scenario.md`:

> **QuickMart** ahora tiene un data team de 5 personas:
> - 2 Data Engineers (full access a S3, Glue, Lambda)
> - 2 Data Analysts (read-only S3, Athena)
> - 1 Data Science Lead (ML services + production data)

Necesitas configurar IAM para que cada rol tenga **solo** los permisos necesarios.

### Step 2: Revisar Starter Files (10 min)

```
starter/
├── iam_setup.py          # Script Python (boto3) - 40% completo
├── policies/
│   ├── data_engineer.json    # TODO: Policy para engineers
│   ├── data_analyst.json     # TODO: Policy para analysts
│   └── ml_scientist.json     # TODO: Policy para DS
├── bucket_policy.json    # TODO: S3 bucket policy
└── requirements.txt      # boto3
```

### Step 3: Implementar Solución (40 min)

**Orden recomendado:**

1. **Escribe IAM Policies** (15 min)
   - `policies/data_engineer.json` - Full access a data services
   - `policies/data_analyst.json` - Read-only
   - `policies/ml_scientist.json` - ML + S3 specific buckets

2. **Implementa iam_setup.py** (20 min)
   - Crear grupos
   - Crear users y asignar a grupos
   - Attach policies a grupos
   - Crear role para Lambda

3. **Configura S3 Bucket Policy** (5 min)
   - Restrict delete operations
   - Allow cross-account access (simulado)

### Step 4: Validar (5 min)

```bash
# Ejecuta el script
python my_solution/iam_setup.py

# Valida permisos
python ../../validation/integration/test_iam_permissions.py

# Validación completa
../../scripts/validate-module.sh 01
```

### Step 5: Test Real (10 min)

Prueba los permisos creados:

```bash
# Como data analyst (read-only)
AWS_PROFILE=analyst aws s3 ls s3://my-data-lake/  # ✅ Funciona
AWS_PROFILE=analyst aws s3 rm s3://my-data-lake/file.txt  # ❌ Access Denied

# Como data engineer (full access)
AWS_PROFILE=engineer aws s3 rm s3://my-data-lake/file.txt  # ✅ Funciona
```

---

## 📝 Requisitos de la Solución

### IAM Policies Requeridas

**Data Engineer Policy:**
- ✅ Full access: S3, Glue, Lambda, Athena, EMR
- ✅ EC2 read-only (para debugging)
- ❌ NO puede modificar IAM
- ❌ NO puede acceder a billing

**Data Analyst Policy:**
- ✅ S3 GetObject, ListBucket (read-only)
- ✅ Athena query execution
- ✅ Glue Data Catalog read
- ❌ NO puede PutObject, DeleteObject
- ❌ NO puede crear/modificar Glue jobs

**ML Scientist Policy:**
- ✅ SageMaker full access
- ✅ S3 access solo a `ml-models/` y `training-data/` buckets
- ✅ Lambda read-only (para inference endpoints)
- ❌ NO puede acceder a `raw-data/` bucket

### S3 Bucket Policy

Debe implementar:
- ✅ Deny DeleteObject para todos excepto admins
- ✅ Require encryption en uploads (server-side)
- ✅ Allow cross-account read para cuenta partner (simulado)

---

## 🎓 Conceptos Clave

### Identity-Based vs Resource-Based Policies

```
Identity-Based Policy (IAM Policy):
├── Se attacha a: User, Group o Role
├── Define: Qué puede hacer esta identidad
└── Ejemplo: "User john.doe puede leer S3"

Resource-Based Policy (S3 Bucket Policy):
├── Se attacha a: Recurso (S3 bucket, Lambda, etc.)
├── Define: Quién puede acceder este recurso
└── Ejemplo: "Bucket data-lake permite read a account 123456"
```

### Policy Evaluation Logic

```
1. Explicit DENY → Siempre gana
2. Explicit ALLOW → Permite acción
3. Implicit DENY → Default (si no hay ALLOW)

Ejemplo:
- IAM policy: ALLOW s3:PutObject
- Bucket policy: DENY s3:PutObject
- Resultado: DENY (explicit deny gana)
```

### Least Privilege Principle

```
❌ MAL:
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
}

✅ BIEN:
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:ListBucket"],
  "Resource": [
    "arn:aws:s3:::my-data-lake",
    "arn:aws:s3:::my-data-lake/*"
  ],
  "Condition": {
    "StringEquals": {
      "s3:prefix": ["analytics/*", "reports/*"]
    }
  }
}
```

---

## 🔍 Debugging Tips

### Problema: "Access Denied" al ejecutar operación

```bash
# 1. Verifica qué identity estás usando
aws sts get-caller-identity --endpoint-url=http://localhost:4566

# 2. Lista policies attachadas al user
aws iam list-attached-user-policies --user-name john.doe --endpoint-url=...

# 3. Obtén el policy document
aws iam get-policy-version --policy-arn=... --version-id=... --endpoint-url=...

# 4. Simula policy evaluation (en AWS real, no LocalStack)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/john.doe \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::my-bucket/file.txt
```

### Problema: Policy JSON mal formado

Valida JSON antes de crear policy:

```bash
# Con jq
cat policies/data_engineer.json | jq .

# O usa AWS policy validator
aws iam validate-policy-document --policy-document file://policies/data_engineer.json
```

### Problema: LocalStack no soporta feature X de IAM

LocalStack Community tiene limitaciones:
- ✅ Soporta: Users, groups, roles, policies básicas
- ❌ NO soporta: Policy conditions complejas, federation, MFA
- Solución: Documenta qué harías en AWS real

---

## ✅ Checklist de Completitud

- [ ] 3 IAM policies escritas en JSON (engineer, analyst, scientist)
- [ ] S3 bucket policy con deny rules
- [ ] `iam_setup.py` crea grupos, users, asigna policies
- [ ] Script ejecuta sin errores
- [ ] Puedes explicar diferencia entre identity-based y resource-based policies
- [ ] Entiendes policy evaluation logic (deny > allow)
- [ ] Tests de permisos pasan (read-only user NO puede delete)

---

## 📊 Expected Output

```
🔐 IAM Setup for QuickMart Data Team
=====================================

Step 1: Creating IAM Groups...
✅ Created group: data-engineers
✅ Created group: data-analysts
✅ Created group: ml-scientists

Step 2: Creating IAM Policies...
✅ Created policy: DataEngineerPolicy
✅ Created policy: DataAnalystPolicy
✅ Created policy: MLScientistPolicy

Step 3: Attaching policies to groups...
✅ Attached DataEngineerPolicy to data-engineers
✅ Attached DataAnalystPolicy to data-analysts
✅ Attached MLScientistPolicy to ml-scientists

Step 4: Creating IAM Users...
✅ Created user: alice.engineer
✅ Created user: bob.engineer
✅ Created user: carol.analyst
✅ Created user: david.analyst
✅ Created user: eve.scientist

Step 5: Adding users to groups...
✅ Added alice.engineer to data-engineers
✅ Added bob.engineer to data-engineers
✅ Added carol.analyst to data-analysts
✅ Added david.analyst to data-analysts
✅ Added eve.scientist to ml-scientists

Step 6: Creating Lambda execution role...
✅ Created role: lambda-data-processor-role
✅ Attached trust policy for Lambda service

Step 7: Applying S3 bucket policy...
✅ Applied bucket policy to: my-data-lake-raw

Summary:
--------
👥 Users created: 5
📦 Groups created: 3
📋 Policies created: 3
🎭 Roles created: 1
🪣 Buckets secured: 1

✨ IAM setup completed successfully!
```

---

## 🚀 Next Steps

1. **Exercise 03:** S3 Advanced Features (versioning, lifecycle, replication)
2. **Experimenta:**
   - Crea policy para permitir acceso solo a ciertos prefixes
   - Implementa MFA delete (documenta, LocalStack no lo soporta)
   - Setup cross-account role assumption

3. **Reflexiona:**
   - ¿Cómo revocarías acceso a un employee que deja la compañía?
   - ¿Qué pasa si un engineer necesita acceso temporal a billing?
   - ¿Cómo auditarías quién accedió qué datos?

---

## 📚 Referencias

- IAM Policies Reference: `aws iam help`
- Policy Examples: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_examples.html
- boto3 IAM: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html

**Recuerda:** En producción NUNCA des más permisos de los necesarios. Es más fácil expandir permisos después que revocar acceso indebido.
