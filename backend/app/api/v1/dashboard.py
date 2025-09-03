from flask import request
from flask_login import login_required
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode
from app.models import Device, Order, Alarm, DeviceBin
from app.extensions import db


@bp.route('/dashboard/summary', methods=['GET'])
@login_required
def dashboard_summary():
    """Get dashboard summary data"""
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
        
        # Base query filters
        device_filter = []
        order_filter = [
            Order.server_ts >= from_date,
            Order.server_ts <= to_date
        ]
        
        if merchant_id:
            device_filter.append(Device.merchant_id == merchant_id)
            order_filter.append(Device.merchant_id == merchant_id)
        
        # Device statistics
        device_query = db.session.query(Device.status, func.count(Device.device_id)).group_by(Device.status)
        if device_filter:
            device_query = device_query.filter(and_(*device_filter))
        
        device_stats = device_query.all()
        
        device_total = sum(count for _, count in device_stats)
        online_count = 0
        
        for status, count in device_stats:
            if status.value == 'online':
                online_count = count
                break
        
        online_rate = online_count / device_total if device_total > 0 else 0
        
        # Sales statistics
        order_query = db.session.query(func.sum(Order.total_price)).filter(and_(*order_filter))
        if merchant_id:
            order_query = order_query.join(Device).filter(Device.merchant_id == merchant_id)
        
        total_sales = order_query.scalar() or 0
        
        # Today's sales
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_filter = order_filter + [Order.server_ts >= today_start]
        
        today_query = db.session.query(func.sum(Order.total_price)).filter(and_(*today_filter))
        if merchant_id:
            today_query = today_query.join(Device).filter(Device.merchant_id == merchant_id)
        
        sales_today = float(today_query.scalar() or 0)
        
        # Week's sales
        week_start = today_start - timedelta(days=7)
        week_filter = order_filter + [Order.server_ts >= week_start]
        
        week_query = db.session.query(func.sum(Order.total_price)).filter(and_(*week_filter))
        if merchant_id:
            week_query = week_query.join(Device).filter(Device.merchant_id == merchant_id)
        
        sales_week = float(week_query.scalar() or 0)
        
        # Open alarms
        alarms_query = db.session.query(Alarm).filter(Alarm.status == 'open')
        if merchant_id:
            alarms_query = alarms_query.join(Device).filter(Device.merchant_id == merchant_id)
        
        alarms_open = alarms_query.count()
        
        # Low materials
        materials_query = db.session.query(DeviceBin).filter(
            DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
        )
        if merchant_id:
            materials_query = materials_query.join(Device).filter(Device.merchant_id == merchant_id)
        
        materials_low = materials_query.count()
        
        # Trend data (simplified - daily sales for the period)
        daily_sales = []
        daily_online_rates = []
        
        current_date = from_date.date()
        end_date = to_date.date()
        
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            
            day_sales_query = db.session.query(func.sum(Order.total_price)).filter(
                and_(Order.server_ts >= day_start, Order.server_ts < day_end)
            )
            if merchant_id:
                day_sales_query = day_sales_query.join(Device).filter(Device.merchant_id == merchant_id)
            
            day_sales = float(day_sales_query.scalar() or 0)
            daily_sales.append({
                "date": current_date.isoformat(),
                "value": day_sales
            })
            
            # For online rate trend, use current online rate (simplified)
            daily_online_rates.append({
                "date": current_date.isoformat(),
                "value": online_rate
            })
            
            current_date += timedelta(days=1)
        
        return success_response({
            "device_total": device_total,
            "online_rate": round(online_rate, 3),
            "sales_today": sales_today,
            "sales_week": sales_week,
            "alarms_open": alarms_open,
            "materials_low": materials_low,
            "trends": {
                "sales": daily_sales,
                "online_rate": daily_online_rates
            }
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get dashboard summary: {str(e)}",
            status_code=500
        )