# app/core/dependencies.py - Authentication Dependencies
"""
CorePath Impact Authentication Dependencies
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SecurityUtils
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    try:
        # Verify and decode token
        payload = SecurityUtils.verify_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for active status)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current verified user (email must be verified)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user (admin role required)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_merchant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current merchant user (merchant role or approved merchant required)
    """
    if current_user.is_merchant:
        return current_user
    
    # Check if user has approved merchant profile
    from app.models.merchant import Merchant, MerchantStatus
    merchant = db.query(Merchant).filter(
        Merchant.user_id == current_user.id,
        Merchant.status == MerchantStatus.APPROVED.value,
        Merchant.is_active == True
    ).first()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant access required"
        )
    
    return current_user


def require_role(required_role: str):
    """
    Dependency factory for role-based access control
    Usage: user = Depends(require_role("admin"))
    """
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return check_role


def require_any_role(allowed_roles: list):
    """
    Dependency factory for multiple role access control
    Usage: user = Depends(require_any_role(["admin", "merchant"]))
    """
    async def check_roles(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return check_roles


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Useful for endpoints that work for both authenticated and anonymous users
    """
    if not credentials:
        return None
    
    try:
        payload = SecurityUtils.verify_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            return None
        
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(user_id)
        
        if user and user.is_active:
            return user
        
        return None
    except:
        return None


# Rate limiting dependencies (placeholder for future implementation)
def rate_limit(requests_per_minute: int = 60):
    """
    Rate limiting dependency (placeholder)
    In production, this would use Redis or similar
    """
    async def check_rate_limit():
        # TODO: Implement actual rate limiting
        # For now, just pass through
        pass
    
    return check_rate_limit


# Permission-based dependencies
class Permissions:
    """Permission constants"""
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    READ_PRODUCTS = "read:products"
    WRITE_PRODUCTS = "write:products"
    READ_ORDERS = "read:orders"
    WRITE_ORDERS = "write:orders"
    READ_MERCHANTS = "read:merchants"
    WRITE_MERCHANTS = "write:merchants"
    READ_ANALYTICS = "read:analytics"
    ADMIN_ACCESS = "admin:access"


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control
    """
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        # Admin users have all permissions
        if current_user.is_admin:
            return current_user
        
        # Basic permission mapping based on roles
        user_permissions = []
        
        if current_user.is_merchant:
            user_permissions.extend([
                Permissions.READ_PRODUCTS,
                Permissions.READ_MERCHANTS,
                Permissions.WRITE_MERCHANTS  # Own profile only
            ])
        
        # All authenticated users can read basic data
        user_permissions.extend([
            Permissions.READ_PRODUCTS,
            Permissions.READ_ORDERS  # Own orders only
        ])
        
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return current_user
    
    return check_permission