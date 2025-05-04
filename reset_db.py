#!/usr/bin/env python
"""
Script to reset the database by dropping and recreating all tables.
"""
import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import DATABASE_URL
from app.database import Base
from app.models import user, department, result, project  # Import all models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_database():
    """Drop and recreate all tables in the database."""
    try:
        # Create engine with more permissive options
        engine = create_engine(DATABASE_URL)
        
        # Connect to the database
        with engine.connect() as conn:
            # Test connection
            logger.info("Testing database connection...")
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Connection successful: {result.scalar()}")
            
            # Use raw SQL to drop schema with cascade
            logger.info("Dropping all tables with CASCADE...")
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
            logger.info("Schema reset successfully.")
            
            # Create all tables
            logger.info("Creating all tables...")
            Base.metadata.create_all(engine)
            logger.info("All tables created successfully.")
            
        logger.info("Database reset completed successfully.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
