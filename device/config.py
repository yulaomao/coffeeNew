import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import appdirs

# Load environment variables
load_dotenv()

class Config:
    # Backend API configuration
    BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "https://backend.example.com/api/v1")
    DEVICE_ID: str = os.getenv("DEVICE_ID", "D001")
    DEVICE_TOKEN: Optional[str] = os.getenv("DEVICE_TOKEN") or None
    MERCHANT_ID: Optional[str] = os.getenv("MERCHANT_ID") or None
    
    # UI configuration
    UI_LANG: str = os.getenv("UI_LANG", "zh-CN")
    UI_FULLSCREEN: bool = os.getenv("UI_FULLSCREEN", "true").lower() == "true"
    UI_SCREEN_WIDTH: int = int(os.getenv("UI_SCREEN_WIDTH", "1080"))
    UI_SCREEN_HEIGHT: int = int(os.getenv("UI_SCREEN_HEIGHT", "1920"))
    
    # Agent configuration
    POLL_INTERVAL_SEC: int = int(os.getenv("POLL_INTERVAL_SEC", "5"))
    HEARTBEAT_INTERVAL_SEC: int = int(os.getenv("HEARTBEAT_INTERVAL_SEC", "30"))
    OFFLINE_THRESHOLD_SEC: int = int(os.getenv("OFFLINE_THRESHOLD_SEC", "600"))
    
    # Material configuration
    LOW_MATERIAL_PCT: int = int(os.getenv("LOW_MATERIAL_PCT", "20"))
    
    # Queue configuration
    ALLOW_QUEUE: bool = os.getenv("ALLOW_QUEUE", "false").lower() == "true"
    QUEUE_LENGTH: int = int(os.getenv("QUEUE_LENGTH", "1"))
    
    # Path configuration
    ASSETS_DIR: Path = Path(os.getenv("ASSETS_DIR", "./device/assets")).resolve()
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", appdirs.user_cache_dir("coffee_device"))).resolve()
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", appdirs.user_log_dir("coffee_device"))).resolve()
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for dir_path in [cls.ASSETS_DIR, cls.CACHE_DIR, cls.LOG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories
        (cls.ASSETS_DIR / "recipes").mkdir(exist_ok=True)
        (cls.ASSETS_DIR / "packages").mkdir(exist_ok=True)
        (cls.CACHE_DIR / "images").mkdir(exist_ok=True)

config = Config()