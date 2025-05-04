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
@router.get("", response_model=None)
async def get_all_departments(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db)
):
    """
    Get all departments
    """
    try:
        # Get departments with pagination
        departments, total = get_departments(
            db=db, 
            page=page, 
            limit=limit, 
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Debug log
        print(f"DEBUG - Departments: {departments}")
        print(f"DEBUG - Total: {total}")
        
        # Format departments to match Express backend format
        formatted_departments = []
        for dept in departments:
            dept_dict = dept.to_dict()
            # Convert snake_case to camelCase for frontend
            formatted_dept = {
                "_id": dept_dict["id"],
                "name": dept_dict["name"],
                "code": dept_dict["code"],
                "description": dept_dict["description"],
                "establishedDate": dept_dict["established_date"],
                "isActive": dept_dict["is_active"],
                "hodId": dept_dict["hod_id"],
                "createdAt": dept_dict["created_at"],
                "updatedAt": dept_dict["updated_at"]
            }
            formatted_departments.append(formatted_dept)
        
        # Return departments in Express format
        return {
            "status": "success",
            "data": {
                "departments": formatted_departments
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        print(f"DEBUG - Error getting departments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=None)
async def add_department(
    department_data: dict,
    db: Session = Depends(get_db)
):
    """
    Add a new department
    """
    try:
        # Print request data for debugging
        print(f"DEBUG - Department creation request data: {department_data}")
        
        # Convert camelCase to snake_case for backend
        department_create = DepartmentCreate(
            name=department_data.get("name"),
            code=department_data.get("code"),
            description=department_data.get("description"),
            established_date=department_data.get("establishedDate"),
            is_active=department_data.get("isActive", True),
            hod_id=department_data.get("hodId")
        )
        
        # Create department
        department = create_department(db, department_create)
        
        # Format department to match Express backend format
        dept_dict = department.to_dict()
        formatted_dept = {
            "_id": dept_dict["id"],
            "name": dept_dict["name"],
            "code": dept_dict["code"],
            "description": dept_dict["description"],
            "establishedDate": dept_dict["established_date"],
            "isActive": dept_dict["is_active"],
            "hodId": dept_dict["hod_id"],
            "createdAt": dept_dict["created_at"],
            "updatedAt": dept_dict["updated_at"]
        }
        
        # Return in Express format
        return {
            "status": "success",
            "data": {
                "department": formatted_dept
            }
        }
    except Exception as e:
        print(f"DEBUG - Error creating department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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

@router.delete("/{department_id}", response_model=None)
async def delete_department_by_id(
    department_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete department by ID
    """
    try:
        # Print debug info
        print(f"DEBUG - Deleting department with ID: {department_id}")
        
        delete_department(db, department_id)
        
        # Format response to match Express backend format
        return {
            "status": "success",
            "message": "Department deleted successfully"
        }
    except Exception as e:
        print(f"DEBUG - Error deleting department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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

@router.get("/{department_id}", response_model=None)
async def get_department_by_id(
    department_id: str,
    db: Session = Depends(get_db)
):
    """
    Get department by ID
    """
    try:
        department = get_department(db, department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        # Format department to match Express backend format
        dept_dict = department.to_dict()
        formatted_dept = {
            "_id": dept_dict["id"],
            "name": dept_dict["name"],
            "code": dept_dict["code"],
            "description": dept_dict["description"],
            "establishedDate": dept_dict["established_date"],
            "isActive": dept_dict["is_active"],
            "hodId": dept_dict["hod_id"],
            "createdAt": dept_dict["created_at"],
            "updatedAt": dept_dict["updated_at"]
        }
        
        # Return in Express format
        return {
            "status": "success",
            "data": {
                "department": formatted_dept
            }
        }
    except Exception as e:
        print(f"DEBUG - Error getting department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{department_id}", response_model=None)
async def update_department_by_id(
    department_id: str,
    department_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update department by ID
    """
    try:
        # Print request data for debugging
        print(f"DEBUG - Department update request data: {department_data}")
        
        # Convert camelCase to snake_case for backend
        department_update = DepartmentUpdate(
            name=department_data.get("name"),
            code=department_data.get("code"),
            description=department_data.get("description"),
            established_date=department_data.get("establishedDate"),
            is_active=department_data.get("isActive"),
            hod_id=department_data.get("hodId")
        )
        
        # Update department
        department = update_department(db, department_id, department_update)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        # Format department to match Express backend format
        dept_dict = department.to_dict()
        formatted_dept = {
            "_id": dept_dict["id"],
            "name": dept_dict["name"],
            "code": dept_dict["code"],
            "description": dept_dict["description"],
            "establishedDate": dept_dict["established_date"],
            "isActive": dept_dict["is_active"],
            "hodId": dept_dict["hod_id"],
            "createdAt": dept_dict["created_at"],
            "updatedAt": dept_dict["updated_at"]
        }
        
        # Return in Express format
        return {
            "status": "success",
            "data": {
                "department": formatted_dept
            }
        }
    except Exception as e:
        print(f"DEBUG - Error updating department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Old delete endpoint removed