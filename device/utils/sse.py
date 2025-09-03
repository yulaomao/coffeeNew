from typing import Dict, Any, Callable, List
import asyncio
from loguru import logger

class SSEEvent:
    """Server-Sent Event for internal communication"""
    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = asyncio.get_event_loop().time()

class EventBus:
    """Simple event bus for internal application communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: List[SSEEvent] = []
        self._max_history = 100
    
    def subscribe(self, event_type: str, callback: Callable[[SSEEvent], None]):
        """Subscribe to events of a specific type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[SSEEvent], None]):
        """Unsubscribe from events"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                pass
    
    def emit(self, event_type: str, data: Any = None):
        """Emit an event"""
        event = SSEEvent(event_type, data)
        
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Notify subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")
        
        logger.debug(f"Emitted event: {event_type}")
    
    def get_recent_events(self, event_type: str = None, limit: int = 10) -> List[SSEEvent]:
        """Get recent events, optionally filtered by type"""
        events = self._history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def clear_history(self):
        """Clear event history"""
        self._history.clear()

# Event type constants
EVENT_DEVICE_STATUS_CHANGED = "device_status_changed"
EVENT_MATERIAL_UPDATED = "material_updated"
EVENT_ORDER_CREATED = "order_created"
EVENT_ORDER_STATUS_CHANGED = "order_status_changed"
EVENT_PAYMENT_STATUS_CHANGED = "payment_status_changed"
EVENT_COMMAND_RECEIVED = "command_received"
EVENT_COMMAND_COMPLETED = "command_completed"
EVENT_RECIPE_UPDATED = "recipe_updated"
EVENT_UI_PAGE_CHANGED = "ui_page_changed"
EVENT_NETWORK_STATUS_CHANGED = "network_status_changed"
EVENT_ERROR_OCCURRED = "error_occurred"

# Global event bus instance
event_bus = EventBus()