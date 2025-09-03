from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Boolean, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class PaymentMethod(PyEnum):
    WECHAT = 'wechat'
    ALIPAY = 'alipay'
    CARD = 'card'
    CORP = 'corp'


class PaymentStatus(PyEnum):
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'
    REFUND_FAILED = 'refund_failed'


class Order(BaseModel):
    __tablename__ = 'orders'
    __use_id_pk__ = False
    
    order_id = Column(String(255), primary_key=True)  # Natural primary key
    device_id = Column(String(255), ForeignKey('devices.device_id'), nullable=False)
    device_ts = Column(DateTime, nullable=True)  # Timestamp from device
    server_ts = Column(DateTime, default=datetime.utcnow, nullable=False)  # Server timestamp
    items_count = Column(Integer, nullable=False, default=0)
    total_price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default='CNY')
    payment_method = Column(String(20), nullable=False)
    payment_status = Column(String(20), nullable=False, default=PaymentStatus.UNPAID.value)
    is_exception = Column(Boolean, default=False, nullable=False)
    address = Column(String(500), nullable=True)
    meta = Column(JSON, nullable=True)
    
    # Add constraints for enum fields
    __table_args__ = (
        CheckConstraint(
            payment_method.in_([method.value for method in PaymentMethod]),
            name='ck_order_payment_method'
        ),
        CheckConstraint(
            payment_status.in_([status.value for status in PaymentStatus]),
            name='ck_order_payment_status'
        ),
    )
    
    # Relationships
    device = relationship('Device', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', lazy='dynamic')
    
    def __repr__(self):
        return f'<Order {self.order_id}>'
    
    def is_paid(self):
        """Check if order is paid."""
        return self.payment_status == PaymentStatus.PAID.value
    
    def is_refunded(self):
        """Check if order is refunded."""
        return self.payment_status == PaymentStatus.REFUNDED.value