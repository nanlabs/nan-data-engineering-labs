# Makefile - Module 16: Data Security & Compliance

.PHONY: help setup install test validate clean security-scan format lint docs

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
VENV := venv

help: ## Show this help message
	@echo "Module 16: Data Security & Compliance - Available Commands"
	@echo "==========================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Create virtual environment and install dependencies
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing dependencies..."
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "✓ Setup complete"

install: ## Install dependencies
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed"

test: ## Run all tests
	@echo "Running security tests..."
	$(PYTEST) validation/ -v --cov=exercises --cov-report=html
	@echo "✓ Tests complete"

validate: ## Validate security configurations
	@echo "Validating IAM policies..."
	$(PYTHON) validation/test_security.py --test iam
	@echo "Validating encryption..."
	$(PYTHON) validation/test_security.py --test encryption
	@echo "Validating compliance..."
	$(PYTHON) validation/test_security.py --test compliance
	@echo "✓ Validation complete"

security-scan: ## Run security scanners
	@echo "Running Bandit (Python security scanner)..."
	bandit -r exercises/ -f json -o reports/bandit-report.json
	@echo "Running Safety (dependency vulnerability check)..."
	safety check --json > reports/safety-report.json
	@echo "Checking IAM policies with Parliament..."
	find exercises/ -name "*.json" -exec parliament --json {} \\;
	@echo "✓ Security scan complete"

lint: ## Run linters
	@echo "Running pylint..."
	pylint exercises/ --output-format=colorized
	@echo "Running mypy (type checking)..."
	mypy exercises/ --ignore-missing-imports
	@echo "✓ Linting complete"

format: ## Format code
	@echo "Formatting with black..."
	black exercises/ validation/
	@echo "Sorting imports..."
	isort exercises/ validation/
	@echo "✓ Formatting complete"

docs: ## Generate documentation
	@echo "Generating documentation..."
	mkdocs build
	@echo "✓ Documentation generated in site/"

clean: ## Clean temporary files
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ site/
	@echo "✓ Cleaned"

# Exercise-specific commands
ex01: ## Run Exercise 01: IAM & Access Control
	@echo "Exercise 01: IAM & Access Control"
	cd exercises/01-iam-access-control && $(PYTHON) create_iam_roles.py

ex02: ## Run Exercise 02: Data Encryption
	@echo "Exercise 02: Data Encryption"
	cd exercises/02-data-encryption && $(PYTHON) create_kms_keys.py

ex03: ## Run Exercise 03: Data Masking
	@echo "Exercise 03: Data Masking & Anonymization"
	cd exercises/03-data-masking-anonymization && $(PYTHON) presidio_pii_detection.py

ex04: ## Run Exercise 04: Audit & Compliance
	@echo "Exercise 04: Audit & Compliance"
	cd exercises/04-audit-compliance && $(PYTHON) setup_cloudtrail.py

ex05: ## Run Exercise 05: Data Governance
	@echo "Exercise 05: Data Governance"
	cd exercises/05-data-governance && $(PYTHON) setup_lake_formation.py

ex06: ## Run Exercise 06: Security Monitoring
	@echo "Exercise 06: Security Monitoring"
	cd exercises/06-security-monitoring && $(PYTHON) setup_guardduty.py

# AWS resource management
aws-setup: ## Setup AWS infrastructure
	@echo "Setting up AWS infrastructure..."
	./infrastructure/init-aws.sh
	@echo "✓ AWS infrastructure setup complete"

aws-cleanup: ## Cleanup AWS resources
	@echo "Cleaning up AWS resources..."
	./scripts/cleanup.sh
	@echo "✓ AWS cleanup complete"

# Security validation
validate-iam: ## Validate IAM policies
	@echo "Validating IAM policies..."
	find exercises/ -name "*-policy.json" -exec policy-sentry analyze {} \\;
	find exercises/ -name "*-policy.json" -exec parliament {} \\;
	@echo "✓ IAM validation complete"

validate-encryption: ## Check encryption status
	@echo "Validating encryption..."
	aws s3api list-buckets --query 'Buckets[*].Name' --output text | xargs -I {} aws s3api get-bucket-encryption --bucket {}
	@echo "✓ Encryption validation complete"

compliance-report: ## Generate compliance report
	@echo "Generating compliance report..."
	$(PYTHON) scripts/generate_compliance_report.py --output reports/compliance-report.html
	@echo "✓ Report generated: reports/compliance-report.html"
