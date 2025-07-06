# app/models/merchant.py - Created by setup script
"""
CorePath Impact Merchant & Referral Models
Database models for merchant system and referral tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

from app.core.database import Base


class MerchantStatus(PyEnum):
    """Merchant status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class ReferralStatus(PyEnum):
    """Referral status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PayoutStatus(PyEnum):
    """Payout status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Merchant(Base):
    """Merchant model for referral partners"""
    __tablename__ = "merchants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Business information
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(100), nullable=True)  # individual, company, ngo, etc.
    business_description = Column(Text, nullable=True)
    
    # Contact information
    contact_person = Column(String(200), nullable=True)
    business_email = Column(String(255), nullable=True)
    business_phone = Column(String(20), nullable=True)
    
    # Business address
    business_address = Column(JSON, nullable=True)
    
    # Tax and legal information
    tax_id = Column(String(100), nullable=True)
    business_license = Column(String(200), nullable=True)
    
    # Merchant configuration
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    commission_rate = Column(Float, default=0.05)  # 5% default commission
    points_per_referral = Column(Integer, default=500)  # 500 points per referral
    
    # Status and approval
    status = Column(String(20), default=MerchantStatus.PENDING.value)
    is_active = Column(Boolean, default=True)
    
    # Application details
    application_notes = Column(Text, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Performance metrics
    total_referrals = Column(Integer, default=0)
    successful_referrals = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    total_points_earned = Column(Integer, default=0)
    
    # Payout information
    payout_method = Column(String(50), nullable=True)  # bank, mobile_money, etc.
    payout_details = Column(JSON, nullable=True)  # Bank account, M-Pesa number, etc.
    minimum_payout = Column(Float, default=100.0)  # Minimum payout amount
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    last_referral_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="merchant_profile")
    referrals = relationship("MerchantReferral", back_populates="merchant", cascade="all, delete-orphan")
    payouts = relationship("MerchantPayout", back_populates="merchant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Merchant(id={self.id}, business_name='{self.business_name}', code='{self.referral_code}')>"
    
    @property
    def is_approved(self) -> bool:
        """Check if merchant is approved"""
        return self.status == MerchantStatus.APPROVED.value
    
    @property
    def conversion_rate(self) -> float:
        """Calculate referral conversion rate"""
        if self.total_referrals == 0:
            return 0.0
        return (self.successful_referrals / self.total_referrals) * 100
    
    @property
    def pending_earnings(self) -> float:
        """Calculate pending earnings (not yet paid out)"""
        total_paid = sum(payout.amount for payout in self.payouts if payout.status == PayoutStatus.COMPLETED.value)
        return max(0, self.total_earnings - total_paid)
    
    @property
    def can_request_payout(self) -> bool:
        """Check if merchant can request payout"""
        return (
            self.is_approved and 
            self.is_active and 
            self.pending_earnings >= self.minimum_payout
        )
    
    def add_earnings(self, amount: float, points: int = 0):
        """Add earnings from a successful referral"""
        self.total_earnings += amount
        self.total_points_earned += points
        self.successful_referrals += 1
        self.last_referral_at = datetime.utcnow()
    
    def add_referral_attempt(self):
        """Record a referral attempt"""
        self.total_referrals += 1


class MerchantReferral(Base):
    """Track individual referrals made by merchants"""
    __tablename__ = "merchant_referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    
    # Referral tracking
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null until user registers
    referred_email = Column(String(255), nullable=True)  # Track email before registration
    referral_token = Column(String(100), unique=True, nullable=False, index=True)  # Unique tracking token
    
    # Order tracking
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Linked order for commission
    
    # Commission details
    commission_amount = Column(Float, default=0.0)
    points_awarded = Column(Integer, default=0)
    commission_rate = Column(Float, nullable=False)  # Rate at time of referral
    
    # Status and tracking
    status = Column(String(20), default=ReferralStatus.PENDING.value)
    
    # Source tracking
    referral_source = Column(String(100), nullable=True)  # website, social, email, etc.
    landing_page = Column(String(500), nullable=True)  # Where user landed
    user_agent = Column(String(500), nullable=True)  # Browser info
    ip_address = Column(String(45), nullable=True)
    
    # Conversion tracking
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_at = Column(DateTime(timezone=True), nullable=True)
    first_purchase_at = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration (referrals expire after 30 days if no purchase)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    merchant = relationship("Merchant", back_populates="referrals")
    referred_user = relationship("User", foreign_keys=[referred_user_id], backref="merchant_referrals")
    order = relationship("Order", backref="merchant_referral")
    
    def __repr__(self):
        return f"<MerchantReferral(id={self.id}, merchant_id={self.merchant_id}, status='{self.status}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if referral has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until referral expires"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def conversion_time(self) -> int:
        """Calculate time from click to purchase in hours"""
        if not self.first_purchase_at:
            return 0
        delta = self.first_purchase_at - self.clicked_at
        return int(delta.total_seconds() / 3600)
    
    def mark_registered(self, user_id: int):
        """Mark referral as registered"""
        self.referred_user_id = user_id
        self.registered_at = datetime.utcnow()
    
    def mark_converted(self, order_id: int, commission_amount: float, points: int):
        """Mark referral as converted with first purchase"""
        self.order_id = order_id
        self.commission_amount = commission_amount
        self.points_awarded = points
        self.status = ReferralStatus.COMPLETED.value
        self.first_purchase_at = datetime.utcnow()


class MerchantPayout(Base):
    """Track merchant payouts"""
    __tablename__ = "merchant_payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    
    # Payout details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="KES")
    
    # Status and processing
    status = Column(String(20), default=PayoutStatus.PENDING.value)
    
    # Payment method and details
    payout_method = Column(String(50), nullable=False)  # bank, mobile_money, etc.
    payout_details = Column(JSON, nullable=True)  # Account details
    
    # External tracking
    external_transaction_id = Column(String(200), nullable=True)
    processor_reference = Column(String(200), nullable=True)
    
    # Processing information
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who processed
    processing_notes = Column(Text, nullable=True)
    failure_reason = Column(String(500), nullable=True)
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="payouts")
    processed_by_user = relationship("User", foreign_keys=[processed_by])
    
    def __repr__(self):
        return f"<MerchantPayout(id={self.id}, merchant_id={self.merchant_id}, amount={self.amount})>"
    
    def mark_completed(self, transaction_id: str = None):
        """Mark payout as completed"""
        self.status = PayoutStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        if transaction_id:
            self.external_transaction_id = transaction_id
    
    def mark_failed(self, reason: str):
        """Mark payout as failed"""
        self.status = PayoutStatus.FAILED.value
        self.failure_reason = reason
        self.processed_at = datetime.utcnow()


class ReferralLink(Base):
    """Track custom referral links created by merchants"""
    __tablename__ = "referral_links"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False)
    
    # Link details
    name = Column(String(200), nullable=False)  # Link name for merchant tracking
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL slug
    target_url = Column(String(500), nullable=False)  # Where to redirect
    
    # Tracking parameters
    campaign_name = Column(String(200), nullable=True)
    campaign_source = Column(String(100), nullable=True)  # facebook, email, etc.
    campaign_medium = Column(String(100), nullable=True)  # social, cpc, etc.
    
    # Performance tracking
    click_count = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    merchant = relationship("Merchant", backref="referral_links")
    
    def __repr__(self):
        return f"<ReferralLink(id={self.id}, slug='{self.slug}', clicks={self.click_count})>"
    
    @property
    def conversion_rate(self) -> float:
        """Calculate link conversion rate"""
        if self.unique_clicks == 0:
            return 0.0
        return (self.conversions / self.unique_clicks) * 100
    
    @property
    def full_url(self) -> str:
        """Get full referral URL"""
        return f"https://corepathimpact.com/ref/{self.slug}"
    
    def record_click(self, is_unique: bool = False):
        """Record a click on this referral link"""
        self.click_count += 1
        if is_unique:
            self.unique_clicks += 1
    
    def record_conversion(self):
        """Record a conversion from this link"""
        self.conversions += 1


class MerchantApplication(Base):
    """Track merchant application details and documents"""
    __tablename__ = "merchant_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=True)  # Set after approval
    
    # Application data (JSON store for flexibility)
    application_data = Column(JSON, nullable=False)
    
    # Documents
    documents = Column(JSON, nullable=True)  # Store document URLs and metadata
    
    # Review process
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), default=MerchantStatus.PENDING.value)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    applicant = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    merchant = relationship("Merchant", backref="application")
    
    def __repr__(self):
        return f"<MerchantApplication(id={self.id}, user_id={self.user_id}, status='{self.status}')>"