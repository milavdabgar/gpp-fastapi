#!/usr/bin/env python3
"""
Seed the database with initial data for testing or development
"""
import logging
import sys
import os
import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base, SessionLocal
from app.models.user import User, Role
from app.models.department import Department
from app.services.init import initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def seed_departments(db):
    """Seed departments table with initial data"""
    departments = [
        {
            "name": "Computer Engineering",
            "code": "06",
            "description": "Department of Computer Engineering",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        },
        {
            "name": "Civil Engineering",
            "code": "09",
            "description": "Department of Civil Engineering",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        },
        {
            "name": "Electrical Engineering",
            "code": "11",
            "description": "Department of Electrical Engineering",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        },
        {
            "name": "Information Technology",
            "code": "17",
            "description": "Department of Information Technology",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        },
        {
            "name": "Mechanical Engineering",
            "code": "19",
            "description": "Department of Mechanical Engineering",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        },
        {
            "name": "CTSD",
            "code": "83",
            "description": "Department of Craft and Technology Skill Development",
            "established_date": datetime.datetime(2000, 1, 1),
            "is_active": True
        }
    ]
    
    for dept_data in departments:
        # Check if department already exists
        existing = db.query(Department).filter(Department.code == dept_data["code"]).first()
        if existing:
            logger.info(f"Department {dept_data['name']} already exists, skipping")
            continue
        
        # Create department
        department = Department(**dept_data)
        db.add(department)
        logger.info(f"Added department: {dept_data['name']}")
    
    db.commit()
    logger.info("Departments seeded successfully")

def seed_test_users(db):
    """Seed test users for development"""
    # Get roles
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    student_role = db.query(Role).filter(Role.name == "student").first()
    faculty_role = db.query(Role).filter(Role.name == "faculty").first()
    hod_role = db.query(Role).filter(Role.name == "hod").first()
    jury_role = db.query(Role).filter(Role.name == "jury").first()
    
    # Get computer engineering department
    ce_dept = db.query(Department).filter(Department.code == "06").first()
    
    # Test user data
    test_users = [
        {
            "name": "John Doe",
            "email": "john.doe@gppalanpur.in",
            "password": "Test@123",
            "department_id": ce_dept.id if ce_dept else None,
            "roles": [student_role, jury_role],
            "selected_role": "student"
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@gppalanpur.in",
            "password": "Test@123",
            "department_id": ce_dept.id if ce_dept else None,
            "roles": [faculty_role],
            "selected_role": "faculty"
        },
        {
            "name": "Robert Johnson",
            "email": "robert.johnson@gppalanpur.in",
            "password": "Test@123",
            "department_id": ce_dept.id if ce_dept else None,
            "roles": [hod_role, faculty_role],
            "selected_role": "hod"
        },
        {
            "name": "Emily Davis",
            "email": "emily.davis@gppalanpur.in",
            "password": "Test@123",
            "department_id": ce_dept.id if ce_dept else None,
            "roles": [jury_role],
            "selected_role": "jury"
        }
    ]
    
    for user_data in test_users:
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            logger.info(f"User {user_data['email']} already exists, skipping")
            continue
        
        # Create user
        user = User(
            name=user_data["name"],
            email=user_data["email"],
            department_id=user_data["department_id"],
            roles=user_data["roles"],
            selected_role=user_data["selected_role"]
        )
        user.set_password(user_data["password"])
        db.add(user)
        logger.info(f"Added user: {user_data['email']}")
    
    db.commit()
    logger.info("Test users seeded successfully")

def main():
    """Main function to seed the database"""
    logger.info("Starting database seeding")
    
    # Create database session
    db = SessionLocal()
    try:
        # Initialize database with default roles and admin user
        initialize_database(db)
        
        # Seed departments
        seed_departments(db)
        
        # Seed test users
        seed_test_users(db)
        
        logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()