#!/usr/bin/env python3
"""
智能咖啡机设备端主程序 - Flask Web版本
Smart Coffee Machine Device Application - Flask Web Version

转换为Web应用版本 - Flask + WebSocket + 设备代理
"""

import sys
import asyncio
import signal
import threading
from pathlib import Path
from loguru import logger

# Add device directory to path
device_dir = Path(__file__).parent
sys.path.insert(0, str(device_dir))

from config import config
from agent.supervisor import agent_supervisor
from utils.sse import event_bus

class CoffeeMachineApp:
    """Main coffee machine application - Web version"""
    
    def __init__(self):
        self.running = False
        self.web_app = None
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
        
        logger.info("Logging configured for Web version")
    
    async def start_agent(self):
        """Start background agent"""
        logger.info("Starting device agent...")
        await agent_supervisor.start()
    
    async def stop_agent(self):
        """Stop background agent"""
        logger.info("Stopping device agent...")
        await agent_supervisor.stop()
    
    def start_web_ui(self):
        """Start Flask Web UI application"""
        try:
            # Import and run the Flask web application
            logger.info("Starting Flask Web UI...")
            from web_app import app, socketio, run_agent
            
            # Start agent in background thread
            agent_thread = threading.Thread(target=run_agent, daemon=True)
            agent_thread.start()
            
            # Get configuration
            host = getattr(config, 'WEB_HOST', '0.0.0.0')
            port = getattr(config, 'WEB_PORT', 5000)
            debug = getattr(config, 'DEBUG', False)
            
            logger.info(f"Starting Flask app on {host}:{port}")
            logger.info("Web UI will be available at:")
            logger.info(f"  - Local: http://localhost:{port}")
            logger.info(f"  - Network: http://{host}:{port}")
            
            # Run Flask app with SocketIO
            socketio.run(app, host=host, port=port, debug=debug)
            
            return 0
            
        except ImportError as e:
            logger.error(f"Flask dependencies not available: {e}")
            logger.error("Please install Flask requirements: pip install Flask flask-socketio eventlet")
            return 1
        except Exception as e:
            logger.error(f"Failed to start Web UI: {e}")
            return 1
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
            # Flask app shutdown will be handled by Flask itself
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run(self):
        """Main run method - synchronous for Flask"""
        logger.info("Starting Smart Coffee Machine Web Application...")
        logger.info(f"Device ID: {config.DEVICE_ID}")
        logger.info(f"Backend URL: {config.BACKEND_BASE_URL}")
        logger.info(f"UI Language: {config.UI_LANG}")
        logger.info("UI Type: Web Browser Interface")
        
        self.running = True
        self.setup_signal_handlers()
        
        try:
            # Start Web UI (this will block until server stops)
            ui_result = self.start_web_ui()
            return ui_result
        
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.exception(f"Application error: {e}")
            return 1
        finally:
            logger.info("Smart Coffee Machine stopped")

def main():
    """Main entry point"""
    app = CoffeeMachineApp()
    return app.run()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)