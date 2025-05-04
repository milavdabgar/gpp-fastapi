from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import UploadFile, status
import csv
import io
import uuid

from app.models.faculty import Faculty, FacultyQualification
from app.models.department import Department
from app.models.user import User
from app.schemas.faculty import FacultyCreate, FacultyUpdate, QualificationCreate
from app.middleware.error import AppError
from app.services.user import get_user_by_email

def get_faculty(db: Session, faculty_id: str) -> Optional[Faculty]:
    """Get a faculty member by ID"""
    return db.query(Faculty).filter(Faculty.id == faculty_id).first()

def get_faculty_by_user_id(db: Session, user_id: str) -> Optional[Faculty]:
    """Get a faculty member by user ID"""
    return db.query(Faculty).filter(Faculty.user_id == user_id).first()

def get_faculty_by_employee_id(db: Session, employee_id: str) -> Optional[Faculty]:
    """Get a faculty member by employee ID"""
    return db.query(Faculty).filter(Faculty.employee_id == employee_id).first()

def get_faculties(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[str] = None
) -> Tuple[List[Faculty], int]:
    """Get all faculty members with filtering and pagination"""
    query = db.query(Faculty)
    
    # Apply filters
    if department_id:
        query = query.filter(Faculty.department_id == department_id)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    return query.all(), total

def create_faculty(db: Session, faculty: FacultyCreate) -> Faculty:
    """Create a new faculty member and associated user if needed"""
    # Check if employee ID already exists
    existing_faculty = get_faculty_by_employee_id(db, faculty.employee_id)
    if existing_faculty:
        raise AppError(
            message=f"Employee ID {faculty.employee_id} already exists",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Check if department exists
    department = db.query(Department).filter(Department.id == faculty.department_id).first()
    if not department:
        raise AppError(
            message=f"Department with ID {faculty.department_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user with email already exists
    user = get_user_by_email(db, faculty.email)
    if not user:
        # Create new user
        user = User(
            name=faculty.name,
            email=faculty.email,
            department_id=faculty.department_id
        )
        
        # Set password if provided, otherwise use default
        if faculty.password:
            user.set_password(faculty.password)
        else:
            user.set_password("123456")  # Default password
        
        # Set faculty role
        from app.services.user import get_role
        faculty_role = get_role(db, "faculty")
        if faculty_role:
            user.roles = [faculty_role]
            user.selected_role = "faculty"
        
        db.add(user)
        db.flush()  # Flush to get the ID without committing
    
    # Create faculty
    db_faculty = Faculty(
        user_id=user.id,
        employee_id=faculty.employee_id,
        department_id=faculty.department_id,
        designation=faculty.designation,
        specializations=faculty.specializations,
        joining_date=faculty.joining_date,
        status=faculty.status,
        experience_years=faculty.experience.years,
        experience_details=faculty.experience.details
    )
    
    db.add(db_faculty)
    db.flush()
    
    # Add qualifications
    for qual in faculty.qualifications:
        db_qualification = FacultyQualification(
            faculty_id=db_faculty.id,
            degree=qual.degree,
            field=qual.field,
            institution=qual.institution,
            year=qual.year
        )
        db.add(db_qualification)
    
    # Commit all changes
    db.commit()
    db.refresh(db_faculty)
    
    return db_faculty

def update_faculty(db: Session, faculty_id: str, faculty_data: FacultyUpdate) -> Optional[Faculty]:
    """Update an existing faculty member"""
    # Get faculty
    db_faculty = get_faculty(db, faculty_id)
    if not db_faculty:
        return None
    
    # Get associated user
    user = db.query(User).filter(User.id == db_faculty.user_id).first()
    if not user and (faculty_data.name or faculty_data.email):
        raise AppError(
            message="Associated user not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Update user info if provided
    if user:
        if faculty_data.name:
            user.name = faculty_data.name
        
        if faculty_data.email and faculty_data.email != user.email:
            # Check if new email already exists
            existing_user = get_user_by_email(db, faculty_data.email)
            if existing_user and existing_user.id != user.id:
                raise AppError(
                    message=f"Email {faculty_data.email} already exists",
                    status_code=status.HTTP_409_CONFLICT
                )
            user.email = faculty_data.email
    
    # Update faculty fields if provided
    if faculty_data.employee_id and faculty_data.employee_id != db_faculty.employee_id:
        # Check if employee ID already exists
        existing = get_faculty_by_employee_id(db, faculty_data.employee_id)
        if existing and existing.id != faculty_id:
            raise AppError(
                message=f"Employee ID {faculty_data.employee_id} already exists",
                status_code=status.HTTP_409_CONFLICT
            )
        db_faculty.employee_id = faculty_data.employee_id
    
    if faculty_data.department_id:
        # Check if department exists
        department = db.query(Department).filter(Department.id == faculty_data.department_id).first()
        if not department:
            raise AppError(
                message=f"Department with ID {faculty_data.department_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        db_faculty.department_id = faculty_data.department_id
        
        # Update user's department as well
        if user:
            user.department_id = faculty_data.department_id
    
    if faculty_data.designation:
        db_faculty.designation = faculty_data.designation
        
    if faculty_data.specializations:
        db_faculty.specializations = faculty_data.specializations
        
    if faculty_data.joining_date:
        db_faculty.joining_date = faculty_data.joining_date
        
    if faculty_data.status:
        db_faculty.status = faculty_data.status
        
    if faculty_data.experience:
        if 'years' in faculty_data.experience:
            db_faculty.experience_years = faculty_data.experience['years']
        if 'details' in faculty_data.experience:
            db_faculty.experience_details = faculty_data.experience['details']
    
    # Update qualifications if provided
    if faculty_data.qualifications:
        # Remove existing qualifications
        db.query(FacultyQualification).filter(
            FacultyQualification.faculty_id == faculty_id
        ).delete()
        
        # Add new qualifications
        for qual_data in faculty_data.qualifications:
            qual = FacultyQualification(
                faculty_id=faculty_id,
                degree=qual_data['degree'],
                field=qual_data.get('field', ''),
                institution=qual_data.get('institution', ''),
                year=qual_data['year']
            )
            db.add(qual)
    
    # Commit changes
    db.commit()
    db.refresh(db_faculty)
    
    return db_faculty

def delete_faculty(db: Session, faculty_id: str) -> bool:
    """Delete a faculty member"""
    faculty = get_faculty(db, faculty_id)
    if not faculty:
        return False
    
    # Get associated user
    user = db.query(User).filter(User.id == faculty.user_id).first()
    
    if user:
        # If user only has faculty role, delete the user
        if len(user.roles) == 1 and any(role.name == "faculty" for role in user.roles):
            db.delete(user)
        else:
            # Otherwise, just remove the faculty role
            faculty_role = next((role for role in user.roles if role.name == "faculty"), None)
            if faculty_role:
                user.roles.remove(faculty_role)
                
                # Update selected role if needed
                if user.selected_role == "faculty" and user.roles:
                    user.selected_role = user.roles[0].name
    
    # Delete faculty
    db.delete(faculty)
    db.commit()
    
    return True

def get_faculties_by_department(db: Session, department_id: str) -> List[Faculty]:
    """Get all faculty members for a specific department"""
    return db.query(Faculty).filter(Faculty.department_id == department_id).all()

def import_faculties_from_csv(db: Session, file: UploadFile) -> Dict[str, Any]:
    """Import faculty members from a CSV file"""
    if not file.filename.endswith('.csv'):
        raise AppError(
            message="File must be a CSV",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Read CSV file
    content = file.file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    
    # Process rows
    results = []
    for i, row in enumerate(csv_reader):
        try:
            # Find department
            department_name = row.get('Department', '')
            department = db.query(Department).filter(Department.name == department_name).first()
            if not department:
                raise ValueError(f"Department '{department_name}' not found")
            
            # Check if user exists with this email
            email = row.get('Email', '')
            user = get_user_by_email(db, email) if email else None
            
            # Create or update user
            if not user and email and row.get('Name'):
                # Create new user
                user = User(
                    name=row['Name'],
                    email=email,
                    department_id=department.id
                )
                user.set_password("Student@123")  # Default password
                
                # Assign faculty role
                faculty_role = db.query(UserRole).filter(UserRole.name == "faculty").first()
                if faculty_role:
                    user.roles = [faculty_role]
                    user.selected_role = "faculty"
                
                db.add(user)
                db.flush()
            
            if not user:
                raise ValueError("User email and name are required for new faculty members")
            
            # Parse qualifications
            qualifications = []
            if row.get('Qualifications'):
                for q_str in row['Qualifications'].split(';'):
                    parts = q_str.split('|')
                    if len(parts) >= 3:
                        qualifications.append({
                            'degree': parts[0].strip(),
                            'field': parts[1].strip() if len(parts) > 1 else '',
                            'institution': parts[2].strip() if len(parts) > 2 else '',
                            'year': int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else datetime.datetime.now().year
                        })
            
            # Create faculty
            faculty = Faculty(
                user_id=user.id,
                department_id=department.id,
                employee_id=row.get('Employee ID', ''),
                designation=row.get('Designation', ''),
                specializations=row.get('Specializations', '').split(';') if row.get('Specializations') else [],
                joining_date=datetime.datetime.strptime(row.get('Joining Date', ''), '%Y-%m-%d') if row.get('Joining Date') else datetime.datetime.now(),
                status=row.get('Status', 'active'),
                experience_years=int(row.get('Experience Years', 0)) if row.get('Experience Years', '').isdigit() else 0,
                experience_details=row.get('Experience Details', '')
            )
            
            db.add(faculty)
            db.flush()
            
            # Add qualifications
            for qual in qualifications:
                db_qualification = FacultyQualification(
                    faculty_id=faculty.id,
                    degree=qual['degree'],
                    field=qual.get('field', ''),
                    institution=qual.get('institution', ''),
                    year=qual.get('year', datetime.datetime.now().year)
                )
                db.add(db_qualification)
            
            results.append({
                "name": user.name,
                "email": user.email,
                "employee_id": faculty.employee_id
            })
            
        except Exception as e:
            results.append({
                "error": str(e),
                "row": row
            })
    
    # Commit changes
    db.commit()
    
    return {"results": results}

def export_faculties_to_csv(db: Session) -> str:
    """Export faculty members to a CSV file"""
    faculties = db.query(Faculty).join(User).join(Department).all()
    
    # Prepare CSV data
    output = io.StringIO()
    fieldnames = [
        'Employee ID', 'Name', 'Email', 'Department', 'Designation', 'Status',
        'Joining Date', 'Specializations', 'Qualifications', 'Experience Years',
        'Experience Details', 'Created At', 'Last Updated'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for faculty in faculties:
        user = faculty.user
        department = faculty.department
        
        # Format qualifications
        qualifications = []
        for q in faculty.qualifications:
            qualifications.append(f"{q.degree}|{q.field}|{q.institution}|{q.year}")
        
        # Write row
        writer.writerow({
            'Employee ID': faculty.employee_id,
            'Name': user.name if user else '',
            'Email': user.email if user else '',
            'Department': department.name if department else '',
            'Designation': faculty.designation,
            'Status': faculty.status,
            'Joining Date': faculty.joining_date.strftime('%Y-%m-%d') if faculty.joining_date else '',
            'Specializations': '; '.join(faculty.specializations) if faculty.specializations else '',
            'Qualifications': '; '.join(qualifications),
            'Experience Years': faculty.experience_years,
            'Experience Details': faculty.experience_details or '',
            'Created At': faculty.created_at.strftime('%Y-%m-%d') if faculty.created_at else '',
            'Last Updated': faculty.updated_at.strftime('%Y-%m-%d') if faculty.updated_at else ''
        })
    
    return output.getvalue()