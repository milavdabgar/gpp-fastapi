from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentWithUser, SyncResult,
    DataResponse, ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.student import (
    get_student, get_students, create_student, update_student,
    delete_student, get_students_by_department, sync_student_users,
    import_students_from_csv, export_students_to_csv
)
from app.middleware.auth import require_admin_or_principal
from app.middleware.error import AppError

router = APIRouter(
    prefix="/students",
    tags=["students"]
)

# All routes require admin or principal role
@router.get("", response_model=PaginatedResponse[List[StudentWithUser]])
async def get_all_students(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    department: Optional[str] = None,
    batch: Optional[str] = None,
    semester: Optional[int] = None,
    semester_status: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "enrollment_no",
    sort_order: str = "asc",
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get all students with filtering and pagination
    """
    skip = (page - 1) * limit
    students, total = get_students(
        db, skip, limit, search, department, batch, semester, 
        semester_status, category, sort_by, sort_order
    )
    
    return PaginatedResponse(
        status="success",
        data=[StudentWithUser.from_orm(student) for student in students],
        pagination=PaginatedMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit
        )
    )

@router.post("", response_model=DataResponse[StudentResponse])
async def add_student(
    student_data: StudentCreate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Create a new student
    """
    try:
        student = create_student(db, student_data)
        return DataResponse(
            status="success",
            message="Student created successfully",
            data=StudentResponse.from_orm(student)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.post("/sync", response_model=DataResponse[SyncResult])
async def sync_students(
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Sync all users with student role to ensure they have student records
    """
    try:
        result = sync_student_users(db)
        return DataResponse(
            status="success",
            message="Students synced successfully",
            data=SyncResult(**result)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/export-csv", response_class=Response)
async def export_student_csv(
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Export students to a CSV file
    """
    try:
        csv_content = export_students_to_csv(db)
        
        # Return CSV file
        response = Response(content=csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=students.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
        
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.post("/upload-csv", response_model=DataResponse)
async def upload_student_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Import students from a CSV file
    """
    try:
        result = import_students_from_csv(db, file)
        return DataResponse(
            status="success",
            message="Students imported successfully",
            data=result
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/{student_id}", response_model=DataResponse[StudentWithUser])
async def get_student_by_id(
    student_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get a student by ID
    """
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return DataResponse(
        status="success",
        data=StudentWithUser.from_orm(student)
    )

@router.patch("/{student_id}", response_model=DataResponse[StudentResponse])
async def update_student_by_id(
    student_id: str,
    student_data: StudentUpdate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Update a student by ID
    """
    try:
        updated_student = update_student(db, student_id, student_data)
        if not updated_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return DataResponse(
            status="success",
            message="Student updated successfully",
            data=StudentResponse.from_orm(updated_student)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.delete("/{student_id}", response_model=ResponseBase)
async def delete_student_by_id(
    student_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Delete a student by ID
    """
    success = delete_student(db, student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return ResponseBase(
        status="success",
        message="Student deleted successfully"
    )

@router.get("/department/{department_id}", response_model=DataResponse[List[StudentResponse]])
async def get_students_by_department_id(
    department_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get all students for a specific department
    """
    students_list = get_students_by_department(db, department_id)
    
    return DataResponse(
        status="success",
        data=[StudentResponse.from_orm(student) for student in students_list]
    )