#!/usr/bin/env python3
"""
Initialize production database on Render
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from backend.database.connection import init_db, test_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize production database schema."""
    logger.info("Initializing production database...")
    
    # Check database connection
    if not test_connection():
        logger.error("Failed to connect to database")
        return False
    
    logger.info("Database connection successful")
    
    # Initialize schema
    try:
        init_db()
        logger.info("Database schema initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)