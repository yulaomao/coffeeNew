from .base import SensorType, SensorReading
from .simulator import simulator
from .real_stub import real_hardware
from typing import Dict, Any, List
import asyncio
from loguru import logger

class SensorManager:
    """Unified sensor management interface"""
    
    def __init__(self, hal_instance):
        self.hal = hal_instance
        self._sensor_cache = {}
        self._cache_ttl = {}
        self._cache_duration = 1.0  # Cache readings for 1 second
    
    async def read_temperature(self) -> float:
        """Read temperature sensor"""
        reading = await self._cached_read(SensorType.TEMPERATURE)
        return reading.value if reading else 0.0
    
    async def read_cup_present(self) -> bool:
        """Check if cup is present"""
        reading = await self._cached_read(SensorType.CUP_PRESENT)
        return reading.value if reading else False
    
    async def read_door_status(self) -> bool:
        """Check if door is open"""
        reading = await self._cached_read(SensorType.DOOR_OPEN)
        return reading.value if reading else False
    
    async def read_water_level(self) -> float:
        """Read water level percentage"""
        reading = await self._cached_read(SensorType.WATER_LEVEL)
        return reading.value if reading else 0.0
    
    async def _cached_read(self, sensor_type: SensorType) -> SensorReading:
        """Read sensor value with caching"""
        now = asyncio.get_event_loop().time()
        
        # Check cache
        if sensor_type in self._sensor_cache:
            if now - self._cache_ttl.get(sensor_type, 0) < self._cache_duration:
                return self._sensor_cache[sensor_type]
        
        # Read fresh value
        try:
            reading = await self.hal.read_sensor(sensor_type)
            self._sensor_cache[sensor_type] = reading
            self._cache_ttl[sensor_type] = now
            return reading
        except Exception as e:
            logger.error(f"Failed to read sensor {sensor_type}: {e}")
            return SensorReading(sensor_type, None, now)
    
    async def get_all_readings(self) -> Dict[str, Any]:
        """Get all sensor readings"""
        return {
            "temperature": await self.read_temperature(),
            "cup_present": await self.read_cup_present(),
            "door_open": await self.read_door_status(),
            "water_level": await self.read_water_level()
        }
    
    def clear_cache(self):
        """Clear sensor cache"""
        self._sensor_cache.clear()
        self._cache_ttl.clear()

# Create sensor managers for both HAL implementations
simulator_sensors = SensorManager(simulator)
real_hardware_sensors = SensorManager(real_hardware)