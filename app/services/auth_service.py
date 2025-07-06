# app/services/auth_service.py - Created by setup script
"""
CorePath Impact Authentication Service
Business logic for user authentication and management
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserProfile, UserSession
from app.core.security import SecurityUtils, create_token_response
from app.core.config import settings
from app.schemas.auth import UserRegisterRequest, UserLoginRequest


class AuthService:
    """Authentication service with business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: UserRegisterRequest) -> Tuple[User, dict]:
        """
        Register a new user
        Returns: (user, token_response)
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        password_hash = SecurityUtils.get_password_hash(user_data.password)
        verification_token = SecurityUtils.generate_random_string(64)
        
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            email_verification_token=verification_token,
            role="customer"  # Default role
        )
        
        self.db.add(new_user)
        self.db.flush()  # Get the user ID
        
        # Create user profile with signup bonus points
        profile = UserProfile(
            user_id=new_user.id,
            current_points_balance=settings.SIGNUP_BONUS_POINTS,
            total_points_earned=settings.SIGNUP_BONUS_POINTS
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(new_user)
        
        # Create tokens
        token_response = create_token_response(new_user.id, new_user.email)
        
        # TODO: Send verification email (when email service is implemented)
        print(f"📧 Verification token for {new_user.email}: {verification_token}")
        
        return new_user, token_response
    
    def authenticate_user(self, login_data: UserLoginRequest) -> Tuple[User, dict]:
        """
        Authenticate user and return tokens
        Returns: (user, token_response)
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not SecurityUtils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Create tokens
        token_response = create_token_response(user.id, user.email)
        
        return user, token_response
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def verify_email(self, token: str) -> User:
        """Verify user email with token"""
        user = self.db.query(User).filter(User.email_verification_token == token).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Mark as verified
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token = None
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def request_password_reset(self, email: str) -> str:
        """Request password reset for user"""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists or not
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="If email exists, reset instructions have been sent"
            )
        
        # Generate reset token
        reset_token = SecurityUtils.generate_random_string(64)
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        
        self.db.commit()
        
        # TODO: Send password reset email
        print(f"🔑 Password reset token for {user.email}: {reset_token}")
        
        return reset_token
    
    def reset_password(self, token: str, new_password: str) -> User:
        """Reset user password with token"""
        user = self.db.query(User).filter(User.password_reset_token == token).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Check if token is expired
        if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Update password
        user.password_hash = SecurityUtils.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> User:
        """Change user password (authenticated)"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not SecurityUtils.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = SecurityUtils.get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        try:
            payload = SecurityUtils.verify_token(refresh_token)
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("user_id")
            email = payload.get("sub")
            
            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token data"
                )
            
            # Verify user still exists and is active
            user = self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new tokens
            return create_token_response(user.id, user.email)
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    def deactivate_user(self, user_id: int) -> User:
        """Deactivate user account"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_user_session(self, user_id: int, device_info: str = None, ip_address: str = None) -> UserSession:
        """Create a new user session"""
        session_token = SecurityUtils.generate_random_string(64)
        refresh_token = SecurityUtils.generate_random_string(64)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def logout_user(self, user_id: int, session_token: str = None):
        """Logout user and invalidate sessions"""
        if session_token:
            # Logout specific session
            session = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.session_token == session_token
            ).first()
            if session:
                session.is_active = False
        else:
            # Logout all sessions
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).update({"is_active": False})
        
        self.db.commit()