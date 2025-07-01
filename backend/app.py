import logging
import atexit
from flask import Flask
from flask_cors import CORS
from backend.api.routes import api_bp
from backend.database.connection import init_db, test_connection
from backend.config import DEBUG, API_HOST, API_PORT
from backend.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask app."""
    app = Flask(__name__)
    
    # Enable CORS with proper headers for CSP
    CORS(app, origins=["http://localhost:5174", "http://localhost:5173"], 
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy"}, 200
    
    # Root route
    @app.route("/")
    def root():
        return {
            "message": "Hyperliquid Counter-Trading API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "api_docs": "/api",
                "losers": "/api/losers",
                "traders": "/api/traders",
                "opportunities": "/api/opportunities"
            }
        }, 200
    
    return app


def main():
    """Main entry point."""
    # Test database connection
    if not test_connection():
        logger.error("Failed to connect to database. Exiting.")
        return
    
    # Initialize database schema
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Start background data collection scheduler
    try:
        start_scheduler()
        logger.info("Real-time data collection scheduler started (30s intervals)")
        
        # Register cleanup function
        atexit.register(stop_scheduler)
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # Create and run app
    app = create_app()
    logger.info(f"Starting Flask API on {API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)


if __name__ == "__main__":
    main()