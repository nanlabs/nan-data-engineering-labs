# 🚀 Setup Guide

## Complete Installation & Configuration Guide

This guide walks you through setting up the Cloud Data Engineering learning environment from scratch.

---

## 📋 System Requirements

### Minimum Requirements

- **OS:** Linux, macOS, or Windows with WSL2
- **RAM:** 8GB (16GB recommended)
- **Disk Space:** 10GB free
- **CPU:** 4 cores (8 recommended)

### Software Requirements

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Python | 3.9+ | Scripts and data processing |
| Git | 2.30+ | Version control |

---

## 🐧 Installation by Operating System

### Linux (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip

# Install Git
sudo apt install git

# Verify installations
docker --version
docker compose version
python3 --version
git --version
```text

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install Python 3.9+
brew install python@3.9

# Install Git
brew install git

# Start Docker Desktop
open /Applications/Docker.app

# Verify installations
docker --version
docker compose version
python3 --version
git --version
```text

### Windows (WSL2)

```powershell
# 1. Install WSL2 (run in PowerShell as Administrator)
wsl --install

# 2. Reboot system

# 3. Install Ubuntu from Microsoft Store

# 4. Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# 5. Enable WSL2 backend in Docker Desktop settings

# 6. Open Ubuntu terminal and follow Linux instructions above
```text

---

## 📦 Project Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd nan-data-engineering-labs

# Check directory structure
ls -la
```

Expected structure:

```text
nan-data-engineering-labs/
├── docker-compose.yml
├── Makefile
├── README.md
├── LEARNING-PATH.md
├── requirements.txt
├── .gitignore
├── modules/
├── shared/
├── scripts/
└── docs/
```text

### 2. Run Automated Setup

```bash
# Make setup script executable
chmod +x scripts/setup-environment.sh

# Run setup
bash scripts/setup-environment.sh
```text

The setup script will:

1. ✅ Verify Docker and Python installations
2. ✅ Create Python virtual environment
3. ✅ Install Python dependencies
4. ✅ Configure AWS credentials for LocalStack
5. ✅ Generate sample datasets
6. ✅ Create necessary directories
7. ✅ Pull Docker images
8. ✅ Create .env file

**Estimated time:** 10-15 minutes (depending on internet speed)

### 3. Verify Setup

```bash
# Check Python environment
source venv/bin/activate
python --version
pip list | grep boto3

# Check Docker images
docker images | grep localstack
docker images | grep kafka
docker images | grep spark

# Check directory structure
ls -la shared/data/common-datasets/
ls -la modules/
```

---

## 🐳 Starting Services

### Start All Services

```bash
# Using Makefile (recommended)
make up

# Or using docker-compose directly
docker-compose up -d
```text

### Verify Services Are Running

```bash
# Check container status
docker-compose ps

# Should see:
# - localstack (healthy)
# - kafka (running)
# - zookeeper (running)
# - postgres (running)
# - trino (running)
# - spark-master (running)
# - spark-worker (running)
# - minio (running)
```text

### Test Service Connectivity

```bash
# Test LocalStack (AWS services)
aws --endpoint-url=http://localhost:4566 s3 ls

# Test PostgreSQL
docker exec -it cloud-de-postgres psql -U cloudde -d data_warehouse -c "SELECT 1;"

# Test MinIO
curl http://localhost:9001

# Test Trino
curl http://localhost:8080/ui/
```text

### Service Endpoints

| Service | Endpoint | Credentials |
|---------|----------|-------------|
| LocalStack | <http://localhost:4566> | test/test |
| MinIO Console | <http://localhost:9001> | minioadmin/minioadmin |
| MinIO API | <http://localhost:9000> | minioadmin/minioadmin |
| PostgreSQL | localhost:5432 | cloudde/cloudde123 |
| Trino UI | <http://localhost:8080> | - |
| Spark UI | <http://localhost:8081> | - |
| Kafka | localhost:29092 | - |

---

## 🔧 Configuration

### Environment Variables

The `.env` file is created automatically by setup. To customize:

```bash
# Edit .env file
nano .env

# Example customizations:
AWS_DEFAULT_REGION=us-west-2  # Change region
POSTGRES_PASSWORD=newpassword  # Change password
```

### AWS CLI Configuration

```bash
# Configure AWS CLI for LocalStack
aws configure --profile localstack

AWS Access Key ID: test
AWS Secret Access Key: test
Default region name: us-east-1
Default output format: json

# Use with LocalStack
aws --endpoint-url=http://localhost:4566 --profile localstack s3 ls
```text

### Python Virtual Environment

```bash
# Activate venv
source venv/bin/activate

# Deactivate when done
deactivate

# Install additional packages if needed
pip install <package-name>
pip freeze > requirements-custom.txt
```text

---

## 🧪 Verification Tests

### Run All Verification Tests

```bash
# Test LocalStack connectivity
make test-localstack

# Test Python environment
python shared/utilities/aws_helpers.py

# Generate sample data
python shared/utilities/data_generators.py

# Check progress tracking
make progress
```text

### Manual Service Tests

#### LocalStack (AWS Services)

```bash
# Create S3 bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://test-bucket

# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Upload file
echo "test" > test.txt
aws --endpoint-url=http://localhost:4566 s3 cp test.txt s3://test-bucket/

# Verify
aws --endpoint-url=http://localhost:4566 s3 ls s3://test-bucket/
```

#### Kafka

```bash
# Create topic
docker exec -it cloud-de-kafka kafka-topics \
  --create --topic test-topic \
  --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

# List topics
docker exec -it cloud-de-kafka kafka-topics \
  --list --bootstrap-server localhost:9092
```text

#### Spark

```bash
# Access Spark master
docker exec -it cloud-de-spark-master spark-shell --version

# Open Spark UI in browser
open http://localhost:8081
```text

---

## 🐛 Troubleshooting

### Docker Issues

**Problem:** Docker daemon not running

```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker

# macOS
# Start Docker Desktop application

# Windows
# Start Docker Desktop
```text

**Problem:** Permission denied

```bash
# Linux - add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Problem:** Port already in use

```bash
# Find process using port
sudo lsof -i :4566  # Replace with your port

# Kill process
kill -9 <PID>
```text

### LocalStack Issues

**Problem:** LocalStack not starting

```bash
# Check logs
docker-compose logs localstack

# Restart LocalStack
docker-compose restart localstack

# Clean start
docker-compose down
docker volume rm nan-data-engineering-labs_localstack-volume
docker-compose up -d
```text

**Problem:** Services not available

```bash
# Check which services are running
curl http://localhost:4566/_localstack/health

# Restart specific service
docker-compose restart localstack
```text

### Python Issues

**Problem:** Module not found

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem:** Python version mismatch

```bash
# Check Python version
python --version

# Use specific version
python3.9 -m venv venv
source venv/bin/activate
```text

### Network Issues

**Problem:** Cannot connect to services

```bash
# Check if services are running
docker-compose ps

# Check network
docker network ls
docker network inspect nan-data-engineering-labs_cloud-de-network

# Restart networking
docker-compose down
docker-compose up -d
```text

---

## 🧹 Cleanup & Reset

### Stop Services

```bash
# Stop all services
make down

# Or
docker-compose down
```text

### Clean All Data

```bash
# Stop and remove volumes
make clean

# Or manually
docker-compose down -v
rm -rf localstack-volume/
rm -rf .localstack/
```

### Complete Reset

```bash
# Remove everything
docker-compose down -v --rmi all
rm -rf venv/
rm -rf shared/data/common-datasets/*
rm .env

# Run setup again
bash scripts/setup-environment.sh
```text

---

## 🔄 Updating

### Pull Latest Changes

```bash
# Pull from git
git pull origin main

# Regenerate modules if structure changed
python scripts/generate_structure.py

# Rebuild Docker images
docker-compose pull
docker-compose up -d --force-recreate
```text

### Update Python Dependencies

```bash
# Activate venv
source venv/bin/activate

# Update packages
pip install --upgrade -r requirements.txt
```text

---

## 💡 Tips & Best Practices

### Resource Management

```bash
# Check Docker resource usage
docker stats

# Clean unused Docker resources
docker system prune -a

# Limit Docker resources (Docker Desktop settings)
# CPU: 4-8 cores
# Memory: 6-8 GB
# Swap: 1-2 GB
```

### Daily Workflow

```bash
# Start your day
cd nan-data-engineering-labs
source venv/bin/activate
make up

# Work on modules...

# End your day
make down
deactivate
```text

### Backup Your Work

```bash
# Backup my_solution directories
tar -czf my-solutions-$(date +%Y%m%d).tar.gz \
  modules/*/exercises/*/my_solution/

# Backup progress
cp -r modules/ backup/modules-$(date +%Y%m%d)/
```text

---

## 📚 Next Steps

After successful setup:

1. **Read LEARNING-PATH.md** - Understand the learning journey
2. **Check progress** - Run `make progress`
3. **Start Module 01** - `cd modules/module-01-cloud-fundamentals`
4. **Review troubleshooting** - Bookmark [docs/troubleshooting.md](troubleshooting.md)
5. **Explore LocalStack** - Read [docs/localstack-guide.md](localstack-guide.md)

---

## ❓ Getting Help

- **Setup Issues:** Review this guide
- **Service Issues:** Check [troubleshooting.md](troubleshooting.md)
- **LocalStack:** See [localstack-guide.md](localstack-guide.md)
- **Module Questions:** Each module has `theory/resources.md`

---

**Setup complete! You're ready to begin your Cloud Data Engineering journey! 🚀**
