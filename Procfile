web: python run.py
worker: celery -A run.celery worker --loglevel=info
beat: celery -A run.celery beat --loglevel=info