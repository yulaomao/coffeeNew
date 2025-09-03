from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class RecipeStep(BaseModel):
    step_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    type: str = Field(..., max_length=50)  # e.g., "dispense", "heat", "wait"
    params: Dict[str, Any] = {}
    duration: Optional[float] = None  # seconds
    temperature: Optional[float] = None  # celsius
    materials: Optional[List[str]] = None  # material codes


class RecipeMaterialMapping(BaseModel):
    material_code: str = Field(..., max_length=50)
    bin_index: int = Field(..., ge=0)
    amount: float = Field(..., gt=0)
    unit: str = Field(..., max_length=20)


class RecipeSchema(BaseModel):
    version: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    prep_time: Optional[int] = None  # seconds
    steps: List[RecipeStep]
    materials: List[RecipeMaterialMapping]
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('steps')
    def steps_not_empty(cls, v):
        if not v:
            raise ValueError('Steps list cannot be empty')
        return v
    
    @validator('materials')
    def materials_not_empty(cls, v):
        if not v:
            raise ValueError('Materials list cannot be empty')
        return v


class RecipeCreateRequest(BaseModel):
    name: str = Field(..., max_length=200)
    version: str = Field(..., max_length=50)
    schema: RecipeSchema
    enabled: bool = True


class RecipeUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=50)
    schema: Optional[RecipeSchema] = None
    enabled: Optional[bool] = None


class RecipeResponse(BaseModel):
    id: int
    name: str
    version: Optional[str]
    schema: Optional[Dict[str, Any]]
    enabled: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class RecipePackageResponse(BaseModel):
    package_id: str
    version: Optional[str]
    package_url: Optional[str]
    md5: Optional[str]
    size: Optional[int]
    manifest: Optional[Dict[str, Any]]
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PublishRecipeRequest(BaseModel):
    device_compatibility: Optional[List[str]] = None  # List of compatible device models
    notes: Optional[str] = Field(None, max_length=500)


class DispatchRecipeRequest(BaseModel):
    device_ids: List[str] = Field(..., min_items=1)
    note: Optional[str] = Field(None, max_length=500)
    
    @validator('device_ids')
    def device_ids_not_empty(cls, v):
        if not v:
            raise ValueError('Device IDs list cannot be empty')
        return v