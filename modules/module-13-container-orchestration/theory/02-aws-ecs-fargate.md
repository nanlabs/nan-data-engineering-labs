# AWS ECS & Fargate para Data Engineering

## 📋 Índice

1. [Introducción a ECS](#introduccion-ecs)
2. [ECS vs Fargate vs EC2](#ecs-vs-fargate-vs-ec2)
3. [Task Definitions](#task-definitions)
4. [Services y Deployment](#services-deployment)
5. [Networking en ECS](#networking-ecs)
6. [Storage y Logging](#storage-logging)
7. [Scheduling y Batch Processing](#scheduling-batch)
8. [Monitoring y Troubleshooting](#monitoring)

---

## 1. Introducción a ECS

**Amazon Elastic Container Service (ECS)** es un servicio de orquestación de containers completamente administrado.

### Arquitectura ECS

```
┌──────────────────────────────────────────────────────────┐
│                    AWS ECS Architecture                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              ECS Cluster                             │ │
│  │  (Logical grouping of tasks/services)               │ │
│  └────────────┬────────────────────┬───────────────────┘ │
│               │                    │                      │
│    ┌──────────▼──────┐   ┌────────▼──────────┐          │
│    │   Fargate       │   │   EC2 Launch Type │          │
│    │  (Serverless)   │   │   (Self-managed)  │          │
│    └──────────┬──────┘   └────────┬──────────┘          │
│               │                    │                      │
│      ┌────────▼────────────────────▼────────┐            │
│      │          ECS Tasks                    │            │
│      │  (Running containers from Task Def)  │            │
│      └────────┬──────────────────────────────┘            │
│               │                                           │
│      ┌────────▼────────────┐                             │
│      │   Docker Container  │                             │
│      │   (From ECR image)  │                             │
│      └─────────────────────┘                             │
│                                                           │
│  ┌──────────────────────────────────────────┐            │
│  │  Supporting Services                      │            │
│  │  • ECR (Container Registry)              │            │
│  │  • CloudWatch Logs                       │            │
│  │  • Application Load Balancer             │            │
│  │  • VPC, Subnets, Security Groups         │            │
│  │  • IAM Roles                             │            │
│  └──────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

### Componentes Principales

1. **Cluster**: Agrupación lógica de recursos (EC2 o Fargate)
2. **Task Definition**: Blueprint del container (imagen, CPU, memoria, variables)
3. **Task**: Instancia running de una Task Definition
4. **Service**: Mantiene N tasks corriendo con load balancing
5. **ECR**: Container registry (Docker Hub de AWS)

---

## 2. ECS vs Fargate vs EC2

| Aspecto | Fargate | EC2 Launch Type | Kubernetes (EKS) |
|---------|---------|-----------------|------------------|
| **Management** | Serverless | Manage instances | Manage cluster |
| **Pricing** | Per task (vCPU + GB) | Per EC2 instance | Per EC2 + EKS control plane |
| **Scaling** | Automático | Manual/ASG | HPA + Cluster Autoscaler |
| **Task Size** | Max 16 vCPU, 120 GB | Flexible | Flexible |
| **Startup** | ~30s | ~5s (warm pool) | ~10s |
| **Networking** | awsvpc only | bridge, host, awsvpc | CNI plugin |
| **GPU Support** | ❌ No | ✅ Sí | ✅ Sí |
| **Best For** | Serverless pipelines | GPU workloads, HPC | Complex orchestration |

### Cuándo Usar Cada Uno

**Fargate** ✅:
- ETL pipelines serverless (corridas esporádicas)
- Microservices con carga variable
- CI/CD agents
- No quieres gestionar servers

**ECS EC2** ✅:
- GPU workloads (ML training, Spark GPU)
- Costo predecible 24/7
- Necesitas control fino de instancias
- Daemon tasks (monitoring agents)

**EKS (Kubernetes)** ✅:
- Multi-cloud portability
- Ecosistema K8s (Helm, Operators)
- Complex stateful applications
- Ya tienes experiencia K8s

---

## 3. Task Definitions

Una **Task Definition** es un template JSON/YAML que define cómo correr containers.

### Ejemplo: ETL Pipeline Task

**`etl-task-definition.json`**:

```json
{
  "family": "data-etl-pipeline",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "etl-container",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/data-etl:v1.0",
      "essential": true,
      "cpu": 1024,
      "memory": 2048,
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "BATCH_SIZE",
          "value": "1000"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/data-etl",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "etl"
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "efs-data",
          "containerPath": "/data",
          "readOnly": false
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "efs-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-12345678",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

### IAM Roles

**Execution Role** (usado por ECS agent):
- Pull images de ECR
- Enviar logs a CloudWatch
- Leer secrets de Secrets Manager

**Task Role** (usado por tu application):
- Acceso a S3, RDS, DynamoDB
- Principio de least privilege

`task-execution-role-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/ecs/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:db-password-*"
    }
  ]
}
```

`task-role-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-bucket",
        "arn:aws:s3:::my-data-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:UpdateTable",
        "glue:CreatePartition"
      ],
      "Resource": "*"
    }
  ]
}
```

### Register Task Definition

```bash
# Register via AWS CLI
aws ecs register-task-definition \
  --cli-input-json file://etl-task-definition.json

# List task definition revisions
aws ecs list-task-definitions \
  --family-prefix data-etl-pipeline

# Describe specific revision
aws ecs describe-task-definition \
  --task-definition data-etl-pipeline:5
```

---

## 4. Services y Deployment

### ECS Service

Un **Service** mantiene un número deseado de tasks corriendo y las reemplaza si fallan.

**Terraform Example**:

```hcl
resource "aws_ecs_cluster" "main" {
  name = "data-processing-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_service" "api" {
  name            = "data-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  launch_type     = "FARGATE"
  desired_count   = 3

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  # Auto Scaling
  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Application Auto Scaling
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

### Deployment Strategies

**Rolling Update** (default):
```
Old tasks:  ████████ → ████░░░░ → ░░░░░░░░
New tasks:  ░░░░░░░░ → ░░░░████ → ████████
```

**Blue/Green Deployment** (con CodeDeploy):
```
Blue (old):  ████████ (100% traffic)
                ⬇️
Green (new): ████████ (canary 10%)
                ⬇️
Green (new): ████████ (100% traffic)
Blue (old):  ░░░░░░░░ (terminated)
```

---

## 5. Networking en ECS

### awsvpc Network Mode

Cada task obtiene su propio **ENI** (Elastic Network Interface):

```
┌────────────────────────────────────────┐
│            VPC                          │
│  ┌──────────────────────────────────┐  │
│  │  Subnet (10.0.1.0/24)            │  │
│  │                                   │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐   │  │
│  │  │Task 1│  │Task 2│  │Task 3│   │  │
│  │  │ ENI  │  │ ENI  │  │ ENI  │   │  │
│  │  │.10   │  │.11   │  │.12   │   │  │
│  │  └──────┘  └──────┘  └──────┘   │  │
│  │      ▲         ▲         ▲       │  │
│  └──────┼─────────┼─────────┼───────┘  │
│         └─────────┴─────────┘          │
│         Security Group Rules           │
└────────────────────────────────────────┘
```

**Ventajas**:
- True network isolation
- Security groups por task
- Flow logs granulares
- Required for Fargate

### Service Discovery

AWS Cloud Map permite service-to-service communication por DNS:

```hcl
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "data.local"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "etl" {
  name = "etl-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_ecs_service" "etl" {
  # ...
  service_registries {
    registry_arn = aws_service_discovery_service.etl.arn
  }
}
```

Ahora puedes conectar desde otra task:

```python
import requests

# Service discovery DNS
response = requests.get("http://etl-service.data.local:8080/status")
```

---

## 6. Storage y Logging

### EFS Integration

Para data pipelines que necesitan shared storage:

```hcl
resource "aws_efs_file_system" "data" {
  creation_token = "ecs-data-storage"
  encrypted      = true

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
}

resource "aws_efs_mount_target" "data" {
  count           = length(aws_subnet.private[*].id)
  file_system_id  = aws_efs_file_system.data.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs.id]
}

# Task Definition with EFS
resource "aws_ecs_task_definition" "etl" {
  family = "etl-with-efs"
  # ...

  volume {
    name = "efs-data"

    efs_volume_configuration {
      file_system_id          = aws_efs_file_system.data.id
      transit_encryption      = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.etl.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name  = "etl"
    image = "my-etl:latest"
    mountPoints = [{
      sourceVolume  = "efs-data"
      containerPath = "/data"
      readOnly      = false
    }]
  }])
}
```

### CloudWatch Logs

**Logging Configuration**:

```json
{
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/data-pipeline",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "task",
      "awslogs-datetime-format": "%Y-%m-%d %H:%M:%S"
    }
  }
}
```

**Structured Logging**:

```python
import json
import logging
import sys

# Configure JSON logging
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "task_id": os.environ.get("ECS_TASK_ID", "unknown"),
            "container": os.environ.get("ECS_CONTAINER_METADATA_URI", "unknown")
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("ETL pipeline started", extra={"pipeline": "sales_etl"})
```

**CloudWatch Insights Query**:

```sql
fields @timestamp, message, task_id
| filter level = "ERROR"
| stats count() by task_id
| sort count desc
```

---

## 7. Scheduling y Batch Processing

### EventBridge Scheduled Tasks

Para ETL pipelines que corren diariamente:

```hcl
resource "aws_cloudwatch_event_rule" "daily_etl" {
  name                = "daily-etl-trigger"
  description         = "Run ETL pipeline daily at 2 AM UTC"
  schedule_expression = "cron(0 2 * * ? *)"
}

resource "aws_cloudwatch_event_target" "ecs_task" {
  rule      = aws_cloudwatch_event_rule.daily_etl.name
  target_id = "ecs-etl-task"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.eventbridge_ecs.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.etl.arn
    launch_type         = "FARGATE"

    network_configuration {
      subnets          = aws_subnet.private[*].id
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = false
    }
  }

  input = jsonencode({
    containerOverrides = [{
      name = "etl"
      environment = [{
        name  = "EXECUTION_DATE"
        value = "$$.Execution.StartTime"
      }]
    }]
  })
}
```

### Step Functions + ECS

Para workflows complejos:

```json
{
  "Comment": "ETL Pipeline with ECS",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "data-cluster",
        "TaskDefinition": "extract-task",
        "LaunchType": "FARGATE",
        "NetworkConfiguration": {
          "AwsvpcConfiguration": {
            "Subnets": ["subnet-12345"],
            "SecurityGroups": ["sg-12345"]
          }
        }
      },
      "Next": "Transform"
    },
    "Transform": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "data-cluster",
        "TaskDefinition": "transform-task",
        "LaunchType": "FARGATE",
        "Overrides": {
          "ContainerOverrides": [{
            "Name": "transform",
            "Environment": [{
              "Name": "INPUT_PATH",
              "Value.$": "$.output.data_path"
            }]
          }]
        }
      },
      "Next": "Load"
    },
    "Load": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask.sync",
      "Parameters": {
        "Cluster": "data-cluster",
        "TaskDefinition": "load-task",
        "LaunchType": "FARGATE"
      },
      "End": true
    }
  }
}
```

---

## 8. Monitoring y Troubleshooting

### CloudWatch Container Insights

```hcl
resource "aws_ecs_cluster" "main" {
  name = "data-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
```

**Métricas disponibles**:
- CPU Utilization
- Memory Utilization
- Network bytes in/out
- Task count
- Service restarts

### CloudWatch Dashboard

```hcl
resource "aws_cloudwatch_dashboard" "ecs" {
  dashboard_name = "ecs-data-pipeline"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", {stat = "Average", period = 300}],
            [".", "MemoryUtilization", {"."}]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "ECS Resource Usage"
        }
      },
      {
        type = "log"
        properties = {
          query = "SOURCE '/ecs/data-pipeline' | fields @timestamp, @message | filter level = 'ERROR' | sort @timestamp desc | limit 20"
          region = "us-east-1"
          title = "Recent Errors"
        }
      }
    ]
  })
}
```

### Troubleshooting Common Issues

**Task fails to start**:

```bash
# Check task stopped reason
aws ecs describe-tasks \
  --cluster data-cluster \
  --tasks arn:aws:ecs:us-east-1:123:task/abc123 \
  --query 'tasks[0].stoppedReason'

# Common causes:
# - Cannot pull image (check ECR permissions)
# - Cannot create ENI (check subnet capacity)
# - Task execution role missing permissions
```

**OOM (Out of Memory)**:

```bash
# Check CloudWatch Logs for OOM killer
aws logs filter-log-events \
  --log-group-name /ecs/data-pipeline \
  --filter-pattern "oom-killer"

# Solution: Increase memory in task definition
```

**Slow task startup**:

```bash
# Analyze task lifecycle
aws ecs describe-tasks \
  --cluster data-cluster \
  --tasks task-id \
  --include TAGS \
  | jq '.tasks[0].attachments'

# Check:
# - Image pull time (optimize layers)
# - ENI attachment time (VPC capacity)
# - Health check delays
```

---

## 🎯 Checklist de Production-Ready ECS

### Security
- [ ] Task execution role con least privilege
- [ ] Task role específico por workload
- [ ] Secrets en Secrets Manager (no environment variables)
- [ ] Security groups restrictivos
- [ ] ECS Exec deshabilitado (o auditado)
- [ ] Images escaneadas (ECR scan on push)

### Reliability
- [ ] Health checks configurados
- [ ] Restart policy apropiado
- [ ] Auto scaling configurado
- [ ] Multi-AZ deployment
- [ ] Circuit breakers habilitados

### Performance
- [ ] CPU y memory tuned (no over/under provisioned)
- [ ] Task placement strategies
- [ ] Network mode awsvpc
- [ ] EFS Throughput Mode adecuado

### Observability
- [ ] Container Insights enabled
- [ ] CloudWatch Logs con retention policy
- [ ] Structured logging (JSON)
- [ ] CloudWatch Dashboard
- [ ] Alarmas para métricas clave

### Cost Optimization
- [ ] Fargate Spot para workloads fault-tolerant
- [ ] Right-sizing de tasks
- [ ] Logs retention policy (no infinity)
- [ ] EFS Infrequent Access para archivos viejos

---

## 📚 Referencias

- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [ECS Best Practices Guide](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Fargate Pricing](https://aws.amazon.com/fargate/pricing/)

---

**Próximo**: [03 - Kubernetes & EKS](03-kubernetes-eks.md) para orquestación avanzada.
