from functools import wraps
from flask import request, current_app
from flask_login import current_user
from pydantic import BaseModel, ValidationError
from app.api.response import validation_error_response, error_response, ErrorCode
import json


def validate_json(schema_class: BaseModel):
    """Decorator to validate JSON request body using Pydantic"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not request.is_json:
                    return error_response(
                        ErrorCode.INVALID_FORMAT,
                        "Request must be JSON",
                        status_code=400
                    )
                
                json_data = request.get_json()
                if json_data is None:
                    return error_response(
                        ErrorCode.INVALID_ARGUMENT,
                        "Invalid JSON data",
                        status_code=400
                    )
                
                # Validate using Pydantic
                validated_data = schema_class(**json_data)
                request.validated_json = validated_data
                
            except ValidationError as e:
                return validation_error_response(e.errors())
            except Exception as e:
                return error_response(
                    ErrorCode.VALIDATION_ERROR,
                    f"Validation failed: {str(e)}",
                    status_code=400
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_device_token():
    """Decorator to require device token when enabled"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_app.config.get('ENABLE_DEVICE_TOKEN'):
                token = request.headers.get('X-Device-Token')
                if not token:
                    return error_response(
                        ErrorCode.UNAUTHORIZED,
                        "Device token required",
                        status_code=401
                    )
                
                # In a real implementation, validate the token
                # For now, just check if it exists
                if not _validate_device_token(token):
                    return error_response(
                        ErrorCode.UNAUTHORIZED,
                        "Invalid device token",
                        status_code=401
                    )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(required_roles):
    """Decorator to require specific user roles"""
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return error_response(
                    ErrorCode.UNAUTHORIZED,
                    "Authentication required",
                    status_code=401
                )
            
            if current_user.role.value not in required_roles:
                return error_response(
                    ErrorCode.FORBIDDEN,
                    "Insufficient permissions",
                    status_code=403
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _validate_device_token(token):
    """Validate device token (placeholder implementation)"""
    # In a real implementation, this would validate the token
    # against a secure storage or use JWT validation
    return len(token) >= 32  # Simple check for demo