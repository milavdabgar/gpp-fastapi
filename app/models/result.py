from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, func, ARRAY, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

from app.database import Base

class Result(Base):
    """Result model, equivalent to MongoDB's ResultModel"""
    __tablename__ = "results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    st_id = Column(String(50), nullable=False)
    enrollment_no = Column(String(20), nullable=False, index=True)
    extype = Column(String(20), nullable=True)
    examid = Column(Integer, nullable=True)
    exam = Column(String(100), nullable=True)
    declaration_date = Column(DateTime, nullable=True)
    academic_year = Column(String(20), nullable=True)
    semester = Column(Integer, nullable=False)
    unit_no = Column(Float, nullable=True)
    exam_number = Column(Float, nullable=True)
    name = Column(String(100), nullable=False)
    instcode = Column(Integer, nullable=True)
    inst_name = Column(String(200), nullable=True)
    course_name = Column(String(100), nullable=True)
    branch_code = Column(Integer, nullable=True)
    branch_name = Column(String(100), nullable=False)
    
    # Summary data
    total_credits = Column(Float, nullable=True)
    earned_credits = Column(Float, nullable=True)
    spi = Column(Float, nullable=True)
    cpi = Column(Float, nullable=True)
    cgpa = Column(Float, nullable=True)
    result = Column(String(20), nullable=True)
    trials = Column(Integer, default=1)
    remark = Column(String(100), nullable=True)
    current_backlog = Column(Integer, default=0)
    total_backlog = Column(Integer, default=0)
    
    # Batch tracking
    upload_batch = Column(String(36), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subjects = relationship("ResultSubject", back_populates="result", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Create unique compound index
        {"postgresql_partition_by": "RANGE (examid)"}
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "st_id": self.st_id,
            "enrollment_no": self.enrollment_no,
            "extype": self.extype,
            "examid": self.examid,
            "exam": self.exam,
            "declaration_date": self.declaration_date.isoformat() if self.declaration_date else None,
            "academic_year": self.academic_year,
            "semester": self.semester,
            "unit_no": self.unit_no,
            "exam_number": self.exam_number,
            "name": self.name,
            "instcode": self.instcode,
            "inst_name": self.inst_name,
            "course_name": self.course_name,
            "branch_code": self.branch_code,
            "branch_name": self.branch_name,
            "subjects": [s.to_dict() for s in self.subjects],
            "total_credits": self.total_credits,
            "earned_credits": self.earned_credits,
            "spi": self.spi,
            "cpi": self.cpi,
            "cgpa": self.cgpa,
            "result": self.result,
            "trials": self.trials,
            "remark": self.remark,
            "current_backlog": self.current_backlog,
            "total_backlog": self.total_backlog,
            "upload_batch": self.upload_batch,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ResultSubject(Base):
    """Result subject model"""
    __tablename__ = "result_subjects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String(36), ForeignKey("results.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    credits = Column(Float, default=0)
    grade = Column(String(5), nullable=True)
    is_backlog = Column(Boolean, default=False)
    
    # Grade details
    theory_ese_grade = Column(String(5), nullable=True)
    theory_pa_grade = Column(String(5), nullable=True)
    theory_total_grade = Column(String(5), nullable=True)
    practical_pa_grade = Column(String(5), nullable=True)
    practical_viva_grade = Column(String(5), nullable=True)
    practical_total_grade = Column(String(5), nullable=True)
    
    # Relationships
    result = relationship("Result", back_populates="subjects")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "grade": self.grade,
            "is_backlog": self.is_backlog,
            "theory_ese_grade": self.theory_ese_grade,
            "theory_pa_grade": self.theory_pa_grade,
            "theory_total_grade": self.theory_total_grade,
            "practical_pa_grade": self.practical_pa_grade,
            "practical_viva_grade": self.practical_viva_grade,
            "practical_total_grade": self.practical_total_grade
        }