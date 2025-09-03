from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models import BaseModel


class DeviceBin(BaseModel):
    __tablename__ = 'device_bins'
    
    device_id = Column(String(255), ForeignKey('devices.device_id'), nullable=False)
    bin_index = Column(Integer, nullable=False)
    material_code = Column(String(100), ForeignKey('material_dictionaries.code'), nullable=True)
    remaining = Column(Float, nullable=True, default=0.0)
    capacity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    threshold_low_pct = Column(Float, nullable=True, default=20.0)
    last_sync = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship('Device', back_populates='bins')
    material = relationship('MaterialDictionary', back_populates='device_bins')
    
    # Composite unique constraint for device + bin_index
    __table_args__ = (
        {'sqlite_autoincrement': True}  # For SQLite compatibility
    )
    
    def __repr__(self):
        return f'<DeviceBin {self.device_id}:{self.bin_index}>'
    
    def is_low(self):
        """Check if bin material is running low."""
        if not self.capacity or not self.threshold_low_pct:
            return False
        threshold_amount = self.capacity * (self.threshold_low_pct / 100)
        return self.remaining <= threshold_amount
    
    def remaining_percentage(self):
        """Get remaining material as percentage."""
        if not self.capacity or self.capacity == 0:
            return 0
        return (self.remaining / self.capacity) * 100