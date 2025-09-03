"""
Core API endpoints backed by the database (SQLAlchemy models).
All responses are standardized via api_response().
"""
from datetime import datetime, timedelta, date
from collections import defaultdict
from flask import jsonify, request
from sqlalchemy import func, and_, or_

from app import db
from app.api import bp
from app.models.device import Device, DeviceStatus
from app.models.merchant import Merchant
from app.models.location import Location
from app.models.device_bin import DeviceBin
from app.models.material_dictionary import MaterialDictionary
from app.models.order import Order, PaymentStatus
from app.models.order_item import OrderItem
from app.models.remote_command import RemoteCommand, CommandStatus, CommandType
from app.models.alarm import Alarm, AlarmSeverity, AlarmStatus, AlarmType


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
        # Parse date range
        to_dt = request.args.get('to')
        from_dt = request.args.get('from')
        merchant_id = request.args.get('merchant_id')

        now = datetime.utcnow()
        to_dt = datetime.fromisoformat(to_dt) if to_dt else now
        from_dt = datetime.fromisoformat(from_dt) if from_dt else (to_dt - timedelta(days=7))

        device_q = Device.query
        order_q = Order.query
        alarm_q = Alarm.query
        bin_q = DeviceBin.query

        if merchant_id:
            try:
                mid = int(merchant_id)
            except ValueError:
                return api_response(error={
                    'code': 'INVALID_PARAMETER',
                    'message': 'merchant_id must be integer'
                })
            device_q = device_q.filter(Device.merchant_id == mid)
            order_q = order_q.join(Device, Device.device_id == Order.device_id).filter(Device.merchant_id == mid)
            alarm_q = alarm_q.join(Device, Device.device_id == Alarm.device_id).filter(Device.merchant_id == mid)
            bin_q = bin_q.join(Device, Device.device_id == DeviceBin.device_id).filter(Device.merchant_id == mid)

        device_total = device_q.count()
        online_count = device_q.filter(Device.status == DeviceStatus.ONLINE.value).count()
        online_rate = round((online_count / device_total) * 100, 1) if device_total else 0.0

        # Sales today and week
        start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sales_today_q = order_q.filter(and_(Order.server_ts >= start_of_today, Order.server_ts <= now))
        sales_today_amount = sales_today_q.with_entities(func.coalesce(func.sum(Order.total_price), 0.0)).scalar() or 0.0
        sales_today_count = sales_today_q.count()

        sales_week_q = order_q.filter(and_(Order.server_ts >= from_dt, Order.server_ts <= to_dt))
        sales_week_amount = sales_week_q.with_entities(func.coalesce(func.sum(Order.total_price), 0.0)).scalar() or 0.0
        sales_week_count = sales_week_q.count()

        # Open alarms
        alarms_open = alarm_q.filter(Alarm.status == AlarmStatus.OPEN.value).count()

        # Low materials count (bins where remaining% <= threshold OR empty)
        low_bins_count = bin_q.filter(
            or_(
                and_(DeviceBin.capacity.isnot(None), DeviceBin.capacity > 0, DeviceBin.remaining <= (DeviceBin.capacity * (DeviceBin.threshold_low_pct / 100.0))),
                DeviceBin.remaining <= 0
            )
        ).count()

        # Sales trend for last 7 days
        days = [to_dt.date() - timedelta(days=i) for i in range(6, -1, -1)]
        sales_by_day = {d: 0.0 for d in days}
        trend_rows = (sales_week_q
            .with_entities(func.date(Order.server_ts).label('d'), func.coalesce(func.sum(Order.total_price), 0.0))
            .group_by(func.date(Order.server_ts)).all())
        for d, amount in trend_rows:
            if isinstance(d, date):
                sales_by_day[d] = float(amount or 0.0)
            else:
                # Some DBs may return string; parse fallback
                try:
                    sales_by_day[datetime.fromisoformat(str(d)).date()] = float(amount or 0.0)
                except Exception:
                    pass

        sales_trend = [{ 'date': d.isoformat(), 'amount': round(sales_by_day[d], 2) } for d in days]

        # Online rate trend (no historical data table yet; reuse snapshot for now)
        online_trend = [{ 'date': d.isoformat(), 'rate': online_rate } for d in days]

        summary_data = {
            'device_total': device_total,
            'online_rate': online_rate,
            'sales_today': {
                'amount': round(sales_today_amount, 2),
                'currency': 'CNY',
                'orders_count': sales_today_count
            },
            'sales_week': {
                'amount': round(sales_week_amount, 2),
                'currency': 'CNY',
                'orders_count': sales_week_count
            },
            'alarms_open': alarms_open,
            'materials_low': low_bins_count,
            'trends': {
                'sales': sales_trend,
                'online_rate': online_trend
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
        q = request.args.get('query', '')
        merchant_id = request.args.get('merchant_id')
        model = request.args.get('model')
        status = request.args.get('status')
        address = request.args.get('address')

        query = Device.query.outerjoin(Merchant, Merchant.id == Device.merchant_id).outerjoin(Location, Location.id == Device.location_id)

        if q:
            like = f"%{q}%"
            query = query.filter(or_(Device.alias.ilike(like), Device.device_id.ilike(like)))

        if merchant_id:
            try:
                mid = int(merchant_id)
            except ValueError:
                return api_response(error={'code': 'INVALID_PARAMETER', 'message': 'merchant_id must be integer'})
            query = query.filter(Device.merchant_id == mid)

        if model:
            query = query.filter(Device.model == model)

        if status:
            query = query.filter(Device.status == status)

        if address:
            like_addr = f"%{address}%"
            query = query.filter(Location.address.ilike(like_addr))

        total = query.count()
        items = query.order_by(Device.device_id).offset((page - 1) * page_size).limit(page_size).all()

        def device_to_dict(d: Device):
            return {
                'device_id': d.device_id,
                'alias': d.alias,
                'model': d.model,
                'fw_version': d.fw_version,
                'status': d.status,
                'last_seen': d.last_seen.isoformat() if d.last_seen else None,
                'ip': d.ip,
                'wifi_ssid': d.wifi_ssid,
                'temperature': d.temperature,
                'merchant': {'id': d.merchant.id, 'name': d.merchant.name} if d.merchant else None,
                'location': {'id': d.location.id, 'name': d.location.name, 'address': d.location.address} if d.location else None,
                'tags': d.tags or {}
            }

        return api_response({
            'devices': [device_to_dict(d) for d in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size
            },
            'filters': {
                'query': q,
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
        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        orders_today = Order.query.filter(and_(Order.device_id == device_id, Order.server_ts >= start_of_today)).all()
        revenue_today = sum(o.total_price for o in orders_today)

        bins = DeviceBin.query.filter(DeviceBin.device_id == device_id).all()
        total_bins = len(bins)
        low_bins = 0
        empty_bins = 0
        for b in bins:
            pct = (b.remaining / b.capacity * 100.0) if b.capacity else 0.0
            if (b.remaining or 0) <= 0:
                empty_bins += 1
            elif b.threshold_low_pct is not None and pct <= b.threshold_low_pct:
                low_bins += 1

        device_data = {
            'device_id': d.device_id,
            'alias': d.alias,
            'status': d.status,
            'uptime_hours': None,  # Not tracked yet
            'total_orders_today': len(orders_today),
            'revenue_today': round(revenue_today, 2),
            'materials_status': {
                'total_bins': total_bins,
                'low_bins': low_bins,
                'empty_bins': empty_bins
            },
            'last_maintenance': None,
            'next_maintenance': None
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

        query = Order.query
        if device_id:
            query = query.filter(Order.device_id == device_id)

        if merchant_id:
            try:
                mid = int(merchant_id)
            except ValueError:
                return api_response(error={'code': 'INVALID_PARAMETER', 'message': 'merchant_id must be integer'})
            query = query.join(Device, Device.device_id == Order.device_id).filter(Device.merchant_id == mid)

        if payment_method:
            query = query.filter(Order.payment_method == payment_method)

        if exception is not None:
            is_exception = str(exception).lower() == 'true'
            query = query.filter(Order.is_exception == is_exception)

        if from_date:
            fd = datetime.fromisoformat(from_date)
            query = query.filter(Order.server_ts >= fd)
        if to_date:
            td = datetime.fromisoformat(to_date)
            query = query.filter(Order.server_ts <= td)

        total = query.count()
        rows = query.order_by(Order.server_ts.desc()).offset((page - 1) * page_size).limit(page_size).all()

        def order_to_dict(o: Order):
            return {
                'order_id': o.order_id,
                'device_id': o.device_id,
                'device_ts': o.device_ts.isoformat() if o.device_ts else None,
                'server_ts': o.server_ts.isoformat() if o.server_ts else None,
                'items_count': o.items_count,
                'total_price': o.total_price,
                'currency': o.currency,
                'payment_method': o.payment_method,
                'payment_status': o.payment_status,
                'is_exception': o.is_exception,
                'address': o.address,
                'items': [
                    {
                        'name': it.name,
                        'qty': it.qty,
                        'unit_price': it.unit_price
                    } for it in o.items.order_by(OrderItem.id).all()
                ]
            }

        return api_response({
            'orders': [order_to_dict(o) for o in rows],
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
        rows = MaterialDictionary.query.order_by(MaterialDictionary.code).all()
        materials = [{
            'id': m.id,
            'code': m.code,
            'name': m.name,
            'type': m.type,
            'unit': m.unit,
            'density': m.density,
            'enabled': m.enabled,
            'created_at': m.created_at.isoformat() if getattr(m, 'created_at', None) else None,
            'updated_at': m.updated_at.isoformat() if getattr(m, 'updated_at', None) else None,
        } for m in rows]

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
        
        # Create or update device in DB
        d = Device.query.get(data['device_id'])
        if not d:
            d = Device(device_id=data['device_id'], merchant_id=int(data['merchant_id']))
            db.session.add(d)
        d.model = data.get('model')
        d.alias = data.get('alias')
        d.fw_version = data.get('fw_version')
        d.status = data.get('status', DeviceStatus.REGISTERED.value)
        d.last_seen = datetime.utcnow()
        d.ip = data.get('ip')
        d.wifi_ssid = data.get('wifi_ssid')
        d.temperature = data.get('temperature')
        d.location_id = data.get('location_id')
        d.tags = data.get('tags')
        d.extra = data.get('extra')
        db.session.commit()

        response_data = {
            'device_id': d.device_id,
            'status': d.status,
            'registered_at': d.last_seen.isoformat()
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

        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        d.status = data.get('status', d.status)
        d.last_seen = datetime.utcnow()
        d.temperature = data.get('temperature', d.temperature)
        db.session.commit()

        response_data = {
            'device_id': d.device_id,
            'status': d.status,
            'received_at': d.last_seen.isoformat(),
            'next_sync': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }

        return api_response(response_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'STATUS_UPDATE_ERROR',
            'message': f'Status update failed: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/materials')
def device_materials(device_id):
    """Get device materials/bins status."""
    try:
        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        rows = (DeviceBin.query
            .filter(DeviceBin.device_id == device_id)
            .outerjoin(MaterialDictionary, MaterialDictionary.code == DeviceBin.material_code)
            .order_by(DeviceBin.bin_index)
            .all())

        bins = []
        last_sync = None
        normal = low = empty = 0
        for b in rows:
            pct = (b.remaining / b.capacity * 100.0) if (b.capacity and b.capacity > 0) else 0.0
            status = 'normal'
            if (b.remaining or 0) <= 0:
                status = 'empty'
                empty += 1
            elif b.threshold_low_pct is not None and pct <= b.threshold_low_pct:
                status = 'low'
                low += 1
            else:
                normal += 1
            item_last_sync = b.last_sync.isoformat() if b.last_sync else None
            if b.last_sync and (last_sync is None or b.last_sync > datetime.fromisoformat(last_sync)):
                last_sync = b.last_sync.isoformat()
            bins.append({
                'bin_index': b.bin_index,
                'material_code': b.material_code,
                'material_name': b.material.name if b.material else None,
                'remaining': b.remaining,
                'capacity': b.capacity,
                'unit': b.unit,
                'threshold_low_pct': b.threshold_low_pct,
                'last_sync': item_last_sync,
                'status': status
            })

        return api_response({
            'device_id': device_id,
            'bins': bins,
            'summary': {
                'total_bins': len(bins),
                'normal_bins': normal,
                'low_bins': low,
                'empty_bins': empty,
                'last_sync': last_sync
            }
        })
        
    except Exception as e:
        return api_response(error={
            'code': 'DEVICE_MATERIALS_ERROR',
            'message': f'Failed to fetch device materials: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/orders')
def device_orders(device_id):
    """Get recent orders for a specific device."""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)

        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        rows = (Order.query.filter(Order.device_id == device_id)
                .order_by(Order.server_ts.desc()).limit(limit).all())

        def order_to_dict(o: Order):
            return {
                'order_id': o.order_id,
                'device_id': o.device_id,
                'device_ts': o.device_ts.isoformat() if o.device_ts else None,
                'server_ts': o.server_ts.isoformat() if o.server_ts else None,
                'items_count': o.items_count,
                'total_price': o.total_price,
                'currency': o.currency,
                'payment_method': o.payment_method,
                'payment_status': o.payment_status,
                'is_exception': o.is_exception,
                'items': [
                    {
                        'name': it.name,
                        'qty': it.qty,
                        'unit_price': it.unit_price
                    } for it in o.items.order_by(OrderItem.id).all()
                ]
            }

        return api_response({
            'device_id': device_id,
            'orders': [order_to_dict(o) for o in rows],
            'total_count': len(rows)
        })
        
    except ValueError as e:
        return api_response(error={
            'code': 'INVALID_PARAMETER',
            'message': f'Invalid parameter value: {str(e)}'
        })
    except Exception as e:
        return api_response(error={
            'code': 'DEVICE_ORDERS_ERROR',
            'message': f'Failed to fetch device orders: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/commands')
def device_commands(device_id):
    """Get command history for a specific device."""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)

        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        rows = (RemoteCommand.query.filter(RemoteCommand.device_id == device_id)
                .order_by(RemoteCommand.issued_at.desc()).limit(limit).all())

        def cmd_to_dict(c: RemoteCommand):
            return {
                'command_id': c.command_id,
                'device_id': c.device_id,
                'type': c.type,
                'status': c.status,
                'issued_at': c.issued_at.isoformat() if c.issued_at else None,
                'sent_at': c.sent_at.isoformat() if c.sent_at else None,
                'result_at': c.result_at.isoformat() if c.result_at else None,
                'payload': c.payload,
                'result_payload': c.result_payload,
                'attempts': c.attempts,
                'max_attempts': c.max_attempts
            }

        return api_response({
            'device_id': device_id,
            'commands': [cmd_to_dict(c) for c in rows],
            'total_count': len(rows)
        })
        
    except ValueError as e:
        return api_response(error={
            'code': 'INVALID_PARAMETER',
            'message': f'Invalid parameter value: {str(e)}'
        })
    except Exception as e:
        return api_response(error={
            'code': 'DEVICE_COMMANDS_ERROR',
            'message': f'Failed to fetch device commands: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/commands', methods=['POST'])
def device_send_command(device_id):
    """Send a command to a specific device."""
    try:
        data = request.get_json()
        if not data:
            return api_response(error={
                'code': 'INVALID_REQUEST',
                'message': 'JSON payload required'
            })
        
        command_type = data.get('type')
        payload = data.get('payload', {})
        
        if not command_type:
            return api_response(error={
                'code': 'INVALID_REQUEST',
                'message': 'Command type is required'
            })

        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        # Create command record
        command_id = f'CMD_{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'
        cmd = RemoteCommand(
            command_id=command_id,
            device_id=device_id,
            type=command_type,
            payload=payload,
            status=CommandStatus.PENDING.value,
            issued_at=datetime.utcnow(),
            attempts=0,
            max_attempts=3
        )
        db.session.add(cmd)
        db.session.commit()

        response_data = {
            'command_id': cmd.command_id,
            'device_id': cmd.device_id,
            'type': cmd.type,
            'status': cmd.status,
            'issued_at': cmd.issued_at.isoformat(),
            'payload': cmd.payload,
            'attempts': cmd.attempts,
            'max_attempts': cmd.max_attempts
        }

        return api_response(response_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'SEND_COMMAND_ERROR',
            'message': f'Failed to send command: {str(e)}',
            'status_code': 500
        })


@bp.route('/devices/<device_id>/sync_state', methods=['POST'])
def device_sync_state(device_id):
    """Sync device state (materials, status, etc.)."""
    try:
        d = Device.query.get(device_id)
        if not d:
            return api_response(error={
                'code': 'DEVICE_NOT_FOUND',
                'message': f'Device {device_id} not found',
                'status_code': 404
            })

        # Optionally enqueue a sync command in DB
        cmd_id = f'SYNC_{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'
        cmd = RemoteCommand(
            command_id=cmd_id,
            device_id=device_id,
            type=CommandType.SYNC.value,
            payload={'actions': ['sync_materials', 'sync_status', 'sync_commands']},
            status=CommandStatus.PENDING.value,
            issued_at=datetime.utcnow()
        )
        db.session.add(cmd)
        db.session.commit()

        response_data = {
            'device_id': device_id,
            'sync_started_at': cmd.issued_at.isoformat(),
            'estimated_completion': (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
            'operations': ['sync_materials', 'sync_status', 'sync_commands'],
            'command_id': cmd.command_id
        }

        return api_response(response_data)
        
    except Exception as e:
        return api_response(error={
            'code': 'SYNC_STATE_ERROR',
            'message': f'Failed to sync device state: {str(e)}',
            'status_code': 500
        })