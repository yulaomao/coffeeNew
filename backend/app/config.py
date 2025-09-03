import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql+psycopg://postgres:postgres@localhost:5432/coffee_admin'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Features
    ENABLE_SSE = os.environ.get('ENABLE_SSE', 'true').lower() == 'true'
    ENABLE_DEVICE_TOKEN = os.environ.get('ENABLE_DEVICE_TOKEN', 'false').lower() == 'true'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Command timeouts (seconds)
    COMMAND_TIMEOUT_DEFAULT = 300  # 5 minutes
    COMMAND_TIMEOUT_UPGRADE = 1800  # 30 minutes
    COMMAND_MAX_ATTEMPTS = 5
    
    # Queue expiration (seconds)
    QUEUE_EXPIRE_DEFAULT = 7 * 24 * 3600  # 7 days