from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class PackageUploadRequest(BaseModel):
    name: str = Field(..., max_length=200)
    version: str = Field(..., max_length=50)
    type: str = Field(..., max_length=50)  # "firmware", "resources", "recipe", etc.
    description: Optional[str] = Field(None, max_length=1000)
    compatibility: Optional[List[str]] = None  # Compatible device models
    metadata: Optional[Dict[str, Any]] = None


class PackageResponse(BaseModel):
    package_id: str
    name: str
    version: Optional[str]
    type: Optional[str]
    description: Optional[str]
    package_url: Optional[str]
    md5: Optional[str]
    size: Optional[int]
    compatibility: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class DispatchPackageRequest(BaseModel):
    device_ids: List[str] = Field(..., min_items=1)
    note: Optional[str] = Field(None, max_length=500)
    priority: Optional[str] = Field("normal", regex="^(low|normal|high|critical)$")
    
    @validator('device_ids')
    def device_ids_not_empty(cls, v):
        if not v:
            raise ValueError('Device IDs list cannot be empty')
        return v