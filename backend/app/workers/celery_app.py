from celery import Celery
from app.config import Config

def create_celery_app():
    """Create Celery app"""
    celery = Celery('coffee_admin')
    
    celery.conf.update(
        broker_url=Config.CELERY_BROKER_URL,
        result_backend=Config.CELERY_RESULT_BACKEND,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_routes={
            'app.workers.jobs.dispatch.*': {'queue': 'dispatch'},
            'app.workers.jobs.exports.*': {'queue': 'exports'},
            'app.workers.jobs.alarms.*': {'queue': 'alarms'},
        },
        beat_schedule={
            'dispatcher-tick': {
                'task': 'app.workers.jobs.dispatch.dispatcher_tick',
                'schedule': 30.0,  # Every 30 seconds
            },
            'timeout-checker': {
                'task': 'app.workers.jobs.dispatch.timeout_checker',
                'schedule': 60.0,  # Every minute
            },
            'export-runner': {
                'task': 'app.workers.jobs.exports.export_runner',
                'schedule': 60.0,  # Every minute
            },
            'alarm-aggregator': {
                'task': 'app.workers.jobs.alarms.alarm_aggregator',
                'schedule': 300.0,  # Every 5 minutes
            },
        }
    )
    
    return celery

celery = create_celery_app()

# Import tasks to register them
from app.workers.jobs import dispatch, exports, alarms