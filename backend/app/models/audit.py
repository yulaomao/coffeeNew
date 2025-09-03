from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, JSON
from app.extensions import db


class SourceType(Enum):
    BACKEND = "backend"
    API = "api"
    DEVICE = "device"


class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100))
    target_id = Column(String(100))
    summary = Column(String(500))
    payload_snip = Column(JSON)
    source = Column(SQLEnum(SourceType), nullable=False, default=SourceType.BACKEND)
    actor_id = Column(Integer, ForeignKey('users.id'))  # nullable for device operations
    ip = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    actor = db.relationship('User', back_populates='audit_logs')
    
    __table_args__ = (
        CheckConstraint(source.in_([s.value for s in SourceType])),
    )
    
    def __repr__(self):
        return f'<OperationLog {self.id} {self.action}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'summary': self.summary,
            'payload_snip': self.payload_snip,
            'source': self.source.value if self.source else None,
            'actor_id': self.actor_id,
            'ip': self.ip,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }