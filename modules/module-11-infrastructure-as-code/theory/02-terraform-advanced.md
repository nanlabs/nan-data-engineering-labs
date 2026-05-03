# Terraform Advanced: Técnicas y Patrones Avanzados

## Tabla de Contenidos
1. [Modules de Terraform](#modules-de-terraform)
2. [Composición de Modules](#composición-de-modules)
3. [Module Registry](#module-registry)
4. [Count y For Each](#count-y-for-each)
5. [Expresiones y Funciones](#expresiones-y-funciones)
6. [Funciones Built-in Útiles](#funciones-built-in-útiles)
7. [Dependencies](#dependencies)
8. [Lifecycle Rules](#lifecycle-rules)
9. [Provisioners](#provisioners)
10. [Remote State](#remote-state)
11. [State Commands](#state-commands)
12. [Workspaces](#workspaces)
13. [Import de Recursos](#import-de-recursos)
14. [Meta-Arguments](#meta-arguments)
15. [Dynamic Blocks](#dynamic-blocks)
16. [Ejemplos Avanzados](#ejemplos-avanzados)

---

## Modules de Terraform

Los **modules** son la forma principal de organizar, reutilizar y compartir código Terraform. Un module es simplemente un directorio que contiene archivos `.tf`.

### ¿Por Qué Usar Modules?

#### Problemas sin Modules

```hcl
# Sin modules: Código repetitivo y difícil de mantener
resource "aws_vpc" "dev_vpc" {
  cidr_block = "10.0.0.0/16"
  # ... 50 líneas de configuration
}

resource "aws_subnet" "dev_subnet_1" {
  vpc_id = aws_vpc.dev_vpc.id
  # ... 20 líneas
}

# Lo mismo para staging
resource "aws_vpc" "staging_vpc" {
  cidr_block = "10.1.0.0/16"
  # ... 50 líneas DUPLICADAS
}

resource "aws_subnet" "staging_subnet_1" {
  vpc_id = aws_vpc.staging_vpc.id
  # ... 20 líneas DUPLICADAS
}

# Y para producción...
# Más duplicación...
```

#### Solution con Modules

```hcl
# Con modules: DRY (Don't Repeat Yourself)
module "dev_vpc" {
  source = "./modules/vpc"

  environment = "dev"
  cidr_block  = "10.0.0.0/16"
}

module "staging_vpc" {
  source = "./modules/vpc"

  environment = "staging"
  cidr_block  = "10.1.0.0/16"
}

module "prod_vpc" {
  source = "./modules/vpc"

  environment = "prod"
  cidr_block  = "10.2.0.0/16"
}
```

### Estructura de un Module

```
modules/
└── vpc/
    ├── main.tf        # Recursos principales
    ├── variables.tf   # Input variables
    ├── outputs.tf     # Outputs
    ├── versions.tf    # Provider requirements
    └── README.md      # Documentación
```

### Crear un Module: VPC Completo

#### modules/vpc/variables.tf

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
  default     = 2
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway for all private subnets"
  type        = bool
  default     = false
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
```

#### modules/vpc/main.tf

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"

  # Calculate subnet CIDR blocks
  private_subnets = [
    for i in range(var.private_subnet_count) :
    cidrsubnet(var.cidr_block, 8, i + 10)
  ]

  public_subnets = [
    for i in range(var.public_subnet_count) :
    cidrsubnet(var.cidr_block, 8, i)
  ]

  # Common tags
  common_tags = merge(
    {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "Terraform"
      Module      = "vpc"
    },
    var.tags
  )
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpc"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-igw"
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = var.public_subnet_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-public-${count.index + 1}"
      Tier = "public"
    }
  )
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = var.private_subnet_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnets[count.index]
  availability_zone = var.availability_zones[count.index % length(var.availability_zones)]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-private-${count.index + 1}"
      Tier = "private"
    }
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.private_subnet_count) : 0
  domain = "vpc"

  depends_on = [aws_internet_gateway.main]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-nat-eip-${count.index + 1}"
    }
  )
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : var.private_subnet_count) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index % var.public_subnet_count].id

  depends_on = [aws_internet_gateway.main]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-nat-${count.index + 1}"
    }
  )
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-public-rt"
    }
  )
}

# Public Route to Internet Gateway
resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Public Route Table Association
resource "aws_route_table_association" "public" {
  count          = var.public_subnet_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count  = var.private_subnet_count
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-private-rt-${count.index + 1}"
    }
  )
}

# Private Routes to NAT Gateway
resource "aws_route" "private_nat_gateway" {
  count                  = var.enable_nat_gateway ? var.private_subnet_count : 0
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

# Private Route Table Association
resource "aws_route_table_association" "private" {
  count          = var.private_subnet_count
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPN Gateway (optional)
resource "aws_vpn_gateway" "main" {
  count  = var.enable_vpn_gateway ? 1 : 0
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpn-gw"
    }
  )
}
```

#### modules/vpc/outputs.tf

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "public_subnet_cidrs" {
  description = "CIDR blocks of public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "CIDR blocks of private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "nat_gateway_ids" {
  description = "IDs of NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "internet_gateway_id" {
  description = "ID of Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "availability_zones" {
  description = "Availability zones used"
  value       = distinct(concat(
    aws_subnet.public[*].availability_zone,
    aws_subnet.private[*].availability_zone
  ))
}
```

#### modules/vpc/versions.tf

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

### Usar el Module

#### environments/dev/main.tf

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source = "../../modules/vpc"

  environment        = "dev"
  project            = "dataplatform"
  cidr_block         = "10.0.0.0/16"
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnet_count = 2
  public_subnet_count  = 2

  enable_nat_gateway = true
  single_nat_gateway = true  # Dev: usar un solo NAT para ahorrar costos

  tags = {
    CostCenter = "Engineering"
    Team       = "DataEngineering"
  }
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}
```

### Best Practices para Modules

#### 1. Estructura Consistente

✅ **DO:**
```
module/
├── main.tf        # Recursos principales
├── variables.tf   # Variables input
├── outputs.tf     # Outputs
├── versions.tf    # Provider requirements
├── locals.tf      # (opcional) Valores locales complejos
└── README.md      # Documentación
```

#### 2. Documentación Clara

```hcl
variable "instance_type" {
  description = <<-EOT
    EC2 instance type for web servers.
    Recommended: t3.medium for production, t3.small for non-prod.
    Must be a t3 instance type.
  EOT
  type        = string

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Instance type must be a t3 instance."
  }
}
```

#### 3. Outputs Útiles

```hcl
# ✅ BIEN: Outputs específicos y útiles
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

# ❌ MAL: Output de todo el objeto
output "vpc" {
  value = aws_vpc.main
}
```

#### 4. Variables con Defaults Razonables

```hcl
# ✅ BIEN: Default razonable
variable "enable_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = false  # Safe default (no extra cost)
}

# ❌ MAL: Sin default para algo que debería tenerlo
variable "enable_encryption" {
  description = "Enable encryption"
  type        = bool
  # Sin default obliga al usuario a especificar
}
```

#### 5. Validation de Variables

```hcl
variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_count" {
  description = "Number of instances"
  type        = number

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}
```

---

## Composición de Modules

La **composición de modules** es la práctica de combinar múltiples modules pequeños para create arquitecturas complejas.

### Ejemplo: Data Platform Architecture

```
root/
├── main.tf
├── modules/
│   ├── networking/      # Module VPC
│   ├── compute/         # Module EC2/ECS
│   ├── database/        # Module RDS/DynamoDB
│   ├── storage/         # Module S3/EFS
│   └── security/        # Module IAM/Security Groups
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

### Module de Networking

```hcl
# modules/networking/main.tf
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.project}-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = var.enable_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = var.tags
}

resource "aws_security_group" "alb" {
  name        = "${var.project}-${var.environment}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-alb-sg" })
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "alb_security_group_id" {
  value = aws_security_group.alb.id
}
```

### Module de Compute

```hcl
# modules/compute/main.tf
resource "aws_security_group" "app" {
  name        = "${var.project}-${var.environment}-app-sg"
  description = "Security group for application servers"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-app-sg" })
}

resource "aws_launch_template" "app" {
  name_prefix   = "${var.project}-${var.environment}-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    app_port = var.app_port
    environment = var.environment
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, { Name = "${var.project}-${var.environment}-app" })
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.project}-${var.environment}-asg"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [aws_lb_target_group.app.arn]

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  health_check_type         = "ELB"
  health_check_grace_period = 300

  tag {
    key                 = "Name"
    value               = "${var.project}-${var.environment}-asg"
    propagate_at_launch = true
  }

  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

resource "aws_lb" "app" {
  name               = "${var.project}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-alb" })
}

resource "aws_lb_target_group" "app" {
  name     = "${var.project}-${var.environment}-tg"
  port     = var.app_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-tg" })
}

resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

### Module de Database

```hcl
# modules/database/main.tf
resource "aws_security_group" "rds" {
  name        = "${var.project}-${var.environment}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-rds-sg" })
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-db-subnet" })
}

resource "aws_db_instance" "main" {
  identifier = "${var.project}-${var.environment}-db"

  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn

  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = merge(var.tags, { Name = "${var.project}-${var.environment}-db" })
}

resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

output "endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}
```

### Composición en Root Module

```hcl
# environments/prod/main.tf
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/data-platform/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.region
}

locals {
  common_tags = {
    Environment = "production"
    Project     = "DataPlatform"
    ManagedBy   = "Terraform"
    CostCenter  = "Engineering"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Networking
module "networking" {
  source = "../../modules/networking"

  project            = "dataplatform"
  environment        = "prod"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)

  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

  enable_nat_gateway = true

  tags = local.common_tags
}

# Compute
module "compute" {
  source = "../../modules/compute"

  project     = "dataplatform"
  environment = "prod"

  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  public_subnet_ids      = module.networking.public_subnet_ids
  alb_security_group_id  = module.networking.alb_security_group_id

  ami_id        = data.aws_ami.amazon_linux.id
  instance_type = "t3.large"

  min_size         = 3
  max_size         = 10
  desired_capacity = 5

  app_port = 8080

  tags = local.common_tags
}

# Database
module "database" {
  source = "../../modules/database"

  project     = "dataplatform"
  environment = "prod"

  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  app_security_group_id = module.compute.app_security_group_id

  engine_version    = "14.7"
  instance_class    = "db.r6g.xlarge"
  allocated_storage = 500

  database_name   = "dataplatform"
  master_username = var.db_username
  master_password = var.db_password

  backup_retention_period = 30
  deletion_protection     = true
  skip_final_snapshot     = false

  tags = local.common_tags
}

# Storage
module "storage" {
  source = "../../modules/storage"

  project     = "dataplatform"
  environment = "prod"

  buckets = {
    raw = {
      versioning = true
      lifecycle_rules = [
        {
          id      = "archive-old-data"
          enabled = true
          transition = {
            days          = 90
            storage_class = "GLACIER"
          }
        }
      ]
    }
    processed = {
      versioning = true
      lifecycle_rules = []
    }
    archive = {
      versioning      = true
      lifecycle_rules = []
    }
  }

  tags = local.common_tags
}

# Outputs
output "alb_dns_name" {
  value = module.compute.alb_dns_name
}

output "database_endpoint" {
  value     = module.database.endpoint
  sensitive = true
}

output "storage_bucket_names" {
  value = module.storage.bucket_names
}
```

---

## Module Registry

El **Terraform Registry** es un repositorio público de modules de Terraform verificados y mantenidos por la comunidad.

### Usar Modules del Registry

```hcl
# Module oficial de AWS VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}
```

### Modules Populares de AWS

```hcl
# EC2 Instance
module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"

  name = "my-instance"

  instance_type = "t3.micro"
  ami           = data.aws_ami.amazon_linux.id

  subnet_id              = module.vpc.private_subnets[0]
  vpc_security_group_ids = [module.security_group.security_group_id]
}

# S3 Bucket
module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.15.1"

  bucket = "my-bucket"
  acl    = "private"

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }
}

# RDS
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.3.0"

  identifier = "mydb"

  engine            = "postgres"
  engine_version    = "14"
  instance_class    = "db.t3.medium"
  allocated_storage = 20

  db_name  = "mydb"
  username = "dbadmin"
  password = var.db_password

  vpc_security_group_ids = [module.security_group_db.security_group_id]

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"

  tags = {
    Environment = "dev"
  }
}

# Security Group
module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "web-server-sg"
  description = "Security group for web servers"
  vpc_id      = module.vpc.vpc_id

  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["http-80-tcp", "https-443-tcp"]
  egress_rules        = ["all-all"]
}

# ALB
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "9.2.0"

  name = "my-alb"

  load_balancer_type = "application"

  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [module.security_group_alb.security_group_id]

  target_groups = [
    {
      name_prefix      = "web-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "instance"
    }
  ]

  http_tcp_listeners = [
    {
      port               = 80
      protocol           = "HTTP"
      target_group_index = 0
    }
  ]
}
```

### Versiones de Modules

```hcl
# ✅ BIEN: Versión específica
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"
}

# ✅ BIEN: Constraint de versión
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.1"  # Cualquier 5.1.x
}

# ❌ MAL: Sin versión (usa la última)
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  # Sin version - puede romper con cambios
}
```

### Fuentes de Modules

```hcl
# Registry público
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"
}

# GitHub (HTTPS)
module "vpc" {
  source = "github.com/terraform-aws-modules/terraform-aws-vpc"
}

# GitHub (SSH)
module "vpc" {
  source = "git@github.com:terraform-aws-modules/terraform-aws-vpc.git"
}

# GitHub con branch/tag/commit
module "vpc" {
  source = "github.com/terraform-aws-modules/terraform-aws-vpc?ref=v5.1.2"
}

# Path local
module "vpc" {
  source = "./modules/vpc"
}

# Path relativo
module "vpc" {
  source = "../../shared-modules/vpc"
}

# S3
module "vpc" {
  source = "s3::https://s3-us-west-2.amazonaws.com/my-modules/vpc.zip"
}
```

---

## Count y For Each

`count` y `for_each` son **meta-arguments** que permiten create múltiples instancias de un resource o module.

### Count

`count` crea N copias idénticas de un resource, identificadas por índice numérico.

```hcl
# Crear 3 S3 buckets
resource "aws_s3_bucket" "example" {
  count  = 3
  bucket = "my-bucket-${count.index}"

  tags = {
    Name  = "Bucket ${count.index}"
    Index = count.index
  }
}

# Referencia a todos
output "all_bucket_ids" {
  value = aws_s3_bucket.example[*].id
}

# Referencia a uno específico
output "first_bucket_id" {
  value = aws_s3_bucket.example[0].id
}
```

#### Count con Condicional

```hcl
# Crear recurso solo si condición es verdadera
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"
}

# Referencia (debe manejar caso vacío)
output "nat_eip" {
  value = length(aws_eip.nat) > 0 ? aws_eip.nat[0].public_ip : null
}
```

#### Count con Variable

```hcl
variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 2
}

resource "aws_instance" "web" {
  count = var.instance_count

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[count.index % length(aws_subnet.public)].id

  tags = {
    Name = "web-${count.index + 1}"
  }
}
```

### For Each

`for_each` crea múltiples recursos basados en un map o set, identificados por key string.

```hcl
# Crear buckets desde un set
variable "bucket_names" {
  type    = set(string)
  default = ["logs", "data", "backups"]
}

resource "aws_s3_bucket" "example" {
  for_each = var.bucket_names

  bucket = "mycompany-${each.value}"

  tags = {
    Name = each.value
  }
}

# Referencia
output "bucket_arns" {
  value = {
    for k, bucket in aws_s3_bucket.example :
    k => bucket.arn
  }
}
```

#### For Each con Map

```hcl
variable "instances" {
  type = map(object({
    instance_type = string
    ami           = string
  }))

  default = {
    web = {
      instance_type = "t3.small"
      ami           = "ami-12345"
    }
    app = {
      instance_type = "t3.medium"
      ami           = "ami-67890"
    }
    worker = {
      instance_type = "t3.large"
      ami           = "ami-abcde"
    }
  }
}

resource "aws_instance" "servers" {
  for_each = var.instances

  ami           = each.value.ami
  instance_type = each.value.instance_type

  tags = {
    Name = each.key
    Role = each.key
  }
}

# Referencia
output "instance_ips" {
  value = {
    for name, instance in aws_instance.servers :
    name => instance.private_ip
  }
}
```

#### For Each con Data Source

```hcl
# Crear subnet en cada AZ
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = toset(slice(data.aws_availability_zones.available.names, 0, 3))
}

resource "aws_subnet" "private" {
  for_each = local.azs

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, index(tolist(local.azs), each.value) + 10)
  availability_zone = each.value

  tags = {
    Name = "private-${each.value}"
    AZ   = each.value
  }
}
```

### Count vs For Each: ¿Cuándo Usar?

| Situación | Usar | Razón |
|-----------|------|-------|
| Cantidad dinámica de recursos idénticos | `count` | Más simple |
| Recursos basados en lista con lógica | `for_each` | Más flexible |
| Condicional (create o no) | `count` (0 o 1) | Idiomatic |
| Resources identificados por nombre | `for_each` | Key significativa |
| Puede cambiar orden de elementos | `for_each` | No afecta existing resources |

#### Ejemplo: Problema con Count

```hcl
# ❌ PROBLEMA con count
variable "users" {
  default = ["alice", "bob", "charlie"]
}

resource "aws_iam_user" "user" {
  count = length(var.users)
  name  = var.users[count.index]
}

# Si eliminas "bob" (índice 1):
# users = ["alice", "charlie"]
# Terraform planea:
# - Eliminar user[2] (charlie)
# - Actualizar user[1] de bob a charlie
# ¡No es lo que querías!
```

```hcl
# ✅ SOLUCIÓN con for_each
variable "users" {
  default = ["alice", "bob", "charlie"]
}

resource "aws_iam_user" "user" {
  for_each = toset(var.users)
  name     = each.value
}

# Si eliminas "bob":
# Terraform solo elimina user["bob"]
# ✅ Correcto!
```

---

## Expresiones y Funciones

### Expresiones Condicionales (Ternary)

```hcl
# Sintaxis: condition ? true_value : false_value

# Condicional simple
resource "aws_instance" "web" {
  instance_type = var.environment == "prod" ? "t3.large" : "t3.small"
}

# Nested conditionals
locals {
  instance_type = (
    var.environment == "prod" ? "t3.large" :
    var.environment == "staging" ? "t3.medium" :
    "t3.small"
  )
}

# Condicional en count
resource "aws_eip" "nat" {
  count  = var.environment == "prod" ? 3 : 1
  domain = "vpc"
}
```

### For Expressions

#### List Comprehension

```hcl
# Transformar lista
variable "subnets" {
  default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

locals {
  # Extraer primer octeto
  first_octets = [for s in var.subnets : split(".", s)[0]]
  # Resultado: ["10", "10", "10"]

  # Crear subnet names
  subnet_names = [for i, s in var.subnets : "subnet-${i}"]
  # Resultado: ["subnet-0", "subnet-1", "subnet-2"]
}

# Con filtro
locals {
  # Solo subnets que empiezan con "10.0.1"
  filtered = [for s in var.subnets : s if can(regex("^10\\.0\\.1", s))]
  # Resultado: ["10.0.1.0/24"]
}

# Nested
variable "environments" {
  default = ["dev", "staging", "prod"]
}

variable "regions" {
  default = ["us-east-1", "us-west-2"]
}

locals {
  # Crear todas las combinaciones
  all_combinations = flatten([
    for env in var.environments : [
      for region in var.regions : "${env}-${region}"
    ]
  ])
  # Resultado: ["dev-us-east-1", "dev-us-west-2", "staging-us-east-1", ...]
}
```

#### Map Comprehension

```hcl
# Transformar map
variable "instances" {
  default = {
    web    = "t3.small"
    app    = "t3.medium"
    worker = "t3.large"
  }
}

locals {
  # Uppercase keys
  uppercase_instances = {
    for k, v in var.instances : upper(k) => v
  }
  # Resultado: { WEB = "t3.small", APP = "t3.medium", ... }

  # Filtrar por valor
  large_instances = {
    for k, v in var.instances : k => v if v == "t3.large"
  }
  # Resultado: { worker = "t3.large" }

  # Transformar valores
  instance_families = {
    for k, v in var.instances : k => split(".", v)[0]
  }
  # Resultado: { web = "t3", app = "t3", worker = "t3" }
}
```

#### Object Comprehension

```hcl
variable "servers" {
  type = list(object({
    name = string
    size = string
    env  = string
  }))

  default = [
    { name = "web-1", size = "small", env = "prod" },
    { name = "web-2", size = "small", env = "prod" },
    { name = "app-1", size = "large", env = "dev" }
  ]
}

locals {
  # Crear map indexado por name
  servers_by_name = {
    for server in var.servers : server.name => server
  }

  # Solo servers de prod
  prod_servers = [
    for server in var.servers : server if server.env == "prod"
  ]

  # Group por environment
  servers_by_env = {
    for server in var.servers :
    server.env => server...  # ... agrupa múltiples valores
  }
  # Resultado: { prod = [{web-1}, {web-2}], dev = [{app-1}] }
}
```

### Splat Expressions

```hcl
# Sintaxis: resource_type.resource_name[*].attribute

resource "aws_instance" "web" {
  count = 3

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}

# Splat para obtener todos los IDs
output "all_instance_ids" {
  value = aws_instance.web[*].id
}

# Splat para obtener todos los IPs
output "all_private_ips" {
  value = aws_instance.web[*].private_ip
}

# Con for_each
resource "aws_s3_bucket" "data" {
  for_each = toset(["logs", "archives", "backups"])
  bucket   = each.value
}

# No se puede usar splat con for_each, usar for:
output "bucket_arns" {
  value = [for bucket in aws_s3_bucket.data : bucket.arn]
}
```

---

## Funciones Built-in Útiles

### String Functions

```hcl
# upper / lower
upper("hello")  # "HELLO"
lower("WORLD")  # "world"

# title / trim
title("hello world")     # "Hello World"
trim("  hello  ", " ")   # "hello"
trimprefix("hello-world", "hello-")  # "world"
trimsuffix("hello.txt", ".txt")      # "hello"

# join / split
join("-", ["a", "b", "c"])  # "a-b-c"
split("-", "a-b-c")         # ["a", "b", "c"]

# format / formatlist
format("Hello, %s!", "World")  # "Hello, World!"
formatlist("instance-%s", ["1", "2", "3"])  # ["instance-1", "instance-2", "instance-3"]

# substr
substr("hello world", 0, 5)  # "hello"
substr("hello world", 6, 5)  # "world"

# replace / regex
replace("hello world", "world", "terraform")  # "hello terraform"
regex("[0-9]+", "abc123def")                  # "123"
regexall("[0-9]+", "a1b2c3")                  # ["1", "2", "3"]

# Ejemplo práctico
locals {
  environment = "Production"
  region      = "us-east-1"

  # Crear resource name normalizado
  resource_prefix = lower(replace("${var.environment}-${var.region}", "_", "-"))
  # Resultado: "production-us-east-1"
}
```

### Collection Functions

```hcl
# length
length([1, 2, 3])              # 3
length({a = 1, b = 2})         # 2
length("hello")                # 5

# concat
concat([1, 2], [3, 4])         # [1, 2, 3, 4]

# merge
merge({a = 1}, {b = 2}, {c = 3})  # {a = 1, b = 2, c = 3}

# flatten
flatten([[1, 2], [3, 4]])      # [1, 2, 3, 4]

# distinct / compact
distinct([1, 2, 2, 3, 3])      # [1, 2, 3]
compact(["a", "", "b", "", "c"])  # ["a", "b", "c"]

# contains / index
contains(["a", "b", "c"], "b")  # true
index(["a", "b", "c"], "b")     # 1

# keys / values
keys({a = 1, b = 2, c = 3})     # ["a", "b", "c"]
values({a = 1, b = 2, c = 3})   # [1, 2, 3]

# lookup
lookup({a = 1, b = 2}, "a", "default")     # 1
lookup({a = 1, b = 2}, "z", "default")     # "default"

# element / slice
element(["a", "b", "c"], 1)                # "b"
slice(["a", "b", "c", "d"], 1, 3)         # ["b", "c"]

# sort / reverse
sort(["c", "a", "b"])                      # ["a", "b", "c"]
reverse([1, 2, 3])                         # [3, 2, 1]

# Ejemplo práctico
variable "tags" {
  type = map(string)
  default = {
    Environment = "production"
    Project     = ""
    Team        = "data"
  }
}

locals {
  # Merge tags default + custom, remove empty
  all_tags = merge(
    {
      ManagedBy = "Terraform"
      CreatedAt = timestamp()
    },
    { for k, v in var.tags : k => v if v != "" }
  )
}
```

### Numeric Functions

```hcl
# min / max
min(1, 2, 3)           # 1
max(1, 2, 3)           # 3

# ceil / floor
ceil(1.3)              # 2
floor(1.7)             # 1

# abs
abs(-5)                # 5

# pow
pow(2, 3)              # 8

# log
log(100, 10)           # 2

# Ejemplo práctico: Calcular tamaño basado en tier
variable "tier" {
  default = "medium"
}

locals {
  tier_multiplier = {
    small  = 1
    medium = 2
    large  = 4
  }

  instance_count = lookup(local.tier_multiplier, var.tier, 1) * 2
  storage_size   = lookup(local.tier_multiplier, var.tier, 1) * 50
}
```

### Filesystem Functions

```hcl
# file - Leer archivo como string
file("${path.module}/config.txt")

# templatefile - Render template con variables
templatefile("${path.module}/template.tpl", {
  name    = "myapp"
  version = "1.0"
})

# fileexists
fileexists("${path.module}/config.txt")  # true/false

# fileset - Encontrar archivos que coinciden con pattern
fileset(path.module, "configs/*.json")   # ["configs/app.json", "configs/db.json"]

# dirname / basename
dirname("/path/to/file.txt")   # "/path/to"
basename("/path/to/file.txt")  # "file.txt"

# pathexpand
pathexpand("~/.ssh/id_rsa")    # "/home/user/.ssh/id_rsa"

# Ejemplo práctico: User data desde template
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  user_data = templatefile("${path.module}/user-data.sh", {
    environment = var.environment
    app_port    = var.app_port
    db_host     = module.database.endpoint
  })
}

# user-data.sh template:
# #!/bin/bash
# echo "Environment: ${environment}"
# echo "App Port: ${app_port}"
# echo "DB Host: ${db_host}"
```

### Date/Time Functions

```hcl
# timestamp - Current timestamp
timestamp()  # "2024-03-07T12:34:56Z"

# formatdate
formatdate("YYYY-MM-DD", timestamp())           # "2024-03-07"
formatdate("hh:mm:ss", timestamp())             # "12:34:56"
formatdate("DD MMM YYYY hh:mm:ss", timestamp()) # "07 Mar 2024 12:34:56"

# timeadd
timeadd(timestamp(), "1h")    # Add 1 hour
timeadd(timestamp(), "24h")   # Add 24 hours
timeadd(timestamp(), "-30m")  # Subtract 30 minutes

# Ejemplo práctico: Snapshot con timestamp
resource "aws_db_snapshot" "backup" {
  db_instance_identifier = aws_db_instance.main.id
  db_snapshot_identifier = "backup-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}
```

### Encoding Functions

```hcl
# base64encode / base64decode
base64encode("hello world")  # "aGVsbG8gd29ybGQ="
base64decode("aGVsbG8gd29ybGQ=")  # "hello world"

# jsonencode / jsondecode
jsonencode({name = "value", count = 123})
# {"count":123,"name":"value"}

jsondecode('{"name":"value","count":123}')
# {name = "value", count = 123}

# yamlencode / yamldecode
yamlencode({name = "value", count = 123})
# count: 123
# name: value

# urlencode
urlencode("hello world!")  # "hello+world%21"

# Ejemplo práctico: Policy document
data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions = ["s3:GetObject"]
    resources = ["arn:aws:s3:::my-bucket/*"]
  }
}

resource "aws_iam_policy" "s3_read" {
  name   = "s3-read"
  policy = data.aws_iam_policy_document.s3_policy.json
}
```

### IP Network Functions

```hcl
# cidrhost - get IP address
cidrhost("10.0.0.0/24", 5)     # "10.0.0.5"

# cidrnetmask - get netmask
cidrnetmask("10.0.0.0/24")     # "255.255.255.0"

# cidrsubnet - create subnet
cidrsubnet("10.0.0.0/16", 8, 1)   # "10.0.1.0/24"
cidrsubnet("10.0.0.0/16", 8, 2)   # "10.0.2.0/24"

# cidrsubnets - múltiples subnets
cidrsubnets("10.0.0.0/16", 8, 8, 8)
# ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24"]

# Ejemplo práctico: Auto-calcular subnets
variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "az_count" {
  default = 3
}

locals {
  # Crear subnets públicas: 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24
  public_subnets = [
    for i in range(var.az_count) :
    cidrsubnet(var.vpc_cidr, 8, i)
  ]

  # Crear subnets privadas: 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24
  private_subnets = [
    for i in range(var.az_count) :
    cidrsubnet(var.vpc_cidr, 8, i + 10)
  ]
}
```

### Type Conversion Functions

```hcl
# tostring / tonumber / tobool
tostring(123)       # "123"
tonumber("123")     # 123
tobool("true")      # true

# tolist / toset / tomap
tolist(["a", "b"])   # Convert to list type
toset(["a", "b", "a"])  # ["a", "b"] (unique)
tomap({a = 1})       # Convert to map type

# type checking
can(tonumber("123"))     # true
can(tonumber("abc"))     # false

# try - Intentar expresión con fallback
try(var.optional_value, "default")
try(jsondecode(file("config.json")), {})

# Ejemplo práctico: Validation robusta
variable "port" {
  type = string
}

locals {
  # Convertir a número si es posible, sino usar default
  port_number = try(tonumber(var.port), 8080)

  # Validar que puerto está en rango válido
  valid_port = local.port_number >= 1 && local.port_number <= 65535
}
```

---

## Dependencies

Terraform automáticamente determina dependencies entre recursos, pero a veces necesitas definirlas explícitamente.

### Dependencies Implícitas

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Subnet depende de VPC (implícito por vpc_id)
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id  # ← Dependency implícita
  cidr_block = "10.0.1.0/24"
}

# Security Group depende de VPC
resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id  # ← Dependency implícita
  # ...
}

# Instance depende de Subnet y Security Group
resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public.id  # ← Dependency implícita
  vpc_security_group_ids = [aws_security_group.web.id]  # ← Dependency implícita
  # ...
}
```

**Orden de creación automático:**
```
1. aws_vpc.main
2. aws_subnet.public, aws_security_group.web (parallelo)
3. aws_instance.web
```

### Dependencies Explícitas con depends_on

Usa `depends_on` cuando:
- La dependency no es obvia de las referencias
- Necesitas ordenar recursos sin referencias directas
- Resources en diferentes providers

```hcl
# Ejemplo: S3 bucket policy necesita que bucket esté completo
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Explícita: asegurar que bucket esté completo
  depends_on = [aws_s3_bucket.data]
}

resource "aws_s3_bucket_policy" "data" {
  bucket = aws_s3_bucket.data.id
  policy = data.aws_iam_policy_document.data_bucket.json

  # Debe esperar a que public access block esté configurado
  depends_on = [aws_s3_bucket_public_access_block.data]
}
```

```hcl
# Ejemplo: IAM role debe existir antes de usarlo
resource "aws_iam_role" "lambda" {
  name = "lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "processor" {
  function_name = "data-processor"
  role          = aws_iam_role.lambda.arn
  # ...

  # Asegurar que policies estén attached antes de create función
  depends_on = [aws_iam_role_policy_attachment.lambda_basic]
}
```

```hcl
# Ejemplo: Multiple dependencies
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  # Múltiples dependencies explícitas
  depends_on = [
    aws_security_group.app,
    aws_iam_role.app,
    aws_s3_bucket.config
  ]
}
```

### Dependency Graph

Ver grafo de dependencies:

```bash
# Generar y visualizar grafo
terraform graph | dot -Tpng > graph.png

# O formato SVG
terraform graph | dot -Tsvg > graph.svg
```

---

## Lifecycle Rules

`lifecycle` es un meta-argument que controla el comportamiento del lifecycle de un resource.

### create_before_destroy

Create el nuevo resource antes de destruir el viejo.

```hcl
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
  }
}

# Útil cuando:
# - Resource es usado por otro que no puede tener downtime
# - Necesitas zero-downtime deployment
```

**Ejemplo con ASG:**

```hcl
resource "aws_launch_template" "app" {
  name_prefix   = "app-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  name = "app-asg"

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  min_size = 2
  max_size = 10

  # ASG debe recrearse cuando launch template cambia
  lifecycle {
    create_before_destroy = true
  }
}
```

### prevent_destroy

Previene destrucción accidental del resource.

```hcl
resource "aws_db_instance" "production" {
  identifier = "prod-database"
  engine     = "postgres"
  # ... otras configuraciones

  lifecycle {
    prevent_destroy = true  # ¡No destruir este recurso!
  }
}

# Si intentas destroy:
# Error: Instance cannot be destroyed
```

**Casos deuso:**
- Databases de producción
- S3 buckets con datos críticos
- State files
- Cualquier recurso crítico

```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "mycompany-terraform-state"

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}
```

### ignore_changes

Ignora cambios a atributos específicos (útil cuando son modificados externamente).

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name = "web-server"
  }

  lifecycle {
    # Ignorar cambios a tags (pueden ser modificados por otros sistemas)
    ignore_changes = [tags]
  }
}
```

**Ignorar múltiples atributos:**

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    ignore_changes = [
      tags,
      user_data,
      ami  # Ignorar cambios de AMI (por ejemplo, patches automáticos)
    ]
  }
}
```

**Ignorar todos los cambios:**

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    ignore_changes = all  # Ignorar TODOS los cambios
  }
}
```

**Caso de uso común: ASG managed instances:**

```hcl
resource "aws_autoscaling_group" "app" {
  name             = "app-asg"
  min_size         = 2
  max_size         = 10
  desired_capacity = 5

  lifecycle {
    # ASG puede scale automáticamente, no forzar desired_capacity
    ignore_changes = [desired_capacity]
  }
}
```

### replace_triggered_by

(Terraform 1.2+) Reemplaza resource cuando otro cambia.

```hcl
resource "aws_ami_copy" "app" {
  name              = "app-ami-${formatdate("YYYYMMDD", timestamp())}"
  source_ami_id     = var.source_ami_id
  source_ami_region = "us-east-1"
}

resource "aws_instance" "app" {
  ami           = aws_ami_copy.app.id
  instance_type = "t3.micro"

  lifecycle {
    # Reemplazar instance cuando AMI cambia
    replace_triggered_by = [
      aws_ami_copy.app.id
    ]
  }
}
```

### Combinando Lifecycle Rules

```hcl
resource "aws_db_instance" "main" {
  identifier = "mydb"
  engine     = "postgres"

  instance_class = var.instance_class
  allocated_storage = var.storage_size

  tags = var.tags

  lifecycle {
    # No destruir accidentalmente
    prevent_destroy = true

    # Crear nueva DB antes de destruir vieja (para migration)
    create_before_destroy = false

    # Ignorar cambios externos a tags
    ignore_changes = [tags]
  }
}
```

---

## Provisioners

⚠️ **WARNING**: Provisioners son un "last resort". HashiCorp recomienda evitarlos cuando sea posible.

### ¿Por Qué Evitar Provisioners?

- Rompen el modelo declarativo de Terraform
- No son idempotentes
- Difíciles de debuggear
- No soportan drift detection
- Pueden dejar recursos en estado inconsistente

### Alternativas Mejores

| En lugar de | Usa |
|-------------|-----|
| `remote-exec` para configure servidor | User data, Cloud-init, o Packer |
| `local-exec` para scripts | Herramientas separadas de orchestration |
| Provisioners para config management | Ansible, Chef, Puppet |

### Cuándo Usar Provisioners (Casos Válidos)

1. **Integraciones con sistemas externos** (APIs que no tienen provider)
2. **Bootstrapping inicial** (una sola vez)
3. **Cleanup de recursos externos** (con `when = destroy`)

### Tipos de Provisioners

#### local-exec

Execute comando en la máquina donde se ejecuta Terraform.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> private_ips.txt"
  }
}
```

**Ejemplo: Invocar script local:**

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  provisioner "local-exec" {
    command = "./scripts/configure-monitoring.sh ${self.id} ${self.private_ip}"

    environment = {
      INSTANCE_ID = self.id
      ENVIRONMENT = var.environment
    }
  }
}
```

**Ejemplo: Cleanup al destruir:**

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  provisioner "local-exec" {
    when    = destroy
    command = "./scripts/deregister-from-monitoring.sh ${self.id}"
  }
}
```

#### remote-exec

Execute comando en el resource remoto.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  key_name      = var.key_name

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file("~/.ssh/id_rsa")
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum update -y",
      "sudo yum install -y httpd",
      "sudo systemctl start httpd",
      "sudo systemctl enable httpd"
    ]
  }

  # ⚠️ MEJOR: Usar user_data para esto
}
```

**Mejor alternativa - User Data:**

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              EOF
}
```

#### file

Copia archivo al resource remoto.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  key_name      = var.key_name

  connection {
    type        = "ssh"
    user        = "ec2-user"
    private_key = file("~/.ssh/id_rsa")
    host        = self.public_ip
  }

  provisioner "file" {
    source      = "configs/app.conf"
    destination = "/tmp/app.conf"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo mv /tmp/app.conf /etc/app.conf",
      "sudo systemctl restart app"
    ]
  }
}
```

### Provisioner Failure Behavior

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  provisioner "remote-exec" {
    inline = ["sudo ./install.sh"]

    # Comportamiento al fallar
    on_failure = continue  # continue = continuar, fail = abortar (default)
  }
}
```

### null_resource con Provisioners

`null_resource` permite usar provisioners sin un resource real.

```hcl
resource "null_resource" "configure_monitoring" {
  # Trigger: re-execute cuando instances cambien
  triggers = {
    instance_ids = join(",", aws_instance.web[*].id)
  }

  provisioner "local-exec" {
    command = "./scripts/configure-monitoring.sh"

    environment = {
      INSTANCE_IDS = join(",", aws_instance.web[*].id)
      ENVIRONMENT  = var.environment
    }
  }
}
```

### Best Practices

```hcl
# ✅ BIEN: Usar user_data para configuration de instancia
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  user_data = templatefile("${path.module}/user-data.sh", {
    environment = var.environment
  })
}

# ❌ MAL: Usar provisioner para lo mismo
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  provisioner "remote-exec" {
    inline = [
      "echo 'environment=${var.environment}' > /etc/environment"
    ]
  }
}
```

---

## Remote State

El **remote state** almacena el state file en una ubicación remota compartida en lugar de localmente.

### Configurar S3 Backend

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/data-platform/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"

    # Optional: KMS encryption
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
  }
}
```

### Setup Inicial

#### 1. Crear S3 Bucket

```hcl
# bootstrap/main.tf
resource "aws_s3_bucket" "terraform_state" {
  bucket = "mycompany-terraform-state"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name      = "Terraform State"
    ManagedBy = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

#### 2. Crear DynamoDB Table para Locking

```hcl
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "terraform-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "Terraform State Lock"
    ManagedBy = "Terraform"
  }
}
```

### Migrar de Local a Remote State

```bash
# 1. Código actual con local state
terraform init
terraform apply

# 2. Agregar backend configuration
# backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

# 3. Re-inicializar (migra state automáticamente)
terraform init -migrate-state

# Terraform preguntará:
# Do you want to copy existing state to the new backend?
# Responde: yes

# 4. Verificar
terraform state list

# 5. (Opcional) Eliminar local state
rm terraform.tfstate*
```

### State Locking

DynamoDB table previene que múltiples usuarios ejecuten Terraform simultáneamente.

```bash
# Usuario 1 ejecuta:
terraform apply
# State locked

# Usuario 2 intenta execute:
terraform apply
# Error: Error acquiring the state lock
# Lock Info:
#   ID:        abc123...
#   Path:      mycompany-terraform-state/prod/terraform.tfstate
#   Operation: OperationTypeApply
#   Who:       user1@machine1
#   Created:   2024-03-07 12:34:56
 ```

**Force unlock (⚠️ usar con cuidado):**

```bash
terraform force-unlock <LOCK_ID>
```

### Backend per Environment

```
environments/
├── dev/
│   ├── backend.tf
│   └── main.tf
├── staging/
│   ├── backend.tf
│   └── main.tf
└── prod/
    ├── backend.tf
    └── main.tf
```

**environments/dev/backend.tf:**
```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**environments/prod/backend.tf:**
```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Partial Backend Configuration

Evita hardcodear valores en código:

```hcl
# backend.tf (sin valores hardcodeados)
terraform {
  backend "s3" {}
}
```

```hcl
# backend-dev.hcl
bucket         = "mycompany-terraform-state"
key            = "dev/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-state-lock"
```

```bash
# Inicializar con config file
terraform init -backend-config=backend-dev.hcl
```

O con CLI flags:

```bash
terraform init \
  -backend-config="bucket=mycompany-terraform-state" \
  -backend-config="key=dev/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

### Remote State Data Source

Leer outputs de otro state:

```hcl
# Project A: Networking
# outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}
```

```hcl
# Project B: Compute
# Leer outputs de Project A
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "mycompany-terraform-state"
    key    = "prod/networking/terraform.tfstate"
    region = "us-east-1"
  }
}

# Usar outputs
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = "t3.micro"
  subnet_id     = data.terraform_remote_state.networking.outputs.private_subnet_ids[0]

  # ...
}
```

---

## State Commands

Comandos avanzados para gestionar state.

### terraform state list

Lista todos los recursos en state:

```bash
$ terraform state list
aws_vpc.main
aws_subnet.public[0]
aws_subnet.public[1]
aws_subnet.private[0]
aws_subnet.private[1]
aws_instance.web[0]
aws_instance.web[1]
module.database.aws_db_instance.main
module.database.aws_security_group.rds
```

### terraform state show

Muestra detalles de un resource:

```bash
$ terraform state show aws_instance.web[0]
# aws_instance.web[0]:
resource "aws_instance" "web" {
    ami                          = "ami-0c55b159cbfafe1f0"
    id                           = "i-1234567890abcdef0"
    instance_type                = "t3.micro"
    private_ip                   = "10.0.1.10"
    public_ip                    = "54.123.45.67"
    subnet_id                    = "subnet-abc123"
    vpc_security_group_ids       = ["sg-xyz789"]
    ...
}
```

### terraform state mv

Mueve/renombra resource en state:

```bash
# Renombrar resource
terraform state mv aws_instance.web aws_instance.app

# Mover a module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Mover entre indexed resources
terraform state mv 'aws_instance.web[0]' 'aws_instance.web[1]'

# Mover a otro state file
terraform state mv -state-out=../other/terraform.tfstate aws_instance.web aws_instance.web
```

**Caso de uso: Refactoring:**

```hcl
# Antes
resource "aws_instance" "server" {
  count = 3
  # ...
}

# Después (usando for_each)
variable "servers" {
  default = {
    web = {}
    app = {}
    worker = {}
  }
}

resource "aws_instance" "server" {
  for_each = var.servers
  # ...
}
```

```bash
# Migrar state
terraform state mv 'aws_instance.server[0]' 'aws_instance.server["web"]'
terraform state mv 'aws_instance.server[1]' 'aws_instance.server["app"]'
terraform state mv 'aws_instance.server[2]' 'aws_instance.server["worker"]'
```

### terraform state rm

Elimina resource de state (sin destruir resource real):

```bash
# Remover un resource
terraform state rm aws_instance.web

# Remover múltiples
terraform state rm aws_instance.web[0] aws_instance.web[1]

# Remover todo un module
terraform state rm module.networking
```

**Cuándo usar:**
- Resource fue eliminado manualmente en console
- Quieres que Terraform deje de gestionar un resource
- Moviendo resource a otro state

### terraform state pull

Descarga y muestra remote state:

```bash
terraform state pull > terraform.tfstate.backup
```

### terraform state push

Sube state local a remote (⚠️ peligroso):

```bash
terraform state push terraform.tfstate
```

### terraform state replace-provider

Cambia provider de resources existentes:

```bash
# Cambiar de provider viejo a nuevo
terraform state replace-provider \
  registry.terraform.io/-/aws \
  registry.terraform.io/hashicorp/aws
```

---

## Workspaces

**Workspaces** permiten gestionar múltiples estados de la misma configuration.

### Comandos de Workspace

```bash
# Listar workspaces
terraform workspace list

# Crear nuevo workspace
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Cambiar workspace
terraform workspace select dev

# Workspace actual
terraform workspace show

# Eliminar workspace
terraform workspace delete dev
```

### Usar Workspaces en Configuration

```hcl
# Nombre del workspace actual
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  tags = {
    Name        = "web-${terraform.workspace}"
    Environment = terraform.workspace
  }
}

# Configuration diferente por workspace
locals {
  instance_count = {
    dev     = 1
    staging = 2
    prod    = 5
  }

  instance_type = {
    dev     = "t3.small"
    staging = "t3.medium"
    prod    = "t3.large"
  }
}

resource "aws_instance" "web" {
  count = local.instance_count[terraform.workspace]

  ami           = var.ami_id
  instance_type = local.instance_type[terraform.workspace]

  tags = {
    Name        = "web-${terraform.workspace}-${count.index + 1}"
    Environment = terraform.workspace
  }
}
```

### Workspaces con S3 Backend

S3 backend crea diferentes state files por workspace:

```
s3://mycompany-terraform-state/
├── env:/
│   ├── dev/
│   │   └── terraform.tfstate
│   ├── staging/
│   │   └── terraform.tfstate
│   └── prod/
│       └── terraform.tfstate
└── terraform.tfstate  # default workspace
```

### Workspaces vs Directorios Separados

| Aspecto | Workspaces |Directorios Separados |
|---------|------------|---------------------|
| Mismo código | ✅ Sí | ❌ Duplicado |
| State files | S3 diferentes keys | Diferentes backends |
| Cambiar entre envs | `workspace select` | `cd ../other-env` |
| Variables por env | Ternarios complejos | Archivos `.tfvars` separados |
| Isolation | Menos (mismo backend) | M (backends separados) |
| Recomendado para | Dev/test rápido | Prod (mejor isolation) |

### Best Practice: Directorios > Workspaces

Para production, preferir directorios separados:

```
environments/
├── dev/
│   ├── backend.tf
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars
├── staging/
│   ├── backend.tf
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars
└── prod/
    ├── backend.tf
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars
```

**Beneficios:**
- Mejor isolation (diferentes S3 buckets)
- Config diferente por environment
- Menos riesgo de aplicar cambios al env equivocado
- Más claro qué environment estás gestionando

---

## Import de Recursos

`terraform import` permite traer recursos existentes al state de Terraform.

### Import Básico

```bash
# Sintaxis
terraform import <RESOURCE_TYPE>.<NAME> <ID>

# Ejemplo: Importar EC2 instance
terraform import aws_instance.web i-1234567890abcdef0

# Ejemplo: Importar S3 bucket
terraform import aws_s3_bucket.data my-existing-bucket

# Ejemplo: Importar VPC
terraform import aws_vpc.main vpc-abc123
```

### Process de Import

```hcl
# 1. Define el resource (sin todos los detalles aún)
resource "aws_instance" "imported" {
  # Solo necesario para import, llenar después
}
```

```bash
# 2. Importa el resource
terraform import aws_instance.imported i-1234567890abcdef0

# Output:
# aws_instance.imported: Importing from ID "i-1234567890abcdef0"...
# aws_instance.imported: Import complete!
#   Imported aws_instance (ID: i-1234567890abcdef0)
```

```bash
# 3. Ver detalles del resource importado
terraform state show aws_instance.imported

# Copia output a tu configuration
```

```hcl
# 4. Actualiza resource con detalles completos
resource "aws_instance" "imported" {
  ami           = "ami-abc123"
  instance_type = "t3.micro"
  subnet_id     = "subnet-xyz789"

  tags = {
    Name = "Imported Instance"
  }
}
```

```bash
# 5. Plan para verify (no debe haber cambios)
terraform plan

# Debería mostrar: No changes. Infrastructure is up-to-date.
```

### Import con Count/For_Each

```bash
# Con count
terraform import 'aws_instance.web[0]' i-1234567890abcdef0
terraform import 'aws_instance.web[1]' i-0abcdef1234567890

# Con for_each
terraform import 'aws_instance.web["web-1"]' i-1234567890abcdef0
terraform import 'aws_instance.web["app-1"]' i-0abcdef1234567890
```

### Import deModule Resources

```bash
terraform import module.networking.aws_vpc.main vpc-abc123
terraform import module.compute.aws_instance.web i-123456
```

### Bulk Import Script

```bash
#!/bin/bash
# import-instances.sh

INSTANCES=(
  "web-1:i-1234567890abcdef0"
  "web-2:i-0abcdef1234567890"
  "app-1:i-567890abcdef1234"
)

for instance in "${INSTANCES[@]}"; do
  NAME="${instance%%:*}"
  ID="${instance##*:}"

  echo "Importing $NAME ($ID)..."
  terraform import "aws_instance.servers[\"$NAME\"]" "$ID"
done
```

### Import Block (Terraform 1.5+)

Nueva syntax para declarar imports en código:

```hcl
# Import block
import {
  to = aws_instance.web
  id = "i-1234567890abcdef0"
}

resource "aws_instance" "web" {
  # Configuration...
}
```

```bash
# Plan muestra que importará
terraform plan
# Output:
# aws_instance.web will be imported

# Apply importa el resource
terraform apply
```

### Common Resources y sus IDs

| Resource | ID Format | Ejemplo |
|----------|-----------|---------|
| `aws_instance` | Instance ID | `i-1234567890abcdef0` |
| `aws_vpc` | VPC ID | `vpc-abc123` |
| `aws_subnet` | Subnet ID | `subnet-xyz789` |
| `aws_s3_bucket` | Bucket name | `my-bucket` |
| `aws_db_instance` | DB identifier | `mydb` |
| `aws_security_group` | SG ID | `sg-abc123` |
| `aws_iam_role` | Role name | `MyRole` |
| `aws_iam_policy` | Policy ARN | `arn:aws:iam::123:policy/MyPolicy` |
| `aws_route53_zone` | Zone ID | `Z1234567890ABC` |

---

## Meta-Arguments

Meta-arguments son argumentos especiales que funcionan con cualquier resource/module.

### depends_on

```hcl
resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

resource "aws_lambda_function" "processor" {
  function_name = "processor"
  role          = aws_iam_role.lambda.arn

  depends_on = [aws_iam_role_policy_attachment.lambda]
}
```

### count

```hcl
variable "create_monitoring" {
  type = bool
  default = true
}

resource "aws_cloudwatch_dashboard" "main" {
  count = var.create_monitoring ? 1 : 0

  dashboard_name = "my-dashboard"
  # ...
}
```

### for_each

```hcl
variable "buckets" {
  type = map(object({
    versioning = bool
    encryption = bool
  }))

  default = {
    logs = {
      versioning = true
      encryption = true
    }
    data = {
      versioning = true
      encryption = true
    }
  }
}

resource "aws_s3_bucket" "buckets" {
  for_each = var.buckets

  bucket = each.key

  tags = {
    Name       = each.key
    Versioning = each.value.versioning
  }
}
```

### provider

```hcl
provider "aws" {
  region = "us-east-1"
  alias  = "primary"
}

provider "aws" {
  region = "us-west-2"
  alias  = "backup"
}

# Usar provider específico
resource "aws_s3_bucket" "primary" {
  provider = aws.primary
  bucket   = "primary-bucket"
}

resource "aws_s3_bucket" "backup" {
  provider = aws.backup
  bucket   = "backup-bucket"
}
```

### lifecycle

```hcl
resource "aws_db_instance" "main" {
  identifier = "mydb"

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
    ignore_changes       = [tags]
  }
}
```

---

## Dynamic Blocks

Dynamic blocks generan bloques nested dinámicamente.

### Sintaxis Básica

```hcl
# Sin dynamic (repetitivo)
resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

# Con dynamic (DRY)
variable "ingress_rules" {
  default = [
    { port = 80, cidr = ["0.0.0.0/0"] },
    { port = 443, cidr = ["0.0.0.0/0"] },
    { port = 22, cidr = ["10.0.0.0/8"] }
  ]
}

resource "aws_security_group" "web" {
  name = "web-sg"

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr
    }
  }
}
```

### Ejemplo Realista: Security Group

```hcl
variable "security_rules" {
  type = map(object({
    type        = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))

  default = {
    http = {
      type        = "ingress"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP from anywhere"
    }
    https = {
      type        = "ingress"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS from anywhere"
    }
    ssh = {
      type        = "ingress"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["10.0.0.0/8"]
      description = "SSH from internal"
    }
  }
}

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = { for k, v in var.security_rules : k => v if v.type == "ingress" }
    content {
      description = ingress.value.description
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  dynamic "egress" {
    for_each = { for k, v in var.security_rules : k => v if v.type == "egress" }
    content {
      description = egress.value.description
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = egress.value.cidr_blocks
    }
  }
}
```

### Dynamic con Nested Blocks

```hcl
variable "s3_lifecycle_rules" {
  type = list(object({
    id      = string
    enabled = bool
    transitions = list(object({
      days          = number
      storage_class = string
    }))
    expiration_days = number
  }))

  default = [
    {
      id      = "log-retention"
      enabled = true
      transitions = [
        { days = 30, storage_class = "STANDARD_IA" },
        { days = 90, storage_class = "GLACIER" }
      ]
      expiration_days = 365
    }
  ]
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  dynamic "rule" {
    for_each = var.s3_lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "transition" {
        for_each = rule.value.transitions
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      expiration {
        days = rule.value.expiration_days
      }
    }
  }
}
```

---

## Ejemplos Avanzados

### Multi-Region Deployment

```hcl
# main.tf
locals {
  regions = ["us-east-1", "us-west-2", "eu-west-1"]
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

module "infrastructure_us_east" {
  source = "./modules/regional-infrastructure"

  providers = {
    aws = aws.us_east_1
  }

  region      = "us-east-1"
  environment = var.environment
}

module "infrastructure_us_west" {
  source = "./modules/regional-infrastructure"

  providers = {
    aws = aws.us_west_2
  }

  region      = "us-west-2"
  environment = var.environment
}

module "infrastructure_eu_west" {
  source = "./modules/regional-infrastructure"

  providers = {
    aws = aws.eu_west_1
  }

  region      = "eu-west-1"
  environment = var.environment
}
```

### Conditional Resources with Complex Logic

```hcl
locals {
  # Crear ALB solo en prod o si explicitly habilitado
  create_alb = var.environment == "prod" || var.force_alb

  # Usar RDS multi-AZ solo en prod
  rds_multi_az = var.environment == "prod"

  # Auto-scaling config basado en environment
  asg_config = {
    dev = {
      min  = 1
      max  = 3
      desired = 1
    }
    staging = {
      min  = 2
      max  = 5
      desired = 2
    }
    prod = {
      min  = 5
      max  = 20
      desired = 10
    }
  }

  current_asg_config = lookup(local.asg_config, var.environment, local.asg_config.dev)
}

resource "aws_lb" "main" {
  count = local.create_alb ? 1 : 0

  name               = "${var.project}-${var.environment}-alb"
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
}

resource "aws_db_instance" "main" {
  identifier = "${var.project}-${var.environment}-db"

  engine         = "postgres"
  instance_class = var.db_instance_class

  multi_az = local.rds_multi_az

  backup_retention_period = var.environment == "prod" ? 30 : 7
}

resource "aws_autoscaling_group" "app" {
  name = "${var.project}-${var.environment}-asg"

  min_size         = local.current_asg_config.min
  max_size         = local.current_asg_config.max
  desired_capacity = local.current_asg_config.desired
}
```

### Blue-Green Deployment Pattern

```hcl
variable "active_env" {
  description = "Currently active environment (blue or green)"
  type        = string
  default     = "blue"

  validation {
    condition     = contains(["blue", "green"], var.active_env)
    error_message = "Active environment must be blue or green."
  }
}

locals {
  environments = {
    blue = {
      instance_count = var.active_env == "blue" ? var.desired_capacity : 1
      weight         = var.active_env == "blue" ? 100 : 0
    }
    green = {
      instance_count = var.active_env == "green" ? var.desired_capacity : 1
      weight         = var.active_env == "green" ? 100 : 0
    }
  }
}

# Blue environment
module "blue_environment" {
  source = "./modules/app-environment"

  name           = "${var.project}-blue"
  instance_count = local.environments.blue.instance_count
  ami_id         = var.blue_ami_id
}

# Green environment
module "green_environment" {
  source = "./modules/app-environment"

  name           = "${var.project}-green"
  instance_count = local.environments.green.instance_count
  ami_id         = var.green_ami_id
}

# ALB with weighted routing
resource "aws_lb_listener_rule" "blue" {
  listener_arn = aws_lb_listener.main.arn

  action {
    type             = "forward"
    target_group_arn = module.blue_environment.target_group_arn

    forward {
      target_group {
        arn    = module.blue_environment.target_group_arn
        weight = local.environments.blue.weight
      }

      target_group {
        arn    = module.green_environment.target_group_arn
        weight = local.environments.green.weight
      }
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

### Complete Data Pipeline Infrastructure

```hcl
# Data pipeline con múltiples stages
module "data_lake" {
  source = "./modules/data-lake"

  environment = var.environment
  project     = var.project

  buckets = {
    raw = {
      versioning = true
      lifecycle_rules = [
        {
          id         = "expire-old-raw"
          enabled    = true
          expiration = 90
        }
      ]
    }
    processed = {
      versioning = true
      lifecycle_rules = [
        {
          id         = "transition-to-glacier"
          enabled    = true
          transition = {
            days          = 180
            storage_class = "GLACIER"
          }
        }
      ]
    }
    curated = {
      versioning    = true
      replication   = true
      lifecycle_rules = []
    }
  }
}

module "glue_catalog" {
  source = "./modules/glue-catalog"

  environment = var.environment
  project     = var.project

  databases = {
    raw       = { location = module.data_lake.bucket_arns.raw }
    processed = { location = module.data_lake.bucket_arns.processed }
    curated   = { location = module.data_lake.bucket_arns.curated }
  }

  crawlers = {
    raw_data = {
      database_name = "raw"
      s3_target     = "${module.data_lake.bucket_names.raw}/data/"
      schedule      = "cron(0 1 * * ? *)"
    }
  }
}

module "emr_cluster" {
  source = "./modules/emr"

  environment = var.environment
  project     = var.project

  cluster_config = {
    release_label = "emr-6.14.0"
    applications  = ["Spark", "Hadoop", "Hive"]

    master_instance_type = var.environment == "prod" ? "m5.xlarge" : "m5.large"
    core_instance_type   = var.environment == "prod" ? "m5.xlarge" : "m5.large"
    core_instance_count  = var.environment == "prod" ? 5 : 2
  }

  s3_bucket_arn = module.data_lake.bucket_arns.processed
}

module "athena_workgroup" {
  source = "./modules/athena"

  environment = var.environment
  project     = var.project

  workgroups = {
    analytics = {
      output_location = "s3://${module.data_lake.bucket_names.curated}/athena-results/"
      enforce_config  = true

      configuration = {
        bytes_scanned_cutoff_per_query = 1000000000000  # 1TB
        result_configuration_updates = {
          encryption_configuration = {
            encryption_option = "SSE_S3"
          }
        }
      }
    }
  }
}

# Outputs
output "data_lake_buckets" {
  value = {
    for stage, bucket in module.data_lake.bucket_names :
    stage => "s3://${bucket}"
  }
}

output "glue_catalog_databases" {
  value = module.glue_catalog.database_names
}

output "emr_cluster_id" {
  value = module.emr_cluster.cluster_id
  }

output "athena_workgroup_arn" {
  value = module.athena_workgroup.workgroup_arns.analytics
}
```

---

## Best Practices Avanzadas

### 1. Modularización Efectiva

✅ **Crear modules por función, no por tipo de recurso**

```hcl
# ❌ MAL
modules/
├── ec2/
├── s3/
├── rds/

# ✅ BIEN
modules/
├── networking/
├── compute/
├── database/
├── storage/
└── monitoring/
```

### 2. Composition over Inheritance

```hcl
# ✅ BIEN: Componer modules pequeños
module "app" {
  source = "./modules/app"

  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
  db_endpoint = module.database.endpoint
}
```

### 3. Input Validation

```hcl
variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_count" {
  type = number

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 100
    error_message = "Instance count must be between 1 and 100."
  }
}

variable "cidr_block" {
  type = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be valid IPv4 CIDR block."
  }
}
```

### 4. Sensitive Data Handling

```hcl
# ✅ BIEN: Usar secrets manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/master-password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
  # ...
}

# ✅ BIEN: Mark as sensitive
output "db_password" {
  value     = aws_db_instance.main.password
  sensitive = true
}
```

### 5. Resource Tagging Strategy

```hcl
locals {
  common_tags = {
    Environment  = var.environment
    Project      = var.project
    ManagedBy    = "Terraform"
    Owner        = var.owner
    CostCenter   = var.cost_center
    Compliance   = var.compliance_level
    CreatedDate  = formatdate("YYYY-MM-DD", timestamp())
  }

  # Merge con tags específicos
  all_tags = merge(local.common_tags, var.additional_tags)
}

# Aplicar a todos los resources
resource "aws_instance" "web" {
  # ...
  tags = merge(local.all_tags, {
    Name = "${var.project}-${var.environment}-web"
    Role = "webserver"
  })
}
```

---

## Conclusión

En este module avanzado has aprendido:

✅ **Modules**: Crear, usar y componer modules reutilizables
✅ **Count y For Each**: Crear múltiples recursos dinámicamente
✅ **Funciones**: Manipular datos con funciones built-in
✅ **Dependencies**: Gestionar dependencies explícitas e implícitas
✅ **Lifecycle**: Controlar comportamiento de resources
✅ **Remote State**: Gestionar state compartido y collaboration
✅ **State Commands**: Manipular state de forma avanzada
✅ **Workspaces**: Gestionar múltiples environments
✅ **Import**: Traer recursos existentes a Terraform
✅ **Dynamic Blocks**: Generar bloques nested dinámicamente
✅ **Patrones Avanzados**: Blue-green, multi-region, data pipelines

En el siguiente module (`03-iac-patterns.md`), veremos patrones de organización, testing, CI/CD, y governance de Infrastructure as Code.

**¡Sigue practicando estos conceptos avanzados para dominar Terraform!**
