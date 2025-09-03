from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

# Request/Response schemas for backend API communication

# Device registration
class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str = "coffee_machine"
    firmware_version: str = "1.0.0"
    location: Optional[str] = None

class DeviceRegisterResponse(BaseModel):
    ok: bool
    device_token: Optional[str] = None
    message: Optional[str] = None

# Status reporting
class StatusReportRequest(BaseModel):
    device_id: str
    status: str
    temperature: Optional[float] = None
    wifi_ssid: Optional[str] = None
    wifi_signal: Optional[int] = None
    ip: Optional[str] = None
    firmware_version: str
    uptime_seconds: int
    timestamp: datetime

class StatusReportResponse(BaseModel):
    ok: bool
    message: Optional[str] = None

# Material reporting
class MaterialBinReport(BaseModel):
    bin_index: int
    material_code: str
    remaining: float
    capacity: float
    unit: str

class MaterialReportRequest(BaseModel):
    device_id: str
    bins: List[MaterialBinReport]
    timestamp: datetime

class MaterialReportResponse(BaseModel):
    ok: bool
    message: Optional[str] = None

# Commands
class CommandPayload(BaseModel):
    """Base class for command payloads"""
    pass

class MakeProductPayload(CommandPayload):
    recipe_id: int
    order_id: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)

class OpenDoorPayload(CommandPayload):
    duration_seconds: int = 60

class UpgradePayload(CommandPayload):
    package_type: str
    package_url: str
    package_hash: str
    version: str

class SyncPayload(CommandPayload):
    sync_types: List[str] = Field(default_factory=lambda: ["status", "materials"])

class SetParamsPayload(CommandPayload):
    params: Dict[str, Any]

class RestartPayload(CommandPayload):
    reason: str = "remote_command"

class PendingCommand(BaseModel):
    command_id: str
    type: str
    payload: Dict[str, Any]
    issued_at: datetime
    expires_at: Optional[datetime] = None

class PendingCommandsResponse(BaseModel):
    ok: bool
    commands: List[PendingCommand] = Field(default_factory=list)

# Command results
class CommandResultRequest(BaseModel):
    command_id: str
    status: str  # success, fail
    result_payload: Dict[str, Any] = Field(default_factory=dict)
    result_at: datetime
    error_message: Optional[str] = None

class CommandResultResponse(BaseModel):
    ok: bool
    message: Optional[str] = None

# Order reporting
class OrderItemReport(BaseModel):
    recipe_id: int
    recipe_name: str
    price: float
    quantity: int = 1
    options: Dict[str, Any] = Field(default_factory=dict)

class OrderCreateRequest(BaseModel):
    order_id: str
    items: List[OrderItemReport]
    total_price: float
    payment_method: str
    payment_status: str = "paid"
    payment_txn_id: Optional[str] = None
    device_id: str
    created_at: datetime
    is_test: bool = False

class OrderCreateResponse(BaseModel):
    ok: bool
    order_id: Optional[str] = None
    message: Optional[str] = None

# Error response
class ErrorResponse(BaseModel):
    ok: bool = False
    error: Dict[str, Any]

# Recipe package
class RecipePackageInfo(BaseModel):
    package_id: str
    version: str
    download_url: str
    md5_hash: str
    recipes_count: int
    created_at: datetime