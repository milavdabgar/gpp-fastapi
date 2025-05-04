import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User, Role
from app.middleware.error import AppError

logger = logging.getLogger(__name__)

def create_default_roles(db: Session) -> None:
    """
    Create default roles in the database if they don't exist
    """
    try:
        # Define default roles and their permissions
        default_roles = [
            {
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": ["create", "read", "update", "delete"]
            },
            {
                "name": "student",
                "description": "Student user with limited access",
                "permissions": ["read", "create"]
            },
            {
                "name": "faculty",
                "description": "Faculty member with department-level access",
                "permissions": ["read", "create", "update"]
            },
            {
                "name": "hod",
                "description": "Head of Department with department management access",
                "permissions": ["read", "create", "update"]
            },
            {
                "name": "principal",
                "description": "Principal with institution-level access",
                "permissions": ["read", "create", "update"]
            },
            {
                "name": "jury",
                "description": "Jury member for project evaluation",
                "permissions": ["read", "update"]
            }
        ]
        
        # Check and create roles
        for role_data in default_roles:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                logger.info(f"Creating default role: {role_data['name']}")
                # Convert permissions list to a comma-separated string
                permissions_str = ','.join(role_data["permissions"])
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=permissions_str
                )
                db.add(role)
        
        db.commit()
        logger.info("Default roles created successfully")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating default roles: {str(e)}")
        raise AppError(message=f"Error creating default roles: {str(e)}")

def create_admin_user(db: Session) -> None:
    """
    Create an admin user if no admin exists
    """
    try:
        # Check if admin user exists
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            logger.error("Admin role not found, please create roles first")
            raise AppError(message="Admin role not found, please create roles first")
        
        # Check if any admin user exists
        admin_user = db.query(User).filter(
            User.roles.any(Role.name == "admin")
        ).first()
        
        if not admin_user:
            # Create admin user
            logger.info("Creating default admin user")
            admin_user = User(
                name="Admin",
                email="admin@gppalanpur.in",
                selected_role="admin",
                roles=[admin_role]
            )
            admin_user.set_password("Admin@123")
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created successfully")
        else:
            logger.info("Admin user already exists, skipping creation")
            
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise AppError(message=f"Error creating admin user: {str(e)}")

def initialize_database(db: Session) -> None:
    """
    Initialize the database with default roles and admin user
    """
    try:
        # Create default roles
        create_default_roles(db)
        
        # Create admin user
        create_admin_user(db)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise AppError(message=f"Error during database initialization: {str(e)}")