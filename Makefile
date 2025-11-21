# Makefile - CLEANED VERSION
.PHONY: help local-up local-down dev-up dev-down migrate migrate-create run test clean

help:
	@echo "Available commands:"
	@echo "  make local-up       - Start local setup (DB only)"
	@echo "  make local-down     - Stop local setup"
	@echo "  make dev-up         - Start dev setup (DB + App)"
	@echo "  make dev-down       - Stop dev setup"
	@echo "  make migrate        - Run migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make run            - Run app locally"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Clean cache and volumes"

# Local setup (DB only, app runs locally)
local-up:
	docker-compose -f docker-compose.local.yml up -d
	@echo "✅ Local DB started on localhost:5432"
	@echo "Run: make run"

local-down:
	docker-compose -f docker-compose.local.yml down

local-logs:
	docker-compose -f docker-compose.local.yml logs -f

# Dev setup (DB + App in Docker)
dev-up:
	docker-compose -f docker-compose.dev.yml up -d --build
	@echo "✅ Dev environment started"
	@echo "App: http://localhost:8080"
	@echo "Docs: http://localhost:8080/docs"

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f app

dev-rebuild:
	docker-compose -f docker-compose.dev.yml up -d --build

# Migrations (for local setup)
migrate:
	poetry run alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " message; \
	poetry run alembic revision --autogenerate -m "$$message"

migrate-downgrade:
	poetry run alembic downgrade -1

# Run app locally
run:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Testing
test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Linting & Formatting
lint:
	poetry run ruff check app/ tests/

format:
	poetry run ruff format app/ tests/
	poetry run ruff check app/ tests/ --fix

# Cleanup
clean:
	docker-compose -f docker-compose.local.yml down -v
	docker-compose -f docker-compose.dev.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache

.PHONY: install dev
install:
	poetry install --no-dev

dev:
	poetry install
