from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class MaterialCreateRequest(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    type: Optional[str] = Field(None, max_length=100)
    unit: str = Field(..., max_length=20)
    density: Optional[Decimal] = Field(None, ge=0)
    enabled: bool = True


class MaterialUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=20)
    density: Optional[Decimal] = Field(None, ge=0)
    enabled: Optional[bool] = None


class MaterialResponse(BaseModel):
    id: int
    code: str
    name: str
    type: Optional[str]
    unit: Optional[str]
    density: Optional[Decimal]
    enabled: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class MaterialImportRow(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    type: Optional[str] = Field(None, max_length=100)
    unit: str = Field(..., max_length=20)
    density: Optional[float] = Field(None, ge=0)
    enabled: Optional[bool] = True
    
    @validator('code')
    def code_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Code cannot be empty')
        return v.strip()
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class MaterialImportRequest(BaseModel):
    materials: List[MaterialImportRow] = Field(..., min_items=1)
    overwrite_existing: bool = False
    
    @validator('materials')
    def materials_not_empty(cls, v):
        if not v:
            raise ValueError('Materials list cannot be empty')
        return v


class MaterialImportResponse(BaseModel):
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[Dict[str, Any]] = []


class MaterialExportRequest(BaseModel):
    format: str = Field("csv", regex="^(csv|xlsx)$")
    enabled_only: bool = False
    include_usage_stats: bool = False