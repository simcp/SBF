#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.database.connection import init_db, test_connection

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_production_app():
    """Create Flask app for production with database initialization."""
    logger.info("Starting Hyperliquid API in production mode")
    
    # Test database connection
    if not test_connection():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    # Initialize database schema
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't fail completely - database might already be initialized
    
    # Create Flask app
    app = create_app()
    logger.info("Flask app created successfully")
    
    return app

# Create the WSGI application
app = create_production_app()

if __name__ == "__main__":
    # For local testing
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))