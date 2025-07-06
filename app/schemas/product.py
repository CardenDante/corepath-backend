# app/schemas/product.py - Created by setup script
"""
CorePath Impact Product Schemas
Pydantic models for product-related requests and responses
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


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
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "VDC Toolkits",
                "description": "Complete values-driven parenting toolkits for different age groups",
                "parent_id": None,
                "icon": "toolkit",
                "sort_order": 1,
                "is_active": True,
                "meta_title": "VDC Toolkits - Values Driven Child Parenting Tools",
                "meta_description": "Comprehensive parenting toolkits to raise values-driven children"
            }
        }


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
    image_url: Optional[str]
    product_count: int
    full_path: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "VDC Toolkits",
                "slug": "vdc-toolkits",
                "description": "Complete values-driven parenting toolkits",
                "parent_id": None,
                "icon": "toolkit",
                "sort_order": 1,
                "is_active": True,
                "image_url": "/uploads/categories/toolkit.jpg",
                "product_count": 12,
                "full_path": "VDC Toolkits",
                "created_at": "2025-01-07T10:00:00Z",
                "updated_at": "2025-01-07T10:00:00Z"
            }
        }


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
    alt_text: Optional[str]
    caption: Optional[str]
    is_primary: bool
    sort_order: int
    filename: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductVariantCreate(BaseModel):
    """Product variant creation schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Variant name")
    sku: Optional[str] = Field(None, max_length=100, description="Variant SKU")
    price_modifier: float = Field(0.0, description="Price modifier (+/-)")
    inventory_count: int = Field(0, ge=0, description="Inventory count")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Variant attributes")
    is_active: bool = Field(True, description="Variant status")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Ages 4-9",
                "sku": "VDC-EARLY-001",
                "price_modifier": 0.0,
                "inventory_count": 50,
                "attributes": {
                    "age_group": "4-9",
                    "type": "early_development"
                },
                "is_active": True
            }
        }


class ProductVariantResponse(BaseModel):
    """Product variant response schema"""
    id: int
    name: str
    sku: Optional[str]
    price_modifier: float
    final_price: float
    inventory_count: int
    is_in_stock: bool
    attributes: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


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
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @validator('compare_at_price')
    def validate_compare_price(cls, v, values):
        if v is not None and 'price' in values and v <= values['price']:
            raise ValueError('Compare at price must be greater than regular price')
        return v
    
    @validator('dimensions')
    def validate_dimensions(cls, v):
        if v is not None:
            required_keys = ['length', 'width', 'height']
            if not all(key in v for key in required_keys):
                raise ValueError('Dimensions must include length, width, and height')
            if not all(isinstance(v[key], (int, float)) and v[key] > 0 for key in required_keys):
                raise ValueError('All dimension values must be positive numbers')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Early Value Development Toolkit (Ages 4-9)",
                "short_description": "Complete parenting toolkit for children ages 4-9",
                "description": "A comprehensive toolkit including train-up cards, reward charts, and parenting guides specifically designed for early value development in children aged 4-9 years.",
                "price": 79.99,
                "compare_at_price": 99.99,
                "category_id": 1,
                "sku": "VDC-EARLY-001",
                "inventory_count": 100,
                "track_inventory": True,
                "allow_backorder": False,
                "is_featured": True,
                "is_digital": False,
                "weight": 500.0,
                "dimensions": {
                    "length": 25.0,
                    "width": 20.0,
                    "height": 5.0
                },
                "tags": ["toolkit", "early-development", "values", "parenting"],
                "meta_title": "Early Value Development Toolkit - Ages 4-9",
                "meta_description": "Complete VDC toolkit for raising values-driven children aged 4-9"
            }
        }


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
    status: Optional[str] = Field(None, regex="^(draft|active|inactive|out_of_stock)$")
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
    cost_price: Optional[float]
    view_count: int
    purchase_count: int
    discount_percentage: float
    is_in_stock: bool
    primary_image: Optional[str]
    all_image_urls: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Related data
    category: CategoryResponse
    images: List[ProductImageResponse]
    variants: List[ProductVariantResponse]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Early Value Development Toolkit (Ages 4-9)",
                "slug": "early-value-development-toolkit-ages-4-9",
                "short_description": "Complete parenting toolkit for children ages 4-9",
                "price": 79.99,
                "compare_at_price": 99.99,
                "discount_percentage": 20.0,
                "status": "active",
                "is_in_stock": True,
                "primary_image": "/uploads/products/toolkit-main.jpg",
                "view_count": 156,
                "purchase_count": 23,
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


class ProductListResponse(BaseModel):
    """Product list response schema"""
    id: int
    name: str
    slug: str
    short_description: Optional[str]
    price: float
    compare_at_price: Optional[float]
    discount_percentage: float
    status: str
    is_featured: bool
    is_in_stock: bool
    primary_image: Optional[str]
    category_name: str
    view_count: int
    purchase_count: int
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Early Value Development Toolkit",
                "slug": "early-value-development-toolkit-ages-4-9",
                "short_description": "Complete parenting toolkit for children ages 4-9",
                "price": 79.99,
                "compare_at_price": 99.99,
                "discount_percentage": 20.0,
                "status": "active",
                "is_featured": True,
                "is_in_stock": True,
                "primary_image": "/uploads/products/toolkit-main.jpg",
                "category_name": "VDC Toolkits",
                "view_count": 156,
                "purchase_count": 23,
                "created_at": "2025-01-07T10:00:00Z"
            }
        }


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
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
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
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "per_page": 20,
                "pages": 3,
                "has_prev": False,
                "has_next": True
            }
        }