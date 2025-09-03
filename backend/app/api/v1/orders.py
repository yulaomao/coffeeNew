from flask import request
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_, or_
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.api.decorators import validate_json, require_device_token, require_role
from app.schemas.order import OrderCreateRequest, ManualRefundRequest, ExportRequest
from app.models import Order, OrderItem, Device
from app.extensions import db
from app.services.order_service import OrderService
from app.utils.idempotency import get_idempotency_key, is_duplicate_request, mark_request_processed


@bp.route('/orders', methods=['GET'])
@login_required
def list_orders():
    """List orders with filtering and pagination"""
    try:
        # Get query parameters
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        device_id = request.args.get('device_id')
        merchant_id = request.args.get('merchant_id', type=int)
        payment_method = request.args.get('payment_method')
        product_id = request.args.get('product_id')
        exception = request.args.get('exception', type=bool)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # Build query
        query = db.session.query(Order)
        
        # Apply filters
        if from_date:
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            query = query.filter(Order.server_ts >= from_dt)
        
        if to_date:
            to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            query = query.filter(Order.server_ts <= to_dt)
        
        if device_id:
            query = query.filter(Order.device_id == device_id)
        
        if merchant_id:
            query = query.join(Device).filter(Device.merchant_id == merchant_id)
        
        if payment_method:
            query = query.filter(Order.payment_method == payment_method)
        
        if product_id:
            query = query.join(OrderItem).filter(OrderItem.product_id == product_id)
        
        if exception is not None:
            query = query.filter(Order.is_exception == exception)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        orders = query.order_by(Order.server_ts.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to response format
        order_data = [order.to_dict() for order in orders]
        
        return paginated_response(order_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list orders: {str(e)}",
            status_code=500
        )


@bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order details"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return error_response(
                ErrorCode.ORDER_NOT_FOUND,
                "Order not found",
                status_code=404
            )
        
        # Get order items
        items = OrderItem.query.filter_by(order_id=order_id).all()
        
        return success_response({
            "order": order.to_dict(),
            "items": [item.to_dict() for item in items]
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get order: {str(e)}",
            status_code=500
        )


@bp.route('/orders/<order_id>/manual_refund', methods=['POST'])
@login_required
@validate_json(ManualRefundRequest)
@require_role(['admin', 'ops'])
def manual_refund_order(order_id):
    """Process manual refund for order"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return error_response(
                ErrorCode.ORDER_NOT_FOUND,
                "Order not found",
                status_code=404
            )
        
        if order.payment_status.value not in ['paid']:
            return error_response(
                ErrorCode.REFUND_NOT_ALLOWED,
                "Order cannot be refunded",
                status_code=400
            )
        
        refund_data = request.validated_json
        
        # Process refund using order service
        result = OrderService.process_manual_refund(
            order=order,
            reason=refund_data.reason,
            note=refund_data.note,
            processed_by=current_user.id
        )
        
        return success_response(result)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to process refund: {str(e)}",
            status_code=500
        )


@bp.route('/orders/export', methods=['GET'])
@login_required
@require_role(['admin', 'ops'])
def export_orders():
    """Export orders (async task)"""
    try:
        # Get export parameters
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        device_id = request.args.get('device_id')
        merchant_id = request.args.get('merchant_id', type=int)
        payment_method = request.args.get('payment_method')
        payment_status = request.args.get('payment_status')
        exception_only = request.args.get('exception_only', type=bool, default=False)
        format_type = request.args.get('format', 'csv')
        
        # Create export task
        task = OrderService.create_export_task(
            from_date=from_date,
            to_date=to_date,
            device_id=device_id,
            merchant_id=merchant_id,
            payment_method=payment_method,
            payment_status=payment_status,
            exception_only=exception_only,
            format_type=format_type,
            created_by=current_user.id
        )
        
        return success_response({
            "task_id": task.task_id,
            "message": "Export task created"
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to create export task: {str(e)}",
            status_code=500
        )


# Device API endpoint for order creation
@bp.route('/devices/<device_id>/orders/create', methods=['POST'])
@require_device_token()
@validate_json(OrderCreateRequest)
def create_order(device_id):
    """Create new order from device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        order_data = request.validated_json
        
        # Check for idempotency
        idempotency_key = get_idempotency_key(order_data.dict(), [order_data.order_id])
        if is_duplicate_request(idempotency_key):
            # Return existing order
            order = Order.query.get(order_data.order_id)
            if order:
                return success_response({
                    "order_id": order.order_id,
                    "message": "Order already exists"
                })
        
        # Create order using service
        result = OrderService.create_order(device_id=device_id, order_data=order_data)
        
        # Mark request as processed
        mark_request_processed(idempotency_key, result)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to create order: {str(e)}",
            status_code=500
        )