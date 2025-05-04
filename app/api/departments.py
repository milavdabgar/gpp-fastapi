from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentStats,
    DataResponse, ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.department import (
    get_department, get_departments, create_department, update_department,
    delete_department, get_department_stats, import_departments_from_csv,
    export_departments_to_csv
)
from app.middleware.auth import require_admin_or_principal
from app.middleware.error import AppError

router = APIRouter(
    prefix="/departments",
    tags=["departments"]
)

# All routes require admin or principal role
@router.get("", response_model=PaginatedResponse[List[DepartmentResponse]])
async def get_all_departments(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get all departments with pagination
    """
    skip = (page - 1) * limit
    departments, total = get_departments(db, skip, limit, sort_by, sort_order)
    
    return PaginatedResponse(
        status="success",
        data=[DepartmentResponse.from_orm(dept) for dept in departments],
        pagination=PaginatedMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit
        )
    )

@router.post("", response_model=DataResponse[DepartmentResponse])
async def add_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Create a new department
    """
    try:
        department = create_department(db, department_data)
        return DataResponse(
            status="success",
            message="Department created successfully",
            data=DepartmentResponse.from_orm(department)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/stats", response_model=DataResponse[DepartmentStats])
async def get_departments_stats(
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get department statistics
    """
    stats = get_department_stats(db)
    return DataResponse(
        status="success",
        data=DepartmentStats(**stats)
    )

@router.post("/import", response_model=DataResponse)
async def import_departments(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Import departments from CSV file
    """
    try:
        result = import_departments_from_csv(db, file)
        return DataResponse(
            status="success",
            message=result["message"],
            data=result
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/export", response_class=Response)
async def export_departments(
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Export departments to CSV file
    """
    try:
        csv_content = export_departments_to_csv(db)
        
        # Return CSV file
        response = Response(content=csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=departments.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
        
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/{department_id}", response_model=DataResponse[DepartmentResponse])
async def get_department_by_id(
    department_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Get department by ID
    """
    department = get_department(db, department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return DataResponse(
        status="success",
        data=DepartmentResponse.from_orm(department)
    )

@router.patch("/{department_id}", response_model=DataResponse[DepartmentResponse])
async def update_department_by_id(
    department_id: str,
    department_data: DepartmentUpdate,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Update department by ID
    """
    try:
        updated_department = update_department(db, department_id, department_data)
        if not updated_department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        return DataResponse(
            status="success",
            message="Department updated successfully",
            data=DepartmentResponse.from_orm(updated_department)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.delete("/{department_id}", response_model=ResponseBase)
async def delete_department_by_id(
    department_id: str,
    current_user: User = Depends(require_admin_or_principal),
    db: Session = Depends(get_db)
):
    """
    Delete department by ID
    """
    success = delete_department(db, department_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return ResponseBase(
        status="success",
        message="Department deleted successfully"
    )