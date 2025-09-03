from flask import request
from flask_login import login_required
from datetime import datetime, timezone
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.models import OperationLog
from app.extensions import db


@bp.route('/audit', methods=['GET'])
@login_required
def list_audit_logs():
    """List audit logs"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        action = request.args.get('action')
        target_type = request.args.get('target_type')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        
        query = db.session.query(OperationLog)
        
        if action:
            query = query.filter(OperationLog.action == action)
        
        if target_type:
            query = query.filter(OperationLog.target_type == target_type)
        
        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            query = query.filter(OperationLog.created_at >= from_dt)
        
        if to_date:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            query = query.filter(OperationLog.created_at <= to_dt)
        
        total = query.count()
        logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        log_data = [log.to_dict() for log in logs]
        
        return paginated_response(log_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list audit logs: {str(e)}",
            status_code=500
        )