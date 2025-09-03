"""
Simplified API endpoints for demonstration without external dependencies.
This module implements core API functionality using only built-in Python libraries.
"""
from datetime import datetime, timedelta
from flask import jsonify, request
from app.api import bp


def api_response(data=None, error=None):
    """Standard API response format."""
    if error:
        return jsonify({
            'ok': False,
            'error': {
                'code': error.get('code', 'UNKNOWN_ERROR'),
                'message': error.get('message', 'An error occurred'),
                'details': error.get('details', {})
            }
        }), error.get('status_code', 400)
    
    return jsonify({
        'ok': True,
        'data': data or {}
    })


@bp.route('/health')
def health():
    """API health check."""
    return api_response({'status': 'healthy', 'version': 'v1', 'timestamp': datetime.utcnow().isoformat()})


@bp.route('/dashboard/summary')
def dashboard_summary():
    """Dashboard summary with KPIs."""
    try:
        # Mock data for demonstration - in real implementation, this would query the database
        from_date = request.args.get('from', (datetime.utcnow() - timedelta(days=7)).isoformat())
        to_date = request.args.get('to', datetime.utcnow().isoformat())
        merchant_id = request.args.get('merchant_id')
        
        summary_data = {
            'device_total': 3,
            'online_rate': 66.7,  # 2 out of 3 devices online
            'sales_today': {
                'amount': 245.50,
                'currency': 'CNY',
                'orders_count': 12
            },
            'sales_week': {
                'amount': 1432.80,
                'currency': 'CNY', 
                'orders_count': 78
            },
            'alarms_open': 1,
            'materials_low': 2,
            'trends': {
                'sales': [
                    {'date': '2024-01-01', 'amount': 156.30},
                    {'date': '2024-01-02', 'amount': 203.45},
                    {'date': '2024-01-03', 'amount': 189.20},
                    {'date': '2024-01-04', 'amount': 234.67},
                    {'date': '2024-01-05', 'amount': 178.90},
                    {'date': '2024-01-06', 'amount': 225.78},
                    {'date': '2024-01-07', 'amount': 245.50}
                ],
                'online_rate': [
                    {'date': '2024-01-01', 'rate': 100.0},
                    {'date': '2024-01-02', 'rate': 66.7},
                    {'date': '2024-01-03', 'rate': 66.7},
                    {'date': '2024-01-04', 'rate': 100.0},
                    {'date': '2024-01-05', 'rate': 66.7},
                    {'date': '2024-01-06', 'rate': 66.7},
                    {'date': '2024-01-07', 'rate': 66.7}
                ]
            }
        }
        
        return api_response(summary_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'DASHBOARD_ERROR',
            'message': f'Failed to fetch dashboard summary: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices')
def devices_list():
    """List devices with filtering and pagination."""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        query = request.args.get('query', '')
        merchant_id = request.args.get('merchant_id')
        model = request.args.get('model')
        status = request.args.get('status')
        address = request.args.get('address')
        
        # Mock device data - in real implementation, this would query Device model
        all_devices = [
            {
                'device_id': 'CM001',
                'alias': 'Downtown Coffee Machine',
                'model': 'CM-2000',
                'fw_version': '1.2.3',
                'status': 'online',
                'last_seen': '2024-01-01T12:30:00Z',
                'ip': '192.168.1.100',
                'wifi_ssid': 'CoffeeShop_WiFi',
                'temperature': 22.5,
                'merchant': {
                    'id': 1,
                    'name': 'StarBucks Coffee'
                },
                'location': {
                    'id': 1,
                    'name': 'Downtown Store',
                    'address': '123 Main St'
                },
                'tags': {'location': 'indoor', 'priority': 'high'}
            },
            {
                'device_id': 'CM002',
                'alias': 'Mall Coffee Machine',
                'model': 'CM-2000',
                'fw_version': '1.2.2',
                'status': 'offline',
                'last_seen': '2024-01-01T10:30:00Z',
                'ip': '192.168.1.101',
                'wifi_ssid': 'Mall_Guest',
                'temperature': None,
                'merchant': {
                    'id': 1,
                    'name': 'StarBucks Coffee'
                },
                'location': {
                    'id': 2,
                    'name': 'Mall Store',
                    'address': '456 Mall Ave'
                },
                'tags': {'location': 'mall'}
            },
            {
                'device_id': 'CM003',
                'alias': 'Local Coffee Machine',
                'model': 'CM-1000',
                'fw_version': '1.1.5',
                'status': 'online',
                'last_seen': '2024-01-01T12:25:00Z',
                'ip': '192.168.2.50',
                'wifi_ssid': 'Local_Network',
                'temperature': 23.1,
                'merchant': {
                    'id': 2,
                    'name': 'Local Coffee Shop'
                },
                'location': {
                    'id': 3,
                    'name': 'Local Store',
                    'address': '789 Local St'
                },
                'tags': {'location': 'street'}
            }
        ]
        
        # Apply filters
        filtered_devices = all_devices
        
        if query:
            filtered_devices = [d for d in filtered_devices 
                              if query.lower() in d['alias'].lower() or query.lower() in d['device_id'].lower()]
        
        if merchant_id:
            filtered_devices = [d for d in filtered_devices if d['merchant']['id'] == int(merchant_id)]
        
        if model:
            filtered_devices = [d for d in filtered_devices if d['model'] == model]
        
        if status:
            filtered_devices = [d for d in filtered_devices if d['status'] == status]
        
        if address:
            filtered_devices = [d for d in filtered_devices 
                              if address.lower() in d['location']['address'].lower()]
        
        # Apply pagination
        total = len(filtered_devices)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_devices = filtered_devices[start_idx:end_idx]
        
        return api_response({
            'devices': paginated_devices,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size
            },
            'filters': {
                'query': query,
                'merchant_id': merchant_id,
                'model': model,
                'status': status,
                'address': address
            }
        })
        
    except ValueError as e:
        return api_response(error={
            'code': 'INVALID_PARAMETER',
            'message': f'Invalid parameter value: {str(e)}'
        })
    except Exception as e:
        return api_response(error={
            'code': 'DEVICES_ERROR',
            'message': f'Failed to fetch devices: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/summary')
def device_summary(device_id):
    """Get device summary information."""
    try:
        # Mock device summary data
        if device_id not in ['CM001', 'CM002', 'CM003']:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })
        
        device_data = {
            'device_id': device_id,
            'alias': f'{device_id} Coffee Machine',
            'status': 'online' if device_id != 'CM002' else 'offline',
            'uptime_hours': 156.5 if device_id != 'CM002' else 0,
            'total_orders_today': 12 if device_id == 'CM001' else 8 if device_id == 'CM003' else 0,
            'revenue_today': 245.50 if device_id == 'CM001' else 178.30 if device_id == 'CM003' else 0,
            'materials_status': {
                'total_bins': 4 if device_id != 'CM003' else 3,
                'low_bins': 1 if device_id == 'CM001' else 0,
                'empty_bins': 1 if device_id == 'CM002' else 0
            },
            'last_maintenance': '2023-12-15T09:00:00Z',
            'next_maintenance': '2024-02-15T09:00:00Z'
        }
        
        return api_response(device_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'DEVICE_SUMMARY_ERROR',
            'message': f'Failed to fetch device summary: {str(e)}',
            'status_code': 500
        })


@bp.route('/orders')
def orders_list():
    """List orders with filtering and pagination."""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        device_id = request.args.get('device_id')
        merchant_id = request.args.get('merchant_id')
        payment_method = request.args.get('payment_method')
        exception = request.args.get('exception')
        
        # Mock orders data
        all_orders = [
            {
                'order_id': 'ORDER_001',
                'device_id': 'CM001',
                'device_ts': '2024-01-01T09:15:00Z',
                'server_ts': '2024-01-01T09:15:01Z',
                'items_count': 2,
                'total_price': 25.50,
                'currency': 'CNY',
                'payment_method': 'wechat',
                'payment_status': 'paid',
                'is_exception': False,
                'address': '123 Main St',
                'items': [
                    {'name': 'Latte', 'qty': 1, 'unit_price': 18.50},
                    {'name': 'Cappuccino', 'qty': 1, 'unit_price': 7.00}
                ]
            },
            {
                'order_id': 'ORDER_002',
                'device_id': 'CM001',
                'device_ts': '2024-01-01T10:30:00Z',
                'server_ts': '2024-01-01T10:30:01Z',
                'items_count': 1,
                'total_price': 18.00,
                'currency': 'CNY',
                'payment_method': 'alipay',
                'payment_status': 'paid',
                'is_exception': False,
                'address': '123 Main St',
                'items': [
                    {'name': 'Americano', 'qty': 1, 'unit_price': 18.00}
                ]
            },
            {
                'order_id': 'ORDER_006',
                'device_id': 'CM002',
                'device_ts': '2024-01-01T11:00:00Z',
                'server_ts': '2024-01-01T11:00:01Z',
                'items_count': 1,
                'total_price': 20.00,
                'currency': 'CNY',
                'payment_method': 'wechat',
                'payment_status': 'refunded',
                'is_exception': True,
                'address': '456 Mall Ave',
                'items': [
                    {'name': 'Latte', 'qty': 1, 'unit_price': 20.00}
                ]
            },
            {
                'order_id': 'ORDER_007',
                'device_id': 'CM001',
                'device_ts': '2024-01-01T13:30:00Z',
                'server_ts': '2024-01-01T13:30:01Z',
                'items_count': 2,
                'total_price': 35.00,
                'currency': 'CNY',
                'payment_method': 'card',
                'payment_status': 'refund_failed',
                'is_exception': True,
                'address': '123 Main St',
                'items': [
                    {'name': 'Mocha', 'qty': 2, 'unit_price': 17.50}
                ]
            }
        ]
        
        # Apply filters
        filtered_orders = all_orders
        
        if device_id:
            filtered_orders = [o for o in filtered_orders if o['device_id'] == device_id]
        
        if payment_method:
            filtered_orders = [o for o in filtered_orders if o['payment_method'] == payment_method]
        
        if exception is not None:
            is_exception = exception.lower() == 'true'
            filtered_orders = [o for o in filtered_orders if o['is_exception'] == is_exception]
        
        # Apply pagination
        total = len(filtered_orders)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_orders = filtered_orders[start_idx:end_idx]
        
        return api_response({
            'orders': paginated_orders,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size
            },
            'filters': {
                'from': from_date,
                'to': to_date,
                'device_id': device_id,
                'merchant_id': merchant_id,
                'payment_method': payment_method,
                'exception': exception
            }
        })
        
    except ValueError as e:
        return api_response(error={
            'code': 'INVALID_PARAMETER',
            'message': f'Invalid parameter value: {str(e)}'
        })
    except Exception as e:
        return api_response(error={
            'code': 'ORDERS_ERROR',
            'message': f'Failed to fetch orders: {str(e)}',
            'status_code': 500
        })


@bp.route('/materials')
def materials_list():
    """List material dictionary entries."""
    try:
        # Mock materials data
        materials = [
            {
                'id': 1,
                'code': 'COFFEE_BEAN_A',
                'name': 'Arabica Coffee Beans',
                'type': 'bean',
                'unit': 'g',
                'density': 0.6,
                'enabled': True,
                'created_at': '2023-12-01T00:00:00Z',
                'updated_at': '2023-12-01T00:00:00Z'
            },
            {
                'id': 2,
                'code': 'COFFEE_BEAN_R',
                'name': 'Robusta Coffee Beans',
                'type': 'bean',
                'unit': 'g',
                'density': 0.65,
                'enabled': True,
                'created_at': '2023-12-01T00:00:00Z',
                'updated_at': '2023-12-01T00:00:00Z'
            },
            {
                'id': 3,
                'code': 'MILK_POWDER',
                'name': 'Milk Powder',
                'type': 'powder',
                'unit': 'g',
                'density': 0.5,
                'enabled': True,
                'created_at': '2023-12-01T00:00:00Z',
                'updated_at': '2023-12-01T00:00:00Z'
            },
            {
                'id': 4,
                'code': 'SUGAR',
                'name': 'Sugar',
                'type': 'powder',
                'unit': 'g',
                'density': 0.8,
                'enabled': True,
                'created_at': '2023-12-01T00:00:00Z',
                'updated_at': '2023-12-01T00:00:00Z'
            }
        ]
        
        return api_response({
            'materials': materials,
            'total': len(materials)
        })
        
    except Exception as e:
        return api_response(error={
            'code': 'MATERIALS_ERROR',
            'message': f'Failed to fetch materials: {str(e)}',
            'status_code': 500
        })


# Device-specific endpoints for device communication
@bp.route('/devices/register', methods=['POST'])
def device_register():
    """Register a new device."""
    try:
        data = request.get_json()
        if not data:
            return api_response(error={
                'code': 'INVALID_REQUEST',
                'message': 'JSON payload required'
            })
        
        required_fields = ['device_id', 'model', 'merchant_id']
        for field in required_fields:
            if field not in data:
                return api_response(error={
                    'code': 'MISSING_FIELD',
                    'message': f'Required field {field} is missing'
                })
        
        # Mock successful registration
        response_data = {
            'device_id': data['device_id'],
            'status': 'registered',
            'registered_at': datetime.utcnow().isoformat(),
            'token': f"device_token_{data['device_id']}"
        }
        
        return api_response(response_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'REGISTRATION_ERROR',
            'message': f'Device registration failed: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/status', methods=['POST'])
def device_status_update(device_id):
    """Update device status."""
    try:
        data = request.get_json()
        if not data:
            return api_response(error={
                'code': 'INVALID_REQUEST',
                'message': 'JSON payload required'
            })
        
        # Mock successful status update
        response_data = {
            'device_id': device_id,
            'status': data.get('status', 'online'),
            'received_at': datetime.utcnow().isoformat(),
            'next_sync': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        return api_response(response_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'STATUS_UPDATE_ERROR',
            'message': f'Status update failed: {str(e)}',
            'status_code': 500
        })