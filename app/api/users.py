from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, DataResponse,
    ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.user import (
    get_user, get_users, create_user, update_user,
    delete_user, import_users_from_csv, export_users_to_csv
)
from app.middleware.auth import get_authenticated_user, require_admin
from app.middleware.error import AppError

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: User = Depends(get_authenticated_user)
):
    """
    Get current authenticated user information
    """
    # Format response to match React frontend expectations
    user_data = current_user.to_dict()
    
    # Ensure selectedRole is set correctly (camelCase for React)
    if not user_data.get("selectedRole") and user_data.get("roles"):
        user_data["selectedRole"] = user_data.get("selected_role") or user_data["roles"][0]
    
    return {
        "status": "success",
        "message": "User profile retrieved successfully",
        "data": {
            "user": user_data
        }
    }

@router.patch("/updateMe", response_model=DataResponse[UserResponse])
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user information
    """
    # Filter out fields that are not allowed to be updated
    allowed_fields = ["name", "email", "department_id"]
    filtered_data = UserUpdate(
        **{k: v for k, v in user_data.dict(exclude_unset=True).items() if k in allowed_fields}
    )
    
    try:
        updated_user = update_user(db, current_user.id, filtered_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return DataResponse(
            status="success",
            message="User updated successfully",
            data=UserResponse.from_orm(updated_user)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

# Admin routes below - all require admin role
@router.get("", response_model=PaginatedResponse[List[UserResponse]])
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    role: Optional[str] = None,
    department: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users with filtering and pagination (admin only)
    """
    skip = (page - 1) * limit
    users, total = get_users(
        db, skip, limit, search, role, department, sort_by, sort_order
    )
    
    return PaginatedResponse(
        status="success",
        data=[UserResponse.from_orm(user) for user in users],
        pagination=PaginatedMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit
        )
    )

@router.post("", response_model=DataResponse[UserResponse])
async def add_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only)
    """
    try:
        user = create_user(db, user_data)
        return DataResponse(
            status="success",
            message="User created successfully",
            data=UserResponse.from_orm(user)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/{user_id}", response_model=DataResponse[UserResponse])
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return DataResponse(
        status="success",
        data=UserResponse.from_orm(user)
    )

@router.patch("/{user_id}", response_model=DataResponse[UserResponse])
async def update_user_by_id(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user by ID (admin only)
    """
    try:
        updated_user = update_user(db, user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return DataResponse(
            status="success",
            message="User updated successfully",
            data=UserResponse.from_orm(updated_user)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.delete("/{user_id}", response_model=ResponseBase)
async def delete_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user by ID (admin only)
    """
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return ResponseBase(
        status="success",
        message="User deleted successfully"
    )

@router.post("/import", response_model=DataResponse)
async def import_users(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Import users from CSV file (admin only)
    """
    try:
        result = import_users_from_csv(db, file)
        return DataResponse(
            status="success",
            message=f"Successfully imported users. {len(result['errors'])} errors encountered.",
            data=result
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/export", response_class=Response)
async def export_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Export users to CSV file (admin only)
    """
    try:
        csv_content = export_users_to_csv(db)
        
        # Return CSV file
        response = Response(content=csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=users.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
        
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )