from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class QuestionScore(BaseModel):
    q1_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q2_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q3_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q4_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q5_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q6_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q7_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q8_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q9_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q10_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q11_score: float = Field(default=0.0, ge=0.0, le=5.0)
    q12_score: float = Field(default=0.0, ge=0.0, le=5.0)

class FeedbackBase(QuestionScore):
    year: int = Field(..., description="Academic year")
    term: str = Field(..., description="Term (Odd/Even)")
    branch: str = Field(..., description="Branch code")
    semester: int = Field(..., description="Semester number")
    term_start: Optional[datetime] = None
    term_end: Optional[datetime] = None
    subject_code: str = Field(..., description="Subject code")
    subject_name: str = Field(..., description="Subject name")
    faculty_name: str = Field(..., description="Faculty name")
    total_responses: int = Field(default=0, description="Number of responses")
    average_score: float = Field(default=0.0, description="Average score across all questions")

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    year: Optional[int] = None
    term: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    term_start: Optional[datetime] = None
    term_end: Optional[datetime] = None
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    faculty_name: Optional[str] = None
    total_responses: Optional[int] = None
    average_score: Optional[float] = None
    q1_score: Optional[float] = None
    q2_score: Optional[float] = None
    q3_score: Optional[float] = None
    q4_score: Optional[float] = None
    q5_score: Optional[float] = None
    q6_score: Optional[float] = None
    q7_score: Optional[float] = None
    q8_score: Optional[float] = None
    q9_score: Optional[float] = None
    q10_score: Optional[float] = None
    q11_score: Optional[float] = None
    q12_score: Optional[float] = None

class FeedbackInDB(FeedbackBase):
    id: str
    report_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class FeedbackResponse(FeedbackBase):
    id: str
    report_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2

class FeedbackAnalysisResult(BaseModel):
    feedback_id: str
    statistics: Dict[str, Any]
    recommendations: List[str]