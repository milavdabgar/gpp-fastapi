from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

class Department(Base):
    """Department model, equivalent to MongoDB's DepartmentModel"""
    __tablename__ = "departments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=False)
    hod_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    established_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hod = relationship("User", foreign_keys=[hod_id])
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    faculties = relationship("Faculty", back_populates="department")
    students = relationship("Student", back_populates="department")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "hod_id": self.hod_id,
            "established_date": self.established_date.isoformat() if self.established_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }