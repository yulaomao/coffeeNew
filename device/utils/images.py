from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageQt
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QUrl
import hashlib
import requests
from loguru import logger
from ..config import config

class ImageManager:
    """Manage image loading, caching and processing"""
    
    def __init__(self):
        self.cache_dir = config.CACHE_DIR / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, QPixmap] = {}
    
    def get_image_path(self, name: str) -> Optional[Path]:
        """Get path to image asset"""
        # Try different locations
        paths_to_try = [
            config.ASSETS_DIR / "images" / name,
            Path(__file__).parent.parent / "kiosk" / "assets" / "images" / name,
        ]
        
        for path in paths_to_try:
            if path.exists():
                return path
        
        return None
    
    def load_pixmap(self, name: str, size: Optional[tuple] = None) -> Optional[QPixmap]:
        """Load image as QPixmap with optional resizing"""
        cache_key = f"{name}_{size}" if size else name
        
        # Check memory cache
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        
        # Find image file
        image_path = self.get_image_path(name)
        if not image_path:
            logger.warning(f"Image not found: {name}")
            return self._create_placeholder_pixmap(size)
        
        try:
            pixmap = QPixmap(str(image_path))
            
            if size:
                pixmap = pixmap.scaled(size[0], size[1])
            
            self._memory_cache[cache_key] = pixmap
            return pixmap
            
        except Exception as e:
            logger.error(f"Failed to load image {name}: {e}")
            return self._create_placeholder_pixmap(size)
    
    def _create_placeholder_pixmap(self, size: Optional[tuple] = None) -> QPixmap:
        """Create a placeholder pixmap"""
        from PySide6.QtGui import QPainter, QBrush, QColor
        from PySide6.QtCore import Qt
        
        w, h = size or (200, 200)
        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(180, 180, 180))
        painter.drawRect(0, 0, w-1, h-1)
        painter.drawLine(0, 0, w-1, h-1)
        painter.drawLine(0, h-1, w-1, 0)
        painter.end()
        
        return pixmap
    
    def download_image(self, url: str, filename: str) -> Optional[Path]:
        """Download image from URL and save to cache"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Generate filename based on URL hash if not provided
            if not filename:
                url_hash = hashlib.md5(url.encode()).hexdigest()
                filename = f"{url_hash}.jpg"
            
            file_path = self.cache_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None
    
    def clear_memory_cache(self):
        """Clear memory cache"""
        self._memory_cache.clear()
    
    def preload_common_images(self):
        """Preload commonly used images"""
        common_images = [
            "logo.png",
            "background.jpg", 
            "coffee_cup.png",
            "maintenance.png"
        ]
        
        for image_name in common_images:
            self.load_pixmap(image_name)

# Global image manager instance
image_manager = ImageManager()