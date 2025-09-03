.PHONY: venv install migrate init-db run-web run-worker run-beat test lint seed

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

init-db:
	. .venv/bin/activate && python manage.py init-db

migrate:
	. .venv/bin/activate && python manage.py migrate

seed:
	. .venv/bin/activate && python manage.py seed-demo

run-web:
	. .venv/bin/activate && python manage.py run-web

run-worker:
	. .venv/bin/activate && python manage.py run-worker

run-beat:
	. .venv/bin/activate && python manage.py run-beat

test:
	. .venv/bin/activate && pytest --cov=app --maxfail=1 -q