#!/usr/bin/env python3
"""
Flask application entry point.
"""
import os
from app import create_app, make_celery

app = create_app()
celery = make_celery(app)

if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )