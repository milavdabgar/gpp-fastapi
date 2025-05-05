from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# Team Member Models
class TeamMemberBase(BaseModel):
    """Base model for team members"""
    user_id: str
    name: str
    enrollment_no: str
    role: str = "Member"
    is_leader: bool = False

class TeamMemberCreate(TeamMemberBase):
    """Schema for creating team members"""
    pass

class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""
    id: str

    class Config:
        from_attributes = True  # Previously orm_mode = True

# Team Models
class TeamBase(BaseModel):
    """Base team model"""
    name: str
    department_id: str
    event_id: str

class TeamCreate(TeamBase):
    """Schema for creating teams"""
    members: List[Dict[str, Any]] = []

class TeamUpdate(BaseModel):
    """Schema for updating teams"""
    name: Optional[str] = None
    department_id: Optional[str] = None
    event_id: Optional[str] = None

class TeamResponse(TeamBase):
    """Schema for team response"""
    id: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    members: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True  # Previously orm_mode = True