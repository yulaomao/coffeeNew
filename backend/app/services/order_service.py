from datetime import datetime, timezone
from app.models import Order, OrderItem, OperationLog, TaskJob
from app.extensions import db
import uuid


class OrderService:
    @staticmethod
    def create_order(device_id, order_data):
        """Create a new order from device"""
        # Check if order already exists
        existing_order = Order.query.get(order_data.order_id)
        if existing_order:
            return {
                "order_id": existing_order.order_id,
                "message": "Order already exists"
            }
        
        # Create order
        order = Order(
            order_id=order_data.order_id,
            device_id=device_id,
            device_ts=order_data.device_ts,
            server_ts=datetime.now(timezone.utc),
            items_count=len(order_data.items),
            total_price=order_data.total_price,
            currency=order_data.currency,
            payment_method=order_data.payment_method,
            payment_status=order_data.payment_status,
            is_exception=False,
            address=order_data.address,
            meta=order_data.meta
        )
        
        db.session.add(order)
        
        # Create order items
        for item_data in order_data.items:
            order_item = OrderItem(
                order_id=order_data.order_id,
                product_id=item_data.product_id,
                name=item_data.name,
                qty=item_data.qty,
                unit_price=item_data.unit_price,
                options=item_data.options
            )
            db.session.add(order_item)
        
        # Log the order creation
        log = OperationLog(
            action="order_create",
            target_type="order",
            target_id=order_data.order_id,
            summary=f"Order {order_data.order_id} created from device {device_id}",
            payload_snip={
                "device_id": device_id,
                "total_price": float(order_data.total_price),
                "items_count": len(order_data.items),
                "payment_method": order_data.payment_method.value
            },
            source='device'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return {
            "order_id": order.order_id,
            "message": "Order created successfully"
        }
    
    @staticmethod
    def process_manual_refund(order, reason, note, processed_by):
        """Process manual refund for an order"""
        if order.payment_status.value == 'refunded':
            return {
                "status": "already_refunded",
                "message": "Order already refunded"
            }
        
        # Update order status
        order.payment_status = 'refunded'
        order.updated_at = datetime.now(timezone.utc)
        
        # Add refund information to meta
        if not order.meta:
            order.meta = {}
        
        order.meta.update({
            "refund": {
                "reason": reason,
                "note": note,
                "processed_by": processed_by,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "type": "manual"
            }
        })
        
        # Log the refund
        log = OperationLog(
            action="order_refund",
            target_type="order",
            target_id=order.order_id,
            summary=f"Manual refund processed for order {order.order_id}",
            payload_snip={
                "reason": reason,
                "note": note,
                "amount": float(order.total_price)
            },
            source='backend',
            actor_id=processed_by
        )
        db.session.add(log)
        
        db.session.commit()
        
        return {
            "status": "refunded",
            "message": "Refund processed successfully",
            "refund": {
                "reason": reason,
                "note": note,
                "amount": float(order.total_price)
            }
        }
    
    @staticmethod
    def create_export_task(from_date=None, to_date=None, device_id=None, merchant_id=None, 
                          payment_method=None, payment_status=None, exception_only=False,
                          format_type='csv', created_by=None):
        """Create an async export task"""
        task = TaskJob(
            task_id=str(uuid.uuid4()),
            type='export',
            status='pending',
            progress=0,
            params={
                "export_type": "orders",
                "from_date": from_date,
                "to_date": to_date,
                "device_id": device_id,
                "merchant_id": merchant_id,
                "payment_method": payment_method,
                "payment_status": payment_status,
                "exception_only": exception_only,
                "format": format_type,
                "created_by": created_by
            }
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Queue the export task
        from app.workers.jobs.exports import process_export_task
        process_export_task.delay(task.task_id)
        
        return task
    
    @staticmethod
    def get_order_statistics(device_id=None, merchant_id=None, from_date=None, to_date=None):
        """Get order statistics"""
        query = db.session.query(Order)
        
        if device_id:
            query = query.filter(Order.device_id == device_id)
        
        if merchant_id:
            from app.models import Device
            query = query.join(Device).filter(Device.merchant_id == merchant_id)
        
        if from_date:
            query = query.filter(Order.server_ts >= from_date)
        
        if to_date:
            query = query.filter(Order.server_ts <= to_date)
        
        total_orders = query.count()
        total_revenue = query.with_entities(func.sum(Order.total_price)).scalar() or 0
        exception_orders = query.filter(Order.is_exception == True).count()
        
        # Payment method breakdown
        payment_stats = query.with_entities(
            Order.payment_method,
            func.count(Order.order_id).label('count'),
            func.sum(Order.total_price).label('total')
        ).group_by(Order.payment_method).all()
        
        # Payment status breakdown
        status_stats = query.with_entities(
            Order.payment_status,
            func.count(Order.order_id).label('count')
        ).group_by(Order.payment_status).all()
        
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "exception_orders": exception_orders,
            "exception_rate": exception_orders / total_orders if total_orders > 0 else 0,
            "payment_methods": [
                {
                    "method": stat[0].value if stat[0] else "unknown",
                    "count": stat[1],
                    "total": float(stat[2] or 0)
                }
                for stat in payment_stats
            ],
            "payment_status": [
                {
                    "status": stat[0].value if stat[0] else "unknown",
                    "count": stat[1]
                }
                for stat in status_stats
            ]
        }
    
    @staticmethod
    def mark_order_exception(order_id, reason, details=None):
        """Mark an order as exception"""
        order = Order.query.get(order_id)
        if not order:
            return None
        
        order.is_exception = True
        order.updated_at = datetime.now(timezone.utc)
        
        if not order.meta:
            order.meta = {}
        
        order.meta.update({
            "exception": {
                "reason": reason,
                "details": details,
                "marked_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
        # Log the exception
        log = OperationLog(
            action="order_exception",
            target_type="order",
            target_id=order_id,
            summary=f"Order {order_id} marked as exception: {reason}",
            payload_snip={
                "reason": reason,
                "details": details
            },
            source='backend'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return order