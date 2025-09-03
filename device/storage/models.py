from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from ..constants import *

# Enums for type safety
class DeviceStatus(str, Enum):
    IDLE = DEVICE_STATUS_IDLE
    BREWING = DEVICE_STATUS_BREWING
    MAINTENANCE = DEVICE_STATUS_MAINTENANCE
    OUT_OF_SERVICE = DEVICE_STATUS_OUT_OF_SERVICE
    ERROR = DEVICE_STATUS_ERROR

class CommandStatus(str, Enum):
    PENDING = COMMAND_STATUS_PENDING
    SENT = COMMAND_STATUS_SENT
    SUCCESS = COMMAND_STATUS_SUCCESS
    FAIL = COMMAND_STATUS_FAIL

class PaymentStatus(str, Enum):
    PENDING = PAYMENT_STATUS_PENDING
    PAID = PAYMENT_STATUS_PAID
    FAILED = PAYMENT_STATUS_FAILED
    CANCELED = PAYMENT_STATUS_CANCELED

class OrderStatus(str, Enum):
    PENDING = ORDER_STATUS_PENDING
    PAID = ORDER_STATUS_PAID
    BREWING = ORDER_STATUS_BREWING
    COMPLETED = ORDER_STATUS_COMPLETED
    FAILED = ORDER_STATUS_FAILED
    CANCELED = ORDER_STATUS_CANCELED

# Data models
class DeviceState(BaseModel):
    device_id: str
    status: DeviceStatus
    temperature: Optional[float] = None
    wifi_ssid: Optional[str] = None
    wifi_signal: Optional[int] = None
    ip: Optional[str] = None
    firmware_version: str = "1.0.0"
    uptime_seconds: int = 0
    last_seen: datetime
    is_online: bool = True

class Bin(BaseModel):
    bin_index: int
    material_code: str
    remaining: float
    capacity: float
    unit: str
    threshold_low_pct: int = 20
    last_updated: datetime

    def is_low(self) -> bool:
        """Check if material is low"""
        if self.capacity <= 0:
            return True
        return (self.remaining / self.capacity * 100) <= self.threshold_low_pct
    
    def is_sufficient(self, required: float) -> bool:
        """Check if sufficient material for required amount"""
        return self.remaining >= required

class RecipeStep(BaseModel):
    action: str
    bin: Optional[str] = None
    amount: Optional[float] = None
    unit: Optional[str] = None
    water_ml: Optional[int] = None
    duration_ms: int = 1000

class Recipe(BaseModel):
    id: int
    name: str
    price: float
    steps: List[RecipeStep]
    materials: Dict[str, float]  # material_code -> required_amount
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True
    temperature: str = "hot"  # hot, cold, both

class OrderItem(BaseModel):
    recipe_id: int
    recipe_name: str
    price: float
    quantity: int = 1
    options: Dict[str, Any] = Field(default_factory=dict)

class Order(BaseModel):
    order_id: str
    items: List[OrderItem]
    total_price: float
    payment_method: Optional[str] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_txn_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime
    completed_at: Optional[datetime] = None
    is_test: bool = False
    is_exception: bool = False
    device_id: str

class Command(BaseModel):
    command_id: str
    device_id: str
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: CommandStatus = CommandStatus.PENDING
    issued_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

class QueueItem(BaseModel):
    id: Optional[int] = None
    item_type: str  # "order", "command_result", "status", "material"
    item_id: str
    payload: Dict[str, Any]
    created_at: datetime
    retry_count: int = 0
    last_error: Optional[str] = None
    max_retries: int = 3

class RecipePackage(BaseModel):
    package_id: str
    version: str
    download_url: str
    md5_hash: str
    downloaded_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    is_active: bool = False

class OperationLog(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    operation: str
    user: str = "system"
    details: Dict[str, Any] = Field(default_factory=dict)
    device_id: str

class PaymentQR(BaseModel):
    order_id: str
    qr_data: str
    amount: float
    channel: str = "wechat"
    expires_at: datetime
    created_at: datetime