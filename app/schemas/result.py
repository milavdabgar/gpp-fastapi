from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SubjectBase(BaseModel):
    code: str
    name: str
    credits: float = 0
    grade: Optional[str] = None
    is_backlog: bool = False
    theory_ese_grade: Optional[str] = None
    theory_pa_grade: Optional[str] = None
    theory_total_grade: Optional[str] = None
    practical_pa_grade: Optional[str] = None
    practical_viva_grade: Optional[str] = None
    practical_total_grade: Optional[str] = None

class ResultBase(BaseModel):
    st_id: str
    enrollment_no: str
    extype: Optional[str] = None
    examid: Optional[int] = None
    exam: Optional[str] = None
    declaration_date: Optional[datetime] = None
    academic_year: Optional[str] = None
    semester: int
    unit_no: Optional[float] = None
    exam_number: Optional[float] = None
    name: str
    instcode: Optional[int] = None
    inst_name: Optional[str] = None
    course_name: Optional[str] = None
    branch_code: Optional[int] = None
    branch_name: str
    subjects: List[SubjectBase] = []
    total_credits: Optional[float] = None
    earned_credits: Optional[float] = None
    spi: Optional[float] = None
    cpi: Optional[float] = None
    cgpa: Optional[float] = None
    result: Optional[str] = None
    trials: int = 1
    remark: Optional[str] = None
    current_backlog: int = 0
    total_backlog: int = 0
    upload_batch: Optional[str] = None

class ResultImport(BaseModel):
    results: List[ResultBase]

class ResultInDB(ResultBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ResultResponse(ResultBase):
    id: str
    
    class Config:
        orm_mode = True

class ImportResponse(BaseModel):
    status: str
    data: Dict[str, Any]

class BatchInfo(BaseModel):
    batch_id: str
    count: int
    latest_upload: datetime

class BatchesResponse(BaseModel):
    batches: List[BatchInfo]

class BranchSemesterAnalysis(BaseModel):
    branch_name: str
    semester: int
    total_students: int
    pass_count: int
    distinction_count: int
    first_class_count: int
    second_class_count: int
    avg_spi: float
    avg_cpi: float
    pass_percentage: float

class AnalysisResponse(BaseModel):
    analysis: List[BranchSemesterAnalysis]