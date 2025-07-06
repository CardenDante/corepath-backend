# app/services/merchant_service.py - Created by setup script
"""
CorePath Impact Merchant Service
Business logic for merchant system and referral tracking
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import secrets
import string

from app.models.merchant import (
    Merchant, MerchantReferral, MerchantPayout, ReferralLink, MerchantApplication,
    MerchantStatus, ReferralStatus, PayoutStatus
)
from app.models.user import User, UserProfile
from app.models.order import Order
from app.schemas.merchant import (
    MerchantApplicationCreate, MerchantUpdate, ReferralLinkCreate, PayoutRequest
)
from app.core.security import SecurityUtils
from app.core.config import settings
from app.utils.helpers import paginate_query, slugify


class MerchantService:
    """Service for merchant management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Merchant Application Management
    def apply_for_merchant(self, user_id: int, application_data: MerchantApplicationCreate) -> MerchantApplication:
        """Submit merchant application"""
        # Check if user already has an application or is already a merchant
        existing = self.db.query(MerchantApplication).filter(MerchantApplication.user_id == user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a merchant application on file"
            )
        
        existing_merchant = self.db.query(Merchant).filter(Merchant.user_id == user_id).first()
        if existing_merchant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a merchant"
            )
        
        # Create application
        application = MerchantApplication(
            user_id=user_id,
            application_data=application_data.dict(),
            status=MerchantStatus.PENDING.value
        )
        
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def review_application(self, application_id: int, reviewer_id: int, approved: bool, notes: str = None, **kwargs) -> Merchant:
        """Review and approve/reject merchant application"""
        application = self.db.query(MerchantApplication).filter(MerchantApplication.id == application_id).first()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        if application.status != MerchantStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application has already been reviewed"
            )
        
        application.reviewed_by = reviewer_id
        application.review_notes = notes
        application.reviewed_at = datetime.utcnow()
        
        if approved:
            # Create merchant profile
            merchant = self._create_merchant_from_application(application, **kwargs)
            application.status = MerchantStatus.APPROVED.value
            application.merchant_id = merchant.id
            
            self.db.commit()
            self.db.refresh(merchant)
            return merchant
        else:
            application.status = MerchantStatus.REJECTED.value
            self.db.commit()
            return None
    
    def _create_merchant_from_application(self, application: MerchantApplication, **kwargs) -> Merchant:
        """Create merchant profile from approved application"""
        app_data = application.application_data
        
        # Generate unique referral code
        referral_code = self._generate_referral_code()
        
        merchant = Merchant(
            user_id=application.user_id,
            business_name=app_data["business_name"],
            business_type=app_data.get("business_type"),
            business_description=app_data.get("business_description"),
            contact_person=app_data.get("contact_person"),
            business_email=app_data.get("business_email"),
            business_phone=app_data.get("business_phone"),
            business_address=app_data.get("business_address"),
            tax_id=app_data.get("tax_id"),
            business_license=app_data.get("business_license"),
            referral_code=referral_code,
            commission_rate=kwargs.get("commission_rate", 0.05),
            points_per_referral=kwargs.get("points_per_referral", settings.REFERRAL_POINTS),
            status=MerchantStatus.APPROVED.value,
            payout_method=app_data.get("payout_method"),
            payout_details=app_data.get("payout_details"),
            application_notes=app_data.get("application_notes"),
            approved_at=datetime.utcnow()
        )
        
        self.db.add(merchant)
        return merchant
    
    def _generate_referral_code(self) -> str:
        """Generate unique referral code"""
        while True:
            code = SecurityUtils.generate_referral_code(8)
            existing = self.db.query(Merchant).filter(Merchant.referral_code == code).first()
            if not existing:
                return code
    
    # Merchant Profile Management
    def get_merchant_by_user_id(self, user_id: int) -> Optional[Merchant]:
        """Get merchant by user ID"""
        return self.db.query(Merchant).filter(Merchant.user_id == user_id).first()
    
    def get_merchant_by_id(self, merchant_id: int) -> Optional[Merchant]:
        """Get merchant by ID"""
        return self.db.query(Merchant).filter(Merchant.id == merchant_id).first()
    
    def get_merchant_by_code(self, referral_code: str) -> Optional[Merchant]:
        """Get merchant by referral code"""
        return self.db.query(Merchant).filter(Merchant.referral_code == referral_code.upper()).first()
    
    def update_merchant(self, merchant_id: int, merchant_data: MerchantUpdate) -> Merchant:
        """Update merchant profile"""
        merchant = self.get_merchant_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        # Update fields
        update_data = merchant_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(merchant, field, value)
        
        self.db.commit()
        self.db.refresh(merchant)
        
        return merchant
    
    # Referral Tracking
    def track_referral_click(self, referral_code: str, user_data: Dict[str, Any]) -> str:
        """Track a referral click and return tracking token"""
        merchant = self.get_merchant_by_code(referral_code)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid referral code"
            )
        
        if not merchant.is_approved or not merchant.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Merchant is not active"
            )
        
        # Generate unique tracking token
        tracking_token = f"ref_{uuid.uuid4().hex[:12]}"
        
        # Create referral record
        referral = MerchantReferral(
            merchant_id=merchant.id,
            referral_token=tracking_token,
            referred_email=user_data.get("email"),
            commission_rate=merchant.commission_rate,
            referral_source=user_data.get("source"),
            landing_page=user_data.get("landing_page"),
            user_agent=user_data.get("user_agent"),
            ip_address=user_data.get("ip_address"),
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30-day expiry
        )
        
        # Update merchant stats
        merchant.add_referral_attempt()
        
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        
        return tracking_token
    
    def process_referral_registration(self, user_id: int, email: str, tracking_token: str = None):
        """Process user registration from referral"""
        if not tracking_token:
            return  # No referral tracking
        
        referral = self.db.query(MerchantReferral).filter(
            MerchantReferral.referral_token == tracking_token,
            MerchantReferral.status == ReferralStatus.PENDING.value
        ).first()
        
        if not referral or referral.is_expired:
            return  # Invalid or expired referral
        
        # Mark referral as registered
        referral.mark_registered(user_id)
        self.db.commit()
    
    def process_referral_purchase(self, order_id: int) -> Optional[MerchantReferral]:
        """Process first purchase from referred user and award commission"""
        # Get order details
        order = self.db.query(Order).options(joinedload(Order.user)).filter(Order.id == order_id).first()
        if not order:
            return None
        
        # Find active referral for this user
        referral = self.db.query(MerchantReferral).filter(
            MerchantReferral.referred_user_id == order.user_id,
            MerchantReferral.status == ReferralStatus.PENDING.value
        ).first()
        
        if not referral or referral.is_expired:
            return None
        
        # Calculate commission
        commission_amount = order.total_amount * referral.commission_rate
        points_awarded = referral.merchant.points_per_referral
        
        # Mark referral as converted
        referral.mark_converted(order_id, commission_amount, points_awarded)
        
        # Update merchant earnings
        merchant = referral.merchant
        merchant.add_earnings(commission_amount, points_awarded)
        
        # Award points to merchant user
        merchant_user = merchant.user
        if merchant_user.profile:
            merchant_user.profile.add_points(
                points_awarded,
                f"Referral commission from order {order.order_number}"
            )
        
        self.db.commit()
        self.db.refresh(referral)
        
        return referral
    
    # Referral Links Management
    def create_referral_link(self, merchant_id: int, link_data: ReferralLinkCreate) -> ReferralLink:
        """Create custom referral link"""
        merchant = self.get_merchant_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        # Generate unique slug
        base_slug = slugify(link_data.name)[:20]
        slug = base_slug
        counter = 1
        
        while self.db.query(ReferralLink).filter(ReferralLink.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        referral_link = ReferralLink(
            merchant_id=merchant_id,
            name=link_data.name,
            slug=slug,
            target_url=link_data.target_url,
            campaign_name=link_data.campaign_name,
            campaign_source=link_data.campaign_source,
            campaign_medium=link_data.campaign_medium,
            expires_at=link_data.expires_at
        )
        
        self.db.add(referral_link)
        self.db.commit()
        self.db.refresh(referral_link)
        
        return referral_link
    
    def get_merchant_referral_links(self, merchant_id: int) -> List[ReferralLink]:
        """Get all referral links for merchant"""
        return self.db.query(ReferralLink).filter(
            ReferralLink.merchant_id == merchant_id
        ).order_by(desc(ReferralLink.created_at)).all()
    
    def track_link_click(self, slug: str, is_unique: bool = False) -> ReferralLink:
        """Track click on referral link"""
        link = self.db.query(ReferralLink).filter(ReferralLink.slug == slug).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral link not found"
            )
        
        link.record_click(is_unique)
        self.db.commit()
        
        return link
    
    # Payout Management
    def request_payout(self, merchant_id: int, payout_data: PayoutRequest) -> MerchantPayout:
        """Request payout for merchant"""
        merchant = self.get_merchant_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        if not merchant.can_request_payout:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient earnings for payout. Minimum: {merchant.minimum_payout}, Available: {merchant.pending_earnings}"
            )
        
        # Determine payout amount
        payout_amount = payout_data.amount if payout_data.amount else merchant.pending_earnings
        
        if payout_amount > merchant.pending_earnings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payout amount exceeds pending earnings"
            )
        
        # Create payout request
        payout = MerchantPayout(
            merchant_id=merchant_id,
            amount=payout_amount,
            payout_method=payout_data.payout_method or merchant.payout_method,
            payout_details=merchant.payout_details
        )
        
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        
        return payout
    
    def process_payout(self, payout_id: int, processor_id: int, success: bool, transaction_id: str = None, notes: str = None) -> MerchantPayout:
        """Process payout (admin action)"""
        payout = self.db.query(MerchantPayout).filter(MerchantPayout.id == payout_id).first()
        if not payout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payout not found"
            )
        
        payout.processed_by = processor_id
        payout.processing_notes = notes
        payout.processed_at = datetime.utcnow()
        
        if success:
            payout.mark_completed(transaction_id)
        else:
            payout.mark_failed(notes or "Payout processing failed")
        
        self.db.commit()
        self.db.refresh(payout)
        
        return payout
    
    # Analytics and Reporting
    def get_merchant_analytics(self, merchant_id: int, days: int = 30) -> Dict[str, Any]:
        """Get merchant performance analytics"""
        merchant = self.get_merchant_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        # Calculate date ranges
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # This month vs last month
        current_month_start = end_date.replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        # Referrals this month
        referrals_this_month = self.db.query(MerchantReferral).filter(
            MerchantReferral.merchant_id == merchant_id,
            MerchantReferral.created_at >= current_month_start,
            MerchantReferral.status == ReferralStatus.COMPLETED.value
        ).count()
        
        # Referrals last month
        referrals_last_month = self.db.query(MerchantReferral).filter(
            MerchantReferral.merchant_id == merchant_id,
            MerchantReferral.created_at >= last_month_start,
            MerchantReferral.created_at < current_month_start,
            MerchantReferral.status == ReferralStatus.COMPLETED.value
        ).count()
        
        # Earnings this month
        earnings_this_month = self.db.query(func.sum(MerchantReferral.commission_amount)).filter(
            MerchantReferral.merchant_id == merchant_id,
            MerchantReferral.created_at >= current_month_start,
            MerchantReferral.status == ReferralStatus.COMPLETED.value
        ).scalar() or 0.0
        
        # Earnings last month
        earnings_last_month = self.db.query(func.sum(MerchantReferral.commission_amount)).filter(
            MerchantReferral.merchant_id == merchant_id,
            MerchantReferral.created_at >= last_month_start,
            MerchantReferral.created_at < current_month_start,
            MerchantReferral.status == ReferralStatus.COMPLETED.value
        ).scalar() or 0.0
        
        # Top performing referral links
        top_links = self.db.query(ReferralLink).filter(
            ReferralLink.merchant_id == merchant_id
        ).order_by(desc(ReferralLink.conversions)).limit(5).all()
        
        # Recent referrals
        recent_referrals = self.db.query(MerchantReferral).options(
            joinedload(MerchantReferral.referred_user),
            joinedload(MerchantReferral.order)
        ).filter(
            MerchantReferral.merchant_id == merchant_id
        ).order_by(desc(MerchantReferral.created_at)).limit(10).all()
        
        return {
            "total_referrals": merchant.total_referrals,
            "successful_referrals": merchant.successful_referrals,
            "conversion_rate": merchant.conversion_rate,
            "total_earnings": merchant.total_earnings,
            "pending_earnings": merchant.pending_earnings,
            "referrals_this_month": referrals_this_month,
            "earnings_this_month": float(earnings_this_month),
            "referrals_last_month": referrals_last_month,
            "earnings_last_month": float(earnings_last_month),
            "top_referral_links": [
                {
                    "name": link.name,
                    "clicks": link.click_count,
                    "conversions": link.conversions,
                    "conversion_rate": link.conversion_rate
                }
                for link in top_links
            ],
            "recent_referrals": recent_referrals
        }
    
    def get_admin_merchant_stats(self) -> Dict[str, Any]:
        """Get merchant system statistics for admin"""
        total_merchants = self.db.query(Merchant).count()
        active_merchants = self.db.query(Merchant).filter(
            Merchant.status == MerchantStatus.APPROVED.value,
            Merchant.is_active == True
        ).count()
        
        pending_applications = self.db.query(MerchantApplication).filter(
            MerchantApplication.status == MerchantStatus.PENDING.value
        ).count()
        
        total_referrals = self.db.query(MerchantReferral).count()
        successful_referrals = self.db.query(MerchantReferral).filter(
            MerchantReferral.status == ReferralStatus.COMPLETED.value
        ).count()
        
        total_commission_paid = self.db.query(func.sum(MerchantPayout.amount)).filter(
            MerchantPayout.status == PayoutStatus.COMPLETED.value
        ).scalar() or 0.0
        
        pending_payouts = self.db.query(func.sum(MerchantPayout.amount)).filter(
            MerchantPayout.status == PayoutStatus.PENDING.value
        ).scalar() or 0.0
        
        return {
            "total_merchants": total_merchants,
            "active_merchants": active_merchants,
            "pending_applications": pending_applications,
            "total_referrals": total_referrals,
            "successful_referrals": successful_referrals,
            "total_commission_paid": float(total_commission_paid),
            "pending_payouts": float(pending_payouts)
        }
    
    # Utility Methods
    def get_merchants(self, page: int = 1, per_page: int = 20, status: str = None) -> Dict[str, Any]:
        """Get paginated list of merchants"""
        query = self.db.query(Merchant).options(joinedload(Merchant.user))
        
        if status:
            query = query.filter(Merchant.status == status)
        
        query = query.order_by(desc(Merchant.created_at))
        
        return paginate_query(query, page, per_page)
    
    def get_merchant_referrals(self, merchant_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get paginated list of merchant referrals"""
        query = self.db.query(MerchantReferral).options(
            joinedload(MerchantReferral.referred_user),
            joinedload(MerchantReferral.order)
        ).filter(MerchantReferral.merchant_id == merchant_id)
        
        query = query.order_by(desc(MerchantReferral.created_at))
        
        return paginate_query(query, page, per_page)
    
    def get_merchant_payouts(self, merchant_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get paginated list of merchant payouts"""
        query = self.db.query(MerchantPayout).filter(MerchantPayout.merchant_id == merchant_id)
        query = query.order_by(desc(MerchantPayout.requested_at))
        
        return paginate_query(query, page, per_page)