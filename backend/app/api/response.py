from flask import jsonify
from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    # General errors
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Business logic errors
    DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    COMMAND_NOT_SUPPORTED = "COMMAND_NOT_SUPPORTED"
    INSUFFICIENT_MATERIALS = "INSUFFICIENT_MATERIALS"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    REFUND_NOT_ALLOWED = "REFUND_NOT_ALLOWED"
    
    # System errors
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"


def success_response(data: Any = None, status_code: int = 200):
    """Return successful API response"""
    response = {"ok": True}
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
):
    """Return error API response"""
    response = {
        "ok": False,
        "error": {
            "code": code.value,
            "message": message
        }
    }
    if details:
        response["error"]["details"] = details
    
    return jsonify(response), status_code


def paginated_response(items: list, total: int, page: int, page_size: int, **kwargs):
    """Return paginated API response"""
    data = {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "has_next": page * page_size < total,
            "has_prev": page > 1
        }
    }
    data.update(kwargs)
    return success_response(data)


def validation_error_response(errors: Dict[str, Any]):
    """Return validation error response"""
    return error_response(
        ErrorCode.VALIDATION_ERROR,
        "Validation failed",
        details={"validation_errors": errors},
        status_code=422
    )