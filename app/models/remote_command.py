from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class CommandType(PyEnum):
    MAKE_PRODUCT = 'make_product'
    OPEN_DOOR = 'open_door'
    UPGRADE = 'upgrade'
    SYNC = 'sync'
    SET_PARAMS = 'set_params'
    RESTART = 'restart'


class CommandStatus(PyEnum):
    PENDING = 'pending'
    QUEUED = 'queued'
    SENT = 'sent'
    SUCCESS = 'success'
    FAIL = 'fail'
    UNSUPPORTED = 'unsupported'


class RemoteCommand(BaseModel):
    __tablename__ = 'remote_commands'
    
    command_id = Column(String(255), primary_key=True)  # UUID as PK
    device_id = Column(String(255), ForeignKey('devices.device_id'), nullable=False)
    type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default=CommandStatus.PENDING.value)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    result_at = Column(DateTime, nullable=True)
    result_payload = Column(JSON, nullable=True)
    batch_id = Column(String(255), ForeignKey('command_batches.batch_id'), nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    last_error = Column(String(500), nullable=True)
    
    # Add constraints for enum fields
    __table_args__ = (
        CheckConstraint(
            type.in_([cmd_type.value for cmd_type in CommandType]),
            name='ck_command_type'
        ),
        CheckConstraint(
            status.in_([status.value for status in CommandStatus]),
            name='ck_command_status'
        ),
    )
    
    # Relationships
    device = relationship('Device', back_populates='commands')
    batch = relationship('CommandBatch', back_populates='commands')
    
    def __repr__(self):
        return f'<RemoteCommand {self.command_id} {self.type}>'
    
    def is_pending(self):
        """Check if command is pending."""
        return self.status == CommandStatus.PENDING.value
    
    def is_completed(self):
        """Check if command is completed (success or fail)."""
        return self.status in [CommandStatus.SUCCESS.value, CommandStatus.FAIL.value]
    
    def can_retry(self):
        """Check if command can be retried."""
        return self.attempts < self.max_attempts and self.status == CommandStatus.FAIL.value