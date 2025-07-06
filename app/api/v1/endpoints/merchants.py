# app/api/v1/endpoints/merchants.py - Created by setup script
# app/api/v1/endpoints/merchants.py - Phase 4 Merchant Endpoints
"""
CorePath Impact Merchant API Endpoints
Phase 4: Merchant & Referral System
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.models.merchant import Merchant, MerchantApplication
from app.services.merchant_service import MerchantService
from app.schemas.merchant import (
    MerchantApplicationCreate, MerchantResponse, MerchantUpdate,
    ReferralLinkCreate, ReferralLinkResponse, PayoutRequest,
    MerchantAnalytics, ReferralResponse
)
from app.utils.helpers import create_response

router = APIRouter()

# Merchant Application Routes
@router.post("/apply", response_model=dict)
async def apply_for_merchant(
    application: MerchantApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit merchant application"""
    merchant_service = MerchantService(db)
    
    try:
        application_record = merchant_service.apply_for_merchant(
            user_id=current_user.id,
            application_data=application
        )
        
        return create_response(
            data={
                "application_id": application_record.id,
                "status": application_record.status,
                "submitted_at": application_record.submitted_at.isoformat()
            },
            message="Merchant application submitted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}"
        )

@router.get("/application/status", response_model=dict)
async def get_application_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's merchant application status"""
    application = db.query(MerchantApplication).filter(
        MerchantApplication.user_id == current_user.id
    ).first()
    
    if not application:
        return create_response(
            data={"status": "not_applied", "application": None},
            message="No application found"
        )
    
    return create_response(
        data={
            "status": application.status,
            "application": {
                "id": application.id,
                "submitted_at": application.submitted_at.isoformat(),
                "reviewed_at": application.reviewed_at.isoformat() if application.reviewed_at else None,
                "review_notes": application.review_notes
            }
        },
        message="Application status retrieved"
    )

# Merchant Profile Routes
@router.get("/profile", response_model=MerchantResponse)
async def get_merchant_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant profile for current user"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    return merchant

@router.put("/profile", response_model=MerchantResponse)
async def update_merchant_profile(
    merchant_update: MerchantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update merchant profile"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    updated_merchant = merchant_service.update_merchant(merchant.id, merchant_update)
    return updated_merchant

# Referral Tracking Routes
@router.post("/track-referral", response_model=dict)
async def track_referral_click(
    referral_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track a referral click (public endpoint)"""
    merchant_service = MerchantService(db)
    
    # Extract user data from request
    user_data = {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "source": request.query_params.get("source", "direct"),
        "landing_page": str(request.url)
    }
    
    try:
        tracking_token = merchant_service.track_referral_click(referral_code, user_data)
        
        return create_response(
            data={"tracking_token": tracking_token},
            message="Referral click tracked"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track referral: {str(e)}"
        )

@router.get("/referrals", response_model=dict)
async def get_merchant_referrals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant's referrals with pagination"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    referrals = merchant_service.get_merchant_referrals(merchant.id, page, per_page)
    return create_response(data=referrals, message="Referrals retrieved")

# Referral Links Management
@router.post("/referral-links", response_model=ReferralLinkResponse)
async def create_referral_link(
    link_data: ReferralLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create custom referral link"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    referral_link = merchant_service.create_referral_link(merchant.id, link_data)
    return referral_link

@router.get("/referral-links", response_model=List[ReferralLinkResponse])
async def get_referral_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant's referral links"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    return merchant_service.get_merchant_referral_links(merchant.id)

# Analytics Routes
@router.get("/analytics", response_model=MerchantAnalytics)
async def get_merchant_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant performance analytics"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    analytics = merchant_service.get_merchant_analytics(merchant.id, days)
    return analytics

# Payout Routes
@router.post("/request-payout", response_model=dict)
async def request_payout(
    payout_request: PayoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request payout for merchant"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    try:
        payout = merchant_service.request_payout(merchant.id, payout_request)
        
        return create_response(
            data={
                "payout_id": payout.id,
                "amount": payout.amount,
                "status": payout.status,
                "requested_at": payout.requested_at.isoformat()
            },
            message="Payout request submitted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request payout: {str(e)}"
        )

@router.get("/payouts", response_model=dict)
async def get_merchant_payouts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant's payout history"""
    merchant_service = MerchantService(db)
    merchant = merchant_service.get_merchant_by_user_id(current_user.id)
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    payouts = merchant_service.get_merchant_payouts(merchant.id, page, per_page)
    return create_response(data=payouts, message="Payouts retrieved")

# Admin Routes for Merchant Management
@router.get("/admin/applications", response_model=dict)
async def get_merchant_applications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get merchant applications (admin only)"""
    query = db.query(MerchantApplication)
    
    if status:
        query = query.filter(MerchantApplication.status == status)
    
    from app.utils.helpers import paginate_query
    applications = paginate_query(query, page, per_page)
    
    return create_response(data=applications, message="Applications retrieved")

@router.post("/admin/applications/{application_id}/review", response_model=dict)
async def review_merchant_application(
    application_id: int,
    approved: bool,
    notes: Optional[str] = None,
    commission_rate: Optional[float] = None,
    points_per_referral: Optional[int] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Review merchant application (admin only)"""
    merchant_service = MerchantService(db)
    
    kwargs = {}
    if commission_rate:
        kwargs["commission_rate"] = commission_rate
    if points_per_referral:
        kwargs["points_per_referral"] = points_per_referral
    
    try:
        result = merchant_service.review_application(
            application_id=application_id,
            reviewer_id=current_admin.id,
            approved=approved,
            notes=notes,
            **kwargs
        )
        
        if approved and result:
            return create_response(
                data={
                    "merchant_id": result.id,
                    "referral_code": result.referral_code,
                    "status": result.status
                },
                message="Merchant application approved"
            )
        else:
            return create_response(
                message="Merchant application rejected"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review application: {str(e)}"
        )

@router.get("/admin/stats", response_model=dict)
async def get_merchant_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get merchant system statistics (admin only)"""
    merchant_service = MerchantService(db)
    stats = merchant_service.get_admin_merchant_stats()
    
    return create_response(data=stats, message="Merchant system stats retrieved")

@router.get("/admin/merchants", response_model=dict)
async def get_all_merchants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all merchants (admin only)"""
    merchant_service = MerchantService(db)
    merchants = merchant_service.get_merchants(page, per_page, status)
    
    return create_response(data=merchants, message="Merchants retrieved")

# Public referral redirect endpoint
@router.get("/ref/{slug}", response_model=dict)
async def redirect_referral_link(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle referral link redirect"""
    merchant_service = MerchantService(db)
    
    try:
        # Track the click
        link = merchant_service.track_link_click(slug, is_unique=True)
        
        # Return redirect URL
        return create_response(
            data={
                "redirect_url": link.target_url,
                "merchant_code": link.merchant.referral_code
            },
            message="Referral link processed"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process referral link: {str(e)}"
        )