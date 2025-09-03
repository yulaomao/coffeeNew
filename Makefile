.PHONY: help install run-web run-worker run-beat test lint format init-db seed clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

run-web: ## Run Flask web server
	python run.py

run-worker: ## Run Celery worker
	celery -A run.celery worker --loglevel=info

run-beat: ## Run Celery beat scheduler
	celery -A run.celery beat --loglevel=info

test: ## Run tests
	pytest

lint: ## Run linting
	flake8 app/ --max-line-length=100
	isort --check-only app/

format: ## Format code
	black app/ manage.py run.py config.py
	isort app/ manage.py run.py config.py

init-db: ## Initialize database
	python manage.py init-db

seed: ## Create seed data
	python manage.py seed-demo

create-user: ## Create admin user (make create-user EMAIL=admin@test.com PASSWORD=test123 NAME="Test Admin")
	python manage.py create-user --email $(EMAIL) --password $(PASSWORD) --name "$(NAME)" --role admin

clean: ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/