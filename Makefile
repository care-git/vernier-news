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
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(name)"

seed:
	python -m scripts.seed

logs:
	docker compose logs -f api

shell:
	docker compose exec api bash
