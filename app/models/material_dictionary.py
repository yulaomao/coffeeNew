from sqlalchemy import Column, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.models import BaseModel


class MaterialDictionary(BaseModel):
    __tablename__ = 'material_dictionaries'
    
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    unit = Column(String(20), nullable=True)
    density = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    device_bins = relationship('DeviceBin', back_populates='material', lazy='dynamic')
    
    def __repr__(self):
        return f'<MaterialDictionary {self.code}: {self.name}>'