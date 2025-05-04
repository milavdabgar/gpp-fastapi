from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class QualificationBase(BaseModel):
    degree: str
    field: str
    institution: str
    year: int

class QualificationCreate(QualificationBase):
    pass

class QualificationUpdate(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[int] = None

class QualificationResponse(QualificationBase):
    id: str
    
    class Config:
        orm_mode = True

class ExperienceBase(BaseModel):
    years: int = 0
    details: str = ""

class FacultyBase(BaseModel):
    employee_id: str
    department_id: str
    designation: str
    specializations: List[str]
    joining_date: datetime
    status: str = "active"
    experience: ExperienceBase = Field(default_factory=ExperienceBase)
    qualifications: List[QualificationBase] = []

class FacultyCreate(FacultyBase):
    name: str  # User name
    email: str  # User email
    password: Optional[str] = None  # User password

class FacultyUpdate(BaseModel):
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    designation: Optional[str] = None
    specializations: Optional[List[str]] = None
    joining_date: Optional[datetime] = None
    status: Optional[str] = None
    experience: Optional[Dict[str, Any]] = None
    qualifications: Optional[List[Dict[str, Any]]] = None
    name: Optional[str] = None  # User name
    email: Optional[str] = None  # User email

class FacultyInDB(FacultyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FacultyResponse(FacultyBase):
    id: str
    user_id: str
    qualifications: List[QualificationResponse]
    
    class Config:
        orm_mode = True

class FacultyWithUser(FacultyResponse):
    user: Optional[Dict[str, Any]] = None
    department: Optional[Dict[str, Any]] = None