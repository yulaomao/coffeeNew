import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from ..storage.models import Command, CommandStatus
from ..storage.queue import upload_queue
from ..config import config
from ..constants import *
from ..utils.time import utc_now
from ..utils.sse import event_bus, EVENT_COMMAND_RECEIVED, EVENT_COMMAND_COMPLETED
from ..backend.client import backend_client
from .materials import material_manager
from .recipes import recipe_manager
from .orders import order_manager
from .state import state_manager

class CommandProcessor:
    """Processes commands received from backend"""
    
    def __init__(self):
        self.processing_commands = {}  # command_id -> asyncio.Task
    
    async def execute_command(self, command: Command) -> Dict[str, Any]:
        """Execute a command and return result"""
        command_type = command.type
        payload = command.payload
        
        logger.info(f"Executing command {command.command_id}: {command_type}")
        
        try:
            if command_type == COMMAND_MAKE_PRODUCT:
                return await self._handle_make_product(command)
            
            elif command_type == COMMAND_OPEN_DOOR:
                return await self._handle_open_door(command)
            
            elif command_type == COMMAND_UPGRADE:
                return await self._handle_upgrade(command)
            
            elif command_type == COMMAND_SYNC:
                return await self._handle_sync(command)
            
            elif command_type == COMMAND_SET_PARAMS:
                return await self._handle_set_params(command)
            
            elif command_type == COMMAND_RESTART:
                return await self._handle_restart(command)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown command type: {command_type}"
                }
        
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_make_product(self, command: Command) -> Dict[str, Any]:
        """Handle make_product command"""
        payload = command.payload
        recipe_id = payload.get("recipe_id")
        order_id = payload.get("order_id")
        options = payload.get("options", {})
        
        if not recipe_id:
            return {"success": False, "error": "recipe_id required"}
        
        try:
            # Get recipe
            recipe = recipe_manager.get_recipe_by_id(recipe_id)
            if not recipe:
                return {"success": False, "error": f"Recipe {recipe_id} not found"}
            
            # Check material availability
            availability = material_manager.check_recipe_availability(recipe.materials)
            if not all(availability.values()):
                insufficient = [mat for mat, avail in availability.items() if not avail]
                return {
                    "success": False,
                    "error": f"Insufficient materials: {', '.join(insufficient)}"
                }
            
            # Create order if not provided
            if not order_id:
                items = [{"recipe_id": recipe_id, "quantity": 1, "options": options}]
                order = await order_manager.create_order(items, payment_method="remote", is_test=False)
                order_id = order.order_id
                
                # Mark as paid (remote commands are pre-authorized)
                order.payment_status = "paid"
                order.status = "paid"
                order.payment_txn_id = f"remote_{command.command_id}"
                from ..storage.db import db
                db.save_order(order)
            
            # Start brewing
            success = await order_manager.start_brewing(order_id)
            
            if success:
                # Get consumed materials
                order = order_manager.get_order_by_id(order_id)
                consumed_materials = {}
                
                for material_code, amount in recipe.materials.items():
                    consumed_materials[material_code] = amount
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "consumed": consumed_materials,
                    "completed_at": utc_now().isoformat()
                }
            else:
                return {"success": False, "error": "Brewing failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_open_door(self, command: Command) -> Dict[str, Any]:
        """Handle open_door command"""
        payload = command.payload
        duration_seconds = payload.get("duration_seconds", 60)
        
        try:
            from ..hal.simulator import simulator
            success = await simulator.open_door(duration_seconds)
            
            if success:
                return {
                    "success": True,
                    "duration_seconds": duration_seconds,
                    "opened_at": utc_now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to open door"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_upgrade(self, command: Command) -> Dict[str, Any]:
        """Handle upgrade command"""
        payload = command.payload
        package_type = payload.get("package_type")
        package_url = payload.get("package_url")
        package_hash = payload.get("package_hash")
        version = payload.get("version")
        
        if not all([package_type, package_url, package_hash, version]):
            return {"success": False, "error": "Missing required upgrade parameters"}
        
        try:
            if package_type == "recipes":
                # Download and install recipe package
                success = await recipe_manager.download_recipe_package(
                    package_url, package_hash, f"upgrade_{version}", version
                )
                
                if success:
                    return {
                        "success": True,
                        "package_type": package_type,
                        "version": version,
                        "installed_at": utc_now().isoformat()
                    }
                else:
                    return {"success": False, "error": "Recipe package installation failed"}
            
            else:
                # Other package types (firmware, etc.)
                logger.info(f"Upgrade for {package_type} not implemented")
                return {
                    "success": False,
                    "error": f"Upgrade type {package_type} not implemented"
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_sync(self, command: Command) -> Dict[str, Any]:
        """Handle sync command"""
        payload = command.payload
        sync_types = payload.get("sync_types", ["status", "materials"])
        
        results = {}
        
        try:
            for sync_type in sync_types:
                if sync_type == "status":
                    status_data = await state_manager.get_status_report_data()
                    await upload_queue.add_status_report(status_data)
                    results["status"] = "queued"
                
                elif sync_type == "materials":
                    material_data = await material_manager.get_report_data()
                    await upload_queue.add_material_report(material_data)
                    results["materials"] = "queued"
                
                else:
                    results[sync_type] = f"Unknown sync type: {sync_type}"
            
            return {
                "success": True,
                "sync_results": results,
                "synced_at": utc_now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_set_params(self, command: Command) -> Dict[str, Any]:
        """Handle set_params command"""
        payload = command.payload
        params = payload.get("params", {})
        
        if not params:
            return {"success": False, "error": "No parameters provided"}
        
        try:
            updated_params = {}
            
            # Update configuration parameters
            from ..storage.db import db
            for key, value in params.items():
                db.set_kv(f"config_{key}", value)
                updated_params[key] = value
                logger.info(f"Updated parameter {key} = {value}")
            
            return {
                "success": True,
                "updated_params": updated_params,
                "updated_at": utc_now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_restart(self, command: Command) -> Dict[str, Any]:
        """Handle restart command"""
        payload = command.payload
        reason = payload.get("reason", "remote_command")
        
        try:
            logger.warning(f"Restart requested: {reason}")
            
            # In a real implementation, this would trigger application restart
            # For now, just log and return success
            
            return {
                "success": True,
                "reason": reason,
                "restart_requested_at": utc_now().isoformat(),
                "note": "Restart simulation - would restart in real implementation"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def process_command(self, command_data: Dict[str, Any]) -> bool:
        """Process incoming command data"""
        try:
            # Create command object
            command = Command(
                command_id=command_data["command_id"],
                device_id=config.DEVICE_ID,
                type=command_data["type"],
                payload=command_data.get("payload", {}),
                status=CommandStatus.SENT,
                issued_at=datetime.fromisoformat(command_data["issued_at"]),
                sent_at=utc_now()
            )
            
            # Emit command received event
            event_bus.emit(EVENT_COMMAND_RECEIVED, {
                "command_id": command.command_id,
                "type": command.type
            })
            
            # Execute command
            result = await self.execute_command(command)
            
            # Update command status
            if result.get("success"):
                command.status = CommandStatus.SUCCESS
                command.result_payload = result
            else:
                command.status = CommandStatus.FAIL
                command.error_message = result.get("error")
                command.result_payload = result
            
            command.completed_at = utc_now()
            
            # Queue command result for upload
            await self._queue_command_result(command)
            
            # Emit command completed event
            event_bus.emit(EVENT_COMMAND_COMPLETED, {
                "command_id": command.command_id,
                "type": command.type,
                "success": result.get("success", False),
                "error": result.get("error")
            })
            
            logger.info(f"Command {command.command_id} completed: {command.status}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to process command: {e}")
            return False
    
    async def _queue_command_result(self, command: Command):
        """Queue command result for backend upload"""
        try:
            result_data = {
                "command_id": command.command_id,
                "status": command.status,
                "result_payload": command.result_payload,
                "result_at": command.completed_at.isoformat(),
                "error_message": command.error_message
            }
            
            await upload_queue.add_command_result(result_data, command.command_id)
            logger.debug(f"Queued command result for {command.command_id}")
        
        except Exception as e:
            logger.error(f"Failed to queue command result: {e}")

# Global command processor
command_processor = CommandProcessor()