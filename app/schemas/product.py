# app/schemas/product.py - Fixed for Pydantic v2
"""
CorePath Impact Product Schemas
Pydantic v2 compatible models for product-related requests and responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    icon: Optional[str] = Field(None, max_length=100, description="Category icon")
    sort_order: int = Field(0, description="Sort order")
    is_active: bool = Field(True, description="Category status")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO description")


class CategoryCreate(CategoryBase):
    """Category creation schema"""
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class CategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)


class CategoryResponse(CategoryBase):
    """Category response schema"""
    id: int
    slug: str
    image_url: Optional[str] = None
    product_count: int
    full_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class ProductImageCreate(BaseModel):
    """Product image creation schema"""
    alt_text: Optional[str] = Field(None, max_length=200, description="Image alt text")
    caption: Optional[str] = Field(None, max_length=500, description="Image caption")
    is_primary: bool = Field(False, description="Is primary image")
    sort_order: int = Field(0, description="Display order")


class ProductImageResponse(BaseModel):
    """Product image response schema"""
    id: int
    image_url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    is_primary: bool
    sort_order: int
    filename: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    """Product variant creation schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Variant name")
    sku: Optional[str] = Field(None, max_length=100, description="Variant SKU")
    price_modifier: float = Field(0.0, description="Price modifier (+/-)")
    inventory_count: int = Field(0, ge=0, description="Inventory count")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Variant attributes")
    is_active: bool = Field(True, description="Variant status")


class ProductVariantResponse(BaseModel):
    """Product variant response schema"""
    id: int
    name: str
    sku: Optional[str] = None
    price_modifier: float
    final_price: float
    inventory_count: int
    is_in_stock: bool
    attributes: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    short_description: Optional[str] = Field(None, max_length=500, description="Short description")
    description: Optional[str] = Field(None, description="Full description")
    price: float = Field(..., gt=0, description="Product price")
    compare_at_price: Optional[float] = Field(None, gt=0, description="Original price for discounts")
    category_id: int = Field(..., description="Category ID")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")
    inventory_count: int = Field(0, ge=0, description="Inventory count")
    track_inventory: bool = Field(True, description="Track inventory")
    allow_backorder: bool = Field(False, description="Allow backorder")
    is_featured: bool = Field(False, description="Featured product")
    is_digital: bool = Field(False, description="Digital product")
    weight: Optional[float] = Field(None, gt=0, description="Weight in grams")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Dimensions")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO description")


class ProductCreate(ProductBase):
    """Product creation schema"""
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @field_validator('compare_at_price')
    @classmethod
    def validate_compare_price(cls, v, info):
        if v is not None and 'price' in info.data and v <= info.data['price']:
            raise ValueError('Compare at price must be greater than regular price')
        return v
    
    @field_validator('dimensions')
    @classmethod
    def validate_dimensions(cls, v):
        if v is not None:
            required_keys = ['length', 'width', 'height']
            if not all(key in v for key in required_keys):
                raise ValueError('Dimensions must include length, width, and height')
            if not all(isinstance(v[key], (int, float)) and v[key] > 0 for key in required_keys):
                raise ValueError('All dimension values must be positive numbers')
        return v


class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    sku: Optional[str] = Field(None, max_length=100)
    inventory_count: Optional[int] = Field(None, ge=0)
    track_inventory: Optional[bool] = None
    allow_backorder: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|inactive|out_of_stock)$")
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[Dict[str, float]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)


class ProductResponse(ProductBase):
    """Product response schema"""
    id: int
    slug: str
    status: str
    cost_price: Optional[float] = None
    view_count: int
    purchase_count: int
    discount_percentage: float
    is_in_stock: bool
    primary_image: Optional[str] = None
    all_image_urls: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    category: CategoryResponse
    images: List[ProductImageResponse] = []
    variants: List[ProductVariantResponse] = []
    
    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Product list response schema"""
    id: int
    name: str
    slug: str
    short_description: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    discount_percentage: float
    status: str
    is_featured: bool
    is_in_stock: bool
    primary_image: Optional[str] = None
    category_name: str
    view_count: int
    purchase_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProductSearchFilters(BaseModel):
    """Product search and filter schema"""
    q: Optional[str] = Field(None, description="Search query")
    category_id: Optional[int] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    is_featured: Optional[bool] = Field(None, description="Featured products only")
    is_digital: Optional[bool] = Field(None, description="Digital products only")
    in_stock: Optional[bool] = Field(None, description="In stock products only")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v, info):
        if v is not None and 'min_price' in info.data and info.data['min_price'] is not None:
            if v < info.data['min_price']:
                raise ValueError('Max price must be greater than min price')
        return v


class PaginatedProductResponse(BaseModel):
    """Paginated product list response"""
    items: List[ProductListResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool