from datetime import datetime, timezone
import uuid
from app.models import RemoteCommand, CommandBatch, Device, OperationLog
from app.extensions import db
from app.workers.celery_app import celery


class CommandService:
    @staticmethod
    def create_single_command(device_id, command_type, payload=None, max_attempts=5, created_by=None):
        """Create a single command for a device"""
        command = RemoteCommand(
            command_id=str(uuid.uuid4()),
            device_id=device_id,
            type=command_type,
            payload=payload,
            status='pending',
            max_attempts=max_attempts,
            issued_at=datetime.now(timezone.utc)
        )
        
        db.session.add(command)
        
        # Log the operation
        if created_by:
            log = OperationLog(
                action="command_create",
                target_type="command",
                target_id=command.command_id,
                summary=f"Command {command_type} created for device {device_id}",
                payload_snip={
                    "device_id": device_id,
                    "command_type": command_type,
                    "payload": payload
                },
                source='backend',
                actor_id=created_by
            )
            db.session.add(log)
        
        db.session.commit()
        
        # Queue for processing
        CommandService.queue_command_for_dispatch(command.command_id)
        
        return command
    
    @staticmethod
    def create_batch_commands(device_ids, command_type, payload=None, note=None, max_attempts=5, created_by=None):
        """Create a batch of commands for multiple devices"""
        # Create batch record
        batch = CommandBatch(
            batch_id=str(uuid.uuid4()),
            command_type=command_type,
            payload=payload,
            note=note,
            created_by=created_by,
            stats={
                "total": len(device_ids),
                "pending": len(device_ids),
                "queued": 0,
                "sent": 0,
                "success": 0,
                "fail": 0,
                "unsupported": 0
            }
        )
        
        db.session.add(batch)
        
        # Create individual commands
        commands = []
        for device_id in device_ids:
            command = RemoteCommand(
                command_id=str(uuid.uuid4()),
                device_id=device_id,
                type=command_type,
                payload=payload,
                status='pending',
                batch_id=batch.batch_id,
                max_attempts=max_attempts,
                issued_at=datetime.now(timezone.utc)
            )
            commands.append(command)
            db.session.add(command)
        
        # Log the batch operation
        if created_by:
            log = OperationLog(
                action="command_batch_create",
                target_type="command_batch",
                target_id=batch.batch_id,
                summary=f"Batch command {command_type} created for {len(device_ids)} devices",
                payload_snip={
                    "device_count": len(device_ids),
                    "command_type": command_type,
                    "note": note
                },
                source='backend',
                actor_id=created_by
            )
            db.session.add(log)
        
        db.session.commit()
        
        # Queue batch for processing
        CommandService.queue_batch_for_dispatch(batch.batch_id)
        
        return batch, commands
    
    @staticmethod
    def update_command_result(command_id, status, result_payload=None, error_message=None):
        """Update command execution result"""
        command = RemoteCommand.query.get(command_id)
        if not command:
            return None
        
        command.status = status
        command.result_at = datetime.now(timezone.utc)
        command.result_payload = result_payload
        
        if error_message:
            command.last_error = error_message
        
        command.updated_at = datetime.now(timezone.utc)
        
        # Update batch statistics if part of a batch
        if command.batch_id:
            CommandService.update_batch_statistics(command.batch_id)
        
        # Log the result
        log = OperationLog(
            action="command_result",
            target_type="command",
            target_id=command_id,
            summary=f"Command {command.type.value} completed with status {status}",
            payload_snip={
                "device_id": command.device_id,
                "status": status,
                "error_message": error_message
            },
            source='device'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return command
    
    @staticmethod
    def update_batch_statistics(batch_id):
        """Update batch statistics based on command statuses"""
        batch = CommandBatch.query.get(batch_id)
        if not batch:
            return
        
        # Count commands by status
        from sqlalchemy import func
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
    
    @staticmethod
    def retry_failed_commands(batch_id, device_ids=None):
        """Retry failed commands in a batch"""
        query = db.session.query(RemoteCommand).filter(
            RemoteCommand.batch_id == batch_id,
            RemoteCommand.status == 'fail',
            RemoteCommand.attempts < RemoteCommand.max_attempts
        )
        
        if device_ids:
            query = query.filter(RemoteCommand.device_id.in_(device_ids))
        
        commands = query.all()
        
        for command in commands:
            command.status = 'pending'
            command.attempts += 1
            command.last_error = None
            command.updated_at = datetime.now(timezone.utc)
            
            # Queue for retry
            CommandService.queue_command_for_dispatch(command.command_id)
        
        # Update batch statistics
        CommandService.update_batch_statistics(batch_id)
        
        db.session.commit()
        
        return len(commands)
    
    @staticmethod
    def queue_command_for_dispatch(command_id):
        """Queue individual command for dispatch processing"""
        from app.workers.jobs.dispatch import process_single_command
        process_single_command.delay(command_id)
    
    @staticmethod
    def queue_batch_for_dispatch(batch_id):
        """Queue batch for dispatch processing"""
        from app.workers.jobs.dispatch import process_command_batch
        process_command_batch.delay(batch_id)
    
    @staticmethod
    def get_pending_commands_for_device(device_id):
        """Get pending/queued commands for a device"""
        commands = db.session.query(RemoteCommand).filter(
            RemoteCommand.device_id == device_id,
            RemoteCommand.status.in_(['pending', 'queued'])
        ).order_by(RemoteCommand.issued_at).all()
        
        return commands
    
    @staticmethod
    def mark_command_sent(command_id):
        """Mark command as sent to device"""
        command = RemoteCommand.query.get(command_id)
        if command:
            command.status = 'sent'
            command.sent_at = datetime.now(timezone.utc)
            command.updated_at = datetime.now(timezone.utc)
            
            # Update batch statistics if needed
            if command.batch_id:
                CommandService.update_batch_statistics(command.batch_id)
            
            db.session.commit()
        
        return command
    
    @staticmethod
    def check_command_timeout(command_id, timeout_seconds=300):
        """Check if command has timed out"""
        command = RemoteCommand.query.get(command_id)
        if not command:
            return False
        
        if command.status not in ['sent']:
            return False
        
        now = datetime.now(timezone.utc)
        sent_time = command.sent_at or command.issued_at
        
        return (now - sent_time).total_seconds() > timeout_seconds
    
    @staticmethod
    def handle_command_timeout(command_id):
        """Handle command timeout - retry or mark as failed"""
        command = RemoteCommand.query.get(command_id)
        if not command:
            return None
        
        if command.attempts < command.max_attempts:
            # Retry
            command.status = 'pending'
            command.attempts += 1
            command.last_error = "Command timed out"
            command.updated_at = datetime.now(timezone.utc)
            
            CommandService.queue_command_for_dispatch(command_id)
        else:
            # Mark as failed
            command.status = 'fail'
            command.last_error = "Command timed out after max attempts"
            command.result_at = datetime.now(timezone.utc)
            command.updated_at = datetime.now(timezone.utc)
            
            # Update batch statistics if needed
            if command.batch_id:
                CommandService.update_batch_statistics(command.batch_id)
        
        db.session.commit()
        
        return command