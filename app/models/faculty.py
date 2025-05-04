from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, func, ARRAY, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

class Faculty(Base):
    """Faculty model, equivalent to MongoDB's FacultyModel"""
    __tablename__ = "faculties"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    employee_id = Column(String(20), nullable=False, unique=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    designation = Column(String(50), nullable=False)
    specializations = Column(ARRAY(String), nullable=False)
    joining_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    
    # Experience
    experience_years = Column(Integer, nullable=False, default=0)
    experience_details = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="faculty", foreign_keys=[user_id])
    department = relationship("Department", back_populates="faculties")
    qualifications = relationship("FacultyQualification", back_populates="faculty", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "employee_id": self.employee_id,
            "department_id": self.department_id,
            "designation": self.designation,
            "specializations": self.specializations,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "status": self.status,
            "experience": {
                "years": self.experience_years,
                "details": self.experience_details
            },
            "qualifications": [q.to_dict() for q in self.qualifications],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class FacultyQualification(Base):
    """Faculty qualification model"""
    __tablename__ = "faculty_qualifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id = Column(String(36), ForeignKey("faculties.id"), nullable=False)
    degree = Column(String(100), nullable=False)
    field = Column(String(100), nullable=False)
    institution = Column(String(200), nullable=False)
    year = Column(Integer, nullable=False)
    
    # Relationships
    faculty = relationship("Faculty", back_populates="qualifications")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "degree": self.degree,
            "field": self.field,
            "institution": self.institution,
            "year": self.year,
        }