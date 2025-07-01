import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
ENV = os.getenv("FLASK_ENV", "development")
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/hyperliquid_tracker")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))

# Hyperliquid Configuration
HYPERLIQUID_ENV = os.getenv("HYPERLIQUID_ENV", "mainnet")
HYPERLIQUID_API_URL = os.getenv("HYPERLIQUID_API_URL", "https://api.hyperliquid.xyz")

# Data Collection
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", 30))
MAX_TRADERS_TO_TRACK = int(os.getenv("MAX_TRADERS_TO_TRACK", 500))
POSITION_CHECK_INTERVAL = int(os.getenv("POSITION_CHECK_INTERVAL", 10))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# Create logs directory if it doesn't exist
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / LOG_FILE),
        logging.StreamHandler()
    ]
)