# app/core/config.py - Created by setup script
"""
CorePath Impact Backend Configuration
Environment-based settings management
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    PROJECT_NAME: str = "CorePath Impact API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./corepath.db"
    
    # Security
    SECRET_KEY: str = "corepath-secret-key-change-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Storage (Local)
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_IMAGE_TYPES: str = "jpg,jpeg,png,gif,webp"
    
    # Email (Optional for development)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@corepathimpact.com"
    
    # Stripe (for payments)
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # WordPress (for blog)
    WORDPRESS_API_URL: Optional[str] = None
    
    # Points and Rewards
    REFERRAL_POINTS: int = 500  # Points awarded per successful referral
    SIGNUP_BONUS_POINTS: int = 100  # Points for new user signup
    ORDER_POINTS_RATE: float = 0.01  # Points per dollar spent (1%)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_image_extensions(self) -> list:
        """Get list of allowed image file extensions"""
        return [ext.strip().lower() for ext in self.ALLOWED_IMAGE_TYPES.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG
    
    @property
    def is_email_enabled(self) -> bool:
        """Check if email configuration is available"""
        return all([
            self.SMTP_HOST,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD
        ])
    
    @property
    def is_stripe_enabled(self) -> bool:
        """Check if Stripe configuration is available"""
        return all([
            self.STRIPE_PUBLISHABLE_KEY,
            self.STRIPE_SECRET_KEY
        ])


# Create global settings instance
settings = Settings()

# Ensure upload directory exists
upload_dir = settings.UPLOAD_DIR
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)
    
# Create subdirectories for different upload types
subdirs = ["products", "users", "courses"]
for subdir in subdirs:
    subdir_path = os.path.join(upload_dir, subdir)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)