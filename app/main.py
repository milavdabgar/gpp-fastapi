from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    FacultyCreate, FacultyUpdate, FacultyResponse, FacultyWithUser,
    DataResponse, ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.faculty import (
    get_faculty, get_faculties, create_faculty, update_faculty,
    delete_faculty, get_faculties_by_department, import_faculties_from_csv,
    export_faculties_to_csv
)
from app.middleware.auth import require_admin_or_principal
from app.middleware.error import AppError

router = APIRouter(
    prefix="/faculty",
    tags=["faculty"]
)

# All routes require admin or principal role
@router.get("", response_model=PaginatedResponse[List[FacultyWithUser]])
async def get_all_faculty(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[str] = None,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get all faculty members with filtering and pagination
    """
    skip = (page - 1) * limit
    faculty_members, total = get_faculties(db, skip, limit, department_id)
    
    return PaginatedResponse(
        status="success",
        data=[FacultyWithUser.from_orm(faculty) for faculty in faculty_members],
        pagination=PaginatedMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit
        )
    )

@router.post("", response_model=DataResponse[FacultyResponse])
async def add_faculty(
    faculty_data: FacultyCreate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Create a new faculty member
    """
    try:
        faculty = create_faculty(db, faculty_data)
        return DataResponse(
            status="success",
            message="Faculty created successfully",
            data=FacultyResponse.from_orm(faculty)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/export-csv", response_class=Response)
async def export_faculty_csv(
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Export faculty members to a CSV file
    """
    try:
        csv_content = export_faculties_to_csv(db)
        
        # Return CSV file
        response = Response(content=csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=faculty.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
        
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.post("/upload-csv", response_model=DataResponse)
async def upload_faculty_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Import faculty members from a CSV file
    """
    try:
        result = import_faculties_from_csv(db, file)
        return DataResponse(
            status="success",
            message="Faculty imported successfully",
            data=result
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/{faculty_id}", response_model=DataResponse[FacultyWithUser])
async def get_faculty_by_id(
    faculty_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get a faculty member by ID
    """
    faculty = get_faculty(db, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    
    return DataResponse(
        status="success",
        data=FacultyWithUser.from_orm(faculty)
    )

@router.patch("/{faculty_id}", response_model=DataResponse[FacultyResponse])
async def update_faculty_by_id(
    faculty_id: str,
    faculty_data: FacultyUpdate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Update a faculty member by ID
    """
    try:
        updated_faculty = update_faculty(db, faculty_id, faculty_data)
        if not updated_faculty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Faculty not found"
            )
        
        return DataResponse(
            status="success",
            message="Faculty updated successfully",
            data=F