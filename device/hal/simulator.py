from typing import Dict, Any, Optional, Callable, List
import asyncio
import random
from datetime import datetime
from loguru import logger
from .base import (
    HardwareAbstractionLayer, SensorReading, ActuatorCommand, BrewStep,
    SensorType, ActuatorType, InsufficientMaterialException
)
from ..utils.time import utc_now

class CoffeeSimulator(HardwareAbstractionLayer):
    """Simulator implementation of hardware abstraction layer"""
    
    def __init__(self):
        self.initialized = False
        self.is_brewing = False
        self.door_open = False
        self.emergency_stopped = False
        
        # Simulated sensor values
        self.temperature = 85.0  # Celsius
        self.water_level = 100.0  # Percentage
        self.cup_present = False
        
        # Bin levels (percentage full)
        self.bin_levels = {
            0: 85.0,  # BEAN_A
            1: 92.0,  # BEAN_B  
            2: 45.0,  # MILK_POWDER
            3: 78.0,  # SUGAR
            4: 100.0, # WATER (always full in simulation)
        }
        
        # Material mapping
        self.bin_materials = {
            0: "BEAN_A",
            1: "BEAN_B", 
            2: "MILK_POWDER",
            3: "SUGAR",
            4: "WATER"
        }
        
        # Bin capacities (in grams, except water in ml)
        self.bin_capacities = {
            0: 1000,  # BEAN_A
            1: 1000,  # BEAN_B
            2: 500,   # MILK_POWDER  
            3: 300,   # SUGAR
            4: 5000,  # WATER
        }
        
        self.last_maintenance = utc_now()
    
    async def initialize(self) -> bool:
        """Initialize simulated hardware"""
        logger.info("Initializing coffee machine simulator...")
        await asyncio.sleep(0.5)  # Simulate initialization time
        
        self.initialized = True
        self.emergency_stopped = False
        self.temperature = 85.0
        self.door_open = False
        
        logger.info("Coffee machine simulator initialized")
        return True
    
    async def shutdown(self):
        """Shutdown simulated hardware"""
        logger.info("Shutting down coffee machine simulator...")
        self.initialized = False
        self.is_brewing = False
        await asyncio.sleep(0.3)
        logger.info("Coffee machine simulator shut down")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get overall hardware status"""
        return {
            "initialized": self.initialized,
            "is_brewing": self.is_brewing,
            "door_open": self.door_open,
            "emergency_stopped": self.emergency_stopped,
            "temperature": self.temperature,
            "water_level": self.water_level,
            "safe_to_operate": self.is_safe_to_operate()
        }
    
    async def read_sensor(self, sensor_type: SensorType) -> SensorReading:
        """Read simulated sensor value"""
        timestamp = asyncio.get_event_loop().time()
        
        if sensor_type == SensorType.TEMPERATURE:
            # Add some random variation to temperature
            temp_variation = random.uniform(-2.0, 2.0)
            value = max(20.0, min(95.0, self.temperature + temp_variation))
            return SensorReading(sensor_type, value, timestamp, "°C")
        
        elif sensor_type == SensorType.CUP_PRESENT:
            return SensorReading(sensor_type, self.cup_present, timestamp)
        
        elif sensor_type == SensorType.DOOR_OPEN:
            return SensorReading(sensor_type, self.door_open, timestamp)
        
        elif sensor_type == SensorType.WATER_LEVEL:
            return SensorReading(sensor_type, self.water_level, timestamp, "%")
        
        else:
            return SensorReading(sensor_type, None, timestamp)
    
    async def read_all_sensors(self) -> List[SensorReading]:
        """Read all sensor values"""
        sensors = [
            SensorType.TEMPERATURE,
            SensorType.CUP_PRESENT,
            SensorType.DOOR_OPEN,
            SensorType.WATER_LEVEL
        ]
        
        readings = []
        for sensor in sensors:
            reading = await self.read_sensor(sensor)
            readings.append(reading)
        
        return readings
    
    async def control_actuator(self, command: ActuatorCommand) -> bool:
        """Control simulated actuator"""
        if not self.is_safe_to_operate():
            return False
        
        logger.info(f"Actuating {command.actuator_type.value}: {command.action}")
        
        # Simulate actuator response time
        if command.duration_ms:
            await asyncio.sleep(command.duration_ms / 1000.0)
        else:
            await asyncio.sleep(0.1)
        
        # Update simulator state based on command
        if command.actuator_type == ActuatorType.DOOR_LOCK and command.action == "unlock":
            self.door_open = True
        elif command.actuator_type == ActuatorType.DOOR_LOCK and command.action == "lock":
            self.door_open = False
        
        return True
    
    async def brew_coffee(self, recipe: Dict[str, Any], 
                         progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """Simulate coffee brewing process"""
        if not self.is_safe_to_operate():
            raise Exception("Device not safe to operate")
        
        if self.is_brewing:
            raise Exception("Already brewing")
        
        self.is_brewing = True
        consumed_materials = {}
        
        try:
            steps = recipe.get("steps", [])
            materials = recipe.get("materials", {})
            
            # Check material availability first
            for material_code, required_amount in materials.items():
                bin_index = self._get_bin_for_material(material_code)
                if bin_index is None:
                    raise Exception(f"No bin configured for material {material_code}")
                
                current_level = self.bin_levels[bin_index]
                capacity = self.bin_capacities[bin_index]
                available = (current_level / 100.0) * capacity
                
                if available < required_amount:
                    raise InsufficientMaterialException(material_code, required_amount, available)
            
            total_duration = sum(step.get("duration_ms", 1000) for step in steps)
            elapsed = 0
            
            for i, step in enumerate(steps):
                step_duration = step.get("duration_ms", 1000)
                action = step.get("action", "unknown")
                
                # Update progress
                if progress_callback:
                    progress = elapsed / total_duration
                    progress_callback(f"执行步骤: {action}", progress)
                
                logger.info(f"Brewing step {i+1}/{len(steps)}: {action}")
                
                # Simulate step execution
                step_start = asyncio.get_event_loop().time()
                while (asyncio.get_event_loop().time() - step_start) * 1000 < step_duration:
                    if not self.is_safe_to_operate() or self.emergency_stopped:
                        raise Exception("Brewing interrupted")
                    
                    # Update progress during step
                    if progress_callback:
                        step_elapsed = (asyncio.get_event_loop().time() - step_start) * 1000
                        step_progress = min(1.0, step_elapsed / step_duration)
                        overall_progress = (elapsed + step_elapsed) / total_duration
                        progress_callback(f"执行步骤: {action}", overall_progress)
                    
                    await asyncio.sleep(0.1)
                
                # Consume materials for this step
                if "bin" in step and "amount" in step:
                    bin_material = step["bin"]
                    amount = step["amount"]
                    bin_index = self._get_bin_for_material(bin_material)
                    if bin_index is not None:
                        self._consume_material(bin_index, amount)
                        consumed_materials[bin_material] = consumed_materials.get(bin_material, 0) + amount
                
                elapsed += step_duration
            
            # Final progress update
            if progress_callback:
                progress_callback("完成制作", 1.0)
            
            logger.info(f"Coffee brewing completed: {recipe.get('name', 'Unknown')}")
            
            return {
                "success": True,
                "recipe_id": recipe.get("id"),
                "duration_ms": total_duration,
                "consumed": consumed_materials,
                "completed_at": utc_now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Brewing failed: {e}")
            if progress_callback:
                progress_callback("制作失败", 0.0)
            
            return {
                "success": False,
                "error": str(e),
                "consumed": consumed_materials
            }
        
        finally:
            self.is_brewing = False
    
    async def open_door(self, duration_seconds: int = 60) -> bool:
        """Open maintenance door"""
        logger.info(f"Opening maintenance door for {duration_seconds} seconds")
        
        command = ActuatorCommand(
            actuator_type=ActuatorType.DOOR_LOCK,
            action="unlock",
            parameters={"duration_seconds": duration_seconds}
        )
        
        result = await self.control_actuator(command)
        
        if result:
            # Automatically close after duration
            asyncio.create_task(self._auto_close_door(duration_seconds))
        
        return result
    
    async def _auto_close_door(self, delay_seconds: int):
        """Automatically close door after delay"""
        await asyncio.sleep(delay_seconds)
        if self.door_open:
            await self.control_actuator(ActuatorCommand(
                actuator_type=ActuatorType.DOOR_LOCK,
                action="lock",
                parameters={}
            ))
    
    async def run_cleaning_cycle(self, cycle_type: str = "basic") -> bool:
        """Run simulated cleaning cycle"""
        if not self.is_safe_to_operate():
            return False
        
        logger.info(f"Running {cycle_type} cleaning cycle")
        
        # Simulate cleaning duration
        if cycle_type == "deep":
            await asyncio.sleep(3.0)  # 3 seconds for demo
        else:
            await asyncio.sleep(1.5)  # 1.5 seconds for basic
        
        logger.info("Cleaning cycle completed")
        return True
    
    async def calibrate_system(self) -> bool:
        """Run simulated system calibration"""
        logger.info("Running system calibration")
        await asyncio.sleep(2.0)
        logger.info("System calibration completed")
        return True
    
    async def get_bin_levels(self) -> Dict[int, float]:
        """Get current bin levels"""
        return self.bin_levels.copy()
    
    async def set_bin_level(self, bin_index: int, level: float):
        """Set bin level for maintenance"""
        if bin_index in self.bin_levels:
            self.bin_levels[bin_index] = max(0.0, min(100.0, level))
            logger.info(f"Set bin {bin_index} level to {level}%")
    
    async def emergency_stop(self) -> bool:
        """Emergency stop all operations"""
        logger.warning("EMERGENCY STOP activated")
        self.emergency_stopped = True
        self.is_brewing = False
        return True
    
    async def self_test(self) -> Dict[str, bool]:
        """Run simulated self-test"""
        logger.info("Running self-test...")
        await asyncio.sleep(1.0)
        
        return {
            "temperature_sensor": True,
            "water_pump": True,
            "grinder": True,
            "heater": True,
            "door_lock": True,
            "overall": True
        }
    
    def is_safe_to_operate(self) -> bool:
        """Check if device is safe to operate"""
        return (
            self.initialized and
            not self.emergency_stopped and
            not self.door_open and
            self.temperature > 80.0 and
            self.water_level > 10.0
        )
    
    def _get_bin_for_material(self, material_code: str) -> Optional[int]:
        """Get bin index for material code"""
        for bin_index, mat_code in self.bin_materials.items():
            if mat_code == material_code:
                return bin_index
        return None
    
    def _consume_material(self, bin_index: int, amount: float):
        """Consume material from bin"""
        if bin_index not in self.bin_levels:
            return
        
        capacity = self.bin_capacities[bin_index]
        current_amount = (self.bin_levels[bin_index] / 100.0) * capacity
        new_amount = max(0, current_amount - amount)
        new_percentage = (new_amount / capacity) * 100.0
        
        self.bin_levels[bin_index] = new_percentage
        logger.debug(f"Consumed {amount} from bin {bin_index}, new level: {new_percentage:.1f}%")

# Global simulator instance
simulator = CoffeeSimulator()