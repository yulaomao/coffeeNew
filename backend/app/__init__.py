import os
from datetime import datetime, timezone
from flask import Flask
from flask_migrate import Migrate
from app.extensions import db, login_manager, csrf, limiter, cache, migrate
from app.config import Config
from app.models import User, Merchant, Location, Device, DeviceBin, MaterialDictionary, Order, OrderItem, Recipe, RecipePackage, RemoteCommand, CommandBatch, Alarm, TaskJob, OperationLog


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.api.v1 import bp as api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    from app.views.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.views.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.views.devices import bp as devices_bp
    app.register_blueprint(devices_bp)
    
    from app.views.device_detail import bp as device_detail_bp
    app.register_blueprint(device_detail_bp)
    
    from app.views.orders import bp as orders_bp
    app.register_blueprint(orders_bp)
    
    from app.views.materials import bp as materials_bp
    app.register_blueprint(materials_bp)
    
    from app.views.recipes import bp as recipes_bp
    app.register_blueprint(recipes_bp)
    
    from app.views.packages import bp as packages_bp
    app.register_blueprint(packages_bp)
    
    from app.views.dispatch import bp as dispatch_bp
    app.register_blueprint(dispatch_bp)
    
    from app.views.alarms import bp as alarms_bp
    app.register_blueprint(alarms_bp)
    
    from app.views.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)
    
    from app.views.audit import bp as audit_bp
    app.register_blueprint(audit_bp)
    
    # Add metrics endpoint
    from app.metrics import metrics_bp
    app.register_blueprint(metrics_bp)
    
    # Add SSE endpoint if enabled
    if app.config.get('ENABLE_SSE'):
        from app.utils.sse import sse_bp
        app.register_blueprint(sse_bp)
    
    # Context processors for templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}
    
    return app