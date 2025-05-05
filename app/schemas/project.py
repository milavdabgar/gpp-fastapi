from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

# Event schemas
class ScheduleItemBase(BaseModel):
    time: str
    activity: str
    location: str
    coordinator: Dict[str, str]  # {"userId": "...", "name": "..."}
    notes: str = ""

class ScheduleItemCreate(ScheduleItemBase):
    """Schema for creating schedule items"""
    pass

class ScheduleItemUpdate(BaseModel):
    """Schema for updating schedule items"""
    time: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    coordinator: Optional[Dict[str, str]] = None
    notes: Optional[str] = None

class EventBase(BaseModel):
    name: str
    description: str
    academic_year: str
    event_date: datetime
    registration_start_date: datetime
    registration_end_date: datetime
    is_active: bool = True
    status: str = "upcoming"
    publish_results: bool = False

class EventCreate(EventBase):
    schedule: List[ScheduleItemBase] = []
    departments: List[str] = []  # Department IDs

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    academic_year: Optional[str] = None
    event_date: Optional[datetime] = None
    registration_start_date: Optional[datetime] = None
    registration_end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    publish_results: Optional[bool] = None
    departments: Optional[List[str]] = None  # Department IDs

class EventInDB(EventBase):
    id: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class EventResponse(EventBase):
    id: str
    schedule: List[ScheduleItemBase] = []
    departments: List[Dict[str, Any]] = []  # Department objects
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class PublishResultsRequest(BaseModel):
    publish_results: bool

class ScheduleUpdateRequest(BaseModel):
    schedule: List[ScheduleItemBase]

# Team schemas
class TeamMemberBase(BaseModel):
    user_id: str
    name: str
    enrollment_no: str
    role: str = "Member"
    is_leader: bool = False

class TeamMemberCreate(TeamMemberBase):
    """Schema for creating team members"""
    pass

class TeamBase(BaseModel):
    name: str
    department_id: str
    event_id: str
    members: List[TeamMemberBase] = []

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[str] = None
    event_id: Optional[str] = None
    members: Optional[List[Dict[str, Any]]] = None

class TeamInDB(TeamBase):
    id: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class TeamResponse(TeamBase):
    id: str
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class TeamWithDetails(TeamResponse):
    department: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    members: List[Dict[str, Any]] = []

# Location schemas
class LocationBase(BaseModel):
    location_id: str
    section: str
    position: int
    department_id: str
    event_id: str
    is_assigned: bool = False

class LocationCreate(LocationBase):
    pass

class LocationBatchCreate(BaseModel):
    section: str
    start_position: int
    end_position: int
    department_id: str
    event_id: str

class LocationUpdate(BaseModel):
    section: Optional[str] = None
    position: Optional[int] = None
    department_id: Optional[str] = None
    event_id: Optional[str] = None
    is_assigned: Optional[bool] = None

class LocationInDB(LocationBase):
    id: str
    project_id: Optional[str] = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class LocationResponse(LocationBase):
    id: str
    project_id: Optional[str] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class LocationWithDetails(LocationResponse):
    department: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

class AssignProjectRequest(BaseModel):
    project_id: str

# Project schemas
class RequirementsBase(BaseModel):
    power: bool = False
    internet: bool = False
    special_space: bool = False
    other_requirements: str = ""

class GuideBase(BaseModel):
    user_id: str
    name: str
    department: str  # Department ID
    contact_number: str

class ProjectBase(BaseModel):
    title: str
    category: str
    abstract: str
    department_id: str
    status: ProjectStatus = ProjectStatus.DRAFT
    requirements: RequirementsBase = Field(default_factory=RequirementsBase)
    guide: GuideBase
    team_id: str
    event_id: str
    location_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    abstract: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[ProjectStatus] = None
    requirements: Optional[Dict[str, Any]] = None
    guide: Optional[Dict[str, Any]] = None
    team_id: Optional[str] = None
    event_id: Optional[str] = None
    location_id: Optional[str] = None

class EvaluationBase(BaseModel):
    score: float
    feedback: str

class DeptEvaluationRequest(EvaluationBase):
    pass

class CentralEvaluationRequest(EvaluationBase):
    pass

class EvaluationResponse(EvaluationBase):
    completed: bool = True
    jury_id: str
    evaluated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class ProjectInDB(ProjectBase):
    id: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    dept_evaluation: Optional[EvaluationResponse] = None
    central_evaluation: Optional[EvaluationResponse] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class ProjectResponse(ProjectBase):
    id: str
    dept_evaluation: Optional[EvaluationResponse] = None
    central_evaluation: Optional[EvaluationResponse] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class ProjectWithDetails(ProjectResponse):
    department: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    guide_user: Optional[Dict[str, Any]] = None
    guide_department: Optional[Dict[str, Any]] = None

# For project statistics
class ProjectStatistics(BaseModel):
    total: int = 0
    evaluated: int = 0
    pending: int = 0
    average_score: float = 0
    department_wise: Dict[str, int] = {}

class ProjectCategoryCounts(BaseModel):
    category: str
    count: int
    department_count: int
    average_score: float
    department_info: List[str]

class CategoryResponse(BaseModel):
    category_counts: List[ProjectCategoryCounts]