# app/api/v1/api.py - Updated Complete API Router
"""
CorePath Impact API v1 Router
Main router that includes all endpoint routers - COMPLETE SYSTEM
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, products, cart, orders, merchants, admin, courses

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Include user routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Include product routes
api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Products"]
)

# Include cart routes
api_router.include_router(
    cart.router,
    prefix="/cart",
    tags=["Shopping Cart"]
)

# Include order routes
api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Orders"]
)

# Include merchant routes (Phase 4)
api_router.include_router(
    merchants.router,
    prefix="/merchants",
    tags=["Merchants & Referrals"]
)

# Include course routes (Phase 5)
api_router.include_router(
    courses.router,
    prefix="/courses",
    tags=["Courses & Learning"]
)

# Include admin routes (Phase 5)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

# Health check for API
@api_router.get("/health", tags=["Health"])
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "CorePath Impact API v1",
        "features": {
            "authentication": True,
            "users": True,
            "products": True,
            "cart": True,
            "orders": True,
            "merchants": True,
            "referrals": True,
            "courses": True,
            "learning": True,
            "admin": True
        }
    }

# API Information
@api_router.get("/info", tags=["Info"])
async def api_info():
    """API information and available endpoints"""
    return {
        "name": "CorePath Impact API",
        "version": "1.0.0",
        "description": "Values Driven Parenting Platform API - COMPLETE SYSTEM",
        "endpoints": {
            "authentication": "/auth",
            "users": "/users",
            "products": "/products",
            "cart": "/cart",
            "orders": "/orders",
            "merchants": "/merchants",
            "courses": "/courses",
            "admin": "/admin"
        },
        "features": [
            "🔐 JWT Authentication with refresh tokens",
            "👥 User management with profiles",
            "🛍️ Complete e-commerce system",
            "🎯 500-point referral system",
            "📚 Course management & learning",
            "⚡ Complete admin panel",
            "📁 Local file storage",
            "📊 Analytics & reporting"
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "🎉 ALL 5 PHASES COMPLETE!"
    }