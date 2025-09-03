from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


class PaymentMethod(str, Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CARD = "card"
    CORP = "corp"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"
    REFUND_FAILED = "refund_failed"


class OrderItem(BaseModel):
    product_id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    qty: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    options: Optional[Dict[str, Any]] = None


class OrderCreateRequest(BaseModel):
    order_id: str = Field(..., max_length=100)
    device_ts: datetime
    items: List[OrderItem]
    total_price: Decimal = Field(..., ge=0)
    currency: str = Field("CNY", max_length=10)
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    address: Optional[str] = Field(None, max_length=500)
    meta: Optional[Dict[str, Any]] = None
    
    @validator('items')
    def items_not_empty(cls, v):
        if not v:
            raise ValueError('Items list cannot be empty')
        return v


class OrderResponse(BaseModel):
    order_id: str
    device_id: str
    device_ts: Optional[datetime]
    server_ts: Optional[datetime]
    items_count: Optional[int]
    total_price: Optional[Decimal]
    currency: Optional[str]
    payment_method: Optional[str]
    payment_status: Optional[str]
    is_exception: Optional[bool]
    address: Optional[str]
    meta: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class OrderItemResponse(BaseModel):
    id: int
    order_id: str
    product_id: Optional[str]
    name: str
    qty: int
    unit_price: Optional[Decimal]
    options: Optional[Dict[str, Any]]


class OrderDetailResponse(BaseModel):
    order: OrderResponse
    items: List[OrderItemResponse]


class ManualRefundRequest(BaseModel):
    reason: str = Field(..., max_length=200)
    note: Optional[str] = Field(None, max_length=500)


class ExportRequest(BaseModel):
    format: str = Field("csv", regex="^(csv|xlsx)$")
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    device_id: Optional[str] = None
    merchant_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    payment_status: Optional[PaymentStatus] = None
    exception_only: Optional[bool] = False