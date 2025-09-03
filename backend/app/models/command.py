from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, JSON
from app.extensions import db


class CommandType(Enum):
    MAKE_PRODUCT = "make_product"
    OPEN_DOOR = "open_door"
    UPGRADE = "upgrade"
    SYNC = "sync"
    SET_PARAMS = "set_params"
    RESTART = "restart"


class CommandStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    SUCCESS = "success"
    FAIL = "fail"
    UNSUPPORTED = "unsupported"


class RemoteCommand(db.Model):
    __tablename__ = 'remote_commands'
    
    command_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(100), ForeignKey('devices.device_id'), nullable=False)
    type = Column(SQLEnum(CommandType), nullable=False)
    payload = Column(JSON)
    status = Column(SQLEnum(CommandStatus), nullable=False, default=CommandStatus.PENDING)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime(timezone=True))
    result_at = Column(DateTime(timezone=True))
    result_payload = Column(JSON)
    batch_id = Column(String(36), ForeignKey('command_batches.batch_id'))
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    last_error = Column(String(1000))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    device = db.relationship('Device', back_populates='commands')
    batch = db.relationship('CommandBatch', back_populates='commands')
    
    __table_args__ = (
        CheckConstraint(type.in_([t.value for t in CommandType])),
        CheckConstraint(status.in_([s.value for s in CommandStatus])),
    )
    
    def __repr__(self):
        return f'<RemoteCommand {self.command_id} {self.type.value}>'
    
    def to_dict(self):
        return {
            'command_id': self.command_id,
            'device_id': self.device_id,
            'type': self.type.value if self.type else None,
            'payload': self.payload,
            'status': self.status.value if self.status else None,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'result_at': self.result_at.isoformat() if self.result_at else None,
            'result_payload': self.result_payload,
            'batch_id': self.batch_id,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CommandBatch(db.Model):
    __tablename__ = 'command_batches'
    
    batch_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    command_type = Column(SQLEnum(CommandType), nullable=False)
    payload = Column(JSON)
    note = Column(String(500))
    stats = Column(JSON)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    creator = db.relationship('User', back_populates='created_batches')
    commands = db.relationship('RemoteCommand', back_populates='batch', lazy='dynamic')
    
    __table_args__ = (
        CheckConstraint(command_type.in_([t.value for t in CommandType])),
    )
    
    def __repr__(self):
        return f'<CommandBatch {self.batch_id}>'
    
    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'command_type': self.command_type.value if self.command_type else None,
            'payload': self.payload,
            'note': self.note,
            'stats': self.stats,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }