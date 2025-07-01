#!/usr/bin/env python3
"""Script to set up the database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import init_db, test_connection


def main():
    """Set up the database."""
    print("Testing database connection...")
    if not test_connection():
        print("Failed to connect to database!")
        print("Please ensure PostgreSQL is running and the database exists.")
        print("You may need to create the database manually:")
        print("  createdb hyperliquid_tracker")
        return 1
    
    print("Initializing database schema...")
    try:
        init_db()
        print("Database setup complete!")
        return 0
    except Exception as e:
        print(f"Error setting up database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())