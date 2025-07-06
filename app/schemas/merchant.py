"""
CorePath Impact Merchant Schemas
Pydantic models for merchant and referral requests/responses
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Merchant Application Schemas
class MerchantApplicationCreate(BaseModel):
    """Merchant application creation schema"""
    business_name: str = Field(..., min_length=2, max_length=200, description="Business name")
    business_type: str = Field(..., description="Business type (individual, company, ngo, etc.)")
    business_description: Optional[str] = Field(None, max_length=1000, description="Business description")
    
    # Contact information
    contact_person: Optional[str] = Field(None, max_length=200, description="Contact person name")
    business_email: Optional[EmailStr] = Field(None, description="Business email address")
    business_phone: Optional[str] = Field(None, max_length=20, description="Business phone number")
    
    # Business address
    business_address: Optional[Dict[str, str]] = Field(None, description="Business address")
    
    # Legal information
    tax_id: Optional[str] = Field(None, max_length=100, description="Tax ID/Business registration number")
    business_license: Optional[str] = Field(None, max_length=200, description="Business license number")
    
    # Payout preferences
    payout_method: Optional[str] = Field("bank", description="Preferred payout method")
    payout_details: Optional[Dict[str, str]] = Field(None, description="Payout account details")
    
    # Application notes
    application_notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @validator('business_name')
    def validate_business_name(cls, v):
        if not v.strip():
            raise ValueError('Business name cannot be empty')
        return v.strip()
    
    @validator('business_type')
    def validate_business_type(cls, v):
        allowed_types = ['individual', 'company', 'ngo', 'church', 'school', 'other']
        if v.lower() not in allowed_types:
            raise ValueError(f'Business type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "business_name": "ABC Parenting Solutions",
                "business_type": "company",
                "business_description": "We provide parenting workshops and consultations",
                "contact_person": "Jane Smith",
                "business_email": "jane@abcparenting.com",
                "business_phone": "+254712345678",
                "business_address": {
                    "street": "123 Business Avenue",
                    "city": "Nairobi",
                    "postal_code": "00100",
                    "country": "Kenya"
                },
                "tax_id": "P051234567M",
                "payout_method": "bank",
                "payout_details": {
                    "bank_name": "KCB Bank",
                    "account_number": "1234567890",
                    "account_name": "ABC Parenting Solutions"
                },
                "application_notes": "I run parenting workshops and would like to refer families to VDC toolkits"
            }
        }


class MerchantApplicationResponse(BaseModel):
    """Merchant application response schema"""
    id: int
    user_id: int
    business_name: str
    business_type: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    
    class Config:
        from_attributes = True


class MerchantUpdate(BaseModel):
    """Merchant profile update schema"""
    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_description: Optional[str] = Field(None, max_length=1000)
    contact_person: Optional[str] = Field(None, max_length=200)
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = Field(None, max_length=20)
    business_address: Optional[Dict[str, str]] = None
    payout_method: Optional[str] = None
    payout_details: Optional[Dict[str, str]] = None


class MerchantResponse(BaseModel):
    """Merchant profile response schema"""
    id: int
    user_id: int
    business_name: str
    business_type: Optional[str]
    business_description: Optional[str]
    contact_person: Optional[str]
    business_email: Optional[str]
    business_phone: Optional[str]
    business_address: Optional[Dict[str, Any]]
    
    # Merchant configuration
    referral_code: str
    commission_rate: float
    points_per_referral: int
    
    # Status
    status: str
    is_active: bool
    is_approved: bool
    
    # Performance metrics
    total_referrals: int
    successful_referrals: int
    conversion_rate: float
    total_earnings: float
    total_points_earned: int
    pending_earnings: float
    can_request_payout: bool
    
    # Payout info
    payout_method: Optional[str]
    minimum_payout: float
    
    # Timestamps
    created_at: datetime
    approved_at: Optional[datetime]
    last_referral_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "business_name": "ABC Parenting Solutions",
                "business_type": "company",
                "referral_code": "ABC12345",
                "commission_rate": 0.05,
                "points_per_referral": 500,
                "status": "approved",
                "is_active": True,
                "is_approved": True,
                "total_referrals": 25,
                "successful_referrals": 12,
                "conversion_rate": 48.0,
                "total_earnings": 240.0,
                "total_points_earned": 6000,
                "pending_earnings": 180.0,
                "can_request_payout": True,
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


# Referral Schemas
class ReferralLinkCreate(BaseModel):
    """Referral link creation schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Link name for tracking")
    target_url: str = Field(..., description="Target URL to redirect to")
    campaign_name: Optional[str] = Field(None, max_length=200, description="Campaign name")
    campaign_source: Optional[str] = Field(None, max_length=100, description="Traffic source")
    campaign_medium: Optional[str] = Field(None, max_length=100, description="Marketing medium")
    expires_at: Optional[datetime] = Field(None, description="Link expiration date")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Facebook Campaign - January 2025",
                "target_url": "https://corepathimpact.com/products/vdc-toolkit",
                "campaign_name": "New Year Parenting",
                "campaign_source": "facebook",
                "campaign_medium": "social"
            }
        }


class ReferralLinkResponse(BaseModel):
    """Referral link response schema"""
    id: int
    name: str
    slug: str
    target_url: str
    full_url: str
    campaign_name: Optional[str]
    campaign_source: Optional[str]
    campaign_medium: Optional[str]
    
    # Performance metrics
    click_count: int
    unique_clicks: int
    conversions: int
    conversion_rate: float
    
    # Status
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReferralResponse(BaseModel):
    """Individual referral response schema"""
    id: int
    merchant_id: int
    referral_token: str
    referred_email: Optional[str]
    referred_user_id: Optional[int]
    order_id: Optional[int]
    
    # Commission details
    commission_amount: float
    points_awarded: int
    commission_rate: float
    
    # Status and tracking
    status: str
    referral_source: Optional[str]
    
    # Timing
    clicked_at: datetime
    registered_at: Optional[datetime]
    first_purchase_at: Optional[datetime]
    expires_at: datetime
    days_until_expiry: int
    conversion_time: int
    
    # Related data
    referred_user_name: Optional[str]
    order_number: Optional[str]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "merchant_id": 1,
                "referral_token": "ref_abc123xyz",
                "referred_email": "newcustomer@example.com",
                "commission_amount": 20.0,
                "points_awarded": 500,
                "status": "completed",
                "clicked_at": "2025-01-07T10:00:00Z",
                "registered_at": "2025-01-07T10:15:00Z",
                "first_purchase_at": "2025-01-07T11:30:00Z",
                "days_until_expiry": 25,
                "conversion_time": 1
            }
        }


# Payout Schemas
class PayoutRequest(BaseModel):
    """Payout request schema"""
    amount: Optional[float] = Field(None, gt=0, description="Amount to payout (defaults to pending earnings)")
    payout_method: Optional[str] = Field(None, description="Payout method (defaults to merchant preference)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    class Config:
        schema_extra = {
            "example": {
                "amount": 180.0,
                "payout_method": "bank",
                "notes": "Regular monthly payout"
            }
        }


class PayoutResponse(BaseModel):
    """Payout response schema"""
    id: int
    merchant_id: int
    amount: float
    currency: str
    status: str
    payout_method: str
    
    # Processing info
    external_transaction_id: Optional[str]
    processor_reference: Optional[str]
    processing_notes: Optional[str]
    failure_reason: Optional[str]
    
    # Timestamps
    requested_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Analytics Schemas
class MerchantAnalytics(BaseModel):
    """Merchant analytics response schema"""
    # Overview metrics
    total_referrals: int
    successful_referrals: int
    conversion_rate: float
    total_earnings: float
    pending_earnings: float
    
    # Performance over time
    referrals_this_month: int
    earnings_this_month: float
    referrals_last_month: int
    earnings_last_month: float
    
    # Top performing links
    top_referral_links: List[Dict[str, Any]]
    
    # Recent activity
    recent_referrals: List[ReferralResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "total_referrals": 25,
                "successful_referrals": 12,
                "conversion_rate": 48.0,
                "total_earnings": 240.0,
                "pending_earnings": 180.0,
                "referrals_this_month": 8,
                "earnings_this_month": 80.0,
                "referrals_last_month": 5,
                "earnings_last_month": 50.0,
                "top_referral_links": [
                    {
                        "name": "Facebook Campaign",
                        "clicks": 150,
                        "conversions": 8,
                        "conversion_rate": 5.3
                    }
                ],
                "recent_referrals": []
            }
        }


class MerchantDashboard(BaseModel):
    """Merchant dashboard data schema"""
    merchant: MerchantResponse
    analytics: MerchantAnalytics
    referral_links: List[ReferralLinkResponse]
    recent_payouts: List[PayoutResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "merchant": {},
                "analytics": {},
                "referral_links": [],
                "recent_payouts": []
            }
        }


# Admin Schemas
class MerchantApplicationReview(BaseModel):
    """Admin review of merchant application"""
    status: str = Field(..., regex="^(approved|rejected)$", description="Review decision")
    review_notes: Optional[str] = Field(None, max_length=1000, description="Review notes")
    commission_rate: Optional[float] = Field(None, ge=0, le=1, description="Custom commission rate")
    points_per_referral: Optional[int] = Field(None, ge=0, description="Custom points per referral")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "approved",
                "review_notes": "Great application with solid business plan",
                "commission_rate": 0.05,
                "points_per_referral": 500
            }
        }


class AdminMerchantStats(BaseModel):
    """Admin merchant statistics"""
    total_merchants: int
    active_merchants: int
    pending_applications: int
    total_referrals: int
    successful_referrals: int
    total_commission_paid: float
    pending_payouts: float
    
    class Config:
        schema_extra = {
            "example": {
                "total_merchants": 45,
                "active_merchants": 38,
                "pending_applications": 7,
                "total_referrals": 1250,
                "successful_referrals": 480,
                "total_commission_paid": 12500.0,
                "pending_payouts": 3400.0
            }
        }


# Pagination Schemas
class PaginatedMerchantResponse(BaseModel):
    """Paginated merchant list response"""
    items: List[MerchantResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 45,
                "page": 1,
                "per_page": 20,
                "pages": 3,
                "has_prev": False,
                "has_next": True
            }
        }


class PaginatedReferralResponse(BaseModel):
    """Paginated referral list response"""
    items: List[ReferralResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 125,
                "page": 1,
                "per_page": 20,
                "pages": 7,
                "has_prev": False,
                "has_next": True
            }
        }


class PaginatedPayoutResponse(BaseModel):
    """Paginated payout list response"""
    items: List[PayoutResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 28,
                "page": 1,
                "per_page": 20,
                "pages": 2,
                "has_prev": False,
                "has_next": True
            }
        }