#!/usr/bin/env python3
"""
智能咖啡机设备端主程序
Smart Coffee Machine Device Application

一次成型实现指令 - 触控大屏 + 本地代理
"""

import sys
import asyncio
import signal
from pathlib import Path
from loguru import logger

# Add device directory to path
device_dir = Path(__file__).parent
sys.path.insert(0, str(device_dir))

from config import config
from agent.supervisor import agent_supervisor
from utils.sse import event_bus

class CoffeeMachineApp:
    """Main coffee machine application"""
    
    def __init__(self):
        self.running = False
        self.ui_app = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging"""
        # Ensure log directory exists
        config.ensure_directories()
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Console logging
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        
        # File logging with rotation
        log_file = config.LOG_DIR / "device.log"
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
        
        logger.info("Logging configured")
    
    async def start_agent(self):
        """Start background agent"""
        logger.info("Starting device agent...")
        await agent_supervisor.start()
    
    async def stop_agent(self):
        """Stop background agent"""
        logger.info("Stopping device agent...")
        await agent_supervisor.stop()
    
    def start_ui(self):
        """Start PySide6 UI application"""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QTimer
            from kiosk.main_window import CoffeeMachineMainWindow
            
            # Create QApplication
            app = QApplication(sys.argv)
            
            # Set application properties
            app.setApplicationName("智能咖啡机")
            app.setApplicationVersion("1.0.0")
            app.setOrganizationName("Coffee Machine Co.")
            
            # Create main window
            main_window = CoffeeMachineMainWindow()
            
            # Show window
            if config.UI_FULLSCREEN:
                main_window.showFullScreen()
            else:
                main_window.show()
            
            # Setup periodic timer for async tasks
            timer = QTimer()
            timer.timeout.connect(self._process_async_tasks)
            timer.start(100)  # 100ms interval
            
            self.ui_app = app
            logger.info("UI application started")
            
            # Run Qt event loop
            return app.exec()
        
        except ImportError:
            logger.error("PySide6 not available, running in console mode")
            return self.run_console_mode()
        except Exception as e:
            logger.error(f"Failed to start UI: {e}")
            return 1
    
    def _process_async_tasks(self):
        """Process async tasks from Qt timer"""
        # This would process any pending async tasks in the event loop
        pass
    
    def run_console_mode(self):
        """Run in console mode without UI"""
        logger.info("Running in console mode")
        logger.info("Coffee machine agent is running...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Keep running until interrupted
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        return 0
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
            if self.ui_app:
                self.ui_app.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Main run method"""
        logger.info("Starting Smart Coffee Machine...")
        logger.info(f"Device ID: {config.DEVICE_ID}")
        logger.info(f"Backend URL: {config.BACKEND_BASE_URL}")
        logger.info(f"UI Language: {config.UI_LANG}")
        
        self.running = True
        self.setup_signal_handlers()
        
        try:
            # Start background agent
            await self.start_agent()
            
            # Log system status
            status = agent_supervisor.get_supervisor_status()
            logger.info(f"Agent supervisor status: {status['running']}")
            
            # Start UI (this will block until UI closes)
            ui_result = self.start_ui()
            
            return ui_result
        
        finally:
            # Cleanup
            await self.stop_agent()
            logger.info("Smart Coffee Machine stopped")

async def main():
    """Main entry point"""
    app = CoffeeMachineApp()
    return await app.run()

def sync_main():
    """Synchronous main entry point"""
    try:
        # Run async main
        return asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        return 0
    except Exception as e:
        logger.exception(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = sync_main()
    sys.exit(exit_code)