from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import UploadFile, status
import csv
import io
import uuid
import datetime

from app.models.student import (
    Student, StudentGuardian, StudentContact, 
    StudentEducation, StudentSemesterStatus
)
from app.models.department import Department
from app.models.user import User, Role
from app.schemas.student import (
    StudentCreate, StudentUpdate, SemesterStatus, 
    EducationBase, GuardianBase, ContactBase
)
from app.middleware.error import AppError
from app.services.user import get_user_by_email

def get_student(db: Session, student_id: str) -> Optional[Student]:
    """Get a student by ID"""
    return db.query(Student).filter(Student.id == student_id).first()

def get_student_by_user_id(db: Session, user_id: str) -> Optional[Student]:
    """Get a student by user ID"""
    return db.query(Student).filter(Student.user_id == user_id).first()

def get_student_by_enrollment_no(db: Session, enrollment_no: str) -> Optional[Student]:
    """Get a student by enrollment number"""
    return db.query(Student).filter(Student.enrollment_no == enrollment_no).first()

def get_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    batch: Optional[str] = None,
    semester: Optional[int] = None,
    semester_status: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "enrollment_no",
    sort_order: str = "asc"
) -> Tuple[List[Student], int]:
    """Get all students with filtering and pagination"""
    query = db.query(Student)
    
    # Apply filters
    if department_id and department_id != 'all':
        query = query.filter(Student.department_id == department_id)
    
    if batch and batch != 'all':
        query = query.filter(Student.batch == batch)
    
    if semester and not isinstance(semester, str):
        query = query.filter(Student.semester == semester)
    
    if category and category != 'all':
        query = query.filter(Student.category == category)
    
    # Search in student fields
    if search:
        # Find users whose names match the search
        user_ids = db.query(User.id).filter(User.name.ilike(f"%{search}%")).all()
        user_ids = [uid[0] for uid in user_ids]
        
        query = query.filter(or_(
            Student.enrollment_no.ilike(f"%{search}%"),
            Student.first_name.ilike(f"%{search}%"),
            Student.middle_name.ilike(f"%{search}%"),
            Student.last_name.ilike(f"%{search}%"),
            Student.personal_email.ilike(f"%{search}%"),
            Student.institutional_email.ilike(f"%{search}%"),
            Student.user_id.in_(user_ids)
        ))
    
    # Semester status filter
    if semester_status and semester_status != 'all':
        semester_field = f"sem{semester}" if semester else "sem1"
        
        # Join with semester_status
        query = query.join(
            StudentSemesterStatus,
            Student.id == StudentSemesterStatus.student_id
        ).filter(
            getattr(StudentSemesterStatus, semester_field) == semester_status
        )
    
    # Get total count for pagination
    total = query.count()
    
    # Apply sorting
    if sort_by == "userId.name":
        # Special case for sorting by user name
        query = query.join(User, Student.user_id == User.id)
        if sort_order.lower() == "desc":
            query = query.order_by(User.name.desc())
        else:
            query = query.order_by(User.name.asc())
    else:
        # Sort by student field
        if sort_order.lower() == "desc":
            query = query.order_by(getattr(Student, sort_by).desc())
        else:
            query = query.order_by(getattr(Student, sort_by).asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    return query.all(), total

def create_student(db: Session, student: StudentCreate) -> Student:
    """Create a new student and associated user if needed"""
    # Check if enrollment number already exists
    existing_student = get_student_by_enrollment_no(db, student.enrollment_no)
    if existing_student:
        raise AppError(
            message=f"Enrollment number {student.enrollment_no} already exists",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Check if institutional email already exists
    existing_email = db.query(Student).filter(
        Student.institutional_email == student.institutional_email
    ).first()
    if existing_email:
        raise AppError(
            message=f"Institutional email {student.institutional_email} already exists",
            status_code=status.HTTP_409_CONFLICT
        )
    
    # Check if department exists
    department = db.query(Department).filter(Department.id == student.department_id).first()
    if not department:
        raise AppError(
            message=f"Department with ID {student.department_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user with email already exists
    user = get_user_by_email(db, student.email)
    if not user:
        # Create new user
        user = User(
            name=student.name,
            email=student.email,
            department_id=student.department_id
        )
        
        # Set password if provided, otherwise use default
        if student.password:
            user.set_password(student.password)
        else:
            user.set_password("123456")  # Default password
        
        # Set student role
        student_role = db.query(Role).filter(Role.name == "student").first()
        if student_role:
            user.roles = [student_role]
            user.selected_role = "student"
        
        db.add(user)
        db.flush()  # Flush to get the ID without committing
    
    # Create student
    names = student.name.split(' ', 2)
    first_name = names[0] if len(names) > 0 else ""
    middle_name = names[1] if len(names) > 1 else ""
    last_name = names[2] if len(names) > 2 else ""
    
    db_student = Student(
        user_id=user.id,
        department_id=student.department_id,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        full_name=student.name,
        enrollment_no=student.enrollment_no,
        personal_email=student.personal_email,
        institutional_email=student.institutional_email,
        batch=student.batch,
        semester=student.semester,
        status=student.status,
        admission_year=student.admission_year,
        gender=student.gender,
        category=student.category,
        aadhar_no=student.aadhar_no,
        is_complete=student.is_complete,
        term_close=student.term_close,
        is_cancel=student.is_cancel,
        is_pass_all=student.is_pass_all,
        convo_year=student.convo_year,
        shift=student.shift
    )
    
    db.add(db_student)
    db.flush()
    
    # Add guardian information if provided
    if student.guardian:
        guardian = StudentGuardian(
            student_id=db_student.id,
            name=student.guardian.name,
            relation=student.guardian.relation,
            contact=student.guardian.contact,
            occupation=student.guardian.occupation
        )
        db.add(guardian)
    
    # Add contact information if provided
    if student.contact:
        contact = StudentContact(
            student_id=db_student.id,
            mobile=student.contact.mobile,
            email=student.contact.email,
            address=student.contact.address,
            city=student.contact.city,
            state=student.contact.state,
            pincode=student.contact.pincode
        )
        db.add(contact)
    
    # Add education background if provided
    for edu in student.education_background:
        education = StudentEducation(
            student_id=db_student.id,
            degree=edu.degree,
            institution=edu.institution,
            board=edu.board,
            percentage=edu.percentage,
            year_of_passing=edu.year_of_passing
        )
        db.add(education)
    
    # Add semester status if provided
    if student.semester_status:
        semester_status = StudentSemesterStatus(
            student_id=db_student.id,
            sem1=student.semester_status.sem1,
            sem2=student.semester_status.sem2,
            sem3=student.semester_status.sem3,
            sem4=student.semester_status.sem4,
            sem5=student.semester_status.sem5,
            sem6=student.semester_status.sem6,
            sem7=student.semester_status.sem7,
            sem8=student.semester_status.sem8
        )
        db.add(semester_status)
    else:
        # Create default semester status
        semester_status = StudentSemesterStatus(
            student_id=db_student.id
        )
        db.add(semester_status)
    
    # Commit all changes
    db.commit()
    db.refresh(db_student)
    
    return db_student

def delete_student(db: Session, student_id: str) -> bool:
    """Delete a student and optionally the associated user"""
    student = get_student(db, student_id)
    if not student:
        return False
    
    # Get associated user
    user = None
    if student.user_id:
        user = db.query(User).filter(User.id == student.user_id).first()
    
    # Delete related records
    db.query(StudentGuardian).filter(StudentGuardian.student_id == student_id).delete()
    db.query(StudentContact).filter(StudentContact.student_id == student_id).delete()
    db.query(StudentEducation).filter(StudentEducation.student_id == student_id).delete()
    db.query(StudentSemesterStatus).filter(StudentSemesterStatus.student_id == student_id).delete()
    
    # Delete student
    db.delete(student)
    
    # Handle user deletion or role removal
    if user:
        # If user only has student role, delete the user
        if len(user.roles) == 1 and any(role.name == "student" for role in user.roles):
            db.delete(user)
        else:
            # Otherwise, just remove the student role
            student_role = next((role for role in user.roles if role.name == "student"), None)
            if student_role:
                user.roles.remove(student_role)
                
                # Update selected role if needed
                if user.selected_role == "student" and user.roles:
                    user.selected_role = user.roles[0].name
    
    db.commit()
    return True

def get_students_by_department(db: Session, department_id: str) -> List[Student]:
    """Get all students for a specific department"""
    return db.query(Student).filter(Student.department_id == department_id).all()

def sync_student_users(db: Session) -> Dict[str, Any]:
    """Sync all users with student role to ensure they have student records"""
    result = {"created": 0, "existing": 0, "errors": []}
    
    # Get all users with student role
    users = db.query(User).filter(
        User.roles.any(Role.name == "student")
    ).all()
    
    for user in users:
        try:
            # Check if student record already exists
            existing_student = get_student_by_user_id(db, user.id)
            if existing_student:
                result["existing"] += 1
                continue
            
            # Generate enrollment number
            current_year = datetime.datetime.now().year
            last_student = db.query(Student).filter(
                Student.enrollment_no.like(f"{current_year}%")
            ).order_by(Student.enrollment_no.desc()).first()
            
            counter = 1
            if last_student:
                try:
                    counter = int(last_student.enrollment_no[4:]) + 1
                except ValueError:
                    counter = 1
            
            enrollment_no = f"{current_year}{str(counter).zfill(4)}"
            
            # Generate institutional email
            institutional_email = f"{enrollment_no.lower()}@gppalanpur.in"
            
            # Create student record
            student = Student(
                user_id=user.id,
                department_id=user.department_id,
                enrollment_no=enrollment_no,
                institutional_email=institutional_email,
                full_name=user.name,
                admission_year=current_year,
                batch=f"{current_year}-{current_year + 3}",  # 3 year diploma or 4 year degree
                status="active"
            )
            
            # Extract name parts
            names = user.name.split(' ', 2)
            student.first_name = names[0] if len(names) > 0 else ""
            student.middle_name = names[1] if len(names) > 1 else ""
            student.last_name = names[2] if len(names) > 2 else ""
            
            db.add(student)
            
            # Add default semester status
            semester_status = StudentSemesterStatus(
                student_id=student.id
            )
            db.add(semester_status)
            
            db.flush()
            result["created"] += 1
            
        except Exception as e:
            result["errors"].append(f"Error creating student for user {user.name}: {str(e)}")
    
    db.commit()
    return result

def import_students_from_csv(db: Session, file: UploadFile) -> Dict[str, Any]:
    """Import students from a CSV file"""
    if not file.filename.endswith('.csv'):
        raise AppError(
            message="File must be a CSV",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Read CSV file
    content = file.file.read().decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content))
    
    # Process rows
    processed_students = []
    errors = []
    warnings = []
    
    # Group operations by department to minimize DB lookups
    department_cache = {}
    
    for i, row in enumerate(csv_reader):
        try:
            enrollment_no = row.get('enrollment_no') or row.get('Enrollment No') or row.get('MAP_NUMBER')
            if not enrollment_no:
                errors.append({"row": i + 1, "error": "Missing enrollment number"})
                continue
            
            # Handle names
            full_name = row.get('Name') or row.get('name') or row.get('full_name') or row.get('Full Name') or ''
            if not full_name:
                warnings.append({"row": i + 1, "warning": "Missing student name"})
            
            # Generate emails
            institutional_email = row.get('institutional_email') or row.get('Institutional Email') or f"{enrollment_no.lower()}@gppalanpur.in"
            personal_email = row.get('personal_email') or row.get('Personal Email') or row.get('Email') or ''
            
            # Get department
            department_code = row.get('BR_CODE') or row.get('Department Code') or row.get('branch_code')
            department_name = row.get('BR_NAME') or row.get('Department') or row.get('Department Name') or row.get('branch_name')
            
            # Try to find department
            department_id = None
            
            # Try by code first
            if department_code:
                if department_code in department_cache:
                    department_id = department_cache[department_code]
                else:
                    department = db.query(Department).filter(Department.code == department_code).first()
                    if department:
                        department_id = department.id
                        department_cache[department_code] = department_id
            
            # Try by name if code didn't work
            if not department_id and department_name:
                cache_key = f"name:{department_name}"
                if cache_key in department_cache:
                    department_id = department_cache[cache_key]
                else:
                    department = db.query(Department).filter(Department.name == department_name).first()
                    if department:
                        department_id = department.id
                        department_cache[cache_key] = department_id
            
            if not department_id:
                warnings.append({
                    "row": i + 1, 
                    "warning": f"Department not found for: code={department_code}, name={department_name}"
                })
                continue
            
            # Extract name parts
            names = full_name.split(' ', 2)
            first_name = names[0] if len(names) > 0 else ""
            middle_name = names[1] if len(names) > 1 else ""
            last_name = names[2] if len(names) > 2 else ""
            
            # Parse other fields
            try:
                semester = int(row.get('semester') or row.get('Semester') or row.get('sem') or '1')
            except ValueError:
                semester = 1
                warnings.append({"row": i + 1, "warning": "Invalid semester value, using default (1)"})
            
            try:
                admission_year = int(row.get('admission_year') or row.get('Admission Year') or row.get('admissionYear') or '')
            except (ValueError, TypeError):
                # Try to extract from enrollment number
                try:
                    admission_year = int(enrollment_no[:4])
                except ValueError:
                    admission_year = datetime.datetime.now().year
                    warnings.append({"row": i + 1, "warning": "Could not determine admission year, using current year"})
            
            # Determine batch (usually admission year to admission year + program length)
            batch = row.get('batch') or row.get('Batch') or f"{admission_year}-{admission_year + 3}"
            
            # Determine gender
            gender_map = {
                'M': 'M', 'MALE': 'M', 'm': 'M', 'male': 'M',
                'F': 'F', 'FEMALE': 'F', 'f': 'F', 'female': 'F',
                'O': 'O', 'OTHER': 'O', 'o': 'O', 'other': 'O',
                'NB': 'NB', 'NON-BINARY': 'NB', 'non-binary': 'NB', 'nonbinary': 'NB'
            }
            gender_raw = row.get('gender') or row.get('Gender') or ''
            gender = gender_map.get(gender_raw.upper(), 'P')  # Default to 'Prefer not to say'
            
            # Create or update user
            email = personal_email or institutional_email
            
            user = get_user_by_email(db, email)
            if not user:
                # Create new user
                user = User(
                    name=full_name,
                    email=email,
                    department_id=department_id
                )
                user.set_password(enrollment_no)  # Use enrollment number as default password
                
                # Add student role
                student_role = db.query(Role).filter(Role.name == "student").first()
                if student_role:
                    user.roles = [student_role]
                    user.selected_role = "student"
                
                db.add(user)
                db.flush()
            
            # Check if student with this enrollment number already exists
            existing_student = get_student_by_enrollment_no(db, enrollment_no)
            if existing_student:
                # Update existing student
                existing_student.user_id = user.id
                existing_student.department_id = department_id
                existing_student.first_name = first_name
                existing_student.middle_name = middle_name
                existing_student.last_name = last_name
                existing_student.full_name = full_name
                existing_student.personal_email = personal_email
                existing_student.institutional_email = institutional_email
                existing_student.batch = batch
                existing_student.semester = semester
                existing_student.admission_year = admission_year
                existing_student.gender = gender
                
                processed_students.append(existing_student)
            else:
                # Create new student
                student = Student(
                    user_id=user.id,
                    department_id=department_id,
                    enrollment_no=enrollment_no,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    full_name=full_name,
                    personal_email=personal_email,
                    institutional_email=institutional_email,
                    batch=batch,
                    semester=semester,
                    admission_year=admission_year,
                    gender=gender,
                    status="active"
                )
                
                db.add(student)
                db.flush()
                
                # Add default semester status
                semester_status = StudentSemesterStatus(
                    student_id=student.id
                )
                db.add(semester_status)
                
                processed_students.append(student)
            
        except Exception as e:
            errors.append({"row": i + 1, "error": str(e)})
    
    # Commit all changes
    db.commit()
    
    return {
        "results": processed_students,
        "count": len(processed_students),
        "errors": errors if errors else None,
        "warnings": warnings if warnings else None
    }

def export_students_to_csv(db: Session) -> str:
    """Export students to a CSV file"""
    students = db.query(Student).join(
        User, Student.user_id == User.id, isouter=True
    ).join(
        Department, Student.department_id == Department.id, isouter=True
    ).join(
        StudentGuardian, Student.id == StudentGuardian.student_id, isouter=True
    ).join(
        StudentContact, Student.id == StudentContact.student_id, isouter=True
    ).all()
    
    # Prepare CSV data
    output = io.StringIO()
    fieldnames = [
        'Enrollment No', 'Name', 'Email', 'Department', 'Batch', 'Semester',
        'Status', 'Admission Year', 'Mobile', 'Contact Email', 'Address',
        'City', 'State', 'Pincode', 'Guardian Name', 'Guardian Relation',
        'Guardian Contact', 'Guardian Occupation', 'Education Background'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for student in students:
        user = student.user
        department = student.department
        guardian = student.guardian
        contact = student.contact
        
        # Get education background
        education_str = "; ".join([
            f"{edu.degree}|{edu.institution}|{edu.board}|{edu.percentage}|{edu.year_of_passing}"
            for edu in student.education_background
        ]) if student.education_background else ""
        
        # Write row
        writer.writerow({
            'Enrollment No': student.enrollment_no,
            'Name': student.full_name or (user.name if user else ''),
            'Email': user.email if user else student.personal_email or student.institutional_email,
            'Department': department.name if department else '',
            'Batch': student.batch or '',
            'Semester': student.semester or '',
            'Status': student.status or '',
            'Admission Year': student.admission_year or '',
            'Mobile': contact.mobile if contact else '',
            'Contact Email': contact.email if contact else '',
            'Address': contact.address if contact else '',
            'City': contact.city if contact else '',
            'State': contact.state if contact else '',
            'Pincode': contact.pincode if contact else '',
            'Guardian Name': guardian.name if guardian else '',
            'Guardian Relation': guardian.relation if guardian else '',
            'Guardian Contact': guardian.contact if guardian else '',
            'Guardian Occupation': guardian.occupation if guardian else '',
            'Education Background': education_str
        })
    
    return output.getvalue()

def update_student(db: Session, student_id: str, student_data: StudentUpdate) -> Optional[Student]:
    """Update an existing student"""
    # Get student
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    
    # Check if enrollment number is being changed
    if student_data.enrollment_no and student_data.enrollment_no != db_student.enrollment_no:
        # Check if new enrollment number already exists
        existing = get_student_by_enrollment_no(db, student_data.enrollment_no)
        if existing and existing.id != student_id:
            raise AppError(
                message=f"Enrollment number {student_data.enrollment_no} already exists",
                status_code=status.HTTP_409_CONFLICT
            )
        db_student.enrollment_no = student_data.enrollment_no
    
    # Check if institutional email is being changed
    if student_data.institutional_email and student_data.institutional_email != db_student.institutional_email:
        # Check if new institutional email already exists
        existing = db.query(Student).filter(
            Student.institutional_email == student_data.institutional_email
        ).first()
        if existing and existing.id != student_id:
            raise AppError(
                message=f"Institutional email {student_data.institutional_email} already exists",
                status_code=status.HTTP_409_CONFLICT
            )
        db_student.institutional_email = student_data.institutional_email
    
    # Update user if name or email is changing
    if student_data.name or student_data.email:
        user = db.query(User).filter(User.id == db_student.user_id).first()
        if not user:
            raise AppError(
                message="Associated user not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if student_data.name:
            user.name = student_data.name
            
            # Update student name fields
            names = student_data.name.split(' ', 2)
            db_student.first_name = names[0] if len(names) > 0 else ""
            db_student.middle_name = names[1] if len(names) > 1 else ""
            db_student.last_name = names[2] if len(names) > 2 else ""
            db_student.full_name = student_data.name
        
        if student_data.email and student_data.email != user.email:
            # Check if new email already exists
            existing_user = get_user_by_email(db, student_data.email)
            if existing_user and existing_user.id != user.id:
                raise AppError(
                    message=f"Email {student_data.email} already exists",
                    status_code=status.HTTP_409_CONFLICT
                )
            user.email = student_data.email
    
    # Update fields if provided
    if student_data.department_id:
        # Check if department exists
        department = db.query(Department).filter(Department.id == student_data.department_id).first()
        if not department:
            raise AppError(
                message=f"Department with ID {student_data.department_id} not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        db_student.department_id = student_data.department_id
        
        # Update user's department as well
        if db_student.user_id:
            user = db.query(User).filter(User.id == db_student.user_id).first()
            if user:
                user.department_id = student_data.department_id
    
    # Update other simple fields
    if student_data.first_name is not None:
        db_student.first_name = student_data.first_name
    if student_data.middle_name is not None:
        db_student.middle_name = student_data.middle_name
    if student_data.last_name is not None:
        db_student.last_name = student_data.last_name
    if student_data.full_name is not None:
        db_student.full_name = student_data.full_name
    if student_data.personal_email is not None:
        db_student.personal_email = student_data.personal_email
    if student_data.batch is not None:
        db_student.batch = student_data.batch
    if student_data.semester is not None:
        db_student.semester = student_data.semester
    if student_data.status is not None:
        db_student.status = student_data.status
    if student_data.admission_year is not None:
        db_student.admission_year = student_data.admission_year
    if student_data.gender is not None:
        db_student.gender = student_data.gender
    if student_data.category is not None:
        db_student.category = student_data.category
    if student_data.aadhar_no is not None:
        db_student.aadhar_no = student_data.aadhar_no
    if student_data.is_complete is not None:
        db_student.is_complete = student_data.is_complete
    if student_data.term_close is not None:
        db_student.term_close = student_data.term_close
    if student_data.is_cancel is not None:
        db_student.is_cancel = student_data.is_cancel
    if student_data.is_pass_all is not None:
        db_student.is_pass_all = student_data.is_pass_all
    if student_data.convo_year is not None:
        db_student.convo_year = student_data.convo_year
    if student_data.shift is not None:
        db_student.shift = student_data.shift
    
    # Update guardian information if provided
    if student_data.guardian:
        # Check if guardian exists
        guardian = db.query(StudentGuardian).filter(
            StudentGuardian.student_id == student_id
        ).first()
        
        if guardian:
            # Update existing guardian
            if 'name' in student_data.guardian:
                guardian.name = student_data.guardian['name']
            if 'relation' in student_data.guardian:
                guardian.relation = student_data.guardian['relation']
            if 'contact' in student_data.guardian:
                guardian.contact = student_data.guardian['contact']
            if 'occupation' in student_data.guardian:
                guardian.occupation = student_data.guardian['occupation']
        else:
            # Create new guardian
            guardian = StudentGuardian(
                student_id=student_id,
                name=student_data.guardian.get('name', ''),
                relation=student_data.guardian.get('relation', ''),
                contact=student_data.guardian.get('contact', ''),
                occupation=student_data.guardian.get('occupation', '')
            )
            db.add(guardian)
    
    # Update contact information if provided
    if student_data.contact:
        # Check if contact exists
        contact = db.query(StudentContact).filter(
            StudentContact.student_id == student_id
        ).first()
        
        if contact:
            # Update existing contact
            if 'mobile' in student_data.contact:
                contact.mobile = student_data.contact['mobile']
            if 'email' in student_data.contact:
                contact.email = student_data.contact['email']
            if 'address' in student_data.contact:
                contact.address = student_data.contact['address']
            if 'city' in student_data.contact:
                contact.city = student_data.contact['city']
            if 'state' in student_data.contact:
                contact.state = student_data.contact['state']
            if 'pincode' in student_data.contact:
                contact.pincode = student_data.contact['pincode']
        else:
            # Create new contact
            contact = StudentContact(
                student_id=student_id,
                mobile=student_data.contact.get('mobile', ''),
                email=student_data.contact.get('email', ''),
                address=student_data.contact.get('address', ''),
                city=student_data.contact.get('city', ''),
                state=student_data.contact.get('state', ''),
                pincode=student_data.contact.get('pincode', '')
            )
            db.add(contact)
    
    # Update education background if provided
    if student_data.education_background:
        # Remove existing education records
        db.query(StudentEducation).filter(
            StudentEducation.student_id == student_id
        ).delete()
        
        # Add new education records
        for edu_data in student_data.education_background:
            education = StudentEducation(
                student_id=student_id,
                degree=edu_data['degree'],
                institution=edu_data['institution'],
                board=edu_data['board'],
                percentage=edu_data['percentage'],
                year_of_passing=edu_data['year_of_passing']
            )
            db.add(education)
    
    # Update semester status if provided
    if student_data.semester_status:
        # Check if semester status exists
        sem_status = db.query(StudentSemesterStatus).filter(
            StudentSemesterStatus.student_id == student_id
        ).first()
        
        if sem_status:
            # Update existing semester status
            if 'sem1' in student_data.semester_status:
                sem_status.sem1 = student_data.semester_status['sem1']
            if 'sem2' in student_data.semester_status:
                sem_status.sem2 = student_data.semester_status['sem2']
            if 'sem3' in student_data.semester_status:
                sem_status.sem3 = student_data.semester_status['sem3']
            if 'sem4' in student_data.semester_status:
                sem_status.sem4 = student_data.semester_status['sem4']
            if 'sem5' in student_data.semester_status:
                sem_status.sem5 = student_data.semester_status['sem5']
            if 'sem6' in student_data.semester_status:
                sem_status.sem6 = student_data.semester_status['sem6']
            if 'sem7' in student_data.semester_status:
                sem_status.sem7 = student_data.semester_status['sem7']
            if 'sem8' in student_data.semester_status:
                sem_status.sem8 = student_data.semester_status['sem8']
        else:
            # Create new semester status
            sem_status = StudentSemesterStatus(
                student_id=student_id,
                sem1=student_data.semester_status.get('sem1', SemesterStatus.NOT_ATTEMPTED.value),
                sem2=student_data.semester_status.get('sem2', SemesterStatus.NOT_ATTEMPTED.value),
                sem3=student_data.semester_status.get('sem3', SemesterStatus.NOT_ATTEMPTED.value),
                sem4=student_data.semester_status.get('sem4', SemesterStatus.NOT_ATTEMPTED.value),
                sem5=student_data.semester_status.get('sem5', SemesterStatus.NOT_ATTEMPTED.value),
                sem6=student_data.semester_status.get('sem6', SemesterStatus.NOT_ATTEMPTED.value),
                sem7=student_data.semester_status.get('sem7', SemesterStatus.NOT_ATTEMPTED.value),
                sem8=student_data.semester_status.get('sem8', SemesterStatus.NOT_ATTEMPTED.value)
            )
            db.add(sem_status)
    
    # Commit changes
    db.commit()
    db.refresh(db_student)
    
    return db_student