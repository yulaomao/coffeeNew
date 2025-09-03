import hashlib
from flask import request
from app.extensions import cache


def get_idempotency_key(request_data, additional_keys=None):
    """Generate idempotency key from request data"""
    keys = []
    
    # Add request path and method
    keys.append(request.method)
    keys.append(request.path)
    
    # Add request data
    if isinstance(request_data, dict):
        # Sort keys for consistent hashing
        sorted_data = {k: request_data[k] for k in sorted(request_data.keys())}
        keys.append(str(sorted_data))
    else:
        keys.append(str(request_data))
    
    # Add additional keys if provided
    if additional_keys:
        keys.extend(additional_keys)
    
    # Generate hash
    key_string = '|'.join(keys)
    return hashlib.sha256(key_string.encode()).hexdigest()


def is_duplicate_request(idempotency_key, ttl=3600):
    """Check if request with this idempotency key was already processed"""
    cache_key = f"idempotency:{idempotency_key}"
    return cache.get(cache_key) is not None


def mark_request_processed(idempotency_key, result=None, ttl=3600):
    """Mark request as processed and optionally store result"""
    cache_key = f"idempotency:{idempotency_key}"
    cache.set(cache_key, result or "processed", timeout=ttl)


def get_cached_result(idempotency_key):
    """Get cached result for idempotent request"""
    cache_key = f"idempotency:{idempotency_key}"
    return cache.get(cache_key)


def ensure_idempotent(request_data, additional_keys=None, ttl=3600):
    """Decorator/helper to ensure idempotent operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            idempotency_key = get_idempotency_key(request_data, additional_keys)
            
            # Check if already processed
            cached_result = get_cached_result(idempotency_key)
            if cached_result and cached_result != "processed":
                return cached_result
            
            # Process request
            result = func(*args, **kwargs)
            
            # Cache result
            mark_request_processed(idempotency_key, result, ttl)
            
            return result
        return wrapper
    return decorator