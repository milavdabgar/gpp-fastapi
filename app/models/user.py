from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, func, ARRAY, Text
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from datetime import datetime
import uuid

from app.database import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Association table for user roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_name', String(20), ForeignKey('roles.name'), primary_key=True)
)

class User(Base):
    """User model, equivalent to MongoDB's UserModel"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password = Column(String(100), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    
    # Store roles as a relationship to user_roles table
    roles = relationship("Role", secondary=user_roles, backref="users")
    selected_role = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    faculty = relationship("Faculty", back_populates="user", uselist=False)
    student = relationship("Student", back_populates="user", uselist=False)
    
    def set_password(self, password):
        """Hash the password"""
        self.password = pwd_context.hash(password)
    
    def verify_password(self, plain_password):
        """Verify the hashed password"""
        return pwd_context.verify(plain_password, self.password)
    
    def to_dict(self, exclude_fields=None):
        """Convert model to dictionary, excluding sensitive fields"""
        if exclude_fields is None:
            exclude_fields = ["password"]
            
        result = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department_id": self.department_id,
            "roles": [role.name for role in self.roles],
            "selected_role": self.selected_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Remove excluded fields
        for field in exclude_fields:
            if field in result:
                del result[field]
                
        return result

class Role(Base):
    """Role model, equivalent to MongoDB's RoleModel"""
    __tablename__ = "roles"
    
    name = Column(String(20), primary_key=True)
    description = Column(String(200), nullable=False)
    # Store permissions as a comma-separated string instead of JSON
    permissions = Column(String(500), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions.split(',') if self.permissions else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }