import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/hyperliquid_tracker")

# Add SSL parameters for Render.com PostgreSQL
if 'render.com' in DATABASE_URL:
    if '?' in DATABASE_URL:
        DATABASE_URL += '&sslmode=require'
    else:
        DATABASE_URL += '?sslmode=require'

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable pooling for now, can optimize later
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with schema."""
    with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as f:
        schema_sql = f.read()
    
    with engine.begin() as conn:
        # Execute schema SQL
        for statement in schema_sql.split(";"):
            if statement.strip():
                conn.execute(text(statement))
    
    print("Database initialized successfully!")


def test_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False