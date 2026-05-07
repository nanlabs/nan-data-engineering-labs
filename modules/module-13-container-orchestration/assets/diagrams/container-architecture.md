# Arquitecturas de Contenedores para Data Engineering

## Evolución: Desde Servidores Tradicionales hasta Kubernetes

```mermaid
flowchart LR
    subgraph Traditional["⚙️ Servidores Tradicionales"]
        Server[Servidor Físico<br/>- Todo o nada<br/>- Lento deployment<br/>- Alto costo]
    end

    subgraph VM["💻 Máquinas Virtuales"]
        Hypervisor[Hypervisor]
        VM1[VM 1<br/>OS Completo]
        VM2[VM 2<br/>OS Completo]
        VM3[VM 3<br/>OS Completo]

        Hypervisor --> VM1
        Hypervisor --> VM2
        Hypervisor --> VM3
    end

    subgraph Containers["📦 Contenedores"]
        DockerEngine[Docker Engine]
        C1[Container 1<br/>App + Deps]
        C2[Container 2<br/>App + Deps]
        C3[Container 3<br/>App + Deps]

        DockerEngine --> C1
        DockerEngine --> C2
        DockerEngine --> C3
    end

    subgraph Orchestration["☸️ Orquestación"]
        K8s[Kubernetes<br/>- Auto-scaling<br/>- Self-healing<br/>- Load balancing]
    end

    Traditional -->|Evolución| VM
    VM -->|Optimización| Containers
    Containers -->|Escala| Orchestration

    style Traditional fill:#FFE1E1
    style VM fill:#FFF3E0
    style Containers fill:#E8F5E9
    style Orchestration fill:#E1F5FF
```text

## Arquitectura Completa: Docker + ECS + EKS

```mermaid
flowchart TB
    subgraph Dev["👨‍💻 Development"]
        Code[Código Python<br/>ETL Scripts]
        Dockerfile[Dockerfile<br/>Multi-stage]
        DockerCompose[docker-compose.yml<br/>Local Testing]
    end

    subgraph Registry["📦 Container Registry"]
        ECR[Amazon ECR<br/>Private Registry]
        Scan[Image Scanning<br/>Vulnerabilities]
    end

    subgraph ECS["🚀 AWS ECS/Fargate"]
        Cluster1[ECS Cluster]
        TaskDef1[Task Definition<br/>Container Specs]
        Service1[ECS Service<br/>Long-running]
        ScheduledTask[EventBridge<br/>Scheduled Tasks]

        Cluster1 --> TaskDef1
        TaskDef1 --> Service1
        TaskDef1 --> ScheduledTask
    end

    subgraph EKS["☸️ AWS EKS"]
        Cluster2[EKS Cluster]
        Deployment[Deployment<br/>Stateless Apps]
        StatefulSet[StatefulSet<br/>Databases]
        CronJob[CronJob<br/>Scheduled ETL]

        Cluster2 --> Deployment
        Cluster2 --> StatefulSet
        Cluster2 --> CronJob
    end

    subgraph DataPlatform["📊 Data Platform"]
        Spark[Apache Spark<br/>on K8s]
        Airflow[Apache Airflow<br/>KubernetesExecutor]
        Kafka[Apache Kafka<br/>Strimzi Operator]
    end

    subgraph Storage["💾 Storage"]
        S3[S3 Data Lake]
        EBS[EBS Volumes]
        EFS[EFS Shared Storage]
        RDS[(RDS Database)]
    end

    Code --> Dockerfile
    Dockerfile --> ECR
    ECR --> Scan

    DockerCompose -.->|Local Test| Code

    ECR --> TaskDef1
    ECR --> Deployment

    Service1 --> S3
    Service1 --> RDS

    Deployment --> S3
    StatefulSet --> EBS
    CronJob --> S3

    Cluster2 --> Spark
    Cluster2 --> Airflow
    Cluster2 --> Kafka

    Spark --> S3
    Airflow --> S3
    Kafka --> EFS

    style Dev fill:#E8F5E9
    style Registry fill:#FFD700
    style ECS fill:#87CEEB
    style EKS fill:#E1F5FF
    style DataPlatform fill:#FFF3E0
```text

## Docker: Multi-Stage Build para Data Engineering

```mermaid
flowchart TB
    subgraph Stage1["🔨 Stage 1: Builder"]
        Base1[FROM python:3.11-slim as builder]
        Install1[Install build dependencies<br/>gcc, g++, make]
        Deps1[Install Python wheels<br/>pandas, numpy, pyarrow]
        Compile[Compile C extensions<br/>Size: ~800 MB]
    end

    subgraph Stage2["📦 Stage 2: Runtime"]
        Base2[FROM python:3.11-slim as runtime]
        CopyWheels[COPY --from=builder<br/>Only compiled wheels]
        Runtime[Install runtime<br/>dependencies only]
        Copy[COPY application code]
        Final[Final Image<br/>Size: ~280 MB<br/>65% reduction]
    end

    Base1 --> Install1
    Install1 --> Deps1
    Deps1 --> Compile

    Compile -.->|Copy artifacts| CopyWheels

    Base2 --> CopyWheels
    CopyWheels --> Runtime
    Runtime --> Copy
    Copy --> Final

    style Stage1 fill:#FFE1E1
    style Stage2 fill:#E8F5E9
    style Final fill:#90EE90
```text

## ECS Fargate: Arquitectura de Task y Service

```mermaid
flowchart TB
    subgraph VPC["🔒 VPC"]
        subgraph PublicSubnet["Public Subnet"]
            ALB[Application<br/>Load Balancer]
        end

        subgraph PrivateSubnet1["Private Subnet 1a"]
            Task1[Fargate Task 1<br/>Container:<br/>- etl-processor<br/>- 2 vCPU<br/>- 4 GB RAM]
        end

        subgraph PrivateSubnet2["Private Subnet 1b"]
            Task2[Fargate Task 2<br/>Container:<br/>- etl-processor<br/>- 2 vCPU<br/>- 4 GB RAM]
        end

        subgraph PrivateSubnet3["Private Subnet 1c"]
            Task3[Fargate Task 3<br/>Container:<br/>- etl-processor<br/>- 2 vCPU<br/>- 4 GB RAM]
        end
    end

    Internet([Internet]) --> ALB
    ALB --> Task1
    ALB --> Task2
    ALB --> Task3

    Task1 --> S3[(S3 Data Lake)]
    Task2 --> S3
    Task3 --> S3

    Task1 --> RDS[(RDS)]
    Task2 --> RDS
    Task3 --> RDS

    subgraph AutoScaling["📈 Auto Scaling"]
        Target[Target Tracking<br/>CPU: 70%]
        Min[Min: 2 tasks]
        Max[Max: 10 tasks]

        Target --> ScaleOut[Scale Out<br/>Add tasks]
        Target --> ScaleIn[Scale In<br/>Remove tasks]
    end

    Task1 -.->|Metrics| Target
    Task2 -.->|Metrics| Target
    Task3 -.->|Metrics| Target

    style VPC fill:#E1F5FF
    style AutoScaling fill:#FFF3E0
```

## Kubernetes: Arquitectura de Control Plane y Data Plane

```mermaid
flowchart TB
    subgraph ControlPlane["☁️ Control Plane (AWS Managed)"]
        APIServer[API Server<br/>kubectl endpoint]
        Scheduler[Scheduler<br/>Pod placement]
        ControllerMgr[Controller Manager<br/>Desired state]
        etcd[(etcd<br/>Cluster state)]

        APIServer --> Scheduler
        APIServer --> ControllerMgr
        APIServer --> etcd
    end

    subgraph DataPlane["🖥️ Data Plane (Node Groups)"]
        subgraph Node1["Node 1 (t3.large)"]
            Kubelet1[kubelet]
            Pod1[Pod: Spark Driver<br/>4 GB RAM]
            Pod2[Pod: Airflow Worker<br/>2 GB RAM]

            Kubelet1 --> Pod1
            Kubelet1 --> Pod2
        end

        subgraph Node2["Node 2 (t3.large)"]
            Kubelet2[kubelet]
            Pod3[Pod: Spark Executor<br/>4 GB RAM]
            Pod4[Pod: Kafka Broker<br/>4 GB RAM]

            Kubelet2 --> Pod3
            Kubelet2 --> Pod4
        end

        subgraph Node3["Node 3 (t3.xlarge)"]
            Kubelet3[kubelet]
            Pod5[Pod: PostgreSQL<br/>StatefulSet<br/>8 GB RAM]

            Kubelet3 --> Pod5
        end
    end

    APIServer -.->|Schedule| Kubelet1
    APIServer -.->|Schedule| Kubelet2
    APIServer -.->|Schedule| Kubelet3

    Pod1 <-->|RPC| Pod3
    Pod2 <-->|Schedule| Pod1

    Pod5 --> PV1[(PersistentVolume<br/>EBS 100GB)]
    Pod4 --> PV2[(PersistentVolume<br/>EBS 200GB)]

    subgraph Services["🔄 Services"]
        Service1[LoadBalancer<br/>Airflow UI]
        Service2[ClusterIP<br/>PostgreSQL]
        Service3[NodePort<br/>Kafka]
    end

    Service1 --> Pod2
    Service2 --> Pod5
    Service3 --> Pod4

    Internet([Internet]) --> LB[AWS ALB]
    LB --> Service1

    style ControlPlane fill:#FFD700
    style DataPlane fill:#E8F5E9
```text

## Spark on Kubernetes con Spark Operator

```mermaid
flowchart TB
    subgraph User["👨‍💻 Usuario"]
        SparkApp[SparkApplication<br/>YAML Manifest]
    end

    subgraph K8s["☸️ Kubernetes Cluster"]
        APIServer[Kubernetes<br/>API Server]

        subgraph Operator["🔧 Spark Operator"]
            Controller[Spark Operator<br/>Controller]
            CRD[SparkApplication<br/>Custom Resource]
        end

        subgraph DriverPod["Driver Pod"]
            Driver[Spark Driver<br/>- 1 core<br/>- 2 GB RAM<br/>- Orchestrates job]
        end

        subgraph ExecutorPods["Executor Pods (Dynamic)"]
            Exec1[Executor 1<br/>- 2 cores<br/>- 4 GB RAM]
            Exec2[Executor 2<br/>- 2 cores<br/>- 4 GB RAM]
            Exec3[Executor 3<br/>- 2 cores<br/>- 4 GB RAM]
            ExecN[Executor N<br/>Scales 2-10<br/>based on workload]
        end

        subgraph HistoryServer["📊 History Server"]
            History[Spark History<br/>Server Pod]
        end
    end

    subgraph Storage["💾 Storage"]
        S3Events[S3 Event Logs]
        S3Data[S3 Data Lake<br/>Input/Output]
    end

    SparkApp --> APIServer
    APIServer --> Controller
    Controller --> CRD
    CRD --> Driver

    Driver --> Exec1
    Driver --> Exec2
    Driver --> Exec3
    Driver --> ExecN

    Driver -.->|Request| APIServer
    APIServer -.->|Create| Exec1
    APIServer -.->|Create| Exec2
    APIServer -.->|Scale Down| ExecN

    Driver --> S3Events
    Exec1 --> S3Data
    Exec2 --> S3Data
    Exec3 --> S3Data

    S3Events --> History

    style Operator fill:#FFD700
    style DriverPod fill:#87CEEB
    style ExecutorPods fill:#E8F5E9
```text

## Comparación: ECS vs EKS vs Lambda

```mermaid
flowchart TB
    Start([Elegir Plataforma<br/>de Contenedores]) --> Question{Criterios de<br/>Decisión}

    Question --> Duration{Duration<br/>Ejecución}
    Question --> Scale{Escala}
    Question --> Complexity{Complejidad}
    Question --> Cost{Costo}
    Question --> Control{Control}

    Duration -->|< 15 min| Lambda[AWS Lambda<br/>Serverless<br/>✅ Simple<br/>✅ Sin gestión<br/>❌ Límite 15 min]

    Duration -->|15 min - 24h| ECSChoice{ECS Fargate}
    ECSChoice --> ECS[AWS ECS/Fargate<br/>✅ Simple<br/>✅ AWS nativo<br/>✅ Auto-scaling<br/>❌ Vendor lock-in]

    Duration -->|> 24h| EKS[Amazon EKS<br/>Kubernetes<br/>✅ Portabilidad<br/>✅ Ecosistema<br/>❌ Complejidad]

    Scale -->|< 100 tasks| Lambda
    Scale -->|100-1000 tasks| ECS
    Scale -->|> 1000 tasks| EKS

    Complexity -->|Simple| Lambda
    Complexity -->|Medio| ECS
    Complexity -->|Avanzado| EKS

    Cost -->|Pay-per-use| Lambda
    Cost -->|Medio| ECS
    Cost -->|Optimizable| EKS

    Control -->|Bajo| Lambda
    Control -->|Medio| ECS
    Control -->|Alto| EKS

    Lambda --> UseCaseLambda[Use Cases:<br/>- Event processing<br/>- API backends<br/>- Simple ETL]

    ECS --> UseCaseECS[Use Cases:<br/>- Long-running services<br/>- Scheduled jobs<br/>- Simple microservices]

    EKS --> UseCaseEKS[Use Cases:<br/>- Complex platforms<br/>- Multi-cloud<br/>- Data pipelines<br/>- ML workloads]

    style Lambda fill:#FFD700
    style ECS fill:#87CEEB
    style EKS fill:#E8F5E9
```text

## Monitoring Stack para Contenedores

```mermaid
flowchart TB
    subgraph Apps["📦 Containerized Apps"]
        ECSTask[ECS Tasks]
        K8sPods[Kubernetes Pods]
    end

    subgraph Metrics["📊 Metrics Collection"]
        CWAgent[CloudWatch Agent<br/>ECS]
        Prometheus[Prometheus<br/>K8s Metrics]
        NodeExporter[Node Exporter<br/>System Metrics]
    end

    subgraph Visualization["📈 Visualization"]
        CW[CloudWatch<br/>Dashboards]
        Grafana[Grafana<br/>Dashboards]
    end

    subgraph Logs["📝 Logs"]
        CWLogs[CloudWatch Logs]
        FluentBit[Fluent Bit<br/>Log Forwarder]
    end

    subgraph Tracing["🔍 Tracing"]
        XRay[AWS X-Ray<br/>Distributed Tracing]
        Jaeger[Jaeger<br/>OpenTelemetry]
    end

    subgraph Alerting["🚨 Alerting"]
        Alarms[CloudWatch Alarms]
        AlertManager[Alert Manager<br/>Prometheus]
        SNS[SNS Notifications]
        PagerDuty[PagerDuty<br/>Incident Response]
    end

    ECSTask --> CWAgent
    K8sPods --> Prometheus
    K8sPods --> NodeExporter

    CWAgent --> CW
    Prometheus --> Grafana
    NodeExporter --> Prometheus

    ECSTask --> CWLogs
    K8sPods --> FluentBit
    FluentBit --> CWLogs

    ECSTask --> XRay
    K8sPods --> Jaeger

    CW --> Alarms
    Grafana --> AlertManager

    Alarms --> SNS
    AlertManager --> SNS
    SNS --> PagerDuty

    style Metrics fill:#E8F5E9
    style Visualization fill:#E1F5FF
    style Logs fill:#FFF3E0
    style Tracing fill:#FFE1E1
    style Alerting fill:#FFD700
```

## Uso

Estos diagramas muestran:

1. Evolución de infraestructura: servidores → VMs → contenedores → orquestación
2. Arquitectura completa con Docker, ECS y EKS
3. Multi-stage builds para optimización de imágenes
4. ECS Fargate con auto-scaling
5. Kubernetes control plane y data plane
6. Spark on Kubernetes con dynamic allocation
7. Comparación ECS vs EKS vs Lambda
8. Stack completo de monitoreo para contenedores

Para más información, consulta las documentaciones oficiales de [Docker](https://docs.docker.com/), [ECS](https://docs.aws.amazon.com/ecs/) y [EKS](https://docs.aws.amazon.com/eks/).
