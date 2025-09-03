from flask import request
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, and_, or_
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.api.decorators import validate_json, require_device_token, require_role
from app.schemas.device import (
    DeviceRegisterRequest, DeviceStatusRequest, MaterialsReportRequest,
    CommandRequest, BinBindRequest, DeviceResponse, DeviceSummaryResponse,
    DeviceBinResponse
)
from app.models import Device, DeviceBin, Order, RemoteCommand, Alarm, MaterialDictionary
from app.extensions import db
from app.services.device_service import DeviceService
from app.services.command_service import CommandService
from app.utils.idempotency import get_idempotency_key, is_duplicate_request, mark_request_processed


@bp.route('/devices', methods=['GET'])
@login_required
def list_devices():
    """List devices with filtering and pagination"""
    try:
        # Get query parameters
        query_text = request.args.get('query', '').strip()
        merchant_id = request.args.get('merchant_id', type=int)
        model = request.args.get('model', '').strip()
        status = request.args.get('status', '').strip()
        address = request.args.get('address', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # Build query
        query = db.session.query(Device)
        
        # Apply filters
        if query_text:
            search_filter = or_(
                Device.device_id.ilike(f'%{query_text}%'),
                Device.alias.ilike(f'%{query_text}%'),
                Device.model.ilike(f'%{query_text}%')
            )
            query = query.filter(search_filter)
        
        if merchant_id:
            query = query.filter(Device.merchant_id == merchant_id)
        
        if model:
            query = query.filter(Device.model == model)
        
        if status:
            query = query.filter(Device.status == status)
        
        if address:
            query = query.join(Device.location).filter(
                Device.location.has(address.ilike(f'%{address}%'))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        devices = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to response format
        device_data = [device.to_dict() for device in devices]
        
        return paginated_response(device_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list devices: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """Get device details"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        return success_response(device.to_dict())
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/summary', methods=['GET'])
@login_required
def get_device_summary(device_id):
    """Get device summary with statistics"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        # Calculate statistics
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Orders statistics
        orders_today = db.session.query(Order).filter(
            and_(Order.device_id == device_id, Order.server_ts >= today)
        ).count()
        
        orders_week = db.session.query(Order).filter(
            and_(Order.device_id == device_id, Order.server_ts >= week_ago)
        ).count()
        
        # Alarms statistics
        alarms_open = db.session.query(Alarm).filter(
            and_(Alarm.device_id == device_id, Alarm.status == 'open')
        ).count()
        
        # Low materials count
        materials_low = db.session.query(DeviceBin).filter(
            and_(
                DeviceBin.device_id == device_id,
                DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
            )
        ).count()
        
        # Online rate (simplified - based on last seen)
        online_rate = 1.0 if device.status.value == 'online' else 0.0
        
        return success_response({
            "device": device.to_dict(),
            "online_rate": online_rate,
            "orders_today": orders_today,
            "orders_week": orders_week,
            "alarms_open": alarms_open,
            "materials_low": materials_low
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device summary: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/materials', methods=['GET'])
@login_required
def get_device_materials(device_id):
    """Get device material bins"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        bins = DeviceBin.query.filter_by(device_id=device_id).all()
        
        # Convert to response format and add low material flag
        bin_data = []
        for bin_obj in bins:
            bin_dict = bin_obj.to_dict()
            if bin_obj.remaining and bin_obj.capacity and bin_obj.threshold_low_pct:
                threshold = bin_obj.capacity * bin_obj.threshold_low_pct / 100
                bin_dict['is_low'] = bin_obj.remaining < threshold
            else:
                bin_dict['is_low'] = False
            bin_data.append(bin_dict)
        
        return success_response(bin_data)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device materials: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/orders', methods=['GET'])
@login_required
def get_device_orders(device_id):
    """Get device recent orders"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        limit = request.args.get('limit', 10, type=int)
        
        orders = db.session.query(Order).filter_by(device_id=device_id)\
            .order_by(Order.server_ts.desc()).limit(limit).all()
        
        order_data = [order.to_dict() for order in orders]
        
        return success_response(order_data)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device orders: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/commands', methods=['GET'])
@login_required
def get_device_commands(device_id):
    """Get device command history"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        limit = request.args.get('limit', 20, type=int)
        
        commands = db.session.query(RemoteCommand).filter_by(device_id=device_id)\
            .order_by(RemoteCommand.issued_at.desc()).limit(limit).all()
        
        command_data = [command.to_dict() for command in commands]
        
        return success_response(command_data)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device commands: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/commands', methods=['POST'])
@login_required
@validate_json(CommandRequest)
@require_role(['admin', 'ops'])
def send_device_command(device_id):
    """Send command to specific device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        command_data = request.validated_json
        
        # Use command service to create and dispatch command
        command = CommandService.create_single_command(
            device_id=device_id,
            command_type=command_data.type,
            payload=command_data.payload,
            max_attempts=command_data.max_attempts,
            created_by=current_user.id
        )
        
        return success_response(command.to_dict())
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to send command: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/sync_state', methods=['POST'])
@login_required
@require_role(['admin', 'ops'])
def sync_device_state(device_id):
    """Sync device state (send sync command)"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        # Create sync command
        command = CommandService.create_single_command(
            device_id=device_id,
            command_type='sync',
            payload={},
            created_by=current_user.id
        )
        
        return success_response({
            "message": "Sync command sent",
            "command": command.to_dict()
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to sync device: {str(e)}",
            status_code=500
        )


# Device API endpoints (for device client communication)

@bp.route('/devices/register', methods=['POST'])
@require_device_token()
@validate_json(DeviceRegisterRequest)
def register_device():
    """Register new device"""
    try:
        device_data = request.validated_json
        
        # Check for idempotency
        idempotency_key = get_idempotency_key(device_data.dict(), [device_data.device_id])
        if is_duplicate_request(idempotency_key):
            # Return existing device
            device = Device.query.get(device_data.device_id)
            if device:
                return success_response({
                    "device_id": device.device_id,
                    "message": "already registered",
                    "provisioning": {
                        "merchant_id": device.merchant_id,
                        "needs_binding": device.merchant_id is None
                    }
                })
        
        # Use device service to register
        result = DeviceService.register_device(device_data)
        
        # Mark request as processed
        mark_request_processed(idempotency_key, result)
        
        return success_response(result)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to register device: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/status', methods=['POST'])
@require_device_token()
@validate_json(DeviceStatusRequest)
def update_device_status(device_id):
    """Update device status (heartbeat)"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        status_data = request.validated_json
        
        # Update device status
        DeviceService.update_device_status(device, status_data)
        
        return success_response({"message": "Status updated"})
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update device status: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/materials/report', methods=['POST'])
@require_device_token()
@validate_json(MaterialsReportRequest)
def report_materials(device_id):
    """Report device materials"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        materials_data = request.validated_json
        
        # Update materials using device service
        DeviceService.update_device_materials(device, materials_data)
        
        return success_response({"message": "Materials updated"})
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update materials: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/commands/pending', methods=['GET'])
@require_device_token()
def get_pending_commands(device_id):
    """Get pending commands for device"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        # Get pending/queued commands
        commands = db.session.query(RemoteCommand).filter(
            and_(
                RemoteCommand.device_id == device_id,
                RemoteCommand.status.in_(['pending', 'queued'])
            )
        ).order_by(RemoteCommand.issued_at).all()
        
        # Convert to device-friendly format
        command_data = []
        for command in commands:
            command_data.append({
                "command_id": command.command_id,
                "type": command.type.value,
                "payload": command.payload,
                "issued_at": command.issued_at.isoformat(),
                "max_attempts": command.max_attempts,
                "attempts": command.attempts
            })
        
        return success_response(command_data)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get pending commands: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/command_result', methods=['POST'])
@require_device_token()
def submit_command_result(device_id):
    """Submit command execution result"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        data = request.get_json()
        if not data or not data.get('command_id'):
            return error_response(
                ErrorCode.MISSING_REQUIRED_FIELD,
                "command_id is required"
            )
        
        # Update command result using command service
        result = CommandService.update_command_result(
            command_id=data['command_id'],
            status=data.get('status'),
            result_payload=data.get('result_payload'),
            error_message=data.get('error_message')
        )
        
        if not result:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Command not found",
                status_code=404
            )
        
        return success_response({"message": "Result recorded"})
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to submit command result: {str(e)}",
            status_code=500
        )


# Bin management endpoints

@bp.route('/devices/<device_id>/bins', methods=['GET'])
@login_required
def get_device_bins(device_id):
    """Get device bins configuration"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        bins = DeviceBin.query.filter_by(device_id=device_id)\
            .order_by(DeviceBin.bin_index).all()
        
        bin_data = []
        for bin_obj in bins:
            bin_dict = bin_obj.to_dict()
            # Add material info if available
            if bin_obj.material:
                bin_dict['material'] = bin_obj.material.to_dict()
            bin_data.append(bin_dict)
        
        return success_response(bin_data)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get device bins: {str(e)}",
            status_code=500
        )


@bp.route('/devices/<device_id>/bins/<int:bin_index>/bind', methods=['PUT'])
@login_required
@validate_json(BinBindRequest)
@require_role(['admin', 'ops'])
def bind_device_bin(device_id, bin_index):
    """Bind material to device bin"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return error_response(
                ErrorCode.DEVICE_NOT_FOUND,
                "Device not found",
                status_code=404
            )
        
        bind_data = request.validated_json
        
        # Check if material exists
        material = MaterialDictionary.query.filter_by(code=bind_data.material_code).first()
        if not material:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Material not found",
                status_code=404
            )
        
        # Find or create bin
        bin_obj = DeviceBin.query.filter_by(
            device_id=device_id,
            bin_index=bin_index
        ).first()
        
        if not bin_obj:
            bin_obj = DeviceBin(device_id=device_id, bin_index=bin_index)
            db.session.add(bin_obj)
        
        # Update bin configuration
        bin_obj.material_code = bind_data.material_code
        bin_obj.capacity = bind_data.capacity
        bin_obj.unit = bind_data.unit
        bin_obj.threshold_low_pct = bind_data.threshold_low_pct
        bin_obj.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return success_response(bin_obj.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to bind bin: {str(e)}",
            status_code=500
        )