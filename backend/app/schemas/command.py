from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class CommandType(str, Enum):
    MAKE_PRODUCT = "make_product"
    OPEN_DOOR = "open_door"
    UPGRADE = "upgrade"
    SYNC = "sync"
    SET_PARAMS = "set_params"
    RESTART = "restart"


class CommandStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    SUCCESS = "success"
    FAIL = "fail"
    UNSUPPORTED = "unsupported"


class DispatchCommandRequest(BaseModel):
    device_ids: List[str] = Field(..., min_items=1)
    command_type: CommandType
    payload: Optional[Dict[str, Any]] = None
    note: Optional[str] = Field(None, max_length=500)
    max_attempts: Optional[int] = Field(5, ge=1, le=10)
    
    @validator('device_ids')
    def device_ids_not_empty(cls, v):
        if not v:
            raise ValueError('Device IDs list cannot be empty')
        return v


class CommandResultRequest(BaseModel):
    command_id: str
    status: CommandStatus
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    timestamp: datetime


class CommandResponse(BaseModel):
    command_id: str
    device_id: str
    type: Optional[str]
    payload: Optional[Dict[str, Any]]
    status: Optional[str]
    issued_at: Optional[datetime]
    sent_at: Optional[datetime]
    result_at: Optional[datetime]
    result_payload: Optional[Dict[str, Any]]
    batch_id: Optional[str]
    attempts: Optional[int]
    max_attempts: Optional[int]
    last_error: Optional[str]


class CommandBatchResponse(BaseModel):
    batch_id: str
    command_type: Optional[str]
    payload: Optional[Dict[str, Any]]
    note: Optional[str]
    stats: Optional[Dict[str, Any]]
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BatchRetryRequest(BaseModel):
    device_ids: Optional[List[str]] = None  # If None, retry all failed commands
    
    @validator('device_ids')
    def validate_device_ids(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('Device IDs list cannot be empty if provided')
        return v


class PendingCommandResponse(BaseModel):
    command_id: str
    type: str
    payload: Optional[Dict[str, Any]]
    issued_at: datetime
    max_attempts: int
    attempts: int