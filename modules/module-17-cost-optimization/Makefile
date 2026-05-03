# Module 17: Cloud Cost Optimization - Makefile
# Comprehensive automation for cost optimization workflows

.PHONY: help setup validate clean clean-force test test-verbose test-coverage test-report
.PHONY: cost-report cost-by-service cost-by-team cost-by-project cost-by-environment
.PHONY: cost-trend cost-forecast cost-comparison cost-anomalies cost-dashboard
.PHONY: savings-recommendations right-sizing-report waste-report storage-optimization commitment-utilization
.PHONY: ex01 ex02 ex03 ex04 ex05 ex06 all-exercises
.PHONY: docker-up docker-down docker-logs docker-restart localstack-health
.PHONY: jupyter-start jupyter-token jupyter-open
.PHONY: db-connect db-seed db-reset readme

# Variables
PYTHON := python3
VENV := .venv
AWS := aws
DOCKER_COMPOSE := docker-compose
PYTEST := pytest
NOTEBOOK_DIR := notebooks
DATA_DIR := data
REPORTS_DIR := reports
SCRIPTS_DIR := scripts
EXERCISES_DIR := exercises

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ============================================================================
# Help & Documentation
# ============================================================================

help:
	@echo "$(BLUE)Module 17: Cloud Cost Optimization - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Environment:$(NC)"
	@echo "  make setup                  - Run setup.sh (create venv, install deps, start Docker)"
	@echo "  make validate               - Run validate.sh (comprehensive checks)"
	@echo "  make clean                  - Run cleanup.sh with confirmation"
	@echo "  make clean-force            - Run cleanup.sh without confirmation"
	@echo ""
	@echo "$(GREEN)Cost Reporting:$(NC)"
	@echo "  make cost-report            - Generate monthly cost breakdown CSV (last 12 months)"
	@echo "  make cost-by-service        - Service-by-service cost table (top 10)"
	@echo "  make cost-by-team           - Team allocation report"
	@echo "  make cost-by-project        - Project allocation report"
	@echo "  make cost-by-environment    - Environment breakdown (Prod/Dev/Test)"
	@echo "  make cost-trend             - Line chart of last 12 months"
	@echo "  make cost-forecast          - Next 3 months forecast"
	@echo "  make cost-comparison        - Compare current vs last month"
	@echo "  make cost-anomalies         - List recent cost anomalies (30 days)"
	@echo "  make cost-dashboard         - Generate comprehensive dashboard"
	@echo ""
	@echo "$(GREEN)Optimization Analysis:$(NC)"
	@echo "  make savings-recommendations - Get RI/SP recommendations"
	@echo "  make right-sizing-report    - EC2 Compute Optimizer recommendations"
	@echo "  make waste-report           - Identify idle resources"
	@echo "  make storage-optimization   - S3 Storage Lens analysis"
	@echo "  make commitment-utilization - RI/SP utilization report"
	@echo ""
	@echo "$(GREEN)Exercises:$(NC)"
	@echo "  make ex01                   - Run Exercise 01 (Cost Analysis)"
	@echo "  make ex02                   - Run Exercise 02 (Storage Optimization)"
	@echo "  make ex03                   - Run Exercise 03 (Compute Purchasing)"
	@echo "  make ex04                   - Run Exercise 04 (Right-Sizing)"
	@echo "  make ex05                   - Run Exercise 05 (Serverless Costs)"
	@echo "  make ex06                   - Run Exercise 06 (Cost Governance)"
	@echo "  make all-exercises          - Run all exercises sequentially"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test                   - Run pytest suite"
	@echo "  make test-verbose           - Run pytest with -v flag"
	@echo "  make test-coverage          - Run pytest with coverage report"
	@echo "  make test-report            - Generate HTML coverage report"
	@echo ""
	@echo "$(GREEN)Docker & LocalStack:$(NC)"
	@echo "  make docker-up              - Start all Docker services"
	@echo "  make docker-down            - Stop all services"
	@echo "  make docker-logs            - View logs for all services"
	@echo "  make docker-restart         - Restart services"
	@echo "  make localstack-health      - Check LocalStack health"
	@echo ""
	@echo "$(GREEN)Jupyter:$(NC)"
	@echo "  make jupyter-start          - Start Jupyter notebook server"
	@echo "  make jupyter-token          - Display Jupyter access token"
	@echo "  make jupyter-open           - Open Jupyter in browser"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-connect             - Connect to PostgreSQL"
	@echo "  make db-seed                - Seed sample cost data"
	@echo "  make db-reset               - Drop and recreate database"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  make readme                 - Display module README"

# ============================================================================
# Setup & Environment
# ============================================================================

setup:
	@echo "$(YELLOW)Running environment setup...$(NC)"
	@bash $(SCRIPTS_DIR)/setup.sh

validate:
	@echo "$(YELLOW)Running comprehensive validation...$(NC)"
	@bash $(SCRIPTS_DIR)/validate.sh

clean:
	@echo "$(YELLOW)Running cleanup (with confirmation)...$(NC)"
	@bash $(SCRIPTS_DIR)/cleanup.sh

clean-force:
	@echo "$(RED)Running cleanup (no confirmation)...$(NC)"
	@bash $(SCRIPTS_DIR)/cleanup.sh --force

# ============================================================================
# Cost Reporting
# ============================================================================

cost-report:
	@echo "$(YELLOW)Generating monthly cost breakdown...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@$(AWS) ce get-cost-and-usage \
		--time-period Start=$$(date -d '12 months ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--granularity MONTHLY \
		--metrics BlendedCost UnblendedCost \
		--group-by Type=DIMENSION,Key=SERVICE \
		--output json > $(REPORTS_DIR)/cost-by-service-12m.json
	@$(PYTHON) -c "import json,csv,sys; data=json.load(open('$(REPORTS_DIR)/cost-by-service-12m.json')); writer=csv.writer(sys.stdout); writer.writerow(['Month','Service','Cost']); [writer.writerow([r['TimePeriod']['Start'],g['Keys'][0],g['Metrics']['BlendedCost']['Amount']]) for r in data['ResultsByTime'] for g in r['Groups']]" > $(REPORTS_DIR)/cost-by-service-12m.csv
	@echo "$(GREEN)Report saved to $(REPORTS_DIR)/cost-by-service-12m.csv$(NC)"

cost-by-service:
	@echo "$(YELLOW)Analyzing costs by service...$(NC)"
	@$(AWS) ce get-cost-and-usage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--granularity MONTHLY \
		--metrics BlendedCost \
		--group-by Type=DIMENSION,Key=SERVICE \
		--output table

cost-by-team:
	@echo "$(YELLOW)Analyzing costs by team...$(NC)"
	@$(AWS) ce get-cost-and-usage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--granularity MONTHLY \
		--metrics BlendedCost \
		--group-by Type=TAG,Key=Team \
		--output table

cost-by-project:
	@echo "$(YELLOW)Analyzing costs by project...$(NC)"
	@$(AWS) ce get-cost-and-usage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--granularity MONTHLY \
		--metrics BlendedCost \
		--group-by Type=TAG,Key=Project \
		--output table

cost-by-environment:
	@echo "$(YELLOW)Analyzing costs by environment...$(NC)"
	@$(AWS) ce get-cost-and-usage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--granularity MONTHLY \
		--metrics BlendedCost \
		--group-by Type=TAG,Key=Environment \
		--output table

cost-trend:
	@echo "$(YELLOW)Generating cost trend chart...$(NC)"
	@$(PYTHON) -c "import boto3,matplotlib.pyplot as plt,json; ce=boto3.client('ce'); resp=ce.get_cost_and_usage(TimePeriod={'Start':'$$(date -d '12 months ago' +%Y-%m-01)','End':'$$(date +%Y-%m-01)'},Granularity='MONTHLY',Metrics=['BlendedCost']); months=[r['TimePeriod']['Start'] for r in resp['ResultsByTime']]; costs=[float(r['Total']['BlendedCost']['Amount']) for r in resp['ResultsByTime']]; plt.figure(figsize=(12,6)); plt.plot(months,costs,marker='o'); plt.title('AWS Cost Trend (Last 12 Months)'); plt.xlabel('Month'); plt.ylabel('Cost (USD)'); plt.xticks(rotation=45); plt.grid(True); plt.tight_layout(); plt.savefig('$(REPORTS_DIR)/cost-trend.png'); print('Chart saved to $(REPORTS_DIR)/cost-trend.png')"

cost-forecast:
	@echo "$(YELLOW)Generating cost forecast...$(NC)"
	@$(AWS) ce get-cost-forecast \
		--time-period Start=$$(date +%Y-%m-01),End=$$(date -d '+3 months' +%Y-%m-01) \
		--metric BLENDED_COST \
		--granularity MONTHLY \
		--output table

cost-comparison:
	@echo "$(YELLOW)Comparing current month vs last month...$(NC)"
	@$(PYTHON) -c "import boto3,json; ce=boto3.client('ce'); last=ce.get_cost_and_usage(TimePeriod={'Start':'$$(date -d '2 months ago' +%Y-%m-01)','End':'$$(date -d '1 month ago' +%Y-%m-01)'},Granularity='MONTHLY',Metrics=['BlendedCost']); curr=ce.get_cost_and_usage(TimePeriod={'Start':'$$(date -d '1 month ago' +%Y-%m-01)','End':'$$(date +%Y-%m-01)'},Granularity='MONTHLY',Metrics=['BlendedCost']); last_cost=float(last['ResultsByTime'][0]['Total']['BlendedCost']['Amount']); curr_cost=float(curr['ResultsByTime'][0]['Total']['BlendedCost']['Amount']); change=curr_cost-last_cost; pct=(change/last_cost)*100; print(f'Last Month: \$$${last_cost:.2f}'); print(f'Current Month: \$$${curr_cost:.2f}'); print(f'Change: \$$${change:.2f} ({pct:+.1f}%)')"

cost-anomalies:
	@echo "$(YELLOW)Checking for cost anomalies (last 30 days)...$(NC)"
	@$(AWS) ce get-anomalies \
		--date-interval Start=$$(date -d '30 days ago' +%Y-%m-%d),End=$$(date +%Y-%m-%d) \
		--monitor-arn-list "arn:aws:ce::*:anomaly-monitor/*" \
		--output table

cost-dashboard:
	@echo "$(YELLOW)Generating comprehensive cost dashboard...$(NC)"
	@$(PYTHON) $(SCRIPTS_DIR)/generate_dashboard.py

# ============================================================================
# Optimization Analysis
# ============================================================================

savings-recommendations:
	@echo "$(YELLOW)Fetching RI/SP savings recommendations...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@echo "$(BLUE)Reserved Instance Recommendations:$(NC)"
	@$(AWS) ce get-reservation-purchase-recommendation \
		--service AmazonEC2 \
		--lookback-period-in-days SIXTY_DAYS \
		--payment-option ALL_UPFRONT \
		--term-in-years ONE_YEAR \
		--output table
	@echo ""
	@echo "$(BLUE)Savings Plans Recommendations:$(NC)"
	@$(AWS) ce get-savings-plans-purchase-recommendation \
		--savings-plans-type COMPUTE_SP \
		--lookback-period-in-days SIXTY_DAYS \
		--payment-option ALL_UPFRONT \
		--term-in-years ONE_YEAR \
		--output table

right-sizing-report:
	@echo "$(YELLOW)Generating EC2 right-sizing recommendations...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@$(AWS) compute-optimizer get-ec2-instance-recommendations \
		--output json > $(REPORTS_DIR)/right-sizing-recommendations.json
	@$(PYTHON) -c "import json,csv,sys; data=json.load(open('$(REPORTS_DIR)/right-sizing-recommendations.json')); writer=csv.writer(sys.stdout); writer.writerow(['Instance','Current Type','Recommended Type','Current Cost','Recommended Cost','Savings']); [writer.writerow([r['instanceArn'].split('/')[-1],r['currentInstanceType'],r['recommendationOptions'][0]['instanceType'],r['currentInstanceType'],r['recommendationOptions'][0]['instanceType'],r['recommendationOptions'][0]['estimatedMonthlySavings']['value']]) for r in data.get('instanceRecommendations',[]) if r.get('finding')=='Underprovisioned']" > $(REPORTS_DIR)/right-sizing-report.csv
	@echo "$(GREEN)Report saved to $(REPORTS_DIR)/right-sizing-report.csv$(NC)"

waste-report:
	@echo "$(YELLOW)Identifying waste (idle resources)...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@echo "$(BLUE)Idle EC2 Instances (CPU < 5% for 7 days):$(NC)"
	@$(PYTHON) $(EXERCISES_DIR)/exercise-06-cost-governance/cleanup_automation.py --dry-run --idle-ec2
	@echo ""
	@echo "$(BLUE)Unattached EBS Volumes (>30 days):$(NC)"
	@$(PYTHON) $(EXERCISES_DIR)/exercise-06-cost-governance/cleanup_automation.py --dry-run --unattached-volumes
	@echo ""
	@echo "$(BLUE)Old Snapshots (>90 days):$(NC)"
	@$(PYTHON) $(EXERCISES_DIR)/exercise-06-cost-governance/cleanup_automation.py --dry-run --old-snapshots
	@echo ""
	@echo "$(BLUE)Unused Elastic IPs:$(NC)"
	@$(PYTHON) $(EXERCISES_DIR)/exercise-06-cost-governance/cleanup_automation.py --dry-run --unused-eips
	@echo ""
	@echo "$(GREEN)Run 'make clean' to remove identified waste$(NC)"

storage-optimization:
	@echo "$(YELLOW)Analyzing S3 storage optimization opportunities...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@$(AWS) s3control get-storage-lens-configuration-tagging \
		--config-id default-account-dashboard \
		--account-id $$($(AWS) sts get-caller-identity --query Account --output text) \
		--output json > $(REPORTS_DIR)/storage-lens.json
	@$(PYTHON) $(EXERCISES_DIR)/exercise-02-storage-optimization/lifecycle_policies.py
	@echo "$(GREEN)Analysis saved to $(REPORTS_DIR)/storage-optimization.csv$(NC)"

commitment-utilization:
	@echo "$(YELLOW)Checking RI/SP utilization and coverage...$(NC)"
	@echo "$(BLUE)Reserved Instance Utilization:$(NC)"
	@$(AWS) ce get-reservation-utilization \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--output table
	@echo ""
	@echo "$(BLUE)Reserved Instance Coverage:$(NC)"
	@$(AWS) ce get-reservation-coverage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--output table
	@echo ""
	@echo "$(BLUE)Savings Plans Utilization:$(NC)"
	@$(AWS) ce get-savings-plans-utilization \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--output table
	@echo ""
	@echo "$(BLUE)Savings Plans Coverage:$(NC)"
	@$(AWS) ce get-savings-plans-coverage \
		--time-period Start=$$(date -d '1 month ago' +%Y-%m-01),End=$$(date +%Y-%m-01) \
		--output table

# ============================================================================
# Exercises
# ============================================================================

ex01:
	@echo "$(YELLOW)Running Exercise 01: Cost Analysis with Cost Explorer...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-01-cost-analysis && $(PYTHON) cost_explorer_analysis.py
	@cd $(EXERCISES_DIR)/exercise-01-cost-analysis && $(PYTHON) cur_analysis.py
	@cd $(EXERCISES_DIR)/exercise-01-cost-analysis && $(PYTHON) cost_tagging.py
	@echo "$(GREEN)Exercise 01 complete!$(NC)"

ex02:
	@echo "$(YELLOW)Running Exercise 02: Storage Optimization...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-02-storage-optimization && $(PYTHON) lifecycle_policies.py
	@cd $(EXERCISES_DIR)/exercise-02-storage-optimization && $(PYTHON) intelligent_tiering.py
	@cd $(EXERCISES_DIR)/exercise-02-storage-optimization && $(PYTHON) storage_analytics.py
	@echo "$(GREEN)Exercise 02 complete!$(NC)"

ex03:
	@echo "$(YELLOW)Running Exercise 03: Compute Purchasing Strategies...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-03-compute-purchasing && $(PYTHON) ri_analysis.py
	@cd $(EXERCISES_DIR)/exercise-03-compute-purchasing && $(PYTHON) savings_plans.py
	@cd $(EXERCISES_DIR)/exercise-03-compute-purchasing && $(PYTHON) spot_instances.py
	@echo "$(GREEN)Exercise 03 complete!$(NC)"

ex04:
	@echo "$(YELLOW)Running Exercise 04: Right-Sizing Resources...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-04-right-sizing && $(PYTHON) compute_optimizer.py
	@cd $(EXERCISES_DIR)/exercise-04-right-sizing && $(PYTHON) cloudwatch_metrics.py
	@cd $(EXERCISES_DIR)/exercise-04-right-sizing && $(PYTHON) recommendations.py
	@echo "$(GREEN)Exercise 04 complete!$(NC)"

ex05:
	@echo "$(YELLOW)Running Exercise 05: Serverless Cost Analysis...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-05-serverless-costs && $(PYTHON) lambda_cost_analysis.py
	@cd $(EXERCISES_DIR)/exercise-05-serverless-costs && $(PYTHON) fargate_vs_ec2.py
	@cd $(EXERCISES_DIR)/exercise-05-serverless-costs && $(PYTHON) api_gateway_costs.py
	@echo "$(GREEN)Exercise 05 complete!$(NC)"

ex06:
	@echo "$(YELLOW)Running Exercise 06: Cost Governance...$(NC)"
	@cd $(EXERCISES_DIR)/exercise-06-cost-governance && $(PYTHON) budget_alerts.py
	@cd $(EXERCISES_DIR)/exercise-06-cost-governance && $(PYTHON) cleanup_automation.py --dry-run
	@cd $(EXERCISES_DIR)/exercise-06-cost-governance && $(PYTHON) finops_kpis.py
	@echo "$(GREEN)Exercise 06 complete!$(NC)"

all-exercises: ex01 ex02 ex03 ex04 ex05 ex06
	@echo "$(GREEN)All exercises completed successfully!$(NC)"

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "$(YELLOW)Running pytest suite...$(NC)"
	@$(PYTEST) validation/test_cost_optimization.py

test-verbose:
	@echo "$(YELLOW)Running pytest with verbose output...$(NC)"
	@$(PYTEST) validation/test_cost_optimization.py -v

test-coverage:
	@echo "$(YELLOW)Running pytest with coverage...$(NC)"
	@$(PYTEST) validation/test_cost_optimization.py \
		--cov=exercises \
		--cov-report=term-missing \
		--cov-report=html

test-report:
	@echo "$(YELLOW)Generating HTML coverage report...$(NC)"
	@$(PYTEST) validation/test_cost_optimization.py \
		--cov=exercises \
		--cov-report=html
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

# ============================================================================
# Docker & LocalStack
# ============================================================================

docker-up:
	@echo "$(YELLOW)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml up -d
	@echo "$(GREEN)Services started!$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml ps

docker-down:
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml down
	@echo "$(GREEN)Services stopped!$(NC)"

docker-logs:
	@echo "$(YELLOW)Viewing Docker logs...$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml logs --tail=100 -f

docker-restart:
	@echo "$(YELLOW)Restarting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml down
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml up -d
	@echo "$(GREEN)Services restarted!$(NC)"

localstack-health:
	@echo "$(YELLOW)Checking LocalStack health...$(NC)"
	@curl -s http://localhost:4566/_localstack/health | jq '.'

# ============================================================================
# Jupyter
# ============================================================================

jupyter-start:
	@echo "$(YELLOW)Starting Jupyter notebook server...$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml up -d jupyter
	@sleep 3
	@make jupyter-token

jupyter-token:
	@echo "$(YELLOW)Jupyter access token:$(NC)"
	@$(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml logs jupyter 2>&1 | grep -o 'token=[a-f0-9]*' | head -1 || echo "Token not found. Check logs with: make docker-logs"
	@echo ""
	@echo "$(GREEN)Access Jupyter at: http://localhost:8888$(NC)"

jupyter-open:
	@echo "$(YELLOW)Opening Jupyter in browser...$(NC)"
	@$(eval TOKEN := $(shell $(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml logs jupyter 2>&1 | grep -o 'token=[a-f0-9]*' | head -1 | cut -d= -f2))
	@if [ -n "$(TOKEN)" ]; then \
		xdg-open "http://localhost:8888/?token=$(TOKEN)" 2>/dev/null || \
		open "http://localhost:8888/?token=$(TOKEN)" 2>/dev/null || \
		echo "Open manually: http://localhost:8888/?token=$(TOKEN)"; \
	else \
		echo "$(RED)Could not find Jupyter token. Run 'make jupyter-token' first.$(NC)"; \
	fi

# ============================================================================
# Database
# ============================================================================

db-connect:
	@echo "$(YELLOW)Connecting to PostgreSQL...$(NC)"
	@docker exec -it $$($(DOCKER_COMPOSE) -f infrastructure/docker-compose.yml ps -q postgres) \
		psql -U cost_user -d cost_optimization_db

db-seed:
	@echo "$(YELLOW)Seeding sample cost data...$(NC)"
	@$(PYTHON) - <<EOF
	import psycopg2
	import json
	import sys

	conn = psycopg2.connect(
	    host='localhost',
	    port=5432,
	    database='cost_optimization_db',
	    user='cost_user',
	    password='cost_password'
	)
	cur = conn.cursor()

	# Create tables
	cur.execute("""
	    CREATE TABLE IF NOT EXISTS cost_history (
	        id SERIAL PRIMARY KEY,
	        cost_date DATE NOT NULL,
	        service VARCHAR(100),
	        cost_amount DECIMAL(10,2),
	        cost_center VARCHAR(50),
	        team VARCHAR(50),
	        environment VARCHAR(20)
	    )
	""")

	# Insert sample data
	cur.execute("""
	    INSERT INTO cost_history (cost_date, service, cost_amount, cost_center, team, environment)
	    VALUES
	        ('2024-01-01', 'AmazonEC2', 500.00, 'CC-12345', 'Engineering', 'prod'),
	        ('2024-01-01', 'AmazonS3', 350.00, 'CC-12345', 'Data', 'prod'),
	        ('2024-01-01', 'AmazonRDS', 200.00, 'CC-12345', 'Data', 'prod'),
	        ('2024-01-01', 'AWSLambda', 50.00, 'CC-67890', 'Data', 'prod')
	""")

	conn.commit()
	cur.close()
	conn.close()
	print("Sample data seeded successfully!")
	EOF
	@echo "$(GREEN)Database seeded!$(NC)"

db-reset:
	@echo "$(RED)Resetting database (this will delete all data)...$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	@$(PYTHON) - <<EOF
	import psycopg2

	conn = psycopg2.connect(
	    host='localhost',
	    port=5432,
	    database='cost_optimization_db',
	    user='cost_user',
	    password='cost_password'
	)
	cur = conn.cursor()
	cur.execute("DROP TABLE IF EXISTS cost_history CASCADE")
	cur.execute("DROP TABLE IF EXISTS optimization_actions CASCADE")
	conn.commit()
	cur.close()
	conn.close()
	print("Database reset complete!")
	EOF
	@make db-seed

# ============================================================================
# Documentation
# ============================================================================

readme:
	@if command -v mdcat >/dev/null 2>&1; then \
		mdcat README.md; \
	elif command -v glow >/dev/null 2>&1; then \
		glow README.md; \
	else \
		cat README.md; \
	fi
