from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, JSON, Numeric
from app.extensions import db


class DeviceStatus(Enum):
    REGISTERED = "registered"
    ONLINE = "online"
    OFFLINE = "offline"
    FAULT = "fault"
    MAINTENANCE = "maintenance"


class Device(db.Model):
    __tablename__ = 'devices'
    
    device_id = Column(String(100), primary_key=True)
    alias = Column(String(200))
    model = Column(String(100))
    fw_version = Column(String(50))
    status = Column(SQLEnum(DeviceStatus), nullable=False, default=DeviceStatus.REGISTERED)
    last_seen = Column(DateTime(timezone=True))
    ip = Column(String(50))
    wifi_ssid = Column(String(100))
    temperature = Column(Numeric(5, 2))
    merchant_id = Column(Integer, ForeignKey('merchants.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))
    tags = Column(JSON)
    extra = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    merchant = db.relationship('Merchant', back_populates='devices')
    location = db.relationship('Location', back_populates='devices')
    bins = db.relationship('DeviceBin', back_populates='device', lazy='dynamic')
    orders = db.relationship('Order', back_populates='device', lazy='dynamic')
    commands = db.relationship('RemoteCommand', back_populates='device', lazy='dynamic')
    alarms = db.relationship('Alarm', back_populates='device', lazy='dynamic')
    
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in DeviceStatus])),
    )
    
    def __repr__(self):
        return f'<Device {self.device_id}>'
    
    def to_dict(self):
        return {
            'device_id': self.device_id,
            'alias': self.alias,
            'model': self.model,
            'fw_version': self.fw_version,
            'status': self.status.value if self.status else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'ip': self.ip,
            'wifi_ssid': self.wifi_ssid,
            'temperature': float(self.temperature) if self.temperature else None,
            'merchant_id': self.merchant_id,
            'location_id': self.location_id,
            'tags': self.tags,
            'extra': self.extra,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceBin(db.Model):
    __tablename__ = 'device_bins'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), ForeignKey('devices.device_id'), nullable=False)
    bin_index = Column(Integer, nullable=False)
    material_code = Column(String(50), ForeignKey('material_dictionary.code'))
    remaining = Column(Numeric(10, 2))
    capacity = Column(Numeric(10, 2))
    unit = Column(String(20))
    threshold_low_pct = Column(Numeric(5, 2))
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    device = db.relationship('Device', back_populates='bins')
    material = db.relationship('MaterialDictionary', back_populates='bins')
    
    def __repr__(self):
        return f'<DeviceBin {self.device_id}-{self.bin_index}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'bin_index': self.bin_index,
            'material_code': self.material_code,
            'remaining': float(self.remaining) if self.remaining else None,
            'capacity': float(self.capacity) if self.capacity else None,
            'unit': self.unit,
            'threshold_low_pct': float(self.threshold_low_pct) if self.threshold_low_pct else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }