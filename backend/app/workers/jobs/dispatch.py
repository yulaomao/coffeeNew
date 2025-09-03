from datetime import datetime, timezone, timedelta
from app.workers.celery_app import celery
from app.models import RemoteCommand, CommandBatch, Device, OperationLog
from app.extensions import db
from app import create_app


@celery.task
def process_single_command(command_id):
    """Process a single command dispatch"""
    app = create_app()
    with app.app_context():
        try:
            command = RemoteCommand.query.get(command_id)
            if not command:
                return {"error": "Command not found"}
            
            device = Device.query.get(command.device_id)
            if not device:
                command.status = 'fail'
                command.last_error = "Device not found"
                db.session.commit()
                return {"error": "Device not found"}
            
            # Check device compatibility
            if not _is_command_supported(device, command.type.value):
                command.status = 'unsupported'
                command.last_error = f"Command {command.type.value} not supported by device {device.model}"
                db.session.commit()
                return {"status": "unsupported"}
            
            # Check device status
            if device.status.value not in ['online', 'registered']:
                # Queue for later if device is offline
                command.status = 'queued'
                command.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                return {"status": "queued", "reason": "device_offline"}
            
            # Mark as sent (in real implementation, this would actually send to device)
            command.status = 'sent'
            command.sent_at = datetime.now(timezone.utc)
            command.updated_at = datetime.now(timezone.utc)
            
            # Update batch statistics if part of batch
            if command.batch_id:
                _update_batch_statistics(command.batch_id)
            
            db.session.commit()
            
            return {"status": "sent", "command_id": command_id}
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}


@celery.task
def process_command_batch(batch_id):
    """Process all commands in a batch"""
    app = create_app()
    with app.app_context():
        try:
            batch = CommandBatch.query.get(batch_id)
            if not batch:
                return {"error": "Batch not found"}
            
            commands = RemoteCommand.query.filter_by(batch_id=batch_id).all()
            
            results = []
            for command in commands:
                result = process_single_command.apply(args=[command.command_id])
                results.append(result.get())
            
            # Update final batch statistics
            _update_batch_statistics(batch_id)
            
            return {"batch_id": batch_id, "processed": len(results), "results": results}
            
        except Exception as e:
            return {"error": str(e)}


@celery.task
def dispatcher_tick():
    """Periodic task to process pending commands"""
    app = create_app()
    with app.app_context():
        try:
            # Find pending commands
            pending_commands = RemoteCommand.query.filter_by(status='pending').limit(100).all()
            
            processed = 0
            for command in pending_commands:
                process_single_command.delay(command.command_id)
                processed += 1
            
            # Find queued commands with online devices
            queued_commands = db.session.query(RemoteCommand).join(Device).filter(
                RemoteCommand.status == 'queued',
                Device.status == 'online'
            ).limit(50).all()
            
            for command in queued_commands:
                process_single_command.delay(command.command_id)
                processed += 1
            
            return {"processed": processed}
            
        except Exception as e:
            return {"error": str(e)}


@celery.task
def timeout_checker():
    """Check for timed out commands"""
    app = create_app()
    with app.app_context():
        try:
            timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            # Find sent commands that have timed out
            timed_out_commands = RemoteCommand.query.filter(
                RemoteCommand.status == 'sent',
                RemoteCommand.sent_at < timeout_threshold
            ).all()
            
            timeouts_handled = 0
            for command in timed_out_commands:
                if command.attempts < command.max_attempts:
                    # Retry
                    command.status = 'pending'
                    command.attempts += 1
                    command.last_error = "Command timed out, retrying"
                    command.updated_at = datetime.now(timezone.utc)
                    
                    process_single_command.delay(command.command_id)
                else:
                    # Mark as failed
                    command.status = 'fail'
                    command.last_error = "Command timed out after max attempts"
                    command.result_at = datetime.now(timezone.utc)
                    command.updated_at = datetime.now(timezone.utc)
                
                timeouts_handled += 1
            
            db.session.commit()
            
            return {"timeouts_handled": timeouts_handled}
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}


@celery.task
def retry_batch_commands(batch_id, device_ids=None):
    """Retry failed commands in a batch"""
    app = create_app()
    with app.app_context():
        try:
            query = db.session.query(RemoteCommand).filter(
                RemoteCommand.batch_id == batch_id,
                RemoteCommand.status == 'fail',
                RemoteCommand.attempts < RemoteCommand.max_attempts
            )
            
            if device_ids:
                query = query.filter(RemoteCommand.device_id.in_(device_ids))
            
            commands = query.all()
            
            retried = 0
            for command in commands:
                command.status = 'pending'
                command.attempts += 1
                command.last_error = None
                command.updated_at = datetime.now(timezone.utc)
                
                process_single_command.delay(command.command_id)
                retried += 1
            
            db.session.commit()
            
            return {"retried": retried}
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}


def _is_command_supported(device, command_type):
    """Check if device supports the command type"""
    # In a real implementation, this would check device capabilities
    # For now, assume all devices support basic commands
    basic_commands = ['sync', 'restart', 'set_params']
    
    if command_type in basic_commands:
        return True
    
    # Check model-specific support
    if device.model == 'CoffeePro-A':
        return command_type in ['make_product', 'open_door', 'upgrade']
    elif device.model == 'CoffeePro-B':
        return command_type in ['make_product', 'upgrade']
    
    return False


def _update_batch_statistics(batch_id):
    """Update batch statistics"""
    from sqlalchemy import func
    
    batch = CommandBatch.query.get(batch_id)
    if not batch:
        return
    
    stats_query = db.session.query(
        RemoteCommand.status,
        func.count(RemoteCommand.command_id)
    ).filter_by(batch_id=batch_id).group_by(RemoteCommand.status).all()
    
    stats = {
        "total": 0,
        "pending": 0,
        "queued": 0,
        "sent": 0,
        "success": 0,
        "fail": 0,
        "unsupported": 0
    }
    
    for status, count in stats_query:
        stats[status.value] = count
        stats["total"] += count
    
    batch.stats = stats
    batch.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()