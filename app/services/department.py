from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import UploadFile, status
import csv
import io
from datetime import datetime

from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.middleware.error import AppError

def get_department(db: Session, department_id: str) -> Optional[Department]:
    """Get a department by ID"""
    return db.query(Department).filter(Department.id == department_id).first()

def get_department_by_code(db: Session, code: str) -> Optional[Department]:
    """Get a department by code"""
    return db.query(Department).filter(Department.code == code).first()

def get_departments(
    db: Session, 
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> Tuple[List[Department], int]:
    """Get all departments with pagination"""
    query = db.query(Department)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Department.name.ilike(search_term) | 
            Department.code.ilike(search_term) | 
            Department.description.ilike(search_term)
        )
    
    # Get total count for pagination
    total = query.count()
    
    # Apply sorting
    if sort_order.lower() == "desc":
        query = query.order_by(getattr(Department, sort_by).desc())
    else:
        query = query.order_by(getattr(Department, sort_by).asc())
    
    # Calculate skip from page and limit
    skip = (page - 1) * limit
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    return query.all(), total

def create_department(db: Session, department: DepartmentCreate) -> Department:
    """Create a new department"""
    # Check if department code already exists
    existing_department = get_department_by_code(db, department.code)
    if existing_department:
        raise AppError(
            message=f"Department code {department.code} already exists",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Check if HOD user exists if provided
    if department.hod_id:
        hod = db.query(User).filter(User.id == department.hod_id).first()
        if not hod:
            raise AppError(
                message=f"User with ID {department.hod_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has HOD role
        if 'hod' not in [role.name for role in hod.roles]:
            raise AppError(
                message=f"User must have HOD role to be assigned as department head",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # Create the department
    db_department = Department(
        name=department.name,
        code=department.code,
        description=department.description,
        established_date=department.established_date,
        is_active=department.is_active,
        hod_id=department.hod_id
    )
    
    # Add to database
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    
    return db_department

def update_department(db: Session, department_id: str, department: DepartmentUpdate) -> Optional[Department]:
    """Update an existing department"""
    db_department = get_department(db, department_id)
    if not db_department:
        return None
    
    # Update fields if provided
    if department.name is not None:
        db_department.name = department.name
    
    if department.code is not None and department.code != db_department.code:
        # Check if new code already exists
        existing_department = get_department_by_code(db, department.code)
        if existing_department and existing_department.id != department_id:
            raise AppError(
                message=f"Department code {department.code} already exists",
                status_code=status.HTTP_409_CONFLICT
            )
        db_department.code = department.code
    
    if department.description is not None:
        db_department.description = department.description
    
    if department.established_date is not None:
        db_department.established_date = department.established_date
    
    if department.is_active is not None:
        db_department.is_active = department.is_active
    
    # Handle HOD assignment
    if department.hod_id is not None:
        if department.hod_id == "":
            # If empty string, set to None (remove HOD)
            db_department.hod_id = None
        else:
            # Check if HOD user exists
            hod = db.query(User).filter(User.id == department.hod_id).first()
            if not hod:
                raise AppError(
                    message=f"User with ID {department.hod_id} not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has HOD role
            if 'hod' not in [role.name for role in hod.roles]:
                raise AppError(
                    message=f"User must have HOD role to be assigned as department head",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            db_department.hod_id = department.hod_id
    
    # Commit changes
    db.commit()
    db.refresh(db_department)
    
    return db_department

def delete_department(db: Session, department_id: str) -> bool:
    """Delete a department"""
    db_department = get_department(db, department_id)
    if not db_department:
        return False
    
    db.delete(db_department)
    db.commit()
    
    return True

def get_department_stats(db: Session) -> Dict[str, int]:
    """Get department statistics"""
    # Count active and inactive departments
    stats = db.query(
        func.sum(case([(Department.is_active == True, 1)], else_=0)).label('active_count'),
        func.sum(case([(Department.is_active == False, 1)], else_=0)).label('inactive_count')
    ).first()
    
    return {
        "active_count": stats.active_count or 0,
        "inactive_count": stats.inactive_count or 0
    }

def import_departments_from_csv(db: Session, file: UploadFile) -> Dict[str, Any]:
    """Import departments from a CSV file"""
    if not file.filename.endswith('.csv'):
        raise AppError(
            message="File must be a CSV",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Read CSV file
    content = file.file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    
    # Process rows
    successful = []
    failed = []
    for i, row in enumerate(csv_reader):
        try:
            # Validate required fields
            required_fields = ['Name', 'Code', 'Description', 'EstablishedDate']
            for field in required_fields:
                if field not in row or not row[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Parse data
            name = row['Name'].strip()
            code = row['Code'].strip().upper()
            description = row['Description'].strip()
            established_date_str = row['EstablishedDate'].strip()
            
            # Parse date
            try:
                established_date = datetime.strptime(established_date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    established_date = datetime.strptime(established_date_str, '%d/%m/%Y')
                except ValueError:
                    try:
                        established_date = datetime.strptime(established_date_str, '%m/%d/%Y')
                    except ValueError:
                        raise ValueError(f"Invalid date format: {established_date_str}. Use YYYY-MM-DD.")
            
            # Parse boolean
            is_active_str = row.get('IsActive', 'true').strip().lower()
            is_active = is_active_str in ['true', '1', 'yes', 'y']
            
            # Try to update existing department or create new one
            existing_department = get_department_by_code(db, code)
            if existing_department:
                # Update existing department
                existing_department.name = name
                existing_department.description = description
                existing_department.established_date = established_date
                existing_department.is_active = is_active
                db.commit()
                db.refresh(existing_department)
                successful.append(existing_department)
            else:
                # Create new department
                new_department = Department(
                    name=name,
                    code=code,
                    description=description,
                    established_date=established_date,
                    is_active=is_active
                )
                db.add(new_department)
                db.commit()
                db.refresh(new_department)
                successful.append(new_department)
            
        except Exception as e:
            failed.append({
                "row": i + 1,
                "data": row,
                "error": str(e)
            })
    
    return {
        "successful": successful,
        "failed": failed,
        "message": f"{len(successful)} departments processed ({len(failed)} failed)"
    }

def export_departments_to_csv(db: Session) -> str:
    """Export departments to a CSV file"""
    departments = db.query(Department).all()
    
    # Prepare CSV data
    output = io.StringIO()
    fieldnames = ['Name', 'Code', 'Description', 'EstablishedDate', 'IsActive']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for department in departments:
        established_date = department.established_date.strftime('%Y-%m-%d') if department.established_date else ''
        
        writer.writerow({
            'Name': department.name,
            'Code': department.code,
            'Description': department.description,
            'EstablishedDate': established_date,
            'IsActive': 'Yes' if department.is_active else 'No'
        })
    
    return output.getvalue()