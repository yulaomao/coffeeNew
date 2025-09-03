from .base import ActuatorType, ActuatorCommand
from .simulator import simulator
from .real_stub import real_hardware
from typing import Dict, Any, Optional
from loguru import logger
import asyncio

class ActuatorManager:
    """Unified actuator control interface"""
    
    def __init__(self, hal_instance):
        self.hal = hal_instance
    
    async def grind_beans(self, bin_material: str, amount: float, duration_ms: int = 3000) -> bool:
        """Control coffee grinder"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.GRINDER,
            action="grind",
            parameters={
                "bin": bin_material,
                "amount": amount,
                "unit": "g"
            },
            duration_ms=duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Grinder control failed: {e}")
            return False
    
    async def pump_water(self, volume_ml: int, duration_ms: int = 25000) -> bool:
        """Control water pump"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.PUMP,
            action="pump",
            parameters={
                "volume_ml": volume_ml,
                "pressure": "normal"
            },
            duration_ms=duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Pump control failed: {e}")
            return False
    
    async def heat_water(self, target_temp: float = 92.0, duration_ms: int = 10000) -> bool:
        """Control water heater"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.HEATER,
            action="heat",
            parameters={
                "target_temperature": target_temp,
                "unit": "celsius"
            },
            duration_ms=duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Heater control failed: {e}")
            return False
    
    async def mix_ingredients(self, duration_ms: int = 5000) -> bool:
        """Control mixer"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.MIXER,
            action="mix",
            parameters={
                "speed": "medium"
            },
            duration_ms=duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Mixer control failed: {e}")
            return False
    
    async def dispense_powder(self, bin_material: str, amount: float, duration_ms: int = 2000) -> bool:
        """Control powder dispenser"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.DISPENSER,
            action="dispense",
            parameters={
                "bin": bin_material,
                "amount": amount,
                "unit": "g"
            },
            duration_ms=duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Dispenser control failed: {e}")
            return False
    
    async def control_door_lock(self, action: str, duration_seconds: int = 60) -> bool:
        """Control maintenance door lock"""
        command = ActuatorCommand(
            actuator_type=ActuatorType.DOOR_LOCK,
            action=action,  # "unlock" or "lock"
            parameters={
                "duration_seconds": duration_seconds
            }
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Door lock control failed: {e}")
            return False
    
    async def emergency_stop_all(self) -> bool:
        """Emergency stop all actuators"""
        try:
            return await self.hal.emergency_stop()
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False
    
    async def test_actuator(self, actuator_type: ActuatorType, test_duration_ms: int = 1000) -> bool:
        """Test individual actuator"""
        command = ActuatorCommand(
            actuator_type=actuator_type,
            action="test",
            parameters={"test_mode": True},
            duration_ms=test_duration_ms
        )
        
        try:
            return await self.hal.control_actuator(command)
        except Exception as e:
            logger.error(f"Actuator test failed for {actuator_type}: {e}")
            return False
    
    async def run_maintenance_sequence(self, sequence_type: str) -> bool:
        """Run predefined maintenance sequence"""
        logger.info(f"Running maintenance sequence: {sequence_type}")
        
        try:
            if sequence_type == "flush":
                # Flush water system
                await self.pump_water(100, 5000)
                return True
            
            elif sequence_type == "rinse":
                # Rinse brewing chamber
                await self.pump_water(50, 3000)
                await asyncio.sleep(1.0)
                await self.pump_water(50, 3000)
                return True
            
            elif sequence_type == "clean":
                # Basic cleaning cycle
                return await self.hal.run_cleaning_cycle("basic")
            
            elif sequence_type == "deep_clean":
                # Deep cleaning cycle
                return await self.hal.run_cleaning_cycle("deep")
            
            else:
                logger.warning(f"Unknown maintenance sequence: {sequence_type}")
                return False
        
        except Exception as e:
            logger.error(f"Maintenance sequence failed: {e}")
            return False

# Create actuator managers for both HAL implementations
simulator_actuators = ActuatorManager(simulator)
real_hardware_actuators = ActuatorManager(real_hardware)