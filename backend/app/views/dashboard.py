from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime, timezone
from flask import flash, timedelta
from app.models import Device, Order, Alarm, DeviceBin
from app.extensions import db
from sqlalchemy import func

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """Dashboard home page"""
    try:
        # Get query parameters
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        merchant_id = request.args.get('merchant_id', type=int)
        
        # Parse dates
        if from_date:
            from_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        else:
            from_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        if to_date:
            to_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
        else:
            to_date = datetime.now(timezone.utc)
        
        # Device statistics
        device_stats = db.session.query(Device.status, func.count(Device.device_id)).group_by(Device.status).all()
        device_total = sum(count for _, count in device_stats)
        online_count = 0
        
        for status, count in device_stats:
            if status.value == 'online':
                online_count = count
                break
        
        online_rate = online_count / device_total if device_total > 0 else 0
        
        # Sales statistics
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        sales_today = db.session.query(func.sum(Order.total_price)).filter(
            Order.server_ts >= today_start
        ).scalar() or 0
        
        sales_week = db.session.query(func.sum(Order.total_price)).filter(
            Order.server_ts >= week_start
        ).scalar() or 0
        
        # Alarms and materials
        alarms_open = db.session.query(Alarm).filter(Alarm.status == 'open').count()
        
        materials_low = db.session.query(DeviceBin).filter(
            DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
        ).count()
        
        # Recent orders
        recent_orders = db.session.query(Order).order_by(Order.server_ts.desc()).limit(10).all()
        
        # Recent alarms
        recent_alarms = db.session.query(Alarm).order_by(Alarm.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                             device_total=device_total,
                             online_rate=round(online_rate * 100, 1),
                             sales_today=float(sales_today),
                             sales_week=float(sales_week),
                             alarms_open=alarms_open,
                             materials_low=materials_low,
                             recent_orders=recent_orders,
                             recent_alarms=recent_alarms)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html',
                             device_total=0, online_rate=0, sales_today=0, sales_week=0,
                             alarms_open=0, materials_low=0,
                             recent_orders=[], recent_alarms=[])