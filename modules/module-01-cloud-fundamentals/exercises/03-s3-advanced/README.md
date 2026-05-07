# Exercise 03: S3 Advanced Features

**Estimated Duration:** 60-75 minutes
**Difficulty:** ⭐⭐⭐ Intermediatetetete

## 🎯 Objectives de Aprendizaje

- Implement versionado de objetos en S3
- Configure políticas de lifecycle para optimización de costos
- Configure replicación entre buckets
- Implement event notifications con SQS
- Understand storage classes y sus casos de uso

## 📋 Prerequisites

- ✅ Exercise 01: S3 Basics completed
- ✅ Exercise 02: IAM Policies completed
- ✅ LocalStack ejecutándose
- ✅ AWS CLI configurado

## 📖 Conceptos Clave

### S3 Versioning

El versionado permite mantener múltiples variantes de un objeto:

```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket my-bucket \
  --versioning-configuration Status=Enabled

# Upload multiple versions
echo "v1" > file.txt && aws s3 cp file.txt s3://my-bucket/
echo "v2" > file.txt && aws s3 cp file.txt s3://my-bucket/
echo "v3" > file.txt && aws s3 cp file.txt s3://my-bucket/

# List all versions
aws s3api list-object-versions --bucket my-bucket
```text

**Casos de uso:**

- Protección contra borrado accidental
- Auditoría de cambios
- Rollback a versiones anteriores
- Compliance requirements

### Lifecycle Policies

Automatizan la transición entre storage classes:

```json
{
  "Rules": [{
    "Id": "ArchiveOldData",
    "Status": "Enabled",
    "Transitions": [
      {
        "Days": 30,
        "StorageClass": "STANDARD_IA"
      },
      {
        "Days": 90,
        "StorageClass": "GLACIER"
      }
    ],
    "Expiration": {"Days": 365}
  }]
}
```text

**Storage Classes:**

- `STANDARD`: Access frecuente (<$0.023/GB)
- `INTELLIGENT_TIERING`: Auto-optimización
- `STANDARD_IA`: Access infrecuente (<$0.0125/GB)
- `GLACIER`: Archivo (<$0.004/GB, retrieval 3-5h)
- `DEEP_ARCHIVE`: Archivo profundo (<$0.00099/GB, retrieval 12h)

### S3 Replication

Copia automática entre buckets:

```json
{
  "Role": "arn:aws:iam::...",
  "Rules": [{
    "Status": "Enabled",
    "Priority": 1,
    "Filter": {"Prefix": "data/"},
    "Destination": {
      "Bucket": "arn:aws:s3:::backup-bucket"
    }
  }]
}
```text

**Tipos:**

- **CRR (Cross-Region):** Disaster recovery, compliance
- **SRR (Same-Region):** Agregación de logs, replicación test/prod

### Event Notifications

Desencadena acciones cuando cambian objetos:

```json
{
  "QueueConfigurations": [{
    "QueueArn": "arn:aws:sqs:...",
    "Events": ["s3:ObjectCreated:*"],
    "Filter": {
      "Key": {
        "FilterRules": [{"Name": "prefix", "Value": "uploads/"}]
      }
    }
  }]
}
```

## 🎬 Steps a Seguir

### Step 1: Review el Scenario

Lee [starter/scenario.md](starter/scenario.md) para understand el context:

- **QuickMart** necesita optimizar costos de almacenamiento
- Millones de logs históricos ocupando storage STANDARD
- Necesidad de backup automático para disaster recovery
- Pipeline de procesamiento con event-driven architecture

### Step 2: Copiar Starter Files

```bash
cd exercises/03-s3-advanced
cp -r starter/ my_solution/
cd my_solution
```text

### Step 3: Implement Lifecycle Configuration

Edita `s3_lifecycle.py` y completa las funciones con TODOs:

```python
def enable_versioning(bucket_name: str) -> bool:
    # TODO: Enable versioning on bucket
    pass

def create_lifecycle_policy(bucket_name: str, policy: Dict) -> bool:
    # TODO: Apply lifecycle configuration
    pass
```text

**Debes implementar:**

- ✅ Habilitar versionado en bucket principal
- ✅ Create lifecycle rule: 30 días → STANDARD_IA
- ✅ Create lifecycle rule: 90 días → GLACIER
- ✅ Create expiration rule: 365 días
- ✅ Verify que las policies se aplicaron runctamente

### Step 4: Implement Replicación

Edita `s3_replication.py` y completa:

```python
def create_backup_bucket(bucket_name: str) -> bool:
    # TODO: Create destination bucket
    pass

def setup_replication(source_bucket: str, dest_bucket: str, role_arn: str) -> bool:
    # TODO: Configure replication
    pass
```text

**Debes implementar:**

- ✅ Create bucket de backup (destination)
- ✅ Create IAM role para replicación
- ✅ Configure replication rule
- ✅ Verify objetos se replican automáticamente

### Step 5: Implement Event Notifications

Edita `s3_events.py` y completa:

```python
def create_sqs_queue(queue_name: str) -> str:
    # TODO: Create SQS queue
    pass

def configure_bucket_notification(bucket_name: str, queue_arn: str) -> bool:
    # TODO: Set up S3 event notifications
    pass
```

**Debes implementar:**

- ✅ Create SQS queue para recibir notificaciones
- ✅ Configure queue policy (permitir S3 enviar mensajes)
- ✅ Configure bucket notification para `s3:ObjectCreated:*`
- ✅ Test: Upload file → verificar mensaje en SQS

### Step 6: Testing Integral

Ejecuta el script de testing:

```bash
python3 test_s3_advanced.py
```text

**El test debe verificar:**

- ✅ Versioning está habilitado
- ✅ Lifecycle policy existe y está activa
- ✅ Replicación funciona (upload → verifica en backup bucket)
- ✅ Event notifications funcionan (upload → verifica mensaje SQS)

## 🧪 Validation

### Test Manual

```bash
# 1. Test Versioning
aws --endpoint-url=http://localhost:4566 s3api put-bucket-versioning \
  --bucket my-data-lake --versioning-configuration Status=Enabled

echo "version 1" > test.txt
aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://my-data-lake/

echo "version 2" > test.txt
aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://my-data-lake/

# Should show 2 versions
aws --endpoint-url=http://localhost:4566 s3api list-object-versions \
  --bucket my-data-lake --prefix test.txt

# 2. Test Lifecycle
aws --endpoint-url=http://localhost:4566 s3api get-bucket-lifecycle-configuration \
  --bucket my-data-lake | jq .

# 3. Test Replication (requires versioning on both buckets)
aws --endpoint-url=http://localhost:4566 s3 ls s3://my-data-lake-backup/

# 4. Test Events
aws --endpoint-url=http://localhost:4566 sqs receive-message \
  --queue-url http://localhost:4566/000000000000/s3-events | jq .
```text

### Expected Output

```text
✓ Versioning enabled on my-data-lake
✓ Lifecycle policy applied (3 rules)
✓ Backup bucket created: my-data-lake-backup
✓ Replication configured
✓ SQS queue created: s3-events
✓ Event notifications configured

Test Results:
  ✓ Upload file → 2 versions exist
  ✓ Lifecycle rule exists
  ✓ File replicated to backup bucket
  ✓ SQS received ObjectCreated event
```

## 💡 Tips

### Debugging Versioning

```python
# List all versions with details
response = s3.list_object_versions(Bucket='my-bucket')
for version in response.get('Versions', []):
    print(f"Key: {version['Key']}, VersionId: {version['VersionId']}, "
          f"IsLatest: {version['IsLatest']}, Size: {version['Size']}")
```text

### Lifecycle Policy Gotchas

- Minimum 30 days before transitioning to STANDARD_IA
- GLACIER retrieval takes 3-5 hours (use Expedited for 1-5 min)
- Non-current versions need separate rules
- LocalStack simula transitions pero no las ejecuta realmente

### Replication Requirements

1. Versioning must be enabled on BOTH buckets
2. IAM role needs `s3:ReplicateObject` permission
3. LocalStack Pro required for full replication features (Community = basic)

### Event Notification Filters

```python
# Only notify for .json files in uploads/ folder
notification_config = {
    'QueueConfigurations': [{
        'QueueArn': queue_arn,
        'Events': ['s3:ObjectCreated:*'],
        'Filter': {
            'Key': {
                'FilterRules': [
                    {'Name': 'prefix', 'Value': 'uploads/'},
                    {'Name': 'suffix', 'Value': '.json'}
                ]
            }
        }
    }]
}
```text

## 🐛 Troubleshooting

**Error: "VersioningNotEnabled"**

```bash
# Enable on source and destination
aws s3api put-bucket-versioning --bucket BUCKET \
  --versioning-configuration Status=Enabled
```text

**Error: "InvalidArgument: lifecycle Days must be >= 30"**

```json
// Use 30+ days for STANDARD_IA
{"Days": 30, "StorageClass": "STANDARD_IA"}
```

**Error: "SQS queue policy denies SendMessage"**

```python
# Add S3 to SQS policy
policy = {
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "s3.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn
    }]
}
sqs.set_queue_attributes(QueueUrl=queue_url, Attributes={'Policy': json.dumps(policy)})
```text

## 📚 Deliverables

Al finalizar debes tener:

1. ✅ `s3_lifecycle.py` completed y funcional
2. ✅ `s3_replication.py` completed y funcional
3. ✅ `s3_events.py` completed y funcional
4. ✅ `test_s3_advanced.py` ejecutado exitosamente
5. ✅ Screenshot/logs mostrando:
   - Versioning habilitado
   - Lifecycle policy activa
   - Objeto replicado en backup bucket
   - Mensaje SQS con evento S3

## 🚀 Next Step

Una vez completed este exercise: **[Exercise 04: Lambda Functions](../04-lambda-functions/README.md)**

---

**¿Necesitas ayuda?** Consulta [hints.md](hints.md) con 3 niveles de hints progresivos.
