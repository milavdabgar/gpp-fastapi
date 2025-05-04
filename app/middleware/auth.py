from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.services.auth import get_current_active_user, check_role

class RoleChecker:
    """
    Dependency class to check if user has one of the required roles
    """
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    def __call__(self, 
                 current_user: User = Depends(get_current_active_user),
                 db: Session = Depends(get_db)):
        
        if not check_role(current_user, self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.selected_role} not authorized to perform this action. Required roles: {self.required_roles}"
            )
        
        return current_user

# Dependencies for role-based access control
require_admin = RoleChecker(["admin"])
require_faculty = RoleChecker(["faculty", "admin"])
require_student = RoleChecker(["student", "admin"])
require_hod = RoleChecker(["hod", "admin"])
require_principal = RoleChecker(["principal", "admin"])
require_jury = RoleChecker(["jury", "admin"])
require_admin_or_principal = RoleChecker(["admin", "principal"])
require_admin_or_hod = RoleChecker(["admin", "hod"])

# Common auth dependency for all authenticated routes
def get_authenticated_user(current_user: User = Depends(get_current_active_user)):
    return current_user