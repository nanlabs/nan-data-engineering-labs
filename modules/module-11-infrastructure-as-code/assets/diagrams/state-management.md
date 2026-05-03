# Gestión de Estado de Terraform (State Management)

## Arquitectura del Remote State con S3 Backend

```mermaid
flowchart TB
    subgraph Team["👥 Equipo de Desarrollo"]
        Dev1[Desarrollador 1]
        Dev2[Desarrollador 2]
        Dev3[Desarrollador 3]
        CI[CI/CD Pipeline]
    end

    subgraph Backend["🔒 Remote Backend (S3 + DynamoDB)"]
        S3[S3 Bucket<br/>terraform-state-bucket<br/>Versionado Habilitado<br/>Encriptación AES-256]
        DDB[(DynamoDB Table<br/>terraform-locks<br/>LockID as Hash Key)]
    end

    subgraph AWS["☁️ AWS Resources"]
        VPC[VPC]
        EC2[EC2 Instances]
        RDS[(RDS)]
        S3Data[S3 Buckets]
        Lambda[Lambda Functions]
    end

    Dev1 -->|1. terraform plan| Lock1{Intentar Lock}
    Dev2 -->|2. terraform plan| Lock2{Intentar Lock}
    Dev3 -->|3. terraform apply| Lock3{Intentar Lock}
    CI -->|4. terraform apply| Lock4{Intentar Lock}

    Lock1 -->|Lock Adquirido| DDB
    Lock2 -->|❌ Esperando...|Wait[Esperar Liberación]
    Lock3 -->|❌ Esperando...|Wait
    Lock4 -->|❌ Esperando...|Wait

    DDB -->|Lock Activo| S3
    S3 -->|Leer State| Dev1
    Dev1 -->|Ejecutar Operación| AWS
    AWS -->|Actualizar State| S3
    S3 -->|Liberar Lock| DDB
    DDB -->|Lock Liberado| Next[Siguiente Operación]

    Wait -.->|Retry| Next
    Next --> Lock2

    style DDB fill:#FF9800
    style S3 fill:#87CEEB
    style Wait fill:#FFB6C1
```

## State File Structure

```mermaid
graph TB
    State[terraform.tfstate] --> Version[version: 4]
    State --> Serial[serial: 42]
    State --> Lineage[lineage: UUID]
    State --> Outputs[outputs]
    State --> Resources[resources]

    Resources --> R1[Resource 1<br/>aws_vpc]
    Resources --> R2[Resource 2<br/>aws_subnet]
    Resources --> R3[Resource 3<br/>aws_instance]

    R1 --> R1Mode[mode: managed]
    R1 --> R1Type[type: aws_vpc]
    R1 --> R1Name[name: main]
    R1 --> R1Provider[provider: aws]
    R1 --> R1Instances[instances]

    R1Instances --> Attributes[attributes:<br/>- id<br/>- cidr_block<br/>- tags<br/>- arn]
    R1Instances --> Dependencies[dependencies:<br/>- aws_security_group]

    Outputs --> O1[vpc_id]
    Outputs --> O2[subnet_ids]
    Outputs --> O3[instance_ips]

    style State fill:#E1F5FF
    style Resources fill:#E8F5E9
    style Outputs fill:#FFF3E0
```

## State File Versioning con S3

```mermaid
sequenceDiagram
    participant Dev as Desarrollador
    participant TF as Terraform
    participant S3 as S3 Bucket
    participant Versions as S3 Versions

    Note over S3: Estado Inicial: v1

    Dev->>TF: terraform apply (cambio 1)
    TF->>S3: Subir state v2
    S3->>Versions: Archivar v1
    Note over Versions: v1 (archived)
    Note over S3: Estado Actual: v2

    Dev->>TF: terraform apply (cambio 2)
    TF->>S3: Subir state v3
    S3->>Versions: Archivar v2
    Note over Versions: v1, v2 (archived)
    Note over S3: Estado Actual: v3

    Dev->>TF: ❌ Error en cambio 3
    TF->>S3: Estado corrupto v4

    Dev->>TF: terraform state pull
    TF->>S3: Obtener state actual
    S3-->>TF: ⚠️ Estado corrupto v4

    Dev->>S3: Recuperar versión anterior
    S3->>Versions: Restaurar v3
    Versions-->>S3: v3 restaurado

    Dev->>TF: terraform state push
    TF->>S3: Subir v3 restaurado
    Note over S3: Estado Actual: v3 (restaurado)

    Note over Dev,Versions: ✅ Recuperación Exitosa
```

## State Locking con DynamoDB

```mermaid
flowchart TD
    Start([Inicio Operación]) --> Request[terraform plan/apply]
    Request --> CreateLock[Crear Lock Entry<br/>en DynamoDB]

    CreateLock --> LockCheck{¿Lock<br/>Disponible?}

    LockCheck -->|❌ Ya Existe| Locked[Lock Activo]
    Locked --> Wait[Esperar...]
    Wait --> Timeout{¿Timeout?}
    Timeout -->|No| LockCheck
    Timeout -->|Sí| Error1[Error: Lock Timeout]

    LockCheck -->|✅ Disponible| Acquire[Adquirir Lock]
    Acquire --> LockInfo[Registrar Info:<br/>- ID<br/>- Operation<br/>- Usuario<br/>- Timestamp]

    LockInfo --> Execute[Ejecutar Operación]
    Execute --> Success{¿Éxito?}

    Success -->|✅ Sí| UpdateState[Actualizar State]
    Success -->|❌ No| Error2[Error en Operación]

    UpdateState --> Release[Liberar Lock]
    Error2 --> Release

    Release --> Delete[Eliminar Entry<br/>de DynamoDB]
    Delete --> End([Fin])

    Error1 --> Manual[Intervención Manual<br/>Forzar Unlock]
    Manual --> Check{¿Validar<br/>Estado?}
    Check -->|Safe| ForceUnlock[terraform force-unlock]
    Check -->|Unsafe| Investigate[Investigar Causa]
    ForceUnlock --> Delete

    style Acquire fill:#90EE90
    style Release fill:#87CEEB
    style Error1 fill:#FF6347
    style Error2 fill:#FF6347
    style Wait fill:#FFD700
```

## DynamoDB Lock Table Structure

```mermaid
erDiagram
    TERRAFORM_LOCKS {
        string LockID PK "Hash Key"
        string Info
        string Operation
        string Path
        string Who
        string Version
        timestamp Created
        string Digest
    }

    TERRAFORM_LOCKS ||--o{ LOCK_INFO : contains

    LOCK_INFO {
        string ID
        string Operation "plan/apply/destroy"
        string Who "usuario@email.com"
        string Version "Terraform v1.6.0"
        string Created "2024-01-15T10:30:00Z"
        string Path "s3://bucket/terraform.tfstate"
    }
```

## State Operations Workflow

```mermaid
flowchart TD
    Start([State Management]) --> Operation{Tipo de<br/>Operación}

    Operation -->|Lectura| Read[terraform state list]
    Operation -->|Inspección| Show[terraform state show]
    Operation -->|Movimiento| Move[terraform state mv]
    Operation -->|Eliminación| Remove[terraform state rm]
    Operation -->|Importación| Import[terraform import]

    Read --> List[Listar Recursos:<br/>- aws_vpc.main<br/>- aws_subnet.public<br/>- aws_instance.web]

    Show --> Details[Mostrar Detalles:<br/>attributes:<br/>  id = vpc-123<br/>  cidr = 10.0.0.0/16]

    Move --> MoveOps[Mover Recurso:<br/>aws_instance.old<br/>→ aws_instance.new]
    MoveOps --> Refactor[Refactorización<br/>Sin Destruir Recursos]

    Remove --> RemoveOps[Eliminar del State<br/>No afecta AWS]
    RemoveOps --> Orphan[Recurso Huérfano<br/>Gestión Manual]

    Import --> ImportOps[Importar Recurso<br/>Existente]
    ImportOps --> Existing[Recurso AWS → State]

    List --> Validate{¿Validar?}
    Details --> Validate
    Refactor --> Validate
    Orphan --> Warning[⚠️ Recurso No Gestionado]
    Existing --> Validate

    Validate -->|Sí| Plan[terraform plan]
    Validate -->|No| End([Fin])
    Plan --> Changes{¿Cambios<br/>Inesperados?}
    Changes -->|Sí| Fix[Corregir State]
    Changes -->|No| End
    Fix --> Operation

    style Move fill:#FFD700
    style Remove fill:#FF6347
    style Import fill:#90EE90
    style Warning fill:#FF9800
```

## State Backends Comparison

```mermaid
graph TB
    Backends[Terraform State Backend] --> Local[Local Backend]
    Backends --> Remote1[S3 Backend]
    Backends --> Remote2[Terraform Cloud]
    Backends --> Remote3[Azure Blob Storage]
    Backends --> Remote4[GCS Backend]

    Local --> LocalPros[✅ Simple<br/>✅ No requiere config<br/>✅ Rápido]
    Local --> LocalCons[❌ No team collaboration<br/>❌ No locking<br/>❌ No encryption<br/>❌ No versioning]

    Remote1 --> S3Pros[✅ Versionado automático<br/>✅ Encryption at rest<br/>✅ Locking con DynamoDB<br/>✅ Multi-user<br/>✅ Bajo costo]
    Remote1 --> S3Cons[❌ Requiere AWS<br/>❌ Setup inicial]

    Remote2 --> TCPros[✅ Team collaboration<br/>✅ Locking nativo<br/>✅ UI visual<br/>✅ Policy enforcement<br/>✅ Sentinel policies]
    Remote2 --> TCCons[❌ Costo adicional<br/>❌ Vendor lock-in]

    Remote3 --> AzurePros[✅ Integración Azure<br/>✅ Blob versioning<br/>✅ Locking nativo]
    Remote3 --> AzureCons[❌ Requiere Azure<br/>❌ Setup moderado]

    Remote4 --> GCSPros[✅ Integración GCP<br/>✅ Object versioning<br/>✅ Locking nativo]
    Remote4 --> GCSCons[❌ Requiere GCP<br/>❌ Setup moderado]

    style Remote1 fill:#90EE90
    style Remote2 fill:#87CEEB
    style Local fill:#FFB6C1
```

## State Backend Configuration

```mermaid
flowchart LR
    subgraph Config["backend.tf"]
        Backend[terraform backend]
    end

    Backend --> S3Config[S3 Backend Config]

    S3Config --> Bucket[bucket:<br/>terraform-state-prod]
    S3Config --> Key[key:<br/>infrastructure/terraform.tfstate]
    S3Config --> Region[region:<br/>us-east-1]
    S3Config --> Encrypt[encrypt: true]
    S3Config --> DynamoTable[dynamodb_table:<br/>terraform-locks]
    S3Config --> Versioning[versioning: true]

    Encrypt --> KMS[KMS Key:<br/>alias/terraform-state]

    Versioning --> Lifecycle[Lifecycle Rules:<br/>- Retain 30 versions<br/>- Transition to IA after 90 days<br/>- Glacier after 365 days]

    DynamoTable --> LockConfig[LockID: Hash Key<br/>Billing: Pay-per-request]

    style Backend fill:#E1F5FF
    style S3Config fill:#87CEEB
    style KMS fill:#FFD700
    style LockConfig fill:#FF9800
```

## Best Practices Checklist

```mermaid
flowchart TD
    Start([State Management<br/>Best Practices]) --> BP1{✅ Remote Backend}
    BP1 -->|Sí| BP2{✅ State Locking}
    BP1 -->|No| Fix1[❌ Configurar S3 Backend]

    BP2 -->|Sí| BP3{✅ Encryption}
    BP2 -->|No| Fix2[❌ Configurar DynamoDB Lock]

    BP3 -->|Sí| BP4{✅ Versioning}
    BP3 -->|No| Fix3[❌ Habilitar Encryption KMS]

    BP4 -->|Sí| BP5{✅ Backup Strategy}
    BP4 -->|No| Fix4[❌ Habilitar S3 Versioning]

    BP5 -->|Sí| BP6{✅ Access Control}
    BP5 -->|No| Fix5[❌ Implementar Backups]

    BP6 -->|Sí| BP7{✅ Audit Logging}
    BP6 -->|No| Fix6[❌ Configurar IAM Policies]

    BP7 -->|Sí| Success[✅ State Management<br/>Production Ready]
    BP7 -->|No| Fix7[❌ Habilitar CloudTrail]

    Fix1 --> Start
    Fix2 --> Start
    Fix3 --> Start
    Fix4 --> Start
    Fix5 --> Start
    Fix6 --> Start
    Fix7 --> Start

    style Success fill:#90EE90
    style Fix1 fill:#FF6347
    style Fix2 fill:#FF6347
    style Fix3 fill:#FF6347
    style Fix4 fill:#FF6347
    style Fix5 fill:#FF6347
    style Fix6 fill:#FF6347
    style Fix7 fill:#FF6347
```

## Uso

Estos diagramas muestran:
1. Arquitectura completa del remote state con S3 y DynamoDB
2. Estructura interna del state file
3. Sistema de versionado automático con S3
4. Mecanismo de state locking para prevenir conflictos
5. Estructura de la tabla DynamoDB para locks
6. Operaciones comunes sobre el state
7. Comparación de diferentes backends
8. Configuration del backend
9. Checklist de best practices

Para más información, consulta la documentación oficial de Terraform sobre [State Management](https://www.terraform.io/docs/language/state/).
