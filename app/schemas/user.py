from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    department_id: Optional[str] = None
    
class UserCreate(UserBase):
    password: str
    roles: List[str] = Field(default_factory=lambda: ["student"])
    selected_role: Optional[str] = None
    
    @validator('roles')
    def validate_roles(cls, v):
        valid_roles = ["student", "faculty", "hod", "principal", "admin", "jury"]
        for role in v:
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}")
        return v
    
    @validator('selected_role')
    def validate_selected_role(cls, v, values):
        if v is None and 'roles' in values and values['roles']:
            return values['roles'][0]
        if v is not None and 'roles' in values and v not in values['roles']:
            raise ValueError(f"Selected role must be one of the assigned roles: {values['roles']}")
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[str] = None
    roles: Optional[List[str]] = None
    
    @validator('roles')
    def validate_roles(cls, v):
        if v is None:
            return v
        valid_roles = ["student", "faculty", "hod", "principal", "admin", "jury"]
        for role in v:
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}")
        return v

class UserInDB(UserBase):
    id: str
    roles: List[str]
    selected_role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: str
    roles: List[str]
    selected_role: str
    
    class Config:
        orm_mode = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    id: str
    selected_role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    selected_role: Optional[str] = None

class RoleSwitchRequest(BaseModel):
    role: str
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["student", "faculty", "hod", "principal", "admin", "jury"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}")
        return v

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: str
    permissions: List[str]
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = ["create", "read", "update", "delete"]
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f"Invalid permission: {permission}")
        return v

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    
    @validator('permissions')
    def validate_permissions(cls, v):
        if v is None:
            return v
        valid_permissions = ["create", "read", "update", "delete"]
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f"Invalid permission: {permission}")
        return v

class RoleInDB(RoleBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class RoleResponse(RoleBase):
    class Config:
        orm_mode = True