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
    get_users, export_roles_to_csv
)
from app.middleware.auth import require_admin
from app.services.auth import get_current_active_user
from app.middleware.error import AppError

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

# Role export endpoint - must be defined before path parameter routes
@router.get("/roles/export", response_class=Response)
async def export_roles_endpoint(
    db: Session = Depends(get_db)
):
    """
    Export roles to CSV file
    """
    try:
        # Generate CSV content
        import io
        import csv
        
        # Get all roles
        roles = get_roles(db)
        
        # Create a string buffer and CSV writer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Description', 'Permissions'])
        
        # Write data
        for role in roles:
            permissions = ','.join(role.permissions) if role.permissions else ''
            writer.writerow([role.name, role.description or '', permissions])
        
        # Get the CSV content
        csv_content = output.getvalue()
        
        # Return CSV file
        response = Response(content=csv_content)
        response.headers["Content-Disposition"] = "attachment; filename=roles.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    except Exception as e:
        print(f"Error exporting roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export roles"
        )

# Role management endpoints - all require admin role
@router.get("/roles", response_model=None)
async def get_all_roles(
    db: Session = Depends(get_db)
):
    """
    Get all roles
    """
    try:
        # Get all roles
        roles = get_roles(db)
        
        # Format roles to match Express backend format
        formatted_roles = []
        for i, role in enumerate(roles):
            role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
                "id": str(role.id) if hasattr(role, 'id') and role.id else f"role_{i}",
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions
            }
            
            # Convert to Express format and ensure _id is never null
            formatted_role = {
                "_id": role_dict.get("id") or f"role_{i}",  # Fallback to generated ID if null
                "name": role_dict.get("name"),
                "description": role_dict.get("description"),
                "permissions": role_dict.get("permissions", []),
                "createdAt": role_dict.get("created_at") or "2025-05-04T00:00:00.000Z"
            }
            formatted_roles.append(formatted_role)
        
        # Return in Express format
        return {
            "status": "success",
            "data": {
                "roles": formatted_roles
            }
        }
    except Exception as e:
        print(f"DEBUG - Error getting roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/roles", response_model=None)
async def add_role(
    role_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new role
    """
    try:
        # Extract role data from request
        name = role_data.get('name')
        description = role_data.get('description')
        permissions = role_data.get('permissions', [])
        
        # Validate required fields
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is required"
            )
        
        # Create the role
        role = create_role(db, name, description, permissions)
        
        # Format role to match Express backend format
        role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
            "id": str(role.id) if hasattr(role, 'id') and role.id else f"role_new",
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions
        }
        
        # Convert to Express format
        formatted_role = {
            "_id": role_dict.get("id") or f"role_new",
            "name": role_dict.get("name"),
            "description": role_dict.get("description"),
            "permissions": role_dict.get("permissions", []),
            "createdAt": role_dict.get("created_at") or "2025-05-04T00:00:00.000Z"
        }
        
        # Return in Express format
        return {
            "status": "success",
            "message": "Role created successfully",
            "data": {
                "role": formatted_role
            }
        }
    except Exception as e:
        print(f"DEBUG - Error creating role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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

@router.patch("/roles/{role_id}", response_model=None)
async def update_role_endpoint(
    role_id: str,
    role_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update role by ID or name
    """
    try:
        # Check if role_id is a generated ID (e.g., role_3)
        if role_id.startswith('role_'):
            # Extract the role from our cached roles based on index
            roles = get_roles(db)
            try:
                index = int(role_id.split('_')[1])
                if index < len(roles):
                    role_name = roles[index].name
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role with ID {role_id} not found"
                    )
            except (ValueError, IndexError):
                # If we can't parse the index, try to find by name
                role_name = role_id
        else:
            # Use the ID as the role name directly
            role_name = role_id
        
        # Extract and clean permissions from request data
        permissions = role_data.get('permissions', [])
        
        # If permissions is a string (could happen if it comes with curly braces), clean it
        if isinstance(permissions, str):
            # Remove any curly braces if present
            cleaned_str = permissions.replace('{', '').replace('}', '')
            permissions = [p.strip() for p in cleaned_str.split(',') if p.strip()]
        
        # Update the role
        updated_role = update_role(
            db, role_name, role_data.get('description'), permissions
        )
        
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with name {role_name} not found"
            )
        
        # Format role to match Express backend format
        role_dict = updated_role.to_dict() if hasattr(updated_role, 'to_dict') else {
            "id": str(updated_role.id) if hasattr(updated_role, 'id') and updated_role.id else role_id,
            "name": updated_role.name,
            "description": updated_role.description,
            "permissions": updated_role.permissions
        }
        
        # Convert to Express format
        formatted_role = {
            "_id": role_dict.get("id") or role_id,
            "name": role_dict.get("name"),
            "description": role_dict.get("description"),
            "permissions": role_dict.get("permissions", []),
            "createdAt": role_dict.get("created_at") or "2025-05-04T00:00:00.000Z"
        }
        
        # Return in Express format
        return {
            "status": "success",
            "message": "Role updated successfully",
            "data": {
                "role": formatted_role
            }
        }
    except Exception as e:
        print(f"DEBUG - Error updating role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/roles/{role_id}", response_model=None)
async def delete_role_endpoint(
    role_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete role by ID or name
    """
    try:
        # Check if role_id is a generated ID (e.g., role_6)
        if role_id.startswith('role_'):
            # Extract the role from our cached roles based on index
            roles = get_roles(db)
            try:
                index = int(role_id.split('_')[1])
                if index < len(roles):
                    role_name = roles[index].name
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role with ID {role_id} not found"
                    )
            except (ValueError, IndexError):
                # If we can't parse the index, try to find by name
                role_name = role_id
        else:
            # Use the ID as the role name directly
            role_name = role_id
        
        # Delete the role
        success = delete_role(db, role_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with name {role_name} not found"
            )
        
        # Return in Express format
        return {
            "status": "success",
            "message": "Role deleted successfully"
        }
    except Exception as e:
        print(f"DEBUG - Error deleting role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Role import endpoint
@router.post("/roles/import", response_model=None)
async def import_roles_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import roles from CSV file
    """
    try:
        # Read CSV file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse CSV
        import csv
        import io
        
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        # Process each row
        imported_roles = []
        errors = []
        
        for i, row in enumerate(csv_reader):
            try:
                # Validate required fields
                if not row.get('Name'):
                    errors.append(f"Row {i+1}: Missing required field 'Name'")
                    continue
                
                # Extract data
                name = row.get('Name')
                description = row.get('Description', '')
                permissions_str = row.get('Permissions', '')
                
                # Handle permissions with or without curly braces
                if permissions_str:
                    # Remove any curly braces if present
                    cleaned_str = permissions_str.replace('{', '').replace('}', '')
                    permissions = [p.strip() for p in cleaned_str.split(',') if p.strip()]
                else:
                    permissions = []
                
                # Check if role already exists
                existing_role = get_role(db, name)
                if existing_role:
                    # Update existing role
                    updated_role = update_role(db, name, description, permissions)
                    imported_roles.append(updated_role)
                else:
                    # Create new role
                    new_role = create_role(db, name, description, permissions)
                    imported_roles.append(new_role)
                    
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        # Format response
        return {
            "status": "success",
            "data": {
                "roles": [
                    {
                        "id": f"role_{i}",
                        "name": role.name,
                        "description": role.description,
                        "permissions": role.permissions
                    } for i, role in enumerate(imported_roles)
                ]
            },
            "message": f"Successfully imported {len(imported_roles)} roles. {len(errors)} errors encountered.",
            "errors": errors
        }
    except Exception as e:
        print(f"Error importing roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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