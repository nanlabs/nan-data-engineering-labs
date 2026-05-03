# Kubernetes: Patrones de Deployment para Data Engineering

## Pod Lifecycle y Estados

```mermaid
stateDiagram-v2
    [*] --> Pending: Pod Created

    Pending --> Scheduling: Waiting for<br/>node assignment
    Scheduling --> Pending: No resources
    Scheduling --> ContainerCreating: Node assigned

    ContainerCreating --> ImagePull: Pulling images
    ImagePull --> Running: Images pulled<br/>containers started

    Running --> Succeeded: All containers<br/>completed successfully
    Running --> Failed: Container error<br/>or crash
    Running --> Running: Restart on failure

    Running --> Terminating: Delete requested
    Terminating --> Succeeded: Graceful shutdown
    Terminating --> Failed: Forced termination

    Succeeded --> [*]
    Failed --> [*]

    note right of Pending
        InitContainers run
        Volume mounting
    end note

    note right of Running
        Liveness probes
        Readiness probes
        Health checks
    end note
```

## Deployment Strategies

```mermaid
flowchart TB
    Start([Deployment Update]) --> Strategy{Strategy<br/>Type}

    Strategy --> RollingUpdate[Rolling Update<br/>Default Strategy]
    Strategy --> Recreate[Recreate<br/>All at once]
    Strategy --> BlueGreen[Blue/Green<br/>Zero downtime]
    Strategy --> Canary[Canary<br/>Gradual rollout]

    subgraph Rolling["🔄 Rolling Update"]
        R1[Current: 3 pods<br/>v1.0]
        R2[Create 1 pod v1.1]
        R3[Total: 4 pods<br/>3x v1.0, 1x v1.1]
        R4[Delete 1 pod v1.0]
        R5[Repeat until<br/>all v1.1]

        R1 --> R2 --> R3 --> R4 --> R5
    end

    subgraph Rec["♻️ Recreate"]
        RC1[Current: 3 pods v1.0]
        RC2[Delete all pods]
        RC3[Downtime ⚠️]
        RC4[Create 3 pods v1.1]

        RC1 --> RC2 --> RC3 --> RC4
    end

    subgraph BG["🔵🟢 Blue/Green"]
        BG1[Blue: 3 pods v1.0<br/>Receiving traffic]
        BG2[Green: 3 pods v1.1<br/>Warmup]
        BG3[Switch Service<br/>to Green]
        BG4[Green active<br/>Blue standby]
        BG5[Delete Blue]

        BG1 --> BG2 --> BG3 --> BG4 --> BG5
    end

    subgraph Can["🐤 Canary"]
        C1[Current: 10 pods v1.0<br/>100% traffic]
        C2[Add 1 pod v1.1<br/>10% traffic]
        C3[Monitor metrics<br/>30 minutes]
        C4{Healthy?}
        C5[Increase to 50%<br/>5 pods v1.1]
        C6[Rollback to v1.0]
        C7[Complete: v1.1<br/>100% traffic]

        C1 --> C2 --> C3 --> C4
        C4 -->|Yes| C5 --> C7
        C4 -->|No| C6
    end

    RollingUpdate --> Rolling
    Recreate --> Rec
    BlueGreen --> BG
    Canary --> Can

    style Rolling fill:#E8F5E9
    style Rec fill:#FFE1E1
    style BG fill:#E1F5FF
    style Can fill:#FFF3E0
```

## StatefulSet vs Deployment

```mermaid
flowchart LR
    subgraph Deployment["Deployment (Stateless)"]
        D1[Pod: web-abc123<br/>Random name<br/>Any node]
        D2[Pod: web-def456<br/>Random name<br/>Any node]
        D3[Pod: web-ghi789<br/>Random name<br/>Any node]

        SvcD[Service<br/>Load Balancer]

        SvcD --> D1
        SvcD --> D2
        SvcD --> D3
    end

    subgraph StatefulSet["StatefulSet (Stateful)"]
        S1[Pod: kafka-0<br/>Fixed name<br/>Fixed node]
        S2[Pod: kafka-1<br/>Fixed name<br/>Fixed node]
        S3[Pod: kafka-2<br/>Fixed name<br/>Fixed node]

        PV1[(PVC: kafka-0<br/>EBS Volume)]
        PV2[(PVC: kafka-1<br/>EBS Volume)]
        PV3[(PVC: kafka-2<br/>EBS Volume)]

        SvcS[Headless Service<br/>DNS per pod]

        S1 --> PV1
        S2 --> PV2
        S3 --> PV3

        SvcS -.-> S1
        SvcS -.-> S2
        SvcS -.-> S3
    end

    Compare{Use Case}

    Compare -->|Stateless<br/>Interchangeable<br/>No persistent data| Deployment
    Compare -->|Stateful<br/>Unique identity<br/>Persistent data<br/>Ordered operations| StatefulSet

    style Deployment fill:#E8F5E9
    style StatefulSet fill:#E1F5FF
```

## Service Types y Network Architecture

```mermaid
flowchart TB
    subgraph Internet["🌐 Internet"]
        Users[External Users]
    end

    subgraph AWS["☁️ AWS"]
        ALB[Application<br/>Load Balancer]
        NLB[Network<br/>Load Balancer]
    end

    subgraph K8sCluster["☸️ Kubernetes Cluster"]
        subgraph Ingress["Ingress Controller"]
            IngressALB[AWS Load Balancer<br/>Controller]
            IngressRules[Ingress Rules<br/>Path-based routing]
        end

        subgraph Services["Services"]
            SvcLB[LoadBalancer Service<br/>External access<br/>Creates AWS ALB/NLB]

            SvcNodePort[NodePort Service<br/>Port on each node<br/>30000-32767]

            SvcClusterIP[ClusterIP Service<br/>Internal only<br/>Default type]

            SvcHeadless[Headless Service<br/>No load balancing<br/>Direct Pod DNS]
        end

        subgraph Pods["Pods"]
            Pod1[Pod: Airflow UI<br/>8080]
            Pod2[Pod: FastAPI<br/>8000]
            Pod3[Pod: PostgreSQL<br/>5432]
            Pod4[Pod: Kafka Broker<br/>9092]
        end
    end

    Users --> ALB
    ALB --> IngressALB
    IngressALB --> IngressRules

    IngressRules -->|/airflow/*| SvcClusterIP
    IngressRules -->|/api/*| SvcClusterIP

    SvcLB --> NLB
    NLB --> Pod1

    SvcNodePort -->|NodePort: 32001| Pod2

    SvcClusterIP --> Pod1
    SvcClusterIP --> Pod2
    SvcClusterIP --> Pod3

    SvcHeadless -.->|kafka-0.kafka| Pod4
    SvcHeadless -.->|kafka-1.kafka| Pod4

    style Ingress fill:#FFD700
    style Services fill:#87CEEB
    style Pods fill:#E8F5E9
```

## Storage: PersistentVolume and PersistentVolumeClaim

```mermaid
flowchart TB
    subgraph Admin["👨‍💼 Cluster Admin"]
        SC[StorageClass<br/>- Type: gp3<br/>- IOPS: 3000<br/>- Provisioner: ebs.csi.aws.com]
    end

    subgraph Developer["👨‍💻 Developer"]
        PVC[PersistentVolumeClaim<br/>Request:<br/>- Size: 100Gi<br/>- AccessMode: ReadWriteOnce<br/>- StorageClass: gp3]
    end

    subgraph K8s["☸️ Kubernetes"]
        CSIDriver[EBS CSI Driver<br/>Dynamic Provisioner]
        PV[PersistentVolume<br/>- Bound to PVC<br/>- Type: AWS EBS]
    end

    subgraph AWS["☁️ AWS"]
        EBS[(EBS Volume<br/>vol-abc123<br/>100 GB gp3)]
    end

    subgraph Pod["Pod"]
        Container[Container<br/>PostgreSQL]
        Mount[VolumeMount<br/>/var/lib/postgresql/data]
    end

    SC --> CSIDriver
    PVC --> CSIDriver
    CSIDriver --> PV
    PV --> EBS

    PVC -.->|References| PV
    Container --> Mount
    Mount --> PV

    Lifecycle{Lifecycle}
    Lifecycle -->|Pod deleted| Retain[Volume Retained]
    Lifecycle -->|PVC deleted| Delete[Volume Deleted]
    Lifecycle -->|Reclaim Policy| Policy[Bound → Released<br/>→ Available]

    style SC fill:#FFD700
    style PVC fill:#87CEEB
    style PV fill:#E8F5E9
    style Pod fill:#E1F5FF
```

## ConfigMaps and Secrets Management

```mermaid
flowchart TB
    subgraph External["🔐 External Secrets"]
        SSM[AWS Systems<br/>Manager<br/>Parameter Store]
        SecretsMgr[AWS Secrets<br/>Manager]
        Vault[HashiCorp Vault]
    end

    subgraph K8sSecrets["☸️ Kubernetes Secrets"]
        ExternalOperator[External Secrets<br/>Operator]

        Secret1[Secret: db-credentials<br/>Type: Opaque<br/>- username<br/>- password]

        Secret2[Secret: api-keys<br/>Type: Opaque<br/>- s3_access_key<br/>- s3_secret_key]

        Secret3[Secret: tls-cert<br/>Type: kubernetes.io/tls<br/>- tls.crt<br/>- tls.key]
    end

    subgraph K8sConfig["⚙️ Kubernetes ConfigMaps"]
        CM1[ConfigMap: app-config<br/>- database_host<br/>- database_port<br/>- log_level]

        CM2[ConfigMap: spark-config<br/>- spark.executor.memory<br/>- spark.executor.cores]
    end

    subgraph Pods["📦 Pods"]
        Pod1[Pod: ETL Job]

        EnvSecret[Environment Variables<br/>from Secret]
        EnvConfig[Environment Variables<br/>from ConfigMap]

        VolumeSecret[Volume Mount<br/>/etc/secrets/<br/>from Secret]
        VolumeConfig[Volume Mount<br/>/etc/config/<br/>from ConfigMap]
    end

    SSM --> ExternalOperator
    SecretsMgr --> ExternalOperator
    Vault --> ExternalOperator

    ExternalOperator --> Secret1
    ExternalOperator --> Secret2

    Secret1 --> EnvSecret
    Secret2 --> VolumeSecret
    Secret3 --> VolumeSecret

    CM1 --> EnvConfig
    CM2 --> VolumeConfig

    EnvSecret --> Pod1
    EnvConfig --> Pod1
    VolumeSecret --> Pod1
    VolumeConfig --> Pod1

    style External fill:#FFD700
    style K8sSecrets fill:#FFE1E1
    style K8sConfig fill:#E1F5FF
    style Pods fill:#E8F5E9
```

## Auto-Scaling: HPA + Cluster Autoscaler

```mermaid
flowchart TB
    subgraph Metrics["📊 Metrics"]
        MetricsServer[Metrics Server<br/>CPU/Memory]
        Prometheus[Prometheus<br/>Custom Metrics]
    end

    subgraph HPA["📈 Horizontal Pod Autoscaler"]
        HPAController[HPA Controller]
        HPAConfig[HPA Config:<br/>- Min: 2 pods<br/>- Max: 10 pods<br/>- Target CPU: 70%<br/>- Target Memory: 80%]
    end

    subgraph Deployment["Deployment"]
        Current[Current: 3 pods<br/>CPU: 85%]
        ScaleUp[Scale Up to 5 pods<br/>CPU drops to 60%]
    end

    subgraph Nodes["🖥️ Nodes"]
        Node1[Node 1<br/>4 pods<br/>80% capacity]
        Node2[Node 2<br/>3 pods<br/>60% capacity]
        NodeNew[Node 3<br/>NO CAPACITY]
    end

    subgraph CA["🔄 Cluster Autoscaler"]
        CAController[Cluster Autoscaler]
        ASG[Auto Scaling Group<br/>Min: 2 nodes<br/>Max: 10 nodes]
    end

    MetricsServer --> HPAController
    Prometheus --> HPAController

    HPAController --> HPAConfig
    HPAConfig --> Current

    Current -->|CPU > 70%| ScaleUp

    ScaleUp -->|Schedule pods| Node1
    ScaleUp -->|Schedule pods| Node2
    ScaleUp -->|Pending pods| NodeNew

    NodeNew -->|No capacity| CAController
    CAController --> ASG
    ASG -->|Add node| NewNode[Node 3<br/>Created<br/>t3.large]

    NewNode -->|Pod scheduled| Running[All pods running<br/>Cluster healthy]

    Quiet[Low traffic period]
    Quiet -->|< 30% CPU| ScaleDown[HPA scales down<br/>to 2 pods]
    ScaleDown -->|Underutilized| CAController
    CAController -->|Remove node| Terminate[Node 1 terminated<br/>Cost saved]

    style HPA fill:#E8F5E9
    style CA fill:#87CEEB
    style Running fill:#90EE90
```

## Deployment Workflow: GitOps with ArgoCD

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant CI as CI Pipeline
    participant ECR as Container Registry
    participant Argo as ArgoCD
    participant K8s as Kubernetes Cluster

    Dev->>Git: 1. Push code changes
    Git->>CI: 2. Trigger build

    activate CI
    CI->>CI: 3. Run tests
    CI->>CI: 4. Build Docker image
    CI->>ECR: 5. Push image<br/>tag: v1.2.3
    deactivate CI

    Dev->>Git: 6. Update K8s manifests<br/>image: v1.2.3

    Git->>Argo: 7. ArgoCD detects change
    activate Argo
    Argo->>Argo: 8. Compare desired vs actual
    Argo->>K8s: 9. Apply changes
    deactivate Argo

    activate K8s
    K8s->>K8s: 10. Rolling update
    K8s->>ECR: 11. Pull image v1.2.3
    K8s->>K8s: 12. Create new pods
    K8s->>K8s: 13. Terminate old pods
    deactivate K8s

    K8s->>Argo: 14. Sync complete
    Argo->>Dev: 15. Deployment successful

    Note over Argo,K8s: Continuous reconciliation<br/>every 3 minutes

    alt Deployment Failed
        K8s->>Argo: Health check failed
        Argo->>K8s: Auto-rollback to v1.2.2
        Argo->>Dev: Alert: Rollback triggered
    end
```

## Resource Management: Requests vs Limits

```mermaid
flowchart TB
    subgraph Pod["Pod Specification"]
        Container[Container Definition]
    end

    Container --> Resources{Resources}

    Resources --> Requests[Requests<br/>Guaranteed minimum]
    Resources --> Limits[Limits<br/>Maximum allowed]

    subgraph Req["📊 Requests"]
        ReqCPU[cpu: 500m<br/>0.5 cores<br/>guaranteed]
        ReqMem[memory: 1Gi<br/>1 GB guaranteed]

        ReqSched[Used for:<br/>- Scheduling decisions<br/>- Node selection<br/>- QoS class]
    end

    subgraph Lim["🚫 Limits"]
        LimCPU[cpu: 2000m<br/>2 cores maximum<br/>throttled if exceeded]
        LimMem[memory: 4Gi<br/>4 GB maximum<br/>killed if exceeded]

        LimEnforce[Enforced by:<br/>- cgroups (CPU)<br/>- OOM killer (Memory)]
    end

    Requests --> Req
    Limits --> Lim

    subgraph QoS["Quality of Service Classes"]
        Guaranteed[Guaranteed<br/>Requests = Limits<br/>Highest priority]

        Burstable[Burstable<br/>Requests < Limits<br/>Medium priority]

        BestEffort[BestEffort<br/>No requests/limits<br/>Lowest priority]
    end

    Req --> QoSLogic{QoS<br/>Class}
    Lim --> QoSLogic

    QoSLogic -->|Requests = Limits| Guaranteed
    QoSLogic -->|Requests < Limits| Burstable
    QoSLogic -->|No values| BestEffort

    subgraph Eviction["Pod Eviction Order"]
        E1[1. BestEffort pods<br/>evicted first]
        E2[2. Burstable pods<br/>exceeding requests]
        E3[3. Guaranteed pods<br/>last resort]

        E1 --> E2 --> E3
    end

    QoSLogic --> Eviction

    style Req fill:#E8F5E9
    style Lim fill:#FFE1E1
    style Guaranteed fill:#90EE90
    style Burstable fill:#FFD700
    style BestEffort fill:#FF9800
```

## Uso

Estos diagramas muestran:
1. Pod lifecycle y estados en Kubernetes
2. Estrategias de deployment (Rolling, Recreate, Blue/Green, Canary)
3. Diferencias entre Deployment y StatefulSet
4. Service types y arquitectura de red
5. PersistentVolume y claims para storage
6. ConfigMaps y Secrets management
7. Auto-scaling con HPA y Cluster Autoscaler
8. GitOps workflow con ArgoCD
9. Resource requests vs limits y QoS classes

Para más información, consulta la [documentación oficial de Kubernetes](https://kubernetes.io/docs/).
