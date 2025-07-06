# app/core/database.py - Updated with all models (Complete)
"""
CorePath Impact Database Configuration
SQLite database setup with SQLAlchemy - ALL PHASES COMPLETE
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
    """Create all database tables - ALL PHASES"""
    try:
        # Import all models to ensure they're registered
        
        # Phase 1: Users and Authentication
        from app.models.user import User, UserProfile, UserSession
        
        # Phase 2: Products and Categories
        from app.models.product import (
            Product, Category, ProductImage, ProductVariant, 
            ProductReview, ProductTag
        )
        
        # Phase 3: Orders and Cart
        from app.models.order import (
            Order, OrderItem, ShoppingCart, CartItem, 
            Payment, Coupon, CouponUsage
        )
        
        # Phase 4: Merchants and Referrals
        from app.models.merchant import (
            Merchant, MerchantReferral, MerchantPayout, 
            ReferralLink, MerchantApplication
        )
        
        # Phase 5: Courses and Admin
        from app.models.course import (
            Course, CourseModule, CourseLesson, CourseEnrollment,
            LessonProgress, CourseReview, CourseCategory, CourseCertificate
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All database tables created successfully!")
        print("📊 Phases complete:")
        print("   ✓ Phase 1: Users & Authentication")
        print("   ✓ Phase 2: Products & Categories") 
        print("   ✓ Phase 3: Shopping Cart & Orders")
        print("   ✓ Phase 4: Merchants & Referrals")
        print("   ✓ Phase 5: Courses & Admin")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables (useful for development)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("🗑️ All database tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        raise


def reset_database():
    """Reset database - drop and recreate all tables"""
    print("🔄 Resetting complete database...")
    drop_tables()
    create_tables()
    print("✅ Complete database reset finished!")


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
    def get_all_tables() -> list:
        """Get list of all tables in database"""
        from sqlalchemy import inspect
        inspector = inspect(engine)
        return inspector.get_table_names()
    
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
    
    @staticmethod
    def get_database_size() -> dict:
        """Get database size information"""
        import os
        
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                "size_bytes": size_bytes,
                "size_mb": round(size_mb, 2),
                "path": db_path
            }
        return {"error": "Database file not found"}


# Health check for database
def check_database_health() -> dict:
    """Check database connection and return status"""
    try:
        with SessionLocal() as db:
            # Try a simple query
            db.execute("SELECT 1")
            
            # Get table information
            tables = DatabaseUtils.get_all_tables()
            db_size = DatabaseUtils.get_database_size()
            
            return {
                "status": "healthy",
                "database": "connected",
                "type": "sqlite",
                "tables_count": len(tables),
                "tables": tables,
                "size_info": db_size
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# Initialize database with sample data (for development)
def init_sample_data():
    """Initialize database with sample data for development"""
    from app.models.user import User, UserProfile, UserRole
    from app.models.product import Category
    from app.core.security import SecurityUtils
    
    with SessionLocal() as db:
        # Create admin user if not exists
        admin_email = "admin@corepathimpact.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            admin_user = User(
                email=admin_email,
                password_hash=SecurityUtils.get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN.value,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.flush()
            
            # Create admin profile
            admin_profile = UserProfile(
                user_id=admin_user.id,
                current_points_balance=1000,
                total_points_earned=1000
            )
            db.add(admin_profile)
            
            print(f"✅ Admin user created: {admin_email} / admin123")
        
        # Create sample categories if not exist
        sample_categories = [
            {"name": "VDC Toolkits", "description": "Values Driven Character Toolkits"},
            {"name": "Books & Guides", "description": "Educational books and guides"},
            {"name": "Training Cards", "description": "Character training cards"},
            {"name": "Online Courses", "description": "Interactive online courses"},
            {"name": "Digital Downloads", "description": "Downloadable content"}
        ]
        
        for cat_data in sample_categories:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                from app.utils.helpers import slugify
                category = Category(
                    name=cat_data["name"],
                    slug=slugify(cat_data["name"]),
                    description=cat_data["description"],
                    is_active=True
                )
                db.add(category)
        
        db.commit()
        print("✅ Sample data initialized!")


# Database migration utilities (for future use)
class DatabaseMigration:
    """Database migration utilities"""
    
    @staticmethod
    def add_column(table_name: str, column_definition: str):
        """Add a column to existing table"""
        with SessionLocal() as db:
            db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
            db.commit()
    
    @staticmethod
    def create_index(table_name: str, column_name: str, index_name: str = None):
        """Create index on table column"""
        if not index_name:
            index_name = f"idx_{table_name}_{column_name}"
        
        with SessionLocal() as db:
            db.execute(f"CREATE INDEX {index_name} ON {table_name} ({column_name})")
            db.commit()


# Performance monitoring
def get_database_performance() -> dict:
    """Get basic database performance metrics"""
    try:
        with SessionLocal() as db:
            # Get table sizes
            tables = DatabaseUtils.get_all_tables()
            table_stats = {}
            
            for table in tables:
                try:
                    count = DatabaseUtils.get_table_count(table)
                    table_stats[table] = count
                except:
                    table_stats[table] = "error"
            
            return {
                "status": "success",
                "table_counts": table_stats,
                "total_tables": len(tables)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }