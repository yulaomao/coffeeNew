import os
import importlib

def _optional_load_dotenv():
    try:
        dotenv = importlib.import_module('dotenv')
        return getattr(dotenv, 'load_dotenv', lambda *a, **k: False)
    except Exception:
        return lambda *a, **k: False

load_dotenv = _optional_load_dotenv()

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql+psycopg://postgres:postgres@localhost:5432/coffee_admin')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Broker/Backend settings (no Redis by default)
    # Prefer environment overrides, otherwise fall back to in-memory/backends
    REDIS_URL = os.environ.get('REDIS_URL')  # Optional; not required by default
    
    # Celery settings: default to in-memory for local/dev without Redis
    CELERY = {
        'broker_url': os.environ.get('CELERY_BROKER_URL', 'memory://'),
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'cache+memory://'),
        'task_ignore_result': True,
        'timezone': 'UTC',
        # Execute tasks eagerly in testing if requested
        'task_always_eager': os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true',
    }
    
    # Security settings
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', '3600'))
    
    # Feature flags
    ENABLE_SSE = os.environ.get('ENABLE_SSE', 'False').lower() == 'true'
    ENABLE_DEVICE_TOKEN = os.environ.get('ENABLE_DEVICE_TOKEN', 'False').lower() == 'true'
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', '20'))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', '100'))
    
    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    # Default to in-memory rate limit storage if not provided
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    # File upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # Use SQLite by default for local development (override via DATABASE_URL if needed)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///coffee_dev.db')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # Ensure Celery tasks run synchronously during tests
    CELERY = Config.CELERY.copy()
    CELERY.update({'task_always_eager': True})


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}