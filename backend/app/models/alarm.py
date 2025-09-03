from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, JSON
from app.extensions import db


class AlarmType(Enum):
    MATERIAL_LOW = "material_low"
    OFFLINE = "offline"
    UPGRADE_FAIL = "upgrade_fail"
    DISPATCH_FAIL = "dispatch_fail"


class AlarmSeverity(Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


class AlarmStatus(Enum):
    OPEN = "open"
    ACK = "ack"
    CLOSED = "closed"


class Alarm(db.Model):
    __tablename__ = 'alarms'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), ForeignKey('devices.device_id'))
    type = Column(SQLEnum(AlarmType), nullable=False)
    severity = Column(SQLEnum(AlarmSeverity), nullable=False, default=AlarmSeverity.WARN)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    status = Column(SQLEnum(AlarmStatus), nullable=False, default=AlarmStatus.OPEN)
    context = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    device = db.relationship('Device', back_populates='alarms')
    
    __table_args__ = (
        CheckConstraint(type.in_([t.value for t in AlarmType])),
        CheckConstraint(severity.in_([s.value for s in AlarmSeverity])),
        CheckConstraint(status.in_([s.value for s in AlarmStatus])),
    )
    
    def __repr__(self):
        return f'<Alarm {self.id} {self.type.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'type': self.type.value if self.type else None,
            'severity': self.severity.value if self.severity else None,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status else None,
            'context': self.context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }