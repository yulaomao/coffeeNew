from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, CheckConstraint, JSON
from app.extensions import db


class TaskType(Enum):
    EXPORT = "export"
    PACKAGE = "package"
    OTHER = "other"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAIL = "fail"
    CANCELED = "canceled"


class TaskJob(db.Model):
    __tablename__ = 'task_jobs'
    
    task_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    result_url = Column(String(500))
    params = Column(JSON)
    error_message = Column(String(1000))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint(type.in_([t.value for t in TaskType])),
        CheckConstraint(status.in_([s.value for s in TaskStatus])),
    )
    
    def __repr__(self):
        return f'<TaskJob {self.task_id} {self.type.value}>'
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'type': self.type.value if self.type else None,
            'status': self.status.value if self.status else None,
            'progress': self.progress,
            'result_url': self.result_url,
            'params': self.params,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }