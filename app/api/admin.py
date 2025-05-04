from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import (
    RoleCreate, RoleUpdate, RoleResponse, DataResponse,
    ResponseBase, PaginatedResponse, PaginatedMeta
)
from app.services.user import (
    get_roles, get_role, create_role, update_role, delete_role, assign_roles,
    get_users
)
from app.middleware.auth import require_admin
from app.middleware.error import AppError

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

# Role management endpoints - all require admin role
@router.get("/roles", response_model=DataResponse[List[RoleResponse]])
async def get_all_roles(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all roles (admin only)
    """
    roles = get_roles(db)
    return DataResponse(
        status="success",
        data=[RoleResponse.from_orm(role) for role in roles]
    )

@router.post("/roles", response_model=DataResponse[RoleResponse])
async def add_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new role (admin only)
    """
    try:
        role = create_role(db, role_data.name, role_data.description, role_data.permissions)
        return DataResponse(
            status="success",
            message="Role created successfully",
            data=RoleResponse.from_orm(role)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.get("/roles/{role_name}", response_model=DataResponse[RoleResponse])
async def get_role_by_name(
    role_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get role by name (admin only)
    """
    role = get_role(db, role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return DataResponse(
        status="success",
        data=RoleResponse.from_orm(role)
    )

@router.patch("/roles/{role_name}", response_model=DataResponse[RoleResponse])
async def update_role_by_name(
    role_name: str,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update role by name (admin only)
    """
    try:
        updated_role = update_role(
            db, role_name, role_data.description, role_data.permissions
        )
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return DataResponse(
            status="success",
            message="Role updated successfully",
            data=RoleResponse.from_orm(updated_role)
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

@router.delete("/roles/{role_name}", response_model=ResponseBase)
async def delete_role_by_name(
    role_name: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete role by name (admin only)
    """
    success = delete_role(db, role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return ResponseBase(
        status="success",
        message="Role deleted successfully"
    )

# User management endpoints
@router.get("/users", response_model=None)
async def get_admin_users(
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
    users, total = get_users(db, skip, limit, search, role, department, sort_by, sort_order)
    
    # Format response to match React frontend expectations
    return {
        "status": "success",
        "message": "Users retrieved successfully",
        "data": {
            "users": [user.to_dict() for user in users]
        },
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    }

# User role assignment
@router.post("/users/{user_id}/roles", response_model=DataResponse[None])
async def assign_user_roles(
    user_id: str,
    roles: List[str],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Assign roles to a user (admin only)
    """
    try:
        updated_user = assign_roles(db, user_id, roles)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return DataResponse(
            status="success",
            message="Roles assigned successfully",
            data={
                "user": updated_user.to_dict(),
                "roles": [role.name for role in updated_user.roles]
            }
        )
    except AppError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )