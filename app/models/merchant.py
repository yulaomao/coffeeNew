from enum import Enum as PyEnum
from sqlalchemy import Column, String, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class MerchantStatus(PyEnum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class Merchant(BaseModel):
    __tablename__ = 'merchants'
    
    name = Column(String(255), nullable=False)
    contact = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default=MerchantStatus.ACTIVE.value)
    
    # Add constraint for status enum
    __table_args__ = (
        CheckConstraint(
            status.in_([status.value for status in MerchantStatus]),
            name='ck_merchant_status'
        ),
    )
    
    # Relationships
    locations = relationship('Location', back_populates='merchant', lazy='dynamic')
    devices = relationship('Device', back_populates='merchant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Merchant {self.name}>'