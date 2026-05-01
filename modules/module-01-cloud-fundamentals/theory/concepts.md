# Fundamental Concepts of Cloud Computing

**Estimated study time:** 3-4 hours
**Nivel:** Fundamental
**Prerequisitos:** Ninguno

---

## 1. Introduction al Cloud Computing

### What is Cloud Computing?

Cloud Computing is the on-demand delivery of IT Resources over the Internet with a pay-per-usage model. Instead of purchasing, owning and maintaining physical data centers and servers, you can access technological services such as computing capacity, storage and databases as needed from a cloud provider such as AWS, Azure or Google Cloud.

### Essential Features of Cloud Computing

According to the NIST (National Institute of Standards and Technology), cloud computing has five essential features:

1. **On-Demand Self-Service (Autoservicio bajo demanda)**
   - Provision Resources automatically without human interaction with the provider
   - Create servers, storage or databases in minutes via console or API
   - Example: Launching an EC2 instance on AWS takes less than 2 minutes

2. **Broad Network Access**
   - Access from any device with an Internet connection
   - APIs available for automation
   - Web consoles, CLI, SDKs in multiple languages

3. **Resource Pooling**
   - Resources shared between multiple clients (multi-tenant)
   - Dynamic allocation on demand
   - The client usually does not know the exact location of the Resources

4. **Rapid Elasticity**
   - Scale Resources up or down automatically
   - Capacidad aparentemente ilimitada
   - Example: Auto Scaling Groups in AWS that add/remove servers based on load

5. **Measured Service (Servicio medido)**
   - I only pay for what you use (pay-as-you-go)
   - Monitoring, control and reporting of Resources Usage
   - Cost optimization based on accurate metrics

### Why Cloud for Data Engineering?

Cloud computing is especially relevant for Data Engineering for several reasons:

**1. Scalability for Large Volumes of Data**
- Process terabytes or petabytes without initial investment in hardware
- Scale processing horizontally for Spark jobs or ETL pipelines
- Virtually unlimited storage (S3 can store infinite objects)

**2. Costo variable vs. Costo Fijo**
- You don't pay for idle capacity
- Process data in batch only when necessary
- Example: A pipeline that runs 1 hour/day only costs 1/24 of the cost of a 24/7 server

**3. Speed ​​and Agility**
- Experiment with new technologies without procurement
- Provision Spark clusters in minutes, not weeks
- Quickly iterate on data architectures

**4. Alcance Global**
- Replicate Data close to your users in multiple regions
- Low latency for global applications
- Compliance with Data residency regulations

**5. Serverless and Managed Services**
- Reduce overhead operacional (no gestionar parches, backups, HA)
- Focus on business logic, not infrastructure
- Example: AWS Glue for ETL without managing Spark servers

---

## 2. Cloud Service Models

There are three main cloud service models, forming an abstraction pyramid:

### Infrastructure as a Service (IaaS)

**Definition:** Provision of critical IT infrastructure (computing, networking, storage) as a service.

**What do you manage:**
- Sistema operativo
- Middleware
- Runtime
- Data
- Aplicaciones

**What the provider manages:**
- Virtualization
- Physical servers
- Physical storage
- Physical networking

**Examples on AWS:**
- **Amazon EC2:** Virtual machines
- **Amazon EBS:** Block Storage
- **Amazon VPC:** Redes virtuales privadas

**Usage Case in Data Engineering:**
```
Necesitas instalar una versión específica de Apache Kafka con configuraciones
custom que no están disponibles en servicios managed. Usas EC2 para desplegar
tu cluster de Kafka con control total sobre la configuración.
```

**Ventajas:**
- Full control over infrastructure
- Maximum flexibility
- Puedes instalar cualquier software

**Desventajas:**
- Mayor responsabilidad operacional
- Debes gestionar OS, seguridad, patches
- More complexity

### Platform as a Service (PaaS)

**Definition:** Provision of a development and deployment platform without managing underlying infrastructure.

**What do you manage:**
- Data
- Aplicaciones

**What the provider manages:**
- Runtime
- Middleware
- Sistema operativo
- Virtualization
- Servidores
- Almacenamiento
- Networking

**Examples on AWS:**
- **AWS Elastic Beanstalk:** Web Application Deployment
- **AWS Lambda:** Functions serverless
- **Amazon RDS:** Managed Relational Databases
- **AWS Glue:** ETL managed with Spark

**Usage Case in Data Engineering:**
```
Necesitas una base de datos PostgreSQL para tu data warehouse. En lugar de
instalar y configurar PostgreSQL en EC2 (IaaS), usas Amazon RDS que gestiona
automáticamente backups, patches, replicación y failover.
```

**Ventajas:**
- Menos overhead operacional
- Focus on development, not infrastructure
- Built-in scalability and high availability

**Desventajas:**
- Less control over configuration
- Vendor lock-in potencial
- Costs may be higher than IaaS

### Software as a Service (SaaS)

**Definition:** Provision of complete applications over the Internet.

**What do you manage:**
- You just use the app

**What the provider manages:**
- The entire technological stack

**Examples:**
- **Snowflake:** Data warehouse cloud-native
- **Databricks:** Unified Data Platform
- **Fivetran:** Data ingestion tool
- **Looker:** Business intelligence

**Usage Case in Data Engineering:**
```
Necesitas ingestar datos de 50 fuentes SaaS (Salesforce, Google Analytics, etc.)
a tu data warehouse. Usar Fivetran (SaaS) te da conectores pre-built y
mantenidos, sin escribir código.
```

**Ventajas:**
- Zero infrastructure management
- Automatic updates
- Acceso inmediato

**Desventajas:**
- Menos flexibilidad
- Total dependence on the vendor
- Costs can escalate quickly

### Comparison Matrix

| Aspecto | IaaS | PaaS | SaaS |
|---------|------|------|------|
| **Control** | Alto | Medio | Bajo |
| **Flexibility** | Maximum | Medium | Limited |
| **Setup time** | Hours/Days | Minutes | Immediate |
| **Operational management** | High | Medium | Minimum |
| **Learning Curve** | Steep | Moderate | Soft |
| **Costo inicial** | Bajo | Medio | Alto |
| **Scalability** | Manual | Semi-automatic | Automatic |

### Which one to choose for Data Engineering?

In Practice, you'll use a **combination of all three**:

- **IaaS:** For specific self-hosted tools (Airflow, Kafka with special configs)
- **PaaS:** For most workloads (Lambda for transformations, RDS for metadata, Glue for ETL)
- **SaaS:** For productivity tools (Databricks, Snowflake, Fivetran)

**Guiding Principle:** Use the highest level of abstraction that satisfies your Requirements. Only downgrade when you need specific control.

---

## 3. AWS Global Infrastructure

Understanding the global AWS infrastructure is critical to designing resilient and performing architectures.

### Regions (Regiones)

An **AWS Region** is a physical geographic location in the world where AWS has multiple data centers.

**Features:**
- AWS has **33+ regions** currently (and growing)
- Each region is completely independent
- Data in one region is NOT automatically replicated to other regions
- Each region has a unique code:`us-east-1`, `eu-west-1`, `ap-southeast-2`, etc.

**Factors for choosing a region:**

1. **Compliance (Cumplimiento)**
   - Data residency regulations (GDPR, local laws)
   - Example: Data of European citizens must be in EU regions

2. **Latency (Latencia)**
   - Proximidad a usuarios finales
   - Example: Users in Brazil → use`sa-east-1` (São Paulo)

3. **Available Services (Servicios disponibles)**
   - Not all services are in all regions
   - New services generally launch first in`us-east-1`

4. **Pricing (Precios)**
   - Prices vary between regions
   - `us-east-1`usually the cheapest, Asia-Pacific regions more expensive

**Example for Data Engineering:**
```
Tienes usuarios en América del Norte y Europa. Decides:
- Data Lake principal en us-east-1 (costo)
- Réplica read-only en eu-west-1 (latencia para usuarios EU)
- Replication con S3 Cross-Region Replication
```

### Availability Zones (AZs)

An Availability Zone is one or more discrete data centers with redundant power, networking and connectivity within a region.

**Features clave:**
- Each region has **minimum 3 AZs** (some have 6+)
- AZs are **physically separated** (different buildings)
- Connected with **low latency networking** (<2ms between AZs)
- Nombradas: `us-east-1a`, `us-east-1b`, `us-east-1c`, etc.

**Visualization:**
```
Region: us-east-1
├── AZ: us-east-1a (Data Center 1, 2)
├── AZ: us-east-1b (Data Center 3, 4)
├── AZ: us-east-1c (Data Center 5, 6)
├── AZ: us-east-1d (Data Center 7)
├── AZ: us-east-1e (Data Center 8)
└── AZ: us-east-1f (Data Center 9)
```

**Why multiple AZs?**

**High Availability:** If a data center fails (fire, power outage, natural disaster), your applications continue working in other AZs.

**Multi-AZ architecture example for Data Engineering:**
```
Data Pipeline:
- Kinesis Data Stream: Réplicas en 3 AZs (automático)
- Lambda processors: Se despliegan en todas las AZs de la región
- RDS Database: Primary en AZ-A, Standby en AZ-B (Multi-AZ)
- S3: Datos replicados automáticamente entre AZs

Si us-east-1a falla → Kinesis sigue escribiendo en 1b y 1c
                    → Lambda sigue procesando
                    → RDS hace failover a AZ-B
                    → S3 sigue disponible
```

### Edge Locations

**Edge Locations** are globally distributed points of presence (PoP) to deliver Content with low latency.

**Features:**
- **450+ Edge Locations** in ~90 cities
- Much more numerous than regions (33) or AZs (~100)
- Mainly used by **CloudFront** (CDN) and **Route 53** (DNS)

**Usage in Data Engineering:**
```
Escenario: Dashboard de BI consumido por 10,000 usuarios globales

Sin Edge Locations:
- Todos los requests van a us-east-1
- Usuarios en Australia experimentan 200-300ms latency

Con CloudFront (Edge Locations):
- Dashboard assets (JS, CSS, imágenes) cacheados en edge
- Usuarios en Australia conectan a edge en Sydney: 20-30ms latency
- 10x mejora en performance
```

### Global Infrastructure Diagram

```mermaid
graph TB
    subgraph "AWS Global Infrastructure"
        subgraph "Region: us-east-1"
            AZ1[AZ-1a<br/>Data Centers 1,2]
            AZ2[AZ-1b<br/>Data Centers 3,4]
            AZ3[AZ-1c<br/>Data Centers 5,6]
        end

        subgraph "Region: eu-west-1"
            AZ4[AZ-1a<br/>Data Centers]
            AZ5[AZ-1b<br/>Data Centers]
            AZ6[AZ-1c<br/>Data Centers]
        end

        subgraph "Region: ap-southeast-2"
            AZ7[AZ-2a<br/>Data Centers]
            AZ8[AZ-2b<br/>Data Centers]
            AZ9[AZ-2c<br/>Data Centers]
        end
    end

    Edge1[Edge Location<br/>New York]
    Edge2[Edge Location<br/>London]
    Edge3[Edge Location<br/>Sydney]

    AZ1 -.->|CloudFront<br/>Distribution| Edge1
    AZ4 -.->|CloudFront<br/>Distribution| Edge2
    AZ7 -.->|CloudFront<br/>Distribution| Edge3
```

### Design Principles for Data Engineering

1. **Design for Failure:** Assume that any component can fail
2. **Multi-AZ by default:** For production workloads
3. **Multi-Region only if necessary:** Adds complexity and cost
4. **Consider latency:** Place Data close to where it is processed

---

## 4. Identity and Access Management (IAM)

IAM is the fundamental security service on AWS. **Everything in AWS requires authentication and authorization via IAM.**

### Concepts Fundamentales

#### Users (Usuarios)

An **IAM User** represents a person or application that interacts with AWS.

**Features:**
- Tiene credenciales permanentes (password o access keys)
- Puede tener permisos asignados directamente (no recomendado)
- Best Practice: Assign permissions via Groups

**Example:**
```
IAM User: john.doe@company.com
- Password: Para AWS Console
- Access Key ID: AKIAIOSFODNN7EXAMPLE
- Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**For Data Engineering:**
```
Escenario: Tienes 5 data engineers en tu equipo

❌ MAL:
- Todos comparten un solo user
- No sabes quién hizo qué cambio

✅ BIEN:
- Cada engineer tiene su propio IAM User
- Logs de CloudTrail muestran quién ejecutó cada acción
- Puedes revocar acceso individualmente
```

#### Groups (Grupos)

An **IAM Group** is a collection of IAM Users.

**Ventajas:**
- Manage permissions at the group level, not user by user
- A user can belong to multiple groups
- Simplify administration at scale

**Structure Example:**
```
Group: DataEngineers
├── Permissions: S3 Full Access, Glue Full Access, Athena Full Access
├── Members:
│   ├── john.doe@company.com
│   ├── jane.smith@company.com
│   └── carlos.garcia@company.com

Group: DataAnalysts
├── Permissions: S3 Read Access, Athena Full Access
├── Members:
│   ├── alice.johnson@company.com
│   └── bob.wilson@company.com
```

#### Roles (Roles)

An **IAM Role** is an identity with specific permissions that can be temporarily **assumed** by trusted entities.

**Key difference with Users:**
- **Users:** Credenciales permanentes
- **Roles:** Credenciales temporales (15min - 12hrs)

**Main Usage Cases:**

**1. EC2 Instances (most common)**
```
EC2 Instance → Asume IAM Role → Obtiene credenciales temporales → Accede a S3

Ventajas:
- No necesitas hardcodear access keys en la instancia
- Credenciales rotan automáticamente
- Puedes revocar acceso sin tocar la instancia
```

**2. Cross-Account Access**
```
Cuenta A (Producción) → Permite Cuenta B (Dev) → Asumir role

Escenario: Developers en cuenta Dev necesitan leer datos de S3 en cuenta Prod
Solución: Crear role en Prod que Cuenta Dev puede asumir temporalmente
```

**3. Lambda Functions**
```
Lambda Function → Execution Role → Permisos para:
├── Leer de S3
├── Escribir a DynamoDB
└── Enviar logs a CloudWatch
```

**4. Federated Access (SSO)**
```
Employee → Autentica con Okta/Azure AD → Asume Role en AWS → Acceso temporal

Ventaja: Single Sign-On, no gestionar passwords en AWS
```

#### Policies

An **IAM Policy** is a JSON document that defines permissions.

**Anatomy of a Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-data-lake/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
```

**Componentes:**
- **Version:** Always "2012-10-17" (policy language version)
- **Statement:** Array of permission statements
  - **Effect:** `Allow` o `Deny`
  - **Action:** What operations (ex:`s3:GetObject`, `glue:*`)
  - **Resource:** In which Resources (ARN)
  - **Condition:** (Opcional) Condiciones adicionales

**Types of policies:**

**1. Managed Policies (AWS-managed):**
```
- AmazonS3FullAccess
- AWSGlueServiceRole
- AmazonAthenaFullAccess
```
Advantage: Maintained by AWS, good to start with
Desventaja: Pueden ser muy permisivas

**2. Customer-Managed Policies:**
```
Políticas custom que creas para tus necesidades específicas
Ejemplo: "DataEngineerReadOnlyProduction"
```

**3. Inline Policies:**
```
Políticas embebidas directamente en un User/Group/Role
Uso: Relaciones 1:1 estrictas
```

**Example for Data Engineering - Restrictive Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadFromRawBucket",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::company-datalake-raw",
        "arn:aws:s3:::company-datalake-raw/*"
      ]
    },
    {
      "Sid": "AllowWriteToProcessedBucket",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::company-datalake-processed/*"
    },
    {
      "Sid": "DenyDeleteOnRawData",
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::company-datalake-raw/*"
    }
  ]
}
```

### IAM Best Practices

1. **Never use Root Account credentials**
   - Root = acceso total, sin restricciones
   - Configure MFA in root
   - Only use root for specific tasks (change payment plan, close account)

2. **Principle of Least Privilege**
   - Give only the minimum necessary permissions
   - Starts restrictive, expand only if necessary
   - Check permissions regularly with IAM Access Analyzer

3. **Use IAM Roles for applications**
   - Never hardcode access keys in code
   - EC2 instances → IAM Role
   - Lambda functions → Execution Role
   - ECS tasks → Task Role

4. **Enable MFA for privileged users**
   - Users who can create/delete Resources
   - Users with access to sensitive data

5. **Rotate credentials regularly**
   - Access keys: Every 90 days
   - AWS can automatically notify you

6. **Use CloudTrail for auditing**
   - Log all API calls
   - Who did what, when, from where
   - Critical for compliance and debugging

### IAM for Data Pipelines - Complete Example

**Scenario:** Pipeline that reads from S3, processes with Lambda, writes to DynamoDB

```
Step 1: Crear IAM Policy para Lambda
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::raw-data-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/ProcessedData"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}

Step 2: Crear IAM Role
Role Name: DataProcessingLambdaRole
Trust Policy: Lambda service can assume this role
Attach: La policy del Step 1

Step 3: Asignar Role a Lambda Function
En la configuración de Lambda → Execution Role → DataProcessingLambdaRole

Step 4: Lambda ejecuta con credenciales temporales
- Lambda asume el role automáticamente
- Obtiene credenciales temporales (1-6 horas según config)
- SDK de AWS (boto3) usa credenciales automáticamente
- Al expirar, Lambda solicita nuevas credenciales
```

---

## 5. Core AWS Services for Data Engineering

### Amazon S3 (Simple Storage Service)

**What it is:** Scalable, durable and low-cost object storage.

**Concepts clave:**
- **Bucket:** Object container (globally unique names)
- **Object:** File + metadata (up to 5TB per object)
- **Key:** Path of the object (ex:`data/year=2024/month=01/file.parquet`)

**Why it is essential for Data Engineering:**
```
S3 es el "sistema de archivos" de la nube para datos

Usos típicos:
├── Data Lake: Almacenamiento central para datos raw, processed, curated
├── Data Warehouse staging: Área de staging antes de cargar a Redshift/Snowflake
├── Backup y archivo: Retención de datos históricos
├── Logs y eventos: Almacenamiento de logs de aplicaciones
└── Datasets para ML: Training data para modelos de machine learning
```

**Storage Classes:**
```
S3 Standard: Acceso frecuente, baja latencia
└─→ S3 Intelligent-Tiering: Mueve datos automáticamente entre tiers
    └─→ S3 Standard-IA: Acceso infrecuente (backups mensuales)
        └─→ S3 Glacier: Archivo (backups anuales, compliance)
            └─→ S3 Glacier Deep Archive: Archivo a largo plazo (7-10 años)

Ejemplo de costos (us-east-1):
- Standard: $0.023/GB/mes
- Standard-IA: $0.0125/GB/mes
- Glacier: $0.004/GB/mes
- Deep Archive: $0.00099/GB/mes
```

**Features esenciales:**
- **Versioning:** Maintain multiple versions of objects
- **Lifecycle Policies:** Automatic transition between storage classes
- **Replication:** Cross-Region o Same-Region replication
- **Event Notifications:** Trigger Lambda cuando suben archivos

### AWS Lambda

**What it is:** Serverless computing service that executes code in response to events.

**Features:**
- No servers to manage
- Automatic auto-scaling (0 to 1000s of concurrent executions)
- Payment per millisecond of execution
- 15 minute limit per invocation

**Uses in Data Engineering:**
```
1. ETL ligero y transformaciones
   S3 (CSV) → Lambda → S3 (Parquet)

2. Orquestación de pipelines
   Lambda que invoca Glue jobs, EMR steps, Step Functions

3. Validación de datos
   Nuevo archivo en S3 → Lambda valida schema → Rechaza o acepta

4. API para consultas
   API Gateway → Lambda → Athena → Resultados

5. Real-time processing
   Kinesis Stream → Lambda → DynamoDB/S3
```

**Limitaciones importantes:**
- 15 min timeout (for long processes use Glue, EMR, Batch)
- 10GB RAM maximum
- 512MB /tmp storage
- Non-persistent (each invocation is stateless)

### Amazon EC2 (Elastic Compute Cloud)

**What it is:** Virtual machines (instances) in the cloud with resizable computing capacity.

**Instance Types relevant to Data:**
```
Compute Optimized (C-family):
- c6i.xlarge: Para procesamiento batch intensivo
- Ejemplo: Procesar millones de registros con Python

Memory Optimized (R-family):
- r6i.2xlarge: Para in-memory processing (Spark)
- Ejemplo: Cluster de Spark con datasets grandes en RAM

Storage Optimized (I-family):
- i3.large: Para databases con alta I/O
- Ejemplo: Elasticsearch cluster para búsqueda de logs
```

**When to use EC2 vs. Lambda:**
```
Usa EC2 si:
- Proceso corre >15 minutos
- Necesitas control del OS
- Software específico no disponible en Lambda
- High-memory workloads (>10GB RAM)

Usa Lambda si:
- Proceso <15 minutos
- Event-driven
- Scaling automático es crítico
- No quieres gestionar servidores
```

### Amazon RDS (Relational Database Service)

**What it is:** Managed relational databases (PostgreSQL, MySQL, SQL Server, Oracle).

**Ventajas sobre EC2 + BD self-hosted:**
```
RDS Gestiona:
├── Backups automáticos (retention configurable)
├── Patches del motor de BD
├── High Availability (Multi-AZ)
├── Read Replicas (escalado de lecturas)
├── Monitoring con CloudWatch
└── Encryption at rest y in transit

Tú solo:
├── Diseñas esquema
├── Optimizas queries
└── Gestionas usuarios y permisos
```

**Uses in Data Engineering:**
```
1. Metadata Store
   - Airflow metadata database
   - Glue Data Catalog (usa RDS internamente)

2. Operational Databases
   - Transactional data source para ETL
   - Read replica para evitar impacto en producción

3. Small Data Warehouses
   - Datasets <1TB con queries SQL
   - Alternativa a Redshift para casos simples
```

**Architecture example:**
```
Production App → RDS Primary (Multi-AZ)
                      ↓
                Read Replica (para reporting/ETL)
                      ↓
                ETL Job (Glue) → Extract data
                      ↓
                S3 Data Lake
```

---

## 6. AWS Pricing Models

Understanding the cost model is critical for optimization and avoiding invoice surprises.

### On-Demand Pricing

**Model:** Payment by Usage, without commitments.

**Features:**
- Sin costos upfront
- Sin contratos a largo plazo
- Pay only for what you use

**When to use:**
```
✅ Workloads impredecibles
✅ Desarrollo y testing
✅ Short-term projects
✅ Aplicaciones con tráfico spiky
```

**Cost example:**
```
Lambda:
- $0.20 por 1M de requests
- $0.0000166667 por GB-segundo

S3:
- $0.023 per GB/month (Standard storage)
- $0.0004 por 1000 GET requests

RDS PostgreSQL (db.t3.medium):
- $0.068 por hora = ~$50/mes
```

### Reserved Instances (RIs)

**Model:** 1 or 3 year commitment in exchange for a discount of up to 75%.

**Types:**
```
1. Standard RI: Máximo descuento, menos flexibilidad
2. Convertible RI: Cambiar instance type, menor descuento
3. Scheduled RI: Para workloads predecibles por horario
```

**Savings example:**
```
EC2 m5.xlarge On-Demand: $0.192/hora × 24 × 365 = $1,681/año

EC2 m5.xlarge 3-year RI: $0.046/hora × 24 × 365 = $403/año

Ahorro: $1,278/año (76% descuento)
```

**When to use:**
```
✅ Workloads de producción estables
✅ Databases que corren 24/7 (RDS, Redshift)
✅ Base layer de Auto Scaling Groups
```

### Spot Instances

**Model:** Purchase unused capacity with a discount of up to 90%.

**Catch:** AWS can terminate your instance with 2 minutes notice.

**When to use:**
```
✅ Batch processing tolerante a interrupciones
✅ Spark jobs que pueden reanudar desde checkpoint
✅ CI/CD test environments
✅ Data processing no time-sensitive

❌ Databases de producción
❌ Aplicaciones stateful sin checkpoint
❌ Real-time processing crítico
```

**Example for Data Engineering:**
```
EMR Cluster para procesamiento nocturno:
- Core nodes: On-Demand (master + state)
- Task nodes: 100% Spot (solo compute)

Costo On-Demand: 10 × m5.2xlarge × 8 horas = $30.72
Costo Spot (70% discount): = $9.22

Ahorro por job: $21.50
Ahorro mensual (30 jobs): $645
```

### Savings Plans

**Model:** Hourly spending commitment for 1 or 3 years.

**Ventajas vs. RIs:**
- More flexibility (any region, instance type, OS)
- Automatically applies to Lambda, Fargate, EC2

**Example:**
```
Te comprometes a gastar $10/hora por 1 año = $87,600

AWS aplica descuento a:
├── EC2 instances (cualquier tipo)
├── Lambda invocations
├── Fargate containers
└── Automatically al uso que más descuento genere
```

### Free Tier

**12 months free** from AWS account creation:
```
EC2:
- 750 horas/mes de t2.micro o t3.micro

S3:
- 5GB de Standard storage
- 20,000 GET requests, 2,000 PUT requests

Lambda:
- 1M requests gratuitos/mes
- 400,000 GB-seconds de compute

RDS:
- 750 horas/mes de db.t2.micro
- 20GB de storage

DynamoDB:
- 25GB de storage
- 25 Read/Write Capacity Units

Athena:
- 10GB de data scanned/mes

Glue:
- 1M objects stored en Data Catalog
```

**Always Free (perpetuo):**
```
Lambda: 1M requests + 400,000 GB-sec/mes
DynamoDB: 25GB + 25 RCU/WCU
CloudWatch: 10 custom metrics, 10 alarms
```

### Cost Optimization Tips for Data Engineering

**1. Use S3 Intelligent-Tiering**
```bash
# Lifecycle policy automática para ahorrar en storage
aws s3api put-bucket-lifecycle-configuration \
  --lifecycle-configuration '{
    "Rules": [{
      "Status": "Enabled",
      "Transitions": [{
        "Days": 90,
        "StorageClass": "INTELLIGENT_TIERING"
      }]
    }]
  }'
```

**2. Compress Data**
```
CSV sin comprimir: 100GB × $0.023 = $2.30/mes
Parquet Snappy: 10GB × $0.023 = $0.23/mes

Ahorro: 90% en storage + menor costo en queries Athena
```

**3. Partition Data in S3**
```
Sin particiones:
s3://bucket/data/

Athena escanea TODO = $5 per TB scanned

Con particiones:
s3://bucket/data/year=2024/month=01/

Athena escanea solo necesario = $0.05 per query

100 queries: $500 vs. $5 → 99% ahorro
```

**4. Use Spot for Batch Workloads**
```python
# EMR con Spot instances
emr_client.run_job_flow(
    Instances={
        'InstanceGroups': [
            {
                'Name': 'Master',
                'Market': 'ON_DEMAND',  # Master siempre On-Demand
                'InstanceRole': 'MASTER',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 1
            },
            {
                'Name': 'Workers',
                'Market': 'SPOT',  # Workers en Spot para ahorrar
                'InstanceRole': 'CORE',
                'InstanceType': 'm5.2xlarge',
                'InstanceCount': 10,
                'BidPrice': '0.15'  # 70% menos que On-Demand
            }
        ]
    }
)
```

---

## 7. AWS Well-Architected Framework

AWS best practices framework based on 5 pillars. **Essential for designing production systems.**

### Pilar 1: Operational Excellence

**Principle:** Execute and monitor systems to deliver business value.

**For Data Engineering:**
```
1. Infrastructure as Code (IaC)
   - Todo en Terraform/CloudFormation
   - Versionado en Git
   - Reproducible y auditable

2. Monitoring y Observability
   - CloudWatch Logs para todos los servicios
   - Métricas custom (ej: registros procesados/minuto)
   - Alarmas para SLAs (99.9% de jobs exitosos)

3. Runbooks y Playbooks
   - Documentar procedimientos comunes
   - "Qué hacer si falla el pipeline nocturno"
   - Scripts de recovery automatizados
```

### Pilar 2: Security

**Principle:** Protect information, systems and assets.

**For Data Engineering:**
```
1. Encryption everywhere
   ├── At Rest: S3 con KMS, RDS encrypted
   ├── In Transit: TLS 1.2+ para todas las conexiones
   └── En processing: Spark con encryption

2. Principle of Least Privilege (IAM)
   - Roles específicos por servicio
   - Policies restrictivas
   - Auditar con Access Analyzer

3. Data Classification
   ├── Public: Open datasets
   ├── Internal: Analytics agregados
   ├── Confidential: PII, financial data
   └── Restricted: Secrets, credentials

4. Compliance
   - GDPR: Right to deletion (S3 lifecycle delete)
   - HIPAA: Encryption + audit logging (CloudTrail)
   - SOC2: Access controls + monitoring
```

### Pilar 3: Reliability

**Principle:** Systems that function correctly and recover from failures.

**For Data Engineering:**
```
1. Multi-AZ por defecto
   - RDS Multi-AZ para metadata stores
   - S3 replica automáticamente entre AZs
   - Lambda se despliega en todas las AZs

2. Backups automatizados
   - S3 Versioning para data lake
   - RDS automated backups (7-35 días retention)
   - Glue Data Catalog backup con scripts

3. Graceful Degradation
   Ejemplo: Pipeline con 3 fuentes de datos
   - Source A falla → Log error, continúa con B y C
   - No falla todo el pipeline por un source

4. Idempotencia
   - Rerun de ETL produce mismo resultado
   - Upserts en lugar de inserts
   - Prevent duplicados con deduplication
```

### Pilar 4: Performance Efficiency

**Principle:** Use Resources efficiently to meet Requirements.

**For Data Engineering:**
```
1. Columnar Formats
   CSV → Parquet: 10x menos storage + 10x queries más rápidos

2. Partitioning
   s3://data/year=2024/month=01/day=15/
   Query solo lee particiones necesarias

3. Right-sizing
   - Lambda: 1GB RAM para transformaciones ligeras
   - Glue: 2 DPU para datasets pequeños, 10 DPU para grandes
   - RDS: db.t3.medium para dev, db.r5.xlarge para prod

4. Caching
   - Athena query results cache (24 horas)
   - Lambda con /tmp para datos reutilizables
   - CloudFront para dashboards
```

### Pilar 5: Cost Optimization

**Principio:** Evitar gastos innecesarios.

**For Data Engineering:**
```
1. Lifecycle Policies
   Raw data: Delete después de 90 días
   Processed data: Move a Glacier después de 1 año

2. Spot Instances
   EMR/Glue clusters para batch processing

3. Serverless donde sea posible
   Lambda < $1/millón de requests
   Athena: Pay per query ($5/TB scanned)
   vs. mantener cluster 24/7

4. Data Compression
   Parquet + Snappy = 90% menos storage

5. Reserved Capacity
   RDS, Redshift para workloads 24/7
```

---

## 8. Key Takeaways for Data Engineers

### Mental Models Esenciales

**1. Think in Services, not Servers**
```
Mentalidad tradicional:
"Necesito un servidor para procesar datos"

Mentalidad Cloud:
"Qué servicio resuelve mi problema con menos overhead?"

Ejemplo:
- Proceso de 5 minutos → Lambda (serverless)
- Proceso de 3 horas → Glue (managed Spark)
- Proceso de 12 horas → EMR (cluster ephemeral)
```

**2. Everything is API-driven**
```python
# No hay UI que hacer click manualmente
# Todo es programático y reproducible

# Crear bucket S3
s3_client.create_bucket(Bucket='my-data-lake')

# Lanzar EMR cluster
emr_client.run_job_flow(...)

# Query con Athena
athena_client.start_query_execution(...)
```

**3. Design for Cost**
```
Cada decisión arquitectónica tiene impacto en costos:

Mala práctica:
- Cluster EMR 24/7 → $5,000/mes
- Solo se usa 2 horas/día

Buena práctica:
- EMR ephemeral clusters
- Launch on-demand → Process → Terminate
- Costo: $300/mes (94% ahorro)
```

**4. Data Lakes como Fundamento**
```
Data Lake (S3):
├── Raw Zone: Datos originales inmutables
├── Processed Zone: Datos limpios y validados
├── Curated Zone: Datasets listos para análisis
└── Archive Zone: Datos históricos (Glacier)

Todo el ecosistema lee/escribe de/a S3:
- Athena queries desde S3
- Glue ETL: S3 → transform → S3
- EMR: S3 input/output
- Lambda: Triggered por S3 events
- SageMaker: Training data en S3
```

### Common Patterns

**Pattern 1: Event-Driven Processing**
```
S3 Upload Event → SNS → Lambda → Process → DynamoDB
                    ↓
                  SQS (for reliability)
```

**Pattern 2: Batch Processing**
```
CloudWatch Event (cron) → Step Function → Glue Job → S3
                                              ↓
                                           SNS (alertas)
```

**Pattern 3: Streaming Processing**
```
Kinesis Data Stream → Lambda → S3 (partitioned)
                        ↓
                   DynamoDB (real-time queries)
```

---

## 9. Escenario Real: E-Commerce Data Pipeline

**Context:** Online store with 100K transactions/day needs analytics pipeline.

**Requirements:**
1. Ingest transactions in real time
2. Process data and calculate daily metrics
3. Store for Historical Analysis
4. Dashboard for stakeholders
5. Bajo costo (<$500/mes)

**Arquitectura AWS:**

```
1. Data Ingestion (Real-time)
   Website/Mobile App → API Gateway → Lambda → Kinesis Data Stream

   Costo: ~$50/mes
   - API Gateway: $3.50 per million requests
   - Lambda: Free tier cubre
   - Kinesis: $0.015 per shard-hour × 2 shards = $22/mes

2. Stream Processing
   Kinesis → Lambda (consumer) → S3 (partitioned Parquet)
                              → DynamoDB (current state)

   Costo: ~$80/mes
   - Lambda: Minimal (free tier)
   - S3: 30GB/mes × $0.023 = $0.70/mes
   - DynamoDB: On-demand, ~$50/mes para 100K writes + reads

3. Batch Processing (Daily)
   CloudWatch Event (daily) → Glue Crawler → Glue ETL Job → S3 (curated)

   Costo: ~$15/mes
   - Glue Crawler: $0.44/hr × 0.5hr/día = $6.60/mes
   - Glue Job: 2 DPU × $0.44/hr × 1hr/día = $13.20/mes

4. Analytics Layer
   Athena (query S3) ← QuickSight (dashboard)

   Costo: ~$50/mes
   - Athena: $5/TB scanned, ~100GB/mes = $0.50/mes
   - QuickSight: $9/user/mes × 5 users = $45/mes

5. Storage
   S3 (12 meses históricos):
   - 30GB/mes × 12 meses = 360GB × $0.023 = $8.30/mes
   - Lifecycle: >6 meses → Standard-IA → ahorro 45%

Total: ~$203/mes

Escalabilidad:
- 100K → 1M transactions/día
- Kinesis: Add shards (linear scaling)
- Lambda: Auto-scales
- Glue: Increase DPUs
- Estimated: ~$600/mes
```

**Advantages of this design:**
- ✅ Serverless: No servers to manage
- ✅ Auto-scaling: Handle traffic spikes
- ✅ Cost-effective: Pay only for use
- ✅ Resilient: Multi-AZ, S3 durability 99.999999999%
- ✅ Analytics-ready: Athena queries in seconds

---

## 10. Self-Assessment Questions

Answer these questions to validate your understanding:

**1. Architecture Design**
```
Diseña una arquitectura AWS para:
- Ingestar logs de 1000 servidores (10GB/día)
- Procesar y almacenar para análisis
- Retener logs 7 años para compliance
- Budget: $200/mes

Considera:
- Qué servicios usarías
- Cómo optimizarías costos
- Dónde aplicarías lifecycle policies
```

**2. IAM Scenario**
```
Tienes un data engineer que necesita:
✅ Leer todos los buckets S3
✅ Ejecutar Glue jobs existentes
❌ NO debe poder eliminar buckets S3
❌ NO debe poder crear nuevos Glue jobs

Escribe la IAM Policy
```

**3. Cost Optimization**
```
Tu factura AWS es $5,000/mes:
- RDS PostgreSQL db.m5.2xlarge 24/7: $2,400
- EMR cluster 24/7 para batch jobs nocturnos: $1,800
- S3 storage 10TB sin lifecycle policies: $230
- Athena queries sobre CSV: $500

¿Cómo optimizarías a <$2,000/mes?
```

**4. Reliability**
```
Tu pipeline ETL falla cada 2-3 semanas con error:
"Lambda timeout después de 15 minutos"

El proceso:
- Lee 50,000 archivos CSV de S3
- Transforma con Pandas
- Escribe a Parquet

¿Qué arquitectura propondrías?
```

**5. Service Selection**
```
Necesitas procesar un dataset de 5GB diariamente:
- Lectura de S3
- Transformaciones (joins, aggregations)
- Escritura a otro bucket S3

Opciones:
A) Lambda
B) Glue (2 DPU)
C) EMR (3-node cluster)
D) EC2 con Spark

¿Cuál elegirías y por qué?
```

**6. Multi-Region Strategy**
```
Aplicación con usuarios en:
- 60% USA
- 30% Europa
- 10% Asia

Data lake en us-east-1.
Usuarios EU se quejan de lentitud en queries.

¿Cómo resolverías sin duplicar costos?
```

---

## Next Steps

**You have completed the theoretical Module.** Now it is time to apply these Concepts:

1. **Exercise 01:** Configure AWS CLI and create your first S3 bucket
2. **Exercise 02:** Crea policies IAM restrictivas
3. **Exercise 03:** Implementa S3 bucket policies
4. **Exercise 04:** Despliega tu primera Lambda function
5. **Exercise 05:** Infrastructure as Code with CloudFormation
6. **Exercise 06:** Cost optimization with lifecycle policies

**Recuerda:**
- Read the Theory completely before starting Exercises
- Check out additional Resources at`theory/resources.md`
- Usa hints progresivos si te atascas
- Just look at the solution when you've tried everything

**Estimated time for Exercises:** 5-8 hours

Success in your Learning! 🚀
