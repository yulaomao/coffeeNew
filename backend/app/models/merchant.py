from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, CheckConstraint
from app.extensions import db


class MerchantStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Merchant(db.Model):
    __tablename__ = 'merchants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(500))
    status = Column(SQLEnum(MerchantStatus), nullable=False, default=MerchantStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    locations = db.relationship('Location', back_populates='merchant', lazy='dynamic')
    devices = db.relationship('Device', back_populates='merchant', lazy='dynamic')
    
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in MerchantStatus])),
    )
    
    def __repr__(self):
        return f'<Merchant {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }