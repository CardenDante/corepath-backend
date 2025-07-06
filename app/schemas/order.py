# app/schemas/order.py - Fixed for Pydantic v2
"""
CorePath Impact Order Schemas
Pydantic v2 compatible models for orders, cart, and payment requests/responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Address Schemas
class AddressBase(BaseModel):
    """Base address schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    address_line_1: str = Field(..., min_length=1, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class ShippingAddress(AddressBase):
    """Shipping address schema"""
    delivery_instructions: Optional[str] = Field(None, max_length=500)


class BillingAddress(AddressBase):
    """Billing address schema"""
    pass


# Cart Schemas
class CartItemAdd(BaseModel):
    """Add item to cart schema"""
    product_id: int = Field(..., description="Product ID")
    variant_id: Optional[int] = Field(None, description="Product variant ID")
    quantity: int = Field(..., ge=1, le=100, description="Quantity")


class CartItemUpdate(BaseModel):
    """Update cart item schema"""
    quantity: int = Field(..., ge=0, le=100, description="Quantity (0 to remove)")


class CartItemResponse(BaseModel):
    """Cart item response schema"""
    id: int
    product_id: int
    product_name: str
    product_slug: str
    product_image: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    is_available: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Shopping cart response schema"""
    id: int
    user_id: int
    items: List[CartItemResponse]
    subtotal: float
    item_count: int
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Order Schemas
class OrderItemCreate(BaseModel):
    """Order item creation schema"""
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    """Order creation schema"""
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: ShippingAddress
    billing_address: Optional[BillingAddress] = None
    shipping_method: str = Field("standard", description="Shipping method")
    payment_method: str = Field(..., description="Payment method")
    use_points: Optional[int] = Field(None, ge=0, description="Points to use for discount")
    coupon_code: Optional[str] = Field(None, description="Coupon code")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    is_gift: bool = Field(False, description="Is this a gift order")
    gift_message: Optional[str] = Field(None, max_length=500, description="Gift message")
    
    @field_validator('billing_address', mode='before')
    @classmethod
    def set_billing_address(cls, v, info):
        """Set billing address to shipping address if not provided"""
        if v is None and 'shipping_address' in info.data:
            return info.data['shipping_address']
        return v


class OrderUpdate(BaseModel):
    """Order update schema (admin only)"""
    status: Optional[str] = Field(None, pattern="^(pending|processing|shipped|delivered|cancelled|refunded)$")
    tracking_number: Optional[str] = Field(None, max_length=100)
    admin_notes: Optional[str] = Field(None, max_length=1000)
    shipping_method: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Order item response schema"""
    id: int
    product_id: int
    product_name: str
    product_sku: Optional[str] = None
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    product_snapshot: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: int
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_provider: Optional[str] = None
    external_payment_id: Optional[str] = None
    transaction_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Order response schema"""
    id: int
    order_number: str
    user_id: int
    status: str
    
    # Customer information
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    
    # Pricing
    subtotal: float
    tax_amount: float
    shipping_amount: float
    discount_amount: float
    points_discount: float
    total_amount: float
    currency: str
    
    # Addresses
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    
    # Additional info
    shipping_method: str
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    tracking_number: Optional[str] = None
    
    # Points
    points_earned: int
    points_used: int
    
    # Flags
    is_gift: bool
    gift_message: Optional[str] = None
    
    # Status properties
    item_count: int
    is_paid: bool
    payment_status: str
    can_cancel: bool
    can_refund: bool
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Related data
    items: List[OrderItemResponse]
    payments: List[PaymentResponse]
    
    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Order list response schema (simplified)"""
    id: int
    order_number: str
    status: str
    customer_name: str
    customer_email: str
    item_count: int
    total_amount: float
    currency: str
    is_paid: bool
    payment_status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Payment Schemas
class PaymentCreate(BaseModel):
    """Payment creation schema"""
    order_id: int
    payment_method: str = Field(..., description="Payment method (card, mobile_money, etc.)")
    amount: Optional[float] = Field(None, description="Amount (defaults to order total)")


class PaymentIntent(BaseModel):
    """Payment intent response schema"""
    client_secret: str
    amount: float
    currency: str
    payment_method_types: List[str]


# Coupon Schemas
class CouponValidate(BaseModel):
    """Coupon validation schema"""
    code: str = Field(..., min_length=1, max_length=50)
    order_amount: Optional[float] = Field(None, description="Order amount for validation")


class CouponResponse(BaseModel):
    """Coupon response schema"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    minimum_order_amount: Optional[float] = None
    maximum_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    usage_count: int
    is_valid: bool
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class CouponValidationResponse(BaseModel):
    """Coupon validation response schema"""
    is_valid: bool
    discount_amount: float
    message: str
    coupon: Optional[CouponResponse] = None


# Shipping Schemas
class ShippingRate(BaseModel):
    """Shipping rate schema"""
    method: str
    name: str
    description: str
    cost: float
    estimated_days: int


class ShippingCalculation(BaseModel):
    """Shipping calculation request schema"""
    items: List[OrderItemCreate]
    shipping_address: ShippingAddress


# Order Statistics Schemas
class OrderStats(BaseModel):
    """Order statistics schema"""
    total_orders: int
    pending_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: float
    average_order_value: float


class RevenueStats(BaseModel):
    """Revenue statistics schema"""
    daily_revenue: List[Dict[str, Any]]
    weekly_revenue: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]


# Pagination Schemas
class PaginatedOrderResponse(BaseModel):
    """Paginated order list response"""
    items: List[OrderListResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool


# Order Search and Filter Schemas
class OrderFilters(BaseModel):
    """Order search and filter schema"""
    status: Optional[str] = Field(None, description="Filter by order status")
    payment_status: Optional[str] = Field(None, description="Filter by payment status")
    customer_email: Optional[str] = Field(None, description="Filter by customer email")
    date_from: Optional[datetime] = Field(None, description="Filter orders from date")
    date_to: Optional[datetime] = Field(None, description="Filter orders to date")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum order amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum order amount")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    @field_validator('max_amount')
    @classmethod
    def validate_amount_range(cls, v, info):
        if v is not None and 'min_amount' in info.data and info.data['min_amount'] is not None:
            if v < info.data['min_amount']:
                raise ValueError('Max amount must be greater than min amount')
        return v


# Checkout Schemas
class CheckoutSummary(BaseModel):
    """Checkout summary schema"""
    items: List[CartItemResponse]
    subtotal: float
    tax_amount: float
    shipping_amount: float
    discount_amount: float
    points_discount: float
    total_amount: float
    available_shipping_methods: List[ShippingRate]
    points_available: int
    points_value: float


# Error Response Schemas
class OrderErrorResponse(BaseModel):
    """Order error response schema"""
    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None