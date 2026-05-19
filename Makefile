.PHONY: up down build test lint format migrate seed logs shell

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check .
	black --check .

format:
	ruff check --fix .
	black .

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

seed:
	docker compose exec api python -m scripts.seed

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash
