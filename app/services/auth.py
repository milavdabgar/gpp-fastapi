from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User
from app.services.user import get_user
from app.middleware.error import AppError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/token")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Decode JWT token and return current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("id")
        selected_role: str = payload.get("selected_role")
        
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, user_id)
    if user is None:
        raise credentials_exception
    
    # Ensure selected role is in the user's roles
    if selected_role and selected_role not in [role.name for role in user.roles]:
        user.selected_role = user.roles[0].name if user.roles else None
    else:
        user.selected_role = selected_role
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if user is active
    """
    return current_user

def check_role(user: User, required_roles: list[str]) -> bool:
    """
    Check if user has one of the required roles
    """
    if not user.selected_role:
        return False
    
    return user.selected_role in required_roles