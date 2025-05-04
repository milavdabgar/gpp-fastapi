from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class SemesterStatus(str, Enum):
    CLEARED = "CLEARED"
    PENDING = "PENDING"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"

class StudentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    DROPPED = "dropped"

class GuardianBase(BaseModel):
    name: str = ""
    relation: str = ""
    contact: str = ""
    occupation: str = ""

class ContactBase(BaseModel):
    mobile: str = ""
    email: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""

class EducationBase(BaseModel):
    degree: str
    institution: str
    board: str
    percentage: float
    year_of_passing: int

class SemesterStatusBase(BaseModel):
    sem1: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem2: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem3: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem4: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem5: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem6: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem7: SemesterStatus = SemesterStatus.NOT_ATTEMPTED
    sem8: SemesterStatus = SemesterStatus.NOT_ATTEMPTED

class StudentBase(BaseModel):
    enrollment_no: str
    department_id: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    personal_email: Optional[str] = None
    institutional_email: str
    batch: Optional[str] = None
    semester: int = 1
    status: StudentStatus = StudentStatus.ACTIVE
    admission_year: int
    gender: Optional[str] = None
    category: Optional[str] = None
    aadhar_no: Optional[str] = None
    is_complete: bool = False
    term_close: bool = False
    is_cancel: bool = False
    is_pass_all: bool = False
    convo_year: Optional[int] = None
    shift: int = 1

class StudentCreate(StudentBase):
    name: str  # User name
    email: str  # User email
    password: Optional[str] = None  # User password
    guardian: Optional[GuardianBase] = None
    contact: Optional[ContactBase] = None
    education_background: List[EducationBase] = []
    semester_status: Optional[SemesterStatusBase] = None

class StudentUpdate(BaseModel):
    enrollment_no: Optional[str] = None
    department_id: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    personal_email: Optional[str] = None
    institutional_email: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    status: Optional[StudentStatus] = None
    admission_year: Optional[int] = None
    gender: Optional[str] = None
    category: Optional[str] = None
    aadhar_no: Optional[str] = None
    is_complete: Optional[bool] = None
    term_close: Optional[bool] = None
    is_cancel: Optional[bool] = None
    is_pass_all: Optional[bool] = None
    convo_year: Optional[int] = None
    shift: Optional[int] = None
    name: Optional[str] = None  # User name
    email: Optional[str] = None  # User email
    guardian: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    education_background: Optional[List[Dict[str, Any]]] = None
    semester_status: Optional[Dict[str, Any]] = None

class StudentInDB(StudentBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class StudentResponse(StudentBase):
    id: str
    user_id: Optional[str] = None
    guardian: Optional[GuardianBase] = None
    contact: Optional[ContactBase] = None
    education_background: List[EducationBase] = []
    semester_status: Optional[SemesterStatusBase] = None
    
    class Config:
        orm_mode = True

class StudentWithUser(StudentResponse):
    user: Optional[Dict[str, Any]] = None
    department: Optional[Dict[str, Any]] = None

# For syncing student users
class SyncResult(BaseModel):
    created: int = 0
    existing: int = 0
    errors: List[str] = []