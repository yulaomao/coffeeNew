from datetime import datetime, timezone
from app.models import Device, DeviceBin, MaterialDictionary, OperationLog
from app.extensions import db
from app.utils.idempotency import get_idempotency_key


class DeviceService:
    @staticmethod
    def register_device(device_data):
        """Register a new device"""
        device = Device.query.get(device_data.device_id)
        
        if device:
            # Device already exists, return existing info
            return {
                "device_id": device.device_id,
                "message": "already registered",
                "provisioning": {
                    "merchant_id": device.merchant_id,
                    "needs_binding": device.merchant_id is None
                }
            }
        
        # Create new device
        device = Device(
            device_id=device_data.device_id,
            model=device_data.model,
            fw_version=device_data.firmware_version,
            status='registered',
            extra={
                "serial": device_data.serial,
                "mac": device_data.mac,
                "registration_address": device_data.address
            }
        )
        
        # Set location if provided
        if device_data.location:
            device.extra["registration_location"] = {
                "lat": device_data.location.lat,
                "lng": device_data.location.lng
            }
        
        db.session.add(device)
        
        # Log the operation
        log = OperationLog(
            action="device_register",
            target_type="device",
            target_id=device_data.device_id,
            summary=f"Device {device_data.device_id} registered",
            payload_snip={
                "model": device_data.model,
                "firmware_version": device_data.firmware_version
            },
            source='device'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return {
            "device_id": device.device_id,
            "message": "registered",
            "provisioning": {
                "merchant_id": None,
                "needs_binding": True
            }
        }
    
    @staticmethod
    def update_device_status(device, status_data):
        """Update device status and heartbeat"""
        device.status = status_data.status
        device.last_seen = status_data.timestamp
        
        if status_data.ip:
            device.ip = status_data.ip
        
        if status_data.wifi_ssid:
            device.wifi_ssid = status_data.wifi_ssid
        
        if status_data.temperature is not None:
            device.temperature = status_data.temperature
        
        if status_data.extra:
            if device.extra:
                device.extra.update(status_data.extra)
            else:
                device.extra = status_data.extra
        
        device.updated_at = datetime.now(timezone.utc)
        
        # Log status update
        log = OperationLog(
            action="device_status_update",
            target_type="device",
            target_id=device.device_id,
            summary=f"Device {device.device_id} status updated to {status_data.status.value}",
            payload_snip={
                "status": status_data.status.value,
                "timestamp": status_data.timestamp.isoformat()
            },
            source='device'
        )
        db.session.add(log)
        
        db.session.commit()
    
    @staticmethod
    def update_device_materials(device, materials_data):
        """Update device material bins"""
        for material_report in materials_data.materials:
            # Find or create bin
            bin_obj = DeviceBin.query.filter_by(
                device_id=device.device_id,
                bin_index=material_report.bin_index
            ).first()
            
            if not bin_obj:
                bin_obj = DeviceBin(
                    device_id=device.device_id,
                    bin_index=material_report.bin_index
                )
                db.session.add(bin_obj)
            
            # Update bin data
            bin_obj.material_code = material_report.material_code
            bin_obj.remaining = material_report.remaining
            bin_obj.capacity = material_report.capacity
            bin_obj.unit = material_report.unit
            bin_obj.last_sync = materials_data.timestamp
            bin_obj.updated_at = datetime.now(timezone.utc)
        
        # Log materials update
        log = OperationLog(
            action="device_materials_update",
            target_type="device",
            target_id=device.device_id,
            summary=f"Device {device.device_id} materials updated",
            payload_snip={
                "bins_count": len(materials_data.materials),
                "timestamp": materials_data.timestamp.isoformat()
            },
            source='device'
        )
        db.session.add(log)
        
        db.session.commit()
    
    @staticmethod
    def check_low_materials(device_id=None):
        """Check for devices with low materials"""
        query = db.session.query(DeviceBin).filter(
            DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
        )
        
        if device_id:
            query = query.filter(DeviceBin.device_id == device_id)
        
        return query.all()
    
    @staticmethod
    def get_device_statistics(device_id):
        """Get comprehensive device statistics"""
        from app.models import Order, Alarm
        
        device = Device.query.get(device_id)
        if not device:
            return None
        
        # Calculate various statistics
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Order statistics
        total_orders = db.session.query(Order).filter_by(device_id=device_id).count()
        orders_today = db.session.query(Order).filter(
            Order.device_id == device_id,
            Order.server_ts >= today
        ).count()
        
        # Alarm statistics
        open_alarms = db.session.query(Alarm).filter(
            Alarm.device_id == device_id,
            Alarm.status == 'open'
        ).count()
        
        # Material statistics
        low_materials = DeviceService.check_low_materials(device_id)
        
        return {
            "device": device.to_dict(),
            "statistics": {
                "total_orders": total_orders,
                "orders_today": orders_today,
                "open_alarms": open_alarms,
                "low_materials_count": len(low_materials),
                "low_materials": [bin_obj.to_dict() for bin_obj in low_materials]
            }
        }