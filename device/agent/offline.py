from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from ..config import config
from ..storage.db import db
from ..utils.time import utc_now

class OfflineManager:
    """Manages offline operation and data synchronization"""
    
    def __init__(self):
        self.is_offline = False
        self.offline_since = None
        self.last_successful_sync = None
        self.offline_threshold = timedelta(seconds=config.OFFLINE_THRESHOLD_SEC)
        
        # Load last sync time from database
        self.last_successful_sync = db.get_kv("last_successful_sync")
        if self.last_successful_sync:
            self.last_successful_sync = datetime.fromisoformat(self.last_successful_sync)
    
    def mark_online(self):
        """Mark device as online after successful backend communication"""
        was_offline = self.is_offline
        self.is_offline = False
        self.offline_since = None
        self.last_successful_sync = utc_now()
        
        # Save to database
        db.set_kv("last_successful_sync", self.last_successful_sync.isoformat())
        
        if was_offline:
            logger.info("Device back online")
    
    def mark_offline(self):
        """Mark device as offline after failed backend communication"""
        if not self.is_offline:
            self.is_offline = True
            self.offline_since = utc_now()
            logger.warning("Device marked as offline")
    
    def check_offline_status(self) -> bool:
        """Check if device should be considered offline based on last sync"""
        if self.last_successful_sync is None:
            return True
        
        time_since_sync = utc_now() - self.last_successful_sync
        should_be_offline = time_since_sync > self.offline_threshold
        
        if should_be_offline and not self.is_offline:
            self.mark_offline()
        
        return self.is_offline
    
    def get_offline_duration(self) -> int:
        """Get offline duration in seconds"""
        if not self.is_offline or not self.offline_since:
            return 0
        
        return int((utc_now() - self.offline_since).total_seconds())
    
    def can_accept_orders(self) -> bool:
        """Check if device can accept new orders based on offline policy"""
        if self.is_offline:
            logger.info("Orders disabled: device is offline")
            return False
        
        return True
    
    def can_process_payments(self) -> bool:
        """Check if device can process payments"""
        if self.is_offline:
            logger.info("Payments disabled: device is offline")
            return False
        
        return True
    
    def can_perform_operations(self) -> Dict[str, bool]:
        """Get allowed operations based on offline status"""
        online_ops = {
            "accept_orders": True,
            "process_payments": True,
            "download_recipes": True,
            "report_status": True,
            "receive_commands": True
        }
        
        offline_ops = {
            "accept_orders": False,  # Disabled when offline
            "process_payments": False,  # Disabled when offline
            "download_recipes": False,  # Disabled when offline
            "report_status": False,  # Will be queued
            "receive_commands": False,  # Disabled when offline
            "maintenance_operations": True,  # Always allowed
            "test_brewing": True,  # Always allowed for testing
            "material_management": True,  # Local operations allowed
            "view_logs": True,  # Local operations allowed
        }
        
        return offline_ops if self.is_offline else online_ops
    
    def get_sync_strategy(self) -> str:
        """Get synchronization strategy based on offline duration"""
        if not self.is_offline:
            return "normal"
        
        offline_duration = self.get_offline_duration()
        
        if offline_duration < 300:  # 5 minutes
            return "quick_retry"
        elif offline_duration < 3600:  # 1 hour
            return "standard_retry"
        else:
            return "full_resync"
    
    def should_queue_data(self) -> bool:
        """Check if data should be queued for later upload"""
        return self.is_offline
    
    def get_offline_status_message(self) -> str:
        """Get user-friendly offline status message"""
        if not self.is_offline:
            return "设备在线"
        
        duration = self.get_offline_duration()
        
        if duration < 60:
            return "网络连接中..."
        elif duration < 300:
            return "网络暂时中断，正在重试连接"
        elif duration < 1800:
            return "网络连接中断，请检查网络设置"
        else:
            return "设备离线，请联系技术支持"
    
    def get_estimated_recovery_time(self) -> str:
        """Get estimated recovery time message"""
        if not self.is_offline:
            return None
        
        duration = self.get_offline_duration()
        
        if duration < 300:
            return "预计1-2分钟内恢复"
        elif duration < 1800:
            return "预计5-10分钟内恢复"
        else:
            return "恢复时间待定"
    
    def get_offline_summary(self) -> Dict[str, Any]:
        """Get comprehensive offline status summary"""
        return {
            "is_offline": self.is_offline,
            "offline_since": self.offline_since.isoformat() if self.offline_since else None,
            "offline_duration_seconds": self.get_offline_duration(),
            "last_successful_sync": self.last_successful_sync.isoformat() if self.last_successful_sync else None,
            "status_message": self.get_offline_status_message(),
            "estimated_recovery": self.get_estimated_recovery_time(),
            "allowed_operations": self.can_perform_operations(),
            "sync_strategy": self.get_sync_strategy()
        }
    
    def reset_offline_status(self):
        """Reset offline status (for testing/maintenance)"""
        self.is_offline = False
        self.offline_since = None
        self.last_successful_sync = utc_now()
        db.set_kv("last_successful_sync", self.last_successful_sync.isoformat())
        logger.info("Offline status reset")

# Global offline manager
offline_manager = OfflineManager()