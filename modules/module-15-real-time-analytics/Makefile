# Module 15: Real-Time Analytics - Makefile
# Convenient commands for development and testing

.PHONY: help setup start stop status logs clean validate test exercise-01 exercise-02 docker-build

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Module 15: Real-Time Analytics$(NC)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Setup environment and install dependencies
	@echo "$(BLUE)Setting up Module 15 environment...$(NC)"
	bash scripts/setup.sh

start: ## Start all Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	cd infrastructure && docker-compose up -d
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo "Services:"
	@echo "  - Flink UI:  http://localhost:8081"
	@echo "  - Grafana:   http://localhost:3000 (admin/admin123)"

stop: ## Stop all Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	cd infrastructure && docker-compose down
	@echo "$(GREEN)✓ Containers stopped$(NC)"

restart: stop start ## Restart all containers

status: ## Show status of all containers
	@echo "$(BLUE)Docker Container Status:$(NC)"
	@docker ps --filter "name=module15" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(BLUE)AWS Services (LocalStack):$(NC)"
	@awslocal kinesis list-streams --region us-east-1 2>/dev/null | grep StreamNames || echo "  Kinesis: Not ready"
	@awslocal dynamodb list-tables --region us-east-1 2>/dev/null | grep TableNames || echo "  DynamoDB: Not ready"
	@echo ""
	@echo "$(BLUE)Flink Cluster:$(NC)"
	@curl -s http://localhost:8081/overview | jq -r '"  Job Manager: Running\n  Task Managers: \(.taskmanagers)\n  Available Slots: \(.["slots-available"])/\(.["slots-total"])"' 2>/dev/null || echo "  Flink: Not ready"

logs: ## Show logs from all containers
	cd infrastructure && docker-compose logs -f

logs-flink: ## Show Flink Job Manager logs
	docker logs -f module15-flink-jobmanager

logs-localstack: ## Show LocalStack logs
	docker logs -f module15-localstack

clean: ## Clean up all data and containers
	@echo "$(RED)This will remove all containers and data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		bash scripts/cleanup.sh; \
	else \
		echo "Cancelled."; \
	fi

deep-clean: clean ## Deep clean (includes Docker images)
	@echo "$(RED)Removing Docker images...$(NC)"
	docker rmi -f localstack/localstack:3.0 || true
	docker rmi -f flink:1.18-java11 || true
	docker rmi -f postgres:15-alpine || true
	docker rmi -f confluentinc/cp-kafka:7.5.0 || true
	docker rmi -f confluentinc/cp-zookeeper:7.5.0 || true
	docker rmi -f grafana/grafana:10.2.0 || true
	@echo "$(GREEN)✓ Images removed$(NC)"

validate: ## Run validation tests
	@echo "$(BLUE)Running validation tests...$(NC)"
	bash scripts/validate.sh

test: ## Run Python unit tests
	@echo "$(BLUE)Running pytest tests...$(NC)"
	pytest validation/ -v --tb=short

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest validation/ -v --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-infrastructure: ## Test infrastructure only
	pytest validation/test_infrastructure.py -v

install-deps: ## Install Python dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

exercise-01: ## Run Exercise 01 (Kinesis Analytics SQL)
	@echo "$(BLUE)Exercise 01: Kinesis Analytics SQL$(NC)"
	@cd exercises/01-kinesis-analytics-sql && \
	echo "1. Reading exercise README..." && \
	echo "2. Check exercise directory for SQL files" && \
	ls -la

exercise-02: ## Run Exercise 02 (Flink Table API)
	@echo "$(BLUE)Exercise 02: Flink Table API$(NC)"
	@cd exercises/02-flink-table-api && \
	echo "Check exercise directory" && \
	ls -la || echo "Exercise not yet created"

generate-data: ## Generate sample streaming events
	@echo "$(BLUE)Generating sample events...$(NC)"
	@cd exercises/01-kinesis-analytics-sql && \
	python generate_events.py --count 1000 --rate 10

stream-continuous: ## Generate continuous event stream
	@echo "$(BLUE)Generating continuous event stream (Ctrl+C to stop)...$(NC)"
	@cd exercises/01-kinesis-analytics-sql && \
	python generate_events.py --count 100000 --rate 50

flink-ui: ## Open Flink Web UI in browser
	@echo "$(BLUE)Opening Flink UI...$(NC)"
	@python3 -m webbrowser http://localhost:8081 || xdg-open http://localhost:8081 || open http://localhost:8081

grafana-ui: ## Open Grafana in browser
	@echo "$(BLUE)Opening Grafana...$(NC)"
	@python3 -m webbrowser http://localhost:3000 || xdg-open http://localhost:3000 || open http://localhost:3000

kinesis-list: ## List all Kinesis streams
	@echo "$(BLUE)Kinesis Streams:$(NC)"
	@awslocal kinesis list-streams --region us-east-1 | jq -r '.StreamNames[]'

kinesis-describe: ## Describe events-stream
	@awslocal kinesis describe-stream --stream-name events-stream --region us-east-1 | jq

dynamodb-list: ## List all DynamoDB tables
	@echo "$(BLUE)DynamoDB Tables:$(NC)"
	@awslocal dynamodb list-tables --region us-east-1 | jq -r '.TableNames[]'

dynamodb-scan: ## Scan realtime-aggregates table
	@awslocal dynamodb scan --table-name realtime-aggregates --region us-east-1 | jq '.Items | length' | xargs -I {} echo "Items in table: {}"

s3-list: ## List all S3 buckets
	@echo "$(BLUE)S3 Buckets:$(NC)"
	@awslocal s3 ls

flink-jobs: ## List running Flink jobs
	@echo "$(BLUE)Running Flink Jobs:$(NC)"
	@curl -s http://localhost:8081/jobs | jq -r '.jobs[] | "\(.id) - \(.status)"'

flink-metrics: ## Show Flink cluster metrics
	@echo "$(BLUE)Flink Cluster Metrics:$(NC)"
	@curl -s http://localhost:8081/overview | jq '{"taskmanagers": .taskmanagers, "slots_total": .["slots-total"], "slots_available": .["slots-available"], "jobs_running": .["jobs-running"], "jobs_finished": .["jobs-finished"]}'

docker-build: ## Rebuild Docker images
	@echo "$(BLUE)Rebuilding Docker images...$(NC)"
	cd infrastructure && docker-compose build --no-cache

docker-pull: ## Pull latest Docker images
	@echo "$(BLUE)Pulling latest images...$(NC)"
	cd infrastructure && docker-compose pull

monitor: ## Monitor system resources
	@echo "$(BLUE)System Resource Monitoring (Ctrl+C to stop)$(NC)"
	@watch -n 2 'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep module15'

shell-flink: ## Open shell in Flink Job Manager
	docker exec -it module15-flink-jobmanager bash

shell-localstack: ## Open shell in LocalStack
	docker exec -it module15-localstack bash

sql-cli: ## Open Flink SQL CLI
	docker exec -it module15-flink-jobmanager ./bin/sql-client.sh

theory: ## Open theory documentation
	@echo "$(BLUE)Theory Documentation:$(NC)"
	@ls -1 theory/*.md | sed 's/^/  - /'
	@echo ""
	@echo "Read concepts: less theory/concepts.md"

progress: ## Show module progress
	@echo "$(BLUE)Module 15 Progress:$(NC)"
	@echo ""
	@cat STATUS.md | grep -A 20 "## 📈 Module Metrics" || echo "See STATUS.md for details"

lint: ## Lint Python code
	@echo "$(BLUE)Linting Python code...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format Python code with black
	@echo "$(BLUE)Formatting Python code...$(NC)"
	black .
	isort .

check-setup: ## Check if environment is properly set up
	@echo "$(BLUE)Checking environment setup...$(NC)"
	@echo -n "Docker: " && docker --version || echo "$(RED)Not installed$(NC)"
	@echo -n "Docker Compose: " && docker-compose --version || echo "$(RED)Not installed$(NC)"
	@echo -n "Python: " && python3 --version || echo "$(RED)Not installed$(NC)"
	@echo -n "AWS CLI: " && aws --version || echo "$(RED)Not installed$(NC)"
	@echo -n "pytest: " && pytest --version || echo "$(RED)Not installed$(NC)"
	@echo -n "curl: " && curl --version | head -1 || echo "$(RED)Not installed$(NC)"
	@echo -n "jq: " && jq --version || echo "$(RED)Not installed$(NC)"

readme: ## Show main README
	@less README.md

update-status: ## Update STATUS.md with current metrics
	@echo "$(BLUE)Updating STATUS.md...$(NC)"
	@echo "Last updated: $$(date)" >> STATUS.md

.PHONY: all
all: setup start ## Setup and start everything
