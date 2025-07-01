import logging
from flask import Flask
from flask_cors import CORS
from backend.api.routes import api_bp
from backend.database.connection import init_db, test_connection
from backend.config import DEBUG, API_HOST, API_PORT

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask app."""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy"}, 200
    
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
    
    # Create and run app
    app = create_app()
    logger.info(f"Starting Flask API on {API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)


if __name__ == "__main__":
    main()