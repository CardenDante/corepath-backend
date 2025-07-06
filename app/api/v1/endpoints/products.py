# app/api/v1/endpoints/products.py - Created by setup script
"""
CorePath Impact Product Endpoints
API endpoints for product and category management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.user import User
from app.services.product_service import ProductService
from app.services.file_service import FileService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductSearchFilters, PaginatedProductResponse,
    ProductImageCreate, ProductImageResponse,
    ProductVariantCreate, ProductVariantResponse
)
from app.schemas.auth import MessageResponse
from app.api.deps import (
    get_current_user, get_current_admin_user, 
    pagination_params, search_params
)

router = APIRouter()


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Get product service instance"""
    return ProductService(db)


def get_file_service() -> FileService:
    """Get file service instance"""
    return FileService()


# Category Endpoints
@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Create a new product category (Admin only)
    
    - **name**: Category name (required)
    - **description**: Category description
    - **parent_id**: Parent category ID for subcategories
    - **icon**: Category icon identifier
    - **sort_order**: Display order
    - **is_active**: Category status
    """
    try:
        category = product_service.create_category(category_data)
        return CategoryResponse.from_orm(category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    include_children: bool = False,
    product_service: ProductService = Depends(get_product_service)
):
    """
    List product categories
    
    - **parent_id**: Filter by parent category (None for root categories)
    - **is_active**: Filter by active status
    - **include_children**: Include child categories
    """
    try:
        categories = product_service.get_categories(parent_id, is_active, include_children)
        return [CategoryResponse.from_orm(cat) for cat in categories]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    """Get category by ID"""
    category = product_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return CategoryResponse.from_orm(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Update a category (Admin only)"""
    try:
        category = product_service.update_category(category_id, category_data)
        return CategoryResponse.from_orm(category)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category"
        )


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: int,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Delete a category (Admin only)"""
    try:
        success = product_service.delete_category(category_id)
        return MessageResponse(
            message="Category deleted successfully",
            success=success
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )


# Product Endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Create a new product (Admin only)
    
    - **name**: Product name (required)
    - **price**: Product price (required)
    - **category_id**: Category ID (required)
    - **description**: Product description
    - **sku**: Stock keeping unit
    - **inventory_count**: Initial inventory
    """
    try:
        product = product_service.create_product(product_data)
        return ProductResponse.from_orm(product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get("/", response_model=PaginatedProductResponse)
async def list_products(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    is_digital: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    pagination: dict = Depends(pagination_params),
    product_service: ProductService = Depends(get_product_service)
):
    """
    List products with search and filtering
    
    - **q**: Search query (name, description)
    - **category_id**: Filter by category
    - **min_price / max_price**: Price range
    - **is_featured**: Featured products only
    - **is_digital**: Digital products only
    - **in_stock**: In stock products only
    - **sort_by**: Sort field (name, price, created_at)
    - **sort_order**: Sort order (asc, desc)
    """
    try:
        filters = ProductSearchFilters(
            q=q,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            is_featured=is_featured,
            is_digital=is_digital,
            in_stock=in_stock,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = product_service.search_products(
            filters,
            pagination["page"],
            pagination["limit"]
        )
        
        # Convert products to list response format
        products = []
        for product in result["items"]:
            product_data = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "short_description": product.short_description,
                "price": product.price,
                "compare_at_price": product.compare_at_price,
                "discount_percentage": product.discount_percentage,
                "status": product.status,
                "is_featured": product.is_featured,
                "is_in_stock": product.is_in_stock,
                "primary_image": product.primary_image,
                "category_name": product.category.name,
                "view_count": product.view_count,
                "purchase_count": product.purchase_count,
                "created_at": product.created_at
            }
            products.append(ProductListResponse(**product_data))
        
        return PaginatedProductResponse(
            items=products,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"],
            has_prev=result["has_prev"],
            has_next=result["has_next"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get("/featured", response_model=List[ProductListResponse])
async def get_featured_products(
    limit: int = 10,
    product_service: ProductService = Depends(get_product_service)
):
    """Get featured products"""
    try:
        products = product_service.get_featured_products(limit)
        
        result = []
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "short_description": product.short_description,
                "price": product.price,
                "compare_at_price": product.compare_at_price,
                "discount_percentage": product.discount_percentage,
                "status": product.status,
                "is_featured": product.is_featured,
                "is_in_stock": product.is_in_stock,
                "primary_image": product.primary_image,
                "category_name": product.category.name,
                "view_count": product.view_count,
                "purchase_count": product.purchase_count,
                "created_at": product.created_at
            }
            result.append(ProductListResponse(**product_data))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve featured products"
        )


@router.get("/category/{category_id}", response_model=PaginatedProductResponse)
async def get_products_by_category(
    category_id: int,
    include_subcategories: bool = False,
    pagination: dict = Depends(pagination_params),
    product_service: ProductService = Depends(get_product_service)
):
    """Get products by category"""
    try:
        result = product_service.get_products_by_category(
            category_id,
            pagination["page"],
            pagination["limit"],
            include_subcategories
        )
        
        # Convert to list response format
        products = []
        for product in result["items"]:
            product_data = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "short_description": product.short_description,
                "price": product.price,
                "compare_at_price": product.compare_at_price,
                "discount_percentage": product.discount_percentage,
                "status": product.status,
                "is_featured": product.is_featured,
                "is_in_stock": product.is_in_stock,
                "primary_image": product.primary_image,
                "category_name": product.category.name,
                "view_count": product.view_count,
                "purchase_count": product.purchase_count,
                "created_at": product.created_at
            }
            products.append(ProductListResponse(**product_data))
        
        return PaginatedProductResponse(
            items=products,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"],
            has_prev=result["has_prev"],
            has_next=result["has_next"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    """Get product by ID"""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return ProductResponse.from_orm(product)


@router.get("/slug/{slug}", response_model=ProductResponse)
async def get_product_by_slug(
    slug: str,
    product_service: ProductService = Depends(get_product_service)
):
    """Get product by slug (increments view count)"""
    product = product_service.get_product_by_slug(slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return ProductResponse.from_orm(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Update a product (Admin only)"""
    try:
        product = product_service.update_product(product_id, product_data)
        return ProductResponse.from_orm(product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Delete a product (Admin only)"""
    try:
        success = product_service.delete_product(product_id)
        return MessageResponse(
            message="Product deleted successfully",
            success=success
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


# Product Image Endpoints
@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    is_primary: bool = Form(False),
    sort_order: int = Form(0),
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload a product image (Admin only)
    
    - **file**: Image file (JPEG, PNG, GIF, WebP)
    - **alt_text**: Image alt text for accessibility
    - **caption**: Image caption
    - **is_primary**: Set as primary product image
    - **sort_order**: Display order
    """
    try:
        # Upload file
        file_info = await file_service.upload_image(file, "products")
        
        # Create image record
        image_data = ProductImageCreate(
            alt_text=alt_text,
            caption=caption,
            is_primary=is_primary,
            sort_order=sort_order
        )
        
        image = product_service.add_product_image(
            product_id,
            image_data,
            file_info["file_url"]
        )
        
        return ProductImageResponse.from_orm(image)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload product image"
        )


@router.put("/images/{image_id}", response_model=ProductImageResponse)
async def update_product_image(
    image_id: int,
    image_data: ProductImageCreate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Update product image metadata (Admin only)"""
    try:
        image = product_service.update_product_image(image_id, image_data)
        return ProductImageResponse.from_orm(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product image"
        )


@router.delete("/images/{image_id}", response_model=MessageResponse)
async def delete_product_image(
    image_id: int,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service),
    file_service: FileService = Depends(get_file_service)
):
    """Delete a product image (Admin only)"""
    try:
        # Get image info before deletion
        from app.models.product import ProductImage
        image = product_service.db.query(ProductImage).filter(ProductImage.id == image_id).first()
        
        if image:
            # Delete file from storage
            file_service.delete_file(image.image_url)
        
        # Delete database record
        success = product_service.delete_product_image(image_id)
        
        return MessageResponse(
            message="Product image deleted successfully",
            success=success
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product image"
        )


# Product Variant Endpoints
@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def add_product_variant(
    product_id: int,
    variant_data: ProductVariantCreate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Add a product variant (Admin only)"""
    try:
        variant = product_service.add_product_variant(product_id, variant_data)
        return ProductVariantResponse.from_orm(variant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add product variant"
        )


@router.put("/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_product_variant(
    variant_id: int,
    variant_data: ProductVariantCreate,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Update a product variant (Admin only)"""
    try:
        variant = product_service.update_product_variant(variant_id, variant_data)
        return ProductVariantResponse.from_orm(variant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product variant"
        )


@router.delete("/variants/{variant_id}", response_model=MessageResponse)
async def delete_product_variant(
    variant_id: int,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Delete a product variant (Admin only)"""
    try:
        success = product_service.delete_product_variant(variant_id)
        return MessageResponse(
            message="Product variant deleted successfully",
            success=success
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product variant"
        )


# Inventory Management
@router.put("/{product_id}/inventory", response_model=ProductResponse)
async def update_product_inventory(
    product_id: int,
    quantity: int,
    operation: str = "set",  # set, add, subtract
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Update product inventory (Admin only)
    
    - **quantity**: Quantity to set/add/subtract
    - **operation**: Operation type (set, add, subtract)
    """
    try:
        product = product_service.update_inventory(product_id, quantity, operation)
        return ProductResponse.from_orm(product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inventory"
        )


# Bulk Operations
@router.put("/bulk-update", response_model=List[ProductResponse])
async def bulk_update_products(
    product_ids: List[int],
    updates: dict,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Bulk update multiple products (Admin only)
    
    - **product_ids**: List of product IDs to update
    - **updates**: Dictionary of fields to update
    """
    try:
        products = product_service.bulk_update_products(product_ids, updates)
        return [ProductResponse.from_orm(product) for product in products]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update products"
        )


# Analytics Endpoints
@router.get("/analytics/popular", response_model=List[ProductListResponse])
async def get_popular_products(
    limit: int = 10,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Get most popular products by purchase count (Admin only)"""
    try:
        products = product_service.get_popular_products(limit)
        
        result = []
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "short_description": product.short_description,
                "price": product.price,
                "compare_at_price": product.compare_at_price,
                "discount_percentage": product.discount_percentage,
                "status": product.status,
                "is_featured": product.is_featured,
                "is_in_stock": product.is_in_stock,
                "primary_image": product.primary_image,
                "category_name": product.category.name,
                "view_count": product.view_count,
                "purchase_count": product.purchase_count,
                "created_at": product.created_at
            }
            result.append(ProductListResponse(**product_data))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular products"
        )


@router.get("/analytics/low-stock", response_model=List[ProductListResponse])
async def get_low_stock_products(
    threshold: int = 10,
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Get products with low stock (Admin only)"""
    try:
        products = product_service.get_low_stock_products(threshold)
        
        result = []
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "short_description": product.short_description,
                "price": product.price,
                "compare_at_price": product.compare_at_price,
                "discount_percentage": product.discount_percentage,
                "status": product.status,
                "is_featured": product.is_featured,
                "is_in_stock": product.is_in_stock,
                "primary_image": product.primary_image,
                "category_name": product.category.name,
                "view_count": product.view_count,
                "purchase_count": product.purchase_count,
                "created_at": product.created_at
            }
            result.append(ProductListResponse(**product_data))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve low stock products"
        )


@router.get("/analytics/stats")
async def get_product_stats(
    admin_user: User = Depends(get_current_admin_user),
    product_service: ProductService = Depends(get_product_service)
):
    """Get product and category statistics (Admin only)"""
    try:
        stats = product_service.get_product_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product statistics"
        )


# File Management Endpoints
@router.post("/upload-multiple", response_model=List[dict])
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    directory: str = "products",
    admin_user: User = Depends(get_current_admin_user),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload multiple images (Admin only)
    
    - **files**: List of image files
    - **directory**: Upload directory (products, categories, etc.)
    """
    try:
        file_infos = await file_service.upload_multiple_images(files, directory, admin_user.id)
        return file_infos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )


@router.delete("/files", response_model=dict)
async def delete_multiple_files(
    file_urls: List[str],
    admin_user: User = Depends(get_current_admin_user),
    file_service: FileService = Depends(get_file_service)
):
    """Delete multiple files (Admin only)"""
    try:
        result = file_service.delete_multiple_files(file_urls)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete files"
        )


@router.get("/files/storage-stats")
async def get_storage_stats(
    admin_user: User = Depends(get_current_admin_user),
    file_service: FileService = Depends(get_file_service)
):
    """Get file storage statistics (Admin only)"""
    try:
        stats = file_service.get_storage_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage statistics"
        )


@router.post("/files/cleanup-temp")
async def cleanup_temp_files(
    max_age_hours: int = 24,
    admin_user: User = Depends(get_current_admin_user),
    file_service: FileService = Depends(get_file_service)
):
    """Clean up temporary files (Admin only)"""
    try:
        deleted_count = file_service.cleanup_temp_files(max_age_hours)
        return {
            "message": f"Cleaned up {deleted_count} temporary files",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup temporary files"
        )