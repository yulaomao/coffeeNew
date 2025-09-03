from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models import BaseModel


class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    # Uses default id PK from BaseModel
    
    order_id = Column(String(255), ForeignKey('orders.order_id'), nullable=False)
    product_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    qty = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    options = Column(JSON, nullable=True)
    
    # Relationships
    order = relationship('Order', back_populates='items')
    
    def __repr__(self):
        return f'<OrderItem {self.name} x{self.qty}>'
    
    def total_price(self):
        """Calculate total price for this item."""
        return self.qty * self.unit_price