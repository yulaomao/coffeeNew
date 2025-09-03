from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class OperationSource(PyEnum):
    BACKEND = 'backend'
    API = 'api'
    DEVICE = 'device'


class OperationLog(BaseModel):
    __tablename__ = 'operation_logs'
    
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=False)
    payload_snip = Column(JSON, nullable=True)  # Snippet of payload for audit
    source = Column(String(20), nullable=False)
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Nullable for device operations
    ip = Column(String(45), nullable=True)  # Support IPv6
    
    # Add constraint for source enum
    __table_args__ = (
        CheckConstraint(
            source.in_([source.value for source in OperationSource]),
            name='ck_operation_source'
        ),
    )
    
    # Relationships
    actor = relationship('User', back_populates='operation_logs')
    
    def __repr__(self):
        return f'<OperationLog {self.action} on {self.target_type}:{self.target_id}>'