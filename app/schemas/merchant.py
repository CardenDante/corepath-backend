# app/schemas/merchant.py - Phase 4 Merchant Schemas
"""
CorePath Impact Merchant Schemas
Request/Response models for merchant system
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, Field


# Base merchant schemas
class MerchantBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    business_description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=200)
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = None


class MerchantApplicationCreate(MerchantBase):
    """Schema for merchant application submission"""
    business_address: Optional[Dict[str, Any]] = None
    tax_id: Optional[str] = Field(None, max_length=100)
    business_license: Optional[str] = Field(None, max_length=200)
    payout_method: Optional[str] = Field(None, max_length=50)
    payout_details: Optional[Dict[str, Any]] = None
    application_notes: Optional[str] = None
    
    @validator('business_phone')
    def validate_phone(cls, v):
        if v:
            from app.utils.helpers import validate_kenyan_phone
            if not validate_kenyan_phone(v):
                raise ValueError('Invalid phone number format')
        return v


class MerchantUpdate(BaseModel):
    """Schema for updating merchant profile"""
    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=200)
    business_email: Optional[EmailStr] = None
    business_phone: Optional[str] = None
    business_address: Optional[Dict[str, Any]] = None
    payout_method: Optional[str] = Field(None, max_length=50)
    payout_details: Optional[Dict[str, Any]] = None


class MerchantResponse(MerchantBase):
    """Schema for merchant profile response"""
    id: int
    user_id: int
    referral_code: str
    commission_rate: float
    points_per_referral: int
    status: str
    is_active: bool
    total_referrals: int
    successful_referrals: int
    total_earnings: float
    total_points_earned: int
    pending_earnings: float
    conversion_rate: float
    minimum_payout: float
    created_at: datetime
    approved_at: Optional[datetime]
    last_referral_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Referral schemas
class ReferralResponse(BaseModel):
    """Schema for referral response"""
    id: int
    merchant_id: int
    referred_user_id: Optional[int]
    referred_email: Optional[str]
    referral_token: str
    commission_amount: float
    points_awarded: int
    status: str
    referral_source: Optional[str]
    clicked_at: datetime
    registered_at: Optional[datetime]
    first_purchase_at: Optional[datetime]
    expires_at: datetime
    is_expired: bool
    conversion_time: Optional[int]
    
    class Config:
        from_attributes = True


# Referral link schemas
class ReferralLinkCreate(BaseModel):
    """Schema for creating referral links"""
    name: str = Field(..., min_length=1, max_length=200)
    target_url: str = Field(..., max_length=500)
    campaign_name: Optional[str] = Field(None, max_length=200)
    campaign_source: Optional[str] = Field(None, max_length=100)
    campaign_medium: Optional[str] = Field(None, max_length=100)
    expires_at: Optional[datetime] = None


class ReferralLinkResponse(BaseModel):
    """Schema for referral link response"""
    id: int
    merchant_id: int
    name: str
    slug: str
    target_url: str
    campaign_name: Optional[str]
    campaign_source: Optional[str]
    campaign_medium: Optional[str]
    click_count: int
    unique_clicks: int
    conversions: int
    conversion_rate: float
    is_active: bool
    expires_at: Optional[datetime]
    full_url: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Payout schemas
class PayoutRequest(BaseModel):
    """Schema for payout request"""
    amount: Optional[float] = Field(None, ge=1)
    payout_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class PayoutResponse(BaseModel):
    """Schema for payout response"""
    id: int
    merchant_id: int
    amount: float
    currency: str
    status: str
    payout_method: str
    requested_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]
    external_transaction_id: Optional[str]
    processing_notes: Optional[str]
    failure_reason: Optional[str]
    
    class Config:
        from_attributes = True


# Analytics schemas
class MerchantAnalytics(BaseModel):
    """Schema for merchant analytics"""
    total_referrals: int
    successful_referrals: int
    conversion_rate: float
    total_earnings: float
    pending_earnings: float
    referrals_this_month: int
    earnings_this_month: float
    referrals_last_month: int
    earnings_last_month: float
    top_referral_links: List[Dict[str, Any]]
    recent_referrals: List[ReferralResponse]


# Application schemas
class MerchantApplicationResponse(BaseModel):
    """Schema for merchant application response"""
    id: int
    user_id: int
    status: str
    application_data: Dict[str, Any]
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    
    class Config:
        from_attributes = True


# Admin schemas
class MerchantStatsResponse(BaseModel):
    """Schema for merchant system statistics"""
    total_merchants: int
    active_merchants: int
    pending_applications: int
    total_referrals: int
    successful_referrals: int
    total_commission_paid: float
    pending_payouts: float


# Commission calculation schemas
class CommissionCalculation(BaseModel):
    """Schema for commission calculation"""
    order_amount: float
    commission_rate: float
    commission_amount: float
    points_awarded: int
    merchant_code: str


# Tracking schemas
class ReferralTrackingData(BaseModel):
    """Schema for referral tracking data"""
    referral_code: str
    source: Optional[str] = "direct"
    landing_page: Optional[str] = None
    email: Optional[EmailStr] = None


class ReferralTrackingResponse(BaseModel):
    """Schema for referral tracking response"""
    tracking_token: str
    merchant_code: str
    expires_at: datetime


# Merchant search and filter schemas
class MerchantFilters(BaseModel):
    """Schema for merchant search filters"""
    status: Optional[str] = None
    business_type: Optional[str] = None
    min_referrals: Optional[int] = None
    min_earnings: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'created_at', 'business_name', 'total_referrals', 
            'successful_referrals', 'total_earnings', 'conversion_rate'
        ]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


# Bulk operations schemas
class BulkMerchantUpdate(BaseModel):
    """Schema for bulk merchant updates"""
    merchant_ids: List[int] = Field(..., min_items=1)
    updates: Dict[str, Any]


class BulkPayoutProcess(BaseModel):
    """Schema for bulk payout processing"""
    payout_ids: List[int] = Field(..., min_items=1)
    approved: bool
    notes: Optional[str] = None


# Email notification schemas
class MerchantNotification(BaseModel):
    """Schema for merchant notifications"""
    type: str  # application_approved, payout_processed, etc.
    merchant_id: int
    data: Dict[str, Any]
    send_email: bool = True
    send_sms: bool = False


# Report schemas
class MerchantReport(BaseModel):
    """Schema for merchant reports"""
    period_start: datetime
    period_end: datetime
    total_merchants: int
    new_merchants: int
    total_referrals: int
    successful_referrals: int
    total_commission: float
    average_commission: float
    top_performers: List[Dict[str, Any]]


# Integration schemas
class MerchantWebhook(BaseModel):
    """Schema for merchant webhook data"""
    event: str
    merchant_id: int
    data: Dict[str, Any]
    timestamp: datetime


# Export schemas
class MerchantExport(BaseModel):
    """Schema for merchant data export"""
    format: str = "csv"  # csv, excel, json
    filters: Optional[MerchantFilters] = None
    include_referrals: bool = False
    include_payouts: bool = False
    date_range: Optional[Dict[str, datetime]] = None