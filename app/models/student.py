from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, func, ARRAY, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class SemesterStatus(enum.Enum):
    CLEARED = "CLEARED"
    PENDING = "PENDING"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"

class StudentStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    DROPPED = "dropped"

class Student(Base):
    """Student model, equivalent to MongoDB's StudentModel"""
    __tablename__ = "students"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    
    # Personal details
    first_name = Column(String(50), nullable=True)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    full_name = Column(String(150), nullable=True)
    enrollment_no = Column(String(20), nullable=False, unique=True, index=True)
    personal_email = Column(String(100), nullable=True)
    institutional_email = Column(String(100), nullable=False, unique=True)
    
    # Academic details
    batch = Column(String(20), nullable=True)
    semester = Column(Integer, default=1)
    status = Column(String(20), nullable=False, default="active")
    admission_year = Column(Integer, nullable=False)
    convo_year = Column(Integer, nullable=True)
    
    # Other details
    gender = Column(String(2), nullable=True)
    category = Column(String(10), nullable=True)
    aadhar_no = Column(String(20), nullable=True)
    shift = Column(Integer, default=1)
    
    # Flags
    is_complete = Column(Boolean, default=False)
    term_close = Column(Boolean, default=False)
    is_cancel = Column(Boolean, default=False)
    is_pass_all = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="student")
    department = relationship("Department", back_populates="students")
    guardian = relationship("StudentGuardian", back_populates="student", uselist=False, cascade="all, delete-orphan")
    contact = relationship("StudentContact", back_populates="student", uselist=False, cascade="all, delete-orphan")
    education_background = relationship("StudentEducation", back_populates="student", cascade="all, delete-orphan")
    semester_status = relationship("StudentSemesterStatus", back_populates="student", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "enrollment_no": self.enrollment_no,
            "personal_email": self.personal_email,
            "institutional_email": self.institutional_email,
            "batch": self.batch,
            "semester": self.semester,
            "status": self.status,
            "admission_year": self.admission_year,
            "gender": self.gender,
            "category": self.category,
            "aadhar_no": self.aadhar_no,
            "is_complete": self.is_complete,
            "term_close": self.term_close,
            "is_cancel": self.is_cancel,
            "is_pass_all": self.is_pass_all,
            "convo_year": self.convo_year,
            "shift": self.shift,
            "guardian": self.guardian.to_dict() if self.guardian else None,
            "contact": self.contact.to_dict() if self.contact else None,
            "education_background": [edu.to_dict() for edu in self.education_background],
            "semester_status": self.semester_status.to_dict() if self.semester_status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class StudentGuardian(Base):
    """Student guardian model"""
    __tablename__ = "student_guardians"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, unique=True)
    name = Column(String(100), nullable=True)
    relation = Column(String(50), nullable=True)
    contact = Column(String(20), nullable=True)
    occupation = Column(String(100), nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="guardian")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "name": self.name or "",
            "relation": self.relation or "",
            "contact": self.contact or "",
            "occupation": self.occupation or "",
        }

class StudentContact(Base):
    """Student contact model"""
    __tablename__ = "student_contacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, unique=True)
    mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(300), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="contact")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "mobile": self.mobile or "",
            "email": self.email or "",
            "address": self.address or "",
            "city": self.city or "",
            "state": self.state or "",
            "pincode": self.pincode or "",
        }

class StudentEducation(Base):
    """Student education background model"""
    __tablename__ = "student_education"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    degree = Column(String(100), nullable=False)
    institution = Column(String(200), nullable=False)
    board = Column(String(100), nullable=False)
    percentage = Column(Integer, nullable=False)
    year_of_passing = Column(Integer, nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="education_background")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "degree": self.degree,
            "institution": self.institution,
            "board": self.board,
            "percentage": self.percentage,
            "year_of_passing": self.year_of_passing,
        }

class StudentSemesterStatus(Base):
    """Student semester status model"""
    __tablename__ = "student_semester_status"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, unique=True)
    sem1 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem2 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem3 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem4 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem5 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem6 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem7 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    sem8 = Column(String(20), default=SemesterStatus.NOT_ATTEMPTED.value)
    
    # Relationships
    student = relationship("Student", back_populates="semester_status")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "sem1": self.sem1,
            "sem2": self.sem2,
            "sem3": self.sem3,
            "sem4": self.sem4,
            "sem5": self.sem5,
            "sem6": self.sem6,
            "sem7": self.sem7,
            "sem8": self.sem8,
        }