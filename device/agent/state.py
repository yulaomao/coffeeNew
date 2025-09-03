import asyncio
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from ..storage.db import db
from ..storage.models import DeviceState, DeviceStatus
from ..config import config
from ..utils.time import utc_now
from ..utils.net import get_network_info, check_internet_connection
from ..hal.simulator import simulator
from ..hal.sensors import simulator_sensors

class StateManager:
    """Manages device state collection and reporting"""
    
    def __init__(self):
        self.current_state = DeviceState(
            device_id=config.DEVICE_ID,
            status=DeviceStatus.IDLE,
            last_seen=utc_now(),
            firmware_version="1.0.0",
            uptime_seconds=0
        )
        self.start_time = utc_now()
    
    async def update_state(self, updates: Dict[str, Any]):
        """Update current device state"""
        for key, value in updates.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
        
        self.current_state.last_seen = utc_now()
        
        # Store in database for persistence
        db.set_kv("device_state", self.current_state.model_dump())
        
        logger.debug(f"Updated device state: {updates}")
    
    async def collect_current_state(self) -> DeviceState:
        """Collect current device state from all sources"""
        try:
            # Get hardware status
            hal_status = await simulator.get_status()
            
            # Get network info
            network_info = get_network_info()
            
            # Get sensor readings
            sensor_readings = await simulator_sensors.get_all_readings()
            
            # Calculate uptime
            uptime = int((utc_now() - self.start_time).total_seconds())
            
            # Update state
            await self.update_state({
                "temperature": sensor_readings.get("temperature"),
                "wifi_ssid": network_info.get("wifi_ssid"),
                "wifi_signal": network_info.get("wifi_signal"),
                "ip": network_info.get("ip"),
                "uptime_seconds": uptime,
                "is_online": network_info.get("connected", False)
            })
            
            return self.current_state
        
        except Exception as e:
            logger.error(f"Failed to collect device state: {e}")
            return self.current_state
    
    async def get_status_report_data(self) -> Dict[str, Any]:
        """Get data for status report to backend"""
        state = await self.collect_current_state()
        
        return {
            "status": state.status,
            "temperature": state.temperature,
            "wifi_ssid": state.wifi_ssid,
            "wifi_signal": state.wifi_signal,
            "ip": state.ip,
            "firmware_version": state.firmware_version,
            "uptime_seconds": state.uptime_seconds
        }
    
    def set_status(self, status: DeviceStatus):
        """Set device status"""
        asyncio.create_task(self.update_state({"status": status}))
    
    def get_current_status(self) -> DeviceStatus:
        """Get current device status"""
        return self.current_state.status
    
    def is_online(self) -> bool:
        """Check if device is online"""
        return self.current_state.is_online
    
    def get_uptime_seconds(self) -> int:
        """Get uptime in seconds"""
        return int((utc_now() - self.start_time).total_seconds())
    
    async def check_connectivity(self) -> bool:
        """Check backend connectivity"""
        try:
            from ..backend.client import backend_client
            return await backend_client.test_connection()
        except Exception:
            return False

# Global state manager
state_manager = StateManager()