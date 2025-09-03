from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from app.extensions import db


class Location(db.Model):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    lat = Column(Numeric(10, 8))  # Latitude with precision
    lng = Column(Numeric(11, 8))  # Longitude with precision
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    merchant = db.relationship('Merchant', back_populates='locations')
    devices = db.relationship('Device', back_populates='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<Location {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'name': self.name,
            'address': self.address,
            'lat': float(self.lat) if self.lat else None,
            'lng': float(self.lng) if self.lng else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }