# app/models/product.py - Created by setup script
"""
CorePath Impact Product Models
Database models for products, categories, and inventory
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

from app.core.database import Base


class ProductStatus(PyEnum):
    """Product status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"


class Category(Base):
    """Product category model"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Category hierarchy
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Display and SEO
    image_url = Column(String(500), nullable=True)
    icon = Column(String(100), nullable=True)  # For category icons
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # SEO fields
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"
    
    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Parent > Child')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    @property
    def product_count(self) -> int:
        """Get number of active products in this category"""
        return len([p for p in self.products if p.status == ProductStatus.ACTIVE.value])


class Product(Base):
    """Main product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(220), unique=True, nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=True, index=True)
    
    # Basic information
    short_description = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Pricing
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)  # Original price for discounts
    cost_price = Column(Float, nullable=True)  # For profit calculations
    
    # Category and organization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    
    # Inventory
    inventory_count = Column(Integer, default=0)
    track_inventory = Column(Boolean, default=True)
    allow_backorder = Column(Boolean, default=False)
    
    # Status and flags
    status = Column(String(20), default=ProductStatus.ACTIVE.value)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    
    # Physical properties
    weight = Column(Float, nullable=True)  # in grams
    dimensions = Column(JSON, nullable=True)  # {"length": 10, "width": 5, "height": 2}
    
    # SEO and marketing
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)  # ["tag1", "tag2"]
    
    # Analytics
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.inventory_count > 0 or self.allow_backorder
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage if compare_at_price is set"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100, 2)
        return 0.0
    
    @property
    def primary_image(self) -> str:
        """Get primary product image URL"""
        primary = next((img for img in self.images if img.is_primary), None)
        return primary.image_url if primary else None
    
    @property
    def all_image_urls(self) -> list:
        """Get all product image URLs"""
        return [img.image_url for img in sorted(self.images, key=lambda x: x.sort_order)]
    
    def increment_view_count(self):
        """Increment product view count"""
        self.view_count += 1
    
    def increment_purchase_count(self, quantity: int = 1):
        """Increment product purchase count"""
        self.purchase_count += quantity
    
    def decrease_inventory(self, quantity: int):
        """Decrease inventory count"""
        if self.track_inventory:
            self.inventory_count = max(0, self.inventory_count - quantity)
    
    def increase_inventory(self, quantity: int):
        """Increase inventory count"""
        if self.track_inventory:
            self.inventory_count += quantity


class ProductImage(Base):
    """Product image model"""
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Image information
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(200), nullable=True)
    caption = Column(String(500), nullable=True)
    
    # Organization
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    # File information
    filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, primary={self.is_primary})>"


class ProductVariant(Base):
    """Product variant model (e.g., different sizes, colors)"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Variant information
    name = Column(String(100), nullable=False)  # e.g., "Large", "Red", "Age 4-9"
    sku = Column(String(100), unique=True, nullable=True)
    
    # Pricing (modifier based on base product price)
    price_modifier = Column(Float, default=0.0)  # +/- amount from base price
    
    # Inventory
    inventory_count = Column(Integer, default=0)
    
    # Variant attributes (flexible JSON storage)
    attributes = Column(JSON, nullable=True)  # {"color": "red", "size": "large"}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    
    def __repr__(self):
        return f"<ProductVariant(id={self.id}, name='{self.name}', product_id={self.product_id})>"
    
    @property
    def final_price(self) -> float:
        """Calculate final price including modifier"""
        return self.product.price + self.price_modifier
    
    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock"""
        return self.inventory_count > 0


class ProductReview(Base):
    """Product review model"""
    __tablename__ = "product_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    
    # Status
    is_approved = Column(Boolean, default=False)
    is_verified_purchase = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProductReview(id={self.id}, product_id={self.product_id}, rating={self.rating})>"


class ProductTag(Base):
    """Product tag model for better organization"""
    __tablename__ = "product_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(60), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Usage count
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ProductTag(id={self.id}, name='{self.name}', usage={self.usage_count})>"