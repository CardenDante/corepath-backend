# app/schemas/order.py - Created by setup script
"""
CorePath Impact Order Schemas
Pydantic models for orders, cart, and payment requests/responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


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
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "address_line_1": "123 Main Street",
                "city": "Nairobi",
                "state": "Nairobi County",
                "postal_code": "00100",
                "country": "Kenya",
                "phone": "+254712345678"
            }
        }


class BillingAddress(AddressBase):
    """Billing address schema"""
    pass


# Cart Schemas
class CartItemAdd(BaseModel):
    """Add item to cart schema"""
    product_id: int = Field(..., description="Product ID")
    variant_id: Optional[int] = Field(None, description="Product variant ID")
    quantity: int = Field(..., ge=1, le=100, description="Quantity")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "variant_id": None,
                "quantity": 2
            }
        }


class CartItemUpdate(BaseModel):
    """Update cart item schema"""
    quantity: int = Field(..., ge=0, le=100, description="Quantity (0 to remove)")
    
    class Config:
        schema_extra = {
            "example": {
                "quantity": 3
            }
        }


class CartItemResponse(BaseModel):
    """Cart item response schema"""
    id: int
    product_id: int
    product_name: str
    product_slug: str
    product_image: Optional[str]
    variant_id: Optional[int]
    variant_name: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    is_available: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "product_id": 1,
                "product_name": "Early Value Development Toolkit",
                "product_slug": "early-value-development-toolkit",
                "product_image": "/uploads/products/toolkit.jpg",
                "variant_id": None,
                "variant_name": None,
                "quantity": 2,
                "unit_price": 79.99,
                "total_price": 159.98,
                "is_available": True,
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


class CartResponse(BaseModel):
    """Shopping cart response schema"""
    id: int
    user_id: int
    items: List[CartItemResponse]
    subtotal: float
    item_count: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "items": [],
                "subtotal": 159.98,
                "item_count": 2,
                "updated_at": "2025-01-07T10:00:00Z"
            }
        }


# Order Schemas
class OrderItemCreate(BaseModel):
    """Order item creation schema"""
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    """Order creation schema"""
    items: List[OrderItemCreate] = Field(..., min_items=1)
    shipping_address: ShippingAddress
    billing_address: Optional[BillingAddress] = None
    shipping_method: str = Field("standard", description="Shipping method")
    payment_method: str = Field(..., description="Payment method")
    use_points: Optional[int] = Field(None, ge=0, description="Points to use for discount")
    coupon_code: Optional[str] = Field(None, description="Coupon code")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    is_gift: bool = Field(False, description="Is this a gift order")
    gift_message: Optional[str] = Field(None, max_length=500, description="Gift message")
    
    @validator('billing_address', pre=True, always=True)
    def set_billing_address(cls, v, values):
        """Set billing address to shipping address if not provided"""
        if v is None and 'shipping_address' in values:
            return values['shipping_address']
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": 1,
                        "variant_id": None,
                        "quantity": 2
                    }
                ],
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address_line_1": "123 Main Street",
                    "city": "Nairobi",
                    "state": "Nairobi County",
                    "postal_code": "00100",
                    "country": "Kenya",
                    "phone": "+254712345678"
                },
                "shipping_method": "standard",
                "payment_method": "card",
                "use_points": 100,
                "notes": "Please deliver in the morning"
            }
        }


class OrderUpdate(BaseModel):
    """Order update schema (admin only)"""
    status: Optional[str] = Field(None, regex="^(pending|processing|shipped|delivered|cancelled|refunded)$")
    tracking_number: Optional[str] = Field(None, max_length=100)
    admin_notes: Optional[str] = Field(None, max_length=1000)
    shipping_method: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Order item response schema"""
    id: int
    product_id: int
    product_name: str
    product_sku: Optional[str]
    variant_id: Optional[int]
    variant_name: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    product_snapshot: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: int
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_provider: Optional[str]
    external_payment_id: Optional[str]
    transaction_reference: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema"""
    id: int
    order_number: str
    user_id: int
    status: str
    
    # Customer information
    customer_email: str
    customer_name: str
    customer_phone: Optional[str]
    
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
    billing_address: Optional[Dict[str, Any]]
    
    # Additional info
    shipping_method: str
    notes: Optional[str]
    admin_notes: Optional[str]
    tracking_number: Optional[str]
    
    # Points
    points_earned: int
    points_used: int
    
    # Flags
    is_gift: bool
    gift_message: Optional[str]
    
    # Status properties
    item_count: int
    is_paid: bool
    payment_status: str
    can_cancel: bool
    can_refund: bool
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    
    # Related data
    items: List[OrderItemResponse]
    payments: List[PaymentResponse]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "order_number": "CP20250107123456",
                "user_id": 1,
                "status": "pending",
                "customer_email": "john@example.com",
                "customer_name": "John Doe",
                "subtotal": 159.98,
                "tax_amount": 0.0,
                "shipping_amount": 10.0,
                "discount_amount": 0.0,
                "points_discount": 1.0,
                "total_amount": 168.98,
                "currency": "KES",
                "shipping_method": "standard",
                "points_earned": 1,
                "points_used": 100,
                "is_paid": False,
                "payment_status": "pending",
                "can_cancel": True,
                "can_refund": False,
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


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
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "order_number": "CP20250107123456",
                "status": "pending",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "item_count": 2,
                "total_amount": 168.98,
                "currency": "KES",
                "is_paid": False,
                "payment_status": "pending",
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


# Payment Schemas
class PaymentCreate(BaseModel):
    """Payment creation schema"""
    order_id: int
    payment_method: str = Field(..., description="Payment method (card, mobile_money, etc.)")
    amount: Optional[float] = Field(None, description="Amount (defaults to order total)")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "payment_method": "card",
                "amount": 168.98
            }
        }


class PaymentIntent(BaseModel):
    """Payment intent response schema"""
    client_secret: str
    amount: float
    currency: str
    payment_method_types: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "client_secret": "pi_1234567890_secret_abcdef",
                "amount": 168.98,
                "currency": "kes",
                "payment_method_types": ["card"]
            }
        }


# Coupon Schemas
class CouponValidate(BaseModel):
    """Coupon validation schema"""
    code: str = Field(..., min_length=1, max_length=50)
    order_amount: Optional[float] = Field(None, description="Order amount for validation")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "WELCOME10",
                "order_amount": 100.0
            }
        }


class CouponResponse(BaseModel):
    """Coupon response schema"""
    id: int
    code: str
    name: str
    description: Optional[str]
    discount_type: str
    discount_value: float
    minimum_order_amount: Optional[float]
    maximum_discount_amount: Optional[float]
    usage_limit: Optional[int]
    usage_count: int
    is_valid: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "code": "WELCOME10",
                "name": "Welcome Discount",
                "description": "10% off for new customers",
                "discount_type": "percentage",
                "discount_value": 10.0,
                "minimum_order_amount": 50.0,
                "maximum_discount_amount": 20.0,
                "usage_limit": 100,
                "usage_count": 15,
                "is_valid": True,
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_until": "2025-12-31T23:59:59Z"
            }
        }


class CouponValidationResponse(BaseModel):
    """Coupon validation response schema"""
    is_valid: bool
    discount_amount: float
    message: str
    coupon: Optional[CouponResponse] = None
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "discount_amount": 10.0,
                "message": "Coupon applied successfully",
                "coupon": {
                    "code": "WELCOME10",
                    "name": "Welcome Discount",
                    "discount_type": "percentage",
                    "discount_value": 10.0
                }
            }
        }


# Shipping Schemas
class ShippingRate(BaseModel):
    """Shipping rate schema"""
    method: str
    name: str
    description: str
    cost: float
    estimated_days: int
    
    class Config:
        schema_extra = {
            "example": {
                "method": "standard",
                "name": "Standard Shipping",
                "description": "5-7 business days",
                "cost": 10.0,
                "estimated_days": 7
            }
        }


class ShippingCalculation(BaseModel):
    """Shipping calculation request schema"""
    items: List[OrderItemCreate]
    shipping_address: ShippingAddress
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 2
                    }
                ],
                "shipping_address": {
                    "city": "Nairobi",
                    "state": "Nairobi County",
                    "country": "Kenya"
                }
            }
        }


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
    
    class Config:
        schema_extra = {
            "example": {
                "total_orders": 150,
                "pending_orders": 12,
                "processing_orders": 8,
                "shipped_orders": 15,
                "delivered_orders": 110,
                "cancelled_orders": 5,
                "total_revenue": 12500.50,
                "average_order_value": 83.34
            }
        }


class RevenueStats(BaseModel):
    """Revenue statistics schema"""
    daily_revenue: List[Dict[str, Any]]
    weekly_revenue: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    
    class Config:
        schema_extra = {
            "example": {
                "daily_revenue": [
                    {"date": "2025-01-07", "revenue": 450.00, "orders": 6},
                    {"date": "2025-01-06", "revenue": 320.50, "orders": 4}
                ],
                "weekly_revenue": [
                    {"week": "2025-W01", "revenue": 2150.00, "orders": 28}
                ],
                "monthly_revenue": [
                    {"month": "2025-01", "revenue": 8750.00, "orders": 95}
                ],
                "top_products": [
                    {"product_name": "VDC Toolkit", "revenue": 2400.00, "quantity": 30}
                ]
            }
        }


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
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "per_page": 20,
                "pages": 8,
                "has_prev": False,
                "has_next": True
            }
        }


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
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v < values['min_amount']:
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
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "subtotal": 159.98,
                "tax_amount": 0.0,
                "shipping_amount": 10.0,
                "discount_amount": 0.0,
                "points_discount": 1.0,
                "total_amount": 168.98,
                "available_shipping_methods": [
                    {
                        "method": "standard",
                        "name": "Standard Shipping",
                        "cost": 10.0,
                        "estimated_days": 7
                    }
                ],
                "points_available": 500,
                "points_value": 5.0
            }
        }


# Error Response Schemas
class OrderErrorResponse(BaseModel):
    """Order error response schema"""
    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Insufficient inventory for product",
                "error_code": "INVENTORY_ERROR",
                "details": {
                    "product_id": 1,
                    "requested_quantity": 5,
                    "available_quantity": 2
                }
            }
        }