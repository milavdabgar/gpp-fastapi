from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, func, ARRAY, JSON, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class ProjectStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class ProjectEvent(Base):
    """Project event model, equivalent to MongoDB's ProjectEventModel"""
    __tablename__ = "project_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    academic_year = Column(String(20), nullable=False)
    event_date = Column(DateTime, nullable=False)
    registration_start_date = Column(DateTime, nullable=False)
    registration_end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="upcoming")
    publish_results = Column(Boolean, default=False)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    schedule = relationship("EventSchedule", back_populates="event", cascade="all, delete-orphan")
    teams = relationship("ProjectTeam", back_populates="event")
    projects = relationship("Project", back_populates="event")
    locations = relationship("ProjectLocation", back_populates="event")
    
    # Many-to-many relationship with departments
    departments = relationship(
        "Department",
        secondary="event_departments",
        backref="events"
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "academic_year": self.academic_year,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "registration_start_date": self.registration_start_date.isoformat() if self.registration_start_date else None,
            "registration_end_date": self.registration_end_date.isoformat() if self.registration_end_date else None,
            "is_active": self.is_active,
            "status": self.status,
            "publish_results": self.publish_results,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "schedule": [s.to_dict() for s in self.schedule],
            "departments": [{"id": d.id, "name": d.name, "code": d.code} for d in self.departments]
        }

# Association table for event-department relationship
event_departments = Table(
    'event_departments',
    Base.metadata,
    Column('event_id', ForeignKey('project_events.id'), primary_key=True),
    Column('department_id', ForeignKey('departments.id'), primary_key=True)
)

class EventSchedule(Base):
    """Event schedule model"""
    __tablename__ = "event_schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("project_events.id"), nullable=False)
    time = Column(String(50), nullable=False)
    activity = Column(String(200), nullable=False)
    location = Column(String(100), nullable=False)
    coordinator_id = Column(String(36), ForeignKey("users.id"))
    coordinator_name = Column(String(100), nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    event = relationship("ProjectEvent", back_populates="schedule")
    coordinator = relationship("User")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "time": self.time,
            "activity": self.activity,
            "location": self.location,
            "coordinator": {
                "userId": self.coordinator_id,
                "name": self.coordinator_name
            },
            "notes": self.notes or "",
        }

class ProjectTeam(Base):
    """Project team model, equivalent to MongoDB's ProjectTeamModel"""
    __tablename__ = "project_teams"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("project_events.id"), nullable=False)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="teams")
    event = relationship("ProjectEvent", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team")
    
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "department_id": self.department_id,
            "event_id": self.event_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "members": [m.to_dict() for m in self.members]
        }

class TeamMember(Base):
    """Team member model"""
    __tablename__ = "team_members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), ForeignKey("project_teams.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    enrollment_no = Column(String(20), nullable=False)
    role = Column(String(50), default="Member")
    is_leader = Column(Boolean, default=False)
    
    # Relationships
    team = relationship("ProjectTeam", back_populates="members")
    user = relationship("User")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "name": self.name,
            "enrollment_no": self.enrollment_no,
            "role": self.role,
            "is_leader": self.is_leader
        }

class ProjectLocation(Base):
    """Project location model, equivalent to MongoDB's ProjectLocationModel"""
    __tablename__ = "project_locations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(20), nullable=False, unique=True)
    section = Column(String(10), nullable=False)
    position = Column(Integer, nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("project_events.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    is_assigned = Column(Boolean, default=False)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department")
    event = relationship("ProjectEvent", back_populates="locations")
    project = relationship("Project", foreign_keys=[project_id], back_populates="location")
    
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "location_id": self.location_id,
            "section": self.section,
            "position": self.position,
            "department_id": self.department_id,
            "event_id": self.event_id,
            "project_id": self.project_id,
            "is_assigned": self.is_assigned,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class DepartmentEvaluation(Base):
    """Department evaluation model"""
    __tablename__ = "department_evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, unique=True)
    completed = Column(Boolean, default=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    jury_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="dept_evaluation")
    jury = relationship("User", foreign_keys=[jury_id])
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "completed": self.completed,
            "score": self.score,
            "feedback": self.feedback,
            "jury_id": self.jury_id,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None
        }

class CentralEvaluation(Base):
    """Central evaluation model"""
    __tablename__ = "central_evaluations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, unique=True)
    completed = Column(Boolean, default=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    jury_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    evaluated_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="central_evaluation")
    jury = relationship("User", foreign_keys=[jury_id])
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "completed": self.completed,
            "score": self.score,
            "feedback": self.feedback,
            "jury_id": self.jury_id,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None
        }

class Project(Base):
    """Project model, equivalent to MongoDB's ProjectModel"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    abstract = Column(Text, nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    status = Column(String(20), default=ProjectStatus.DRAFT.value)
    
    # Requirements
    power_required = Column(Boolean, default=False)
    internet_required = Column(Boolean, default=False)
    special_space_required = Column(Boolean, default=False)
    other_requirements = Column(Text, nullable=True)
    
    # Guide
    guide_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    guide_name = Column(String(100), nullable=False)
    guide_department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    guide_contact = Column(String(20), nullable=False)
    
    # Relationships
    team_id = Column(String(36), ForeignKey("project_teams.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("project_events.id"), nullable=False)
    location_id = Column(String(36), ForeignKey("project_locations.id"), nullable=True)
    
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department")
    guide_user = relationship("User", foreign_keys=[guide_user_id])
    guide_department = relationship("Department", foreign_keys=[guide_department_id])
    team = relationship("ProjectTeam", back_populates="projects")
    event = relationship("ProjectEvent", back_populates="projects")
    location = relationship("ProjectLocation", foreign_keys=[location_id], back_populates="project")
    
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Evaluations
    dept_evaluation = relationship("DepartmentEvaluation", back_populates="project", uselist=False, cascade="all, delete-orphan")
    central_evaluation = relationship("CentralEvaluation", back_populates="project", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "abstract": self.abstract,
            "department_id": self.department_id,
            "status": self.status,
            "requirements": {
                "power": self.power_required,
                "internet": self.internet_required,
                "specialSpace": self.special_space_required,
                "otherRequirements": self.other_requirements or ""
            },
            "guide": {
                "userId": self.guide_user_id,
                "name": self.guide_name,
                "department": self.guide_department_id,
                "contactNumber": self.guide_contact
            },
            "team_id": self.team_id,
            "event_id": self.event_id,
            "location_id": self.location_id,
            "dept_evaluation": self.dept_evaluation.to_dict() if self.dept_evaluation else None,
            "central_evaluation": self.central_evaluation.to_dict() if self.central_evaluation else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }