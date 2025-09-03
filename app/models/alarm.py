from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class AlarmType(PyEnum):
    MATERIAL_LOW = 'material_low'
    OFFLINE = 'offline'
    UPGRADE_FAIL = 'upgrade_fail'
    DISPATCH_FAIL = 'dispatch_fail'


class AlarmSeverity(PyEnum):
    INFO = 'info'
    WARN = 'warn'
    CRITICAL = 'critical'


class AlarmStatus(PyEnum):
    OPEN = 'open'
    ACK = 'ack'
    CLOSED = 'closed'


class Alarm(BaseModel):
    __tablename__ = 'alarms'
    
    device_id = Column(String(255), ForeignKey('devices.device_id'), nullable=False)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default=AlarmStatus.OPEN.value)
    context = Column(JSON, nullable=True)
    
    # Add constraints for enum fields
    __table_args__ = (
        CheckConstraint(
            type.in_([alarm_type.value for alarm_type in AlarmType]),
            name='ck_alarm_type'
        ),
        CheckConstraint(
            severity.in_([severity.value for severity in AlarmSeverity]),
            name='ck_alarm_severity'
        ),
        CheckConstraint(
            status.in_([status.value for status in AlarmStatus]),
            name='ck_alarm_status'
        ),
    )
    
    # Relationships
    device = relationship('Device', back_populates='alarms')
    
    def __repr__(self):
        return f'<Alarm {self.type} {self.severity}>'
    
    def is_open(self):
        """Check if alarm is open."""
        return self.status == AlarmStatus.OPEN.value
    
    def is_critical(self):
        """Check if alarm is critical."""
        return self.severity == AlarmSeverity.CRITICAL.value