import uuid
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from loguru import logger
from ..storage.db import db
from ..storage.models import Order, OrderItem, OrderStatus, PaymentStatus
from ..storage.queue import upload_queue
from ..config import config
from ..utils.time import utc_now
from ..utils.sse import event_bus, EVENT_ORDER_CREATED, EVENT_ORDER_STATUS_CHANGED, EVENT_PAYMENT_STATUS_CHANGED
from ..payment.mock_wechat import mock_wechat
from ..payment.mock_alipay import mock_alipay
from .materials import material_manager
from .recipes import recipe_manager

class OrderManager:
    """Manages order lifecycle, payment integration, and backend reporting"""
    
    def __init__(self):
        self.current_order: Optional[Order] = None
        self.payment_providers = {
            "wechat": mock_wechat,
            "alipay": mock_alipay
        }
    
    async def create_order(self, items: list, payment_method: str = "wechat", is_test: bool = False) -> Order:
        """Create new order"""
        order_id = f"ORD_{config.DEVICE_ID}_{int(utc_now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Convert items to OrderItem objects
        order_items = []
        total_price = 0.0
        
        for item_data in items:
            recipe_id = item_data["recipe_id"]
            quantity = item_data.get("quantity", 1)
            options = item_data.get("options", {})
            
            # Get recipe info
            recipe = recipe_manager.get_recipe_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe {recipe_id} not found")
            
            order_item = OrderItem(
                recipe_id=recipe_id,
                recipe_name=recipe.name,
                price=recipe.price,
                quantity=quantity,
                options=options
            )
            
            order_items.append(order_item)
            total_price += recipe.price * quantity
        
        # Create order
        order = Order(
            order_id=order_id,
            items=order_items,
            total_price=total_price,
            payment_method=payment_method,
            payment_status=PaymentStatus.PENDING,
            status=OrderStatus.PENDING,
            created_at=utc_now(),
            is_test=is_test,
            device_id=config.DEVICE_ID
        )
        
        # Save order
        db.save_order(order)
        self.current_order = order
        
        logger.info(f"Created order {order_id} with {len(order_items)} items, total: ¥{total_price:.2f}")
        
        # Emit event
        event_bus.emit(EVENT_ORDER_CREATED, {
            "order_id": order_id,
            "total_price": total_price,
            "item_count": len(order_items)
        })
        
        return order
    
    async def create_payment(self, order_id: str, payment_method: str = "wechat", expires_in_s: int = 300):
        """Create payment for order"""
        order = db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.payment_status != PaymentStatus.PENDING:
            raise ValueError(f"Order {order_id} payment status is {order.payment_status}")
        
        provider = self.payment_providers.get(payment_method)
        if not provider:
            raise ValueError(f"Payment method {payment_method} not supported")
        
        # Create payment QR
        payment_qr = await provider.create_qr(
            amount=order.total_price,
            order_id=order_id,
            expires_in_s=expires_in_s
        )
        
        logger.info(f"Created {payment_method} payment for order {order_id}, amount: ¥{order.total_price:.2f}")
        
        return payment_qr
    
    async def poll_payment_status(self, order_id: str) -> Dict[str, Any]:
        """Poll payment status"""
        order = db.get_order(order_id)
        if not order:
            return {"status": "error", "message": "Order not found"}
        
        provider = self.payment_providers.get(order.payment_method)
        if not provider:
            return {"status": "error", "message": "Payment provider not found"}
        
        # Poll payment status
        payment_status = await provider.poll(order_id)
        
        # Update order if payment status changed
        if payment_status.status == "paid" and order.payment_status != PaymentStatus.PAID:
            order.payment_status = PaymentStatus.PAID
            order.payment_txn_id = payment_status.txn_id
            order.status = OrderStatus.PAID
            
            db.save_order(order)
            
            logger.info(f"Payment completed for order {order_id}, txn_id: {payment_status.txn_id}")
            
            # Emit payment success event
            event_bus.emit(EVENT_PAYMENT_STATUS_CHANGED, {
                "order_id": order_id,
                "status": "paid",
                "txn_id": payment_status.txn_id
            })
        
        elif payment_status.status in ["failed", "canceled"] and order.payment_status == PaymentStatus.PENDING:
            if payment_status.status == "failed":
                order.payment_status = PaymentStatus.FAILED
            else:
                order.payment_status = PaymentStatus.CANCELED
            
            order.status = OrderStatus.CANCELED
            db.save_order(order)
            
            logger.info(f"Payment {payment_status.status} for order {order_id}: {payment_status.reason}")
            
            # Emit payment failure event
            event_bus.emit(EVENT_PAYMENT_STATUS_CHANGED, {
                "order_id": order_id,
                "status": payment_status.status,
                "reason": payment_status.reason
            })
        
        return {
            "status": payment_status.status,
            "txn_id": payment_status.txn_id,
            "reason": payment_status.reason,
            "amount": payment_status.amount
        }
    
    async def cancel_payment(self, order_id: str) -> bool:
        """Cancel payment"""
        order = db.get_order(order_id)
        if not order:
            return False
        
        provider = self.payment_providers.get(order.payment_method)
        if not provider:
            return False
        
        # Cancel payment
        result = await provider.cancel(order_id)
        
        if result.get("ok"):
            order.payment_status = PaymentStatus.CANCELED
            order.status = OrderStatus.CANCELED
            db.save_order(order)
            
            logger.info(f"Canceled payment for order {order_id}")
            
            event_bus.emit(EVENT_PAYMENT_STATUS_CHANGED, {
                "order_id": order_id,
                "status": "canceled"
            })
            
            return True
        
        return False
    
    async def start_brewing(self, order_id: str, progress_callback: Optional[Callable[[str, float], None]] = None) -> bool:
        """Start brewing process for paid order"""
        order = db.get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return False
        
        if order.payment_status != PaymentStatus.PAID:
            logger.error(f"Order {order_id} not paid, status: {order.payment_status}")
            return False
        
        if order.status != OrderStatus.PAID:
            logger.error(f"Order {order_id} not ready for brewing, status: {order.status}")
            return False
        
        # Update order status
        order.status = OrderStatus.BREWING
        db.save_order(order)
        
        event_bus.emit(EVENT_ORDER_STATUS_CHANGED, {
            "order_id": order_id,
            "status": "brewing"
        })
        
        logger.info(f"Starting brewing for order {order_id}")
        
        try:
            # Process each item in order
            for item in order.items:
                recipe = recipe_manager.get_recipe_by_id(item.recipe_id)
                if not recipe:
                    raise Exception(f"Recipe {item.recipe_id} not found")
                
                # Check material availability
                availability = material_manager.check_recipe_availability(recipe.materials)
                if not all(availability.values()):
                    insufficient = [mat for mat, avail in availability.items() if not avail]
                    raise Exception(f"Insufficient materials: {', '.join(insufficient)}")
                
                # Import HAL here to avoid circular imports
                from ..hal.simulator import simulator
                
                # Start brewing
                result = await simulator.brew_coffee(
                    recipe=recipe.model_dump(),
                    progress_callback=progress_callback
                )
                
                if not result.get("success"):
                    raise Exception(f"Brewing failed: {result.get('error')}")
                
                # Consume materials
                consumed = result.get("consumed", {})
                material_manager.consume_materials(consumed)
            
            # Mark order as completed
            order.status = OrderStatus.COMPLETED
            order.completed_at = utc_now()
            db.save_order(order)
            
            logger.info(f"Completed brewing for order {order_id}")
            
            event_bus.emit(EVENT_ORDER_STATUS_CHANGED, {
                "order_id": order_id,
                "status": "completed"
            })
            
            # Queue for backend reporting
            await self._queue_order_for_upload(order)
            
            return True
        
        except Exception as e:
            logger.error(f"Brewing failed for order {order_id}: {e}")
            
            # Mark order as failed
            order.status = OrderStatus.FAILED
            order.is_exception = True
            db.save_order(order)
            
            event_bus.emit(EVENT_ORDER_STATUS_CHANGED, {
                "order_id": order_id,
                "status": "failed",
                "error": str(e)
            })
            
            return False
    
    async def _queue_order_for_upload(self, order: Order):
        """Queue completed order for backend upload"""
        try:
            order_data = {
                "order_id": order.order_id,
                "items": [item.model_dump() for item in order.items],
                "total_price": order.total_price,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "payment_txn_id": order.payment_txn_id,
                "is_test": order.is_test
            }
            
            await upload_queue.add_order(order_data, order.order_id)
            logger.info(f"Queued order {order.order_id} for backend upload")
        
        except Exception as e:
            logger.error(f"Failed to queue order for upload: {e}")
    
    def get_current_order(self) -> Optional[Order]:
        """Get current active order"""
        return self.current_order
    
    def clear_current_order(self):
        """Clear current order"""
        self.current_order = None
    
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return db.get_order(order_id)
    
    def get_recent_orders(self, limit: int = 10) -> list:
        """Get recent orders"""
        # This would require additional database query methods
        return []
    
    async def create_test_order(self, recipe_id: int) -> Order:
        """Create test order for maintenance/demo"""
        items = [{
            "recipe_id": recipe_id,
            "quantity": 1,
            "options": {}
        }]
        
        order = await self.create_order(items, payment_method="test", is_test=True)
        
        # Automatically mark as paid for test orders
        order.payment_status = PaymentStatus.PAID
        order.status = OrderStatus.PAID
        order.payment_txn_id = f"test_{int(utc_now().timestamp())}"
        
        db.save_order(order)
        
        return order
    
    def simulate_payment_success(self, order_id: str, payment_method: str = "wechat") -> bool:
        """Manually trigger payment success for testing"""
        provider = self.payment_providers.get(payment_method)
        if provider and hasattr(provider, 'simulate_payment_success'):
            return provider.simulate_payment_success(order_id)
        return False
    
    def get_order_summary(self) -> Dict[str, Any]:
        """Get order summary for UI"""
        # This would require additional database queries
        return {
            "total_orders_today": 0,
            "completed_orders_today": 0,
            "failed_orders_today": 0,
            "revenue_today": 0.0,
            "current_order": self.current_order.order_id if self.current_order else None
        }

# Global order manager
order_manager = OrderManager()