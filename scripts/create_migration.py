#!/usr/bin/env python3
import os
import subprocess
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def create_initial_migration():
    """
    Create the initial database migration
    """
    try:
        # Ensure alembic is installed
        logger.info("Checking if alembic is installed...")
        try:
            import alembic
        except ImportError:
            logger.error("Alembic is not installed. Please run: pip install alembic")
            sys.exit(1)
        
        # Check if alembic directory exists
        if not os.path.exists('alembic'):
            logger.info("Initializing alembic...")
            subprocess.run(['alembic', 'init', 'alembic'], check=True)
            logger.info("Alembic initialized")
        
        # Create the initial migration
        logger.info("Creating initial migration...")
        subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Initial migration'], check=True)
        logger.info("Initial migration created")
        
        # Run the migration
        logger.info("Running migration...")
        subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        logger.info("Migration completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_initial_migration()