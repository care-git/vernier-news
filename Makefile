.PHONY: up down build test lint format migrate seed reembed analyse recluster spotcheck logs shell

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

reembed:
	docker compose exec api python -m scripts.reembed

analyse:
	docker compose exec api python -m scripts.analyse_corpus

recluster:
	docker compose exec api python -m scripts.recluster

spotcheck:
	docker compose exec api python -m scripts.spot_check

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash
