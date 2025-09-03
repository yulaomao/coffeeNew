from typing import Dict, Any, Callable, Optional
from functools import wraps
import asyncio
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

def with_retries(max_attempts: int = 3, backoff_factor: float = 1.0):
    """Decorator for adding retry logic to functions"""
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=backoff_factor, min=4, max=10)
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(calls_per_second: float):
    """Simple rate limiting decorator"""
    min_interval = 1.0 / calls_per_second
    last_called = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = asyncio.get_event_loop().time()
            key = f"{func.__name__}_{id(args[0]) if args else 'global'}"
            
            if key in last_called:
                elapsed = now - last_called[key]
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
            
            last_called[key] = asyncio.get_event_loop().time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def log_errors(func: Callable) -> Callable:
    """Decorator to log exceptions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

class RequestSigner:
    """Optional request signing for enhanced security"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key
    
    def sign_request(self, method: str, url: str, body: str, timestamp: str) -> str:
        """Sign request (placeholder for actual implementation)"""
        if not self.secret_key:
            return ""
        
        # Placeholder - implement actual signing logic if needed
        import hashlib
        import hmac
        
        message = f"{method}{url}{body}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, signature: str, method: str, url: str, 
                        body: str, timestamp: str) -> bool:
        """Verify request signature"""
        expected = self.sign_request(method, url, body, timestamp)
        return signature == expected

# Global request signer (can be configured with secret)
request_signer = RequestSigner()