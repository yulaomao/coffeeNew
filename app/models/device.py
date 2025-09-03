from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class DeviceStatus(PyEnum):
    REGISTERED = 'registered'
    ONLINE = 'online'
    OFFLINE = 'offline'
    FAULT = 'fault'
    MAINTENANCE = 'maintenance'


class Device(BaseModel):
    __tablename__ = 'devices'
    __use_id_pk__ = False
    
    device_id = Column(String(255), primary_key=True)  # Natural primary key
    alias = Column(String(255), nullable=True)
    model = Column(String(100), nullable=True)
    fw_version = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default=DeviceStatus.REGISTERED.value)
    last_seen = Column(DateTime, nullable=True)
    ip = Column(String(45), nullable=True)  # Support IPv6
    wifi_ssid = Column(String(255), nullable=True)
    temperature = Column(Float, nullable=True)
    merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    tags = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)
    
    # Add constraint for status enum  
    __table_args__ = (
        CheckConstraint(
            status.in_([status.value for status in DeviceStatus]),
            name='ck_device_status'
        ),
    )
    
    # Relationships
    merchant = relationship('Merchant', back_populates='devices')
    location = relationship('Location', back_populates='devices')
    bins = relationship('DeviceBin', back_populates='device', lazy='dynamic')
    orders = relationship('Order', back_populates='device', lazy='dynamic')
    commands = relationship('RemoteCommand', back_populates='device', lazy='dynamic')
    alarms = relationship('Alarm', back_populates='device', lazy='dynamic')
    
    def __repr__(self):
        return f'<Device {self.device_id}>'
    
    def is_online(self):
        """Check if device is online."""
        return self.status == DeviceStatus.ONLINE.value
    
    def is_offline(self):
        """Check if device is offline."""
        return self.status == DeviceStatus.OFFLINE.value