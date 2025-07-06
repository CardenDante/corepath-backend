# app/models/order.py - Created by setup script
"""
CorePath Impact Order Models
Database models for orders, cart, and payment tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from app.core.database import Base


class OrderStatus(PyEnum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(PyEnum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ShippingMethod(PyEnum):
    """Shipping method enumeration"""
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    DIGITAL = "digital"
    PICKUP = "pickup"


class Order(Base):
    """Main order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order status and tracking
    status = Column(String(20), default=OrderStatus.PENDING.value)
    
    # Pricing breakdown
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    shipping_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    points_discount = Column(Float, nullable=False, default=0.0)  # Points used for discount
    total_amount = Column(Float, nullable=False)
    
    # Currency and payment
    currency = Column(String(3), default="KES")
    
    # Shipping information
    shipping_method = Column(String(20), default=ShippingMethod.STANDARD.value)
    shipping_address = Column(JSON, nullable=True)  # Full address as JSON
    billing_address = Column(JSON, nullable=True)   # Billing address as JSON
    
    # Customer information (denormalized for order history)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(200), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    
    # Order notes and tracking
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    tracking_number = Column(String(100), nullable=True)
    
    # Points earned from this order
    points_earned = Column(Integer, default=0)
    points_used = Column(Integer, default=0)
    
    # Special flags
    is_gift = Column(Boolean, default=False)
    gift_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', status='{self.status}')>"
    
    @property
    def item_count(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items)
    
    @property
    def is_paid(self) -> bool:
        """Check if order is fully paid"""
        paid_amount = sum(
            payment.amount for payment in self.payments 
            if payment.status == PaymentStatus.COMPLETED.value
        )
        return paid_amount >= self.total_amount
    
    @property
    def payment_status(self) -> str:
        """Get overall payment status"""
        if not self.payments:
            return PaymentStatus.PENDING.value
        
        completed_payments = [p for p in self.payments if p.status == PaymentStatus.COMPLETED.value]
        failed_payments = [p for p in self.payments if p.status == PaymentStatus.FAILED.value]
        
        if self.is_paid:
            return PaymentStatus.COMPLETED.value
        elif failed_payments:
            return PaymentStatus.FAILED.value
        else:
            return PaymentStatus.PENDING.value
    
    @property
    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING.value, OrderStatus.PROCESSING.value]
    
    @property
    def can_refund(self) -> bool:
        """Check if order can be refunded"""
        return self.status in [OrderStatus.DELIVERED.value] and self.is_paid
    
    def calculate_totals(self):
        """Recalculate order totals based on items"""
        self.subtotal = sum(item.total_price for item in self.items)
        
        # Calculate tax (if applicable)
        tax_rate = 0.0  # No tax for now, can be configured later
        self.tax_amount = self.subtotal * tax_rate
        
        # Calculate total
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.shipping_amount - 
            self.discount_amount - 
            self.points_discount
        )
        
        # Ensure total is not negative
        self.total_amount = max(0, self.total_amount)
    
    def add_points_discount(self, points_amount: int, points_value: float = 0.01):
        """Apply points discount to order"""
        discount = points_amount * points_value
        self.points_discount = min(discount, self.subtotal)
        self.points_used = int(self.points_discount / points_value)
        self.calculate_totals()
    
    def calculate_points_earned(self, points_rate: float = 0.01):
        """Calculate points earned from this order"""
        self.points_earned = int(self.total_amount * points_rate)


class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Item details (captured at time of order)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100), nullable=True)
    variant_name = Column(String(100), nullable=True)
    
    # Pricing and quantity
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Product snapshot at time of order (for history)
    product_snapshot = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", backref="order_items")
    variant = relationship("ProductVariant", backref="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product='{self.product_name}', qty={self.quantity})>"
    
    def calculate_total(self):
        """Calculate total price for this item"""
        self.total_price = self.unit_price * self.quantity


class ShoppingCart(Base):
    """Shopping cart model (persistent cart)"""
    __tablename__ = "shopping_carts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), nullable=True, index=True)  # For guest carts
    
    # Cart totals (calculated)
    subtotal = Column(Float, default=0.0)
    item_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ShoppingCart(id={self.id}, user_id={self.user_id}, items={len(self.items)})>"
    
    def calculate_totals(self):
        """Recalculate cart totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.item_count = sum(item.quantity for item in self.items)
    
    def clear(self):
        """Clear all items from cart"""
        for item in self.items:
            # Remove from session (will be deleted due to cascade)
            pass
        self.items.clear()
        self.calculate_totals()


class CartItem(Base):
    """Shopping cart item model"""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("shopping_carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True)
    
    # Item details
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # Price at time of adding
    total_price = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cart = relationship("ShoppingCart", back_populates="items")
    product = relationship("Product", backref="cart_items")
    variant = relationship("ProductVariant", backref="cart_items")
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, product_id={self.product_id}, qty={self.quantity})>"
    
    def calculate_total(self):
        """Calculate total price for this cart item"""
        # Use variant price if available, otherwise product price
        if self.variant_id and self.variant:
            self.unit_price = self.variant.final_price
        elif self.product:
            self.unit_price = self.product.price
        
        self.total_price = self.unit_price * self.quantity
    
    @property
    def is_available(self) -> bool:
        """Check if item is still available for purchase"""
        if not self.product or not self.product.is_in_stock:
            return False
        
        if self.variant_id and self.variant:
            return self.variant.is_in_stock and self.variant.is_active
        
        return True


class Payment(Base):
    """Payment tracking model"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="KES")
    status = Column(String(20), default=PaymentStatus.PENDING.value)
    
    # Payment method information
    payment_method = Column(String(50), nullable=False)  # card, mobile_money, bank_transfer
    payment_provider = Column(String(50), nullable=True)  # stripe, mpesa, etc.
    
    # External payment tracking
    external_payment_id = Column(String(200), nullable=True, index=True)
    transaction_reference = Column(String(200), nullable=True)
    
    # Payment metadata
    payment_details = Column(JSON, nullable=True)  # Store provider-specific data
    failure_reason = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status='{self.status}')>"
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED.value
        self.processed_at = datetime.utcnow()
    
    def mark_failed(self, reason: str = None):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED.value
        self.failure_reason = reason
        self.processed_at = datetime.utcnow()


class Coupon(Base):
    """Coupon/discount code model"""
    __tablename__ = "coupons"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Discount configuration
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Float, nullable=False)
    minimum_order_amount = Column(Float, nullable=True)
    maximum_discount_amount = Column(Float, nullable=True)
    
    # Usage limits
    usage_limit = Column(Integer, nullable=True)  # Total usage limit
    usage_limit_per_user = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Validity period
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Coupon(id={self.id}, code='{self.code}', value={self.discount_value})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        
        return True
    
    def calculate_discount(self, order_amount: float) -> float:
        """Calculate discount amount for given order"""
        if not self.is_valid:
            return 0.0
        
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return 0.0
        
        if self.discount_type == "percentage":
            discount = order_amount * (self.discount_value / 100)
        else:  # fixed_amount
            discount = self.discount_value
        
        # Apply maximum discount limit
        if self.maximum_discount_amount:
            discount = min(discount, self.maximum_discount_amount)
        
        return min(discount, order_amount)  # Cannot exceed order amount


class CouponUsage(Base):
    """Track coupon usage by users"""
    __tablename__ = "coupon_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    discount_amount = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    coupon = relationship("Coupon", backref="usage_records")
    user = relationship("User", backref="coupon_usage")
    order = relationship("Order", backref="coupon_usage")
    
    def __repr__(self):
        return f"<CouponUsage(coupon_id={self.coupon_id}, user_id={self.user_id}, discount={self.discount_amount})>"