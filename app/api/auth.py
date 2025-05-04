from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas import (
    LoginRequest, RoleSwitchRequest, Token, UserCreate, UserResponse,
    DataResponse, ResponseBase
)
from app.services.auth import create_access_token, get_current_active_user
from app.services.user import get_user_by_email, create_user
from app.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from app.middleware.error import AppError

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/login", response_model=DataResponse[Token])
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token
    """
    # Find user by email
    user = get_user_by_email(db, login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if selected role is valid for this user
    selected_role = login_data.selected_role
    if selected_role and not any(role.name == selected_role for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role selected",
        )
    
    # Update selected role if provided
    if selected_role:
        user.selected_role = selected_role
        db.commit()
    
    # Generate access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": user.id, "selected_role": user.selected_role},
        expires_delta=access_token_expires,
    )
    
    # Remove password from user data
    user_data = user.to_dict()
    
    return DataResponse(
        status="success",
        message="Login successful",
        data=Token(
            access_token=access_token,
            token_type="bearer"
        )
    )

@router.post("/login/token", response_model=DataResponse[Token])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Find user by email/username
    user = get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": user.id, "selected_role": user.selected_role},
        expires_delta=access_token_expires,
    )
    
    return DataResponse(
        status="success",
        message="Login successful",
        data=Token(
            access_token=access_token,
            token_type="bearer"
        )
    )

@router.post("/signup", response_model=DataResponse[UserResponse])
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    try:
        user = create_user(db, user_data)
        
        # If user has student role, create student record
        if "student" in [role.name for role in user.roles]:
            # This would be handled by a student service in a real implementation
            # Here we just acknowledge the creation should happen
            pass
        
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

@router.post("/switch-role", response_model=DataResponse[Token])
async def switch_role(
    role_data: RoleSwitchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Switch to a different role if the user has that role
    """
    # Check if user has the requested role
    if not any(role.name == role_data.role for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role selected",
        )
    
    # Update selected role
    current_user.selected_role = role_data.role
    db.commit()
    db.refresh(current_user)
    
    # If switching to student role, ensure student record exists
    if role_data.role == "student":
        # This would be handled by a student service in a real implementation
        # Here we just acknowledge the check should happen
        pass
    
    # Generate new access token with updated role
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": current_user.id, "selected_role": current_user.selected_role},
        expires_delta=access_token_expires,
    )
    
    return DataResponse(
        status="success",
        message=f"Switched to {role_data.role} role",
        data=Token(
            access_token=access_token,
            token_type="bearer"
        )
    )