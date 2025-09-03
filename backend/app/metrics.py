from flask import Blueprint, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client.multiprocess import MultiProcessCollector
import os

# Create blueprint for metrics endpoint
metrics_bp = Blueprint('metrics', __name__)

# Create metrics registry
registry = CollectorRegistry()

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    registry=registry
)

api_error_rate = Gauge(
    'api_error_rate',
    'API error rate',
    registry=registry
)

api_latency_avg = Gauge(
    'api_latency_avg_seconds',
    'Average API latency',
    registry=registry
)

# Device metrics
device_online_rate = Gauge(
    'device_online_rate',
    'Device online rate',
    registry=registry
)

devices_total = Gauge(
    'devices_total',
    'Total number of devices',
    ['status'],
    registry=registry
)

# Command metrics
pending_commands_count = Gauge(
    'pending_commands_count',
    'Number of pending commands',
    registry=registry
)

failed_dispatch_rate = Gauge(
    'failed_dispatch_rate',
    'Failed dispatch rate',
    registry=registry
)

command_processing_duration = Histogram(
    'command_processing_duration_seconds',
    'Command processing duration',
    ['command_type', 'status'],
    registry=registry
)

# Order metrics
daily_orders = Gauge(
    'daily_orders_total',
    'Total daily orders',
    registry=registry
)

order_value = Histogram(
    'order_value_cny',
    'Order value in CNY',
    registry=registry
)

# Material metrics
material_low_count = Gauge(
    'material_low_count',
    'Number of devices with low materials',
    registry=registry
)

# Task metrics
background_tasks_total = Counter(
    'background_tasks_total',
    'Total background tasks',
    ['task_type', 'status'],
    registry=registry
)

task_processing_duration = Histogram(
    'task_processing_duration_seconds',
    'Task processing duration',
    ['task_type'],
    registry=registry
)


@metrics_bp.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update metrics from database before exposing
        update_metrics()
        
        # Generate metrics in Prometheus format
        data = generate_latest(registry)
        return Response(data, mimetype=CONTENT_TYPE_LATEST)
    except Exception as e:
        return Response(f"Error generating metrics: {str(e)}", status=500)


def update_metrics():
    """Update metrics from database"""
    from app.models import Device, RemoteCommand, Order, Alarm, DeviceBin, TaskJob
    from app.extensions import db
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func
    
    try:
        # Device metrics
        device_stats = db.session.query(
            Device.status,
            func.count(Device.device_id).label('count')
        ).group_by(Device.status).all()
        
        total_devices = 0
        online_devices = 0
        
        for status, count in device_stats:
            devices_total.labels(status=status.value).set(count)
            total_devices += count
            if status.value == 'online':
                online_devices = count
        
        if total_devices > 0:
            device_online_rate.set(online_devices / total_devices)
        
        # Command metrics
        pending_count = db.session.query(RemoteCommand).filter(
            RemoteCommand.status.in_(['pending', 'queued'])
        ).count()
        pending_commands_count.set(pending_count)
        
        # Daily orders
        today = datetime.now(timezone.utc).date()
        today_orders = db.session.query(Order).filter(
            func.date(Order.server_ts) == today
        ).count()
        daily_orders.set(today_orders)
        
        # Material low count
        low_materials = db.session.query(DeviceBin).filter(
            DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
        ).count()
        material_low_count.set(low_materials)
        
    except Exception as e:
        print(f"Error updating metrics: {e}")


# Middleware to track API metrics
def track_api_metrics(app):
    """Middleware to track API request metrics"""
    @app.before_request
    def before_request():
        from flask import g, request
        import time
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        from flask import g, request
        import time
        
        if hasattr(g, 'start_time') and request.endpoint:
            duration = time.time() - g.start_time
            
            # Track request metrics
            api_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
            
            api_request_duration.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
        
        return response