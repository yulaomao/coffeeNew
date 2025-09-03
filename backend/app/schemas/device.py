from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DeviceStatus(str, Enum):
    REGISTERED = "registered"
    ONLINE = "online"
    OFFLINE = "offline"
    FAULT = "fault"
    MAINTENANCE = "maintenance"


class DeviceLocation(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    firmware_version: str = Field(..., max_length=50)
    serial: Optional[str] = Field(None, max_length=100)
    mac: Optional[str] = Field(None, max_length=50)
    location: Optional[DeviceLocation] = None
    address: Optional[str] = Field(None, max_length=500)


class DeviceStatusRequest(BaseModel):
    status: DeviceStatus
    timestamp: datetime
    ip: Optional[str] = Field(None, max_length=50)
    wifi_ssid: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class MaterialReport(BaseModel):
    bin_index: int = Field(..., ge=0)
    material_code: str = Field(..., max_length=50)
    remaining: float = Field(..., ge=0)
    capacity: float = Field(..., ge=0)
    unit: str = Field(..., max_length=20)


class MaterialsReportRequest(BaseModel):
    timestamp: datetime
    materials: List[MaterialReport]


class DeviceResponse(BaseModel):
    device_id: str
    alias: Optional[str]
    model: Optional[str]
    fw_version: Optional[str]
    status: Optional[str]
    last_seen: Optional[datetime]
    ip: Optional[str]
    wifi_ssid: Optional[str]
    temperature: Optional[float]
    merchant_id: Optional[int]
    location_id: Optional[int]
    tags: Optional[Dict[str, Any]]
    extra: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class DeviceSummaryResponse(BaseModel):
    device: DeviceResponse
    online_rate: float
    orders_today: int
    orders_week: int
    alarms_open: int
    materials_low: int


class DeviceBinResponse(BaseModel):
    id: int
    device_id: str
    bin_index: int
    material_code: Optional[str]
    remaining: Optional[float]
    capacity: Optional[float]
    unit: Optional[str]
    threshold_low_pct: Optional[float]
    last_sync: Optional[datetime]
    is_low: bool = False


class BinBindRequest(BaseModel):
    material_code: str = Field(..., max_length=50)
    capacity: float = Field(..., gt=0)
    unit: str = Field(..., max_length=20)
    threshold_low_pct: float = Field(..., ge=0, le=100)


class CommandRequest(BaseModel):
    type: str = Field(..., max_length=50)
    payload: Optional[Dict[str, Any]] = None
    max_attempts: Optional[int] = Field(5, ge=1, le=10)