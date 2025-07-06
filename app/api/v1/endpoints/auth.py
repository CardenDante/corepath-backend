"""
CorePath Impact Authentication Endpoints
API endpoints for user authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    EmailVerificationRequest,
    ResendVerificationRequest,
    MessageResponse,
    UserResponse
)
from app.api.deps import get_current_user, get_auth_service
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account
    
    - **email**: User's email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, number)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    
    Returns JWT tokens and user information
    """
    try:
        user, token_response = auth_service.register_user(user_data)
        
        # Convert user to response format
        user_response = UserResponse.from_orm(user)
        
        return TokenResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and get access tokens
    
    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Keep user logged in longer
    
    Returns JWT tokens and user information
    """
    try:
        user, token_response = auth_service.authenticate_user(login_data)
        
        # Convert user to response format
        user_response = UserResponse.from_orm(user)
        
        return TokenResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new JWT tokens
    """
    try:
        token_response = auth_service.refresh_token(refresh_data.refresh_token)
        
        # Get user info for response
        from app.core.security import extract_token_data
        token_data = extract_token_data(token_response["access_token"])
        user = auth_service.get_user_by_id(token_data.user_id)
        user_response = UserResponse.from_orm(user)
        
        return TokenResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email address with token
    
    - **token**: Email verification token sent to user's email
    
    Marks user email as verified
    """
    try:
        user = auth_service.verify_email(verification_data.token)
        return MessageResponse(
            message="Email verified successfully",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    resend_data: ResendVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Resend email verification token
    
    - **email**: User's email address
    
    Sends new verification email (if email exists)
    """
    try:
        user = auth_service.get_user_by_email(resend_data.email)
        if user and not user.is_verified:
            # TODO: Implement email sending
            # For now, just regenerate token
            from app.core.security import SecurityUtils
            user.email_verification_token = SecurityUtils.generate_random_string(64)
            auth_service.db.commit()
            
            return MessageResponse(
                message="Verification email sent (check console for token)",
                success=True
            )
        
        # Don't reveal if email exists
        return MessageResponse(
            message="If email exists and is unverified, verification email has been sent",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset token
    
    - **email**: User's email address
    
    Sends password reset email (if email exists)
    """
    try:
        reset_token = auth_service.request_password_reset(reset_data.email)
        return MessageResponse(
            message="If email exists, password reset instructions have been sent",
            success=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token from email
    - **new_password**: New strong password
    - **confirm_password**: Password confirmation
    
    Updates user password
    """
    try:
        user = auth_service.reset_password(reset_data.token, reset_data.new_password)
        return MessageResponse(
            message="Password reset successfully",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password (authenticated)
    
    - **current_password**: User's current password
    - **new_password**: New strong password
    - **confirm_password**: Password confirmation
    
    Requires valid authentication token
    """
    try:
        user = auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        return MessageResponse(
            message="Password changed successfully",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user
    
    Invalidates current session tokens
    Requires valid authentication token
    """
    try:
        auth_service.logout_user(current_user.id)
        return MessageResponse(
            message="Logged out successfully",
            success=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Returns authenticated user's profile data
    Requires valid authentication token
    """
    return UserResponse.from_orm(current_user)


@router.get("/check-email/{email}")
async def check_email_availability(email: str, auth_service: AuthService = Depends(get_auth_service)):
    """
    Check if email is available for registration
    
    - **email**: Email address to check
    
    Returns availability status
    """
    try:
        existing_user = auth_service.get_user_by_email(email)
        is_available = existing_user is None
        
        return {
            "email": email,
            "available": is_available,
            "message": "Email is available" if is_available else "Email is already registered"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check email availability"
        )