# Arquitectura Multi-Región AWS

## Arquitectura Global de Data Platform

```mermaid
flowchart TB
    subgraph Global["🌍 Global Services"]
        R53[Route 53<br/>DNS Global]
        CF[CloudFront<br/>CDN Global]
        IAM[IAM<br/>Gestión Global de Acceso]
    end

    subgraph USEast1["🇺🇸 us-east-1 (Virginia) - PRIMARY"]
        subgraph VPC1["VPC 10.0.0.0/16"]
            subgraph Public1["Public Subnets"]
                NAT1[NAT Gateway]
                ALB1[Application<br/>Load Balancer]
            end
            subgraph Private1["Private Subnets"]
                ECS1[ECS Fargate<br/>Data Processing]
                Lambda1[Lambda Functions<br/>ETL]
                Glue1[Glue Jobs]
            end
            subgraph Data1["Data Subnets"]
                RDS1[(RDS Primary<br/>PostgreSQL)]
                Redshift1[(Redshift<br/>Data Warehouse)]
            end
        end
        S31[S3 Data Lake<br/>Primary Region]
        DynamoDB1[(DynamoDB<br/>Global Tables)]
        KMS1[KMS<br/>Encryption Keys]
    end

    subgraph USWest2["🇺🇸 us-west-2 (Oregon) - SECONDARY"]
        subgraph VPC2["VPC 10.1.0.0/16"]
            subgraph Public2["Public Subnets"]
                NAT2[NAT Gateway]
                ALB2[Application<br/>Load Balancer]
            end
            subgraph Private2["Private Subnets"]
                ECS2[ECS Fargate<br/>Data Processing]
                Lambda2[Lambda Functions<br/>ETL]
                Glue2[Glue Jobs]
            end
            subgraph Data2["Data Subnets"]
                RDS2[(RDS Replica<br/>Read Replica)]
                Redshift2[(Redshift<br/>Disaster Recovery)]
            end
        end
        S32[S3 Data Lake<br/>Replicated<br/>CRR Enabled]
        DynamoDB2[(DynamoDB<br/>Global Tables)]
        KMS2[KMS<br/>Encryption Keys]
    end

    R53 --> CF
    CF --> ALB1
    CF --> ALB2

    ALB1 --> ECS1
    ALB2 --> ECS2

    ECS1 --> Lambda1
    ECS2 --> Lambda2

    Lambda1 --> S31
    Lambda2 --> S32

    S31 -.->|Cross-Region<br/>Replication| S32

    Lambda1 --> DynamoDB1
    Lambda2 --> DynamoDB2
    DynamoDB1 <-.->|Global Tables<br/>Replication| DynamoDB2

    RDS1 -.->|Read Replica<br/>Async Replication| RDS2

    Glue1 --> S31
    Glue2 --> S32

    ECS1 --> RDS1
    ECS2 --> RDS2

    IAM -.-> VPC1
    IAM -.-> VPC2

    style Global fill:#E1F5FF
    style USEast1 fill:#E8F5E9
    style USWest2 fill:#FFF3E0
    style S31 fill:#87CEEB
    style S32 fill:#87CEEB
    style RDS1 fill:#4CAF50
    style RDS2 fill:#8BC34A
```text

## Estrategia de Disaster Recovery

```mermaid
flowchart TD
    Start([Inicio]) --> Monitor[Monitoreo Continuo<br/>CloudWatch + Route53 Health Checks]
    Monitor --> Status{Estado<br/>Primary Region}

    Status -->|✅ Healthy| Primary[us-east-1<br/>PRIMARY ACTIVE]
    Status -->|❌ Failure| Detect[Detectar Fallo]

    Primary --> Traffic1[100% Tráfico]
    Traffic1 --> Monitor

    Detect --> Alert[Alerta SNS<br/>Notificar Equipo]
    Alert --> Failover[Iniciar Failover]

    Failover --> DNS[Route53 DNS Update]
    DNS --> Secondary[us-west-2<br/>SECONDARY ACTIVE]
    Secondary --> Traffic2[100% Tráfico]

    Traffic2 --> Verify{¿Operación<br/>Normal?}
    Verify -->|Sí| Stable[Sistema Estable]
    Verify -->|No| Rollback[Investigar Problema]

    Stable --> Wait[Esperar Primary Recovery]
    Wait --> PrimaryStatus{Primary<br/>Restaurado?}

    PrimaryStatus -->|No| Stable
    PrimaryStatus -->|Sí| Failback[Iniciar Failback]

    Failback --> Sync[Sincronizar Datos]
    Sync --> TestPrimary[Validar Primary]
    TestPrimary --> SwitchBack[DNS Update a Primary]
    SwitchBack --> Monitor

    Rollback --> Manual[Intervención Manual]
    Manual --> Stable

    style Primary fill:#90EE90
    style Secondary fill:#FFD700
    style Alert fill:#FF6347
    style Stable fill:#87CEEB
```text

## Terraform Module Structure para Multi-Región

```mermaid
graph TB
    Root[Root Module<br/>main.tf] --> Provider1[Provider us-east-1]
    Root --> Provider2[Provider us-west-2]

    Provider1 --> Region1[Module: region]
    Provider2 --> Region2[Module: region]

    Region1 --> VPC1[Module: vpc]
    Region1 --> Compute1[Module: compute]
    Region1 --> Data1[Module: data-storage]
    Region1 --> Network1[Module: networking]

    Region2 --> VPC2[Module: vpc]
    Region2 --> Compute2[Module: compute]
    Region2 --> Data2[Module: data-storage]
    Region2 --> Network2[Module: networking]

    VPC1 --> Outputs1[Outputs:<br/>vpc_id<br/>subnet_ids<br/>security_groups]
    VPC2 --> Outputs2[Outputs:<br/>vpc_id<br/>subnet_ids<br/>security_groups]

    Outputs1 --> Global[Global Resources:<br/>Route53<br/>CloudFront<br/>IAM]
    Outputs2 --> Global

    Global --> State[(Remote State<br/>S3 + DynamoDB Lock)]

    style Root fill:#E1F5FF
    style Global fill:#FFE1E1
    style State fill:#87CEEB
```text

## Replicación de Datos

```mermaid
flowchart LR
    subgraph Primary["Primary Region (us-east-1)"]
        S3P[S3 Bucket<br/>data-lake-primary]
        RDSP[(RDS Primary<br/>Writer)]
        DDEP[(DynamoDB<br/>Table)]
    end

    subgraph Secondary["Secondary Region (us-west-2)"]
        S3S[S3 Bucket<br/>data-lake-secondary]
        RDSS[(RDS Replica<br/>Reader)]
        DDES[(DynamoDB<br/>Global Table)]
    end

    S3P -->|S3 Cross-Region<br/>Replication<br/>Async| S3S
    RDSP -->|RDS Read Replica<br/>Async Replication<br/>~1-5 sec lag| RDSS
    DDEP <-->|DynamoDB Global Tables<br/>Active-Active<br/>~1 sec lag| DDES

    S3P -.->|Lifecycle Policy| Glacier[S3 Glacier<br/>Long-term Archive]
    S3S -.->|Lifecycle Policy| GlacierS[S3 Glacier<br/>Long-term Archive]

    style S3P fill:#87CEEB
    style S3S fill:#87CEEB
    style RDSP fill:#4CAF50
    style RDSS fill:#8BC34A
    style DDEP fill:#FF9800
    style DDES fill:#FF9800
```

## Cost Optimization Multi-Región

```mermaid
flowchart TD
    Start([Evaluación de Costos]) --> Strategy{Estrategia<br/>DR}

    Strategy -->|Pilot Light| Pilot[Recursos Mínimos<br/>en Secondary]
    Strategy -->|Warm Standby| Warm[Recursos Reducidos<br/>Siempre Activos]
    Strategy -->|Hot Standby| Hot[Recursos Completos<br/>Active-Active]

    Pilot --> PilotCost[Costo: ~10-20%<br/>RTO: 30-60 min<br/>RPO: 5-15 min]
    Warm --> WarmCost[Costo: ~40-60%<br/>RTO: 5-15 min<br/>RPO: 1-5 min]
    Hot --> HotCost[Costo: ~100-150%<br/>RTO: <1 min<br/>RPO: <1 min]

    PilotCost --> Optimize[Optimizaciones]
    WarmCost --> Optimize
    HotCost --> Optimize

    Optimize --> Opt1[Reserved Instances]
    Optimize --> Opt2[Savings Plans]
    Optimize --> Opt3[S3 Lifecycle Policies]
    Optimize --> Opt4[Right Sizing]
    Optimize --> Opt5[Auto Scaling]

    Opt1 --> Result[Reducción 30-50%]
    Opt2 --> Result
    Opt3 --> Result
    Opt4 --> Result
    Opt5 --> Result

    style Pilot fill:#E8F5E9
    style Warm fill:#FFF3E0
    style Hot fill:#FFEBEE
    style Result fill:#90EE90
```text

## Network Peering y Conectividad

```mermaid
flowchart TB
    subgraph OnPrem["🏢 On-Premises"]
        DC[Data Center]
        Corp[Corporate Network]
    end

    subgraph Transit["Transit Gateway"]
        TGW[AWS Transit Gateway<br/>Hub Central]
    end

    subgraph Region1["us-east-1"]
        VPC1[VPC 10.0.0.0/16]
        DX1[Direct Connect<br/>Dedicated 10Gbps]
    end

    subgraph Region2["us-west-2"]
        VPC2[VPC 10.1.0.0/16]
        DX2[Direct Connect<br/>Dedicated 10Gbps]
    end

    subgraph Region3["eu-west-1"]
        VPC3[VPC 10.2.0.0/16]
        VPN3[VPN Connection<br/>Backup]
    end

    DC --> DX1
    DC --> DX2
    Corp --> VPN3

    DX1 --> TGW
    DX2 --> TGW
    VPN3 --> TGW

    TGW --> VPC1
    TGW --> VPC2
    TGW --> VPC3

    VPC1 -.->|VPC Peering<br/>Backup| VPC2
    VPC2 -.->|VPC Peering<br/>Backup| VPC3

    style OnPrem fill:#E0E0E0
    style Transit fill:#87CEEB
    style Region1 fill:#E8F5E9
    style Region2 fill:#FFF3E0
    style Region3 fill:#E1F5FF
```text

## Uso

Estos diagramas muestran:

1. Arquitectura completa multi-región con servicios globales y regionales
2. Estrategia de disaster recovery y failover
3. Estructura de modules Terraform para gestionar múltiples regiones
4. Patrones de replicación de datos entre regiones
5. Estrategias de optimización de costos
6. Conectividad de red entre regiones y on-premises

**RTO** (Recovery Time Objective): Tiempo máximo de inactividad aceptable
**RPO** (Recovery Point Objective): Máxima pérdida de datos aceptable
