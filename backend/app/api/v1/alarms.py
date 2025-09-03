from flask import request
from flask_login import login_required
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.models import Alarm
from app.extensions import db


@bp.route('/alarms', methods=['GET'])
@login_required
def list_alarms():
    """List alarms"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        type_filter = request.args.get('type')
        status_filter = request.args.get('status')
        device_id = request.args.get('device_id')
        
        query = db.session.query(Alarm)
        
        if type_filter:
            query = query.filter(Alarm.type == type_filter)
        
        if status_filter:
            query = query.filter(Alarm.status == status_filter)
        
        if device_id:
            query = query.filter(Alarm.device_id == device_id)
        
        total = query.count()
        alarms = query.order_by(Alarm.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        alarm_data = [alarm.to_dict() for alarm in alarms]
        
        return paginated_response(alarm_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list alarms: {str(e)}",
            status_code=500
        )


@bp.route('/alarms/<int:alarm_id>/ack', methods=['POST'])
@login_required
def acknowledge_alarm(alarm_id):
    """Acknowledge an alarm"""
    try:
        alarm = Alarm.query.get(alarm_id)
        if not alarm:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Alarm not found",
                status_code=404
            )
        
        alarm.status = 'ack'
        db.session.commit()
        
        return success_response({
            "message": "Alarm acknowledged",
            "alarm": alarm.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to acknowledge alarm: {str(e)}",
            status_code=500
        )