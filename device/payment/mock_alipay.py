from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio
from loguru import logger
from .provider import PaymentProvider, PaymentQR, PaymentStatus
from ..utils.time import utc_now

class MockAlipayProvider(PaymentProvider):
    """Mock Alipay provider for testing and demo"""
    
    def __init__(self):
        self.active_payments = {}  # order_id -> payment_data
        self.test_mode = True
        self.auto_pay_delay = 12  # Auto-pay after 12 seconds (slightly different from WeChat)
    
    async def create_qr(self, amount: float, order_id: str, expires_in_s: int = 300) -> PaymentQR:
        """Create QR code for Alipay payment"""
        expire_time = utc_now() + timedelta(seconds=expires_in_s)
        
        # Create QR data (mock format)
        qr_data = f"ALIPAY:ORDER:{order_id}:AMOUNT:{amount:.2f}"
        
        # Generate QR code image
        qr_image = self._generate_qr_image(qr_data)
        
        # Store payment info
        self.active_payments[order_id] = {
            "amount": amount,
            "status": "pending",
            "created_at": utc_now(),
            "expires_at": expire_time,
            "txn_id": None
        }
        
        logger.info(f"Created Alipay payment QR for order {order_id}, amount: ¥{amount:.2f}")
        
        # In test mode, auto-complete payment after delay
        if self.test_mode:
            asyncio.create_task(self._auto_complete_payment(order_id))
        
        return PaymentQR(
            qr_image=qr_image,
            expire_ts=expire_time,
            channel="alipay",
            order_id=order_id,
            amount=amount
        )
    
    async def poll(self, order_id: str) -> PaymentStatus:
        """Poll Alipay payment status"""
        if order_id not in self.active_payments:
            return PaymentStatus(
                status="failed",
                reason="Payment not found"
            )
        
        payment_data = self.active_payments[order_id]
        
        # Check expiration
        if utc_now() > payment_data["expires_at"]:
            payment_data["status"] = "canceled"
            payment_data["reason"] = "Payment expired"
        
        return PaymentStatus(
            status=payment_data["status"],
            txn_id=payment_data.get("txn_id"),
            reason=payment_data.get("reason"),
            amount=payment_data["amount"]
        )
    
    async def cancel(self, order_id: str) -> Dict[str, Any]:
        """Cancel Alipay payment"""
        if order_id in self.active_payments:
            self.active_payments[order_id]["status"] = "canceled"
            self.active_payments[order_id]["reason"] = "Canceled by user"
            logger.info(f"Canceled Alipay payment for order {order_id}")
            return {"ok": True}
        
        return {"ok": False, "error": "Payment not found"}
    
    async def _auto_complete_payment(self, order_id: str):
        """Auto-complete payment after delay (test mode only)"""
        await asyncio.sleep(self.auto_pay_delay)
        
        if order_id in self.active_payments:
            payment = self.active_payments[order_id]
            if payment["status"] == "pending":
                payment["status"] = "paid"
                payment["txn_id"] = f"ap_txn_{order_id}_{int(utc_now().timestamp())}"
                logger.info(f"Auto-completed Alipay payment for order {order_id}")
    
    def simulate_payment_success(self, order_id: str) -> bool:
        """Manually trigger payment success (for testing)"""
        if order_id in self.active_payments:
            payment = self.active_payments[order_id]
            if payment["status"] == "pending":
                payment["status"] = "paid"
                payment["txn_id"] = f"ap_manual_{order_id}_{int(utc_now().timestamp())}"
                logger.info(f"Manually completed Alipay payment for order {order_id}")
                return True
        return False
    
    def simulate_payment_failure(self, order_id: str, reason: str = "Payment failed") -> bool:
        """Manually trigger payment failure (for testing)"""
        if order_id in self.active_payments:
            payment = self.active_payments[order_id]
            if payment["status"] == "pending":
                payment["status"] = "failed"
                payment["reason"] = reason
                logger.info(f"Manually failed Alipay payment for order {order_id}: {reason}")
                return True
        return False
    
    def get_active_payments(self) -> Dict[str, Dict[str, Any]]:
        """Get all active payments (for debugging)"""
        return self.active_payments.copy()
    
    def clear_expired_payments(self):
        """Clean up expired payments"""
        now = utc_now()
        expired_orders = []
        
        for order_id, payment in self.active_payments.items():
            if now > payment["expires_at"] and payment["status"] == "pending":
                payment["status"] = "canceled"
                payment["reason"] = "Expired"
                expired_orders.append(order_id)
        
        if expired_orders:
            logger.info(f"Marked {len(expired_orders)} Alipay payments as expired")

# Global mock Alipay provider
mock_alipay = MockAlipayProvider()