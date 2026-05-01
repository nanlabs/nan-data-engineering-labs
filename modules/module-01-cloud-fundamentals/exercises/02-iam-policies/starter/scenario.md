# Escenario: QuickMart Data Team Access Control

## Contexto

QuickMart ha crecido y ahora tiene un equipo de datos completo. El CTO te pidió implementar **access control** robusto siguiendo el principio de **least privilege**.

## Team Structure

### Data Engineers (2 personas)
**Nombres:** Alice Smith, Bob Johnson

**Responsabilidades:**
- Construir y mantener data pipelines
- Escribir Glue ETL jobs y Lambda functions
- Configurar infraestructura (S3, EMR, Kinesis)
- Troubleshooting de pipelines en producción

**Permisos Necesarios:**
- ✅ Full access: S3, Glue, Lambda, Athena, EMR, Kinesis
- ✅ EC2 read-only (para debugging de EMR clusters)
- ✅ CloudWatch Logs (para monitoring)
- ❌ NO pueden modificar IAM (seguridad)
- ❌ NO pueden ver billing information

### Data Analysts (2 personas)
**Nombres:** Carol Davis, David Martinez

**Responsabilidades:**
- Ejecutar queries en Athena
- Crear dashboards en QuickSight
- Explorar datos en S3 (read-only)
- Revisar Glue Data Catalog

**Permisos Necesarios:**
- ✅ S3 read-only (GetObject, ListBucket)
- ✅ Athena query execution (CreateNamedQuery, StartQueryExecution)
- ✅ Glue Data Catalog read-only
- ✅ QuickSight (asume ya configurado)
- ❌ NO pueden escribir/eliminar en S3
- ❌ NO pueden crear/modificar Glue jobs
- ❌ NO pueden lanzar EMR clusters

### ML/Data Science Lead (1 persona)
**Nombre:** Eve Wilson

**Responsabilidades:**
- Entrenar modelos de ML con SageMaker
- Acceder training datasets
- Desplegar modelos en Lambda para inference
- Experimentación con notebooks

**Permisos Necesarios:**
- ✅ SageMaker full access
- ✅ S3 access SOLO a:
  - `s3://my-data-lake-curated/ml-models/*`
  - `s3://my-data-lake-curated/training-data/*`
  - `s3://sagemaker-quickmart-*/*` (para SageMaker)
- ✅ Lambda read-only (para entender inference endpoints)
- ✅ ECR (para custom Docker images)
- ❌ NO puede acceder a `raw-data` (datos sensibles sin anonimizar)
- ❌ NO puede acceder a `transactions` (PII, GDPR)

---

## Requisitos de Seguridad

### 1. Principle of Least Privilege

**Cada user debe tener SOLO los permisos necesarios para su trabajo.**

Ejemplo:
```
❌ MAL - Data Analyst con admin access:
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}

✅ BIEN - Data Analyst con permisos específicos:
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:ListBucket"],
  "Resource": ["arn:aws:s3:::my-data-lake/*"]
}
```

### 2. Separation of Duties

**Ninguna persona debe tener acceso completo a producción sin oversight.**

- Data Engineers pueden crear infraestructura
- Pero NO pueden modificar IAM (evita self-privilege escalation)
- Admins (tú) gestionan IAM

### 3. Data Classification

**Diferentes niveles de sensibilidad:**

```
Public:
├── s3://my-data-lake-curated/public-datasets/
└── Acceso: Todos los analysts

Internal:
├── s3://my-data-lake-processed/analytics/
└── Acceso: Analysts + Engineers

Confidential:
├── s3://my-data-lake-raw/transactions/
└── Acceso: Solo Engineers (con logging)

Restricted:
├── s3://my-data-lake-raw/pii/
└── Acceso: NADIE (solo via pipeline automatizado)
```

### 4. Audit Logging

**Cada acción debe ser auditable.**

- CloudTrail registra todas las API calls
- S3 access logging habilitado
- Revisión mensual de accesos inusuales

---

## S3 Bucket Security Requirements

### Bucket: `my-data-lake-raw`

**Reglas:**
1. ❌ **NOBODY** puede eliminar objetos (except admins)
2. ✅ Uploads deben usar server-side encryption
3. ✅ Logs de access habilitados
4. ✅ Versioning habilitado (recovery de deletes accidentales)

**Bucket Policy debe implementar:**
```json
{
  "Statement": [
    {
      "Sid": "DenyDeleteForNonAdmins",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::my-data-lake-raw/*",
      "Condition": {
        "StringNotEquals": {
          "aws:username": ["admin-user"]
        }
      }
    },
    {
      "Sid": "RequireEncryption",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-data-lake-raw/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

### Bucket: `my-data-lake-processed`

**Reglas:**
1. ✅ Engineers pueden read/write
2. ✅ Analysts pueden solo read
3. ✅ Particiones por domain (sales/, marketing/, product/)
4. ✅ Lifecycle policy: Move a IA después de 90 días

---

## Cross-Account Access (Bonus)

QuickMart tiene un partner (ficticio account `999999999999`) que necesita acceso **read-only** a ciertos reports.

**Setup:**
1. Crear role `PartnerReportReader` en tu account
2. Trust policy permite account 999999999999 asumir el role
3. Role tiene permisos S3 read-only a `s3://my-data-lake-curated/partner-reports/*`

**Flujo:**
```
Partner AWS Account
    ↓
Asume role: arn:aws:iam::YOUR_ACCOUNT:role/PartnerReportReader
    ↓
Obtiene credenciales temporales (1 hora)
    ↓
Lee reports desde S3
```

---

## Tu Tarea

Implementa el access control completo:

1. **Crear 3 IAM Groups:**
   - `data-engineers`
   - `data-analysts`
   - `ml-scientists`

2. **Escribir 3 IAM Policies (JSON):**
   - `DataEngineerPolicy`
   - `DataAnalystPolicy`
   - `MLScientistPolicy`

3. **Crear 5 IAM Users:**
   - alice.engineer, bob.engineer → grupo data-engineers
   - carol.analyst, david.analyst → grupo data-analysts
   - eve.scientist → grupo ml-scientists

4. **Configurar S3 Bucket Policy** para `my-data-lake-raw`:
   - Deny deletes
   - Require encryption

5. **Crear Lambda Execution Role:**
   - Trust policy para Lambda service
   - Permisos: S3 read/write, CloudWatch Logs

6. **Documentar:**
   - Qué permisos tiene cada grupo
   - Por qué elegiste esos permisos
   - Cómo testear que funciona

---

## Testing

Después de implementar, debes poder:

```bash
# Test 1: Analyst NO puede delete
export AWS_PROFILE=carol.analyst
aws s3 rm s3://my-data-lake-raw/file.json --endpoint-url=http://localhost:4566
# Expected: Error - Access Denied

# Test 2: Engineer SÍ puede delete
export AWS_PROFILE=alice.engineer
aws s3 rm s3://my-data-lake-processed/temp.json --endpoint-url=http://localhost:4566
# Expected: Success

# Test 3: Scientist NO puede acceder raw data
export AWS_PROFILE=eve.scientist
aws s3 ls s3://my-data-lake-raw/ --endpoint-url=http://localhost:4566
# Expected: Error - Access Denied

# Test 4: Scientist SÍ puede acceder ML data
export AWS_PROFILE=eve.scientist
aws s3 ls s3://my-data-lake-curated/ml-models/ --endpoint-url=http://localhost:4566
# Expected: Success (lista objetos)
```

---

## Compliance Considerations

**GDPR (European users):**
- PII debe estar en buckets separados con access logging
- Right to deletion debe ser implementable
- Data retention policies (lifecycle rules)

**HIPAA (si manejan health data):**
- Encryption at rest mandatory
- Audit trails completos
- Access reviews trimestrales

**SOC2:**
- Least privilege documented
- Change management para IAM
- Regular access reviews

---

## Reflexión

Después de completar, responde:

1. **¿Cómo revocarías acceso si Bob renuncia?**
   - Opción A: Eliminar user
   - Opción B: Remover de grupo
   - Opción C: Attach deny policy
   - ¿Cuál es mejor y por qué?

2. **Alice necesita acceso temporal a billing por auditoría. ¿Cómo lo harías?**
   - Sin modificar su policy permanente
   - Solo por 24 horas
   - Auditable

3. **Detectaste que Carol accedió a datos sensibles fuera de su scope. ¿Qué haces?**
   - Investigar en CloudTrail
   - Revocar acceso inmediato
   - Revisar policies (¿error de config?)

¡Adelante con la implementación! 🔐
