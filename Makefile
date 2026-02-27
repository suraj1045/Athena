# ─────────────────────────────────────────────────────────────
# Athena — Makefile
# Common development and deployment commands
# ─────────────────────────────────────────────────────────────

.PHONY: help install install-dev install-ml test lint typecheck format clean deploy-infra

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────

install: ## Install core dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

install-ml: ## Install ML/training dependencies
	pip install -r requirements-ml.txt

# ── Quality ───────────────────────────────────────────────────

test: ## Run all tests
	pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linter (ruff)
	ruff check src/ tests/

typecheck: ## Run static type checking (mypy)
	mypy src/ --strict

format: ## Auto-format code (black + ruff)
	black src/ tests/
	ruff check src/ tests/ --fix

# ── Infrastructure ────────────────────────────────────────────

up: ## Start the local FOSS services (Postgres, Redis, MinIO)
	docker-compose up -d

down: ## Stop the local FOSS services
	docker-compose down

# ── Cleanup ───────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov dist build *.egg-info
