from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric
from app.extensions import db


class MaterialDictionary(db.Model):
    __tablename__ = 'material_dictionary'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(100))
    unit = Column(String(20))
    density = Column(Numeric(8, 4))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    bins = db.relationship('DeviceBin', back_populates='material', lazy='dynamic')
    
    def __repr__(self):
        return f'<MaterialDictionary {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'unit': self.unit,
            'density': float(self.density) if self.density else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }