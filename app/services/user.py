from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import UploadFile, HTTPException, status

from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate
from app.middleware.error import AppError
import csv
import io
import uuid

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    department_id: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> Tuple[List[User], int]:
    """Get all users with filtering and pagination"""
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    if role and role != "all":
        query = query.join(User.roles).filter(Role.name == role)
    
    if department_id and department_id != "all":
        query = query.filter(User.department_id == department_id)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply sorting
    if sort_order.lower() == "desc":
        query = query.order_by(getattr(User, sort_by).desc())
    else:
        query = query.order_by(getattr(User, sort_by).asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    return query.all(), total

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    # Check if email already exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise AppError(
            message=f"Email {user.email} is already registered",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Get roles or create new ones if they don't exist
    roles = []
    for role_name in user.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            roles.append(role)
    
    # Create the user
    db_user = User(
        name=user.name,
        email=user.email,
        department_id=user.department_id,
        roles=roles,
        selected_role=user.selected_role or user.roles[0] if user.roles else None
    )
    
    # Set password
    db_user.set_password(user.password)
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_user(db: Session, user_id: str, user: UserUpdate) -> Optional[User]:
    """Update an existing user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Update fields if provided
    if user.name is not None:
        db_user.name = user.name
    
    if user.email is not None and user.email != db_user.email:
        # Check if new email already exists
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            raise AppError(
                message=f"Email {user.email} is already registered",
                status_code=status.HTTP_409_CONFLICT
            )
        db_user.email = user.email
    
    if user.department_id is not None:
        db_user.department_id = user.department_id
    
    if user.roles is not None:
        # Get roles
        roles = []
        for role_name in user.roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                roles.append(role)
        
        db_user.roles = roles
        
        # Update selected role if it's no longer in the roles list
        if db_user.selected_role not in user.roles:
            db_user.selected_role = user.roles[0] if user.roles else None
    
    # Commit changes
    db.commit()
    db.refresh(db_user)
    
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    
    return True

def import_users_from_csv(db: Session, file: UploadFile) -> Dict[str, Any]:
    """Import users from a CSV file"""
    if not file.filename.endswith('.csv'):
        raise AppError(
            message="File must be a CSV",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Read CSV file
    content = file.file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    
    # Process rows
    users = []
    errors = []
    for i, row in enumerate(csv_reader):
        try:
            # Validate required fields
            required_fields = ['Name', 'Email']
            for field in required_fields:
                if field not in row or not row[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Map friendly column names to actual data
            name = row.get('Name', '')
            email = row.get('Email', '')
            department_id = row.get('Department', '')
            roles_str = row.get('Roles', 'student')
            roles = [role.strip() for role in roles_str.split(',')]
            selected_role = row.get('Selected Role', roles[0] if roles else 'student')
            
            # Check if user with email already exists
            existing_user = get_user_by_email(db, email)
            if existing_user:
                errors.append(f"Skipping user {name}: Email '{email}' already exists")
                continue
            
            # Create new user with default password
            password = "User@123"  # Default password
            db_user = User(
                name=name,
                email=email,
                department_id=department_id,
                selected_role=selected_role
            )
            db_user.set_password(password)
            
            # Get roles
            user_roles = []
            for role_name in roles:
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    user_roles.append(role)
            
            db_user.roles = user_roles
            
            # Add to database
            db.add(db_user)
            users.append(db_user)
            
        except Exception as e:
            errors.append(f"Error in row {i+1}: {str(e)}")
    
    # Commit all changes
    if users:
        db.commit()
        for user in users:
            db.refresh(user)
    
    return {
        "users": users,
        "errors": errors,
        "summary": f"Successfully imported {len(users)} users. {len(errors)} errors encountered."
    }

def export_users_to_csv(db: Session) -> str:
    """Export users to a CSV file"""
    users = db.query(User).all()
    
    # Prepare CSV data
    output = io.StringIO()
    fieldnames = ['Name', 'Email', 'Department', 'Roles', 'Selected Role', 'Created At']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for user in users:
        department_name = user.department.name if user.department else ''
        roles = ', '.join([role.name for role in user.roles])
        
        writer.writerow({
            'Name': user.name,
            'Email': user.email,
            'Department': department_name,
            'Roles': roles,
            'Selected Role': user.selected_role,
            'Created At': user.created_at.isoformat() if user.created_at else ''
        })
    
    return output.getvalue()

def get_roles(db: Session) -> List[Role]:
    """Get all roles"""
    return db.query(Role).all()

def get_role(db: Session, role_name: str) -> Optional[Role]:
    """Get a role by name"""
    return db.query(Role).filter(Role.name == role_name).first()

def create_role(db: Session, role_name: str, description: str, permissions: List[str]) -> Role:
    """Create a new role"""
    # Check if role already exists
    existing_role = get_role(db, role_name)
    if existing_role:
        raise AppError(
            message=f"Role {role_name} already exists",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Create role
    db_role = Role(
        name=role_name,
        description=description,
        permissions=permissions
    )
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return db_role

def update_role(db: Session, role_name: str, description: Optional[str] = None, 
               permissions: Optional[List[str]] = None) -> Optional[Role]:
    """Update an existing role"""
    db_role = get_role(db, role_name)
    if not db_role:
        return None
    
    # Update fields if provided
    if description is not None:
        db_role.description = description
    
    if permissions is not None:
        db_role.permissions = permissions
    
    db.commit()
    db.refresh(db_role)
    
    return db_role

def delete_role(db: Session, role_name: str) -> bool:
    """Delete a role"""
    db_role = get_role(db, role_name)
    if not db_role:
        return False
    
    db.delete(db_role)
    db.commit()
    
    return True

def assign_roles(db: Session, user_id: str, roles: List[str]) -> Optional[User]:
    """Assign roles to a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Get roles
    user_roles = []
    for role_name in roles:
        role = get_role(db, role_name)
        if role:
            user_roles.append(role)
        else:
            raise AppError(
                message=f"Role {role_name} does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    # Update user roles
    db_user.roles = user_roles
    
    # Update selected role to the first role if current is not in the new roles
    if not db_user.selected_role or db_user.selected_role not in roles:
        db_user.selected_role = roles[0] if roles else None
    
    db.commit()
    db.refresh(db_user)
    
    return db_user