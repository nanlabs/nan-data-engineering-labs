.PHONY: help setup up down clean validate progress check-deps install-deps validate-contract validate-language validate-all

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Run initial environment setup
	@echo "🚀 Setting up Cloud Data Engineering environment..."
	@bash scripts/setup-environment.sh

install-deps: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements.txt

up: ## Start all Docker services (LocalStack, Kafka, etc.)
	@echo "🐳 Starting Docker services..."
	@docker-compose up -d
	@echo "✅ Services started. LocalStack: http://localhost:4566"

down: ## Stop all Docker services
	@echo "🛑 Stopping Docker services..."
	@docker-compose down

clean: ## Stop services and remove volumes
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@rm -rf .localstack/ localstack-volume/

validate: ## Validate a specific module (usage: make validate MODULE=module-01-cloud-fundamentals)
	@bash scripts/validate-module.sh $(MODULE)

validate-contract: ## Validate module contracts (strict core + headings)
	@python scripts/validate_learning_labs.py --strict-core --strict-headings

validate-language: ## Validate English governance scope
	@python scripts/validate_english_content.py

validate-all: ## Run contract and language validators
	@python scripts/validate_learning_labs.py --strict-core --strict-headings
	@python scripts/validate_english_content.py

progress: ## Show learning progress
	@python scripts/progress.py

check-deps: ## Check prerequisites for a module (usage: make check-deps MODULE=module-05-data-lakehouse)
	@python scripts/check-prerequisites.py $(MODULE)

generate: ## Generate module structure
	@python scripts/generate_structure.py

logs: ## Show Docker service logs
	@docker-compose logs -f

restart: down up ## Restart all services

test-localstack: ## Test LocalStack connection
	@aws --endpoint-url=http://localhost:4566 s3 ls || echo "LocalStack not ready"
