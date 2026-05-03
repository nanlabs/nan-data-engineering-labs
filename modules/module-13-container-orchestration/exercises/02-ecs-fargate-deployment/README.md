# Exercise 02: ECS Fargate Deployment

## 📋 Información General

- **Level**: Intermedio
- **Duration estimada**: 3-4 hours
- **Prerequisites**:
  - Exercise 01 completed
  - Cuenta AWS activa
  - AWS CLI configurado
  - Terraform instalado

## 🎯 Objectives de Aprendizaje

1. Crear ECS Cluster con Fargate
2. Definir Task Definitions
3. Crear ECS Services con Load Balancer
4. Implementar Auto Scaling
5. CloudWatch Logging y Monitoring
6. CI/CD con GitHub Actions

---

## 📚 Context

Desplegarás la aplicación ETL del exercise 01 en AWS ECS Fargate como:
- **Scheduled Task**: Corre diariamente a las 2 AM
- **API Service**: REST API para trigger manual

**Arquitectura**:

```
┌──────────────────────────────────────────────────────────┐
│                    AWS ECS Architecture                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Application Load Balancer (ALB)                 │  │
│  │  Port 80 → Target Group                          │  │
│  └────────────────┬──────────────────────────────────┘  │
│                   │                                      │
│           ┌───────┴───────┐                             │
│           │                │                             │
│    ┌──────▼──────┐  ┌─────▼───────┐                    │
│    │  ECS Task 1 │  │  ECS Task 2 │                    │
│    │  (API)      │  │  (API)      │                    │
│    │  Fargate    │  │  Fargate    │                    │
│    └─────────────┘  └─────────────┘                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  EventBridge Rule                                 │  │
│  │  cron(0 2 * * ? *)                               │  │
│  │  ↓                                                │  │
│  │  ECS Run Task (Scheduled ETL)                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RDS PostgreSQL                                   │  │
│  │  Multi-AZ                                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  CloudWatch                                       │  │
│  │  • Logs (/ecs/data-pipeline)                     │  │
│  │  • Metrics (CPU, Memory)                         │  │
│  │  • Alarms                                         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 🏗️ Parte 1: Infrastructure con Terraform

### Step 1.1: VPC y Networking

Create `terraform/vpc.tf`:

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ecs-data-vpc"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "ecs-public-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "ecs-private-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ecs-igw"
  }
}

# NAT Gateway (for private subnets)
resource "aws_eip" "nat" {
  count  = 2
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "ecs-nat-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "ecs-public-rt"
  }
}

resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "ecs-private-rt-${count.index + 1}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Data source for AZs
data "aws_availability_zones" "available" {
  state = "available"
}
```

### Step 1.2: Security Groups

Create `terraform/security_groups.tf`:

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "ecs-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ecs-alb-sg"
  }
}

# ECS Tasks Security Group
resource "aws_security_group" "ecs_tasks" {
  name        = "ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ecs-tasks-sg"
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "ecs-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  tags = {
    Name = "ecs-rds-sg"
  }
}
```

### Step 1.3: RDS PostgreSQL

Create `terraform/rds.tf`:

```hcl
# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "ecs-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "ECS DB Subnet Group"
  }
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier             = "ecs-analytics-db"
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  storage_encrypted      = true

  db_name  = "analytics"
  username = "dataeng"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true

  tags = {
    Name = "ecs-analytics-db"
  }
}

# Random password
resource "random_password" "db_password" {
  length  = 16
  special = false
}

# Store password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name = "ecs-db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "dataeng"
    password = random_password.db_password.result
    host     = aws_db_instance.postgres.address
    port     = 5432
    dbname   = "analytics"
  })
}
```

### Step 1.4: ECS Cluster

Create `terraform/ecs.tf`:

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "data-processing-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = "production"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/data-pipeline"
  retention_in_days = 7
}

# IAM Role for Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "ecs-task-execution-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        aws_secretsmanager_secret.db_password.arn
      ]
    }]
  })
}

# IAM Role for Tasks
resource "aws_iam_role" "ecs_task" {
  name = "ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "ecs-task-s3-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.data.arn,
        "${aws_s3_bucket.data.arn}/*"
      ]
    }]
  })
}

# S3 Bucket for data
resource "aws_s3_bucket" "data" {
  bucket = "ecs-data-pipeline-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}
```

### Step 1.5: Task Definition

Create `terraform/task_definition.tf`:

```hcl
# API Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "data-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "api"
    image = "${aws_ecr_repository.app.repository_url}:latest"

    portMappings = [{
      containerPort = 8080
      protocol      = "tcp"
    }]

    environment = [{
      name  = "ENVIRONMENT"
      value = "production"
    }]

    secrets = [{
      name      = "DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.db_password.arn}:host::"
    }, {
      name      = "DB_PASSWORD"
      valueFrom = "${aws_secretsmanager_secret.db_password.arn}:password::"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = "data-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
```

### Step 1.6: ECS Service con ALB

Create `terraform/service.tf`:

```hcl
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "ecs-data-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "ecs-data-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "api" {
  name        = "ecs-api-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 60
    interval            = 300
    matcher             = "200"
  }

  deregistration_delay = 30
}

# Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "data-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  launch_type     = "FARGATE"
  desired_count   = 2

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

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  depends_on = [aws_lb_listener.http]
}

# Auto Scaling
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

# Output
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}
```

### Step 1.7: Scheduled Task

Create `terraform/scheduled_task.tf`:

```hcl
# EventBridge Rule (daily at 2 AM UTC)
resource "aws_cloudwatch_event_rule" "daily_etl" {
  name                = "daily-etl-trigger"
  description         = "Run ETL pipeline daily at 2 AM UTC"
  schedule_expression = "cron(0 2 * * ? *)"
}

# EventBridge Target
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
}

# IAM Role for EventBridge
resource "aws_iam_role" "eventbridge_ecs" {
  name = "eventbridge-ecs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_ecs" {
  name = "eventbridge-ecs-policy"
  role = aws_iam_role.eventbridge_ecs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:RunTask"
      ]
      Resource = [
        aws_ecs_task_definition.etl.arn
      ]
    }, {
      Effect = "Allow"
      Action = [
        "iam:PassRole"
      ]
      Resource = [
        aws_iam_role.ecs_task_execution.arn,
        aws_iam_role.ecs_task.arn
      ]
    }]
  })
}

# ETL Task Definition
resource "aws_ecs_task_definition" "etl" {
  family                   = "data-etl"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "etl"
    image = "${aws_ecr_repository.app.repository_url}:latest"

    command = ["python", "etl.py"]

    secrets = [{
      name      = "DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.db_password.arn}:host::"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "etl"
      }
    }
  }])
}
```

---

## 🚀 Parte 2: Deploy

### Step 2.1: Initialize Terraform

```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

### Step 2.2: Push Image to ECR

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_repository_url)

# Build and push
docker build -t data-api:latest ../app/
docker tag data-api:latest $(terraform output -raw ecr_repository_url):latest
docker push $(terraform output -raw ecr_repository_url):latest
```

### Step 2.3: Verify Deployment

```bash
# Get ALB DNS
terraform output alb_dns_name

# Test API
curl http://$(terraform output -raw alb_dns_name)/health

# View ECS services
aws ecs list-services --cluster data-processing-cluster

# View tasks
aws ecs list-tasks --cluster data-processing-cluster --service-name data-api

# View logs
aws logs tail /ecs/data-pipeline --follow
```

---

## ✅ Validation

### 1. ECS Service Running

```bash
aws ecs describe-services \
  --cluster data-processing-cluster \
  --services data-api \
  | jq '.services[0].runningCount'
# Should be 2
```

### 2. ALB Health Check

```bash
curl http://$(terraform output -raw alb_dns_name)/health
# Should return 200 OK
```

### 3. Auto Scaling Configured

```bash
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs
```

### 4. Scheduled Task Created

```bash
aws events list-rules --name-prefix daily-etl
```

---

## 🎓 Conclusión

Has aprendido a:
✅ Desplegar containers en ECS Fargate
✅ Configurar networking (VPC, subnets, security groups)
✅ Implementar Load Balancer con health checks
✅ Auto scaling de containers
✅ Scheduled tasks con EventBridge
✅ Secrets management con Secrets Manager

**Próximo**: [Exercise 03 - ECS Data Pipeline](../03-ecs-data-pipeline/) - ETL complejo con múltiples tasks.
