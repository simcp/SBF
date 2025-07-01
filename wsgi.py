#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_production_app():
    """Create Flask app for production with database initialization."""
    try:
        from backend.app import create_app
        from backend.database.connection import init_db, test_connection
        
        logger.info("Starting Hyperliquid API in production mode")
        
        # Check if DATABASE_URL is configured
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("No DATABASE_URL configured - running without database")
        else:
            logger.info(f"Database URL configured: {database_url[:50]}...")
            
            # Test database connection
            try:
                if test_connection():
                    logger.info("Database connection successful")
                    # Initialize database schema
                    try:
                        init_db()
                        logger.info("Database initialized successfully")
                    except Exception as e:
                        logger.warning(f"Database initialization failed: {e}")
                        # Don't fail completely - database might already be initialized
                else:
                    logger.warning("Database connection failed - continuing without database")
            except Exception as e:
                logger.warning(f"Database setup error: {e} - continuing without database")
        
        # Create Flask app
        app = create_app()
        logger.info("Flask app created successfully")
        
        return app
        
    except ImportError as e:
        logger.error(f"Failed to import backend modules: {e}")
        # Create a minimal Flask app for error reporting
        try:
            from flask import Flask
            app = Flask(__name__)
            
            @app.route("/")
            def error():
                return {"error": f"Backend import failed: {str(e)}", "status": "error"}, 500
            
            @app.route("/health")
            def health():
                return {"status": "error", "message": f"Import error: {str(e)}"}, 500
                
            return app
            
        except ImportError:
            logger.error("Even Flask is not available - creating basic WSGI app")
            # If even Flask isn't available, create a basic WSGI app
            def basic_app(environ, start_response):
                status = '500 Internal Server Error'
                headers = [('Content-type', 'application/json')]
                start_response(status, headers)
                return [f'{{"error": "Critical import error: {str(e)}", "status": "error"}}'.encode('utf-8')]
            return basic_app

# Create the WSGI application
try:
    app = create_production_app()
    logger.info("WSGI application created successfully")
except Exception as e:
    logger.error(f"Failed to create WSGI application: {e}")
    # Create a minimal error app
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route("/")
        def error_page():
            return f"Application startup failed: {str(e)}", 500
        
        @app.route("/health")
        def health():
            return {"status": "error", "message": str(e)}, 500
    except:
        # Last resort - basic WSGI app
        def app(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/plain')]
            start_response(status, headers)
            return [f"Critical startup error: {str(e)}".encode('utf-8')]

if __name__ == "__main__":
    # For local testing
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))