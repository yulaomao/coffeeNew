from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
from PIL import Image

@dataclass
class PaymentQR:
    """Payment QR code data"""
    qr_image: bytes
    expire_ts: datetime
    channel: str
    order_id: str
    amount: float

@dataclass
class PaymentStatus:
    """Payment status result"""
    status: str  # pending, paid, failed, canceled
    txn_id: Optional[str] = None
    reason: Optional[str] = None
    amount: Optional[float] = None

class PaymentProvider(ABC):
    """Abstract payment provider interface"""
    
    @abstractmethod
    async def create_qr(self, amount: float, order_id: str, expires_in_s: int = 300) -> PaymentQR:
        """Create QR code for payment"""
        pass
    
    @abstractmethod
    async def poll(self, order_id: str) -> PaymentStatus:
        """Poll payment status"""
        pass
    
    @abstractmethod
    async def cancel(self, order_id: str) -> Dict[str, Any]:
        """Cancel payment"""
        pass
    
    def _generate_qr_image(self, data: str, size: int = 256) -> bytes:
        """Generate QR code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to desired size
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()