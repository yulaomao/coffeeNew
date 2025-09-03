from datetime import datetime, timezone, timedelta
from app.workers.celery_app import celery
from app.models import Alarm, Device, DeviceBin
from app.extensions import db
from app import create_app


@celery.task
def alarm_aggregator():
    """Aggregate and create alarms based on system conditions"""
    app = create_app()
    with app.app_context():
        try:
            alarms_created = 0
            
            # Check for offline devices
            alarms_created += _check_offline_devices()
            
            # Check for low materials
            alarms_created += _check_low_materials()
            
            # Check for failed dispatches (would need more logic)
            # alarms_created += _check_failed_dispatches()
            
            return {"alarms_created": alarms_created}
            
        except Exception as e:
            return {"error": str(e)}


def _check_offline_devices():
    """Check for devices that have been offline too long"""
    offline_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
    
    offline_devices = Device.query.filter(
        Device.last_seen < offline_threshold,
        Device.status != 'offline'
    ).all()
    
    alarms_created = 0
    
    for device in offline_devices:
        # Update device status
        device.status = 'offline'
        
        # Check if alarm already exists
        existing_alarm = Alarm.query.filter(
            Alarm.device_id == device.device_id,
            Alarm.type == 'offline',
            Alarm.status == 'open'
        ).first()
        
        if not existing_alarm:
            # Create offline alarm
            alarm = Alarm(
                device_id=device.device_id,
                type='offline',
                severity='warn',
                title=f"Device {device.device_id} offline",
                description=f"Device has been offline since {device.last_seen}",
                status='open',
                context={
                    "last_seen": device.last_seen.isoformat(),
                    "offline_duration": str(datetime.now(timezone.utc) - device.last_seen)
                }
            )
            db.session.add(alarm)
            alarms_created += 1
    
    db.session.commit()
    return alarms_created


def _check_low_materials():
    """Check for bins with low materials"""
    low_bins = db.session.query(DeviceBin).filter(
        DeviceBin.remaining < (DeviceBin.capacity * DeviceBin.threshold_low_pct / 100)
    ).all()
    
    alarms_created = 0
    
    for bin_obj in low_bins:
        # Check if alarm already exists
        existing_alarm = Alarm.query.filter(
            Alarm.device_id == bin_obj.device_id,
            Alarm.type == 'material_low',
            Alarm.status == 'open',
            Alarm.context.contains({"bin_index": bin_obj.bin_index})
        ).first()
        
        if not existing_alarm:
            # Calculate percentage remaining
            pct_remaining = (bin_obj.remaining / bin_obj.capacity * 100) if bin_obj.capacity else 0
            
            # Create material low alarm
            alarm = Alarm(
                device_id=bin_obj.device_id,
                type='material_low',
                severity='warn' if pct_remaining > 10 else 'critical',
                title=f"Low material in bin {bin_obj.bin_index}",
                description=f"Material {bin_obj.material_code} is running low ({pct_remaining:.1f}% remaining)",
                status='open',
                context={
                    "bin_index": bin_obj.bin_index,
                    "material_code": bin_obj.material_code,
                    "remaining": float(bin_obj.remaining),
                    "capacity": float(bin_obj.capacity),
                    "threshold_pct": float(bin_obj.threshold_low_pct),
                    "remaining_pct": pct_remaining
                }
            )
            db.session.add(alarm)
            alarms_created += 1
    
    db.session.commit()
    return alarms_created