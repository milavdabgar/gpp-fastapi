from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    ResultCreate, ResultResponse, ResultAnalysis, BatchResponse,
    DataResponse, ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.result import (
    get_result, get_results, import_results, export_results,
    get_branch_analysis, get_upload_batches, delete_result,
    delete_results_by_batch, get_student_results
)
from app.middleware.auth import get_authenticated_user, require_admin
from app.middleware.error import AppError

router = APIRouter(
    prefix="/results",
    tags=["results"]
)

@router.get("", response_model=PaginatedResponse[List[ResultResponse]])
async def get_all_results(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    branch: Optional[str] = None,
    semester: Optional[int] = None,
    exam_type: Optional[str] = None,
    sort_by: str = "declaration_date",
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get all results with filtering and pagination"""
    return await get_results(db, page, limit, search, branch, semester, exam_type, sort_by)

@router.post("/import", response_model=ResponseBase)
async def import_results_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import results from CSV file"""
    return await import_results(db, file)

@router.get("/export", response_class=Response)
async def export_results_endpoint(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export results to CSV"""
    return await export_results(db)

@router.get("/analysis", response_model=List[ResultAnalysis])
async def get_analysis(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get branch-wise result analysis"""
    return await get_branch_analysis(db)

@router.get("/batches", response_model=List[BatchResponse])
async def get_batches(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get uploaded result batches"""
    return await get_upload_batches(db)

@router.delete("/batch/{batch_id}", response_model=ResponseBase)
async def delete_batch(
    batch_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete results by batch ID"""
    return await delete_results_by_batch(db, batch_id)

@router.get("/student/{enrollment_no}", response_model=List[ResultResponse])
async def get_student_results_endpoint(
    enrollment_no: str,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get results for a specific student"""
    if not current_user.is_admin and current_user.enrollment_no != enrollment_no:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these results"
        )
    return await get_student_results(db, enrollment_no)

@router.get("/{id}", response_model=ResultResponse)
async def get_result_endpoint(
    id: str,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Get a specific result by ID"""
    result = await get_result(db, id)
    if not current_user.is_admin and current_user.enrollment_no != result.student_enrollment_no:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this result"
        )
    return result

@router.delete("/{id}", response_model=ResponseBase)
async def delete_result_endpoint(
    id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a specific result"""
    return await delete_result(db, id)