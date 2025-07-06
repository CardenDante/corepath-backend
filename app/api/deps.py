# app/api/deps.py - Created by setup script
"""
CorePath Impact API Dependencies
Dependency injection functions for FastAPI
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import extract_token_data
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# Security scheme for JWT tokens
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance"""
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user from JWT token
    Usage: current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials
    token_data = extract_token_data(token)
    
    user = auth_service.get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for active status)
    Usage: user: User = Depends(get_current_active_user)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user (email must be verified)
    Usage: user: User = Depends(get_current_verified_user)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please verify your email first."
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    Get current admin user (must be admin role)
    Usage: admin: User = Depends(get_current_admin_user)
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_current_merchant_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    Get current merchant user (must be merchant role)
    Usage: merchant: User = Depends(get_current_merchant_user)
    """
    if current_user.role not in [UserRole.MERCHANT.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant access required"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Usage: user: Optional[User] = Depends(get_optional_current_user)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = extract_token_data(token)
        user = auth_service.get_user_by_id(token_data.user_id)
        
        if user and user.is_active:
            return user
    except:
        pass
    
    return None


class RoleChecker:
    """Role-based access control checker"""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_verified_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


# Convenience role checkers
require_admin = RoleChecker([UserRole.ADMIN.value])
require_merchant = RoleChecker([UserRole.MERCHANT.value, UserRole.ADMIN.value])
require_customer = RoleChecker([UserRole.CUSTOMER.value, UserRole.MERCHANT.value, UserRole.ADMIN.value])


def pagination_params(
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> dict:
    """
    Pagination parameters dependency
    Usage: pagination: dict = Depends(pagination_params)
    """
    if page < 1:
        page = 1
    
    if limit < 1:
        limit = 20
    elif limit > max_limit:
        limit = max_limit
    
    offset = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "offset": offset
    }


def search_params(
    q: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc"
) -> dict:
    """
    Search and sorting parameters dependency
    Usage: search: dict = Depends(search_params)
    """
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"
    
    return {
        "query": q.strip() if q else None,
        "sort_by": sort_by,
        "sort_order": sort_order
    }


# Database transaction decorator (for service methods)
class DatabaseTransaction:
    """Database transaction context manager for service methods"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()


def get_db_transaction(db: Session = Depends(get_db)) -> DatabaseTransaction:
    """
    Get database transaction context
    Usage: with get_db_transaction() as db: ...
    """
    return DatabaseTransaction(db)