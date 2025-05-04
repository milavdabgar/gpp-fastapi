from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    code: str
    description: str
    established_date: datetime
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    hod_id: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    hod_id: Optional[str] = None
    established_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class DepartmentInDB(DepartmentBase):
    id: str
    hod_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DepartmentResponse(DepartmentBase):
    id: str
    hod_id: Optional[str] = None
    
    class Config:
        orm_mode = True

class DepartmentWithHOD(DepartmentResponse):
    hod: Optional[dict] = None

# For statistics/dashboard
class DepartmentStats(BaseModel):
    active_count: int
    inactive_count: int