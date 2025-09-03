from flask import request
from flask_login import login_required, current_user
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.api.decorators import validate_json, require_role
from app.schemas.command import DispatchCommandRequest, BatchRetryRequest
from app.models import RemoteCommand, CommandBatch
from app.extensions import db
from app.services.command_service import CommandService


@bp.route('/commands/dispatch', methods=['POST'])
@login_required
@validate_json(DispatchCommandRequest)
@require_role(['admin', 'ops'])
def dispatch_commands():
    """Dispatch commands to multiple devices"""
    try:
        dispatch_data = request.validated_json
        
        # Create batch commands
        batch, commands = CommandService.create_batch_commands(
            device_ids=dispatch_data.device_ids,
            command_type=dispatch_data.command_type,
            payload=dispatch_data.payload,
            note=dispatch_data.note,
            max_attempts=dispatch_data.max_attempts,
            created_by=current_user.id
        )
        
        return success_response({
            "batch_id": batch.batch_id,
            "message": f"Commands dispatched to {len(dispatch_data.device_ids)} devices",
            "commands_created": len(commands)
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to dispatch commands: {str(e)}",
            status_code=500
        )


@bp.route('/commands/batches', methods=['GET'])
@login_required
def list_command_batches():
    """List command batches"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        query = db.session.query(CommandBatch).order_by(CommandBatch.created_at.desc())
        
        total = query.count()
        batches = query.offset((page - 1) * page_size).limit(page_size).all()
        
        batch_data = [batch.to_dict() for batch in batches]
        
        return paginated_response(batch_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list batches: {str(e)}",
            status_code=500
        )


@bp.route('/commands/batches/<batch_id>', methods=['GET'])
@login_required
def get_command_batch(batch_id):
    """Get command batch details"""
    try:
        batch = CommandBatch.query.get(batch_id)
        if not batch:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Batch not found",
                status_code=404
            )
        
        # Get associated commands
        commands = RemoteCommand.query.filter_by(batch_id=batch_id).all()
        
        return success_response({
            "batch": batch.to_dict(),
            "commands": [command.to_dict() for command in commands]
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get batch: {str(e)}",
            status_code=500
        )


@bp.route('/commands/batches/<batch_id>/retry', methods=['POST'])
@login_required
@validate_json(BatchRetryRequest)
@require_role(['admin', 'ops'])
def retry_batch_commands(batch_id):
    """Retry failed commands in batch"""
    try:
        batch = CommandBatch.query.get(batch_id)
        if not batch:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Batch not found",
                status_code=404
            )
        
        retry_data = request.validated_json
        
        retried_count = CommandService.retry_failed_commands(
            batch_id=batch_id,
            device_ids=retry_data.device_ids
        )
        
        return success_response({
            "message": f"Retried {retried_count} commands",
            "retried_count": retried_count
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to retry commands: {str(e)}",
            status_code=500
        )