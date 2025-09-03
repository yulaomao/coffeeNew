import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from ..config import config
from ..constants import *
from ..utils.time import utc_now
from ..utils.sse import event_bus, EVENT_NETWORK_STATUS_CHANGED, EVENT_ERROR_OCCURRED
from ..backend.client import backend_client
from ..storage.queue import upload_queue
from .state import state_manager
from .materials import material_manager  
from .commands import command_processor
from .offline import offline_manager

class AgentSupervisor:
    """Main agent supervisor managing all device operations"""
    
    def __init__(self):
        self.running = False
        self.heartbeat_task = None
        self.command_poll_task = None
        self.upload_task = None
        self.material_sync_task = None
        
        self.heartbeat_interval = config.HEARTBEAT_INTERVAL_SEC
        self.poll_interval = config.POLL_INTERVAL_SEC
        
        # Track last operations
        self.last_heartbeat = None
        self.last_command_poll = None
        self.last_upload_attempt = None
        self.last_material_sync = None
    
    async def start(self):
        """Start the agent supervisor"""
        if self.running:
            logger.warning("Agent supervisor already running")
            return
        
        self.running = True
        logger.info("Starting agent supervisor...")
        
        # Initialize hardware
        from ..hal.simulator import simulator
        await simulator.initialize()
        
        # Set initial device status
        state_manager.set_status(DEVICE_STATUS_IDLE)
        
        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.command_poll_task = asyncio.create_task(self._command_poll_loop())
        self.upload_task = asyncio.create_task(self._upload_loop())
        self.material_sync_task = asyncio.create_task(self._material_sync_loop())
        
        logger.info("Agent supervisor started")
    
    async def stop(self):
        """Stop the agent supervisor"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping agent supervisor...")
        
        # Cancel background tasks
        tasks = [
            self.heartbeat_task,
            self.command_poll_task,
            self.upload_task,
            self.material_sync_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Shutdown hardware
        from ..hal.simulator import simulator
        await simulator.shutdown()
        
        logger.info("Agent supervisor stopped")
    
    async def _heartbeat_loop(self):
        """Heartbeat loop - regularly report status to backend"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(min(self.heartbeat_interval, 60))  # Fallback delay
    
    async def _send_heartbeat(self):
        """Send heartbeat/status to backend"""
        try:
            status_data = await state_manager.get_status_report_data()
            response = await backend_client.post_status(status_data)
            
            if response.ok:
                self.last_heartbeat = utc_now()
                offline_manager.mark_online()
                logger.debug("Heartbeat sent successfully")
            else:
                logger.warning(f"Heartbeat failed: {response.message}")
                offline_manager.mark_offline()
        
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            offline_manager.mark_offline()
    
    async def _command_poll_loop(self):
        """Command polling loop - check for pending commands"""
        while self.running:
            try:
                if not offline_manager.is_offline:
                    await self._poll_commands()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Command poll error: {e}")
                await asyncio.sleep(min(self.poll_interval, 30))  # Fallback delay
    
    async def _poll_commands(self):
        """Poll for pending commands from backend"""
        try:
            response = await backend_client.get_pending_commands()
            
            if response.ok:
                self.last_command_poll = utc_now()
                offline_manager.mark_online()
                
                commands = response.commands
                logger.debug(f"Polled {len(commands)} pending commands")
                
                # Process each command
                for command_data in commands:
                    asyncio.create_task(
                        command_processor.process_command(command_data.model_dump())
                    )
            else:
                logger.warning(f"Command poll failed: {response}")
                offline_manager.mark_offline()
        
        except Exception as e:
            logger.error(f"Failed to poll commands: {e}")
            offline_manager.mark_offline()
    
    async def _upload_loop(self):
        """Upload loop - process pending upload queue"""
        while self.running:
            try:
                if not offline_manager.is_offline:
                    await self._process_upload_queue()
                await asyncio.sleep(30)  # Check upload queue every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Upload loop error: {e}")
                await asyncio.sleep(60)  # Longer delay on error
    
    async def _process_upload_queue(self):
        """Process items in upload queue"""
        try:
            # Define upload callback for different item types
            async def upload_callback(item) -> bool:
                try:
                    if item.item_type == "order":
                        response = await backend_client.post_order(item.payload)
                        return response.ok
                    
                    elif item.item_type == "command_result":
                        response = await backend_client.post_command_result(**item.payload)
                        return response.ok
                    
                    elif item.item_type == "status":
                        response = await backend_client.post_status(item.payload)
                        return response.ok
                    
                    elif item.item_type == "material":
                        bins_data = item.payload.get("bins", [])
                        response = await backend_client.report_materials(bins_data)
                        return response.ok
                    
                    else:
                        logger.warning(f"Unknown upload item type: {item.item_type}")
                        return False
                
                except Exception as e:
                    logger.error(f"Upload callback error for {item.item_type}: {e}")
                    return False
            
            # Process queue
            await upload_queue.process_all_pending(upload_callback)
            self.last_upload_attempt = utc_now()
            offline_manager.mark_online()
        
        except Exception as e:
            logger.error(f"Failed to process upload queue: {e}")
            offline_manager.mark_offline()
    
    async def _material_sync_loop(self):
        """Material sync loop - sync material levels with HAL"""
        while self.running:
            try:
                await self._sync_materials()
                await asyncio.sleep(60)  # Sync materials every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Material sync error: {e}")
                await asyncio.sleep(120)  # Longer delay on error
    
    async def _sync_materials(self):
        """Sync material levels and report if needed"""
        try:
            # Sync with HAL
            await material_manager.sync_with_hal()
            self.last_material_sync = utc_now()
            
            # Report if needed and online
            if material_manager.needs_reporting() and not offline_manager.is_offline:
                material_data = await material_manager.get_report_data()
                await upload_queue.add_material_report(material_data)
                material_manager.mark_reported()
                logger.debug("Queued material report")
        
        except Exception as e:
            logger.error(f"Failed to sync materials: {e}")
    
    async def force_sync(self) -> bool:
        """Force immediate sync of all data"""
        logger.info("Forcing immediate sync...")
        
        try:
            # Force heartbeat
            await self._send_heartbeat()
            
            # Force material sync and report
            await self._sync_materials()
            
            # Process upload queue
            await self._process_upload_queue()
            
            # Poll commands
            await self._poll_commands()
            
            logger.info("Force sync completed")
            return True
        
        except Exception as e:
            logger.error(f"Force sync failed: {e}")
            return False
    
    def get_supervisor_status(self) -> Dict[str, Any]:
        """Get supervisor status"""
        return {
            "running": self.running,
            "heartbeat_interval": self.heartbeat_interval,
            "poll_interval": self.poll_interval,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_command_poll": self.last_command_poll.isoformat() if self.last_command_poll else None,
            "last_upload_attempt": self.last_upload_attempt.isoformat() if self.last_upload_attempt else None,
            "last_material_sync": self.last_material_sync.isoformat() if self.last_material_sync else None,
            "offline_status": offline_manager.get_offline_summary(),
            "queue_status": upload_queue.get_queue_status()
        }
    
    async def handle_emergency(self, reason: str):
        """Handle emergency situation"""
        logger.critical(f"EMERGENCY: {reason}")
        
        # Stop all operations
        from ..hal.simulator import simulator
        await simulator.emergency_stop()
        
        # Set device to error status
        state_manager.set_status(DEVICE_STATUS_ERROR)
        
        # Emit error event
        event_bus.emit(EVENT_ERROR_OCCURRED, {
            "type": "emergency",
            "reason": reason,
            "timestamp": utc_now().isoformat()
        })
        
        # Try to report to backend
        try:
            await self._send_heartbeat()
        except:
            pass  # Ignore if can't report
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            "overall_status": "healthy",
            "issues": [],
            "warnings": []
        }
        
        try:
            # Check if supervisor is running
            if not self.running:
                health["issues"].append("Supervisor not running")
                health["overall_status"] = "unhealthy"
            
            # Check offline status
            if offline_manager.is_offline:
                health["warnings"].append(f"Device offline for {offline_manager.get_offline_duration()} seconds")
                if offline_manager.get_offline_duration() > 1800:  # 30 minutes
                    health["overall_status"] = "degraded"
            
            # Check material levels
            low_bins = material_manager.get_low_bins()
            empty_bins = material_manager.get_empty_bins()
            
            if empty_bins:
                health["issues"].append(f"{len(empty_bins)} bins empty")
                health["overall_status"] = "degraded"
            elif low_bins:
                health["warnings"].append(f"{len(low_bins)} bins low")
            
            # Check hardware status
            from ..hal.simulator import simulator
            hal_status = await simulator.get_status()
            
            if not hal_status.get("safe_to_operate"):
                health["issues"].append("Hardware not safe to operate")
                health["overall_status"] = "unhealthy"
            
            # Check upload queue
            queue_status = upload_queue.get_queue_status()
            if queue_status["total_pending"] > 100:
                health["warnings"].append(f"Large upload queue: {queue_status['total_pending']} items")
        
        except Exception as e:
            health["issues"].append(f"Health check error: {str(e)}")
            health["overall_status"] = "unknown"
        
        return health

# Global agent supervisor
agent_supervisor = AgentSupervisor()