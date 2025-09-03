from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models import BaseModel


class Location(BaseModel):
    __tablename__ = 'locations'
    
    merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Relationships
    merchant = relationship('Merchant', back_populates='locations')
    devices = relationship('Device', back_populates='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<Location {self.name}>'