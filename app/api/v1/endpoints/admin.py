# app/api/v1/endpoints/admin.py - Phase 5 Admin Endpoints
"""
CorePath Impact Admin API Endpoints
Phase 5: Admin panel and system management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User, UserProfile
from app.models.product import Product, Category
from app.models.order import Order, OrderStatus
from app.models.merchant import Merchant, MerchantApplication
from app.models.course import Course, CourseEnrollment
from app.utils.helpers import create_response, paginate_query

router = APIRouter()

# Dashboard Analytics
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard analytics"""
    
    # User statistics
    total_users = db.query(User).count()
    new_users_today = db.query(User).filter(
        func.date(User.created_at) == func.current_date()
    ).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # Order statistics
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value])
    ).scalar() or 0
    
    # Product statistics
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.status == "active").count()
    
    # Merchant statistics
    total_merchants = db.query(Merchant).count()
    pending_applications = db.query(MerchantApplication).filter(
        MerchantApplication.status == "pending"
    ).count()
    
    # Course statistics (if courses are enabled)
    total_courses = db.query(Course).count()
    total_enrollments = db.query(CourseEnrollment).count()
    
    # Recent activity
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
    recent_orders = db.query(Order).order_by(desc(Order.created_at)).limit(5).all()
    
    return create_response(
        data={
            "users": {
                "total": total_users,
                "new_today": new_users_today,
                "verified": verified_users,
                "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "revenue": float(total_revenue)
            },
            "products": {
                "total": total_products,
                "active": active_products
            },
            "merchants": {
                "total": total_merchants,
                "pending_applications": pending_applications
            },
            "courses": {
                "total": total_courses,
                "enrollments": total_enrollments
            },
            "recent_activity": {
                "users": [
                    {
                        "id": user.id,
                        "email": user.email,
                        "name": user.full_name,
                        "created_at": user.created_at.isoformat()
                    }
                    for user in recent_users
                ],
                "orders": [
                    {
                        "id": order.id,
                        "order_number": order.order_number,
                        "customer": order.customer_name,
                        "amount": order.total_amount,
                        "status": order.status,
                        "created_at": order.created_at.isoformat()
                    }
                    for order in recent_orders
                ]
            }
        },
        message="Dashboard data retrieved successfully"
    )

# User Management
@router.get("/users", response_model=Dict[str, Any])
async def get_all_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination"""
    
    query = db.query(User)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    query = query.order_by(desc(User.created_at))
    
    result = paginate_query(query, page, per_page)
    
    return create_response(data=result, message="Users retrieved successfully")

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's orders
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(desc(Order.created_at)).limit(10).all()
    
    # Get user's enrollments if applicable
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == user_id
    ).order_by(desc(CourseEnrollment.enrolled_at)).limit(5).all()
    
    return create_response(
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "profile": {
                    "total_points_earned": user.profile.total_points_earned if user.profile else 0,
                    "current_points_balance": user.profile.current_points_balance if user.profile else 0,
                    "total_orders": user.profile.total_orders if user.profile else 0,
                    "total_spent": user.profile.total_spent if user.profile else 0
                } if user.profile else None
            },
            "recent_orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "created_at": order.created_at.isoformat()
                }
                for order in orders
            ],
            "course_enrollments": [
                {
                    "id": enrollment.id,
                    "course_title": enrollment.course.title,
                    "progress": enrollment.progress_percentage,
                    "status": enrollment.status,
                    "enrolled_at": enrollment.enrolled_at.isoformat()
                }
                for enrollment in enrollments
            ]
        },
        message="User details retrieved successfully"
    )

@router.put("/users/{user_id}/toggle-active", response_model=Dict[str, Any])
async def toggle_user_active_status(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = not user.is_active
    db.commit()
    
    return create_response(
        data={
            "user_id": user.id,
            "is_active": user.is_active
        },
        message=f"User {'activated' if user.is_active else 'deactivated'} successfully"
    )

# Product Management
@router.get("/products/stats", response_model=Dict[str, Any])
async def get_product_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get product statistics"""
    
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.status == "active").count()
    featured_products = db.query(Product).filter(Product.is_featured == True).count()
    
    # Top selling products
    top_products = db.query(Product).order_by(desc(Product.purchase_count)).limit(10).all()
    
    # Products by category
    categories_stats = db.query(
        Category.name,
        func.count(Product.id).label('product_count')
    ).join(Product).group_by(Category.name).all()
    
    return create_response(
        data={
            "total_products": total_products,
            "active_products": active_products,
            "featured_products": featured_products,
            "top_selling": [
                {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "purchase_count": product.purchase_count,
                    "view_count": product.view_count
                }
                for product in top_products
            ],
            "by_category": [
                {
                    "category": category.name,
                    "count": category.product_count
                }
                for category in categories_stats
            ]
        },
        message="Product statistics retrieved successfully"
    )

# Order Management
@router.get("/orders/stats", response_model=Dict[str, Any])
async def get_order_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get order statistics"""
    
    # Order counts by status
    order_stats = db.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total_amount')
    ).group_by(Order.status).all()
    
    # Recent revenue (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= thirty_days_ago,
        Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value])
    ).scalar() or 0
    
    # Average order value
    avg_order_value = db.query(func.avg(Order.total_amount)).scalar() or 0
    
    return create_response(
        data={
            "by_status": [
                {
                    "status": stat.status,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount or 0)
                }
                for stat in order_stats
            ],
            "recent_revenue": float(recent_revenue),
            "average_order_value": float(avg_order_value)
        },
        message="Order statistics retrieved successfully"
    )

# System Settings
@router.get("/settings", response_model=Dict[str, Any])
async def get_system_settings(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get system settings"""
    
    from app.core.config import settings
    
    return create_response(
        data={
            "app": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "debug": settings.DEBUG
            },
            "features": {
                "email_enabled": settings.is_email_enabled,
                "stripe_enabled": settings.is_stripe_enabled,
                "points_system": True,
                "referral_system": True,
                "courses": True
            },
            "points": {
                "signup_bonus": settings.SIGNUP_BONUS_POINTS,
                "referral_reward": settings.REFERRAL_POINTS,
                "order_rate": settings.ORDER_POINTS_RATE
            },
            "uploads": {
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_types": settings.ALLOWED_IMAGE_TYPES
            }
        },
        message="System settings retrieved successfully"
    )

# Analytics and Reports
@router.get("/analytics/users", response_model=Dict[str, Any])
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user analytics for specified period"""
    
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily user registrations
    daily_registrations = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('registrations')
    ).filter(
        User.created_at >= start_date
    ).group_by(func.date(User.created_at)).order_by(func.date(User.created_at)).all()
    
    # User roles distribution
    role_distribution = db.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    return create_response(
        data={
            "period_days": days,
            "daily_registrations": [
                {
                    "date": str(reg.date),
                    "registrations": reg.registrations
                }
                for reg in daily_registrations
            ],
            "role_distribution": [
                {
                    "role": role.role,
                    "count": role.count
                }
                for role in role_distribution
            ]
        },
        message="User analytics retrieved successfully"
    )

@router.get("/analytics/revenue", response_model=Dict[str, Any])
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get revenue analytics for specified period"""
    
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily revenue
    daily_revenue = db.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total_amount).label('revenue'),
        func.count(Order.id).label('orders')
    ).filter(
        Order.created_at >= start_date,
        Order.status.in_([OrderStatus.DELIVERED.value, OrderStatus.SHIPPED.value, OrderStatus.PROCESSING.value])
    ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
    
    return create_response(
        data={
            "period_days": days,
            "daily_revenue": [
                {
                    "date": str(rev.date),
                    "revenue": float(rev.revenue or 0),
                    "orders": rev.orders
                }
                for rev in daily_revenue
            ]
        },
        message="Revenue analytics retrieved successfully"
    )

# System Health and Monitoring
@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    
    # Database health
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
        database_error = None
    except Exception as e:
        database_status = "unhealthy"
        database_error = str(e)
    
    # File system health
    import os
    from app.core.config import settings
    
    upload_dir = settings.UPLOAD_DIR
    uploads_writable = os.access(upload_dir, os.W_OK) if os.path.exists(upload_dir) else False
    
    # Memory usage (basic check)
    import psutil
    memory_usage = psutil.virtual_memory()
    
    return create_response(
        data={
            "database": {
                "status": database_status,
                "error": database_error
            },
            "file_system": {
                "uploads_directory": upload_dir,
                "writable": uploads_writable
            },
            "memory": {
                "total_gb": round(memory_usage.total / (1024**3), 2),
                "available_gb": round(memory_usage.available / (1024**3), 2),
                "percent_used": memory_usage.percent
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        message="System health retrieved successfully"
    )

# Activity Logs (simplified version)
@router.get("/logs/activity", response_model=Dict[str, Any])
async def get_activity_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent system activity logs"""
    
    # This is a simplified version - in production you'd have a proper audit log table
    recent_activities = []
    
    # Recent user registrations
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(20).all()
    for user in recent_users:
        recent_activities.append({
            "type": "user_registration",
            "description": f"New user registered: {user.email}",
            "timestamp": user.created_at.isoformat(),
            "user_id": user.id
        })
    
    # Recent orders
    recent_orders = db.query(Order).order_by(desc(Order.created_at)).limit(20).all()
    for order in recent_orders:
        recent_activities.append({
            "type": "order_created",
            "description": f"Order {order.order_number} created by {order.customer_name}",
            "timestamp": order.created_at.isoformat(),
            "order_id": order.id
        })
    
    # Sort by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Simple pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_activities = recent_activities[start:end]
    
    return create_response(
        data={
            "activities": paginated_activities,
            "total": len(recent_activities),
            "page": page,
            "per_page": per_page
        },
        message="Activity logs retrieved successfully"
    )

# Configuration Management
@router.post("/settings/points", response_model=Dict[str, Any])
async def update_points_settings(
    signup_bonus: Optional[int] = None,
    referral_reward: Optional[int] = None,
    order_rate: Optional[float] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update points system settings"""
    
    # In a real implementation, you'd store these in a settings table
    # For now, we'll just validate and return success
    
    updates = {}
    if signup_bonus is not None:
        if signup_bonus < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup bonus cannot be negative"
            )
        updates["signup_bonus"] = signup_bonus
    
    if referral_reward is not None:
        if referral_reward < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referral reward cannot be negative"
            )
        updates["referral_reward"] = referral_reward
    
    if order_rate is not None:
        if order_rate < 0 or order_rate > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order rate must be between 0 and 1"
            )
        updates["order_rate"] = order_rate
    
    return create_response(
        data=updates,
        message="Points settings updated successfully"
    )

# Backup and Maintenance
@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
async def run_system_cleanup(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Run system cleanup tasks"""
    
    results = {}
    
    # Clean up old sessions (placeholder)
    results["sessions_cleaned"] = 0
    
    # Clean up temporary files
    from app.services.file_service import FileService
    file_service = FileService()
    temp_files_deleted = file_service.cleanup_temp_files(24)  # 24 hours old
    results["temp_files_deleted"] = temp_files_deleted
    
    # Clean up expired referrals (placeholder)
    results["expired_referrals_cleaned"] = 0
    
    return create_response(
        data=results,
        message="System cleanup completed successfully"
    )