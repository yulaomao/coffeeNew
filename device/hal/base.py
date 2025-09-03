from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import asyncio

class SensorType(Enum):
    TEMPERATURE = "temperature"
    CUP_PRESENT = "cup_present" 
    DOOR_OPEN = "door_open"
    WATER_LEVEL = "water_level"
    BIN_LEVEL = "bin_level"

class ActuatorType(Enum):
    GRINDER = "grinder"
    PUMP = "pump"
    HEATER = "heater"
    MIXER = "mixer"
    DOOR_LOCK = "door_lock"
    DISPENSER = "dispenser"

@dataclass
class SensorReading:
    sensor_type: SensorType
    value: Any
    timestamp: float
    unit: Optional[str] = None

@dataclass
class ActuatorCommand:
    actuator_type: ActuatorType
    action: str
    parameters: Dict[str, Any]
    duration_ms: Optional[int] = None

@dataclass
class BrewStep:
    action: str
    parameters: Dict[str, Any]
    duration_ms: int
    expected_outcome: Optional[str] = None

class HALException(Exception):
    """Hardware Abstraction Layer exception"""
    pass

class InsufficientMaterialException(HALException):
    """Raised when insufficient material for operation"""
    def __init__(self, material: str, required: float, available: float):
        self.material = material
        self.required = required
        self.available = available
        super().__init__(f"Insufficient {material}: required {required}, available {available}")

class HardwareAbstractionLayer(ABC):
    """Abstract base class for hardware abstraction layer"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize hardware systems"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Shutdown hardware systems"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get overall hardware status"""
        pass
    
    # Sensor operations
    @abstractmethod
    async def read_sensor(self, sensor_type: SensorType) -> SensorReading:
        """Read value from sensor"""
        pass
    
    @abstractmethod
    async def read_all_sensors(self) -> List[SensorReading]:
        """Read all sensor values"""
        pass
    
    # Actuator operations
    @abstractmethod
    async def control_actuator(self, command: ActuatorCommand) -> bool:
        """Control actuator"""
        pass
    
    # High-level operations
    @abstractmethod
    async def brew_coffee(self, recipe: Dict[str, Any], 
                         progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """Brew coffee according to recipe"""
        pass
    
    @abstractmethod
    async def open_door(self, duration_seconds: int = 60) -> bool:
        """Open maintenance door"""
        pass
    
    @abstractmethod
    async def run_cleaning_cycle(self, cycle_type: str = "basic") -> bool:
        """Run cleaning cycle"""
        pass
    
    @abstractmethod
    async def calibrate_system(self) -> bool:
        """Run system calibration"""
        pass
    
    # Material management
    @abstractmethod
    async def get_bin_levels(self) -> Dict[int, float]:
        """Get current bin levels"""
        pass
    
    @abstractmethod
    async def set_bin_level(self, bin_index: int, level: float):
        """Set bin level (for maintenance)"""
        pass
    
    # Safety and diagnostics
    @abstractmethod
    async def emergency_stop(self) -> bool:
        """Emergency stop all operations"""
        pass
    
    @abstractmethod
    async def self_test(self) -> Dict[str, bool]:
        """Run self-test on all systems"""
        pass
    
    @abstractmethod
    def is_safe_to_operate(self) -> bool:
        """Check if device is safe to operate"""
        pass