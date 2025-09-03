import asyncio
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from ..storage.db import db
from ..storage.models import Bin
from ..config import config
from ..utils.time import utc_now
from ..utils.sse import event_bus, EVENT_MATERIAL_UPDATED
from ..hal.simulator import simulator

class MaterialManager:
    """Manages material levels and reporting"""
    
    def __init__(self):
        self.bins: List[Bin] = []
        self.last_report_time = None
        self._initialize_bins()
    
    def _initialize_bins(self):
        """Initialize bins with default data"""
        # Try to load from database first
        saved_bins = db.get_bins()
        if saved_bins:
            self.bins = saved_bins
            logger.info(f"Loaded {len(self.bins)} bins from database")
        else:
            # Initialize default bins
            default_bins = [
                Bin(
                    bin_index=0,
                    material_code="BEAN_A",
                    remaining=85.0,
                    capacity=100.0,
                    unit="g",
                    threshold_low_pct=20,
                    last_updated=utc_now()
                ),
                Bin(
                    bin_index=1,
                    material_code="BEAN_B", 
                    remaining=92.0,
                    capacity=100.0,
                    unit="g",
                    threshold_low_pct=20,
                    last_updated=utc_now()
                ),
                Bin(
                    bin_index=2,
                    material_code="MILK_POWDER",
                    remaining=45.0,
                    capacity=50.0,
                    unit="g",
                    threshold_low_pct=20,
                    last_updated=utc_now()
                ),
                Bin(
                    bin_index=3,
                    material_code="SUGAR",
                    remaining=78.0,
                    capacity=30.0,
                    unit="g", 
                    threshold_low_pct=20,
                    last_updated=utc_now()
                ),
                Bin(
                    bin_index=4,
                    material_code="WATER",
                    remaining=100.0,
                    capacity=500.0,
                    unit="ml",
                    threshold_low_pct=10,
                    last_updated=utc_now()
                )
            ]
            
            self.bins = default_bins
            self._save_bins()
            logger.info("Initialized default bins")
    
    def _save_bins(self):
        """Save bins to database"""
        db.save_bins(self.bins)
    
    async def sync_with_hal(self):
        """Sync bin levels with hardware abstraction layer"""
        try:
            hal_levels = await simulator.get_bin_levels()
            
            for bin_data in self.bins:
                if bin_data.bin_index in hal_levels:
                    # Convert percentage to actual amount
                    hal_percentage = hal_levels[bin_data.bin_index]
                    actual_amount = (hal_percentage / 100.0) * bin_data.capacity
                    
                    if abs(actual_amount - bin_data.remaining) > 0.1:  # Threshold for updates
                        bin_data.remaining = actual_amount
                        bin_data.last_updated = utc_now()
                        logger.debug(f"Updated bin {bin_data.bin_index} from HAL: {actual_amount:.1f} {bin_data.unit}")
            
            self._save_bins()
            event_bus.emit(EVENT_MATERIAL_UPDATED, {"bins": self.get_bins_data()})
            
        except Exception as e:
            logger.error(f"Failed to sync with HAL: {e}")
    
    def get_bins(self) -> List[Bin]:
        """Get all bins"""
        return self.bins.copy()
    
    def get_bins_data(self) -> List[Dict[str, Any]]:
        """Get bins data for reporting"""
        return [
            {
                "bin_index": bin_data.bin_index,
                "material_code": bin_data.material_code,
                "remaining": bin_data.remaining,
                "capacity": bin_data.capacity,
                "unit": bin_data.unit
            }
            for bin_data in self.bins
        ]
    
    def get_bin_by_index(self, bin_index: int) -> Bin:
        """Get bin by index"""
        for bin_data in self.bins:
            if bin_data.bin_index == bin_index:
                return bin_data
        return None
    
    def get_bin_by_material(self, material_code: str) -> Bin:
        """Get bin by material code"""
        for bin_data in self.bins:
            if bin_data.material_code == material_code:
                return bin_data
        return None
    
    def is_material_sufficient(self, material_code: str, required_amount: float) -> bool:
        """Check if material is sufficient for required amount"""
        bin_data = self.get_bin_by_material(material_code)
        if not bin_data:
            return False
        
        return bin_data.is_sufficient(required_amount)
    
    def check_recipe_availability(self, recipe_materials: Dict[str, float]) -> Dict[str, bool]:
        """Check if all materials are available for recipe"""
        availability = {}
        
        for material_code, required_amount in recipe_materials.items():
            availability[material_code] = self.is_material_sufficient(material_code, required_amount)
        
        return availability
    
    def consume_materials(self, materials: Dict[str, float]):
        """Consume materials (after successful brewing)"""
        for material_code, amount in materials.items():
            bin_data = self.get_bin_by_material(material_code)
            if bin_data:
                bin_data.remaining = max(0.0, bin_data.remaining - amount)
                bin_data.last_updated = utc_now()
                logger.info(f"Consumed {amount} {bin_data.unit} of {material_code}, remaining: {bin_data.remaining}")
        
        self._save_bins()
        event_bus.emit(EVENT_MATERIAL_UPDATED, {"bins": self.get_bins_data()})
    
    def set_bin_level(self, bin_index: int, new_level: float):
        """Set bin level (for maintenance/refill)"""
        bin_data = self.get_bin_by_index(bin_index)
        if bin_data:
            bin_data.remaining = max(0.0, min(bin_data.capacity, new_level))
            bin_data.last_updated = utc_now()
            self._save_bins()
            
            logger.info(f"Set bin {bin_index} ({bin_data.material_code}) level to {new_level} {bin_data.unit}")
            event_bus.emit(EVENT_MATERIAL_UPDATED, {"bins": self.get_bins_data()})
            
            return True
        return False
    
    def calibrate_bin(self, bin_index: int, actual_level: float):
        """Calibrate bin level based on actual measurement"""
        return self.set_bin_level(bin_index, actual_level)
    
    def get_low_bins(self) -> List[Bin]:
        """Get bins with low material levels"""
        return [bin_data for bin_data in self.bins if bin_data.is_low()]
    
    def get_empty_bins(self) -> List[Bin]:
        """Get empty bins"""
        return [bin_data for bin_data in self.bins if bin_data.remaining <= 0]
    
    async def get_report_data(self) -> Dict[str, Any]:
        """Get material report data for backend"""
        # Sync with HAL first
        await self.sync_with_hal()
        
        return {
            "bins": self.get_bins_data(),
            "timestamp": utc_now().isoformat()
        }
    
    def needs_reporting(self) -> bool:
        """Check if materials need to be reported"""
        if self.last_report_time is None:
            return True
        
        # Report if any bin changed significantly since last report
        now = utc_now()
        for bin_data in self.bins:
            if (now - bin_data.last_updated).total_seconds() < 300:  # Changed in last 5 minutes
                return True
        
        return False
    
    def mark_reported(self):
        """Mark materials as reported"""
        self.last_report_time = utc_now()
    
    def get_material_summary(self) -> Dict[str, Any]:
        """Get material summary for UI"""
        total_bins = len(self.bins)
        low_bins = len(self.get_low_bins())
        empty_bins = len(self.get_empty_bins())
        
        return {
            "total_bins": total_bins,
            "low_bins": low_bins,
            "empty_bins": empty_bins,
            "normal_bins": total_bins - low_bins - empty_bins,
            "needs_attention": low_bins > 0 or empty_bins > 0
        }

# Global material manager
material_manager = MaterialManager()