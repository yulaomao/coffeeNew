from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, JSON, Numeric, Boolean
from app.extensions import db


class PaymentMethod(Enum):
    WECHAT = "wechat"
    ALIPAY = "alipay"
    CARD = "card"
    CORP = "corp"


class PaymentStatus(Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"
    REFUND_FAILED = "refund_failed"


class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = Column(String(100), primary_key=True)
    device_id = Column(String(100), ForeignKey('devices.device_id'), nullable=False)
    device_ts = Column(DateTime(timezone=True))
    server_ts = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items_count = Column(Integer)
    total_price = Column(Numeric(10, 2))
    currency = Column(String(10), default='CNY')
    payment_method = Column(SQLEnum(PaymentMethod))
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.UNPAID)
    is_exception = Column(Boolean, default=False)
    address = Column(String(500))
    meta = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    device = db.relationship('Device', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy='dynamic')
    
    __table_args__ = (
        CheckConstraint(payment_method.in_([p.value for p in PaymentMethod])),
        CheckConstraint(payment_status.in_([p.value for p in PaymentStatus])),
    )
    
    def __repr__(self):
        return f'<Order {self.order_id}>'
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'device_id': self.device_id,
            'device_ts': self.device_ts.isoformat() if self.device_ts else None,
            'server_ts': self.server_ts.isoformat() if self.server_ts else None,
            'items_count': self.items_count,
            'total_price': float(self.total_price) if self.total_price else None,
            'currency': self.currency,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'payment_status': self.payment_status.value if self.payment_status else None,
            'is_exception': self.is_exception,
            'address': self.address,
            'meta': self.meta,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), ForeignKey('orders.order_id'), nullable=False)
    product_id = Column(String(100))
    name = Column(String(200), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    options = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    
    def __repr__(self):
        return f'<OrderItem {self.order_id}-{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'name': self.name,
            'qty': self.qty,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'options': self.options,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }