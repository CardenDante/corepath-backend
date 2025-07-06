# app/core/database.py - Created by setup script
"""
CorePath Impact Database Configuration
SQLite database setup with SQLAlchemy
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create SQLite engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for database operations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models.user import User, UserProfile
        # More models will be imported as we add them
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables (useful for development)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("🗑️ Database tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        raise


def reset_database():
    """Reset database - drop and recreate all tables"""
    print("🔄 Resetting database...")
    drop_tables()
    create_tables()
    print("✅ Database reset complete")


# Database utilities
class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def table_exists(table_name: str) -> bool:
        """Check if a table exists in the database"""
        from sqlalchemy import inspect
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    
    @staticmethod
    def get_table_count(table_name: str) -> int:
        """Get number of rows in a table"""
        with SessionLocal() as db:
            result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()
    
    @staticmethod
    def backup_database(backup_path: str = "backup.db"):
        """Create a backup of the database"""
        import shutil
        import os
        
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"📦 Database backed up to: {backup_path}")
        else:
            print("❌ Database file not found")


# Health check for database
def check_database_health() -> dict:
    """Check database connection and return status"""
    try:
        with SessionLocal() as db:
            # Try a simple query
            db.execute("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "type": "sqlite"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }