from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, Float, JSON, CheckConstraint
from app.models import BaseModel


class TaskType(PyEnum):
    EXPORT = 'export'
    PACKAGE = 'package'
    OTHER = 'other'


class TaskStatus(PyEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAIL = 'fail'
    CANCELED = 'canceled'


class TaskJob(BaseModel):
    __tablename__ = 'task_jobs'
    
    task_id = Column(String(255), primary_key=True)  # UUID as PK
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value)
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    result_url = Column(String(500), nullable=True)
    params = Column(JSON, nullable=True)
    error_message = Column(String(1000), nullable=True)
    
    # Add constraints for enum fields
    __table_args__ = (
        CheckConstraint(
            type.in_([task_type.value for task_type in TaskType]),
            name='ck_task_type'
        ),
        CheckConstraint(
            status.in_([status.value for status in TaskStatus]),
            name='ck_task_status'
        ),
        CheckConstraint(
            progress >= 0 and progress <= 100,
            name='ck_task_progress'
        ),
    )
    
    def __repr__(self):
        return f'<TaskJob {self.task_id} {self.type}>'
    
    def is_completed(self):
        """Check if task is completed."""
        return self.status in [TaskStatus.SUCCESS.value, TaskStatus.FAIL.value, TaskStatus.CANCELED.value]
    
    def is_running(self):
        """Check if task is currently running."""
        return self.status == TaskStatus.RUNNING.value