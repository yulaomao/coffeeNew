import asyncio
from typing import List, Optional
from datetime import datetime
from loguru import logger
from .db import db
from .models import QueueItem
from ..utils.time import utc_now

class UploadQueue:
    """Queue manager for items pending upload to backend"""
    
    def __init__(self):
        self._processing = False
    
    async def add_order(self, order_data: dict, order_id: str):
        """Add order to upload queue"""
        item = QueueItem(
            item_type="order",
            item_id=order_id,
            payload=order_data,
            created_at=utc_now()
        )
        db.add_to_queue(item)
        logger.info(f"Added order {order_id} to upload queue")
    
    async def add_command_result(self, command_result: dict, command_id: str):
        """Add command result to upload queue"""
        item = QueueItem(
            item_type="command_result",
            item_id=command_id,
            payload=command_result,
            created_at=utc_now()
        )
        db.add_to_queue(item)
        logger.info(f"Added command result {command_id} to upload queue")
    
    async def add_status_report(self, status_data: dict):
        """Add status report to upload queue"""
        import uuid
        status_id = str(uuid.uuid4())
        item = QueueItem(
            item_type="status",
            item_id=status_id,
            payload=status_data,
            created_at=utc_now()
        )
        db.add_to_queue(item)
        logger.debug("Added status report to upload queue")
    
    async def add_material_report(self, material_data: dict):
        """Add material report to upload queue"""
        import uuid
        material_id = str(uuid.uuid4())
        item = QueueItem(
            item_type="material",
            item_id=material_id,
            payload=material_data,
            created_at=utc_now()
        )
        db.add_to_queue(item)
        logger.info("Added material report to upload queue")
    
    def get_pending_items(self, item_type: Optional[str] = None) -> List[QueueItem]:
        """Get pending items from queue"""
        return db.get_pending_queue_items(item_type)
    
    async def process_item(self, item: QueueItem, upload_callback) -> bool:
        """Process a single queue item"""
        try:
            success = await upload_callback(item)
            if success:
                db.mark_queue_item_processed(item.id)
                logger.info(f"Successfully processed queue item {item.id} ({item.item_type})")
                return True
            else:
                db.increment_queue_retry(item.id, "Upload failed")
                logger.warning(f"Failed to process queue item {item.id}, retry count: {item.retry_count + 1}")
                return False
        except Exception as e:
            error_msg = str(e)
            db.increment_queue_retry(item.id, error_msg)
            logger.error(f"Error processing queue item {item.id}: {error_msg}")
            return False
    
    async def process_all_pending(self, upload_callback):
        """Process all pending items in queue"""
        if self._processing:
            logger.debug("Queue processing already in progress")
            return
        
        self._processing = True
        try:
            pending_items = self.get_pending_items()
            logger.info(f"Processing {len(pending_items)} pending queue items")
            
            for item in pending_items:
                await self.process_item(item, upload_callback)
                # Small delay to avoid overwhelming the backend
                await asyncio.sleep(0.1)
        
        finally:
            self._processing = False
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        pending_orders = len(self.get_pending_items("order"))
        pending_results = len(self.get_pending_items("command_result"))
        pending_status = len(self.get_pending_items("status"))
        pending_materials = len(self.get_pending_items("material"))
        
        return {
            "total_pending": pending_orders + pending_results + pending_status + pending_materials,
            "pending_orders": pending_orders,
            "pending_command_results": pending_results,
            "pending_status": pending_status,
            "pending_materials": pending_materials,
            "is_processing": self._processing
        }
    
    def clear_failed_items(self, max_age_hours: int = 24):
        """Clear items that have exceeded max retry attempts and are old"""
        # This would require additional database operations
        # For now, items that exceed max retries will just be ignored
        pass

# Global queue instance
upload_queue = UploadQueue()