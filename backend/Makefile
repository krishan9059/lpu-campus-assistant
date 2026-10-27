.PHONY: install dev test lint format seed ingest evaluate calibrate run docker-build docker-up

install:
	pip install -e ".[ml,dev]"

dev:
	uvicorn app.main:app --reload --port 8000

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests
	ruff format --check app tests

format:
	ruff format app tests
	ruff check app tests --fix

seed:
	python -m app.cli.seed

seed-reset:
	python -m app.cli.seed --reset

ingest:
	python -m app.cli.ingest

reindex:
	python -m app.cli.ingest --rebuild

evaluate:
	python -m app.cli.evaluate

calibrate:
	python -m app.cli.calibrate

docker-build:
	docker build -t lpu-campus-assistant-backend .

docker-up:
	docker compose up --build
