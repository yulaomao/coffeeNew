from flask import request
from flask_login import login_required
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.models import TaskJob
from app.extensions import db


@bp.route('/tasks', methods=['GET'])
@login_required
def list_tasks():
    """List background tasks"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        type_filter = request.args.get('type')
        status_filter = request.args.get('status')
        
        query = db.session.query(TaskJob)
        
        if type_filter:
            query = query.filter(TaskJob.type == type_filter)
        
        if status_filter:
            query = query.filter(TaskJob.status == status_filter)
        
        total = query.count()
        tasks = query.order_by(TaskJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        task_data = [task.to_dict() for task in tasks]
        
        return paginated_response(task_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list tasks: {str(e)}",
            status_code=500
        )


@bp.route('/tasks/<task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a background task"""
    try:
        task = TaskJob.query.get(task_id)
        if not task:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Task not found",
                status_code=404
            )
        
        if task.status.value not in ['pending', 'running']:
            return error_response(
                ErrorCode.INVALID_ARGUMENT,
                "Task cannot be cancelled",
                status_code=400
            )
        
        task.status = 'canceled'
        db.session.commit()
        
        return success_response({
            "message": "Task cancelled",
            "task": task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to cancel task: {str(e)}",
            status_code=500
        )