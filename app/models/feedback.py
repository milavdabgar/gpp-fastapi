from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analysis"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    year = Column(Integer, nullable=False)
    term = Column(String, nullable=False)  # Odd/Even
    branch = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    term_start = Column(DateTime, nullable=True)
    term_end = Column(DateTime, nullable=True)
    subject_code = Column(String, nullable=False)
    subject_name = Column(String, nullable=False)
    faculty_name = Column(String, nullable=False)
    total_responses = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    
    # Individual question scores
    q1_score = Column(Float, default=0.0)
    q2_score = Column(Float, default=0.0)
    q3_score = Column(Float, default=0.0)
    q4_score = Column(Float, default=0.0)
    q5_score = Column(Float, default=0.0)
    q6_score = Column(Float, default=0.0)
    q7_score = Column(Float, default=0.0)
    q8_score = Column(Float, default=0.0)
    q9_score = Column(Float, default=0.0)
    q10_score = Column(Float, default=0.0)
    q11_score = Column(Float, default=0.0)
    q12_score = Column(Float, default=0.0)
    
    # Analysis results
    report_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)