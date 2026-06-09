# Presence — developer convenience targets.
.DEFAULT_GOAL := help
.PHONY: help install dev-db migrate revision api worker web test test-api test-web lint fmt

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install all deps (api via uv, web via pnpm)
	cd apps/api && uv sync
	pnpm install

dev-db: ## Start local infra (Supabase stack + Redis)
	supabase start
	docker compose up -d redis

migrate: ## Apply DB migrations
	cd apps/api && uv run alembic upgrade head

revision: ## Create a new migration: make revision m="message"
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

api: ## Run the FastAPI dev server
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

worker: ## Run the Celery worker
	cd apps/api && uv run celery -A app.worker.celery_app.celery_app worker --loglevel=info

web: ## Run the Next.js dev server
	pnpm --filter @presence/web dev

test: test-api test-web ## Run all tests

test-api: ## Run backend tests
	cd apps/api && uv run pytest

test-web: ## Run web tests (Vitest)
	pnpm --filter @presence/web test

lint: ## Lint everything
	cd apps/api && uv run ruff check .
	pnpm --filter @presence/web lint

fmt: ## Format backend code
	cd apps/api && uv run ruff format .
