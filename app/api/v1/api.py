# app/api/v1/api.py - Created by setup script
"""
CorePath Impact API v1 Router
Main router that includes all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

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

# Health check for API
@api_router.get("/health", tags=["Health"])
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "CorePath Impact API v1"
    }