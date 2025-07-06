# app/api/v1/endpoints/users.py - Created by setup script
"""
CorePath Impact User Management Endpoints
API endpoints for user profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User, UserProfile
from app.schemas.auth import UserResponse, MessageResponse
from app.api.deps import get_current_user, get_current_admin_user, pagination_params
from pydantic import BaseModel, EmailStr, Field

router = APIRouter()


class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    newsletter_subscribed: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+254712345678",
                "bio": "Passionate about values-driven parenting",
                "address_line_1": "123 Main Street",
                "city": "Nairobi",
                "state": "Nairobi County",
                "postal_code": "00100",
                "country": "Kenya",
                "newsletter_subscribed": True,
                "email_notifications": True,
                "sms_notifications": False
            }
        }


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    
    # Profile data
    bio: Optional[str]
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    newsletter_subscribed: bool
    email_notifications: bool
    sms_notifications: bool
    
    # Points and stats
    current_points_balance: int
    total_points_earned: int
    total_points_spent: int
    total_orders: int
    total_spent: float
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self) -> str:
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])

    class Config:
        from_attributes = True


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's complete profile
    
    Returns user information including profile data, points, and statistics
    """
    try:
        # Get or create user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            # Create default profile if doesn't exist
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Combine user and profile data
        profile_data = {
            # User data
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            
            # Profile data
            "bio": profile.bio,
            "address_line_1": profile.address_line_1,
            "address_line_2": profile.address_line_2,
            "city": profile.city,
            "state": profile.state,
            "postal_code": profile.postal_code,
            "country": profile.country,
            "newsletter_subscribed": profile.newsletter_subscribed,
            "email_notifications": profile.email_notifications,
            "sms_notifications": profile.sms_notifications,
            
            # Points and stats
            "current_points_balance": profile.current_points_balance,
            "total_points_earned": profile.total_points_earned,
            "total_points_spent": profile.total_points_spent,
            "total_orders": profile.total_orders,
            "total_spent": profile.total_spent,
        }
        
        return UserProfileResponse(**profile_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    
    Updates user and profile information with provided data
    Only provided fields will be updated
    """
    try:
        # Update user fields
        user_fields = ["first_name", "last_name", "phone"]
        for field in user_fields:
            value = getattr(profile_update, field, None)
            if value is not None:
                setattr(current_user, field, value)
        
        # Get or create user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
        
        # Update profile fields
        profile_fields = [
            "bio", "address_line_1", "address_line_2", "city", "state", 
            "postal_code", "country", "newsletter_subscribed", 
            "email_notifications", "sms_notifications"
        ]
        
        for field in profile_fields:
            value = getattr(profile_update, field, None)
            if value is not None:
                setattr(profile, field, value)
        
        db.commit()
        db.refresh(current_user)
        db.refresh(profile)
        
        # Return updated profile
        profile_data = {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "bio": profile.bio,
            "address_line_1": profile.address_line_1,
            "address_line_2": profile.address_line_2,
            "city": profile.city,
            "state": profile.state,
            "postal_code": profile.postal_code,
            "country": profile.country,
            "newsletter_subscribed": profile.newsletter_subscribed,
            "email_notifications": profile.email_notifications,
            "sms_notifications": profile.sms_notifications,
            "current_points_balance": profile.current_points_balance,
            "total_points_earned": profile.total_points_earned,
            "total_points_spent": profile.total_points_spent,
            "total_orders": profile.total_orders,
            "total_spent": profile.total_spent,
        }
        
        return UserProfileResponse(**profile_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/points")
async def get_user_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's points information
    
    Returns points balance and statistics
    """
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        return {
            "current_balance": profile.current_points_balance,
            "total_earned": profile.total_points_earned,
            "total_spent": profile.total_points_spent,
            "available_for_redemption": profile.current_points_balance
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve points information"
        )


@router.delete("/account", response_model=MessageResponse)
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user account
    
    Marks account as inactive but preserves data
    """
    try:
        current_user.is_active = False
        db.commit()
        
        return MessageResponse(
            message="Account deactivated successfully",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


# Admin endpoints
@router.get("/admin/users", response_model=list[UserResponse])
async def list_all_users(
    pagination: dict = Depends(pagination_params),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    
    Returns paginated list of all users
    """
    try:
        users = db.query(User)\
                 .offset(pagination["offset"])\
                 .limit(pagination["limit"])\
                 .all()
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/admin/users/{user_id}", response_model=UserProfileResponse)
async def get_user_by_id(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get specific user by ID (Admin only)
    
    Returns complete user profile information
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        profile_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "bio": profile.bio,
            "address_line_1": profile.address_line_1,
            "address_line_2": profile.address_line_2,
            "city": profile.city,
            "state": profile.state,
            "postal_code": profile.postal_code,
            "country": profile.country,
            "newsletter_subscribed": profile.newsletter_subscribed,
            "email_notifications": profile.email_notifications,
            "sms_notifications": profile.sms_notifications,
            "current_points_balance": profile.current_points_balance,
            "total_points_earned": profile.total_points_earned,
            "total_points_spent": profile.total_points_spent,
            "total_orders": profile.total_orders,
            "total_spent": profile.total_spent,
        }
        
        return UserProfileResponse(**profile_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/admin/users/{user_id}/toggle-status", response_model=MessageResponse)
async def toggle_user_status(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle user active status (Admin only)
    
    Activates or deactivates user account
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't allow admin to deactivate themselves
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own account status"
            )
        
        user.is_active = not user.is_active
        db.commit()
        
        status_text = "activated" if user.is_active else "deactivated"
        return MessageResponse(
            message=f"User account {status_text} successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )